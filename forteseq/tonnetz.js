// tonnetz.js -- jsui for the standalone Tonnetz M4L device. A JS reimplementation of the
// 2D visualisations from HexaChord (Louis Bigo, https://gitlab.com/lbigo/hexachord): a
// generalized Tonnetz lattice plus the chromatic and fifths circles, with the pitch
// classes currently sounding highlighted in real time. NONE of HexaChord's Java is reused,
// only the concepts and the lattice math (a few lines of modular arithmetic). See
// src/Model/Music/Tonnetze/PlanarUnfoldedTonnetz.java there: pc(x,y) = (x*g0 - y*g2) mod 12.
//
// v3: the three views can be shown side by side at once (`view all`, the default); the
// drawing follows the floating window's size; nodes are coloured per pitch class from a
// circle-of-fifths hue wheel (matches sidebrain.net/relative-keys); the chord tones can be
// joined into a polygon on the circles (aug triad -> equilateral triangle, dim7 -> square)
// and/or the trace drawn as a chronological path; a footer line shows set-class info fed by
// pcsetinfo.js.
//
// Drawn in the same idiom as forteseq/circleoffifths.js (mgraphics, no ES6). Fed by the
// device patch:  [notein] -> [pack 0 0] -> [p tonnetz_window] -> [prepend note] -> here
//
// v4: two more views -- a piano keyboard (one-octave collapsed, or the full MIDI range) and
// a guitar fretboard (every position of a sounding pitch class, or only the exact sounding
// notes), with adjustable tuning/frets and a shared zoom + pan.
//
// v5: three overlays from Bigo et al. CMJ 2015. `faces` now also draws the chord's
// 1-simplices (every lattice edge with both ends sounding) and fattens sounding nodes -- the
// chord's full simplicial closure (Fig. 5b), not just the filled triangle. `plr` draws the
// neo-Riemannian P/L/R arrows from a sounding major/minor triad to its three edge-neighbours
// (Fig. 4a). `xfprev` previews a transformation (transpose by `xpose`, or invert about
// `invc`) by drawing the resulting pitch classes as magenta ghost rings -- purely a drawing,
// the MIDI is never touched (Fig. 11, eqs. 4/5).
//
// v6: the single "view" tab is replaced by seven independent on/off flags (`vton` `vchr`
// `vfif` `vvoc` `vpno` `vgtr` `vdia`); whatever is on is packed into a near-square auto-grid.
// Two are new panels: `vvoc` = a voice-leading space of the twelve trichord set-classes
// (HexaChord's third representation; fed the current set-class by pcsetinfo.js's `setclass`
// message), and `vdia` = a diatonic Tonnetz (axes are diatonic thirds, only the seven notes
// of `keyroot`/`keymode` appear -- N=7, Bigo p.13). harm and P/L/R are chromatic-lattice
// concepts and are suppressed on the diatonic panel.
//
// v7: `regtrace` draws the timed trajectory as a path of lattice REGIONS (Fig. 8/9) -- each
// pitch-class-set segment is anchored to the triangle/edge/vertex nearest the previous one
// (greedy "small movements") and drawn faded by age. `bestfit`/`autofit` come from the
// decoupled tonnetzfit.js: the interval vector whose lattice represents the recent music
// most compactly, shown as a caption and optionally followed by the live abc.
//
// v8: `vtet` = an eighth panel, Gollin's three-dimensional Tonnetz (1998; paper Fig. 4b/6b).
// The complex K[a,b,c,d] has 4-note chords (dominant sevenths, half-diminished) as
// tetrahedra; it is drawn as a flat isometric projection of the cubic lattice whose three
// axes are the cumulative interval sums of `tetpreset`. When four sounding pitch classes
// span a lattice tetrahedron its faces are filled. Also: a short last row of the panel grid
// is now centred at the common cell width instead of one panel stretching to full width.
//
// Messages:
//   note <pitch> <vel>   MIDI note; vel 0 = note-off. Ref-counted (per pitch class AND per
//                        MIDI note); a fresh pitch-class onset pushes the trace.
//   list <pc> ...        replace the active pitch-class set outright (no trace push)
//   clear                drop all active notes and the trace
//   vton/vchr/vfif/vvoc/vpno/vgtr/vdia/vtet <0|1>   show/hide each panel (Tonnetz, chromatic,
//                        fifths, voice-leading space, piano, guitar, diatonic Tonnetz, 3-D Tonnetz)
//   tetpreset <i>        3-D Tonnetz: pick the 4-note chord class from TET_PRESETS[i]
//   keyroot <0..11>      diatonic panel: tonic pitch class
//   keymode <0|1>        diatonic panel: 0 major scale | 1 natural minor
//   setclass <p ...>     current set-class prime form (from pcsetinfo.js; lights the vvoc node)
//   pianomode <0|1>      piano: 0 one octave (pitch classes) | 1 full MIDI 0..127 (notes)
//   guitarmode <0|1>     guitar: 0 all fretboard positions of sounding pcs | 1 only exact notes
//   tuning <i>           guitar tuning index (see TUNINGS)
//   frets <n>            guitar fret count 12..24
//   zoom <f>             piano/guitar horizontal zoom 1..8
//   pan <f>              piano/guitar horizontal pan 0..1 (only when zoomed past the panel)
//   abc <a> <b> <c>      generalized Tonnetz interval-class vector (default 3 4 5 = classic)
//   preset <i>           pick abc from PRESETS[i]
//   radius <px>          lattice spacing in pixels (Tonnetz), 24..120
//   trace <0|1>          keep recently-released pitch classes lit
//   tracelen <n>         how many onsets / region segments the trace remembers (1..24)
//   regtrace <0|1>       draw the trajectory as a path of lattice regions (Tonnetz only)
//   bestfit <a> <b> <c>  most-compact interval vector for the recent music (from tonnetzfit.js)
//   autofit <0|1>        let bestfit drive the live abc
//   harm <0|1>           light lattice neighbours of sounding notes (Tonnetz only)
//   faces <0|1>          fill a Tonnetz triangle when all three of its pitch classes sound
//   labels <0|1>         note names (1, default) vs pitch-class numbers (0)
//   colors <0|1>         per-pitch-class colours (1, default) vs uniform blue
//   chordpoly <0|1>      join the sounding notes into a polygon on the circles (1, default)
//   tracepath <0|1>      draw the trace as a chronological path on the circles (0, default)
//   plr <0|1>            draw P/L/R arrows from a sounding maj/min triad (Tonnetz only)
//   xfprev <0|1>         draw a transformation preview as ghost rings (does not touch MIDI)
//   xfmode <0|1>         preview mode: 0 transpose by `xpose`, 1 invert about `invc`
//   xpose <0..11>        semitones for the transpose preview
//   invc <0..11>         inversion centre (pitch class) for the invert preview
//   info <text ...>      set the footer analysis line (from pcsetinfo.js)
//   refresh              force a resize check + redraw
//
// Outlet 0 (back into the patch, to keep the Preset menu and the a/b/c numboxes in sync):
//   abc <a> <b> <c>      emitted when a preset is picked -> drives the a/b/c numboxes
//   presetsel <i>        emitted when a/b/c equals a preset -> selects it in the menu

autowatch = 1;
inlets = 1;
outlets = 1;   // back to the patch: `abc a b c` (from a preset pick) and `presetsel <i>`

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var SELF = this;   // captured so helper functions can reach .patcher / .box reliably

// ---- palette -------------------------------------------------------------------------
// sidebrain.net/relative-keys colours a circle of fifths as an HSL wheel: hue advances one
// step per fifth. k = fifth index of the pitch class = (pc*7) mod 12; hue = k*30 deg.
// Tune PC_SAT / PC_LUM to taste; the table is rebuilt from them at load.
var PC_SAT = 0.62, PC_LUM = 0.55;
var PC_COLOR = [];       // PC_COLOR[pc] = [r,g,b] in 0..1
var PC_TEXT  = [];       // readable text colour for a filled node of that pc

