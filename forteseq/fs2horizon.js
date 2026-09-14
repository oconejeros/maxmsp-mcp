// fs2horizon.js -- jsui: the "próximos pasos" panel for FORTESEQ2's floating window.
//
// One ROW per voice. Each row is:  [ history ]  [ pattern grid ]
//   history  -- up to HIST_MAX notes already played, dim, newest next to the grid. EXACT.
//   pattern  -- the reading order the sequencer is walking:
//       kind 1 (full cycle): the whole loop of the shape, cols = its length (Recto = n,
//               Modos = n·n, pendulum doubles it), capped at PATTERN_MAX. The playhead column
//               (from hcursor) is boxed. The loop content is stable, so this barely redraws.
//       kind 0 (rolling): Súper / SúperMín, or any cycle longer than the cap -- one pass is
//               hundreds of steps, so the grid is a rolling HORIZON_MAX-ahead window from the
//               live cursor, fading left→right, with a » marker meaning "the pattern is longer".
//   A short flash lights the playhead cell each time that voice sounds (the fs2colmon "bang").
//
// Fed by forteseq2.js outlet 3 (shared with fs2colmon.js -- both dispatch on the selector):
//   hpattern <v> <kind> <cols> <c0..>   -- MIDI notes, -1 = blank.
//   hcursor  <v> <pos>                  -- playhead column within the grid (0 in kind 0).
//   hist     <v> <h0..>                 -- up to HIST_MAX played notes, newest first.
//   hstatus  <readMode> <readDir> <setIdx1> <mode>  -- the config line at the bottom.
//   hshape   <n> <cols> <rawL> <d0..>  -- the STATIC reading-order strip: which degree index the
//            shape reads at each position of one full cycle (downsampled if rawL > cols). One
//            shared row under the grid. cols 0 = hide (chord mode). Sent only on shape change.
//   hshapecur <pos>  -- cursor column within that strip, one number per tick.
//   ornscale <count> <forte> <vec> <is12> <pc0..>  -- READ_ORNAMENT's resulting scale (Slonimsky's
//            Master Chord): the pitch-class aggregate of one ornament pass. count 0 = clear (any
//            other reading order). Drawn as a 12-chip strip + label above the status line.
//   vkey <v> <forte> <tonica> <keyOwn> <readOwn> <patron> <dir> <ornTipo> <muted>  -- everything
//            about what voice v is ACTUALLY doing right now, all resolved own-vs-shared exactly
//            like the audio path (voicePcsFor/voiceRootFor/voiceReadModeOf/voiceReadDirOf/
//            voiceOrnamentPitchAt): forte/tonica (its set+root), patron/dir (its reading order,
//            READ_NAMES/DIR_NAMES index), ornTipo (ORN_TYPE_NAMES index, -1 unless its effective
//            patron is Ornamento), muted (voiceMute[v]). keyOwn/readOwn (0/1) just say whether
//            that forte+tonica / patron+dir came from this voice's own override or the shared
//            globals -- drawn as a small label at the left of the row, under the "V<n>" tag this
//            file otherwise never printed (rows were previously told apart only by top-to-bottom
//            order). A muted row is drawn dimmed throughout, so a glance tells sounding voices
//            from silent ones.
//   colvoices <n>   colbang <v>   color <0|1>   clear   colmon ...(ignored)
//
// Colour = the circle-of-fifths wheel from pccolor.js, sat/lum matched to fs2colmon / tonnetz.

include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var SELF = this;   // capturado para .patcher.wind (seguir a la ventana flotante)

