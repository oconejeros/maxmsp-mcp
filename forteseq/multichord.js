// multichord.js -- engine for multichord.amxd (annular voice-leading space). Two exploration
// modes, picked by `mode` / the Mode menu:
//
//   Nearest (mode 0) -- madmusicalscience.com/multichord: every transposition of every chord type
//     is a node in one big graph; the "current" chord sits at the centre, and its neighbours are
//     laid out in rings by voice-leading distance -- the nearer a chord sounds, the closer its
//     ring. Repeated nearest-first hops walk the entire graph (it's connected: every chord has
//     *some* neighbour).
//   Steps (mode 1) -- madmusicalscience.com/cs.html, generalized: chords stay inside one fixed
//     scale, and a neighbour differs by moving exactly one voice by one scale-step (Callender/
//     Quinn/Tymoczko generalized voice-leading spaces). See stepsNeighborsOf() below.
//
// Either way, turning the Nav control steps to the next-ranked neighbour and recentres the whole
// space there; clicking a node in the jsui jumps straight to it. computeRankList() dispatches to
// whichever mode is active; both resolve back through UNIVERSE_BY_MASK, so the rest of the engine
// (recentering, the jsui wire format) never needs to know which mode produced a given neighbour.
//
// The chord universe is FORTESEQ's own 351 Forte Tn-classes (rotate12/buildClasses below is the
// same algorithm as forteseq2.js/pcset351.js, kept as an independent copy since this device is
// standalone), expanded to all 4095 concrete transposed pitch-class sets.
//
// All the colour maths lives in the shared module pccolor.js: this file `include()`s it in Max and
// `require()`s it in node. Everything above the "Max-facing engine" divider is pure and covered by
// `node multichord.js --check`.

var PC;
if (typeof require === 'function' && typeof module !== 'undefined') {
	PC = require('./pccolor.js');
} else {
	if (typeof include === 'function') include('pccolor.js');
	PC = {
		pcToColor: pcToColor, harmonyToColor: harmonyToColor, rgbToHsl: rgbToHsl,
		noteName: noteName, intervalVector: intervalVector, dissonancePct: dissonancePct
	};
}

function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
function clampInt(v, lo, hi) { v = Math.round(Number(v)); if (!isFinite(v)) return lo; return v < lo ? lo : (v > hi ? hi : v); }
function mod12(n) { return ((Math.round(n) % 12) + 12) % 12; }
function mod360(n) { return ((n % 360) + 360) % 360; }

// --- 351 Forte Tn-class generator (byte-identical algorithm to forteseq2.js / pcset351.js) -----

function popcount(x) {
	var c = 0;
	while (x) { c += x & 1; x >>= 1; }
	return c;
}

function rotate12(x) { return ((x << 1) | (x >> 11)) & 0xFFF; }

// -> 351 canonical pc-sets (each the lowest-bitmask rotation of its Tn-class), sorted by
// cardinality then value -- ChordIdx 0..350 in that order.
function buildClasses() {
	var seen = {}, canon = [];
	for (var n = 1; n < 4096; n++) {
		var best = n, cur = n;
		for (var r = 0; r < 11; r++) { cur = rotate12(cur); if (cur < best) best = cur; }
		if (!seen[best]) { seen[best] = true; canon.push(best); }
	}
	canon.sort(function (a, b) {
		var ca = popcount(a), cb = popcount(b);
		if (ca !== cb) return ca - cb;
		return a - b;
	});
	var classes = [];
	for (var i = 0; i < canon.length; i++) {
		var bits = canon[i], pcs = [];
		for (var p = 0; p < 12; p++) if (bits & (1 << p)) pcs.push(p);
		classes.push(pcs);
	}
	return classes;
}

function transposeSet(pcs, t) {
	var out = [];
	for (var i = 0; i < pcs.length; i++) out.push(mod12(pcs[i] + t));
	return out.sort(function (a, b) { return a - b; });
}
function bitmask(pcs) { var m = 0; for (var i = 0; i < pcs.length; i++) m |= (1 << pcs[i]); return m; }

// -> [{mask, pcs, card, classIdx, t}, ...], one entry per nonempty 12-bit mask (exactly 4095).
// Built outward from the 351 classes (351*12 = 4212 transpositions) and deduped by mask: a class
// that is itself transpositionally symmetric (e.g. the diminished 7th, the whole-tone hexachord)
// revisits a mask it already produced at a smaller t, which is exactly the 4212-4095=117 overlap
// symmetry theory predicts -- so a plain "first one wins" dedup is correct, not a workaround.
function buildUniverse(classes) {
	var byMask = {}, universe = [];
	for (var ci = 0; ci < classes.length; ci++) {
		for (var t = 0; t < 12; t++) {
			var pcs = transposeSet(classes[ci], t);
			var m = bitmask(pcs);
			if (byMask.hasOwnProperty(m)) continue;
			byMask[m] = true;
			universe.push({ mask: m, pcs: pcs, card: pcs.length, classIdx: ci, t: t });
		}
	}
	return universe;
}

