// harmonograph_ui.js -- jsui for harmonograph.amxd. Draws the summed-pendulum curve (a portrait
// of the perfectly-balanced rhythmic stack), a dot at every MIDI onset (flashes when it fires),
// a phosphor comet tracing the loop, and a per-layer rotation/weight drag ring.
//
// Fed by harmonograph.js's tagged outlet, split off by `route n ms curve marks hit cyc`:
//   curve  <grid n>  <point count S>  x0 y0 x1 y1 ...     (world coords, centred on the origin)
//   marks  <count>   x0 y0 L0  x1 y1 L1 ...               (one per onset; L = first layer on it)
//   hit    <mark index>                                   (that onset just sounded)
//   cyc    <period ms>                                    (a new loop just started; length in ms)
//   lay    <count>   rot0 wt0 pitch0  rot1 wt1 pitch1 ...  (per active layer: rotation turns,
//                                                          weight, MIDI pitch)
//
// Sends back:  drag <layer> <rotTurns> <weight>   -- the subpatcher routes it to that layer's
//                                                    Rot / Weight numboxes (display + engine both track).
//
// Messages:
//   harmcolor <0|1>   0 (default) fixed per-layer decorative palette | 1 colour each layer's
//                     onset dots + drag handle by that layer's pitch class (pccolor.js's
//                     circle-of-fifths wheel), so the picture reads as harmony, not just index.
//
// Also polls this.patcher.rect ~4x/sec (started from curve(), which always fires at least once on
// load) and keeps its own box.rect filling the window below the fixed controls -- Max gives no
// resize notification for a plain patcher window, so this is how the canvas tracks the user
// dragging the floating window bigger/smaller. See TOP_MARGIN below; must match build_harmonograph.py's JSUI_Y.

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;
include('pccolor.js');   // pitch-class hue wheel, shared with tonnetz/animidi/invertedprism/multichord

outlets = 1;

var TWO_PI = Math.PI * 2;

var BG = [0.075, 0.085, 0.105, 1];
var CURVE_COL = [0.58, 0.84, 0.95, 0.45];
var LAYER_COL = [
	[0.30, 0.78, 0.72],   // teal
	[0.88, 0.56, 0.34],   // amber
	[0.56, 0.56, 0.96],   // periwinkle
	[0.90, 0.46, 0.62],   // rose
	[0.56, 0.82, 0.44],   // green
	[0.82, 0.76, 0.40],   // gold
	[0.44, 0.72, 0.92],   // sky
	[0.76, 0.50, 0.88]    // violet
];
var FLASH_MS = 190;
var COMET_TAIL = 0.10;         // fraction of the loop the comet tail spans
var COMET_COL = [0.72, 0.92, 1.0];
var RING_IN = 0.30, RING_OUT = 0.48;   // drag ring radii, as fractions of the canvas half-min
var GRAB_PX = 16;

// "la visual autoajustable": the floating window is user-resizable by dragging its edge, but Max
// does not reflow child boxes when a plain patcher window resizes -- nothing pushes new bounds to
// this jsui on its own. paint()/layout() already scale their drawing to whatever box.rect says
// (always did, box.rect-driven), so the only missing piece is keeping box.rect itself in step
// with the window. Polled rather than event-driven because Max gives js/jsui no "window resized"
// notification to listen for; this.patcher.rect DOES read the window's live on-screen bounds, so
// a cheap periodic diff is the whole mechanism -- same idiom as the comet/flash 33ms Task above.
var TOP_MARGIN = 292;    // must match build_harmonograph.py's JSUI_Y -- everything above this y is fixed controls
var EDGE_MARGIN = 8;
var MIN_W = 200, MIN_H = 150;
var _lastWinW = -1, _lastWinH = -1;
var resizeWatch = null;

var gPts = [];                 // [[x, y], ...]
var gMarks = [];               // [[x, y, layer], ...]
var gFlash = [];               // parallel to gMarks: ms timestamp of last hit, or 0
var gLay = [];                 // [[rotTurns, weight], ...] per active layer
var gExt = 1;                  // half-extent of a square window centred on the origin
var gCycStart = 0;             // ms timestamp of the last "cyc" message
var gCycDur = 0;               // loop length in ms
var dragLayer = -1;            // layer index being dragged, or -1
var anim = null;
var harmColor = 0;             // 0 fixed LAYER_COL palette | 1 colour by each layer's pitch class

