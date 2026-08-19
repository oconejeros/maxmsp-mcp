autowatch = 1;
inlets = 1;
outlets = 8;   // 0 = note events (see emitNote), 1 = current set index (1-351),
               // 2 = notes for display (names), 3 = all-voice summary for viz,
               // 4 = preset recall broadcast (tagged pairs, routed in Max),
               // 5 = voice note names for monitor,
               // 6 = current set's pitch classes (0-11, transposed by root) for circle-of-fifths,
               // 7 = Forte name and interval vector of the current set, as two symbols.
               //
               // v1 spent one outlet per voice (0/3/4/5) plus a separate articulation outlet (10)
               // that HAD to fire before the pitch so makenote's cold inlets were already loaded.
               // That made the voice count a property of the patcher wiring, and made correctness
               // depend on JS call order. Here every note leaves as one self-describing message on
               // outlet 0, so the voice count is just NUM_VOICES and nothing depends on ordering.

var currentBpm = 120;   // tracked purely for presets; actual timing is handled in Max via expr_ms
var presets = {};        // in-memory preset store: slot -> captured state object

var MAX_VOICES = 16;    // hard ceiling: every per-voice array is allocated at this size once, so
                        // changing NUM_VOICES never reallocates and never invalidates a stored preset
var NUM_VOICES = 4;     // how many of those voices are actually live; set from Max via setnumvoices()
var busId = 1;          // which FORTESEQ bus this engine broadcasts on; receivers filter on (bus, voice)

// Per-voice state. All MAX_VOICES long; entries at or above NUM_VOICES are simply never read.
// `filled` and `padVoices` are function declarations, so hoisting makes them available to these
// initialisers even though they are written further down.
var voiceOctaveList = filled(MAX_VOICES, null);  // per-voice octave PATTERN (list); a single-value list = old fixed-octave behavior
var voiceMute = filled(MAX_VOICES, 1);           // all muted by default except voice 1, set just below
var voicePos = filled(MAX_VOICES, 0);            // independent per-voice cursor into the CURRENT chord's pitch classes, advanced only by triggervoice()
var voiceExternal = filled(MAX_VOICES, 0);       // 1 = this voice is skipped by the shared clock and only sounds via triggervoice()
var voiceRangeMin = filled(MAX_VOICES, 0);       // per-voice register clamp, low bound (MIDI note); default 0-127 = no effective clamp
var voiceRangeMax = filled(MAX_VOICES, 127);     // per-voice register clamp, high bound (MIDI note)
// Independent voices. voicePos above was already a per-voice cursor, but only triggervoice()
// ever moved it: under the shared clock every voice was handed the SAME note and could differ
// only by octave, which is why four voices sounded like one voice doubled. Turning voiceIndep
// on lets the clock walk each voice's own cursor, so the voice count finally buys texture.
var voiceIndep = 0;                              // 0 = one shared note per step (historic behavior), 1 = every voice reads for itself
var voiceDegOffset = filled(MAX_VOICES, 0);      // how many DEGREES of the current set this voice sits above its own reading
var voiceDiv = filled(MAX_VOICES, 1);            // clock divider: this voice sounds on 1 of every N steps
for (var initV = 0; initV < MAX_VOICES; initV++) voiceOctaveList[initV] = [0];
voiceMute[0] = 0;

function filled(n, val) {
	var a = [];
	for (var i = 0; i < n; i++) a.push(val);
	return a;
}

// Pads a per-voice array recalled from a preset out to MAX_VOICES. A preset stored while the
// device ran fewer voices is shorter than the live arrays; without this it would leave holes
// that read as undefined the moment NUM_VOICES is raised past the stored count.
function padVoices(arr, val) {
	var a = (arr ? arr.slice() : []).slice(0, MAX_VOICES);
	while (a.length < MAX_VOICES) a.push(val);
	return a;
}
var root = 0;                      // semitone transpose applied to everything (tonic/root shift)
var masterOctave = 0;               // global octave transpose applied to everything, on top of per-voice octave and root
var patternStep = 0;               // increments once per step() call, in every mode; drives octave-list position
var DEBUG_STEP = 0;                // 1 = trace every step()/triggervoice() to the Max console. Invaluable for telling
                                   // apart "the clock is driving" from "only external triggers are driving" -- only
                                   // step() ever advances setIndex, so STEP lines missing means the set cannot change.

var NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

var sets = [];        // arrays of pitch classes (0-11), sorted by cardinality then value
var mode = 0;          // 0 = chords, 1 = arpeggio
var rotShape = 0;      // 0 = rotate once per full 351-set pass, 1 = rotate every set change
// Which degree of the set comes next. This used to be permMode, with three values; those three
// keep their numbers -- old presets, and automation lanes in saved Live sets, carry them -- and
// the shapes added later are appended after, so the reading order stays ONE control instead of
// two that would have to be kept in agreement.
var READ_RECTO = 0,      // straight ascending pass, the historic default
	READ_SUPER = 1,      // superpermutation, brute force (n <= PERM_CAP)
	READ_SUPERMIN = 2,   // superpermutation, proven minimal where one is tabulated (n <= 5)
	READ_MODOS = 3,      // one mode per pass: pass p starts on degree p and climbs past the top
	READ_COPRIMO = 4,    // skip by a fixed number of degrees, coprime with n so nothing repeats
	READ_ZIGZAG = 5,     // outside in: lowest, highest, second lowest, second highest...
	READ_URNA = 6;       // random without replacement, reshuffled once per pass
var READ_MAX = 6;
var readMode = READ_RECTO;
var readDir = 0;        // 0 = adelante, 1 = atras, 2 = alterna: pendulum over the whole pass
var coprimeSkip = 2;    // degrees to skip in READ_COPRIMO; snapped to a coprime of the cardinality
var locked = 0;        // 0 = advance through all 351, 1 = stay on lockIndex and only permute
var lockIndex = 0;     // which set (0-based) to freeze on when locked
var setIndex = 0;      // which of the 351 Tn-classes we're on
var noteIndex = 0;     // position within current set's arpeggio (arpeggio mode)
var rotation = 0;      // round-robin rotation offset for arpeggio starting note (normal mode)

var PERM_CAP = 6;          // max cardinality for full superpermutation cycling (6! = 720)
var permList = [];         // cached index permutations for one cardinality (superpermutation modes)
var permCachedForN = -1;   // which CARDINALITY permList holds. Permutations of indices depend on
                           // nothing but n, so every set of that size reuses the same list.
var permSetTag = -1;       // which setIndex the SHARED permutation walk (permIndex) is currently on
var permIndex = 0;         // which permutation in permList we're on

// Proven-minimal superpermutations for n=1..5 (0-indexed positions into the set's pcs array).
// Source: Wikipedia "Superpermutation" article, verified locally to contain every permutation
// of n elements as a contiguous substring. No proven minimum exists for n>=6 (open problem),
// so those cardinalities fall back to the brute-force cycle above.
var MINIMAL_SUPERPERMS = {
	1: [0],
	2: [0, 1, 0],
	3: [0, 1, 2, 0, 1, 0, 2, 1, 0],
	4: [0, 1, 2, 3, 0, 1, 2, 0, 3, 1, 2, 0, 1, 3, 2, 0, 1, 0, 2, 3, 1, 0, 2, 1, 3, 0, 2, 1, 0, 3, 2, 1, 0],
	5: [0, 1, 2, 3, 4, 0, 1, 2, 3, 0, 4, 1, 2, 3, 0, 1, 4, 2, 3, 0, 1, 2, 4, 3, 0, 1, 2, 0, 3, 4, 1, 2, 0, 3, 1, 4, 2, 0, 3, 1, 2, 4, 0, 3, 1, 2, 0, 4, 3, 1, 2, 0, 1, 3, 4, 2, 0, 1, 3, 2, 4, 0, 1, 3, 2, 0, 4, 1, 3, 2, 0, 1, 4, 3, 2, 0, 1, 0, 2, 3, 4, 1, 0, 2, 3, 1, 4, 0, 2, 3, 1, 0, 4, 2, 3, 1, 0, 2, 4, 3, 1, 0, 2, 1, 3, 4, 0, 2, 1, 3, 0, 4, 2, 1, 3, 0, 2, 4, 1, 3, 0, 2, 1, 4, 3, 0, 2, 1, 0, 3, 4, 2, 1, 0, 3, 2, 4, 1, 0, 3, 2, 1, 4, 0, 3, 2, 1, 0, 4, 3, 2, 1, 0]
};
var minimalPos = 0;        // position within the minimal superpermutation sequence
var minimalCachedFor = -1; // which setIndex the minimal sequence is active for

var CHORD_BASE = 48;       // C3 - low end of chord voicing
var CHORD_SPAN_OCT = 4;    // chords spread across ~4 octaves
var MELODY_BASE = 60;      // C4 - melody register (kept to one octave for a playable line)

// ---------------------------------------------------------------------------
// Articulation: accent grid + two dynamic groups
// ---------------------------------------------------------------------------
// Every note belongs to one of two groups, NORMAL (0) or ACCENT (1), decided by a
// hand-drawn grid of up to 16 cells. Each group owns its own velocity band, note
// length and rest probability, so one grid drives dynamics, duration and silence
// together instead of three unrelated mechanisms.
//
// Velocity is drawn at random inside the group's band: the distance between min and
// max IS the amount of humanisation (min == max gives a dead-mechanical line).
//
// The grid is read at (position + per-voice phase) % cycleLength. When cycleLength
// equals the set's cardinality the accents lock onto the same chord tones every pass;
// when it is coprime with the cardinality the pattern rotates against the harmony and
// a single drawn accent walks the whole chord -- long-form variation with nothing random
// in it. That is the whole point of leaving the length free.

var ACCENT_MAX = 16;
var accentGrid = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];  // 1 = accent, 0 = normal
var accentCycle = 4;         // how many leading cells of accentGrid are in play (1..ACCENT_MAX)
var accentTieToN = 0;        // 1 = ignore accentCycle and use the current set's cardinality instead
var voicePhase = filled(MAX_VOICES, 0);  // per-voice read offset into the grid, so voices accent at different points

var GROUP_NORMAL = 0, GROUP_ACCENT = 1;
var groupVelMin = [55, 95];    // low edge of each group's velocity band
var groupVelMax = [80, 115];   // high edge; velocity is uniform-random between the two
var groupDurDiv = [16, 4];     // note length as a denominator: 4 = quarter, 8 = eighth, 16 = sixteenth
var groupSilence = [0, 0];     // percent chance this group's note is dropped and becomes a rest

// The accent grid can be drawn cell by cell or generated. With euclidOn = 1 it holds E(k, n):
// k accents spread as evenly as `accentCycle` cells allow, then turned by euclidRot. Generating
// writes the same array the toggles write, so nothing downstream knows where the pattern came
// from -- and the grid is echoed back to the toggles, so the drawing never lies about it.
var euclidOn = 0;
var euclidK = 4;
var euclidRot = 0;

