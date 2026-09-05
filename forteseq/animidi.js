// animidi.js -- jsui for the standalone ANIMIDI M4L device. A scrolling bar-graph score in
// the manner of Stephen Malinowski's Music Animation Machine (musanim.com): time runs
// horizontally past a fixed "now" line, y = pitch, a note is a horizontal bar as long as it
// sounds, bars brighten while held, and colour encodes pitch class (the same circle-of-
// fifths hue wheel tonnetz.js / circleoffifths.js use). NONE of Malinowski's software is
// reused, only the visual idea.
//
// Drawn in the same idiom as forteseq/tonnetz.js (mgraphics, no ES6). Unlike tonnetz.js --
// which is state-only and redraws on each note on/off -- this file runs a free-running Task
// that redraws ~30 fps so the picture scrolls even when no MIDI is arriving, and keeps a
// timestamped event buffer instead of ref-counted pitch-class voices.
//
// Two time models, behind the TimeMode tab:
//   0 "Tiempo real"  notes appear AT the now-line and scroll left. Wall-clock driven
//                    (Date.getTime()), gated by the Live transport (frozen while stopped),
//                    but always running when loaded outside Live so a plain test patch
//                    still scrolls. Scale is px per second.
//   1 "Lookahead"    the whole clip is on screen: notes sit to the RIGHT of the now-line
//                    and travel toward it, brightening as they cross. A free-running
//                    PREVIEW: driven by the same wall clock as Tiempo real (lookaheadBeats,
//                    scaled by the Live tempo), looping over the clip's own note span -- it
//                    does NOT chase Live's bar position (that re-cues / loops short and
//                    jumped the picture). The clip's notes are read once via the Live API
//                    (Clip.get_notes_extended, whole clip); ReadClip / transport-start re-read.
//
// Fed by the device patch:
//   notein -> pack 0 0 0 -> prepend note   -> here      (pitch vel chan; vel 0 = note-off)
//   live.observer is_playing -> prepend transport       -> here
//   live.observer tempo      -> prepend tempo           -> here
//   live.observer current_song_time -> prepend songpos  -> here   (beats)
//   control strip -> prepend <sel> -> here
//
// Messages:
//   note <pitch> <vel> <chan>   MIDI note; vel 0 = note-off.
//   transport <0|1>             Live transport play state (gates the real-time clock).
//   tempo <bpm>                 Live tempo (lookahead: px-per-beat = pxPerSec*60/bpm).
//   songpos <beats>             Live song position in beats (stored only; not used to scroll).
//   timemode <0|1>              0 real-time trailing | 1 clip lookahead.
//   pxpersec <f>                horizontal scale, px per second (20..400).
//   colormode <0..4>            0 pitch-class wheel | 1 per-MIDI-channel | 2 fixed accent |
//                               3 acorde mezclado (OKLab blend of the held+AnWin chord) | 4
//                               disonancia (McKay % of that same chord, bucketed into threshold
//                               bands). Both 3 and 4 use the AnWin window (see `anwin` below),
//                               same idea as tonnetz/pcsetinfo, so a melodic line reads as one
//                               aggregated chord instead of whatever single note is held right now.
//   rangemode <0|1>             y-axis: 0 auto-fit to the music | 1 fixed rangelo..rangehi.
//   rangelo / rangehi <0..127>  fixed y-axis bounds (used when rangemode == 1).
//   grid <0|1>                  octave lines + beat/bar lines.
//   piano <0|1>                 Barras: piano keyboard gutter down the left edge.
//   vellane <0|1>               Barras: velocity line-graph lane along the bottom.
//   harmlane <0|1>              Barras: harmony-colour spectrum lane along the bottom (a strip
//                               of contiguous colour blocks, the OKLab blend of whatever's
//                               sounding within AnWin -- same colour as tonnetz's "Col" panel,
//                               not the McKay dissonance band -- independent of ColorMode, like
//                               VelLane).
//   anwin <seconds>             analysis window shared by ColorMode 3/4 and HarmLane, 0..10
//                               (default 1.2): a pc counts toward the chord while held AND for
//                               this many seconds after its onset, so a melodic run reads as one
//                               chord instead of single notes (which are never dissonant alone).
//                               Same idea as tonnetz/pcsetinfo's AnWin; 0 = instantaneous
//                               (concurrent notes only). Set it to the same value as tonnetz's
//                               AnWin to get comparable colours from both devices on one track.
//   notetags <0|1>              Barras: note-name label on each sounding note at the now-line.
//   viewmode <0|1|2|3>          0 Barras | 1 Espiral | 2 Dodecaedro | 3 Práctica (falling
//                               MIDI roll onto a keyboard at the bottom; both time models).
//   fps <n>                     redraw rate, 15..60 (default 30).
//   spin <0..100>               Espiral / Dodecaedro rotation gain.
//   spinmode <0|1>              0 Pulso (rotation tracks the beat) | 1 Notas (each note-on
//                               kicks the spin, direction = melodic contour).
//   readclip                    (lookahead) re-read the current clip's notes via the Live API.
//   clear                       drop all events and the cached clip notes.
//   refresh                     force a window-follow re-check + redraw.

autowatch = 1;
inlets = 1;
outlets = 1;   // unused; kept so the jsui box has a matching outlet count

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var SELF = this;   // captured so helper functions can reach .patcher / .box reliably

// ---- palette -----------------------------------------------------------------------------
// Circle-of-fifths hue wheel (as in tonnetz.js / sidebrain.net/relative-keys): the hue
// advances one 30-deg step per fifth, so PC_COLOR[pc] = hue( baseHue + ((pc*7)%12)*30 ).
// baseHue is the hue GIVEN TO C (pc 0); the HueC control rotates the whole wheel with it
// (e.g. HueC = 220 -> C is blue and every other note keeps its relative offset). baseSat /
// baseLum (the Sat / Lum controls) scale the whole set. colormode 1 (per channel) and 2
// (fixed) ignore all three.
// hue/mix/dissonance math lives in pccolor.js (shared with tonnetz.js, invertedprism.js,
// multichord.js) so the wheel formula and the OKLab/threshold machinery are defined once.
include('pccolor.js');

var baseHue = 0;         // hue for C, degrees 0..359
var baseSat = 0.62;      // 0..1
var baseLum = 0.55;      // 0..1
var PC_COLOR = [];       // PC_COLOR[pc] = [r,g,b] in 0..1

function rebuildPalette() {
	for (var pc = 0; pc < 12; pc++) {
		var c = pcToColor(pc, { baseHue: baseHue, sat: baseSat, lum: baseLum });
		PC_COLOR[pc] = [c.r, c.g, c.b];
	}
}
rebuildPalette();

// per-voice palette -- a voice is a Live track index (or a MIDI channel outside Live).
// 24 well-separated hues, indexed voice % 24.  Used by colormode 1 and by VoiceMode.
var VOICE_N = 24;
var VOICE_COLOR = [];
for (var _v = 0; _v < VOICE_N; _v++) {
	var _vc = hslToRgb((_v * 137.5) % 360, 0.58, 0.56);   // golden-angle spread
	VOICE_COLOR[_v] = [_vc.r, _vc.g, _vc.b];
}

var BG        = [0.11, 0.11, 0.12, 1];
var FRAME     = [0.30, 0.30, 0.32, 1];
var GRID_OCT  = [0.24, 0.24, 0.27, 1];
var GRID_BEAT = [0.20, 0.20, 0.23, 1];
var GRID_BAR  = [0.34, 0.34, 0.38, 1];
var NOWLINE   = [0.92, 0.86, 0.42, 0.9];
var COL_ACCENT = [0.594, 0.72, 0.928, 1];   // colormode 2 (Fijo)
var COL_TEXT  = [0.68, 0.68, 0.72, 1];
var COL_TRACE = [0.72, 0.58, 0.16, 1];       // the fading melodic thread (Espiral / Dodecaedro)
var KEY_WHITE = [0.86, 0.86, 0.88, 1];       // piano gutter (Barras) + keyboard (Práctica)
var KEY_BLACK = [0.14, 0.14, 0.16, 1];
var PLAYED_SHADE = [0.55, 0.62, 0.85, 0.07]; // Lookahead: the "already swept" band left of now

var KEYBOARD_W = 46;    // left piano gutter width in Barras
var KB_H       = 66;    // bottom keyboard height in Práctica
var VEL_H      = 58;    // velocity lane height in Barras (when VelLane is on)
var HARM_H     = 34;    // harmony-colour spectrum lane height in Barras (when HarmLane is on)

var NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
function isBlackPc(pc) { return [1, 3, 6, 8, 10].indexOf(((pc % 12) + 12) % 12) >= 0; }
function noteLabel(p) { p = Math.round(p); return NOTE_NAMES[((p % 12) + 12) % 12] + (Math.floor(p / 12) - 1); }

// ---- state -----------------------------------------------------------------------------
var events = [];         // {pitch, vel, voice, tOn, tOff}  -- voice = Live track idx (or MIDI chan outside Live)
var held   = [];         // held[pitch] = index into events of that pitch's open note (or undefined)
for (var i = 0; i < 128; i++) held[i] = -1;

// this device's own Live track index, resolved once via the Live API (see resolveMyVoice).
// -1 = unknown / outside Live -> note() falls back to the incoming MIDI channel.
var myVoice = -1;

var timeMode  = 0;       // 0 real-time trailing | 1 clip lookahead
var pxPerSec  = 90;
var colorMode = 0;
var rangeMode = 0;       // 0 auto | 1 fixed
var rangeLo   = 36, rangeHi = 96;
var gridOn    = 1;
var fpsRate   = 30;
var pianoOn   = 1;       // Barras: show the piano keyboard gutter down the left edge
var velLane   = 0;       // Barras: show a velocity line-graph lane along the bottom
var harmLane  = 0;       // Barras: show the harmony-colour spectrum lane along the bottom
var anWinSec  = 1.2;     // harmlane analysis window, seconds (0 = instantaneous); see doc header
var currentChordCol = null;   // colorMode 3 cache: OKLab blend of the currently-held chord
var currentDissCol  = null;   // colorMode 4 cache: dissonance-band colour of the same chord
var NEUTRAL_COL = [0.42, 0.42, 0.42];   // colorMode 3/4 fallback when nothing is held
var noteTags  = 0;       // Barras: label sounding notes with their name at the now-line

// view selector + voice grouping + spiral/dodeca controls (phase 2 of the device)
var viewMode  = 0;       // 0 Barras | 1 Espiral | 2 Dodecaedro | 3 Práctica (falling roll -> keyboard)
var voiceMode = 0;       // 0 Off | 1 Figura (shape per voice) | 2 Carriles  (Barras only; colour is separate, see ColorMode)
var traceLen  = 16;      // onsetQ cap -- the melodic thread length for Espiral / Dodecaedro
var spinAmt   = 20;      // 0..100 rotation speed for Espiral / Dodecaedro (0 = static)
var ringGap   = 24;      // px between octave rings in Espiral
var onsetQ    = [];      // recent note-ONs: {pc, pitch, vel, voice, t}  -- fades oldest->newest

