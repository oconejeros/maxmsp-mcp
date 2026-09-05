// forteseq/harmonograph.js -- standalone Perfectly-Balanced (PB) rhythm generator, drawn as a
// harmonograph / Lissajous curve. This file is the pure-math half only, plus a `node --check`
// harness; the Max-facing engine (inlets/outlets/Task, message handlers, real-time scheduling)
// is appended in the .amxd phase, exactly the split forteseqwf.js draws between its pure half
// and its engine half.
//
// Companion to forteseqwf.js (Well-Formed rhythms). PB and WF are the two generative modes of
// Milne et al.'s XronoMorph, grounded in the same "DFT of the onset set" framework but with no
// merged algorithm -- they run as independent parallel generators. This file is PB only.
//
// Sources: Milne, Herff, Bulger, Sethares & Dean, "XronoMorph: Algorithmic Generation of
// Perfectly Balanced and Well-Formed Rhythms" (NIME 2016); Milne, Bulger, Herff & Sethares,
// "Perfect Balance: A Novel Organizational Principle for Musical Scales and Meters" (MCM 2015);
// Amiot & Noll, for the result that a rhythm is perfectly balanced iff the first Fourier
// coefficient of its onset set vanishes -- equivalently, the centre of gravity of the onsets,
// mapped onto the unit circle, sits at the circle's centre.
//
// The one fact the whole device leans on: a regular K-gon (K >= 2) is perfectly balanced at ANY
// rotation, and the union of perfectly balanced rhythms is perfectly balanced. So a stack of
// independently-rotated regular polygons over their common (LCM) grid is PB for free -- no
// scoring, no search. checkPolygonBalance / checkStackBalance / checkRotationInvariance verify
// all three claims against the centroid directly.
//
// Grid vs time: with integer (grid-snapped) rotation every onset is an integer step on the LCM
// grid and the eventual engine reads it as a step array (cheap -- see forteseq-hot-path).
// Continuous rotation slides the onsets off the grid; still perfectly balanced (a rotated
// balanced set stays balanced), but then scheduled by time, like the WF device.
//
// The harmonograph curve is a portrait of that same stack: layer K -> pendulum frequency K,
// rotation -> phase, weight -> amplitude, an optional decay -> damping (the pen spiralling in).
// It is decoration plus a manipulation surface only -- it never carries the MIDI.

var TWO_PI = Math.PI * 2;

var MAX_K = 30;        // XronoMorph's largest prime polygon is 29
var MAX_GRID = 5040;   // 7! -- the LCM of any small polygon set stays under this; engine refuses past it
var MAX_SAMPLES = 4096;
var MAX_LAYERS = 8;

// --- integer helpers --------------------------------------------------------------------------

function clampInt(v, lo, hi) { v = Math.round(v); if (!isFinite(v)) return lo; return v < lo ? lo : (v > hi ? hi : v); }
function clampNum(v, lo, hi) { if (!isFinite(v)) return lo; return v < lo ? lo : (v > hi ? hi : v); }

function gcd(a, b) {
	a = Math.abs(Math.round(a)); b = Math.abs(Math.round(b));
	while (b) { var t = b; b = a % b; a = t; }
	return a || 1;
}
function lcm(a, b) {
	a = Math.round(a); b = Math.round(b);
	if (!a || !b) return 0;
	return Math.abs(a * b) / gcd(a, b);
}
function lcmAll(list) {
	var r = 1;
	for (var i = 0; i < list.length; i++) r = lcm(r, list[i]);
	return r;
}
function gridTooBig(n) { return n > MAX_GRID; }

// --- perfectly-balanced polygon onsets ------------------------------------------------------

// K points spread over an n-step circle, rotated by `rot` (in grid steps; may be fractional for
// smooth/continuous rotation). When n is an exact multiple of K the points are at i*(n/K)+rot --
// exactly evenly spaced, so the K-gon is perfectly balanced at ANY rot (a rotated balanced set
// stays balanced). When n is NOT a multiple of K this falls back to round(i*n/K)+rot, which is
// only approximately even -- render() never hits that branch (it always passes the LCM grid), it
// exists so the function is safe to call standalone. Returns positions in [0, n), sorted.
function polygonOnsets(K, n, rot) {
	K = Math.round(K);
	var out = [];
	if (K < 1 || n <= 0) return out;
	rot = rot || 0;
	var exact = (n % K === 0);
	var span = n / K;
	for (var i = 0; i < K; i++) {
		var p = exact ? (i * span + rot) : (Math.round(i * n / K) + rot);
		p = ((p % n) + n) % n;
		out.push(p);
	}
	out.sort(function (a, b) { return a - b; });
	return out;
}

// Centroid magnitude of an onset set: |(1/N) * sum exp(2*pi*i * p/n)|. This is fhat(1)/N, the
// first Fourier coefficient normalised by the onset count. Perfect balance <=> this is 0.
function centroidMag(positions, n) {
	var N = positions.length;
	if (N === 0 || n <= 0) return 0;
	var re = 0, im = 0;
	for (var i = 0; i < N; i++) {
		var a = TWO_PI * positions[i] / n;
		re += Math.cos(a); im += Math.sin(a);
	}
	re /= N; im /= N;
	return Math.sqrt(re * re + im * im);
}

// XronoMorph's own convention: balance = 1 - |centre of gravity|. 1 = perfectly balanced.
function balanceScore(positions, n) { return 1 - centroidMag(positions, n); }

// Centroid magnitude of a STACK, weighting each merged onset by how many polygons landed on it.
// "The union of PB rhythms is PB" is a statement about the integer-weighted onset function
// (MCM 2015's integer combinations) -- a step hit by k polygons carries weight k. Measure the
// deduplicated set without those weights and coincident onsets skew the centroid. This is the
// number render() reports and the self-tests assert against; centroidMag() above stays the
// unweighted primitive for a single collision-free polygon.
function stackCentroidMag(onsets, n) {
	var wsum = 0, re = 0, im = 0;
	for (var i = 0; i < onsets.length; i++) {
		var w = onsets[i].count || (onsets[i].layers ? onsets[i].layers.length : 1);
		var a = TWO_PI * onsets[i].pos / n;
		re += w * Math.cos(a); im += w * Math.sin(a);
		wsum += w;
	}
	if (wsum === 0) return 0;
	re /= wsum; im /= wsum;
	return Math.sqrt(re * re + im * im);
}