function hsl2rgb(h, s, l) {
	h = ((h % 360) + 360) % 360 / 360;
	var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
	var p = 2 * l - q;
	function hue(t) {
		if (t < 0) t += 1; if (t > 1) t -= 1;
		if (t < 1 / 6) return p + (q - p) * 6 * t;
		if (t < 1 / 2) return q;
		if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
		return p;
	}
	return [hue(h + 1 / 3), hue(h), hue(h - 1 / 3)];
}
for (var _pc = 0; _pc < 12; _pc++) {
	var _k = (_pc * 7) % 12;
	var _c = hsl2rgb(_k * 30, PC_SAT, PC_LUM);
	PC_COLOR[_pc] = _c;
	PC_TEXT[_pc] = (0.299 * _c[0] + 0.587 * _c[1] + 0.114 * _c[2]) > 0.62
		? [0.1, 0.1, 0.1, 1] : [1, 1, 1, 1];
}

// fixed-look palette (used when colors == 0, and for chrome)
var BG        = [0.14, 0.14, 0.14, 1];
var PANEL_BG  = [0.135, 0.135, 0.145, 1];
var FRAME     = [0.30, 0.30, 0.32, 1];
var COL_IDLE  = [0.42, 0.42, 0.42, 1];
var COL_TEXT_IDLE   = [0.68, 0.68, 0.68, 1];
var COL_ACTIVE      = [0.594, 0.72, 0.928, 1];
var COL_TEXT_ACTIVE = [0.10, 0.10, 0.10, 1];
var COL_TRACE  = [0.72, 0.58, 0.16, 1];
var COL_HARM   = [0.32, 0.68, 0.36, 1];
var COL_EDGE   = [0.33, 0.33, 0.33, 1];
var COL_FACE   = [0.594, 0.72, 0.928, 0.16];
var COL_POLY   = [0.92, 0.92, 0.95, 0.9];
var COL_POLY_F = [0.92, 0.92, 0.95, 0.08];
var COL_INFO   = [0.62, 0.66, 0.72, 1];
var COL_GHOST  = [0.87, 0.42, 0.92, 1];   // transformation-preview ghost (magenta)

var NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
var FIFTHS = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5];
var CHROM  = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];

// piano
var WHITE_PC   = [0, 2, 4, 5, 7, 9, 11];       // pitch classes of the white keys, in order
var BLACK_PC   = [1, 3, 6, 8, 10];
var BLACK_AFTER = [0, 1, 3, 4, 5];             // black key j sits after white index BLACK_AFTER[j]
var KEY_WHITE  = [0.90, 0.90, 0.90, 1];
var KEY_BLACK  = [0.12, 0.12, 0.13, 1];

// guitar -- open-string MIDI notes low->high; order MUST match the Tuning menu in build_tonnetz.py
var TUNINGS = [
	[40, 45, 50, 55, 59, 64],   // 0 Estandar  E A D G B E
	[38, 45, 50, 55, 59, 64],   // 1 Drop D
	[38, 45, 50, 55, 57, 62],   // 2 DADGAD
	[28, 33, 38, 43],           // 3 Bajo 4    E A D G
	[23, 28, 33, 38, 43],       // 4 Bajo 5    B E A D G
	[43, 48, 52, 57]            // 5 Ukelele   G C E A (drawn linear)
];
var INLAY = [3, 5, 7, 9, 15, 17, 19, 21];

// abc = HexaChord's interval-class label for the triangle's three edges. Realised as two
// directed lattice axes: x-step = a semitones, y-step = a+b semitones; the third edge is b.
// Classic Tonnetz [3,4,5]: x = minor third, y = fifth (7 -> ic 5), diagonal = major third.
var PRESETS = [
	[3, 4, 5], [1, 1, 10], [2, 2, 8], [1, 4, 7], [2, 3, 7],
	[1, 2, 9], [3, 3, 6], [4, 4, 4], [1, 5, 6], [2, 5, 5]
];

// ---- state -----------------------------------------------------------------------------
var voices = [];         // voices[pc]  = held notes of that pitch class
var midiVoices = [];     // midiVoices[n] = held notes of that exact MIDI note (0..127)
var activeSet = [];
var traceQ = [];

// eight independent panel flags: Tonnetz, chromatic, fifths, voice-leading, piano, guitar,
// diatonic Tonnetz, 3-D (Gollin) Tonnetz. Whatever is on is packed into an auto-grid by paint().
var viewOn   = [1, 1, 1, 0, 0, 0, 0, 0];
var VIEW_KIND = ['tonnetz', 'chrom', 'fifths', 'vl', 'piano', 'guitar', 'diat', 'tet'];

// item E: Gollin's 3-D Tonnetz K[a,b,c,d]. Each preset is a 4-note chord's cyclic interval
// structure (sums to 12); the three lattice axes are its cumulative sums a, a+b, a+b+c.
// MUST match TET_PRESET_NAMES in build_tonnetz.py.
var TET_PRESETS = [
	[2, 3, 3, 4],   // 0  dominant 7th / half-diminished (Forte 4-27)
	[3, 4, 3, 2],   // 1  minor 7th (4-26)
	[4, 3, 4, 1],   // 2  major 7th (4-20)
	[3, 3, 3, 3],   // 3  diminished 7th (4-28)
	[3, 4, 4, 1],   // 4  minor-major 7th (4-19)
	[2, 2, 4, 4]    // 5  augmented 7th / 7#5 (4-24)
];
var tetAbc = [2, 3, 3, 4];
var curAbc   = [3, 4, 5];
var lastPresetSel = 0;   // which PRESETS row abc currently equals (-1 = none); guards the sync loop
var keyRoot  = 0;        // diatonic panel tonic (pitch class)
var keyMinor = 0;        // 0 major, 1 natural minor
var tzDiat   = 0;        // set by paintTonnetz while it draws the diatonic panel; pcAt() reads it
var MAJ_SCALE = [0, 2, 4, 5, 7, 9, 11];
var MIN_SCALE = [0, 2, 3, 5, 7, 8, 10];
var vlClass  = "";       // current set-class prime-form string (from pcsetinfo `setclass`)
var vlQ      = [];        // recent matched trichord primes, for the path
var spacing  = 46;
var traceOn = 1, traceLen = 8;
var harmOn  = 1;
var facesOn = 1;
var labelsOn = 1;
var colorsOn = 1;
var chordPolyOn = 1;
var tracePathOn = 0;
var regTraceOn = 0;      // path of lattice regions (v7)
var segs = [];           // recent pc-set segments: {set:[pcs], t:ms}
var fitAbc = null;       // most-compact interval vector from tonnetzfit.js
var autoFitOn = 0;
var plrOn = 0;           // neo-Riemannian P/L/R arrows on the Tonnetz
var xfPrevOn = 0;        // transformation-preview ghost
var xfMode = 0;          // 0 transpose by xposeN, 1 invert about invcN
var xposeN = 0;
var invcN = 0;
var ghostSet = [];       // preview pitch classes (rebuilt each paint; empty when off)
var infoText = "";
var pianoMode = 0;       // 0 one octave, 1 full MIDI range
var guitarMode = 0;      // 0 all positions of active pcs, 1 exact sounding notes only
var tuningIdx = 0;
var fretCount = 22;
var zoomF = 1;
var panF = 0.5;

for (var i = 0; i < 12; i++) voices[i] = 0;
for (var i = 0; i < 128; i++) midiVoices[i] = 0;

// ---- window follow -------------------------------------------------------------------
// The jsui box is left oversized; we draw only within the floating window's real size, read
// from the subpatcher's Wind. Also try to match the box rect to it (harmless if read-only).
var BOX_PAD_X = 8;     // must match the jsui box x in build_tonnetz.py
var BOX_TOP   = 152;   // five-row control strip reserved at the top of the window (match build_tonnetz.py jsui y)

function windSize() {
	try {
		var s = SELF.patcher.wind.size;
		if (s && s[0] > 60 && s[1] > 60) return s;
	} catch (e) {}
	return null;
}
function viewportWH() {
	var s = windSize(), w, h;
	if (s) { w = s[0] - BOX_PAD_X * 2; h = s[1] - BOX_TOP - 8; }
	else { var b = box.rect; w = b[2] - b[0]; h = b[3] - b[1]; }
	return [Math.max(120, w), Math.max(90, h)];
}
function fitToWindow() {
	var s = windSize();
	if (!s) return;
	var r = [BOX_PAD_X, BOX_TOP, s[0] - BOX_PAD_X, s[1] - 8];
	try {
		var b = box.rect;
		if (b[0] != r[0] || b[1] != r[1] || b[2] != r[2] || b[3] != r[3]) {
			try { box.rect = r; } catch (e2) {}
			mgraphics.redraw();
		}
	} catch (e) {}
}
var _fit = new Task(fitToWindow, SELF);
_fit.interval = 250;
_fit.repeat();