// spin: Pulso = rotation follows the beat (the original behaviour); Notas = a "special
// mode" where each note-on kicks an angular velocity that decays, and the kick direction
// follows the melodic contour (up = one way, down = the other). Spin is the gain on both.
var spinMode  = 0;       // 0 Pulso | 1 Notas
var spinPhase = 0;       // accumulated rotation in degrees (used when spinMode === 1)
var spinVel   = 0;       // current speed, deg per ~33 ms, decays toward 0
var lastOnsetPitch = -1; // previous note-on pitch, for the contour-following kick direction

// real-time clock: wall-clock ms that only advances while the transport plays. tOn / tOff
// are stamped against scrollMs. Until a `transport` message has ever arrived (plain test
// patch, or no observer wired) the clock free-runs so something is always visible.
var scrollMs        = 0;
var lastWall        = (new Date()).getTime();
var transportPlaying = 0;
var gotTransport    = 0;
var hasLiveApi      = (typeof LiveAPI !== "undefined");
function clockRunning() { return gotTransport ? transportPlaying : 1; }

// lookahead clock. Its OWN wall-clock accumulator (previewMs), separate from scrollMs so
// re-cueing it does not disturb Tiempo real. Advances whenever clockRunning() (same gate as
// Tiempo real) and snaps back to 0 on the transport's stop->play EDGE (see transport()), so
// stop + play returns the preview to the clip's start. It does NOT chase Live's bar
// position -- it free-runs the whole clip, looping over the note span via posInLoop.
// (Earlier attempts to derive run/stop or the position from the metro-banged [transport]
// stream twitched once per bar: that stream is bar-quantised here, not smooth beats.)
var songBeat        = 0;
var tempoBpm        = 120;
var previewMs       = 0;
function lookaheadBeats() { return (previewMs / 1000) * tempoBpm / 60; }
// current position in beats for whichever time model is active: the preview clock in
// Lookahead, the real-time (scrollMs) clock otherwise. Used for beat/bar grid lines and
// the Espiral "Pulso" spin.
function posBeatNow() {
	return (timeMode === 1) ? lookaheadBeats() : (scrollMs / 1000) * tempoBpm / 60;
}

// auto y-range, with hysteresis so it does not jitter every note
var autoLo = 48, autoHi = 84;

// cached clip notes for lookahead
var clipNotes   = [];   // {pitch, start, dur, vel}  -- times in beats within the clip
var clipLoopStart = 0, clipLoopEnd = 4;
var clipMsg = "";       // short status line

// ---- viewport ------------------------------------------------------------------------
// The subpatcher opens in PRESENTATION view (build_animidi.py: openinpresentation 1) so the
// popup stays locked/interactive even with the Max editor open. In presentation view
// box.rect IS the presentation rect, so the jsui can still be stretched to fill the whole
// floating window: a slow Task reads the window size and matches the box to it, reserving
// STRIP_H px at the top for the control strip. Falls back to the box's own rect until the
// window size is readable.
var STRIP_H = 96;   // control-strip height / jsui y -- must match build_animidi.py
var VP_PAD  = 8;
function windSize() {
	try {
		var s = SELF.patcher.wind.size;
		if (s && s[0] > 80 && s[1] > 80) return s;
	} catch (e) {}
	return null;
}
function viewportWH() {
	var s = windSize();
	if (s) return [Math.max(200, s[0] - VP_PAD * 2), Math.max(120, s[1] - STRIP_H - VP_PAD)];
	var b = box.rect;
	return [Math.max(200, b[2] - b[0]), Math.max(120, b[3] - b[1])];
}
function fitToWindow() {
	var s = windSize();
	if (!s) return;
	var r = [VP_PAD, STRIP_H, Math.round(s[0]) - VP_PAD, Math.round(s[1]) - VP_PAD];   // [l,t,r,b]
	try {
		var b = box.rect;
		if (!b || Math.round(b[0]) != r[0] || Math.round(b[1]) != r[1]
			|| Math.round(b[2]) != r[2] || Math.round(b[3]) != r[3]) {
			try { box.rect = r; } catch (e2) {}
			mgraphics.redraw();
		}
	} catch (e) {}
}
var _fit = new Task(fitToWindow, SELF);
_fit.interval = 300;
_fit.repeat();
function refresh() { resolveMyVoice(); fitToWindow(); mgraphics.redraw(); }

// ---- animation clock -----------------------------------------------------------------
// Driven BOTH by a JS Task and by a `bang` from a metro in the patch (bang() -> tick()),
// so the scroll keeps going even if one path is throttled. tick() advances the scroll
// clock from the wall-clock delta, so a dropped frame just makes the next step longer.
var _lastTickErr = "";
function tick() {
	try {
		var now = (new Date()).getTime();
		var dt = now - lastWall;
		lastWall = now;
		if (dt < 0) dt = 0; if (dt > 250) dt = 250;   // clamp after a stall / tab switch
		if (clockRunning()) { scrollMs += dt; previewMs += dt; }   // real-time + lookahead clocks
		if (spinMode === 1) {                           // note-driven rotation: decay + integrate
			var sk = dt / 33;
			spinVel *= Math.pow(0.93, sk);
			if (Math.abs(spinVel) < 0.0005) spinVel = 0;
			spinPhase += spinVel * sk;
		}
		pruneEvents();
		if (colorMode === 3 || colorMode === 4) recomputeChordColors();   // let the AnWin window age out on its own
		mgraphics.redraw();
	} catch (e) {
		if (String(e) !== _lastTickErr) { _lastTickErr = String(e); post("animidi tick error: " + e + "\n"); }
	}
}
function bang() { tick(); }
var _anim = new Task(tick, SELF);
_anim.interval = Math.round(1000 / fpsRate);
_anim.repeat();

// drop events that have fully scrolled off the left edge (real-time mode only; lookahead
// draws from clipNotes, not events)
function pruneEvents() {
	if (timeMode === 1) return;
	var wh = viewportWH();
	var spanMs = (wh[0] / pxPerSec) * 1000 + 2000;   // + margin
	var cut = scrollMs - spanMs;
	var k = 0;
	while (k < events.length && (events[k].tOff >= 0 && events[k].tOff < cut)) k++;
	if (k > 0) {
		events.splice(0, k);
		// held[] indices shifted -- rebuild
		for (var p = 0; p < 128; p++) held[p] = -1;
		for (var i = 0; i < events.length; i++) if (events[i].tOff < 0) held[events[i].pitch] = i;
	}
}

// AnWin onset log for heldPcs() -- same idea as pcsetinfo.js's anEvents/analysisPcs (which is
// what feeds tonnetz's swatches): a pc counts toward the chord for anWinSec seconds after its
// onset, not just while literally held, so a melodic line aggregates into one set instead of
// always reading as whatever single note is down right now. Timestamped in scrollMs (this
// device's own real-time clock) rather than Date.now() so it matches tOn/tOff already do.
var anEvents = [];   // { pc, t } note-on log, pruned by age
function pruneAnEvents() {
	if (anWinSec <= 0) { if (anEvents.length) anEvents = []; return; }
	var cut = scrollMs - anWinSec * 1000;
	var k = 0;
	while (k < anEvents.length && anEvents[k].t < cut) k++;
	if (k > 0) anEvents.splice(0, k);
}
// distinct pitch classes among the notes currently held PLUS any pc whose onset fell within
// the last anWinSec seconds -- the chord ColorMode 3/4 colour from. Order doesn't matter:
// dissonanceBand/harmonyToColor are set functions.
function heldPcs() {
	pruneAnEvents();
	var pcs = [], seen = {};
	for (var p = 0; p < 128; p++) {
		if (held[p] >= 0 && events[held[p]]) {
			var pc = p % 12;
			if (!seen[pc]) { seen[pc] = 1; pcs.push(pc); }
		}
	}
	for (var i = 0; i < anEvents.length; i++) {
		if (!seen[anEvents[i].pc]) { seen[anEvents[i].pc] = 1; pcs.push(anEvents[i].pc); }
	}
	return pcs;
}
// recomputes the colorMode 3 (acorde mezclado) / 4 (disonancia) caches from the held chord.
// Called whenever `held` changes so colorFor() stays a cheap lookup during painting.
function recomputeChordColors() {
	var pcs = heldPcs();
	if (!pcs.length) { currentChordCol = NEUTRAL_COL; currentDissCol = NEUTRAL_COL; return; }
	var blend = harmonyToColor(pcs, { baseHue: baseHue, sat: baseSat }, 'oklab');
	currentChordCol = [blend.r, blend.g, blend.b];
	var db = dissonanceBand(pcs);
	var bc = bandColor(db.band, db.nBands);
	currentDissCol = [bc.r, bc.g, bc.b];
}