// --- musicalidad ------------------------------------------------------------------------
// In drum mode a pitch class stops being a note and becomes a pad: the set chooses WHICH drums
// play, and the reading order chooses when. Nothing that moves a note vertically applies, so
// the register controls sit idle while it is on -- see padFor().
var drumOn = 0;
var drumBase = 36;     // C1, the bottom-left pad of a Drum Rack

// The harmony has always changed when the reading pass ended. harmRate > 0 puts it on its own
// clock instead -- a set change every N steps, whatever the reading is doing.
var harmRate = 0;
var harmCount = 0;

// A root that walks on every harmonic change, on top of the Raiz dial. The dial stays the
// origin of the walk, so moving it transposes the whole sequence.
var rootSeqIdx = 0;      // 0 = no sequence; ROOT_RANDOM = a new root drawn each change
var rootSeqPos = 0;
var rootSeqOffset = 0;   // what the sequence is contributing right now

// How a chord is spread, and whether the next one may choose its inversion to stay near the one
// that just sounded.
var voicingMode = 0;
var voiceLead = 0;
var lastChord = null;    // the voicing that last sounded, at pitch, for that comparison

function popcount(x) {
	var c = 0;
	while (x) { c += x & 1; x >>= 1; }
	return c;
}

function rotate12(x) {
	return ((x << 1) | (x >> 11)) & 0xFFF;
}

function buildSets() {
	var seen = {};
	var canon = [];
	for (var n = 1; n < 4096; n++) {
		var best = n;
		var cur = n;
		for (var r = 0; r < 11; r++) {
			cur = rotate12(cur);
			if (cur < best) best = cur;
		}
		if (!seen[best]) {
			seen[best] = true;
			canon.push(best);
		}
	}
	canon.sort(function (a, b) {
		var ca = popcount(a), cb = popcount(b);
		if (ca !== cb) return ca - cb;
		return a - b;
	});
	for (var i = 0; i < canon.length; i++) {
		var bits = canon[i];
		var pcs = [];
		for (var p = 0; p < 12; p++) {
			if (bits & (1 << p)) pcs.push(p);
		}
		sets.push(pcs);
	}
}

// ---------------------------------------------------------------------------
// Set-class theory: Forte numbers, interval vectors, traversal order, filters
// ---------------------------------------------------------------------------
// The 351 sets this engine plays are Tn-classes: transposition only, so a major triad (047) and
// a minor one (037) are two different sets. Forte's catalogue is coarser -- 224 Tn/TnI classes,
// where a set and its inversion share one number -- so it is used here as a LABEL on top of the
// 351, never as a replacement. Two Tn-classes share a Forte number: the one whose own prime form
// IS Forte's gets the suffix A, its inversion gets B, and a set that inverts onto itself gets no
// suffix at all. That is the convention the Wikipedia list uses.

var VEC_DIGITS = "0123456789ABC";   // an interval vector entry reaches 12 in the aggregate
var PC_DIGITS = "0123456789TE";

// Normal order: the rotation of the set with the smallest span, ties going to whichever is
// packed furthest to the left. Returned transposed to start on 0, which is what every
// comparison below wants.
function zeroedNormalOrder(pcs) {
	var p = pcs.slice().sort(function (a, b) { return a - b; });
	var n = p.length;
	if (n === 0) return [];
	var best = null;
	for (var i = 0; i < n; i++) {
		var rot = [];
		for (var k = 0; k < n; k++) rot.push((((p[(i + k) % n] - p[i]) % 12) + 12) % 12);
		if (best === null || betterNormal(rot, best)) best = rot;
	}
	return best;
}

function betterNormal(a, b) {
	var n = a.length;
	if (a[n - 1] !== b[n - 1]) return a[n - 1] < b[n - 1];        // smaller span wins
	for (var i = 1; i < n; i++) if (a[i] !== b[i]) return a[i] < b[i];   // then packed left
	return false;
}

function lexLess(a, b) {
	for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] < b[i];
	return false;
}

function invertPcs(pcs) {
	var out = [];
	for (var i = 0; i < pcs.length; i++) out.push(((-pcs[i] % 12) + 12) % 12);
	return out;
}

// Forte's prime form, not Rahn's. The two disagree on exactly five classes (5-20, 6-Z29, 6-31,
// 7-20, 8-26), where Forte packs from the left and Rahn from the right: 5-20 is 01378 here and
// 01568 in Rahn. Forte's is the one that goes with Forte's numbering.
function primeFormOf(pcs) {
	var a = zeroedNormalOrder(pcs);
	var b = zeroedNormalOrder(invertPcs(pcs));
	return lexLess(b, a) ? b : a;
}

function intervalVectorOf(pcs) {
	var v = [0, 0, 0, 0, 0, 0];
	for (var i = 0; i < pcs.length; i++) {
		for (var j = i + 1; j < pcs.length; j++) {
			var d = (((pcs[j] - pcs[i]) % 12) + 12) % 12;
			if (d > 6) d = 12 - d;
			v[d - 1]++;
		}
	}
	return v;
}

function pcsDigits(pcs) {
	var s = "";
	for (var i = 0; i < pcs.length; i++) s += PC_DIGITS[pcs[i]];
	return s;
}

// Within each cardinality Forte ordered the classes by interval vector, descending. That rule
// recovers the whole numbering except for one thing: when two classes share a vector (a Z pair)
// one keeps its place and the other is pushed to the end of the cardinality, and which is which
// is historical. Those 19 are listed here -- one tetrachord, three pentachords, fifteen
// hexachords. Cardinalities 7..12 are not sorted at all; Forte numbered them as the complements
// of 5..0. Derived here and cross-checked row by row against the 224 entries of
// en.wikipedia.org/wiki/List_of_set_classes.
var LATE_Z = ["0137",
	"01247", "03458", "01258",
	"012347", "012348", "012378", "023458", "012358", "012368", "012369", "012568",
	"012569", "023469", "012469", "012479", "012579", "013479", "014679"];

var forteClass = {};   // prime-form digit string -> {vec, num, ord, card}

function buildForte() {
	var byCard = {};
	// every Tn/TnI class shows up as the prime form of some Tn-class, and sets[] holds all 351
	// of those; the empty set is the only one missing, and card 12 needs it as its complement
	var seedSets = [[]];
	for (var i = 0; i < sets.length; i++) seedSets.push(sets[i]);
	for (var s = 0; s < seedSets.length; s++) {
		var pf = primeFormOf(seedSets[s]);
		var key = pcsDigits(pf);
		if (forteClass[key]) continue;
		forteClass[key] = { pf: pf, vec: intervalVectorOf(pf), card: pf.length };
		if (!byCard[pf.length]) byCard[pf.length] = [];
		byCard[pf.length].push(key);
	}

	var isLate = {};
	for (var z = 0; z < LATE_Z.length; z++) isLate[LATE_Z[z]] = true;

	for (var card = 0; card <= 6; card++) {
		var keys = byCard[card] || [];
		var early = [], late = [];
		for (var k = 0; k < keys.length; k++) {
			if (isLate[keys[k]]) late.push(keys[k]); else early.push(keys[k]);
		}
		early.sort(function (a, b) {
			var va = forteClass[a].vec, vb = forteClass[b].vec;
			for (var q = 0; q < 6; q++) if (va[q] !== vb[q]) return vb[q] - va[q];
			return 0;
		});
		// a late member sits at the end, but the late members keep the order of their partners
		var partnerPos = function (key) {
			var v = forteClass[key].vec;
			for (var q = 0; q < early.length; q++) {
				var w = forteClass[early[q]].vec;
				if (v[0] === w[0] && v[1] === w[1] && v[2] === w[2] &&
					v[3] === w[3] && v[4] === w[4] && v[5] === w[5]) return q;
			}
			return 9999;
		};
		late.sort(function (a, b) { return partnerPos(a) - partnerPos(b); });
		var zVec = {};
		for (var m = 0; m < late.length; m++) zVec[forteClass[late[m]].vec.join(",")] = true;
		var all = early.concat(late);
		for (var n = 0; n < all.length; n++) {
			var e = forteClass[all[n]];
			e.ord = n;
			e.num = card + "-" + (zVec[e.vec.join(",")] ? "Z" : "") + (n + 1);
		}
	}

	for (var big = 7; big <= 12; big++) {
		var list = byCard[big] || [];
		for (var b = 0; b < list.length; b++) {
			var ent = forteClass[list[b]];
			var comp = [];
			for (var p = 0; p < 12; p++) {
				var found = 0;
				for (var q2 = 0; q2 < ent.pf.length; q2++) if (ent.pf[q2] === p) found = 1;
				if (!found) comp.push(p);
			}
			var cKey = pcsDigits(primeFormOf(comp));
			var cEnt = forteClass[cKey];
			ent.num = big + "-" + cEnt.num.split("-")[1];
			ent.ord = cEnt.ord;
		}
	}

	// The catalogue has a known shape, and a wrong prime-form routine would break it. Post rather
	// than throw: a device that labels sets wrongly is still a device that plays.
	var EXPECT = [1, 1, 6, 12, 29, 38, 50, 38, 29, 12, 6, 1, 1];
	var total = 0;
	for (var c2 = 0; c2 <= 12; c2++) {
		var got = (byCard[c2] || []).length;
		total += got;
		if (got !== EXPECT[c2]) post("forteseq2: WARNING cardinalidad " + c2 + " tiene " + got +
			" clases, se esperaban " + EXPECT[c2] + "\n");
	}
	if (total !== 224) post("forteseq2: WARNING catalogo de Forte con " + total + " clases, no 224\n");
}

// Per-set labels, parallel to sets[].
var setBits = [];        // bitmask of the set, for fast filtering
var setCard = [];        // cardinality
var setVec = [];         // interval vector
var setForte = [];       // "4-Z15A"
var setForteOrd = [];    // position within its cardinality, for the Forte traversal order

function buildSetLabels() {
	for (var i = 0; i < sets.length; i++) {
		var pcs = sets[i];
		var bits = 0;
		for (var j = 0; j < pcs.length; j++) bits |= (1 << pcs[j]);
		setBits.push(bits);
		setCard.push(pcs.length);
		setVec.push(intervalVectorOf(pcs));

		var tn = zeroedNormalOrder(pcs);
		var tnInv = zeroedNormalOrder(invertPcs(pcs));
		var pf = lexLess(tnInv, tn) ? tnInv : tn;
		var ent = forteClass[pcsDigits(pf)];
		var letter = "";
		var symmetric = 1;
		for (var t = 0; t < tn.length; t++) if (tn[t] !== tnInv[t]) symmetric = 0;
		if (!symmetric) letter = lexLess(tnInv, tn) ? "B" : "A";
		setForte.push(ent ? ent.num + letter : "?");
		setForteOrd.push(ent ? ent.ord : 0);
	}
}

function vecString(i) {
	var v = setVec[i], s = "<";
	for (var k = 0; k < 6; k++) s += VEC_DIGITS[v[k]];
	return s + ">";
}