// Patron tonnetz.js / animidi.js: la caja jsui se deja SOBREDIMENSIONADA (add_fs2_setpick.py) y
// paint() pinta dentro de viewportWH() -- el tamano real de la ventana del subpatcher. NO se
// confia en escribir box.rect (de solo lectura en el popup M4L) -- fitToWindow() lo intenta igual
// como bonus inerte, pero el tamano/posicion real de la caja quedan fijos desde que la ventana
// abre, sea cual sea el valor que este archivo escriba.
//
// "Vista Popup" (tools/add_fs2_popup_tabs.py) hace a Horizonte y Selector EXCLUYENTES -- un
// "script show/hide" real sobre la caja del que no se ve, ya no una superposicion con margen
// reservado -- asi que este jsui ya no necesita reservarle espacio a nadie: cuando esta oculto,
// fs2setpick.js no dibuja nada encima.
var WPAD = 8;
function windSize() {
	try {
		var s = SELF.patcher.wind.size;
		if (s && s[0] > 60 && s[1] > 60) return s;
	} catch (e) {}
	return null;
}
function leftMargin() { return 0; }
function viewportWH() {
	var s = windSize();
	var margin = leftMargin();
	if (s) return [Math.max(300, Math.round(s[0]) - margin - WPAD * 2),
		Math.max(140, Math.round(s[1]) - WPAD * 2)];
	return [844, 284];   // sin lectura de ventana
}
function fitToWindow() {
	var s = windSize();
	if (!s) { mgraphics.redraw(); return; }
	var x0 = WPAD + leftMargin();
	var r = [x0, WPAD, Math.max(x0 + 200, Math.round(s[0]) - WPAD),
		Math.max(WPAD + 120, Math.round(s[1]) - WPAD)];
	try {
		var b = box.rect;
		if (b[0] != r[0] || b[1] != r[1] || b[2] != r[2] || b[3] != r[3]) { try { box.rect = r; } catch (e2) {} }
	} catch (e3) {}
	mgraphics.redraw();
}
var _fit = new Task(fitToWindow, SELF);
_fit.interval = 250;
_fit.repeat();
fitToWindow();
function onresize() { fitToWindow(); }

var MAXROWS = 16;
var HIST_MAX = 8;
var PATTERN_MAX = 48;

var NN = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
var READ_NAMES = ['Recto', 'Súper', 'SúperMín', 'Modos', 'Coprimo', 'Zigzag', 'Urna', 'Ornamento'];
var DIR_NAMES = ['adelante', 'atrás', 'alterna'];
var ORN_TYPE_NAMES = ['Interp', 'Infra', 'Ultra', 'Infra-Inter', 'Infra-Ultra', 'Inf-Int-Ult'];

var voices = 4;
var colorOn = 1;
var pat = [];            // pat[v] = { kind, cols, cells:[...] }
var cur = [];            // cur[v] = playhead column
var played = [];         // played[v] = [newest ... oldest]  (the `hist` message; array can't share the name)
var pulse = [];          // bang flash amount per row
var status = null;       // [readMode, readDir, setIdx1, mode] or null
var shape = null;        // { n, cols, rawL, degs:[...] } -- the static reading-order strip
var shapeCur = 0;        // cursor column within the shape strip
var vkeyInfo = [];       // vkeyInfo[v] = { forte, tonic, keyOwn, readOwn, patron, dir, ornT, muted } or null
var i;
for (i = 0; i < MAXROWS; i++) { pat.push({ kind: 1, cols: 0, cells: [] }); cur.push(0); played.push([]); pulse.push(0); vkeyInfo.push(null); }

var PC_RGB = [];         // pitch class -> colour (the note grid)
var DEG_RGB = [];        // degree index -> muted warm colour (the shape strip; deliberately unlike PC_RGB)
for (i = 0; i < 12; i++) {
	var c = pcToColor(i, { baseHue: 0, sat: 0.62, lum: 0.52 });
	PC_RGB.push([c.r, c.g, c.b]);
	var d = pcToColor(i, { baseHue: 35, sat: 0.28, lum: 0.60 });
	DEG_RGB.push([d.r, d.g, d.b]);
}

// --- inlet messages ----------------------------------------------------------------------

