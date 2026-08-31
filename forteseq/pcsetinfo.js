// pcsetinfo.js -- set-class analysis for the Tonnetz device, kept apart from the visual
// jsui so it can also feed a standalone display later. Pure analysis: it never touches the
// MIDI stream. Fed the same note feed as tonnetz.js.
//
//   inlet 0:
//     note <pitch> <vel>   MIDI note, ref-counted; vel 0 = off
//     list <pc> ...        set the active pitch-class set outright
//     clear                empty it
//     bang                 re-emit the current analysis
//
//   inlet 0 (study mode -- shapes without MIDI):
//     studyset <card> <idx1> <rot> <tonic> <inv>
//                          build a set from a Forte class and push it to the jsui as `list`
//                          + the usual `info` / `setclass`. card 1-12 (the union covers all
//                          351 Tn-classes), idx1 1-based position in the current traversal
//                          (clamped), rot rotates the interval necklace (0 = prime form;
//                          others its modes), tonic 0-11 anchor pc, inv 0|1 inverted form.
//                          Gated in the patch by the Study toggle.
//     disssort <0|1>       1 = order the walk by McKay dissonance (1 = least .. N = most)
//     studytrav <0..3>     restrict the walk: 0 all | 1 simetricos (inv. symmetric) |
//                          2 inv. de quintas (M7 == a rotation) | 3 espejo de quintas
//                          (M7 == the inversion). Composes with disssort.
//     studymove <0|1>      what `tonic` does: 0 = transpose the whole figure (default),
//                          1 = "Rota raiz": `list` stays the prime necklace at pc 0 and
//                          `studyspell <tonic>` tells the jsui to rotate names/colours on the
//                          chromatic Tonnetz + circles (shape looks pinned) while piano /
//                          guitar shift the lit notes by that amount (still real pitches).
//
//   outlet 0 -> tonnetz.js : `info <text>`      (one compact line for the jsui footer; starts
//                                               with the chord symbol, ends with `diso <pct>%
//                                               (<label>)`, `q5span <n>`, then any of the
//                                               invariance tags `sim` / `q5` / `q5esp`; also
//                                               carries `mod <McKay modality name>`)
//                            `setclass <p ...>` (prime form; lights the voice-leading node)
//                            `chord <sym>`      (root-relative chord symbol, e.g. `C7/E`; `-`
//                                               = none, `""` = empty set)
//                            `keyguess <root> <minor> <conf>`  (Krumhansl-Schmuckler key
//                                               estimate over a rolling window; suppressed in
//                                               study mode. root 0-11, minor 0|1, conf ~0..1)
//                            `list <pc ...>`    (study mode only; the set to display)
//                            `studyroot <pc>`   (study mode: pc to draw as the root, -1 = none)
//                            `studyspell <n>`   (Rota raiz: rotate names/colours by n semitones)
//   outlet 1 -> future display : tagged lists, one per field:
//     card <n> | notes <name...> | chord <sym> | chords <alt...> | forte <sym> |
//     iv <a b c d e f> | prime <p...> | name <sym> | modality <McKay name> |
//     diso <pct 0..100, McKay> | q5span <n 0..11> | keyguess <root> <minor> <conf> |
//     inv <sym> <fifthSame> <fifthMirror> | tn <index> <351>
//
// Forte data (cardinalities 3-9) embedded from Wikipedia "List of set classes". Prime form
// and normal order use the Rahn algorithm; A/B suffix from which representative the sounding
// set matches. Sets whose Rahn prime differs from the table (a handful of hexachords) still
// resolve to the base Forte number via a transposition/inversion-invariant fingerprint.

autowatch = 1;
inlets = 1;
outlets = 2;

var NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