// --- traversal order -------------------------------------------------------------------
// sets[] is never reordered: presets store setIndex raw, and the Set numbox names a set by its
// place in the catalogue. An alternative order is a permutation of indices laid over the top.

var ORDER_CARD = 0, ORDER_FORTE = 1, ORDER_CONS = 2, ORDER_NEIGH = 3;
var orderMode = ORDER_CARD;
var order = [];
var orderPosOf = [];

// Huron's aggregate dyadic consonance, one weight per interval class. Positive = consonant, so
// a fifth pulls a set up the list and a semitone pushes it down. Normalised by the number of
// intervals in the set, otherwise a big set would always outweigh a small one.
var IC_CONSONANCE = [-1.428, -0.582, 0.594, 0.386, 1.240, -0.453];

function consonanceOf(i) {
	var n = setCard[i];
	var pairs = n * (n - 1) / 2;
	if (pairs <= 0) return 0;
	var v = setVec[i], t = 0;
	for (var k = 0; k < 6; k++) t += IC_CONSONANCE[k] * v[k];
	return t / pairs;
}

// Walks the catalogue by common tones instead of by number: from each set the chain goes to
// whichever unvisited set shares the most pitch classes with it, so a full pass drifts through
// the harmony rather than jumping. Ties go to the smaller symmetric difference and then to the
// lower index, which keeps the chain deterministic across reloads.
function neighbourChain() {
	var used = [], chain = [];
	for (var i = 0; i < sets.length; i++) used.push(0);
	var cur = 0;
	used[0] = 1;
	chain.push(0);
	for (var s = 1; s < sets.length; s++) {
		var cb = setBits[cur], bestI = -1, bestShared = -1, bestDiff = 99;
		for (var j = 0; j < sets.length; j++) {
			if (used[j]) continue;
			var shared = popcount(cb & setBits[j]);
			var diff = popcount(cb ^ setBits[j]);
			if (shared > bestShared || (shared === bestShared && diff < bestDiff)) {
				bestShared = shared; bestDiff = diff; bestI = j;
			}
		}
		used[bestI] = 1;
		chain.push(bestI);
		cur = bestI;
	}
	return chain;
}

function buildOrder() {
	var idx = [];
	for (var i = 0; i < sets.length; i++) idx.push(i);
	if (orderMode === ORDER_FORTE) {
		idx.sort(function (a, b) {
			if (setCard[a] !== setCard[b]) return setCard[a] - setCard[b];
			if (setForteOrd[a] !== setForteOrd[b]) return setForteOrd[a] - setForteOrd[b];
			var la = setForte[a], lb = setForte[b];   // A before B
			return la < lb ? -1 : (la > lb ? 1 : 0);
		});
	} else if (orderMode === ORDER_CONS) {
		idx.sort(function (a, b) {
			var d = consonanceOf(b) - consonanceOf(a);
			if (d < 0) return -1;
			if (d > 0) return 1;
			return a - b;
		});
	} else if (orderMode === ORDER_NEIGH) {
		idx = neighbourChain();
	}
	order = idx;
	orderPosOf = [];
	for (var k = 0; k < order.length; k++) orderPosOf[order[k]] = k;
}

// --- filter ----------------------------------------------------------------------------
var filterOn = 0;
var cardMin = 1, cardMax = 12;
var maskBits = 0xFFF;    // 12 chromatic cells, C at bit 0; the toggles are absolute pitch classes
var maskMode = 0;        // 0 = set fits inside the mask, 1 = set contains the mask, 2 = shares >= k
var maskK = 1;
var maskFit = 1;         // 1 = a set may move to the transposition where it satisfies the mask
var allowed = [];
var setFit = [];         // the transposition each set was fitted to; equals root when fit is off

// Transpositions to try, nearest to the root first, so a fitted set stays as close to the key
// the root names as the mask allows.
var FIT_ORDER = [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6];

function maskOk(b) {
	if (maskMode === 0) return (b & (~maskBits) & 0xFFF) === 0;   // fits inside the mask
	if (maskMode === 1) return (b & maskBits) === maskBits;        // contains the whole mask
	return popcount(b & maskBits) >= maskK;                        // shares at least k notes
}

// The transposition the current set actually sounds at. Normally that is the root; with the mask
// fitting sets into place it is the transposition that made this set fit, which is the whole
// point of fit -- otherwise "only what fits in C major" leaves out C major.
// Root movements worth walking through. Every one starts on 0 so that switching a sequence on
// does not jump the harmony: the first chord after the switch sounds where it already was.
var ROOT_SEQUENCES = [
	null,                                       // Raiz fija: solo el dial
	[0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7],     // Cuartas: el ciclo entero
	[0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5],     // Quintas
	[0, 3, 6, 9],                               // Terceras m: el ciclo disminuido
	[0, 4, 8],                                  // Terceras M: el ciclo aumentado
	[0, 2, 4, 6, 8, 10],                        // Tonos
	[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],     // Cromatica
	[0, 6],                                     // Tritono
	[0, 5, 7]                                   // I IV V
];
var ROOT_RANDOM = ROOT_SEQUENCES.length;        // one past the list: a root drawn at random

// Called once per harmonic change, from advanceSet(), which is the only place the harmony moves.
function rootSeqAdvance() {
	if (rootSeqIdx === ROOT_RANDOM) {
		rootSeqOffset = Math.floor(Math.random() * 12);
		return;
	}
	var seq = ROOT_SEQUENCES[rootSeqIdx];
	if (!seq) { rootSeqOffset = 0; return; }
	rootSeqPos = (rootSeqPos + 1) % seq.length;
	rootSeqOffset = seq[rootSeqPos];
}

// What actually sounds as the root. The sequence is added on top of BOTH branches on purpose:
// with the mask fit on, the fit picks the transposition where the set fits the mask, and a root
// sequence then carries it away from there -- asking for a root walk is the more deliberate of
// the two requests, so it wins, and the mask stops describing what you hear.
function effRoot() {
	var base = (filterOn && maskFit && setIndex < setFit.length) ? setFit[setIndex] : root;
	return base + rootSeqOffset;
}

function rotl12(bits, r) {
	r = ((r % 12) + 12) % 12;
	if (r === 0) return bits & 0xFFF;
	return ((bits << r) | (bits >> (12 - r))) & 0xFFF;
}

// Rebuilt whenever a filter control or the root moves. The mask is written in absolute pitch
// classes -- toggle 1 is C, whatever the root is -- and sets[] stores them untransposed, so the
// comparison has to happen at the transposition that will actually sound.
function buildFilter() {
	allowed = [];
	setFit = [];
	var pass = 0;
	for (var i = 0; i < sets.length; i++) {
		var ok = 1;
		var fit = root;
		if (filterOn) {
			if (setCard[i] < cardMin || setCard[i] > cardMax) ok = 0;
			if (ok && maskFit) {
				// Sets are stored at one canonical rotation each, which is rarely the rotation
				// that fits: the diatonic class is stored as 013568T, so testing it in place
				// would keep the major scale out of "fits inside C major". Move it instead.
				ok = 0;
				for (var d = 0; d < FIT_ORDER.length; d++) {
					var t = (((root + FIT_ORDER[d]) % 12) + 12) % 12;
					if (maskOk(rotl12(setBits[i], t))) { ok = 1; fit = t; break; }
				}
			} else if (ok) {
				ok = maskOk(rotl12(setBits[i], root)) ? 1 : 0;
			}
		}
		allowed.push(ok);
		setFit.push(fit);
		pass += ok;
	}
	if (pass === 0) {
		// A filter nothing passes would freeze the sequence on whatever set happened to be
		// playing, which reads as a broken device. Falling back to the whole catalogue at least
		// keeps it moving, and the console says why.
		post("forteseq2: el filtro no deja pasar ningun set, se ignora\n");
		for (var k = 0; k < allowed.length; k++) allowed[k] = 1;
	}
}

// Moves to the next playable set and reports whether the catalogue wrapped, which is what the
// rotation-per-pass option keys off. Order and filter both live here, so every caller in step()
// gets them without knowing about either.
function advanceSet() {
	var total = order.length;
	if (!total) return 0;
	var pos = orderPosOf[setIndex];
	if (pos === undefined) pos = 0;
	for (var i = 1; i <= total; i++) {
		var raw = pos + i;
		var p = raw % total;
		if (allowed[order[p]]) {
			setIndex = order[p];
			rootSeqAdvance();   // the only place the harmony moves, so the only place the root walks
			return raw >= total ? 1 : 0;
		}
	}
	return 0;
}

// The harmony follows the reading -- a set change when the pass ends, how the device has always
// worked -- or runs on its own clock. Only one of the two ever moves the catalogue: with
// harmRate > 0 the end of a pass advances nothing, so a reading order that takes 720 steps to
// finish can sit over a chord that changes every 4.
function advanceOnPass() {
	if (harmRate > 0) return 0;
	return advanceSet();
}

// The other half of that: the clock-driven set change, counted in steps. `rotation` is bumped
// here for the same reason the pass-driven path bumps it, since this is now where the set moves.
function harmonyStep() {
	if (harmRate <= 0 || locked) return;
	harmCount++;
	if (harmCount < harmRate) return;
	harmCount = 0;
	var wrapped = advanceSet();
	if (rotShape === 1 || (wrapped && rotShape === 0)) rotation++;
}

function emitSetReadouts(displayPcs) {
	outlet(1, setIndex + 1);
	outlet(2, displayNotes(displayPcs));
	outlet(7, [setForte[setIndex], vecString(setIndex)]);
}

// --- setters ---------------------------------------------------------------------------

function setorder(m) {
	m = Math.round(m);
	if (m < 0) m = 0;
	if (m > 3) m = 3;
	orderMode = m;
	buildOrder();
}

function setfilter(f) {
	filterOn = f ? 1 : 0;
	buildFilter();
}

// Two setters rather than one taking a pair: Live restores parameters one at a time on set
// reload, so a combined message would pair whichever arrived first with the other's stale value.
function setcardmin(n) {
	n = Math.round(n);
	if (n < 1) n = 1;
	if (n > 12) n = 12;
	cardMin = n;
	buildFilter();
}

function setcardmax(n) {
	n = Math.round(n);
	if (n < 1) n = 1;
	if (n > 12) n = 12;
	cardMax = n;
	buildFilter();
}

// setmask <c1> ... <c12>: the whole mask arrives as one list, so a redraw can never leave it
// half applied between two notes -- same reason setaccentgrid takes a list.
function setmask() {
	var bits = 0;
	for (var i = 0; i < 12 && i < arguments.length; i++) if (arguments[i]) bits |= (1 << i);
	maskBits = bits;
	buildFilter();
}

function setmaskmode(m) {
	m = Math.round(m);
	if (m < 0) m = 0;
	if (m > 2) m = 2;
	maskMode = m;
	buildFilter();
}

// 1 = a set that does not satisfy the mask where it sits may move to a transposition where it
// does, and then plays there. 0 = it is tested exactly where it sits, which is stricter and
// keeps the root meaning what it says, at the cost of letting very few sets through.
function setmaskfit(f) {
	maskFit = f ? 1 : 0;
	buildFilter();
}