function nowMs() { return (new Date()).getTime(); }

function harmcolor(v) { harmColor = v ? 1 : 0; mgraphics.redraw(); }

// colour for layer i: its pitch class on the circle-of-fifths wheel when HarmColor is on
// (gLay[i][2] is the MIDI pitch, sent by harmonograph.js's `lay` message), else the fixed
// decorative swatch. Falls back to the fixed swatch if pitch data hasn't arrived yet.
function layerColor(i) {
	if (harmColor && gLay[i] && gLay[i][2] !== undefined) {
		var c = pcToColor(((gLay[i][2] % 12) + 12) % 12, { baseHue: 220, sat: 0.62, lum: 0.55 });
		return [c.r, c.g, c.b];
	}
	return LAYER_COL[((i % LAYER_COL.length) + LAYER_COL.length) % LAYER_COL.length];
}

// 0..1 position within the current loop, or -1 when no loop is running / it has gone stale.
function cometPhase() {
	if (gCycDur <= 0) return -1;
	var dt = nowMs() - gCycStart;
	if (dt < 0 || dt > gCycDur * 1.15) return -1;   // stale: transport stopped or Run off
	var ph = dt / gCycDur;
	return ph > 1 ? 1 : ph;
}

// --- inbound messages -----------------------------------------------------------------------

function cyc(ms) {
	ms = Number(ms);
	if (isFinite(ms) && ms > 0) { gCycDur = ms; gCycStart = nowMs(); ensureAnim(); }
}

function curve() {
	ensureResizeWatch();   // curve() fires at least once on load (loadbang re-bangs the layer numboxes)
	var a = arrayfromargs(arguments);
	var count = Math.round(a[1] || 0);
	gPts = [];
	for (var i = 0; i < count && (3 + i * 2) < a.length; i++) {
		gPts.push([a[2 + i * 2], a[3 + i * 2]]);
	}
	computeExtent();
	mgraphics.redraw();
}

function marks() {
	var a = arrayfromargs(arguments);
	var count = Math.round(a[0] || 0);
	gMarks = [];
	gFlash = [];
	for (var i = 0; i < count && (3 + i * 3) < a.length; i++) {
		gMarks.push([a[1 + i * 3], a[2 + i * 3], Math.round(a[3 + i * 3]) || 0]);
		gFlash.push(0);
	}
	mgraphics.redraw();
}

function lay() {
	var a = arrayfromargs(arguments);
	var count = Math.round(a[0] || 0);
	var nl = [];
	for (var i = 0; i < count && (2 + i * 3) < a.length; i++) {
		nl.push([a[1 + i * 3], a[2 + i * 3], Math.round(a[3 + i * 3]) || 0]);
	}
	// don't yank the handle the user is currently dragging (rot/weight only; pitch always updates)
	if (dragLayer >= 0 && dragLayer < nl.length && dragLayer < gLay.length) {
		nl[dragLayer][0] = gLay[dragLayer][0];
		nl[dragLayer][1] = gLay[dragLayer][1];
	}
	gLay = nl;
	mgraphics.redraw();
}

function hit(i) {
	i = Math.round(i);
	if (i >= 0 && i < gFlash.length) {
		gFlash[i] = nowMs();
		ensureAnim();
	}
}

// --- geometry ------------------------------------------------------------------------------

function computeExtent() {
	var e = 0.1;
	for (var i = 0; i < gPts.length; i++) {
		var p = gPts[i];
		if (Math.abs(p[0]) > e) e = Math.abs(p[0]);
		if (Math.abs(p[1]) > e) e = Math.abs(p[1]);
	}
	gExt = e;   // symmetric window: a rotating figure grows/shrinks in place, never jumps
}

