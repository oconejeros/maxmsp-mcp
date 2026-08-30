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
// Messages:
//   note <pitch> <vel>   MIDI note; vel 0 = note-off. Ref-counted (per pitch class AND per
//                        MIDI note); a fresh pitch-class onset pushes the trace.
//   list <pc> ...        replace the active pitch-class set outright (no trace push)
//   clear                drop all active notes and the trace
//   view <0..5>          0 all (default) | 1 Tonnetz | 2 chromatic | 3 fifths | 4 piano | 5 guitar
//   space <0..2>         legacy alias -> view 1..3
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
//   tracelen <n>         how many onsets the trace remembers (1..24)
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

autowatch = 1;
inlets = 1;
outlets = 0;

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

var curView  = 0;        // 0 all, 1 tonnetz, 2 chromatic, 3 fifths, 4 piano, 5 guitar
                         // (state var kept apart from the view() handler -- a `var view` shadows it)
var curAbc   = [3, 4, 5];
var spacing  = 46;
var traceOn = 1, traceLen = 8;
var harmOn  = 1;
var facesOn = 1;
var labelsOn = 1;
var colorsOn = 1;
var chordPolyOn = 1;
var tracePathOn = 0;
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
var BOX_TOP   = 118;   // four-row control strip reserved at the top of the window

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
function axX() { return curAbc[0]; }
function axY() { return curAbc[0] + curAbc[1]; }
function pcAt(p, q) { return mod12(p * axX() + q * axY()); }

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
	mgraphics.redraw();
}
function msg_int(v) { list(v); }
function msg_float(v) { list(v); }
function clear() {
	for (var i = 0; i < 12; i++) voices[i] = 0;
	for (var j = 0; j < 128; j++) midiVoices[j] = 0;
	activeSet = []; traceQ = [];
	mgraphics.redraw();
}
function view(v) { curView = Math.max(0, Math.min(5, Math.round(v))); mgraphics.redraw(); }
function space(v) { curView = Math.max(0, Math.min(2, Math.round(v))) + 1; mgraphics.redraw(); }
function pianomode(v) { pianoMode = v ? 1 : 0; mgraphics.redraw(); }
function guitarmode(v) { guitarMode = v ? 1 : 0; mgraphics.redraw(); }
function tuning(v) { tuningIdx = Math.max(0, Math.min(TUNINGS.length - 1, Math.round(v))); mgraphics.redraw(); }
function frets(v) { fretCount = Math.max(12, Math.min(24, Math.round(v))); mgraphics.redraw(); }
function zoom(v) { zoomF = Math.max(1, Math.min(8, v)); mgraphics.redraw(); }
function pan(v) { panF = Math.max(0, Math.min(1, v)); mgraphics.redraw(); }
function abc(a, b, c) {
	curAbc = [Math.max(1, Math.round(a)), Math.max(1, Math.round(b)), Math.max(1, Math.round(c))];
	mgraphics.redraw();
}
function preset(i) {
	i = Math.round(i);
	if (i >= 0 && i < PRESETS.length) { curAbc = PRESETS[i].slice(); mgraphics.redraw(); }
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

	if (curView === 0) {
		var row1 = Math.round(cH * 0.46);
		var row2 = Math.round((cH - row1) / 2);
		var row3 = cH - row1 - row2;
		var cw = W / 3;
		panel({ x: 0,      y: 0, w: cw, h: row1 }, 1);
		panel({ x: cw,     y: 0, w: cw, h: row1 }, 2);
		panel({ x: cw * 2, y: 0, w: W - cw * 2, h: row1 }, 3);
		panel({ x: 0, y: row1, w: W, h: row2 }, 4);
		panel({ x: 0, y: row1 + row2, w: W, h: row3 }, 5);
	} else {
		panel({ x: 0, y: 0, w: W, h: cH }, curView);
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

// one framed panel: whichView 1=Tonnetz 2=chromatic 3=fifths 4=piano 5=guitar
function panel(r, whichView) {
	mgraphics.set_source_rgba(PANEL_BG);
	mgraphics.rectangle(r.x + 1, r.y + 1, r.w - 2, r.h - 2);
	mgraphics.fill();

	if (whichView === 1) paintTonnetz(r);
	else if (whichView === 4) paintPiano(r);
	else if (whichView === 5) paintGuitar(r);
	else paintCircle(r, whichView === 3 ? FIFTHS : CHROM,
		whichView === 3 ? "Quintas" : "Cromatico");

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
function paintTonnetz(r) {
	G.cx = r.x + r.w / 2; G.cy = r.y + r.h / 2; G.S = spacing; G.r = r;
	var S = spacing, p, q;
	var pMax = Math.min(26, Math.ceil(r.w / S) + 2);
	var qMax = Math.min(26, Math.ceil(r.h / (S * 0.8660254)) + 2);
	var harmSet = harmNeighbours();

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

	if (plrOn) paintPLR(pMax, qMax);
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