// forte | prime-per-row (Rahn normal order transposed to 0; chars 0-9, A=10) | ic-vector.
// Cardinalities 3-6 only, verbatim from Wikipedia "List of set classes". Sets of cardinality
// 7-11 are resolved from their complements (which share the Forte ordinal); 1, 2 and 12 are
// special-cased. This keeps the embedded table small and side-steps transcription risk in
// the large-cardinality rows.
var FORTE_RAW =
"3-1|012|210000 3-2A|013|111000 3-2B|023|111000 3-3A|014|101100 3-3B|034|101100 " +
"3-4A|015|100110 3-4B|045|100110 3-5A|016|100011 3-5B|056|100011 3-6|024|020100 " +
"3-7A|025|011010 3-7B|035|011010 3-8A|026|010101 3-8B|046|010101 3-9|027|010020 " +
"3-10|036|002001 3-11A|037|001110 3-11B|047|001110 3-12|048|000300 " +
"4-1|0123|321000 4-2A|0124|221100 4-2B|0234|221100 4-3|0134|212100 4-4A|0125|211110 " +
"4-4B|0345|211110 4-5A|0126|210111 4-5B|0456|210111 4-6|0127|210021 4-7|0145|201210 " +
"4-8|0156|200121 4-9|0167|200022 4-10|0235|122010 4-11A|0135|121110 4-11B|0245|121110 " +
"4-12A|0236|112101 4-12B|0346|112101 4-13A|0136|112011 4-13B|0356|112011 " +
"4-14A|0237|111120 4-14B|0457|111120 4-Z15A|0146|111111 4-Z15B|0256|111111 " +
"4-16A|0157|110121 4-16B|0267|110121 4-17|0347|102210 4-18A|0147|102111 4-18B|0367|102111 " +
"4-19A|0148|101310 4-19B|0348|101310 4-20|0158|101220 4-21|0246|030201 4-22A|0247|021120 " +
"4-22B|0357|021120 4-23|0257|021030 4-24|0248|020301 4-25|0268|020202 4-26|0358|012120 " +
"4-27A|0258|012111 4-27B|0368|012111 4-28|0369|004002 4-Z29A|0137|111111 4-Z29B|0467|111111 " +
"5-1|01234|432100 5-2A|01235|332110 5-2B|02345|332110 5-3A|01245|322210 5-3B|01345|322210 " +
"5-4A|01236|322111 5-4B|03456|322111 5-5A|01237|321121 5-5B|04567|321121 5-6A|01256|311221 " +
"5-6B|01456|311221 5-7A|01267|310132 5-7B|01567|310132 5-8|02346|232201 5-9A|01246|231211 " +
"5-9B|02456|231211 5-10A|01346|223111 5-10B|02356|223111 5-11A|02347|222220 5-11B|03457|222220 " +
"5-Z12|01356|222121 5-13A|01248|221311 5-13B|02348|221311 5-14A|01257|221131 5-14B|02567|221131 " +
"5-15|01268|220222 5-16A|01347|213211 5-16B|03467|213211 5-Z17|01348|212320 5-Z18A|01457|212221 " +
"5-Z18B|02367|212221 5-19A|01367|212122 5-19B|01467|212122 5-20A|01568|211231 5-20B|02378|211231 " +
"5-21A|01458|202420 5-21B|03478|202420 5-22|01478|202321 5-23A|02357|132130 5-23B|02457|132130 " +
"5-24A|01357|131221 5-24B|02467|131221 5-25A|02358|123121 5-25B|03568|123121 5-26A|02458|122311 " +
"5-26B|03468|122311 5-27A|01358|122230 5-27B|03578|122230 5-28A|02368|122212 5-28B|02568|122212 " +
"5-29A|01368|122131 5-29B|02578|122131 5-30A|01468|121321 5-30B|02478|121321 5-31A|01369|114112 " +
"5-31B|02369|114112 5-32A|01469|113221 5-32B|02569|113221 5-33|02468|040402 5-34|02469|032221 " +
"5-35|02479|032140 5-Z36A|01247|222121 5-Z36B|03567|222121 5-Z37|03458|212320 5-Z38A|01258|212221 " +
"5-Z38B|03678|212221 " +
"6-1|012345|543210 6-2A|012346|443211 6-2B|023456|443211 6-Z3A|012356|433221 6-Z3B|013456|433221 " +
"6-Z4|012456|432321 6-5A|012367|422232 6-5B|014567|422232 6-Z6|012567|421242 6-7|012678|420243 " +
"6-8|023457|343230 6-9A|012357|342231 6-9B|024567|342231 6-Z10A|013457|333321 6-Z10B|023467|333321 " +
"6-Z11A|012457|333231 6-Z11B|023567|333231 6-Z12A|012467|332232 6-Z12B|013567|332232 " +
"6-Z13|013467|324222 6-14A|013458|323430 6-14B|034578|323430 6-15A|012458|323421 6-15B|034678|323421 " +
"6-16A|014568|322431 6-16B|023478|322431 6-Z17A|012478|322332 6-Z17B|014678|322332 " +
"6-18A|012578|322242 6-18B|013678|322242 6-Z19A|013478|313431 6-Z19B|014578|313431 6-20|014589|303630 " +
"6-21A|023468|242412 6-21B|024568|242412 6-22A|012468|241422 6-22B|024678|241422 6-Z23|023568|234222 " +
"6-Z24A|013468|233331 6-Z24B|024578|233331 6-Z25A|013568|233241 6-Z25B|023578|233241 6-Z26|013578|232341 " +
"6-27A|013469|225222 6-27B|023569|225222 6-Z28|013569|224322 6-Z29|023679|224232 6-30A|013679|224223 " +
"6-30B|023689|224223 6-31A|014579|223431 6-31B|024589|223431 6-32|024579|143250 6-33A|023579|143241 " +
"6-33B|024679|143241 6-34A|013579|142422 6-34B|024689|142422 6-35|02468A|060603 " +
"6-Z36A|012347|433221 6-Z36B|034567|433221 6-Z37|012348|432321 6-Z38|012378|421242 " +
"6-Z39A|023458|333321 6-Z39B|034568|333321 6-Z40A|012358|333231 6-Z40B|035678|333231 " +
"6-Z41A|012368|332232 6-Z41B|025678|332232 6-Z42|012369|324222 6-Z43A|012568|322332 6-Z43B|023678|322332 " +
"6-Z44A|012569|313431 6-Z44B|014569|313431 6-Z45|023469|234222 6-Z46A|012469|233331 6-Z46B|024569|233331 " +
"6-Z47A|012479|233241 6-Z47B|023479|233241 6-Z48|012579|232341 6-Z49|013479|224322 6-Z50|014679|224232";

var byPrime = {};    // prime string "0,3,6,8" -> forte "4-27B"
var byCanon = {};    // Tn/I fingerprint mask -> base forte "4-27"
var icvByForte = {}; // forte -> "012111"

(function buildTables() {
	var toks = FORTE_RAW.replace(/\s+/g, " ").split(" ");
	for (var i = 0; i < toks.length; i++) {
		var t = toks[i];
		if (!t) continue;
		var f = t.split("|");
		if (f.length !== 3) continue;
		var forte = f[0];
		var pcs = [];
		for (var c = 0; c < f[1].length; c++) {
			var ch = f[1].charAt(c);
			pcs.push(ch === "A" ? 10 : ch === "B" ? 11 : parseInt(ch, 10));
		}
		byPrime[pcs.join(",")] = forte;
		var base = forte.replace(/[AB]$/, "");
		var cm = canonMask(pcs);
		if (byCanon[cm] === undefined) byCanon[cm] = base;
		icvByForte[forte] = f[2];
	}
})();

// ---- pitch-class-set math -----------------------------------------------------------
function mod12(n) { return ((n % 12) + 12) % 12; }

function uniqSorted(pcs) {
	var s = [];
	for (var i = 0; i < pcs.length; i++) {
		var p = mod12(Math.round(pcs[i]));
		if (s.indexOf(p) < 0) s.push(p);
	}
	s.sort(function (a, b) { return a - b; });
	return s;
}

// Rahn normal order, then transposed so it starts at 0. Returns [] for empty.
function normal0(pcs) {
	var s = uniqSorted(pcs);
	var n = s.length;
	if (n === 0) return [];
	if (n === 1) return [0];
	var best = null;
	for (var i = 0; i < n; i++) {
		var rot = [];
		for (var j = 0; j < n; j++) rot.push(mod12(s[(i + j) % n] - s[i]));
		if (best === null || moreCompact(rot, best)) best = rot;
	}
	return best;
}

