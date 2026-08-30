// tonnetzfit.js -- "which generalized Tonnetz represents this music most compactly?"
// A decoupled analyser for the Tonnetz device, kept apart from the visual jsui (same idea
// as pcsetinfo.js) so it never touches the MIDI stream. Fed the same note feed.
//
// Bigo et al. CMJ 2015, p.20 ("compliance"): HexaChord picks the chord complex whose
// trajectory for a piece is the most compact, and treats that as a stylistic signature.
// This is a lightweight local proxy: over a rolling window of the last K pitch-class sets,
// for each candidate interval vector [a,b,c] count the pairs of notes in each set that are
// NOT a single lattice step apart in K[a,b,c]. Fewer non-adjacent pairs = the chords sit as
// tighter shapes in that lattice = more compact. The argmin is emitted as `bestfit`.
//
//   inlet 0:
//     note <pitch> <vel>   MIDI note, ref-counted; vel 0 = off  (a new pc-set pushes a window slot)
//     list <pc> ...        set the active pitch-class set outright
//     clear                empty the window
//     bang                 re-emit
//     window <n>           rolling-window size (2..32, default 8)
//
//   outlet 0 -> tonnetz.js : `bestfit <a> <b> <c>`   (lowest-penalty candidate)
//   outlet 1 -> future display : `fit <a> <b> <c> <penalty>` one per candidate, then `fitwin <n>`

autowatch = 1;
inlets = 1;
outlets = 2;

// candidate complexes -- must line up with PRESETS[] in tonnetz.js
var CAND = [
	[3, 4, 5], [1, 1, 10], [2, 2, 8], [1, 4, 7], [2, 3, 7],
	[1, 2, 9], [3, 3, 6], [4, 4, 4], [1, 5, 6], [2, 5, 5]
];

var voices = [];
for (var _i = 0; _i < 12; _i++) voices[_i] = 0;
var explicit = null;
var win = [];          // rolling list of pc-set strings' arrays
var winMax = 8;

function mod12(n) { return ((n % 12) + 12) % 12; }

function activePcs() {
	if (explicit) return explicit.slice();
	var a = [];
	for (var pc = 0; pc < 12; pc++) if (voices[pc] > 0) a.push(pc);
	return a;
}

function pushWindow(set) {
	if (set.length === 0) return;
	var key = set.join(",");
	if (win.length && win[win.length - 1].join(",") === key) return;
	win.push(set.slice());
	while (win.length > winMax) win.shift();
}

// pairs of pcs in `set` that are not one lattice step apart in K[a,b,c]
function nonAdjPairs(set, a, b) {
	var ax = mod12(a), ay = mod12(a + b);
	var steps = [ax, mod12(-ax), ay, mod12(-ay), mod12(ay - ax), mod12(ax - ay)];
	var pen = 0;
	for (var i = 0; i < set.length; i++)
		for (var j = i + 1; j < set.length; j++) {
			var d = mod12(set[j] - set[i]);
			if (steps.indexOf(d) < 0) pen++;
		}
	return pen;
}

function note(pitch, vel) {
	explicit = null;
	var pc = mod12(Math.round(pitch));
	if (vel > 0) voices[pc]++;
	else if (voices[pc] > 0) voices[pc]--;
	pushWindow(activePcs());
	emit();
}
function list() {
	explicit = [];
	var raw = arrayfromargs(arguments);
	for (var i = 0; i < raw.length; i++) {
		var pc = mod12(Math.round(raw[i]));
		if (explicit.indexOf(pc) < 0) explicit.push(pc);
	}
	explicit.sort(function (x, y) { return x - y; });
	pushWindow(explicit);
	emit();
}
function clear() {
	for (var i = 0; i < 12; i++) voices[i] = 0;
	explicit = null;
	win = [];
	emit();
}
function bang() { emit(); }
function winsize(n) {
	winMax = Math.max(2, Math.min(32, Math.round(n)));
	while (win.length > winMax) win.shift();
	emit();
}

function emit() {
	if (win.length === 0) {
		outlet(0, "bestfit", CAND[0][0], CAND[0][1], CAND[0][2]);
		return;
	}
	var best = 0, bestPen = 1e18;
	for (var c = 0; c < CAND.length; c++) {
		var pen = 0;
		for (var w = 0; w < win.length; w++) pen += nonAdjPairs(win[w], CAND[c][0], CAND[c][1]);
		outlet(1, ["fit", CAND[c][0], CAND[c][1], CAND[c][2], pen]);
		if (pen < bestPen) { bestPen = pen; best = c; }
	}
	outlet(1, ["fitwin", win.length]);
	outlet(0, "bestfit", CAND[best][0], CAND[best][1], CAND[best][2]);
}

function loadbang() { emit(); }
