// forteseqwf.js -- standalone Well-Formed (Moment-of-Symmetry) rhythm generator. Deliberately NOT
// part of forteseq2.js: a WF voice's onsets generally don't land on any step grid (that's the
// entire point at irrational r), so it can't be read through voiceRhyPat/voiceSoundsAt the way
// the Euclidean per-voice rhythm is. This is a separate device that will output plain MIDI and
// reach FORTESEQ2 (or anything else) through forteseqhub.amxd's existing Enviar path, same as any
// other MIDI source -- zero coupling to the harmony engine, zero regression risk to golden.txt.
//
// Sources: Milne, Herff, Bulger, Sethares & Dean, "XronoMorph: Algorithmic Generation of Perfectly
// Balanced and Well-Formed Rhythms" (NIME 2016); Milne, "XronoMorph: Investigating Paths Through
// Rhythmic Space" (in The Oxford Handbook of Algorithmic Music, 2019); Milne & Dean,
// "Computational Creation and Morphing of Multilevel Rhythms by Control of Evenness", Computer
// Music Journal 40(1):35-53 (2016) -- the closed-form equations the first two papers both defer
// to. The onset-COUNT recursion is verified against the one worked numeric example the 2019
// chapter gives (Fig. 7), and the r-value recursion (below, in wfNextLevel) matches the CMJ
// paper's Equations 2 and 4 exactly -- it was originally derived here independently, before the
// CMJ paper was in hand, from the same stated construction rule and checked only by the
// subset-nesting property; see checkFig7Example() and checkRefinement() for that verification,
// which still stands as the deeper reason to trust it.

// --- base word: maximally-even placement of m long (L) markers among m+n slots -----------------

// Bjorklund's algorithm, duplicated from forteseq2.js on purpose (see header) rather than shared,
// so this file has zero dependency on the engine. Written out rather than taken as the one-line
// Bresenham shortcut, because floor(i*k/n) only agrees with it some of the time -- see the
// comment at forteseq2.js's own copy for the E(5,8) counterexample.
function bjorklund(k, n) {
	var i, out = [];
	if (n < 1) return out;
	if (k <= 0) { for (i = 0; i < n; i++) out.push(0); return out; }
	if (k >= n) { for (i = 0; i < n; i++) out.push(1); return out; }
	var a = [], b = [];
	for (i = 0; i < k; i++) a.push([1]);
	for (i = 0; i < n - k; i++) b.push([0]);
	while (b.length > 1) {
		var m = Math.min(a.length, b.length);
		var na = [], nb = [];
		for (i = 0; i < m; i++) na.push(a[i].concat(b[i]));
		var rest = (a.length > m) ? a : b;
		for (i = m; i < rest.length; i++) nb.push(rest[i]);
		a = na;
		b = nb;
	}
	for (i = 0; i < a.length; i++) out = out.concat(a[i]);
	for (i = 0; i < b.length; i++) out = out.concat(b[i]);
	return out;
}

// bjorklund(m, m+n) is exactly the Christoffel/maximally-even word the papers construct via a
// cutting sequence: m markers spread as evenly as possible among m+n slots, no rest cells (every
// slot is either a long or a short interonset interval, unlike a Euclidean onset/silence pattern).
function wfBaseWord(m, n) {
	var pat = bjorklund(m, m + n);
	var word = [];
	for (var i = 0; i < pat.length; i++) word.push(pat[i] ? 'L' : 'S');
	return word;
}

function wfBaseLevel(m, n, r) {
	return { word: wfBaseWord(m, n), m: m, n: n, r: r };
}

// --- one hierarchy step -------------------------------------------------------------------------

// r=1 means L=s: every interval is already identical, so there is nothing left for "long" vs
// "short" to mean and the split formulas below divide by (r-1)=0. The papers are explicit that
// the hierarchy simply terminates at such a level, not that it degenerates gracefully.
function wfIsIsochronous(level, eps) {
	if (eps === undefined) eps = 1e-9;
	return Math.abs(level.r - 1) < eps;
}

// Standard Sturmian/Christoffel morphism (Berstel et al.), applied per-symbol: r>=2 splits every
// L into a new L+S (S unchanged); r<2 splits every L into a new L+S AND relabels every old S as a
// new L. `reverse` is the L/R control: it only flips which half of a split comes first (L->"SL"
// instead of "LS"), so it changes onset order/timing but never the resulting (m,n) counts or r'.
// The (m,n) and r updates below are exactly Milne & Dean's Equations 2 and 4 (CMJ 40(1):35-53,
// 2016, using their j/k/r_i notation for our m/n/r) -- confirmed after the fact, see file header.
function wfNextLevel(level, reverse) {
	if (wfIsIsochronous(level)) {
		throw new Error('wfNextLevel: level is isochronous (r=1) -- the hierarchy terminates here, see wfHierarchy');
	}
	var word = level.word, m = level.m, n = level.n, r = level.r;
	var newWord = [];
	var mNew, nNew, rNew;
	var i;
	if (r >= 2) {
		for (i = 0; i < word.length; i++) {
			if (word[i] === 'L') {
				if (reverse) { newWord.push('S'); newWord.push('L'); }
				else { newWord.push('L'); newWord.push('S'); }
			} else {
				newWord.push('S');
			}
		}
		mNew = m; nNew = m + n; rNew = r - 1;
	} else {
		for (i = 0; i < word.length; i++) {
			if (word[i] === 'L') {
				if (reverse) { newWord.push('S'); newWord.push('L'); }
				else { newWord.push('L'); newWord.push('S'); }
			} else {
				newWord.push('L');
			}
		}
		mNew = m + n; nNew = m; rNew = 1 / (r - 1);
	}
	return { word: newWord, m: mNew, n: nNew, r: rNew };
}

// Builds up to `levels` levels (level 0 = base) -- fewer if an earlier level turns out isochronous,
// per the papers ("once a level ... is perfectly even it cannot be split any further and the
// hierarchy terminates"). reverse[i-1] is the L/R flag used for the split that produces level i.
function wfHierarchy(m, n, r, levels, reverse) {
	var out = [wfBaseLevel(m, n, r)];
	for (var i = 1; i < levels; i++) {
		if (wfIsIsochronous(out[i - 1])) break;
		out.push(wfNextLevel(out[i - 1], !!(reverse && reverse[i - 1])));
	}
	return out;
}

// How the r-recursion ends, from a base (m, n, r) -- forward-iterating the r-map (wfNextLevel's
// Eq. 2/4 on the counts alone, no word needed) until r hits 1 (isochronous) or a step budget
// runs out. Word length starts at m+n and grows by m each step (every L splits, every S stays),
// so this also yields the pulse count of the isochronous grid. `maxSteps` caps the metallic /
// generic-irrational cases, where r cycles or wanders and exactly 1 is never reached.
//   -> { level, pulses, capped }
//      level  : 0-based hierarchy level where r == 1 (0 = the base is already isochronous), or -1
//      pulses : onset count of that isochronous level, or -1
//      capped : true if the budget ran out first -- "deeply non-isochronous"
function isochronyOutlook(m, n, r, maxSteps) {
	if (maxSteps === undefined) maxSteps = 64;
	if (Math.abs(r - 1) < 1e-9) return { level: 0, pulses: m + n, capped: false };
	for (var step = 1; step <= maxSteps; step++) {
		var len = 2 * m + n;                          // this step's word length
		if (r >= 2) { n = m + n; r = r - 1; }         // (m, n, r) -> (m, m+n, r-1)
		else { var nm = m + n; r = 1 / (r - 1); n = m; m = nm; }   // -> (m+n, m, 1/(r-1))
		if (!isFinite(r)) return { level: -1, pulses: -1, capped: true };
		if (Math.abs(r - 1) < 1e-9) return { level: step, pulses: len, capped: false };
	}
	return { level: -1, pulses: -1, capped: true };
}

// --- durations and onset times, per level, independent of every other level --------------------

// mL + ns = d (d = period duration, from the tempo control) and r = L/s together pin down L and s
// uniquely for this level's own (m, n, r) -- no dependency on any other level's numbers.
function wfDurations(level, d) {
	var m = level.m, n = level.n, r = level.r;
	var s = d / (m * r + n);
	var L = r * s;
	var out = [];
	for (var i = 0; i < level.word.length; i++) out.push(level.word[i] === 'L' ? L : s);
	return out;
}

// Onset times within one period, starting at 0. word.length onsets; the final onset's own
// duration is not included in the returned array (it is the gap back to the next period's 0).
function wfOnsets(level, d) {
	var durs = wfDurations(level, d);
	var onsets = [];
	var t = 0;
	for (var i = 0; i < durs.length; i++) { onsets.push(t); t += durs[i]; }
	return onsets;
}

// --- Universal / Complementary --------------------------------------------------------------

function approxIncludes(arr, x, eps) {
	for (var i = 0; i < arr.length; i++) if (Math.abs(arr[i] - x) < eps) return true;
	return false;
}

// Onsets in `levelOnsets` that are NOT present in `prevOnsets` (same d, adjacent levels).
// Universal mode plays levelOnsets in full; Complementary mode plays only what this returns --
// the "new" events this level adds. eps defaults to a period-relative tolerance because onset
// times accumulate float error over many additions; an absolute epsilon would be wrong at very
// different d scales.
function wfNewOnsets(levelOnsets, prevOnsets, d, eps) {
	if (eps === undefined) eps = d * 1e-9;
	var out = [];
	for (var i = 0; i < levelOnsets.length; i++) {
		if (!approxIncludes(prevOnsets, levelOnsets[i], eps)) out.push(levelOnsets[i]);
	}
	return out;
}

// --- metallic ratios: the r-values that never approach isochrony at any level ------------------

// M_k = (k + sqrt(k^2+4)) / 2. k=1 golden (phi), k=2 silver (delta), k=3 bronze (sigma); the
// family continues. Each M_k is a fixed point of the level recursion with period k (see
// checkMetallicRatios()): starting there, r cycles through k values forever instead of ever
// settling toward 1 (isochrony).
function metallicRatio(k) {
	return (k + Math.sqrt(k * k + 4)) / 2;
}

// --- phi_s snap values: Stern-Brocot "deeply nonisochronous" r0 values (Milne & Dean 2016, CMJ
// 40(1):35-53, crediting Wilson 1997) -------------------------------------------------------------
// A DIFFERENT family from metallicRatio() above: metallicRatio(k) cycles through k distinct
// r-values forever. A phi_s value instead settles onto a SINGLE value -- phi itself -- but only
// starting at hierarchy level s; levels 0..s-1 are ordinary, non-repeating r-values first. The
// paper states r0 = (a*phi+c)/(b*phi+d) for "adjacent members a/b, c/d from level s and s+1 of the
// Stern-Brocot tree" but does not give the enumeration algorithm (which pair, how many per s).
// That was worked out and verified here by simulation against wfNextLevel itself (not just
// algebra): since r stays >=1 throughout this file's convention, the relevant part of the tree is
// the branch rooted at the boundary pair (1/1, 1/0), and the pairing that actually locks onto phi
// (confirmed for tree-depths 1-5) is a Stern-Brocot node together with its DIRECT PARENT -- not
// "whichever of the two fractions bounding it is numerically smaller", which was also tried and
// does not produce consistent lock-in. A node at tree-depth D locks in at hierarchy level s = D+1
// (a real, verified offset, not D itself). Roughly half of the resulting pairs have a/b > c/d,
// contradicting the paper's literal "a/b < c/d" -- forcing that ordering was tried too and breaks
// the lock-in, confirmed by simulation, so this file trusts the parent/child construction (checked
// directly against the recursion) over the literal inequality in the paper's prose.
//
// s=0 is the degenerate case r0=phi itself (the root boundary, not a real tree node) and s=1 has
// no valid member at all -- the family only becomes non-empty at s=2, with 2^(s-2) members per s.

// sbTreeNode(D): the D-th-depth-first Stern-Brocot node value on the >=1 branch, walked by always
// descending toward the "left" child (mediant of the running boundary's low end and the previous
// node), together with its direct parent -- one concrete node per depth, sufficient to build every
// (parent, node) pair actually needed by sbPhiPairs via bit-path traversal below.
function sbNodeAtPath(bits) {
	// bits: array of 0/1, one per tree level below the root, 0 = descend toward lo, 1 = toward hi.
	// Returns {parent: {a,b}, node: {c,d}} for the node reached by following that path from the
	// boundary pair (1/1, 1/0).
	var lo = { a: 1, b: 1 }, hi = { a: 1, b: 0 };
	var parent = null, node = { a: 1, b: 1 };
	for (var i = 0; i < bits.length; i++) {
		var mediant = { a: lo.a + hi.a, b: lo.b + hi.b };
		parent = node;
		node = mediant;
		if (bits[i] === 0) { hi = node; } else { lo = node; }
	}
	return { parent: parent, node: node };
}

