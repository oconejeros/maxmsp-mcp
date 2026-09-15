// fs2horizon.js -- jsui: the "próximos pasos" panel for FORTESEQ2's floating window.
//
// A fixed GLOBAL sidebar (x=0..GLOBAL_W, drawn once, see paint()'s "fixed global sidebar" block)
// sits to the left of everything, always visible, in up to FOUR columns, each with FIXED row
// indices (no dynamic per-column counter) so nothing in one column ever shifts because of what's
// happening in another:
//   col 1 -- Run/Ind/Flt/Lck/Dir/Patron/Enlace (Run first -- the transport; Dir above Patron on
//     request; Enlace/linkMin -- the common-tone constraint on the next set -- appended last).
//   col 2 -- Set/Root/R.Arm/Orden/Rango/PresetSilencio/SilNorm+SilAcc (the last row -- groupSilence
//     -- is what a Preset Silencio pick on the row above only OVERWRITES; worth its own row).
//   col 3 -- the Ornamento cluster (Tipo/Notas+Base/BaseModo), drawn ONLY while Patron===Ornamento
//     (`ornOpen`); GLOBAL_W itself grows to make room for it (see paint()'s GLOBAL_W formula) --
//     the one thing that DOES move when Ornamento toggles is the lookahead grid getting narrower,
//     never col 1/2's own content. Mode-specific rows appear at the BOTTOM of this same column,
//     mutually exclusive since ornBaseMode is a single value -- costs nothing extra either way
//     (nothing below them to push, GLOBAL_W already fixed by ornOpen alone): Esquema Cuarteto
//     (QUAD_SCHEME_NAMES) while ornBaseMode is Cuarteto; Orn Base Paso while it's Grados; Orn Serie
//     Inicio/Paso (one row) + Pico (another) while it's Serie. Orn Base Interval itself (col 3 row
//     1's "ornbase" chip, alongside Notas) stays unconditional -- pre-existing, out of scope here.
//   col 4 -- the Filtro cluster (n min/n max, Modo Mask, Mask k + Mask Fit), drawn ONLY while Flt is
//     on (`filtOpen`) -- same GLOBAL_W-grows-not-reflows deal as col 3. Mask k only joins Mask Fit
//     on its row while Modo Mask is Int (MASK_MODE_INT); every other mode ignores Mask k entirely,
//     same as the engine's own maskOk() branches. The raw 12-bit chromatic mask stays out (that's
//     fs2setpick.js's piano-UI territory, a click-grid rather than a knob), and so does the 6-pair
//     Vector IC (interval-class min/max) -- composition-time fine-tuning, same call as leaving
//     Tension/Curva/Modelo/Prog Favoritos out next to Enlace in col 1.
//   Ornamento (col 3) and Filtro (col 4) pack into the sidebar's conditional slots left to right
//     with no gap between them -- Ornamento always claims the first free slot when open, Filtro
//     takes whichever is left -- so either, both, or neither can be showing at once.
//   Run is the one field with no gecho/querynext mirror: obj-18 ("Run") bypasses forteseq2.js
//     entirely, gating the metro straight at the Max-patching level, so it has its own independent
//     read (hrun, tapped off obj-18's own outlet via send/receive FS2_RUN_STATE) and write (a plain
//     `outlet(0, ['run', v])`, intercepted by a `route run` fed in parallel off the same source that
//     feeds obj-819, NOT through the engine) -- see add_fs2_run_sync.py.
// All for the SHARED values every voice falls back to when its own "Propia" override is off --
// same chip/dropdown/drag-scrub language as the per-voice rows, populated by hstatus/ornbasemode/
// groot/gornament/gflags/gharm/gorden/grango/gsilpre (see those handlers) into `globalState`, and
// hit-tested in onclick() via `globalChipGeo` using the v=-1 sentinel throughout (openMenu,
// dragBox, DRAG_SPECS' `global: true` entries). Orden/Rango/PresetSilencio are setup-time globals
// (traversal order, voicing range template, articulation silence preset) rather than per-voice
// performance ones, added anyway on request -- Rango/PresetSilencio are "apply this preset" fire-
// and-forget actions engine-side (rangeTemplateIndex/silencePresetIndex just record what was last
// picked, for this readout), unlike Orden which is real persistent state (orderMode). Modo
// (Acordes/Arpegio) is read into globalState.mode (hstatus) and used internally (see keyMoot/
// readMoot below) but has NO chip here -- setmode() has no existing panel-side control to
// cross-check against, unlike every other global setter here, so it stayed engine-only.
//
// One ROW per voice, to the right of the global sidebar. Each row is:
// [ label+toggles ]  [ pattern grid ]  [ history ]
//   history  -- up to HIST_MAX notes already played, at the row's far right; the newest sits at
//              the block's own LEFT edge (against the grid boundary) and each note drifts right
//              as newer ones arrive, dimming with age, until it falls off the row's right edge.
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
//   hstatus  <readMode> <readDir> <setIdx1> <mode> <locked>  -- the config line at the bottom;
//            also mirrored into globalState (patron/dir/setIdx/mode/locked) for the sidebar.
//   groot <root>  gornament <ornType> <ornCount> <ornBaseInterval>  gflags <indep> <filtered>
//   gharm <harmRate>  gorden <orderMode>  grango <rangeTemplateIndex>  gsilpre <silencePresetIndex>
//   gornquad <ornQuadScheme>  gornstep <ornBaseStep>
//   gornseries <ornSeriesStart> <ornSeriesStep> <ornSeriesPeak>
//   gsilence <groupSilence[NORMAL]> <groupSilence[ACCENT]>  genlace <linkMin>
//   gcard <cardMin> <cardMax>  gmaskmode <maskMode>  gmaskk <maskK>  gmaskfit <maskFit>
//            -- the rest of globalState: none of these have a per-voice override, so one debounced
//            emit each covers every row equally (see querynext() in forteseq2.js). hrun is the one
//            exception -- NOT sent by forteseq2.js/querynext at all, see the sidebar note above.
//   hshape   <n> <cols> <rawL> <d0..>  -- the STATIC reading-order strip: which degree index the
//            shape reads at each position of one full cycle (downsampled if rawL > cols). One
//            shared row under the grid. cols 0 = hide (chord mode). Sent only on shape change.
//   hshapecur <pos>  -- cursor column within that strip, one number per tick.
//   ornscale <count> <forte> <vec> <is12> <pc0..>  -- READ_ORNAMENT's resulting scale (Slonimsky's
//            Master Chord): the pitch-class aggregate of one ornament pass. count 0 = clear (any
//            other reading order). Drawn as a 12-chip strip + label above the status line.
//   ornbasemode <mode>  -- global ornBaseMode (ORN_BASE_INTERVAL/DEGREES/QUADRITONE/SERIES), no
//            per-voice override. Only DEGREES actually reads a voice's set; every row whose Patron
//            is Ornamento under any other base mode dims its forte/vector/Z-modality lines and
//            hides its Set box (setMoot in paint()) -- the set is real but has no effect there.
//            Separately, TonProp (Ton) and Lectura Propia (Lec) only take effect while a voice is
//            self-cursored -- its own Ext, or the global Ind while in Arpegio (voiceSelfCursored()
//            in forteseq2.js; the shared-clock path every other row falls back to never reads
//            voiceKeyOwn/voiceReadMode/voiceReadDir at all). Off that, paint() dims the forte/
//            tonic/vector/Z-modality lines (keyMoot/keyDim) and the Patron/Dir/Ornamento lines
//            (readMoot/readDim), and hides the Set/Patron/Dir/OrnTipo/OrnNotas/OrnBase controls
//            those toggles would otherwise unlock -- same "real but inert" treatment as setMoot.
//   vkey <v> <forte> <tonica> <keyOwn> <readOwn> <patron> <dir> <ornTipo> <muted> <keyLock>
//        <artOwn> <ext> <ornNotas> <ornBase> <vector> <disonancia> <zRel> <modalidad> <espejo>
//        <setIdx> <velMin> <velMax> <durDiv> <silence> <grado> <div> <euLarg> <euPuls> <euGir>
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
//            glance tells sounding voices from silent ones. Once Lec is on, a Patron dropdown
//            appears right under Ext (gate column) and a Dir cycling chip appears in the detail
//            cluster; once Patron is actually Ornamento, an OrnTipo dropdown appears below Dir, and
//            OrnNotas/OrnBase (count/interval) appear side by side below THAT. Once Ton is on, a
//            Set box (setIdx, cardinal 1-351 -- sets[] is already sorted that way) appears below
//            Patron in the gate column. Patron/OrnTipo open a floating list (openMenu/menuItemGeo,
//            drawn last in paint() so it sits above every row) instead of cycling -- 8 and 6 values
//            respectively is a lot to click through one at a time; Dir (3 values) stays a plain
//            cycling chip; Set/OrnNotas/OrnBase (wide numeric ranges) are click-drag scrub boxes
//            instead (dragBox/ondrag(), the same up=increase convention as Max's own numbox).
//            velMin/velMax/durDiv/silence (Articulacion) are this voice's own values regardless of
//            whether artOwn is on -- unlike Patron/Ornamento there is no single "shared" value to
//            fall back to (the shared side varies by accent-grid group, Normal vs Acento), so the
//            popup just always shows the voice's own numbers, same gate-by-artOwn-only treatment
//            as Set/keyOwn; drawn as two more click-drag rows once artOwn is on. grado/div/euLarg/
//            euPuls/euGir (reharmonization offset, clock divider, per-voice Euclidean gate) have
//            NO gate at all, same as their panel controls -- always-visible rows. Trig (fires this
//            voice's own cursor by hand) is a momentary button, no stored value, no gate either.
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
var READ_ORNAMENT = 7;   // same value as forteseq2.js's READ_ORNAMENT -- shows the OrnTipo chip
// Abbreviations for the narrow Patron/Dir chips (dcw is only ~43px) -- the full READ_NAMES/
// DIR_NAMES strings are used everywhere else (the label block, OrnTipo's wider chip).
var PATRON_ABBR = ['Recto', 'Súper', 'SMin', 'Modos', 'Coprim', 'Zigzag', 'Urna', 'Ornam'];
var DIR_ABBR = ['Adel', 'Atrs', 'Alt'];
var ORN_BASE_MODE_NAMES = ['Intervalo', 'Grados', 'Cuarteto', 'Serie'];
var ORN_BASE_QUADRITONE = 2;   // same value as forteseq2.js's ORN_BASE_QUADRITONE
var ORN_BASE_SERIES = 3;       // same value as forteseq2.js's ORN_BASE_SERIES
// Orn Base Cuarteto's own scheme -- only meaningful (and only shown, col 3 row 3) while
// globalState.ornBaseMode === ORN_BASE_QUADRITONE, same names as forteseq2.js's QUAD_SCHEME_NAMES
// and the real panel widget (fs2_obj_775, "Orn Base Cuarteto").
var QUAD_SCHEME_NAMES = ['4 Aumentadas', 'Aum+May+men+dim', '2dim+May+men'];
// Second sidebar column (setup-time globals, not per-voice): same enum-index-to-label idiom as
// everything above. Orden's index 0 ("Card") is a real value (ORDER_CARD in forteseq2.js);
// Rango/Preset Silencio's index 0 is the menu's own category label / "nothing applied yet" --
// same distinction the panel's own live.menu widgets already draw, nothing special to handle here.
var ORDER_NAMES = ['Card', 'Forte', 'Cons', 'Vec', 'McKay', 'Natural', 'Modal'];
var RANGE_NAMES = ['Rango', 'Libre', 'SATB', 'Cuerdas', 'Maderas', 'Metales', 'Teclado', 'Ancho', 'Cluster'];
var SILPRE_NAMES = ['Silencio', 'Todo', 'Solo ac.', 'Solo norm.', 'Ralo', 'Muy ralo'];
// Fourth sidebar column (the Filtro cluster), same idiom, names copied straight from the real
// panel widget's own parameter_enum (fs2_maskmode) so the popup never disagrees with the panel.
var MASK_MODE_NAMES = ['Sub', 'Con', 'Int'];
var MASK_MODE_INT = 2;   // same value as forteseq2.js's maskMode===2 branch -- Mask k only matters here

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