function setmaskk(k) {
	k = Math.round(k);
	if (k < 1) k = 1;
	if (k > 12) k = 12;
	maskK = k;
	buildFilter();
}

buildSets();
buildForte();
buildSetLabels();
buildOrder();
buildFilter();

function loadbang() {
	post("forteseq2: built " + sets.length + " Tn-classes over 224 Forte classes, bus " + busId +
		", " + NUM_VOICES + "/" + MAX_VOICES + " voices\n");
}

function setmode(m) {
	mode = m ? 1 : 0;
	noteIndex = 0;
}

function setlock(l) {
	locked = l ? 1 : 0;
}

function setlockindex(i) {
	var idx = Math.round(i) - 1;   // live.numbox now outputs the real 1-351 value directly
	if (idx < 0) idx = 0;
	if (idx > sets.length - 1) idx = sets.length - 1;
	lockIndex = idx;
	setIndex = idx;   // jump there immediately even if not locked, so picking a set previews it right away;
	                  // lockIndex is what actually keeps it pinned once locked is turned on

	// update the readouts right now instead of waiting for the next clock tick/trigger.
	// NOTE: deliberately NOT calling emitVoices() here - that sends real notes out the
	// note bus and made picking a set in the numbox audibly fire a stray note.
	// Only the set-level index/notes readouts preview immediately; the per-voice MIDI
	// monitor only updates from an actual clock tick/trigger, same as real playback.
	emitSetReadouts(sets[setIndex]);
}

function setvoiceoctavelist() {
	var v = Math.round(arguments[0]);
	var idx = v - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	var list = [];
	for (var i = 1; i < arguments.length; i++) {
		var n = Math.round(arguments[i]);
		if (isFinite(n)) list.push(n);   // skip NaN/garbage from partial/malformed input (e.g. mid-typing)
	}
	if (list.length === 0) {
		post("setvoiceoctavelist: ignored invalid/empty input for voice " + v + "\n");
		return;   // keep the previous valid list rather than corrupting it
	}
	voiceOctaveList[idx] = list;
}

// Simple generator: every "everyN" notes, step one octave toward "range", starting from
// "base"; wraps back to base after.
// e.g. everyN=4, range=2  -> [0,0,0,0, 1,1,1,1, 2,2,2,2] (then repeats).
// e.g. everyN=4, range=-2 -> [0,0,0,0, -1,-1,-1,-1, -2,-2,-2,-2] (then repeats).
function setvoiceoctavesimple(v, everyN, range, steps, base) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	everyN = Math.round(everyN);
	range = Math.round(range);
	if (everyN < 1) everyN = 1;
	// steps = how many octave alterations happen between 0 and range (default: one per
	// integer octave, i.e. the old fixed behavior). Lower steps skips intermediate octaves
	// so the climb reaches "range" in fewer, bigger jumps instead of always going 1 at a time.
	if (steps === undefined || steps === null) steps = Math.abs(range);
	steps = Math.round(steps);
	if (steps < 1) steps = 1;
	// base = the octave the pattern starts from, so a voice can sit an octave up while it
	// climbs. It replaces the old setvoiceoctavelist control: base=n with range=0 collapses
	// to the fixed list [n], which is exactly what that control used to send.
	if (base === undefined || base === null) base = 0;
	base = Math.round(base);

	var list = [];
	var lastLevel = null;
	for (var i = 0; i <= steps; i++) {
		var level = Math.round(i * range / steps);
		if (level === lastLevel) continue; // collapse steps finer than the integer octave grid
		lastLevel = level;
		for (var j = 0; j < everyN; j++) list.push(level + base);
	}
	voiceOctaveList[idx] = list;
	post("voice " + v + " octave pattern: every " + everyN + " notes, range " + range + ", steps " + steps + ", base " + base + " -> [" + list.join(",") + "]\n");
}

// Fires ONE voice from an external rhythmic MIDI trigger, independent of the shared clock.
// Always plays a note from the CURRENTLY active chord (same setIndex/pcs as every other voice)
// but walks its own pitch-class + octave-pattern cursor forward one step per call, so each
// voice's line advances at whatever rate its own trigger arrives, decoupled from the others.
function triggervoice(v) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	if (voiceMute[idx]) return;
	var pcs = sets[setIndex];
	if (!pcs || pcs.length === 0) return;

	var pos = voicePos[idx];
	var n = pcs.length;
	var pc;

	// Walk the same permuted order the shared clock uses, so an externally triggered
	// voice permutes too instead of falling back to a plain linear pass through the
	// chord. Not gated on `mode` (Acordes/Arp): triggervoice always emits one note per
	// trigger, so only the reading order is meaningful here. degreeAt() is the only copy of that
	// reading order, shared with the clock-driven voices, so a voice sounds the same whether
	// the clock or an external trigger moved it.
	pc = pitchForDegree(pcs, degreeAt(n, pos) + voiceDegOffset[idx]);

	var list = voiceOctaveList[idx];
	var oct = list[pos % list.length];
	var shift = oct * 12 + effRoot() + masterOctave * 12;
	var vmin = voiceRangeMin[idx], vmax = voiceRangeMax[idx];
	var shifted = drumOn ? padFor(pc) : foldToRange(MELODY_BASE + pc + shift, vmin, vmax);

	voicePos[idx] = pos + 1;

	// Read the accent grid at this voice's OWN cursor, not patternStep: an externally
	// triggered voice advances at its trigger's rate, so its accents have to follow that
	// rate too or they would drift against the notes they are supposed to be shaping.
	// The cursor still advances on a rest, so silences occupy a step instead of being skipped.
	var art = articulationFor(idx, pos, n);

	if (DEBUG_STEP) {
		// NOTE: triggervoice() never advances setIndex -- only step() does. If notes are
		// arriving here and STEP lines are absent, the PC set cannot change by design.
		post("TRIG v" + (idx + 1) + " | set=" + (setIndex + 1) + " n=" + n +
			" pos=" + pos + " -> note " + shifted +
			" | grp=" + (art.group ? "ACC" : "nrm") + " vel=" + art.vel +
			" dur=" + Math.round(art.dur) + (art.rest ? " REST" : "") + "\n");
	}
	if (art.rest) return;

	emitNote(idx, art, shifted);
}

// The far end of the Hub's Enviar mode: [receive FORTESEQ_TRIG] -> [prepend trig] delivers
// (bus, voice) here for every note a Hub in that mode plays. The bus test lives in JS rather
// than in the patcher because busId already lives here -- a patcher-side [== ] fed from the bus
// numbox would be a SECOND copy of the address, and the two would disagree the moment one is
// set without the other. Wrong-bus triggers are dropped silently on purpose: every engine in
// the Live set sees every trigger, so a post() here would flood the console at note rate.
// triggervoice() does the rest of the vetting (voice in range, not muted).
function trig(b, v) {
	if (Math.round(b) !== busId) return;
	triggervoice(v);
}

// One note event per message, ALWAYS exactly five atoms:
//     <bus> <voice 1-N> <velocity> <duration ms> <pitch>
// A chord goes out as one message per pitch rather than one message with a pitch list. Two
// reasons, both learned from v1: a fixed-length payload makes the receiver a plain [unpack],
// with no zl slice / zl reg dance to peel a variable tail; and makenote's list method reads
// atom 2 of any list as the VELOCITY, so v1's chord mode -- which sent [p1 p2 p3 ...] straight
// into makenote -- played only p1, at a velocity equal to p2, silently discarding both the
// rest of the chord and the articulation velocity that had just been loaded. Rounding the
// duration keeps every atom an int, which sidesteps the float-truncation traps in [unpack].
function emitNote(voiceIdx, art, pitches) {
	var list = (pitches instanceof Array) ? pitches : [pitches];
	var dur = Math.round(art.dur);
	for (var i = 0; i < list.length; i++) {
		outlet(0, [busId, voiceIdx + 1, art.vel, dur, list[i]]);
	}
}

// Which bus this engine broadcasts on. Purely an address: it changes nothing about what the
// engine generates, which is why it is deliberately kept out of the preset store -- same call
// as io_mode in v1. Two engines sharing a bus is a legitimate setup (they layer), but two
// engines sharing a bus AND a voice number will double-trigger the same receiver.
function setbus(b) {
	var n = Math.round(b);
	if (n < 1) n = 1;
	busId = n;
}

// Voice count as a runtime value. v1 could not do this at all: four outlets meant four voices,
// full stop. Raising it activates voices that were already allocated and already muted, so
// nothing new sounds until its mute is lifted.
function setnumvoices(n) {
	n = Math.round(n);
	if (n < 1) n = 1;
	if (n > MAX_VOICES) n = MAX_VOICES;
	NUM_VOICES = n;
	post("forteseq2: " + NUM_VOICES + " voices active (max " + MAX_VOICES + ")\n");
}

function setvoicemute(v, m) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceMute[idx] = m ? 1 : 0;
}

function setvoiceexternal(v, e) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceExternal[idx] = e ? 1 : 0;
}

// 0 = every clock-driven voice gets the same note and can differ only by octave and register
// (what the device did until now). 1 = every voice reads the set through its own cursor,
// degree offset and clock divider. Deliberately global rather than per-voice: with a degree
// offset of 0 and a divider of 1 an independent voice already reproduces the shared reading,
// so a per-voice switch would only be a second way of saying the same thing.
function setvoiceindep(x) {
	voiceIndep = x ? 1 : 0;
}

// How many degrees of the CURRENT set this voice sits above its own reading. Degrees, not
// semitones: offset 2 is "a third within this set", so the interval re-spells itself as the
// harmony changes instead of dragging one fixed transposition through every chord. Offsets
// 0,1,2,3 across four voices give a four-part voicing of whatever set is playing; negative
// values put the voice below. Voices cannot cross, because pitchForDegree() adds an octave
// every time the index runs past the end of the set.
function setvoicedegoffset(v, d) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	d = Math.round(d);
	if (!isFinite(d)) return;
	voiceDegOffset[idx] = d;
}

// Clock divider: the voice sounds on one step out of every N, and its cursor advances only when
// it sounds. This is what turns independent cursors from parallel motion into counterpoint,
// since voices on different dividers drift apart and meet again on their common multiple.
// Phase comes from the global patternStep rather than a per-voice counter, so every divider
// lands together on the step where the pattern restarts instead of drifting off the grid.
function setvoicediv(v, d) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	d = Math.round(d);
	if (d < 1) d = 1;
	voiceDiv[idx] = d;
}

// Register clamp per voice: min + span (like Tritonet's Min/Range), so max is always >= min.
function setvoicerange(v, min, span) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	min = Math.round(min);
	span = Math.round(span);
	if (span < 0) span = 0;
	voiceRangeMin[idx] = min;
	voiceRangeMax[idx] = min + span;
}