// ---- message handlers ---------------------------------------------------------------
// shared: push a note on/off event tagged with a voice id (a Live track index, or a MIDI
// channel outside Live). vel 0 = note-off.
function pushNoteEvent(pitch, vel, voice) {
	var n = Math.round(pitch);
	if (n < 0 || n > 127) return;
	var vv = Math.max(0, Math.round(voice));
	if (vel > 0) {
		if (held[n] >= 0 && events[held[n]]) events[held[n]].tOff = scrollMs;   // retrigger: close the old one
		events.push({ pitch: n, vel: vel, voice: vv, tOn: scrollMs, tOff: -1 });
		held[n] = events.length - 1;
		pushOnset({ pc: n % 12, pitch: n, vel: vel, voice: vv, t: scrollMs });
		anEvents.push({ pc: n % 12, t: scrollMs });
		if (anEvents.length > 512) anEvents.shift();
		if (spinMode === 1 && spinAmt > 0) {           // kick the note-driven spin along the contour
			var dir = (lastOnsetPitch < 0 || n === lastOnsetPitch) ? 1 : (n > lastOnsetPitch ? 1 : -1);
			spinVel += dir * (spinAmt / 100) * 3.2 * (0.45 + vel / 127);
			if (spinVel > 14) spinVel = 14; else if (spinVel < -14) spinVel = -14;
		}
		lastOnsetPitch = n;
	} else {
		if (held[n] >= 0 && events[held[n]]) events[held[n]].tOff = scrollMs;
		held[n] = -1;
	}
	recomputeChordColors();
	mgraphics.redraw();
}
// this device's OWN track MIDI (notein -> pack 0 0 0 -> prepend note). Normally tagged with
// this device's Live track index (matches how Lookahead labels the same track). BUT if the
// incoming stream carries MORE THAN ONE MIDI channel (a multi-channel part merged onto one
// track), switch to per-channel voices so Tiempo real shows the parts in distinct colours
// like Lookahead does. (Multi-channel files that Live SPLIT into tracks all arrive on ch 1,
// so they stay on the track index; their other tracks still need an ANIMIDIFeed device.)
var _chanSeen = {}, _chanCount = 0, _multiChan = 0;
function note(pitch, vel, chan) {
	var c = (chan === undefined) ? 1 : Math.round(chan);
	if (vel > 0 && c >= 1 && !_chanSeen[c]) {
		_chanSeen[c] = 1; _chanCount++;
		if (_chanCount > 1) _multiChan = 1;
	}
	var v = _multiChan ? (c - 1) : ((myVoice >= 0) ? myVoice : (c - 1));
	pushNoteEvent(pitch, vel, v);
}
// a note forwarded from an ANIMIDIFeed device on another track (receive ANIMIDI_NOTE ->
// prepend busnote). Already carries that track's index.
function busnote(pitch, vel, trackIdx) { pushNoteEvent(pitch, vel, trackIdx); }
function msg_int(v)  { pushNoteEvent(v, 127, (myVoice >= 0 ? myVoice : 0)); }
function transport(v) {
	gotTransport = 1;
	var p = v ? 1 : 0;
	var edge = (p && !transportPlaying);   // stop -> play, ONLY (never a repeated is_playing 1)
	transportPlaying = p;
	if (edge && timeMode === 1) readclip();   // the (possibly slow) clip read on the play edge
	if (edge) previewMs = 0;                  // then re-cue the preview to the clip start
	lastWall = (new Date()).getTime();        // LAST: the next dt must not include readclip time
}
function tempo(v)   { if (v > 0) tempoBpm = v; }
function songpos(v) { if (v !== undefined && !isNaN(v)) songBeat = v; }   // stored only
function timemode(v) {
	timeMode = v ? 1 : 0;
	if (timeMode === 1) {
		if (hasLiveApi) readclip();
		previewMs = 0;
		lastWall = (new Date()).getTime();
	}
	mgraphics.redraw();
}
function pxpersec(v) { pxPerSec = Math.max(10, Math.min(600, v)); mgraphics.redraw(); }
function colormode(v) { colorMode = Math.max(0, Math.min(4, Math.round(v))); mgraphics.redraw(); }
function rangemode(v) { rangeMode = v ? 1 : 0; mgraphics.redraw(); }
function rangelo(v) { rangeLo = Math.max(0, Math.min(127, Math.round(v))); mgraphics.redraw(); }
function rangehi(v) { rangeHi = Math.max(0, Math.min(127, Math.round(v))); mgraphics.redraw(); }
function grid(v) { gridOn = v ? 1 : 0; mgraphics.redraw(); }
function piano(v) { pianoOn = v ? 1 : 0; mgraphics.redraw(); }
function vellane(v) { velLane = v ? 1 : 0; mgraphics.redraw(); }
function harmlane(v) { harmLane = v ? 1 : 0; mgraphics.redraw(); }
function anwin(v) { anWinSec = Math.max(0, Math.min(10, +v || 0)); mgraphics.redraw(); }
function notetags(v) { noteTags = v ? 1 : 0; mgraphics.redraw(); }
function viewmode(v) { viewMode = Math.max(0, Math.min(3, Math.round(v))); mgraphics.redraw(); }
function voicemode(v) { voiceMode = Math.max(0, Math.min(2, Math.round(v))); mgraphics.redraw(); }
function tracelen(v) {
	traceLen = Math.max(2, Math.min(64, Math.round(v)));
	while (onsetQ.length > traceLen) onsetQ.shift();
	mgraphics.redraw();
}
function spin(v) { spinAmt = Math.max(0, Math.min(100, v)); mgraphics.redraw(); }
function spinmode(v) { spinMode = v ? 1 : 0; spinVel = 0; mgraphics.redraw(); }
function ringgap(v) { ringGap = Math.max(8, Math.min(60, v)); mgraphics.redraw(); }
function pushOnset(o) { onsetQ.push(o); while (onsetQ.length > traceLen) onsetQ.shift(); }
function basehue(v) { baseHue = ((Math.round(v) % 360) + 360) % 360; rebuildPalette(); mgraphics.redraw(); }
function basesat(v) { baseSat = Math.max(0, Math.min(100, v)) / 100; rebuildPalette(); mgraphics.redraw(); }
function baselum(v) { baseLum = Math.max(0, Math.min(100, v)) / 100; rebuildPalette(); mgraphics.redraw(); }
function fps(v) {
	fpsRate = Math.max(15, Math.min(60, Math.round(v)));
	_anim.interval = Math.round(1000 / fpsRate);
	mgraphics.redraw();
}
function clear() {
	events = [];
	for (var p = 0; p < 128; p++) held[p] = -1;
	clipNotes = [];
	onsetQ = [];
	anEvents = [];
	currentChordCol = null; currentDissCol = null;
	spinVel = 0; spinPhase = 0; lastOnsetPitch = -1;
	previewMs = 0;
	_chanSeen = {}; _chanCount = 0; _multiChan = 0;
	mgraphics.redraw();
}

// ---- Live API -----------------------------------------------------------------------
// House rules from forteseq2.js / midibounce.js: guard on typeof LiveAPI, ONE reusable
// object re-pointed by id/path, wrap the whole sequence in try/catch (a throw kills the js).
function idOf(ret) {   // ["id", 123] -> 123
	if (!ret) return 0;
	for (var i = 0; i < ret.length; i++) if (ret[i] === "id") return ret[i + 1];
	return 0;
}
function first(ret) { return (ret && ret.length !== undefined) ? ret[0] : ret; }
function trackIndexFromPath(p) { var m = String(p).match(/tracks (\d+)/); return m ? parseInt(m[1], 10) : -1; }

// this device's own Live track index -> myVoice (so its own notein is tagged like the bus)
function resolveMyVoice() {
	myVoice = -1;
	if (typeof LiveAPI === "undefined") return;
	try {
		var dev = new LiveAPI(null, "this_device");
		var trk = new LiveAPI(null);
		trk.id = idOf(dev.get("canonical_parent"));
		myVoice = trackIndexFromPath(trk.path);
	} catch (e) { myVoice = -1; }
}