// is a more compact than b? compare outermost interval inward (Rahn), then leftmost pcs.
function moreCompact(a, b) {
	for (var k = a.length - 1; k >= 1; k--) {
		if (a[k] !== b[k]) return a[k] < b[k];
	}
	for (var m = 1; m < a.length; m++) {
		if (a[m] !== b[m]) return a[m] < b[m];
	}
	return false;
}

function invert(pcs) {
	var out = [];
	for (var i = 0; i < pcs.length; i++) out.push(mod12(-pcs[i]));
	return out;
}

// Rahn prime form (transposed to 0): the more compact of normal0(set) and normal0(inverse).
function primeForm(pcs) {
	var a = normal0(pcs);
	if (a.length < 2) return a;
	var b = normal0(invert(pcs));
	return moreCompact(b, a) ? b : a;
}

// transposition/inversion-invariant fingerprint: min 12-bit mask over all 24 T/I images.
function canonMask(pcs) {
	var s = uniqSorted(pcs);
	var m = 0;
	for (var i = 0; i < s.length; i++) m |= (1 << s[i]);
	var best = 0xFFF;
	for (var inv = 0; inv < 2; inv++) {
		var mm = inv ? invMask(m) : m;
		for (var t = 0; t < 12; t++) {
			if (mm < best) best = mm;
			mm = ((mm << 1) | (mm >> 11)) & 0xFFF;
		}
	}
	return best;
}
function invMask(m) {
	var r = 0;
	for (var p = 0; p < 12; p++) if (m & (1 << p)) r |= (1 << mod12(-p));
	return r;
}

// transposition-only fingerprint: min 12-bit mask over the 12 rotations (no inversion).
function tnMask(pcs) {
	var s = uniqSorted(pcs);
	if (!s.length) return 0;
	var m = 0, i;
	for (i = 0; i < s.length; i++) m |= (1 << s[i]);
	var best = m, cur = m;
	for (var r = 0; r < 11; r++) { cur = ((cur << 1) | (cur >> 11)) & 0xFFF; if (cur < best) best = cur; }
	return best;
}
// M7: the circle-of-fifths map, pc -> 7*pc mod 12 (self-inverse). Drawing a set on the
// fifths circle == drawing mul7(set) on the chromatic circle.
function mul7(pcs) {
	var o = [];
	for (var i = 0; i < pcs.length; i++) o.push(mod12(7 * pcs[i]));
	return o;
}
// M5: the by-fourths reading, pc -> 5*pc mod 12 (= invert of M7). Used for McKay's modality.
function mul5(pcs) {
	var o = [];
	for (var i = 0; i < pcs.length; i++) o.push(mod12(5 * pcs[i]));
	return o;
}

// McKay's "modalities" (Harmonic Processions, ch. 26), transcribed verbatim from FORTESEQ2
// (forteseq2.js MODALITY_TABLE): name a set by its QUINTAL prime form -- pack it along the
// circle of fifths (M7) or fourths (M5), whichever is tighter -- then read its span
// (offsets[last] + 1, the book counts the anchor as span 1) and which "extra" fifths (7,8,9)
// beyond the diatonic envelope it holds. Span 8+ splits sharp vs flat by which reading won.
var MODALITY_TABLE = [
	{ span: 3,  mask: 0, sharp: "Suspended Triad",   flat: "Suspended Triad" },
	{ span: 4,  mask: 0, sharp: "Quartal",           flat: "Quartal" },
	{ span: 5,  mask: 0, sharp: "Pentatonic",        flat: "Pentatonic" },
	{ span: 6,  mask: 0, sharp: "Ionian Hexachord",  flat: "Ionian Hexachord" },
	{ span: 7,  mask: 0, sharp: "Diatonic",          flat: "Diatonic" },
	{ span: 8,  mask: 0, sharp: "Lydian",            flat: "Mixolydian" },
	{ span: 9,  mask: 0, sharp: "Enigmatic",         flat: "Mystic" },
	{ span: 9,  mask: 1, sharp: "Blues",             flat: "Blues" },
	{ span: 10, mask: 0, sharp: "Diminished",        flat: "Diminished" },
	{ span: 10, mask: 1, sharp: "Hungarian",         flat: "Romanian" },
	{ span: 10, mask: 2, sharp: "Augmented",         flat: "Augmented" },
	{ span: 10, mask: 3, sharp: "Chromatic F#C#G#",  flat: "Chromatic BbEbAb" },
	{ span: 11, mask: 2, sharp: "Whole-Tone",        flat: "Whole-Tone" },
	{ span: 11, mask: 3, sharp: "Chromatic F#C#D#",  flat: "Chromatic BbEbDb" },
	{ span: 11, mask: 5, sharp: "Octatonic",         flat: "Octatonic" },
	{ span: 11, mask: 6, sharp: "Chromatic C#G#D#",  flat: "Chromatic EbAbDb" },
	{ span: 11, mask: 7, sharp: "Chromatic F#C#G#D#", flat: "Chromatic BbEbAbDb" },
	{ span: 12, mask: 7, sharp: "12-Tone",           flat: "12-Tone" }
];
var MODALITY_KEY = {};
for (var _mi = 0; _mi < MODALITY_TABLE.length; _mi++)
	MODALITY_KEY[MODALITY_TABLE[_mi].span + "," + MODALITY_TABLE[_mi].mask] = MODALITY_TABLE[_mi];

function npEntry(offs) {
	var n = 0;
	for (var k = 0; k < offs.length; k++) n += Math.pow(10, offs[k]);
	return n;
}
function spanMask(offs) {
	var mx = offs[offs.length - 1], m = 0;
	for (var k = 0; k < offs.length; k++) {
		var o = offs[k];
		if (o === mx) continue;   // the span-defining note itself is not a distinguishing extra
		if (o === 7) m |= 1;
		else if (o === 8) m |= 2;
		else if (o === 9) m |= 4;
	}
	return { span: mx + 1, mask: m };
}
// McKay modality name, or "" if the set is too small / off the table.
function modalityName(pcs) {
	var s = uniqSorted(pcs);
	if (s.length < 2) return "";
	var sharp = normal0(mul7(s)), flat = normal0(mul5(s));
	var eS = npEntry(sharp), eF = npEntry(flat), proj, win;
	if (eS < eF) { proj = "sharp"; win = sharp; }
	else if (eF < eS) { proj = "flat"; win = flat; }
	else { proj = "sym"; win = sharp; }
	var sm = spanMask(win);
	var e = MODALITY_KEY[sm.span + "," + sm.mask];
	if (!e) return "";
	if (proj === "sym") return e.sharp === e.flat ? e.sharp : e.sharp + "/" + e.flat;
	return proj === "sharp" ? e.sharp : e.flat;
}