// Union of a stack of independently-rotated regular polygons over their common (LCM) grid.
// layers: [{ K, rot, weight }]. Balance is automatic -- every polygon is individually PB, and
// the union of PB sets is PB. Near-duplicate onsets (two polygons landing on the same step) are
// merged, keeping the larger weight and listing every contributing layer.
//   -> { n, onsets: [{ pos, weight, K, layers:[idx...] }] (sorted by pos), layers }
function pbStack(layers) {
	layers = layers || [];
	var Ks = [], i;
	for (i = 0; i < layers.length; i++) {
		if (Math.round(layers[i].K) >= 2) Ks.push(clampInt(layers[i].K, 2, MAX_K));
	}
	var n = Ks.length ? lcmAll(Ks) : 1;

	var raw = [];
	for (i = 0; i < layers.length; i++) {
		if (Math.round(layers[i].K) < 2) continue;
		var K = clampInt(layers[i].K, 2, MAX_K);
		var w = (layers[i].weight == null || !isFinite(layers[i].weight)) ? 1 : layers[i].weight;
		var pts = polygonOnsets(K, n, layers[i].rot || 0);
		for (var j = 0; j < pts.length; j++) raw.push({ pos: pts[j], weight: w, K: K, layer: i });
	}
	raw.sort(function (a, b) { return a.pos - b.pos; });

	var eps = n * 1e-9;
	var onsets = [];
	for (i = 0; i < raw.length; i++) {
		var last = onsets[onsets.length - 1];
		if (last && Math.abs(raw[i].pos - last.pos) <= eps) {
			if (raw[i].weight > last.weight) last.weight = raw[i].weight;
			last.layers.push(raw[i].layer);
			last.count++;
		} else {
			onsets.push({ pos: raw[i].pos, weight: raw[i].weight, K: raw[i].K, layers: [raw[i].layer], count: 1 });
		}
	}
	return { n: n, onsets: onsets, layers: layers };
}

// --- harmonograph curve --------------------------------------------------------------------

// One rhythm layer -> one pendulum. freq = K (K full oscillations per loop), phase from the
// polygon rotation (a full n-step rotation is one turn), amplitude from the layer weight,
// damping from an optional decay: `damp` is the number of e-foldings over the whole curve, so
// decay 0 = no damping and decay 3 = amplitude down to ~5% by the end.
function layerToPendulum(layer, n, axis) {
	return {
		freq: clampInt(layer.K, 2, MAX_K),
		amp: (layer.weight == null || !isFinite(layer.weight)) ? 1 : layer.weight,
		phase: TWO_PI * ((layer.rot || 0) / (n || 1)),
		damp: (layer.decay == null || !isFinite(layer.decay)) ? 0 : Math.max(0, layer.decay),
		axis: axis || 'x'
	};
}

// Sample the summed pendulum motion over `loops` loops. Each pendulum contributes to x, to y, to
// both, or -- 'rot', a rotary pendulum -- a circular term (cos to x, sin to y). Returns
// samples+1 points, so an undamped integer-frequency curve closes exactly (last point == first).
//   pendulums: [{ freq, amp, phase, damp, axis }]   axis in 'x' | 'y' | 'xy' | 'rot'
function harmonoCurve(pendulums, samples, opts) {
	opts = opts || {};
	var loops = opts.loops || 1;
	var N = clampInt(samples || 1200, 16, MAX_SAMPLES);
	var pts = [];
	for (var s = 0; s <= N; s++) {
		var t = (s / N) * loops;                      // 0 .. loops
		var frac = loops > 0 ? (t / loops) : 0;       // 0 .. 1, drives the damping envelope
		var x = 0, y = 0;
		for (var p = 0; p < pendulums.length; p++) {
			var pd = pendulums[p];
			var env = pd.amp * Math.exp(-(pd.damp || 0) * frac);
			var ang = TWO_PI * pd.freq * t + pd.phase;
			var sn = Math.sin(ang), cs = Math.cos(ang);
			if (pd.axis === 'y') { y += env * sn; }
			else if (pd.axis === 'xy') { x += env * sn; y += env * sn; }
			else if (pd.axis === 'rot') { x += env * cs; y += env * sn; }
			else { x += env * sn; }
		}
		pts.push({ x: x, y: y });
	}
	return pts;
}

function curveBounds(curve) {
	var mnx = Infinity, mxx = -Infinity, mny = Infinity, mxy = -Infinity;
	for (var i = 0; i < curve.length; i++) {
		var c = curve[i];
		if (c.x < mnx) mnx = c.x; if (c.x > mxx) mxx = c.x;
		if (c.y < mny) mny = c.y; if (c.y > mxy) mxy = c.y;
	}
	return { minx: mnx, maxx: mxx, miny: mny, maxy: mxy, w: mxx - mnx, h: mxy - mny };
}

// Where each MIDI onset lands on the curve: onset at grid position `pos` maps to loop fraction
// pos/n, indexed into the curve. Assumes a single-loop curve (opts.loops === 1 in render()).
function onsetMarks(onsets, n, curve) {
	var out = [];
	if (!curve || curve.length < 2 || n <= 0) return out;
	var last = curve.length - 1;
	for (var i = 0; i < onsets.length; i++) {
		var idx = Math.round((onsets[i].pos / n) * last);
		if (idx < 0) idx = 0; else if (idx > last) idx = last;
		out.push({ x: curve[idx].x, y: curve[idx].y, pos: onsets[i].pos, weight: onsets[i].weight });
	}
	return out;
}

// --- one-call render: everything the engine and the jsui need from a set of layers -----------

var AXIS_CYCLE = ['x', 'y', 'rot'];

// layers: [{ K, rot, weight, axis? }].  opts: { samples, loops }.
//   -> { n, onsets, pendulums, curve, marks, centroid, balance }
function render(layers, opts) {
	opts = opts || {};
	layers = (layers || []).slice(0, MAX_LAYERS);
	var stack = pbStack(layers);

	var pend = [];
	for (var i = 0; i < layers.length; i++) {
		if (Math.round(layers[i].K) < 2) continue;
		var axis = layers[i].axis || AXIS_CYCLE[pend.length % AXIS_CYCLE.length];
		pend.push(layerToPendulum(layers[i], stack.n, axis));
	}

	var samples = clampInt(opts.samples || 1200, 16, MAX_SAMPLES);
	var curve = harmonoCurve(pend, samples, { loops: opts.loops || 1 });

	var cmag = stackCentroidMag(stack.onsets, stack.n);

	return {
		n: stack.n,
		onsets: stack.onsets,
		pendulums: pend,
		curve: curve,
		marks: onsetMarks(stack.onsets, stack.n, curve),
		centroid: cmag,
		balance: 1 - cmag
	};
}

// ================================================================================================
// Max-facing engine: state, message handlers, tempo-sync clock, and one Task per onset re-armed
// every cycle -- the same idiom forteseqwf.js uses. Everything ABOVE this line is pure and
// Node-testable; the functions below reference Max globals (Task / outlet / post / inlets /
// outlets) that are undefined under node, but --check never calls them.
// ================================================================================================

