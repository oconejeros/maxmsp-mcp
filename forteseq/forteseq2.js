autowatch = 1;
inlets = 1;
outlets = 7;   // 0 = note events (see emitNote), 1 = current set index (1-351),
               // 2 = notes for display (names), 3 = all-voice summary for viz,
               // 4 = preset recall broadcast (tagged pairs, routed in Max),
               // 5 = voice note names for monitor,
               // 6 = current set's pitch classes (0-11, transposed by root) for circle-of-fifths.
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
var permMode = 0;      // 0 = normal rotation, 1 = superpermutation (brute force), 2 = superpermutation (minimal, n<=5)
var locked = 0;        // 0 = advance through all 351, 1 = stay on lockIndex and only permute
var lockIndex = 0;     // which set (0-based) to freeze on when locked
var setIndex = 0;      // which of the 351 Tn-classes we're on
var noteIndex = 0;     // position within current set's arpeggio (arpeggio mode)
var rotation = 0;      // round-robin rotation offset for arpeggio starting note (normal mode)

var PERM_CAP = 6;          // max cardinality for full superpermutation cycling (6! = 720)
var permList = [];         // cached permutations of the current set (brute-force superpermutation mode)
var permCachedFor = -1;    // which setIndex permList was built for
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

buildSets();

function loadbang() {
	post("forteseq2: built " + sets.length + " Tn-classes, bus " + busId +
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
	outlet(1, setIndex + 1);
	outlet(2, displayNotes(sets[setIndex]));
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
	// trigger, so only permMode is meaningful here. Same cardinality limits as step():
	// minimal superpermutations exist for n<=5, brute force up to PERM_CAP, else linear.
	if (permMode === 2 && MINIMAL_SUPERPERMS[n]) {
		var minSeq = MINIMAL_SUPERPERMS[n];
		pc = pcs[minSeq[pos % minSeq.length]];
	} else if ((permMode === 1 || permMode === 2) && n <= PERM_CAP) {
		if (permCachedFor !== setIndex) {
			permList = heapPermutations(pcs);
			permCachedFor = setIndex;
		}
		// each voice advances through the permutation list at its own pace
		pc = permList[Math.floor(pos / n) % permList.length][pos % n];
	} else {
		pc = pcs[pos % n];
	}

	var list = voiceOctaveList[idx];
	var oct = list[pos % list.length];
	var shift = oct * 12 + root + masterOctave * 12;
	var vmin = voiceRangeMin[idx], vmax = voiceRangeMax[idx];
	var shifted = foldToRange(MELODY_BASE + pc + shift, vmin, vmax);

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

function setroot(r) {
	root = Math.round(r);
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
		permMode: permMode,
		locked: locked,
		lockIndex: lockIndex,
		root: root,
		masterOctave: masterOctave,
		bpm: currentBpm,
		voiceOctaveList: voiceOctaveList.map(function (l) { return l.slice(); }),
		voiceMute: voiceMute.slice(),
		voiceExternal: voiceExternal.slice(),
		voiceRangeMin: voiceRangeMin.slice(),
		voiceRangeMax: voiceRangeMax.slice(),
		accentGrid: accentGrid.slice(),
		accentCycle: accentCycle,
		accentTieToN: accentTieToN,
		voicePhase: voicePhase.slice(),
		groupVelMin: groupVelMin.slice(),
		groupVelMax: groupVelMax.slice(),
		groupDurDiv: groupDurDiv.slice(),
		groupSilence: groupSilence.slice(),
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
	permMode = p.permMode;
	locked = p.locked;
	lockIndex = p.lockIndex;
	root = p.root;
	masterOctave = p.masterOctave || 0;
	currentBpm = p.bpm;
	voiceOctaveList = padVoices(p.voiceOctaveList, null).map(
		function (l) { return l ? l.slice() : [0]; });
	voiceMute = padVoices(p.voiceMute, 1);
	voiceExternal = padVoices(p.voiceExternal, 0);
	voiceRangeMin = padVoices(p.voiceRangeMin, 0);
	voiceRangeMax = padVoices(p.voiceRangeMax, 127);

	// Presets stored before the articulation engine existed have none of these fields; fall
	// back to the module defaults so an old slot recalls as the plain fixed-velocity device
	// it was saved as, instead of throwing.
	accentGrid = p.accentGrid ? p.accentGrid.slice() : [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
	accentCycle = p.accentCycle || 4;
	accentTieToN = p.accentTieToN || 0;
	voicePhase = padVoices(p.voicePhase, 0);
	groupVelMin = p.groupVelMin ? p.groupVelMin.slice() : [55, 95];
	groupVelMax = p.groupVelMax ? p.groupVelMax.slice() : [80, 115];
	groupDurDiv = p.groupDurDiv ? p.groupDurDiv.slice() : [16, 4];
	groupSilence = p.groupSilence ? p.groupSilence.slice() : [0, 0];

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
	permList = heapPermutations(restoredPcs);
	permCachedFor = setIndex;
	minimalCachedFor = setIndex;

	outlet(4, ["masteroct", masterOctave]);
	outlet(4, ["mode", mode]);
	outlet(4, ["shape", rotShape]);
	outlet(4, ["permmode", permMode]);
	outlet(4, ["locked", locked]);
	outlet(4, ["lockindex", lockIndex + 1]);
	outlet(4, ["root", root]);
	outlet(4, ["bpm", currentBpm]);
	outlet(4, ["accentcycle", accentCycle]);
	outlet(4, ["accenttie", accentTieToN]);
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
	}
	post("preset: recalled slot " + slot + "\n");
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
		var shift = oct * 12 + root + masterOctave * 12;
		var shifted;
		var repr;
		var vmin = voiceRangeMin[v], vmax = voiceRangeMax[v];
		if (noteData instanceof Array) {
			shifted = [];
			for (var i = 0; i < noteData.length; i++) shifted.push(foldToRange(noteData[i] + shift, vmin, vmax));
			repr = shifted[0];
		} else {
			shifted = foldToRange(noteData + shift, vmin, vmax);
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

function expandChord(pcs) {
	var n = pcs.length;
	var notes = [];
	for (var i = 0; i < n; i++) {
		var octaves = (n > 1) ? Math.floor(i * CHORD_SPAN_OCT / n) : 0;
		notes.push(CHORD_BASE + pcs[i] + octaves * 12);
	}
	return notes;
}

function displayNotes(pcs) {
	var names = [];
	for (var i = 0; i < pcs.length; i++) names.push(noteName(MELODY_BASE + pcs[i] + root + masterOctave * 12));
	return names;
}

function heapPermutations(arr) {
	var result = [];
	var a = arr.slice();
	var n = a.length;
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

function step() {
	patternStep++;
	if (locked) setIndex = lockIndex;
	if (setIndex >= sets.length) setIndex = 0;
	var pcs = sets[setIndex];
	var n = pcs.length;
	if (DEBUG_STEP) {
		post("STEP " + patternStep + " | set=" + (setIndex + 1) + " n=" + n +
			" | locked=" + locked + " mode=" + mode + " perm=" + permMode +
			" | noteIdx=" + noteIndex + " permIdx=" + permIndex + " minPos=" + minimalPos + "\n");
	}
	outlet(6, pcs.map(function(p) { return ((p + root) % 12 + 12) % 12; }));

	if (mode === 1 && permMode === 2 && MINIMAL_SUPERPERMS[n]) {
		var minSeq = MINIMAL_SUPERPERMS[n];
		if (minimalCachedFor !== setIndex) {
			minimalCachedFor = setIndex;
			minimalPos = 0;
		}

		outlet(1, setIndex + 1);
		outlet(2, displayNotes(pcs));
		emitVoices(MELODY_BASE + pcs[minSeq[minimalPos]]);

		minimalPos++;
		if (minimalPos >= minSeq.length) {
			minimalPos = 0;
			if (!locked) {
				setIndex++;
				if (setIndex >= sets.length) setIndex = 0;
				minimalCachedFor = -1;
			}
		}
		return;
	}

	if (mode === 1 && (permMode === 1 || permMode === 2) && n <= PERM_CAP) {
		if (permCachedFor !== setIndex) {
			permList = heapPermutations(pcs);
			permCachedFor = setIndex;
			permIndex = 0;
			noteIndex = 0;
		}
		var curPerm = permList[permIndex];

		outlet(1, setIndex + 1);
		outlet(2, displayNotes(curPerm));
		emitVoices(MELODY_BASE + curPerm[noteIndex]);

		noteIndex++;
		if (noteIndex >= n) {
			noteIndex = 0;
			permIndex++;
			if (permIndex >= permList.length) {
				permIndex = 0;
				if (!locked) {
					setIndex++;
					if (setIndex >= sets.length) setIndex = 0;
					permCachedFor = -1;   // force rebuild for the new set next step
				}
			}
		}
		return;
	}

	outlet(1, setIndex + 1);
	outlet(2, displayNotes(pcs));

	if (mode === 0) {
		emitVoices(expandChord(pcs));
		if (!locked) {
			setIndex = (setIndex + 1) % sets.length;
		}
	} else {
		var playPos = (noteIndex + rotation) % n;
		emitVoices(MELODY_BASE + pcs[playPos]);
		noteIndex++;
		if (noteIndex >= n) {
			noteIndex = 0;
			if (locked) {
				rotation = (rotation + 1) % n;   // only one set in the loop, so always rotate per cycle
			} else {
				if (rotShape === 1) {
					rotation = (rotation + 1) % n;
				}
				setIndex++;
				if (setIndex >= sets.length) {
					setIndex = 0;
					if (rotShape === 0) {
						rotation++;
					}
				}
			}
		}
	}
}

function setshape(s) {
	rotShape = s ? 1 : 0;
}

function setpermmode(p) {
	permMode = Math.round(p);
	if (permMode < 0) permMode = 0;
	if (permMode > 2) permMode = 2;
	noteIndex = 0;
	permIndex = 0;
	permCachedFor = -1;
	minimalPos = 0;
	minimalCachedFor = -1;
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

function bang() {
	step();
}
