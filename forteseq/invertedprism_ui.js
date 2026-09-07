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
//   path       <n> <anchorA> <anchorB> [t r g b root]*n   (n=0 whenever a full pair isn't ready --
//              anchorA/anchorB are ALWAYS sent, even -1, and are the engine's own pathAnchor: the
//              authoritative source for which points get an A/B tag, see path() below)
// `heardcolor r g b a` (the live reharmoniser) is filtered out before it reaches this jsui --
// it drives a `panel` swatch up in the control row instead (see build_invertedprism.py).
//
// Sends back:  addpoint <pc> <lum>   setpoint <i> <pc> <lum>   rempoint <i>   setgroup <i> <grp>
//              setpathanchor <slot> <i>
// Shift-click an existing point to cycle it through the polychord groups (0..3); each group
// blends independently into its own blob and they all sound together, stacked.
// Right-click an existing point (or cmd-click on macOS / ctrl-click on Windows, where either is
// reliably delivered) to cycle it through the path-anchor slots instead: unset -> A -> B -> unset.
// With both A and B set, the device's "Path" button commits every
// sampled step as a simultaneous polychord; "Next" instead walks one step at a time, replacing
// just the currently-sounding chord on each press (see invertedprism.js's pathcommit/pathnext).

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
var gPathAnchor = [-1, -1];    // point indices cycled via cmd-click; -1 = unset
var gPath = [];                // [{t, r,g,b, root}, ...] read-only preview of the path between them
var gBaseHue = 0;              // echoed by the engine's "basehue" message -- see basehue() below
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
	if (typeof pcToColor === 'function') return pcToColor(pc, { baseHue: gBaseHue, sat: 0.62, lum: 0.55 });
	return { r: 0.6, g: 0.6, b: 0.6 };
}

// --- inbound ------------------------------------------------------------------------------

// echoed every engine tick (see invertedprism.js's recompute()) so the column labels and each
// point's own dot -- both drawn locally via pcColor() above -- actually track the Hue control,
// instead of always drawing at a hardcoded baseHue regardless of what it's set to.
function basehue(v) { gBaseHue = Number(v) || 0; mgraphics.redraw(); }

function points() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gPoints = [];
	for (var i = 0; i < n && (4 + i * 4) < a.length; i++) {
		gPoints.push([Math.round(a[1 + i * 4]), a[2 + i * 4], Math.round(a[3 + i * 4]), Math.round(a[4 + i * 4])]);
	}
	// gPathAnchor is NOT touched here -- the "path" message (below) is the engine's own echo of
	// its pathAnchor state and is the only thing that gets to correct it, so the two can never
	// drift apart even when rempoint/clear/pathcommit/a FIFO addpoint() eviction reshuffle indices.
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
// "path <n> <anchorA> <anchorB> [t r g b root]*n" -- anchorA/anchorB are the engine's OWN
// pathAnchor, always sent (even -1, even with only one set): this is the single source of truth
// for which points show an A/B tag, overriding whatever the local cmd-click cycle guessed.
function path() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gPathAnchor = [Math.round(a[1] == null ? -1 : a[1]), Math.round(a[2] == null ? -1 : a[2])];
	gPath = [];
	for (var i = 0; i < n && (7 + i * 5) < a.length; i++) {
		var o = 3 + i * 5;
		gPath.push({ t: a[o], r: a[o + 1], g: a[o + 2], b: a[o + 3], root: Math.round(a[o + 4]) });
	}
	mgraphics.redraw();
}

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