// sbPhiPairs(s): every {a,b,c,d} pair (parent a/b, node c/d) whose weighted mediant locks the
// r-recursion onto phi starting exactly at hierarchy level s (0-indexed, matching wfHierarchy's
// own array index). Enumerates all 2^(s-2) tree-depth-(s-1) nodes via their binary path.
function sbPhiPairs(s) {
	if (s < 2) return [];
	var depth = s - 1;                    // tree depth D that locks in at hierarchy level s = D+1
	var count = Math.pow(2, depth - 1);   // 2^(D-1) distinct nodes at depth D
	var out = [];
	for (var i = 0; i < count; i++) {
		// D-1 bits actually distinguish the 2^(D-1) sibling nodes at depth D; a final, arbitrary
		// trailing bit is required only to make sbNodeAtPath walk the full D steps to reach that
		// depth -- it does not affect which node is reached, since a node's own value is fixed
		// once the boundary state going INTO its mediant step is fixed by the earlier D-1 bits.
		var bits = [];
		for (var b = depth - 2; b >= 0; b--) bits.push((i >> b) & 1);
		bits.push(0);
		var pn = sbNodeAtPath(bits);
		out.push({ a: pn.parent.a, b: pn.parent.b, c: pn.node.a, d: pn.node.b });
	}
	return out;
}

// phiSnapValue(a,b,c,d): the actual r0 for one Stern-Brocot pair. Reuses metallicRatio(1) for phi
// rather than a separate constant, since that value is already independently verified to 1e-12 by
// checkMetallicRatios().
function phiSnapValue(a, b, c, d) {
	var phi = metallicRatio(1);
	return (a * phi + c) / (b * phi + d);
}

// phiSnapValues(s): the numeric r0 candidates for level s, sorted ascending -- the same role
// Milne's MeanTimes/XronoMorph give these values as markers above the r-slider.
function phiSnapValues(s) {
	return sbPhiPairs(s).map(function (p) { return phiSnapValue(p.a, p.b, p.c, p.d); }).sort(function (x, y) { return x - y; });
}

// --- r-slider marker catalog: all four XronoMorph marker families, from the recursion -----------
//
// XronoMorph's r-slider carries four kinds of tick: `n` (a level, and every level above it, is
// isochronous -- a rational r), and `phi`/`delta`/`sigma` (the r-value of every higher level is
// pinned to the golden / silver / bronze section forever -- "deeply nonisochronous", never
// approaching an even pulse). In the app the `n` ticks are computed live from j/k/levels and the
// phi/delta/sigma ticks are a hard-wired bank of ~50 individual `expr` radicals. Both are exactly
// the INVERSE ORBIT of a target under this file's own one-step r-map, so we generate all four
// here from wfNextLevel's r-rule instead of transcribing a table -- and checkMarkers() below
// verifies every generated value forward against wfNextLevel itself.
//
// Forward r-map (wfNextLevel on r alone): r>=2 -> r-1 ; 1<r<2 -> 1/(r-1) ; r==1 terminates.
// Inverting it: a value t has predecessor t+1 (from the r>=2 branch, always valid here since
// t>=1 => t+1>=2) and, only when t>1, predecessor 1+1/t (from the 1<r<2 branch: r-1 = 1/t).
// 1+1/phi == phi exactly, so phi's 1+1/t predecessor is itself -- markerPredecessors drops any
// candidate equal to t so that self-loop doesn't spin.

function markerPredecessors(t) {
	var out = [t + 1];
	if (t > 1 + 1e-12) {
		var u = 1 + 1 / t;
		if (u > 1 + 1e-9 && Math.abs(u - t) > 1e-12) out.push(u);
	}
	return out;
}

// markerSeeds(): {value, family} for the orbit target of each family. `n` targets isochrony
// (r=1); the metallic families target their whole recursion cycle (phi is a 1-cycle, silver a
// 2-cycle {d, d-1}, bronze a 3-cycle {s, s-1, s-2}) -- reusing metallicRatio() so the constants
// stay defined in exactly one place.
function markerSeeds() {
	var d = metallicRatio(2), s = metallicRatio(3);
	return [
		{ value: 1, family: 'n' },
		{ value: metallicRatio(1), family: 'phi' },
		{ value: d, family: 'delta' }, { value: d - 1, family: 'delta' },
		{ value: s, family: 'sigma' }, { value: s - 1, family: 'sigma' }, { value: s - 2, family: 'sigma' }
	];
}

// generateMarkers(rMax, sMaxByFamily): breadth-first inverse iteration from every seed. A node
// reached in k inverse steps is an r0 whose forward orbit lands on that family's target after
// exactly k steps -- so its `level` (the hierarchy level at which it becomes / stays pinned) is
// k. Kept iff 1 < r <= rMax and level <= that family's cap. Deduped by r to 1e-9, keeping the
// smallest level (so "pinned at exactly this level, never earlier" holds -- checkMarkers asserts
// it). The seed value itself is level 0: emitted for phi/delta/sigma (phi, 1.414..., 1.303...
// really are slider ticks) but NOT for `n`, since r=1 is the degenerate isochronous point.
//
// Per-family caps because the families fill at very different rates: rationals want depth 5 to
// reproduce the slider's `n` ticks the user catalogued (1.2, 1.25, 1.286, ... 6.0), while the
// metallic inverse-trees double every level and are musically indistinct past depth ~3 -- the
// same principal-convergent depth XronoMorph's hand-built expr bank stops at.
function generateMarkers(rMax, sMaxByFamily) {
	var seen = {};          // r.toFixed(9) -> {r, family, level}
	var queue = [];
	var seeds = markerSeeds();
	var maxCap = 0;
	for (var f in sMaxByFamily) if (sMaxByFamily.hasOwnProperty(f) && sMaxByFamily[f] > maxCap) maxCap = sMaxByFamily[f];
	for (var i = 0; i < seeds.length; i++) {
		queue.push({ value: seeds[i].value, family: seeds[i].family, level: 0 });
	}
	for (var qi = 0; qi < queue.length; qi++) {
		var node = queue[qi];
		var cap = sMaxByFamily[node.family];
		if (cap === undefined) cap = maxCap;
		var key = node.value.toFixed(9);
		var emit = !(node.family === 'n' && node.level === 0) && node.level <= cap;
		if (node.value > 1 + 1e-9 && node.value <= rMax + 1e-9 && emit) {
			var prev = seen[key];
			if (!prev || node.level < prev.level) {
				seen[key] = { r: node.value, family: node.family, level: node.level };
			}
		}
		if (node.level >= cap) continue;
		var preds = markerPredecessors(node.value);
		for (var p = 0; p < preds.length; p++) {
			// Prune before enqueueing: the t+1 branch only ever grows, so once it passes rMax
			// nothing below it on that branch comes back. The 1+1/t branch stays in (1,2).
			if (preds[p] > rMax + 1e-9 && preds[p] >= node.value) continue;
			var pk = preds[p].toFixed(9);
			var seenAt = seen[pk];
			if (seenAt && seenAt.level <= node.level + 1) continue;
			queue.push({ value: preds[p], family: node.family, level: node.level + 1 });
		}
	}
	var list = [];
	for (var k in seen) if (seen.hasOwnProperty(k)) list.push(seen[k]);
	list.sort(function (a, b) { return a.r - b.r; });
	return list;
}

// One umenu item / one --dump-markers label: ascii, no spaces (a bare umenu `append` atom).
function markerLabel(mk) {
	return mk.family + '_' + mk.r.toFixed(3) + '_L' + mk.level;
}

function nearestMarker(v, markers) {
	var best = null, bestD = Infinity;
	for (var i = 0; i < markers.length; i++) {
		var d = Math.abs(markers[i].r - v);
		if (d < bestD) { bestD = d; best = markers[i]; }
	}
	return best;
}

// "phi L3" when v sits on a marker (within eps), else "-" -- the readout next to the R control.
function markerTagString(v, markers, eps) {
	if (eps === undefined) eps = 1e-6;
	var m = nearestMarker(v, markers);
	if (m && Math.abs(m.r - v) <= eps) return m.family + ' L' + m.level;
	return '-';
}

var MARKER_RMAX = 6.0;
var MARKER_SMAX = { n: 5, phi: 3, delta: 3, sigma: 3 };
var MARKERS = generateMarkers(MARKER_RMAX, MARKER_SMAX);

// --- config snapshot + interpolation: the shape a preset slot stores and a morph blends --------
//
// One plain object holds a complete WF setup. It is what storepreset() writes, what recallpreset()
// applies, and -- lerped -- what a morph feeds startCycle(). Keeping a single shape means one
// serializer, one clone, one interpolation table, instead of the field-by-field mirror that
// forteseq2's first preset store got wrong. vel/dur are here even though the device has no control
// for them yet: excluding them would just add a special case to every function below, and the
// same lerp serves recall at x=0/1 for free.
//
//   config = { r, period, beats, sync, m, n, levels,
//              on:[6], uc:[6], lr:[6], pitch:[6], vel:[6], dur:[6], __name? }

var CONFIG_SPEC = {
	r:      { kind: 'r' },
	period: { kind: 'cont', lo: 50,   hi: 60000 },
	beats:  { kind: 'cont', lo: 0.25, hi: 64 },
	sync:   { kind: 'bool' },
	m:      { kind: 'int',  lo: 1, hi: 64 },
	n:      { kind: 'int',  lo: 0, hi: 64 },
	levels: { kind: 'int',  lo: 1, hi: 6 },
	on:     { kind: 'boolA' },
	uc:     { kind: 'boolA' },
	lr:     { kind: 'boolA' },
	pitch:  { kind: 'intA', lo: 0, hi: 127 },
	vel:    { kind: 'intA', lo: 1, hi: 127 },
	dur:    { kind: 'intA', lo: 1, hi: 60000 },

	// --- probability + per-step (Probfier-style decimation) layer ---
	gprob:  { kind: 'int', lo: 0, hi: 100 },     // global probability %
	lprob:  { kind: 'intA', lo: 0, hi: 100 },    // per-level probability %, len 6
	lstep:  { kind: 'intA', lo: 1, hi: 8 },      // per-level "keep 1 of every N" of that level's own onsets, len 6
	seed:   { kind: 'pick' },                    // RNG seed -- NEVER lerped: a blended seed is meaningless

	// --- articulation / accent layer (ported from forteseq2's group model) ---
	arton:  { kind: 'bool' },
	acyc:   { kind: 'int', lo: 1, hi: 16 },      // accent-grid read length
	atie:   { kind: 'bool' },                    // 1 -> read length follows m+n instead of acyc
	aeuc:   { kind: 'bool' },                    // Euclidean grid generator on
	aeuck:  { kind: 'int', lo: 0, hi: 16 },
	aeucr:  { kind: 'int', lo: 0, hi: 15 },
	agrid:  { kind: 'boolA', len: 16 },          // the 16 accent cells
	aphase: { kind: 'intA', lo: 0, hi: 15 },     // per-level offset into the accent read, len 6
	nvmin:  { kind: 'int', lo: 1, hi: 127 },     // Normal group velocity band
	nvmax:  { kind: 'int', lo: 1, hi: 127 },
	nfig:   { kind: 'int', lo: 1, hi: 32 },      // Normal group figura (note-value denominator)
	nsil:   { kind: 'int', lo: 0, hi: 100 },     // Normal group silencio %
	avmin:  { kind: 'int', lo: 1, hi: 127 },     // Accent group
	avmax:  { kind: 'int', lo: 1, hi: 127 },
	afig:   { kind: 'int', lo: 1, hi: 32 },
	asil:   { kind: 'int', lo: 0, hi: 100 }
};

// The order fields are written to / read from a preset line. lr only carries 5 entries: the L/R
// flag is the split that PRODUCES the next level, and level 6 has no level 7 (mirrors the engine
// and the .amxd, which has no wf_lr6). p/vel/dur are the per-level pitch/velocity/duration.
var CONFIG_LINE_FIELDS = ['r', 'period', 'beats', 'sync', 'm', 'n', 'levels',
	'on1', 'on2', 'on3', 'on4', 'on5', 'on6',
	'uc1', 'uc2', 'uc3', 'uc4', 'uc5', 'uc6',
	'lr1', 'lr2', 'lr3', 'lr4', 'lr5',
	'p1', 'p2', 'p3', 'p4', 'p5', 'p6',
	'vel1', 'vel2', 'vel3', 'vel4', 'vel5', 'vel6',
	'dur1', 'dur2', 'dur3', 'dur4', 'dur5', 'dur6',
	'gprob', 'seed', 'arton', 'acyc', 'atie', 'aeuc', 'aeuck', 'aeucr',
	'nvmin', 'nvmax', 'nfig', 'nsil', 'avmin', 'avmax', 'afig', 'asil',
	'lprob1', 'lprob2', 'lprob3', 'lprob4', 'lprob5', 'lprob6',
	'lstep1', 'lstep2', 'lstep3', 'lstep4', 'lstep5', 'lstep6',
	'aphase1', 'aphase2', 'aphase3', 'aphase4', 'aphase5', 'aphase6',
	'agrid1', 'agrid2', 'agrid3', 'agrid4', 'agrid5', 'agrid6', 'agrid7', 'agrid8',
	'agrid9', 'agrid10', 'agrid11', 'agrid12', 'agrid13', 'agrid14', 'agrid15', 'agrid16'];