// Everything the fixed global sidebar (paint()'s "global column" block) reads and writes -- the
// shared value every voice falls back to when its own "Propia" override is off. Populated from
// hstatus/ornbasemode (already sent for the status line/setMoot -- now also mirrored here) plus
// the 3 new messages below (groot/gornament/gflags/gharm), all debounced engine-side the same way.
var globalState = { patron: 0, dir: 0, mode: 1, locked: 0, setIdx: 1, root: 0,
	indep: false, filtered: false, harmRate: 0, ornType: 0, ornCount: 1, ornBase: 4, ornBaseMode: 0,
	orden: 0, rango: 0, silpre: 0, run: 0, ornQuad: 0,
	ornStep: 1, ornSeriesStart: 1, ornSeriesStep: 1, ornSeriesPeak: 4,
	silNorm: 0, silAcc: 0, enlace: 0,
	cardMin: 1, cardMax: 12, maskMode: 0, maskK: 1, maskFit: 1 };

function hstatus(rm, rd, setIdx1, md, lockedFlag) {
	status = [Math.round(rm), Math.round(rd), Math.round(setIdx1), Math.round(md), Math.round(lockedFlag || 0)];
	globalState.patron = Math.round(rm);
	globalState.dir = Math.round(rd);
	globalState.setIdx = Math.round(setIdx1);
	globalState.mode = Math.round(md);
	globalState.locked = Math.round(lockedFlag || 0);
	mgraphics.redraw();
}

// Global (no per-voice override -- see forteseq2.js's own ornBaseMode). ORN_BASE_DEGREES (1) is
// the only base mode that reads the set at all; every other one (Interval/Quadritone/Series) picks
// its principal tones from a fixed interval pattern that never touches pcs[]. Used to dim the
// forte/vector/Z-modality lines and hide the Set scrub box for a voice whose Patron is Ornamento
// under one of those set-blind base modes -- its Set genuinely has no effect on what it plays.
var ornBaseMode = 0;
var ORN_BASE_DEGREES = 1;   // same value as forteseq2.js's ORN_BASE_DEGREES
function ornbasemode(m) {
	ornBaseMode = Math.round(m);
	globalState.ornBaseMode = ornBaseMode;
	mgraphics.redraw();
}

function groot(r) { globalState.root = Math.round(r); mgraphics.redraw(); }
function gornament(t, c, b) {
	globalState.ornType = Math.round(t);
	globalState.ornCount = Math.round(c);
	globalState.ornBase = Math.round(b);
	mgraphics.redraw();
}
function gflags(ind, filt) {
	globalState.indep = !!Math.round(ind);
	globalState.filtered = !!Math.round(filt);
	mgraphics.redraw();
}
function gharm(r) { globalState.harmRate = Math.round(r); mgraphics.redraw(); }
function gorden(m) { globalState.orden = Math.round(m); mgraphics.redraw(); }
function grango(t) { globalState.rango = Math.round(t); mgraphics.redraw(); }
function gsilpre(t) { globalState.silpre = Math.round(t); mgraphics.redraw(); }
function gornquad(s) { globalState.ornQuad = Math.round(s); mgraphics.redraw(); }
function gornstep(s) { globalState.ornStep = Math.round(s); mgraphics.redraw(); }
function gornseries(a, b, c) {
	globalState.ornSeriesStart = Math.round(a);
	globalState.ornSeriesStep = Math.round(b);
	globalState.ornSeriesPeak = Math.round(c);
	mgraphics.redraw();
}
// Run (obj-18, "Arranca y detiene el motor") never goes through forteseq2.js at all -- it gates
// the metro directly at the Max-patching level (see add_fs2_run_sync.py). This is the one global
// sidebar field with no gecho/querynext mirror behind it: hrun() is fed straight from a second,
// independent tap on obj-18's own outlet (send FS2_RUN_STATE), so it reflects a click on the panel
// toggle exactly the same as a click here.
function hrun(v) { globalState.run = Math.round(v) ? 1 : 0; mgraphics.redraw(); }
function gsilence(a, b) { globalState.silNorm = Math.round(a); globalState.silAcc = Math.round(b); mgraphics.redraw(); }
function genlace(n) { globalState.enlace = Math.round(n); mgraphics.redraw(); }
function gcard(a, b) { globalState.cardMin = Math.round(a); globalState.cardMax = Math.round(b); mgraphics.redraw(); }
function gmaskmode(m) { globalState.maskMode = Math.round(m); mgraphics.redraw(); }
function gmaskk(k) { globalState.maskK = Math.round(k); mgraphics.redraw(); }
function gmaskfit(f) { globalState.maskFit = Math.round(f) ? 1 : 0; mgraphics.redraw(); }

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
function vkey(v, forte, tonic, keyOwn, readOwn, patron, dir, ornT, muted, keyLock,
		artOwn, ext, ornN, ornB, vec, diss, zRel, modality, mirror, setIdx,
		velMin, velMax, durDiv, silence, grado, div, euLarg, euPuls, euGir) {
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
		zRel: String(zRel || "-"), modality: String(modality || "-"), mirror: String(mirror || "-"),
		setIdx: Math.round(setIdx === undefined ? 1 : setIdx),
		velMin: Math.round(velMin === undefined ? 55 : velMin),
		velMax: Math.round(velMax === undefined ? 80 : velMax),
		durDiv: Math.round(durDiv === undefined ? 16 : durDiv),
		silence: Math.round(silence === undefined ? 0 : silence),
		grado: Math.round(grado === undefined ? 0 : grado),
		div: Math.round(div === undefined ? 1 : div),
		euLarg: Math.round(euLarg === undefined ? 0 : euLarg),
		euPuls: Math.round(euPuls === undefined ? 0 : euPuls),
		euGir: Math.round(euGir === undefined ? 0 : euGir)
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
		mgraphics.set_font_size(w >= 26 ? 14 : 10);
		mgraphics.move_to(x + w / 2 - name.length * (w >= 26 ? 4.0 : 2.8), y + h / 2 + 4);
		mgraphics.show_text(name);
		if (w >= 24) {
			var oct = Math.floor(note / 12) - 1;   // MIDI 60 = C4
			mgraphics.set_font_size(9);
			mgraphics.move_to(x + w - 11, y + 11);
			mgraphics.show_text(String(oct));
		}
	}
}

// Geometry of the last paint(): rowGeo tells onclick() which voice row a click landed on, chipGeo
// the exact rect of each of the 6 per-voice toggle chips within that row (undefined entries when
// showDetail is false, i.e. the window is too narrow for the Art/Lec/Ton/Fijar cluster).
var rowGeo = null;
var chipGeo = [];
// Same idea as chipGeo but for the fixed global sidebar (paint()'s "global column" block) --
// singular, not per-voice, rebuilt once per paint(). Hit-tested by onclick() before the per-row
// logic, using the v=-1 sentinel throughout (see DRAG_SPECS/openMenu/dragBox above).
var globalChipGeo = {};
// Dropdown state for the Patron/OrnTipo chips (Dir stays a plain cycling chip, only 3 values).
// At most one open at a time; menuItemGeo is rebuilt every paint() from whichever row/kind is
// open, same "rebuilt each frame, hit-tested by onclick()" convention as chipGeo/rowGeo above.
var openMenu = null;      // { v, kind: 'patron'|'ornt' } or null
var menuItemGeo = [];