// Max's jsui onclick passes modifiers as (x, y, but, cmd, shift, capslock, option, ctrl) -- "cmd"
// only ever fires on macOS (it's the Command key); on Windows the equivalent secondary-click
// modifier arrives as "ctrl" instead, in the LAST slot, not the 4th. Reading only `cmd` (as this
// function used to) meant cmd-click silently never fired on Windows at all -- and even `ctrl`
// stayed unreliable in testing (Windows may translate a physical Ctrl+left-click into a
// synthetic right-click before onclick ever sees a modifier flag). So this also accepts a plain
// right-click (but===2) as an unambiguous, OS-independent trigger -- jsui still gets onclick for
// a right-click while the device is locked/running (Live's normal state), it only opens Max's
// object context menu in an unlocked *edit* patcher, which this isn't.
function onclick(x, y, but, cmd, shift, capslock, option, ctrl) {
	var p = plot();
	var i = pickPoint(x, y);
	if (shift && i >= 0) {
		// shift-click an existing point: cycle it through the polychord groups instead of dragging
		var g = ((gPoints[i][3] || 0) + 1) % GROUP_RING.length;
		outlet(0, "setgroup", i, g);
		dragIdx = -1;
		return;
	}
	if ((cmd || ctrl || but === 2) && i >= 0) {
		// cmd-click an existing point: cycle it through the path-anchor slots (unset -> A -> B ->
		// unset) instead of dragging. This mutates gPathAnchor optimistically for instant visual
		// feedback, but the engine's own "path" echo (see path() above) is the actual source of
		// truth and will correct this moments later if `points` has changed shape meanwhile.
		if (gPathAnchor[0] === i) { gPathAnchor[0] = -1; gPathAnchor[1] = i; }
		else if (gPathAnchor[1] === i) { gPathAnchor[1] = -1; }
		else if (gPathAnchor[0] < 0) { gPathAnchor[0] = i; }
		else if (gPathAnchor[1] < 0) { gPathAnchor[1] = i; }
		else { gPathAnchor[0] = i; }   // both slots taken by other points -- replace A
		outlet(0, "setpathanchor", 0, gPathAnchor[0]);
		outlet(0, "setpathanchor", 1, gPathAnchor[1]);
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
		// path-anchor marker: a letter tag above any point cmd-clicked into slot A or B
		var anchorTag = (gPathAnchor[0] === i) ? 'A' : ((gPathAnchor[1] === i) ? 'B' : null);
		if (anchorTag) {
			mgraphics.set_source_rgba([1, 1, 1, 0.95]);
			mgraphics.set_font_size(10);
			mgraphics.move_to(px - 3, py - r - 6);
			mgraphics.show_text(anchorTag);
		}
	}

	// path preview: a dotted line + small dots for each sampled step, read-only (the "Path"
	// button in the device commits it into real points). Drawn at each step's OWN root/lightness,
	// same coordinate helpers the cluster blobs already use above.
	if (gPath.length > 1) {
		var stepXY = [];
		for (var si = 0; si < gPath.length; si++) {
			var st = gPath[si];
			var lum = (typeof rgbToHsl === 'function') ? rgbToHsl(st.r, st.g, st.b).l : 0.5;
			stepXY.push([colX(st.root, p), lumY(lum, p)]);
		}
		mgraphics.set_source_rgba([1, 1, 1, 0.35]);
		mgraphics.set_line_width(1);
		for (si = 0; si < stepXY.length; si++) {
			if (si === 0) mgraphics.move_to(stepXY[si][0], stepXY[si][1]);
			else mgraphics.line_to(stepXY[si][0], stepXY[si][1]);
		}
		mgraphics.stroke();
		for (si = 0; si < gPath.length; si++) {
			var sx = stepXY[si][0], sy = stepXY[si][1];
			mgraphics.set_source_rgba([gPath[si].r, gPath[si].g, gPath[si].b, 0.9]);
			mgraphics.ellipse(sx - 4, sy - 4, 8, 8);
			mgraphics.fill();
			mgraphics.set_source_rgba([1, 1, 1, 0.8]);
			mgraphics.set_line_width(1);
			mgraphics.ellipse(sx - 4, sy - 4, 8, 8);
			mgraphics.stroke();
		}
	}

	// readout
	mgraphics.set_source_rgba([0.85, 0.88, 0.92, 0.9]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(p.x0, p.h - 5);
	mgraphics.show_text(String(gHarm[0]) + '   diss ' + gHarm[2] + '%');
}