// inversionally symmetric: the set equals its own mirror (interval necklace is a palindrome).
function isInvSym(pcs) { return tnMask(pcs) === tnMask(invert(pcs)); }
// "invarianza de quintas": chromatic and fifths-circle shapes match by rotation alone.
function isFifthSame(pcs) { return tnMask(pcs) === tnMask(mul7(pcs)); }
// "espejo de quintas": they match only after a flip -- M7 gives the inversion, not a rotation.
function isFifthMirror(pcs) { return !isFifthSame(pcs) && canonMask(pcs) === canonMask(mul7(pcs)); }

function intervalVector(pcs) {
	var s = uniqSorted(pcs);
	var v = [0, 0, 0, 0, 0, 0];
	for (var i = 0; i < s.length; i++)
		for (var j = i + 1; j < s.length; j++) {
			var d = mod12(s[j] - s[i]);
			if (d > 6) d = 12 - d;
			if (d >= 1) v[d - 1]++;
		}
	return v;
}

function complement(pcs) {
	var s = uniqSorted(pcs), out = [];
	for (var p = 0; p < 12; p++) if (s.indexOf(p) < 0) out.push(p);
	return out;
}

// Forte label for a set.
//   card 3-6 : look up the set's own normal order (matches the A or B row directly), then
//              the prime form, then a T/I fingerprint for at least the base number.
//   card 7-11: the complement shares the ordinal -- resolve that and swap the cardinal.
//   card 1,2,12: fixed.
function forteName(pcs) {
	var s = uniqSorted(pcs);
	var n = s.length;
	if (n === 0) return "";
	if (n === 1) return "1-1";
	if (n === 12) return "12-1";
	if (n === 2) {
		var d = mod12(s[1] - s[0]); if (d > 6) d = 12 - d;
		return "2-" + d;
	}
	if (n >= 7) {
		var cf = forteName(complement(s));
		return cf ? (n + cf.substring(cf.indexOf("-"))) : "";
	}
	var nf = normal0(s).join(",");
	if (byPrime[nf]) return byPrime[nf];
	var p = primeForm(s).join(",");
	if (byPrime[p]) return byPrime[p];
	var cm = canonMask(s);
	return byCanon[cm] !== undefined ? byCanon[cm] : "";
}

// small dictionary of familiar sonorities, keyed by Forte label (with A/B where relevant)
var NAMES = {
	"3-11A": "triada menor", "3-11B": "triada mayor", "3-10": "triada disminuida",
	"3-12": "triada aumentada", "3-9": "cuartal (sus)", "3-6": "tono entero (3)",
	"3-7A": "incompleta de 7a",
	"4-27B": "7a de dominante", "4-27A": "semidisminuida (m7b5)", "4-26": "7a menor",
	"4-20": "7a mayor", "4-19A": "menor (maj7)", "4-19B": "aumentada (maj7)",
	"4-28": "7a disminuida", "4-25": "6a aumentada (francesa)", "4-23": "cuartal",
	"4-24": "aumentada add9", "4-22A": "mayor add9", "4-21": "tono entero (4)",
	"5-35": "pentatonica", "5-34": "dominante 9", "5-33": "tono entero (5)",
	"6-35": "tono entero (hexatonia)", "6-32": "hexacordo diatonico",
	"6-20": "escala aumentada (hexatonia)", "6-7": "hexacordo simetrico (E)",
	"7-35": "escala diatonica", "7-34": "menor melodica asc",
	"7-32A": "menor armonica", "7-32B": "mayor armonica",
	"8-28": "escala octatonica", "9-12": "eneacordo aumentado"
};

function ivString(v) {
	for (var i = 0; i < v.length; i++) if (v[i] > 9) return v.join(" ");
	return v.join("");
}

// ---- root-relative chord naming (ai.chord-monitor / pychord idea) ------------------
// A chord SYMBOL, unlike a set class, has a chosen root. For every sounding pc we try it as
// the root, read the intervals above it, and look the shape up in CHORD_QUALITIES (key =
// the sorted interval set, "0" always first). Candidates are ranked so the bass note wins
// when it explains the chord, then completeness, then a natural-spelled root.
var SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
var FLAT_NAMES  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
// pc -> the tidier of the two spellings (naturals first, then whichever is shorter)
function noteName(pc) {
	pc = mod12(pc);
	var a = SHARP_NAMES[pc], b = FLAT_NAMES[pc];
	if (a.length === 1) return a;
	return b.length <= a.length ? b : a;
}
function accidentals(pc) { return noteName(pc).length - 1; }