function defaultConfig() {
	return {
		r: 1.5, period: 2000, beats: 4, sync: 0, m: 3, n: 5, levels: 2,
		on: [1, 0, 0, 0, 0, 0], uc: [0, 0, 0, 0, 0, 0], lr: [0, 0, 0, 0, 0, 0],
		pitch: [60, 62, 64, 65, 67, 69],
		vel: [100, 100, 100, 100, 100, 100],
		dur: [100, 100, 100, 100, 100, 100],
		gprob: 100, lprob: [100, 100, 100, 100, 100, 100],
		lstep: [1, 1, 1, 1, 1, 1], seed: 1,
		arton: 0, acyc: 4, atie: 0, aeuc: 0, aeuck: 4, aeucr: 0,
		agrid: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
		aphase: [0, 0, 0, 0, 0, 0],
		nvmin: 55, nvmax: 80, nfig: 16, nsil: 0,
		avmin: 95, avmax: 115, afig: 8, asil: 0
	};
}

function cloneConfig(c) {
	var out = { r: c.r, period: c.period, beats: c.beats, sync: c.sync, m: c.m, n: c.n, levels: c.levels,
		on: c.on.slice(), uc: c.uc.slice(), lr: c.lr.slice(),
		pitch: c.pitch.slice(), vel: c.vel.slice(), dur: c.dur.slice(),
		gprob: c.gprob, lprob: c.lprob.slice(), lstep: c.lstep.slice(), seed: c.seed,
		arton: c.arton, acyc: c.acyc, atie: c.atie, aeuc: c.aeuc, aeuck: c.aeuck, aeucr: c.aeucr,
		agrid: c.agrid.slice(), aphase: c.aphase.slice(),
		nvmin: c.nvmin, nvmax: c.nvmax, nfig: c.nfig, nsil: c.nsil,
		avmin: c.avmin, avmax: c.avmax, afig: c.afig, asil: c.asil };
	if (c.__name !== undefined) out.__name = c.__name;
	return out;
}

function lerp(a, b, x) { return a + (b - a) * x; }

// r morph: default path is a straight line in XronoMorph's own slider coordinate t = (r-1)/r
// (r = 1 -> t = 0, r -> inf -> t -> 1, r = 2 -> t = 0.5), which keeps the sweep perceptually even
// the way dragging the r-slider does. `linear` takes the blunt straight line in r instead.
function lerpR(rA, rB, x, linear) {
	if (linear) return Math.max(1, lerp(rA, rB, x));
	var tA = (rA - 1) / rA, tB = (rB - 1) / rB;
	var t = Math.min(lerp(tA, tB, x), 1 - 1e-9);
	return Math.max(1, 1 / (1 - t));
}