inlets = 1;
// outlet 0: the original tagged stream (n/ms/curve/marks/hit/cyc/lay), unchanged since Step 3.
// outlet 1 (Step 8 hardening): a SEPARATE, dedicated channel for the preset-menu UI protocol
// (clear/append/set). It started as a "presetmenu"-tagged message sharing outlet 0, round-tripped
// through route/prepend/route to reach the umenu without also hitting the jsui -- and that round
// trip was empirically observed, live, to occasionally mangle the tag into a stray small integer
// (verified with a print object sniffing the raw signal: a freshly-built identical prepend object
// never reproduced it, only the one wired into the real chain did, repeatedly, even after being
// individually recreated in place -- so the fix here is structural, not a guess at the Max-
// internal cause). A dedicated outlet needs no tag, no route, no prepend: nothing left in the
// path that could mangle it.
// outlet 2 (bugfix, same day): pushes the current slot's stored name into the name textedit
// via `set <name>` (silent) whenever the current slot changes -- see syncNameBox().
outlets = 3;

var MIN_PERIOD_MS = 50;
var MAX_PERIOD_MS = 60000;
var MAX_ONSETS_PER_CYCLE = 400;   // circuit breaker, per forteseq-hot-path's runaway lesson

var running = 0;
var periodMs = 2000;
var syncTempo = 0, beatsPerPeriod = 4, liveTempo = 120, transportPlaying = 0;

var AXIS_NAMES = ['x', 'y', 'xy', 'rot'];      // matches the L# Axis menu order

var numLayers = 2;
var layerK      = [3, 4, 5, 3, 4, 5, 3, 4];
var layerRot    = [0, 0, 0, 0, 0, 0, 0, 0];   // turns (0..1); the engine scales by the LCM grid
var layerWeight = [1, 1, 1, 1, 1, 1, 1, 1];
var layerPitch  = [48, 52, 55, 59, 62, 64, 67, 71];
var layerAxis   = [0, 1, 2, 0, 1, 2, 0, 1];    // index into AXIS_NAMES
var baseVel = 100, baseDur = 120;
var accentPerCoincidence = 12;                 // +vel for each extra polygon landing on one step
var globalDecay = 0;                            // pendulum damping (e-foldings over the loop); drawing only
var CURVE_SAMPLES = 480;                        // jsui polyline resolution (see emitCurve)

// Step 6: per-layer + global probability, and a pair of shared MiniSteps-style quantized
// modulators (one lane for Rot, one for Weight) with a per-layer depth knob into each. The lane
// is shared across all 8 layers -- depth 0 is a no-op -- to keep the param count buildable (see
// forteseq-harmonograph-device memory: per-layer lanes would have meant 128+ new params).
var layerProb = [100, 100, 100, 100, 100, 100, 100, 100];   // per-layer onset survival chance, %
var globalProb = 100;                                        // extra gate on top, %
var layerRotDepth    = [0, 0, 0, 0, 0, 0, 0, 0];             // 0..100 (%) of ROT_MOD_RANGE_TURNS
var layerWeightDepth = [0, 0, 0, 0, 0, 0, 0, 0];             // 0..100 (%) of full weight swing

var MOD_LANE_SIZE = 8;                          // fixed step-array size (Live params are fixed slots)
var MOD_LEVELS = 8;                             // quantized step values are 0..MOD_LEVELS-1
var ROT_MOD_RANGE_TURNS = 0.5;                  // +-1 modUnit * 100% depth = +-0.5 turn
var rotStepVal    = [4, 4, 4, 4, 4, 4, 4, 4];
var weightStepVal = [4, 4, 4, 4, 4, 4, 4, 4];
var rotSteps = 8, weightSteps = 8;              // how many of the 8 slots are actually used (2..8)
var rotModPos = 0, weightModPos = 0;            // advances by one every cycle (startCycle)

var scheduledTasks = [];

function clampMs(v) { v = Math.round(Number(v)); if (!isFinite(v)) return periodMs; return v < MIN_PERIOD_MS ? MIN_PERIOD_MS : (v > MAX_PERIOD_MS ? MAX_PERIOD_MS : v); }
function clampCount(v, lo, hi) { v = Math.round(Number(v)); if (!isFinite(v)) return lo; return v < lo ? lo : (v > hi ? hi : v); }
function layerIdx(i) { i = Math.round(i); return (i >= 0 && i < MAX_LAYERS) ? i : -1; }

function stopAllTasks() {
	for (var i = 0; i < scheduledTasks.length; i++) scheduledTasks[i].cancel();
	scheduledTasks = [];
}

function setrun(v) { running = v ? 1 : 0; if (!running) stopAllTasks(); }
function setperiod(v) { periodMs = clampMs(v); }
function setnumlayers(v) { numLayers = clampCount(v, 1, MAX_LAYERS); emitCurve(); }
function setlayerk(i, v) { i = layerIdx(i); if (i < 0) return; layerK[i] = clampCount(v, 2, MAX_K); emitCurve(); }
function setlayerrot(i, v) { i = layerIdx(i); if (i < 0) return; v = Number(v); layerRot[i] = isFinite(v) ? v : 0; emitCurve(); }
function setlayerweight(i, v) { i = layerIdx(i); if (i < 0) return; v = Number(v); layerWeight[i] = (isFinite(v) && v >= 0) ? v : 1; emitCurve(); }
function setlayerpitch(i, v) { i = layerIdx(i); if (i < 0) return; layerPitch[i] = clampCount(v, 0, 127); }
function setlayeraxis(i, v) { i = layerIdx(i); if (i < 0) return; layerAxis[i] = clampCount(v, 0, AXIS_NAMES.length - 1); emitCurve(); }
function setvel(v) { baseVel = clampCount(v, 1, 127); }
function setdur(v) { baseDur = clampCount(v, 1, 60000); }
function setdecay(v) { v = Number(v); globalDecay = (isFinite(v) && v >= 0) ? v : 0; emitCurve(); }

function setlayerprob(i, v) { i = layerIdx(i); if (i < 0) return; layerProb[i] = clampNum(Number(v), 0, 100); }
function setglobalprob(v) { globalProb = clampNum(Number(v), 0, 100); }
function setlayerrotdepth(i, v) { i = layerIdx(i); if (i < 0) return; layerRotDepth[i] = clampNum(Number(v), 0, 100); }
function setlayerweightdepth(i, v) { i = layerIdx(i); if (i < 0) return; layerWeightDepth[i] = clampNum(Number(v), 0, 100); }

