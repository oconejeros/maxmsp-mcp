// multichord_ui.js -- jsui canvas for multichord.amxd. Two views, picked independently of Mode
// by the View control (`view()` below) -- either exploration mode (Nearest/Steps) can be looked
// at either way:
//
// Rings (view 0) -- an annular voice-leading space: the current chord sits at the centre; its
//   neighbours (whichever mode's graph produced them) are laid out in concentric rings, ring
//   radius = distance (voice-leading distance in Nearest mode, elementary-move hop count in
//   Steps mode), angular position = hue. Click a node to jump there.
// Spiral (view 1) -- madmusicalscience.com/cs.html-style: ONE continuous curve winding n times
//   around an annulus (n = chord size), k equally-spaced points per winding (k = scale size --
//   the configured scale in Steps mode, or the chromatic 12-point circle in Nearest mode, which
//   has no scale of its own). A dot per voice, a connecting arc threading voice-to-voice along
//   the spiral, and a small pairwise scale-step-distance matrix. Read-only (no click navigation
//   -- these dots are the current chord's own voices, not reachable neighbours; use Nav or the
//   ▲/▼ buttons).
//
// Fed by multichord.js's tagged outlet, split off by the patch's `route`:
//   center    <mode> <classIdx> <rootPc> <diss%> <r> <g> <b> <n> <pc0> <pc1> ... <pcN-1>
//   ringinfo  <k>  dist_0 dist_1 ... dist_{k-1}                      (ring index -> distance)
//   nodes     <n>  [ring angleDeg r g b card pc_0..pc_{card-1} rank]*n  (pcs, not classIdx/t --
//             lets the spiral view place same-cardinality neighbours without its own 351-class
//             table; each node's block is variable-width, sized by its own `card`)
//   scale     <scaleLen> <pc0> ... <pc_{scaleLen-1}>   (always sent -- chromatic-12 in Nearest mode)
//   voices    <k> <deg0> ... <deg_{k-1}>               (always sent)
//   shiftmoves <count> [voiceIdx degree rank]*count    (every direct single-voice-shift move from
//             the current chord, each already resolved to its rank in the full neighbour list --
//             NOT sourced from `nodes`, which is capped/decimated for Rings' whole-graph view and
//             would starve out most of this small same-cardinality set)
//   view      <0|1>                                    (local UI-only setting, from the View menu)
//
// Sends back:  selectrank <rank>   (a node was clicked -- jump there and recentre)
//   -- in Rings view (0), any visible node; in Spiral view (1), only a same-cardinality
//   single-voice-moved "shift ghost" (see paintVoiceRings) -- drop/add-sized neighbours aren't
//   geometrically placeable on a fixed-winding-count spiral, so they stay Rings/Nav-only.

if (typeof include === 'function') include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;
outlets = 1;

var NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
var PAD = 10;
var FOOTER_H = 20;
var GRAB_PX = 12;
var BG = [0.07, 0.075, 0.09, 1];

var gMode = 0;
var gView = 0;   // 0 = Rings, 1 = Spiral -- independent of gMode, set only by view()
var gCenter = { classIdx: 0, rootPc: 0, diss: 0, r: 0.6, g: 0.6, b: 0.6, pcs: [0, 4, 7] };
var gRingDist = [];        // [dist0, dist1, ...] ring index -> voice-leading distance
var gNodes = [];           // [{ring, angleDeg, r,g,b, classIdx, t, rank}, ...]
var gScale = [];           // Steps mode: the scale's own pcs, index = degree
var gVoices = [];          // Steps mode: current chord's degree per voice, ascending
var gShiftMoves = [];      // every direct single-voice-shift move: [{voiceIdx, degree, rank}, ...]
var gGhostHits = [];       // Spiral view only: clickable {x, y, rank}, rebuilt from gShiftMoves each paint
var hoverRank = -1;