function clampNum(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
function clampRoundInt(v, lo, hi) { v = Math.round(v); return v < lo ? lo : (v > hi ? hi : v); }

// The interpolation table. x <= 0 is config a untouched, x >= 1 is config b untouched (so a morph
// docked at either end plays that slot exactly, and recall reuses this at x = 0/1). In between:
// continuous fields lerp, integer fields round the lerp, and every boolean -- sync, the per-level
// On/U-C/L-R flags -- flips at the halfway point.
function lerpConfig(a, b, x, rLinear) {
	if (x <= 0) return cloneConfig(a);
	if (x >= 1) return cloneConfig(b);
	var out = {};
	for (var key in CONFIG_SPEC) {
		if (!CONFIG_SPEC.hasOwnProperty(key)) continue;
		var spec = CONFIG_SPEC[key], i, n;
		if (spec.kind === 'r') {
			out.r = lerpR(a.r, b.r, x, rLinear);
		} else if (spec.kind === 'cont') {
			out[key] = clampNum(lerp(a[key], b[key], x), spec.lo, spec.hi);
		} else if (spec.kind === 'int') {
			out[key] = clampRoundInt(lerp(a[key], b[key], x), spec.lo, spec.hi);
		} else if (spec.kind === 'bool') {
			out[key] = (x < 0.5 ? a[key] : b[key]) ? 1 : 0;
		} else if (spec.kind === 'pick') {
			// no blend: a seed halfway between two seeds is not "between" the two sequences.
			out[key] = (x < 0.5) ? a[key] : b[key];
		} else if (spec.kind === 'boolA') {
			out[key] = [];
			n = spec.len || 6;
			for (i = 0; i < n; i++) out[key].push((x < 0.5 ? a[key][i] : b[key][i]) ? 1 : 0);
		} else if (spec.kind === 'intA') {
			out[key] = [];
			n = spec.len || 6;
			for (i = 0; i < n; i++) out[key].push(clampRoundInt(lerp(a[key][i], b[key][i], x), spec.lo, spec.hi));
		}
	}
	return out;
}

// One preset-file line, minus the leading "<slot>\t" and any "__name=" (savepresets adds those,
// same as forteseq2). configFromParts rebuilds a config from the tab fields, starting from
// defaultConfig() so a short line (older format, hand-edited) just keeps defaults for what it
// omits, and unknown "key=value" fields are ignored.
function configToLine(c) {
	var f = [];
	f.push('r=' + c.r, 'period=' + c.period, 'beats=' + c.beats, 'sync=' + (c.sync ? 1 : 0),
		'm=' + c.m, 'n=' + c.n, 'levels=' + c.levels);
	for (var i = 0; i < 6; i++) f.push('on' + (i + 1) + '=' + (c.on[i] ? 1 : 0));
	for (i = 0; i < 6; i++) f.push('uc' + (i + 1) + '=' + (c.uc[i] ? 1 : 0));
	for (i = 0; i < 5; i++) f.push('lr' + (i + 1) + '=' + (c.lr[i] ? 1 : 0));
	for (i = 0; i < 6; i++) f.push('p' + (i + 1) + '=' + c.pitch[i]);
	for (i = 0; i < 6; i++) f.push('vel' + (i + 1) + '=' + c.vel[i]);
	for (i = 0; i < 6; i++) f.push('dur' + (i + 1) + '=' + c.dur[i]);
	f.push('gprob=' + c.gprob, 'seed=' + c.seed,
		'arton=' + (c.arton ? 1 : 0), 'acyc=' + c.acyc, 'atie=' + (c.atie ? 1 : 0),
		'aeuc=' + (c.aeuc ? 1 : 0), 'aeuck=' + c.aeuck, 'aeucr=' + c.aeucr,
		'nvmin=' + c.nvmin, 'nvmax=' + c.nvmax, 'nfig=' + c.nfig, 'nsil=' + c.nsil,
		'avmin=' + c.avmin, 'avmax=' + c.avmax, 'afig=' + c.afig, 'asil=' + c.asil);
	for (i = 0; i < 6; i++) f.push('lprob' + (i + 1) + '=' + c.lprob[i]);
	for (i = 0; i < 6; i++) f.push('lstep' + (i + 1) + '=' + c.lstep[i]);
	for (i = 0; i < 6; i++) f.push('aphase' + (i + 1) + '=' + c.aphase[i]);
	for (i = 0; i < 16; i++) f.push('agrid' + (i + 1) + '=' + (c.agrid[i] ? 1 : 0));
	return f.join('\t');
}

function configFromParts(parts) {
	var c = defaultConfig();
	var arr = { on: 'on', uc: 'uc', lr: 'lr' }, pre;
	for (var i = 0; i < parts.length; i++) {
		var eq = parts[i].lastIndexOf('=');
		if (eq <= 0) continue;
		var key = parts[i].slice(0, eq), val = parseFloat(parts[i].slice(eq + 1));
		if (!isFinite(val)) continue;
		if (key === 'r' || key === 'period' || key === 'beats') c[key] = val;
		else if (key === 'sync') c.sync = val ? 1 : 0;
		else if (key === 'm' || key === 'n' || key === 'levels') c[key] = Math.round(val);
		else if ((pre = key.slice(0, 2)) === 'on' || pre === 'uc' || pre === 'lr') {
			var idx = parseInt(key.slice(2), 10) - 1;
			var dst = pre === 'on' ? c.on : (pre === 'uc' ? c.uc : c.lr);
			if (idx >= 0 && idx < 6) dst[idx] = val ? 1 : 0;
		} else if (key.charAt(0) === 'p' && key.length <= 3) {
			var pi = parseInt(key.slice(1), 10) - 1;
			if (pi >= 0 && pi < 6) c.pitch[pi] = Math.round(val);
		} else if (key.slice(0, 3) === 'vel') {
			var vi = parseInt(key.slice(3), 10) - 1;
			if (vi >= 0 && vi < 6) c.vel[vi] = Math.round(val);
		} else if (key.slice(0, 3) === 'dur') {
			var di = parseInt(key.slice(3), 10) - 1;
			if (di >= 0 && di < 6) c.dur[di] = Math.round(val);
		} else if (key.slice(0, 5) === 'lprob') {
			var qi = parseInt(key.slice(5), 10) - 1;
			if (qi >= 0 && qi < 6) c.lprob[qi] = Math.round(val);
		} else if (key.slice(0, 5) === 'lstep') {
			var si = parseInt(key.slice(5), 10) - 1;
			if (si >= 0 && si < 6) c.lstep[si] = Math.round(val);
		} else if (key.slice(0, 6) === 'aphase') {
			var hi_ = parseInt(key.slice(6), 10) - 1;
			if (hi_ >= 0 && hi_ < 6) c.aphase[hi_] = Math.round(val);
		} else if (key.slice(0, 5) === 'agrid') {
			var gi = parseInt(key.slice(5), 10) - 1;
			if (gi >= 0 && gi < 16) c.agrid[gi] = val ? 1 : 0;
		} else if (key === 'gprob' || key === 'acyc' ||
			key === 'aeuck' || key === 'aeucr' || key === 'nvmin' || key === 'nvmax' ||
			key === 'nfig' || key === 'nsil' || key === 'avmin' || key === 'avmax' ||
			key === 'afig' || key === 'asil') {
			c[key] = Math.round(val);
		} else if (key === 'seed') {
			c.seed = Math.round(val);
		} else if (key === 'arton' || key === 'atie' || key === 'aeuc') {
			c[key] = val ? 1 : 0;
		}
	}
	return c;
}

function configEquals(a, b, eps) {
	if (eps === undefined) eps = 1e-12;
	var keys = ['r', 'period', 'beats', 'sync', 'm', 'n', 'levels',
		'gprob', 'seed', 'arton', 'acyc', 'atie', 'aeuc', 'aeuck', 'aeucr',
		'nvmin', 'nvmax', 'nfig', 'nsil', 'avmin', 'avmax', 'afig', 'asil'];
	for (var i = 0; i < keys.length; i++) if (Math.abs((a[keys[i]] || 0) - (b[keys[i]] || 0)) > eps) return false;
	var arrs = ['on', 'uc', 'lr', 'pitch', 'vel', 'dur', 'lprob', 'lstep', 'aphase', 'agrid'];
	for (i = 0; i < arrs.length; i++) {
		var len = a[arrs[i]].length;
		for (var j = 0; j < len; j++) if (Math.abs((a[arrs[i]][j] || 0) - (b[arrs[i]][j] || 0)) > eps) return false;
	}
	return true;
}

// --- probability / per-step / articulation: pure decision helpers ------------------------------
// Node-testable. Every one that needs randomness takes an `rng` function () -> [0,1) so the
// self-tests stay deterministic; the engine half owns the one live rng and its seeding.

// xorshift32. Max's JS engine predates Math.imul, so this uses only shifts / xor / >>>.
function makeRng(seed) {
	var s = (seed >>> 0) || 0x9E3779B9;   // 0 is a fixed point of xorshift -- never seed it
	return function () {
		s ^= s << 13; s >>>= 0;
		s ^= s >>> 17;
		s ^= s << 5;  s >>>= 0;
		return s / 4294967296;
	};
}

// One flat, time-ordered list of the cycle's onsets across every active level. The step index k
// the decimation and the accent read both use is a position in THIS list -- "the k-th hit of the
// bar", regardless of level. Tie-break equal times by level so k is deterministic under a seed.
function mergeSortedOnsets(perLevel) {
	var out = [];
	for (var i = 0; i < perLevel.length; i++) {
		var lv = perLevel[i].lv, t = perLevel[i].times;
		for (var j = 0; j < t.length; j++) out.push({ t: t[j], lv: lv });
	}
	out.sort(function (a, b) { return (a.t - b.t) || (a.lv - b.lv); });
	return out;
}

// Probfier's per-pad "step" mode, applied per level: keep index 0, N, 2N, ... of that level's own
// onset list. The list is rebuilt every cycle, so the step index resets each cycle. n <= 1 is a no-op.
function decimate(arr, n) {
	if (!(n > 1)) return arr;
	var out = [];
	for (var i = 0; i < arr.length; i += n) out.push(arr[i]);
	return out;
}

// p_global x p_level, as a 0..1 pass probability. 100 anywhere is a no-op.
function effectiveProb(gprob, lprob) { return (gprob / 100) * (lprob / 100); }

// Accent-grid read length: acyc, or the base word length m+n when "tie" is on. 1..16.
function accentReadLen(acyc, tieWord, m, n) {
	var len = Math.round(tieWord ? (m + n) : acyc);
	if (len < 1) len = 1;
	if (len > 16) len = 16;
	return len;
}

// 0 = Normal group, 1 = Accent group, from the cell the k-th onset (offset by its level's phase)
// lands on in the cyclic read.
function accentGroupAt(k, phaseLv, grid, len) {
	var idx = ((Math.round(k) + phaseLv) % len + len) % len;
	return grid[idx] ? 1 : 0;
}

// Uniform integer in [lo, hi], clamped to a legal MIDI velocity. Tolerates lo > hi (swapped).
function pickVel(rng, lo, hi) {
	if (lo > hi) { var t = lo; lo = hi; hi = t; }
	var v = lo + Math.floor(rng() * (hi - lo + 1));
	return v < 1 ? 1 : (v > 127 ? 127 : v);
}

// "Figura": a note-value denominator (4 = quarter, 8 = eighth, ...) as an absolute ms length off
// the host tempo -- same as forteseq2's articulation, decoupled from the cycle period.
function figuraMs(div, bpm) {
	if (!(div > 0)) div = 16;
	if (!(bpm > 0)) bpm = 120;
	return Math.max(1, (60000 / bpm) * (4 / div));
}

// A cycle fires only when Run is on, and -- in tempo-sync mode -- only while the Live transport is
// playing. Free-running mode ignores the transport entirely (that is the point of not syncing).
// Pure so --check can pin the truth table; startCycle() and the patch's metro gate both use it.
function shouldRunCycle(running, syncTempo, transportPlaying) {
	if (!running) return false;
	if (syncTempo && !transportPlaying) return false;
	return true;
}

// Euclidean accent grid: fill cells 0..cycle-1 from bjorklund(k, cycle) rotated by rot, clear the
// rest. Reuses this file's own bjorklund. Returns a fresh 16-array.
function euclidGrid(k, cycle, rot) {
	cycle = Math.round(cycle); if (cycle < 1) cycle = 1; if (cycle > 16) cycle = 16;
	k = Math.round(k); if (k < 0) k = 0; if (k > cycle) k = cycle;
	var pat = bjorklund(k, cycle);
	var r = ((Math.round(rot) % cycle) + cycle) % cycle;
	var g = [];
	for (var i = 0; i < 16; i++) g.push(i < cycle ? (pat[(i + r) % cycle] ? 1 : 0) : 0);
	return g;
}

// ================================================================================================
// Max-facing engine: state, message handlers, and Task-based real-time scheduling. Everything
// above this point is pure and Node-testable; everything below only runs inside a Max `js` object
// -- Task/outlet/inlets/autowatch are Max globals, undefined under node, and never called from any
// checkXxx() above. Same scheduling idiom forteseq2.js's own sub-clock already uses for
// humanize/strum/ratchet (one Task per event, re-armed every cycle) -- see forteseq-hot-path.
// ================================================================================================

inlets = 1;
outlets = 1;

var MAX_LEVELS = 6;

var running = 0;
var baseM = 3, baseN = 5, baseR = 1.5;
var numLevels = 1;
var levelOn = [1, 0, 0, 0, 0, 0];
var levelUC = [0, 0, 0, 0, 0, 0];       // 0 = Universal, 1 = Complementary
var levelReverse = [0, 0, 0, 0, 0, 0];  // L/R for the split that PRODUCES level i+2 (level 1 = base has none)
var levelPitch = [60, 60, 60, 60, 60, 60];
var levelVel = [100, 100, 100, 100, 100, 100];
var levelDur = [100, 100, 100, 100, 100, 100];
var periodMs = 2000;

// Tempo-sync state (see settempo/setsynctempo/setbeatsperperiod below). periodMs stays the single
// field startCycle()/wfOnsets() ever read -- sync mode is just a second way of writing to it, same
// as the manual setperiod() message, never a parallel code path through the rest of the engine.
var syncTempo = 0;
var beatsPerPeriod = 4;
var liveTempo = 120;
// Live transport play state, from a live.observer on live_set is_playing (see forteseqwf.amxd).
// Only consulted in sync mode -- see shouldRunCycle() / startCycle() / settransport().
var transportPlaying = 0;

// Preset bank + morph. presetBank holds config dicts (see CONFIG_SPEC); a morph blends two of its
// slots -- slot 0 meaning "the current edited state" -- without touching the visible controls or
// the stored slots, feeding startCycle() directly. morphEngaged() gates the whole thing: with
// morphA and morphB both 0 the engine runs exactly as it did before any of this was added.
var PRESET_FILE = "forteseqwf_presets.txt";
var PRESET_SLOTS = 20;
var presetSlot = 1;
var presetBank = [];              // slot -> config (+ optional __name); index 0 unused
var morphA = 0, morphB = 0, morphX = 0, morphRLinear = 0, quantizeR = 0;

// --- probability + per-step + articulation layers --------------------------------------------
// All of this is in the config dict, so it stores / recalls / morphs. rngSeed + a seeded rng
// make a given seed + config reproduce the same drop / accent sequence; cycleIndex advances the
// stream per cycle and resets on Run-on so a re-trigger replays it. With globalProb 100, every
// levelProb 100, every levelStep 1 and artOn 0, startCycle() is byte-identical to the pre-layer engine.
var rngSeed = 1;
var cycleIndex = 0;
var rng = makeRng(1);

var globalProb = 100;                              // 0..100 %
var levelProb = [100, 100, 100, 100, 100, 100];    // per-level %
var levelStep = [1, 1, 1, 1, 1, 1];               // per level, 1..8: keep 1 of every N of that level's own onsets

var artOn = 0;
var accentGrid = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
var accentCycle = 4;                               // 1..16
var accentTieWord = 0;                             // 1 -> read length = m+n
var euclidOn = 0, euclidK = 4, euclidRot = 0;
var levelPhase = [0, 0, 0, 0, 0, 0];               // 0..15 per level
var GROUP_NORMAL = 0, GROUP_ACCENT = 1;
var groupVelMin = [55, 95];
var groupVelMax = [80, 115];
var groupFigura = [16, 8];                         // note-value denominator
var groupSilence = [0, 0];                         // 0..100 % drop chance

var scheduledTasks = [];

function levelIndex(lv) {
	var i = Math.round(lv) - 1;
	return (i >= 0 && i < MAX_LEVELS) ? i : -1;
}

// Hard caps, independent of whatever a UI control's own range happens to be set to (a runaway
// on 2026-08-26 got past an unbounded setm/setperiod because a live.numbox's own default range
// silently clamped a value in a way the engine never checked itself -- these bounds are the
// engine's own defense, not a substitute for setting real ranges in the patch).
var MIN_PERIOD_MS = 50;
var MAX_PERIOD_MS = 60000;
var MAX_MN = 64;             // per base level; also caps how large a hierarchy level can grow to
var MAX_ONSETS_PER_CYCLE = 500;  // circuit breaker: startCycle() refuses to schedule past this

function clampInt(v, lo, hi) {
	v = Math.round(v);
	if (!isFinite(v)) return lo;
	if (v < lo) return lo;
	if (v > hi) return hi;
	return v;
}

function setrun(v) {
	running = v ? 1 : 0;
	if (!running) stopAllTasks();
	else cycleIndex = 0;   // restart the RNG stream so a re-trigger reproduces the same sequence
}
function setperiod(ms) { ms = Number(ms); if (isFinite(ms)) periodMs = clampInt(ms, MIN_PERIOD_MS, MAX_PERIOD_MS); }

// Tempo sync: when on, periodMs is DERIVED (beatsPerPeriod * ms-per-beat) instead of set directly by
// setperiod(). settempo() is fed by a live.observer on the Live Set's tempo property in the patch (see
// forteseqwf.amxd) -- it is NOT read from Max's transport, so it keeps working even if the transport
// is stopped (unlike a metro driven by a note-value/@quantize interval, see max_metro_transport_stall).
var MIN_BEATS_PER_PERIOD = 0.25, MAX_BEATS_PER_PERIOD = 64;
function clampFloat(v, lo, hi) {
	if (!isFinite(v)) return lo;
	if (v < lo) return lo;
	if (v > hi) return hi;
	return v;
}
function recomputeSyncedPeriod() {
	if (!syncTempo) return;
	var ms = beatsPerPeriod * (60000 / liveTempo);
	periodMs = clampInt(ms, MIN_PERIOD_MS, MAX_PERIOD_MS);
	// Diagnostic tag -1 (0 is already reserved for wf_levelviz, see fireNote/startCycle): tells the
	// patch's wf_metro what ms to actually run at now that the JS side owns the computation, so Max
	// never has to duplicate the beats->ms math itself. Real notes use tag lv+1 (always >=1); the
	// level-ladder diagnostic uses tag 0 -- neither collides with -1.
	outlet(0, -1, periodMs);
}
function setsynctempo(v) { syncTempo = v ? 1 : 0; recomputeSyncedPeriod(); }
// In sync mode a stopped transport means "no cycles". Kill any Tasks already in flight so the tail
// does not ring out; the free-running metro keeps ticking and startCycle()'s gate silently drops
// each cycle until the transport starts again (then the next tick plays -- no Run re-toggle).
// Free-running mode (Sync off) ignores the transport entirely.
function settransport(v) {
	transportPlaying = v ? 1 : 0;
	if (syncTempo && !transportPlaying) stopAllTasks();
}
function setbeatsperperiod(v) { beatsPerPeriod = clampFloat(Number(v), MIN_BEATS_PER_PERIOD, MAX_BEATS_PER_PERIOD); recomputeSyncedPeriod(); }
function settempo(bpm) { bpm = Number(bpm); if (isFinite(bpm) && bpm > 0) { liveTempo = bpm; recomputeSyncedPeriod(); } }

function setm(v) { baseM = clampInt(v, 1, MAX_MN); }
function setn(v) { baseN = clampInt(v, 0, MAX_MN); }

// setr also owns the "quantize to nearest r-slider marker" behaviour: when quantizeR is on, an
// incoming value snaps to the closest MARKERS entry, and the snapped value is pushed BACK to the
// wf_r control as a `set` (display only, no outlet -- see the "ui" tag) so the knob stops lying.
// The morph path deliberately never comes through here, so a sweep is never stair-stepped.
function setr(v) {
	v = Number(v);
	if (!(isFinite(v) && v >= 1)) return;
	if (quantizeR && MARKERS.length) {
		var snapped = nearestMarker(v, MARKERS).r;
		if (snapped !== v) { v = snapped; baseR = v; outlet(0, "ui", "r", baseR); }
		else baseR = v;
	} else {
		baseR = v;
	}
	outlet(0, "markertag", markerTagString(baseR, MARKERS, 1e-6));
}

function setlevels(v) { v = Math.round(v); if (v >= 1 && v <= MAX_LEVELS) numLevels = v; }
function setlevelon(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelOn[i] = v ? 1 : 0; }
function setleveluc(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelUC[i] = v ? 1 : 0; }
function setlevellr(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelReverse[i] = v ? 1 : 0; }
function setlevelpitch(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelPitch[i] = Math.round(v); }
function setlevelvel(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelVel[i] = Math.round(v); }
function setleveldur(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelDur[i] = Math.round(v); }

// --- probability + per-step ------------------------------------------------------------------
function setglobalprob(v) { globalProb = clampInt(v, 0, 100); }
function setlevelprob(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelProb[i] = clampInt(v, 0, 100); }
function setlevelstep(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelStep[i] = clampInt(v, 1, 8); }
function setseed(v) { v = Math.round(Number(v)); if (isFinite(v)) rngSeed = (v >>> 0) || 1; }

// --- articulation / accent ------------------------------------------------------------------
function setarton(v) { artOn = v ? 1 : 0; }
function setaccentgrid() {
	for (var i = 0; i < 16; i++) accentGrid[i] = (i < arguments.length && arguments[i]) ? 1 : 0;
}
function setaccentcycle(c) { accentCycle = clampInt(c, 1, 16); applyEuclid(); }
function setaccenttie(t) { accentTieWord = t ? 1 : 0; }
function seteuclid(on) { euclidOn = on ? 1 : 0; applyEuclid(); }
function seteuclidk(k) { euclidK = clampInt(k, 0, 16); applyEuclid(); }
function seteuclidrot(r) { euclidRot = clampInt(r, 0, 15); applyEuclid(); }
function setlevelphase(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelPhase[i] = clampInt(v, 0, 15); }
function setgroupvelmin(g, v) { g = Math.round(g); if (g === 0 || g === 1) groupVelMin[g] = clampInt(v, 1, 127); }
function setgroupvelmax(g, v) { g = Math.round(g); if (g === 0 || g === 1) groupVelMax[g] = clampInt(v, 1, 127); }
function setgroupfigura(g, v) { g = Math.round(g); if (g === 0 || g === 1) groupFigura[g] = clampInt(v, 1, 32); }
function setgroupsilence(g, v) { g = Math.round(g); if (g === 0 || g === 1) groupSilence[g] = clampInt(v, 0, 100); }

// Regenerate the accent grid from the Euclidean control trio and echo it back to the toggles.
// Only fires while Euclid is on; the "accentgrid" tag rides wf_engine's single outlet like the
// "ui" recall-repaint stream (see emitConfigUI / the fireNote comment).
function applyEuclid() {
	if (!euclidOn) return;
	var g = euclidGrid(euclidK, accentCycle, euclidRot);
	for (var i = 0; i < 16; i++) accentGrid[i] = g[i];
	outlet.apply(this, [0, "accentgrid"].concat(accentGrid));
}

// --- config snapshot <-> engine state -----------------------------------------------------------

// The live engine state as one config dict. With morph off this is what every cycle runs from, so
// its shape and clamping must match the individual setters above exactly.
function configFromCurrent() {
	return {
		r: baseR, period: periodMs, beats: beatsPerPeriod, sync: syncTempo,
		m: baseM, n: baseN, levels: numLevels,
		on: levelOn.slice(), uc: levelUC.slice(), lr: levelReverse.slice(),
		pitch: levelPitch.slice(), vel: levelVel.slice(), dur: levelDur.slice(),
		gprob: globalProb, lprob: levelProb.slice(), lstep: levelStep.slice(), seed: rngSeed,
		arton: artOn, acyc: accentCycle, atie: accentTieWord,
		aeuc: euclidOn, aeuck: euclidK, aeucr: euclidRot,
		agrid: accentGrid.slice(), aphase: levelPhase.slice(),
		nvmin: groupVelMin[0], nvmax: groupVelMax[0], nfig: groupFigura[0], nsil: groupSilence[0],
		avmin: groupVelMin[1], avmax: groupVelMax[1], afig: groupFigura[1], asil: groupSilence[1]
	};
}

// Write a config into the engine vars. No persistence, no morph side effects -- recallpreset()
// uses this, and so would any future "reset" message. Re-derives the synced period at the end so
// a slot saved with Sync on lands on the current host tempo, not the tempo it was saved at.
function applyConfig(c) {
	baseR = (isFinite(c.r) && c.r >= 1) ? c.r : 1;
	baseM = clampInt(c.m, 1, MAX_MN);
	baseN = clampInt(c.n, 0, MAX_MN);
	numLevels = clampInt(c.levels, 1, MAX_LEVELS);
	periodMs = clampInt(c.period, MIN_PERIOD_MS, MAX_PERIOD_MS);
	beatsPerPeriod = clampFloat(Number(c.beats), MIN_BEATS_PER_PERIOD, MAX_BEATS_PER_PERIOD);
	syncTempo = c.sync ? 1 : 0;
	for (var i = 0; i < MAX_LEVELS; i++) {
		levelOn[i] = c.on[i] ? 1 : 0;
		levelUC[i] = c.uc[i] ? 1 : 0;
		levelReverse[i] = c.lr[i] ? 1 : 0;
		levelPitch[i] = Math.round(c.pitch[i]);
		levelVel[i] = Math.round(c.vel[i]);
		levelDur[i] = Math.round(c.dur[i]);
		levelProb[i] = clampInt(c.lprob[i], 0, 100);
		levelStep[i] = clampInt(c.lstep[i], 1, 8);
		levelPhase[i] = clampInt(c.aphase[i], 0, 15);
	}
	globalProb = clampInt(c.gprob, 0, 100);
	rngSeed = (Math.round(Number(c.seed)) >>> 0) || 1;
	artOn = c.arton ? 1 : 0;
	accentCycle = clampInt(c.acyc, 1, 16);
	accentTieWord = c.atie ? 1 : 0;
	euclidOn = c.aeuc ? 1 : 0;
	euclidK = clampInt(c.aeuck, 0, 16);
	euclidRot = clampInt(c.aeucr, 0, 15);
	for (i = 0; i < 16; i++) accentGrid[i] = c.agrid[i] ? 1 : 0;   // stored grid already reflects any Euclid
	groupVelMin[0] = clampInt(c.nvmin, 1, 127); groupVelMax[0] = clampInt(c.nvmax, 1, 127);
	groupFigura[0] = clampInt(c.nfig, 1, 32);   groupSilence[0] = clampInt(c.nsil, 0, 100);
	groupVelMin[1] = clampInt(c.avmin, 1, 127); groupVelMax[1] = clampInt(c.avmax, 1, 127);
	groupFigura[1] = clampInt(c.afig, 1, 32);   groupSilence[1] = clampInt(c.asil, 0, 100);
	if (syncTempo) recomputeSyncedPeriod();
}

// Push a config out to the visible controls after a recall. `set` (not the raw value) so each
// live.* object only repaints -- it must NOT fire its own outlet back into the engine, which
// applyConfig() has already loaded. vel/dur have no control, so no token for them.
function emitConfigUI(c) {
	outlet(0, "ui", "r", c.r);
	outlet(0, "ui", "period", c.period);
	outlet(0, "ui", "bpp", c.beats);
	outlet(0, "ui", "sync", c.sync ? 1 : 0);
	outlet(0, "ui", "m", c.m);
	outlet(0, "ui", "n", c.n);
	outlet(0, "ui", "levels", c.levels);
	for (var i = 0; i < MAX_LEVELS; i++) {
		outlet(0, "ui", "on" + (i + 1), c.on[i] ? 1 : 0);
		outlet(0, "ui", "uc" + (i + 1), c.uc[i] ? 1 : 0);
		outlet(0, "ui", "p" + (i + 1), Math.round(c.pitch[i]));
		if (i < MAX_LEVELS - 1) outlet(0, "ui", "lr" + (i + 1), c.lr[i] ? 1 : 0);
		outlet(0, "ui", "lprob" + (i + 1), Math.round(c.lprob[i]));
		outlet(0, "ui", "lstep" + (i + 1), Math.round(c.lstep[i]));
		outlet(0, "ui", "aphase" + (i + 1), Math.round(c.aphase[i]));
	}
	outlet(0, "ui", "gprob", c.gprob);
	outlet(0, "ui", "seed", c.seed);
	outlet(0, "ui", "arton", c.arton ? 1 : 0);
	outlet(0, "ui", "acyc", c.acyc);
	outlet(0, "ui", "atie", c.atie ? 1 : 0);
	outlet(0, "ui", "aeuc", c.aeuc ? 1 : 0);
	outlet(0, "ui", "aeuck", c.aeuck);
	outlet(0, "ui", "aeucr", c.aeucr);
	outlet(0, "ui", "nvmin", c.nvmin); outlet(0, "ui", "nvmax", c.nvmax);
	outlet(0, "ui", "nfig", c.nfig);   outlet(0, "ui", "nsil", c.nsil);
	outlet(0, "ui", "avmin", c.avmin); outlet(0, "ui", "avmax", c.avmax);
	outlet(0, "ui", "afig", c.afig);   outlet(0, "ui", "asil", c.asil);
	outlet.apply(this, [0, "accentgrid"].concat(c.agrid));
	outlet(0, "markertag", markerTagString(c.r, MARKERS, 1e-6));
}

// --- preset bank on disk (Max File, next to the .amxd -- same mechanism as forteseq2) ----------

// Next to the .amxd, not wherever Max's current directory happens to be: a bare filename only
// resolves via the search path when READING, so writing one lands somewhere unpredictable.
function devPath(file) {
	var fp = "";
	try { fp = this.patcher.filepath; } catch (e) { fp = ""; }
	if (!fp) return file;
	var cut = fp.lastIndexOf("/");
	if (cut < 0) cut = fp.lastIndexOf("\\");
	return cut >= 0 ? fp.slice(0, cut + 1) + file : file;
}

function presetSlotOf(slot) {
	var s = (slot === undefined || slot === null) ? presetSlot : Math.round(slot);
	if (!(s >= 1 && s <= PRESET_SLOTS)) {
		post("forteseqwf: slot " + s + " fuera de rango (1.." + PRESET_SLOTS + ")\n");
		return -1;
	}
	return s;
}

function setpresetslot(n) {
	n = Math.round(n);
	if (!isFinite(n) || n < 1) n = 1;
	if (n > PRESET_SLOTS) n = PRESET_SLOTS;
	presetSlot = n;
	sendPresetName(n);
}

function sendPresetName(s) {
	var c = presetBank[s];
	outlet(0, "presetname", (c && c.__name) ? c.__name : "-");
}

function sendPresetList() {
	var s = "";
	for (var i = 1; i <= PRESET_SLOTS; i++) s += (i > 1 ? " " : "") + (presetBank[i] ? i : "-");
	outlet(0, "presetslots", s);
}

function setpresetname(slot, name) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	if (!presetBank[s]) presetBank[s] = configFromCurrent();
	presetBank[s].__name = "" + name;
	savepresets();
	sendPresetName(s);
}

function storepreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	var c = configFromCurrent();
	var old = presetBank[s] && presetBank[s].__name;
	if (old) c.__name = old;   // re-storing over a named slot keeps its label
	presetBank[s] = c;
	savepresets();
	sendPresetList();
	sendPresetName(s);
	post("forteseqwf: slot " + s + " guardado\n");
}

function recallpreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	var c = presetBank[s];
	if (!c) { post("forteseqwf: slot " + s + " vacio\n"); return; }
	applyConfig(c);
	emitConfigUI(c);
	post("forteseqwf: slot " + s + " cargado\n");
}

function clearpreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	presetBank[s] = null;
	savepresets();
	sendPresetList();
	sendPresetName(s);
	post("forteseqwf: slot " + s + " borrado\n");
}

// Tab-separated for the same reason forteseq2 uses it: a value never contains a tab, and the file
// stays readable. Header line so the format explains itself. One line per non-empty slot:
// "<slot>\t[__name=...]\t<configToLine>".
function savepresets() {
	if (typeof File === "undefined") return;
	var f = new File(devPath(PRESET_FILE), "write", "TEXT");
	if (!f.isopen) { post("forteseqwf: no pude escribir " + devPath(PRESET_FILE) + "\n"); return; }
	try {
		f.eof = 0;
		f.position = 0;
		f.writeline("forteseqwf presets 1");
		for (var s = 1; s <= PRESET_SLOTS; s++) {
			var c = presetBank[s];
			if (!c) continue;
			var line = "" + s;
			if (c.__name) line += "\t__name=" + c.__name;
			line += "\t" + configToLine(c);
			f.writeline(line);
		}
	} catch (e) {
		post("forteseqwf: fallo al guardar presets: " + e + "\n");
	}
	f.close();
}

function loadpresets() {
	if (typeof File === "undefined") return;
	var f = new File(devPath(PRESET_FILE), "read", "TEXT");
	if (!f.isopen) return;   // no file yet is first run, not an error
	presetBank = [];
	var count = 0;
	try {
		f.readline(200);   // header
		while (f.position < f.eof) {
			var line = "" + f.readline(65536);
			if (!line) continue;
			var parts = line.split("\t");
			var s = Math.round(parseFloat(parts[0]));
			if (!(s >= 1 && s <= PRESET_SLOTS)) continue;
			var rest = parts.slice(1);
			var nm = null;
			for (var i = 0; i < rest.length; i++) {
				if (rest[i].slice(0, 7) === "__name=") { nm = rest[i].slice(7); break; }
			}
			var c = configFromParts(rest);
			if (nm !== null) c.__name = nm;
			presetBank[s] = c;
			count++;
		}
	} catch (e) {
		post("forteseqwf: fallo al leer presets: " + e + "\n");
	}
	f.close();
	sendPresetList();
	sendPresetName(presetSlot);
	post("forteseqwf: " + count + " slots leidos\n");
}

// --- morph -------------------------------------------------------------------------------------

function restoreMetroPeriod() {
	if (syncTempo) recomputeSyncedPeriod();   // recomputes periodMs and emits the -1 tag
	else outlet(0, -1, periodMs);
}

function setmorph(x) { morphX = clampFloat(Number(x), 0, 1); }
function setmorphrlinear(v) { morphRLinear = v ? 1 : 0; }
function setquantizer(v) { quantizeR = v ? 1 : 0; if (quantizeR) setr(baseR); }

function setmorpha(v) {
	morphA = clampInt(v, 0, PRESET_SLOTS);
	if (morphA === 0 && morphB === 0) restoreMetroPeriod();
}
function setmorphb(v) {
	morphB = clampInt(v, 0, PRESET_SLOTS);
	if (morphA === 0 && morphB === 0) restoreMetroPeriod();
}

// Slot 0, or an empty slot, resolves to the current edited state -- so "morph from what I have now
// to slot 5" needs no extra capture step.
function resolveMorphSlot(n) {
	return (n === 0 || !presetBank[n]) ? configFromCurrent() : cloneConfig(presetBank[n]);
}

function morphEngaged() {
	return running && !(morphA === 0 && morphB === 0);
}

// The config a cycle actually plays when a morph is engaged, else null (startCycle falls back to
// configFromCurrent). If the blended config wants Sync, its period is re-derived from the live
// host tempo here, overriding whatever ms the two slots stored.
function activeConfig() {
	if (!morphEngaged()) return null;
	var c = lerpConfig(resolveMorphSlot(morphA), resolveMorphSlot(morphB), morphX, morphRLinear);
	if (c.sync) c.period = clampInt(c.beats * (60000 / liveTempo), MIN_PERIOD_MS, MAX_PERIOD_MS);
	return c;
}

function stopAllTasks() {
	for (var i = 0; i < scheduledTasks.length; i++) scheduledTasks[i].cancel();
	scheduledTasks = [];
}