// --- circular (chroma-circle) voice-leading distance ---------------------------------------
// Same nearest-neighbour-both-directions shape as forteseq2.js's chordDistance (used there for
// real voicings in open pitch space), but circular: pc 11 and pc 0 are distance 1, not 11. That
// also makes it well-defined between mismatched cardinalities without any special-casing.

function circDist(a, b) { var d = Math.abs(a - b) % 12; return Math.min(d, 12 - d); }

function chordDistanceCircular(a, b) {
	var total = 0, i, j, d, best;
	for (i = 0; i < a.length; i++) {
		best = 1e9;
		for (j = 0; j < b.length; j++) { d = circDist(a[i], b[j]); if (d < best) best = d; }
		total += best;
	}
	for (j = 0; j < b.length; j++) {
		best = 1e9;
		for (i = 0; i < a.length; i++) { d = circDist(a[i], b[j]); if (d < best) best = d; }
		total += best;
	}
	return total;
}

// -> [{node, dist, hue, color}, ...] ascending by dist (ties: hue, then mask, for determinism),
// excluding the centre's own mask. `rank` for the Nav dial is simply the index into this array.
function neighborsOf(centerPcs, centerMask, universe, paletteOpts) {
	var out = [];
	for (var i = 0; i < universe.length; i++) {
		var u = universe[i];
		if (u.mask === centerMask) continue;
		var col = PC.harmonyToColor(u.pcs, paletteOpts, 'oklab');
		var hsl = PC.rgbToHsl(col.r, col.g, col.b);
		out.push({ node: u, dist: chordDistanceCircular(centerPcs, u.pcs), hue: hsl.h, color: col });
	}
	out.sort(function (a, b) {
		if (a.dist !== b.dist) return a.dist - b.dist;
		if (a.hue !== b.hue) return a.hue - b.hue;
		return a.node.mask - b.node.mask;
	});
	return out;
}

// --- elementary "scale-step" neighbours (Callender/Quinn/Tymoczko generalized voice-leading
// spaces, e.g. madmusicalscience.com/cs.html): a chord is a subset of DEGREE indices into a
// fixed `scale` (itself just one more of the same pc-sets everything else here uses). Three kinds
// of elementary move, each one hop:
//   shift -- move ONE existing voice by one scale-step (+1 or -1, mod scale length), skipping any
//            move that would collide with a degree another voice already occupies (cardinality
//            unchanged -- the classic "single common-tone-preserving move", generalized from a
//            fixed 12-tone chromatic scale (what Tonnetz does) to any scale/chord-size pair).
//   drop  -- remove one voice (cardinality -1), if that stays >= minSize.
//   add   -- add a voice on any unoccupied degree (cardinality +1), if that stays <= maxSize.
// drop/add let exploration modulate between different-sized chords within [minSize, maxSize]
// instead of only ever re-voicing a fixed-size chord.

function degreeSetOf(pcs, scale) {
	var out = [];
	for (var i = 0; i < pcs.length; i++) {
		var idx = scale.indexOf(pcs[i]);
		if (idx < 0) return null;
		out.push(idx);
	}
	return out.sort(function (a, b) { return a - b; });
}

function elementaryMoves(degSet, scaleLen, minSize, maxSize) {
	minSize = minSize == null ? 1 : minSize;
	maxSize = maxSize == null ? scaleLen : maxSize;
	var out = [], occ = {}, i;
	for (i = 0; i < degSet.length; i++) occ[degSet[i]] = true;
	// shift
	for (i = 0; i < degSet.length; i++) {
		for (var dir = -1; dir <= 1; dir += 2) {
			var nd = ((degSet[i] + dir) % scaleLen + scaleLen) % scaleLen;
			if (occ[nd]) continue;
			var next = degSet.slice();
			next[i] = nd;
			out.push(next.sort(function (a, b) { return a - b; }));
		}
	}
	// drop
	if (degSet.length > minSize) {
		for (i = 0; i < degSet.length; i++) {
			var shrunk = degSet.slice();
			shrunk.splice(i, 1);
			out.push(shrunk);
		}
	}
	// add
	if (degSet.length < maxSize) {
		for (var d = 0; d < scaleLen; d++) {
			if (occ[d]) continue;
			out.push(degSet.concat([d]).sort(function (a, b) { return a - b; }));
		}
	}
	return out;
}