// key = interval set above the root; value = quality suffix ("" = bare major triad).
var CHORD_QUALITIES = {
	"0,4,7": "", "0,3,7": "m", "0,3,6": "dim", "0,4,8": "aug",
	"0,2,7": "sus2", "0,5,7": "sus4",
	"0,4,7,9": "6", "0,3,7,9": "m6", "0,4,7,10": "7", "0,4,7,11": "maj7",
	"0,3,7,10": "m7", "0,3,6,10": "m7b5", "0,3,6,9": "dim7", "0,3,7,11": "mMaj7",
	"0,4,8,10": "aug7", "0,4,8,11": "augMaj7", "0,4,7,10,14": "9", "0,4,7,11,14": "maj9",
	"0,3,7,10,14": "m9", "0,4,7,10,13": "7b9", "0,2,4,7": "add9", "0,2,3,7": "m(add9)",
	"0,4,7,9,14": "6/9", "0,5,10": "quartal", "0,4,7,10,17": "11", "0,4,7,10,21": "13",
	"0,4,6,10": "7b5", "0,4,8,10,14": "9#5", "0,1,4,7": "sus(b9)"
};
// partial fallbacks: a 4-note shape missing its fifth still reads as the seventh chord
var CHORD_QUALITIES_PARTIAL = {
	"0,4,10": "7 (no5)", "0,3,10": "m7 (no5)", "0,4,11": "maj7 (no5)", "0,4,9": "6 (no5)"
};
// prior on naming when two roots both fit (Am7 == C6, Bm7b5 == Dm6): a tertian stack
// beats a chord with an added 2nd/6th. Higher = the name we'd rather print.
function qualityRank(q) {
	if (q === "" || q === "m") return 6;                                  // plain triads
	if (q === "7" || q === "maj7" || q === "m7" || q === "m7b5" ||
	    q === "dim7" || q === "mMaj7") return 5;                          // core sevenths
	if (q === "dim" || q === "aug" || q === "sus2" || q === "sus4") return 4;
	if (/^(9|maj9|m9|11|13|7b9|7b5|9#5|augMaj7|aug7)$/.test(q)) return 3; // extensions
	if (/no5/.test(q)) return 1;
	return 2;                                                             // 6, m6, add9, 6/9, quartal, ...
}

// -> { sym: "C7", full: "C7/E", alts: ["Am add..","..."] }  (or the single note name)
function nameChord(pcs, bass) {
	var s = uniqSorted(pcs);
	if (s.length === 0) return { sym: "", full: "", alts: [] };
	if (s.length === 1) { var n1 = noteName(s[0]); return { sym: n1, full: n1, alts: [] }; }
	var cands = [];
	for (var i = 0; i < s.length; i++) {
		var root = s[i], ivs = [];
		for (var j = 0; j < s.length; j++) ivs.push(mod12(s[j] - root));
		ivs.sort(function (a, b) { return a - b; });
		var key = ivs.join(",");
		var q = CHORD_QUALITIES[key], partial = false;
		if (q === undefined && CHORD_QUALITIES_PARTIAL[key] !== undefined) { q = CHORD_QUALITIES_PARTIAL[key]; partial = true; }
		if (q === undefined) continue;
		var score = 40 + qualityRank(q) * 3;
		if (bass >= 0 && mod12(bass) === root) score += 100;
		if (partial) score -= 15;
		score -= accidentals(root);
		score -= root === s[0] ? 0 : 1;   // tiny nudge toward the lowest pc as root
		cands.push({ root: root, sym: noteName(root) + q, score: score });
	}
	if (cands.length === 0) {
		// nothing matched: fall back to the Forte familiar-name, anchored at the prime form
		var fb = NAMES[forteName(s)] || "";
		var anchor = noteName(s[0]);
		return { sym: fb ? anchor + " " + fb : anchor + "?", full: fb ? anchor + " " + fb : anchor + "?", alts: [] };
	}
	cands.sort(function (a, b) { return b.score - a.score; });
	var best = cands[0];
	var full = best.sym;
	if (bass >= 0 && mod12(bass) !== best.root && s.indexOf(mod12(bass)) >= 0)
		full = best.sym + "/" + noteName(bass);
	var alts = [];
	for (var k = 1; k < cands.length && alts.length < 2; k++)
		if (cands[k].sym !== best.sym) alts.push(cands[k].sym);
	return { sym: best.sym, full: full, alts: alts };
}

// ---- Krumhansl-Schmuckler key finding (ai.scale-monitor idea) ---------------------
// Correlate a pitch-class histogram against the 24 major/minor tone profiles. We have no
// note durations, so the histogram is summed membership over a rolling window of recent
// pc-sets (same trick as tonnetzfit.js). Returns {root, minor, conf}; conf is the winning
// Pearson r (roughly 0..1), plus the margin over the runner-up folded in.
var KS_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88];
var KS_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17];
function pearson(a, b) {
	var n = a.length, sa = 0, sb = 0, saa = 0, sbb = 0, sab = 0;
	for (var i = 0; i < n; i++) { sa += a[i]; sb += b[i]; saa += a[i] * a[i]; sbb += b[i] * b[i]; sab += a[i] * b[i]; }
	var num = n * sab - sa * sb;
	var den = Math.sqrt((n * saa - sa * sa) * (n * sbb - sb * sb));
	return den === 0 ? 0 : num / den;
}
function detectKey(hist) {
	var total = 0;
	for (var i = 0; i < 12; i++) total += hist[i];
	if (total === 0) return { root: 0, minor: 0, conf: 0 };
	var best = null, second = -2;
	for (var root = 0; root < 12; root++) {
		var rot = [];
		for (var k = 0; k < 12; k++) rot.push(hist[mod12(root + k)]);
		var rMaj = pearson(rot, KS_MAJOR), rMin = pearson(rot, KS_MINOR);
		var pick = rMaj >= rMin ? { root: root, minor: 0, r: rMaj } : { root: root, minor: 1, r: rMin };
		if (!best || pick.r > best.r) { second = best ? best.r : second; best = pick; }
		else if (pick.r > second) second = pick.r;
	}
	var conf = Math.max(0, best.r) * (0.6 + 0.4 * Math.max(0, Math.min(1, (best.r - second) * 4)));
	return { root: best.root, minor: best.minor, conf: conf };
}

// widest empty arc on the circle of fifths, in fifth-steps (0 = one pc, 12 = whole circle).
// Small = the set packs tightly in fifths (consonant, diatonic); large = scattered. This is
// the spread zb.noteConsonance reads off the same circle.
function fifthSpan(pcs) {
	var s = uniqSorted(pcs);
	if (s.length < 2) return 0;
	var f = [];
	for (var i = 0; i < s.length; i++) f.push(mod12(s[i] * 7));
	f.sort(function (a, b) { return a - b; });
	var span = 12 - (f[f.length - 1] - f[0]);   // gap that wraps around
	for (var k = 1; k < f.length; k++) span = Math.max(span, f[k] - f[k - 1]);
	return 12 - span;   // report the OCCUPIED arc: 0 tight .. 11 scattered
}

