autowatch = 1;
inlets = 1;
outlets = 8;   // 0 = note events (see emitNote), 1 = current set index (1-351),
               // 2 = notes for display (names), 3 = RETIRED - see below,
               // 4 = preset recall broadcast (tagged pairs, routed in Max),
               // 5 = voice note names for monitor,
               // 6 = current set's pitch classes (0-11, transposed by root) for circle-of-fifths,
               // 7 = Forte name and interval vector of the current set, as two symbols.
               //
               // Outlet 3 used to carry a per-voice array of raw MIDI numbers. Outlet 5 supersedes
               // it -- same information, already named -- and its destination in FORTESEQ2.amxd was
               // never connected, so it was allocating an array per step and sending it nowhere.
               // The outlet is kept in the count rather than removed: taking it out would renumber
               // 4 through 7 and silently move every cord attached to them.
               //
               // v1 spent one outlet per voice (0/3/4/5) plus a separate articulation outlet (10)
               // that HAD to fire before the pitch so makenote's cold inlets were already loaded.
               // That made the voice count a property of the patcher wiring, and made correctness
               // depend on JS call order. Here every note leaves as one self-describing message on
               // outlet 0, so the voice count is just NUM_VOICES and nothing depends on ordering.

// The tempo Live is running at, delivered by [transport] through setbpmtrack(). It does NOT set
// the step interval -- that is the metro's job, from the Rate dial or a note value -- but
// articulationFor() divides it to get note LENGTHS, which is what unhooks how long a note rings
// from how often notes arrive. (An older comment here claimed it was kept "purely for presets";
// that stopped being true when articulation started reading it.)
var currentBpm = 120;

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

// Per-voice rhythm. The accent grid decides how loud a voice speaks; this decides whether it
// speaks at all. Each voice carries its own E(k, n) and is silent on the cells that are not
// onsets -- so four voices on the same clock, given lengths that do not divide each other, stop
// being four copies of one rhythm and start being counterpoint. Coprime lengths are the whole
// point: 3 against 5 against 8 realigns once every 120 steps.
//
// Length 0 means no pattern at all, which is what every voice did before this existed, and is
// why there is no separate on/off per voice: a rhythm of no length is no rhythm.
var voiceRhyLen = filled(MAX_VOICES, 0);   // n: cells in this voice's pattern, 0 = sounds always
var voiceRhyK = filled(MAX_VOICES, 1);     // k: onsets spread over those cells
var voiceRhyRot = filled(MAX_VOICES, 0);   // where the pattern starts, which is what offsets voices
var voiceRhyPat = [];                      // the resolved pattern, rebuilt only when one of the three moves

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
		favs.push(0);

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
// The chain is deterministic and depends on nothing -- not the root, not the filter, not the
// reading order -- so it is worth computing once. It is O(351 squared) with a popcount in the
// inner loop, about a million and a half operations, and it used to run in full every time the
// traversal order was set to Vec, which in Max means on the scheduler thread.
var neighbourCache = null;

