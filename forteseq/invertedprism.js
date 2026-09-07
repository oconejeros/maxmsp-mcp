// invertedprism.js -- engine for invertedprism.amxd (colour -> harmony). You place colour points
// on a canvas -- each is a fundamental pitch class, its vertical position its lightness -- they
// blend under the chosen model, and the resultant colour's hue / saturation / lightness become a
// chord's root / density / register. The inverse (reharmoniser): a held chord -> its colour
// signature -> the fundamentals whose blend matches it.
//
// All the colour maths lives in the shared module pccolor.js: this file `include()`s it in Max
// and `require()`s it in node. Everything above the "Max-facing engine" divider is pure and
// covered by `node invertedprism.js --check`.

var PC;
if (typeof require === 'function' && typeof module !== 'undefined') {
	PC = require('./pccolor.js');
} else {
	if (typeof include === 'function') include('pccolor.js');
	PC = {
		pcToColor: pcToColor, mixColors: mixColors, colorToHarmony: colorToHarmony,
		harmonyToColor: harmonyToColor, splitColor: splitColor, rgbToHsl: rgbToHsl,
		oklabDist: oklabDist, noteName: noteName, octaveToLum: octaveToLum, lerpOklab: lerpOklab,
		intervalVector: intervalVector, dissonancePct: dissonancePct
	};
}

var MODELS = ['sub', 'add', 'oklab'];

function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
function clampInt(v, lo, hi) { v = Math.round(Number(v)); if (!isFinite(v)) return lo; return v < lo ? lo : (v > hi ? hi : v); }
function mod12(n) { return ((Math.round(n) % 12) + 12) % 12; }

// A point's vertical position (0..1) is the lightness of ITS colour before blending, so dragging
// a fundamental low darkens its contribution and pulls the resultant register down. Kept away
// from pure black/white so a single low point doesn't crush the blend -- widened to 0.10..0.90
// (was 0.18..0.82): the old band only reached colorToHarmony's octaves 3-6 of its nominal 2-7
// before visibly washing to near-black/near-white, so the usable register range was narrower
// than it looked. This trades a bit more washing at the very top/bottom for reaching octaves
// 2 and 7 as well.
function pointLightness(lum) { return 0.10 + clamp01(lum) * 0.80; }

// Two points on the same pitch class are the same fundamental, just clicked at slightly
// different heights -- fold them into one contribution (averaging lum) before colouring.
// Left un-folded, two near-identical-hue swatches at different lightness muddy the OKLab
// average just enough to read as lower saturation, walking the chord ladder from a dyad
// down through maj7 / m7 / quartal purely because the same note got clicked twice.
function pointsToColors(points, baseHue, sat) {
	var byPc = {}, order = [], i, pc;
	for (i = 0; i < points.length; i++) {
		if (points[i].on === 0) continue;
		pc = Math.round(points[i].pc);
		if (!byPc.hasOwnProperty(pc)) { byPc[pc] = { sum: 0, n: 0 }; order.push(pc); }
		byPc[pc].sum += points[i].lum;
		byPc[pc].n++;
	}
	var out = [];
	for (i = 0; i < order.length; i++) {
		var agg = byPc[order[i]];
		out.push(PC.pcToColor(order[i], { baseHue: baseHue, sat: sat, lum: pointLightness(agg.sum / agg.n) }));
	}
	return out;
}

// 0..1 position of a pitch class on the circle of fifths (the canvas X axis).
function fifthsAngle(pc) { return (((Math.round(pc) * 7) % 12) + 12) % 12 / 12; }