function refresh() { fitToWindow(); mgraphics.redraw(); }

// ---- helpers -------------------------------------------------------------------------
function mod12(n) { return ((n % 12) + 12) % 12; }
function isActive(pc) { return activeSet.indexOf(pc) >= 0; }
function inTrace(pc)  { return traceOn && traceQ.indexOf(pc) >= 0; }
function label(pc)    { return labelsOn ? NOTE_NAMES[pc] : String(pc); }

function rebuildActive() {
	activeSet = [];
	for (var pc = 0; pc < 12; pc++) if (voices[pc] > 0) activeSet.push(pc);
}
function pushTrace(pc) {
	var k = traceQ.indexOf(pc);
	if (k >= 0) traceQ.splice(k, 1);
	traceQ.push(pc);
	while (traceQ.length > traceLen) traceQ.shift();
}
// a fresh pc-set opens a new trajectory segment (Fig. 8's segmentation rule)
function pushSeg() {
	var s = activeSet.slice().sort(function (a, b) { return a - b; });
	if (s.length === 0) return;
	if (segs.length && segs[segs.length - 1].set.join(",") === s.join(",")) return;
	segs.push({ set: s, t: (new Date()).getTime() });
	while (segs.length > traceLen) segs.shift();
}
// diatonic scale degree -> pitch class in the current key
function scalePc(deg) {
	var sc = keyMinor ? MIN_SCALE : MAJ_SCALE;
	deg = ((deg % 7) + 7) % 7;
	return mod12(keyRoot + sc[deg]);
}
// axes: chromatic uses curAbc (semitones); diatonic uses a fixed stack of diatonic thirds
// (2 scale steps per x, 4 per y) so triangles are diatonic triads.
function axX() { return tzDiat ? 2 : curAbc[0]; }
function axY() { return tzDiat ? 4 : curAbc[0] + curAbc[1]; }
function pcAt(p, q) { return tzDiat ? scalePc(p * 2 + q * 4) : mod12(p * axX() + q * axY()); }

// ---- message handlers ---------------------------------------------------------------
function note(pitch, vel) {
	var n = Math.round(pitch);
	var pc = mod12(n);
	if (vel > 0) {
		if (voices[pc] === 0) pushTrace(pc);
		voices[pc]++;
		if (n >= 0 && n < 128) midiVoices[n]++;
	} else {
		if (voices[pc] > 0) voices[pc]--;
		if (n >= 0 && n < 128 && midiVoices[n] > 0) midiVoices[n]--;
	}
	rebuildActive();
	pushSeg();
	mgraphics.redraw();
}
function activeNotes() {
	var a = [];
	for (var n = 0; n < 128; n++) if (midiVoices[n] > 0) a.push(n);
	return a;
}
function list() {
	activeSet = [];
	var a = arrayfromargs(arguments);
	for (var i = 0; i < a.length; i++) {
		var pc = mod12(Math.round(a[i]));
		if (activeSet.indexOf(pc) < 0) activeSet.push(pc);
	}
	pushSeg();
	mgraphics.redraw();
}
function msg_int(v) { list(v); }
function msg_float(v) { list(v); }
function clear() {
	for (var i = 0; i < 12; i++) voices[i] = 0;
	for (var j = 0; j < 128; j++) midiVoices[j] = 0;
	activeSet = []; traceQ = []; segs = [];
	mgraphics.redraw();
}
function setViewFlag(i, v) { viewOn[i] = v ? 1 : 0; mgraphics.redraw(); }
function vton(v) { setViewFlag(0, v); }
function vchr(v) { setViewFlag(1, v); }
function vfif(v) { setViewFlag(2, v); }
function vvoc(v) { setViewFlag(3, v); }
function vpno(v) { setViewFlag(4, v); }
function vgtr(v) { setViewFlag(5, v); }
function vdia(v) { setViewFlag(6, v); }
function vtet(v) { setViewFlag(7, v); }
function tetpreset(i) {
	i = Math.round(i);
	if (i >= 0 && i < TET_PRESETS.length) { tetAbc = TET_PRESETS[i].slice(); mgraphics.redraw(); }
}
function keyroot(v) { keyRoot = mod12(Math.round(v)); mgraphics.redraw(); }
function keymode(v) { keyMinor = v ? 1 : 0; mgraphics.redraw(); }
function setclass() {
	var s = arrayfromargs(arguments).join(" ");
	if (s !== vlClass) {
		vlClass = s;
		for (var i = 0; i < VL_NODES.length; i++) {
			if (VL_NODES[i][0] === s) {
				if (vlQ.length === 0 || vlQ[vlQ.length - 1] !== s) {
					vlQ.push(s);
					while (vlQ.length > 8) vlQ.shift();
				}
				break;
			}
		}
	}
	mgraphics.redraw();
}
function pianomode(v) { pianoMode = v ? 1 : 0; mgraphics.redraw(); }
function guitarmode(v) { guitarMode = v ? 1 : 0; mgraphics.redraw(); }
function tuning(v) { tuningIdx = Math.max(0, Math.min(TUNINGS.length - 1, Math.round(v))); mgraphics.redraw(); }
function frets(v) { fretCount = Math.max(12, Math.min(24, Math.round(v))); mgraphics.redraw(); }
function zoom(v) { zoomF = Math.max(1, Math.min(8, v)); mgraphics.redraw(); }
function pan(v) { panF = Math.max(0, Math.min(1, v)); mgraphics.redraw(); }
// abc <- the a/b/c numboxes. If the vector matches a preset, tell the menu to follow (once).
function abc(a, b, c) {
	curAbc = [Math.max(1, Math.round(a)), Math.max(1, Math.round(b)), Math.max(1, Math.round(c))];
	var idx = -1;
	for (var i = 0; i < PRESETS.length; i++)
		if (PRESETS[i][0] === curAbc[0] && PRESETS[i][1] === curAbc[1] && PRESETS[i][2] === curAbc[2]) { idx = i; break; }
	if (idx >= 0 && idx !== lastPresetSel) {
		lastPresetSel = idx;
		outlet(0, "presetsel", idx);
	} else if (idx < 0) {
		lastPresetSel = -1;
	}
	mgraphics.redraw();
}
// preset <- the menu. Push the vector out to the a/b/c numboxes so the two always agree.
function preset(i) {
	i = Math.round(i);
	if (i >= 0 && i < PRESETS.length) {
		curAbc = PRESETS[i].slice();
		lastPresetSel = i;
		outlet(0, "abc", curAbc[0], curAbc[1], curAbc[2]);
		mgraphics.redraw();
	}
}
function radius(v) { spacing = Math.max(24, Math.min(120, v)); mgraphics.redraw(); }
function trace(v) { traceOn = v ? 1 : 0; mgraphics.redraw(); }
function tracelen(v) {
	traceLen = Math.max(1, Math.min(24, Math.round(v)));
	while (traceQ.length > traceLen) traceQ.shift();
	mgraphics.redraw();
}
function harm(v) { harmOn = v ? 1 : 0; mgraphics.redraw(); }
function faces(v) { facesOn = v ? 1 : 0; mgraphics.redraw(); }
function labels(v) { labelsOn = v ? 1 : 0; mgraphics.redraw(); }
function colors(v) { colorsOn = v ? 1 : 0; mgraphics.redraw(); }
function chordpoly(v) { chordPolyOn = v ? 1 : 0; mgraphics.redraw(); }
function tracepath(v) { tracePathOn = v ? 1 : 0; mgraphics.redraw(); }
function regtrace(v) { regTraceOn = v ? 1 : 0; mgraphics.redraw(); }
function bestfit(a, b, c) {
	fitAbc = [Math.round(a), Math.round(b), Math.round(c)];
	if (autoFitOn) curAbc = fitAbc.slice();
	mgraphics.redraw();
}
function autofit(v) {
	autoFitOn = v ? 1 : 0;
	if (autoFitOn && fitAbc) curAbc = fitAbc.slice();
	mgraphics.redraw();
}
function plr(v) { plrOn = v ? 1 : 0; mgraphics.redraw(); }
function xfprev(v) { xfPrevOn = v ? 1 : 0; mgraphics.redraw(); }
function xfmode(v) { xfMode = v ? 1 : 0; mgraphics.redraw(); }
function xpose(v) { xposeN = Math.max(0, Math.min(11, Math.round(v))); mgraphics.redraw(); }
function invc(v) { invcN = Math.max(0, Math.min(11, Math.round(v))); mgraphics.redraw(); }
function info() { infoText = arrayfromargs(arguments).join(" "); mgraphics.redraw(); }

