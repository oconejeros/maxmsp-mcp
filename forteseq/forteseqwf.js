// forteseqwf.js -- standalone Well-Formed (Moment-of-Symmetry) rhythm generator. Deliberately NOT
// part of forteseq2.js: a WF voice's onsets generally don't land on any step grid (that's the
// entire point at irrational r), so it can't be read through voiceRhyPat/voiceSoundsAt the way
// the Euclidean per-voice rhythm is. This is a separate device that will output plain MIDI and
// reach FORTESEQ2 (or anything else) through forteseqhub.amxd's existing Enviar path, same as any
// other MIDI source -- zero coupling to the harmony engine, zero regression risk to golden.txt.
//
// Sources: Milne, Herff, Bulger, Sethares & Dean, "XronoMorph: Algorithmic Generation of Perfectly
// Balanced and Well-Formed Rhythms" (NIME 2016); Milne, "XronoMorph: Investigating Paths Through
// Rhythmic Space" (in The Oxford Handbook of Algorithmic Music, 2019). Both papers state the
// level-to-level construction in words but explicitly defer the closed-form equations to Milne &
// Dean, Computer Music Journal 40(1):35-53 (2016), which is not in hand. The onset-COUNT
// recursion below is verified against the one worked numeric example the 2019 chapter gives
// (Fig. 7). The r-value recursion is mechanically derived from the same stated construction rule,
// not read off a source -- see checkFig7Example() and checkRefinement() for why that derivation
// is trusted anyway: the theory requires every level's onsets to be an exact subset of the next
// level's (a hierarchy only ever adds events), so an independent per-level construction that
// still nests correctly is strong evidence the formula is right, not just self-consistent.

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

function setrun(v) { running = v ? 1 : 0; if (!running) stopAllTasks(); }
function setperiod(ms) { ms = Number(ms); if (isFinite(ms)) periodMs = clampInt(ms, MIN_PERIOD_MS, MAX_PERIOD_MS); }
function setm(v) { baseM = clampInt(v, 1, MAX_MN); }
function setn(v) { baseN = clampInt(v, 0, MAX_MN); }
function setr(v) { v = Number(v); if (isFinite(v) && v >= 1) baseR = v; }
function setlevels(v) { v = Math.round(v); if (v >= 1 && v <= MAX_LEVELS) numLevels = v; }
function setlevelon(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelOn[i] = v ? 1 : 0; }
function setleveluc(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelUC[i] = v ? 1 : 0; }
function setlevellr(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelReverse[i] = v ? 1 : 0; }
function setlevelpitch(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelPitch[i] = Math.round(v); }
function setlevelvel(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelVel[i] = Math.round(v); }
function setleveldur(lv, v) { var i = levelIndex(lv); if (i < 0) return; levelDur[i] = Math.round(v); }

function stopAllTasks() {
	for (var i = 0; i < scheduledTasks.length; i++) scheduledTasks[i].cancel();
	scheduledTasks = [];
}

// makenote (downstream in the Max patch) takes a 3-item (pitch, velocity, duration) list and
// generates the matching note-off itself -- so this is the only outlet call an onset ever needs;
// there is no separate note-off Task to manage.
function fireNote(pitch, vel, dur) {
	outlet(0, pitch, vel, dur);
}

function scheduleOnset(delayMs, pitch, vel, dur) {
	var t = new Task(function () { fireNote(pitch, vel, dur); }, this);
	t.schedule(delayMs);
	scheduledTasks.push(t);
}

// Called once per period (see bang(), fed by a metro at periodMs). Rebuilding the hierarchy from
// scratch every cycle is deliberate, not lazy: per forteseq-hot-path, the real cost in this
// project is JS<->Max boundary crossings (outlet calls), not JS computation, so caching here would
// buy nothing and risks a stale-hierarchy bug when a param changes mid-cycle.
function startCycle() {
	stopAllTasks();
	if (!running) return;
	var reverseFlags = levelReverse.slice(0, Math.max(0, numLevels - 1));
	var h = wfHierarchy(baseM, baseN, baseR, numLevels, reverseFlags);
	var prevOnsets = null;
	var totalScheduled = 0;
	for (var lv = 0; lv < h.length; lv++) {
		var onsets = wfOnsets(h[lv], periodMs);
		if (levelOn[lv]) {
			var toPlay = levelUC[lv] ? wfNewOnsets(onsets, prevOnsets || [], periodMs) : onsets;
			for (var i = 0; i < toPlay.length; i++) {
				if (totalScheduled >= MAX_ONSETS_PER_CYCLE) {
					post('forteseqwf: circuit breaker -- refusing to schedule past ' + MAX_ONSETS_PER_CYCLE + ' onsets this cycle (m=' + baseM + ' n=' + baseN + ' levels=' + numLevels + ')\n');
					return;
				}
				scheduleOnset(toPlay[i], levelPitch[lv], levelVel[lv], levelDur[lv]);
				totalScheduled++;
			}
		}
		prevOnsets = onsets;
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

		function main() {
			checkFig7Example();
			checkTermination();
			checkRefinement();
			checkComplementary();
			checkLeftRight();
			checkMetallicRatios();
			if (failures === 0) {
				console.log('ALL OK');
				process.exitCode = 0;
			} else {
				console.error(failures + ' failure(s)');
				process.exitCode = 1;
			}
		}

		if (process.argv.indexOf('--check') !== -1) main();
	})();
}