// ---- state + handlers -------------------------------------------------------------
var voices = [];
for (var _i = 0; _i < 12; _i++) voices[_i] = 0;
var explicit = null;   // non-null when set by `list` instead of note ref-counting

// per-MIDI-note ref-count, so the chord namer knows the actual bass (list/study sets have
// no octave -> bassMidi() returns -1 there and the ranking falls back to completeness).
var midiHeld = [];
for (var _m = 0; _m < 128; _m++) midiHeld[_m] = 0;
function bassMidi() {
	if (explicit) return -1;
	for (var n = 0; n < 128; n++) if (midiHeld[n] > 0) return n;
	return -1;
}

// rolling window of recent pc-sets for Krumhansl-Schmuckler key finding (see detectKey).
// each entry keeps the set's bass pc (-1 if unknown) so the histogram can lean on it -- the
// bass carries most of the tonal weight and is what separates a key from its relative.
var keyWin = [];
var KEY_WIN_MAX = 16;
function pushKeyWin(pcs, bassPc) {
	if (!pcs.length) return;
	var arr = pcs.slice().sort(function (a, b) { return a - b; });
	var s = arr.join(","), bp = (bassPc == null ? -1 : bassPc);
	var e = s + "@" + bp;
	if (keyWin.length) {
		var prev = keyWin[keyWin.length - 1].split("@");
		var pArr = prev[0].split(",");
		// same bass and the new set only adds notes -> a chord still being built up; replace
		// the in-progress entry instead of stacking fragments of one sonority
		if (parseInt(prev[1], 10) === bp && pArr.every(function (x) { return arr.indexOf(parseInt(x, 10)) >= 0; })) {
			keyWin[keyWin.length - 1] = e;
			return;
		}
		if (keyWin[keyWin.length - 1] === e) return;
	}
	keyWin.push(e);
	while (keyWin.length > KEY_WIN_MAX) keyWin.shift();
}
function keyHistogram() {
	var h = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
	var n = keyWin.length;
	for (var i = 0; i < n; i++) {
		if (!keyWin[i]) continue;
		var at = keyWin[i].split("@");
		var parts = at[0].split(","), bp = parseInt(at[1], 10);
		// recent sets weigh much more -- a cadence resolves, and the goal chord names the key
		var w = Math.pow((i + 1) / n, 1.6);
		for (var k = 0; k < parts.length; k++) h[mod12(parseInt(parts[k], 10))] += w;
		if (bp >= 0) h[mod12(bp)] += w * 1.5;   // tonal centre of gravity
	}
	return h;
}
function lowestHeldPc() {
	for (var n = 0; n < 128; n++) if (midiHeld[n] > 0) return mod12(n);
	return -1;
}

function activePcs() {
	if (explicit) return explicit.slice();
	var a = [];
	for (var pc = 0; pc < 12; pc++) if (voices[pc] > 0) a.push(pc);
	return a;
}

var studyTag = "";     // "3-11B  12/19" while a study set is showing; cleared by any MIDI
var studyRoot = -1;    // the pc drawn as the root marker in study mode; -1 = none
var spellRot = 0;      // Rota raiz: semitones to rotate the jsui's note names / colours by

function note(pitch, vel) {
	explicit = null;
	studyTag = "";
	studyRoot = -1;
	spellRot = 0;
	var n = Math.round(pitch);
	var pc = mod12(n);
	if (vel > 0) {
		voices[pc]++;
		if (n >= 0 && n < 128) midiHeld[n]++;
		// only a note-ON is a musical event for key finding; releasing a chord one finger at
		// a time would otherwise flood the window with shrinking fragments and a drifting bass
		pushKeyWin(activePcs(), lowestHeldPc());
	} else {
		if (voices[pc] > 0) voices[pc]--;
		if (n >= 0 && n < 128 && midiHeld[n] > 0) midiHeld[n]--;
	}
	emit();
}
function list() {
	explicit = uniqSorted(arrayfromargs(arguments));
	pushKeyWin(explicit, explicit.length ? explicit[0] : -1);
	emit();
}
function clear() {
	for (var i = 0; i < 12; i++) voices[i] = 0;
	for (var m = 0; m < 128; m++) midiHeld[m] = 0;
	keyWin = [];
	explicit = null;
	studyTag = "";
	studyRoot = -1;
	spellRot = 0;
	emit();
}
function bang() { emit(); }

// ---- study mode: a set from a Forte class, no MIDI ---------------------------------
// BY_CARD[n] = every card-n Forte catalog entry as {pcs (prime form, starts at 0), forte},
// in catalog order, A and B (the two inversions) kept as SEPARATE entries. Full range 1..12:
// 1,6,19,43,66,80,66,43,19,6,1,1 = 351 (every non-empty Tn-class). 3-6 straight from
// FORTE_RAW; 1 and 2 synthetic; 7-12 = complements of the 5..0 catalog (same count each).
var BY_CARD = null;
function buildByCard() {
	BY_CARD = {};
	var toks = FORTE_RAW.replace(/\s+/g, " ").split(" ");
	for (var i = 0; i < toks.length; i++) {
		var f = toks[i].split("|");
		if (f.length !== 3) continue;
		var pcs = [];
		for (var c = 0; c < f[1].length; c++) {
			var ch = f[1].charAt(c);
			pcs.push(ch === "A" ? 10 : ch === "B" ? 11 : parseInt(ch, 10));
		}
		var cd = pcs.length;
		if (!BY_CARD[cd]) BY_CARD[cd] = [];
		BY_CARD[cd].push({ pcs: pcs, forte: f[0] });
	}
	BY_CARD[1] = [{ pcs: [0], forte: "1-1" }];
	BY_CARD[2] = [];
	for (var d = 1; d <= 6; d++) BY_CARD[2].push({ pcs: [0, d], forte: "2-" + d });
	for (var cc = 7; cc <= 11; cc++) {          // 7<-5, 8<-4, 9<-3, 10<-2, 11<-1
		var src = BY_CARD[12 - cc] || [];
		BY_CARD[cc] = [];
		for (var k = 0; k < src.length; k++) {
			// primeForm collapses inversion, so an A source and its B source both land on
			// the complement class's A form. Re-derive A here and flip it for the B rows so
			// 7-29A / 7-29B (etc.) stay the two distinct inversions the user studies.
			var sf = src[k].forte;
			var pf = primeForm(complement(src[k].pcs));
			BY_CARD[cc].push({
				pcs: sf.charAt(sf.length - 1) === "B" ? normal0(invert(pf)) : pf,
				forte: cc + sf.substring(sf.indexOf("-"))
			});
		}
	}
	var agg = [];
	for (var p = 0; p < 12; p++) agg.push(p);
	BY_CARD[12] = [{ pcs: agg, forte: "12-1" }];
}