// BFS out to `maxDepth` elementary moves from `startDegSet`, deduped by visited degree-set.
// -> [{degreeSet, pcs, mask, hue, color, dist}, ...] ascending by (dist, hue, mask); dist = hop count.
function stepsNeighborsOf(scale, startDegSet, maxDepth, paletteOpts, minSize, maxSize) {
	var scaleLen = scale.length;
	var visited = {};
	visited[startDegSet.join(',')] = true;
	var frontier = [startDegSet], out = [];
	for (var depth = 1; depth <= maxDepth && frontier.length; depth++) {
		var nextFrontier = [];
		for (var f = 0; f < frontier.length; f++) {
			var moves = elementaryMoves(frontier[f], scaleLen, minSize, maxSize);
			for (var m = 0; m < moves.length; m++) {
				var key = moves[m].join(',');
				if (visited[key]) continue;
				visited[key] = true;
				nextFrontier.push(moves[m]);
				var pcs = [];
				for (var di = 0; di < moves[m].length; di++) pcs.push(scale[moves[m][di]]);
				pcs.sort(function (a, b) { return a - b; });
				var col = PC.harmonyToColor(pcs, paletteOpts, 'oklab');
				var hsl = PC.rgbToHsl(col.r, col.g, col.b);
				out.push({ degreeSet: moves[m], pcs: pcs, mask: bitmask(pcs), hue: hsl.h, color: col, dist: depth });
			}
		}
		frontier = nextFrontier;
	}
	out.sort(function (a, b) {
		if (a.dist !== b.dist) return a.dist - b.dist;
		if (a.hue !== b.hue) return a.hue - b.hue;
		return a.mask - b.mask;
	});
	return out;
}

// --- ring / angular layout -------------------------------------------------------------------
// Distance is always a small integer, so the ring index IS that integer -- no artificial
// bucketing. Within a ring, nodes are placed by hue angle (so the layout doubles as a colour
// wheel) and decimated evenly across the hue-sorted order if a ring is over-full, so the visible
// subset still spans the whole wheel instead of clumping at one arc.

var RINGS_MAX = 6;
var NODES_PER_RING_MAX = 10;

// ranked: neighborsOf() output (ascending by dist; index == rank).
// -> { rings: [{dist, nodes:[{node,dist,color,angleDeg,rank}, ...]}, ...], visible: <count> }
function ringLayout(ranked, opts) {
	opts = opts || {};
	var ringsMax = opts.ringsMax || RINGS_MAX;
	var perRingMax = opts.perRingMax || NODES_PER_RING_MAX;
	var groups = [], byDist = {}, i;
	for (i = 0; i < ranked.length; i++) {
		var d = ranked[i].dist;
		if (!byDist.hasOwnProperty(d)) {
			if (groups.length >= ringsMax) break;   // ranked is sorted ascending, so every later
			                                          // entry is >= every distance already seen
			byDist[d] = { dist: d, items: [] };
			groups.push(byDist[d]);
		}
		byDist[d].items.push({ entry: ranked[i], rank: i });
	}
	var rings = [], visible = 0;
	for (var g = 0; g < groups.length; g++) {
		var items = groups[g].items.slice().sort(function (a, b) { return a.entry.hue - b.entry.hue; });
		if (items.length > perRingMax) {
			var picked = [], step = items.length / perRingMax;
			for (var k = 0; k < perRingMax; k++) picked.push(items[Math.floor(k * step)]);
			items = picked;
		}
		var nodes = [];
		for (var n = 0; n < items.length; n++) {
			nodes.push({
				node: items[n].entry.node, dist: items[n].entry.dist, color: items[n].entry.color,
				angleDeg: items[n].entry.hue, rank: items[n].rank
			});
		}
		visible += nodes.length;
		rings.push({ dist: groups[g].dist, nodes: nodes });
	}
	return { rings: rings, visible: visible };
}

// --- voicing (absolute pitch, for audible output) -------------------------------------------
// Each note's OWN target is spread across `span` semitones around the reference pitch according
// to its position in the sorted pc order -- span=0 collapses every note onto the same target
// (every note nearest-octaves to one shared point, which is what always produced a tight closed
// cluster that self-stabilises back to the same register on every hop). A nonzero span pulls the
// chord open into a wider register instead. Not a port of forteseq2's full nearest-register
// solver -- a small, proportionate "keep near previous, but let it breathe" nudge.

function voiceChord(pcs, prevRefPitch, span) {
	span = span == null ? 0 : span;
	var ref = (prevRefPitch == null) ? 60 : prevRefPitch;
	var sorted = pcs.slice().sort(function (a, b) { return a - b; });
	var out = [];
	for (var i = 0; i < sorted.length; i++) {
		var target = sorted.length > 1
			? ref - span / 2 + (i / (sorted.length - 1)) * span
			: ref;
		var pc = sorted[i], best = pc, bestD = 1e9;
		for (var k = -1; k <= 9; k++) {
			var n = pc + 12 * k;
			if (n < 0 || n > 127) continue;
			var d = Math.abs(n - target);
			if (d < bestD) { bestD = d; best = n; }
		}
		out.push(best);
	}
	out.sort(function (a, b) { return a - b; });
	return out;
}

// ================================================================================================
// Max-facing engine: state, message handlers. Nothing below runs under `--check` (outlet is a
// Max global).
// ================================================================================================

inlets = 1;
outlets = 1;

var STEPS_DEPTH = 6;   // how many elementary-move hops the "Steps" mode BFS explores out to

var CLASSES = buildClasses();
var UNIVERSE = buildUniverse(CLASSES);
var UNIVERSE_BY_MASK = {};
for (var _u = 0; _u < UNIVERSE.length; _u++) UNIVERSE_BY_MASK[UNIVERSE[_u].mask] = UNIVERSE[_u];