function neighbourChain() {
	if (neighbourCache) return neighbourCache.slice();
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
	neighbourCache = chain;
	return chain.slice();   // buildOrder() keeps what it is given; the cache must stay unreachable
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

// A floor and a ceiling on each entry of the interval vector -- the same six counts the readout
// prints as <001110>. "Sin semitonos" is ic1 max 0; "que tenga tritono" is ic6 min 1. The vector
// does not move when a set is transposed, so this is the one part of the filter the mask fit
// cannot argue with: a set either has those intervals or it does not, wherever it ends up.
var vecMin = [0, 0, 0, 0, 0, 0];
var vecMax = [12, 12, 12, 12, 12, 12];
var vecCond = 0;         // 1 while any entry is off its default, so the usual case costs one test

// The shortlist. Indexed by the set's place in sets[], which never moves, so a list means the
// same thing under every reading order and across reloads. It is a filter like the others rather
// than a mode of its own, so "solo favoritos" still obeys cardinality, vector and mask.
var favs = [];
// The same information as favs[], in the order you marked them. favs[] answers "is this one
// a favourite" in O(1), which is what the filter needs on all 351 every rebuild; favSeq is
// what a progression needs, because the order IS the progression -- eight sets you chose,
// played in the sequence you chose them in, is songwriting rather than filtering.
var favSeq = [];
var favOnly = 0;
var favEcho = -1;        // which set the Fav toggle was last told about

function vecCondRefresh() {
	vecCond = 0;
	for (var k = 0; k < 6; k++) if (vecMin[k] > 0 || vecMax[k] < 12) vecCond = 1;
}

function vecCondOk(i) {
	var v = setVec[i];
	for (var k = 0; k < 6; k++) if (v[k] < vecMin[k] || v[k] > vecMax[k]) return 0;
	return 1;
}

function favCount() {
	var n = 0;
	for (var i = 0; i < favs.length; i++) if (favs[i]) n++;
	return n;
}

// Out to the pattr that carries the list inside the Live set. The leading -1 is there so that an
// empty list still arrives as a message: Max drops a list with nothing in it, and "ya no hay
// favoritos" has to be a state the device can be told about.
function sendFavList() {
	var l = ["favlist", -1];
	for (var i = 0; i < favSeq.length; i++) l.push(favSeq[i]);
	outlet(4, l);
	savefavs();
}

// --- the list on disk -----------------------------------------------------------------------
// The pattr keeps the list inside the patcher, and that turned out not to survive a Live set
// being saved and reopened: Live stores parameter values per instance, and 351 flags are not a
// parameter. So the list lives in a file next to the device as well. That makes it global rather
// than per-song -- a shortlist of set classes you like follows you from one set to the next,
// which is what a list of favourites usually wants to be anyway.
var FAV_FILE = "forteseq2_favs.txt";
var favSaveWarned = 0;

// Next to the .amxd, not wherever Max happens to think the current folder is. A bare filename is
// only resolved by the search path when READING; writing one would land somewhere unpredictable.
function devPath(file) {
	var fp = "";
	try { fp = this.patcher.filepath; } catch (e) { fp = ""; }
	if (!fp) return file;
	var cut = fp.lastIndexOf("/");
	if (cut < 0) cut = fp.lastIndexOf("\\");
	return cut >= 0 ? fp.slice(0, cut + 1) + file : file;
}

function favPath() { return devPath(FAV_FILE); }

function savefavs() {
	if (typeof File === "undefined") return;   // fuera de Max no hay disco, y los tests corren igual
	var line = "";
	// favSeq and not an ascending sweep: the order is part of what is being saved.
	for (var i = 0; i < favSeq.length; i++) line += (line ? " " : "") + favSeq[i];
	var f = new File(favPath(), "write", "TEXT");
	if (!f.isopen) {
		if (!favSaveWarned) {
			favSaveWarned = 1;   // una vez por sesion: esto se llama en cada marca
			post("forteseq2: no pude escribir " + favPath() +
				", los favoritos duran hasta cerrar\n");
		}
		return;
	}
	try {
		f.eof = 0;        // una lista mas corta no puede dejar la cola de la anterior atras
		f.position = 0;
		f.writeline(line);
	} catch (e) {
		post("forteseq2: fallo al guardar favoritos: " + e + "\n");
	}
	f.close();
}

function loadfavs() {
	if (typeof File === "undefined") return;
	var f = new File(favPath(), "read", "TEXT");
	if (!f.isopen) return;   // todavia no hay archivo, que no es un error sino el primer arranque
	var line = "";
	try { line = f.readline(8192); } catch (e) { line = ""; }
	f.close();
	favSetAll(("" + line).split(" "), 0);
	favEcho = -1;            // que el toggle se repinte en la primera nota
	if (favOnly) requestFilter();
	post("forteseq2: " + favCount() + " favoritos leidos de " + favPath() + "\n");
}

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
	// While the listener owns the harmony the chord sounds in the key it was played in, and
	// the Raiz dial steps aside rather than fighting it. Latch keeps that key; releasing in
	// Sigue hands it straight back. The root SEQUENCE is added either way -- it carries the
	// whole harmony around by design, and that does not stop being true because you played it.
	var base = listenOn ? listenTr
		: ((filterOn && maskFit && setIndex < setFit.length) ? setFit[setIndex] : root);
	return base + rootSeqOffset + modRootShift();
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
	filterDirty = 0;
	var pass = 0;
	for (var i = 0; i < sets.length; i++) {
		var ok = 1;
		var fit = root;
		if (filterOn) {
			if (setCard[i] < cardMin || setCard[i] > cardMax) ok = 0;
			if (ok && favOnly && !favs[i]) ok = 0;
			if (ok && vecCond && !vecCondOk(i)) ok = 0;
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
		// Written by index rather than pushed onto two fresh arrays. The length is always
		// sets.length, so the two arrays are allocated once for the life of the device
		// instead of twice per rebuild -- and rebuilds are frequent, see requestFilter().
		allowed[i] = ok;
		setFit[i] = fit;
		pass += ok;
	}
	if (pass === 0) {
		// A filter nothing passes would freeze the sequence on whatever set happened to be
		// playing, which reads as a broken device. Falling back to the whole catalogue at least
		// keeps it moving, and the console says why.
		post("forteseq2: el filtro no deja pasar ningun set, se ignora\n");
		for (var k = 0; k < allowed.length; k++) allowed[k] = 1;
	}
	// The consonance the filter still allows, which is the range the tension curve sweeps. It
	// belongs here because it moves exactly when the filter does and nowhere else: asking for
	// "as harsh as possible" has to mean as harsh as the sets you left in the catalogue.
	consLow = 1e9;
	consHigh = -1e9;
	for (var c = 0; c < allowed.length; c++) {
		if (!allowed[c]) continue;
		var cv = consonanceOf(c);
		if (cv < consLow) consLow = cv;
		if (cv > consHigh) consHigh = cv;
	}
	if (consLow > consHigh) { consLow = 0; consHigh = 0; }
}

// buildFilter() walks all 351 sets against up to twelve transpositions each -- some four thousand
// iterations -- and almost every filter control used to call it outright. Dragging the Raiz dial
// fired it once per increment, and loading a Live set fired it once per filter parameter as Live
// restored them one at a time: a burst of dozens at the worst possible moment.
//
// So the setters mark the filter dirty and ASK for a rebuild, and a Task collapses however many
// asks arrive in one scheduler pass into a single one. The cost is that a filter change can land
// one step late -- the set already chosen keeps playing for that step, which no ear catches.
// Outside Max there is no Task, so the harness rebuilds synchronously and sees the old ordering.
var filterDirty = 0;
var filterTask = null;

function requestFilter() {
	filterDirty = 1;
	if (typeof Task === "undefined") { buildFilter(); return; }
	if (!filterTask) filterTask = new Task(function () { if (filterDirty) buildFilter(); });
	filterTask.cancel();
	filterTask.schedule(0);
}

// Moves to the next playable set and reports whether the catalogue wrapped, which is what the
// rotation-per-pass option keys off. Order and filter both live here, so every caller in step()
// gets them without knowing about either.
// --- the harmonic path -------------------------------------------------------------------
// Until now the next set was simply the next allowed one in the traversal order. Three ways of
// choosing it instead, in the order they override each other: a curated progression beats a
// tension curve, and a tension curve beats the plain walk. Common tones constrain the last two
// but never the first -- if you chose the sequence yourself, being told your own progression is
// too far apart would be impertinent.
var linkMin = 0;      // fewest pitch classes the next set must share with this one; 0 = no rule
var tensLen = 0;      // set changes in one tension cycle; 0 = no curve
var tensShape = 0;    // 0 = rising, 1 = falling, 2 = arch
var tensPos = 0;
var favSeqOn = 0;     // play the favourites in the order they were marked
var consLow = 0, consHigh = 0;   // the consonance the filter currently allows, from buildFilter()

// A set's pitch classes at the transposition it will be played at. With the mask fit off every
// set is rotated by the same root, so common tones between two of them are the same as between
// their stored forms and this costs nothing; with the fit on each set has its own transposition
// and the rotation is the only way to count them honestly.
//
// The root SEQUENCE is deliberately left out. It carries the whole harmony around by design --
// the comment on effRoot() already says a root walk is the more deliberate request -- so it
// shifts both sets equally as far as this is concerned, and asking common tones to also chase a
// moving root would make the constraint unsatisfiable for no musical gain.
function fittedBits(i) {
	var base = (filterOn && maskFit && i < setFit.length) ? setFit[i] : root;
	return rotl12(setBits[i], base);
}

// Where in the cycle the tension sits, 0 = as consonant as the filter allows, 1 = as harsh.
function tensionAt(pos, len, shape) {
	if (len < 2) return 0;
	if (shape === 2) {                       // arch: out and back inside one cycle
		var g = (pos / len) * 2;
		return g <= 1 ? g : 2 - g;
	}
	var f = pos / (len - 1);
	return shape === 1 ? 1 - f : f;
}

// The plain walk: the next allowed set in the traversal order, skipping any that does not share
// enough with the one sounding. If a whole lap finds nothing that does, it takes the next allowed
// one anyway -- a constraint that can freeze the sequence is worse than a constraint that bends.
function advanceInOrder() {
	var total = order.length;
	var pos = orderPosOf[setIndex];
	if (pos === undefined) pos = 0;
	var cb = linkMin > 0 ? fittedBits(setIndex) : 0;
	var fallback = -1, fallbackRaw = 0;
	for (var i = 1; i <= total; i++) {
		var raw = pos + i;
		var cand = order[raw % total];
		if (!allowed[cand]) continue;
		if (linkMin > 0) {
			if (fallback < 0) { fallback = cand; fallbackRaw = raw; }
			if (popcount(cb & fittedBits(cand)) < linkMin) continue;
		}
		setIndex = cand;
		rootSeqAdvance();   // the only place the harmony moves, so the only place the root walks
		return raw >= total ? 1 : 0;
	}
	if (fallback >= 0) {
		setIndex = fallback;
		rootSeqAdvance();
		return fallbackRaw >= total ? 1 : 0;
	}
	return 0;
}

// The curve: the harmony is asked to be about this consonant right now, and the closest allowed
// set that also satisfies the common-tone rule gets it. Scanning all 351 is fine here -- this
// runs once per set change, not once per note.
function advanceByTension() {
	tensPos = (tensPos + 1) % tensLen;
	var target = consHigh - tensionAt(tensPos, tensLen, tensShape) * (consHigh - consLow);
	var cb = linkMin > 0 ? fittedBits(setIndex) : 0;
	var best = -1, bestD = 1e9, loose = -1, looseD = 1e9;
	for (var i = 0; i < order.length; i++) {
		var c = order[i];
		if (c === setIndex || !allowed[c]) continue;
		var d = consonanceOf(c) - target;
		if (d < 0) d = -d;
		if (d < looseD) { looseD = d; loose = c; }
		if (linkMin > 0 && popcount(cb & fittedBits(c)) < linkMin) continue;
		if (d < bestD) { bestD = d; best = c; }
	}
	if (best < 0) best = loose;
	if (best < 0) return 0;
	setIndex = best;
	rootSeqAdvance();
	// "Wrapped" drives the shape rotation and the end-of-pass answer. A lap of the catalogue
	// means nothing here, so what is reported is the cycle coming round, which is the thing that
	// actually repeats.
	return tensPos === 0 ? 1 : 0;
}

// The progression: your favourites, in the order you marked them. The filter is not consulted --
// you picked these by hand, and a set you chose being filtered out from under you would be the
// device arguing with you. An empty list falls back to the plain walk rather than to silence.
function advanceFavSeq() {
	var n = favSeq.length;
	if (!n) return advanceInOrder();
	var k = favSeq.indexOf(setIndex);   // -1 lands on favSeq[0], which is where to come in
	setIndex = favSeq[(k + 1) % n];
	rootSeqAdvance();
	return (k + 1) >= n ? 1 : 0;
}

function advanceSet() {
	if (!order.length) return 0;
	// Two ways the harmony stops being this device's to choose. A hand on the keys IS the
	// harmony, and an engine following the bus is being told one.
	if (listenMode && heldBits) return 0;
	if (followOn) return 0;
	if (favSeqOn) return advanceFavSeq();
	if (tensLen > 0) return advanceByTension();
	return advanceInOrder();
}

// --- listening ----------------------------------------------------------------------------
// The catalogue holds every Tn-class of every cardinality, so ANY chord you can play is in it:
// 351 classes times 12 transpositions covers all 4095 non-empty pitch-class sets. Identifying
// what a hand is holding is therefore a lookup and never a search, and never fails.
//
// Built once from setBits. Where a set maps to the same sounding notes at several transpositions
// -- the whole-tone scale at 0 and at 2, the diminished seventh at 0, 3, 6, 9 -- the first one
// wins, which keeps a symmetrical chord from jumping key every time you replay it.
var classOf = {};

function buildClassIndex() {
	classOf = {};
	var n = 0;
	for (var i = 0; i < sets.length; i++) {
		for (var t = 0; t < 12; t++) {
			var b = rotl12(setBits[i], t);
			if (classOf[b] === undefined) { classOf[b] = [i, t]; n++; }
		}
	}
	// Every one of the 4095 non-empty pitch-class sets, and no more: the catalogue holds no
	// empty class, so bitmask 0 is never produced. Anything less means this ran before
	// setBits was filled -- which it did, the first time -- and the only symptom would be a
	// listener that silently never identifies anything.
	if (n !== 4095) post("forteseq2: WARNING el indice de clases cubre " + n + " de 4095\n");
}

var listenMode = 0;      // 0 = off, 1 = follows the hand, 2 = latch
var listenOn = 0;        // 1 while the listener owns the harmony
var listenTr = 0;        // the transposition it was heard at
var listenPrev = -1;     // where the sequence was when the hand went down
var heldCount = filled(12, 0);   // per pitch class, how many keys are down
var heldBits = 0;

// Counted per pitch class rather than flagged, so a chord doubled at the octave survives one of
// the two notes being lifted, and so a re-articulated note cannot clear a class still held.
function noteheard(pitch, vel) {
	var pc = ((Math.round(pitch) % 12) + 12) % 12;
	var on = Math.round(vel) > 0;
	if (on) heldCount[pc]++;
	else if (heldCount[pc] > 0) heldCount[pc]--;
	var bits = 0;
	for (var i = 0; i < 12; i++) if (heldCount[i] > 0) bits |= (1 << i);
	if (bits === heldBits) return;
	var wasEmpty = (heldBits === 0);
	heldBits = bits;
	if (!listenMode) return;

	if (on) {
		// Only a note going DOWN takes a chord. Adding one to what is held extends the chord
		// and is heard at once, which is what makes it feel responsive.
		if (wasEmpty) listenPrev = setIndex;
		var e = classOf[bits];
		if (!e) return;                 // cannot happen; costs one branch to be sure of it
		setIndex = e[0];
		listenTr = e[1];
		listenOn = 1;
	} else if (bits) {
		// A chord let go note by note must NOT be re-read on the way out. Reading the
		// leftovers would mean latching a major triad usually caught whichever single note
		// your finger left last -- which is what it did before this branch existed.
		return;
	} else if (listenMode === 1) {
		// Sigue: the hand comes off and the sequence gets its harmony back, where it was.
		listenOn = 0;
		if (listenPrev >= 0) setIndex = listenPrev;
	}
	// Latch keeps both the set and the key, and the sequence carries on from there.
	readoutInvalidate();
}

function setlisten(m) {
	m = Math.round(m);
	if (!isFinite(m) || m < 0 || m > 2) m = 0;
	listenMode = m;
	if (!m) { listenOn = 0; readoutInvalidate(); }
}

// Clears the hand without needing the note-offs to arrive -- which they do not, if the mode was
// switched or the track re-armed mid-chord. The same reason the Hub has a PANIC button.
function listenpanic() {
	for (var i = 0; i < 12; i++) heldCount[i] = 0;
	heldBits = 0;
	listenOn = 0;
	if (listenPrev >= 0 && listenMode === 1) setIndex = listenPrev;
	readoutInvalidate();
}

// --- one harmony across several engines -----------------------------------------------------
// emitVoices() drives every voice from a single setIndex, so one engine is one harmony in N
// registers and a second device has always been a second harmony. These two close that: the
// leader says which class it is on, and a follower on the same bus takes it. Only which SET
// travels -- root, octave, voicing and register stay local, because two engines in different
// keys or registers over one harmony is the point of having two.
var bcastOn = 0;
var followOn = 0;

function setbroadcast(b) { bcastOn = b ? 1 : 0; }

function setfollow(f) {
	followOn = f ? 1 : 0;
	readoutInvalidate();
}

// A follower does not re-broadcast -- it only ever sends from its own choosing -- so there is no
// loop to break here. The filter is not consulted for the same reason the progression does not:
// something outside this device already decided.
function followset(b, i) {
	if (!followOn || Math.round(b) !== busId) return;
	i = Math.round(i);
	if (!isFinite(i) || i < 0 || i >= sets.length || i === setIndex) return;
	setIndex = i;
	readoutInvalidate();
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

// --- readouts ---------------------------------------------------------------------------
// The set number, its note names and its Forte label describe the HARMONY, which typically moves
// once per pass -- but this used to rebuild and resend all three on every clock step: up to twelve
// note-name strings from displayNotes(), a vector string from vecString(), three list messages
// across the JS boundary and three comment redraws, per note. The memo below is the same idea the
// Fav echo already used one line down, applied to the rest of the readout.
//
// The key cannot be setIndex alone. displayNotes() reads effRoot() and masterOctave, so moving the
// root has to repaint; and the superpermutation branch of step() hands in a REORDERED copy of the
// set that genuinely changes faster than setIndex does. So the pitch classes are compared element
// by element -- no allocation, and correct for every caller.
var readoutIndex = -1, readoutRoot = null, readoutOct = null;
var readoutPcs = [];

function readoutUnchanged(pcs) {
	if (setIndex !== readoutIndex || effRoot() !== readoutRoot || masterOctave !== readoutOct) return 0;
	var n = pcs.length;
	if (n !== readoutPcs.length) return 0;
	for (var i = 0; i < n; i++) if (pcs[i] !== readoutPcs[i]) return 0;
	return 1;
}

// Forces the next emitSetReadouts() through even if nothing it watches moved. Needed wherever the
// readouts have to be repainted for a reason the memo cannot see -- a preset recall, say, where
// the display was overwritten by something else while setIndex happened to stay put.
function readoutInvalidate() {
	readoutIndex = -1;
	readoutPcs = [];
}

function emitSetReadouts(displayPcs) {
	if (readoutUnchanged(displayPcs)) return;
	readoutIndex = setIndex;
	readoutRoot = effRoot();
	readoutOct = masterOctave;
	readoutPcs = displayPcs.slice();   // once per harmonic change, not once per note

	outlet(1, setIndex + 1);
	outlet(2, displayNotes(displayPcs));
	outlet(7, [setForte[setIndex], vecString(setIndex)]);
	// The Fav toggle is about whatever is sounding, so it has to be repainted when the harmony
	// moves -- but only then, or every note would push a parameter change into Live.
	if (setIndex !== favEcho) {
		favEcho = setIndex;
		outlet(4, ["fav", favs[setIndex] ? 1 : 0]);
	}
	// The memo above is what makes this affordable: it fires once per harmonic change, not
	// once per note, so a follower hears the harmony move and nothing else.
	if (bcastOn) outlet(4, ["setbcast", busId, setIndex]);
}

// The circle-of-fifths feed: the current set's pitch classes at sounding transposition. Same story
// as the readouts -- it only changes when the harmony or the root does, and it used to allocate a
// closure plus an array on every single step. Kept on its own memo rather than folded into
// emitSetReadouts() because it wants the plain set, not the permuted display copy.
var circleIndex = -1, circleRoot = null;

function emitCircle(pcs) {
	var er = effRoot();
	if (setIndex === circleIndex && er === circleRoot) return;
	circleIndex = setIndex;
	circleRoot = er;
	var out = [];
	for (var i = 0; i < pcs.length; i++) out.push((((pcs[i] + er) % 12) + 12) % 12);
	outlet(6, out);
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
	requestFilter();
}

// Two setters rather than one taking a pair: Live restores parameters one at a time on set
// reload, so a combined message would pair whichever arrived first with the other's stale value.
function setcardmin(n) {
	n = Math.round(n);
	if (n < 1) n = 1;
	if (n > 12) n = 12;
	cardMin = n;
	requestFilter();
}

function setcardmax(n) {
	n = Math.round(n);
	if (n < 1) n = 1;
	if (n > 12) n = 12;
	cardMax = n;
	requestFilter();
}

// setmask <c1> ... <c12>: the whole mask arrives as one list, so a redraw can never leave it
// half applied between two notes -- same reason setaccentgrid takes a list.
function setmask() {
	var bits = 0;
	for (var i = 0; i < 12 && i < arguments.length; i++) if (arguments[i]) bits |= (1 << i);
	maskBits = bits;
	requestFilter();
}

function setmaskmode(m) {
	m = Math.round(m);
	if (m < 0) m = 0;
	if (m > 2) m = 2;
	maskMode = m;
	requestFilter();
}

// 1 = a set that does not satisfy the mask where it sits may move to a transposition where it
// does, and then plays there. 0 = it is tested exactly where it sits, which is stricter and
// keeps the root meaning what it says, at the cost of letting very few sets through.
function setmaskfit(f) {
	maskFit = f ? 1 : 0;
	requestFilter();
}

function setmaskk(k) {
	k = Math.round(k);
	if (k < 1) k = 1;
	if (k > 12) k = 12;
	maskK = k;
	requestFilter();
}

// setvecmin <ic> <n> / setvecmax <ic> <n>: the interval class travels with the value instead of
// living in a second control, so Live restoring the twelve numboxes one at a time can never pair
// a value with the wrong entry. A floor above its ceiling lets nothing through, and the filter's
// own fallback says so on the console rather than freezing the sequence.
function setvecmin(k, n) {
	k = Math.round(k);
	if (k < 1 || k > 6) return;
	n = Math.round(n);
	if (n < 0) n = 0;
	if (n > 12) n = 12;
	vecMin[k - 1] = n;
	vecCondRefresh();
	requestFilter();
}

function setvecmax(k, n) {
	k = Math.round(k);
	if (k < 1 || k > 6) return;
	n = Math.round(n);
	if (n < 0) n = 0;
	if (n > 12) n = 12;
	vecMax[k - 1] = n;
	vecCondRefresh();
	requestFilter();
}

// Marks the set that is playing right now, which is what makes the button usable while browsing:
// oir algo, marcarlo, seguir. The value it already holds is ignored, because the echo that
// repaints the toggle comes straight back in as if a hand had moved it.
// Marks or unmarks one set, maintaining favSeq: marking appends, unmarking removes and closes
// the gap. Re-marking one that is already in the list cannot reach here -- setfav() returns
// early when nothing changed, which is what stops the toggle's own echo from bouncing -- so
// to move a set to the end of the progression you unmark it and mark it again.
function favMark(i, v) {
	var k = favSeq.indexOf(i);
	if (v) { if (k < 0) favSeq.push(i); }
	else if (k >= 0) favSeq.splice(k, 1);
	favs[i] = v ? 1 : 0;
}

// Replaces the whole list from an ORDERED one, which is the shape the file and the pattr both
// hand over. Duplicates are dropped rather than marked twice, so a set appears once in the
// progression however many times it is named.
function favSetAll(list, from) {
	for (var i = 0; i < favs.length; i++) favs[i] = 0;
	favSeq = [];
	for (var a = from; a < list.length; a++) {
		var idx = Math.round(list[a]);
		if (idx >= 0 && idx < favs.length && !favs[idx]) { favs[idx] = 1; favSeq.push(idx); }
	}
}

function setfav(f) {
	var v = f ? 1 : 0;
	if (favs[setIndex] === v) return;
	favMark(setIndex, v);
	if (favOnly) requestFilter();
	post("forteseq2: " + favCount() + " favoritos\n");
	sendFavList();
}

// --- the harmonic path, from outside ------------------------------------------------------

function setlink(n) {
	n = Math.round(n);
	if (!isFinite(n) || n < 0) n = 0;
	if (n > 6) n = 6;
	linkMin = n;
}

// Length of the tension cycle in set changes. Turning it on restarts the shape, so the curve
// begins where you asked rather than wherever the counter happened to be.
function settension(n) {
	n = Math.round(n);
	if (!isFinite(n) || n < 0) n = 0;
	if (n > 16) n = 16;
	if (n === tensLen) return;
	tensLen = n;
	tensPos = 0;
}

function settenshape(s) {
	s = Math.round(s);
	if (!isFinite(s) || s < 0 || s > 2) s = 0;
	tensShape = s;
}

function setfavseq(f) {
	favSeqOn = f ? 1 : 0;
}

function setfavonly(f) {
	favOnly = f ? 1 : 0;
	requestFilter();
}

function clearfavs() {
	for (var i = 0; i < favs.length; i++) favs[i] = 0;
	favSeq = [];
	favEcho = -1;
	if (favOnly) requestFilter();
	post("forteseq2: lista de favoritos vacia\n");
	sendFavList();
	outlet(4, ["fav", 0]);
}

// setfavlist -1 <index> ...: the whole list at once, from the pattr that saves it with the Live
// set. It answers rather than announces -- no sendFavList() from here -- so the round trip that
// follows every mark ends instead of bouncing.
function setfavlist() {
	// The -1 is also the shape check: a pattr that has never been written outputs whatever it
	// happens to hold, and a bare 0 arriving here would silently make set 1 a favourite.
	if (arguments.length < 1 || Math.round(arguments[0]) !== -1) return;
	var was = favCount();
	favSetAll(arguments, 1);   // skip the -1 that marked the message as a real list
	favEcho = -1;
	if (favOnly) requestFilter();
	savefavs();
	var now = favCount();
	// Silent when the list comes back unchanged, which is what the echo of a single mark looks
	// like; loud when the Live set actually hands us a list at load.
	if (now !== was) post("forteseq2: " + now + " favoritos\n");
}

buildSets();
buildForte();
buildSetLabels();   // fills setBits, which the class index reads
buildClassIndex();
buildOrder();
buildFilter();

function loadbang() {
	post("forteseq2: built " + sets.length + " Tn-classes over 224 Forte classes, bus " + busId +
		", " + NUM_VOICES + "/" + MAX_VOICES + " voices\n");
	loadfavs();
	loadpresets();
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
	pc = pitchForDegree(pcs, degreeAt(n, pos) + voiceDegOffset[idx] + modDeg());

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

	// Straight out, not into the ring: see emitNote(). This is the one caller with no step.
	emitNote(idx, art, shifted, 1);
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
// --- modulacion ---------------------------------------------------------------------------------
// Four modulators, each pointed at one destination. What matters most is what they do NOT do:
// none of them ever writes a parameter. The dial keeps saying what you set it to, the modulator
// adds an amount on top at the moment the value is read, and a depth of 0 hands back exactly the
// old number. A modulator that wrote into `root` would fight the dial for it, lose your setting
// on the way past, leave you unable to see where you actually were -- and then Live would save
// the set with whatever the sweep happened to be passing through.
//
// They advance on STEPS, not on milliseconds. This is a sequencer: a cycle of eight steps is
// eight steps at any tempo and lands on the grid, where an LFO in hertz drifts against it. The
// phase is derived from a counter rather than accumulated, so nothing can creep over a long set.
// Only Azar and Paseo carry state, and both draw once per cycle, which makes Ciclo their hold
// time and keeps one meaning for that control across all six shapes.
var MOD_N = 4;
var MOD_SINE = 0, MOD_TRI = 1, MOD_SAW = 2, MOD_SQ = 3, MOD_SH = 4, MOD_WALK = 5;

// Destination 0 is "-", a modulator with nothing to move. The spans are what depth 100 reaches,
// and they are deliberately musical rather than the parameter's whole range: an octave control
// swinging over its full six octaves is not modulation, it is noise.
var MOD_DEST_NAMES = ["-", "Raiz", "Octava", "Vel", "Largo", "Silencio", "Swing", "Rasgueo",
	"Ratchet", "Grado"];
var MOD_SPAN = [0, 12, 3, 63, 100, 100, 25, 8, 100, 7];
var D_ROOT = 1, D_OCT = 2, D_VEL = 3, D_DUR = 4, D_SIL = 5, D_SWING = 6, D_STRUM = 7,
	D_RATCHET = 8, D_DEG = 9;

var modShape = filled(MOD_N, 0);
var modCycle = filled(MOD_N, 8);      // steps per cycle, and the hold time for the two random shapes
var modDepth = filled(MOD_N, 0);      // -100..100; a negative depth simply turns the shape over
var modPhase = filled(MOD_N, 0);      // percent of a cycle, which is what puts two of them in quadrature
var modDest = filled(MOD_N, 0);
var modHeld = filled(MOD_N, 0);       // what Azar drew, or where Paseo has wandered to
var modCell = filled(MOD_N, -1);      // which cycle that held value belongs to
var modPos = 0;                       // steps since the engine started: the modulators' own clock
var modActive = 0;                    // 1 while at least one modulator has both a destination and depth
var modSum = filled(MOD_SPAN.length, 0);   // this step's total contribution, per destination

// Every shape is bipolar, so the dial is always the CENTRE of the sweep rather than one end of
// it. That is the property that makes a destination predictable: raising depth opens the swing
// symmetrically around the number you can see, and lowering it back to 0 closes it onto that
// same number. Destinations that sit at the end of their range by default -- Silencio at 0,
// Ratchet at 100 -- therefore spend half the sweep clamped, which is why their annotations say
// to park the dial mid-range first.
function modValue(k) {
	var cyc = modCycle[k];
	var pos = modPos + Math.round(cyc * modPhase[k] / 100);
	var cell = Math.floor(pos / cyc);
	var ph = (pos - cell * cyc) / cyc;
	switch (modShape[k]) {
	case MOD_SINE: return Math.sin(2 * Math.PI * ph);
	case MOD_TRI: return ph < 0.25 ? 4 * ph : (ph < 0.75 ? 2 - 4 * ph : 4 * ph - 4);
	case MOD_SAW: return 2 * ph - 1;
	case MOD_SQ: return ph < 0.5 ? 1 : -1;
	}
	// Azar and Paseo. The phase offset shifts `cell` along with everything else, so two of them
	// on one cycle draw at different moments instead of jumping together.
	if (cell === modCell[k]) return modHeld[k];
	modCell[k] = cell;
	if (modShape[k] === MOD_SH) {
		modHeld[k] = Math.random() * 2 - 1;
	} else {
		// A walk that clamps at the edges sticks to them, and a modulator stuck at its limit reads
		// as a broken one. Reflecting turns it around instead.
		var w = modHeld[k] + (Math.random() * 2 - 1) * 0.5;
		if (w > 1) w = 2 - w;
		if (w < -1) w = -2 - w;
		modHeld[k] = w;
	}
	return modHeld[k];
}

// One pass per step, summed per destination, so every read afterwards is a single array lookup
// instead of a loop over four modulators. Two modulators aimed at the same destination add up,
// which is the reason this is a sum and not a last-writer-wins assignment.
//
// The early return is not only an optimisation. modValue() draws from Math.random for Azar and
// Paseo, and the regression harness seeds that generator: if an idle modulator consumed a draw,
// every velocity and every rest coin downstream would shift, and the golden file would report a
// change in the notes that nobody made.
function modStep() {
	modPos++;
	if (!modActive) return;
	for (var d = 1; d < modSum.length; d++) modSum[d] = 0;
	for (var k = 0; k < MOD_N; k++) {
		var dest = modDest[k];
		if (!dest || !modDepth[k]) continue;
		modSum[dest] += modValue(k) * (modDepth[k] / 100) * MOD_SPAN[dest];
	}
}

// Called by every modulation setter. The clearing pass matters: modStep() rebuilds modSum only
// while something is active, so switching the last modulator off without this would leave its
// final contribution frozen into the sum for good.
function modRefresh() {
	var a = 0;
	for (var k = 0; k < MOD_N; k++) if (modDest[k] > 0 && modDepth[k] !== 0) a = 1;
	if (!a) for (var d = 0; d < modSum.length; d++) modSum[d] = 0;
	modActive = a;
	readoutInvalidate();   // Raiz and Octava reach the readout, and the readout caches
}

function modIndex(k) {
	k = Math.round(k) - 1;
	return (k >= 0 && k < MOD_N) ? k : -1;
}

function setmodshape(k, s) {
	var i = modIndex(k);
	if (i < 0) return;
	s = Math.round(s);
	if (!isFinite(s) || s < 0 || s > MOD_WALK) s = 0;
	if (s === modShape[i]) return;
	modShape[i] = s;
	modCell[i] = -1;   // a change of shape draws afresh instead of keeping the other shape's value
	modRefresh();
}

function setmodcycle(k, n) {
	var i = modIndex(k);
	if (i < 0) return;
	n = Math.round(n);
	if (!isFinite(n) || n < 1) n = 1;
	if (n > 64) n = 64;
	modCycle[i] = n;
	modRefresh();
}

function setmoddepth(k, p) {
	var i = modIndex(k);
	if (i < 0) return;
	p = Math.round(p);
	if (!isFinite(p)) p = 0;
	if (p < -100) p = -100;
	if (p > 100) p = 100;
	modDepth[i] = p;
	modRefresh();
}

function setmodphase(k, p) {
	var i = modIndex(k);
	if (i < 0) return;
	p = Math.round(p);
	if (!isFinite(p) || p < 0) p = 0;
	if (p > 100) p = 100;
	modPhase[i] = p;
	modRefresh();
}

function setmoddest(k, d) {
	var i = modIndex(k);
	if (i < 0) return;
	d = Math.round(d);
	if (!isFinite(d) || d < 0 || d >= MOD_SPAN.length) d = 0;
	modDest[i] = d;
	modRefresh();
}

// The readers. Each is a guarded lookup, so an unmodulated device pays one comparison per read
// and nothing else.
function modRootShift() {
	if (!modActive) return 0;
	return Math.round(modSum[D_ROOT]) + 12 * Math.round(modSum[D_OCT]);
}

function modDeg() {
	return modActive ? Math.round(modSum[D_DEG]) : 0;
}

function modAt(d) {
	return modActive ? modSum[d] : 0;
}

// --- what the sub-clock buys ------------------------------------------------------------------
// Four features, one mechanism: each decides an offset in sub-ticks and hands it to schedule().
// Every default here is the value that produces offset 0, so a device that never touches these
// controls behaves exactly as it did before they existed.

var swingPct = 50;          // 50 = straight; 66 = the offbeat lands two thirds of the way
var humanizePct = 0;        // 0-100, scaled to +/- half a step of timing jitter
var strumSub = 0;           // sub-ticks between consecutive notes of one chord
var strumDir = 0;           // 0 = up, 1 = down, 2 = random, 3 = alternate
var strumFlip = 0;          // which way the alternating strum is going
var ratchetN = [1, 1];      // repeats per note, per articulation group (normal, accent)
var ratchetPct = 100;       // how often a ratchet actually fires
var ratchetDecay = 0;       // 0-100, how much velocity is lost across the repeats
var voiceTimeOffset = filled(MAX_VOICES, 0);   // a fixed shove per voice, in sub-ticks
var stepSwing = 0;          // the swing offset in force for the step being built

function setswing(p) {
	p = Math.round(p);
	if (!isFinite(p) || p < 50) p = 50;
	if (p > 75) p = 75;
	swingPct = p;
}

// Every other step is pushed late by a fraction of the gap between steps. The fraction is the
// familiar swing percentage: 50 is straight, 66 is triplet feel, 75 is a dotted lilt. It can only
// move in whole sub-ticks, so Sub decides how fine the swing can be -- at Sub 1 there is nowhere
// to put it and swing does nothing, which is honest rather than surprising.
function swingOffset() {
	var sw = swingPct + modAt(D_SWING);
	if (sw <= 50 || subDiv < 2) return 0;
	if (sw > 75) sw = 75;
	var step = Math.floor(subPos / subDiv);
	if ((step % 2) === 0) return 0;
	return Math.round(subDiv * (sw - 50) / 50);
}

function sethumanize(p) {
	p = Math.round(p);
	if (!isFinite(p) || p < 0) p = 0;
	if (p > 100) p = 100;
	humanizePct = p;
}

// Timing jitter, drawn per note so two voices on the same step do not move together -- that
// independence is most of what makes it read as players rather than as a shifted grid. Never
// negative on the way out: schedule() clamps at 0, and a note cannot sound before its own step.
function humanizeOffset() {
	if (humanizePct <= 0 || subDiv < 2) return 0;
	var span = subDiv * humanizePct / 200;
	return Math.round((Math.random() * 2 - 1) * span);
}

function setstrum(n) {
	n = Math.round(n);
	if (!isFinite(n) || n < 0) n = 0;
	if (n > SUB_MAX) n = SUB_MAX;
	strumSub = n;
}

function setstrumdir(d) {
	d = Math.round(d);
	if (!isFinite(d) || d < 0 || d > 3) d = 0;
	strumDir = d;
}

// Spreads the notes of one chord across consecutive sub-ticks instead of striking them together.
// emitVoices() hands chords in ascending pitch, so index order IS low to high.
function strumOffset(i, n) {
	var ss = strumSub + Math.round(modAt(D_STRUM));
	if (ss <= 0 || n < 2) return 0;
	if (ss > SUB_MAX) ss = SUB_MAX;
	if (strumDir === 1) return (n - 1 - i) * ss;
	if (strumDir === 2) return Math.floor(Math.random() * n) * ss;
	if (strumDir === 3) return (strumFlip ? (n - 1 - i) : i) * ss;
	return i * ss;
}

function setratchet(g, n) {
	var i = groupIndex(g);
	if (i < 0) return;
	n = Math.round(n);
	if (!isFinite(n) || n < 1) n = 1;
	if (n > 4) n = 4;
	ratchetN[i] = n;
}

function setratchetprob(p) {
	p = Math.round(p);
	if (!isFinite(p) || p < 0) p = 0;
	if (p > 100) p = 100;
	ratchetPct = p;
}

function setratchetdecay(p) {
	p = Math.round(p);
	if (!isFinite(p) || p < 0) p = 0;
	if (p > 100) p = 100;
	ratchetDecay = p;
}

// A fixed shove per voice, which is what turns four voices playing the same rhythm into an
// ensemble that is not quite together. Distinct from Fase, which offsets a voice's reading of the
// accent grid rather than when it sounds.
function setvoicetimeoffset(v, t) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	t = Math.round(t);
	if (!isFinite(t) || t < 0) t = 0;
	if (t > SUB_MAX - 1) t = SUB_MAX - 1;
	voiceTimeOffset[idx] = t;
}

// One note becomes n, evenly spread over the step and fading if asked. The repeats are shortened
// to match their spacing, or a ratchet would just be one note with extra note-ons stacked inside
// it. Ratchet is per articulation group on purpose: with the accent grid driving it, the roll
// lands on the cells you drew rather than everywhere.
function scheduleBurst(voiceIdx, art, dur, pitch, off) {
	var n = ratchetN[art.group];
	var pct = ratchetPct + modAt(D_RATCHET);
	if (n <= 1 || subDiv < 2 || (pct < 100 && (Math.random() * 100) >= pct)) {
		schedule(off, [busId, voiceIdx + 1, art.vel, dur, pitch]);
		return;
	}
	var gap = Math.floor(subDiv / n);
	if (gap < 1) gap = 1;
	var sub = Math.round(dur / n);
	if (sub < 1) sub = 1;
	for (var r = 0; r < n; r++) {
		var vel = Math.round(art.vel * (1 - (ratchetDecay / 100) * (r / (n - 1))));
		if (vel < 1) vel = 1;
		if (vel > 127) vel = 127;
		schedule(off + r * gap, [busId, voiceIdx + 1, vel, sub, pitch]);
	}
}

// --- the sub-clock ----------------------------------------------------------------------------
// Everything the engine knows about pitch arrives on a perfectly square grid: one metro, every
// voice on an integer divider of it, every attack exactly on the beat. Swing, humanize, strum and
// ratchets all need to place a note BETWEEN two steps, and the note bus is five fixed atoms with
// no room for an onset offset -- adding a sixth would break every receiver.
//
// The way out is not a Task queue. Max runs js in the low-priority thread and a Task would jitter
// exactly where jitter is least forgivable. Instead the metro beats subDiv times per step and the
// engine decides which sub-tick each note leaves on. Timing is then the metro's own, the bus keeps
// its five atoms, and one mechanism serves all four features.
//
// With subDiv = 1 and every offset at its default of zero, a note is scheduled at offset 0 and
// flushed in the same tick it was scheduled: the old code path exactly, which is what lets the
// regression prove this changed nothing.
var SUB_MAX = 8;
var subDiv = 1;      // metro ticks per step; the Max side multiplies the metro to match
var subPos = 0;      // absolute sub-tick counter, never reset while running
var RING = 128;      // slots ahead a note may be scheduled; far more than any offset can reach
var pending = [];    // RING buckets of queued [bus, voice, vel, dur, pitch]

function setsub(n) {
	n = Math.round(n);
	if (!isFinite(n) || n < 1) n = 1;
	if (n > SUB_MAX) n = SUB_MAX;
	if (n === subDiv) return;
	subDiv = n;
	// A change of resolution restarts the count so the next step lands on a sub-tick 0 rather than
	// wherever the old cycle happened to be. Anything already queued is dropped: it was measured in
	// the old grid and would land at the wrong moment in the new one.
	subPos = 0;
	flushAllPending();
}

function schedule(offset, msg) {
	var off = Math.round(offset);
	if (!isFinite(off) || off < 0) off = 0;
	if (off >= RING) off = RING - 1;
	var slot = (subPos + off) % RING;
	if (!pending[slot]) pending[slot] = [];
	pending[slot].push(msg);
}

// Sends whatever is due on this sub-tick, in the order it was queued -- which for the default
// case is the order emitVoices() produced it, voice by voice.
function flushPending() {
	var slot = subPos % RING;
	var q = pending[slot];
	if (!q || !q.length) return;
	for (var i = 0; i < q.length; i++) outlet(0, q[i]);
	q.length = 0;
}

function flushAllPending() {
	for (var i = 0; i < RING; i++) if (pending[i]) pending[i].length = 0;
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
function emitNote(voiceIdx, art, pitches, now) {
	var list = (pitches instanceof Array) ? pitches : [pitches];
	var dur = Math.round(art.dur);

	// A note that did not come from a step has nothing to be placed relative to. The whole
	// sub-clock exists to put a note BETWEEN two steps, and every offset it produces is a
	// fraction of one step: swing is half the gap to the next, humanize is a jitter measured
	// against it, Desf shoves a voice by sub-ticks of it, and a ratchet divides it. An
	// externally triggered note has no step, so none of the five mean anything for it -- and
	// the ring would only make it wait for a metro tick it has nothing to do with.
	//
	// That wait is what made v2 feel slower than v1 from a MIDI clip. flushPending() runs
	// from bang() and nowhere else, so a trigger between two ticks came out on the NEXT one,
	// quantised to the metro grid, and with the transport stopped it never came out at all:
	// the notes piled up in one ring slot and fired together the moment Run went on.
	if (now) {
		for (var k = 0; k < list.length; k++) {
			outlet(0, [busId, voiceIdx + 1, art.vel, dur, list[k]]);
		}
		return;
	}

	var base = stepSwing + voiceTimeOffset[voiceIdx];
	for (var i = 0; i < list.length; i++) {
		var off = base + strumOffset(i, list.length) + humanizeOffset();
		scheduleBurst(voiceIdx, art, dur, list[i], off);
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

// Writes Grado = 0, step, 2*step ... across the live voices in one go: with step 1 the four of
// them read consecutive degrees of the set, which is the chord stacked up, and with step 0 they
// all come back to the same degree. It writes OTHER parameters, so its button is an action and
// stays off fs2_harm_init -- otherwise loading a set would silently undo whatever was tweaked by
// hand afterwards. Same rule as Rango and Preset Silencio.
function stackvoices(step) {
	step = (step === undefined) ? 1 : Math.round(step);
	if (!isFinite(step)) return;
	for (var v = 0; v < NUM_VOICES; v++) {
		var g = v * step;
		if (g < -8) g = -8;
		if (g > 8) g = 8;    // el numbox de Grado no pasa de ahi, y el eco tiene que caer adentro
		voiceDegOffset[v] = g;
		if (v < 4) outlet(4, ["v" + (v + 1) + "grado", g]);   // solo hay cuatro tiras en la UI
	}
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
	requestFilter();   // the mask is absolute, so what fits inside it changes when the root moves
}

function setmasteroctave(o) {
	masterOctave = Math.round(o);
}

function setbpmtrack(b) {
	currentBpm = b;
}

// --- presets ------------------------------------------------------------------------------------
// What replaced the ~190 lines that used to sit here.
//
// The old store was a JavaScript object mirroring every setting field by field. It had three
// problems and only the first was obvious. It lived in memory, so it did not survive reopening
// the Live set. It needed editing in two more places for every parameter added, on top of the
// setter and the three registries inside the .amxd. And -- the one that would have bitten
// hardest -- recalling a slot moved the ENGINE without moving the CONTROLS, so every dial in the
// device would have been left lying about what was playing.
//
// Live already knows all of these values: they are device parameters, it saves them with the set
// and it can set them back. So a preset here is a list of (name, value) read through the Live API
// and written next to the .amxd, exactly where savefavs() puts the favourites -- which makes the
// slots follow you from one set to the next instead of being trapped inside one song.
//
// Recall sets the parameters and then asks the controls to speak. That second half is the whole
// trick: setting a parameter through the API changes what a control DISPLAYS but does not fire
// its outlet, so the engine would never hear about it. `outputvalue` is the message that makes a
// live.* object emit what it holds, and the device already fans that message out to every control
// -- it is how the engine gets loaded when the set opens. Recall simply runs that path again.
var PRESET_FILE = "forteseq2_presets.txt";
var PRESET_SLOTS = 8;
var presetSlot = 1;
var presetBank = [];      // slot -> {name: value}; index 0 goes unused so slots read as they look
var presetIdOf = null;    // parameter longname -> Live API id, built once
var presetApi = null;     // ONE LiveAPI object, re-pointed by id rather than 183 of them

// Deliberately kept out of every slot. Run is the transport, and a preset that starts or stops
// the sequencer is a preset you cannot audition. Bus is an address rather than a sound, which is
// the same reason the old store left it out. Trig is momentary. Pagina is only where you happen
// to be looking, and Slot is the control you are about to press.
var PRESET_SKIP = { "Run": 1, "Bus": 1, "Trig": 1, "Pagina": 1, "Slot": 1 };

// Builds the name -> id map once. Doing it lazily rather than at load time matters: the device's
// own parameters are not all reachable through the API at the instant the js object is created,
// and a map built too early would be short without ever saying so.
function presetScan() {
	if (presetIdOf) return presetIdOf;
	if (typeof LiveAPI === "undefined") return null;   // fuera de Live no hay API, y los tests corren igual
	var map = {}, n = 0;
	try {
		var dev = new LiveAPI(null, "this_device");
		var ids = dev.get("parameters");   // ["id", 1, "id", 2, ...]
		presetApi = new LiveAPI(null);
		for (var i = 0; i < ids.length; i++) {
			if (typeof ids[i] !== "number") continue;
			presetApi.id = ids[i];
			var raw = presetApi.get("name");
			// A name with a space in it comes back as several atoms, so joining is not optional:
			// taking [0] would turn "Oct Maestra" into "Oct" and collide with anything shorter.
			// Duck-typed rather than tested with `instanceof Array`, for the same reason the test
			// harness uses Array.isArray: an array built in another realm is not an instance of
			// THIS realm's Array, instanceof answers false, and the name quietly becomes
			// "Oct,Maestra" -- near enough to look right in the file, wrong enough that it would
			// never match a parameter again.
			var nm = (raw && typeof raw.join === "function") ? raw.join(" ") : ("" + raw);
			if (nm && !map.hasOwnProperty(nm)) { map[nm] = ids[i]; n++; }
		}
	} catch (e) {
		post("forteseq2: no pude leer los parametros del device: " + e + "\n");
		return null;
	}
	presetIdOf = map;
	post("forteseq2: los presets ven " + n + " parametros\n");
	return map;
}

// Drops the map so the next store or recall rebuilds it. Worth having as a message rather than
// only as internal state: if the device is edited while the set is open, the ids move.
function presetrescan() {
	presetIdOf = null;
	presetApi = null;
	post("forteseq2: mapa de parametros descartado, se rearma en el proximo guardar o cargar\n");
}

function setpresetslot(n) {
	n = Math.round(n);
	if (!isFinite(n) || n < 1) n = 1;
	if (n > PRESET_SLOTS) n = PRESET_SLOTS;
	presetSlot = n;
}

// Both messages take the slot either as an argument or from the Slot control, so the buttons can
// stay bare `storepreset` / `recallpreset` messages and the number lives in one place.
function presetSlotOf(slot) {
	var s = (slot === undefined || slot === null) ? presetSlot : Math.round(slot);
	if (!(s >= 1 && s <= PRESET_SLOTS)) {
		post("forteseq2: el slot " + s + " esta fuera de rango (1.." + PRESET_SLOTS + ")\n");
		return -1;
	}
	return s;
}

function storepreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	var map = presetScan();
	if (!map) {
		post("forteseq2: los presets necesitan la Live API, que solo existe dentro de Live\n");
		return;
	}
	var vals = {}, n = 0;
	// Wrapped because an exception thrown inside a js object stops the whole script in Live:
	// the sequencer would go silent and the only clue would be one line in the console.
	try {
		for (var nm in map) {
			if (PRESET_SKIP[nm]) continue;
			presetApi.id = map[nm];
			var v = presetApi.get("value");
			vals[nm] = (v && typeof v.join === "function") ? v[0] : v;
			n++;
		}
	} catch (e) {
		post("forteseq2: fallo leyendo " + nm + ": " + e + "\n");
		return;
	}
	presetBank[s] = vals;
	savepresets();
	sendPresetList();
	post("forteseq2: slot " + s + " guardado, " + n + " parametros\n");
}

function recallpreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	var vals = presetBank[s];
	if (!vals) {
		post("forteseq2: el slot " + s + " esta vacio\n");
		return;
	}
	var map = presetScan();
	if (!map) {
		post("forteseq2: los presets necesitan la Live API, que solo existe dentro de Live\n");
		return;
	}
	var n = 0, miss = 0, nm = "";
	// Same reason as in storepreset(): a throw here would take the sequencer down with it.
	try {
		for (nm in vals) {
			// A name the device no longer has means a slot written by an older version. Skipping
			// it silently is the right call: the rest of the slot is still exactly what was saved,
			// and refusing the whole recall over one retired control would throw away the good part.
			if (!map.hasOwnProperty(nm)) { miss++; continue; }
			presetApi.id = map[nm];
			presetApi.set("value", vals[nm]);
			n++;
		}
	} catch (e) {
		post("forteseq2: fallo escribiendo " + nm + ": " + e + "\n");
	}
	// Sent even after a failure: a half-applied slot still has to reach the engine, or the
	// dials would be showing one thing while the sequencer plays another.
	// The controls now DISPLAY the slot but have not said so out loud. This is what makes them
	// speak, and it is the same message the device sends itself when the Live set opens.
	outlet(4, ["initui"]);
	post("forteseq2: slot " + s + " cargado, " + n + " parametros" +
		(miss ? " (" + miss + " que este device ya no tiene)" : "") + "\n");
}

function clearpreset(slot) {
	var s = presetSlotOf(slot);
	if (s < 0) return;
	presetBank[s] = null;
	savepresets();
	sendPresetList();
	post("forteseq2: slot " + s + " borrado\n");
}

// Which slots have something in them, as one symbol for a comment. Cheap enough to resend on
// every change, and without it the eight slots are eight identical blanks.
function sendPresetList() {
	var s = "";
	for (var i = 1; i <= PRESET_SLOTS; i++) s += (i > 1 ? " " : "") + (presetBank[i] ? i : "-");
	outlet(4, ["presetslots", s]);
}

// --- the slots on disk ---------------------------------------------------------------------------
// Tab separated rather than JSON, for one reason that outweighs the extra parsing: parameter
// names have spaces in them ("Oct Maestra", "V1 Grado", "M1 Forma"), so a space cannot separate
// fields, and a tab cannot appear inside a name. The file stays something you can open and read.
function savepresets() {
	if (typeof File === "undefined") return;
	var f = new File(devPath(PRESET_FILE), "write", "TEXT");
	if (!f.isopen) {
		post("forteseq2: no pude escribir " + devPath(PRESET_FILE) +
			", los slots duran hasta cerrar\n");
		return;
	}
	try {
		f.eof = 0;        // un banco mas chico no puede dejar la cola del anterior atras
		f.position = 0;
		f.writeline("forteseq2 presets 1");
		for (var s = 1; s <= PRESET_SLOTS; s++) {
			var vals = presetBank[s];
			if (!vals) continue;
			var line = "" + s;
			for (var nm in vals) line += "\t" + nm + "=" + vals[nm];
			f.writeline(line);
		}
	} catch (e) {
		post("forteseq2: fallo al guardar los presets: " + e + "\n");
	}
	f.close();
}

function loadpresets() {
	if (typeof File === "undefined") return;
	var f = new File(devPath(PRESET_FILE), "read", "TEXT");
	if (!f.isopen) return;   // todavia no hay archivo, que es el primer arranque y no un error
	presetBank = [];
	var count = 0;
	try {
		f.readline(200);   // la cabecera, que solo esta para que el archivo se explique solo
		while (f.position < f.eof) {
			var line = "" + f.readline(65536);
			var parts = line.split("\t");
			var s = Math.round(parseFloat(parts[0]));
			if (!(s >= 1 && s <= PRESET_SLOTS)) continue;
			var vals = {};
			for (var i = 1; i < parts.length; i++) {
				// lastIndexOf, not indexOf: a name may not contain "=" today, but splitting from
				// the right costs nothing and cannot be broken by one that does later.
				var eq = parts[i].lastIndexOf("=");
				if (eq <= 0) continue;
				var v = parseFloat(parts[i].slice(eq + 1));
				if (isFinite(v)) vals[parts[i].slice(0, eq)] = v;
			}
			presetBank[s] = vals;
			count++;
		}
	} catch (e) {
		post("forteseq2: fallo al leer los presets: " + e + "\n");
	}
	f.close();
	sendPresetList();
	post("forteseq2: " + count + " slots leidos de " + devPath(PRESET_FILE) + "\n");
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
	var vel = lo + Math.floor(Math.random() * (hi - lo + 1)) + Math.round(modAt(D_VEL));
	if (vel < 1) vel = 1;       // velocity 0 is a note-off, never a note
	if (vel > 127) vel = 127;

	// Length comes from a note-value denominator against the BPM, not from a fraction of the
	// step interval -- that is precisely what unhooks articulation from the BPM dial. div 4 is
	// one beat, so ms = (60000/bpm) * 4/div.
	var bpm = currentBpm > 0 ? currentBpm : 120;
	var div = groupDurDiv[g] > 0 ? groupDurDiv[g] : 16;
	var sil = groupSilence[g] + modAt(D_SIL);

	return {
		group: g,
		vel: vel,
		// Largo SCALES the length instead of replacing it, so a modulated note keeps the
		// proportion between the two articulation groups rather than flattening them together.
		dur: Math.max(1, (60000 / bpm) * (4 / div) * (1 + modAt(D_DUR) / 100)),
		rest: sil > 0 && (Math.random() * 100) < sil
	};
}

// --- the per-voice monitor --------------------------------------------------------------------
// One comment showing what each voice is playing. It used to be rebuilt and resent on every step:
// NUM_VOICES strings plus a list message plus a comment redraw, per note. Two things changed.
// It is skippable outright (setmonitor), because at speed nobody can read it anyway; and when it
// is on it only emits when the notes it names actually differ from the ones on screen, which in
// Acordes with a slow harmonic rhythm is a handful of times per pass instead of every step.
var monitorOn = 1;
var MON_SILENT = -1;                       // muted, external or resting: shows as "--"
var monShown = filled(MAX_VOICES, -2);     // what the comment currently reads
var monScratch = filled(MAX_VOICES, -2);   // what this step would put there; reused, never realloc'd
var monShownCount = -1;                    // the NUM_VOICES the visible line was built for

function setmonitor(x) {
	monitorOn = x ? 1 : 0;
	monShownCount = -1;   // switching it back on must repaint, whatever the notes are doing
}

function emitMonitor() {
	if (!monitorOn) return;
	var v;
	if (monShownCount === NUM_VOICES) {
		var same = 1;
		for (v = 0; v < NUM_VOICES; v++) if (monScratch[v] !== monShown[v]) { same = 0; break; }
		if (same) return;
	}
	var labelled = [];
	for (v = 0; v < NUM_VOICES; v++) {
		monShown[v] = monScratch[v];
		labelled.push("V" + (v + 1) + ":" +
			(monScratch[v] === MON_SILENT ? "--" : noteName(monScratch[v])));
	}
	monShownCount = NUM_VOICES;
	outlet(5, labelled);
}

function emitVoices(noteData) {
	// cardinality of the set currently sounding, for the "tie the accent cycle to n" option
	var curSet = sets[setIndex];
	var card = curSet ? curSet.length : 1;
	for (var v = 0; v < NUM_VOICES; v++) {
		if (voiceMute[v] || voiceExternal[v]) { monScratch[v] = MON_SILENT; continue; }
		// The voice's own pattern, read against the shared step because here every voice is
		// handed the same one. Off-cells drop out before any of the pitch work is done.
		if (!voiceSoundsAt(v, patternStep)) { monScratch[v] = MON_SILENT; continue; }
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
		if (art.rest) { monScratch[v] = MON_SILENT; continue; }

		monScratch[v] = repr;
		emitNote(v, art, shifted);
	}
	emitMonitor();
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
// `off` is added to every note of `a` on the way past, which is exactly
// chordDistance(shiftChord(a, off), b) without building the shifted copy. The voice leading tries
// sixty candidates per step and this is the inner loop of all sixty, so the array it is not
// allocating is the point. Order does not matter to the measure, so shifting in place is safe.
function chordDistance(a, off, b) {
	var total = 0, i, j, d, best, ai;
	for (i = 0; i < a.length; i++) {
		ai = a[i] + off;
		best = 1e9;
		for (j = 0; j < b.length; j++) { d = ai > b[j] ? ai - b[j] : b[j] - ai; if (d < best) best = d; }
		total += best;
	}
	for (j = 0; j < b.length; j++) {
		best = 1e9;
		for (i = 0; i < a.length; i++) { ai = a[i] + off; d = ai > b[j] ? ai - b[j] : b[j] - ai; if (d < best) best = d; }
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
// Every inversion of the current set, already voiced. This depends on nothing but (setIndex,
// voicingMode) -- lastChord does not enter into it -- so the same arrays stand for as long as the
// harmony holds. Rebuilding them per step was the bulk of what the voice leading cost: twelve
// closedStack walks, twelve applyVoicing slices and twelve sorts on every single note. Keyed on
// setIndex because chordFor() is only ever handed sets[setIndex].
var stackCache = null, stackCacheSet = -1, stackCacheVoicing = -1;

function voicedRotations(pcs) {
	if (stackCache && stackCacheSet === setIndex && stackCacheVoicing === voicingMode) return stackCache;
	var out = [];
	for (var r = 0; r < pcs.length; r++) out.push(applyVoicing(closedStack(pcs, r), voicingMode));
	stackCache = out;
	stackCacheSet = setIndex;
	stackCacheVoicing = voicingMode;
	return out;
}

function chordFor(pcs) {
	var er = effRoot();
	var cands = voicedRotations(pcs);
	var plain = cands[0];
	if (!voiceLead || !lastChord) {
		// A cached array leaves here. That is safe because emitVoices() only ever reads what it is
		// handed -- it builds its own shifted copy -- and it is the point: no allocation at all on
		// the path that most sets take.
		lastChord = shiftChord(plain, er);
		return plain;
	}
	// The winner is remembered as (which inversion, which octave) rather than as a built array, so
	// the loop allocates nothing and only the chord that actually won is ever materialised.
	var bestCand = plain, bestOct = 0, bestScore = 1e9;
	for (var r = 0; r < cands.length; r++) {
		var cand = cands[r];
		for (var o = -2; o <= 2; o++) {
			var off = o * 12 + er;
			var score = chordDistance(cand, off, lastChord) +
				Math.abs((cand[0] + off) - (CHORD_BASE + er)) * 0.25;
			if (score < bestScore) { bestScore = score; bestCand = cand; bestOct = o * 12; }
		}
	}
	var chosen = shiftChord(bestCand, bestOct);
	lastChord = shiftChord(chosen, er);
	return chosen;
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
	for (var v = 0; v < NUM_VOICES; v++) {
		// external voices belong to triggervoice(); the clock must not move their cursor too
		if (voiceExternal[v]) { monScratch[v] = MON_SILENT; continue; }
		var div = voiceDiv[v] > 0 ? voiceDiv[v] : 1;
		if (((patternStep - 1) % div) !== 0) { monScratch[v] = MON_SILENT; continue; }

		var pos = voicePos[v];
		// The pattern is read against the steps this voice is actually given, not against the
		// clock -- with a divider of 3 the voice sees every third step, and its rhythm counts
		// those. Reading it against the raw step instead would let a divider and a pattern land
		// on disjoint cells and silence the voice for good, which is a trap and not a feature.
		// The cursor still advances: an off-cell is a gate, like a mute or a rest, so the voice
		// keeps its place in the harmony instead of playing a slower melody.
		if (!voiceSoundsAt(v, (patternStep - 1) / div)) {
			voicePos[v] = pos + 1;
			monScratch[v] = MON_SILENT;
			continue;
		}
		// Acordes: the cursor is frozen at 0, so the voice holds its degree and the chord changes
		// only when the set does -- four voices at offsets 0,1,2,3 read as a four-part chorale.
		// Arpegio: the cursor walks, and the offset keeps the voices a fixed number of degrees apart.
		var readIdx = (mode === 1) ? pos : 0;
		var pc = pitchForDegree(pcs, degreeAt(n, readIdx) + voiceDegOffset[v] + modDeg());
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
		if (voiceMute[v] || art.rest) { monScratch[v] = MON_SILENT; continue; }

		monScratch[v] = note;
		emitNote(v, art, note);
	}
	emitMonitor();
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
	emitCircle(pcs);

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
			? MELODY_BASE + pitchForDegree(pcs, deg + modDeg())
			: MELODY_BASE + pcs[((deg + rotation + modDeg()) % n + n) % n]);
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

// --- per-voice rhythm -------------------------------------------------------------------

// Resolved once per change rather than once per step: bjorklund() allocates, and a voice's
// pattern only moves when someone turns one of its three dials.
function rebuildVoiceRhythm(v) {
	var n = voiceRhyLen[v];
	if (!(n >= 1)) { voiceRhyPat[v] = null; return; }
	var k = voiceRhyK[v] > n ? n : voiceRhyK[v];
	var pat = bjorklund(k, n);
	var r = ((voiceRhyRot[v] % n) + n) % n;
	var out = [];
	for (var i = 0; i < n; i++) out.push(pat[(i + r) % n]);
	voiceRhyPat[v] = out;
}

function rebuildAllVoiceRhythms() {
	for (var v = 0; v < MAX_VOICES; v++) rebuildVoiceRhythm(v);
}

// Does this voice speak on this cell of its own pattern? No pattern means yes, always, which
// keeps every voice exactly where it was before per-voice rhythm existed.
function voiceSoundsAt(v, idx) {
	var pat = voiceRhyPat[v];
	if (!pat) return 1;
	var n = pat.length;
	var i = Math.round(idx) % n;
	if (i < 0) i += n;
	return pat[i];
}

function setvoiceeuclen(v, n) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	n = Math.round(n);
	if (!isFinite(n) || n < 0) n = 0;
	if (n > ACCENT_MAX) n = ACCENT_MAX;
	voiceRhyLen[idx] = n;
	rebuildVoiceRhythm(idx);
}

function setvoiceeuck(v, k) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	k = Math.round(k);
	if (!isFinite(k) || k < 0) k = 0;
	if (k > ACCENT_MAX) k = ACCENT_MAX;
	voiceRhyK[idx] = k;
	rebuildVoiceRhythm(idx);
}

function setvoiceeucrot(v, r) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	r = Math.round(r);
	if (!isFinite(r) || r < 0) r = 0;
	if (r > ACCENT_MAX - 1) r = ACCENT_MAX - 1;
	voiceRhyRot[idx] = r;
	rebuildVoiceRhythm(idx);
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

// One metro tick. With subDiv = 1 that is one step, as it always was. Above that, only every
// subDiv-th tick runs the sequence and the rest exist so a note can be placed between two steps.
//
// step() SCHEDULES rather than sends, so the flush has to come after it or a note placed at
// offset 0 would wait a whole sub-tick. Placing it after also means notes queued by an earlier
// step and due now leave in the same pass, in the order they were queued.
function bang() {
	if (subDiv <= 1 || (subPos % subDiv) === 0) {
		modStep();          // before swingOffset(), which is one of the things it moves
		stepSwing = swingOffset();
		step();
		if (strumDir === 3) strumFlip = strumFlip ? 0 : 1;
	}
	flushPending();
	subPos++;
}