// Lookahead: read the playing MIDI clip on EVERY track, tag each note with its track index
// (the voice). The scroll reference (loopStart/End) is this device's own track's clip, or
// the first clip found. v1 assumes the other clips are bar-1 aligned (true for a split
// multi-channel import).
function readclip() {
	if (typeof LiveAPI === "undefined") { clipMsg = "sin Live API"; return; }
	if (myVoice < 0) resolveMyVoice();
	try {
		clipNotes = [];
		var song = new LiveAPI(null, "live_set");
		var tp = Number(first(song.get("tempo")));   // authoritative tempo -> preview runs at the right rate
		if (tp > 0) tempoBpm = tp;
		var ids = song.get("tracks");
		var t = new LiveAPI(null), cl = new LiveAPI(null);
		var nTracks = 0, maxEnd = 0;
		for (var k = 0; k < ids.length; k++) {
			if (ids[k] !== "id") continue;
			t.id = ids[k + 1];
			var ti = trackIndexFromPath(t.path);
			var psi = t.get("playing_slot_index");
			var slot = (psi && psi.length) ? Number(psi[0]) : -1;
			var cp = null;
			if (slot >= 0) cp = "live_set tracks " + ti + " clip_slots " + slot + " clip";
			else if (ti === myVoice) {
				var dc = new LiveAPI(null, "live_set view detail_clip");
				if (dc && dc.id && dc.id !== "0" && dc.id !== 0) cp = dc.path.replace(/"/g, "");
			}
			if (!cp) continue;
			cl.path = cp;
			if (!cl.id || cl.id === "0" || cl.id === 0) continue;
			if (Number(first(cl.get("is_midi_clip"))) !== 1) continue;
			var len = Number(first(cl.get("length"))) || 4;
			// read the WHOLE clip, not just its loop brace -- `length` is the loop length for
			// a looping clip, which truncated the preview to a few beats.
			var raw = cl.call("get_notes_extended", 0, 128, 0, Math.max(len, 4096));
			var obj = (typeof raw === "string") ? JSON.parse(raw) : raw;
			var arr = (obj && obj.notes) ? obj.notes : [];
			for (var i = 0; i < arr.length; i++) {
				var nn = arr[i];
				var st = Number(nn.start_time), du = Number(nn.duration);
				if (st + du > maxEnd) maxEnd = st + du;
				clipNotes.push({ pitch: Math.round(nn.pitch), start: st,
					dur: du, vel: Number(nn.velocity), voice: ti });
			}
			nTracks++;
		}
		// scroll span = the full note extent, rounded up to a bar (min 4 beats). Lookahead
		// loops over this via posInLoop, independent of Live's transport / loop brace.
		clipLoopStart = 0;
		clipLoopEnd = Math.max(4, Math.ceil(maxEnd / 4) * 4);
		clipMsg = clipNotes.length + " notas / " + nTracks + " pistas  ("
			+ clipLoopStart.toFixed(1) + ".." + clipLoopEnd.toFixed(1) + ")";
	} catch (e) {
		clipMsg = "error al leer clips: " + e;
		clipNotes = [];
	}
	previewMs = 0;                        // a fresh read restarts the preview at the clip's start
	lastWall = (new Date()).getTime();   // and the next frame's dt must not count this read
	mgraphics.redraw();
}

// ---- painting ----------------------------------------------------------------------
function yRange() {
	if (rangeMode === 1) return [Math.min(rangeLo, rangeHi), Math.max(rangeLo, rangeHi) + 1];
	// auto: observed min/max across live events (or clip notes in lookahead), with margin
	var lo = 127, hi = 0, seen = false, i;
	var src = (timeMode === 1) ? clipNotes : events;
	for (i = 0; i < src.length; i++) {
		var p = src[i].pitch;
		if (p < lo) lo = p; if (p > hi) hi = p; seen = true;
	}
	if (!seen) { lo = 48; hi = 84; }
	else { lo -= 3; hi += 4; }
	// hysteresis: ease toward the target so the axis does not snap on every note
	autoLo += (lo - autoLo) * 0.12;
	autoHi += (hi - autoHi) * 0.12;
	var a = Math.max(0, Math.floor(autoLo)), b = Math.min(128, Math.ceil(autoHi));
	if (b - a < 30) {   // keep at least ~2.5 octaves on screen so bars stay slim
		var mid = (a + b) / 2;
		a = Math.max(0, Math.round(mid - 15));
		b = Math.min(128, a + 30);
	}
	return [a, b];
}

// colour source, chosen by ColorMode: 0 = por Nota (circle-of-fifths pc wheel),
// 1 = por Voz (per-track hue), 2 = Fijo (one accent colour), 3 = Acorde (OKLab blend of the
// held chord), 4 = Disonancia (McKay % of the held chord, bucketed by threshold). 3/4 colour
// every currently-sounding note the SAME -- they describe the chord, not the individual pitch.
function colorFor(pc, voice) {
	if (colorMode === 4) return (currentDissCol || NEUTRAL_COL).concat(1);
	if (colorMode === 3) return (currentChordCol || NEUTRAL_COL).concat(1);
	if (colorMode === 2) return COL_ACCENT;
	if (colorMode === 1) return VOICE_COLOR[((voice % VOICE_N) + VOICE_N) % VOICE_N].concat(1);
	return PC_COLOR[((pc % 12) + 12) % 12].concat(1);
}

// distinct voices (track indices) seen, sorted, capped at 8 (lane count). Unions the live
// buffer and the lookahead clip notes so lanes work in both time modes.
function voicesSeen() {
	var s = [], i;
	for (i = 0; i < events.length; i++) if (s.indexOf(events[i].voice) < 0) s.push(events[i].voice);
	for (i = 0; i < clipNotes.length; i++) if (s.indexOf(clipNotes[i].voice) < 0) s.push(clipNotes[i].voice);
	s.sort(function (a, b) { return a - b; });
	if (s.length === 0) s = [Math.max(0, myVoice)];
	return s.slice(0, 8);
}

// colour (always from ColorMode) + glyph kind (from VoiceMode: 1 Figura = a shape per
// voice, else plain). Colour and shape are independent now.
function voiceStyle(ev) {
	var v = ((ev.voice % VOICE_N) + VOICE_N) % VOICE_N;
	return { col: colorFor(ev.pitch, ev.voice), kind: (voiceMode === 1 ? (v % 6) : 0) };
}

// a note bar drawn in one of 6 styles so overlapping voices stay legible without colour.
// (x,y) is the top-left, w the duration width, h the thickness. x is also the onset edge.
function drawBar(kind, x, y, w, h) {
	if (kind === 5) {                                  // hollow / outline
		mgraphics.set_line_width(1.5);
		mgraphics.rectangle(x + 0.75, y + 0.75, Math.max(1, w - 1.5), Math.max(1, h - 1.5));
		mgraphics.stroke();
		return;
	}
	if (kind === 4) {                                  // dashed / segmented
		var seg = Math.max(3, h), xx = x;
		while (xx < x + w) { mgraphics.rectangle(xx, y, Math.min(seg, x + w - xx), h); mgraphics.fill(); xx += seg + 2; }
		return;
	}
	mgraphics.rectangle(x, y, w, h); mgraphics.fill();
	var cy = y + h / 2;
	if (kind === 1) {                                  // rounded ends
		mgraphics.ellipse(x - h / 2, y, h, h); mgraphics.fill();
		mgraphics.ellipse(x + w - h / 2, y, h, h); mgraphics.fill();
	} else if (kind === 2) {                           // diamond onset cap
		var d = h * 1.1;
		mgraphics.move_to(x, cy - d / 2); mgraphics.line_to(x + d / 2, cy);
		mgraphics.line_to(x, cy + d / 2); mgraphics.line_to(x - d / 2, cy);
		mgraphics.close_path(); mgraphics.fill();
	} else if (kind === 3) {                           // chevron onset cap
		var d2 = h * 1.2;
		mgraphics.move_to(x - d2 * 0.6, cy - d2 / 2); mgraphics.line_to(x, cy);
		mgraphics.line_to(x - d2 * 0.6, cy + d2 / 2); mgraphics.line_to(x - d2 * 0.2, cy + d2 / 2);
		mgraphics.line_to(x + d2 * 0.4, cy); mgraphics.line_to(x - d2 * 0.2, cy - d2 / 2);
		mgraphics.close_path(); mgraphics.fill();
	}
}

var NOTE_THICK = 10;   // px height of a note bar (recomputed each paint from the row height)
var LABEL_FS   = 13;   // note-name font size for Espiral / Dodecaedro
var _lastPaintErr = "";

// a small filled marker in one of 6 shapes -- the Espiral counterpart of drawBar's 6 bar
// styles, so voices stay distinct there too. (x,y) is the centre, r the nominal radius.
function drawGlyph(kind, x, y, r) {
	kind = ((Math.round(kind) % 6) + 6) % 6;
	if (kind === 0) { mgraphics.ellipse(x - r, y - r, 2 * r, 2 * r); mgraphics.fill(); return; }
	if (kind === 1) { mgraphics.rectangle(x - r, y - r, 2 * r, 2 * r); mgraphics.fill(); return; }
	if (kind === 5) {                                   // plus / cross
		var t = r * 0.5;
		mgraphics.rectangle(x - t, y - r, 2 * t, 2 * r); mgraphics.fill();
		mgraphics.rectangle(x - r, y - t, 2 * r, 2 * t); mgraphics.fill();
		return;
	}
	var pts = (kind === 2) ? 3 : (kind === 3) ? 4 : 5;  // triangle / diamond / pentagon
	var rot = -90, i, a;
	mgraphics.move_to(x + r * 1.15 * Math.cos(rot * Math.PI / 180), y + r * 1.15 * Math.sin(rot * Math.PI / 180));
	for (i = 1; i < pts; i++) {
		a = (rot + i * 360 / pts) * Math.PI / 180;
		mgraphics.line_to(x + r * 1.15 * Math.cos(a), y + r * 1.15 * Math.sin(a));
	}
	mgraphics.close_path(); mgraphics.fill();
}
function paint() {
  try {
	var wh = viewportWH();
	var W = wh[0], H = wh[1];

	mgraphics.set_source_rgba(BG);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();

	if (viewMode === 1) paintSpiral(W, H);
	else if (viewMode === 2) paintDodeca(W, H);
	else if (viewMode === 3) paintPractica(W, H);
	else paintBarras(W, H);

	// frame + status (all views)
	mgraphics.set_source_rgba(FRAME);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(0.5, 0.5, W - 1, H - 1);
	mgraphics.stroke();

	mgraphics.set_source_rgba(COL_TEXT);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(9);
	mgraphics.move_to(8, 13);
	var vname = viewMode === 1 ? "Espiral" : viewMode === 2 ? "Dodecaedro"
		: viewMode === 3 ? "Práctica" : "Barras";
	var tag = (viewMode === 1 || viewMode === 2) ? vname
		: (timeMode === 1 ? (vname + " / Lookahead   " + clipMsg)
			: (vname + " / Tiempo real" + (clockRunning() ? "" : "  (transporte detenido)")));
	mgraphics.show_text(tag);

	if ((viewMode === 0 || viewMode === 3) && (colorMode === 1 || voiceMode === 1)) paintVoiceLegend(W, H);
	else if (colorMode === 0) paintLegend(W, H);
  } catch (e) {
	if (String(e) !== _lastPaintErr) { _lastPaintErr = String(e); post("animidi paint error: " + e + "\n"); }
  }
}

// the scrolling bar-graph score (the original ANIMIDI view)
function paintBarras(W, H) {
	var yr = yRange();
	var loP = yr[0], hiP = yr[1];
	var rows = hiP - loP;

	// lanes: one horizontal band per voice (track) seen -- works in real-time AND lookahead
	var lanes = (voiceMode === 2) ? voicesSeen() : null;
	// the velocity + harmony lanes (toggles) eat VEL_H/HARM_H off the bottom, stacked -- the
	// note plot ends at plotBot, which is what paintGrid / paintRealtime / paintLookahead /
	// drawLeftPiano get as "H".
	var lanesH = (velLane ? VEL_H : 0) + (harmLane ? HARM_H : 0);
	var plotBot = lanesH ? Math.max(120, H - lanesH) : H;
	var rowH = plotBot / rows;
	NOTE_THICK = Math.max(3, Math.min(14, rowH * 0.8));   // slim bars, never fatter than 14px

	function yFor(pitch, voice) {
		var frac = (pitch - loP + 0.5) / (hiP - loP);
		if (!lanes) return plotBot - frac * plotBot;
		var li = lanes.indexOf(voice); if (li < 0) li = 0;
		var bandH = plotBot / lanes.length, top = li * bandH;
		return top + bandH * (0.96 - frac * 0.92);
	}

	// left piano gutter (toggle): the plot starts to its right
	var plotL = (pianoOn && !lanes) ? KEYBOARD_W : 0;   // lanes mode has no room / no meaning for it
	// Lookahead pins "ahora" to the piano edge on the LEFT so the whole width is the runway
	// of upcoming notes; Tiempo real keeps it near the right so the trailing history shows.
	var nowX = Math.round(plotL + (W - plotL) * (timeMode === 1 ? 0.0 : 0.80)) + 0.5;
	if (gridOn) paintGrid(W, plotBot, loP, hiP, rowH, nowX, lanes, plotL);

	if (timeMode === 1) paintLookahead(W, plotBot, nowX, loP, hiP, yFor, plotL);
	else                paintRealtime(W, plotBot, nowX, loP, hiP, yFor, plotL);

	mgraphics.set_source_rgba(NOWLINE);
	mgraphics.set_line_width(1.5);
	mgraphics.move_to(nowX, 0); mgraphics.line_to(nowX, plotBot); mgraphics.stroke();

	if (plotL > 0) drawLeftPiano(plotBot, loP, hiP);
	// stack the lanes: harmony spectrum first (closest to the note plot), then velocity below.
	var laneY = plotBot;
	if (harmLane) { paintHarmLane(W, laneY + HARM_H, nowX, loP, hiP, plotL, laneY); laneY += HARM_H; }
	if (velLane)  { paintVelLane(W, laneY + VEL_H, nowX, loP, hiP, plotL, laneY); laneY += VEL_H; }
}

// harmony-colour spectrum lane along the bottom HARM_H px: a strip of contiguous colour
// blocks, one per stretch of unchanging harmony, coloured by dissonanceBand/bandColor of
// whichever pitch classes are concurrently sounding -- independent of ColorMode (like VelLane
// is independent of it, this always reads via the threshold/disonancia mapping). Built
// entirely in screen-space from the note spans Barras/Lookahead already compute (their x math,
// mirrored here) plus the SAME events/clipNotes buffers -- no separate history buffer.
function paintHarmLane(W, H, nowX, loP, hiP, plotL, plotBot) {
	var top = plotBot, laneH = H - plotBot;
	if (laneH < 6) return;
	mgraphics.set_source_rgba(0.08, 0.08, 0.09, 1);
	mgraphics.rectangle(plotL, top, W - plotL, laneH); mgraphics.fill();

	// gather every visible note as a screen-space [x0, x1] span tagged with its pitch class.
	// AnWin (anWinSec): a pc keeps counting toward the lane's colour for winPx past its OWN
	// onset even after it's released -- a melodic run reads as one aggregated set instead of
	// single, never-dissonant-alone notes -- so x1 is widened to at least x0 + winPx. winPx is
	// the same in both time models: beatPx * (anWinSec*tempo/60) reduces to anWinSec*pxPerSec.
	var spans = [], i, winPx = anWinSec * pxPerSec;
	if (timeMode === 1) {
		if (clipNotes.length) {
			var beatPx = pxPerSec * 60 / Math.max(1, tempoBpm);
			var loopLen = Math.max(0.01, clipLoopEnd - clipLoopStart);
			var posInLoop = clipLoopStart + (((lookaheadBeats() - clipLoopStart) % loopLen) + loopLen) % loopLen;
			var leftBeats = nowX / beatPx, rightBeats = (W - nowX) / beatPx;
			var repEnd = Math.min(64, Math.ceil((rightBeats + leftBeats) / loopLen) + 1);
			for (var rep = -1; rep <= repEnd; rep++) {
				for (i = 0; i < clipNotes.length; i++) {
					var cn = clipNotes[i];
					var xOn = nowX + ((cn.start - posInLoop) + rep * loopLen) * beatPx;
					var xOff = Math.max(xOn + cn.dur * beatPx, xOn + winPx);
					if (xOff < plotL || xOn > W) continue;
					spans.push({ x0: Math.max(plotL, xOn), x1: Math.min(W, xOff), pc: ((cn.pitch % 12) + 12) % 12 });
				}
			}
		}
	} else {
		for (i = 0; i < events.length; i++) {
			var ev = events[i];
			var exOn = nowX - (scrollMs - ev.tOn) * pxPerSec / 1000;
			var exOffRaw = ev.tOff < 0 ? nowX : nowX - (scrollMs - ev.tOff) * pxPerSec / 1000;
			var exOff = Math.max(exOffRaw, exOn + winPx);
			if (exOff < plotL || exOn > W) continue;
			spans.push({ x0: Math.max(plotL, exOn), x1: Math.min(W, exOff), pc: ((ev.pitch % 12) + 12) % 12 });
		}
	}

	// sweep-line: cut the lane at every span boundary, colour each resulting slice by the OKLab
	// blend of the pcs active at its midpoint (a chord change only happens at a boundary, so
	// this is exact) -- same colour tonnetz's "Col" panel shows, not the McKay dissonance band.
	var bounds = [plotL, W], s;
	for (i = 0; i < spans.length; i++) {
		s = spans[i];
		if (s.x0 > plotL && s.x0 < W) bounds.push(s.x0);
		if (s.x1 > plotL && s.x1 < W) bounds.push(s.x1);
	}
	bounds.sort(function (a, b) { return a - b; });

	for (i = 0; i < bounds.length - 1; i++) {
		var xa = bounds[i], xb = bounds[i + 1];
		if (xb - xa < 0.25) continue;
		var mid = (xa + xb) / 2, pcs = [], seen = {};
		for (var k = 0; k < spans.length; k++) {
			s = spans[k];
			if (mid >= s.x0 && mid <= s.x1 && !seen[s.pc]) { seen[s.pc] = 1; pcs.push(s.pc); }
		}
		var col;
		if (pcs.length) {
			var blend = harmonyToColor(pcs, { baseHue: baseHue, sat: baseSat }, 'oklab');
			col = [blend.r, blend.g, blend.b];
		} else col = [0.16, 0.16, 0.18];
		mgraphics.set_source_rgba(col[0], col[1], col[2], 1);
		mgraphics.rectangle(xa, top, xb - xa, laneH); mgraphics.fill();
	}

	mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 1);
	mgraphics.set_line_width(1);
	mgraphics.move_to(plotL, top + 0.5); mgraphics.line_to(W, top + 0.5); mgraphics.stroke();
	mgraphics.set_source_rgba(NOWLINE);
	mgraphics.set_line_width(1.5);
	mgraphics.move_to(nowX, top); mgraphics.line_to(nowX, H); mgraphics.stroke();
}