function voiceColor(i, k) {
	var h = (k > 0) ? (i / k * 300) : 0;   // 0..300 deg -- rainbow-ish, avoids wrapping back to red
	if (typeof hslToRgb === 'function') return hslToRgb(h, 0.6, 0.62);
	return { r: 0.6, g: 0.6, b: 0.6 };
}
function circStepDist(a, b, n) { var d = Math.abs(a - b) % n; return Math.min(d, n - d); }

function plot() {
	var w = box.rect[2] - box.rect[0], h = box.rect[3] - box.rect[1];
	var side = Math.min(w, h - FOOTER_H) - PAD * 2;
	return { w: w, h: h, cx: w / 2, cy: (h - FOOTER_H) / 2, maxR: side / 2 };
}
function ringRadius(ringIdx, p) {
	var k = Math.max(1, gRingDist.length);
	return p.maxR * (ringIdx + 1) / (k + 0.4);
}
function nodeXY(node, p) {
	var rr = ringRadius(node.ring, p);
	var a = node.angleDeg * Math.PI / 180;
	return { x: p.cx + rr * Math.cos(a), y: p.cy + rr * Math.sin(a) };
}

// --- inbound ------------------------------------------------------------------------------

function center() {
	var a = arrayfromargs(arguments);
	gMode = Math.round(a[0]);
	var n = Math.round(a[7] || 0), pcs = [];
	for (var i = 0; i < n; i++) pcs.push(Math.round(a[8 + i]));
	gCenter = {
		classIdx: Math.round(a[1]), rootPc: Math.round(a[2]), diss: a[3],
		r: a[4], g: a[5], b: a[6], pcs: pcs
	};
	mgraphics.redraw();
}
function scale() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gScale = [];
	for (var i = 0; i < n; i++) gScale.push(Math.round(a[1 + i]));
	mgraphics.redraw();
}
function voices() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gVoices = [];
	for (var i = 0; i < n; i++) gVoices.push(Math.round(a[1 + i]));
	mgraphics.redraw();
}
function shiftmoves() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gShiftMoves = [];
	for (var i = 0; i < n; i++) {
		var o = 1 + i * 3;
		gShiftMoves.push({ voiceIdx: Math.round(a[o]), degree: Math.round(a[o + 1]), rank: Math.round(a[o + 2]) });
	}
	mgraphics.redraw();
}
function view() {
	var a = arrayfromargs(arguments);
	gView = Math.round(a[0]) === 1 ? 1 : 0;
	mgraphics.redraw();
}
function ringinfo() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gRingDist = [];
	for (var i = 0; i < n; i++) gRingDist.push(a[1 + i]);
	mgraphics.redraw();
}
function nodes() {
	var a = arrayfromargs(arguments), n = Math.round(a[0] || 0);
	gNodes = [];
	var off = 1;
	for (var i = 0; i < n && off < a.length; i++) {
		var ring = Math.round(a[off]), angleDeg = a[off + 1];
		var rr = a[off + 2], gg = a[off + 3], bb = a[off + 4];
		var card = Math.round(a[off + 5]);
		var pcs = [];
		for (var pi = 0; pi < card; pi++) pcs.push(Math.round(a[off + 6 + pi]));
		var rank = Math.round(a[off + 6 + card]);
		gNodes.push({ ring: ring, angleDeg: angleDeg, r: rr, g: gg, b: bb, pcs: pcs, rank: rank });
		off += 6 + card + 1;
	}
	mgraphics.redraw();
}

// --- mouse -------------------------------------------------------------------------------

function pickNode(x, y) {
	var p = plot(), best = -1, bd = GRAB_PX * GRAB_PX;
	for (var i = 0; i < gNodes.length; i++) {
		var xy = nodeXY(gNodes[i], p);
		var d = (x - xy.x) * (x - xy.x) + (y - xy.y) * (y - xy.y);
		if (d < bd) { bd = d; best = i; }
	}
	return best;
}
function pickGhost(x, y) {
	var best = -1, bd = GRAB_PX * GRAB_PX;
	for (var i = 0; i < gGhostHits.length; i++) {
		var gh = gGhostHits[i];
		var d = (x - gh.x) * (x - gh.x) + (y - gh.y) * (y - gh.y);
		if (d < bd) { bd = d; best = i; }
	}
	return best;
}
function onclick(x, y) {
	if (gView === 1) {
		var gi = pickGhost(x, y);
		if (gi >= 0) outlet(0, "selectrank", gGhostHits[gi].rank);
		return;
	}
	var i = pickNode(x, y);
	if (i >= 0) outlet(0, "selectrank", gNodes[i].rank);
}
function onidleout() { hoverRank = -1; mgraphics.redraw(); }