// looks up which Forte class `pcs` belongs to AND at what transposition -- not just when `pcs`
// happens to already be its class's own canonical (minimal-bitmask) rotation (e.g. [0,4,7] is,
// by luck, but [0,2,4,5,7,9,11] the major scale is not: its canonical rotation is rooted
// elsewhere). Reuses UNIVERSE_BY_MASK (every concrete pc-set resolves to exactly one (classIdx, t)).
function identifyPcs(pcs) {
	var u = UNIVERSE_BY_MASK[bitmask(pcs)];
	return u ? { classIdx: u.classIdx, t: u.t } : { classIdx: 0, t: 0 };
}

var _defaultCenter = identifyPcs([0, 4, 7]);          // default centre: C major
var classIdx = _defaultCenter.classIdx;
var rootPc = _defaultCenter.t;
var baseHue = 220, palSat = 0.62, palLum = 0.55;
var rankList = [];        // current-mode neighbour list for the current centre
var lastVoicing = [];
var lastRefPitch = 60;
var voiceSpan = 24;        // semitones the voicing spreads across; 0 = fully closed

// mode 0 = "Nearest" (neighborsOf: ranked by voice-leading distance across the whole 4095-chord
// universe). mode 1 = "Steps" (stepsNeighborsOf: elementary single-scale-step moves within a
// fixed scale, madmusicalscience.com/cs.html-style). The scale is just another (classIdx, root)
// pair, independent of the centre chord's own (classIdx, rootPc).
var mode = 0;
var _defaultScale = identifyPcs([0, 2, 4, 5, 7, 9, 11]);   // default scale: major
var scaleClassIdx = _defaultScale.classIdx;
var scaleRootPc = _defaultScale.t;
var minSize = 3, maxSize = 7;   // Steps-mode chord-size bounds: drop/add moves stay within these

function paletteOpts() { return { baseHue: baseHue, sat: palSat, lum: palLum }; }
function centerPcs() { return transposeSet(CLASSES[classIdx], rootPc); }
function scalePcs() { return transposeSet(CLASSES[scaleClassIdx], scaleRootPc); }

// the 12-point chromatic circle, used as the spiral view's implicit "scale" in Nearest mode
// (which has no scale concept of its own) -- every pc is trivially one of its own degrees, so
// degreeSetOf() against this always succeeds regardless of what the centre chord actually is.
var CHROMATIC12 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];

// Resolves the scale to treat `pcs` against for every scale-relative operation (the spiral view,
// scalar transposition): the configured Steps-mode scale if `pcs` fits it, else CHROMATIC12 --
// also used outright in Nearest mode, which has no scale of its own. Root/ChordIdx can be changed
// directly while in Steps mode to a chord that ISN'T a subset of the configured scale (unlike a
// Mode switch, which reseeds through reseedSteps() to guarantee a fit), so this fallback keeps
// every scale-relative feature working (rather than degreeSetOf() returning null) instead of
// degrading silently -- see the "View flips itself" fix this was introduced for.
function scaleAndDegreesFor(pcs) {
	var scale = (mode === 1) ? scalePcs() : CHROMATIC12;
	var degSet = degreeSetOf(pcs, scale);
	if (!degSet) { scale = CHROMATIC12; degSet = degreeSetOf(pcs, scale); }
	return { scale: scale, degSet: degSet };
}

// dispatches to the right neighbour generator for the current mode. Steps mode always resolves
// each candidate back through UNIVERSE_BY_MASK so the rest of the engine (recenterToRank,
// emitState, the jsui wire format) never needs to know which mode produced a node -- every
// concrete pc-set has exactly one (classIdx, t) identity regardless of how it was reached.
function computeRankList(pcs) {
	if (mode === 1) {
		var scale = scalePcs();
		var degSet = degreeSetOf(pcs, scale);
		if (degSet) {
			var raw = stepsNeighborsOf(scale, degSet, STEPS_DEPTH, paletteOpts(), minSize, maxSize);
			var out = [];
			for (var i = 0; i < raw.length; i++) {
				var u = UNIVERSE_BY_MASK[raw[i].mask];
				if (u) out.push({ node: u, dist: raw[i].dist, hue: raw[i].hue, color: raw[i].color });
			}
			return out;
		}
		// the current centre isn't a subset of the current scale (e.g. just switched modes into
		// an incompatible chord) -- fall back to Nearest so navigation never dead-ends silently.
	}
	return neighborsOf(pcs, bitmask(pcs), UNIVERSE, paletteOpts());
}

function voiceAndEmit(pcs) {
	if (lastVoicing.length) outlet.apply(this, [0, "noteoff"].concat(lastVoicing));
	var v = voiceChord(pcs, lastRefPitch, voiceSpan);
	outlet.apply(this, [0, "noteon"].concat(v));
	var sum = 0;
	for (var k = 0; k < v.length; k++) sum += v[k];
	lastRefPitch = v.length ? sum / v.length : lastRefPitch;
	lastVoicing = v;
}