// velocity line-graph lane along the bottom VEL_H px (like an Ableton clip's velocity
// editor, but as a connected line): a faint stem + a dot per visible note at its velocity
// height, a polyline through the dots in time order, and reference lines at 0/32/64/96/127.
function paintVelLane(W, H, nowX, loP, hiP, plotL, plotBot) {
	var top = plotBot, laneH = H - plotBot;
	if (laneH < 16) return;
	mgraphics.set_source_rgba(0.08, 0.08, 0.09, 1);
	mgraphics.rectangle(plotL, top, W - plotL, laneH); mgraphics.fill();
	mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 1);
	mgraphics.set_line_width(1);
	mgraphics.move_to(plotL, top + 0.5); mgraphics.line_to(W, top + 0.5); mgraphics.stroke();

	function velY(vv) { return top + laneH - 3 - (Math.max(0, Math.min(127, vv)) / 127) * (laneH - 6); }

	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(7);
	var marks = [0, 32, 64, 96, 127], m;
	for (m = 0; m < marks.length; m++) {
		var gy = velY(marks[m]);
		mgraphics.set_source_rgba(GRID_BEAT[0], GRID_BEAT[1], GRID_BEAT[2], 1);
		mgraphics.set_line_width(1);
		mgraphics.move_to(plotL, gy); mgraphics.line_to(W, gy); mgraphics.stroke();
		mgraphics.set_source_rgba(COL_TEXT[0], COL_TEXT[1], COL_TEXT[2], 0.75);
		mgraphics.move_to(plotL + 2, gy - 1); mgraphics.show_text("" + marks[m]);
	}

	// collect (x, vel, colour) for every visible note onset, using the same x math the
	// note views use
	var pts = [], i;
	if (timeMode === 1) {
		if (clipNotes.length) {
			var beatPx = pxPerSec * 60 / Math.max(1, tempoBpm);
			var loopLen = Math.max(0.01, clipLoopEnd - clipLoopStart);
			var posInLoop = clipLoopStart + (((lookaheadBeats() - clipLoopStart) % loopLen) + loopLen) % loopLen;
			var leftBeats = nowX / beatPx, rightBeats = (W - nowX) / beatPx;
			var repEnd = Math.min(64, Math.ceil((rightBeats + leftBeats) / loopLen) + 1);
			for (var rep = -1; rep <= repEnd; rep++) {
				for (i = 0; i < clipNotes.length; i++) {
					var cn = clipNotes[i];
					var x = nowX + ((cn.start - posInLoop) + rep * loopLen) * beatPx;
					if (x < plotL || x > W) continue;
					pts.push({ x: x, v: cn.vel, c: colorFor(cn.pitch, (cn.voice === undefined ? 0 : cn.voice)) });
				}
			}
		}
	} else {
		for (i = 0; i < events.length; i++) {
			var ev = events[i];
			var ex = nowX - (scrollMs - ev.tOn) * pxPerSec / 1000;
			if (ex < plotL || ex > W) continue;
			pts.push({ x: ex, v: ev.vel, c: colorFor(ev.pitch, ev.voice) });
		}
	}
	pts.sort(function (a, b) { return a.x - b.x; });

	var k, p;
	for (k = 0; k < pts.length; k++) {              // stems + dots
		p = pts[k];
		var vy = velY(p.v);
		mgraphics.set_source_rgba(p.c[0], p.c[1], p.c[2], 0.45);
		mgraphics.set_line_width(1);
		mgraphics.move_to(p.x, top + laneH - 3); mgraphics.line_to(p.x, vy); mgraphics.stroke();
		mgraphics.set_source_rgba(p.c[0], p.c[1], p.c[2], 1);
		mgraphics.ellipse(p.x - 2, vy - 2, 4, 4); mgraphics.fill();
	}
	if (pts.length >= 2) {                          // the line graph through the dots
		mgraphics.set_source_rgba(COL_TEXT[0], COL_TEXT[1], COL_TEXT[2], 0.6);
		mgraphics.set_line_width(1.3);
		mgraphics.move_to(pts[0].x, velY(pts[0].v));
		for (k = 1; k < pts.length; k++) mgraphics.line_to(pts[k].x, velY(pts[k].v));
		mgraphics.stroke();
	}

	mgraphics.set_source_rgba(NOWLINE);
	mgraphics.set_line_width(1.5);
	mgraphics.move_to(nowX, top); mgraphics.line_to(nowX, H); mgraphics.stroke();
}

// note-name label for a note sounding at the now-line (notetags toggle). A small dark pill
// just past the now-line, flipped to the left near the right edge.
function drawNowTag(nowX, yc, pitch, W) {
	var lbl = noteLabel(pitch);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(9);
	var tw = lbl.length * 6.2 + 6;
	var x = nowX + 3;
	if (x + tw > W) x = nowX - 3 - tw;
	mgraphics.set_source_rgba(0, 0, 0, 0.62);
	mgraphics.rectangle(x, yc - 7, tw, 13); mgraphics.fill();
	mgraphics.set_source_rgba(1, 1, 1, 0.96);
	mgraphics.move_to(x + 3, yc + 3);
	mgraphics.show_text(lbl);
}

// vertical piano keyboard down the left KEYBOARD_W px of Barras: one row per semitone of
// the visible range, white keys full width, black keys shorter and on top; a held key
// lights in its note colour. Ableton-style piano-roll gutter.
function drawLeftPiano(H, loP, hiP) {
	var rowH = H / (hiP - loP);
	mgraphics.set_line_width(1);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(8);
	var pass, n, pc, yTop, kw, on, col;
	for (pass = 0; pass < 2; pass++) {          // whites first, then blacks on top
		for (n = loP; n < hiP; n++) {
			pc = ((n % 12) + 12) % 12;
			var black = isBlackPc(pc);
			if ((pass === 0) === black) continue;
			yTop = H - (n - loP + 1) * rowH;
			kw = black ? KEYBOARD_W * 0.62 : KEYBOARD_W;
			on = (held[n] >= 0 && events[held[n]]);
			if (on) { col = colorFor(pc, events[held[n]].voice); mgraphics.set_source_rgba(col[0], col[1], col[2], 1); }
			else mgraphics.set_source_rgba(black ? KEY_BLACK : KEY_WHITE);
			mgraphics.rectangle(0, yTop, kw, Math.max(1, rowH - 0.5)); mgraphics.fill();
			mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 0.7);
			mgraphics.rectangle(0, yTop, kw, Math.max(1, rowH)); mgraphics.stroke();
			if (pc === 0 && rowH >= 7) {
				mgraphics.set_source_rgba(on ? 0.1 : 0.42, on ? 0.1 : 0.42, on ? 0.1 : 0.45, 1);
				mgraphics.move_to(2, yTop + rowH - 2);
				mgraphics.show_text("C" + (Math.round(n / 12) - 1));
			}
		}
	}
}