// item G: pitch classes the preview would produce -- transpose (eq. 4) or invert (eq. 5).
function computeGhost() {
	ghostSet = [];
	if (!xfPrevOn) return;
	for (var i = 0; i < activeSet.length; i++) {
		var g = xfMode ? mod12(invcN - activeSet[i]) : mod12(activeSet[i] + xposeN);
		if (ghostSet.indexOf(g) < 0) ghostSet.push(g);
	}
}

// ---- painting ---------------------------------------------------------------------
function paint() {
	var wh = viewportWH();
	var W = wh[0], H = wh[1];
	var footer = 22;
	var cH = H - footer;
	computeGhost();

	mgraphics.set_source_rgba(BG);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();

	var active = [];
	for (var vi = 0; vi < viewOn.length; vi++) if (viewOn[vi]) active.push(vi);

	if (active.length === 0) {
		mgraphics.set_source_rgba(COL_TEXT_IDLE);
		mgraphics.select_font_face("Arial");
		mgraphics.set_font_size(12);
		mgraphics.move_to(16, cH / 2);
		mgraphics.show_text("Sin vistas -- enciende una arriba");
	} else {
		// auto-grid: near-square; a short last row keeps the common cell width and is
		// centred (rather than one panel stretching across the whole width).
		var nA = active.length;
		var cols = Math.ceil(Math.sqrt(nA));
		var rows = Math.ceil(nA / cols);
		var cellW = W / cols;
		var cellH = cH / rows;
		var k = 0;
		for (var gr = 0; gr < rows; gr++) {
			var inRow = (gr < rows - 1) ? cols : (nA - cols * (rows - 1));
			var xoff = (W - inRow * cellW) / 2;
			for (var gc = 0; gc < inRow; gc++) {
				panel({ x: xoff + gc * cellW, y: gr * cellH, w: cellW, h: cellH }, VIEW_KIND[active[k]]);
				k++;
			}
		}
	}

	// footer: set-class info
	mgraphics.set_source_rgba(PANEL_BG);
	mgraphics.rectangle(0, cH, W, footer);
	mgraphics.fill();
	if (infoText.length) {
		mgraphics.set_source_rgba(COL_INFO);
		mgraphics.select_font_face("Arial");
		mgraphics.set_font_size(11);
		mgraphics.move_to(8, cH + 15);
		mgraphics.show_text(infoText);
	}
}

// one framed panel, dispatched by kind string (see VIEW_KIND)
function panel(r, kind) {
	mgraphics.set_source_rgba(PANEL_BG);
	mgraphics.rectangle(r.x + 1, r.y + 1, r.w - 2, r.h - 2);
	mgraphics.fill();

	if (kind === 'tonnetz') paintTonnetz(r, 0);
	else if (kind === 'diat') paintTonnetz(r, 1);
	else if (kind === 'piano') paintPiano(r);
	else if (kind === 'guitar') paintGuitar(r);
	else if (kind === 'vl') paintVL(r);
	else if (kind === 'tet') paintTet(r);
	else if (kind === 'fifths') paintCircle(r, FIFTHS, "Quintas");
	else paintCircle(r, CHROM, "Cromatico");

	mgraphics.set_source_rgba(FRAME);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(r.x + 0.5, r.y + 0.5, r.w - 1, r.h - 1);
	mgraphics.stroke();
}

function nodeFill(pc) { return colorsOn ? PC_COLOR[pc].concat(1) : COL_ACTIVE; }
function nodeText(pc) { return colorsOn ? PC_TEXT[pc] : COL_TEXT_ACTIVE; }

// ---- generalized Tonnetz ---------------------------------------------------------
var G = { cx: 0, cy: 0, S: 46, r: null };
function sx(p, q) { return G.cx + p * G.S + q * G.S * 0.5; }
function sy(p, q) { return G.cy - q * G.S * 0.8660254; }
function inRect(x, y) {
	return x > G.r.x - G.S * 0.5 && x < G.r.x + G.r.w + G.S * 0.5 &&
	       y > G.r.y - G.S * 0.5 && y < G.r.y + G.r.h + G.S * 0.5;
}
function harmNeighbours() {
	var out = [];
	if (!harmOn) return out;
	var steps = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, -1], [-1, 1]];
	for (var a = 0; a < activeSet.length; a++)
		for (var s = 0; s < steps.length; s++) {
			var npc = mod12(activeSet[a] + steps[s][0] * axX() + steps[s][1] * axY());
			if (activeSet.indexOf(npc) < 0 && out.indexOf(npc) < 0) out.push(npc);
		}
	return out;
}
function triFace(p, q, tri) {
	for (var i = 0; i < 3; i++) if (!isActive(pcAt(p + tri[i][0], q + tri[i][1]))) return;
	mgraphics.move_to(sx(p + tri[0][0], q + tri[0][1]), sy(p + tri[0][0], q + tri[0][1]));
	mgraphics.line_to(sx(p + tri[1][0], q + tri[1][1]), sy(p + tri[1][0], q + tri[1][1]));
	mgraphics.line_to(sx(p + tri[2][0], q + tri[2][1]), sy(p + tri[2][0], q + tri[2][1]));
	mgraphics.close_path();
	mgraphics.fill();
}
function edge(p0, q0, p1, q1) {
	mgraphics.move_to(sx(p0, q0), sy(p0, q0));
	mgraphics.line_to(sx(p1, q1), sy(p1, q1));
	mgraphics.stroke();
}
function paintTonnetz(r, diatonic) {
	tzDiat = diatonic ? 1 : 0;
	G.cx = r.x + r.w / 2; G.cy = r.y + r.h / 2; G.S = spacing; G.r = r;
	var S = spacing, p, q;
	var pMax = Math.min(26, Math.ceil(r.w / S) + 2);
	var qMax = Math.min(26, Math.ceil(r.h / (S * 0.8660254)) + 2);
	var harmSet = tzDiat ? [] : harmNeighbours();

	if (facesOn && activeSet.length >= 3) {
		mgraphics.set_source_rgba(COL_FACE);
		for (p = -pMax; p <= pMax; p++)
			for (q = -qMax; q <= qMax; q++) {
				triFace(p, q, [[0, 0], [1, 0], [0, 1]]);
				triFace(p, q, [[1, 0], [0, 1], [1, 1]]);
			}
	}

	mgraphics.set_source_rgba(COL_EDGE);
	mgraphics.set_line_width(1);
	for (p = -pMax; p <= pMax; p++)
		for (q = -qMax; q <= qMax; q++) {
			if (!inRect(sx(p, q), sy(p, q))) continue;
			edge(p, q, p + 1, q); edge(p, q, p, q + 1); edge(p, q, p + 1, q - 1);
		}

	// item A: the chord's 1-simplices -- any lattice edge with both endpoints sounding
	if (facesOn && activeSet.length >= 2) {
		mgraphics.set_source_rgba(COL_POLY);
		mgraphics.set_line_width(2.5);
		for (p = -pMax; p <= pMax; p++)
			for (q = -qMax; q <= qMax; q++) {
				if (!inRect(sx(p, q), sy(p, q)) || !isActive(pcAt(p, q))) continue;
				if (isActive(pcAt(p + 1, q)))     edge(p, q, p + 1, q);
				if (isActive(pcAt(p, q + 1)))     edge(p, q, p, q + 1);
				if (isActive(pcAt(p + 1, q - 1))) edge(p, q, p + 1, q - 1);
			}
	}

	mgraphics.select_font_face("Arial Bold");
	mgraphics.set_font_size(10);
	var rad = Math.max(9, Math.min(15, S * 0.28));
	for (p = -pMax; p <= pMax; p++)
		for (q = -qMax; q <= qMax; q++) {
			var x = sx(p, q), y = sy(p, q);
			if (!inRect(x, y)) continue;
			drawNode(x, y, rad, pcAt(p, q), harmSet.indexOf(pcAt(p, q)) >= 0);
		}

	if (regTraceOn && !tzDiat) paintRegionTrace(pMax, qMax);
	if (plrOn && !tzDiat) paintPLR(pMax, qMax);

	mgraphics.set_source_rgba(COL_TEXT_IDLE);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(10);
	mgraphics.move_to(r.x + 8, r.y + 15);
	mgraphics.show_text(tzDiat
		? ("Diatonico  " + NOTE_NAMES[keyRoot] + (keyMinor ? " menor" : " mayor"))
		: "Tonnetz");
	if (fitAbc && !tzDiat) {
		mgraphics.set_source_rgba(COL_INFO);
		mgraphics.set_font_size(9);
		mgraphics.move_to(r.x + 8, r.y + r.h - 8);
		mgraphics.show_text("ajuste  " + fitAbc.join(" ") + (autoFitOn ? "  (auto)" : ""));
	}
	tzDiat = 0;
}