// nudges the register up/down an octave and re-voices the CURRENT centre in place -- doesn't
// move the centre or touch rankList, just where the voicing sits.
function shiftRegister(delta) {
	lastRefPitch = Math.max(24, Math.min(108, lastRefPitch + delta));
	voiceAndEmit(centerPcs());
}

function emitState() {
	var pcs = centerPcs();
	var col = PC.harmonyToColor(pcs, paletteOpts(), 'oklab');
	var diss = Math.round(PC.dissonancePct(PC.intervalVector(pcs)) * 10) / 10;

	outlet.apply(this, [0, "center", mode, classIdx, rootPc, diss, col.r, col.g, col.b, pcs.length].concat(pcs));

	var lay = ringLayout(rankList, {});
	var rmsg = [0, "ringinfo", lay.rings.length];
	var r;
	for (r = 0; r < lay.rings.length; r++) rmsg.push(lay.rings[r].dist);
	outlet.apply(this, rmsg);

	// nodes: variable-width per node (ring, angleDeg, r, g, b, card, pc_0..pc_{card-1}, rank) --
	// pcs (not classIdx/t) so the jsui's spiral view can place same-cardinality neighbours on the
	// current spiral without needing its own copy of the 351-class table (see paintVoiceRings's
	// "shift ghost" markers in multichord_ui.js).
	var nmsg = [0, "nodes", lay.visible];
	for (r = 0; r < lay.rings.length; r++) {
		var ring = lay.rings[r];
		for (var n = 0; n < ring.nodes.length; n++) {
			var nd = ring.nodes[n];
			var npcs = nd.node.pcs;
			nmsg.push(r, nd.angleDeg, nd.color.r, nd.color.g, nd.color.b, npcs.length);
			for (var pi = 0; pi < npcs.length; pi++) nmsg.push(npcs[pi]);
			nmsg.push(nd.rank);
		}
	}
	outlet.apply(this, nmsg);

	// Feeds the jsui's alternate spiral view (madmusicalscience.com/cs.html-style -- one
	// continuous curve winding n times around an annulus, n = chord size, k = scale size),
	// which the user can pick independently of Mode via the View control.
	var sd = scaleAndDegreesFor(pcs), scale = sd.scale, degSet = sd.degSet;
	outlet.apply(this, [0, "scale", scale.length].concat(scale));
	outlet.apply(this, [0, "voices", degSet.length].concat(degSet));

	// The spiral view's clickable overlay: EVERY direct (one-hop) single-voice-shift move from
	// the current chord, each tagged with its rank in the FULL (uncapped) rankList so a click can
	// selectrank straight to it. Deliberately NOT sourced from the "nodes" message above -- that
	// list is capped/hue-decimated for Rings view's whole-graph overview (drop/add moves included,
	// distances out past 1 hop), which starves out exactly the small, same-cardinality, depth-1
	// set the spiral can actually place. Computed fresh here instead: shift-only elementaryMoves
	// (drop/add excluded by pinning min=max=current size) against the same scale/degSet as above,
	// each candidate looked up in rankList by mask.
	if (degSet.length) {
		var shifts = elementaryMoves(degSet, scale.length, degSet.length, degSet.length);
		var smsg = [0, "shiftmoves", shifts.length];
		for (var si = 0; si < shifts.length; si++) {
			var cand = shifts[si], diffIdx = 0;
			for (var ci = 0; ci < cand.length; ci++) if (cand[ci] !== degSet[ci]) diffIdx = ci;
			var candPcs = [];
			for (var di = 0; di < cand.length; di++) candPcs.push(scale[cand[di]]);
			var cmask = bitmask(candPcs), rank = -1;
			for (var ri = 0; ri < rankList.length; ri++) {
				if (rankList[ri].node.mask === cmask) { rank = ri; break; }
			}
			if (rank < 0) continue;   // depth-1 shifts are always in rankList; defensive only
			smsg.push(diffIdx, cand[diffIdx], rank);
		}
		smsg[2] = (smsg.length - 3) / 3;   // actual emitted count (may be < shifts.length if any lookup missed)
		outlet.apply(this, smsg);
	}
}

// rebuilds the neighbour list (mode-dependent) against the CURRENT centre, revoices, and emits.
function recenter() {
	var pcs = centerPcs();
	rankList = computeRankList(pcs);
	voiceAndEmit(pcs);
	emitState();
}

// palette-only change: recolour the current rankList without moving the centre or the voicing.
function recolor() {
	rankList = computeRankList(centerPcs());
	emitState();
}

// Steps mode only: reset the centre to the scale's first `minSize` degrees -- an always-valid
// starting point (drop/add moves can grow it up to maxSize from there), used whenever the
// scale/size bounds change while already exploring in Steps.
function reseedSteps() {
	var scale = scalePcs();
	var k = Math.min(minSize, scale.length);
	var pcs = scale.slice(0, k).sort(function (a, b) { return a - b; });
	var u = UNIVERSE_BY_MASK[bitmask(pcs)];
	if (u) { classIdx = u.classIdx; rootPc = u.t; }
	recenter();
	outlet(0, "dialsync", 0);
}