// makenote (downstream in the Max patch) takes a 3-item (pitch, velocity, duration) list and
// generates the matching note-off itself -- so this is the only outlet call an onset ever needs;
// there is no separate note-off Task to manage. The channel/level number goes out FIRST, because
// the patch routes on it with a Max `route 1 2 3 4 5 6` object (route strips the matched leading
// value and sends the rest out the corresponding numbered outlet) into one of six fixed-channel
// makenote+noteout pairs -- level N always reaches MIDI channel N. This list is `route`'s only
// consumer, so its argument list (1-6) and MAX_LEVELS (6) both encode the same fact and must be
// kept in sync if either ever changes. Tag 0 is reserved on this same outlet for the diagnostic
// message below (see startCycle), and tag -1 is reserved for the tempo-sync diagnostic (see
// recomputeSyncedPeriod) -- no real note ever uses either, since lv is always 0-based and lv+1 is
// always >=1, so `wf_route`'s unconnected reject outlet swallows tag-0/-1 messages for free.
//
// The preset/morph layer adds four SYMBOL-tagged shapes on this same outlet -- `ui <token> <val>`
// (recall repaint, routed to the controls via `set` so they never re-fire), and `presetslots` /
// `presetname` / `markertag` (readout text). A new `route ui presetslots presetname markertag`
// (wf_uiroute) in the patch is their only consumer; the three numeric routes reject them the same
// way wf_route already rejects tag 0/-1.
function fireNote(lv, pitch, vel, dur) {
	outlet(0, lv + 1, pitch, vel, dur);
}

function scheduleOnset(lv, delayMs, pitch, vel, dur) {
	var t = new Task(function () { fireNote(lv, pitch, vel, dur); }, this);
	t.schedule(delayMs);
	scheduledTasks.push(t);
}

// Called once per period (see bang(), fed by a metro at periodMs). Rebuilding the hierarchy from
// scratch every cycle is deliberate, not lazy: per forteseq-hot-path, the real cost in this
// project is JS<->Max boundary crossings (outlet calls), not JS computation, so caching here would
// buy nothing and risks a stale-hierarchy bug when a param changes mid-cycle.
function startCycle() {
	stopAllTasks();
	// Run off, or sync mode with the transport stopped -> nothing this cycle. The metro keeps
	// free-running on wall-clock ms (so it can never fail to restart, unlike a stalled
	// transport-quantized metro), and this gate just drops the cycles: when the transport starts
	// again, the very next tick plays -- no need to re-toggle Run.
	if (!shouldRunCycle(running, syncTempo, transportPlaying)) return;

	// Re-seed the RNG per cycle from the fixed seed XOR the cycle number: bars evolve, but the
	// whole run is reproducible from rngSeed (which setrun(1) restarts). Cheap enough to do
	// unconditionally -- when probability/silencio are all off the rng is never actually drawn.
	cycleIndex++;
	rng = makeRng((rngSeed ^ (cycleIndex * 2654435761)) >>> 0);

	// One config drives the cycle. activeConfig() is the morph blend when a morph is engaged
	// (morphA/morphB not both 0), otherwise null and we run from the live vars -- byte-identical
	// to the pre-morph engine. Under a morph the blended period owns the metro this cycle, pushed
	// out on the same -1 tag the tempo-sync path already uses.
	var mc = activeConfig();
	var cfg = mc || configFromCurrent();
	if (mc) outlet(0, -1, cfg.period);

	var reverseFlags = cfg.lr.slice(0, Math.max(0, cfg.levels - 1));
	var h = wfHierarchy(cfg.m, cfg.n, cfg.r, cfg.levels, reverseFlags);

	// Diagnostic for wf_levelviz (jsui level-ladder): h.length is the REAL level count, which can
	// be less than cfg.levels if an earlier level came out isochronous and wfHierarchy stopped on
	// its own (see wfHierarchy's own comment) -- that distinction is exactly what "which level is
	// my rhythm actually at" means, and nothing else in this file exposes it. Tag 0 (see fireNote)
	// keeps this off the note-routing path entirely.
	// Layout: 0  levelCount  r[0..k-1]  pulses[0..k-1]  isoLevel  isoPulses  isoCapped
	// isoLevel/isoPulses come from the forward r-map probe (independent of the Levels cap), so the
	// viz can show "isochrony at level X, N pulses" even when the built ladder stopped short.
	var diag = [0, h.length];
	for (var dl = 0; dl < h.length; dl++) diag.push(h[dl].r);
	for (dl = 0; dl < h.length; dl++) diag.push(h[dl].word.length);
	var ol = isochronyOutlook(cfg.m, cfg.n, cfg.r);
	diag.push(ol.level, ol.pulses, ol.capped ? 1 : 0);
	outlet.apply(this, [0].concat(diag));

	// Per level: onsets + U/C (unchanged -- prevOnsets is still the FULL onset set so the next
	// level's U/C diff is intact). Then per-level decimation (Probfier's "step" mode, over this
	// level's own onsets). Collect the survivors tagged with their level.
	var perLevel = [];
	var prevOnsets = null;
	for (var lv = 0; lv < h.length; lv++) {
		var onsets = wfOnsets(h[lv], cfg.period);
		if (cfg.on[lv]) {
			var times = cfg.uc[lv] ? wfNewOnsets(onsets, prevOnsets || [], cfg.period) : onsets;
			times = decimate(times, cfg.lstep[lv] | 0);
			perLevel.push({ lv: lv, times: times });
		}
		prevOnsets = onsets;
	}

	// One time-sorted list across every active level -- the step index k the accent read uses.
	// With arton 0, gprob/lprob all 100 and every lstep 1 this loop schedules the exact same
	// onsets as the old level-major loop, just in time order (Task delays unchanged).
	var merged = mergeSortedOnsets(perLevel);
	var readLen = accentReadLen(cfg.acyc, cfg.atie, cfg.m, cfg.n);
	var totalScheduled = 0;
	for (var k = 0; k < merged.length; k++) {
		if (totalScheduled >= MAX_ONSETS_PER_CYCLE) {
			post('forteseqwf: circuit breaker -- refusing to schedule past ' + MAX_ONSETS_PER_CYCLE + ' onsets this cycle (m=' + cfg.m + ' n=' + cfg.n + ' levels=' + cfg.levels + ')\n');
			return;
		}
		var mlv = merged[k].lv;

		// (a) probability: p_global x p_level, one roll per surviving onset
		var pEff = effectiveProb(cfg.gprob, cfg.lprob[mlv]);
		if (pEff < 1 && rng() >= pEff) continue;

		var pitch = cfg.pitch[mlv], vel = cfg.vel[mlv], dur = cfg.dur[mlv];

		// (b) articulation: accent classifies the onset; the group's band supplies vel/figura, and
		// its silencio% is a second, independent drop.
		if (cfg.arton) {
			var g = accentGroupAt(k, cfg.aphase[mlv], cfg.agrid, readLen);
			var sil = g ? cfg.asil : cfg.nsil;
			if (sil > 0 && rng() * 100 < sil) continue;
			vel = pickVel(rng, g ? cfg.avmin : cfg.nvmin, g ? cfg.avmax : cfg.nvmax);
			dur = Math.round(figuraMs(g ? cfg.afig : cfg.nfig, liveTempo));
		}

		scheduleOnset(mlv, merged[k].t, pitch, vel, dur);
		totalScheduled++;
	}
}

function bang() { startCycle(); }

// ================================================================================================
// Self-test. Runs only under node (Max's js object has no `require`/`process`), mirroring
// test/harness.js's spirit but as its own small harness -- this file has no Max stubs to load and
// no golden.txt to diff against yet.
// ================================================================================================