// v7: the trajectory as a path of lattice regions. Each segment is anchored to the
// triangle (>=3 notes), edge (2) or vertex (1) closest to the previous anchor -- the paper's
// "small movements" criterion -- and the chain is drawn faded oldest -> newest.
function anchorFor(set, prev, pMax, qMax) {
	var tris = [[[0, 0], [1, 0], [0, 1]], [[1, 0], [0, 1], [1, 1]]];
	var best = null, bestD = 1e18;
	function consider(poly) {
		var cx = 0, cy = 0, k;
		for (k = 0; k < poly.length; k++) { cx += poly[k][0]; cy += poly[k][1]; }
		cx /= poly.length; cy /= poly.length;
		var d = prev ? (cx - prev[0]) * (cx - prev[0]) + (cy - prev[1]) * (cy - prev[1])
		             : (cx - G.cx) * (cx - G.cx) + (cy - G.cy) * (cy - G.cy);
		if (d < bestD) { bestD = d; best = { cx: cx, cy: cy, poly: poly }; }
	}
	var p, q;
	if (set.length >= 3) {
		for (p = -pMax; p <= pMax; p++)
			for (q = -qMax; q <= qMax; q++)
				for (var t = 0; t < 2; t++) {
					var V = tris[t], ok = true, poly = [];
					for (var v = 0; v < 3; v++) {
						if (set.indexOf(pcAt(p + V[v][0], q + V[v][1])) < 0) { ok = false; break; }
						poly.push([sx(p + V[v][0], q + V[v][1]), sy(p + V[v][0], q + V[v][1])]);
					}
					if (ok) consider(poly);
				}
		if (best) return best;
	}
	if (set.length >= 2) {
		var dirs = [[1, 0], [0, 1], [1, -1]];
		for (p = -pMax; p <= pMax; p++)
			for (q = -qMax; q <= qMax; q++) {
				if (set.indexOf(pcAt(p, q)) < 0) continue;
				for (var e = 0; e < 3; e++) {
					if (set.indexOf(pcAt(p + dirs[e][0], q + dirs[e][1])) < 0) continue;
					consider([[sx(p, q), sy(p, q)],
					          [sx(p + dirs[e][0], q + dirs[e][1]), sy(p + dirs[e][0], q + dirs[e][1])]]);
				}
			}
		if (best) return best;
	}
	for (p = -pMax; p <= pMax; p++)
		for (q = -qMax; q <= qMax; q++)
			if (set.indexOf(pcAt(p, q)) >= 0) consider([[sx(p, q), sy(p, q)]]);
	return best;
}
function paintRegionTrace(pMax, qMax) {
	if (segs.length === 0) return;
	var prev = null, anchors = [], i;
	for (i = 0; i < segs.length; i++) {
		var a = anchorFor(segs[i].set, prev, pMax, qMax);
		anchors.push(a);
		if (a) prev = [a.cx, a.cy];
	}
	for (i = 0; i < anchors.length; i++) {
		var an = anchors[i];
		if (!an) continue;
		var age = (i + 1) / anchors.length;
		if (i > 0 && anchors[i - 1]) {
			mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], 0.12 + 0.55 * age);
			mgraphics.set_line_width(1.5);
			mgraphics.move_to(anchors[i - 1].cx, anchors[i - 1].cy);
			mgraphics.line_to(an.cx, an.cy);
			mgraphics.stroke();
		}
		mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], 0.08 + 0.30 * age);
		if (an.poly.length >= 3) {
			mgraphics.move_to(an.poly[0][0], an.poly[0][1]);
			for (var k = 1; k < an.poly.length; k++) mgraphics.line_to(an.poly[k][0], an.poly[k][1]);
			mgraphics.close_path();
			mgraphics.fill();
		} else if (an.poly.length === 2) {
			mgraphics.set_line_width(3);
			mgraphics.move_to(an.poly[0][0], an.poly[0][1]);
			mgraphics.line_to(an.poly[1][0], an.poly[1][1]);
			mgraphics.stroke();
		} else {
			mgraphics.ellipse(an.cx - 3, an.cy - 3, 6, 6);
			mgraphics.fill();
		}
	}
}

// voice-leading space: the twelve trichord set-classes, hand-placed by parsimonious
// proximity (HexaChord's third representation, after Tymoczko 2011). Keys are Rahn prime
// forms -- exactly what pcsetinfo.js sends in its `setclass` message.
var VL_NODES = [
	["0 1 2", 0.10, 0.24, "3-1"],  ["0 1 3", 0.24, 0.40, "3-2"],
	["0 1 4", 0.22, 0.66, "3-3"],  ["0 1 5", 0.20, 0.88, "3-4"],
	["0 1 6", 0.44, 0.90, "3-5"],  ["0 2 4", 0.46, 0.15, "3-6"],
	["0 2 5", 0.50, 0.48, "3-7"],  ["0 2 6", 0.64, 0.27, "3-8"],
	["0 2 7", 0.70, 0.60, "3-9"],  ["0 3 6", 0.80, 0.39, "3-10"],
	["0 3 7", 0.84, 0.70, "3-11"], ["0 4 8", 0.94, 0.52, "3-12"]
];
var VL_EDGES = [
	[0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [5, 6], [1, 7], [7, 5],
	[7, 8], [6, 8], [8, 9], [9, 10], [10, 11], [9, 7], [6, 4], [4, 8], [5, 3]
];
function paintVL(r) {
	mgraphics.set_source_rgba(COL_TEXT_IDLE);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(10);
	mgraphics.move_to(r.x + 8, r.y + 15);
	mgraphics.show_text("Conduccion de voces");

	var pad = 26;
	var x0 = r.x + pad, y0 = r.y + pad + 6;
	var w = r.w - pad * 2, h = r.h - pad * 2 - 6;
	if (w < 40 || h < 40) return;
	function px(i) { return x0 + VL_NODES[i][1] * w; }
	function py(i) { return y0 + VL_NODES[i][2] * h; }

	mgraphics.set_source_rgba(COL_EDGE);
	mgraphics.set_line_width(1);
	for (var e = 0; e < VL_EDGES.length; e++) {
		mgraphics.move_to(px(VL_EDGES[e][0]), py(VL_EDGES[e][0]));
		mgraphics.line_to(px(VL_EDGES[e][1]), py(VL_EDGES[e][1]));
		mgraphics.stroke();
	}

	if (vlQ.length >= 2) {
		var idxOf = {};
		for (var n = 0; n < VL_NODES.length; n++) idxOf[VL_NODES[n][0]] = n;
		mgraphics.set_line_width(2);
		for (var t = 1; t < vlQ.length; t++) {
			var ia = idxOf[vlQ[t - 1]], ib = idxOf[vlQ[t]];
			if (ia === undefined || ib === undefined) continue;
			var aa = 0.15 + 0.75 * (t / (vlQ.length - 1));
			mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], aa);
			mgraphics.move_to(px(ia), py(ia)); mgraphics.line_to(px(ib), py(ib)); mgraphics.stroke();
		}
	}

	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(8);
	var rad = Math.max(7, Math.min(15, Math.min(w, h) * 0.055));
	for (var i = 0; i < VL_NODES.length; i++) {
		var on = VL_NODES[i][0] === vlClass;
		mgraphics.ellipse(px(i) - rad, py(i) - rad, rad * 2, rad * 2);
		if (on) {
			mgraphics.set_source_rgba(COL_ACTIVE); mgraphics.fill();
		} else {
			mgraphics.set_source_rgba(PANEL_BG); mgraphics.fill_preserve();
			mgraphics.set_source_rgba(COL_IDLE); mgraphics.set_line_width(1); mgraphics.stroke();
		}
		var lab = VL_NODES[i][3];
		mgraphics.set_source_rgba(on ? COL_TEXT_ACTIVE : COL_TEXT_IDLE);
		mgraphics.move_to(px(i) - lab.length * 2.4, py(i) + 3);
		mgraphics.show_text(lab);
	}
}