function recenterToClass(fi, root) {
	classIdx = clampInt(fi, 0, CLASSES.length - 1);
	rootPc = mod12(root);
	recenter();
	outlet(0, "dialsync", 0);
}

function recenterToRank(idx) {
	if (!rankList.length) return;
	idx = clampInt(idx, 0, rankList.length - 1);
	var picked = rankList[idx].node;
	classIdx = picked.classIdx;
	rootPc = picked.t;
	recenter();
}

// Scalar transposition (Tymoczko, A Geometry of Music §4.2): shift EVERY voice by the same
// number of scale-steps at once, preserving the chord's shape/position relative to the scale --
// unlike Nav/shift-ghosts, which move to a nearby chord that may not share the same shape at all.
// Uses whatever scale scaleAndDegreesFor() resolves (no separate scale concept). Shifting every
// degree by the same delta mod scaleLen is a bijection on the scale's own distinct pcs, so the
// result is guaranteed to be a valid, already-a-member-of-the-universe pc-set.
function scalarTranspose(delta) {
	var sd = scaleAndDegreesFor(centerPcs());
	var scaleLen = sd.scale.length;
	var newPcs = [];
	for (var i = 0; i < sd.degSet.length; i++) {
		var nd = ((sd.degSet[i] + delta) % scaleLen + scaleLen) % scaleLen;
		newPcs.push(sd.scale[nd]);
	}
	newPcs.sort(function (a, b) { return a - b; });
	var u = UNIVERSE_BY_MASK[bitmask(newPcs)];
	if (!u) return;   // defensive only -- see comment above, this shouldn't be reachable
	classIdx = u.classIdx;
	rootPc = u.t;
	recenter();
	outlet(0, "dialsync", 0);
}
function scalarup() { scalarTranspose(1); }
function scalardown() { scalarTranspose(-1); }

function setroot(v) { recenterToClass(classIdx, v); }
function setchordidx(v) { recenterToClass(v, rootPc); }
function dial(v) { recenterToRank(v); }
function selectrank(v) {
	if (!rankList.length) return;
	var idx = clampInt(v, 0, rankList.length - 1);
	recenterToRank(idx);
	outlet(0, "dialsync", idx);
}
function sethuec(v) { v = Number(v); if (isFinite(v)) { baseHue = mod360(v); recolor(); } }
function setpalsat(v) { v = Number(v); if (isFinite(v)) { palSat = clamp01(v); recolor(); } }
function setpallum(v) { v = Number(v); if (isFinite(v)) { palLum = clamp01(v); recolor(); } }
function setspan(v) { v = Number(v); if (isFinite(v)) { voiceSpan = Math.max(0, Math.min(48, v)); voiceAndEmit(centerPcs()); } }
function regup() { shiftRegister(12); }
function regdown() { shiftRegister(-12); }

// mode 1 = Steps. Only reseeds to the scale's first `minSize` degrees when the CURRENT centre
// doesn't already fit the (possibly just-restored) scale -- so flipping modes on loadbang restore
// reproduces exactly the saved state instead of discarding it, while flipping modes interactively
// mid-session still falls back gracefully if the current chord makes no sense in the new scale.
function setmode(v) {
	mode = clampInt(v, 0, 1);
	if (mode === 1 && !degreeSetOf(centerPcs(), scalePcs())) reseedSteps();
	else { recenter(); outlet(0, "dialsync", 0); }
}
function setscaleidx(v) { scaleClassIdx = clampInt(v, 0, CLASSES.length - 1); if (mode === 1) reseedSteps(); }
function setscaleroot(v) { scaleRootPc = mod12(v); if (mode === 1) reseedSteps(); }
function setminsize(v) {
	minSize = clampInt(v, 1, 12);
	if (minSize > maxSize) maxSize = minSize;
	if (mode === 1) reseedSteps();
}
function setmaxsize(v) {
	maxSize = clampInt(v, 1, 12);
	if (maxSize < minSize) minSize = maxSize;
	if (mode === 1) reseedSteps();
}

function bang() { if (!rankList.length) recenter(); else emitState(); }

// ================================================================================================
// node --check harness
// ================================================================================================