function hpattern() {
	var a = arrayfromargs(arguments);
	var v = Math.round(a[0]);
	if (!(v >= 0 && v < MAXROWS)) return;
	var kind = Math.round(a[1]);
	var cols = Math.max(0, Math.min(PATTERN_MAX, Math.round(a[2])));
	var cells = [];
	for (var k = 0; k < cols; k++) cells.push(noteOrBlank(a[3 + k]));
	pat[v] = { kind: kind, cols: cols, cells: cells };
	mgraphics.redraw();
}

function hcursor(v, pos) {
	v = Math.round(v);
	if (!(v >= 0 && v < MAXROWS)) return;
	cur[v] = Math.round(pos);
	mgraphics.redraw();
}

function hist() {
	var a = arrayfromargs(arguments);
	var v = Math.round(a[0]);
	if (!(v >= 0 && v < MAXROWS)) return;
	var h = [];
	for (var k = 1; k < a.length && k <= HIST_MAX; k++) h.push(noteOrBlank(a[k]));
	played[v] = h;
	mgraphics.redraw();
}

function colvoices(n) {
	n = Math.max(1, Math.min(MAXROWS, Math.round(n)));
	if (n === voices) return;
	voices = n;
	mgraphics.redraw();
}

function colbang(v) {
	v = Math.round(v);
	if (!(v >= 0 && v < MAXROWS)) return;
	pulse[v] = 1;
	mgraphics.redraw();
	startDecay();
}

function hstatus(rm, rd, setIdx1, md, lockedFlag) {
	status = [Math.round(rm), Math.round(rd), Math.round(setIdx1), Math.round(md), Math.round(lockedFlag || 0)];
	mgraphics.redraw();
}

function hshape() {
	var a = arrayfromargs(arguments);
	var n = Math.round(a[0]);
	var cols = Math.max(0, Math.round(a[1]));
	if (cols === 0) { shape = null; mgraphics.redraw(); return; }
	var rawL = Math.max(cols, Math.round(a[2]));
	var degs = [];
	for (var k = 0; k < cols; k++) degs.push(Math.round(a[3 + k]));
	shape = { n: n, cols: cols, rawL: rawL, degs: degs };
	mgraphics.redraw();
}

function hshapecur(pos) {
	shapeCur = Math.round(pos);
	mgraphics.redraw();
}

// READ_ORNAMENT's resulting scale (Slonimsky's Master Chord). null = not in Ornamento.
var ornScale = null;   // { forte, vec, is12, pcs:[...] }
function ornscale() {
	var a = arrayfromargs(arguments);
	var n = Math.round(a[0]);
	if (!(n > 0)) { ornScale = null; mgraphics.redraw(); return; }
	var pcs = [];
	for (var k = 0; k < n && (4 + k) < a.length; k++) pcs.push((((Math.round(a[4 + k]) % 12) + 12) % 12));
	ornScale = { forte: String(a[1]), vec: String(a[2]), is12: Math.round(a[3]) === 1, pcs: pcs };
	mgraphics.redraw();
}

// Everything about what voice v is ACTUALLY doing right now -- own key, own reading order, own
// ornament shape if applicable, whether it's muted. See the message doc at the top of this file.
// Sent under demand, debounced engine-side per voice.
function vkey(v, forte, tonic, keyOwn, readOwn, patron, dir, ornT, muted, keyLock) {
	v = Math.round(v);
	if (!(v >= 0 && v < MAXROWS)) return;
	vkeyInfo[v] = {
		forte: String(forte), tonic: String(tonic),
		keyOwn: !!Math.round(keyOwn), readOwn: !!Math.round(readOwn),
		patron: Math.round(patron), dir: Math.round(dir), ornT: Math.round(ornT),
		muted: !!Math.round(muted), keyLock: Math.round(keyLock === undefined ? -1 : keyLock)
	};
	mgraphics.redraw();
}

function color(on) {
	colorOn = on ? 1 : 0;
	mgraphics.redraw();
}