function modLaneIdx(i) { i = Math.round(i); return (i >= 0 && i < MOD_LANE_SIZE) ? i : -1; }
function setrotstep(i, v) { i = modLaneIdx(i); if (i < 0) return; rotStepVal[i] = clampCount(v, 0, MOD_LEVELS - 1); emitCurve(); }
function setweightstep(i, v) { i = modLaneIdx(i); if (i < 0) return; weightStepVal[i] = clampCount(v, 0, MOD_LEVELS - 1); emitCurve(); }
function setrotsteps(v) { rotSteps = clampCount(v, 2, MOD_LANE_SIZE); }
function setweightsteps(v) { weightSteps = clampCount(v, 2, MOD_LANE_SIZE); }

// Quantized step value (0..MOD_LEVELS-1) -> modulation unit in -1..1, centred on the lane's midpoint.
function modUnit(v) { return (v - (MOD_LEVELS - 1) / 2) / ((MOD_LEVELS - 1) / 2); }
function advanceMod() {
	rotModPos = (rotModPos + 1) % Math.max(1, rotSteps);
	weightModPos = (weightModPos + 1) % Math.max(1, weightSteps);
}

// Per-onset probability gate, rng injectable so it's unit-testable without Math.random.
// layerIdxs: the layers that landed on this (possibly merged) onset. Returns the subset that
// survive their own per-layer roll -- an empty result means the onset doesn't sound this cycle.
function pickSurvivors(layerIdxs, probArr, rand) {
	rand = rand || Math.random;
	var out = [];
	for (var i = 0; i < layerIdxs.length; i++) {
		var li = layerIdxs[i];
		var p = (probArr[li] == null) ? 100 : probArr[li];
		if (p >= 100 || rand() * 100 < p) out.push(li);
	}
	return out;
}
function passProb(p, rand) {
	rand = rand || Math.random;
	if (p >= 100) return true;
	if (p <= 0) return false;
	return rand() * 100 < p;
}

// Step 7: in-device preset slots, ported from forteseq2.js's own scheme so the whole forteseq
// family saves patterns the same way -- NOT Live's device-preset browser (one .adv file per save,
// buried in the User Library) but a bank the device itself owns: LiveAPI("this_device") scans
// the device's OWN Live parameters generically (no per-device name list to maintain), reads every
// value into presetBank[slot], and the whole bank round-trips to a plain-text file next to the
// .amxd. This is why Step 6 built every new control as a real live.numbox Live parameter rather
// than raw js state -- storepreset/recallpreset only see what LiveAPI can enumerate.
var PRESET_FILE = "harmonograph_presets.txt";
var PRESET_SLOTS = 20;
var presetSlot = 1;
var presetBank = [];      // slot -> {paramName: value, __name?}; index 0 unused so slots read as they look
var presetIdOf = null;    // parameter longname -> Live API id, built once per open patcher
var presetApi = null;     // one LiveAPI, re-pointed by id
// Excluded from every slot: Run/Open aren't sounds (transport + window state), and Slot is the
// navigation control itself -- storing "was on slot 5" inside slot 5 would be circular.
var PRESET_SKIP = { "Run": 1, "Open": 1, "Slot": 1 };

function devPath(file) {
	var fp = "";
	try { fp = this.patcher.filepath; } catch (e) { fp = ""; }
	if (!fp) return file;
	var cut = fp.lastIndexOf("/");
	if (cut < 0) cut = fp.lastIndexOf("\\");
	return cut >= 0 ? fp.slice(0, cut + 1) + file : file;
}

function presetScan() {
	if (presetIdOf) return presetIdOf;
	if (typeof LiveAPI === "undefined") return null;   // outside Live there is no API, and --check never calls this
	var map = {}, n = 0;
	try {
		var dev = new LiveAPI(null, "this_device");
		var ids = dev.get("parameters");   // ["id", 1, "id", 2, ...]
		presetApi = new LiveAPI(null);
		for (var i = 0; i < ids.length; i++) {
			if (typeof ids[i] !== "number") continue;
			presetApi.id = ids[i];
			var raw = presetApi.get("name");
			var nm = (raw && typeof raw.join === "function") ? raw.join(" ") : ("" + raw);
			if (nm && !map.hasOwnProperty(nm)) { map[nm] = ids[i]; n++; }
		}
	} catch (e) {
		post('harmonograph: no pude leer los parametros del device: ' + e + '\n');
		return null;
	}
	presetIdOf = map;
	post('harmonograph: los presets ven ' + n + ' parametros\n');
	return map;
}

function presetrescan() {
	presetIdOf = null;
	presetApi = null;
	post('harmonograph: mapa de parametros descartado, se rearma en el proximo guardar o cargar\n');
}

function presetSlotOf(slot) {
	var s = (slot === undefined || slot === null) ? presetSlot : Math.round(slot);
	if (!(s >= 1 && s <= PRESET_SLOTS)) {
		post('harmonograph: el slot ' + s + ' esta fuera de rango (1..' + PRESET_SLOTS + ')\n');
		return -1;
	}
	return s;
}

function setpresetslot(n) {
	n = Math.round(n);
	if (!isFinite(n) || n < 1) n = 1;
	if (n > PRESET_SLOTS) n = PRESET_SLOTS;
	presetSlot = n;
	highlightPresetSlot(n);
	syncNameBox(n);
}

// Keeps the name textedit showing the TRUE current slot's name, not whatever was last typed.
// Needed because Save now captures the box's live content unconditionally (see the build
// script's save_bid -> obj-nameedit bang) -- without this, switching slots without editing the
// name field would let a stale name from a different slot get stamped onto the new one.
function syncNameBox(s) {
	var vals = presetBank[s];
	outlet(2, 'set', (vals && vals.__name) ? vals.__name : '');
}

// Step 8: "Slot + Save/Load/Clear together, and let me see the presets by name" -- rather than
// a bare numbox plus a separate name readout, the whole bank drives one umenu showing every
// slot's name at once ("01: Denso 4v", "02: (vacio)", ...). `clear`/`append <label>` rebuild the
// umenu's item list outright, `set <index>` just moves its highlight -- exactly the messages a
// plain Max umenu already understands natively, sent as-is on the dedicated outlet 1 (see the
// `outlets = 2` note above) with no tag and no further processing needed on the Max side. Picking
// a menu item feeds back into the Slot numbox (single source of truth, same idiom as the drag
// ring), NOT a direct recall -- browsing the names should not by itself overwrite the current pattern.
function presetLabel(s) {
	var vals = presetBank[s];
	var nm = (vals && vals.__name) ? vals.__name : '(vacio)';
	return (s < 10 ? '0' : '') + s + ': ' + nm;
}
function sendPresetMenu() {
	outlet(1, 'clear');
	for (var s = 1; s <= PRESET_SLOTS; s++) outlet(1, 'append', presetLabel(s));
	highlightPresetSlot(presetSlot);
}
function highlightPresetSlot(s) { outlet(1, 'set', s - 1); }

