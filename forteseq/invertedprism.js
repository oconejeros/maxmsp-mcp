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
		oklabDist: oklabDist, noteName: noteName,
		intervalVector: intervalVector, dissonancePct: dissonancePct
	};
}

var MODELS = ['sub', 'add', 'oklab'];

function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
function clampInt(v, lo, hi) { v = Math.round(Number(v)); if (!isFinite(v)) return lo; return v < lo ? lo : (v > hi ? hi : v); }
function mod12(n) { return ((Math.round(n) % 12) + 12) % 12; }

// A point's vertical position (0..1) is the lightness of ITS colour before blending, so dragging
// a fundamental low darkens its contribution and pulls the resultant register down. Kept away
// from pure black/white so a single low point doesn't crush the blend.
function pointLightness(lum) { return 0.18 + clamp01(lum) * 0.64; }

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
	var baseHue = opts.baseHue == null ? 220 : opts.baseHue;
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
var baseHue = 220, palSat = 0.62;
var splitK = 3;
var lastBlend = { r: 0.5, g: 0.5, b: 0.5 };
var voices = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];   // voices[pc] = held-note count, for the live reharmoniser

var recalcTask = null;

function scheduleRecompute() {
	if (recalcTask) return;
	recalcTask = new Task(function () { recalcTask = null; recompute(); }, this);
	recalcTask.schedule(60);   // coalesce a drag burst into ~16 chords/sec
}

function recompute() {
	var clusters = pointsToClusters(points, MODELS[model], { baseHue: baseHue, sat: palSat });
	if (!clusters.length) {
		outlet(0, "clusters", 0);
		outlet(0, "harm", "-", -1, 0);
		outlet(0, "points", 0);
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
	if (points.length >= MAX_POINTS) return;
	points.push(normalizePoint({ pc: pc == null ? 0 : pc, lum: lum == null ? 0.5 : lum, on: 1, grp: 0 }));
	scheduleRecompute();
}
function rempoint(i) {
	i = Math.round(i);
	if (i >= 0 && i < points.length) { points.splice(i, 1); scheduleRecompute(); }
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
function clear() { points = []; scheduleRecompute(); }
function setmodel(v) { model = clampInt(v, 0, MODELS.length - 1); scheduleRecompute(); }
function setbasehue(v) { v = Number(v); if (isFinite(v)) { baseHue = ((v % 360) + 360) % 360; scheduleRecompute(); } }
function setsat(v) { v = Number(v); if (isFinite(v)) { palSat = clamp01(v); scheduleRecompute(); } }
function setk(v) { splitK = clampInt(v, 2, 6); }
function emit() { recompute(); }
function bang() { recompute(); }

// --- reharmoniser: a held chord -> its colour -> the fundamentals whose blend matches it -------

function emitHeard(pcs) {
	// 4 values, always (r g b alpha) -- the device patch feeds this straight to a `panel`
	// object's "bgcolor" attribute message, which wants exactly 4 numbers.
	if (!pcs.length) { outlet(0, "heardcolor", 0.1, 0.1, 0.12, 1); return; }
	var c = PC.harmonyToColor(pcs, { baseHue: baseHue, sat: palSat }, MODELS[model]);
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
function note(pitch, vel) {
	var pc = mod12(pitch);
	if (vel > 0) voices[pc]++;
	else if (voices[pc] > 0) voices[pc]--;
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
			approxEq(pointLightness(0), 0.18, 'lum 0 -> 0.18 (not black)');
			approxEq(pointLightness(1), 0.82, 'lum 1 -> 0.82 (not white)');
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

		function main() {
			checkFifthsAngle();
			checkPointLightness();
			checkForwardPipeline();
			checkClusters();
			checkSplitRoundTrip();
			if (failures === 0) { console.log('ALL OK'); process.exitCode = 0; }
			else { console.error(failures + ' failure(s)'); process.exitCode = 1; }
		}

		if (process.argv.indexOf('--check') !== -1) main();
		else console.error('usage: node forteseq/invertedprism.js --check');
	})();
}
