// fs2setpick.js -- jsui: el panel IZQUIERDO del popup "Proximos 16" de FORTESEQ2.
//
// Barra de voz COMPARTIDA arriba (Compartido + V1..Vn, cada chip tenido con el color real de lo
// que esa voz tiene asignado -- de vcolor) + Soltar. Debajo, TRES secciones siempre visibles,
// apiladas (no exclusivas -- antes eran 3 modos que se turnaban con un boton, ahora conviven; la
// ventana ya era redimensionable, asi que mas alto = mas lugar para las tres):
//
//   MASCARA  -- piano cromatico de una octava + rejilla de swatches, uno por cada pitch-class set
//               que PASA el filtro actual (pintado con harmonyToColor()). Click en una tecla
//               incluye/excluye esa nota de la mascara (setmask + setfilter). Click en un swatch
//               asigna ese set al destino elegido en la barra compartida.
//
//   Z-PARES  -- lista de TODOS los sets con Z-mate (independiente del Filtro), filtrable por
//               cardinalidad. Click normal asigna al destino elegido; el toggle "Par" (unico
//               remanente de la version anterior de este panel) hace que el click en cambio
//               reparta el set A / su Z-mate mitad y mitad entre TODAS las voces (assignzpair).
//
//   RED      -- red padre/hijo (agregar/quitar una nota, ver neighborsOf() en forteseq2.js) --
//               el mecanismo del sitio "66 Shapes" de Miles Okazaki, aqui sin su filtro de 3
//               reglas: cualquier vecino de las 351 clases Tn es valido. Padres (izq, card-1) e
//               Hijos (der, card+1) del set "centrado"; click asigna Y recentra, asi que caminar
//               la red es clickear repetido. Volver retrocede un paso (o recentra en lo que suena).
//
// Entra por outlet 3 de forteseq2.js (compartido con fs2horizon.js / fs2colmon.js -- se despacha
// por el selector, sin [route]):
//   filtclear                                         -- vacia la rejilla de Mascara.
//   filtinfo  <total> <shown>                         -- shown = total (sin tope; el panel filtra por n notas).
//   filtset   <slot> <idx1> <forte> <rootAbs> <pc...>  -- un set permitido; pc ya transpuesto.
//   maskecho  <m0..m11>                                -- mascara real del motor; el panel la adopta.
//   zclear  zset <idx1> <forte> <mate> <pc...>         -- panel Z-pares.
//   nbclear <idx1> <forte> <card>  nbset <p0|h1> <slot> <idx1> <forte> <rootAbs> <pc...>  -- Red.
//   vkey <v0> <forte> <tonic> <keyOwn> ...             -- que set tiene cada voz (barra compartida).
//   vcolor <v0> <pc...>                                -- pcs reales de esa voz, para tenir su chip.
//   hstatus <...> <idx1>  groot <root>                 -- para sembrar Red (Volver).
//   color <0|1>  clear  bang                           -- toggle Color Monitor / limpiar / loadbang.
// (todos los selectores de horizon/colmon llegan igual y se ignoran aqui.)
//
// Sale por outlet 0 -> outlet del subpatcher -> js forteseq2.js inlet 0:
//   setmask <12 ints>   setfilter 1
//   setroot <r>   setlockindex <idx1>   setlock 1                    -- destino Compartido.
//   assignvoiceset <v> <idx1>            (Z-pares: raiz sigue a la compartida, como siempre)
//   assignvoicesetroot <v> <idx1> <rootAbs>   (Mascara/Red: raiz fija a lo mostrado)
//   assignzpair <idx1>   setvoicekeyown <v> 0   queryzsets   queryneighbors <idx1> <rootAbs>
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

// --- estado: Mascara -------------------------------------------------------------------------

var maskArr = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1];   // mascara cromatica, C = slot 0, absoluta
var colorOn = 1;
var filtSets = [];        // filtSets[slot] = { idx1, forte, rootAbs, pcs:[...], rgb:[r,g,b] }
var filtTotal = 0;        // cuantos pasan en total
var filtShown = 0;        // cuantos se enviaron (<= FILT_MAX)
var maskPage = 0;
var mCard = 0;            // filtro local por cantidad de notas (0 = todas); solo afecta lo que se MUESTRA
var M_CARDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
var mView = null;         // cache de maskView(); null = recalcular
var mRequested = false;   // ya se pidio queryfiltsets al motor (ver paintMaskSection)
var selIdx = -1;          // idx1 del swatch fijado en Compartido (-1 = ninguno)
var maskHover = '';       // nombre Forte bajo el puntero, seccion Mascara
var maskGeo = null;       // rects del ultimo paint(), para hit-testing coherente

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

// Los sets que pasan el filtro del motor (filtSets, huecos posibles), reducidos a los de mCard
// notas. Es lo que la rejilla pagina y a lo que apuntan el hit-test y el hover.
function maskView() {
	if (mView) return mView;
	var out = [];
	for (var i = 0; i < filtSets.length; i++) {
		var s = filtSets[i];
		if (s && (!mCard || s.pcs.length === mCard)) out.push(s);
	}
	mView = out;
	return out;
}