function clear() {
	for (var k = 0; k < MAXROWS; k++) { pat[k] = { kind: 1, cols: 0, cells: [] }; cur[k] = 0; played[k] = []; pulse[k] = 0; vkeyInfo[k] = null; }
	shape = null; shapeCur = 0; ornScale = null;
	mgraphics.redraw();
}

function colmon() {}   // the small strip's payload rides the same outlet; not ours
function filtclear() {}   // fs2setpick.js (piano de mascara + rejilla de sets) tambien va por outlet 3
function filtinfo() {}
function filtset() {}
function maskecho() {}

function bang() { mgraphics.redraw(); }   // loadbang safety

function noteOrBlank(x) {
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

function statusText() {
	if (!status) return '';
	var rm = READ_NAMES[status[0]] || ('modo ' + status[0]);
	var rd = DIR_NAMES[status[1]] || ('dir ' + status[1]);
	var md = status[3] === 0 ? 'Acordes' : 'Arpegio';
	var shp = '';
	var k = pat[0] || {};
	if (k.cols) shp = '   ·   ' + (k.kind === 1 ? ('ciclo ' + k.cols) : ('ventana ' + k.cols + ', patrón más largo'));
	if (shape && shape.cols) {
		shp += '   ·   forma ' + shape.rawL + (shape.rawL > shape.cols ? ' (submuestreada)' : '');
	}
	// El lock duro (fs2setpick.js) congela el setIndex COMPARTIDO para toda la ensamble -- afecta a
	// todas las voces por igual, asi que va una sola vez aca y no repetido en cada fila de vkey.
	if (status[4]) shp += '   ·   Fijado';
	return md + '   ·   ' + rm + '   ·   ' + rd + '   ·   Set ' + status[2] + shp;
}

function drawCell(x, y, w, h, note, dim, label) {
	var pc = note < 0 ? -1 : (((note % 12) + 12) % 12);
	if (pc < 0) {
		mgraphics.set_source_rgba([0.155, 0.155, 0.165, 1]);
	} else if (colorOn) {
		var rgb = PC_RGB[pc];
		mgraphics.set_source_rgba([rgb[0] * dim, rgb[1] * dim, rgb[2] * dim, 1]);
	} else {
		var g = 0.34 * dim + 0.06;
		mgraphics.set_source_rgba([g, g, g, 1]);
	}
	mgraphics.rectangle(x + 1, y + 1, w - 2, h - 2);
	mgraphics.fill();
	if (pc >= 0 && label && w >= 15) {
		var lum = colorOn
			? (PC_RGB[pc][0] * 0.299 + PC_RGB[pc][1] * 0.587 + PC_RGB[pc][2] * 0.114) * dim
			: 0.3;
		mgraphics.set_source_rgba(lum > 0.55 ? [0, 0, 0, 1] : [0.95, 0.95, 0.95, 1]);
		var name = NN[pc];
		mgraphics.set_font_size(w >= 26 ? 10 : 8);
		mgraphics.move_to(x + w / 2 - name.length * (w >= 26 ? 3.0 : 2.4), y + h / 2 + 3);
		mgraphics.show_text(name);
		if (w >= 24) {
			var oct = Math.floor(note / 12) - 1;   // MIDI 60 = C4
			mgraphics.set_font_size(6.5);
			mgraphics.move_to(x + w - 7, y + 8);
			mgraphics.show_text(String(oct));
		}
	}
}

function paint() {
	var wh = viewportWH();
	var W = wh[0], H = wh[1];
	mgraphics.translate(leftMargin(), 0);   // caja fija en x=8; esto es lo unico que se mueve

	mgraphics.set_source_rgba([0.11, 0.11, 0.12, 1]);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();
	mgraphics.select_font_face('Arial');

	var headH = 16;
	var statusH = status ? 15 : 0;
	var shapeH = (shape && shape.cols > 0) ? 34 : 0;   // the static reading-order strip
	var ornH = (ornScale && status && status[0] === 7) ? 22 : 0;   // READ_ORNAMENT resulting-scale strip
	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH);
	var rowH = gridH / nRows;

	var keyW = 150;   // left zone: "V<n>" + forte/tonica + patron/dir + orn tipo (vkey), all it has
	var histW = Math.round(Math.min((W - keyW) * 0.28, HIST_MAX * 22));   // played notes
	var histCW = histW / HIST_MAX;
	var gridX = keyW + histW + 4;
	var gridW = Math.max(1, W - gridX);

	// header ticks: a few 1-based indices across the grid, using row 0's column count
	var cols0 = (pat[0] && pat[0].cols) || 1;
	mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
	mgraphics.set_font_size(8);
	var nTicks = Math.min(6, cols0);
	for (var t = 0; t < nTicks; t++) {
		var ci = Math.round(t * (cols0 - 1) / Math.max(1, nTicks - 1));
		mgraphics.move_to(gridX + ci * (gridW / cols0) + 2, headH - 5);
		mgraphics.show_text(String(ci + 1));
	}
	mgraphics.set_source_rgba([0.45, 0.45, 0.5, 1]);
	mgraphics.set_font_size(8);
	mgraphics.move_to(keyW + 4, headH - 5);
	mgraphics.show_text('tocado');

	for (var v = 0; v < nRows; v++) {
		var y = headH + v * rowH;
		var P = pat[v] || { kind: 1, cols: 0, cells: [] };
		var hv = played[v] || [];

		// voice tag + everything vkey knows about it: its own key / reading order / ornament if it
		// has overrides, the shared ones otherwise. The only place any row in this popup is
		// labeled by voice number at all; previously only top-to-bottom order told them apart.
		// A muted voice is dimmed throughout its row -- categorically not sounding, so it should
		// read as visually "off" next to the ones that are.
		var vk = vkeyInfo[v];
		var rowDim = (vk && vk.muted) ? 0.35 : 1.0;
		var anyOwn = vk && (vk.keyOwn || vk.readOwn);

		// Font sizes scale with the room this row actually has (a tall window like this one should
		// use it) instead of staying pinned at the smallest legible size regardless of space.
		var fsV = Math.max(11, Math.min(18, rowH * 0.11));
		var fsInfo = Math.max(10, Math.min(14, rowH * 0.085));
		var lh = fsInfo + 6;

		mgraphics.set_source_rgba(anyOwn ? [1 * rowDim, 0.75 * rowDim, 0.3 * rowDim, 1] : [0.6 * rowDim, 0.6 * rowDim, 0.66 * rowDim, 1]);
		mgraphics.set_font_size(fsV);
		mgraphics.move_to(4, y + fsV + 2);
		mgraphics.show_text('V' + (v + 1) + (vk && vk.muted ? ' ·mute' : ''));
		if (vk && rowH >= 24) {
			mgraphics.set_font_size(fsInfo);
			mgraphics.set_source_rgba([0.68 * rowDim, 0.68 * rowDim, 0.74 * rowDim, 1]);
			var ky = y + fsV + lh;
			mgraphics.move_to(4, ky);
			// "*" ya marca TonProp (clave propia); "Fij" es la excepcion dentro de eso -- progresar
			// (avanzar con cada cambio de armonia) es el estado por defecto y no necesita marca,
			// solo la voz fijada (voiceKeyLock) la necesita.
			mgraphics.show_text(vk.forte + ' ' + vk.tonic + (vk.keyOwn ? ' *' : '') + (vk.keyLock === 1 ? ' ·Fij' : ''));
			if (rowH >= fsV + 2 * lh + 6) {
				ky += lh;
				var pname = READ_NAMES[vk.patron] || ('modo ' + vk.patron);
				var dsuf = vk.dir ? (' ' + (DIR_NAMES[vk.dir] || vk.dir)) : '';
				mgraphics.move_to(4, ky);
				mgraphics.show_text(pname + dsuf + (vk.readOwn ? ' *' : ''));
			}
			if (rowH >= fsV + 3 * lh + 6 && vk.ornT >= 0) {
				ky += lh;
				mgraphics.move_to(4, ky);
				mgraphics.show_text(ORN_TYPE_NAMES[vk.ornT] || ('orn ' + vk.ornT));
			}
		}

		// history: newest is hv[0], drawn nearest the grid (rightmost slot)
		for (var hslot = 0; hslot < HIST_MAX; hslot++) {
			var hidx = hslot;                       // 0..HIST_MAX-1, oldest slot on the left
			var age = HIST_MAX - 1 - hslot;         // -> hv index (older = higher)
			var note = (age < hv.length) ? hv[age] : -1;
			var dim = (0.40 + 0.15 * (hslot / (HIST_MAX - 1))) * rowDim;   // older = dimmer
			drawCell(keyW + hidx * histCW, y, histCW, rowH, note, dim, histCW >= 20);
		}

		// pattern grid
		var cols = P.cols || 0;
		var cellW = cols > 0 ? gridW / cols : gridW;
		for (var p = 0; p < cols; p++) {
			var n = P.cells[p];
			var x = gridX + p * cellW;
			var dim2 = ((P.kind === 1) ? 1.0 : (1.0 - (p / Math.max(1, cols - 1)) * 0.45)) * rowDim;
			drawCell(x, y, cellW, rowH, n, dim2, true);
			// playhead box (full-cycle mode)
			if (P.kind === 1 && p === (((cur[v] % cols) + cols) % cols)) {
				var flash = pulse[v] > 0 ? pulse[v] : 0;
				mgraphics.set_source_rgba([1, 1, 1, 0.85 + 0.15 * flash]);
				mgraphics.set_line_width(2);
				mgraphics.rectangle(x + 1, y + 1.5, cellW - 2, rowH - 3);
				mgraphics.stroke();
			}
		}

		// rolling mode: left-edge "next" bar + right-edge "longer than this" marker
		if (P.kind === 0 && cols > 0) {
			mgraphics.set_source_rgba([0.62, 0.62, 0.68, 0.9 + 0.1 * (pulse[v] || 0)]);
			mgraphics.rectangle(gridX, y + 1, 2, rowH - 2);
			mgraphics.fill();
			mgraphics.set_source_rgba([0.55, 0.55, 0.6, 1]);
			mgraphics.set_font_size(11);
			mgraphics.move_to(W - 12, y + rowH / 2 + 4);
			mgraphics.show_text('»');
		}

		// bang flash on the playhead cell
		if (pulse[v] > 0 && cols > 0) {
			var pc0 = (P.kind === 1) ? (((cur[v] % cols) + cols) % cols) : 0;
			var fx = gridX + pc0 * cellW;
			mgraphics.set_source_rgba([1, 1, 1, pulse[v] * 0.5]);
			mgraphics.rectangle(fx + 1, y + 1, cellW - 2, rowH - 2);
			mgraphics.fill();
		}

		if (v > 0) {
			mgraphics.set_source_rgba([0, 0, 0, 0.5]);
			mgraphics.set_line_width(1);
			mgraphics.move_to(0, y);
			mgraphics.line_to(W, y);
			mgraphics.stroke();
		}
	}

	// separator between history zone and grid
	mgraphics.set_source_rgba([0, 0, 0, 0.6]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(gridX - 2, headH);
	mgraphics.line_to(gridX - 2, headH + gridH);
	mgraphics.stroke();

	// --- the static "forma" strip: how the reading order walks the shape, cell by cell -------
	if (shapeH) {
		var sy = headH + gridH + 10;         // gap above holds the pointer
		var sh = shapeH - 12;
		var sc = shape.cols;
		var scw = W / sc;
		var scur = (((shapeCur % sc) + sc) % sc);
		for (var s = 0; s < sc; s++) {
			var deg = shape.degs[s];
			var dpc = ((deg % 12) + 12) % 12;
			var rgb = DEG_RGB[dpc];
			// dim strongly away from the cursor: past = a visible trail, future = darker
			var lit = (s === scur) ? 1.0 : (s < scur ? 0.68 : 0.42);
			mgraphics.set_source_rgba([rgb[0] * lit, rgb[1] * lit, rgb[2] * lit, 1]);
			mgraphics.rectangle(s * scw + 0.5, sy, Math.max(1, scw - 1), sh);
			mgraphics.fill();
			if (scw >= 14) {
				mgraphics.set_source_rgba([0.06, 0.06, 0.06, 1]);
				mgraphics.set_font_size(scw >= 20 ? 9 : 7);
				mgraphics.move_to(s * scw + scw / 2 - 3, sy + sh / 2 + 3);
				mgraphics.show_text(String(deg));
			}
		}
		// playhead: a bright bar through the cursor cell, taller than the strip, + a triangle above
		var cx = scur * scw;
		var cw = Math.max(2, scw);
		mgraphics.set_source_rgba([1, 0.95, 0.4, 0.28]);           // soft glow on the cell
		mgraphics.rectangle(cx, sy - 2, cw, sh + 4);
		mgraphics.fill();
		mgraphics.set_source_rgba([1, 0.95, 0.4, 1]);              // bright outline
		mgraphics.set_line_width(2);
		mgraphics.rectangle(cx + 1, sy - 2, Math.max(1, cw - 2), sh + 4);
		mgraphics.stroke();
		var tx = cx + cw / 2;                                       // downward triangle in the gap
		mgraphics.move_to(tx - 5, sy - 10);
		mgraphics.line_to(tx + 5, sy - 10);
		mgraphics.line_to(tx, sy - 3);
		mgraphics.close_path();
		mgraphics.fill();
		// label + position readout
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(4, sy - 3);
		mgraphics.show_text('forma  ' + (scur + 1) + '/' + shape.rawL);
	}

	// --- the resulting-scale strip: Slonimsky's Master Chord for the running ornament ----------
	if (ornH) {
		var oy = headH + gridH + shapeH;
		mgraphics.set_source_rgba([0.09, 0.09, 0.10, 1]);
		mgraphics.rectangle(0, oy, W, ornH);
		mgraphics.fill();
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(4, oy + ornH / 2 + 3);
		mgraphics.show_text('escala');
		var ocw = Math.max(4, Math.min(20, (W - 220) / 12));
		var ox = 40;
		for (var oi = 0; oi < 12; oi++) {
			var lit = ornScale.pcs.indexOf(oi) >= 0;
			if (lit && colorOn) {
				var org = PC_RGB[oi];
				mgraphics.set_source_rgba([org[0], org[1], org[2], 1]);
			} else if (lit) {
				mgraphics.set_source_rgba([0.72, 0.72, 0.74, 1]);
			} else {
				mgraphics.set_source_rgba([0.17, 0.17, 0.18, 1]);
			}
			mgraphics.rectangle(ox + oi * ocw + 1, oy + 4, ocw - 2, ornH - 8);
			mgraphics.fill();
		}
		mgraphics.set_source_rgba([0.68, 0.68, 0.72, 1]);
		mgraphics.set_font_size(9);
		mgraphics.move_to(ox + 12 * ocw + 10, oy + ornH / 2 + 3);
		mgraphics.show_text(ornScale.forte + '   ' + ornScale.vec + (ornScale.is12 ? '   [12 tonos]' : ''));
	}

	if (statusH) {
		var sy = H - statusH;
		mgraphics.set_source_rgba([0.09, 0.09, 0.10, 1]);
		mgraphics.rectangle(0, sy, W, statusH);
		mgraphics.fill();
		mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
		mgraphics.set_font_size(9);
		mgraphics.move_to(4, sy + statusH - 4);
		mgraphics.show_text(statusText());
	}
}