// Names the CURRENT slot (not an arbitrary one -- same "act on presetSlot" default as
// storepreset/recallpreset/clearpreset) from the toolbar's textedit box.
function setpresetname(name) {
	var s = presetSlot;
	if (!presetBank[s]) presetBank[s] = {};
	presetBank[s].__name = '' + name;
	savepresets();
	sendPresetMenu();
}

function storepreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	var map = presetScan();
	if (!map) { post('harmonograph: los presets necesitan la Live API, que solo existe dentro de Live\n'); return; }
	var vals = {}, n = 0, nm = '';
	// Wrapped because an exception inside a js object stops the whole script in Live -- the
	// sequencer would go silent with only one line in the console to explain it.
	try {
		for (nm in map) {
			if (PRESET_SKIP[nm]) continue;
			presetApi.id = map[nm];
			var v = presetApi.get('value');
			vals[nm] = (v && typeof v.join === 'function') ? v[0] : v;
			n++;
		}
	} catch (e) {
		post('harmonograph: fallo leyendo ' + nm + ': ' + e + '\n');
		return;
	}
	var oldName = (presetBank[s] && presetBank[s].__name) || '';
	if (oldName) vals.__name = oldName;
	presetBank[s] = vals;
	savepresets();
	sendPresetMenu();
	post('harmonograph: slot ' + s + ' guardado, ' + n + ' parametros\n');
}

function recallpreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	var vals = presetBank[s];
	if (!vals) { post('harmonograph: el slot ' + s + ' esta vacio\n'); return; }
	var map = presetScan();
	if (!map) { post('harmonograph: los presets necesitan la Live API, que solo existe dentro de Live\n'); return; }
	var n = 0, miss = 0, nm = '';
	try {
		for (nm in vals) {
			if (nm === '__name') continue;
			// A name the device no longer has means a slot written by an older version -- skip it
			// silently, the rest of the slot is still exactly what was saved.
			if (!map.hasOwnProperty(nm)) { miss++; continue; }
			presetApi.id = map[nm];
			presetApi.set('value', vals[nm]);
			n++;
		}
	} catch (e) {
		post('harmonograph: fallo escribiendo ' + nm + ': ' + e + '\n');
	}
	emitCurve();   // the recalled Rot/Weight/K/Axis values redraw right away, not next cycle
	post('harmonograph: slot ' + s + ' cargado, ' + n + ' parametros' +
		(miss ? ' (' + miss + ' que este device ya no tiene)' : '') + '\n');
}

function clearpreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	presetBank[s] = null;
	savepresets();
	sendPresetMenu();
	if (s === presetSlot) syncNameBox(s);
	post('harmonograph: slot ' + s + ' borrado\n');
}

// Tab separated rather than JSON: parameter names can have spaces ("L1 RotDepth" reads fine, but
// nothing rules out a future rename with one), so a space cannot separate fields and a tab cannot
// appear inside a name -- the file stays something you can open and read.
function savepresets() {
	if (typeof File === 'undefined') return;   // outside Max there is no disk, and --check never calls this
	var f = new File(devPath(PRESET_FILE), 'write', 'TEXT');
	if (!f.isopen) {
		post('harmonograph: no pude escribir ' + devPath(PRESET_FILE) + ', los slots duran hasta cerrar\n');
		return;
	}
	try {
		f.eof = 0;        // a smaller bank cannot leave the previous one's tail behind
		f.position = 0;
		f.writeline('harmonograph presets 1');
		for (var s = 1; s <= PRESET_SLOTS; s++) {
			var vals = presetBank[s];
			if (!vals) continue;
			var line = '' + s;
			if (vals.__name) line += '\t__name=' + vals.__name;
			for (var nm in vals) {
				if (nm === '__name') continue;
				line += '\t' + nm + '=' + vals[nm];
			}
			f.writeline(line);
		}
	} catch (e) {
		post('harmonograph: fallo al guardar los presets: ' + e + '\n');
	}
	f.close();
}

function loadpresets() {
	if (typeof File === 'undefined') return;
	var f = new File(devPath(PRESET_FILE), 'read', 'TEXT');
	if (!f.isopen) return;   // no file yet -- first run, not an error
	presetBank = [];
	try {
		f.readline(200);   // the header, there only so the file explains itself
		while (f.position < f.eof) {
			var line = '' + f.readline(65536);
			var parts = line.split('\t');
			var s = Math.round(parseFloat(parts[0]));
			if (!(s >= 1 && s <= PRESET_SLOTS)) continue;
			var vals = {};
			for (var i = 1; i < parts.length; i++) {
				var eq = parts[i].lastIndexOf('=');
				if (eq <= 0) continue;
				var key = parts[i].slice(0, eq);
				if (key === '__name') { vals.__name = parts[i].slice(eq + 1); continue; }
				var v = parseFloat(parts[i].slice(eq + 1));
				if (isFinite(v)) vals[key] = v;
			}
			presetBank[s] = vals;
		}
	} catch (e) {
		post('harmonograph: fallo al leer los presets: ' + e + '\n');
	}
	f.close();
	sendPresetMenu();
	syncNameBox(presetSlot);
}

// Tempo sync: periodMs is DERIVED when on, same shape as forteseqwf. settempo() is fed by a
// live.observer on the Live Set's tempo; the derived ms is pushed out tagged "ms" so the patch's
// metro picks it up without re-doing the beats->ms math (see the .amxd's `route n ms`).
function recomputeSyncedPeriod() {
	if (!syncTempo) return;
	periodMs = clampMs(beatsPerPeriod * (60000 / liveTempo));
	outlet(0, "ms", periodMs);
}
function setsync(v) { syncTempo = v ? 1 : 0; recomputeSyncedPeriod(); }
function setbeats(v) { v = Number(v); if (isFinite(v) && v > 0) { beatsPerPeriod = v < 0.25 ? 0.25 : (v > 64 ? 64 : v); recomputeSyncedPeriod(); } }
function settempo(v) { v = Number(v); if (isFinite(v) && v > 0) { liveTempo = v; recomputeSyncedPeriod(); } }
function settransport(v) { transportPlaying = v ? 1 : 0; if (syncTempo && !transportPlaying) stopAllTasks(); }

function shouldRun() {
	if (!running) return false;
	if (syncTempo && !transportPlaying) return false;
	return true;
}

