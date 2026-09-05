// invertedprism_ui.js -- jsui canvas for invertedprism.amxd.
//
// The canvas is a (circle-of-fifths x lightness) space: X = which pitch class (12 columns in
// fifths order, C..F), Y = lightness / register (top = light/high, bottom = dark/low). You drop
// colour points (each a fundamental), drag them between columns / up and down; the engine blends
// them and a glowing blob shows where the resultant colour -- hence the chord -- lands.
//
// Fed by invertedprism.js's tagged outlet, split off by the patch's `route`:
//   points     <count>  pc lum on grp  pc lum on grp ...
//   clusters   <count>  grp r g b x01 y01 rootPc diss%  ... (one polychord blob per active group)
//   harm       <name> <root pc> <diss %>            (footer text; name is every group's chord, joined)
// `heardcolor r g b a` (the live reharmoniser) is filtered out before it reaches this jsui --
// it drives a `panel` swatch up in the control row instead (see build_invertedprism.py).
//
// Sends back:  addpoint <pc> <lum>   setpoint <i> <pc> <lum>   rempoint <i>   setgroup <i> <grp>
// Shift-click an existing point to cycle it through the polychord groups (0..3); each group
// blends independently into its own blob and they all sound together, stacked.

if (typeof include === 'function') include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;
outlets = 1;

var NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
var PAD_L = 26, PAD_T = 22, PAD_R = 12, PAD_B = 18;
var GRAB_PX = 14;
var BG = [0.07, 0.075, 0.09, 1];

var gPoints = [];              // [[pc, lum, on, grp], ...]
var gClusters = [];            // [{grp, r,g,b, x,y, root, diss}, ...] one blob per active group
var gHarm = ['-', -1, 0];
var dragIdx = -1;
// (the reharmoniser swatch lives outside the canvas now, up with the other controls -- a
// `panel` object driven directly by "heardcolor", filtered out of this jsui's inlet before
// it gets here. See build_invertedprism.py.)

// polychord group -> ring colour drawn around a point's dot (group 0 = no ring, its own colour is enough)
var GROUP_RING = [null, [1, 0.62, 0.16], [0.3, 0.85, 1], [0.85, 0.4, 1]];

function mod(n, m) { return ((n % m) + m) % m; }
function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
function colOfPc(pc) { return mod(Math.round(pc) * 7, 12); }         // fifths-circle column index
function pcOfCol(idx) { return mod(Math.round(idx) * 7, 12); }       // inverse

function plot() {
	var w = box.rect[2] - box.rect[0], h = box.rect[3] - box.rect[1];
	return { w: w, h: h, x0: PAD_L, y0: PAD_T, pw: w - PAD_L - PAD_R, ph: h - PAD_T - PAD_B };
}
function colX(pc, p) { return p.x0 + (colOfPc(pc) + 0.5) / 12 * p.pw; }
function lumY(lum, p) { return p.y0 + (1 - clamp01(lum)) * p.ph; }
function xToCol(x, p) {
	var c = Math.round((x - p.x0) / p.pw * 12 - 0.5);
	return c < 0 ? 0 : (c > 11 ? 11 : c);
}
function yToLum(y, p) { return clamp01(1 - (y - p.y0) / p.ph); }

function pcColor(pc) {
	if (typeof pcToColor === 'function') return pcToColor(pc, { baseHue: 220, sat: 0.62, lum: 0.55 });
	return { r: 0.6, g: 0.6, b: 0.6 };
}

// --- inbound ------------------------------------------------------------------------------

function points() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gPoints = [];
	for (var i = 0; i < n && (4 + i * 4) < a.length; i++) {
		gPoints.push([Math.round(a[1 + i * 4]), a[2 + i * 4], Math.round(a[3 + i * 4]), Math.round(a[4 + i * 4])]);
	}
	mgraphics.redraw();
}
function clusters() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gClusters = [];
	for (var i = 0; i < n && (8 + i * 8) < a.length; i++) {
		var o = 1 + i * 8;
		gClusters.push({
			grp: Math.round(a[o]), r: a[o + 1], g: a[o + 2], b: a[o + 3],
			x: a[o + 4], y: a[o + 5], root: Math.round(a[o + 6]), diss: a[o + 7]
		});
	}
	mgraphics.redraw();
}
function harm() { var a = arrayfromargs(arguments); gHarm = [a[0], Math.round(a[1]), a[2]]; mgraphics.redraw(); }

// --- mouse -------------------------------------------------------------------------------

function pickPoint(x, y) {
	var p = plot(), best = -1, bd = GRAB_PX * GRAB_PX;
	for (var i = 0; i < gPoints.length; i++) {
		var px = colX(gPoints[i][0], p), py = lumY(gPoints[i][1], p);
		var d = (x - px) * (x - px) + (y - py) * (y - py);
		if (d < bd) { bd = d; best = i; }
	}
	return best;
}

