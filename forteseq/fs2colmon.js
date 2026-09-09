// fs2colmon.js -- jsui: the per-voice note monitor for FORTESEQ2, sat beside the tabs.
//
// One ROW per voice, five cells wide. The CENTRE cell is the note sounding now (biggest,
// brightest); the two to its left are the two it played just before; the two to its right are
// the next two the reading order will feed it. Each cell shows the note name plus a small
// octave digit, so two voices an octave apart read differently (they no longer collapse to
// one pitch class). A short flash lights ONLY the centre cell each time that voice actually
// sounds a note -- the "bang" the forteseqhub devices show.
//
// The forward pair can read blank: forteseq2.js only sends a note there while the current
// set and rotation are certain to survive that far -- at a chord change it stops guessing
// rather than show a note the harmony has already moved past.
//
// Fed by forteseq2.js outlet 3 (retired for years, reused here), wired straight into this
// jsui in FORTESEQ2.amxd -- it dispatches on the selector itself, no [route] in front:
//   colmon <v> <h2> <h1> <cur> <f1> <f2>  -- MIDI note numbers (register included), or -1 for
//                                            blank/silence. Debounced engine-side.
//   colvoices <n>                         -- NUM_VOICES changed; reshape.
//   colbang <v>                           -- voice v sounded; flash its centre cell.
//   color <0|1>                           -- the "Color" toggle in the panel.
//   clear                                 -- blank every cell.
//
// Colour is the shared circle-of-fifths wheel from pccolor.js (C = red, +30 deg per fifth),
// precomputed once into a 12-entry table -- colouring a cell is then a table lookup, so the
// toggle costs nothing on the hot path.

include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var MAXROWS = 8;          // the panel only has room for this many voice rows; extra voices fold off
var NCELLS = 5;
var NOWCOL = 2;           // centre cell = the note sounding now

var NN = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

var voices = 4;
var colorOn = 1;
var cells = [];           // cells[v] = [h2, h1, cur, f1, f2]  (MIDI note numbers, -1 = blank)
var pulse = [];           // pulse[v] = 0..1, decays after a colbang -- lights the centre cell
var i;
for (i = 0; i < MAXROWS; i++) { cells.push([-1, -1, -1, -1, -1]); pulse.push(0); }

// pc -> [r,g,b] once. sat/lum chosen to read on a dark panel and to match tonnetz/ANIMIDI.
var PC_RGB = [];
for (i = 0; i < 12; i++) {
	var c = pcToColor(i, { baseHue: 0, sat: 0.62, lum: 0.52 });
	PC_RGB.push([c.r, c.g, c.b]);
}

// --- inlet messages ----------------------------------------------------------------------

function colvoices(n) {
	n = Math.max(1, Math.min(MAXROWS, Math.round(n)));
	if (n === voices) return;
	voices = n;
	mgraphics.redraw();
}

function colmon() {
	var a = arrayfromargs(arguments);
	var v = Math.round(a[0]);
	if (!(v >= 0 && v < MAXROWS)) return;
	cells[v] = [noteOrSilent(a[1]), noteOrSilent(a[2]), noteOrSilent(a[3]), noteOrSilent(a[4]), noteOrSilent(a[5])];
	mgraphics.redraw();
}

function colbang(v) {
	v = Math.round(v);
	if (!(v >= 0 && v < MAXROWS)) return;
	pulse[v] = 1;
	mgraphics.redraw();
	startDecay();
}

function color(on) {
	colorOn = on ? 1 : 0;
	mgraphics.redraw();
}

function clear() {
	for (var k = 0; k < MAXROWS; k++) { cells[k] = [-1, -1, -1, -1, -1]; pulse[k] = 0; }
	mgraphics.redraw();
}

// forteseq2.js multiplexes the fs2horizon.js window feed onto this same outlet 3. This jsui
// dispatches on the selector, so name the ones it must ignore, or Max logs
// "fs2colmon: doesn't understand ..." once per tick.
function hpattern() {}
function hcursor() {}
function hist() {}
function hstatus() {}
function hshape() {}
function hshapecur() {}
function filtclear() {}   // el panel fs2setpick.js del popup viaja por el mismo outlet 3
function filtinfo() {}
function filtset() {}
function maskecho() {}

function bang() { mgraphics.redraw(); }   // loadbang safety

function noteOrSilent(x) {
	x = Math.round(x);
	return (isFinite(x) && x >= 0) ? x : -1;
}

// --- pulse decay -----------------------------------------------------------------------

var decayTask = null;
function startDecay() {
	if (decayTask) return;
	decayTask = new Task(tickDecay, this);
	decayTask.interval = 33;
	decayTask.repeat();
}
function tickDecay() {
	var any = 0;
	for (var k = 0; k < MAXROWS; k++) {
		if (pulse[k] > 0) {
			pulse[k] *= 0.72;
			if (pulse[k] < 0.03) pulse[k] = 0; else any = 1;
		}
	}
	mgraphics.redraw();
	if (!any && decayTask) { decayTask.cancel(); decayTask = null; }
}