// The current layer list, each rotation converted from turns to steps on the LCM grid. Rot and
// Weight are pushed by the shared quantized modulators first, scaled by each layer's own depth
// (0 = no effect); the modulators' step position itself advances once per cycle (advanceMod).
function currentLayers() {
	var Ks = [], i;
	for (i = 0; i < numLayers; i++) Ks.push(clampCount(layerK[i], 2, MAX_K));
	var n = lcmAll(Ks);
	var rotMod = modUnit(rotStepVal[rotModPos % Math.max(1, rotSteps)]);
	var wtMod = modUnit(weightStepVal[weightModPos % Math.max(1, weightSteps)]);
	var out = [];
	for (i = 0; i < numLayers; i++) {
		var rotTurns = (layerRot[i] || 0) + rotMod * (layerRotDepth[i] / 100) * ROT_MOD_RANGE_TURNS;
		var wt = layerWeight[i] * (1 + wtMod * (layerWeightDepth[i] / 100));
		if (wt < 0) wt = 0;
		out.push({
			K: Ks[i], rot: rotTurns * n, weight: wt,
			decay: globalDecay, axis: AXIS_NAMES[layerAxis[i]] || 'x'
		});
	}
	return out;
}

// Push the harmonograph curve + onset markers to the jsui (tagged; split off by the patch's
// `route n ms curve marks hit`). Fires only on a layer/count change -- never per tick. During a
// drag the setters fire ~30x/s, so a 40ms throttle coalesces the burst (with a trailing Task so
// the final state always lands); the ~1k-atom curve message is otherwise rare enough not to matter.
var _curveTask = null, _curveLast = 0;
function emitCurve() {
	if (typeof outlet === 'undefined') return;   // pure --check context
	var now = (new Date()).getTime();
	if (now - _curveLast < 40) {
		if (!_curveTask) {
			_curveTask = new Task(function () { _curveTask = null; emitCurve(); }, this);
			_curveTask.schedule(45);
		}
		return;
	}
	_curveLast = now;
	var res = render(currentLayers(), { samples: CURVE_SAMPLES, loops: 1 });
	var msg = [0, "curve", res.n, res.curve.length];
	for (var i = 0; i < res.curve.length; i++) msg.push(res.curve[i].x, res.curve[i].y);
	outlet.apply(this, msg);
	var mk = [0, "marks", res.onsets.length];
	for (i = 0; i < res.onsets.length; i++) {
		mk.push(res.marks[i].x, res.marks[i].y, res.onsets[i].layers[0] || 0);
	}
	outlet.apply(this, mk);
	// per-layer (rotation turns, weight, MIDI pitch) so the jsui can place a draggable handle
	// per layer and, when HarmColor is on, colour it by that layer's pitch class.
	var lay = [0, "lay", numLayers];
	for (i = 0; i < numLayers; i++) lay.push(layerRot[i] || 0, layerWeight[i], layerPitch[i] || 0);
	outlet.apply(this, lay);
}

function scheduleOnset(delayMs, pitch, vel, dur, markIdx) {
	var t = new Task(function () {
		outlet(0, "n", pitch, vel, dur);
		outlet(0, "hit", markIdx);
	}, this);
	t.schedule(delayMs);
	scheduledTasks.push(t);
}

// One cycle, fed by the metro's bang. Rebuilt from scratch every period (per forteseq-hot-path:
// JS compute is free, boundary crossings are the cost, and pbStack over a handful of polygons is
// nothing). Coincident onsets get a velocity bump per SURVIVING extra polygon (pbStack's `count`
// counts every polygon regardless of probability, so re-derive it from the layers that actually
// rolled a hit). The quantized Rot/Weight modulators advance one step, and the curve is refreshed,
// once per cycle -- cheap even at MIN_PERIOD_MS thanks to emitCurve's own throttle.
function startCycle() {
	stopAllTasks();
	if (!shouldRun()) return;
	outlet(0, "cyc", periodMs);   // tells the jsui a new loop started + how long it is (comet timing)
	var res = pbStack(currentLayers());
	if (res.n && res.n >= 1) {
		var scheduled = 0;
		for (var i = 0; i < res.onsets.length; i++) {
			if (scheduled >= MAX_ONSETS_PER_CYCLE) {
				post('harmonograph: circuit breaker -- refusing past ' + MAX_ONSETS_PER_CYCLE + ' onsets (grid ' + res.n + ')\n');
				break;
			}
			var o = res.onsets[i];
			var survivors = pickSurvivors(o.layers, layerProb, Math.random);
			if (survivors.length === 0) continue;
			if (!passProb(globalProb, Math.random)) continue;
			var delay = (o.pos / res.n) * periodMs;
			var lyr = survivors[0];
			var pitch = clampCount(layerPitch[lyr], 0, 127);
			var vel = baseVel + (survivors.length - 1) * accentPerCoincidence;
			if (vel > 127) vel = 127;
			scheduleOnset(delay, pitch, vel, baseDur, i);
			scheduled++;
		}
	}
	advanceMod();
	emitCurve();
}

function bang() { startCycle(); }

// Called automatically by Max when the patcher containing this js object loads -- distinct from
// (and in addition to) any [loadbang] object wired into inlet 0, same idiom as forteseq2.js.
function loadbang() { loadpresets(); }