// The whole forward pipeline as one pure call.
//   points: [{pc, lum, on}]   modelName: 'sub'|'add'|'oklab'   opts: {baseHue, sat}
//   -> { active, blend:{r,g,b}, harm:<colorToHarmony result>, canvasX, canvasY }  (or null if nothing active)
function pointsToChord(points, modelName, opts) {
	opts = opts || {};
	var baseHue = opts.baseHue == null ? 0 : opts.baseHue;
	var sat = opts.sat == null ? 0.62 : opts.sat;
	var cols = pointsToColors(points, baseHue, sat);
	if (!cols.length) return null;
	var blend = PC.mixColors(cols, modelName);
	var harm = PC.colorToHarmony(blend, { baseHue: baseHue });
	if (cols.length === 1) {
		// One fundamental should sound as itself. The saturation->density ladder only means
		// something once colours are actually blending -- with a single point it would otherwise
		// read that point's fixed palette saturation and hand back the open-fifth (root+5th) rung,
		// so every lone point plays a dyad instead of its own note.
		var iv = PC.intervalVector([0]);
		harm = {
			root: harm.root, base: harm.base, octave: harm.octave,
			intervals: [0], notes: [harm.base], name: PC.noteName(harm.root),
			intervalVector: iv, dissonancePct: PC.dissonancePct(iv)
		};
	}
	var hsl = PC.rgbToHsl(blend.r, blend.g, blend.b);
	return {
		active: cols.length, blend: blend, harm: harm,
		canvasX: fifthsAngle(harm.root),   // where the resultant sits on the fifths circle
		canvasY: hsl.l                      // ...and its lightness = register
	};
}

// Polychord mode: points carry a group index (0..MAX_GROUPS-1). Each group blends and reads
// its own chord INDEPENDENTLY of the others -- its own blob on the canvas, its own root -- and
// the groups all sound together, stacked, as one polychord. A single group (the default -- every
// point starts in group 0) degenerates to exactly the old single-blend behaviour.
//   -> [ {grp, active, blend, harm, canvasX, canvasY}, ... ]  one entry per non-empty group, grp ascending
function pointsToClusters(points, modelName, opts) {
	var byGrp = {}, order = [], i, g;
	for (i = 0; i < points.length; i++) {
		if (points[i].on === 0) continue;
		g = points[i].grp || 0;
		if (!byGrp.hasOwnProperty(g)) { byGrp[g] = []; order.push(g); }
		byGrp[g].push(points[i]);
	}
	order.sort(function (a, b) { return a - b; });
	var clusters = [];
	for (i = 0; i < order.length; i++) {
		var res = pointsToChord(byGrp[order[i]], modelName, opts);
		if (res) { res.grp = order[i]; clusters.push(res); }
	}
	return clusters;
}

// Register mode: pure(-ish) helpers for making the reharmoniser's "heard" swatch reflect the
// actual register of the notes currently held, instead of colorToHarmony's fixed default
// lightness. heldPitches: { <midi pitch>: holdCount }. -> null if nothing is held.
function heldAvgOctave(heldPitches) {
	var sum = 0, n = 0;
	for (var p in heldPitches) {
		if (!heldPitches.hasOwnProperty(p)) continue;
		if (heldPitches[p] > 0) { sum += Math.floor(Number(p) / 12); n++; }
	}
	return n > 0 ? sum / n : null;
}

// The lum override to pass into harmonyToColor's opts, or null to fall through to its own
// fixed default -- gated on registerMode being on AND something actually being held.
function registerLum(registerMode, avgOctave) {
	if (!registerMode || avgOctave == null) return null;
	return PC.octaveToLum(avgOctave);
}

// Path mode: sample the OKLab path between two anchor points' colours into `steps` chords
// (endpoints included), reusing exactly the same pointLightness + colorToHarmony a normal
// point already goes through, so an anchor behaves like any other point.
//   pointA/pointB: {pc, lum}   -> [{t, color:{r,g,b}, harm:<colorToHarmony result>}, ...]
function pathToSteps(pointA, pointB, steps, baseHue, sat) {
	var cA = PC.pcToColor(pointA.pc, { baseHue: baseHue, sat: sat, lum: pointLightness(pointA.lum) });
	var cB = PC.pcToColor(pointB.pc, { baseHue: baseHue, sat: sat, lum: pointLightness(pointB.lum) });
	var out = [];
	for (var i = 0; i < steps; i++) {
		var t = steps > 1 ? i / (steps - 1) : 0;
		var col = PC.lerpOklab(cA, cB, t);
		out.push({ t: t, color: col, harm: PC.colorToHarmony(col, { baseHue: baseHue }) });
	}
	return out;
}