// item B: neo-Riemannian P/L/R. From the sounding major or minor triad, draw an arrow to
// each of the three lattice triangles that share an edge with it, labelled by which pair of
// common tones the edge carries (root+fifth = P, third+fifth = L, root+third = R).
function triadInfo(set) {
	if (set.length !== 3) return null;
	var s = set.slice().sort(function (a, b) { return a - b; });
	for (var i = 0; i < 3; i++) {
		var r = s[i], b = s[(i + 1) % 3], c = s[(i + 2) % 3];
		var i1 = mod12(b - r), i2 = mod12(c - r);
		if ((i1 === 3 && i2 === 7) || (i1 === 4 && i2 === 7)) return { root: r, third: b, fifth: c };
	}
	return null;
}
function plrLabel(shared, ti) {
	function has(x) { return shared.indexOf(x) >= 0; }
	if (has(ti.root) && has(ti.fifth)) return "P";
	if (has(ti.third) && has(ti.fifth)) return "L";
	if (has(ti.root) && has(ti.third)) return "R";
	return "";
}
function paintPLR(pMax, qMax) {
	var ti = triadInfo(activeSet);
	if (!ti) return;
	var want = [ti.root, ti.third, ti.fifth];
	var tris = [[[0, 0], [1, 0], [0, 1]], [[1, 0], [0, 1], [1, 1]]];
	var found = null, bestD = 1e18;
	for (var p = -pMax; p <= pMax; p++)
		for (var q = -qMax; q <= qMax; q++)
			for (var t = 0; t < 2; t++) {
				var V = tris[t];
				var vx = [p + V[0][0], p + V[1][0], p + V[2][0]];
				var vy = [q + V[0][1], q + V[1][1], q + V[2][1]];
				if (want.indexOf(pcAt(vx[0], vy[0])) < 0 ||
				    want.indexOf(pcAt(vx[1], vy[1])) < 0 ||
				    want.indexOf(pcAt(vx[2], vy[2])) < 0) continue;
				var cx = (sx(vx[0], vy[0]) + sx(vx[1], vy[1]) + sx(vx[2], vy[2])) / 3;
				var cy = (sy(vx[0], vy[0]) + sy(vx[1], vy[1]) + sy(vx[2], vy[2])) / 3;
				var d = (cx - G.cx) * (cx - G.cx) + (cy - G.cy) * (cy - G.cy);
				if (d < bestD) { bestD = d; found = { vx: vx, vy: vy }; }
			}
	if (!found) return;
	var vx = found.vx, vy = found.vy;
	var scx = (sx(vx[0], vy[0]) + sx(vx[1], vy[1]) + sx(vx[2], vy[2])) / 3;
	var scy = (sy(vx[0], vy[0]) + sy(vx[1], vy[1]) + sy(vx[2], vy[2])) / 3;

	mgraphics.select_font_face("Arial Bold");
	mgraphics.set_font_size(11);
	for (var e = 0; e < 3; e++) {
		var a = e, b = (e + 1) % 3, cc = (e + 2) % 3;
		var nx = vx[a] + vx[b] - vx[cc], ny = vy[a] + vy[b] - vy[cc];   // reflect across edge
		var ncx = (sx(vx[a], vy[a]) + sx(vx[b], vy[b]) + sx(nx, ny)) / 3;
		var ncy = (sy(vx[a], vy[a]) + sy(vx[b], vy[b]) + sy(nx, ny)) / 3;
		var lbl = plrLabel([pcAt(vx[a], vy[a]), pcAt(vx[b], vy[b])], ti);
		mgraphics.set_source_rgba(COL_HARM);
		mgraphics.set_line_width(1.5);
		mgraphics.move_to(scx, scy);
		mgraphics.line_to(ncx, ncy);
		mgraphics.stroke();
		mgraphics.ellipse(ncx - 2.5, ncy - 2.5, 5, 5);
		mgraphics.fill();
		mgraphics.set_source_rgba(1, 1, 1, 1);
		mgraphics.move_to(ncx + 4, ncy - 4);
		mgraphics.show_text(lbl);
	}
}

// ---- Gollin's three-dimensional Tonnetz (item E) --------------------------------
// K[a,b,c,d]: 4-note chords (dominant seventh / half-diminished) as tetrahedra, drawn as a
// flat isometric projection of the cubic lattice. The three axes are the cumulative interval
// sums g1 = a, g2 = a+b, g3 = a+b+c, so a lattice cell's "up" tetrahedron
// {n, n+g1, n+g2, n+g3} and "down" tetrahedron fill the alternated cubic honeycomb; the
// octahedral gaps are non-chord regions and stay empty (paper Fig. 4b / 6b, p.12-14). No
// depth sort -- this is a lattice schematic, like the figures, not a shaded 3-D render.
function paintTet(r) {
	mgraphics.set_source_rgba(COL_TEXT_IDLE);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(10);
	mgraphics.move_to(r.x + 8, r.y + 15);
	mgraphics.show_text("Tonnetz 3D  K[" + tetAbc.join(" ") + "]");

	var g1 = tetAbc[0], g2 = tetAbc[0] + tetAbc[1], g3 = tetAbc[0] + tetAbc[1] + tetAbc[2];
	var S = Math.max(16, Math.min(54, spacing * 0.68));
	var COS = 0.8660254, SIN = 0.5;
	var cx = r.x + r.w / 2, cy = r.y + r.h / 2 + 6;
	var RG = Math.max(2, Math.min(3, Math.round(Math.min(r.w, r.h) / (S * 2))));

	function ix(i, j, k) { return cx + (i - k) * S * COS; }
	function iy(i, j, k) { return cy + (i + k) * S * SIN - j * S; }
	function tpc(i, j, k) { return mod12(i * g1 + j * g2 + k * g3); }
	function inR(x, y) {
		return x > r.x - S && x < r.x + r.w + S && y > r.y - S && y < r.y + r.h + S;
	}

	// 1-skeleton: the six edge directions within a tetrahedron cell
	var EDIRS = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, -1, 0], [1, 0, -1], [0, 1, -1]];
	mgraphics.set_source_rgba(COL_EDGE);
	mgraphics.set_line_width(1);
	var i, j, k;
	for (i = -RG; i <= RG; i++)
		for (j = -RG; j <= RG; j++)
			for (k = -RG; k <= RG; k++) {
				var x0 = ix(i, j, k), y0 = iy(i, j, k);
				var vis0 = inR(x0, y0);
				for (var e = 0; e < EDIRS.length; e++) {
					var d = EDIRS[e];
					var x1 = ix(i + d[0], j + d[1], k + d[2]), y1 = iy(i + d[0], j + d[1], k + d[2]);
					if (!vis0 && !inR(x1, y1)) continue;
					mgraphics.move_to(x0, y0);
					mgraphics.line_to(x1, y1);
					mgraphics.stroke();
				}
			}

	// filled tetrahedra: any cell whose four pitch classes all sound
	var UP = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]];
	var DN = [[1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]];
	var FACES = [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]];
	var filled = 0;   // a symmetric chord (dim7) spans hundreds of tetrahedra -- cap the fill
	function tryTet(bi, bj, bk, V) {
		if (filled >= 24) return;
		var xs = [], ys = [], v, anyVis = false;
		for (v = 0; v < 4; v++) {
			var I = bi + V[v][0], J = bj + V[v][1], K = bk + V[v][2];
			if (!isActive(tpc(I, J, K))) return;
			var px = ix(I, J, K), py = iy(I, J, K);
			if (inR(px, py)) anyVis = true;
			xs.push(px); ys.push(py);
		}
		if (!anyVis) return;
		var f;
		mgraphics.set_source_rgba(COL_FACE);
		for (f = 0; f < 4; f++) {
			mgraphics.move_to(xs[FACES[f][0]], ys[FACES[f][0]]);
			mgraphics.line_to(xs[FACES[f][1]], ys[FACES[f][1]]);
			mgraphics.line_to(xs[FACES[f][2]], ys[FACES[f][2]]);
			mgraphics.close_path();
			mgraphics.fill();
		}
		mgraphics.set_source_rgba(COL_POLY);
		mgraphics.set_line_width(1.5);
		for (f = 0; f < 4; f++) {
			mgraphics.move_to(xs[FACES[f][0]], ys[FACES[f][0]]);
			mgraphics.line_to(xs[FACES[f][1]], ys[FACES[f][1]]);
			mgraphics.line_to(xs[FACES[f][2]], ys[FACES[f][2]]);
			mgraphics.close_path();
			mgraphics.stroke();
		}
		filled++;
	}
	if (activeSet.length >= 4) {
		for (i = -RG; i <= RG; i++)
			for (j = -RG; j <= RG; j++)
				for (k = -RG; k <= RG; k++) { tryTet(i, j, k, UP); tryTet(i, j, k, DN); }
	}

	// vertices (drawNode gives colour / active swell / trace / ghost ring for free)
	mgraphics.select_font_face("Arial Bold");
	mgraphics.set_font_size(9);
	var rad = Math.max(7, Math.min(12, S * 0.30));
	for (i = -RG; i <= RG; i++)
		for (j = -RG; j <= RG; j++)
			for (k = -RG; k <= RG; k++) {
				var vx = ix(i, j, k), vy = iy(i, j, k);
				if (!inR(vx, vy)) continue;
				drawNode(vx, vy, rad, tpc(i, j, k), false);
			}
}