function filtclear() {
	mView = null;
	filtSets = [];
	filtTotal = 0;
	filtShown = 0;
	maskPage = 0;
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
	if (a.length < 5) return;
	var slot = Math.round(a[0]);
	if (!(slot >= 0 && slot < 4096)) return;
	var pcs = [];
	for (var k = 4; k < a.length; k++) {
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
	mView = null;
	filtSets[slot] = { idx1: Math.round(a[1]), forte: String(a[2]), rootAbs: Math.round(a[3]), pcs: pcs, rgb: rgb };
	if (selIdx >= 0 && filtSets[slot].idx1 === selIdx) forteOfSel = filtSets[slot].forte;
	scheduleRedraw();
}

function maskecho() {
	var a = arrayfromargs(arguments);
	for (var k = 0; k < 12 && k < a.length; k++) maskArr[k] = a[k] ? 1 : 0;
	mgraphics.redraw();
}

var forteOfSel = '';      // nombre Forte del set fijado en Compartido, para el pie cuando no hay hover

// --- barra de voz COMPARTIDA ------------------------------------------------------------------
// Usada por click en CUALQUIERA de las 3 secciones de abajo: 0 = Compartido, 1..n = esa voz.
// zVoices/zVoiceCount vienen de vkey() (que set/forte tiene cada voz); voiceColorMap de vcolor()
// (las pcs reales que suenan, para tenir el chip con harmonyToColor en vez de un azul generico).
var sharedTarget = 0;
var zVoices = [];         // zVoices[v0] = { forte, own }
var zVoiceCount = 4;
var voiceColorMap = {};   // v0 -> [r,g,b]
var barGeo = null;

function vcolor() {
	var a = arrayfromargs(arguments);
	if (a.length < 1) return;
	var v = Math.round(a[0]);
	if (!(v >= 0 && v < 8)) return;
	var pcs = [];
	for (var k = 1; k < a.length; k++) pcs.push(((Math.round(a[k]) % 12) + 12) % 12);
	if (pcs.length) {
		var c = harmonyToColor(pcs, COLOR_OPTS, 'oklab');
		voiceColorMap[v] = [c.r, c.g, c.b];
	} else {
		delete voiceColorMap[v];
	}
	scheduleRedraw();
}

// Punto unico de asignacion para las 3 secciones. rootAbs null/undefined = el candidato no tiene
// una raiz absoluta propia (sets de Z-pares: "cada voz guarda su propio root", como siempre) --
// Compartido entonces no toca root, y una voz usa assignvoiceset (sigue la raiz compartida).
// rootAbs numerico (Mascara, Red) = Compartido fija esa raiz explicita, y una voz usa
// assignvoicesetroot (raiz FIJA a lo que se ve, no sigue mas la compartida).
function assignToTarget(idx1, rootAbs) {
	var hasRoot = (rootAbs !== null && rootAbs !== undefined);
	if (sharedTarget === 0) {
		if (hasRoot) outlet(0, ['setroot', rootAbs]);
		outlet(0, ['setlockindex', idx1]);
		outlet(0, ['setlock', 1]);
	} else if (hasRoot) {
		outlet(0, ['assignvoicesetroot', sharedTarget, idx1, rootAbs]);
	} else {
		outlet(0, ['assignvoiceset', sharedTarget, idx1]);
	}
}

function drawTargetRow(x, y, w) {
	var targets = [];
	var nT = zVoiceCount + 1;
	var tw = w / nT;
	for (var t = 0; t < nT; t++) {
		var tr = { x: x + t * tw, y: y, w: tw - 3, h: 26 };
		targets.push(tr);
		if (t === 0) {
			drawChip(tr, 'Compartido', sharedTarget === 0);
		} else {
			var vv = zVoices[t - 1];
			var rgb = (vv && vv.own) ? voiceColorMap[t - 1] : null;
			drawChip(tr, 'V' + t, sharedTarget === t, (vv && vv.own) ? vv.forte : '-', rgb);
		}
	}
	return targets;
}

function paintBar(W) {
	var soltarR = { x: W - 6 - 44, y: 3, w: 44, h: 15 };
	drawChip(soltarR, 'Soltar', false);
	mgraphics.set_source_rgba([0.55, 0.55, 0.6, 1]);
	mgraphics.set_font_size(9);
	mgraphics.move_to(6, 13);
	mgraphics.show_text('Voz destino');
	var targets = drawTargetRow(6, 21, W - 12);
	barGeo = { soltar: soltarR, targets: targets, h: 50 };
	return barGeo.h;
}

function barClick(x, y) {
	if (!barGeo) return false;
	if (ptIn(barGeo.soltar, x, y)) {
		for (var v = 1; v <= zVoiceCount; v++) outlet(0, ['setvoicekeyown', v, 0]);
		return true;
	}
	for (var t = 0; t < barGeo.targets.length; t++) {
		if (ptIn(barGeo.targets[t], x, y)) { sharedTarget = t; mgraphics.redraw(); return true; }
	}
	return false;
}

// --- seccion Z-pares --------------------------------------------------------------------------
var zSets = [];           // { idx1, forte, mate, pcs, rgb }
var zCard = 0;            // 0 = todas las cardinalidades
var zParMode = 0;         // toggle "Par": ON = click reparte A / su Z-mate entre TODAS las voces
var zPage = 0;
var zHover = '';
var zGeo = null;
var Z_CARDS = [0, 4, 5, 6, 7, 8];

function zclear() { zSets = []; zPage = 0; scheduleRedraw(); }

// El motor solo manda zclear/zset cuando se le pide (queryzsets). Al pasar a la disposicion
// simultanea se perdio el pedido que hacia el modo Z antiguo, y la lista quedaba vacia para
// siempre. Un pedido por sesion de popup; un click sobre una lista vacia lo rearma (por si el
// motor aun no habia construido sets[] en el primer paint).
var zRequested = false;
function zEnsureLoaded() {
	if (zRequested) return;
	zRequested = true;
	outlet(0, ['queryzsets']);
}

function zset() {
	var a = arrayfromargs(arguments);
	if (a.length < 5) return;
	var pcs = [];
	for (var k = 4; k < a.length; k++) pcs.push(((Math.round(a[k]) % 12) + 12) % 12);
	var c = pcs.length ? harmonyToColor(pcs, COLOR_OPTS, 'oklab') : { r: 0.5, g: 0.5, b: 0.5 };
	zSets.push({ idx1: Math.round(a[1]), forte: String(a[2]), mate: String(a[3]), pcs: pcs, rgb: [c.r, c.g, c.b] });
	scheduleRedraw();
}

function zView() {
	if (!zCard) return zSets;
	var out = [];
	for (var i = 0; i < zSets.length; i++) if (zSets[i].pcs.length === zCard) out.push(zSets[i]);
	return out;
}

function zClick(x, y) {
	if (!zGeo) return;
	if (zSets.length === 0) zRequested = false;
	if (ptIn(zGeo.parChip, x, y)) { zParMode = zParMode ? 0 : 1; mgraphics.redraw(); return; }
	for (var c = 0; c < zGeo.chips.cards.length; c++) {
		if (ptIn(zGeo.chips.cards[c], x, y)) { zCard = Z_CARDS[c]; zPage = 0; mgraphics.redraw(); return; }
	}
	var view = zView();
	var pages = Math.max(1, Math.ceil(view.length / zGeo.pageSize));
	if (ptIn(zGeo.prevBtn, x, y)) { if (zPage > 0) { zPage--; mgraphics.redraw(); } return; }
	if (ptIn(zGeo.nextBtn, x, y)) { if (zPage < pages - 1) { zPage++; mgraphics.redraw(); } return; }
	var gi = zCellAt(x, y, view);
	if (gi < 0) return;
	if (zParMode) outlet(0, ['assignzpair', view[gi].idx1]);
	else assignToTarget(view[gi].idx1, null);
}

function zCellAt(x, y, view) {
	if (!zGeo || !ptIn(zGeo.grid, x, y)) return -1;
	var col = Math.floor((x - zGeo.grid.x) / zGeo.cw);
	var row = Math.floor((y - zGeo.grid.y) / zGeo.ch);
	if (col < 0 || col >= zGeo.cols || row < 0) return -1;
	var gi = zPage * zGeo.pageSize + row * zGeo.cols + col;
	return (gi >= 0 && gi < view.length) ? gi : -1;
}

function drawSwatchCell(cx, cy, cw, ch, rgb, highlighted, label) {
	mgraphics.set_source_rgba(colorOn ? [rgb[0], rgb[1], rgb[2], 1] : [0.35, 0.35, 0.38, 1]);
	mgraphics.rectangle(cx + 1.5, cy + 1.5, cw - 3, ch - 3);
	mgraphics.fill();
	if (highlighted) {
		mgraphics.set_source_rgba([1, 1, 1, 0.95]);
		mgraphics.set_line_width(2);
		mgraphics.rectangle(cx + 2, cy + 2, cw - 4, ch - 4);
	} else {
		mgraphics.set_source_rgba([0, 0, 0, 0.4]);
		mgraphics.set_line_width(1);
		mgraphics.rectangle(cx + 1.5, cy + 1.5, cw - 3, ch - 3);
	}
	mgraphics.stroke();
	if (cw >= 34) {
		var lum = rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114;
		mgraphics.set_source_rgba(lum > 0.55 ? [0, 0, 0, 0.9] : [0.95, 0.95, 0.95, 0.9]);
		mgraphics.set_font_size(11);   // was 8: forte numbers are the whole point of the swatch
		mgraphics.move_to(cx + 4, cy + ch - 7);
		mgraphics.show_text(label);
	}
}

function paintZSection(x, y, w, h) {
	zEnsureLoaded();
	mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(x, y + 11);
	mgraphics.show_text('Z-pares: ' + zView().length);

	var parChip = { x: x + w - 6 - 38, y: y, w: 38, h: 15 };
	drawChip(parChip, 'Par', zParMode !== 0);

	var chips = { cards: [] };
	for (var c = 0; c < Z_CARDS.length; c++) {
		var r = { x: x + c * 36, y: y + 17, w: 32, h: 14 };
		chips.cards.push(r);
		drawChip(r, Z_CARDS[c] ? String(Z_CARDS[c]) : 'Todos', zCard === Z_CARDS[c]);
	}

	var headH = 34, footH = 0;
	var gridW = w;
	var cols = Math.max(4, Math.floor(gridW / 46));
	var cw = gridW / cols, ch = 26;
	var rows = Math.max(1, Math.floor((h - headH - footH) / ch));
	var pageSize = cols * rows;
	var prevBtn = { x: x + w - 44, y: y, w: 18, h: 14 };
	var nextBtn = { x: x + w - 22, y: y, w: 18, h: 14 };
	// prevBtn/nextBtn comparten fila con "Par"; se dibujan solo si hacen falta (mas abajo) asi que
	// se empujan un poco a la izquierda del chip Par para no superponerse.
	prevBtn.x -= 42; nextBtn.x -= 42;

	zGeo = {
		parChip: parChip, chips: chips,
		grid: { x: x, y: y + headH, w: gridW, h: rows * ch },
		cols: cols, cw: cw, ch: ch, pageSize: pageSize, prevBtn: prevBtn, nextBtn: nextBtn
	};

	var view = zView();
	var pages = Math.max(1, Math.ceil(view.length / pageSize));
	if (zPage > pages - 1) zPage = pages - 1;
	if (zPage < 0) zPage = 0;
	if (pages > 1) {
		drawBtn(prevBtn, '<', zPage > 0);
		drawBtn(nextBtn, '>', zPage < pages - 1);
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(prevBtn.x - 26, y + 11);
		mgraphics.show_text((zPage + 1) + '/' + pages);
	}

	for (var k = 0; k < pageSize; k++) {
		var gi = zPage * pageSize + k;
		if (gi >= view.length) break;
		var s = view[gi];
		var cx = x + (k % cols) * cw, cy = y + headH + Math.floor(k / cols) * ch;
		var assigned = false;
		for (var v = 0; v < zVoiceCount; v++) if (zVoices[v] && zVoices[v].own && zVoices[v].forte === s.forte) assigned = true;
		drawSwatchCell(cx, cy, cw, ch, s.rgb, assigned, s.forte);
	}
}

// --- seccion Red (padre/hijo) -------------------------------------------------------------------
// Generaliza "un set relacionado" (Z-pares) a TODA la red de vecinos por agregar/quitar una nota
// (neighborsOf() en forteseq2.js) -- el mecanismo del sitio "66 Shapes" de Miles Okazaki, aqui sin
// su filtro de 3 reglas: cualquier vecino de las 351 clases Tn es valido, no solo esas 66 escalas.
// Click en un vecino: lo asigna al destino de la barra compartida Y recentra la navegacion sobre
// el, asi que "caminar" la red es clickear repetido. Volver retrocede un paso en el historial; si
// esta vacio, recentra en el set realmente sonando (sharedIdx1/sharedRoot, de hstatus/groot).
var redCenter = -1;          // idx1 (1-based) del set centrado; -1 = todavia no se sembro
var redRootAbs = 0;
var redCenterForte = '-', redCenterCard = 0;
var redParents = [];         // { idx1, forte, rootAbs, pcs, rgb }
var redChildren = [];
var redPPage = 0, redCPage = 0;
var redHistory = [];         // pila de { idx1, rootAbs } visitados, para Volver
var redHover = '';
var redGeo = null;
var sharedIdx1 = 1, sharedRoot = 0;   // cache de hstatus/groot, solo para sembrar/Volver

function nbclear(idx1, forte, card) {
	redCenterForte = String(forte);
	redCenterCard = Math.round(card) || 0;
	redParents = [];
	redChildren = [];
	scheduleRedraw();
}

function nbset() {
	var a = arrayfromargs(arguments);
	if (a.length < 5) return;
	var kind = Math.round(a[0]);
	var pcs = [];
	for (var k = 5; k < a.length; k++) pcs.push(((Math.round(a[k]) % 12) + 12) % 12);
	var c = pcs.length ? harmonyToColor(pcs, COLOR_OPTS, 'oklab') : { r: 0.5, g: 0.5, b: 0.5 };
	var e = { idx1: Math.round(a[2]), forte: String(a[3]), rootAbs: Math.round(a[4]), pcs: pcs, rgb: [c.r, c.g, c.b] };
	(kind ? redChildren : redParents).push(e);
	scheduleRedraw();
}

function redQuery() { outlet(0, ['queryneighbors', redCenter, redRootAbs]); }

function redGoHome() {
	redCenter = sharedIdx1;
	redRootAbs = sharedRoot;
	redQuery();
}

function redBack() {
	if (redHistory.length === 0) { redGoHome(); return; }
	var h = redHistory.pop();
	redCenter = h.idx1;
	redRootAbs = h.rootAbs;
	redQuery();
}

// Primer paint: siembra desde lo que realmente suena. Reabrir/redimensionar el popup no debe
// perder donde el usuario estaba navegando -- solo se siembra una vez.
function redEnsureSeeded() {
	if (redCenter < 0) redGoHome();
}

function redAssign(e) {
	assignToTarget(e.idx1, e.rootAbs);
	redHistory.push({ idx1: redCenter, rootAbs: redRootAbs });
	redCenter = e.idx1;
	redRootAbs = e.rootAbs;
	redQuery();
}

// Dibuja una zona (Padres o Hijos) Y devuelve su geometria de hit-test. page es el valor guardado
// (redPPage/redCPage); el caller debe releerlo de geo.page por si se clampeo.
function drawNeighborZone(x, y, w, h, label, list, page) {
	mgraphics.set_source_rgba([0.55, 0.55, 0.6, 1]);
	mgraphics.set_font_size(9);
	mgraphics.move_to(x, y + 10);
	mgraphics.show_text(label + ' (' + list.length + ')');

	var subHeadH = 13;
	var cols = Math.max(2, Math.floor(w / 44));
	var ch = 24;
	var gridY = y + subHeadH;
	var rows = Math.max(1, Math.floor((h - subHeadH) / ch));
	var pageSize = cols * rows;
	var pages = Math.max(1, Math.ceil(list.length / pageSize));
	if (page > pages - 1) page = pages - 1;
	if (page < 0) page = 0;

	var prevBtn = { x: x + w - 36, y: y, w: 16, h: 11 };
	var nextBtn = { x: x + w - 18, y: y, w: 16, h: 11 };
	if (pages > 1) {
		drawBtn(prevBtn, '<', page > 0);
		drawBtn(nextBtn, '>', page < pages - 1);
	}

	var cw = w / cols;
	for (var k = 0; k < pageSize; k++) {
		var gi = page * pageSize + k;
		if (gi >= list.length) break;
		var s = list[gi];
		var col = k % cols, row = Math.floor(k / cols);
		var cx = x + col * cw, cy = gridY + row * ch;
		drawSwatchCell(cx, cy, cw, ch, s.rgb, false, s.forte);
	}

	return {
		x: x, y: gridY, w: w, h: rows * ch, cols: cols, cw: cw, ch: ch,
		pageSize: pageSize, page: page, pages: pages, prevBtn: prevBtn, nextBtn: nextBtn, list: list
	};
}

function redCellAt(zone, x, y) {
	if (!zone || !ptIn(zone, x, y)) return -1;
	var col = Math.floor((x - zone.x) / zone.cw);
	var row = Math.floor((y - zone.y) / zone.ch);
	if (col < 0 || col >= zone.cols || row < 0) return -1;
	var gi = zone.page * zone.pageSize + row * zone.cols + col;
	return (gi >= 0 && gi < zone.list.length) ? gi : -1;
}

function paintRedSection(x, y, w, h) {
	redEnsureSeeded();

	mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(x, y + 11);
	mgraphics.show_text('Red: ' + redCenterForte + ' (n=' + redCenterCard + ')');

	var backR = { x: x + w - 6 - 44, y: y, w: 44, h: 15 };
	drawChip(backR, 'Volver', false);

	var headH = 20, footH = 0;
	var half = Math.floor((w - 6) / 2);
	var pz = drawNeighborZone(x, y + headH, half, h - headH - footH, 'Padres', redParents, redPPage);
	redPPage = pz.page;
	var cz = drawNeighborZone(x + half + 6, y + headH, half, h - headH - footH, 'Hijos', redChildren, redCPage);
	redCPage = cz.page;

	redGeo = { back: backR, parents: pz, children: cz };
}

function redClick(x, y) {
	if (!redGeo) return;
	if (ptIn(redGeo.back, x, y)) { redBack(); return; }
	if (ptIn(redGeo.parents.prevBtn, x, y)) { if (redPPage > 0) { redPPage--; mgraphics.redraw(); } return; }
	if (ptIn(redGeo.parents.nextBtn, x, y)) { if (redPPage < redGeo.parents.pages - 1) { redPPage++; mgraphics.redraw(); } return; }
	if (ptIn(redGeo.children.prevBtn, x, y)) { if (redCPage > 0) { redCPage--; mgraphics.redraw(); } return; }
	if (ptIn(redGeo.children.nextBtn, x, y)) { if (redCPage < redGeo.children.pages - 1) { redCPage++; mgraphics.redraw(); } return; }
	var pi = redCellAt(redGeo.parents, x, y);
	if (pi >= 0) { redAssign(redParents[pi]); return; }
	var ci = redCellAt(redGeo.children, x, y);
	if (ci >= 0) { redAssign(redChildren[ci]); return; }
}

// --- dibujo compartido: chips/botones -----------------------------------------------------------

function drawChip(r, label, on, sub, rgb) {
	if (rgb) {
		mgraphics.set_source_rgba([rgb[0], rgb[1], rgb[2], 1]);
	} else {
		mgraphics.set_source_rgba(on ? [0.30, 0.42, 0.62, 1] : [0.22, 0.22, 0.25, 1]);
	}
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.fill();
	mgraphics.set_source_rgba(on ? [1, 1, 1, 0.9] : [0, 0, 0, 0.5]);
	mgraphics.set_line_width(on ? 2 : 1);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.stroke();
	var lum = rgb ? (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114) : 0.3;
	mgraphics.set_source_rgba(rgb ? (lum > 0.55 ? [0, 0, 0, 0.9] : [0.95, 0.95, 0.95, 0.9]) : [0.9, 0.9, 0.92, 1]);
	mgraphics.set_font_size(sub ? 9 : 10);
	mgraphics.move_to(r.x + 4, r.y + (sub ? 11 : r.h - 4));
	mgraphics.show_text(label);
	if (sub) {
		mgraphics.set_source_rgba(rgb ? (lum > 0.55 ? [0, 0, 0, 0.75] : [0.85, 0.88, 0.95, 0.85]) : [0.75, 0.8, 0.9, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(r.x + 4, r.y + r.h - 4);
		mgraphics.show_text(sub);
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
function hsilprob() {}
function hcursor() {}
function hist() {}
// hstatus <readMode> <readDir> <idx1> <mode> <locked> -- solo idx1 interesa aqui, cacheado para
// que la seccion Red sepa a donde volver (redGoHome()).
function hstatus(readMode, readDir, idx1) {
	sharedIdx1 = Math.round(idx1) || 1;
}
function hshape() {}
function hshapecur() {}
function colvoices() {}
function colbang() {}
function colmon() {}
// vkey <v0> <forte> <tonic> <keyOwn> ... -- solo interesa que set tiene cada voz (barra compartida).
function vkey(v, forte, tonic, keyOwn) {
	v = Math.round(v);
	if (!(v >= 0 && v < 8)) return;
	zVoices[v] = { forte: String(forte), own: keyOwn ? 1 : 0 };
	if (v + 1 > zVoiceCount) zVoiceCount = v + 1;
	scheduleRedraw();
}
function ornscale() {}
function ornbasemode() {}
// groot <root> -- cacheado por la misma razon que hstatus arriba (seccion Red, Volver).
function groot(r) { sharedRoot = Math.round(r) || 0; }
function gornament() {}
function gflags() {}
function gharm() {}
function gorden() {}
function gordrev() {}
function grango() {}
function gsilpre() {}
function gsilence() {}
function genlace() {}
function gornquad() {}
function gornstep() {}
function gornseries() {}
function gcard() {}
function gmaskmode() {}
function gmaskk() {}
function gmaskfit() {}
function gsub() {}
function ggroove() {}
function gratchet() {}
function gaccent() {}
function geuclid() {}
function gvelmin() {}
function gvelmax() {}
function gfig() {}
function gaccentgrid() {}
function gtension() {}
function gfavstate() {}
function gregistro() {}
function grecorrido() {}
function gvec1() {}
function gvec2() {}
function gvec3() {}
function gvec4() {}
function gvec5() {}
function gvec6() {}
function grandmask() {}
function grandacc() {}
function gvoicing() {}
function gmod1() {}
function gmod2() {}
function gmod3() {}
function gmod4() {}
function gsesion() {}

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

function maskSwatchAt(x, y) {
	if (!maskGeo || !ptIn(maskGeo.grid, x, y)) return -1;
	var col = Math.floor((x - maskGeo.grid.x) / maskGeo.cw);
	var row = Math.floor((y - maskGeo.grid.y) / maskGeo.ch);
	if (col < 0 || col >= maskGeo.cols || row < 0) return -1;
	var gi = maskPage * maskGeo.pageSize + row * maskGeo.cols + col;
	if (gi < 0 || gi >= maskView().length) return -1;
	return gi;
}

function maskPageCount() {
	if (!maskGeo || maskGeo.pageSize <= 0) return 1;
	return Math.max(1, Math.ceil(maskView().length / maskGeo.pageSize));
}

function onclick(x, y, but) {
	if (!but) return;
	if (barClick(x, y)) return;
	if (filtSets.length === 0) mRequested = false;
	if (maskGeo) {
		if (ptIn(maskGeo.keys, x, y)) {
			var pc = keyAt(x - maskGeo.keys.x, y - maskGeo.keys.y, maskGeo.keys.w, maskGeo.keys.h);
			if (pc >= 0) { maskArr[pc] ^= 1; emitMask(); mgraphics.redraw(); }
			return;
		}
		for (var mc = 0; mc < maskGeo.cardChips.length; mc++) {
			if (ptIn(maskGeo.cardChips[mc], x, y)) { mCard = M_CARDS[mc]; maskPage = 0; mgraphics.redraw(); return; }
		}
		if (ptIn(maskGeo.prevBtn, x, y)) { if (maskPage > 0) { maskPage--; mgraphics.redraw(); } return; }
		if (ptIn(maskGeo.nextBtn, x, y)) { if (maskPage < maskPageCount() - 1) { maskPage++; mgraphics.redraw(); } return; }
		var gi = maskSwatchAt(x, y);
		if (gi >= 0) {
			var fs = maskView()[gi];
			if (sharedTarget === 0) { selIdx = fs.idx1; forteOfSel = fs.forte; }
			assignToTarget(fs.idx1, fs.rootAbs);
			mgraphics.redraw();
			return;
		}
	}
	// Z y Red viven en bandas de Y disjuntas (apiladas, ver paint()), asi que delegar a las dos
	// sin pre-filtrar es seguro: cada una ya hace su propio hit-test completo contra sus rects, y
	// una coordenada solo puede caer dentro de las de UNA de las dos.
	zClick(x, y);
	redClick(x, y);
}

function onidle(x, y) {
	var f = '';
	if (maskGeo) {
		var gi = maskSwatchAt(x, y);
		if (gi >= 0) f = maskView()[gi].forte;
	}
	if (!f && zGeo) {
		var zv = zView(), zi = zCellAt(x, y, zv);
		if (zi >= 0) f = zv[zi].forte + '  <->  ' + zv[zi].mate;
	}
	if (!f && redGeo) {
		var pi = redCellAt(redGeo.parents, x, y);
		var ci = pi < 0 ? redCellAt(redGeo.children, x, y) : -1;
		var e = pi >= 0 ? redParents[pi] : (ci >= 0 ? redChildren[ci] : null);
		if (e) f = e.forte + '  (raiz ' + e.rootAbs + ')';
	}
	if (f !== maskHover) { maskHover = f; mgraphics.redraw(); }
}

function onidleout() {
	if (maskHover !== '') { maskHover = ''; mgraphics.redraw(); }
}

// --- dibujo ------------------------------------------------------------------------------

function selectedNames() {
	var out = [];
	for (var k = 0; k < 12; k++) if (maskArr[k]) out.push(NN[k]);
	return out;
}

function drawPiano(pz, keys) {
	mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
	mgraphics.select_font_face('Arial');
	mgraphics.set_font_size(10);
	mgraphics.move_to(pz.x + 2, pz.y + 11);
	mgraphics.show_text('Mascara cromatica');

	var ww = keys.w / 7;
	var bw = ww * 0.6, bh = keys.h * 0.62;

	for (var wi = 0; wi < 7; wi++) {
		var pc = WHITE_PC[wi];
		var kx = keys.x + wi * ww;
		fillKey(kx, keys.y, ww, keys.h, pc, maskArr[pc], false);
	}
	for (var j = 0; j < 5; j++) {
		var bpc = BLACK_PC[j];
		var bx = keys.x + (BLACK_AFTER[j] + 1) * ww - bw / 2;
		fillKey(bx, keys.y, bw, bh, bpc, maskArr[bpc], true);
	}

	var names = selectedNames();
	mgraphics.set_source_rgba([0.55, 0.55, 0.6, 1]);
	mgraphics.set_font_size(9);
	mgraphics.move_to(pz.x + 2, pz.y + pz.h - 3);
	mgraphics.show_text((names.length ? names.join(' ') : '(vacia)') + '   (' + names.length + ')');
}

function fillKey(x, y, w, h, pc, on, isBlack) {
	var rgb = PC_RGB[pc];
	if (on && colorOn) {
		mgraphics.set_source_rgba([rgb[0], rgb[1], rgb[2], 1]);
	} else if (on) {
		mgraphics.set_source_rgba([0.80, 0.80, 0.80, 1]);
	} else {
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

function paintMaskSection(x, y, w, h) {
	// El motor solo re-emite la rejilla cuando cambia el filtro (firma), asi que un jsui recien
	// (re)cargado -- popup reabierto, js recargado -- quedaba vacio. Un pedido por sesion; un click
	// en una rejilla vacia lo rearma (ver onclick).
	if (!mRequested) { mRequested = true; outlet(0, ['queryfiltsets']); }
	var pianoH = Math.max(56, Math.min(96, Math.round(h * 0.45)));
	var pz = { x: x, y: y, w: w, h: pianoH };
	var keys = { x: pz.x + 2, y: pz.y + 14, w: pz.w - 4, h: pz.h - 14 - 14 };
	if (keys.h < 20) keys.h = 20;
	drawPiano(pz, keys);

	var gz = { x: x, y: y + pianoH + 4, w: w, h: h - pianoH - 4 };
	mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
	mgraphics.set_font_size(9);
	mgraphics.move_to(gz.x, gz.y + 9);
	var view = maskView();
	var htxt = 'Sets que pasan: ' + view.length + (view.length < filtTotal ? ' / ' + filtTotal : '');
	mgraphics.show_text(htxt);

	// filtro por cantidad de notas: una fila de chips (Todos, 1..12) bajo el titulo
	var cardChips = [];
	var cx0 = gz.x;
	for (var mc = 0; mc < M_CARDS.length; mc++) {
		var cwid = M_CARDS[mc] ? 24 : 34;
		var cr = { x: cx0, y: gz.y + 12, w: cwid, h: 13 };
		cardChips.push(cr);
		drawChip(cr, M_CARDS[mc] ? String(M_CARDS[mc]) : 'Todos', mCard === M_CARDS[mc]);
		cx0 += cwid + 2;
	}

	var headH = 28;
	var gridTop = gz.y + headH;
	var gridH = Math.max(1, gz.h - headH);
	var cols = Math.max(4, Math.floor(gz.w / 46));
	var cw = gz.w / cols, ch = 26;
	var rows = Math.max(1, Math.floor(gridH / ch));
	var pageSize = cols * rows;

	var btnW = 18, btnH = 12;
	var prevBtn = { x: x + w - btnW * 2 - 4, y: gz.y, w: btnW, h: btnH };
	var nextBtn = { x: x + w - btnW, y: gz.y, w: btnW, h: btnH };

	maskGeo = {
		piano: pz, keys: keys,
		grid: { x: gz.x, y: gridTop, w: gz.w, h: rows * ch },
		cols: cols, cw: cw, ch: ch, pageSize: pageSize,
		prevBtn: prevBtn, nextBtn: nextBtn, cardChips: cardChips
	};

	var pc = maskPageCount();
	if (maskPage > pc - 1) maskPage = pc - 1;
	if (maskPage < 0) maskPage = 0;

	var multi = pageSize > 0 && view.length > pageSize;
	if (multi) {
		drawBtn(prevBtn, '<', maskPage > 0);
		drawBtn(nextBtn, '>', maskPage < maskPageCount() - 1);
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(prevBtn.x - 26, gz.y + 9);
		mgraphics.show_text((maskPage + 1) + '/' + maskPageCount());
	}

	for (var k = 0; k < pageSize; k++) {
		var gi = maskPage * pageSize + k;
		if (gi >= view.length) break;
		var s = view[gi];
		var cx = gz.x + (k % cols) * cw, cy = gridTop + Math.floor(k / cols) * ch;
		var assigned = s.idx1 === selIdx;
		if (!assigned) for (var v = 0; v < zVoiceCount; v++) if (zVoices[v] && zVoices[v].own && zVoices[v].forte === s.forte) assigned = true;
		drawSwatchCell(cx, cy, cw, ch, s.rgb, assigned, s.forte);
	}
}

function paint() {
	var wh = viewportWH();
	var W = wh[0], H = wh[1];

	mgraphics.set_source_rgba([0.11, 0.11, 0.12, 1]);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();
	mgraphics.select_font_face('Arial');

	var barH = paintBar(W);
	mgraphics.set_source_rgba([0, 0, 0, 0.6]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(0, barH + 1);
	mgraphics.line_to(W, barH + 1);
	mgraphics.stroke();

	var footH = 14;
	var avail = Math.max(60, H - barH - 4 - footH);
	var maskH = Math.max(96, Math.round(avail * 0.42));
	var zH = Math.max(56, Math.round(avail * 0.24));
	var redH = Math.max(78, avail - maskH - zH);

	var yy = barH + 6;
	paintMaskSection(6, yy, W - 12, maskH);
	yy += maskH + 3;
	mgraphics.set_source_rgba([0, 0, 0, 0.5]);
	mgraphics.move_to(0, yy - 2); mgraphics.line_to(W, yy - 2); mgraphics.stroke();

	paintZSection(6, yy, W - 12, zH);
	yy += zH + 3;
	mgraphics.set_source_rgba([0, 0, 0, 0.5]);
	mgraphics.move_to(0, yy - 2); mgraphics.line_to(W, yy - 2); mgraphics.stroke();

	paintRedSection(6, yy, W - 12, redH);

	if (maskHover || forteOfSel) {
		mgraphics.set_source_rgba([0.62, 0.62, 0.68, 1]);
		mgraphics.set_font_size(9);
		mgraphics.move_to(6, H - 4);
		mgraphics.show_text(maskHover || ('Fijado: ' + forteOfSel));
	}
}