// a 12-swatch legend (chromatic order, C first) so the rotated palette is readable. Drawn
// on its own dark panel so it stays legible over same-coloured bars in Barras (that was the
// "no se ve abajo a la izquierda" bug -- the swatches used to camouflage into the notes).
function paintLegend(W, H) {
	var sw = 16, x0 = 8, gap = 2;
	var panelW = 12 * (sw + gap) + 8, panelH = sw + 8;
	var px = 4, py = H - panelH - 4 - (viewMode === 0 ? (velLane ? VEL_H : 0) + (harmLane ? HARM_H : 0) : 0);
	mgraphics.set_source_rgba(0.06, 0.06, 0.07, 0.86);
	mgraphics.rectangle(px, py, panelW, panelH); mgraphics.fill();
	mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 0.8);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(px + 0.5, py + 0.5, panelW - 1, panelH - 1); mgraphics.stroke();
	var y0 = py + 4;
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(9);
	for (var pc = 0; pc < 12; pc++) {
		var x = x0 + pc * (sw + gap);
		var c = PC_COLOR[pc];
		mgraphics.set_source_rgba(c[0], c[1], c[2], 1);
		mgraphics.rectangle(x, y0, sw, sw); mgraphics.fill();
		var lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2];
		mgraphics.set_source_rgba(lum > 0.6 ? 0.1 : 0.95, lum > 0.6 ? 0.1 : 0.95, lum > 0.6 ? 0.1 : 0.95, 1);
		mgraphics.move_to(x + 2, y0 + sw - 4);
		mgraphics.show_text(NOTE_NAMES[pc]);
	}
}

// legend for VoiceMode / ColorMode=Voz: one entry per voice (track) seen -- marker + vN, on
// its own dark panel. The marker matches the view: drawGlyph shape in Espiral, drawBar
// style in Barras, plain swatch otherwise.
function paintVoiceLegend(W, H) {
	var vs = voicesSeen();
	var sw = 16, x0 = 8, cell = 58;
	var panelW = Math.max(1, vs.length) * cell + 8, panelH = sw + 8;
	var px = 4, py = H - panelH - 4 - (viewMode === 0 ? (velLane ? VEL_H : 0) + (harmLane ? HARM_H : 0) : 0);
	mgraphics.set_source_rgba(0.06, 0.06, 0.07, 0.86);
	mgraphics.rectangle(px, py, panelW, panelH); mgraphics.fill();
	mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 0.8);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(px + 0.5, py + 0.5, panelW - 1, panelH - 1); mgraphics.stroke();
	var y0 = py + 4;
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(9);
	for (var i = 0; i < vs.length; i++) {
		var v = ((vs[i] % VOICE_N) + VOICE_N) % VOICE_N;
		var x = x0 + i * cell;
		// marker colour = the per-voice hue only when ColorMode is "Voz"; otherwise neutral,
		// because the notes are not that colour -- the shape + number carry the key.
		if (colorMode === 1) { var c = VOICE_COLOR[v]; mgraphics.set_source_rgba(c[0], c[1], c[2], 1); }
		else mgraphics.set_source_rgba(COL_TEXT[0], COL_TEXT[1], COL_TEXT[2], 1);
		if (voiceMode === 1 && viewMode === 1) drawGlyph(v % 6, x + sw / 2, y0 + sw / 2, sw / 2);
		else if (voiceMode === 1) drawBar(v % 6, x, y0, sw, sw);
		else { mgraphics.rectangle(x, y0, sw, sw); mgraphics.fill(); }
		mgraphics.set_source_rgba(COL_TEXT);
		mgraphics.move_to(x + sw + 3, y0 + sw - 4);
		mgraphics.show_text("v" + vs[i]);
	}
}

// ---- Espiral: a pitch helix -------------------------------------------------------
// angle = pitch class (C at 12 o'clock), radius grows one ring per octave. A held note is
// a dot; the recent melody (onsetQ) is a fading thread winding in / out. `Spin` rotates the
// whole wheel with the beat (one turn per bar at Spin=25), folding rhythm back in as angle.
function spiralPt(pitch, g) {
	var rel = pitch - g.loP;
	var ang = (-90 + rel * 30 + g.spinDeg) * Math.PI / 180;
	var rad = g.r0 + (rel / 12) * g.ring;
	return [g.cx + rad * Math.cos(ang), g.cy + rad * Math.sin(ang)];
}
function paintSpiral(W, H) {
	var yr = yRange(), loP = yr[0], hiP = yr[1];
	var nOct = Math.max(1, (hiP - loP) / 12);
	var cx = W / 2, cy = H / 2 + 6;
	var rMax = Math.min(W, H) / 2 - 28;   // margin for the (now larger) rim note names
	var r0 = Math.max(14, rMax * 0.12);
	var ring = Math.min(ringGap, (rMax - r0) / nOct);
	var posBeat = posBeatNow();
	// Pulso: rotation tracks the beat (one turn/bar at Spin=25). Notas: the note-driven
	// phase integrated in tick() from each onset's contour-following kick.
	var spinDeg = (spinMode === 1) ? spinPhase : (spinAmt / 25) * posBeat * 90;
	var g = { cx: cx, cy: cy, loP: loP, r0: r0, ring: ring, spinDeg: spinDeg };

	// faint guide spiral
	mgraphics.set_source_rgba(GRID_OCT[0], GRID_OCT[1], GRID_OCT[2], 1);
	mgraphics.set_line_width(1);
	var p0 = spiralPt(loP, g);
	mgraphics.move_to(p0[0], p0[1]);
	for (var pp = loP + 1; pp <= hiP; pp += 1) { var q = spiralPt(pp, g); mgraphics.line_to(q[0], q[1]); }
	mgraphics.stroke();

	// 12 radial spokes + note names at the rim
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(LABEL_FS);
	for (var pc = 0; pc < 12; pc++) {
		var a = (-90 + pc * 30 + spinDeg) * Math.PI / 180;
		var ix = cx + r0 * Math.cos(a), iy = cy + r0 * Math.sin(a);
		var ox = cx + (rMax + 2) * Math.cos(a), oy = cy + (rMax + 2) * Math.sin(a);
		mgraphics.set_source_rgba(GRID_BEAT[0], GRID_BEAT[1], GRID_BEAT[2], 1);
		mgraphics.move_to(ix, iy); mgraphics.line_to(ox, oy); mgraphics.stroke();
		var cc = PC_COLOR[pc];
		mgraphics.set_source_rgba(cc[0], cc[1], cc[2], 0.95);
		mgraphics.move_to(cx + (rMax + 14) * Math.cos(a) - 6, cy + (rMax + 14) * Math.sin(a) + 5);
		mgraphics.show_text(NOTE_NAMES[pc]);
	}

	// melodic thread from onsetQ, fading oldest -> newest
	var n = onsetQ.length;
	if (n >= 2) {
		mgraphics.set_line_width(2);
		for (var i = 1; i < n; i++) {
			var A = spiralPt(onsetQ[i - 1].pitch, g), B = spiralPt(onsetQ[i].pitch, g);
			var aa = 0.12 + 0.7 * (i / (n - 1));
			var lc = (colorMode === 1) ? VOICE_COLOR[((onsetQ[i].voice % VOICE_N) + VOICE_N) % VOICE_N] : COL_TRACE;
			mgraphics.set_source_rgba(lc[0], lc[1], lc[2], aa);
			mgraphics.move_to(A[0], A[1]); mgraphics.line_to(B[0], B[1]); mgraphics.stroke();
		}
	}
	if (n >= 1) {
		var last = spiralPt(onsetQ[n - 1].pitch, g);
		mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], 1);
		mgraphics.ellipse(last[0] - 3, last[1] - 3, 6, 6); mgraphics.fill();
	}

	// held notes -- a bright marker (size ~ velocity). VoiceMode = Figura -> the voice's
	// drawGlyph shape, so voices are told apart here too; else a plain dot.
	for (var e = 0; e < events.length; e++) {
		var ev = events[e];
		if (ev.tOff >= 0 || ev.pitch < loP || ev.pitch >= hiP) continue;
		var P = spiralPt(ev.pitch, g);
		var rr = 3 + (ev.vel / 127) * 6;
		var col = colorFor(ev.pitch, ev.voice);
		mgraphics.set_source_rgba(col[0], col[1], col[2], 1);
		if (voiceMode === 1) drawGlyph((((ev.voice % VOICE_N) + VOICE_N) % VOICE_N) % 6, P[0], P[1], rr + 1);
		else { mgraphics.ellipse(P[0] - rr, P[1] - rr, rr * 2, rr * 2); mgraphics.fill(); }
	}

	if (colorMode === 1 || voiceMode === 1) paintVoiceLegend(W, H);
	else if (colorMode === 0) paintLegend(W, H);
}
// ---- Dodecaedro: 12 faces = 12 pitch classes ------------------------------------
// A regular dodecahedron (20 vertices from phi). Its 12 face centres point along the 12
// icosahedron directions; each face's 5 vertices are the 5 dodecahedron vertices nearest
// that direction. Face f <-> pitch class f. The solid slowly rotates (Spin); the sounding
// faces light up; successive notes draw a fading line between front-facing face centres.
var _PHI = (1 + Math.sqrt(5)) / 2, _IPHI = 1 / _PHI;
var DODECA_V = [];
(function () {
	var s = [1, -1];
	for (var a = 0; a < 2; a++) for (var b = 0; b < 2; b++) for (var c = 0; c < 2; c++)
		DODECA_V.push([s[a], s[b], s[c]]);
	for (var i = 0; i < 2; i++) for (var j = 0; j < 2; j++) {
		DODECA_V.push([0, s[i] * _IPHI, s[j] * _PHI]);
		DODECA_V.push([s[i] * _IPHI, s[j] * _PHI, 0]);
		DODECA_V.push([s[i] * _PHI, 0, s[j] * _IPHI]);
	}
	for (var k = 0; k < DODECA_V.length; k++) {
		var v = DODECA_V[k], m = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
		v[0] /= m; v[1] /= m; v[2] /= m;
	}
})();
var DODECA_N = [], DODECA_F = [];
(function () {
	// the 12 face-normal directions = vertices of the dual icosahedron
	var dirs = [], s = [1, -1];
	for (var i = 0; i < 2; i++) for (var j = 0; j < 2; j++) {
		dirs.push([0, s[i] * _PHI, s[j]]);
		dirs.push([s[i], 0, s[j] * _PHI]);
		dirs.push([s[i] * _PHI, s[j], 0]);
	}
	function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
	for (var d = 0; d < 12; d++) {
		var dir = dirs[d], dm = Math.sqrt(dot(dir, dir));
		dir = [dir[0] / dm, dir[1] / dm, dir[2] / dm];
		DODECA_N.push(dir);
		var scored = [];
		for (var k = 0; k < DODECA_V.length; k++) scored.push([k, dot(DODECA_V[k], dir)]);
		scored.sort(function (x, y) { return y[1] - x[1]; });
		var idx = [scored[0][0], scored[1][0], scored[2][0], scored[3][0], scored[4][0]];
		// order the pentagon by angle around the face centre, in the face plane
		var u = DODECA_V[idx[0]];
		var uu = [u[0] - dir[0] * dot(u, dir), u[1] - dir[1] * dot(u, dir), u[2] - dir[2] * dot(u, dir)];
		var um = Math.sqrt(dot(uu, uu)); uu = [uu[0] / um, uu[1] / um, uu[2] / um];
		var ww = [dir[1] * uu[2] - dir[2] * uu[1], dir[2] * uu[0] - dir[0] * uu[2], dir[0] * uu[1] - dir[1] * uu[0]];
		idx.sort(function (x, y) {
			var px = DODECA_V[x], py = DODECA_V[y];
			return Math.atan2(dot(px, ww), dot(px, uu)) - Math.atan2(dot(py, ww), dot(py, uu));
		});
		DODECA_F.push(idx);
	}
})();