// Turns pathToSteps' output into new canvas points, one per step, spread across the polychord
// groups (wrapping at maxGroups) so each step sounds as its own independent voice.
function pathStepsToPoints(steps, maxGroups) {
	var pts = [];
	for (var i = 0; i < steps.length; i++) {
		var hsl = PC.rgbToHsl(steps[i].color.r, steps[i].color.g, steps[i].color.b);
		pts.push({ pc: steps[i].harm.root, lum: hsl.l, on: 1, grp: i % maxGroups });
	}
	return pts;
}

// ================================================================================================
// Max-facing engine: state, message handlers, a debounced recompute. Nothing below runs under
// `--check` (outlet / Task are Max globals).
// ================================================================================================

inlets = 1;
outlets = 1;

var MAX_POINTS = 12;
var MAX_GROUPS = 4;             // polychord groups; group 0 is where every new point starts
var points = [
	{ pc: 0, lum: 0.5, on: 1, grp: 0 },
	{ pc: 4, lum: 0.55, on: 1, grp: 0 },
	{ pc: 7, lum: 0.6, on: 1, grp: 0 }
];
var model = 2;                 // index into MODELS
var baseHue = 0, palSat = 0.62;
var splitK = 3;
var lastBlend = { r: 0.5, g: 0.5, b: 0.5 };
var voices = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];   // voices[pc] = held-note count, for the live reharmoniser
var registerMode = 0;          // 0 = fixed heardcolor lightness (default), 1 = derived from held register
var heldPitches = {};          // <midi pitch>: hold-count -- parallel to voices[], keeps the octave voices[] discards
var pathAnchor = [-1, -1];     // indices into `points` picked as path endpoints, or -1 = unset
var pathSteps = 4;             // chords to sample along the path (2..MAX_GROUPS, so each gets its own voice)
var pathStepIdx = -1;          // which step "Next" last landed on, wrapping; -1 = hasn't started
var pathCursorIdx = -1;        // index into `points` holding that one step's chord, or -1 = none yet

var recalcTask = null;

function scheduleRecompute() {
	if (recalcTask) return;
	recalcTask = new Task(function () { recalcTask = null; recompute(); }, this);
	recalcTask.schedule(60);   // coalesce a drag burst into ~16 chords/sec
}

function recompute() {
	// the jsui draws the column labels and each point's own dot using ITS OWN copy of the hue-wheel
	// formula (pcColor() in invertedprism_ui.js) -- it has no other way to know the live baseHue,
	// so echo it every tick, same as clusters/points/path. Without this the canvas silently kept
	// drawing at baseHue=0 forever regardless of what the Hue control was set to.
	outlet(0, "basehue", baseHue);
	var clusters = pointsToClusters(points, MODELS[model], { baseHue: baseHue, sat: palSat });
	if (!clusters.length) {
		outlet(0, "clusters", 0);
		outlet(0, "harm", "-", -1, 0);
		outlet(0, "points", 0);
		emitPathPreview();
		return;
	}
	lastBlend = clusters[0].blend;
	// one blob per group, all independent: grp r g b canvasX canvasY root diss%
	var cmsg = [0, "clusters", clusters.length], notes = [], names = [], dissSum = 0, ci;
	for (ci = 0; ci < clusters.length; ci++) {
		var c = clusters[ci];
		cmsg.push(c.grp, c.blend.r, c.blend.g, c.blend.b, c.canvasX, c.canvasY, c.harm.root,
			Math.round(c.harm.dissonancePct * 10) / 10);
		notes = notes.concat(c.harm.notes);
		names.push(c.harm.name);
		dissSum += c.harm.dissonancePct;
	}
	outlet.apply(this, cmsg);
	// footer readout: every group's name strung together, and the polychord's average dissonance
	outlet(0, "harm", names.join(' / '), clusters[0].harm.root, Math.round(dissSum / clusters.length * 10) / 10);
	outlet.apply(this, [0, "chord"].concat(notes));
	// echo the point layout for the jsui
	var pmsg = [0, "points", points.length];
	for (var i = 0; i < points.length; i++) pmsg.push(points[i].pc, points[i].lum, points[i].on, points[i].grp || 0);
	outlet.apply(this, pmsg);
	// path preview rides the same debounced tick, so the anchor indices the jsui displays can
	// never drift from pathAnchor itself -- see emitPathPreview()'s own comment.
	emitPathPreview();
}