// ---- chromatic / fifths circle -------------------------------------------------
function paintCircle(r, order, title) {
	var cx = r.x + r.w / 2, cy = r.y + r.h / 2 + 6;
	var rad = Math.min(r.w, r.h) / 2 - 22;
	if (rad < 20) rad = 20;

	mgraphics.set_source_rgba(COL_TEXT_IDLE);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(10);
	mgraphics.move_to(r.x + 8, r.y + 15);
	mgraphics.show_text(title);

	function ptOf(pc) {
		var i = order.indexOf(pc);
		var ang = (Math.PI * 2 * i / 12) - Math.PI / 2;
		return [cx + rad * Math.cos(ang), cy + rad * Math.sin(ang)];
	}

	// chord polygon: sounding notes joined in circle order
	if (chordPolyOn && activeSet.length >= 2) {
		var pts = [];
		for (var a = 0; a < activeSet.length; a++) pts.push([order.indexOf(activeSet[a]), ptOf(activeSet[a])]);
		pts.sort(function (u, v) { return u[0] - v[0]; });
		mgraphics.set_line_width(1.5);
		mgraphics.move_to(pts[0][1][0], pts[0][1][1]);
		for (var k = 1; k < pts.length; k++) mgraphics.line_to(pts[k][1][0], pts[k][1][1]);
		mgraphics.close_path();
		mgraphics.set_source_rgba(COL_POLY_F); mgraphics.fill_preserve();
		mgraphics.set_source_rgba(COL_POLY); mgraphics.stroke();
	}

	// transformation-preview ghost polygon
	if (ghostSet.length >= 2) {
		var gp = [];
		for (var g = 0; g < ghostSet.length; g++) gp.push([order.indexOf(ghostSet[g]), ptOf(ghostSet[g])]);
		gp.sort(function (u, v) { return u[0] - v[0]; });
		mgraphics.set_line_width(1.5);
		mgraphics.move_to(gp[0][1][0], gp[0][1][1]);
		for (var gk = 1; gk < gp.length; gk++) mgraphics.line_to(gp[gk][1][0], gp[gk][1][1]);
		mgraphics.close_path();
		mgraphics.set_source_rgba(COL_GHOST[0], COL_GHOST[1], COL_GHOST[2], 0.5);
		mgraphics.stroke();
	}

	// trace path: chronological, fading old -> new
	if (tracePathOn && traceQ.length >= 2) {
		mgraphics.set_line_width(2);
		for (var t = 1; t < traceQ.length; t++) {
			var p0 = ptOf(traceQ[t - 1]), p1 = ptOf(traceQ[t]);
			var aa = 0.15 + 0.75 * (t / (traceQ.length - 1));
			mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], aa);
			mgraphics.move_to(p0[0], p0[1]); mgraphics.line_to(p1[0], p1[1]); mgraphics.stroke();
		}
		var last = ptOf(traceQ[traceQ.length - 1]);
		mgraphics.set_source_rgba(COL_TRACE[0], COL_TRACE[1], COL_TRACE[2], 1);
		mgraphics.ellipse(last[0] - 3, last[1] - 3, 6, 6); mgraphics.fill();
	}

	mgraphics.select_font_face("Arial Bold");
	mgraphics.set_font_size(10);
	var nr = Math.max(10, Math.min(15, rad * 0.26));
	for (var i = 0; i < 12; i++) {
		var pc = order[i];
		var pt = ptOf(pc);
		drawNode(pt[0], pt[1], nr, pc, false);
	}
}

// one lattice / circle vertex, coloured by its state
function drawNode(x, y, rad, pc, isHarm) {
	var rr = isActive(pc) ? rad * 1.15 : rad;   // item A: sounding vertices sit a bit proud
	mgraphics.set_line_width(1.5);
	mgraphics.ellipse(x - rr, y - rr, rr * 2, rr * 2);

	var textCol;
	if (isActive(pc)) {
		mgraphics.set_source_rgba(nodeFill(pc)); mgraphics.fill();
		textCol = nodeText(pc);
	} else if (inTrace(pc)) {
		if (colorsOn) { var c = PC_COLOR[pc]; mgraphics.set_source_rgba(c[0], c[1], c[2], 0.45); }
		else mgraphics.set_source_rgba(COL_TRACE);
		mgraphics.fill();
		textCol = colorsOn ? PC_TEXT[pc] : COL_TEXT_ACTIVE;
	} else if (isHarm) {
		mgraphics.set_source_rgba(colorsOn ? PC_COLOR[pc].concat(1) : COL_HARM);
		mgraphics.stroke();
		textCol = colorsOn ? PC_COLOR[pc].concat(1) : COL_HARM;
	} else {
		if (colorsOn) {
			var d = PC_COLOR[pc];
			mgraphics.set_source_rgba(d[0], d[1], d[2], 0.10); mgraphics.fill_preserve();
		}
		mgraphics.set_source_rgba(COL_IDLE); mgraphics.stroke();
		textCol = COL_TEXT_IDLE;
	}

	var s = label(pc);
	mgraphics.set_source_rgba(textCol);
	mgraphics.move_to(x - (s.length > 1 ? 8 : 4), y + 4);
	mgraphics.show_text(s);

	// item G: transformation-preview ghost ring
	if (ghostSet.length && !isActive(pc) && ghostSet.indexOf(pc) >= 0) {
		mgraphics.set_source_rgba(COL_GHOST);
		mgraphics.set_line_width(2);
		mgraphics.ellipse(x - rad - 3, y - rad - 3, (rad + 3) * 2, (rad + 3) * 2);
		mgraphics.stroke();
	}
}

// ---- piano keyboard ---------------------------------------------------------------
function keyFill(pc) { return colorsOn ? PC_COLOR[pc].concat(1) : COL_ACTIVE; }
function isWhitePc(pc) { return WHITE_PC.indexOf(pc) >= 0; }

// horizontal offset for content of width `total` inside a panel of width `w`:
// centred if it fits, panned by panF if it overflows.
function hOffset(total, w) {
	return total > w ? -(total - w) * panF : (w - total) / 2;
}

function drawKey(kx, ky, kw, kh, pc, on, traced, white) {
	mgraphics.rectangle(kx, ky, kw, kh);
	if (on) { mgraphics.set_source_rgba(keyFill(pc)); mgraphics.fill_preserve(); }
	else if (traced && colorsOn) {
		var c = PC_COLOR[pc];
		mgraphics.set_source_rgba(c[0], c[1], c[2], white ? 0.35 : 0.5);
		mgraphics.fill_preserve();
	} else {
		mgraphics.set_source_rgba(white ? KEY_WHITE : KEY_BLACK);
		mgraphics.fill_preserve();
	}
	mgraphics.set_source_rgba(FRAME);
	mgraphics.set_line_width(1);
	mgraphics.stroke();
	if (labelsOn && white && kw > 13) {
		mgraphics.set_source_rgba(on ? PC_TEXT[pc] : [0.42, 0.42, 0.45, 1]);
		mgraphics.select_font_face("Arial");
		mgraphics.set_font_size(8);
		mgraphics.move_to(kx + kw / 2 - 4, ky + kh - 5);
		mgraphics.show_text(NOTE_NAMES[pc]);
	}
}

