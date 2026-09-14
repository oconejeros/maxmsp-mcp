"""Popup "Horizonte" (Proximos N pasos): controles por voz (On/Ext/Art/Lec/Ton/Fijar) + reordenar
la fila a [etiqueta+toggles][grid][tocado] + detalle ampliado de set/ornamentacion. Ver el plan
aprobado para el contexto completo.

    python tools/add_fs2_voice_controls.py            dry run, writes nothing
    python tools/add_fs2_voice_controls.py --apply    do it (device closed in Max AND Live)

## Que cambia

**forteseq/forteseq2.js** -- emitVoiceKeyReadouts() (outlet 3 'vkey') se amplia de 10 a 19 campos:
agrega artOwn/ext (ya existian como estado, sin eco) y ornNotas/ornBase (analogos por voz de
ornCount/ornBaseInterval), y reutiliza vecString/dissonancePercent/zMateOf/modalityNameOf/
mirrorForteOf -- las mismas funciones que ya arma emitSetReadouts() para la pestana "Filtro" --
indexadas por el set EFECTIVO de la voz (si). Sin funciones nuevas.

**forteseq/fs2horizon.js**:
  * vkey() recibe los 9 campos nuevos.
  * Layout de fila: keyW pasa de una zona fija de 150px a GATE_W(60)+TXT_W(118)+DETAIL_W(92)=270;
    el grid arranca justo despues (gridX=keyW) y el tocado se muda al extremo derecho (histX=W-histW).
  * El historial invierte su orden interno: antes newest=hslot mas a la derecha del bloque
    (age=HIST_MAX-1-hslot); ahora newest=hslot mas a la izquierda del bloque, pegado al grid
    (age=hslot) -- efecto neto: la nota recien tocada sigue naciendo junto al grid, el bloque
    entero vive del otro lado.
  * El bloque de etiqueta gana 2 lineas de revelado progresivo (vector+disonancia, Z/modalidad/
    espejo) y la linea de ornamento pasa a incluir cantidad+base.
  * 6 chips clickeables por voz (drawChip/ptIn/onclick nuevos, mismo patron optimista que
    fs2setpick.js) que mandan los mismos mensajes setvoice* que ya envian las live.* de "Voces N".

**forteseq/FORTESEQ2.amxd**: una sola patchline dentro de obj-751 ([p fs2_window]):
  obj-2 (fs2horizon.js) outlet 0 -> obj-4 (el outlet compartido del subpatcher), que ya sale
  directo a obj-23 (el engine) al nivel superior -- ese cable no se toca, ya existe. Mismo cableado
  que uso (y luego revirtio) tools/add_fs2_horizon_jump.py para una feature distinta; aca NO se
  agrega ningun route/sel -- los selectores setvoice* van derecho al engine igual que todo lo demas
  que ya pasa por obj-4.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
ENGINE_JS = os.path.join('forteseq', 'forteseq2.js')
HORIZON_JS = os.path.join('forteseq', 'fs2horizon.js')

WIN_ID = 'obj-751'


# ============================================================================================
# forteseq2.js -- emitVoiceKeyReadouts()
# ============================================================================================

ENGINE_OLD = '''function emitVoiceKeyReadouts() {
	for (var v = 0; v < NUM_VOICES; v++) {
		var keyOwn = voiceKeyOwn[v];
		var si = keyOwn ? voiceSetIndex[v] : setIndex;
		var forte = setForte[si] || "-";
		var tonic = NOTE_NAMES[pc12(keyOwn ? voiceRootOffset[v] : effRoot())];
		var readOwn = voiceReadOwn[v];
		var patron = readOwn ? voiceReadMode[v] : readMode;
		var dir = readOwn ? voiceReadDir[v] : readDir;
		var ornT = (patron === READ_ORNAMENT) ? (readOwn ? voiceOrnType[v] : ornType) : -1;
		var muted = voiceMute[v] ? 1 : 0;
		// -1 = TonProp off (Fijar doesn't apply to anything), 0 = progresando (advanceVoiceKeys()
		// steps it every harmony change), 1 = Fijar (voiceKeyLock skips it, see advanceVoiceKeys()).
		var keyLock = keyOwn ? (voiceKeyLock[v] ? 1 : 0) : -1;
		var sig = forte + "," + tonic + "," + keyOwn + "," + readOwn + "," + patron + "," + dir + "," + ornT + "," + muted + "," + keyLock;
		if (sig === qnVKeyShown[v]) continue;
		qnVKeyShown[v] = sig;
		outlet(3, ["vkey", v, forte, tonic, keyOwn, readOwn, patron, dir, ornT, muted, keyLock]);
	}
}'''

ENGINE_NEW = '''function emitVoiceKeyReadouts() {
	for (var v = 0; v < NUM_VOICES; v++) {
		var keyOwn = voiceKeyOwn[v];
		var si = keyOwn ? voiceSetIndex[v] : setIndex;
		var forte = setForte[si] || "-";
		var tonic = NOTE_NAMES[pc12(keyOwn ? voiceRootOffset[v] : effRoot())];
		var readOwn = voiceReadOwn[v];
		var patron = readOwn ? voiceReadMode[v] : readMode;
		var dir = readOwn ? voiceReadDir[v] : readDir;
		var ornT = (patron === READ_ORNAMENT) ? (readOwn ? voiceOrnType[v] : ornType) : -1;
		var ornN = (ornT >= 0) ? (readOwn ? voiceOrnCount[v] : ornCount) : -1;
		var ornB = (ornT >= 0) ? (readOwn ? voiceOrnBase[v] : ornBaseInterval) : -1;
		var muted = voiceMute[v] ? 1 : 0;
		// -1 = TonProp off (Fijar doesn't apply to anything), 0 = progresando (advanceVoiceKeys()
		// steps it every harmony change), 1 = Fijar (voiceKeyLock skips it, see advanceVoiceKeys()).
		var keyLock = keyOwn ? (voiceKeyLock[v] ? 1 : 0) : -1;
		var artOwn = voiceArtOwn[v] ? 1 : 0;
		var ext = voiceExternal[v] ? 1 : 0;
		// Mismas funciones que emitSetReadouts() ya usa para la pestana "Filtro" (outlet 7),
		// aca indexadas por el set EFECTIVO de esta voz (si) en vez del set compartido.
		var vec = vecString(si);
		var diss = dissonancePercent(si).toFixed(2);
		var zm = zMateOf(si);
		var modality = modalityNameOf(si);
		var mm = mirrorForteOf(si);
		var sig = forte + "," + tonic + "," + keyOwn + "," + readOwn + "," + patron + "," + dir + "," + ornT + "," +
			ornN + "," + ornB + "," + muted + "," + keyLock + "," + artOwn + "," + ext + "," + vec + "," + diss;
		if (sig === qnVKeyShown[v]) continue;
		qnVKeyShown[v] = sig;
		outlet(3, ["vkey", v, forte, tonic, keyOwn, readOwn, patron, dir, ornT, muted, keyLock,
			artOwn, ext, ornN, ornB, vec, diss, zm ? ("Z:" + zm) : "-", modality, mm ? ("Esp:" + mm) : "-"]);
	}
}'''


# ============================================================================================
# fs2horizon.js -- ordered list of (label, old, new) replacements, each applied exactly once
# ============================================================================================

HZ_EDITS = []

HZ_EDITS.append(('header: row-order line', '''// One ROW per voice. Each row is:  [ history ]  [ pattern grid ]
//   history  -- up to HIST_MAX notes already played, dim, newest next to the grid. EXACT.''', '''// One ROW per voice. Each row is:  [ label+toggles ]  [ pattern grid ]  [ history ]
//   history  -- up to HIST_MAX notes already played, at the row's far right; the newest sits at
//              the block's own LEFT edge (against the grid boundary) and each note drifts right
//              as newer ones arrive, dimming with age, until it falls off the row's right edge.'''))

HZ_EDITS.append(('header: vkey contract doc', '''//   vkey <v> <forte> <tonica> <keyOwn> <readOwn> <patron> <dir> <ornTipo> <muted>  -- everything
//            about what voice v is ACTUALLY doing right now, all resolved own-vs-shared exactly
//            like the audio path (voicePcsFor/voiceRootFor/voiceReadModeOf/voiceReadDirOf/
//            voiceOrnamentPitchAt): forte/tonica (its set+root), patron/dir (its reading order,
//            READ_NAMES/DIR_NAMES index), ornTipo (ORN_TYPE_NAMES index, -1 unless its effective
//            patron is Ornamento), muted (voiceMute[v]). keyOwn/readOwn (0/1) just say whether
//            that forte+tonica / patron+dir came from this voice's own override or the shared
//            globals -- drawn as a small label at the left of the row, under the "V<n>" tag this
//            file otherwise never printed (rows were previously told apart only by top-to-bottom
//            order). A muted row is drawn dimmed throughout, so a glance tells sounding voices
//            from silent ones.''', '''//   vkey <v> <forte> <tonica> <keyOwn> <readOwn> <patron> <dir> <ornTipo> <muted> <keyLock>
//        <artOwn> <ext> <ornNotas> <ornBase> <vector> <disonancia> <zRel> <modalidad> <espejo>
//            -- everything about what voice v is ACTUALLY doing right now, all resolved
//            own-vs-shared exactly like the audio path (voicePcsFor/voiceRootFor/
//            voiceReadModeOf/voiceReadDirOf/voiceOrnamentPitchAt): forte/tonica (its set+root),
//            patron/dir (its reading order, READ_NAMES/DIR_NAMES index), ornTipo/ornNotas/ornBase
//            (ORN_TYPE_NAMES index + count + interval base, -1 unless its effective patron is
//            Ornamento), muted (voiceMute[v]), keyLock (Fijar). vector/disonancia/zRel/modalidad/
//            espejo are the same set-class detail emitSetReadouts() already sends the main panel's
//            "Filtro" tab (outlet 7), here recomputed for this voice's own effective set. keyOwn/
//            readOwn/artOwn/ext (0/1) say whether forte+tonica / patron+dir / articulation / the
//            trigger source came from this voice's own override or the shared globals -- drawn as
//            On/Ext/Art/Lec/Ton/Fijar toggle chips plus a small label block at the left of the
//            row, under the "V<n>" tag. Clicking a chip sends the matching setvoice* message
//            straight to the engine (see onclick()). A muted row is drawn dimmed throughout, so a
//            glance tells sounding voices from silent ones.'''))

HZ_EDITS.append(('vkey(): signature + storage', '''function vkey(v, forte, tonic, keyOwn, readOwn, patron, dir, ornT, muted, keyLock) {
	v = Math.round(v);
	if (!(v >= 0 && v < MAXROWS)) return;
	vkeyInfo[v] = {
		forte: String(forte), tonic: String(tonic),
		keyOwn: !!Math.round(keyOwn), readOwn: !!Math.round(readOwn),
		patron: Math.round(patron), dir: Math.round(dir), ornT: Math.round(ornT),
		muted: !!Math.round(muted), keyLock: Math.round(keyLock === undefined ? -1 : keyLock)
	};
	mgraphics.redraw();
}''', '''function vkey(v, forte, tonic, keyOwn, readOwn, patron, dir, ornT, muted, keyLock,
		artOwn, ext, ornN, ornB, vec, diss, zRel, modality, mirror) {
	v = Math.round(v);
	if (!(v >= 0 && v < MAXROWS)) return;
	vkeyInfo[v] = {
		forte: String(forte), tonic: String(tonic),
		keyOwn: !!Math.round(keyOwn), readOwn: !!Math.round(readOwn),
		patron: Math.round(patron), dir: Math.round(dir), ornT: Math.round(ornT),
		muted: !!Math.round(muted), keyLock: Math.round(keyLock === undefined ? -1 : keyLock),
		artOwn: !!Math.round(artOwn || 0), ext: !!Math.round(ext || 0),
		ornN: Math.round(ornN), ornB: Math.round(ornB),
		vec: String(vec), diss: String(diss),
		zRel: String(zRel || "-"), modality: String(modality || "-"), mirror: String(mirror || "-")
	};
	mgraphics.redraw();
}'''))

HZ_EDITS.append(('paint(): row geometry + zone layout', '''	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH);
	var rowH = gridH / nRows;

	var keyW = 150;   // left zone: "V<n>" + forte/tonica + patron/dir + orn tipo (vkey), all it has
	var histW = Math.round(Math.min((W - keyW) * 0.28, HIST_MAX * 22));   // played notes
	var histCW = histW / HIST_MAX;
	var gridX = keyW + histW + 4;
	var gridW = Math.max(1, W - gridX);''', '''	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH);
	var rowH = gridH / nRows;
	rowGeo = { headH: headH, rowH: rowH, nRows: nRows };   // read by onclick() to find the row hit

	var GATE_W = 60;    // On + Ext, al inicio de la fila (deciden si la voz existe)
	var DETAIL_W = 92;  // Art/Lec/Ton/Fijar en cluster 2x2, en el borde etiqueta/grid
	var TXT_W = 118;    // bloque de texto vkey (V<n>/forte-tonica/patron-dir/orn/vector/Z-modalidad)
	var keyW = GATE_W + TXT_W + DETAIL_W;
	var showDetail = (W - keyW) > 260;   // bajo eso el grid quedaria inservible
	if (!showDetail) keyW = GATE_W + TXT_W;
	var histW = Math.round(Math.min((W - keyW) * 0.28, HIST_MAX * 22));   // played notes
	var histCW = histW / HIST_MAX;
	var histX = W - histW;
	var gridX = keyW;
	var gridW = Math.max(1, histX - gridX - 4);'''))

HZ_EDITS.append(('paint(): "tocado" header label position', '''	mgraphics.set_source_rgba([0.45, 0.45, 0.5, 1]);
	mgraphics.set_font_size(8);
	mgraphics.move_to(keyW + 4, headH - 5);
	mgraphics.show_text('tocado');''', '''	mgraphics.set_source_rgba([0.45, 0.45, 0.5, 1]);
	mgraphics.set_font_size(8);
	mgraphics.move_to(histX + 4, headH - 5);
	mgraphics.show_text('tocado');'''))

HZ_EDITS.append(('paint(): chips + label detail (merged, tabs verified against source)', '\t\tvar lh = fsInfo + 6;\n\n\t\tmgraphics.set_source_rgba(anyOwn ? [1 * rowDim, 0.75 * rowDim, 0.3 * rowDim, 1] : [0.6 * rowDim, 0.6 * rowDim, 0.66 * rowDim, 1]);\n\t\tmgraphics.set_font_size(fsV);\n\t\tmgraphics.move_to(4, y + fsV + 2);\n\t\tmgraphics.show_text(\'V\' + (v + 1) + (vk && vk.muted ? \' ·mute\' : \'\'));\n\t\tif (vk && rowH >= 24) {\n\t\t\tmgraphics.set_font_size(fsInfo);\n\t\t\tmgraphics.set_source_rgba([0.68 * rowDim, 0.68 * rowDim, 0.74 * rowDim, 1]);\n\t\t\tvar ky = y + fsV + lh;\n\t\t\tmgraphics.move_to(4, ky);\n\t\t\t// "*" ya marca TonProp (clave propia); "Fij" es la excepcion dentro de eso -- progresar\n\t\t\t// (avanzar con cada cambio de armonia) es el estado por defecto y no necesita marca,\n\t\t\t// solo la voz fijada (voiceKeyLock) la necesita.\n\t\t\tmgraphics.show_text(vk.forte + \' \' + vk.tonic + (vk.keyOwn ? \' *\' : \'\') + (vk.keyLock === 1 ? \' ·Fij\' : \'\'));\n\t\t\tif (rowH >= fsV + 2 * lh + 6) {\n\t\t\t\tky += lh;\n\t\t\t\tvar pname = READ_NAMES[vk.patron] || (\'modo \' + vk.patron);\n\t\t\t\tvar dsuf = vk.dir ? (\' \' + (DIR_NAMES[vk.dir] || vk.dir)) : \'\';\n\t\t\t\tmgraphics.move_to(4, ky);\n\t\t\t\tmgraphics.show_text(pname + dsuf + (vk.readOwn ? \' *\' : \'\'));\n\t\t\t}\n\t\t\tif (rowH >= fsV + 3 * lh + 6 && vk.ornT >= 0) {\n\t\t\t\tky += lh;\n\t\t\t\tmgraphics.move_to(4, ky);\n\t\t\t\tmgraphics.show_text(ORN_TYPE_NAMES[vk.ornT] || (\'orn \' + vk.ornT));\n\t\t\t}\n\t\t}', '\t\tvar lh = fsInfo + 6;\n\n\t\tvar chipH = 15, chipGap = 2;\n\t\tvar cg = { on: { x: 2, y: y + 2, w: GATE_W - 6, h: chipH },\n\t\t\text: { x: 2, y: y + 2 + chipH + chipGap, w: GATE_W - 6, h: chipH } };\n\t\tdrawChip(cg.on, (vk && vk.muted) ? \'Off\' : \'On\', !(vk && vk.muted));\n\t\tdrawChip(cg.ext, \'Ext\', !!(vk && vk.ext));\n\t\tif (showDetail) {\n\t\t\tvar dx0 = GATE_W + TXT_W + 2;\n\t\t\tvar dcw = (DETAIL_W - 6) / 2;\n\t\t\tcg.art = { x: dx0, y: y + 2, w: dcw, h: chipH };\n\t\t\tcg.lec = { x: dx0 + dcw + 2, y: y + 2, w: dcw, h: chipH };\n\t\t\tcg.ton = { x: dx0, y: y + 2 + chipH + chipGap, w: dcw, h: chipH };\n\t\t\tcg.fijar = { x: dx0 + dcw + 2, y: y + 2 + chipH + chipGap, w: dcw, h: chipH };\n\t\t\tdrawChip(cg.art, \'Art\', !!(vk && vk.artOwn));\n\t\t\tdrawChip(cg.lec, \'Lec\', !!(vk && vk.readOwn));\n\t\t\tdrawChip(cg.ton, \'Ton\', !!(vk && vk.keyOwn));\n\t\t\tdrawChip(cg.fijar, \'Fij\', vk ? vk.keyLock === 1 : false);\n\t\t}\n\t\tchipGeo[v] = cg;\n\n\t\tmgraphics.set_source_rgba(anyOwn ? [1 * rowDim, 0.75 * rowDim, 0.3 * rowDim, 1] : [0.6 * rowDim, 0.6 * rowDim, 0.66 * rowDim, 1]);\n\t\tmgraphics.set_font_size(fsV);\n\t\tmgraphics.move_to(GATE_W + 4, y + fsV + 2);\n\t\tmgraphics.show_text(\'V\' + (v + 1) + (vk && vk.muted ? \' ·mute\' : \'\'));\n\t\tif (vk && rowH >= 24) {\n\t\t\tmgraphics.set_font_size(fsInfo);\n\t\t\tmgraphics.set_source_rgba([0.68 * rowDim, 0.68 * rowDim, 0.74 * rowDim, 1]);\n\t\t\tvar ky = y + fsV + lh;\n\t\t\tmgraphics.move_to(GATE_W + 4, ky);\n\t\t\t// "*" ya marca TonProp (clave propia); "Fij" es la excepcion dentro de eso -- progresar\n\t\t\t// (avanzar con cada cambio de armonia) es el estado por defecto y no necesita marca,\n\t\t\t// solo la voz fijada (voiceKeyLock) la necesita.\n\t\t\tmgraphics.show_text(vk.forte + \' \' + vk.tonic + (vk.keyOwn ? \' *\' : \'\') + (vk.keyLock === 1 ? \' ·Fij\' : \'\'));\n\t\t\tif (rowH >= fsV + 2 * lh + 6) {\n\t\t\t\tky += lh;\n\t\t\t\tvar pname = READ_NAMES[vk.patron] || (\'modo \' + vk.patron);\n\t\t\t\tvar dsuf = vk.dir ? (\' \' + (DIR_NAMES[vk.dir] || vk.dir)) : \'\';\n\t\t\t\tmgraphics.move_to(GATE_W + 4, ky);\n\t\t\t\tmgraphics.show_text(pname + dsuf + (vk.readOwn ? \' *\' : \'\'));\n\t\t\t}\n\t\t\tif (rowH >= fsV + 3 * lh + 6 && vk.ornT >= 0) {\n\t\t\t\tky += lh;\n\t\t\t\tmgraphics.move_to(GATE_W + 4, ky);\n\t\t\t\tmgraphics.show_text((ORN_TYPE_NAMES[vk.ornT] || (\'orn \' + vk.ornT)) + \' ×\' + vk.ornN + \' I\' + vk.ornB + (vk.readOwn ? \' *\' : \'\'));\n\t\t\t}\n\t\t\tif (rowH >= fsV + 4 * lh + 6) {\n\t\t\t\tky += lh;\n\t\t\t\tmgraphics.move_to(GATE_W + 4, ky);\n\t\t\t\tmgraphics.show_text(\'<\' + vk.vec + \'> \' + vk.diss + \'%\');\n\t\t\t}\n\t\t\tif (rowH >= fsV + 5 * lh + 6) {\n\t\t\t\tky += lh;\n\t\t\t\tmgraphics.move_to(GATE_W + 4, ky);\n\t\t\t\tvar extras = [];\n\t\t\t\tif (vk.zRel !== \'-\') extras.push(vk.zRel);\n\t\t\t\textras.push(vk.modality);\n\t\t\t\tif (vk.mirror !== \'-\') extras.push(vk.mirror);\n\t\t\t\tmgraphics.show_text(extras.join(\' · \'));\n\t\t\t}\n\t\t}'))

HZ_EDITS.append(('paint(): history block, reversed internal order', '\t\t// history: newest is hv[0], drawn nearest the grid (rightmost slot)\n\t\tfor (var hslot = 0; hslot < HIST_MAX; hslot++) {\n\t\t\tvar hidx = hslot;                       // 0..HIST_MAX-1, oldest slot on the left\n\t\t\tvar age = HIST_MAX - 1 - hslot;         // -> hv index (older = higher)\n\t\t\tvar note = (age < hv.length) ? hv[age] : -1;\n\t\t\tvar dim = (0.40 + 0.15 * (hslot / (HIST_MAX - 1))) * rowDim;   // older = dimmer\n\t\t\tdrawCell(keyW + hidx * histCW, y, histCW, rowH, note, dim, histCW >= 20);\n\t\t}', "\t\t// history: newest is hv[0], drawn at the block's LEFT edge (against the grid); ages rightward\n\t\tfor (var hslot = 0; hslot < HIST_MAX; hslot++) {\n\t\t\tvar hidx = hslot;                       // 0..HIST_MAX-1, 0 = left edge of block (vs. grid)\n\t\t\tvar age = hslot;                        // hslot 0 = age 0 = newest, pinned next to the grid\n\t\t\tvar note = (age < hv.length) ? hv[age] : -1;\n\t\t\tvar dim = (0.55 - 0.15 * (hslot / (HIST_MAX - 1))) * rowDim;   // newest bright, oldest dim\n\t\t\tdrawCell(histX + hidx * histCW, y, histCW, rowH, note, dim, histCW >= 20);\n\t\t}"))

HZ_EDITS.append(('paint(): rolling-mode overflow marker position', '\t\t\tmgraphics.move_to(W - 12, y + rowH / 2 + 4);', '\t\t\tmgraphics.move_to(gridX + gridW - 12, y + rowH / 2 + 4);'))

HZ_EDITS.append(('paint(): hist/grid separator line position', '''	// separator between history zone and grid
	mgraphics.set_source_rgba([0, 0, 0, 0.6]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(gridX - 2, headH);
	mgraphics.line_to(gridX - 2, headH + gridH);
	mgraphics.stroke();''', '''	// separator between grid and history zone
	mgraphics.set_source_rgba([0, 0, 0, 0.6]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(histX - 2, headH);
	mgraphics.line_to(histX - 2, headH + gridH);
	mgraphics.stroke();'''))

ONCLICK_BLOCK = '''// Geometry of the last paint(): rowGeo tells onclick() which voice row a click landed on, chipGeo
// the exact rect of each of the 6 per-voice toggle chips within that row (undefined entries when
// showDetail is false, i.e. the window is too narrow for the Art/Lec/Ton/Fijar cluster).
var rowGeo = null;
var chipGeo = [];

function ptIn(r, x, y) {
	return r && x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h;
}

function drawChip(r, label, on) {
	mgraphics.set_source_rgba(on ? [0.55, 0.42, 0.15, 1] : [0.22, 0.22, 0.25, 1]);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.fill();
	mgraphics.set_source_rgba([0, 0, 0, 0.5]);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.stroke();
	mgraphics.set_source_rgba(on ? [1, 0.85, 0.55, 1] : [0.55, 0.55, 0.6, 1]);
	mgraphics.set_font_size(9);
	mgraphics.move_to(r.x + 3, r.y + r.h - 3);
	mgraphics.show_text(label);
}

// Click one of the 6 per-voice toggle chips -> send the same setvoice* message the "Voces N" tabs
// already send (prepend setvoice<name> #<voice 1-based>). Optimistic local update + redraw, same
// convention fs2setpick.js's own onclick() uses for its piano-key clicks -- never wait for the
// echo; emitVoiceKeyReadouts() will re-send a fresh vkey next cycle if anything is out of sync.
function onclick(x, y, but) {
	if (!but || !rowGeo) return;
	if (y < rowGeo.headH) return;
	var v = Math.floor((y - rowGeo.headH) / rowGeo.rowH);
	if (v < 0 || v >= rowGeo.nRows) return;
	var vk = vkeyInfo[v], cg = chipGeo[v];
	if (!vk || !cg) return;
	if (ptIn(cg.on, x, y)) { vk.muted = !vk.muted; outlet(0, ['setvoicemute', v + 1, vk.muted ? 1 : 0]); mgraphics.redraw(); return; }
	if (ptIn(cg.ext, x, y)) { vk.ext = !vk.ext; outlet(0, ['setvoiceexternal', v + 1, vk.ext ? 1 : 0]); mgraphics.redraw(); return; }
	if (cg.art && ptIn(cg.art, x, y)) { vk.artOwn = !vk.artOwn; outlet(0, ['setvoiceartown', v + 1, vk.artOwn ? 1 : 0]); mgraphics.redraw(); return; }
	if (cg.lec && ptIn(cg.lec, x, y)) { vk.readOwn = !vk.readOwn; outlet(0, ['setvoicereadown', v + 1, vk.readOwn ? 1 : 0]); mgraphics.redraw(); return; }
	if (cg.ton && ptIn(cg.ton, x, y)) { vk.keyOwn = !vk.keyOwn; outlet(0, ['setvoicekeyown', v + 1, vk.keyOwn ? 1 : 0]); mgraphics.redraw(); return; }
	if (cg.fijar && ptIn(cg.fijar, x, y)) { var nl = vk.keyLock === 1 ? 0 : 1; vk.keyLock = nl; outlet(0, ['setvoicekeylock', v + 1, nl]); mgraphics.redraw(); return; }
}

'''


def apply_engine(content):
    assert content.count(ENGINE_OLD) == 1, 'forteseq2.js: emitVoiceKeyReadouts() no calzo (0 o >1 match)'
    return content.replace(ENGINE_OLD, ENGINE_NEW, 1)


def apply_horizon(content):
    for label, old, new in HZ_EDITS:
        n = content.count(old)
        assert n == 1, 'fs2horizon.js: "%s" no calzo (%d matches, esperaba 1)' % (label, n)
        content = content.replace(old, new, 1)
    assert content.count('function paint() {') == 1
    assert 'function onclick' not in content, 'fs2horizon.js: ya tiene onclick() -- ya aplicado?'
    content = content.replace('function paint() {', ONCLICK_BLOCK + 'function paint() {', 1)
    return content


def main():
    apply_it = '--apply' in sys.argv

    engine_src = open(ENGINE_JS, encoding='utf-8').read()
    engine_new = apply_engine(engine_src)

    horizon_src = open(HORIZON_JS, encoding='utf-8').read()
    horizon_new = apply_horizon(horizon_src)

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    win = bx[WIN_ID]
    subP = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in subP['boxes']}
    assert sbx['obj-2']['filename'] == 'fs2horizon.js' and sbx['obj-4']['maxclass'] == 'outlet'
    assert not any(l['patchline']['source'] == ['obj-2', 0] for l in subP['lines']), 'obj-2 ya tiene wire de outlet -- ya aplicado?'
    assert any(l['patchline']['source'] == [WIN_ID, 0] and l['patchline']['destination'] == ['obj-23', 0] for l in P['lines']), \
        'no encontre el cable obj-751 -> obj-23 (deberia existir sin tocar)'

    subP['lines'].append({'patchline': {'source': ['obj-2', 0], 'destination': ['obj-4', 0]}})

    print('forteseq2.js: emitVoiceKeyReadouts() ampliado (artOwn/ext/ornN/ornB/vec/diss/Z/modalidad/espejo)')
    print('fs2horizon.js: %d ediciones aplicadas + chipGeo/onclick/drawChip/ptIn insertados' % len(HZ_EDITS))
    print('inside %s: obj-2 (fs2horizon.js) outlet -> obj-4 (ya sale a obj-23, sin tocar ese cable)' % WIN_ID)

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-voicecontrols')
    open(ENGINE_JS, 'w', encoding='utf-8', newline='\n').write(engine_new)
    open(HORIZON_JS, 'w', encoding='utf-8', newline='\n').write(horizon_new)
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    win2 = bx2[WIN_ID]['patcher']
    assert any(l['patchline']['source'] == ['obj-2', 0] and l['patchline']['destination'] == ['obj-4', 0]
               for l in win2['lines'])

    print('\nescrito %s, %s, %s (.before-voicecontrols del .amxd guardado). Sigue:' % (ENGINE_JS, HORIZON_JS, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, la fs2horizon jsui, el device completo, script stop/start')


main()