// Dosia McKay's dissonance level, from the interval vector -- the same calculation FORTESEQ2
// uses (forteseq2.js: IC_DISSONANCE_MCKAY / dissonanceOf / dissonancePercent). Each interval
// class is weighted by the inverse of how often it occurs in the diatonic scale (P4 x6,
// M2 x5, m3 x4, M3 x3, m2 x2, TT x1 -> weights 1/6, 1/5, 1/4, 1/3, 1/2, 1). The level is the
// RAW weighted sum (not normalised by pair count -- so a bigger set scores higher), then
// shown as a percentage of the twelve-tone set's own level (23.4, the max any set reaches).
// Verified against the book: major triad 3-11B -> 0.75 -> 3.21%, diatonic 7-35 -> 6 -> 25.64%.
var IC_DISSONANCE_MCKAY = [1 / 2, 1 / 5, 1 / 4, 1 / 3, 1 / 6, 1];   // ic1..ic6
var MCKAY_CHROMATIC = 23.4;
function dissonanceOf(iv) {
	var t = 0;
	for (var k = 0; k < 6; k++) t += IC_DISSONANCE_MCKAY[k] * iv[k];
	return t;
}
function dissonancePercent(iv) { return dissonanceOf(iv) / MCKAY_CHROMATIC * 100; }
function disoLabel(pct) {
	return pct < 4 ? "muy consonante" : pct < 10 ? "consonante"
	     : pct < 20 ? "medio" : pct < 40 ? "disonante" : "muy disonante";
}

// DissSort (toggle): order the walk by dissonance (1 = least, N = most). StudyTrav (menu):
// restrict the walk to set classes with a chosen invariance. They compose -- filter the
// list, then optionally sort that subset by dissonanceOf ascending (FORTESEQ2's ORDER_DISS).
var DISO_SORT = 0;
function disssort(v) { DISO_SORT = v ? 1 : 0; }

// StudyMove (menu): what StudyTonic does. 0 "Transpone" = slide the whole figure round the
// chromatic circle (the original behaviour). 1 "Rota raiz" = `list` stays the prime necklace
// at pc 0; the chromatic Tonnetz + circles rotate names/colours so the root shows where C
// sits, while piano/guitar shift the lit notes and keep showing real pitches. `rot` still
// reshapes; `inv` still flips.
var STUDY_MOVE = 0;
function studymove(v) { STUDY_MOVE = v ? 1 : 0; }

var STUDY_FILTER = 0;     // 0 todos | 1 simetricos | 2 inv. de quintas | 3 espejo de quintas
var FILTER_LABEL = ["todos", "simetricos", "inv.5tas", "espejo5tas"];
var FILTER_TAG   = ["", "  simetricos", "  inv.5tas", "  espejo5tas"];
var FILT_ORDER = {};      // key = card*4 + filter -> array of catalog indices, catalog order
function studytrav(v) { STUDY_FILTER = Math.max(0, Math.min(3, Math.round(v))); }
function filterList(card, f) {
	var key = card * 4 + f;
	if (FILT_ORDER[key]) return FILT_ORDER[key];
	var lst = BY_CARD[card] || [], out = [];
	for (var i = 0; i < lst.length; i++) {
		var p = lst[i].pcs;
		if (f === 0 || (f === 1 && isInvSym(p)) || (f === 2 && isFifthSame(p)) || (f === 3 && isFifthMirror(p)))
			out.push(i);
	}
	FILT_ORDER[key] = out;
	return out;
}

function studyset(card, idx1, rot, tonic, inv) {
	if (!BY_CARD) buildByCard();
	card = Math.max(1, Math.min(12, Math.round(card)));
	var lst = BY_CARD[card] || [];
	if (!lst.length) return;
	var order = filterList(card, STUDY_FILTER).slice();
	if (DISO_SORT) order.sort(function (a, b) {
		var da = dissonanceOf(intervalVector(lst[a].pcs)), db = dissonanceOf(intervalVector(lst[b].pcs));
		return da !== db ? da - db : a - b;
	});
	var total = order.length;
	if (!total) {
		studyTag = "(sin sets: " + FILTER_LABEL[STUDY_FILTER] + ", card " + card + ")";
		studyRoot = -1;
		spellRot = 0;
		outlet(0, "info", "estudio " + studyTag);
		outlet(0, "setclass", "");
		outlet(0, "studyroot", -1);
		outlet(0, "studyspell", 0);
		return;
	}
	var pos = Math.max(0, Math.min(total - 1, Math.round(idx1) - 1));
	var idx = order[pos];
	studyTag = lst[idx].forte + (inv ? "*" : "") + "  " + (pos + 1) + "/" + total
		+ FILTER_TAG[STUDY_FILTER] + (DISO_SORT ? "  x diso" : "");
	var base = lst[idx].pcs.slice();
	if (inv) base = normal0(invert(base));
	var n = base.length;
	var t = Math.round(tonic);
	var r = (((Math.round(rot) % n) + n) % n);
	var rel = [];                            // interval necklace rotated to start on member r
	for (var i = 0; i < n; i++) rel.push(mod12(base[(i + r) % n] - base[r]));
	var outPcs = [];
	if (STUDY_MOVE) {
		// Rota raiz: `list` stays the prime necklace anchored at 0. spellRot tells the jsui
		// how far to rotate names/colours on the chromatic Tonnetz + circles (shape looks
		// pinned there); the fixed surfaces (piano/guitar) instead shift the lit notes by
		// spellRot so they still show the real transposed pitches.
		for (var j = 0; j < n; j++) outPcs.push(rel[j]);
		spellRot = mod12(t);
		studyRoot = spellRot;              // the real root pc
		studyTag += "  raiz " + NOTE_NAMES[spellRot] + " (forma fija)";
	} else {                                // Transpone: slide the whole figure to the tonic
		var tn = mod12(t);
		for (var k = 0; k < n; k++) outPcs.push(mod12(rel[k] + tn));
		spellRot = 0;
		studyRoot = tn;                     // rel[0] is 0, so the anchored note is the tonic
	}
	explicit = uniqSorted(outPcs);
	outlet(0, ["list"].concat(explicit));   // -> jsui activeSet
	outlet(0, "studyspell", spellRot);      // -> jsui label/colour rotation (Rota raiz)
	emit();                                  // -> jsui footer (info / setclass) + studyroot
}