function normalizePoint(p) {
	p.pc = clampInt(p.pc, 0, 11);
	p.lum = clamp01(Number(p.lum));
	p.on = p.on === 0 ? 0 : 1;
	p.grp = clampInt(p.grp == null ? 0 : p.grp, 0, MAX_GROUPS - 1);
	return p;
}

function setpoint(i, pc, lum) {
	i = Math.round(i);
	if (i < 0 || i >= points.length) return;
	points[i] = normalizePoint({ pc: pc, lum: lum, on: points[i].on, grp: points[i].grp });
	scheduleRecompute();
}
function addpoint(pc, lum) {
	if (points.length >= MAX_POINTS) {
		points.shift();          // rolling buffer: drop the oldest point to keep sculpting instead
		pathAnchor = [-1, -1];   // of silently refusing -- indices shift under this, so drop any
		pathCursorIdx = -1;      // anchor/cursor rather than risk one silently pointing elsewhere
	}
	points.push(normalizePoint({ pc: pc == null ? 0 : pc, lum: lum == null ? 0.5 : lum, on: 1, grp: 0 }));
	scheduleRecompute();
}
function rempoint(i) {
	i = Math.round(i);
	if (i >= 0 && i < points.length) {
		points.splice(i, 1);
		pathAnchor = [-1, -1];   // indices shift under a splice -- safest to just drop any anchor
		pathCursorIdx = -1;      // and any "Next" cursor along with it
		scheduleRecompute();
	}
}
function pointon(i, v) {
	i = Math.round(i);
	if (i >= 0 && i < points.length) { points[i].on = v ? 1 : 0; scheduleRecompute(); }
}
// cycles a point between the polychord groups (dragged in from the jsui on a shift-click)
function setgroup(i, g) {
	i = Math.round(i);
	if (i >= 0 && i < points.length) { points[i].grp = clampInt(g, 0, MAX_GROUPS - 1); scheduleRecompute(); }
}
function clear() { points = []; pathAnchor = [-1, -1]; pathCursorIdx = -1; scheduleRecompute(); }
function setmodel(v) { model = clampInt(v, 0, MODELS.length - 1); scheduleRecompute(); }
function setbasehue(v) { v = Number(v); if (isFinite(v)) { baseHue = ((v % 360) + 360) % 360; scheduleRecompute(); } }
function setsat(v) { v = Number(v); if (isFinite(v)) { palSat = clamp01(v); scheduleRecompute(); } }
function setk(v) { splitK = clampInt(v, 2, 6); }
function emit() { recompute(); }
function bang() { recompute(); }

// --- reharmoniser: a held chord -> its colour -> the fundamentals whose blend matches it -------

function setregmode(v) { registerMode = v ? 1 : 0; }

function emitHeard(pcs) {
	// 4 values, always (r g b alpha) -- the device patch feeds this straight to a `panel`
	// object's "bgcolor" attribute message, which wants exactly 4 numbers.
	if (!pcs.length) { outlet(0, "heardcolor", 0.1, 0.1, 0.12, 1); return; }
	var opts = { baseHue: baseHue, sat: palSat };
	var lum = registerLum(registerMode, heldAvgOctave(heldPitches));
	if (lum != null) opts.lum = lum;
	var c = PC.harmonyToColor(pcs, opts, MODELS[model]);
	lastBlend = c;
	outlet(0, "heardcolor", c.r, c.g, c.b, 1);
}

// Manual "heard <pcs...>" message -- same path a live notein feeds, useful for testing from a message box.
function heard() {
	var a = arrayfromargs(arguments), pcs = [];
	for (var i = 0; i < a.length; i++) { var pc = Math.round(a[i]); if (isFinite(pc)) pcs.push(((pc % 12) + 12) % 12); }
	emitHeard(pcs);
}

