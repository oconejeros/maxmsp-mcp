// fs2setpick.js -- jsui: el panel IZQUIERDO del popup "Proximos 16" de FORTESEQ2.
//
// Dos zonas apiladas en un canvas de ~380 x 284:
//
//   ARRIBA  -- piano cromatico de una octava (7 blancas + 5 negras), cada tecla tenida por el
//              color de circulo de quintas de pccolor.js. Click en una tecla la incluye/excluye
//              de la mascara cromatica de 12 celdas del motor (C = slot 0, absoluta). Cada cambio
//              manda  setmask <12 ints>  +  setfilter 1  al motor. Un renglon bajo el teclado
//              lista las notas elegidas + conteo. mode/fit/k y el rango de cardinalidad se dejan
//              a la pestana Filtro -- este panel no los toca.
//
//   ABAJO   -- rejilla de swatches, uno por cada pitch-class set que PASA el filtro actual,
//              pintado con harmonyToColor(). Click en un swatch fija ese set (lock duro):
//              setlockindex <idx1>  +  setlock 1. El swatch elegido queda contorneado; el pie
//              muestra el nombre Forte del swatch bajo el puntero. Si pasan mas de FILT_MAX,
//              se pagina con los botones < >.
//
// Entra por outlet 3 de forteseq2.js (compartido con fs2horizon.js / fs2colmon.js -- se
// despacha por el selector, sin [route]):
//   filtclear                                  -- vacia la rejilla.
//   filtinfo  <total> <shown>                  -- shown = min(total, 64).
//   filtset   <slot> <idx1> <forte> <pc...>    -- un set permitido; pc ya transpuesto por effRoot.
//   maskecho  <m0..m11>                        -- mascara real del motor; el panel la adopta.
//   color <0|1>  clear  bang                   -- toggle Color Monitor / limpiar / loadbang.
// (todos los selectores de horizon/colmon llegan igual y se ignoran aqui.)
//
// Sale por outlet 0 -> outlet del subpatcher -> js forteseq2.js inlet 0:
//   setmask <12 ints>   setfilter 1   setlockindex <idx1>   setlock 1
//
// idiom jsui del repo: fs2colmon.js (tabla PC_RGB), tonnetz.js (piano de una octava),
// midirouter_grid.js (hit-test de teclas).

include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var SELF = this;   // capturado para que los helpers alcancen .patcher / .box

var NN = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
var WHITE_PC = [0, 2, 4, 5, 7, 9, 11];
var BLACK_PC = [1, 3, 6, 8, 10];
var BLACK_AFTER = [0, 1, 3, 4, 5];   // la negra j se sienta tras la blanca de indice BLACK_AFTER[j]
var COLOR_OPTS = { baseHue: 0, sat: 0.62, lum: 0.52 };   // igual que fs2colmon / tonnetz / horizonte

var PC_RGB = [], PC_TEXT = [];
for (var _i = 0; _i < 12; _i++) {
	var _c = pcToColor(_i, COLOR_OPTS);
	PC_RGB.push([_c.r, _c.g, _c.b]);
	var _lum = _c.r * 0.299 + _c.g * 0.587 + _c.b * 0.114;
	PC_TEXT.push(_lum > 0.55 ? [0, 0, 0, 1] : [0.95, 0.95, 0.95, 1]);
}

// --- estado --------------------------------------------------------------------------------

var maskArr = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1];   // mascara cromatica, C = slot 0, absoluta
var colorOn = 1;
var filtSets = [];        // filtSets[slot] = { idx1, forte, pcs:[...], rgb:[r,g,b] }
var filtTotal = 0;        // cuantos pasan en total
var filtShown = 0;        // cuantos se enviaron (<= FILT_MAX)
var page = 0;
var selIdx = -1;          // idx1 del swatch fijado (-1 = ninguno)
var forteOfSel = '';      // nombre Forte del set fijado, para el pie cuando no hay hover
var hoverForte = '';      // nombre Forte bajo el puntero
var geo = null;           // rects del ultimo paint(), para hit-testing coherente