// inline 351 Tn-class index (same canonical rotation-min as pcset351.js buildSets)
var TN_CANON = null;
function buildTnCanon() {
	function pop(x) { var c = 0; while (x) { c += x & 1; x >>= 1; } return c; }
	function rot(x) { return ((x << 1) | (x >> 11)) & 0xFFF; }
	var seen = {}, canon = [];
	for (var n = 1; n < 4096; n++) {
		var best = n, cur = n;
		for (var r = 0; r < 11; r++) { cur = rot(cur); if (cur < best) best = cur; }
		if (!seen[best]) { seen[best] = true; canon.push(best); }
	}
	canon.sort(function (a, b) { var ca = pop(a), cb = pop(b); return ca !== cb ? ca - cb : a - b; });
	TN_CANON = {};
	for (var i = 0; i < canon.length; i++) TN_CANON[canon[i]] = i + 1;
}
function tnIndex(pcs) {
	if (!TN_CANON) buildTnCanon();
	var s = uniqSorted(pcs);
	if (!s.length) return 0;
	var m = 0; for (var i = 0; i < s.length; i++) m |= (1 << s[i]);
	var best = m, cur = m;
	for (var r = 0; r < 11; r++) { cur = ((cur << 1) | (cur >> 11)) & 0xFFF; if (cur < best) best = cur; }
	return TN_CANON[best] || 0;
}

function emit() {
	var pcs = activePcs();
	var card = pcs.length;

	if (card === 0) {
		outlet(0, "info", "-");
		outlet(0, "setclass", "");
		outlet(0, "chord", "");
		outlet(0, "studyroot", -1);
		outlet(0, "studyspell", 0);
		outlet(1, ["card", 0]);
		return;
	}

	// pcs spelled the way the panels draw them (Rota raiz rotates every name by spellRot)
	var npcs = [];
	for (var i = 0; i < pcs.length; i++) npcs.push(mod12(pcs[i] + spellRot));
	var names = [];
	for (i = 0; i < npcs.length; i++) names.push(NOTE_NAMES[npcs[i]]);

	var chordInfo = nameChord(npcs, spellRot ? -1 : bassMidi());
	var fsp = fifthSpan(pcs);
	var iv = intervalVector(pcs);
	var prime = primeForm(pcs);
	var forte = forteName(pcs);
	var nm = forte && NAMES[forte] ? NAMES[forte] : "";
	var modal = modalityName(pcs);   // McKay modality (FORTESEQ2's MODALITY_TABLE)
	var tn = tnIndex(pcs);

	var dpct = card >= 2 ? dissonancePercent(iv) : 0;
	var sym = isInvSym(pcs), q5 = isFifthSame(pcs), q5e = isFifthMirror(pcs);
	var invTags = [];
	if (sym) invTags.push("sim");
	if (q5) invTags.push("q5");
	if (q5e) invTags.push("q5esp");

	var line = (studyTag ? "estudio " + studyTag + "  |  " : "")
		+ (chordInfo.full ? chordInfo.full + "  |  " : "")
		+ card + (card === 1 ? " nota" : " notas") + "  " + names.join(" ");
	if (forte) line += "  |  " + forte;
	line += "  |  IV " + ivString(iv);
	line += "  |  [" + prime.join(" ") + "]";
	if (nm) line += "  |  " + nm;
	if (modal) line += "  |  mod " + modal;
	if (card >= 2) line += "  |  diso " + dpct.toFixed(1) + "% (" + disoLabel(dpct) + ")";
	if (card >= 2) line += "  |  q5span " + fsp;
	if (card >= 2 && invTags.length) line += "  |  " + invTags.join(" ");
	if (tn) line += "  |  Tn " + tn + "/351";

	outlet(0, "info", line);
	outlet(0, "setclass", prime.join(" "));
	outlet(0, "chord", chordInfo.full || "-");
	if (!studyTag) {
		var kg = detectKey(keyHistogram());
		outlet(0, "keyguess", kg.root, kg.minor, Math.round(kg.conf * 100) / 100);
		outlet(1, ["keyguess", kg.root, kg.minor, Math.round(kg.conf * 100) / 100]);
	}
	outlet(0, "studyroot", studyTag ? studyRoot : -1);

	outlet(1, ["card", card]);
	outlet(1, ["notes"].concat(names));
	outlet(1, ["chord", chordInfo.sym || "-"]);
	if (chordInfo.alts.length) outlet(1, ["chords"].concat(chordInfo.alts));
	outlet(1, ["forte", forte || "-"]);
	outlet(1, ["iv"].concat(iv));
	outlet(1, ["prime"].concat(prime));
	outlet(1, ["name", nm || "-"]);
	outlet(1, ["modality", modal || "-"]);               // McKay modality name
	outlet(1, ["diso", Math.round(dpct * 100) / 100]);   // McKay dissonance, % of chromatic
	outlet(1, ["q5span", fsp]);                          // occupied arc on the circle of fifths
	outlet(1, ["inv", sym ? 1 : 0, q5 ? 1 : 0, q5e ? 1 : 0]);   // symmetric | fifth-same | fifth-mirror
	outlet(1, ["tn", tn, 351]);
}

function loadbang() { emit(); }