// Fed by [notein] -> [pack 0 0] -> [prepend note] in the device patch: tracks held notes (so
// overlapping voices of the same pc, or a stuck-looking note-off, don't desync) and pushes the
// colour of whatever's currently held to the heardcolor swatch as the performance moves.
// heldPitches mirrors voices[] one-for-one but keyed by the absolute pitch, not just its pitch
// class, so the actual octave survives for registerMode (voices[] alone throws it away).
function note(pitch, vel) {
	var pc = mod12(pitch);
	if (vel > 0) {
		voices[pc]++;
		heldPitches[pitch] = (heldPitches[pitch] || 0) + 1;
	} else if (voices[pc] > 0) {
		voices[pc]--;
		if (heldPitches[pitch] > 0) heldPitches[pitch]--;
		if (heldPitches[pitch] <= 0) delete heldPitches[pitch];
	}
	var pcs = [];
	for (var i = 0; i < 12; i++) if (voices[i] > 0) pcs.push(i);
	emitHeard(pcs);
}

// Solve for splitK fundamentals whose blend is closest to the last blend / heard colour, and
// emit them as new canvas points.
function split() {
	var sp = PC.splitColor(lastBlend, splitK, MODELS[model], { baseHue: baseHue, sat: palSat });
	if (!sp) return;
	outlet.apply(this, [0, "split"].concat(sp.pcs));
	points = [];
	for (var i = 0; i < sp.pcs.length; i++) points.push({ pc: sp.pcs[i], lum: 0.5, on: 1, grp: 0 });
	pathAnchor = [-1, -1];
	scheduleRecompute();
}

// --- path mode: pick two existing points as anchors, sample the OKLab path between their
// colours into up to MAX_GROUPS chords, and (on commit) seed them as new points -- one per
// polychord group -- without disturbing the manual shift-click grouping system in any way. ---

// slot 0 or 1; i = point index, or anything out of range clears that slot. Routed through the
// same debounced recompute() as everything else, so emitPathPreview() -- the only thing that
// ever tells the jsui which indices are anchors -- is the single source of truth. (A previous
// version let the jsui track anchor slots entirely on its own, optimistically; the two states
// could permanently drift apart the moment `points` changed shape from under it -- e.g. after a
// pathcommit() or a FIFO addpoint() eviction -- silently breaking the A/B cmd-click cycle. The
// jsui below still updates its display optimistically for snappy feedback, but this echo is what
// actually corrects it moments later.)
function setpathanchor(slot, i) {
	slot = Math.round(slot);
	if (slot !== 0 && slot !== 1) return;
	i = Math.round(i);
	pathAnchor[slot] = (i >= 0 && i < points.length) ? i : -1;
	pathStepIdx = -1;   // a new/changed anchor pair is a new path -- restart "Next" at step 0
	scheduleRecompute();
}
function setpathsteps(n) { pathSteps = clampInt(n, 2, MAX_GROUPS); pathStepIdx = -1; scheduleRecompute(); }

// Read-only feedback for the jsui, called once per recompute() tick -- never on every drag.
// "path <n> <anchorA> <anchorB> [t r g b root]*n": the anchor indices are ALWAYS sent (even -1,
// even with only one set) so the jsui can authoritatively mirror them; n is 0 whenever there
// isn't a complete, in-range pair to sample yet.
function emitPathPreview() {
	var a0 = pathAnchor[0] >= points.length ? -1 : pathAnchor[0];
	var a1 = pathAnchor[1] >= points.length ? -1 : pathAnchor[1];
	if (a0 < 0 || a1 < 0) {
		outlet(0, "path", 0, a0, a1);
		return;
	}
	var steps = pathToSteps(points[a0], points[a1], pathSteps, baseHue, palSat);
	var pmsg = [0, "path", steps.length, a0, a1];
	for (var i = 0; i < steps.length; i++) {
		pmsg.push(steps[i].t, steps[i].color.r, steps[i].color.g, steps[i].color.b, steps[i].harm.root);
	}
	outlet.apply(this, pmsg);
}