// --- seguir a la ventana flotante -----------------------------------------------------
// Patron tonnetz.js / animidi.js: la caja jsui se deja SOBREDIMENSIONADA (add_fs2_setpick.py)
// y NO se confia en escribir box.rect (a menudo es de solo lectura en el popup M4L). paint()
// pinta dentro de viewportWH(), derivado de la ventana real del subpatcher; lo que se dibuja
// fuera queda fuera de la ventana. El panel izquierdo tiene ANCHO FIJO (PANEL_W); fs2horizon.js
// ocupa el resto -- su x de arranque (HZ_X = PAD + PANEL_W + GAP) coincide alla y en el tool.
var PAD = 8, PANEL_W = 380, GAP = 8;
function windSize() {
	try {
		var s = SELF.patcher.wind.size;
		if (s && s[0] > 60 && s[1] > 60) return s;
	} catch (e) {}
	return null;
}
function viewportWH() {
	var s = windSize();
	if (s) return [PANEL_W, Math.max(160, Math.round(s[1]) - PAD * 2)];
	return [PANEL_W, 284];   // sin lectura de ventana: el tamano fijo de siempre
}
function fitToWindow() {
	// intento de calzar la caja tambien (inofensivo si es de solo lectura); paint() no depende de esto
	var s = windSize();
	if (!s) { mgraphics.redraw(); return; }
	var r = [PAD, PAD, PAD + PANEL_W, Math.max(PAD + 160, Math.round(s[1]) - PAD)];
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

// --- entrada: mensajes por selector en inlet 0 ------------------------------------------

function filtclear() {
	filtSets = [];
	filtTotal = 0;
	filtShown = 0;
	page = 0;
	scheduleRedraw();
}

function filtinfo(total, shown) {
	filtTotal = Math.max(0, Math.round(total));
	filtShown = Math.max(0, Math.round(shown));
	// si el filtro se estrecho, la pagina actual puede quedar fuera de rango
	scheduleRedraw();
}

function filtset() {
	var a = arrayfromargs(arguments);
	if (a.length < 4) return;
	var slot = Math.round(a[0]);
	if (!(slot >= 0 && slot < 4096)) return;
	var pcs = [];
	for (var k = 3; k < a.length; k++) {
		var p = Math.round(a[k]);
		if (isFinite(p)) pcs.push(((p % 12) + 12) % 12);
	}
	var rgb;
	if (pcs.length) {
		var c = harmonyToColor(pcs, COLOR_OPTS, 'oklab');
		rgb = [c.r, c.g, c.b];
	} else {
		rgb = [0.5, 0.5, 0.5];
	}
	filtSets[slot] = { idx1: Math.round(a[1]), forte: String(a[2]), pcs: pcs, rgb: rgb };
	if (selIdx >= 0 && filtSets[slot].idx1 === selIdx) forteOfSel = filtSets[slot].forte;
	scheduleRedraw();
}

function maskecho() {
	var a = arrayfromargs(arguments);
	for (var k = 0; k < 12 && k < a.length; k++) maskArr[k] = a[k] ? 1 : 0;
	mgraphics.redraw();
}

function color(on) {
	colorOn = on ? 1 : 0;
	mgraphics.redraw();
}

function clear() {
	filtclear();   // deja maskArr intacta; solo vacia la rejilla
}

function bang() { mgraphics.redraw(); }   // loadbang safety

// Estos viajan por el mismo outlet 3 (feed del horizonte / monitor de columnas). No son nuestros.
function hpattern() {}
function hcursor() {}
function hist() {}
function hstatus() {}
function hshape() {}
function hshapecur() {}
function colvoices() {}
function colbang() {}
function colmon() {}

// --- repintado coalescido ---------------------------------------------------------------
// filtset llega ~64 veces en una misma pasada del scheduler; un Task a schedule(0) las junta
// en un solo redraw.
var redrawTask = null;
function scheduleRedraw() {
	if (redrawTask) return;
	redrawTask = new Task(function () { redrawTask = null; mgraphics.redraw(); });
	redrawTask.schedule(0);
}

// --- salida ---------------------------------------------------------------------------------

function emitMask() {
	var m = [];
	for (var k = 0; k < 12; k++) m.push(maskArr[k]);
	outlet(0, ['setmask'].concat(m));
	outlet(0, ['setfilter', 1]);
}

// --- interaccion --------------------------------------------------------------------------

function onresize() { fitToWindow(); mgraphics.redraw(); }

function ptIn(r, x, y) {
	return r && x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h;
}

// x,y relativos al origen de las teclas. Negras primero (tapan a las blancas), luego blancas.
function keyAt(x, y, w, ph) {
	var ww = w / 7;
	var bw = ww * 0.6, bh = ph * 0.62;
	for (var j = 0; j < 5; j++) {
		var bx = (BLACK_AFTER[j] + 1) * ww - bw / 2;
		if (x >= bx && x <= bx + bw && y >= 0 && y <= bh) return BLACK_PC[j];
	}
	if (x < 0 || x > w || y < 0 || y > ph) return -1;
	var wi = Math.floor(x / ww);
	if (wi < 0) wi = 0;
	if (wi > 6) wi = 6;
	return WHITE_PC[wi];
}

function swatchAt(x, y) {
	if (!geo || !ptIn(geo.grid, x, y)) return -1;
	var col = Math.floor((x - geo.grid.x) / geo.cw);
	var row = Math.floor((y - geo.grid.y) / geo.ch);
	if (col < 0 || col >= geo.cols || row < 0) return -1;
	var gi = page * geo.pageSize + row * geo.cols + col;
	if (gi < 0 || gi >= filtShown) return -1;
	return gi;
}

function pageCount() {
	if (!geo || geo.pageSize <= 0) return 1;
	return Math.max(1, Math.ceil(filtShown / geo.pageSize));
}

function onclick(x, y, but) {
	if (!but || !geo) return;

	if (ptIn(geo.keys, x, y)) {
		var pc = keyAt(x - geo.keys.x, y - geo.keys.y, geo.keys.w, geo.keys.h);
		if (pc >= 0) { maskArr[pc] ^= 1; emitMask(); mgraphics.redraw(); }
		return;
	}
	if (ptIn(geo.prevBtn, x, y)) {
		if (page > 0) { page--; mgraphics.redraw(); }
		return;
	}
	if (ptIn(geo.nextBtn, x, y)) {
		if (page < pageCount() - 1) { page++; mgraphics.redraw(); }
		return;
	}
	var gi = swatchAt(x, y);
	if (gi >= 0 && filtSets[gi]) {
		selIdx = filtSets[gi].idx1;
		forteOfSel = filtSets[gi].forte;
		outlet(0, ['setlockindex', selIdx]);
		outlet(0, ['setlock', 1]);
		mgraphics.redraw();
	}
}

function onidle(x, y) {
	var f = '';
	var gi = swatchAt(x, y);
	if (gi >= 0 && filtSets[gi]) f = filtSets[gi].forte;
	if (f !== hoverForte) { hoverForte = f; mgraphics.redraw(); }
}

function onidleout() {
	if (hoverForte !== '') { hoverForte = ''; mgraphics.redraw(); }
}

// --- dibujo ------------------------------------------------------------------------------

function selectedNames() {
	var out = [];
	for (var k = 0; k < 12; k++) if (maskArr[k]) out.push(NN[k]);
	return out;
}

function drawPiano(pz) {
	// titulo
	mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
	mgraphics.select_font_face('Arial');
	mgraphics.set_font_size(10);
	mgraphics.move_to(pz.x + 2, pz.y + 11);
	mgraphics.show_text('Mascara cromatica');

	var keys = geo.keys;
	var ww = keys.w / 7;
	var bw = ww * 0.6, bh = keys.h * 0.62;

	// blancas
	for (var wi = 0; wi < 7; wi++) {
		var pc = WHITE_PC[wi];
		var kx = keys.x + wi * ww;
		fillKey(kx, keys.y, ww, keys.h, pc, maskArr[pc], false);
	}
	// negras encima
	for (var j = 0; j < 5; j++) {
		var bpc = BLACK_PC[j];
		var bx = keys.x + (BLACK_AFTER[j] + 1) * ww - bw / 2;
		fillKey(bx, keys.y, bw, bh, bpc, maskArr[bpc], true);
	}

	// renglon de notas elegidas
	var names = selectedNames();
	mgraphics.set_source_rgba([0.55, 0.55, 0.6, 1]);
	mgraphics.set_font_size(9);
	mgraphics.move_to(pz.x + 2, pz.y + pz.h - 5);
	mgraphics.show_text((names.length ? names.join(' ') : '(vacia)') + '   (' + names.length + ')');
}

function fillKey(x, y, w, h, pc, on, isBlack) {
	var rgb = PC_RGB[pc];
	if (on && colorOn) {
		mgraphics.set_source_rgba([rgb[0], rgb[1], rgb[2], 1]);
	} else if (on) {
		mgraphics.set_source_rgba([0.80, 0.80, 0.80, 1]);
	} else {
		// excluida: la MISMA tinta pero muy apagada, para que se lea el mapa de color siempre
		var f = isBlack ? 0.28 : 0.20;
		mgraphics.set_source_rgba([rgb[0] * f + 0.04, rgb[1] * f + 0.04, rgb[2] * f + 0.04, 1]);
	}
	mgraphics.rectangle(x + 0.5, y + 0.5, w - 1, h - 1);
	mgraphics.fill();
	mgraphics.set_source_rgba([0, 0, 0, 0.55]);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(x + 0.5, y + 0.5, w - 1, h - 1);
	mgraphics.stroke();

	if (w >= 13) {
		mgraphics.set_source_rgba(on ? PC_TEXT[pc] : [0.5, 0.5, 0.52, 1]);
		mgraphics.set_font_size(w >= 20 ? 9 : 7);
		var nm = NN[pc];
		mgraphics.move_to(x + w / 2 - nm.length * (w >= 20 ? 2.6 : 2.0), y + h - 5);
		mgraphics.show_text(nm);
	}
}

function drawGrid(gz, headH, footH) {
	var W = geo.W;
	// cabecera
	mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(gz.x, gz.y + 11);
	var htxt = 'Sets que pasan: ' + filtShown + (filtShown < filtTotal ? ' / ' + filtTotal : '');
	mgraphics.show_text(htxt);

	var multi = geo.pageSize > 0 && filtShown > geo.pageSize;
	if (multi) {
		drawBtn(geo.prevBtn, '<', page > 0);
		drawBtn(geo.nextBtn, '>', page < pageCount() - 1);
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_font_size(9);
		var ptxt = (page + 1) + '/' + pageCount();
		mgraphics.move_to(geo.prevBtn.x - 26, gz.y + 11);
		mgraphics.show_text(ptxt);
	}

	// celdas
	var grid = geo.grid;
	for (var k = 0; k < geo.pageSize; k++) {
		var gi = page * geo.pageSize + k;
		if (gi >= filtShown) break;
		var s = filtSets[gi];
		if (!s) continue;
		var col = k % geo.cols;
		var row = Math.floor(k / geo.cols);
		var cx = grid.x + col * geo.cw;
		var cy = grid.y + row * geo.ch;

		if (colorOn) mgraphics.set_source_rgba([s.rgb[0], s.rgb[1], s.rgb[2], 1]);
		else mgraphics.set_source_rgba([0.35, 0.35, 0.38, 1]);
		mgraphics.rectangle(cx + 1.5, cy + 1.5, geo.cw - 3, geo.ch - 3);
		mgraphics.fill();

		if (s.idx1 === selIdx) {
			mgraphics.set_source_rgba([1, 1, 1, 0.95]);
			mgraphics.set_line_width(2);
			mgraphics.rectangle(cx + 2, cy + 2, geo.cw - 4, geo.ch - 4);
			mgraphics.stroke();
		} else {
			mgraphics.set_source_rgba([0, 0, 0, 0.4]);
			mgraphics.set_line_width(1);
			mgraphics.rectangle(cx + 1.5, cy + 1.5, geo.cw - 3, geo.ch - 3);
			mgraphics.stroke();
		}

		if (geo.cw >= 40) {
			var lum = s.rgb[0] * 0.299 + s.rgb[1] * 0.587 + s.rgb[2] * 0.114;
			mgraphics.set_source_rgba(lum > 0.55 ? [0, 0, 0, 0.9] : [0.95, 0.95, 0.95, 0.9]);
			mgraphics.set_font_size(8);
			mgraphics.move_to(cx + 4, cy + geo.ch - 6);
			mgraphics.show_text(s.forte);
		}
	}

	// pie: nombre Forte
	var foot = hoverForte || forteOfSel || '';
	if (foot) {
		mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
		mgraphics.set_font_size(9);
		mgraphics.move_to(gz.x, geo.H - 5);
		mgraphics.show_text((hoverForte ? '' : 'Fijado: ') + foot);
	}
}

function drawBtn(r, label, enabled) {
	mgraphics.set_source_rgba(enabled ? [0.30, 0.30, 0.34, 1] : [0.17, 0.17, 0.19, 1]);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.fill();
	mgraphics.set_source_rgba([0, 0, 0, 0.5]);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.stroke();
	mgraphics.set_source_rgba(enabled ? [0.85, 0.85, 0.88, 1] : [0.45, 0.45, 0.48, 1]);
	mgraphics.set_font_size(11);
	mgraphics.move_to(r.x + r.w / 2 - 3, r.y + r.h - 4);
	mgraphics.show_text(label);
}

function paint() {
	var wh = viewportWH();
	var W = wh[0], H = wh[1];

	mgraphics.set_source_rgba([0.11, 0.11, 0.12, 1]);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();
	mgraphics.select_font_face('Arial');

	// --- zonas ---
	var pianoH = Math.round(H * 0.52);
	if (pianoH < 128) pianoH = 128;
	if (pianoH > 168) pianoH = 168;
	if (pianoH > H - 60) pianoH = Math.max(60, H - 60);

	var pz = { x: 6, y: 6, w: W - 12, h: pianoH - 6 };
	var keys = { x: pz.x + 2, y: pz.y + 16, w: pz.w - 4, h: pz.h - 16 - 18 };
	if (keys.h < 24) keys.h = 24;

	var headH = 16, footH = 16;
	var gz = { x: 6, y: pianoH + 4, w: W - 12, h: H - (pianoH + 4) };
	var gridTop = gz.y + headH;
	var gridBottom = H - footH;

	var btnW = 20, btnH = 14;
	var prevBtn = { x: W - 6 - btnW * 2 - 4, y: gz.y, w: btnW, h: btnH };
	var nextBtn = { x: W - 6 - btnW, y: gz.y, w: btnW, h: btnH };

	var gridW = gz.w;
	var gridH = Math.max(1, gridBottom - gridTop);
	var cols = Math.max(4, Math.floor(gridW / 46));
	var cw = gridW / cols;
	var ch = 30;
	var rows = Math.max(1, Math.floor(gridH / ch));
	var pageSize = cols * rows;

	geo = {
		W: W, H: H,
		piano: pz, keys: keys,
		grid: { x: gz.x, y: gridTop, w: gridW, h: rows * ch },
		cols: cols, cw: cw, ch: ch, pageSize: pageSize,
		prevBtn: prevBtn, nextBtn: nextBtn
	};

	// clamp de pagina si el filtro se estrecho
	var pc = pageCount();
	if (page > pc - 1) page = pc - 1;
	if (page < 0) page = 0;

	drawPiano(pz);

	// separador entre zonas
	mgraphics.set_source_rgba([0, 0, 0, 0.6]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(0, pianoH + 1);
	mgraphics.line_to(W, pianoH + 1);
	mgraphics.stroke();

	drawGrid(gz, headH, footH);
}
