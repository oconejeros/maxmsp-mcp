autowatch = 1;
inlets = 1;
outlets = 10;  // 0 = voice1 MIDI, 1 = current set index (1-351), 2 = notes for display (names),
               // 3 = voice2 MIDI, 4 = voice3 MIDI, 5 = voice4 MIDI, 6 = all-voice summary for viz,
               // 7 = preset recall broadcast (tagged pairs, routed in Max), 8 = voice note names for monitor,
               // 9 = current set's pitch classes (0-11, transposed by root) for circle-of-fifths display

var currentBpm = 120;   // tracked purely for presets; actual timing is handled in Max via expr_ms
var presets = {};        // in-memory preset store: slot -> captured state object

var NUM_VOICES = 4;
var VOICE_OUTLETS = [0, 3, 4, 5];
var voiceOctaveList = [[0], [0], [0], [0]];   // per-voice octave PATTERN (list); a single-value list = old fixed-octave behavior
var voiceMute = [0, 1, 1, 1];     // voice 1 active by default; voices 2-4 muted until enabled
var voicePos = [0, 0, 0, 0];      // independent per-voice cursor into the CURRENT chord's pitch classes, advanced only by triggervoice()
var voiceExternal = [0, 0, 0, 0]; // 1 = this voice is skipped by the shared clock and only sounds via triggervoice()
var voiceRangeMin = [0, 0, 0, 0];      // per-voice register clamp, low bound (MIDI note); default 0-127 = no effective clamp
var voiceRangeMax = [127, 127, 127, 127];  // per-voice register clamp, high bound (MIDI note)
var root = 0;                      // semitone transpose applied to everything (tonic/root shift)
var masterOctave = 0;               // global octave transpose applied to everything, on top of per-voice octave and root
var patternStep = 0;               // increments once per step() call, in every mode; drives octave-list position

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
	post("pcset351: built " + sets.length + " Tn-classes\n");
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
	// NOTE: deliberately NOT calling emitVoices() here - that sends real notes out
	// VOICE_OUTLETS and made picking a set in the numbox audibly fire a stray note.
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

// Simple generator: every "everyN" notes, step one octave toward "range"; wraps back to 0 after.
// e.g. everyN=4, range=2  -> [0,0,0,0, 1,1,1,1, 2,2,2,2] (then repeats).
// e.g. everyN=4, range=-2 -> [0,0,0,0, -1,-1,-1,-1, -2,-2,-2,-2] (then repeats).
function setvoiceoctavesimple(v, everyN, range, steps) {
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

	var list = [];
	var lastLevel = null;
	for (var i = 0; i <= steps; i++) {
		var level = Math.round(i * range / steps);
		if (level === lastLevel) continue; // collapse steps finer than the integer octave grid
		lastLevel = level;
		for (var j = 0; j < everyN; j++) list.push(level);
	}
	voiceOctaveList[idx] = list;
	post("voice " + v + " octave pattern: every " + everyN + " notes, range " + range + ", steps " + steps + " -> [" + list.join(",") + "]\n");
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
	var pc = pcs[pos % pcs.length];
	var list = voiceOctaveList[idx];
	var oct = list[pos % list.length];
	var shift = oct * 12 + root + masterOctave * 12;
	var vmin = voiceRangeMin[idx], vmax = voiceRangeMax[idx];
	var shifted = foldToRange(MELODY_BASE + pc + shift, vmin, vmax);

	voicePos[idx] = pos + 1;
	outlet(VOICE_OUTLETS[idx], shifted);
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
	voiceOctaveList = p.voiceOctaveList.map(function (l) { return l.slice(); });
	voiceMute = p.voiceMute.slice();
	voiceExternal = p.voiceExternal ? p.voiceExternal.slice() : [0, 0, 0, 0];
	voiceRangeMin = p.voiceRangeMin ? p.voiceRangeMin.slice() : [0, 0, 0, 0];
	voiceRangeMax = p.voiceRangeMax ? p.voiceRangeMax.slice() : [127, 127, 127, 127];

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

	outlet(7, ["masteroct", masterOctave]);
	outlet(7, ["mode", mode]);
	outlet(7, ["shape", rotShape]);
	outlet(7, ["permmode", permMode]);
	outlet(7, ["locked", locked]);
	outlet(7, ["lockindex", lockIndex + 1]);
	outlet(7, ["root", root]);
	outlet(7, ["bpm", currentBpm]);
	for (var v = 0; v < NUM_VOICES; v++) {
		outlet(7, ["v" + (v + 1) + "octlist"].concat(voiceOctaveList[v]));
		outlet(7, ["v" + (v + 1) + "mute", voiceMute[v]]);
		outlet(7, ["v" + (v + 1) + "external", voiceExternal[v]]);
		outlet(7, ["v" + (v + 1) + "range", voiceRangeMin[v], voiceRangeMax[v] - voiceRangeMin[v]]);
	}
	post("preset: recalled slot " + slot + "\n");
}

function noteName(midi) {
	var m = Math.round(midi);
	var pc = ((m % 12) + 12) % 12;
	var octave = Math.floor(m / 12) - 1;   // MIDI 60 = C4
	return NOTE_NAMES[pc] + octave;
}

function emitVoices(noteData) {
	var summary = [];
	var names = [];
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
		summary.push(repr);
		names.push(noteName(repr));
		outlet(VOICE_OUTLETS[v], shifted);
	}
	outlet(6, summary);
	outlet(8, ["V1:" + names[0], "V2:" + names[1], "V3:" + names[2], "V4:" + names[3]]);
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
	outlet(9, pcs.map(function(p) { return ((p + root) % 12 + 12) % 12; }));

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

function bang() {
	step();
}