// Commits the current path: replaces `points` with one point per sampled step (grp = its index,
// wrapping at MAX_GROUPS so every step is an independent voice). The manual grp/shift-click
// system is untouched afterward -- these become ordinary points like any other.
function pathcommit() {
	if (pathAnchor[0] < 0 || pathAnchor[1] < 0 ||
		pathAnchor[0] >= points.length || pathAnchor[1] >= points.length) return;
	var steps = pathToSteps(points[pathAnchor[0]], points[pathAnchor[1]], pathSteps, baseHue, palSat);
	points = pathStepsToPoints(steps, MAX_GROUPS);
	pathAnchor = [-1, -1];
	pathStepIdx = -1;
	pathCursorIdx = -1;
	scheduleRecompute();
}

// "Next": walks the path ONE step at a time instead of committing all of it as a simultaneous
// polychord -- each press advances pathStepIdx (wrapping) and replaces just ONE point (a
// dedicated "cursor", tracked by pathCursorIdx) with that step's chord, so the currently-sounding
// single chord morphs along the A->B path on repeat presses. The two anchor points themselves are
// left alone (unlike pathcommit(), which consumes them) -- keep pressing Next to keep walking the
// same path; re-anchor (cmd-click new points) to trace a different one.
function pathnext() {
	if (pathAnchor[0] < 0 || pathAnchor[1] < 0 ||
		pathAnchor[0] >= points.length || pathAnchor[1] >= points.length) return;
	if (pathCursorIdx === pathAnchor[0] || pathCursorIdx === pathAnchor[1]) pathCursorIdx = -1;
	var steps = pathToSteps(points[pathAnchor[0]], points[pathAnchor[1]], pathSteps, baseHue, palSat);
	if (!steps.length) return;
	pathStepIdx = (pathStepIdx + 1) % steps.length;
	var hsl = PC.rgbToHsl(steps[pathStepIdx].color.r, steps[pathStepIdx].color.g, steps[pathStepIdx].color.b);
	var cursorPt = normalizePoint({ pc: steps[pathStepIdx].harm.root, lum: hsl.l, on: 1, grp: 0 });
	if (pathCursorIdx >= 0 && pathCursorIdx < points.length) {
		points[pathCursorIdx] = cursorPt;
	} else if (points.length < MAX_POINTS) {
		points.push(cursorPt);
		pathCursorIdx = points.length - 1;
	}   // else: canvas already full -- Next is a no-op until a slot frees up (never evicts an anchor)
	scheduleRecompute();
}

// ================================================================================================
// node --check harness
// ================================================================================================