// --- paint ------------------------------------------------------------------------------

function paint() {
	var p = plot();
	mgraphics.set_source_rgba(BG);
	mgraphics.rectangle(0, 0, p.w, p.h);
	mgraphics.fill();

	// Dispatch purely on gView -- the user's explicit choice -- never on whether gVoices/gScale
	// happen to be populated. Falling back to Rings here when the spiral's data was momentarily
	// empty used to make the canvas silently switch views on its own (e.g. right after changing
	// Root/ChordIdx in Steps mode, before the engine's fallback-to-chromatic fix below existed);
	// paintVoiceRings now degrades to a placeholder internally instead, so View always means what
	// it says.
	if (gView === 1) paintVoiceRings(p);
	else paintNeighbors(p);

	// footer readout: centre chord's note names + cardinality + dissonance % + mode/scale-size,
	// so the controls that determine the spiral's winding count (chord size) and point density
	// (scale size) are always legible without hunting through ScaleIdx/MinSize/MaxSize numbers.
	var names = [];
	for (var i = 0; i < gCenter.pcs.length; i++) names.push(NOTE_NAMES[((gCenter.pcs[i] % 12) + 12) % 12]);
	mgraphics.set_source_rgba([0.85, 0.88, 0.92, 0.9]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(PAD, p.h - 5);
	mgraphics.show_text(names.join(' ') + '   (' + gCenter.pcs.length + ' notes)   diss ' + gCenter.diss + '%'
		+ '   [' + (gMode === 1 ? 'Steps' : 'Nearest') + ']'
		+ (gScale.length ? '   chord=' + gCenter.pcs.length + ' scale=' + gScale.length : ''));
}

// Rings view: rings = distance from the centre (voice-leading distance in Nearest mode, hop
// count in Steps mode), angle = hue.
function paintNeighbors(p) {
	// ring guides + distance labels
	mgraphics.set_font_size(9);
	for (var ri = 0; ri < gRingDist.length; ri++) {
		var rr = ringRadius(ri, p);
		mgraphics.set_source_rgba([1, 1, 1, 0.08]);
		mgraphics.set_line_width(1);
		mgraphics.ellipse(p.cx - rr, p.cy - rr, rr * 2, rr * 2);
		mgraphics.stroke();
		mgraphics.set_source_rgba([1, 1, 1, 0.35]);
		mgraphics.move_to(p.cx + 2, p.cy - rr + 10);
		mgraphics.show_text(String(gRingDist[ri]));
	}

	// lines from the centre to every visible node
	for (var i = 0; i < gNodes.length; i++) {
		var xy = nodeXY(gNodes[i], p);
		mgraphics.set_source_rgba([gNodes[i].r, gNodes[i].g, gNodes[i].b, 0.22]);
		mgraphics.set_line_width(1);
		mgraphics.move_to(p.cx, p.cy);
		mgraphics.line_to(xy.x, xy.y);
		mgraphics.stroke();
	}

	// the neighbour nodes
	for (i = 0; i < gNodes.length; i++) {
		var nd = gNodes[i];
		xy = nodeXY(nd, p);
		var rad = (nd.rank === hoverRank) ? 7 : 5;
		mgraphics.set_source_rgba([nd.r, nd.g, nd.b, 0.9]);
		mgraphics.ellipse(xy.x - rad, xy.y - rad, rad * 2, rad * 2);
		mgraphics.fill();
		mgraphics.set_source_rgba([0, 0, 0, 0.5]);
		mgraphics.set_line_width(1);
		mgraphics.ellipse(xy.x - rad, xy.y - rad, rad * 2, rad * 2);
		mgraphics.stroke();
	}

	// centre chord: bigger disc + glow
	var maxR = 12;
	for (var k = 4; k >= 1; k--) {
		var gr = maxR * k / 2;
		mgraphics.set_source_rgba([gCenter.r, gCenter.g, gCenter.b, 0.08]);
		mgraphics.ellipse(p.cx - gr, p.cy - gr, gr * 2, gr * 2);
		mgraphics.fill();
	}
	mgraphics.set_source_rgba([gCenter.r, gCenter.g, gCenter.b, 0.98]);
	mgraphics.ellipse(p.cx - maxR, p.cy - maxR, maxR * 2, maxR * 2);
	mgraphics.fill();
	mgraphics.set_source_rgba([0, 0, 0, 0.6]);
	mgraphics.set_line_width(1.5);
	mgraphics.ellipse(p.cx - maxR, p.cy - maxR, maxR * 2, maxR * 2);
	mgraphics.stroke();
}

// Spiral view: madmusicalscience.com/cs.html-style ("a curve winding n times around an annulus
// ... containing k equally spaced points", n = chord size, k = scale size -- chromatic-12 when
// the engine is in Nearest mode, since it has no scale of its own). ONE continuous spiral, not n
// separate closed rings: radius grows linearly with total angle swept across n full turns, so
// voice i (its own turn, i=0 innermost) sits at absolute angle i*360 + (its scale degree)/k*360.
// Within any single turn the radius only changes by 1/n of the full span, so each turn still
// *reads* as close to a plain ring (matching the reference screenshots) while the whole thing is
// mathematically one winding curve, not n disconnected ones.
function paintVoiceRings(p) {
	var k = gVoices.length, scaleLen = gScale.length;
	if (!k || !scaleLen) {
		// No data yet (e.g. right at load, before the engine's first state arrives) -- a
		// placeholder, not a fallback to Rings: View stays exactly what the user picked.
		mgraphics.set_source_rgba([1, 1, 1, 0.3]);
		mgraphics.set_font_size(10);
		mgraphics.move_to(p.cx - 40, p.cy);
		mgraphics.show_text('(waiting for data)');
		return;
	}
	var innerR = Math.min(p.maxR * 0.15, 18), outerR = p.maxR;
	var maxTheta = k * 2 * Math.PI;

	function spiralR(theta) { return innerR + (outerR - innerR) * (theta / maxTheta); }
	function polar(theta, r) {
		var a = theta - Math.PI / 2;   // 0 at top
		return { x: p.cx + r * Math.cos(a), y: p.cy + r * Math.sin(a) };
	}
	// voice i's absolute position along the spiral: i full turns + its own degree within turn i+1
	function voiceTheta(i) { return i * 2 * Math.PI + (gVoices[i] / scaleLen) * 2 * Math.PI; }

	// faint background spiral, sampled finely enough to look smooth
	mgraphics.set_source_rgba([1, 1, 1, 0.12]);
	mgraphics.set_line_width(1);
	var steps = Math.max(120, k * scaleLen * 3);
	for (var s = 0; s <= steps; s++) {
		var th = maxTheta * s / steps;
		var pt = polar(th, spiralR(th));
		if (s === 0) mgraphics.move_to(pt.x, pt.y); else mgraphics.line_to(pt.x, pt.y);
	}
	mgraphics.stroke();

	// the k equally-spaced points on every turn (background grid)
	mgraphics.set_source_rgba([1, 1, 1, 0.16]);
	for (var w = 0; w < k; w++) {
		for (var j = 0; j < scaleLen; j++) {
			var thJ = w * 2 * Math.PI + (j / scaleLen) * 2 * Math.PI;
			var ptJ = polar(thJ, spiralR(thJ));
			mgraphics.ellipse(ptJ.x - 1.5, ptJ.y - 1.5, 3, 3);
			mgraphics.fill();
		}
	}

	// bright arc threading through the CURRENT chord's actual voice positions, one turn each
	var voiceThetas = [], i;
	for (i = 0; i < k; i++) voiceThetas.push(voiceTheta(i));
	if (k > 1) {
		mgraphics.set_source_rgba([1, 1, 1, 0.55]);
		mgraphics.set_line_width(1.8);
		var segSteps = 24;
		for (i = 0; i < k - 1; i++) {
			for (var ss = 0; ss <= segSteps; ss++) {
				var t = voiceThetas[i] + (voiceThetas[i + 1] - voiceThetas[i]) * ss / segSteps;
				var pp = polar(t, spiralR(t));
				if (ss === 0) mgraphics.move_to(pp.x, pp.y); else mgraphics.line_to(pp.x, pp.y);
			}
		}
		mgraphics.stroke();
	}

	// clickable "shift ghost" markers, one per gShiftMoves entry: every direct single-voice-shift
	// move from the current chord, engine-computed fresh each state (not decimated the way
	// Rings' node list is), so the full reachable set is always shown. This is what makes the
	// spiral view interactive rather than a read-only snapshot: clicking a ghost recentres and
	// plays the resulting chord, same as clicking a node in Rings view.
	gGhostHits = [];
	for (var mi = 0; mi < gShiftMoves.length; mi++) {
		var mv = gShiftMoves[mi];
		var gth = mv.voiceIdx * 2 * Math.PI + (mv.degree / scaleLen) * 2 * Math.PI;
		var gxy = polar(gth, spiralR(gth));
		var ghoverd = (mv.rank === hoverRank) ? 7 : 5;
		mgraphics.set_source_rgba([1, 1, 1, 0.5]);
		mgraphics.ellipse(gxy.x - ghoverd, gxy.y - ghoverd, ghoverd * 2, ghoverd * 2);
		mgraphics.fill();
		mgraphics.set_source_rgba([0, 0, 0, 0.6]);
		mgraphics.set_line_width(1);
		mgraphics.ellipse(gxy.x - ghoverd, gxy.y - ghoverd, ghoverd * 2, ghoverd * 2);
		mgraphics.stroke();
		gGhostHits.push({ x: gxy.x, y: gxy.y, rank: mv.rank });
	}

	// one labeled, coloured dot per voice (rainbow by voice index)
	mgraphics.set_font_size(9);
	for (i = 0; i < k; i++) {
		var xy = polar(voiceThetas[i], spiralR(voiceThetas[i]));
		var c = voiceColor(i, k);
		mgraphics.set_source_rgba([c.r, c.g, c.b, 0.95]);
		mgraphics.ellipse(xy.x - 6, xy.y - 6, 12, 12);
		mgraphics.fill();
		mgraphics.set_source_rgba([0, 0, 0, 0.6]);
		mgraphics.set_line_width(1);
		mgraphics.ellipse(xy.x - 6, xy.y - 6, 12, 12);
		mgraphics.stroke();
		mgraphics.set_source_rgba([1, 1, 1, 0.85]);
		mgraphics.move_to(xy.x + 8, xy.y + 3);
		mgraphics.show_text(NOTE_NAMES[((gScale[gVoices[i]] % 12) + 12) % 12]);
	}

	// pairwise scale-step distance matrix, top-right corner
	var cell = 16, mx = p.w - PAD - k * cell, my = PAD;
	mgraphics.set_font_size(8);
	for (i = 0; i < k; i++) {
		for (var j = 0; j < k; j++) {
			var cx0 = mx + j * cell, cy0 = my + i * cell;
			var same = i === j;
			var dist = circStepDist(gVoices[i], gVoices[j], scaleLen);
			mgraphics.set_source_rgba(same ? [1, 1, 1, 0.05] : [1, 1, 1, 0.1]);
			mgraphics.rectangle(cx0, cy0, cell - 1, cell - 1);
			mgraphics.fill();
			mgraphics.set_source_rgba([0.85, 0.88, 0.92, same ? 0.35 : 0.8]);
			mgraphics.move_to(cx0 + 4, cy0 + 12);
			mgraphics.show_text(String(dist));
		}
	}
}