// Folds a note into [min,max] by transposing whole octaves (never remaps pitch class), same
// principle as Tritonet's MinLimit/MaxLimit fold, but done as a plain loop instead of the
// division-based Max patch cords since we're already in JS.
function foldToRange(note, min, max) {
	if (max < min) max = min;
	var n = Math.round(note);
	while (n < min) n += 12;
	while (n > max) n -= 12;
	return n;
}

// Register templates: one [min, max] pair per voice, in sounding MIDI notes, top voice first --
// V1 is the soprano and V4 the bass, the way a score is scored. These are working ranges, not
// the extremes of each instrument: what a player covers comfortably all evening.
// Entry 0 applies nothing, so the menu in Live can carry its own name in its first item.
var RANGE_TEMPLATES = [
	null,                                                        // Rango: the menu's own label
	[[0, 127]],                                                  // Libre: no clamp at all
	[[60, 81], [55, 74], [48, 67], [40, 60]],                    // SATB
	[[55, 93], [55, 84], [48, 79], [36, 69]],                    // Cuerdas: vln I, vln II, vla, vc
	[[60, 96], [58, 88], [50, 86], [34, 70]],                    // Maderas: fl, ob, cl, fg
	[[55, 82], [41, 77], [40, 70], [28, 58]],                    // Metales: tpt, cor, tbn, tuba
	[[72, 96], [60, 84], [48, 72], [21, 48]],                    // Teclado: cuatro manos de piano
	[[84, 108], [60, 84], [36, 60], [24, 48]],                   // Ancho: una octava por voz, sin cruce
	[[60, 72], [60, 72], [60, 72], [60, 72]]                     // Cluster: las cuatro en la misma octava
];

// Writes a whole template into the per-voice clamps and echoes each pair back to its strip, so
// the Min/Span boxes show what is actually in force. Nothing is locked: a voice can be nudged
// afterwards, and then the menu is only a record of what was last applied.
function setrangetemplate(t) {
	t = Math.round(t);
	var tpl = (t >= 0 && t < RANGE_TEMPLATES.length) ? RANGE_TEMPLATES[t] : null;
	if (!tpl) return;
	for (var v = 0; v < NUM_VOICES; v++) {
		// More voices than the template names wraps back to the top rather than leaving the
		// extra ones behind: the device caps at four, the engine allows sixteen.
		var pair = tpl[v % tpl.length];
		voiceRangeMin[v] = pair[0];
		voiceRangeMax[v] = pair[1];
		outlet(4, ["v" + (v + 1) + "range", pair[0], pair[1] - pair[0]]);
	}
}

function setdrum(x) {
	drumOn = x ? 1 : 0;
}

function setdrumbase(b) {
	var n = Math.round(b);
	if (!isFinite(n) || n < 0) n = 0;
	if (n > 115) n = 115;   // the top pad of a twelve-wide set has to stay inside MIDI
	drumBase = n;
}

function setharmrate(r) {
	var n = Math.round(r);
	if (!isFinite(n) || n < 0) n = 0;
	if (n > 64) n = 64;
	harmRate = n;
	harmCount = 0;   // a new rate counts from here, not from wherever the old one had got to
}

function setrootseq(i) {
	var n = Math.round(i);
	if (!isFinite(n) || n < 0 || n > ROOT_RANDOM) n = 0;
	rootSeqIdx = n;
	rootSeqPos = 0;
	// Every sequence begins on 0, so switching one on leaves the harmony where it stands and the
	// walk starts at the next set change. Azar is the exception and has to draw its first root.
	rootSeqOffset = (n === ROOT_RANDOM) ? Math.floor(Math.random() * 12) : 0;
}

function setvoicing(m) {
	var n = Math.round(m);
	if (!isFinite(n) || n < 0 || n > VOICING_OPEN) n = 0;
	voicingMode = n;
	lastChord = null;   // the shape changed, so the chord to lead from is no longer this one
}

function setvoicelead(x) {
	voiceLead = x ? 1 : 0;
	lastChord = null;   // start the chain from the next chord rather than from a stale one
}

function setroot(r) {
	root = Math.round(r);
	buildFilter();   // the mask is absolute, so what fits inside it changes when the root moves
}

function setmasteroctave(o) {
	masterOctave = Math.round(o);
}

function setbpmtrack(b) {
	currentBpm = b;
}

function storepreset(slot) {
	slot = Math.round(slot);
	if (slot < 1) return;
	presets[slot] = {
		mode: mode,
		rotShape: rotShape,
		permMode: readMode,       // stored under its old key: a slot stays readable both ways
		readDir: readDir,
		coprimeSkip: coprimeSkip,
		locked: locked,
		lockIndex: lockIndex,
		root: root,
		masterOctave: masterOctave,
		bpm: currentBpm,
		voiceOctaveList: voiceOctaveList.map(function (l) { return l.slice(); }),
		voiceMute: voiceMute.slice(),
		voiceExternal: voiceExternal.slice(),
		voiceIndep: voiceIndep,
		voiceDegOffset: voiceDegOffset.slice(),
		voiceDiv: voiceDiv.slice(),
		voicePos: voicePos.slice(),      // part of the sequence position once voices read independently
		voiceRangeMin: voiceRangeMin.slice(),
		voiceRangeMax: voiceRangeMax.slice(),
		orderMode: orderMode,
		filterOn: filterOn,
		cardMin: cardMin,
		cardMax: cardMax,
		maskBits: maskBits,
		maskMode: maskMode,
		maskK: maskK,
		maskFit: maskFit,
		accentGrid: accentGrid.slice(),
		accentCycle: accentCycle,
		accentTieToN: accentTieToN,
		euclidOn: euclidOn,
		euclidK: euclidK,
		euclidRot: euclidRot,
		voicePhase: voicePhase.slice(),
		groupVelMin: groupVelMin.slice(),
		groupVelMax: groupVelMax.slice(),
		groupDurDiv: groupDurDiv.slice(),
		groupSilence: groupSilence.slice(),
		drumOn: drumOn,
		drumBase: drumBase,
		harmRate: harmRate,
		rootSeqIdx: rootSeqIdx,
		rootSeqPos: rootSeqPos,
		voicingMode: voicingMode,
		voiceLead: voiceLead,
		// sequence position, so recall picks up exactly where it was instead of restarting
		setIndex: setIndex,
		noteIndex: noteIndex,
		rotation: rotation,
		permIndex: permIndex,
		minimalPos: minimalPos,
		patternStep: patternStep
	};
	post("preset: stored slot " + slot + "\n");
}