if (typeof require !== 'undefined' && typeof process !== 'undefined') {
	(function () {
		var failures = 0;
		function eq(got, want, label) {
			if (got !== want) { console.error('FAIL ' + label + ': got ' + got + ', want ' + want); failures++; }
		}
		function approxEq(got, want, label, eps) {
			eps = eps === undefined ? 1e-9 : eps;
			if (!(Math.abs(got - want) <= eps)) {
				console.error('FAIL ' + label + ': got ' + got + ', want ' + want); failures++;
			}
		}

		function checkFifthsAngle() {
			var f0 = failures;
			approxEq(fifthsAngle(0), 0, 'C at angle 0');
			approxEq(fifthsAngle(7), 1 / 12, 'G one step round the fifths circle');
			approxEq(fifthsAngle(1), 7 / 12, 'C# is seven fifths from C');
			if (failures === f0) console.log('OK   checkFifthsAngle: pitch class -> circle-of-fifths position.');
		}

		function checkPointLightness() {
			var f0 = failures;
			approxEq(pointLightness(0), 0.10, 'lum 0 -> 0.10 (not black)');
			approxEq(pointLightness(1), 0.90, 'lum 1 -> 0.90 (not white)');
			approxEq(pointLightness(0.5), 0.5, 'lum 0.5 -> 0.5');
			if (failures === f0) console.log('OK   checkPointLightness: vertical position maps into a safe lightness band.');
		}

		function checkForwardPipeline() {
			var f0 = failures;
			var opts = { baseHue: 220, sat: 0.62 };
			// a single C point -> root should be C (0)
			var one = pointsToChord([{ pc: 0, lum: 0.5, on: 1 }], 'oklab', opts);
			eq(one.harm.root, 0, 'single C point -> root C');
			eq(one.active, 1, 'one active point');
			eq(one.harm.notes.length, 1, 'a single point plays one note, not a dyad');
			eq(one.harm.notes[0], one.harm.base, 'that note is the root itself');
			eq(one.harm.dissonancePct, 0, 'a single note is 0% dissonant');
			// nothing on -> null
			eq(pointsToChord([{ pc: 0, lum: 0.5, on: 0 }], 'oklab', opts), null, 'no active points -> null');
			// a low point sits lower than a high point (same pc)
			var lo = pointsToChord([{ pc: 0, lum: 0.05, on: 1 }], 'oklab', opts);
			var hi = pointsToChord([{ pc: 0, lum: 0.95, on: 1 }], 'oklab', opts);
			if (!(hi.harm.base > lo.harm.base)) { console.error('FAIL high point should give a higher chord'); failures++; }
			// canvasX is the fifths angle of the resulting root
			approxEq(one.canvasX, fifthsAngle(one.harm.root), 'canvasX == fifths angle of root');
			// model actually changes the blend: sub vs add of two complementary-ish pcs differ
			var sub = pointsToChord([{ pc: 0, lum: 0.5, on: 1 }, { pc: 6, lum: 0.5, on: 1 }], 'sub', opts);
			var add = pointsToChord([{ pc: 0, lum: 0.5, on: 1 }, { pc: 6, lum: 0.5, on: 1 }], 'add', opts);
			if (PC.oklabDist(sub.blend, add.blend) < 0.05) { console.error('FAIL sub and add should differ'); failures++; }
			// the same pitch class clicked twice (at different heights) folds into ONE contribution,
			// so it still reads as a single note, not a denser chord than clicking it once.
			var twice = pointsToChord([{ pc: 0, lum: 0.4, on: 1 }, { pc: 0, lum: 0.6, on: 1 }], 'oklab', opts);
			eq(twice.active, 1, 'duplicate pitch class folds to one active colour');
			eq(twice.harm.notes.length, 1, 'duplicate pitch class still plays a single note');
			if (failures === f0) console.log('OK   checkForwardPipeline: points -> blend -> chord; lightness->register, model matters.');
		}

		function checkClusters() {
			var f0 = failures;
			var opts = { baseHue: 220, sat: 0.62 };
			// two points in the SAME group -> one blended cluster (the old single-blend behaviour)
			var same = pointsToClusters(
				[{ pc: 0, lum: 0.5, on: 1, grp: 0 }, { pc: 7, lum: 0.5, on: 1, grp: 0 }], 'oklab', opts);
			eq(same.length, 1, 'same-group points -> one cluster');
			// two points in DIFFERENT groups -> two independent clusters, each its own single-note chord
			var poly = pointsToClusters(
				[{ pc: 0, lum: 0.5, on: 1, grp: 0 }, { pc: 6, lum: 0.5, on: 1, grp: 1 }], 'oklab', opts);
			eq(poly.length, 2, 'different-group points -> two clusters');
			eq(poly[0].grp, 0, 'clusters come back sorted by group, ascending');
			eq(poly[1].grp, 1, 'second cluster is group 1');
			eq(poly[0].harm.root, 0, 'group 0 blends only its own point -> root C');
			eq(poly[1].harm.root, 6, 'group 1 blends only its own point -> root F#, unaffected by group 0');
			// a group with nothing on contributes no cluster at all
			var sparse = pointsToClusters(
				[{ pc: 0, lum: 0.5, on: 1, grp: 0 }, { pc: 6, lum: 0.5, on: 0, grp: 1 }], 'oklab', opts);
			eq(sparse.length, 1, 'a muted group drops out of the polychord entirely');
			if (failures === f0) console.log('OK   checkClusters: groups blend independently into a polychord.');
		}

		function checkSplitRoundTrip() {
			var f0 = failures;
			var opts = { baseHue: 220, sat: 0.62 };
			var target = pointsToChord([{ pc: 0, lum: 0.5, on: 1 }, { pc: 4, lum: 0.5, on: 1 }, { pc: 7, lum: 0.5, on: 1 }], 'oklab', opts);
			var sp = PC.splitColor(target.blend, 3, 'oklab', opts);
			eq(sp.pcs.length, 3, 'split returns 3 pcs');
			// approximate: splitColor searches with pcToColor's default lightness, not the points' own
			if (!(sp.dist < 0.06)) { console.error('FAIL split dist too large: ' + sp.dist); failures++; }
			if (failures === f0) console.log('OK   checkSplitRoundTrip: splitColor recovers a matching fundamental set.');
		}

		function checkHeldAvgOctave() {
			var f0 = failures;
			eq(heldAvgOctave({}), null, 'no held pitches -> null');
			eq(heldAvgOctave({ 60: 1 }), 5, 'middle C (60) -> octave 5');
			eq(heldAvgOctave({ 60: 1, 72: 1 }), 5.5, 'octave 5 + octave 6 -> average 5.5');
			eq(heldAvgOctave({ 60: 0, 72: 1 }), 6, 'a released (0-count) pitch does not count');
			if (failures === f0) console.log('OK   checkHeldAvgOctave: averages the octave of currently-held pitches.');
		}

		function checkRegisterLum() {
			var f0 = failures;
			eq(registerLum(0, 5), null, 'register mode off -> no lum override');
			eq(registerLum(1, null), null, 'register mode on but nothing held -> no lum override');
			approxEq(registerLum(1, 2), PC.octaveToLum(2), 'register mode on -> octaveToLum of the held average', 1e-9);
			if (failures === f0) console.log('OK   checkRegisterLum: gates the lum override on registerMode + a held note.');
		}

		function checkPathToSteps() {
			var f0 = failures;
			var a = { pc: 0, lum: 0.5 }, b = { pc: 6, lum: 0.5 };
			var steps = pathToSteps(a, b, 4, 0, 0.62);
			eq(steps.length, 4, 'pathToSteps returns the requested step count');
			var cA = PC.pcToColor(0, { baseHue: 0, sat: 0.62, lum: pointLightness(0.5) });
			var cB = PC.pcToColor(6, { baseHue: 0, sat: 0.62, lum: pointLightness(0.5) });
			approxEq(steps[0].color.r, cA.r, 'first step == anchor A', 1e-4);
			approxEq(steps[0].color.g, cA.g, 'first step == anchor A (g)', 1e-4);
			approxEq(steps[3].color.r, cB.r, 'last step == anchor B', 1e-4);
			approxEq(steps[3].color.g, cB.g, 'last step == anchor B (g)', 1e-4);
			var pts = pathStepsToPoints(steps, 4);
			eq(pts.length, 4, 'pathStepsToPoints returns one point per step');
			eq(pts[0].grp, 0, 'first point in group 0');
			eq(pts[3].grp, 3, 'fourth point in group 3');
			eq(pathToSteps(a, b, 2, 0, 0.62).length, 2, 'step count is respected (2 anchors only)');
			if (failures === f0) console.log('OK   checkPathToSteps: samples an OKLab path between two anchors into distinct chords.');
		}

		function main() {
			checkFifthsAngle();
			checkPointLightness();
			checkForwardPipeline();
			checkClusters();
			checkSplitRoundTrip();
			checkHeldAvgOctave();
			checkRegisterLum();
			checkPathToSteps();
			if (failures === 0) { console.log('ALL OK'); process.exitCode = 0; }
			else { console.error(failures + ' failure(s)'); process.exitCode = 1; }
		}

		if (process.argv.indexOf('--check') !== -1) main();
		else console.error('usage: node forteseq/invertedprism.js --check');
	})();
}