function paintDodeca(W, H) {
	var cx = W / 2, cy = H / 2 + 6;
	var scale = Math.min(W, H) * 0.32;
	// Pulso: yaw advances with wall-clock time. Notas: the note-driven phase from tick().
	var yaw = 0.5 + ((spinMode === 1) ? spinPhase * Math.PI / 180
		: (spinAmt / 100) * scrollMs * 0.0006);
	var tilt = -0.42;
	var cyaw = Math.cos(yaw), syaw = Math.sin(yaw), ct = Math.cos(tilt), st = Math.sin(tilt);
	var camD = 3.4;
	function rot(v) {                                   // yaw about Y, then tilt about X
		var x = v[0] * cyaw + v[2] * syaw;
		var z = -v[0] * syaw + v[2] * cyaw;
		var y = v[1] * ct - z * st;
		z = v[1] * st + z * ct;
		return [x, y, z];
	}
	function proj(v) {
		var s = camD / (camD - v[2]);
		return [cx + s * scale * v[0], cy - s * scale * v[1]];
	}
	var RV = [], i;
	for (i = 0; i < DODECA_V.length; i++) RV.push(proj(rot(DODECA_V[i])));
	var RN = [], FC = [], vis = [];
	for (i = 0; i < 12; i++) {
		var nrm = rot(DODECA_N[i]);
		RN.push(nrm);
		vis.push(nrm[2] > 0.02);
		var f = DODECA_F[i], sx = 0, sy = 0;
		for (var k = 0; k < 5; k++) { sx += RV[f[k]][0]; sy += RV[f[k]][1]; }
		FC.push([sx / 5, sy / 5]);
	}

	// held pitch classes + their loudest velocity
	var pcVel = [];
	for (i = 0; i < 12; i++) pcVel[i] = -1;
	for (var e = 0; e < events.length; e++) {
		var ev = events[e];
		if (ev.tOff >= 0) continue;
		var pc = ((ev.pitch % 12) + 12) % 12;
		if (ev.vel > pcVel[pc]) pcVel[pc] = ev.vel;
	}

	// faces (front-facing only)
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(LABEL_FS);
	for (i = 0; i < 12; i++) {
		if (!vis[i]) continue;
		var fa = DODECA_F[i];
		mgraphics.move_to(RV[fa[0]][0], RV[fa[0]][1]);
		for (var j = 1; j < 5; j++) mgraphics.line_to(RV[fa[j]][0], RV[fa[j]][1]);
		mgraphics.close_path();
		if (pcVel[i] >= 0) {
			var c = PC_COLOR[i];
			mgraphics.set_source_rgba(c[0], c[1], c[2], 0.28 + 0.6 * (pcVel[i] / 127));
			mgraphics.fill_preserve();
		}
		mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 0.9);
		mgraphics.set_line_width(1.2);
		mgraphics.stroke();
		mgraphics.set_source_rgba(COL_TEXT[0], COL_TEXT[1], COL_TEXT[2], pcVel[i] >= 0 ? 1 : 0.5);
		mgraphics.move_to(FC[i][0] - 6, FC[i][1] + 5);
		mgraphics.show_text(NOTE_NAMES[i]);
	}

	// melodic thread between front-facing face centres, fading oldest -> newest
	var n = onsetQ.length;
	if (n >= 2) {
		mgraphics.set_line_width(2);
		for (i = 1; i < n; i++) {
			var a = ((onsetQ[i - 1].pc % 12) + 12) % 12, b = ((onsetQ[i].pc % 12) + 12) % 12;
			if (!vis[a] || !vis[b]) continue;
			var aa = 0.12 + 0.7 * (i / (n - 1));
			mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], aa);
			mgraphics.move_to(FC[a][0], FC[a][1]); mgraphics.line_to(FC[b][0], FC[b][1]); mgraphics.stroke();
		}
		var lp = ((onsetQ[n - 1].pc % 12) + 12) % 12;
		if (vis[lp]) {
			mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], 1);
			mgraphics.ellipse(FC[lp][0] - 3, FC[lp][1] - 3, 6, 6); mgraphics.fill();
		}
	}
}

function paintGrid(W, H, loP, hiP, rowH, nowX, lanes, plotL) {
	plotL = plotL || 0;
	mgraphics.set_line_width(1);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(8);
	if (lanes) {
		// lane separators + vN labels instead of octave lines
		for (var li = 0; li < lanes.length; li++) {
			var yb = li * (H / lanes.length);
			mgraphics.set_source_rgba(GRID_OCT);
			mgraphics.move_to(plotL, yb); mgraphics.line_to(W, yb); mgraphics.stroke();
			mgraphics.set_source_rgba(COL_TEXT);
			mgraphics.move_to(plotL + 3, yb + 10);
			mgraphics.show_text("v" + lanes[li]);
		}
	} else {
		// octave lines (every C), labelled -- label only when there is no left piano showing it
		for (var p = Math.ceil(loP / 12) * 12; p < hiP; p += 12) {
			var y = H - (p - loP) * rowH;
			mgraphics.set_source_rgba(GRID_OCT);
			mgraphics.move_to(plotL, y); mgraphics.line_to(W, y); mgraphics.stroke();
			if (plotL === 0) {
				mgraphics.set_source_rgba(COL_TEXT);
				mgraphics.move_to(3, y - 2);
				mgraphics.show_text("C" + (Math.round(p / 12) - 1));
			}
		}
	}
	// beat / bar lines -- 4/4 assumed for v1. A line sits at every integer beat B; its
	// screen x is nowX + (B - posBeat)*beatPx in BOTH modes. Real-time knows nothing to the
	// right of now, so it is clipped there.
	var beatPx = pxPerSec * 60 / Math.max(1, tempoBpm);
	if (beatPx < 6) return;   // too dense to be useful
	var posBeat = posBeatNow();
	var firstB = Math.floor(posBeat - nowX / beatPx) - 1;
	var lastB  = Math.ceil(posBeat + (W - nowX) / beatPx) + 1;
	for (var B = firstB; B <= lastB; B++) {
		var bx = nowX + (B - posBeat) * beatPx;
		if (bx < plotL - 2 || bx > W + 2) continue;
		if (timeMode !== 1 && bx > nowX + 1) continue;
		var isBar = (((B % 4) + 4) % 4) === 0;
		mgraphics.set_source_rgba(isBar ? GRID_BAR : GRID_BEAT);
		mgraphics.set_line_width(isBar ? 1.2 : 1);
		mgraphics.move_to(bx + 0.5, 0); mgraphics.line_to(bx + 0.5, H); mgraphics.stroke();
	}
}

function paintRealtime(W, H, nowX, loP, hiP, yFor, plotL) {
	plotL = plotL || 0;
	var barH = NOTE_THICK;
	for (var i = 0; i < events.length; i++) {
		var ev = events[i];
		if (ev.pitch < loP || ev.pitch >= hiP) continue;
		var endMs = (ev.tOff < 0) ? scrollMs : ev.tOff;   // held note grows to the now-line
		// each edge as px LEFT of the now-line; a longer-held note has an older tOn -> wider bar
		var xStart = nowX - (scrollMs - ev.tOn) * pxPerSec / 1000;   // left edge  (note-on)
		var xEnd   = nowX - (scrollMs - endMs)  * pxPerSec / 1000;   // right edge (note-off / now)
		if (xEnd < plotL || xStart > W) continue;                    // fully off-screen
		var left  = Math.max(plotL, xStart);
		var right = Math.min(W, xEnd);
		var w = Math.max(2, right - left);
		var y = yFor(ev.pitch, ev.voice) - barH / 2;
		var st = voiceStyle(ev);
		var isHeld = (ev.tOff < 0);
		mgraphics.set_source_rgba(st.col[0], st.col[1], st.col[2], isHeld ? 1 : 0.72);
		drawBar(st.kind, left, y, w, barH);
		if (isHeld && xEnd <= W) {   // bright cap riding the now-line while the key is down
			mgraphics.set_source_rgba(1, 1, 1, 0.55);
			mgraphics.rectangle(Math.max(plotL, xEnd - 2), y, 2, barH);
			mgraphics.fill();
		}
		if (noteTags && isHeld) drawNowTag(nowX, yFor(ev.pitch, ev.voice), ev.pitch, W);
	}
}