// Set/OrnNotas/OrnBase are plain numbers over a wide-ish range -- a dropdown list (351 entries for
// Set!) or a cycling chip would both be unusable, so these scrub vertically instead, the same
// click-drag convention Max's own live.numbox already uses (and that the panel's Set/OrnNotas/
// OrnBase controls already are). onclick() only arms dragBox (a plain click changes nothing, same
// as numbox); ondrag() -- a real jsui callback, see harmonograph_ui.js's onclick/ondrag pair for
// the precedent -- does the actual scrubbing and sends the message, one voice/field at a time.
var dragBox = null;   // { v, kind, startY, startVal } or null -- v === -1 means the global sidebar, not a voice
// Each spec's send(v, nv, state) builds and fires the actual outlet(0, [...]) message: `v` is the
// 0-based voice index (ignored by global specs, which carry no voice number at all) and `state` is
// vkeyInfo[v] for a per-voice spec or globalState for a `global: true` one -- Articulacion's 4
// fields need it because setvoicearticulation() takes all 4 at once, so nudging just one still has
// to resend the other 3 unchanged (reading them back out of the same row's current vkeyInfo).
var DRAG_SPECS = {
	setbox: { min: 1, max: 351, field: 'setIdx', pxPerUnit: 4,
		send: function (v, nv) { outlet(0, ['setvoicesetindex', v + 1, nv]); } },
	ornnotas: { min: 1, max: 4, field: 'ornN', pxPerUnit: 16,
		send: function (v, nv) { outlet(0, ['setvoiceorncount', v + 1, nv]); } },
	ornbase: { min: 1, max: 14, field: 'ornB', pxPerUnit: 10,
		send: function (v, nv) { outlet(0, ['setvoiceornbase', v + 1, nv]); } },
	grado: { min: -8, max: 8, field: 'grado', pxPerUnit: 8,
		send: function (v, nv) { outlet(0, ['setvoicedegoffset', v + 1, nv]); } },
	div: { min: 1, max: 16, field: 'div', pxPerUnit: 10,
		send: function (v, nv) { outlet(0, ['setvoicediv', v + 1, nv]); } },
	euclen: { min: 0, max: 16, field: 'euLarg', pxPerUnit: 8,
		send: function (v, nv) { outlet(0, ['setvoiceeuclen', v + 1, nv]); } },
	euck: { min: 0, max: 16, field: 'euPuls', pxPerUnit: 8,
		send: function (v, nv) { outlet(0, ['setvoiceeuck', v + 1, nv]); } },
	eucrot: { min: 0, max: 15, field: 'euGir', pxPerUnit: 10,
		send: function (v, nv) { outlet(0, ['setvoiceeucrot', v + 1, nv]); } },
	artvmin: { min: 1, max: 127, field: 'velMin', pxPerUnit: 3,
		send: function (v, nv, vk) { outlet(0, ['setvoicearticulation', v + 1, nv, vk.velMax, vk.durDiv, vk.silence]); } },
	artvmax: { min: 1, max: 127, field: 'velMax', pxPerUnit: 3,
		send: function (v, nv, vk) { outlet(0, ['setvoicearticulation', v + 1, vk.velMin, nv, vk.durDiv, vk.silence]); } },
	artdur: { min: 1, max: 32, field: 'durDiv', pxPerUnit: 6,
		send: function (v, nv, vk) { outlet(0, ['setvoicearticulation', v + 1, vk.velMin, vk.velMax, nv, vk.silence]); } },
	artsil: { min: 0, max: 100, field: 'silence', pxPerUnit: 4,
		send: function (v, nv, vk) { outlet(0, ['setvoicearticulation', v + 1, vk.velMin, vk.velMax, vk.durDiv, nv]); } },
	// Global sidebar (v === -1 sentinel, no voice index in the outgoing message) -- see paint()'s
	// global-column block and onclick()'s v===-1 branch.
	gset: { min: 1, max: 351, field: 'setIdx', pxPerUnit: 4, global: true,
		send: function (v, nv) { outlet(0, ['setlockindex', nv]); } },
	groot: { min: -24, max: 24, field: 'root', pxPerUnit: 4, global: true,
		send: function (v, nv) { outlet(0, ['setroot', nv]); } },
	gornnotas: { min: 1, max: 4, field: 'ornCount', pxPerUnit: 16, global: true,
		send: function (v, nv) { outlet(0, ['setorncount', nv]); } },
	gornbase: { min: 1, max: 14, field: 'ornBase', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setornbaseinterval', nv]); } },
	gharm: { min: 0, max: 64, field: 'harmRate', pxPerUnit: 6, global: true,
		send: function (v, nv) { outlet(0, ['setharmrate', nv]); } },
	// Col 3's mode-specific rows (Grados/Serie), same global-sidebar idiom -- see paint()'s col 3
	// block for which one is actually drawn (mutually exclusive, gated by globalState.ornBaseMode).
	gornstep: { min: 1, max: 4, field: 'ornStep', pxPerUnit: 16, global: true,
		send: function (v, nv) { outlet(0, ['setornbasestep', nv]); } },
	gserstart: { min: 1, max: 6, field: 'ornSeriesStart', pxPerUnit: 12, global: true,
		send: function (v, nv) { outlet(0, ['setornseriesstart', nv]); } },
	gserstep: { min: 1, max: 4, field: 'ornSeriesStep', pxPerUnit: 16, global: true,
		send: function (v, nv) { outlet(0, ['setornseriesstep', nv]); } },
	gserpeak: { min: 1, max: 8, field: 'ornSeriesPeak', pxPerUnit: 8, global: true,
		send: function (v, nv) { outlet(0, ['setornseriespeak', nv]); } },
	// Col 1's Enlace and col 2's Silencio Normal/Acento -- same global-sidebar idiom, see paint().
	genlace: { min: 0, max: 6, field: 'enlace', pxPerUnit: 14, global: true,
		send: function (v, nv) { outlet(0, ['setlink', nv]); } },
	gsilnorm: { min: 0, max: 100, field: 'silNorm', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setgroupsilence', 0, nv]); } },
	gsilacc: { min: 0, max: 100, field: 'silAcc', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setgroupsilence', 1, nv]); } },
	// Col 4 (Filtro cluster), same global-sidebar idiom, see paint()'s filtOpen block.
	gnmin: { min: 1, max: 12, field: 'cardMin', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setcardmin', nv]); } },
	gnmax: { min: 1, max: 12, field: 'cardMax', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setcardmax', nv]); } },
	gmaskk: { min: 1, max: 12, field: 'maskK', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setmaskk', nv]); } }
};

// "Pagina" (fs2_pagina) values for the tabs each advanced chip's real control lives on -- see
// add_fs2_gotopage.py for how these were measured. On/mute (cg.on) has no page: its control is
// always on the main panel, never gated by Pagina.
var PAGE_VOCES1 = 6, PAGE_VOCES2 = 7, PAGE_VOCES3 = 9, PAGE_VOCES4 = 10;

function ptIn(r, x, y) {
	return r && x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h;
}

function drawChip(r, label, on, disabled, dim) {
	dim = dim === undefined ? 1 : dim;
	mgraphics.set_source_rgba(on ? [0.55 * dim, 0.42 * dim, 0.15 * dim, 1] : [0.22, 0.22, 0.25, 1]);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.fill();
	mgraphics.set_source_rgba([0, 0, 0, 0.5]);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.stroke();
	mgraphics.set_source_rgba(on ? [1 * dim, 0.85 * dim, 0.55 * dim, 1] : (disabled ? [0.4, 0.4, 0.44, 1] : [0.55, 0.55, 0.6, 1]));
	mgraphics.set_font_size(11);
	mgraphics.move_to(r.x + 3, r.y + r.h - 4);
	mgraphics.show_text(label);
}

// Click one of the 6 per-voice toggle chips -> send the same setvoice* message the "Voces N" tabs
// already send (prepend setvoice<name> #<voice 1-based>). Optimistic local update + redraw, same
// convention fs2setpick.js's own onclick() uses for its piano-key clicks -- never wait for the
// echo; emitVoiceKeyReadouts() will re-send a fresh vkey next cycle if anything is out of sync.
function onclick(x, y, but) {
	if (!but || !rowGeo) return;
	// A dropdown is open: hitting one of its items selects it, anything else just closes the menu.
	// Handled before the row lookup below because the open list can extend past its own row's
	// bounds (it floats above whatever paint() drew there last frame).
	if (openMenu) {
		for (var mi = 0; mi < menuItemGeo.length; mi++) {
			if (ptIn(menuItemGeo[mi], x, y)) {
				if (openMenu.v === -1) {
					if (openMenu.kind === 'gpatron') {
						globalState.patron = mi;
						outlet(0, ['setreadmode', mi]);
					} else if (openMenu.kind === 'gornt') {
						globalState.ornType = mi;
						outlet(0, ['setorntype', mi]);
					} else if (openMenu.kind === 'gornbasemode') {
						globalState.ornBaseMode = mi;
						outlet(0, ['setornbasemode', mi]);
					} else if (openMenu.kind === 'gorden') {
						globalState.orden = mi;
						outlet(0, ['setorder', mi]);
					} else if (openMenu.kind === 'grango') {
						globalState.rango = mi;
						outlet(0, ['setrangetemplate', mi]);
					} else if (openMenu.kind === 'gsilpre') {
						globalState.silpre = mi;
						outlet(0, ['setsilencepreset', mi]);
					} else if (openMenu.kind === 'gornquad') {
						globalState.ornQuad = mi;
						outlet(0, ['setornquadscheme', mi]);
					} else if (openMenu.kind === 'gmaskmode') {
						globalState.maskMode = mi;
						outlet(0, ['setmaskmode', mi]);
					}
				} else {
					var vkm = vkeyInfo[openMenu.v];
					if (vkm) {
						if (openMenu.kind === 'patron') {
							vkm.patron = mi;
							outlet(0, ['setvoicereadmode', openMenu.v + 1, mi]);
						} else if (openMenu.kind === 'ornt') {
							vkm.ornT = mi;
							outlet(0, ['setvoiceorntype', openMenu.v + 1, mi]);
							outlet(0, ['gotopage', PAGE_VOCES3]);
						}
					}
				}
				openMenu = null; menuItemGeo = [];
				mgraphics.redraw(); return;
			}
		}
		openMenu = null; menuItemGeo = [];
		mgraphics.redraw(); return;
	}
	// The fixed global sidebar -- checked before the per-row lookup below since it isn't part of
	// any voice row (x never overlaps a row's own chips, but checking explicitly here avoids
	// wastefully falling through to the row-hit math on every sidebar click).
	if (ptIn(globalChipGeo.run, x, y)) { globalState.run = globalState.run ? 0 : 1; outlet(0, ['run', globalState.run]); mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.ind, x, y)) { globalState.indep = !globalState.indep; outlet(0, ['setvoiceindep', globalState.indep ? 1 : 0]); mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.flt, x, y)) { globalState.filtered = !globalState.filtered; outlet(0, ['setfilter', globalState.filtered ? 1 : 0]); mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.lck, x, y)) { globalState.locked = globalState.locked ? 0 : 1; outlet(0, ['setlock', globalState.locked]); mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.patron, x, y)) { openMenu = { v: -1, kind: 'gpatron' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.dir, x, y)) { globalState.dir = (Math.round(globalState.dir) + 1) % 3; outlet(0, ['setreaddir', globalState.dir]); mgraphics.redraw(); return; }
	if (globalChipGeo.ornt && ptIn(globalChipGeo.ornt, x, y)) { openMenu = { v: -1, kind: 'gornt' }; mgraphics.redraw(); return; }
	if (globalChipGeo.ornnotas && ptIn(globalChipGeo.ornnotas, x, y)) { dragBox = { v: -1, kind: 'gornnotas', startY: y, startVal: globalState.ornCount }; return; }
	if (globalChipGeo.ornbase && ptIn(globalChipGeo.ornbase, x, y)) { dragBox = { v: -1, kind: 'gornbase', startY: y, startVal: globalState.ornBase }; return; }
	if (globalChipGeo.ornbasemode && ptIn(globalChipGeo.ornbasemode, x, y)) { openMenu = { v: -1, kind: 'gornbasemode' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.set, x, y)) { dragBox = { v: -1, kind: 'gset', startY: y, startVal: globalState.setIdx }; return; }
	if (ptIn(globalChipGeo.root, x, y)) { dragBox = { v: -1, kind: 'groot', startY: y, startVal: globalState.root }; return; }
	if (ptIn(globalChipGeo.harm, x, y)) { dragBox = { v: -1, kind: 'gharm', startY: y, startVal: globalState.harmRate }; return; }
	if (ptIn(globalChipGeo.orden, x, y)) { openMenu = { v: -1, kind: 'gorden' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.rango, x, y)) { openMenu = { v: -1, kind: 'grango' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.silpre, x, y)) { openMenu = { v: -1, kind: 'gsilpre' }; mgraphics.redraw(); return; }
	if (globalChipGeo.ornquad && ptIn(globalChipGeo.ornquad, x, y)) { openMenu = { v: -1, kind: 'gornquad' }; mgraphics.redraw(); return; }
	if (globalChipGeo.ornstep && ptIn(globalChipGeo.ornstep, x, y)) { dragBox = { v: -1, kind: 'gornstep', startY: y, startVal: globalState.ornStep }; return; }
	if (globalChipGeo.serstart && ptIn(globalChipGeo.serstart, x, y)) { dragBox = { v: -1, kind: 'gserstart', startY: y, startVal: globalState.ornSeriesStart }; return; }
	if (globalChipGeo.serstep && ptIn(globalChipGeo.serstep, x, y)) { dragBox = { v: -1, kind: 'gserstep', startY: y, startVal: globalState.ornSeriesStep }; return; }
	if (globalChipGeo.serpeak && ptIn(globalChipGeo.serpeak, x, y)) { dragBox = { v: -1, kind: 'gserpeak', startY: y, startVal: globalState.ornSeriesPeak }; return; }
	if (ptIn(globalChipGeo.enlace, x, y)) { dragBox = { v: -1, kind: 'genlace', startY: y, startVal: globalState.enlace }; return; }
	if (ptIn(globalChipGeo.silnorm, x, y)) { dragBox = { v: -1, kind: 'gsilnorm', startY: y, startVal: globalState.silNorm }; return; }
	if (ptIn(globalChipGeo.silacc, x, y)) { dragBox = { v: -1, kind: 'gsilacc', startY: y, startVal: globalState.silAcc }; return; }
	if (globalChipGeo.nmin && ptIn(globalChipGeo.nmin, x, y)) { dragBox = { v: -1, kind: 'gnmin', startY: y, startVal: globalState.cardMin }; return; }
	if (globalChipGeo.nmax && ptIn(globalChipGeo.nmax, x, y)) { dragBox = { v: -1, kind: 'gnmax', startY: y, startVal: globalState.cardMax }; return; }
	if (globalChipGeo.maskmode && ptIn(globalChipGeo.maskmode, x, y)) { openMenu = { v: -1, kind: 'gmaskmode' }; mgraphics.redraw(); return; }
	if (globalChipGeo.maskk && ptIn(globalChipGeo.maskk, x, y)) { dragBox = { v: -1, kind: 'gmaskk', startY: y, startVal: globalState.maskK }; return; }
	if (globalChipGeo.maskfit && ptIn(globalChipGeo.maskfit, x, y)) { globalState.maskFit = globalState.maskFit ? 0 : 1; outlet(0, ['setmaskfit', globalState.maskFit]); mgraphics.redraw(); return; }
	if (y < rowGeo.headH) return;
	var v = Math.floor((y - rowGeo.headH) / rowGeo.rowH);
	if (v < 0 || v >= rowGeo.nRows) return;
	var vk = vkeyInfo[v], cg = chipGeo[v];
	if (!vk || !cg) return;
	if (ptIn(cg.on, x, y)) { vk.muted = !vk.muted; outlet(0, ['setvoicemute', v + 1, vk.muted ? 1 : 0]); mgraphics.redraw(); return; }
	if (ptIn(cg.ext, x, y)) {
		vk.ext = !vk.ext;
		outlet(0, ['setvoiceexternal', v + 1, vk.ext ? 1 : 0]);
		if (vk.ext) outlet(0, ['gotopage', PAGE_VOCES1]);
		mgraphics.redraw(); return;
	}
	if (cg.art && ptIn(cg.art, x, y)) {
		vk.artOwn = !vk.artOwn;
		outlet(0, ['setvoiceartown', v + 1, vk.artOwn ? 1 : 0]);
		if (vk.artOwn) outlet(0, ['gotopage', PAGE_VOCES2]);
		mgraphics.redraw(); return;
	}
	if (cg.lec && ptIn(cg.lec, x, y)) {
		vk.readOwn = !vk.readOwn;
		outlet(0, ['setvoicereadown', v + 1, vk.readOwn ? 1 : 0]);
		if (vk.readOwn) outlet(0, ['gotopage', PAGE_VOCES2]);
		mgraphics.redraw(); return;
	}
	if (cg.ton && ptIn(cg.ton, x, y)) {
		vk.keyOwn = !vk.keyOwn;
		if (!vk.keyOwn) vk.keyLock = 0;   // Fijar has no effect without TonProp -- keep it from looking "already on" if TonProp comes back
		outlet(0, ['setvoicekeyown', v + 1, vk.keyOwn ? 1 : 0]);
		if (vk.keyOwn) outlet(0, ['gotopage', PAGE_VOCES4]);
		mgraphics.redraw(); return;
	}
	if (cg.fijar && vk.keyOwn && ptIn(cg.fijar, x, y)) {
		var nl = vk.keyLock === 1 ? 0 : 1; vk.keyLock = nl;
		outlet(0, ['setvoicekeylock', v + 1, nl]);
		if (nl) outlet(0, ['gotopage', PAGE_VOCES4]);
		mgraphics.redraw(); return;
	}
	// Patron -- only actionable while this voice's own reading order is in use (readOwn). Opens the
	// dropdown (drawn in paint(), hit-tested above) instead of cycling in place -- 8 values is a lot
	// to click through one at a time. No gotopage here: Lec's own click already jumped to Voces2
	// (where Patron/Dir live) the moment it turned on.
	if (cg.patron && vk.readOwn && ptIn(cg.patron, x, y)) {
		openMenu = { v: v, kind: 'patron' };
		mgraphics.redraw(); return;
	}
	// Dir -- only 3 values, stays a plain cycling chip (no dropdown needed for that few).
	if (cg.dir && vk.readOwn && ptIn(cg.dir, x, y)) {
		vk.dir = (Math.round(vk.dir) + 1) % 3;
		outlet(0, ['setvoicereaddir', v + 1, vk.dir]);
		mgraphics.redraw(); return;
	}
	// OrnTipo -- only actionable when Patron is actually Ornamento. Also a dropdown now; the
	// gotopage-to-Voces3 send moves to the actual selection (see the menu-hit branch above) since
	// opening the list is not itself a commitment to a value.
	if (cg.ornt && vk.readOwn && vk.patron === READ_ORNAMENT && ptIn(cg.ornt, x, y)) {
		openMenu = { v: v, kind: 'ornt' };
		mgraphics.redraw(); return;
	}
	// Set -- only actionable while this voice has its own fixed set (keyOwn/TonProp); arms a drag
	// scrub (see ondrag() below) instead of changing anything on the click itself, same as clicking
	// a Max numbox without moving the mouse.
	if (cg.setbox && vk.keyOwn && ptIn(cg.setbox, x, y)) {
		dragBox = { v: v, kind: 'setbox', startY: y, startVal: vk.setIdx };
		return;
	}
	if (cg.ornnotas && vk.readOwn && vk.patron === READ_ORNAMENT && ptIn(cg.ornnotas, x, y)) {
		dragBox = { v: v, kind: 'ornnotas', startY: y, startVal: vk.ornN };
		return;
	}
	if (cg.ornbase && vk.readOwn && vk.patron === READ_ORNAMENT && ptIn(cg.ornbase, x, y)) {
		dragBox = { v: v, kind: 'ornbase', startY: y, startVal: vk.ornB };
		return;
	}
	// Trig -- fires this voice's own cursor one step by hand (external-trigger auditioning),
	// same as the panel's momentary "Trig" button. Not a stored value: no dragBox, no echo needed.
	if (cg.trig && ptIn(cg.trig, x, y)) {
		outlet(0, ['triggervoice', v + 1]);
		return;
	}
	// Grado/Div -- unconditional, same as the panel's "essential" strip (no "Propia" chip gates
	// them there either).
	if (cg.grado && ptIn(cg.grado, x, y)) {
		dragBox = { v: v, kind: 'grado', startY: y, startVal: vk.grado };
		return;
	}
	if (cg.div && ptIn(cg.div, x, y)) {
		dragBox = { v: v, kind: 'div', startY: y, startVal: vk.div };
		return;
	}
	// Ritmo euclidiano por voz -- also unconditional (Largo=0 already means "no pattern", the
	// panel doesn't gate these behind anything either).
	if (cg.euclen && ptIn(cg.euclen, x, y)) {
		dragBox = { v: v, kind: 'euclen', startY: y, startVal: vk.euLarg };
		return;
	}
	if (cg.euck && ptIn(cg.euck, x, y)) {
		dragBox = { v: v, kind: 'euck', startY: y, startVal: vk.euPuls };
		return;
	}
	if (cg.eucrot && ptIn(cg.eucrot, x, y)) {
		dragBox = { v: v, kind: 'eucrot', startY: y, startVal: vk.euGir };
		return;
	}
	// Articulacion values -- only actionable while this voice has its own Art on (artOwn).
	if (cg.artvmin && vk.artOwn && ptIn(cg.artvmin, x, y)) {
		dragBox = { v: v, kind: 'artvmin', startY: y, startVal: vk.velMin };
		return;
	}
	if (cg.artvmax && vk.artOwn && ptIn(cg.artvmax, x, y)) {
		dragBox = { v: v, kind: 'artvmax', startY: y, startVal: vk.velMax };
		return;
	}
	if (cg.artdur && vk.artOwn && ptIn(cg.artdur, x, y)) {
		dragBox = { v: v, kind: 'artdur', startY: y, startVal: vk.durDiv };
		return;
	}
	if (cg.artsil && vk.artOwn && ptIn(cg.artsil, x, y)) {
		dragBox = { v: v, kind: 'artsil', startY: y, startVal: vk.silence };
		return;
	}
}

// Vertical click-drag scrub for Set/OrnNotas/OrnBase, armed by onclick() above (dragBox holds
// which voice/field and where the gesture started). Up = increase, same convention as Max's own
// numbox. `but` is 0 on the final call of a gesture (mouse released) -- see harmonograph_ui.js's
// ondrag() for the same pattern.
function ondrag(x, y, but) {
	if (!dragBox) return;
	var spec = DRAG_SPECS[dragBox.kind];
	var state = (dragBox.v === -1) ? globalState : vkeyInfo[dragBox.v];
	if (state && spec) {
		var delta = Math.round((dragBox.startY - y) / spec.pxPerUnit);
		var nv = dragBox.startVal + delta;
		if (nv < spec.min) nv = spec.min;
		if (nv > spec.max) nv = spec.max;
		if (state[spec.field] !== nv) {
			state[spec.field] = nv;
			spec.send(dragBox.v, nv, state);
			mgraphics.redraw();
		}
	}
	if (!but) dragBox = null;
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
	rowGeo = { headH: headH, rowH: rowH, nRows: nRows };   // read by onclick() to find the row hit

	var G_COL_W = 86, G_GAP = 4;   // width of each of the (up to) 4 fixed sidebar columns, and the gap between them
	var ornOpen = globalState.patron === READ_ORNAMENT;   // col 3 slot only exists while Patron IS Ornamento
	var filtOpen = !!globalState.filtered;                // col 4 slot only exists while Flt is on
	var extraCols = (ornOpen ? 1 : 0) + (filtOpen ? 1 : 0);   // how many of the 2 conditional slots are showing
	var GLOBAL_W = 2 + G_COL_W + G_GAP + G_COL_W + 2 + extraCols * (G_GAP + G_COL_W);
	// barra fija de globales, hasta CUATRO columnas, siempre visible, dibujada una sola vez fuera del
	// loop de filas. Las cuatro son de FILAS FIJAS (sin contador dinamico) para que nada dentro de una
	// columna se corra por lo que pase en otra: col 1 = Ind/Flt/Lck/Dir/Patron/Enlace; col 2 = Set/
	// Root/R.Arm/Orden/Rango/PresetSil/SilNorm+SilAcc; col 3 = el cluster de Ornamento (Tipo/Notas+
	// Base/BaseModo + fila de sub-modo), SOLO mientras Patron===Ornamento; col 4 = el cluster de
	// Filtro (n min/n max, Modo Mask, Mask k/Mask Fit), SOLO mientras Flt esta prendido. Los dos
	// slots condicionales se empaquetan uno tras otro sin hueco -- Ornamento siempre se queda con el
	// PRIMER slot libre si esta abierto, Filtro toma el que quede -- y GLOBAL_W crece en vez de
	// reflowear col 1/2: el unico corrimiento cuando cualquiera de los dos aparece es el grid de
	// lookahead achicandose.
	var GATE_W = 72;    // On + Ext + Trig + Patron + Set, al inicio de la fila (deciden si la voz existe)
	var DETAIL_W = 110; // Art/Lec/Ton/Fijar/Grado/Div/Ritmo/Dir/OrnTipo en cluster, en el borde etiqueta/grid -- ensanchado junto con GATE_W para que los textos mas grandes de los chips/dropdown entren comodos
	var TXT_W = 118;    // bloque de texto vkey (V<n>/forte-tonica/patron-dir/orn/vector/Z-modalidad)
	var keyW = GLOBAL_W + GATE_W + TXT_W + DETAIL_W;
	var showDetail = (W - keyW) > 260;   // bajo eso el grid quedaria inservible
	if (!showDetail) keyW = GLOBAL_W + GATE_W + TXT_W;
	var histW = Math.round(Math.min((W - keyW) * 0.28, HIST_MAX * 22));   // played notes
	var histCW = histW / HIST_MAX;
	var histX = W - histW;
	var gridX = keyW;
	var gridW = Math.max(1, histX - gridX - 4);

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
	mgraphics.move_to(histX + 4, headH - 5);
	mgraphics.show_text('tocado');

	// Set by the row loop below when that row's Patron/OrnTipo dropdown is the open one (openMenu);
	// drawn as a final pass AFTER every row so the floating list lands on top of whatever the NEXT
	// row painted, instead of getting immediately painted over by it. The fixed global sidebar
	// below can also set this (openMenu.v === -1), same floating-list mechanism.
	var pendingMenu = null;

	// --- fixed global sidebar: x=0..GLOBAL_W, drawn once (not per voice), shares no x-range with
	// any row's own content so paint order against the loop below does not matter -- only the
	// floating dropdown list (pendingMenu, set here too) needs to land on top, and that already
	// happens last, after the loop. globalState is populated by hstatus/ornbasemode/groot/
	// gornament/gflags/gharm (see those handlers above).
	globalChipGeo = {};
	var gChipH = 18, gChipGap = 2;
	var g1x = 2, g1w = G_COL_W;
	var g2x = g1x + g1w + G_GAP, g2w = G_COL_W;
	var slot3x = g2x + g2w + G_GAP;                                            // first conditional slot
	var g3x = slot3x, g3w = G_COL_W;                                           // Ornamento always claims it first
	var g4x = slot3x + (ornOpen ? (G_GAP + G_COL_W) : 0), g4w = G_COL_W;       // Filtro takes whichever is free
	var gy = headH + 2;
	function gRow(n) { return gy + n * (gChipH + gChipGap); }
	function gFits(n) { return gRow(n) + gChipH <= H; }
	mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
	mgraphics.set_font_size(8);
	mgraphics.move_to(g1x, headH - 5);
	mgraphics.show_text('Global');
	mgraphics.move_to(g2x, headH - 5);
	mgraphics.show_text('Set/Setup');
	if (ornOpen) {
		mgraphics.move_to(g3x, headH - 5);
		mgraphics.show_text('Ornamento');
	}
	if (filtOpen) {
		mgraphics.move_to(g4x, headH - 5);
		mgraphics.show_text('Filtro');
	}

	// Column 1 -- Run/Ind/Flt/Lck/Dir/Patron/Enlace, FIXED rows 0-6. Run sits first (transport,
	// decides whether anything downstream plays at all); Dir sits ABOVE Patron per request -- none
	// of these depend on each other's state so a fixed order costs nothing (unlike the old inline
	// Ornamento sub-fields, which genuinely only exist conditionally -- those moved to col 3 below
	// instead of growing this column, so col 1 never reflows regardless of what Patron is set to).
	// Enlace (linkMin, common-tone constraint on the next set) sits last, appended rather than
	// slotted between Lck and Dir -- it is independent of every other row here, so where exactly
	// costs nothing either.
	if (gFits(0)) {
		globalChipGeo.run = { x: g1x, y: gRow(0), w: g1w, h: gChipH };
		drawChip(globalChipGeo.run, 'Run', !!globalState.run);
	}
	if (gFits(1)) {
		globalChipGeo.ind = { x: g1x, y: gRow(1), w: g1w, h: gChipH };
		drawChip(globalChipGeo.ind, 'Ind', globalState.indep);
	}
	if (gFits(2)) {
		globalChipGeo.flt = { x: g1x, y: gRow(2), w: g1w, h: gChipH };
		drawChip(globalChipGeo.flt, 'Flt', globalState.filtered);
	}
	if (gFits(3)) {
		globalChipGeo.lck = { x: g1x, y: gRow(3), w: g1w, h: gChipH };
		drawChip(globalChipGeo.lck, 'Lck', !!globalState.locked);
	}
	if (gFits(4)) {
		globalChipGeo.dir = { x: g1x, y: gRow(4), w: g1w, h: gChipH };
		drawChip(globalChipGeo.dir, DIR_ABBR[Math.round(globalState.dir)] || '?', false);
	}
	if (gFits(5)) {
		globalChipGeo.patron = { x: g1x, y: gRow(5), w: g1w, h: gChipH };
		var gPatronOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gpatron';
		drawChip(globalChipGeo.patron, PATRON_ABBR[Math.round(globalState.patron)] || '?', gPatronOpen);
		if (gPatronOpen) pendingMenu = { v: -1, kind: 'gpatron', anchor: globalChipGeo.patron, items: READ_NAMES, cur: Math.round(globalState.patron) };
	}
	if (gFits(6)) {
		globalChipGeo.enlace = { x: g1x, y: gRow(6), w: g1w, h: gChipH };
		drawChip(globalChipGeo.enlace, 'Enl ' + globalState.enlace, false);
	}

	// Column 2 -- Set/Root/R.Arm/Orden/Rango/PresetSil/SilNorm+SilAcc, FIXED rows 0-6. Same
	// drag-scrub DRAG_SPECS entries as before for Set/Root/R.Arm/SilNorm/SilAcc; Orden/Rango/
	// PresetSil are dropdowns like Patron above.
	if (gFits(0)) {
		globalChipGeo.set = { x: g2x, y: gRow(0), w: g2w, h: gChipH };
		drawChip(globalChipGeo.set, 'Set ' + globalState.setIdx, false);
	}
	if (gFits(1)) {
		globalChipGeo.root = { x: g2x, y: gRow(1), w: g2w, h: gChipH };
		drawChip(globalChipGeo.root, 'R' + (globalState.root > 0 ? '+' : '') + globalState.root, false);
	}
	if (gFits(2)) {
		globalChipGeo.harm = { x: g2x, y: gRow(2), w: g2w, h: gChipH };
		drawChip(globalChipGeo.harm, 'RA' + globalState.harmRate, false);
	}
	if (gFits(3)) {
		globalChipGeo.orden = { x: g2x, y: gRow(3), w: g2w, h: gChipH };
		var gOrdenOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gorden';
		drawChip(globalChipGeo.orden, ORDER_NAMES[Math.round(globalState.orden)] || '?', gOrdenOpen);
		if (gOrdenOpen) pendingMenu = { v: -1, kind: 'gorden', anchor: globalChipGeo.orden, items: ORDER_NAMES, cur: Math.round(globalState.orden) };
	}
	if (gFits(4)) {
		globalChipGeo.rango = { x: g2x, y: gRow(4), w: g2w, h: gChipH };
		var gRangoOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'grango';
		drawChip(globalChipGeo.rango, RANGE_NAMES[Math.round(globalState.rango)] || '?', gRangoOpen);
		if (gRangoOpen) pendingMenu = { v: -1, kind: 'grango', anchor: globalChipGeo.rango, items: RANGE_NAMES, cur: Math.round(globalState.rango) };
	}
	if (gFits(5)) {
		globalChipGeo.silpre = { x: g2x, y: gRow(5), w: g2w, h: gChipH };
		var gSilpreOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gsilpre';
		drawChip(globalChipGeo.silpre, SILPRE_NAMES[Math.round(globalState.silpre)] || '?', gSilpreOpen);
		if (gSilpreOpen) pendingMenu = { v: -1, kind: 'gsilpre', anchor: globalChipGeo.silpre, items: SILPRE_NAMES, cur: Math.round(globalState.silpre) };
	}
	// Row 6 -- Silencio Normal/Acento (groupSilence), side by side like Notas/Base in col 3 -- a
	// Preset Silencio pick (row 5) only OVERWRITES these two, so seeing/nudging them directly here
	// is worth a row of its own rather than only being reachable through a preset.
	if (gFits(6)) {
		var g2dcw = (g2w - 2) / 2;
		globalChipGeo.silnorm = { x: g2x, y: gRow(6), w: g2dcw, h: gChipH };
		globalChipGeo.silacc = { x: g2x + g2dcw + 2, y: gRow(6), w: g2dcw, h: gChipH };
		drawChip(globalChipGeo.silnorm, 'N' + globalState.silNorm, false);
		drawChip(globalChipGeo.silacc, 'A' + globalState.silAcc, false);
	}

	// Column 3 -- the WHOLE Ornamento cluster (Tipo/Notas+Base/BaseModo), only drawn while Patron
	// IS Ornamento (ornOpen, computed above alongside GLOBAL_W). Not gated further by voice or
	// panel state -- if col 3 is drawn at all it always has all three rows (FIXED 0-2), since
	// GLOBAL_W already accounted for its width whenever ornOpen is true.
	if (ornOpen) {
		if (gFits(0)) {
			globalChipGeo.ornt = { x: g3x, y: gRow(0), w: g3w, h: gChipH };
			var gOrntOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gornt';
			drawChip(globalChipGeo.ornt, ORN_TYPE_NAMES[Math.round(globalState.ornType)] || '?', gOrntOpen);
			if (gOrntOpen) pendingMenu = { v: -1, kind: 'gornt', anchor: globalChipGeo.ornt, items: ORN_TYPE_NAMES, cur: Math.round(globalState.ornType) };
		}
		if (gFits(1)) {
			var gdcw = (g3w - 2) / 2;
			globalChipGeo.ornnotas = { x: g3x, y: gRow(1), w: gdcw, h: gChipH };
			globalChipGeo.ornbase = { x: g3x + gdcw + 2, y: gRow(1), w: gdcw, h: gChipH };
			drawChip(globalChipGeo.ornnotas, '×' + globalState.ornCount, false);
			drawChip(globalChipGeo.ornbase, 'I' + globalState.ornBase, false);
		}
		if (gFits(2)) {
			globalChipGeo.ornbasemode = { x: g3x, y: gRow(2), w: g3w, h: gChipH };
			var gObmOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gornbasemode';
			drawChip(globalChipGeo.ornbasemode, ORN_BASE_MODE_NAMES[Math.round(globalState.ornBaseMode)] || '?', gObmOpen);
			if (gObmOpen) pendingMenu = { v: -1, kind: 'gornbasemode', anchor: globalChipGeo.ornbasemode, items: ORN_BASE_MODE_NAMES, cur: Math.round(globalState.ornBaseMode) };
		}
		// Row 3 -- Orn Base Cuarteto's own scheme, ONLY while ornBaseMode IS Cuarteto (its real panel
		// widget, fs2_obj_775, sits on the same page regardless but has no effect otherwise -- same
		// rule the popup already applies elsewhere, e.g. setMoot). A conditional row at the BOTTOM of
		// an already-conditional column costs nothing extra: nothing below it to push down, and col 3's
		// width (part of GLOBAL_W) was already fixed by ornOpen alone, so this never resizes anything.
		if (Math.round(globalState.ornBaseMode) === ORN_BASE_QUADRITONE && gFits(3)) {
			globalChipGeo.ornquad = { x: g3x, y: gRow(3), w: g3w, h: gChipH };
			var gOrnQuadOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gornquad';
			drawChip(globalChipGeo.ornquad, QUAD_SCHEME_NAMES[Math.round(globalState.ornQuad)] || '?', gOrnQuadOpen);
			if (gOrnQuadOpen) pendingMenu = { v: -1, kind: 'gornquad', anchor: globalChipGeo.ornquad, items: QUAD_SCHEME_NAMES, cur: Math.round(globalState.ornQuad) };
		}
		// Row 3 -- Orn Base Paso, ONLY while ornBaseMode IS Grados (ORN_BASE_DEGREES). Same rule and
		// same "costs nothing extra" reasoning as the Cuarteto row just above -- mutually exclusive
		// with it (ornBaseMode can only be one value), so never both drawn at once.
		if (Math.round(globalState.ornBaseMode) === ORN_BASE_DEGREES && gFits(3)) {
			globalChipGeo.ornstep = { x: g3x, y: gRow(3), w: g3w, h: gChipH };
			drawChip(globalChipGeo.ornstep, 'Paso ' + globalState.ornStep, false);
		}
		// Rows 3-4 -- the three Orn Serie fields, ONLY while ornBaseMode IS Serie (ORN_BASE_SERIES).
		// Inicio/Paso share row 3 (same side-by-side layout as Notas/Base above); Pico gets its own
		// row 4 since three fields across one 86px column is too tight to click reliably. Also
		// mutually exclusive with the Cuarteto/Grados rows above -- ornBaseMode is a single value.
		if (Math.round(globalState.ornBaseMode) === ORN_BASE_SERIES) {
			if (gFits(3)) {
				var sdcw = (g3w - 2) / 2;
				globalChipGeo.serstart = { x: g3x, y: gRow(3), w: sdcw, h: gChipH };
				globalChipGeo.serstep = { x: g3x + sdcw + 2, y: gRow(3), w: sdcw, h: gChipH };
				drawChip(globalChipGeo.serstart, 'I' + globalState.ornSeriesStart, false);
				drawChip(globalChipGeo.serstep, 'P' + globalState.ornSeriesStep, false);
			}
			if (gFits(4)) {
				globalChipGeo.serpeak = { x: g3x, y: gRow(4), w: g3w, h: gChipH };
				drawChip(globalChipGeo.serpeak, 'Pico ' + globalState.ornSeriesPeak, false);
			}
		}
	}   // else: globalChipGeo.ornt/ornnotas/ornbase/ornbasemode/ornquad/ornstep/serstart/serstep/
		// serpeak simply stay unset (fresh {} above), same as any other not-currently-applicable chip

	// Column 4 -- the Filtro cluster (n min/n max, Modo Mask, Mask k/Mask Fit), only drawn while Flt
	// is on (filtOpen, computed above alongside GLOBAL_W). The raw 12-bit pitch-class mask stays
	// fs2setpick.js's piano-UI territory (a click-grid, not a knob); Vector IC (6 interval-class
	// min/max pairs) stays out too -- composition-time fine-tuning, not a live-performance knob,
	// same call as Tension/Curva/Modelo/Prog Favoritos next to Enlace. This is the shallow half:
	// single numbers and one 3-way mode, each with a real panel widget already.
	if (filtOpen) {
		if (gFits(0)) {
			var ndcw = (g4w - 2) / 2;
			globalChipGeo.nmin = { x: g4x, y: gRow(0), w: ndcw, h: gChipH };
			globalChipGeo.nmax = { x: g4x + ndcw + 2, y: gRow(0), w: ndcw, h: gChipH };
			drawChip(globalChipGeo.nmin, 'n' + globalState.cardMin, false);
			drawChip(globalChipGeo.nmax, 'n' + globalState.cardMax, false);
		}
		if (gFits(1)) {
			globalChipGeo.maskmode = { x: g4x, y: gRow(1), w: g4w, h: gChipH };
			var gMaskModeOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gmaskmode';
			drawChip(globalChipGeo.maskmode, MASK_MODE_NAMES[Math.round(globalState.maskMode)] || '?', gMaskModeOpen);
			if (gMaskModeOpen) pendingMenu = { v: -1, kind: 'gmaskmode', anchor: globalChipGeo.maskmode, items: MASK_MODE_NAMES, cur: Math.round(globalState.maskMode) };
		}
		// Row 2 -- Mask Fit always (the "let a set transpose to satisfy the mask" adjustment applies
		// in every Modo Mask); Mask k joins it ONLY in Int mode -- every other mode ignores it, same
		// as maskOk()'s own branches. Mutually exclusive with itself, so no extra cost either way.
		if (gFits(2)) {
			if (Math.round(globalState.maskMode) === MASK_MODE_INT) {
				var mdcw = (g4w - 2) / 2;
				globalChipGeo.maskk = { x: g4x, y: gRow(2), w: mdcw, h: gChipH };
				globalChipGeo.maskfit = { x: g4x + mdcw + 2, y: gRow(2), w: mdcw, h: gChipH };
				drawChip(globalChipGeo.maskk, 'k' + globalState.maskK, false);
			} else {
				globalChipGeo.maskfit = { x: g4x, y: gRow(2), w: g4w, h: gChipH };
			}
			drawChip(globalChipGeo.maskfit, 'Fit', !!globalState.maskFit);
		}
	}   // else: globalChipGeo.nmin/nmax/maskmode/maskk/maskfit simply stay unset (fresh {} above)

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
		// This voice's set plays no part in what it actually sounds: Patron is Ornamento and the
		// global base mode does not read the set at all (see ornbasemode() above). The forte name/
		// vector/Z-modality lines and the Set scrub box are real but moot in that state, so they
		// dim instead of disappearing outright -- still there to glance at (e.g. before switching
		// Patron back), just visibly not the thing driving the sound right now.
		var setMoot = vk && vk.patron === READ_ORNAMENT && ornBaseMode !== ORN_BASE_DEGREES;
		var setDim = setMoot ? 0.4 : 1.0;

		// TonProp (Ton) and Lectura Propia (Lec) only take effect while this voice has its OWN
		// cursor -- Ext on, or the global Ind on while in Arpegio -- same voiceSelfCursored() the
		// engine itself gates on (see forteseq2.js: emitVoices(), the shared-clock path every other
		// voice's row falls back to, never reads voiceKeyOwn/voiceReadMode/voiceReadDir at all).
		// Off that, a voice's own key/reading-order sits there correctly configured but inert --
		// same "real but not what's sounding" situation as setMoot above, same treatment: dim the
		// readouts, hide the controls that would otherwise look like they do something right now.
		var selfCursored = vk && (vk.ext || (globalState.mode === 1 && globalState.indep));
		var keyMoot = vk && vk.keyOwn && !selfCursored;
		var readMoot = vk && vk.readOwn && !selfCursored;
		var keyDim = keyMoot ? 0.4 : 1.0;
		var readDim = readMoot ? 0.4 : 1.0;

		// Font sizes scale with the room this row actually has (a tall window like this one should
		// use it) instead of staying pinned at the smallest legible size regardless of space.
		var fsV = Math.max(11, Math.min(18, rowH * 0.11));
		var fsInfo = Math.max(10, Math.min(14, rowH * 0.085));
		var lh = fsInfo + 6;

		var chipH = 18, chipGap = 2;   // bumped from 15 so the bigger chip font (drawChip, now 11) has room
		var cg = { on: { x: GLOBAL_W + 2, y: y + 2, w: GATE_W - 6, h: chipH },
			ext: { x: GLOBAL_W + 2, y: y + 2 + chipH + chipGap, w: GATE_W - 6, h: chipH } };
		drawChip(cg.on, (vk && vk.muted) ? 'Off' : 'On', !(vk && vk.muted));
		drawChip(cg.ext, 'Ext', !!(vk && vk.ext));

		// Trig -- unconditional (fires this voice by hand regardless of Propia/Ext state, same as
		// the panel's own always-visible Trig button). Momentary: no drag, no echo, just a click.
		var trigY = y + 2 + 2 * (chipH + chipGap);
		if (rowH >= (trigY - y) + chipH + 4) {
			cg.trig = { x: GLOBAL_W + 2, y: trigY, w: GATE_W - 6, h: chipH };
			drawChip(cg.trig, 'Trig', false);
		}

		// Gate column keeps growing downward with Patron (readOwn) / Set (keyOwn) -- a dynamic row
		// counter instead of fixed slots, since the two conditions are independent and either can be
		// on without the other. Each only draws once its own condition holds AND there is room for
		// one more row without bleeding into the next voice's row.
		var gateRow = 3;
		if (vk && vk.readOwn && !readMoot) {
			var patronY = y + 2 + gateRow * (chipH + chipGap);
			if (rowH >= (patronY - y) + chipH + 4) {
				cg.patron = { x: GLOBAL_W + 2, y: patronY, w: GATE_W - 6, h: chipH };
				var patronOpen = openMenu && openMenu.v === v && openMenu.kind === 'patron';
				drawChip(cg.patron, PATRON_ABBR[Math.round(vk.patron)] || '?', patronOpen);
				if (patronOpen) pendingMenu = { v: v, kind: 'patron', anchor: cg.patron, items: READ_NAMES, cur: Math.round(vk.patron) };
				gateRow++;
			}
		}
		if (vk && vk.keyOwn && !setMoot && !keyMoot) {
			var setY = y + 2 + gateRow * (chipH + chipGap);
			if (rowH >= (setY - y) + chipH + 4) {
				cg.setbox = { x: GLOBAL_W + 2, y: setY, w: GATE_W - 6, h: chipH };
				drawChip(cg.setbox, 'Set ' + vk.setIdx, false);
				gateRow++;
			}
		}

		if (showDetail) {
			var dx0 = GLOBAL_W + GATE_W + TXT_W + 2;
			var dcw = (DETAIL_W - 6) / 2;
			cg.art = { x: dx0, y: y + 2, w: dcw, h: chipH };
			cg.lec = { x: dx0 + dcw + 2, y: y + 2, w: dcw, h: chipH };
			cg.ton = { x: dx0, y: y + 2 + chipH + chipGap, w: dcw, h: chipH };
			cg.fijar = { x: dx0 + dcw + 2, y: y + 2 + chipH + chipGap, w: dcw, h: chipH };
			drawChip(cg.art, 'Art', !!(vk && vk.artOwn));
			drawChip(cg.lec, 'Lec', !!(vk && vk.readOwn), false, readDim);
			drawChip(cg.ton, 'Ton', !!(vk && vk.keyOwn), false, keyDim);
			drawChip(cg.fijar, 'Fij', !!(vk && vk.keyOwn && vk.keyLock === 1), !(vk && vk.keyOwn), keyDim);

			// Grado/Div/Ritmo euclidiano -- unconditional, rows 2-4, same as the panel (no "Propia"
			// chip gates any of these there either -- Grado/Div live in the always-visible essential
			// strip, the per-voice Euclid grid has no gate at all).
			if (vk) {
				var gradoY = y + 2 + 2 * (chipH + chipGap);
				if (rowH >= (gradoY - y) + chipH + 4) {
					cg.grado = { x: dx0, y: gradoY, w: dcw, h: chipH };
					cg.div = { x: dx0 + dcw + 2, y: gradoY, w: dcw, h: chipH };
					drawChip(cg.grado, 'G' + (vk.grado > 0 ? '+' : '') + vk.grado, false);
					drawChip(cg.div, 'Dv' + vk.div, false);
				}
				var euY = y + 2 + 3 * (chipH + chipGap);
				if (rowH >= (euY - y) + chipH + 4) {
					cg.euclen = { x: dx0, y: euY, w: dcw, h: chipH };
					cg.euck = { x: dx0 + dcw + 2, y: euY, w: dcw, h: chipH };
					drawChip(cg.euclen, 'L' + vk.euLarg, false);
					drawChip(cg.euck, 'P' + vk.euPuls, false);
				}
				var eurY = y + 2 + 4 * (chipH + chipGap);
				if (rowH >= (eurY - y) + chipH + 4) {
					cg.eucrot = { x: dx0, y: eurY, w: DETAIL_W - 6, h: chipH };
					drawChip(cg.eucrot, 'Giro ' + vk.euGir, false);
				}
			}

			// Same dynamic-row-counter idea as the gate column above, continuing from row 5 (after
			// the unconditional rows 2-4): Articulacion values (if artOwn), then Dir, then (only if
			// Patron is actually Ornamento) OrnTipo, then OrnNotas/OrnBase side by side -- each
			// conditioned on the previous one actually having drawn, so nothing leaves a gap.
			var detailRow = 5;
			if (vk && vk.artOwn) {
				var avY = y + 2 + detailRow * (chipH + chipGap);
				if (rowH >= (avY - y) + chipH + 4) {
					cg.artvmin = { x: dx0, y: avY, w: dcw, h: chipH };
					cg.artvmax = { x: dx0 + dcw + 2, y: avY, w: dcw, h: chipH };
					drawChip(cg.artvmin, 'Vm' + vk.velMin, false);
					drawChip(cg.artvmax, 'VM' + vk.velMax, false);
					detailRow++;

					var afY = y + 2 + detailRow * (chipH + chipGap);
					if (rowH >= (afY - y) + chipH + 4) {
						cg.artdur = { x: dx0, y: afY, w: dcw, h: chipH };
						cg.artsil = { x: dx0 + dcw + 2, y: afY, w: dcw, h: chipH };
						drawChip(cg.artdur, 'Fig' + vk.durDiv, false);
						drawChip(cg.artsil, 'Sil' + vk.silence, false);
						detailRow++;
					}
				}
			}
			if (vk && vk.readOwn && !readMoot) {
				var dirY = y + 2 + detailRow * (chipH + chipGap);
				if (rowH >= (dirY - y) + chipH + 4) {
					cg.dir = { x: dx0, y: dirY, w: DETAIL_W - 6, h: chipH };
					drawChip(cg.dir, DIR_ABBR[Math.round(vk.dir)] || '?', false);
					detailRow++;

					if (vk.patron === READ_ORNAMENT) {
						var otY = y + 2 + detailRow * (chipH + chipGap);
						if (rowH >= (otY - y) + chipH + 4) {
							cg.ornt = { x: dx0, y: otY, w: DETAIL_W - 6, h: chipH };
							var orntOpen = openMenu && openMenu.v === v && openMenu.kind === 'ornt';
							drawChip(cg.ornt, ORN_TYPE_NAMES[Math.round(vk.ornT)] || '?', orntOpen);
							if (orntOpen) pendingMenu = { v: v, kind: 'ornt', anchor: cg.ornt, items: ORN_TYPE_NAMES, cur: Math.round(vk.ornT) };
							detailRow++;

							// OrnNotas (count) / OrnBase (interval) -- same click-drag scrub as Set.
							var onY = y + 2 + detailRow * (chipH + chipGap);
							if (rowH >= (onY - y) + chipH + 4) {
								cg.ornnotas = { x: dx0, y: onY, w: dcw, h: chipH };
								cg.ornbase = { x: dx0 + dcw + 2, y: onY, w: dcw, h: chipH };
								drawChip(cg.ornnotas, '×' + vk.ornN, false);
								drawChip(cg.ornbase, 'I' + vk.ornB, false);
								detailRow++;
							}
						}
					}
				}
			}
		}
		chipGeo[v] = cg;

		mgraphics.set_source_rgba(anyOwn ? [1 * rowDim, 0.75 * rowDim, 0.3 * rowDim, 1] : [0.6 * rowDim, 0.6 * rowDim, 0.66 * rowDim, 1]);
		mgraphics.set_font_size(fsV);
		mgraphics.move_to(GLOBAL_W + GATE_W + 4, y + fsV + 2);
		mgraphics.show_text('V' + (v + 1) + (vk && vk.muted ? ' ·mute' : ''));
		if (vk && rowH >= 24) {
			mgraphics.set_font_size(fsInfo);
			mgraphics.set_source_rgba([0.68 * rowDim * setDim * keyDim, 0.68 * rowDim * setDim * keyDim, 0.74 * rowDim * setDim * keyDim, 1]);
			var ky = y + fsV + lh;
			mgraphics.move_to(GLOBAL_W + GATE_W + 4, ky);
			// "*" ya marca TonProp (clave propia); "Fij" es la excepcion dentro de eso -- progresar
			// (avanzar con cada cambio de armonia) es el estado por defecto y no necesita marca,
			// solo la voz fijada (voiceKeyLock) la necesita. Dimmed (setDim) when Patron is Ornamento
			// under a set-blind base mode, or (keyDim) when TonProp is on but this voice isn't
			// self-cursored -- either way real but not what is actually sounding.
			mgraphics.show_text(vk.forte + ' ' + vk.tonic + (vk.keyOwn ? ' *' : '') + (vk.keyLock === 1 ? ' ·Fij' : ''));
			mgraphics.set_source_rgba([0.68 * rowDim * readDim, 0.68 * rowDim * readDim, 0.74 * rowDim * readDim, 1]);   // Patron/Dir/Orn below -- dimmed (readDim) when Lectura Propia is on but moot, same reasoning
			if (rowH >= fsV + 2 * lh + 6) {
				ky += lh;
				var pname = READ_NAMES[vk.patron] || ('modo ' + vk.patron);
				var dsuf = vk.dir ? (' ' + (DIR_NAMES[vk.dir] || vk.dir)) : '';
				mgraphics.move_to(GLOBAL_W + GATE_W + 4, ky);
				mgraphics.show_text(pname + dsuf + (vk.readOwn ? ' *' : ''));
			}
			if (rowH >= fsV + 3 * lh + 6 && vk.ornT >= 0) {
				ky += lh;
				mgraphics.move_to(GLOBAL_W + GATE_W + 4, ky);
				mgraphics.show_text((ORN_TYPE_NAMES[vk.ornT] || ('orn ' + vk.ornT)) + ' ×' + vk.ornN + ' I' + vk.ornB + (vk.readOwn ? ' *' : ''));
			}
			if (rowH >= fsV + 4 * lh + 6) {
				ky += lh;
				mgraphics.move_to(GLOBAL_W + GATE_W + 4, ky);
				mgraphics.set_source_rgba([0.68 * rowDim * setDim * keyDim, 0.68 * rowDim * setDim * keyDim, 0.74 * rowDim * setDim * keyDim, 1]);
				mgraphics.show_text('<' + vk.vec + '> ' + vk.diss + '%');
			}
			if (rowH >= fsV + 5 * lh + 6) {
				ky += lh;
				mgraphics.move_to(GLOBAL_W + GATE_W + 4, ky);
				mgraphics.set_source_rgba([0.68 * rowDim * setDim * keyDim, 0.68 * rowDim * setDim * keyDim, 0.74 * rowDim * setDim * keyDim, 1]);
				var extras = [];
				if (vk.zRel !== '-') extras.push(vk.zRel);
				extras.push(vk.modality);
				if (vk.mirror !== '-') extras.push(vk.mirror);
				mgraphics.show_text(extras.join(' · '));
			}
		}

		// history: newest is hv[0], drawn at the block's LEFT edge (against the grid); ages rightward
		for (var hslot = 0; hslot < HIST_MAX; hslot++) {
			var hidx = hslot;                       // 0..HIST_MAX-1, 0 = left edge of block (vs. grid)
			var age = hslot;                        // hslot 0 = age 0 = newest, pinned next to the grid
			var note = (age < hv.length) ? hv[age] : -1;
			var dim = (0.55 - 0.15 * (hslot / (HIST_MAX - 1))) * rowDim;   // newest bright, oldest dim
			drawCell(histX + hidx * histCW, y, histCW, rowH, note, dim, histCW >= 20);
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
			mgraphics.move_to(gridX + gridW - 12, y + rowH / 2 + 4);
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

	// The open Patron/OrnTipo dropdown, if any -- drawn last so it floats on top of every row,
	// including whichever one comes after its own (see pendingMenu's own comment above).
	menuItemGeo = [];
	if (pendingMenu) {
		var miH = 18;   // matches the bumped chipH so the open list reads at the same size as the chips
		var mx = pendingMenu.anchor.x;
		var mw = Math.max(pendingMenu.anchor.w, 110);
		var totalH = miH * pendingMenu.items.length + 2;
		var my = pendingMenu.anchor.y + pendingMenu.anchor.h + 1;
		if (my + totalH > H) my = pendingMenu.anchor.y - totalH - 1;   // flip upward if it would run off the bottom
		if (my < 0) my = 0;
		mgraphics.set_source_rgba([0.08, 0.08, 0.09, 0.98]);
		mgraphics.rectangle(mx, my, mw, totalH);
		mgraphics.fill();
		mgraphics.set_source_rgba([0, 0, 0, 0.8]);
		mgraphics.set_line_width(1);
		mgraphics.rectangle(mx, my, mw, totalH);
		mgraphics.stroke();
		for (var mi = 0; mi < pendingMenu.items.length; mi++) {
			var ir = { x: mx, y: my + 1 + mi * miH, w: mw, h: miH };
			menuItemGeo.push(ir);
			var selected = (mi === pendingMenu.cur);
			mgraphics.set_source_rgba(selected ? [0.35, 0.28, 0.12, 1] : [0.08, 0.08, 0.09, 1]);
			mgraphics.rectangle(ir.x, ir.y, ir.w, ir.h);
			mgraphics.fill();
			mgraphics.set_source_rgba(selected ? [1, 0.85, 0.55, 1] : [0.75, 0.75, 0.8, 1]);
			mgraphics.set_font_size(11);
			mgraphics.move_to(ir.x + 3, ir.y + ir.h - 4);
			mgraphics.show_text(pendingMenu.items[mi]);
		}
	}

	// separator between grid and history zone
	mgraphics.set_source_rgba([0, 0, 0, 0.6]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(histX - 2, headH);
	mgraphics.line_to(histX - 2, headH + gridH);
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