function onclick(x, y, but, cmd, shift) {
	var p = plot();
	var i = pickPoint(x, y);
	if (shift && i >= 0) {
		// shift-click an existing point: cycle it through the polychord groups instead of dragging
		var g = ((gPoints[i][3] || 0) + 1) % GROUP_RING.length;
		outlet(0, "setgroup", i, g);
		dragIdx = -1;
		return;
	}
	dragIdx = i;
	if (dragIdx < 0) {
		outlet(0, "addpoint", pcOfCol(xToCol(x, p)), yToLum(y, p));
	}
}
function ondrag(x, y, but) {
	if (dragIdx < 0) return;
	var p = plot();
	outlet(0, "setpoint", dragIdx, pcOfCol(xToCol(x, p)), yToLum(y, p));
	if (!but) dragIdx = -1;
}
function ondblclick(x, y) {
	var i = pickPoint(x, y);
	if (i >= 0) { outlet(0, "rempoint", i); dragIdx = -1; }
}

// --- paint ------------------------------------------------------------------------------

function paint() {
	var p = plot();
	mgraphics.set_source_rgba(BG);
	mgraphics.rectangle(0, 0, p.w, p.h);
	mgraphics.fill();

	// column guides + note names (fifths order)
	mgraphics.set_font_size(9);
	for (var c = 0; c < 12; c++) {
		var pc = pcOfCol(c);
		var x = p.x0 + (c + 0.5) / 12 * p.pw;
		mgraphics.set_source_rgba([1, 1, 1, 0.05]);
		mgraphics.set_line_width(1);
		mgraphics.move_to(x, p.y0); mgraphics.line_to(x, p.y0 + p.ph); mgraphics.stroke();
		var col = pcColor(pc);
		mgraphics.set_source_rgba([col.r, col.g, col.b, 0.7]);
		mgraphics.move_to(x - 6, p.y0 - 8);
		mgraphics.show_text(NOTE_NAMES[pc]);
	}
	// light / dark edge hints
	mgraphics.set_source_rgba([1, 1, 1, 0.25]);
	mgraphics.move_to(4, p.y0 + 6); mgraphics.show_text('hi');
	mgraphics.move_to(4, p.y0 + p.ph - 2); mgraphics.show_text('lo');

	// blend blob(s): one disc per active polychord group, at its OWN root/register -- each
	// group blends independently, so with several groups you get several blobs, and all of
	// them sound together as the polychord. Size + glow track that group's saturation -- a
	// pure resultant (consonant) blooms; a muddy one (dissonant) stays a small dim dot.
	for (var ci = 0; ci < gClusters.length; ci++) {
		var cl = gClusters[ci];
		var bx = p.x0 + (Math.round(cl.x * 12) + 0.5) / 12 * p.pw;   // root column
		var by = p.y0 + (1 - clamp01(cl.y)) * p.ph;
		var bsat = (typeof rgbToHsl === 'function') ? rgbToHsl(cl.r, cl.g, cl.b).s : 0.5;
		var maxR = Math.min(p.pw, p.ph) * (0.06 + bsat * 0.26);
		for (var k = 5; k >= 1; k--) {
			var rr = maxR * k / 5;
			mgraphics.set_source_rgba([cl.r, cl.g, cl.b, 0.05 + bsat * 0.11]);
			mgraphics.ellipse(bx - rr, by - rr, rr * 2, rr * 2);
			mgraphics.fill();
		}
		mgraphics.set_source_rgba([cl.r, cl.g, cl.b, 0.6]);
		mgraphics.set_line_width(1);
		mgraphics.ellipse(bx - maxR, by - maxR, maxR * 2, maxR * 2);
		mgraphics.stroke();
		mgraphics.set_source_rgba([cl.r, cl.g, cl.b, 0.95]);
		mgraphics.ellipse(bx - 5, by - 5, 10, 10);
		mgraphics.fill();
	}

	// the colour points -- a ring around a dot marks which polychord group it belongs to
	// (group 0, the default, gets no ring). Shift-click a point to cycle its ring/group.
	for (var i = 0; i < gPoints.length; i++) {
		var pt = gPoints[i];
		var px = colX(pt[0], p), py = lumY(pt[1], p);
		var lc = pcColor(pt[0]);
		var on = pt[2] !== 0;
		var grp = pt[3] || 0;
		var r = (i === dragIdx) ? 8 : 6;
		mgraphics.set_source_rgba([lc.r, lc.g, lc.b, on ? 0.95 : 0.3]);
		mgraphics.ellipse(px - r, py - r, r * 2, r * 2);
		mgraphics.fill();
		mgraphics.set_source_rgba([0, 0, 0, 0.5]);
		mgraphics.set_line_width(1);
		mgraphics.ellipse(px - r, py - r, r * 2, r * 2);
		mgraphics.stroke();
		var ringCol = GROUP_RING[grp];
		if (ringCol) {
			mgraphics.set_source_rgba([ringCol[0], ringCol[1], ringCol[2], 0.9]);
			mgraphics.set_line_width(2);
			mgraphics.ellipse(px - r - 3, py - r - 3, (r + 3) * 2, (r + 3) * 2);
			mgraphics.stroke();
		}
	}

	// readout
	mgraphics.set_source_rgba([0.85, 0.88, 0.92, 0.9]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(p.x0, p.h - 5);
	mgraphics.show_text(String(gHarm[0]) + '   diss ' + gHarm[2] + '%');
}