function layout() {
	var w = box.rect[2] - box.rect[0];
	var h = box.rect[3] - box.rect[1];
	var half = Math.min(w, h) / 2;
	return { w: w, h: h, ox: w / 2, oy: h / 2, rin: half * RING_IN, rout: half * RING_OUT };
}

function handlePos(L, lo) {
	var th = L[0] * TWO_PI;
	var hr = lo.rin + Math.max(0, Math.min(2, L[1])) / 2 * (lo.rout - lo.rin);
	return [lo.ox + Math.cos(th) * hr, lo.oy - Math.sin(th) * hr];
}

// --- mouse: drag a handle -> rotation (angle) + weight (radius) ---------------------------

function pickHandle(x, y) {
	var lo = layout(), best = -1, bd = GRAB_PX * GRAB_PX;
	for (var i = 0; i < gLay.length; i++) {
		var p = handlePos(gLay[i], lo);
		var d = (x - p[0]) * (x - p[0]) + (y - p[1]) * (y - p[1]);
		if (d < bd) { bd = d; best = i; }
	}
	return best;
}

function applyDrag(x, y) {
	if (dragLayer < 0) return;
	var lo = layout();
	var dx = x - lo.ox, dy = -(y - lo.oy);
	var rot = Math.atan2(dy, dx) / TWO_PI;
	rot -= Math.floor(rot);                                  // wrap to [0, 1)
	var dist = Math.sqrt(dx * dx + dy * dy);
	var wt = (dist - lo.rin) / (lo.rout - lo.rin) * 2;
	if (wt < 0) wt = 0; else if (wt > 2) wt = 2;
	gLay[dragLayer] = [rot, wt];
	outlet(0, "drag", dragLayer, rot, wt);
	mgraphics.redraw();
}

function onclick(x, y) {
	dragLayer = pickHandle(x, y);
	if (dragLayer >= 0) applyDrag(x, y);
}

function ondrag(x, y, but) {
	if (dragLayer < 0) return;
	applyDrag(x, y);
	if (!but) dragLayer = -1;   // final ondrag of a gesture carries button 0
}

// --- animation ---------------------------------------------------------------------------

function ensureAnim() {
	if (anim) return;
	anim = new Task(animTick, this);
	anim.interval = 33;
	anim.repeat();
}

function animTick() {
	var now = nowMs(), live = 0;
	for (var i = 0; i < gFlash.length; i++) {
		if (gFlash[i] && now - gFlash[i] < FLASH_MS) live++;
	}
	if (cometPhase() >= 0) live++;
	mgraphics.redraw();
	if (!live && anim) { anim.cancel(); anim = null; }
}

// Keeps this jsui filling the window below the fixed controls as the user resizes it. Wrapped in
// try/catch and left running unconditionally (unlike animTick, which stops itself when idle):
// cheap at a 4x/s poll, and if this.patcher.rect or box.rect turn out not to behave as expected
// this just never resizes anything, no worse than before Step 8.
function ensureResizeWatch() {
	if (resizeWatch) return;
	resizeWatch = new Task(checkResize, this);
	resizeWatch.interval = 250;
	resizeWatch.repeat();
}

function checkResize() {
	try {
		var r = this.patcher.rect;
		var w = r[2] - r[0], h = r[3] - r[1];
		if (w === _lastWinW && h === _lastWinH) return;
		_lastWinW = w; _lastWinH = h;
		var nw = Math.max(MIN_W, w - EDGE_MARGIN * 2);
		var nh = Math.max(MIN_H, h - TOP_MARGIN - EDGE_MARGIN);
		box.rect = [EDGE_MARGIN, TOP_MARGIN, EDGE_MARGIN + nw, TOP_MARGIN + nh];
		mgraphics.redraw();
	} catch (e) { /* not fatal -- the fixed default layout still works */ }
}

// --- paint -----------------------------------------------------------------------------