if (typeof require !== 'undefined' && typeof process !== 'undefined') {
	(function () {
		var failures = 0;

		function eq(got, want, label) {
			if (got !== want) {
				console.error('FAIL ' + label + ': got ' + got + ', want ' + want);
				failures++;
			}
		}

		function approxEq(got, want, label, eps) {
			eps = eps === undefined ? 1e-9 : eps;
			if (Math.abs(got - want) > eps) {
				console.error('FAIL ' + label + ': got ' + got + ', want ' + want + ' (diff ' + Math.abs(got - want) + ')');
				failures++;
			}
		}

		function wordStr(level) { return level.word.join(''); }

		// The only numeric worked example either source gives (2019 chapter, Fig. 7):
		// 2L,1S -> 2L,3S -> 5L,2S -> 12-isochronous. The paper never states level 0's r-value
		// explicitly; r=2.5 is the unique value that reproduces the exact branch sequence the
		// figure implies (r0>=2, r1<2, r2>=2 at the boundary) -- solved by hand, see the plan.
		function checkFig7Example() {
			var h = wfHierarchy(2, 1, 2.5, 4);
			eq(h[0].m, 2, 'Fig7 level0 m'); eq(h[0].n, 1, 'Fig7 level0 n');
			eq(h[1].m, 2, 'Fig7 level1 m'); eq(h[1].n, 3, 'Fig7 level1 n');
			approxEq(h[1].r, 1.5, 'Fig7 level1 r');
			eq(h[2].m, 5, 'Fig7 level2 m'); eq(h[2].n, 2, 'Fig7 level2 n');
			approxEq(h[2].r, 2.0, 'Fig7 level2 r');
			eq(h[3].m, 5, 'Fig7 level3 m'); eq(h[3].n, 7, 'Fig7 level3 n');
			approxEq(h[3].r, 1.0, 'Fig7 level3 r (isochronous)');
			eq(h[3].word.length, 12, 'Fig7 level3 total events');
			// isochronous means every duration in the final level is identical.
			var durs = wfDurations(h[3], 1200);
			for (var i = 1; i < durs.length; i++) approxEq(durs[i], durs[0], 'Fig7 level3 duration[' + i + '] == duration[0]');
			if (failures === 0) console.log('OK   checkFig7Example: 2L1S -> 2L3S -> 5L2S -> 12 isochronous, r0=2.5 matches the book\'s own figure.');
		}

		// isochronyOutlook: the forward r-probe agrees with actually building the hierarchy out to
		// isochrony, matches the Fig. 7 pulse count, and correctly reports "never" for the metallic
		// ratios (r cycles) and integers (r -> r-1 -> ... -> 1 in exactly r-1 steps).
		function checkIsochronyOutlook() {
			var f0 = failures;
			var o = isochronyOutlook(2, 1, 2.5);
			eq(o.level, 3, 'outlook Fig7 level'); eq(o.pulses, 12, 'outlook Fig7 pulses'); eq(o.capped, false, 'outlook Fig7 not capped');

			// base already isochronous
			var oi = isochronyOutlook(3, 5, 1);
			eq(oi.level, 0, 'outlook r=1 level'); eq(oi.pulses, 8, 'outlook r=1 pulses');

			// integer r=k reaches isochrony in exactly k-1 steps; cross-check pulses against a real build
			for (var k = 2; k <= 6; k++) {
				var ok = isochronyOutlook(1, 1, k);
				eq(ok.level, k - 1, 'outlook int r=' + k + ' level');
				var hk = wfHierarchy(1, 1, k, k + 2);
				eq(wfIsIsochronous(hk[hk.length - 1]), true, 'outlook int r=' + k + ' build ends isochronous');
				eq(ok.pulses, hk[hk.length - 1].word.length, 'outlook int r=' + k + ' pulses match build');
				eq(ok.level, hk.length - 1, 'outlook int r=' + k + ' level matches build');
			}

			// metallic ratios never reach r == 1 -- the probe must report capped, not a bogus level
			var metals = [metallicRatio(1), metallicRatio(2), metallicRatio(3), 1 + Math.sqrt(2)];
			for (var i = 0; i < metals.length; i++) {
				var om = isochronyOutlook(3, 5, metals[i], 200);
				eq(om.capped, true, 'outlook metallic ' + metals[i].toFixed(4) + ' capped');
				eq(om.level, -1, 'outlook metallic ' + metals[i].toFixed(4) + ' level -1');
			}

			// a rational that does terminate, but past a shallow Levels cap: probe still finds it
			var od = isochronyOutlook(3, 5, 1.2);   // 1.2 -> 5 -> 4 -> 3 -> 2 -> 1
			eq(od.capped, false, 'outlook r=1.2 terminates');
			eq(od.level, 5, 'outlook r=1.2 level');
			var hd = wfHierarchy(3, 5, 1.2, 12);
			eq(od.pulses, hd[hd.length - 1].word.length, 'outlook r=1.2 pulses match build');

			if (failures === f0) console.log('OK   checkIsochronyOutlook: forward r-probe matches the built hierarchy (level + pulse count), Fig. 7 = 12, metallic ratios report "never".');
		}

		// The run gate: sync mode follows the Live transport, free-running mode does not.
		function checkRunGate() {
			var f0 = failures;
			eq(shouldRunCycle(0, 0, 0), false, 'run off -> no cycle');
			eq(shouldRunCycle(0, 1, 1), false, 'run off -> no cycle even in sync + playing');
			eq(shouldRunCycle(1, 0, 0), true, 'free-run + transport stopped -> still runs');
			eq(shouldRunCycle(1, 0, 1), true, 'free-run + transport playing -> runs');
			eq(shouldRunCycle(1, 1, 0), false, 'sync + transport stopped -> no cycle');
			eq(shouldRunCycle(1, 1, 1), true, 'sync + transport playing -> cycle');
			if (failures === f0) console.log('OK   checkRunGate: sync mode gates on the Live transport, free-running mode ignores it.');
		}

		// The real verification for the r-value recursion, since no source gives the equations:
		// the theory requires level j's onsets to be a strict subset of level j+1's (a hierarchy
		// only ever inserts new events, never moves the old ones). Built independently per level
		// (own word, own r, own d) -- if the r' formula were wrong this fails immediately.
		function checkRefinement() {
			var cases = [
				[2, 1, 2.5], [3, 5, 1.2], [1, 1, Math.sqrt(2)], [4, 3, 7 / 3],
				[2, 3, metallicRatio(1)], [1, 1, metallicRatio(2)], [3, 1, metallicRatio(3)]
			];
			var d = 1000;
			for (var c = 0; c < cases.length; c++) {
				var m = cases[c][0], n = cases[c][1], r = cases[c][2];
				var h = wfHierarchy(m, n, r, 6);
				var prevOnsets = null;
				for (var lv = 0; lv < h.length; lv++) {
					var onsets = wfOnsets(h[lv], d);
					eq(onsets.length, h[lv].word.length, 'refinement case ' + c + ' level ' + lv + ' onset count');
					// closes the period exactly
					var durs = wfDurations(h[lv], d);
					var total = 0;
					for (var i = 0; i < durs.length; i++) total += durs[i];
					approxEq(total, d, 'refinement case ' + c + ' level ' + lv + ' durations sum to d', d * 1e-9);
					if (prevOnsets) {
						for (i = 0; i < prevOnsets.length; i++) {
							if (!approxIncludes(onsets, prevOnsets[i], d * 1e-9)) {
								console.error('FAIL refinement case ' + c + ' level ' + lv + ': onset ' + prevOnsets[i] + ' from the previous level is missing -- r-recursion is wrong.');
								failures++;
							}
						}
					}
					prevOnsets = onsets;
				}
			}
			if (failures === 0) console.log('OK   checkRefinement: every tested level\'s onsets are an exact subset of the next level\'s, across 7 (m,n,r) starting points and 6 levels each.');
		}

		// U/C: the union of "new" onsets across all levels must equal the top level's full onset
		// set exactly, and no onset should ever be claimed as "new" twice.
		function checkComplementary() {
			var d = 777;
			var h = wfHierarchy(3, 5, Math.E, 5);
			var seen = [];
			var prevOnsets = [];
			for (var lv = 0; lv < h.length; lv++) {
				var onsets = wfOnsets(h[lv], d);
				var fresh = wfNewOnsets(onsets, prevOnsets, d);
				for (var i = 0; i < fresh.length; i++) {
					if (approxIncludes(seen, fresh[i], d * 1e-9)) {
						console.error('FAIL checkComplementary: onset ' + fresh[i] + ' claimed as new at two different levels');
						failures++;
					}
					seen.push(fresh[i]);
				}
				prevOnsets = onsets;
			}
			eq(seen.length, h[h.length - 1].word.length, 'checkComplementary: union of all "new" onsets covers the top level exactly');
			if (failures === 0) console.log('OK   checkComplementary: U/C partition is exact and non-overlapping across 5 levels.');
		}

		// L/R changes onset timing but never the (m,n,r) sequence.
		function checkLeftRight() {
			var a = wfHierarchy(3, 4, 1.8, 4, [false, false, false]);
			var b = wfHierarchy(3, 4, 1.8, 4, [true, true, true]);
			for (var lv = 0; lv < a.length; lv++) {
				eq(a[lv].m, b[lv].m, 'L/R level ' + lv + ' m unaffected');
				eq(a[lv].n, b[lv].n, 'L/R level ' + lv + ' n unaffected');
				approxEq(a[lv].r, b[lv].r, 'L/R level ' + lv + ' r unaffected');
			}
			var wa = wordStr(a[2]), wb = wordStr(b[2]);
			if (wa === wb) { console.error('FAIL checkLeftRight: reversed split produced an identical word at level 2 -- L/R is a no-op'); failures++; }
			if (failures === 0) console.log('OK   checkLeftRight: same (m,n,r) at every level, different word/timing (level 2: ' + wa + ' vs ' + wb + ').');
		}

		// The three named metallic ratios, and the general pattern: M_k is a period-k fixed
		// point of the recursion (verified algebraically in the plan: phi-1 = 1/phi, so r<2
		// applies and 1/(phi-1) = phi again immediately; silver and bronze the same one level
		// later). Also checks k=4 doesn't cycle any *earlier* than period 4, to catch a formula
		// that trivially fixes everything.
		function checkMetallicRatios() {
			approxEq(metallicRatio(1), 1.618033988749895, 'golden ratio value', 1e-12);
			approxEq(metallicRatio(2), 2.414213562373095, 'silver ratio value', 1e-12);
			approxEq(metallicRatio(3), 3.302775637731995, 'bronze ratio value', 1e-12);
			for (var k = 1; k <= 4; k++) {
				var r0 = metallicRatio(k);
				var level = { word: ['L'], m: 1, n: 0, r: r0 }; // word/m/n are irrelevant to the r-only cycle check
				var r = r0;
				for (var step = 1; step <= k; step++) {
					level = wfNextLevel(level, false);
					r = level.r;
					if (step < k) {
						if (Math.abs(r - r0) < 1e-9) {
							console.error('FAIL checkMetallicRatios: M_' + k + ' cycled back to itself after only ' + step + ' step(s), expected period ' + k);
							failures++;
						}
					}
				}
				approxEq(r, r0, 'M_' + k + ' returns to its own value after exactly ' + k + ' step(s)', 1e-8);
			}
			if (failures === 0) console.log('OK   checkMetallicRatios: golden/silver/bronze values correct, and M_k cycles with period exactly k for k=1..4.');
		}

		// phi_s snap values: hand-computed cases at the two smallest s, the degenerate/empty s=0/1
		// cases, and a general lock-in check across s=2..6 -- for every generated r0, wfNextLevel
		// must reach r=phi at exactly level s (not earlier: that's the point of these particular
		// Stern-Brocot pairs over any other irrational r) and stay at phi for several levels after.
		function checkPhiSnapValues() {
			eq(sbPhiPairs(0).length, 0, 'checkPhiSnapValues: s=0 has no real family members (degenerate root case)');
			eq(sbPhiPairs(1).length, 0, 'checkPhiSnapValues: s=1 has no valid member');

			var p2 = sbPhiPairs(2);
			eq(p2.length, 1, 'checkPhiSnapValues: s=2 has exactly 1 pair');
			if (p2.length === 1) {
				eq(p2[0].a, 1, 's=2 pair a'); eq(p2[0].b, 1, 's=2 pair b');
				eq(p2[0].c, 2, 's=2 pair c'); eq(p2[0].d, 1, 's=2 pair d');
				approxEq(phiSnapValue(p2[0].a, p2[0].b, p2[0].c, p2[0].d), 1.381966011250105, 's=2 phi-snap value', 1e-9);
			}

			var p3 = sbPhiPairs(3);
			eq(p3.length, 2, 'checkPhiSnapValues: s=3 has exactly 2 pairs');
			if (p3.length === 2) {
				var v3 = phiSnapValues(3);
				approxEq(v3[0], 1.7236067977499790, 's=3 phi-snap value (lower)', 1e-9);
				approxEq(v3[1], 2.3819660112501050, 's=3 phi-snap value (upper)', 1e-9);
			}

			var phi = metallicRatio(1);
			for (var s = 2; s <= 6; s++) {
				var pairs = sbPhiPairs(s);
				eq(pairs.length, Math.pow(2, s - 2), 'checkPhiSnapValues: s=' + s + ' pair count is 2^(s-2)');
				for (var p = 0; p < pairs.length; p++) {
					var r0 = phiSnapValue(pairs[p].a, pairs[p].b, pairs[p].c, pairs[p].d);
					var level = { word: ['L'], m: 1, n: 0, r: r0 }; // word/m/n irrelevant to the r-only walk
					for (var i = 0; i < s + 5; i++) {
						var isPhi = Math.abs(level.r - phi) < 1e-7;
						if (i < s && isPhi) {
							console.error('FAIL checkPhiSnapValues: s=' + s + ' pair ' + p + ' reached phi early, at level ' + i + ' instead of ' + s);
							failures++;
						}
						if (i >= s && !isPhi) {
							console.error('FAIL checkPhiSnapValues: s=' + s + ' pair ' + p + ' is not locked at phi at level ' + i + ' (r=' + level.r + ')');
							failures++;
						}
						level = wfNextLevel(level, false);
					}
				}
			}
			if (failures === 0) console.log('OK   checkPhiSnapValues: hand-computed s=2/3 values correct, s=0/1 empty, and every generated r0 for s=2..6 locks onto phi at exactly its own level, never earlier.');
		}

		// Rational r reaches isochrony at some finite level and the hierarchy must stop there
		// (dividing by r-1=0 otherwise) -- this is what checkRefinement's case 0 caught before
		// wfHierarchy grew the isochrony guard: it asked for 6 levels of (m=2,n=1,r=2.5), which
		// per checkFig7Example is isochronous already at level 3.
		function checkTermination() {
			var h = wfHierarchy(2, 1, 2.5, 6);
			eq(h.length, 4, 'checkTermination: (2,1,r=2.5) hierarchy stops at 4 levels (0..3), not the requested 6');
			if (!wfIsIsochronous(h[h.length - 1])) { console.error('FAIL checkTermination: last level is not actually isochronous'); failures++; }
			var threw = false;
			try { wfNextLevel(h[h.length - 1], false); } catch (e) { threw = true; }
			if (!threw) { console.error('FAIL checkTermination: wfNextLevel on an isochronous level should throw, not silently produce NaN/Infinity'); failures++; }
			if (failures === 0) console.log('OK   checkTermination: hierarchy stops exactly at isochrony, and splitting past it fails loudly instead of producing NaN.');
		}

		// The r-slider marker catalog. The real correctness property is forward: walk wfNextLevel
		// from each generated r0 exactly `level` times and confirm it has reached that family's
		// target cycle -- and had NOT reached it at any earlier step. Plus spot-checks against the
		// independently-built phiSnapValues()/metallicRatio() where the families overlap.
		function checkMarkers() {
			var phi = metallicRatio(1), d = metallicRatio(2), s = metallicRatio(3);
			function onTarget(family, r) {
				var e = 1e-7;
				if (family === 'n') return Math.abs(r - 1) < e;
				if (family === 'phi') return Math.abs(r - phi) < e;
				if (family === 'delta') return Math.abs(r - d) < e || Math.abs(r - (d - 1)) < e;
				return Math.abs(r - s) < e || Math.abs(r - (s - 1)) < e || Math.abs(r - (s - 2)) < e;
			}
			if (MARKERS.length < 12) {
				console.error('FAIL checkMarkers: only ' + MARKERS.length + ' markers generated, expected dozens');
				failures++;
			}
			for (var i = 0; i < MARKERS.length; i++) {
				var mk = MARKERS[i];
				if (!(mk.r > 1 && mk.r <= MARKER_RMAX + 1e-9)) {
					console.error('FAIL checkMarkers: ' + markerLabel(mk) + ' outside (1, ' + MARKER_RMAX + ']');
					failures++;
				}
				if (mk.level > MARKER_SMAX[mk.family]) {
					console.error('FAIL checkMarkers: ' + markerLabel(mk) + ' level exceeds its family cap');
					failures++;
				}
				// Walk the r-only recursion. word/m/n are irrelevant here (same trick the metallic
				// and phi-snap checks use); guard the isochronous throw for the `n` family.
				var lvl = { word: ['L'], m: 1, n: 0, r: mk.r };
				var reachedAt = -1;
				for (var step = 0; step <= mk.level + 3; step++) {
					if (onTarget(mk.family, lvl.r)) { reachedAt = step; break; }
					if (wfIsIsochronous(lvl)) break;   // n family: r==1 is the target, caught above
					lvl = wfNextLevel(lvl, false);
				}
				if (reachedAt !== mk.level) {
					console.error('FAIL checkMarkers: ' + markerLabel(mk) + ' reaches its ' + mk.family +
						' target at step ' + reachedAt + ', not ' + mk.level);
					failures++;
				}
			}
			// distinct r values
			for (i = 1; i < MARKERS.length; i++) {
				if (Math.abs(MARKERS[i].r - MARKERS[i - 1].r) < 1e-9) {
					console.error('FAIL checkMarkers: duplicate r ' + MARKERS[i].r);
					failures++;
				}
			}
			// every canonical phi-snap value within the phi cap is somewhere in the phi family
			for (var sp = 2; sp <= Math.min(MARKER_SMAX.phi, 6); sp++) {
				var want = phiSnapValues(sp);
				for (var w = 0; w < want.length; w++) {
					if (want[w] > MARKER_RMAX + 1e-9) continue;
					var found = false;
					for (var m2 = 0; m2 < MARKERS.length; m2++) {
						if (MARKERS[m2].family === 'phi' && Math.abs(MARKERS[m2].r - want[w]) < 1e-7) { found = true; break; }
					}
					if (!found) {
						console.error('FAIL checkMarkers: phiSnapValues(' + sp + ') value ' + want[w] + ' missing from the phi family');
						failures++;
					}
				}
			}
			// the metallic ratios themselves are level-0 members of their families
			var mustHave = [['phi', phi], ['delta', d], ['delta', d - 1], ['sigma', s], ['sigma', s - 1], ['sigma', s - 2]];
			for (var mh = 0; mh < mustHave.length; mh++) {
				var fam = mustHave[mh][0], val = mustHave[mh][1], ok = false;
				for (i = 0; i < MARKERS.length; i++) {
					if (MARKERS[i].family === fam && Math.abs(MARKERS[i].r - val) < 1e-9 && MARKERS[i].level === 0) { ok = true; break; }
				}
				if (val <= MARKER_RMAX + 1e-9 && !ok) {
					console.error('FAIL checkMarkers: ' + fam + ' cycle member ' + val + ' not present at level 0');
					failures++;
				}
			}
			if (failures === 0) console.log('OK   checkMarkers: ' + MARKERS.length + ' markers, each verified forward against wfNextLevel to lock on its n/phi/delta/sigma target at exactly its tagged level.');
		}

		function dumpMarkers() {
			for (var i = 0; i < MARKERS.length; i++) {
				var mk = MARKERS[i];
				console.log(i + '\t' + mk.r + '\t' + mk.family + '\t' + mk.level + '\t' + markerLabel(mk));
			}
			console.log('# count=' + MARKERS.length);
		}

		// config dict: interpolation endpoints exact, midpoint sane, disk round-trip lossless, and
		// applyConfig(configFromCurrent()) a genuine no-op (morph off must not perturb the engine).
		function checkConfigMorph() {
			var a = defaultConfig();
			var b = defaultConfig();
			b.r = 3.303; b.period = 4000; b.beats = 8; b.m = 2; b.n = 7; b.levels = 5;
			b.on = [1, 1, 1, 0, 0, 0]; b.uc = [0, 1, 0, 1, 0, 0]; b.lr = [1, 0, 1, 0, 1, 0];
			b.pitch = [48, 50, 52, 53, 55, 57]; b.vel = [90, 90, 90, 90, 90, 90]; b.dur = [200, 200, 200, 200, 200, 200];
			// exercise every new-field kind through the round trip / lerp
			b.gprob = 70; b.lprob = [100, 80, 60, 40, 20, 0]; b.lstep = [1, 2, 3, 4, 5, 6]; b.seed = 424242;
			b.arton = 1; b.acyc = 12; b.atie = 1; b.aeuc = 1; b.aeuck = 5; b.aeucr = 2;
			b.agrid = [1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1];
			b.aphase = [0, 1, 2, 3, 4, 5];
			b.nvmin = 40; b.nvmax = 70; b.nfig = 12; b.nsil = 15;
			b.avmin = 100; b.avmax = 120; b.afig = 6; b.asil = 30;

			if (!configEquals(lerpConfig(a, b, 0), a)) { console.error('FAIL checkConfigMorph: x=0 is not config a'); failures++; }
			if (!configEquals(lerpConfig(a, b, 1), b)) { console.error('FAIL checkConfigMorph: x=1 is not config b'); failures++; }
			if (!configEquals(lerpConfig(a, b, -5), a) || !configEquals(lerpConfig(a, b, 9), b)) {
				console.error('FAIL checkConfigMorph: x outside [0,1] not clamped to endpoints'); failures++;
			}
			if (!configEquals(lerpConfig(b, b, 0.37), b, 1e-9)) { console.error('FAIL checkConfigMorph: lerp of a config with itself drifts'); failures++; }

			var mid = lerpConfig(a, b, 0.5);
			if (mid.m !== Math.round((a.m + b.m) / 2)) { console.error('FAIL checkConfigMorph: m not rounded lerp at x=0.5'); failures++; }
			if (mid.period !== (a.period + b.period) / 2) { console.error('FAIL checkConfigMorph: period not linear at x=0.5'); failures++; }
			// r in slider space: r=1 -> t=0, so lerpR(1.5, 3.303, x) stays within [1.5, 3.303] and monotone
			var rPrev = -1, mono = true;
			for (var x = 0; x <= 1.0001; x += 0.1) {
				var rr = lerpR(1.5, 3.303, Math.min(x, 1), false);
				if (rr < 1.5 - 1e-9 || rr > 3.303 + 1e-9) mono = false;
				if (rr < rPrev - 1e-9) mono = false;
				rPrev = rr;
			}
			if (!mono) { console.error('FAIL checkConfigMorph: lerpR not monotone/bounded in slider space'); failures++; }

			// seed is 'pick', never blended: a=1 below x=0.5, b's above
			if (lerpConfig(a, b, 0.3).seed !== a.seed || lerpConfig(a, b, 0.7).seed !== b.seed) {
				console.error('FAIL checkConfigMorph: seed did not pick (should snap a<->b at 0.5, never interpolate)'); failures++;
			}
			// arton snaps, agrid cells cross at 0.5
			if (lerpConfig(a, b, 0.6).arton !== b.arton || lerpConfig(a, b, 0.4).arton !== a.arton) {
				console.error('FAIL checkConfigMorph: arton did not snap at 0.5'); failures++;
			}
			if (lerpConfig(a, b, 0.6).agrid[2] !== b.agrid[2]) { console.error('FAIL checkConfigMorph: agrid cell did not cross at 0.5'); failures++; }
			if (lerpConfig(a, b, 0.5).gprob !== Math.round((a.gprob + b.gprob) / 2)) { console.error('FAIL checkConfigMorph: gprob not rounded lerp'); failures++; }

			// disk round-trip
			var rt = configFromParts(configToLine(b).split('\t'));
			if (!configEquals(rt, b)) { console.error('FAIL checkConfigMorph: configToLine/configFromParts not lossless'); failures++; }

			// applyConfig(configFromCurrent()) must not perturb the engine (syncTempo defaults to 0,
			// so recomputeSyncedPeriod -- which would call the Max-only `outlet` -- is never reached).
			var before = configFromCurrent();
			applyConfig(cloneConfig(before));
			if (!configEquals(configFromCurrent(), before)) { console.error('FAIL checkConfigMorph: applyConfig(configFromCurrent()) changed engine state'); failures++; }

			if (failures === 0) console.log('OK   checkConfigMorph: lerp endpoints exact, midpoint linear/rounded, slider-space r monotone, new fields (seed pick / grid cross / gprob lerp) correct, disk round-trip lossless, applyConfig round-trips.');
		}

		// The probability + per-step layer, on the pure helpers (startCycle itself is Max-only).
		function checkProbability() {
			approxEq(effectiveProb(100, 100), 1, 'effectiveProb 100x100');
			approxEq(effectiveProb(0, 80), 0, 'effectiveProb 0x80');
			approxEq(effectiveProb(50, 50), 0.25, 'effectiveProb 50x50');

			// merge is time-sorted, tie-broken by level, and keeps the level tag
			var merged = mergeSortedOnsets([{ lv: 2, times: [0, 400, 800] }, { lv: 0, times: [0, 200, 600] }]);
			eq(merged.length, 6, 'mergeSortedOnsets count');
			eq(merged[0].t === 0 && merged[0].lv === 0, true, 'mergeSortedOnsets tie-break by level');
			var ordered = true;
			for (var i = 1; i < merged.length; i++) if (merged[i].t < merged[i - 1].t) ordered = false;
			eq(ordered, true, 'mergeSortedOnsets time-ordered');

			// per-level decimation: keep index 0, N, 2N, ... of a level's own onset list
			eq(decimate([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 3).join(','), '0,3,6,9', 'decimate n=3');
			eq(decimate([10, 20, 30, 40, 50], 2).join(','), '10,30,50', 'decimate n=2');
			eq(decimate([5, 6, 7], 1).join(','), '5,6,7', 'decimate n=1 no-op');
			eq(decimate([], 4).length, 0, 'decimate empty');

			// pEff=1 -> rng()>=1 is never true -> nothing dropped, rng untouched
			var r1 = makeRng(7), drops = 0;
			for (i = 0; i < 200; i++) { var p = effectiveProb(100, 100); if (p < 1 && r1() >= p) drops++; }
			eq(drops, 0, 'pEff=1 drops nothing');
			// pEff=0 -> everything dropped
			var r2 = makeRng(7); drops = 0;
			for (i = 0; i < 200; i++) { var q = effectiveProb(0, 100); if (q < 1 && r2() >= q) drops++; }
			eq(drops, 200, 'pEff=0 drops everything');
			// ~50% over many draws
			var r3 = makeRng(12345), pass = 0;
			for (i = 0; i < 5000; i++) if (r3() < 0.5) pass++;
			if (Math.abs(pass / 5000 - 0.5) > 0.03) { console.error('FAIL checkProbability: rng not ~uniform (' + (pass / 5000) + ')'); failures++; }

			// determinism: two fresh rngs from the same seed agree
			var a = makeRng(42), b = makeRng(42);
			for (i = 0; i < 20; i++) if (a() !== b()) { console.error('FAIL checkProbability: makeRng not deterministic'); failures++; break; }
			// seed 0 must not lock up (xorshift fixed point)
			var z = makeRng(0);
			if (!(z() > 0 && z() < 1)) { console.error('FAIL checkProbability: makeRng(0) degenerate'); failures++; }

			if (failures === 0) console.log('OK   checkProbability: effectiveProb / merge+sort / decimation / pEff extremes / rng uniformity + determinism all correct.');
		}

		// The articulation / accent layer, on the pure helpers.
		function checkArticulation() {
			// accentGroupAt matches the plain cyclic grid read, phase and wrap included
			var grid = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0];
			var okAll = true;
			for (var len = 1; len <= 16; len++)
				for (var ph = 0; ph <= 15; ph++)
					for (var k = 0; k < 40; k++) {
						var want = grid[((k + ph) % len + len) % len] ? 1 : 0;
						if (accentGroupAt(k, ph, grid, len) !== want) okAll = false;
					}
			eq(okAll, true, 'accentGroupAt == cyclic grid read');

			// read length: acyc, or m+n when tie, clamped 1..16
			eq(accentReadLen(4, 0, 3, 5), 4, 'accentReadLen acyc');
			eq(accentReadLen(4, 1, 3, 5), 8, 'accentReadLen tie -> m+n');
			eq(accentReadLen(99, 0, 3, 5), 16, 'accentReadLen clamps high');
			eq(accentReadLen(0, 0, 0, 0), 1, 'accentReadLen clamps low');

			// pickVel: in range, degenerate, swapped
			var rv = makeRng(9);
			eq(pickVel(rv, 60, 60), 60, 'pickVel degenerate');
			var inRange = true;
			for (var i = 0; i < 2000; i++) { var v = pickVel(rv, 40, 90); if (v < 40 || v > 90) inRange = false; }
			eq(inRange, true, 'pickVel stays in [lo,hi]');
			var rv2 = makeRng(9), rv3 = makeRng(9);
			eq(pickVel(rv2, 90, 40), pickVel(rv3, 40, 90), 'pickVel tolerates lo>hi (swaps)');
			eq(pickVel(makeRng(1), 200, 200), 127, 'pickVel clamps to 127');

			// figuraMs: note-value denominator vs bpm
			approxEq(figuraMs(4, 120), 500, 'figuraMs quarter @120');
			approxEq(figuraMs(8, 120), 250, 'figuraMs eighth @120');
			approxEq(figuraMs(16, 120), 125, 'figuraMs sixteenth @120');
			eq(figuraMs(0, 0) >= 1, true, 'figuraMs guards zero args');

			// euclidGrid: first `cycle` cells == bjorklund, rest 0; rotation shifts
			var g = euclidGrid(4, 8, 0), bj = bjorklund(4, 8), match = true;
			for (i = 0; i < 8; i++) if ((g[i] ? 1 : 0) !== bj[i]) match = false;
			for (i = 8; i < 16; i++) if (g[i] !== 0) match = false;
			eq(match, true, 'euclidGrid rot 0 == bjorklund in first `cycle` cells, 0 after');
			var g1 = euclidGrid(3, 8, 1), g0 = euclidGrid(3, 8, 0), shifted = true;
			for (i = 0; i < 8; i++) if (g1[i] !== g0[(i + 1) % 8]) shifted = false;
			eq(shifted, true, 'euclidGrid rotation shifts the pattern');

			if (failures === 0) console.log('OK   checkArticulation: accentGroupAt / accentReadLen / pickVel / figuraMs / euclidGrid all correct.');
		}

		function main() {
			checkFig7Example();
			checkTermination();
			checkIsochronyOutlook();
			checkRunGate();
			checkRefinement();
			checkComplementary();
			checkLeftRight();
			checkMetallicRatios();
			checkPhiSnapValues();
			checkMarkers();
			checkConfigMorph();
			checkProbability();
			checkArticulation();
			if (failures === 0) {
				console.log('ALL OK');
				process.exitCode = 0;
			} else {
				console.error(failures + ' failure(s)');
				process.exitCode = 1;
			}
		}

		if (process.argv.indexOf('--dump-markers') !== -1) dumpMarkers();
		if (process.argv.indexOf('--check') !== -1) main();
	})();
}