function recallpreset(slot) {
	slot = Math.round(slot);
	var p = presets[slot];
	if (!p) {
		post("preset: slot " + slot + " is empty\n");
		return;
	}
	mode = p.mode;
	rotShape = p.rotShape;
	readMode = p.permMode;
	// Slots stored before the other reading orders existed have neither field; the fallbacks are
	// forward motion and the default skip, which is what such a slot played.
	readDir = p.readDir || 0;
	coprimeSkip = p.coprimeSkip || 2;
	locked = p.locked;
	lockIndex = p.lockIndex;
	root = p.root;
	masterOctave = p.masterOctave || 0;
	currentBpm = p.bpm;
	voiceOctaveList = padVoices(p.voiceOctaveList, null).map(
		function (l) { return l ? l.slice() : [0]; });
	voiceMute = padVoices(p.voiceMute, 1);
	voiceExternal = padVoices(p.voiceExternal, 0);
	// Slots stored before independent voices existed carry none of these four; the fallbacks
	// are exactly the shared-note behavior such a slot was saved as.
	voiceIndep = p.voiceIndep || 0;
	voiceDegOffset = padVoices(p.voiceDegOffset, 0);
	voiceDiv = padVoices(p.voiceDiv, 1);
	voicePos = padVoices(p.voicePos, 0);
	voiceRangeMin = padVoices(p.voiceRangeMin, 0);
	voiceRangeMax = padVoices(p.voiceRangeMax, 127);

	// Slots stored before the theory layer carry no order or filter; the fallbacks are the plain
	// catalogue order with no filter, which is what such a slot played.
	orderMode = p.orderMode || 0;
	filterOn = p.filterOn || 0;
	cardMin = p.cardMin || 1;
	cardMax = p.cardMax || 12;
	maskBits = (p.maskBits === undefined) ? 0xFFF : p.maskBits;
	maskMode = p.maskMode || 0;
	maskK = p.maskK || 1;
	maskFit = (p.maskFit === undefined) ? 1 : p.maskFit;
	buildOrder();
	buildFilter();

	// Presets stored before the articulation engine existed have none of these fields; fall
	// back to the module defaults so an old slot recalls as the plain fixed-velocity device
	// it was saved as, instead of throwing.
	accentGrid = p.accentGrid ? p.accentGrid.slice() : [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
	accentCycle = p.accentCycle || 4;
	accentTieToN = p.accentTieToN || 0;
	// A slot stored before the generator existed carries a hand-drawn grid and nothing else; off
	// is the only reading that leaves that grid alone.
	euclidOn = p.euclidOn || 0;
	euclidK = p.euclidK || 4;
	euclidRot = p.euclidRot || 0;
	voicePhase = padVoices(p.voicePhase, 0);
	groupVelMin = p.groupVelMin ? p.groupVelMin.slice() : [55, 95];
	groupVelMax = p.groupVelMax ? p.groupVelMax.slice() : [80, 115];
	groupDurDiv = p.groupDurDiv ? p.groupDurDiv.slice() : [16, 4];
	groupSilence = p.groupSilence ? p.groupSilence.slice() : [0, 0];
	// A slot stored before this phase existed played notes, on the reading's own harmonic rhythm,
	// with a fixed root and the historic spread -- which is exactly what all six defaults are.
	drumOn = p.drumOn || 0;
	drumBase = (p.drumBase === undefined) ? 36 : p.drumBase;
	harmRate = p.harmRate || 0;
	harmCount = 0;
	rootSeqIdx = p.rootSeqIdx || 0;
	rootSeqPos = p.rootSeqPos || 0;
	// The offset is derived rather than stored: it is whatever the sequence says at that position,
	// so a slot cannot recall a root the sequence would never produce.
	var rseq = ROOT_SEQUENCES[rootSeqIdx];
	rootSeqOffset = rseq ? rseq[rootSeqPos % rseq.length] : 0;
	voicingMode = p.voicingMode || 0;
	voiceLead = p.voiceLead || 0;
	lastChord = null;   // the chord that sounded before the recall is not the one to lead from

	// restore sequence position exactly, so recall continues instead of restarting
	setIndex = p.setIndex;
	noteIndex = p.noteIndex;
	rotation = p.rotation;
	permIndex = p.permIndex;
	minimalPos = p.minimalPos;
	patternStep = p.patternStep;
	// rebuild the permutation caches for the restored setIndex so permIndex/minimalPos stay valid
	// (without this, step()'s cache-miss check would silently reset them back to 0)
	var restoredPcs = sets[setIndex];
	ensurePermCache(restoredPcs.length);
	permSetTag = setIndex;
	minimalCachedFor = setIndex;

	outlet(4, ["indep", voiceIndep]);
	outlet(4, ["order", orderMode]);
	outlet(4, ["filter", filterOn]);
	outlet(4, ["cardmin", cardMin]);
	outlet(4, ["cardmax", cardMax]);
	outlet(4, ["maskmode", maskMode]);
	outlet(4, ["maskk", maskK]);
	outlet(4, ["maskfit", maskFit]);
	var maskCells = ["mask"];
	for (var mc = 0; mc < 12; mc++) maskCells.push((maskBits & (1 << mc)) ? 1 : 0);
	outlet(4, maskCells);
	outlet(4, ["masteroct", masterOctave]);
	outlet(4, ["mode", mode]);
	outlet(4, ["shape", rotShape]);
	outlet(4, ["permmode", readMode]);
	outlet(4, ["readdir", readDir]);
	outlet(4, ["coprime", coprimeSkip]);
	outlet(4, ["locked", locked]);
	outlet(4, ["lockindex", lockIndex + 1]);
	outlet(4, ["root", root]);
	outlet(4, ["bpm", currentBpm]);
	outlet(4, ["accentcycle", accentCycle]);
	outlet(4, ["accenttie", accentTieToN]);
	outlet(4, ["euclid", euclidOn]);
	outlet(4, ["euclidk", euclidK]);
	outlet(4, ["euclidrot", euclidRot]);
	outlet(4, ["drum", drumOn]);
	outlet(4, ["drumbase", drumBase]);
	outlet(4, ["harmrate", harmRate]);
	outlet(4, ["rootseq", rootSeqIdx]);
	outlet(4, ["voicing", voicingMode]);
	outlet(4, ["voicelead", voiceLead]);
	outlet(4, ["accentgrid"].concat(accentGrid));
	for (var g = GROUP_NORMAL; g <= GROUP_ACCENT; g++) {
		outlet(4, ["g" + g + "vel", groupVelMin[g], groupVelMax[g]]);
		outlet(4, ["g" + g + "dur", groupDurDiv[g]]);
		outlet(4, ["g" + g + "silence", groupSilence[g]]);
	}
	for (var v = 0; v < NUM_VOICES; v++) {
		outlet(4, ["v" + (v + 1) + "octlist"].concat(voiceOctaveList[v]));
		outlet(4, ["v" + (v + 1) + "mute", voiceMute[v]]);
		outlet(4, ["v" + (v + 1) + "external", voiceExternal[v]]);
		outlet(4, ["v" + (v + 1) + "range", voiceRangeMin[v], voiceRangeMax[v] - voiceRangeMin[v]]);
		outlet(4, ["v" + (v + 1) + "phase", voicePhase[v]]);
		outlet(4, ["v" + (v + 1) + "grado", voiceDegOffset[v]]);
		outlet(4, ["v" + (v + 1) + "div", voiceDiv[v]]);
	}
	post("preset: recalled slot " + slot + "\n");
}

// A pitch class as a Drum Rack pad. Nothing that moves a note vertically applies: the octave
// pattern, the master octave and the register clamp all exist to put a note in a register, and
// a rack has no registers -- its rows are unrelated instruments, so folding a note into a range
// would land on a different drum instead of on the same one lower down. The root does count: it
// slides the whole set across the rack, which is the one transposition that means something here.
function padFor(pc) {
	var pad = drumBase + ((((Math.round(pc) + effRoot()) % 12) + 12) % 12);
	return pad > 127 ? 127 : pad;
}

function noteName(midi) {
	var m = Math.round(midi);
	var pc = ((m % 12) + 12) % 12;
	var octave = Math.floor(m / 12) - 1;   // MIDI 60 = C4
	return NOTE_NAMES[pc] + octave;
}

// Decides which group a voice's note belongs to at a given sequence position, and resolves
// that into the concrete velocity / length / rest verdict for the note about to play.
// `n` is the current set's cardinality, consulted only when the cycle is tied to it.
function articulationFor(v, pos, n) {
	var len = accentTieToN ? n : accentCycle;
	if (!(len > 0)) len = 1;
	if (len > ACCENT_MAX) len = ACCENT_MAX;

	var idx = (Math.round(pos) + voicePhase[v]) % len;
	if (idx < 0) idx += len;
	var g = accentGrid[idx] ? GROUP_ACCENT : GROUP_NORMAL;

	var lo = groupVelMin[g], hi = groupVelMax[g];
	if (lo > hi) { var swap = lo; lo = hi; hi = swap; }   // tolerate the two dials crossing
	var vel = lo + Math.floor(Math.random() * (hi - lo + 1));
	if (vel < 1) vel = 1;       // velocity 0 is a note-off, never a note
	if (vel > 127) vel = 127;

	// Length comes from a note-value denominator against the BPM, not from a fraction of the
	// step interval -- that is precisely what unhooks articulation from the BPM dial. div 4 is
	// one beat, so ms = (60000/bpm) * 4/div.
	var bpm = currentBpm > 0 ? currentBpm : 120;
	var div = groupDurDiv[g] > 0 ? groupDurDiv[g] : 16;

	return {
		group: g,
		vel: vel,
		dur: (60000 / bpm) * (4 / div),
		rest: groupSilence[g] > 0 && (Math.random() * 100) < groupSilence[g]
	};
}

function emitVoices(noteData) {
	var summary = [];
	var names = [];
	// cardinality of the set currently sounding, for the "tie the accent cycle to n" option
	var curSet = sets[setIndex];
	var card = curSet ? curSet.length : 1;
	for (var v = 0; v < NUM_VOICES; v++) {
		if (voiceMute[v] || voiceExternal[v]) { summary.push(0); names.push("--"); continue; }
		var list = voiceOctaveList[v];
		var oct = list[patternStep % list.length];
		var shift = oct * 12 + effRoot() + masterOctave * 12;
		var shifted;
		var repr;
		var vmin = voiceRangeMin[v], vmax = voiceRangeMax[v];
		if (noteData instanceof Array) {
			shifted = [];
			for (var i = 0; i < noteData.length; i++) {
				shifted.push(drumOn ? padFor(noteData[i]) : foldToRange(noteData[i] + shift, vmin, vmax));
			}
			repr = shifted[0];
		} else {
			shifted = drumOn ? padFor(noteData) : foldToRange(noteData + shift, vmin, vmax);
			repr = shifted;
		}
		// A rest reads as "--" in the monitor, same as a muted or external voice: from the
		// listener's side nothing sounds, and the readout should not claim otherwise.
		var art = articulationFor(v, patternStep, card);
		if (art.rest) { summary.push(0); names.push("--"); continue; }

		summary.push(repr);
		names.push(noteName(repr));
		emitNote(v, art, shifted);
	}
	outlet(3, summary);
	var labelled = [];
	for (var m = 0; m < NUM_VOICES; m++) labelled.push("V" + (m + 1) + ":" + names[m]);
	outlet(5, labelled);
}

var VOICING_SPREAD = 0, VOICING_CLOSED = 1, VOICING_DROP2 = 2, VOICING_DROP3 = 3,
	VOICING_DROP24 = 4, VOICING_OPEN = 5;

// The set stacked upward from one of its members. Rotating it puts a different member in the
// bass and carries the ones that wrapped round up an octave, which is exactly what an inversion
// is -- and it is the only thing a voicing can vary, since the pitch classes themselves are fixed.
function closedStack(pcs, rot) {
	var n = pcs.length;
	var out = [CHORD_BASE + pcs[rot % n]];
	for (var i = 1; i < n; i++) {
		var p = CHORD_BASE + pcs[(rot + i) % n];
		while (p <= out[i - 1]) p += 12;
		out.push(p);
	}
	return out;
}

// Every mode is a rearrangement of that same closed stack, which is what makes them comparable
// when the voice leading has to choose between them. Spread is the historic one: with rot 0 it
// reproduces the old expandChord() note for note, so a set saved before this existed sounds the
// same. A drop is undefined below its own size -- a triad has no fourth voice to drop -- and
// falls back to the closed stack rather than to silence. A drop needs one more voice than the
// one it drops, or the note it moves is the bass and the chord just sinks an octave.
function applyVoicing(st, m) {
	var n = st.length, out = st.slice(), k;
	if (m === VOICING_SPREAD) {
		for (k = 0; k < n; k++) out[k] = st[k] + ((n > 1) ? Math.floor(k * CHORD_SPAN_OCT / n) : 0) * 12;
	} else if (m === VOICING_OPEN) {
		for (k = 1; k < n; k += 2) out[k] += 12;      // one up, one in place: an interlocked spread
	} else if (m === VOICING_DROP2 && n >= 3) {
		out[n - 2] -= 12;
	} else if (m === VOICING_DROP3 && n >= 4) {
		out[n - 3] -= 12;
	} else if (m === VOICING_DROP24 && n >= 4) {
		out[n - 2] -= 12;
		out[n - 4] -= 12;
	}
	out.sort(function (a, b) { return a - b; });
	return out;
}

// How far two chords are from each other: every note's distance to the nearest note in the other
// chord, counted in both directions. Nearest-note rather than voice against voice because the
// two chords rarely have the same number of notes -- a triad following a nine-note set still has
// to be scored, and pairing them up by position would score it as nonsense.
function chordDistance(a, b) {
	var total = 0, i, j, d, best;
	for (i = 0; i < a.length; i++) {
		best = 1e9;
		for (j = 0; j < b.length; j++) { d = a[i] > b[j] ? a[i] - b[j] : b[j] - a[i]; if (d < best) best = d; }
		total += best;
	}
	for (j = 0; j < b.length; j++) {
		best = 1e9;
		for (i = 0; i < a.length; i++) { d = a[i] > b[j] ? a[i] - b[j] : b[j] - a[i]; if (d < best) best = d; }
		total += best;
	}
	return total;
}

function shiftChord(notes, by) {
	var out = [];
	for (var i = 0; i < notes.length; i++) out.push(notes[i] + by);
	return out;
}

// The chord this set should sound as. With the voice leading off that is one voicing of the
// canonical rotation, as before. With it on, every inversion is tried at every octave within
// reach and the one nearest the chord that just sounded wins. The comparison happens AFTER the
// root is added, because a moving root is exactly what makes two chords far apart. The pull term
// keeps a long run from wandering off: without it each chord only has to be near its neighbour,
// and a hundred small steps in the same direction cost nothing.
function chordFor(pcs) {
	var er = effRoot();
	var plain = applyVoicing(closedStack(pcs, 0), voicingMode);
	if (!voiceLead || !lastChord) {
		lastChord = shiftChord(plain, er);
		return plain;
	}
	var bestCand = plain, bestScore = 1e9;
	for (var r = 0; r < pcs.length; r++) {
		var cand = applyVoicing(closedStack(pcs, r), voicingMode);
		for (var o = -2; o <= 2; o++) {
			var at = shiftChord(cand, o * 12 + er);
			var score = chordDistance(at, lastChord) + Math.abs(at[0] - (CHORD_BASE + er)) * 0.25;
			if (score < bestScore) { bestScore = score; bestCand = shiftChord(cand, o * 12); }
		}
	}
	lastChord = shiftChord(bestCand, er);
	return bestCand;
}

function displayNotes(pcs) {
	var names = [];
	for (var i = 0; i < pcs.length; i++) names.push(noteName(MELODY_BASE + pcs[i] + effRoot() + masterOctave * 12));
	return names;
}

// Every permutation of the INDICES 0..n-1, in Heap's algorithm order. Indices rather than the
// pitch classes themselves for two reasons: one cached list now serves every set of that
// cardinality instead of being rebuilt per set, and a permutation can be composed with a
// per-voice degree offset before it is turned into a pitch. Heap's order depends only on
// positions, so pcs[heapPermutations(n)[k][j]] is exactly the sequence the old value-based
// version produced -- the audible result is unchanged.
function heapPermutations(n) {
	var result = [];
	var a = [];
	for (var k0 = 0; k0 < n; k0++) a.push(k0);
	var c = new Array(n);
	for (var k = 0; k < n; k++) c[k] = 0;
	result.push(a.slice());
	var i = 0;
	var tmp;
	while (i < n) {
		if (c[i] < i) {
			if (i % 2 === 0) {
				tmp = a[0]; a[0] = a[i]; a[i] = tmp;
			} else {
				tmp = a[c[i]]; a[c[i]] = a[i]; a[i] = tmp;
			}
			result.push(a.slice());
			c[i]++;
			i = 0;
		} else {
			c[i] = 0;
			i++;
		}
	}
	return result;
}

// permList holds the index permutations for ONE cardinality, shared by every set of that size.
function ensurePermCache(n) {
	if (permCachedForN === n && permList.length) return;
	permList = heapPermutations(n);
	permCachedForN = n;
}

function gcd(a, b) {
	while (b) { var t = a % b; a = b; b = t; }
	return a;
}

// The skip the user asked for, snapped to the nearest value coprime with the cardinality. Only a
// coprime skip visits every degree before any repeats; a skip sharing a factor with n collapses
// the read into a shorter loop over part of the set. Ties go to the smaller skip. On a seven-note
// set a skip of 2 is a chain of thirds, which is why 2 is the default.
function coprimeStepFor(n) {
	if (n <= 2) return 1;
	var want = Math.round(coprimeSkip);
	if (!isFinite(want) || want < 1) want = 1;
	for (var d = 0; d < n; d++) {
		var lo = want - d, hi = want + d;
		if (lo >= 1 && lo < n && gcd(lo, n) === 1) return lo;
		if (hi >= 1 && hi < n && gcd(hi, n) === 1) return hi;
	}
	return 1;
}

var urnBag = [], urnBagN = -1, urnBagPass = -1;

// Random without replacement: every degree sounds once before any of them sounds twice, and the
// bag is reshuffled for the next pass. The draw is cached per (cardinality, pass) rather than
// rolled per note so that voices sitting at different points of the SAME pass agree on the order
// -- that is what makes the urn a phrase heard from several places instead of unrelated noise.
// The pass number has to be handed in: the shape's own cycle is n long, so the position modulo
// that cycle cannot tell one pass from the next, and the urn would shuffle once and then repeat
// forever like a fixed permutation.
function urnAt(n, i, pass) {
	if (urnBagN !== n || urnBagPass !== pass) {
		urnBag = [];
		for (var k = 0; k < n; k++) urnBag.push(k);
		for (var j = n - 1; j > 0; j--) {
			var r = Math.floor(Math.random() * (j + 1));
			var t = urnBag[j]; urnBag[j] = urnBag[r]; urnBag[r] = t;
		}
		urnBagN = n;
		urnBagPass = pass;
	}
	return urnBag[i % n];
}

// How long one pass of the SHAPE is, before direction is taken into account.
function shapeCycleLength(n) {
	if (readMode === READ_SUPERMIN && MINIMAL_SUPERPERMS[n]) return MINIMAL_SUPERPERMS[n].length;
	if ((readMode === READ_SUPER || readMode === READ_SUPERMIN) && n <= PERM_CAP) {
		ensurePermCache(n);
		return permList.length * n;
	}
	if (readMode === READ_MODOS) return n * n;   // n modes, n degrees each
	return n;
}

// The degree the shape puts at position i of its own pass; `pass` counts completed passes, which
// only the urn needs. Modos is the one shape that returns
// degrees past n-1 on purpose: pitchForDegree() reads those as the next octave up, which is what
// re-voices each successive mode above the last instead of folding it back on itself.
function shapeDegreeAt(n, i, pass) {
	if (readMode === READ_SUPERMIN && MINIMAL_SUPERPERMS[n]) return MINIMAL_SUPERPERMS[n][i];
	if ((readMode === READ_SUPER || readMode === READ_SUPERMIN) && n <= PERM_CAP) {
		ensurePermCache(n);
		return permList[Math.floor(i / n) % permList.length][i % n];
	}
	if (readMode === READ_MODOS) return Math.floor(i / n) + (i % n);
	if (readMode === READ_COPRIMO) return (i * coprimeStepFor(n)) % n;
	if (readMode === READ_ZIGZAG) return (i % 2 === 0) ? (i >> 1) : (n - 1 - (i >> 1));
	if (readMode === READ_URNA) return urnAt(n, i, pass);
	return i % n;
}

// Which degree the reading order says to play at position pos. This is the ONE place the reading
// order lives: the shared clock, the independent voices and triggervoice() all come through here,
// so a voice sounds the same whichever of them moved it. Shape and direction are separate on
// purpose -- any shape can be read backwards or as a pendulum, and the pendulum does not repeat
// the note at either end, so the turn is heard as a turn and not as a stutter.
function degreeAt(n, pos) {
	pos = Math.round(pos);
	if (!isFinite(pos) || pos < 0) pos = 0;
	var L = shapeCycleLength(n);
	if (L < 1) L = 1;
	var i, pass;
	if (readDir === 1) {
		pass = Math.floor(pos / L);
		i = L - 1 - (pos % L);
	} else if (readDir === 2 && L > 1) {
		var period = 2 * L - 2;
		pass = Math.floor(pos / period);
		var q = pos % period;
		i = (q < L) ? q : period - q;
	} else {
		pass = Math.floor(pos / L);
		i = pos % L;
	}
	return shapeDegreeAt(n, i, pass);
}

// How many steps one complete pass takes, direction included. It decides when the set is allowed
// to change, so no reading order is ever cut off half way -- a superpermutation gets to finish,
// and a pendulum gets to come back, before the harmony moves.
function readCycleLength(n) {
	var L = shapeCycleLength(n);
	if (readDir === 2 && L > 1) return 2 * L - 2;
	return L;
}

// Turns a degree index into a pitch, letting the index run past the end of the set: degree n is
// degree 0 an octave up. That is what makes a per-voice degree offset stack into a chord
// (offsets 0,1,2,3 on a three-note set give root, third, fifth, root+12) and what stops two
// voices from crossing, since a larger offset always lands higher.
function pitchForDegree(pcs, deg) {
	var n = pcs.length;
	var wrapped = ((deg % n) + n) % n;
	return pcs[wrapped] + 12 * Math.floor(deg / n);
}

// The independent-voice counterpart of emitVoices(): instead of one note handed to every voice,
// each voice resolves its own pitch from its own cursor. Muted voices and rests still advance
// the cursor -- a mute is a gate, not a pause, so unmuting mid-phrase drops the voice back in
// where it would have been rather than where it left off.
function emitVoicesIndependent(pcs, n) {
	var summary = [];
	var names = [];
	for (var v = 0; v < NUM_VOICES; v++) {
		// external voices belong to triggervoice(); the clock must not move their cursor too
		if (voiceExternal[v]) { summary.push(0); names.push("--"); continue; }
		var div = voiceDiv[v] > 0 ? voiceDiv[v] : 1;
		if (((patternStep - 1) % div) !== 0) { summary.push(0); names.push("--"); continue; }

		var pos = voicePos[v];
		// Acordes: the cursor is frozen at 0, so the voice holds its degree and the chord changes
		// only when the set does -- four voices at offsets 0,1,2,3 read as a four-part chorale.
		// Arpegio: the cursor walks, and the offset keeps the voices a fixed number of degrees apart.
		var readIdx = (mode === 1) ? pos : 0;
		var pc = pitchForDegree(pcs, degreeAt(n, readIdx) + voiceDegOffset[v]);
		var list = voiceOctaveList[v];
		var oct = list[pos % list.length];
		var note = drumOn ? padFor(pc)
			: foldToRange(MELODY_BASE + pc + oct * 12 + effRoot() + masterOctave * 12,
				voiceRangeMin[v], voiceRangeMax[v]);
		// the accent grid is read at this voice's own cursor for the same reason triggervoice()
		// does it: a voice on a divider advances slower, and its accents have to follow its notes
		var art = articulationFor(v, pos, n);
		voicePos[v] = pos + 1;

		if (DEBUG_STEP) {
			post("  IND v" + (v + 1) + " | pos=" + pos + " deg+" + voiceDegOffset[v] +
				" div=" + div + " -> note " + note +
				" | grp=" + (art.group ? "ACC" : "nrm") + " vel=" + art.vel +
				(voiceMute[v] ? " MUTED" : "") + (art.rest ? " REST" : "") + "\n");
		}
		if (voiceMute[v] || art.rest) { summary.push(0); names.push("--"); continue; }

		summary.push(note);
		names.push(noteName(note));
		emitNote(v, art, note);
	}
	outlet(3, summary);
	var labelled = [];
	for (var m = 0; m < NUM_VOICES; m++) labelled.push("V" + (m + 1) + ":" + names[m]);
	outlet(5, labelled);
}

// One clock step with independent voices. The shared permutation walk (permIndex/minimalPos) is
// not used here at all: every voice derives its position from its own cursor, so the only thing
// left for the step to decide is when the harmony moves on.
function stepIndependent(pcs, n) {
	emitSetReadouts(pcs);
	emitVoicesIndependent(pcs, n);

	if (locked) return;
	if (mode === 0) {
		advanceOnPass();   // acordes: one set per step, same as the shared path
		return;
	}
	noteIndex++;
	if (noteIndex >= readCycleLength(n)) {
		noteIndex = 0;
		advanceOnPass();
	}
}

function step() {
	patternStep++;
	if (locked) setIndex = lockIndex;
	harmonyStep();   // may move the set before this step reads it, when the harmony has its own clock
	if (setIndex >= sets.length) setIndex = 0;
	var pcs = sets[setIndex];
	var n = pcs.length;
	if (DEBUG_STEP) {
		post("STEP " + patternStep + " | set=" + (setIndex + 1) + " n=" + n +
			" | locked=" + locked + " mode=" + mode + " read=" + readMode + "/" + readDir +
			" | noteIdx=" + noteIndex + " permIdx=" + permIndex + " minPos=" + minimalPos + "\n");
	}
	var er = effRoot();
	outlet(6, pcs.map(function(p) { return ((p + er) % 12 + 12) % 12; }));

	if (voiceIndep) {
		stepIndependent(pcs, n);
		return;
	}

	if (mode === 1 && readDir === 0 && readMode === READ_SUPERMIN && MINIMAL_SUPERPERMS[n]) {
		var minSeq = MINIMAL_SUPERPERMS[n];
		if (minimalCachedFor !== setIndex) {
			minimalCachedFor = setIndex;
			minimalPos = 0;
		}

		emitSetReadouts(pcs);
		emitVoices(MELODY_BASE + pcs[minSeq[minimalPos]]);

		minimalPos++;
		if (minimalPos >= minSeq.length) {
			minimalPos = 0;
			if (!locked) {
				advanceOnPass();
				minimalCachedFor = -1;
			}
		}
		return;
	}

	if (mode === 1 && readDir === 0 &&
		(readMode === READ_SUPER || readMode === READ_SUPERMIN) && n <= PERM_CAP) {
		ensurePermCache(n);
		if (permSetTag !== setIndex) {
			permSetTag = setIndex;
			permIndex = 0;
			noteIndex = 0;
		}
		var curPerm = permList[permIndex];   // indices into pcs, not pitch classes
		var permPcs = [];
		for (var pi = 0; pi < curPerm.length; pi++) permPcs.push(pcs[curPerm[pi]]);

		emitSetReadouts(permPcs);
		emitVoices(MELODY_BASE + permPcs[noteIndex]);

		noteIndex++;
		if (noteIndex >= n) {
			noteIndex = 0;
			permIndex++;
			if (permIndex >= permList.length) {
				permIndex = 0;
				if (!locked) {
					advanceOnPass();
					permSetTag = -1;   // force the permIndex reset above on the new set next step
				}
			}
		}
		return;
	}

	emitSetReadouts(pcs);

	if (mode === 0) {
		emitVoices(chordFor(pcs));
		if (!locked) {
			advanceOnPass();
		}
	} else {
		// The reading order picks the degree; `rotation` still turns the whole pass by one degree
		// per pass, as it always did. Modos is the exception: its degrees deliberately climb past
		// the top of the set to re-voice each mode upward, so it reads through pitchForDegree()
		// and leaves rotation alone, which would only fight it.
		var deg = degreeAt(n, noteIndex);
		emitVoices(readMode === READ_MODOS
			? MELODY_BASE + pitchForDegree(pcs, deg)
			: MELODY_BASE + pcs[(deg + rotation) % n]);
		noteIndex++;
		if (noteIndex >= readCycleLength(n)) {
			noteIndex = 0;
			if (locked) {
				rotation = (rotation + 1) % n;   // only one set in the loop, so always rotate per cycle
			} else {
				if (rotShape === 1) {
					rotation = (rotation + 1) % n;
				}
				// advanceSet() reports the wrap, which is what "rotate once per full pass" keys
				// off -- with an alternative order or a filter in play, "wrapped" is no longer
				// the same thing as "setIndex came back to 0"
				if (advanceOnPass() && rotShape === 0) {
					rotation++;
				}
			}
		}
	}
}

function setshape(s) {
	rotShape = s ? 1 : 0;
}

// A change of reading order restarts the pass rather than landing mid-phrase in a walk that was
// counted for the previous shape.
function resetReadWalk() {
	noteIndex = 0;
	permIndex = 0;
	permSetTag = -1;
	minimalPos = 0;
	minimalCachedFor = -1;
	urnBagPass = -1;
}

function setreadmode(p) {
	readMode = Math.round(p);
	if (!isFinite(readMode) || readMode < 0) readMode = 0;
	if (readMode > READ_MAX) readMode = READ_MAX;
	resetReadWalk();
}

// The message name the device has been sending since the reading order had only three values.
// Kept so an older patch, preset or automation lane still selects the same three.
function setpermmode(p) {
	setreadmode(p);
}

function setreaddir(d) {
	readDir = Math.round(d);
	if (!isFinite(readDir) || readDir < 0) readDir = 0;
	if (readDir > 2) readDir = 2;
	resetReadWalk();
}

// Not a walk reset: changing the skip mid-pass is a change of interval, not of place.
function setcoprime(k) {
	coprimeSkip = Math.round(k);
	if (!isFinite(coprimeSkip) || coprimeSkip < 1) coprimeSkip = 1;
	if (coprimeSkip > 11) coprimeSkip = 11;
}

// --- articulation setters --------------------------------------------------------------

// setaccentgrid <c1> <c2> ... : the whole grid arrives as one list from the Max UI, so a
// redraw can never leave it half-updated between two notes. Cells beyond what was sent are
// cleared, which makes "shorten the pattern" behave the way the drawing looks.
function setaccentgrid() {
	for (var i = 0; i < ACCENT_MAX; i++) {
		accentGrid[i] = (i < arguments.length && arguments[i]) ? 1 : 0;
	}
}

function setaccentcycle(c) {
	c = Math.round(c);
	if (c < 1) c = 1;
	if (c > ACCENT_MAX) c = ACCENT_MAX;
	accentCycle = c;
	applyEuclid();          // the cycle IS the n of E(k,n), so the pattern is refitted to it
}

// Bjorklund's algorithm: k onsets spread over n cells as evenly as n allows. Written out rather
// than taken as the one-line Bresenham shortcut, because floor(i*k/n) only agrees with it some
// of the time -- it gets E(3,8) right (10010010) and E(5,8) wrong, answering 10101011 where the
// maximally even pattern, the cinquillo, is 10110110.
function bjorklund(k, n) {
	var i, out = [];
	if (n < 1) return out;
	if (k <= 0) { for (i = 0; i < n; i++) out.push(0); return out; }
	if (k >= n) { for (i = 0; i < n; i++) out.push(1); return out; }
	var a = [], b = [];
	for (i = 0; i < k; i++) a.push([1]);
	for (i = 0; i < n - k; i++) b.push([0]);
	// Pair each remainder group onto the front of the sequence until at most one is left over;
	// what remains unpaired is what makes the pattern uneven, and there is never more of it.
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

// Rewrites the grid from (k, accentCycle, rotation) and hands it back to the toggles. Cells past
// the cycle are cleared, so shortening the cycle behaves the way the drawing looks.
function applyEuclid() {
	if (!euclidOn) return;
	var n = accentCycle;
	var k = euclidK > n ? n : euclidK;
	var pat = bjorklund(k, n);
	var r = ((euclidRot % n) + n) % n;
	for (var i = 0; i < ACCENT_MAX; i++) accentGrid[i] = (i < n) ? pat[(i + r) % n] : 0;
	outlet(4, ["accentgrid"].concat(accentGrid));
}

// 1 = the grid is generated, 0 = it is whatever the toggles say. Turning it on regenerates at
// once, so the drawing and the sound never disagree about which one is in charge.
function seteuclid(on) {
	euclidOn = on ? 1 : 0;
	applyEuclid();
}

function seteuclidk(k) {
	k = Math.round(k);
	if (!isFinite(k) || k < 0) k = 0;
	if (k > ACCENT_MAX) k = ACCENT_MAX;
	euclidK = k;
	applyEuclid();
}

function seteuclidrot(r) {
	r = Math.round(r);
	if (!isFinite(r) || r < 0) r = 0;
	if (r > ACCENT_MAX - 1) r = ACCENT_MAX - 1;
	euclidRot = r;
	applyEuclid();
}

// 1 = the cycle length follows the current set's cardinality, so accents lock onto the same
// chord tones every pass. 0 = the free length set by setaccentcycle, which rotates the
// pattern against the harmony whenever the two are coprime.
function setaccenttie(t) {
	accentTieToN = t ? 1 : 0;
}

function setvoicephase(v, p) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	p = Math.round(p);
	if (p < 0) p = 0;
	if (p > ACCENT_MAX - 1) p = ACCENT_MAX - 1;
	voicePhase[idx] = p;
}

// group index for every setter below: 0 = normal, 1 = accent. Returns -1 for anything else
// so a malformed message is dropped rather than corrupting a group.
function groupIndex(g) {
	g = Math.round(g);
	return (g === GROUP_NORMAL || g === GROUP_ACCENT) ? g : -1;
}

function setgroupvel(g, min, max) {
	var i = groupIndex(g);
	if (i < 0) return;
	min = Math.round(min);
	max = Math.round(max);
	if (min < 1) min = 1;         // 0 would be a note-off
	if (max > 127) max = 127;
	groupVelMin[i] = min;
	groupVelMax[i] = max;
}

// The UI exposes min and max as two independent Live parameters, so each needs a setter of its
// own. Going through setgroupvel would mean packing the two dials together, and on a set reload
// Live restores parameters one at a time -- whichever arrived first would be paired with the
// other's stale value for one message. articulationFor() already swaps a crossed pair, so
// letting them move independently costs nothing.
function setgroupvelmin(g, v) {
	var i = groupIndex(g);
	if (i < 0) return;
	v = Math.round(v);
	if (v < 1) v = 1;             // 0 would be a note-off
	if (v > 127) v = 127;
	groupVelMin[i] = v;
}

function setgroupvelmax(g, v) {
	var i = groupIndex(g);
	if (i < 0) return;
	v = Math.round(v);
	if (v < 1) v = 1;
	if (v > 127) v = 127;
	groupVelMax[i] = v;
}

// div is a note-value denominator: 1 = whole, 4 = quarter, 8 = eighth, 16 = sixteenth...
function setgroupdur(g, div) {
	var i = groupIndex(g);
	if (i < 0) return;
	div = Math.round(div);
	if (div < 1) div = 1;
	groupDurDiv[i] = div;
}

function setgroupsilence(g, pct) {
	var i = groupIndex(g);
	if (i < 0) return;
	pct = Math.round(pct);
	if (pct < 0) pct = 0;
	if (pct > 100) pct = 100;
	groupSilence[i] = pct;
}

// The textures worth reaching for in one move, as [normal %, accent %]. Silencing a whole group
// is what turns the accent grid from a dynamic into a rhythm: with the normal group at 100 only
// the accented cells sound, so E(5,8) stops being five loud notes among eight and becomes the
// five-note rhythm itself. Entry 0 applies nothing and carries the menu's name.
var SILENCE_PRESETS = [
	null,        // Silencio: the menu's own label
	[0, 0],      // Todo: nothing is dropped
	[100, 0],    // Solo ac.: the grid becomes the rhythm
	[0, 100],    // Solo norm.: the grid becomes a rhythm of rests
	[50, 50],    // Ralo: half of everything, wherever it falls
	[75, 75]     // Muy ralo: a scattering
];

function setsilencepreset(t) {
	t = Math.round(t);
	var pr = (t >= 0 && t < SILENCE_PRESETS.length) ? SILENCE_PRESETS[t] : null;
	if (!pr) return;
	groupSilence[GROUP_NORMAL] = pr[0];
	groupSilence[GROUP_ACCENT] = pr[1];
	outlet(4, ["g0silence", pr[0]]);
	outlet(4, ["g1silence", pr[1]]);
}

function bang() {
	step();
}