// ================================================================================================
// node --check harness -- runs only under node (Max's js object has no require/process).
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
				console.error('FAIL ' + label + ': got ' + got + ', want ' + want + ' (diff ' + Math.abs(got - want) + ')');
				failures++;
			}
		}
		function mag(pt) { return Math.sqrt(pt.x * pt.x + pt.y * pt.y); }

		function checkGcdLcm() {
			var f0 = failures;
			eq(gcd(12, 8), 4, 'gcd(12,8)');
			eq(lcm(12, 8), 24, 'lcm(12,8)');
			eq(lcmAll([2, 3, 4]), 12, 'lcmAll(2,3,4)');
			eq(lcmAll([3, 4, 5]), 60, 'lcmAll(3,4,5)');
			eq(lcmAll([2, 2, 3]), 6, 'lcmAll(2,2,3)');
			eq(lcmAll([6]), 6, 'lcmAll(6)');
			eq(gridTooBig(5041), true, 'gridTooBig over');
			eq(gridTooBig(60), false, 'gridTooBig under');
			if (failures === f0) console.log('OK   checkGcdLcm: gcd / lcm / lcmAll / grid cap.');
		}

		// A regular K-gon (K >= 2) on an exact grid is perfectly balanced -- at any rotation,
		// integer or fractional. A monogon (K = 1) is not: its centroid sits on the rim.
		function checkPolygonBalance() {
			var f0 = failures;
			var Ks = [2, 3, 4, 5, 6, 7, 8, 11, 12, 13];
			for (var i = 0; i < Ks.length; i++) {
				var K = Ks[i], n = K * 5;
				var rots = [0, 2, 1.37];
				for (var r = 0; r < rots.length; r++) {
					var pts = polygonOnsets(K, n, rots[r]);
					eq(pts.length, K, 'K=' + K + ' rot=' + rots[r] + ' onset count');
					approxEq(centroidMag(pts, n), 0, 'K=' + K + ' rot=' + rots[r] + ' balanced');
				}
			}
			approxEq(centroidMag(polygonOnsets(1, 12, 0), 12), 1, 'monogon centroid = 1 (unbalanced)');
			if (failures === f0) console.log('OK   checkPolygonBalance: every regular K-gon balanced at integer and fractional rotation; monogon is not.');
		}

		// The union of independently-rotated regular polygons is perfectly balanced, and the LCM
		// grid is the natural common denominator.
		function checkStackBalance() {
			var f0 = failures;
			function bal(layers) { var s = pbStack(layers); return stackCentroidMag(s.onsets, s.n); }
			approxEq(bal([{ K: 2, rot: 0 }, { K: 2, rot: 1 }, { K: 3, rot: 1 }]), 0, 'digon + offset digon + triangle balanced');
			approxEq(bal([{ K: 3, rot: 0 }, { K: 4, rot: 0 }, { K: 5, rot: 0 }]), 0, '3-4-5 balanced');
			approxEq(bal([{ K: 2, rot: 0 }, { K: 3, rot: 0 }, { K: 7, rot: 0 }]), 0, '2-3-7 balanced');
			eq(pbStack([{ K: 2 }, { K: 2 }, { K: 3 }]).n, 6, 'lcm(2,2,3) = 6');
			eq(pbStack([{ K: 3 }, { K: 4 }, { K: 5 }]).n, 60, 'lcm(3,4,5) = 60');
			// a layer with K < 2 is ignored, not an error
			eq(pbStack([{ K: 1 }, { K: 3 }]).n, 3, 'sub-digon layer ignored');
			if (failures === f0) console.log('OK   checkStackBalance: unions of coprime polygons balanced; grid is the LCM of the K values.');
		}

		// The theorem in action: rotating any layer by any amount -- fractional included, all
		// three layers independently -- never disturbs the union's balance.
		function checkRotationInvariance() {
			var f0 = failures;
			var rots = [0, 1.37, 2.5, 3.9, 7.13, 11.6];
			for (var a = 0; a < rots.length; a++)
				for (var b = 0; b < rots.length; b++)
					for (var c = 0; c < rots.length; c++) {
						var s = pbStack([{ K: 3, rot: rots[a] }, { K: 4, rot: rots[b] }, { K: 5, rot: rots[c] }]);
						approxEq(stackCentroidMag(s.onsets, s.n), 0,
							'rot-invariant [' + rots[a] + ',' + rots[b] + ',' + rots[c] + ']');
					}
			if (failures === f0) console.log('OK   checkRotationInvariance: ' + (rots.length * rots.length * rots.length) + ' independent-rotation stacks, all still balanced.');
		}

		function checkLayerToPendulum() {
			var f0 = failures;
			var p = layerToPendulum({ K: 5, rot: 3, weight: 0.8, decay: 1.5 }, 20, 'y');
			eq(p.freq, 5, 'K -> freq');
			approxEq(p.amp, 0.8, 'weight -> amp');
			approxEq(p.phase, TWO_PI * 3 / 20, 'rot -> phase');
			approxEq(p.damp, 1.5, 'decay -> damp');
			eq(p.axis, 'y', 'axis passthrough');
			eq(layerToPendulum({ K: 1 }, 12, 'x').freq, 2, 'freq clamped up to 2');
			eq(layerToPendulum({ K: 99 }, 12, 'x').freq, MAX_K, 'freq clamped down to MAX_K');
			var q = layerToPendulum({ K: 4, rot: 0 }, 8, 'x');
			approxEq(q.amp, 1, 'missing weight -> amp 1');
			approxEq(q.damp, 0, 'missing decay -> damp 0');
			if (failures === f0) console.log('OK   checkLayerToPendulum: K/rot/weight/decay map to freq/phase/amp/damp, with clamps.');
		}

		// Undamped + integer frequency + whole loops => the curve returns exactly to its start.
		// Add damping and the final point is pulled in toward the origin (the pen spiralling in).
		function checkCurveClosure() {
			var f0 = failures;
			var undamped = harmonoCurve(
				[{ freq: 3, amp: 1, phase: 0.7, damp: 0, axis: 'x' }, { freq: 2, amp: 1, phase: 0.7, damp: 0, axis: 'y' }],
				500, { loops: 1 });
			var d0 = mag({ x: undamped[0].x - undamped[500].x, y: undamped[0].y - undamped[500].y });
			approxEq(d0, 0, 'undamped curve closes');

			var damped = harmonoCurve(
				[{ freq: 3, amp: 1, phase: 0.7, damp: 2, axis: 'x' }, { freq: 2, amp: 1, phase: 0.7, damp: 2, axis: 'y' }],
				500, { loops: 1 });
			var m0 = mag(damped[0]), mN = mag(damped[500]);
			if (!(mN < 0.3 * m0)) { console.error('FAIL damped curve spirals in: end mag ' + mN + ' not << start mag ' + m0); failures++; }
			if (!(mN > 0)) { console.error('FAIL damped curve not fully collapsed'); failures++; }
			approxEq(mN / m0, Math.exp(-2), 'damping envelope is exp(-decay) over the loop', 1e-6);
			if (failures === f0) console.log('OK   checkCurveClosure: undamped curve closes; damped curve decays to exp(-decay) of its start.');
		}

		// The 3:2 Lissajous: unit box, x peaks at t = 1/12, y peaks at t = 1/8, both cross zero
		// at t = 1/2.
		function checkLissajous() {
			var f0 = failures;
			var c = harmonoCurve(
				[{ freq: 3, amp: 1, phase: 0, damp: 0, axis: 'x' }, { freq: 2, amp: 1, phase: 0, damp: 0, axis: 'y' }],
				1200, { loops: 1 });
			var b = curveBounds(c);
			approxEq(b.maxx, 1, 'Lissajous max x');
			approxEq(b.minx, -1, 'Lissajous min x');
			approxEq(b.maxy, 1, 'Lissajous max y');
			approxEq(b.miny, -1, 'Lissajous min y');
			approxEq(c[100].x, 1, 'x peak at t = 1/12');
			approxEq(c[150].y, 1, 'y peak at t = 1/8');
			approxEq(c[600].x, 0, 'x zero at t = 1/2');
			approxEq(c[600].y, 0, 'y zero at t = 1/2');
			if (failures === f0) console.log('OK   checkLissajous: 3:2 figure sits in the unit box with the right extrema.');
		}

		function checkOnsetMarks() {
			var f0 = failures;
			var r = render([{ K: 3, rot: 0 }, { K: 4, rot: 0 }], { samples: 240 });
			eq(r.marks.length, r.onsets.length, 'one mark per onset');
			var last = r.curve.length - 1;
			for (var i = 0; i < r.marks.length; i++) {
				var idx = Math.round((r.onsets[i].pos / r.n) * last);
				approxEq(r.marks[i].x, r.curve[idx].x, 'mark ' + i + ' x lies on curve');
				approxEq(r.marks[i].y, r.curve[idx].y, 'mark ' + i + ' y lies on curve');
			}
			if (failures === f0) console.log('OK   checkOnsetMarks: every onset marker sits on the sampled curve.');
		}

		function checkRender() {
			var f0 = failures;
			var r = render([{ K: 2, rot: 0, weight: 1 }, { K: 3, rot: 1, weight: 1 }, { K: 5, rot: 2, weight: 1 }], { samples: 512 });
			eq(r.n, 30, 'render grid = lcm(2,3,5)');
			eq(r.onsets.length, 10, 'render onset count (2 + 3 + 5)');
			approxEq(r.centroid, 0, 'render stack balanced');
			approxEq(r.balance, 1, 'render balance score');
			eq(r.curve.length, 513, 'render curve length = samples + 1');
			eq(r.marks.length, r.onsets.length, 'render marks == onsets');
			eq(r.pendulums.length, 3, 'render one pendulum per layer');
			eq(r.pendulums[0].axis, 'x', 'axis cycle 0 -> x');
			eq(r.pendulums[1].axis, 'y', 'axis cycle 1 -> y');
			eq(r.pendulums[2].axis, 'rot', 'axis cycle 2 -> rot');
			var rax = render([{ K: 3, axis: 'rot' }, { K: 4 }], { samples: 64 });
			eq(rax.pendulums[0].axis, 'rot', 'explicit layer axis wins over the cycle');
			for (var i = 1; i < r.onsets.length; i++) {
				if (!(r.onsets[i].pos > r.onsets[i - 1].pos)) {
					console.error('FAIL render onsets not strictly ascending at ' + i); failures++;
				}
			}
			if (failures === f0) console.log('OK   checkRender: end-to-end -- LCM grid, balanced stack, closed sorted onsets, curve + markers.');
		}

		function checkModUnit() {
			var f0 = failures;
			approxEq(modUnit(0), -1, 'modUnit(0) = -1 (bottom quantized level)');
			approxEq(modUnit(MOD_LEVELS - 1), 1, 'modUnit(max level) = 1');
			approxEq(modUnit((MOD_LEVELS - 1) / 2), 0, 'modUnit(centre level) = 0');
			if (failures === f0) console.log('OK   checkModUnit: quantized step value 0..' + (MOD_LEVELS - 1) + ' maps to modulation unit -1..1.');
		}

		// Per-layer depth scales the shared quantized Rot/Weight lanes into currentLayers(); depth 0
		// must be a strict no-op (the "shared lane, per-layer depth" design only works if it is).
		function checkModulationAppliesToLayers() {
			var f0 = failures;
			numLayers = 1; layerK[0] = 4; layerRot[0] = 0.25; layerWeight[0] = 1;
			rotSteps = 8; weightSteps = 8; rotModPos = 0; weightModPos = 0;

			layerRotDepth[0] = 100; layerWeightDepth[0] = 100;
			rotStepVal[0] = 0; weightStepVal[0] = 0;
			var lo = currentLayers()[0];
			rotStepVal[0] = MOD_LEVELS - 1; weightStepVal[0] = MOD_LEVELS - 1;
			var hi = currentLayers()[0];
			if (!(hi.rot > lo.rot)) { console.error('FAIL modulation: max step should rotate further than min step'); failures++; }
			if (!(hi.weight > lo.weight)) { console.error('FAIL modulation: max step should weigh more than min step'); failures++; }

			layerRotDepth[0] = 0; layerWeightDepth[0] = 0;
			var flat = currentLayers()[0];
			approxEq(flat.rot, layerRot[0] * lcmAll([4]), 'zero rot depth is a no-op regardless of step value', 1e-9);
			approxEq(flat.weight, layerWeight[0], 'zero weight depth is a no-op regardless of step value');

			layerRotDepth[0] = 0; layerWeightDepth[0] = 0; rotStepVal[0] = 4; weightStepVal[0] = 4; numLayers = 2;
			if (failures === f0) console.log('OK   checkModulationAppliesToLayers: per-layer depth scales the shared quantized lanes into rot/weight; depth 0 is a no-op.');
		}

		function checkAdvanceModWraps() {
			var f0 = failures;
			rotSteps = 3; weightSteps = 5; rotModPos = 0; weightModPos = 0;
			for (var i = 0; i < 3; i++) advanceMod();
			eq(rotModPos, 0, 'rotModPos wraps at its own Steps count (3)');
			eq(weightModPos, 3, 'weightModPos keeps counting independently (not yet wrapped at 5)');
			rotSteps = 8; weightSteps = 8; rotModPos = 0; weightModPos = 0;
			if (failures === f0) console.log('OK   checkAdvanceModWraps: the two lanes advance and wrap independently on their own Steps count.');
		}

		// rng is injected so the gate logic is deterministic under --check, no dependence on Math.random.
		function checkProbabilityGate() {
			var f0 = failures;
			var lowRand = function () { return 0; };       // always wins the roll
			var highRand = function () { return 0.999; };  // almost never wins
			eq(pickSurvivors([0, 1], [100, 100], highRand).length, 2, 'prob 100 always survives, even against a high roll');
			eq(pickSurvivors([0, 1], [0, 0], lowRand).length, 0, 'prob 0 never survives, even against a low roll');
			eq(pickSurvivors([0, 1], [50, 50], highRand).length, 0, 'prob 50 fails a high roll');
			eq(pickSurvivors([0, 1], [50, 50], lowRand).length, 2, 'prob 50 passes a low roll');
			eq(pickSurvivors([0, 2], [100, 999, 0], lowRand).join(','), '0', 'mixed layer probabilities keep only the surviving layer');
			eq(passProb(100, highRand), true, 'global prob 100 always passes');
			eq(passProb(0, lowRand), false, 'global prob 0 never passes');
			eq(passProb(50, lowRand), true, 'global prob 50 passes a low roll');
			eq(passProb(50, highRand), false, 'global prob 50 fails a high roll');
			if (failures === f0) console.log('OK   checkProbabilityGate: per-layer and global probability gates threshold-tested against an injectable rng.');
		}

		function main() {
			checkGcdLcm();
			checkPolygonBalance();
			checkStackBalance();
			checkRotationInvariance();
			checkLayerToPendulum();
			checkCurveClosure();
			checkLissajous();
			checkOnsetMarks();
			checkRender();
			checkModUnit();
			checkModulationAppliesToLayers();
			checkAdvanceModWraps();
			checkProbabilityGate();
			if (failures === 0) { console.log('ALL OK'); process.exitCode = 0; }
			else { console.error(failures + ' failure(s)'); process.exitCode = 1; }
		}

		if (process.argv.indexOf('--check') !== -1) main();
		else console.error('usage: node forteseq/harmonograph.js --check');
	})();
}