// --- paint ---------------------------------------------------------------------------------

var FADE = [0.62, 0.82, 1.0, 0.82, 0.62];   // past/future read as solid, just a touch dimmer than centre

function paint() {
	var W = box.rect[2] - box.rect[0];
	var H = box.rect[3] - box.rect[1];

	mgraphics.set_source_rgba([0.11, 0.11, 0.12, 1]);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();
	mgraphics.select_font_face('Arial');

	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	// no gutter, no per-voice labels -- the coloured V1..V4 strip just to the left already
	// names these rows. fixed pitch so the rows still land on the voice strips: jsui box top
	// at device y33, header 14, then 24 px per row -> device y47/71/95/119.
	var headH = 14;
	var rowH = 24;
	var cellW = W / NCELLS;

	// header: a single right-pointing arrow -- reading order feeds notes left -> right
	// (two cells of past on the left, "now" in the centre, two of lookahead on the right).
	(function () {
		var ymid = headH * 0.5;
		var x0 = W * 0.38, x1 = W * 0.60;
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_line_width(1);
		mgraphics.move_to(x0, ymid);
		mgraphics.line_to(x1, ymid);
		mgraphics.stroke();
		mgraphics.move_to(x1 + 4, ymid);
		mgraphics.line_to(x1 - 2, ymid - 3);
		mgraphics.line_to(x1 - 2, ymid + 3);
		mgraphics.close_path();
		mgraphics.fill();
	})();

	for (var v = 0; v < nRows; v++) {
		var y = headH + v * rowH;

		for (var r = 0; r < NCELLS; r++) {
			var note = cells[v][r];
			var pc = note < 0 ? -1 : (((note % 12) + 12) % 12);
			var oct = note < 0 ? null : (Math.floor(note / 12) - 1);   // MIDI 60 = C4
			var x = r * cellW;
			var isCur = (r === NOWCOL);
			var fade = FADE[r];

			if (pc < 0) {
				mgraphics.set_source_rgba([0.155, 0.155, 0.165, 1]);
			} else if (colorOn) {
				var rgb = PC_RGB[pc];
				mgraphics.set_source_rgba([rgb[0] * fade, rgb[1] * fade, rgb[2] * fade, 1]);
			} else {
				var g = (isCur ? 0.42 : 0.30) * fade + 0.06;
				mgraphics.set_source_rgba([g, g, g, 1]);
			}
			var inset = isCur ? 0.5 : 1.5;
			mgraphics.rectangle(x + inset, y + inset, cellW - 2 * inset, rowH - 2 * inset);
			mgraphics.fill();

			if (isCur) {                          // centre cell gets a quiet outline even at rest
				mgraphics.set_source_rgba([0.5, 0.5, 0.55, 0.5]);
				mgraphics.set_line_width(1);
				mgraphics.rectangle(x + 0.5, y + 0.5, cellW - 1, rowH - 1);
				mgraphics.stroke();
			}

			if (pc >= 0) {
				var lum = colorOn ? (PC_RGB[pc][0] * 0.299 + PC_RGB[pc][1] * 0.587 + PC_RGB[pc][2] * 0.114) * fade : 0.3;
				mgraphics.set_source_rgba(lum > 0.55 ? [0, 0, 0, 1] : [0.95, 0.95, 0.95, 1]);
				// note name, centred
				mgraphics.set_font_size(isCur ? 11 : 8);
				var name = NN[pc];
				mgraphics.move_to(x + cellW / 2 - name.length * (isCur ? 3.2 : 2.4), y + rowH / 2 + (isCur ? 2 : 3));
				mgraphics.show_text(name);
				// octave digit, small, tucked into the top-right corner
				mgraphics.set_font_size(6.5);
				mgraphics.move_to(x + cellW - 6.5, y + 7);
				mgraphics.show_text(String(oct));
			}

			// bang flash: centre cell only, white overlay + outline, scaled by pulse
			if (isCur && pulse[v] > 0) {
				mgraphics.set_source_rgba([1, 1, 1, pulse[v] * 0.55]);
				mgraphics.rectangle(x + 0.5, y + 0.5, cellW - 1, rowH - 1);
				mgraphics.fill();
				mgraphics.set_source_rgba([1, 1, 1, pulse[v] * 0.95]);
				mgraphics.set_line_width(2);
				mgraphics.rectangle(x + 1, y + 1, cellW - 2, rowH - 2);
				mgraphics.stroke();
			}
		}

		if (v > 0) {
			mgraphics.set_source_rgba([0, 0, 0, 0.5]);
			mgraphics.set_line_width(1);
			mgraphics.move_to(0, y);
			mgraphics.line_to(W, y);
			mgraphics.stroke();
		}
	}
}