if (typeof require !== 'undefined' && typeof process !== 'undefined') {
	(function () {
		var failures = 0;
		function eq(got, want, label) {
			if (got !== want) { console.error('FAIL ' + label + ': got ' + got + ', want ' + want); failures++; }
		}
		function ok(cond, label) {
			if (!cond) { console.error('FAIL ' + label); failures++; }
		}

		function checkClasses() {
			var f0 = failures;
			var classes = buildClasses();
			eq(classes.length, 351, '351 Forte Tn-classes');
			eq(classes[0].join(','), '0', 'the single-note class canonicalises to [0]');
			if (failures === f0) console.log('OK   checkClasses: buildClasses -> 351 canonical Tn-classes.');
		}

		function checkUniverse() {
			var f0 = failures;
			var classes = buildClasses();
			var universe = buildUniverse(classes);
			eq(universe.length, 4095, 'universe covers every nonempty 12-bit mask exactly once');
			var seen = {}, dup = false;
			for (var i = 0; i < universe.length; i++) {
				if (seen[universe[i].mask]) dup = true;
				seen[universe[i].mask] = true;
			}
			ok(!dup, 'no duplicate masks in the universe');
			// round-trip: find [0,4,7]'s entry, confirm its (classIdx, t) reproduces it
			var target = [0, 4, 7], tmask = bitmask(target), found = null;
			for (i = 0; i < universe.length; i++) if (universe[i].mask === tmask) { found = universe[i]; break; }
			ok(!!found, '[0,4,7] is present in the universe');
			if (found) {
				var back = transposeSet(classes[found.classIdx], found.t);
				eq(back.join(','), target.join(','), 'universe entry round-trips through transposeSet');
			}
			if (failures === f0) console.log('OK   checkUniverse: 4095 unique masks, round-trips through (classIdx, t).');
		}

		// Regression: identifyPcs() must find the right (classIdx, t) at ANY transposition, not
		// just when the input happens to already be its class's own canonical rotation. [0,4,7]
		// passes even a naive t=0-only bitmask match by luck; the major scale does not -- an
		// earlier version of this function silently fell back to (0,0) for it.
		function checkIdentifyPcs() {
			var f0 = failures;
			function roundTrips(pcs, label) {
				var id = identifyPcs(pcs);
				var back = transposeSet(CLASSES[id.classIdx], id.t);
				eq(back.join(','), pcs.slice().sort(function (a, b) { return a - b; }).join(','), label);
			}
			roundTrips([0, 4, 7], 'identifyPcs round-trips a major triad');
			roundTrips([0, 2, 4, 5, 7, 9, 11], 'identifyPcs round-trips the major scale (not its own canonical rotation)');
			if (failures === f0) console.log('OK   checkIdentifyPcs: (classIdx, t) lookup round-trips even when the input is not the canonical rotation.');
		}

		function checkCircDist() {
			var f0 = failures;
			eq(circDist(11, 0), 1, 'pc 11 and pc 0 wrap to distance 1');
			eq(circDist(0, 0), 0, 'self distance 0');
			eq(chordDistanceCircular([0, 4, 7], [0, 4, 7]), 0, 'identical chords -> distance 0');
			eq(chordDistanceCircular([0, 4, 7], [0, 3, 8]),
				chordDistanceCircular([0, 3, 8], [0, 4, 7]), 'chordDistanceCircular is symmetric');
			eq(chordDistanceCircular([0, 4, 7], [0, 4, 7, 10]), 2,
				'adding the 7th (pc10, nearest existing tone is 0 at circular distance 2) costs 2');
			if (failures === f0) console.log('OK   checkCircDist: circular voice-leading distance, wraps and handles mismatched cardinality.');
		}

		function checkStepsNeighbors() {
			var f0 = failures;
			var major = [0, 2, 4, 5, 7, 9, 11];   // C major, scale length 7
			eq(degreeSetOf([0, 4, 7], major).join(','), '0,2,4', 'root-position triad -> scale degrees 0,2,4');
			eq(degreeSetOf([0, 1, 7], major), null, 'a pc outside the scale (1) -> not a valid degree set');

			// bounded to exactly size 3 (minSize=maxSize=3): add/drop are excluded, only shift moves.
			// [0,2,4]: every voice has empty degrees on both sides -- all 6 shift candidates are valid
			var spread = elementaryMoves([0, 2, 4], 7, 3, 3);
			eq(spread.length, 6, 'size-locked: no adjacent voices -> all 2*3 shift candidates are collision-free');
			// [0,1,2]: adjacent voices -- 4 of the 6 shift candidates collide, only 2 survive
			var cluster = elementaryMoves([0, 1, 2], 7, 3, 3);
			eq(cluster.length, 2, 'size-locked: adjacent degrees block collisions, leaving only the outward moves');
			var dupFree = true;
			for (var i = 0; i < spread.length; i++) if (spread[i].length !== 3 || spread[i][0] === spread[i][1] || spread[i][1] === spread[i][2]) dupFree = false;
			ok(dupFree, 'every shift move keeps 3 distinct occupied degrees');

			// unbounded (default minSize=1, maxSize=scaleLen=7): add/drop join the 6 shift moves --
			// 3 drops (remove each occupied degree) + 4 adds (fill each of the 4 unoccupied degrees)
			var free = elementaryMoves([0, 2, 4], 7);
			eq(free.length, 13, 'default bounds add 3 drop-a-voice + 4 add-a-voice moves to the 6 shifts');
			var sizes = free.map(function (d) { return d.length; });
			eq(sizes.filter(function (s) { return s === 2; }).length, 3, 'exactly 3 neighbours drop to a dyad');
			eq(sizes.filter(function (s) { return s === 4; }).length, 4, 'exactly 4 neighbours grow to a tetrad');
			eq(sizes.filter(function (s) { return s === 3; }).length, 6, 'the 6 shift moves keep the same size');

			// boundary respect: at minSize, no drop moves; at maxSize, no add moves
			var atMin = elementaryMoves([0, 2, 4], 7, 3, 5);
			ok(atMin.every(function (d) { return d.length >= 3; }), 'at minSize=3, nothing shrinks below 3');
			var atMax = elementaryMoves([0, 2, 4], 7, 1, 3);
			ok(atMax.every(function (d) { return d.length <= 3; }), 'at maxSize=3, nothing grows past 3');

			var opts = { baseHue: 220, sat: 0.62, lum: 0.55 };
			var one = stepsNeighborsOf(major, [0, 2, 4], 1, opts, 3, 3);
			eq(one.length, 6, 'size-locked depth-1 BFS returns exactly the 6 collision-free shift moves');
			ok(one.every(function (n) { return n.dist === 1; }), 'every depth-1 neighbour is 1 hop away');
			var deeper = stepsNeighborsOf(major, [0, 2, 4], 3, opts, 3, 3);
			ok(deeper.length > one.length, 'a deeper BFS finds strictly more (2- and 3-hop) neighbours');
			ok(deeper.every(function (n) { return n.degreeSet.join(',') !== '0,2,4'; }), 'the starting chord itself is never returned as its own neighbour');
			var modulating = stepsNeighborsOf(major, [0, 2, 4], 2, opts, 2, 4);
			ok(modulating.some(function (n) { return n.degreeSet.length !== 3; }), 'with a [2,4] size range, exploration reaches differently-sized chords');
			if (failures === f0) console.log('OK   checkStepsNeighbors: shift/drop/add moves, size bounds respected, BFS depth-limited.');
		}

		function checkRingLayout() {
			var f0 = failures;
			// synthetic ranked list: 3 nodes at dist 1 (different hues), 15 nodes at dist 2, dist 3..8 with 1 each
			var ranked = [], d, hue;
			function push(dist, h) {
				ranked.push({ node: { mask: ranked.length + 1, classIdx: 0, t: 0 }, dist: dist, hue: h, color: { r: 0.5, g: 0.5, b: 0.5 } });
			}
			push(1, 10); push(1, 200); push(1, 100);
			for (hue = 0; hue < 15; hue++) push(2, hue * 24);
			for (d = 3; d <= 8; d++) push(d, 0);
			var lay = ringLayout(ranked, {});
			ok(lay.rings.length <= RINGS_MAX, 'ringLayout caps at RINGS_MAX distinct distances');
			eq(lay.rings.length, RINGS_MAX, 'exactly RINGS_MAX rings present in this synthetic set');
			for (var r = 0; r < lay.rings.length; r++) {
				ok(lay.rings[r].nodes.length <= NODES_PER_RING_MAX, 'ring ' + r + ' respects NODES_PER_RING_MAX');
			}
			eq(lay.rings[1].nodes.length, NODES_PER_RING_MAX, 'the 15-node ring is decimated down to the cap');
			// within-ring nodes are hue-sorted
			var hues = lay.rings[0].nodes.map(function (n) { return n.angleDeg; });
			var sorted = hues.slice().sort(function (a, b) { return a - b; });
			eq(hues.join(','), sorted.join(','), 'nodes within a ring are placed in ascending hue order');
			if (failures === f0) console.log('OK   checkRingLayout: distance = ring index, hue-sorted placement, capped + decimated.');
		}

		function checkVoiceChord() {
			var f0 = failures;
			// span=0: every note targets the same ref (60). pc7's nearest octave is 55 (|55-60|=5),
			// not 67 (|67-60|=7), so the triad voices as 55/60/64, not root-position 60/64/67.
			var v1 = voiceChord([0, 4, 7], 60, 0);
			eq(v1.join(','), '55,60,64', 'span 0: every note voiced to its nearest octave around the same reference pitch');
			var mean1 = (v1[0] + v1[1] + v1[2]) / 3;
			var v2 = voiceChord([0, 4, 7], mean1, 0);
			eq(v2.join(','), v1.join(','), 'feeding back the mean stays in the same octave band (no drift) at span 0');
			// span 24: targets spread ref-12 .. ref .. ref+12, so the chord opens up instead of
			// clustering -- pc0->target48->48, pc4->target60->64, pc7->target72->67.
			var v3 = voiceChord([0, 4, 7], 60, 24);
			eq(v3.join(','), '48,64,67', 'span 24 spreads the same triad into an open voicing');
			if (!((v3[v3.length - 1] - v3[0]) > (v1[v1.length - 1] - v1[0]))) {
				console.error('FAIL a nonzero span should widen the voicing vs span 0'); failures++;
			}
			if (failures === f0) console.log('OK   checkVoiceChord: span 0 stays closed and stable; a nonzero span opens the voicing.');
		}

		function main() {
			checkClasses();
			checkUniverse();
			checkIdentifyPcs();
			checkCircDist();
			checkStepsNeighbors();
			checkRingLayout();
			checkVoiceChord();
			if (failures === 0) { console.log('ALL OK'); process.exitCode = 0; }
			else { console.error(failures + ' failure(s)'); process.exitCode = 1; }
		}

		if (process.argv.indexOf('--check') !== -1 && require.main === module) main();
		else if (require.main === module) console.error('usage: node forteseq/multichord.js --check');
	})();
}