function paintPiano(r) {
	mgraphics.set_source_rgba(COL_TEXT_IDLE);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(10);
	mgraphics.move_to(r.x + 8, r.y + 14);
	mgraphics.show_text(pianoMode ? "Piano  (completo)" : "Piano  (octava)");

	var pad = 6;
	var x0 = r.x + pad, y0 = r.y + 20;
	var w = r.w - pad * 2, h = r.h - 26;
	if (h < 20 || w < 40) return;
	var L = x0, R = x0 + w;

	if (pianoMode === 0) {
		var whiteW = (w / 7) * zoomF;
		var xoff = hOffset(whiteW * 7, w);
		var blackW = whiteW * 0.6, blackH = h * 0.62;
		for (var i = 0; i < 7; i++) {
			var wpc = WHITE_PC[i];
			var wx = x0 + xoff + i * whiteW;
			if (wx + whiteW < L || wx > R) continue;
			drawKey(wx, y0, Math.max(1, whiteW - 1), h, wpc, isActive(wpc), inTrace(wpc), true);
		}
		for (var j = 0; j < 5; j++) {
			var bpc = BLACK_PC[j];
			var bx = x0 + xoff + (BLACK_AFTER[j] + 1) * whiteW - blackW / 2;
			if (bx + blackW < L || bx > R) continue;
			drawKey(bx, y0, blackW, blackH, bpc, isActive(bpc), inTrace(bpc), false);
		}
		return;
	}

	// full MIDI 0..127
	var nW = 0;
	for (var n = 0; n < 128; n++) if (isWhitePc(mod12(n))) nW++;
	var wW = (w / nW) * zoomF;
	var off = hOffset(wW * nW, w);
	var bW = wW * 0.62, bH = h * 0.62;
	var an = activeNotes();
	function onNote(m) { return an.indexOf(m) >= 0; }

	var wi = 0;
	for (var n = 0; n < 128; n++) {
		if (!isWhitePc(mod12(n))) continue;
		var kx = x0 + off + wi * wW;
		wi++;
		if (kx + wW < L || kx > R) continue;
		drawKey(kx, y0, Math.max(1, wW - 1), h, mod12(n), onNote(n), false, true);
		if (labelsOn && mod12(n) === 0 && wW > 9) {
			mgraphics.set_source_rgba([0.46, 0.46, 0.52, 1]);
			mgraphics.select_font_face("Arial");
			mgraphics.set_font_size(7);
			mgraphics.move_to(kx + 1, y0 + h - 3);
			mgraphics.show_text("C" + (Math.floor(n / 12) - 1));
		}
	}
	wi = 0;
	for (var n = 0; n < 128; n++) {
		if (isWhitePc(mod12(n))) { wi++; continue; }
		var bx = x0 + off + wi * wW - bW / 2;
		if (bx + bW < L || bx > R) continue;
		drawKey(bx, y0, bW, bH, mod12(n), onNote(n), false, false);
	}
}

// ---- guitar fretboard ------------------------------------------------------------
function paintGuitar(r) {
	mgraphics.set_source_rgba(COL_TEXT_IDLE);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(10);
	mgraphics.move_to(r.x + 8, r.y + 14);
	mgraphics.show_text(guitarMode ? "Guitarra  (suena)" : "Guitarra  (repetidas)");

	var open = TUNINGS[tuningIdx] || TUNINGS[0];
	var nS = open.length;
	var N = fretCount;
	var padL = 24, padR = 8, padT = 22, padB = 16;
	var x0 = r.x + padL, y0 = r.y + padT;
	var w = r.w - padL - padR, h = r.h - padT - padB;
	if (h < 16 || w < 60 || nS < 2) return;
	var L = x0, R = x0 + w;

	var fretW = (w / (N + 1)) * zoomF;      // f=0 is the open-string column
	var off = fretW * (N + 1) > w ? -(fretW * (N + 1) - w) * panF : 0;
	var gap = h / (nS - 1);
	var an = activeNotes();

	function fretX(f) { return x0 + off + (f + 0.5) * fretW; }
	function wireX(f)  { return x0 + off + (f + 1) * fretW; }   // wire after fret f (f=0 = nut)
	function stringY(s) { return y0 + (nS - 1 - s) * gap; }     // low string at the bottom

	// inlays
	mgraphics.set_source_rgba([1, 1, 1, 0.06]);
	for (var d = 0; d < INLAY.length; d++) {
		if (INLAY[d] > N) break;
		var ix = fretX(INLAY[d]);
		if (ix < L || ix > R) continue;
		mgraphics.ellipse(ix - 5, y0 + h / 2 - 5, 10, 10); mgraphics.fill();
	}
	if (N >= 12) { var i12 = fretX(12); if (i12 >= L && i12 <= R) {
		mgraphics.ellipse(i12 - 5, y0 + h * 0.30 - 5, 10, 10); mgraphics.fill();
		mgraphics.ellipse(i12 - 5, y0 + h * 0.70 - 5, 10, 10); mgraphics.fill();
	} }

	// strings + fret wires
	mgraphics.set_source_rgba(COL_EDGE);
	for (var s = 0; s < nS; s++) {
		mgraphics.set_line_width(0.7 + s * 0.22);
		mgraphics.move_to(Math.max(L, x0 + off), stringY(s));
		mgraphics.line_to(Math.min(R, wireX(N)), stringY(s));
		mgraphics.stroke();
	}
	for (var f = 0; f <= N; f++) {
		var fx = wireX(f);
		if (fx < L - 2 || fx > R + 2) continue;
		mgraphics.set_line_width(f === 0 ? 3 : 1);
		mgraphics.set_source_rgba(f === 0 ? [0.6, 0.6, 0.62, 1] : COL_EDGE);
		mgraphics.move_to(fx, y0); mgraphics.line_to(fx, y0 + h); mgraphics.stroke();
	}

	// fret numbers
	mgraphics.set_source_rgba([0.5, 0.5, 0.54, 1]);
	mgraphics.select_font_face("Arial");
	mgraphics.set_font_size(8);
	for (var f = 3; f <= N; f += 2) {
		if (f % 2 === 0 && f !== 12) continue;
		var nx = fretX(f);
		if (nx < L || nx > R) continue;
		mgraphics.move_to(nx - (f > 9 ? 6 : 3), y0 + h + 12);
		mgraphics.show_text(String(f));
	}

	// notes
	var dr = Math.max(4, Math.min(11, Math.min(fretW, gap) * 0.34));
	mgraphics.select_font_face("Arial Bold");
	for (var s = 0; s < nS; s++) {
		for (var f = 0; f <= N; f++) {
			var pitch = open[s] + f;
			var pc = mod12(pitch);
			var on, traced = false;
			if (guitarMode) on = an.indexOf(pitch) >= 0;
			else { on = isActive(pc); traced = !on && inTrace(pc); }
			if (!on && !traced) continue;
			var gx = fretX(f), gy = stringY(s);
			if (gx < L - dr || gx > R + dr) continue;
			mgraphics.ellipse(gx - dr, gy - dr, dr * 2, dr * 2);
			if (on) { mgraphics.set_source_rgba(keyFill(pc)); mgraphics.fill(); }
			else {
				var c = colorsOn ? PC_COLOR[pc] : [COL_TRACE[0], COL_TRACE[1], COL_TRACE[2]];
				mgraphics.set_source_rgba(c[0], c[1], c[2], 0.4); mgraphics.fill();
			}
			if (labelsOn && dr >= 7) {
				var t = label(pc);
				mgraphics.set_source_rgba(on ? PC_TEXT[pc] : [0.85, 0.85, 0.85, 1]);
				mgraphics.set_font_size(8);
				mgraphics.move_to(gx - (t.length > 1 ? 6 : 3), gy + 3);
				mgraphics.show_text(t);
			}
		}
	}
}