function paint() {
	var w = box.rect[2] - box.rect[0];
	var h = box.rect[3] - box.rect[1];

	mgraphics.set_source_rgba(BG);
	mgraphics.rectangle(0, 0, w, h);
	mgraphics.fill();

	if (gPts.length < 2) return;

	var pad = 12;
	var sc = Math.min((w - 2 * pad), (h - 2 * pad)) / (2 * gExt);
	var ox = w / 2, oy = h / 2;
	function X(x) { return ox + sc * x; }
	function Y(y) { return oy - sc * y; }   // flip y so it reads like an oscilloscope

	// the curve, faint
	mgraphics.set_source_rgba(CURVE_COL);
	mgraphics.set_line_width(1);
	mgraphics.move_to(X(gPts[0][0]), Y(gPts[0][1]));
	for (var i = 1; i < gPts.length; i++) mgraphics.line_to(X(gPts[i][0]), Y(gPts[i][1]));
	mgraphics.stroke();

	// phosphor comet: a bright fading segment of arc ending at the current loop phase
	var ph = cometPhase();
	if (ph >= 0) {
		var last = gPts.length - 1;
		var head = Math.round(ph * last);
		var span = Math.max(2, Math.round(COMET_TAIL * last));
		for (var c = 0; c < span; c++) {
			var a = head - c, bpt = head - c - 1;
			if (a < 0) a += last; if (bpt < 0) bpt += last;
			var t = 1 - c / span;                       // 1 at the head, 0 at the tail
			mgraphics.set_source_rgba([COMET_COL[0], COMET_COL[1], COMET_COL[2], t * t]);
			mgraphics.set_line_width(1 + t * 2);
			mgraphics.move_to(X(gPts[a][0]), Y(gPts[a][1]));
			mgraphics.line_to(X(gPts[bpt][0]), Y(gPts[bpt][1]));
			mgraphics.stroke();
		}
		var hx = X(gPts[head][0]), hy = Y(gPts[head][1]);
		mgraphics.set_source_rgba([1, 1, 1, 0.95]);
		mgraphics.ellipse(hx - 3, hy - 3, 6, 6);
		mgraphics.fill();
	}

	// onset dots, brightening + swelling briefly when their note fires
	var now = nowMs();
	for (i = 0; i < gMarks.length; i++) {
		var m = gMarks[i];
		var col = layerColor(m[2]);
		var fl = gFlash[i] ? Math.max(0, 1 - (now - gFlash[i]) / FLASH_MS) : 0;
		var r = 2.2 + fl * 4.5;
		var px = X(m[0]), py = Y(m[1]);
		mgraphics.set_source_rgba([col[0], col[1], col[2], 0.5 + fl * 0.5]);
		mgraphics.ellipse(px - r, py - r, r * 2, r * 2);
		mgraphics.fill();
		if (fl > 0) {
			mgraphics.set_source_rgba([1, 1, 1, fl * 0.75]);
			mgraphics.set_line_width(1);
			mgraphics.ellipse(px - r - 2, py - r - 2, (r + 2) * 2, (r + 2) * 2);
			mgraphics.stroke();
		}
	}

	// drag ring: two faint circles + a handle per active layer (angle = rotation, radius = weight)
	if (gLay.length) {
		var lo = layout();
		mgraphics.set_line_width(1);
		mgraphics.set_source_rgba([0.5, 0.55, 0.62, 0.15]);
		mgraphics.ellipse(lo.ox - lo.rin, lo.oy - lo.rin, lo.rin * 2, lo.rin * 2);
		mgraphics.stroke();
		mgraphics.ellipse(lo.ox - lo.rout, lo.oy - lo.rout, lo.rout * 2, lo.rout * 2);
		mgraphics.stroke();
		for (i = 0; i < gLay.length; i++) {
			var hp = handlePos(gLay[i], lo);
			var lc = layerColor(i);
			mgraphics.set_source_rgba([lc[0], lc[1], lc[2], 0.22]);
			mgraphics.move_to(lo.ox, lo.oy);
			mgraphics.line_to(hp[0], hp[1]);
			mgraphics.stroke();
			var rr = (i === dragLayer) ? 7 : 5;
			mgraphics.set_source_rgba([lc[0], lc[1], lc[2], i === dragLayer ? 1 : 0.85]);
			mgraphics.ellipse(hp[0] - rr, hp[1] - rr, rr * 2, rr * 2);
			mgraphics.fill();
		}
	}
}