function paintLookahead(W, H, nowX, loP, hiP, yFor, plotL) {
	plotL = plotL || 0;
	// the "already swept" band: from the left edge of the plot up to the now-line. Watching
	// notes + the beat grid scroll through it (and reset each loop) reads as the transport
	// advancing. Drawn first so notes sit on top.
	mgraphics.set_source_rgba(PLAYED_SHADE);
	mgraphics.rectangle(plotL, 0, Math.max(0, nowX - plotL), H); mgraphics.fill();
	if (clipNotes.length === 0) return;
	var barH = NOTE_THICK;
	var beatPx = pxPerSec * 60 / Math.max(1, tempoBpm);
	var loopLen = Math.max(0.01, clipLoopEnd - clipLoopStart);
	// how far into the loop we are now
	var posInLoop = clipLoopStart + (((lookaheadBeats() - clipLoopStart) % loopLen) + loopLen) % loopLen;
	var leftBeats  = (nowX) / beatPx;             // beats visible left of now
	var rightBeats = (W - nowX) / beatPx;         // beats visible right of now

	var repEnd = Math.min(64, Math.ceil((rightBeats + leftBeats) / loopLen) + 1);
	for (var rep = -1; rep <= repEnd; rep++) {
		for (var i = 0; i < clipNotes.length; i++) {
			var cn = clipNotes[i];
			if (cn.pitch < loP || cn.pitch >= hiP) continue;
			var cv = (cn.voice === undefined) ? 0 : cn.voice;
			// note start relative to now, in beats, for this loop repetition
			var rel = (cn.start - posInLoop) + rep * loopLen;
			if (rel > rightBeats + 0.5) continue;
			if (rel + cn.dur < -leftBeats - 0.5) continue;
			var x1 = nowX + rel * beatPx;
			var x2 = x1 + Math.max(2, cn.dur * beatPx);
			if (x2 < 0 || x1 > W) continue;
			var y = yFor(cn.pitch, cv) - barH / 2;
			var col = colorFor(cn.pitch, cv);
			// portion already played (left of now) -- kept clearly visible now (was 0.34, all
			// but invisible); portion to come is brighter; the crossing note brightest.
			if (x1 < nowX) {
				var xL = Math.max(plotL, x1);
				var xm = Math.min(x2, nowX);
				if (xm > xL) {
					mgraphics.set_source_rgba(col[0], col[1], col[2], 0.6);
					mgraphics.rectangle(xL, y, xm - xL, barH);
					mgraphics.fill();
				}
			}
			if (x2 > nowX) {
				var xs = Math.max(x1, nowX);
				var crossing = (x1 < nowX + beatPx * 0.15) && (x2 > nowX);
				mgraphics.set_source_rgba(col[0], col[1], col[2], crossing ? 1 : 0.85);
				mgraphics.rectangle(xs, y, Math.min(x2, W) - xs, barH);
				mgraphics.fill();
			}
			if (noteTags && x1 <= nowX && x2 >= nowX) drawNowTag(nowX, y + barH / 2, cn.pitch, W);
		}
	}
}

// ---- Práctica: falling MIDI roll onto a keyboard at the bottom (Synthesia-style) -------
// x = pitch (a real white/black key layout), time = vertical. Lookahead: notes fall from
// the top and land on the key at the now-line. Tiempo real: the note grows up from the key
// while held, then scrolls off the top. Key span + colours reuse yRange() / colorFor /
// voiceStyle, so RangeMode, ColorMode and VoiceMode all still apply.
function practicaKeyLayout(loP, hiP, W) {
	var nW = 0, n;
	for (n = loP; n < hiP; n++) if (!isBlackPc(n)) nW++;
	var whiteW = W / Math.max(1, nW);
	var keys = [], wi = 0;
	for (n = loP; n < hiP; n++) {
		if (isBlackPc(n)) keys.push({ cx: wi * whiteW, isBlack: true });
		else { keys.push({ cx: (wi + 0.5) * whiteW, isBlack: false }); wi++; }
	}
	return { keys: keys, whiteW: whiteW, nWhite: nW };
}

function drawBottomPiano(loP, hiP, W, nowY, lay) {
	var keys = lay.keys, whiteW = lay.whiteW, n, pc, kk, on, col, x;
	mgraphics.set_line_width(1);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(8);
	for (n = loP; n < hiP; n++) {              // whites
		if (isBlackPc(n)) continue;
		kk = keys[n - loP]; x = kk.cx - whiteW / 2;
		on = (held[n] >= 0 && events[held[n]]);
		pc = ((n % 12) + 12) % 12;
		if (on) { col = colorFor(pc, events[held[n]].voice); mgraphics.set_source_rgba(col[0], col[1], col[2], 1); }
		else mgraphics.set_source_rgba(KEY_WHITE);
		mgraphics.rectangle(x, nowY, Math.max(1, whiteW - 1), KB_H); mgraphics.fill();
		mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 0.7);
		mgraphics.rectangle(x, nowY, Math.max(1, whiteW - 1), KB_H); mgraphics.stroke();
		if (pc === 0 && whiteW >= 9) {
			mgraphics.set_source_rgba(on ? 0.1 : 0.42, on ? 0.1 : 0.42, on ? 0.1 : 0.45, 1);
			mgraphics.move_to(x + 2, nowY + 12);
			mgraphics.show_text("C" + (Math.round(n / 12) - 1));
		}
	}
	var bw = whiteW * 0.62;
	for (n = loP; n < hiP; n++) {              // blacks on top
		if (!isBlackPc(n)) continue;
		kk = keys[n - loP]; x = kk.cx - bw / 2;
		on = (held[n] >= 0 && events[held[n]]);
		if (on) { col = colorFor(((n % 12) + 12) % 12, events[held[n]].voice); mgraphics.set_source_rgba(col[0], col[1], col[2], 1); }
		else mgraphics.set_source_rgba(KEY_BLACK);
		mgraphics.rectangle(x, nowY, bw, KB_H * 0.62); mgraphics.fill();
		mgraphics.set_source_rgba(FRAME[0], FRAME[1], FRAME[2], 0.85);
		mgraphics.rectangle(x, nowY, bw, KB_H * 0.62); mgraphics.stroke();
	}
}

function paintPractica(W, H) {
	var yr = yRange(), loP = yr[0], hiP = yr[1];
	if (hiP - loP < 1) return;
	var lay = practicaKeyLayout(loP, hiP, W);
	var keys = lay.keys, whiteW = lay.whiteW;
	var nowY = H - KB_H;
	var beatPx = pxPerSec * 60 / Math.max(1, tempoBpm);
	var posBeat = posBeatNow();

	if (gridOn) {
		mgraphics.set_line_width(1);
		mgraphics.set_source_rgba(GRID_BEAT[0], GRID_BEAT[1], GRID_BEAT[2], 1);
		for (var gi = 0; gi < keys.length; gi++) {
			if (keys[gi].isBlack) continue;
			var vx = keys[gi].cx - whiteW / 2;
			mgraphics.move_to(vx + 0.5, 0); mgraphics.line_to(vx + 0.5, nowY); mgraphics.stroke();
		}
		if (beatPx >= 6) {
			var sign = (timeMode === 1) ? -1 : 1;   // lookahead: future above now; real-time: past above
			var span = nowY / beatPx;
			for (var B = Math.floor(posBeat - span - 1); B <= Math.ceil(posBeat + span + 1); B++) {
				var gy = nowY + sign * (B - posBeat) * beatPx;
				if (gy < 0 || gy > nowY + 1) continue;
				var isBar = (((B % 4) + 4) % 4) === 0;
				mgraphics.set_source_rgba(isBar ? GRID_BAR : GRID_BEAT);
				mgraphics.set_line_width(isBar ? 1.2 : 1);
				mgraphics.move_to(0, gy + 0.5); mgraphics.line_to(W, gy + 0.5); mgraphics.stroke();
			}
		}
	}

	if (timeMode === 1 && clipNotes.length) {
		var loopLen = Math.max(0.01, clipLoopEnd - clipLoopStart);
		var posInLoop = clipLoopStart + (((lookaheadBeats() - clipLoopStart) % loopLen) + loopLen) % loopLen;
		var topBeats = nowY / beatPx;
		var repEnd = Math.min(64, Math.ceil(topBeats / loopLen) + 1);
		for (var rep = -1; rep <= repEnd; rep++) {
			for (var i = 0; i < clipNotes.length; i++) {
				var cn = clipNotes[i];
				if (cn.pitch < loP || cn.pitch >= hiP) continue;
				var rel = (cn.start - posInLoop) + rep * loopLen;      // beats until onset
				if (rel > topBeats + 1) continue;
				if (rel + cn.dur < -0.15) continue;                    // already fully landed
				var yb = nowY - rel * beatPx;                          // leading (bottom) edge
				var yt = yb - Math.max(3, cn.dur * beatPx);
				var dt = Math.max(0, yt), db = Math.min(nowY, yb);
				if (db <= dt) continue;
				var cvv = (cn.voice === undefined) ? 0 : cn.voice;
				var kc = keys[cn.pitch - loP];
				var cw = kc.isBlack ? whiteW * 0.5 : whiteW * 0.82;
				var cx0 = kc.cx - cw / 2;
				var cc = colorFor(cn.pitch, cvv);
				var sounding = (yt <= nowY && yb >= nowY);
				mgraphics.set_source_rgba(cc[0], cc[1], cc[2], sounding ? 1 : 0.82);
				mgraphics.rectangle(cx0, dt, cw, db - dt); mgraphics.fill();
				if (yb <= nowY + 1 && yb >= 2) {   // onset cap on the leading edge
					mgraphics.set_source_rgba(1, 1, 1, 0.5);
					mgraphics.rectangle(cx0, Math.min(nowY, yb) - 2, cw, 2); mgraphics.fill();
				}
			}
		}
	} else if (timeMode === 0) {
		var kk2 = pxPerSec / 1000;
		for (var e = 0; e < events.length; e++) {
			var ev = events[e];
			if (ev.pitch < loP || ev.pitch >= hiP) continue;
			var endMs = (ev.tOff < 0) ? scrollMs : ev.tOff;
			var yt2 = nowY - (scrollMs - ev.tOn) * kk2;   // onset edge (older, higher)
			var yb2 = nowY - (scrollMs - endMs) * kk2;    // offset edge (held -> nowY)
			if (yb2 < 0) continue;                        // scrolled off the top
			var db2 = Math.min(nowY, yb2);
			var dt2 = Math.max(0, yt2);
			if (db2 - dt2 < 3) dt2 = Math.max(0, db2 - 3);   // keep short notes visible
			if (db2 <= dt2) continue;
			var st = voiceStyle(ev);
			var kc2 = keys[ev.pitch - loP];
			var cw2 = kc2.isBlack ? whiteW * 0.5 : whiteW * 0.82;
			var cx2 = kc2.cx - cw2 / 2;
			var isHeld = (ev.tOff < 0);
			mgraphics.set_source_rgba(st.col[0], st.col[1], st.col[2], isHeld ? 1 : 0.78);
			mgraphics.rectangle(cx2, dt2, cw2, db2 - dt2); mgraphics.fill();
			if (isHeld) {
				mgraphics.set_source_rgba(1, 1, 1, 0.55);
				mgraphics.rectangle(cx2, nowY - 2, cw2, 2); mgraphics.fill();
			}
		}
	}

	// keyboard on top of the landed note ends
	mgraphics.set_source_rgba(BG);
	mgraphics.rectangle(0, nowY, W, KB_H); mgraphics.fill();
	drawBottomPiano(loP, hiP, W, nowY, lay);
	mgraphics.set_source_rgba(NOWLINE);
	mgraphics.set_line_width(1.5);
	mgraphics.move_to(0, nowY + 0.5); mgraphics.line_to(W, nowY + 0.5); mgraphics.stroke();
}

resolveMyVoice();
fitToWindow();
post("animidi.js cargado — " + (hasLiveApi ? ("Live API OK, pista " + myVoice) : "sin Live API") + "\n");
mgraphics.redraw();
