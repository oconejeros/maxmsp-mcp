// fs2horizon.js -- jsui: the "próximos pasos" panel for FORTESEQ2's floating window.
//
// A fixed GLOBAL sidebar (x=0..GLOBAL_W, drawn once, see paint()'s "fixed global sidebar" block)
// sits to the left of everything, always visible, in up to SEVEN columns, each with FIXED row
// indices (no dynamic per-column counter) so nothing in one column ever shifts because of what's
// happening in another:
//   col 1 -- Run/Ind/Flt/Lck/Dir/Patron/Enlace/Modo Toque/Sub/Sec Raiz/Oct Maestra+Drum/Pad/
//     Rotacion/Rotar x Cambio/Salto Coprimo (Run first -- the transport; Dir above Patron on
//     request; Enlace/linkMin -- the common-tone constraint on the next set -- appended after
//     those; Modo Toque and Sub next because they are the two GATES of col 5, and a conditional
//     column cannot hold the control that decides whether it exists). Rows 9-13 (Ola 4, Registro y
//     recorrido) went here rather than their own column -- they are single values, not a family
//     with its own on/off state. Oct Maestra+Drum share a row (Drum is the most aggressive gate in
//     the device: on, it kills Oct Maestra, the per-voice octave AND Rango in col 2 -- dimmed both
//     places); Pad is HIDDEN (not dimmed) unless Drum is on; Rotacion has no per-voice gate --
//     chordFor() reads it too, not just the arpeggio walk; Rotar x Cambio dims in Acordes
//     (rotShape only gates the auto-advance of `rotation`, which the chord branch never touches);
//     Salto Coprimo is HIDDEN unless Patron===Coprimo, last row, nothing below it to push.
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
//   col 4 -- the Filtro cluster (n min/n max, Modo Mask, Mask k + Mask Fit, IC1-6 Min/Max, Azar %
//     Mask + Azar Mask button), drawn ONLY while Flt is on (`filtOpen`) -- same
//     GLOBAL_W-grows-not-reflows deal as col 3. Mask k only joins Mask Fit on its row while Modo
//     Mask is Int (MASK_MODE_INT); every other mode ignores Mask k entirely, same as the engine's
//     own maskOk() branches. The raw 12-bit chromatic mask stays out (that's fs2setpick.js's
//     piano-UI territory, a click-grid rather than a knob). Vector IC (Ola 5) is the six IC1-6
//     Min|Max rows at the bottom -- an earlier round called it "composition-time" and left it out,
//     but the plan's audit overturned that: Mask Fit can transpose a set past every other filter
//     condition, but never past the interval-class vector (it's transposition-invariant), so it is
//     the one condition worth seeing live. A Min above its own Max is flagged `alarm` (red), not
//     dimmed -- it silently blocks everything rather than merely doing nothing. Azar % Mask is the
//     drag value randomizemask() reads; the button next to it is a pure action (needs the Live API,
//     posts to the console outside Live) with no echo of its own.
//   col 5 -- the Groove cluster (Swing/Human, Rasg+Dir Rasg, Rat N+Rat A, Prob Rat+Caida), drawn
//     while Sub >= 2. Swing/Human/Rat* all die with subDiv < 2 (swingOffset/humanizeOffset/
//     scheduleBurst each bail on it -- no sub-ticks, nowhere to push the note), so that one gate
//     covers six of the eight. Rasg/Dir Rasg are the exception: strumOffset bails on `n < 2`, not
//     on subDiv, so they technically fire at Sub 1 -- but the offset is measured in SUB-TICKS, and
//     at Sub 1 one sub-tick is a whole STEP, so a 4-note chord ends up spread over 4 steps on top
//     of whatever comes next. That is not a strum, and it is not worth coupling a RHYTHM column to
//     a HARMONIC-TEXTURE control (Modo Toque) that nobody would predict gates it. They dim inside
//     the column in Arpegio instead. Nothing here is ever hidden row-by-row -- every one of these
//     is a candidate for "I moved it and nothing happened", so the value stays visible.
//   col 6 -- Acentos (Ciclo+Tie, Euclid+Pulsos+Giro, VelMin/VelMax/Figura Normal+Acento), drawn
//     always (`accOpen` is a constant true) -- unlike col 3-5 there is no "off" state for
//     articulation, so it just always takes the next packed slot. Ciclo dims while Tie is on
//     (articulationFor() ignores it then); Pulsos/Giro are HIDDEN, not dimmed, while Euclid is off.
//   col 7 -- Camino armonico (Tension+Curva+Modelo, Prog Favoritos+Solo Fav+Fav+Limpiar favs),
//     also always drawn (`caminoOpen` constant true, same reasoning as Acentos). This is
//     advanceSet()'s own precedence chain made visible, and dimming here is the point: Prog
//     Favoritos with a full list dims Tension/Curva/Modelo AND col 1's Enlace (advanceFavSeq()
//     never reads any of them); with an EMPTY list it is a silent trap -- advanceFavSeq() falls
//     through to advanceInOrder() so Enlace revives but Tension stays dead -- flagged with the
//     `alarm` drawChip() color instead of a dim, on both the Prog Favoritos chip and Tension itself.
//     Curva additionally dims whenever Tension is 0 regardless of Prog Favoritos (tensionAt() is
//     its only reader); Modelo never dims (settensmodel() always touches the filter/Orden).
//   col 8 -- Modulacion (Ola 6), also always drawn (`modOpen` constant true, same reasoning as
//     Acentos/Camino -- four modulators always exist, there is no "off" state for the family as a
//     whole). Breaks the chip-per-row idiom on purpose (the plan calls for a matrix, not 20 loose
//     chips): a 4-row x 5-field grid, one row per modulator (M1-M4), fields left to right Forma
//     (dropdown)/Ciclo/Prof/Fase (drag-scrub)/Dest (dropdown) -- same order setmodshape/setmodcycle/
//     setmoddepth/setmodphase/setmoddest take their arguments in. Needs roughly DOUBLE a normal
//     column's width (`MOD_COL_W`, see `condColW()`) -- condSlotX()/GLOBAL_W generalized to a
//     per-column width instead of the uniform G_COL_W every other conditional column uses. A whole
//     row dims when it plainly does nothing (`Dest === "-"` or `Prof === 0`, modStep()'s own early
//     continue); two narrower traps dim on top of that: Dest=Grado only reaches degreeAt() in
//     Arpegio (Acordes never calls it), and Dest=Swing/Rasgueo/Ratchet need Sub >= 2 for the same
//     reason col 5 (Groove) does. Modulators never WRITE their destination parameter -- they sum on
//     top of it at read time (modStep()/modSum) -- so this column mirrors the five knobs only, never
//     the live modulated value; the panel's own dial keeps showing exactly what the user set.
//   Ornamento, Filtro, Groove, Acentos, Camino and Modulacion pack into the sidebar's conditional
//     slots left to right with no gap between them, in that FIXED priority order (condCols/
//     condSlotX in paint()) -- each open family claims the first free slot -- so any combination can
//     be showing at once.
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
// (Acordes/Arpegio) was read-only here for a while -- setmode() looked like it had no panel-side
// control to cross-check against -- but it does: `fs2_mode` obj-19 in fs2pages.maxpat, a live.tab
// wired straight into `prepend setmode`, so it is now a writable chip like the rest.
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
//   gvec1..gvec6 <min> <max>  (Ola 5, one token per interval class, col 4 rows 3-8)
//   grandmask <maskRandomPct>  (Ola 5, col 4 row 9; the "Azar Mask" button next to it needs no sync)
//   gregistro <rootSeqIdx> <masterOctave> <drumOn> <drumBase>  (Ola 4, col 1 rows 9-11)
//   grecorrido <manualRot> <rotShape> <coprimeSkip>  (Ola 4, col 1 rows 12-14)
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
var READ_COPRIMO = 4;    // same value as forteseq2.js's READ_COPRIMO -- gates the Salto row (col 1)
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
// Seventh sidebar column (Camino armonico). Both enums copied straight from the real panel widgets
// (fs2p_curva/fs2p_tensmodel's own parameter_enum) -- index IS value on both, no gsub-style trick.
var CURVA_NAMES = ['Sube', 'Baja', 'Arco'];
var TENSMODEL_NAMES = ['Huron', 'McKay'];
// Modo Toque (fs2_mode, live.tab "Modo"): 0 = Acordes, 1 = Arpegio, same as forteseq2.js's
// `mode = m ? 1 : 0`. Named because Acordes is the gate for Rasg/Dir Rasg (strumOffset() returns 0
// for n < 2, i.e. anything that is not a chord) and for a couple of per-voice moots already here.
var MODE_NAMES = ['Acordes', 'Arpegio'];
var MODE_CHORDS = 0;
// Fifth sidebar column (Groove). `Sub`'s real widget (fs2_sub_g) is a live.menu whose INDEX is not
// its value; the popup deals in the DIVISOR throughout (that is what setsub() takes and what
// querynext's `gsub` carries) and the engine's own gecho converts back to the index for the panel.
// So this list is only used to cycle the chip, never to talk to Max.
var SUB_VALUES = [1, 2, 3, 4, 6, 8];
var SUB_LABELS = ['1', '2', '3', '4', '6', '8'];   // los mismos, como items del dropdown
function subIndexOf(n) {
	for (var k = 0; k < SUB_VALUES.length; k++) if (SUB_VALUES[k] === Math.round(n)) return k;
	return 0;
}
var DIR_RASG_ABBR = ['Arr', 'Aba', 'Azar', 'Alt'];   // fs2_dirrasg's enum, abbreviated for a ~41px chip
// Ola 4 additions to col 1 (Registro/Recorrido, rows 9-13). ROOTSEQ_NAMES copied straight from the
// real widget's own parameter_enum (fs2_rseq2) so the popup never disagrees with the panel.
var ROOTSEQ_NAMES = ['Raiz fija', 'Cuartas', 'Quintas', '3as m', '3as M', 'Tonos', 'Cromatica',
	'Tritono', 'I IV V', 'Azar'];
// Eighth sidebar column (Modulacion, Ola 6). Both enums copied straight from the real panel widgets
// (fs2pages.maxpat's md_m<k>_forma/md_m<k>_dest, same parameter_enum on all four modulators) -- same
// "index IS value" idiom as CURVA_NAMES/TENSMODEL_NAMES. ABBR versions are for the matrix's ~30px
// cells (MOD_COL_W split 5 ways); the dropdown list itself uses the full names, same split as
// PATRON_ABBR/READ_NAMES above.
var MOD_SHAPE_NAMES = ['Seno', 'Triang', 'Diente', 'Cuadr', 'Azar', 'Paseo'];
var MOD_SHAPE_ABBR = ['Sen', 'Tri', 'Die', 'Cua', 'Aza', 'Pas'];
var MOD_DEST_NAMES = ['-', 'Raiz', 'Octava', 'Vel', 'Largo', 'Silencio', 'Swing', 'Rasgueo',
	'Ratchet', 'Grado', 'Human', 'Caida'];
var MOD_DEST_ABBR = ['-', 'Raz', '8va', 'Vel', 'Lrg', 'Sil', 'Swg', 'Rsg', 'Rat', 'Grd', 'Hum', 'Cai'];
// Same indices as forteseq2.js's D_SWING/D_STRUM/D_RATCHET/D_DEG -- for the two narrower show/hide
// traps on top of the "Dest=- or Prof=0" whole-row dim (see the col 8 header comment above).
var MOD_DEST_SWING = 6, MOD_DEST_STRUM = 7, MOD_DEST_RATCHET = 8, MOD_DEST_GRADO = 9;

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
	cardMin: 1, cardMax: 12, maskMode: 0, maskK: 1, maskFit: 1,
	sub: 1, swing: 50, human: 0, rasg: 0, dirRasg: 0,
	ratN: 1, ratA: 1, ratProb: 100, ratCaida: 0,
	accCiclo: 4, accTie: 0, euclidOn: 0, euclidK: 4, euclidRot: 0,
	velMinN: 55, velMinA: 95, velMaxN: 80, velMaxA: 115, figN: 16, figA: 4,
	tension: 0, curva: 0, tensmodel: 0, progfav: 0, favonly: 0, favSeqLen: 0, fav: 0,
	rootSeq: 0, octMaestra: 0, drum: 0, pad: 36, rotacion: 0, rotarx: 0, salto: 2,
	vecMin1: 0, vecMax1: 12, vecMin2: 0, vecMax2: 12, vecMin3: 0, vecMax3: 12,
	vecMin4: 0, vecMax4: 12, vecMin5: 0, vecMax5: 12, vecMin6: 0, vecMax6: 12,
	randMaskPct: 50,
	mod1shape: 0, mod1cycle: 8, mod1depth: 0, mod1phase: 0, mod1dest: 0,
	mod2shape: 0, mod2cycle: 8, mod2depth: 0, mod2phase: 0, mod2dest: 0,
	mod3shape: 0, mod3cycle: 8, mod3depth: 0, mod3phase: 0, mod3dest: 0,
	mod4shape: 0, mod4cycle: 8, mod4depth: 0, mod4phase: 0, mod4dest: 0 };

// La tira de 16 acentos (col 6), read-only en esta ola -- ver ola-2 del plan. Separada de
// globalState porque es un array de tamano fijo, no un escalar por campo.
var ACCENT_MAX_UI = 16;
var accentGridUI = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

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
// IC1-6 Min/Max (Ola 5), one handler per interval class -- same "un token por indice" shape as
// setvecmin/setvecmax themselves, not a shared array field (globalState is flat scalars everywhere
// else, see gsilence/gvelmin above).
function gvec1(a, b) { globalState.vecMin1 = Math.round(a); globalState.vecMax1 = Math.round(b); mgraphics.redraw(); }
function gvec2(a, b) { globalState.vecMin2 = Math.round(a); globalState.vecMax2 = Math.round(b); mgraphics.redraw(); }
function gvec3(a, b) { globalState.vecMin3 = Math.round(a); globalState.vecMax3 = Math.round(b); mgraphics.redraw(); }
function gvec4(a, b) { globalState.vecMin4 = Math.round(a); globalState.vecMax4 = Math.round(b); mgraphics.redraw(); }
function gvec5(a, b) { globalState.vecMin5 = Math.round(a); globalState.vecMax5 = Math.round(b); mgraphics.redraw(); }
function gvec6(a, b) { globalState.vecMin6 = Math.round(a); globalState.vecMax6 = Math.round(b); mgraphics.redraw(); }
function grandmask(p) { globalState.randMaskPct = Math.round(p); mgraphics.redraw(); }
// Groove (col 5). `gsub` viaja suelto porque ademas de su propio valor es el GATE de casi toda la
// columna; los otros siete llegan agrupados en dos mensajes, uno por familia de gate.
function gsub(n) { globalState.sub = Math.round(n); mgraphics.redraw(); }
function ggroove(sw, hu, ra, dr) {
	globalState.swing = Math.round(sw);
	globalState.human = Math.round(hu);
	globalState.rasg = Math.round(ra);
	globalState.dirRasg = Math.round(dr);
	mgraphics.redraw();
}
function gratchet(rn, ra, pr, dc) {
	globalState.ratN = Math.round(rn);
	globalState.ratA = Math.round(ra);
	globalState.ratProb = Math.round(pr);
	globalState.ratCaida = Math.round(dc);
	mgraphics.redraw();
}

// Acentos (col 6) -- Ciclo/Tie, Euclid+Pulsos+Giro, y VelMin/VelMax/Figura por grupo agrupados
// por parametro (misma disciplina que gsilence), mas la tira de 16 acentos read-only.
function gaccent(c, t) {
	globalState.accCiclo = Math.round(c);
	globalState.accTie = Math.round(t) ? 1 : 0;
	mgraphics.redraw();
}
function geuclid(on, k, rot) {
	globalState.euclidOn = Math.round(on) ? 1 : 0;
	globalState.euclidK = Math.round(k);
	globalState.euclidRot = Math.round(rot);
	mgraphics.redraw();
}
function gvelmin(n, a) { globalState.velMinN = Math.round(n); globalState.velMinA = Math.round(a); mgraphics.redraw(); }
function gvelmax(n, a) { globalState.velMaxN = Math.round(n); globalState.velMaxA = Math.round(a); mgraphics.redraw(); }
function gfig(n, a) { globalState.figN = Math.round(n); globalState.figA = Math.round(a); mgraphics.redraw(); }
function gaccentgrid() {
	var a = arrayfromargs(arguments);
	for (var i = 0; i < ACCENT_MAX_UI; i++) accentGridUI[i] = (i < a.length && a[i]) ? 1 : 0;
	mgraphics.redraw();
}

// Camino armonico (col 7) -- dos familias, dos mensajes, misma disciplina que ggroove/gratchet.
function gtension(n, s, m) {
	globalState.tension = Math.round(n);
	globalState.curva = Math.round(s);
	globalState.tensmodel = Math.round(m);
	mgraphics.redraw();
}
function gfavstate(pf, fo, len, fv) {
	globalState.progfav = Math.round(pf) ? 1 : 0;
	globalState.favonly = Math.round(fo) ? 1 : 0;
	globalState.favSeqLen = Math.round(len);
	globalState.fav = Math.round(fv) ? 1 : 0;
	mgraphics.redraw();
}

// Registro y recorrido (Ola 4, col 1 filas 9-13) -- dos mensajes, misma disciplina que
// ggroove/gratchet/gtension. "registro" es exactamente lo que Drum apaga de un saque (Sec Raiz,
// Oct Maestra, Drum, Pad); "recorrido" son las tres formas de caminar el set activo.
function gregistro(rs, om, dr, pd) {
	globalState.rootSeq = Math.round(rs);
	globalState.octMaestra = Math.round(om);
	globalState.drum = Math.round(dr) ? 1 : 0;
	globalState.pad = Math.round(pd);
	mgraphics.redraw();
}
function grecorrido(rot, rx, sk) {
	globalState.rotacion = Math.round(rot);
	globalState.rotarx = Math.round(rx) ? 1 : 0;
	globalState.salto = Math.round(sk);
	mgraphics.redraw();
}

// Modulacion (Ola 6, col 8) -- one message per modulator, matching one matrix row per message
// (see querynext()'s own comment): a drag on modulator 2 never touches globalState.mod1*/mod3*/
// mod4*, so it never forces the other three rows to redraw either.
function gmod1(s, c, d, p, de) {
	globalState.mod1shape = Math.round(s); globalState.mod1cycle = Math.round(c);
	globalState.mod1depth = Math.round(d); globalState.mod1phase = Math.round(p);
	globalState.mod1dest = Math.round(de);
	mgraphics.redraw();
}
function gmod2(s, c, d, p, de) {
	globalState.mod2shape = Math.round(s); globalState.mod2cycle = Math.round(c);
	globalState.mod2depth = Math.round(d); globalState.mod2phase = Math.round(p);
	globalState.mod2dest = Math.round(de);
	mgraphics.redraw();
}
function gmod3(s, c, d, p, de) {
	globalState.mod3shape = Math.round(s); globalState.mod3cycle = Math.round(c);
	globalState.mod3depth = Math.round(d); globalState.mod3phase = Math.round(p);
	globalState.mod3dest = Math.round(de);
	mgraphics.redraw();
}
function gmod4(s, c, d, p, de) {
	globalState.mod4shape = Math.round(s); globalState.mod4cycle = Math.round(c);
	globalState.mod4depth = Math.round(d); globalState.mod4phase = Math.round(p);
	globalState.mod4dest = Math.round(de);
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
		send: function (v, nv) { outlet(0, ['setmaskk', nv]); } },
	// IC1-6 Min/Max (Ola 5), still col 4 -- 12 specs, one per numbox, setvecmin/setvecmax take the
	// interval-class index as their first argument (same "index, then value" shape as setratchet/
	// setgroupvelmin above), so each IC gets its own min spec and its own max spec.
	gvmin1: { min: 0, max: 12, field: 'vecMin1', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmin', 1, nv]); } },
	gvmax1: { min: 0, max: 12, field: 'vecMax1', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmax', 1, nv]); } },
	gvmin2: { min: 0, max: 12, field: 'vecMin2', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmin', 2, nv]); } },
	gvmax2: { min: 0, max: 12, field: 'vecMax2', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmax', 2, nv]); } },
	gvmin3: { min: 0, max: 12, field: 'vecMin3', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmin', 3, nv]); } },
	gvmax3: { min: 0, max: 12, field: 'vecMax3', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmax', 3, nv]); } },
	gvmin4: { min: 0, max: 12, field: 'vecMin4', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmin', 4, nv]); } },
	gvmax4: { min: 0, max: 12, field: 'vecMax4', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmax', 4, nv]); } },
	gvmin5: { min: 0, max: 12, field: 'vecMin5', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmin', 5, nv]); } },
	gvmax5: { min: 0, max: 12, field: 'vecMax5', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmax', 5, nv]); } },
	gvmin6: { min: 0, max: 12, field: 'vecMin6', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmin', 6, nv]); } },
	gvmax6: { min: 0, max: 12, field: 'vecMax6', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setvecmax', 6, nv]); } },
	grandmaskpct: { min: 0, max: 100, field: 'randMaskPct', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setrandmaskpct', nv]); } },
	// Col 5 (Groove), same global-sidebar idiom. setratchet takes the group index first, so Rat N
	// and Rat A are two specs over the same setter -- the same shape gsilnorm/gsilacc already use.
	gswing: { min: 50, max: 75, field: 'swing', pxPerUnit: 5, global: true,
		send: function (v, nv) { outlet(0, ['setswing', nv]); } },
	ghuman: { min: 0, max: 100, field: 'human', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['sethumanize', nv]); } },
	grasg: { min: 0, max: 8, field: 'rasg', pxPerUnit: 12, global: true,
		send: function (v, nv) { outlet(0, ['setstrum', nv]); } },
	gratn: { min: 1, max: 4, field: 'ratN', pxPerUnit: 16, global: true,
		send: function (v, nv) { outlet(0, ['setratchet', 0, nv]); } },
	grata: { min: 1, max: 4, field: 'ratA', pxPerUnit: 16, global: true,
		send: function (v, nv) { outlet(0, ['setratchet', 1, nv]); } },
	gratprob: { min: 0, max: 100, field: 'ratProb', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setratchetprob', nv]); } },
	gratcaida: { min: 0, max: 100, field: 'ratCaida', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setratchetdecay', nv]); } },
	// Col 6 (Acentos), same global-sidebar idiom. VelMin/VelMax/Figura take the group index first
	// (setgroupvelmin/setgroupvelmax/setgroupdur), so Normal and Acento are two specs over the same
	// setter each -- same shape gsilnorm/gsilacc and gratn/grata already use.
	gciclo: { min: 1, max: 16, field: 'accCiclo', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setaccentcycle', nv]); } },
	geuck: { min: 0, max: 16, field: 'euclidK', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['seteuclidk', nv]); } },
	geurot: { min: 0, max: 15, field: 'euclidRot', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['seteuclidrot', nv]); } },
	gvelminn: { min: 1, max: 127, field: 'velMinN', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setgroupvelmin', 0, nv]); } },
	gvelmina: { min: 1, max: 127, field: 'velMinA', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setgroupvelmin', 1, nv]); } },
	gvelmaxn: { min: 1, max: 127, field: 'velMaxN', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setgroupvelmax', 0, nv]); } },
	gvelmaxa: { min: 1, max: 127, field: 'velMaxA', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setgroupvelmax', 1, nv]); } },
	gfign: { min: 1, max: 32, field: 'figN', pxPerUnit: 6, global: true,
		send: function (v, nv) { outlet(0, ['setgroupdur', 0, nv]); } },
	gfiga: { min: 1, max: 32, field: 'figA', pxPerUnit: 6, global: true,
		send: function (v, nv) { outlet(0, ['setgroupdur', 1, nv]); } },
	// Col 7 (Camino armonico), same global-sidebar idiom. Curva/Modelo are dropdowns (openMenu), not
	// drag-scrubs -- see onclick()'s v===-1 branch and paint()'s Camino block.
	gtension: { min: 0, max: 16, field: 'tension', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['settension', nv]); } },
	// Col 1 filas 9-13 (Registro/Recorrido, Ola 4), mismo idioma global-sidebar. Rotacion no tiene un
	// rango fijo en el motor (wrap mod la cardinalidad del set activo, ver setrotation()) -- 0-11
	// cubre cualquier cardinalidad real y el motor mismo hace el wrap final, asi que un arrastre mas
	// alla del set actual simplemente se clampea aca, sin desincronizar nada.
	goctm: { min: -5, max: 5, field: 'octMaestra', pxPerUnit: 8, global: true,
		send: function (v, nv) { outlet(0, ['setmasteroctave', nv]); } },
	gpad: { min: 0, max: 115, field: 'pad', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setdrumbase', nv]); } },
	grotacion: { min: 0, max: 11, field: 'rotacion', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setrotation', nv]); } },
	gsalto: { min: 1, max: 11, field: 'salto', pxPerUnit: 10, global: true,
		send: function (v, nv) { outlet(0, ['setcoprime', nv]); } },
	// Col 8 (Modulacion, Ola 6), same global-sidebar idiom. Forma/Dest are dropdowns (openMenu), not
	// drag-scrubs -- see onclick()'s v===-1 branch and paint()'s Modulacion block. setmod* all take
	// the modulator index k=1..4 as their first argument, same "index, then value" shape as
	// setvecmin/setvecmax/setratchet above.
	gmod1cycle: { min: 1, max: 64, field: 'mod1cycle', pxPerUnit: 6, global: true,
		send: function (v, nv) { outlet(0, ['setmodcycle', 1, nv]); } },
	gmod1depth: { min: -100, max: 100, field: 'mod1depth', pxPerUnit: 2, global: true,
		send: function (v, nv) { outlet(0, ['setmoddepth', 1, nv]); } },
	gmod1phase: { min: 0, max: 100, field: 'mod1phase', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setmodphase', 1, nv]); } },
	gmod2cycle: { min: 1, max: 64, field: 'mod2cycle', pxPerUnit: 6, global: true,
		send: function (v, nv) { outlet(0, ['setmodcycle', 2, nv]); } },
	gmod2depth: { min: -100, max: 100, field: 'mod2depth', pxPerUnit: 2, global: true,
		send: function (v, nv) { outlet(0, ['setmoddepth', 2, nv]); } },
	gmod2phase: { min: 0, max: 100, field: 'mod2phase', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setmodphase', 2, nv]); } },
	gmod3cycle: { min: 1, max: 64, field: 'mod3cycle', pxPerUnit: 6, global: true,
		send: function (v, nv) { outlet(0, ['setmodcycle', 3, nv]); } },
	gmod3depth: { min: -100, max: 100, field: 'mod3depth', pxPerUnit: 2, global: true,
		send: function (v, nv) { outlet(0, ['setmoddepth', 3, nv]); } },
	gmod3phase: { min: 0, max: 100, field: 'mod3phase', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setmodphase', 3, nv]); } },
	gmod4cycle: { min: 1, max: 64, field: 'mod4cycle', pxPerUnit: 6, global: true,
		send: function (v, nv) { outlet(0, ['setmodcycle', 4, nv]); } },
	gmod4depth: { min: -100, max: 100, field: 'mod4depth', pxPerUnit: 2, global: true,
		send: function (v, nv) { outlet(0, ['setmoddepth', 4, nv]); } },
	gmod4phase: { min: 0, max: 100, field: 'mod4phase', pxPerUnit: 3, global: true,
		send: function (v, nv) { outlet(0, ['setmodphase', 4, nv]); } }
};

// "Pagina" (fs2_pagina) values for the tabs each advanced chip's real control lives on -- see
// add_fs2_gotopage.py for how these were measured. On/mute (cg.on) has no page: its control is
// always on the main panel, never gated by Pagina.
var PAGE_VOCES1 = 6, PAGE_VOCES2 = 7, PAGE_VOCES3 = 9, PAGE_VOCES4 = 10;

function ptIn(r, x, y) {
	return r && x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h;
}

// alarm (Ola 3): its own color, independent of on/disabled/dim -- for the plan's "trampas
// silenciosas" (state that LOOKS fine but silently kills another control), never used together
// with dim on the same chip since alarm already implies "look here", the opposite of dimming.
function drawChip(r, label, on, disabled, dim, alarm) {
	dim = dim === undefined ? 1 : dim;
	mgraphics.set_source_rgba(alarm ? [0.55, 0.2, 0.1, 1] : (on ? [0.55 * dim, 0.42 * dim, 0.15 * dim, 1] : [0.22, 0.22, 0.25, 1]));
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.fill();
	mgraphics.set_source_rgba([0, 0, 0, 0.5]);
	mgraphics.set_line_width(1);
	mgraphics.rectangle(r.x, r.y, r.w, r.h);
	mgraphics.stroke();
	mgraphics.set_source_rgba(alarm ? [1, 0.6, 0.4, 1] : (on ? [1 * dim, 0.85 * dim, 0.55 * dim, 1] : (disabled ? [0.4, 0.4, 0.44, 1] : [0.55, 0.55, 0.6, 1])));
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
					} else if (openMenu.kind === 'gsub') {
						// El unico dropdown cuyo item NO es su propio valor: el indice elige de
						// SUB_VALUES y al motor sale el DIVISOR (setsub lo toma asi). La vuelta a
						// indice, para el live.menu del panel, la hace el eco en forteseq2.js.
						globalState.sub = SUB_VALUES[mi];
						outlet(0, ['setsub', globalState.sub]);
					} else if (openMenu.kind === 'gcurva') {
						globalState.curva = mi;
						outlet(0, ['settenshape', mi]);
					} else if (openMenu.kind === 'gtensmodel') {
						globalState.tensmodel = mi;
						outlet(0, ['settensmodel', mi]);
					} else if (openMenu.kind === 'grootseq') {
						globalState.rootSeq = mi;
						outlet(0, ['setrootseq', mi]);
					} else if (openMenu.kind === 'gmod1shape') {
						globalState.mod1shape = mi;
						outlet(0, ['setmodshape', 1, mi]);
					} else if (openMenu.kind === 'gmod1dest') {
						globalState.mod1dest = mi;
						outlet(0, ['setmoddest', 1, mi]);
					} else if (openMenu.kind === 'gmod2shape') {
						globalState.mod2shape = mi;
						outlet(0, ['setmodshape', 2, mi]);
					} else if (openMenu.kind === 'gmod2dest') {
						globalState.mod2dest = mi;
						outlet(0, ['setmoddest', 2, mi]);
					} else if (openMenu.kind === 'gmod3shape') {
						globalState.mod3shape = mi;
						outlet(0, ['setmodshape', 3, mi]);
					} else if (openMenu.kind === 'gmod3dest') {
						globalState.mod3dest = mi;
						outlet(0, ['setmoddest', 3, mi]);
					} else if (openMenu.kind === 'gmod4shape') {
						globalState.mod4shape = mi;
						outlet(0, ['setmodshape', 4, mi]);
					} else if (openMenu.kind === 'gmod4dest') {
						globalState.mod4dest = mi;
						outlet(0, ['setmoddest', 4, mi]);
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
	// IC1-6 Min/Max rows + Azar % Mask (Ola 5), bottom of col 4. Azar Mascara itself is an action
	// (rule 8) -- straight to the message, no dragBox/openMenu, same idiom as clearfavs above.
	if (globalChipGeo.vmin1 && ptIn(globalChipGeo.vmin1, x, y)) { dragBox = { v: -1, kind: 'gvmin1', startY: y, startVal: globalState.vecMin1 }; return; }
	if (globalChipGeo.vmax1 && ptIn(globalChipGeo.vmax1, x, y)) { dragBox = { v: -1, kind: 'gvmax1', startY: y, startVal: globalState.vecMax1 }; return; }
	if (globalChipGeo.vmin2 && ptIn(globalChipGeo.vmin2, x, y)) { dragBox = { v: -1, kind: 'gvmin2', startY: y, startVal: globalState.vecMin2 }; return; }
	if (globalChipGeo.vmax2 && ptIn(globalChipGeo.vmax2, x, y)) { dragBox = { v: -1, kind: 'gvmax2', startY: y, startVal: globalState.vecMax2 }; return; }
	if (globalChipGeo.vmin3 && ptIn(globalChipGeo.vmin3, x, y)) { dragBox = { v: -1, kind: 'gvmin3', startY: y, startVal: globalState.vecMin3 }; return; }
	if (globalChipGeo.vmax3 && ptIn(globalChipGeo.vmax3, x, y)) { dragBox = { v: -1, kind: 'gvmax3', startY: y, startVal: globalState.vecMax3 }; return; }
	if (globalChipGeo.vmin4 && ptIn(globalChipGeo.vmin4, x, y)) { dragBox = { v: -1, kind: 'gvmin4', startY: y, startVal: globalState.vecMin4 }; return; }
	if (globalChipGeo.vmax4 && ptIn(globalChipGeo.vmax4, x, y)) { dragBox = { v: -1, kind: 'gvmax4', startY: y, startVal: globalState.vecMax4 }; return; }
	if (globalChipGeo.vmin5 && ptIn(globalChipGeo.vmin5, x, y)) { dragBox = { v: -1, kind: 'gvmin5', startY: y, startVal: globalState.vecMin5 }; return; }
	if (globalChipGeo.vmax5 && ptIn(globalChipGeo.vmax5, x, y)) { dragBox = { v: -1, kind: 'gvmax5', startY: y, startVal: globalState.vecMax5 }; return; }
	if (globalChipGeo.vmin6 && ptIn(globalChipGeo.vmin6, x, y)) { dragBox = { v: -1, kind: 'gvmin6', startY: y, startVal: globalState.vecMin6 }; return; }
	if (globalChipGeo.vmax6 && ptIn(globalChipGeo.vmax6, x, y)) { dragBox = { v: -1, kind: 'gvmax6', startY: y, startVal: globalState.vecMax6 }; return; }
	if (globalChipGeo.randmaskpct && ptIn(globalChipGeo.randmaskpct, x, y)) { dragBox = { v: -1, kind: 'grandmaskpct', startY: y, startVal: globalState.randMaskPct }; return; }
	if (globalChipGeo.randmask && ptIn(globalChipGeo.randmask, x, y)) { outlet(0, ['randomizemask']); return; }
	// Col 1 rows 7-8 (always drawn) -- Modo Toque toggles, Sub cycles through the six values its
	// real live.menu offers. Sub is deliberately NOT a free 1-8 scrub even though setsub() accepts
	// 5 and 7: those two have no slot in the panel menu, so the echo could not move the widget back.
	if (ptIn(globalChipGeo.modo, x, y)) {
		globalState.mode = Math.round(globalState.mode) === MODE_CHORDS ? 1 : MODE_CHORDS;
		outlet(0, ['setmode', globalState.mode]); mgraphics.redraw(); return;
	}
	if (ptIn(globalChipGeo.sub, x, y)) { openMenu = { v: -1, kind: 'gsub' }; mgraphics.redraw(); return; }
	// Col 1 filas 9-13 (Registro/Recorrido, Ola 4) -- Sec Raiz dropdown; Oct Maestra/Pad/Rotacion
	// drag-scrub; Drum/Rotar x Cambio toggle chips (mismo idioma que ind/flt/lck/tie/euc); Salto solo
	// hit-testable mientras Patron===Coprimo (su geo queda sin setear si no, mismo convenio que
	// maskk/nmin/nmax/eupuls/eugir).
	if (globalChipGeo.rootseq && ptIn(globalChipGeo.rootseq, x, y)) { openMenu = { v: -1, kind: 'grootseq' }; mgraphics.redraw(); return; }
	if (globalChipGeo.octm && ptIn(globalChipGeo.octm, x, y)) { dragBox = { v: -1, kind: 'goctm', startY: y, startVal: globalState.octMaestra }; return; }
	if (globalChipGeo.drum && ptIn(globalChipGeo.drum, x, y)) { globalState.drum = globalState.drum ? 0 : 1; outlet(0, ['setdrum', globalState.drum]); mgraphics.redraw(); return; }
	if (globalChipGeo.pad && ptIn(globalChipGeo.pad, x, y)) { dragBox = { v: -1, kind: 'gpad', startY: y, startVal: globalState.pad }; return; }
	if (globalChipGeo.rotacion && ptIn(globalChipGeo.rotacion, x, y)) { dragBox = { v: -1, kind: 'grotacion', startY: y, startVal: globalState.rotacion }; return; }
	if (globalChipGeo.rotarx && ptIn(globalChipGeo.rotarx, x, y)) { globalState.rotarx = globalState.rotarx ? 0 : 1; outlet(0, ['setshape', globalState.rotarx]); mgraphics.redraw(); return; }
	if (globalChipGeo.salto && ptIn(globalChipGeo.salto, x, y)) { dragBox = { v: -1, kind: 'gsalto', startY: y, startVal: globalState.salto }; return; }
	// Col 5 (Groove) -- only hit-testable while that column is drawn (its geo stays unset otherwise).
	if (globalChipGeo.swing && ptIn(globalChipGeo.swing, x, y)) { dragBox = { v: -1, kind: 'gswing', startY: y, startVal: globalState.swing }; return; }
	if (globalChipGeo.human && ptIn(globalChipGeo.human, x, y)) { dragBox = { v: -1, kind: 'ghuman', startY: y, startVal: globalState.human }; return; }
	if (globalChipGeo.rasg && ptIn(globalChipGeo.rasg, x, y)) { dragBox = { v: -1, kind: 'grasg', startY: y, startVal: globalState.rasg }; return; }
	if (globalChipGeo.dirrasg && ptIn(globalChipGeo.dirrasg, x, y)) {
		globalState.dirRasg = (Math.round(globalState.dirRasg) + 1) % 4;
		outlet(0, ['setstrumdir', globalState.dirRasg]); mgraphics.redraw(); return;
	}
	if (globalChipGeo.ratn && ptIn(globalChipGeo.ratn, x, y)) { dragBox = { v: -1, kind: 'gratn', startY: y, startVal: globalState.ratN }; return; }
	if (globalChipGeo.rata && ptIn(globalChipGeo.rata, x, y)) { dragBox = { v: -1, kind: 'grata', startY: y, startVal: globalState.ratA }; return; }
	if (globalChipGeo.ratprob && ptIn(globalChipGeo.ratprob, x, y)) { dragBox = { v: -1, kind: 'gratprob', startY: y, startVal: globalState.ratProb }; return; }
	if (globalChipGeo.ratcaida && ptIn(globalChipGeo.ratcaida, x, y)) { dragBox = { v: -1, kind: 'gratcaida', startY: y, startVal: globalState.ratCaida }; return; }
	if (globalChipGeo.maskfit && ptIn(globalChipGeo.maskfit, x, y)) { globalState.maskFit = globalState.maskFit ? 0 : 1; outlet(0, ['setmaskfit', globalState.maskFit]); mgraphics.redraw(); return; }
	// Col 6 (Acentos) -- Ciclo/VelMin/VelMax/Figura drag-scrub; Tie/Euclid toggle chips (same idiom
	// as ind/flt/lck); Pulsos/Giro only hit-testable while Euclid is on (their geo stays unset
	// otherwise, same convention as maskk/nmin/nmax).
	if (globalChipGeo.ciclo && ptIn(globalChipGeo.ciclo, x, y)) { dragBox = { v: -1, kind: 'gciclo', startY: y, startVal: globalState.accCiclo }; return; }
	if (globalChipGeo.tie && ptIn(globalChipGeo.tie, x, y)) { globalState.accTie = globalState.accTie ? 0 : 1; outlet(0, ['setaccenttie', globalState.accTie]); mgraphics.redraw(); return; }
	if (globalChipGeo.euc && ptIn(globalChipGeo.euc, x, y)) { globalState.euclidOn = globalState.euclidOn ? 0 : 1; outlet(0, ['seteuclid', globalState.euclidOn]); mgraphics.redraw(); return; }
	if (globalChipGeo.eupuls && ptIn(globalChipGeo.eupuls, x, y)) { dragBox = { v: -1, kind: 'geuck', startY: y, startVal: globalState.euclidK }; return; }
	if (globalChipGeo.eugir && ptIn(globalChipGeo.eugir, x, y)) { dragBox = { v: -1, kind: 'geurot', startY: y, startVal: globalState.euclidRot }; return; }
	if (globalChipGeo.velminn && ptIn(globalChipGeo.velminn, x, y)) { dragBox = { v: -1, kind: 'gvelminn', startY: y, startVal: globalState.velMinN }; return; }
	if (globalChipGeo.velmina && ptIn(globalChipGeo.velmina, x, y)) { dragBox = { v: -1, kind: 'gvelmina', startY: y, startVal: globalState.velMinA }; return; }
	if (globalChipGeo.velmaxn && ptIn(globalChipGeo.velmaxn, x, y)) { dragBox = { v: -1, kind: 'gvelmaxn', startY: y, startVal: globalState.velMaxN }; return; }
	if (globalChipGeo.velmaxa && ptIn(globalChipGeo.velmaxa, x, y)) { dragBox = { v: -1, kind: 'gvelmaxa', startY: y, startVal: globalState.velMaxA }; return; }
	if (globalChipGeo.fign && ptIn(globalChipGeo.fign, x, y)) { dragBox = { v: -1, kind: 'gfign', startY: y, startVal: globalState.figN }; return; }
	if (globalChipGeo.figa && ptIn(globalChipGeo.figa, x, y)) { dragBox = { v: -1, kind: 'gfiga', startY: y, startVal: globalState.figA }; return; }
	// Col 7 (Camino armonico) -- Tension drag-scrub; Curva/Modelo dropdowns; Prog Favoritos/Solo
	// Fav/Fav toggle chips (same idiom as ind/flt/lck/tie/euc); Limpiar favs is an action, no state.
	if (globalChipGeo.tension && ptIn(globalChipGeo.tension, x, y)) { dragBox = { v: -1, kind: 'gtension', startY: y, startVal: globalState.tension }; return; }
	if (globalChipGeo.curva && ptIn(globalChipGeo.curva, x, y)) { openMenu = { v: -1, kind: 'gcurva' }; mgraphics.redraw(); return; }
	if (globalChipGeo.tensmodel && ptIn(globalChipGeo.tensmodel, x, y)) { openMenu = { v: -1, kind: 'gtensmodel' }; mgraphics.redraw(); return; }
	if (globalChipGeo.progfav && ptIn(globalChipGeo.progfav, x, y)) { globalState.progfav = globalState.progfav ? 0 : 1; outlet(0, ['setfavseq', globalState.progfav]); mgraphics.redraw(); return; }
	if (globalChipGeo.favonly && ptIn(globalChipGeo.favonly, x, y)) { globalState.favonly = globalState.favonly ? 0 : 1; outlet(0, ['setfavonly', globalState.favonly]); mgraphics.redraw(); return; }
	if (globalChipGeo.fav && ptIn(globalChipGeo.fav, x, y)) { globalState.fav = globalState.fav ? 0 : 1; outlet(0, ['setfav', globalState.fav]); mgraphics.redraw(); return; }
	if (globalChipGeo.clearfavs && ptIn(globalChipGeo.clearfavs, x, y)) { outlet(0, ['clearfavs']); return; }
	// Col 8 (Modulacion, Ola 6) -- Forma/Dest open a dropdown (openMenu, same as Curva/Modelo above);
	// Ciclo/Prof/Fase arm a drag-scrub. Always drawn (modOpen is a constant true, see paint()), so no
	// `globalChipGeo.mod1shape &&` guard is needed the way Euclid's Pulsos/Giro need one.
	if (ptIn(globalChipGeo.mod1shape, x, y)) { openMenu = { v: -1, kind: 'gmod1shape' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.mod1cycle, x, y)) { dragBox = { v: -1, kind: 'gmod1cycle', startY: y, startVal: globalState.mod1cycle }; return; }
	if (ptIn(globalChipGeo.mod1depth, x, y)) { dragBox = { v: -1, kind: 'gmod1depth', startY: y, startVal: globalState.mod1depth }; return; }
	if (ptIn(globalChipGeo.mod1phase, x, y)) { dragBox = { v: -1, kind: 'gmod1phase', startY: y, startVal: globalState.mod1phase }; return; }
	if (ptIn(globalChipGeo.mod1dest, x, y)) { openMenu = { v: -1, kind: 'gmod1dest' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.mod2shape, x, y)) { openMenu = { v: -1, kind: 'gmod2shape' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.mod2cycle, x, y)) { dragBox = { v: -1, kind: 'gmod2cycle', startY: y, startVal: globalState.mod2cycle }; return; }
	if (ptIn(globalChipGeo.mod2depth, x, y)) { dragBox = { v: -1, kind: 'gmod2depth', startY: y, startVal: globalState.mod2depth }; return; }
	if (ptIn(globalChipGeo.mod2phase, x, y)) { dragBox = { v: -1, kind: 'gmod2phase', startY: y, startVal: globalState.mod2phase }; return; }
	if (ptIn(globalChipGeo.mod2dest, x, y)) { openMenu = { v: -1, kind: 'gmod2dest' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.mod3shape, x, y)) { openMenu = { v: -1, kind: 'gmod3shape' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.mod3cycle, x, y)) { dragBox = { v: -1, kind: 'gmod3cycle', startY: y, startVal: globalState.mod3cycle }; return; }
	if (ptIn(globalChipGeo.mod3depth, x, y)) { dragBox = { v: -1, kind: 'gmod3depth', startY: y, startVal: globalState.mod3depth }; return; }
	if (ptIn(globalChipGeo.mod3phase, x, y)) { dragBox = { v: -1, kind: 'gmod3phase', startY: y, startVal: globalState.mod3phase }; return; }
	if (ptIn(globalChipGeo.mod3dest, x, y)) { openMenu = { v: -1, kind: 'gmod3dest' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.mod4shape, x, y)) { openMenu = { v: -1, kind: 'gmod4shape' }; mgraphics.redraw(); return; }
	if (ptIn(globalChipGeo.mod4cycle, x, y)) { dragBox = { v: -1, kind: 'gmod4cycle', startY: y, startVal: globalState.mod4cycle }; return; }
	if (ptIn(globalChipGeo.mod4depth, x, y)) { dragBox = { v: -1, kind: 'gmod4depth', startY: y, startVal: globalState.mod4depth }; return; }
	if (ptIn(globalChipGeo.mod4phase, x, y)) { dragBox = { v: -1, kind: 'gmod4phase', startY: y, startVal: globalState.mod4phase }; return; }
	if (ptIn(globalChipGeo.mod4dest, x, y)) { openMenu = { v: -1, kind: 'gmod4dest' }; mgraphics.redraw(); return; }
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
	var accGridH = 18;   // the read-only 16-cell accent strip (col 6, Ola 2) -- always shown
	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH - accGridH);
	var rowH = gridH / nRows;
	rowGeo = { headH: headH, rowH: rowH, nRows: nRows };   // read by onclick() to find the row hit

	var G_COL_W = 86, G_GAP = 4;   // width of each fixed sidebar column, and the gap between them
	var ornOpen = globalState.patron === READ_ORNAMENT;   // Ornamento slot only exists while Patron IS Ornamento
	var filtOpen = !!globalState.filtered;                // Filtro slot only exists while Flt is on
	// La columna Groove aparece con Sub >= 2 y con nada mas: UNA causa, una consecuencia, igual que
	// Patron=Ornamento y Flt. Estuvo un rato gateada por `subLive || chordLive` porque strumOffset()
	// no mira subDiv -- su unica condicion es `n < 2` -- asi que Rasg tecnicamente hace algo en
	// Acordes con Sub=1. Pero ese algo es degenerado: el offset se mide en SUB-TICKS y con Sub=1 un
	// sub-tick es un paso entero, asi que Rasg=1 sobre un acorde de 4 notas las reparte en 4 pasos
	// pisando lo que venga. No es un rasgueo, es arpegiar a lo largo de la secuencia. No vale un
	// gate que acopla una columna de RITMO a un control de TEXTURA ARMONICA, que nadie predice.
	// chordLive sobrevive, pero solo para atenuar Rasg/Dir Rasg ADENTRO de la columna.
	var subLive = Math.round(globalState.sub) >= 2;
	var chordLive = Math.round(globalState.mode) === MODE_CHORDS;
	var grooveOpen = subLive;
	// Acentos (col 6) no tiene gate propio -- a diferencia de Ornamento/Filtro/Groove no hay un
	// estado "apagado" para la articulacion o el Euclid global (siempre hay un ciclo de acentos
	// sonando, este o no Euclid prendido), asi que la columna esta siempre presente. Sigue entrando
	// en condCols para heredar el mismo empaquetado de slot -- toma el primero libre DESPUES de
	// Ornamento/Filtro/Groove, nunca reflowea col 1/2 -- en vez de escribirse como una quinta
	// columna fija a mano.
	var accOpen = true;
	// Camino armonico (col 7): tampoco tiene gate propio -- siempre hay una politica de avance de
	// set corriendo (Escuchar/Seguir/Fav curada/Tension/orden normal), nunca un estado "apagado" que
	// la haga desaparecer sin mas -- misma razon que Acentos, ultima en la prioridad de slot.
	var caminoOpen = true;
	// Prog Favoritos (favSeqOn) con la lista LLENA pisa Tension/Curva/Modelo Y Enlace por completo
	// (advanceFavSeq() nunca los consulta). Con la lista VACIA es la trampa silenciosa del plan:
	// advanceFavSeq() cae a advanceInOrder(), asi que Enlace/Orden/filtro reviven pero Tension queda
	// muerta igual (la rama favSeqOn ya devolvio antes de llegar a advanceByTension()). Dos flags
	// separadas porque dimean cosas distintas -- ver el bloque Camino y el chip Enlace de col 1.
	var favSeqActive = !!globalState.progfav && globalState.favSeqLen > 0;
	var favSeqTrap = !!globalState.progfav && globalState.favSeqLen === 0;
	// Modulacion (col 8, Ola 6): also no gate of its own -- four modulators always exist, same
	// reasoning as Acentos/Camino, last in slot priority.
	var modOpen = true;
	// Orden de prioridad de slot, FIJO (Ornamento -> Filtro -> Groove -> Acentos -> Camino ->
	// Modulacion): los slots condicionales se empaquetan sin hueco, cada uno toma el primero libre en
	// este orden. Con mas de dos familias esto ya no se puede escribir a mano, asi que va como lista.
	var condCols = [];
	if (ornOpen) condCols.push('orn');
	if (filtOpen) condCols.push('filt');
	if (grooveOpen) condCols.push('groove');
	if (accOpen) condCols.push('acc');
	if (caminoOpen) condCols.push('camino');
	if (modOpen) condCols.push('mod');
	// Every conditional column is one G_COL_W wide except Modulacion: a 4x5 matrix does not fit in
	// 86px, so it claims roughly two slots' worth of room (MOD_COL_W) instead. condSlotX() below
	// walks condCols summing each one's own width rather than assuming a uniform G_COL_W, which is
	// the only change from the plain "extraCols * (G_GAP + G_COL_W)" formula every earlier column used.
	var MOD_COL_W = G_COL_W * 2 + G_GAP;
	function condColW(name) { return name === 'mod' ? MOD_COL_W : G_COL_W; }
	var extraW = 0;
	for (var _cci = 0; _cci < condCols.length; _cci++) extraW += G_GAP + condColW(condCols[_cci]);
	var GLOBAL_W = 2 + G_COL_W + G_GAP + G_COL_W + 2 + extraW;
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
	var slot3x = g2x + g2w + G_GAP;   // where the first conditional slot starts
	function condSlotX(name) {        // -1 when that family is closed -- its chips then never get a geo
		var x = slot3x;
		for (var ck = 0; ck < condCols.length; ck++) {
			if (condCols[ck] === name) return x;
			x += G_GAP + condColW(condCols[ck]);
		}
		return -1;
	}
	var g3x = condSlotX('orn'), g3w = G_COL_W;
	var g4x = condSlotX('filt'), g4w = G_COL_W;
	var g5x = condSlotX('groove'), g5w = G_COL_W;
	var g6x = condSlotX('acc'), g6w = G_COL_W;
	var g7x = condSlotX('camino'), g7w = G_COL_W;
	var g8x = condSlotX('mod'), g8w = MOD_COL_W;
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
	if (grooveOpen) {
		mgraphics.move_to(g5x, headH - 5);
		mgraphics.show_text('Groove');
	}
	if (accOpen) {
		mgraphics.move_to(g6x, headH - 5);
		mgraphics.show_text('Acentos');
	}
	if (caminoOpen) {
		mgraphics.move_to(g7x, headH - 5);
		mgraphics.show_text('Camino');
	}
	if (modOpen) {
		mgraphics.move_to(g8x, headH - 5);
		mgraphics.show_text('Modulacion');
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
		// Dimmed (idem Rasg/Dir Rasg en col 5) mientras Prog Favoritos maneja la progresion con la
		// lista llena -- advanceFavSeq() nunca consulta linkMin. Con la lista vacia (favSeqTrap)
		// Enlace SI revive (cae a advanceInOrder()), asi que no se dimea ahi.
		drawChip(globalChipGeo.enlace, 'Enl ' + globalState.enlace, false, favSeqActive);
	}
	// Rows 7-8 -- Modo Toque y Sub, los dos GATES de la columna Groove, por eso van aca arriba y
	// siempre visibles: una columna condicional no puede alojar su propio gate (desapareceria con
	// el, y no habria como volver). Modo Toque ademas ya se leia (hstatus lo trae desde siempre) y
	// gobierna varios moot por voz; lo que faltaba era poder escribirlo, que ahora si tiene camino
	// probado (fs2_mode obj-19 -> prepend setmode -> motor, dentro de fs2pages.maxpat).
	if (gFits(7)) {
		globalChipGeo.modo = { x: g1x, y: gRow(7), w: g1w, h: gChipH };
		drawChip(globalChipGeo.modo, MODE_NAMES[Math.round(globalState.mode)] || '?', false);
	}
	// Sub va de dropdown, no de chip que cicla: su widget real ES un live.menu de seis items, asi
	// que la lista es el espejo exacto -- y ciclar +1 por click obliga a dar la vuelta entera para
	// bajar de 8 a 2. El dropdown ya se da vuelta solo si no entra hacia abajo (ver pendingMenu),
	// que importa justo aca por ser la ultima fila de la columna.
	if (gFits(8)) {
		globalChipGeo.sub = { x: g1x, y: gRow(8), w: g1w, h: gChipH };
		var gSubOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gsub';
		drawChip(globalChipGeo.sub, 'Sub ' + globalState.sub, gSubOpen);
		if (gSubOpen) pendingMenu = { v: -1, kind: 'gsub', anchor: globalChipGeo.sub, items: SUB_LABELS, cur: subIndexOf(globalState.sub) };
	}
	// Rows 9-13 (Ola 4) -- Registro y recorrido, agregadas a col 1 en vez de a una columna propia
	// (ver la charla del plan): Sec Raiz sola; Oct Maestra y Drum emparejadas (Drum es el gate mas
	// agresivo del device, apaga Oct Maestra, la octava por voz Y Rango -- ver col 2 mas abajo); Pad
	// OCULTO (no dimeado, no aporta lectura) salvo con Drum on, mismo idioma que Pulsos/Giro bajo
	// Euclid; Rotacion siempre vale (chordFor() la usa tambien en Acordes); Rotar x Cambio dimeada en
	// Acordes (rotShape solo gobierna el auto-avance de `rotation`, que step() ni toca en modo
	// acorde); Salto Coprimo OCULTO salvo con Patron===Coprimo, ultima fila, no empuja nada.
	var drumOn = !!globalState.drum;
	if (gFits(9)) {
		globalChipGeo.rootseq = { x: g1x, y: gRow(9), w: g1w, h: gChipH };
		var gRootSeqOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'grootseq';
		drawChip(globalChipGeo.rootseq, ROOTSEQ_NAMES[Math.round(globalState.rootSeq)] || '?', gRootSeqOpen);
		if (gRootSeqOpen) pendingMenu = { v: -1, kind: 'grootseq', anchor: globalChipGeo.rootseq, items: ROOTSEQ_NAMES, cur: Math.round(globalState.rootSeq) };
	}
	if (gFits(10)) {
		var g1dcw = (g1w - 2) / 2;
		globalChipGeo.octm = { x: g1x, y: gRow(10), w: g1dcw, h: gChipH };
		globalChipGeo.drum = { x: g1x + g1dcw + 2, y: gRow(10), w: g1dcw, h: gChipH };
		drawChip(globalChipGeo.octm, 'O' + (globalState.octMaestra > 0 ? '+' : '') + globalState.octMaestra, false, drumOn);
		drawChip(globalChipGeo.drum, 'Drum', drumOn);
	}
	if (drumOn && gFits(11)) {
		globalChipGeo.pad = { x: g1x, y: gRow(11), w: g1w, h: gChipH };
		drawChip(globalChipGeo.pad, 'Pad ' + globalState.pad, false);
	} else {
		globalChipGeo.pad = null;
	}
	if (gFits(12)) {
		globalChipGeo.rotacion = { x: g1x, y: gRow(12), w: g1w, h: gChipH };
		drawChip(globalChipGeo.rotacion, 'Rot ' + globalState.rotacion, false);
	}
	if (gFits(13)) {
		globalChipGeo.rotarx = { x: g1x, y: gRow(13), w: g1w, h: gChipH };
		drawChip(globalChipGeo.rotarx, 'Rot x Camb', !!globalState.rotarx, chordLive);
	}
	if (Math.round(globalState.patron) === READ_COPRIMO && gFits(14)) {
		globalChipGeo.salto = { x: g1x, y: gRow(14), w: g1w, h: gChipH };
		drawChip(globalChipGeo.salto, 'Salto ' + globalState.salto, false);
	} else {
		globalChipGeo.salto = null;
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
		// Dimmed con Drum on (Ola 4) -- drumOn cambia a padFor(pc), Rango deja de tener efecto, y
		// ya esta en pantalla (ver el bloque de col 1, filas 9-13, mas arriba).
		drawChip(globalChipGeo.rango, RANGE_NAMES[Math.round(globalState.rango)] || '?', gRangoOpen, drumOn);
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

	// Column 4 -- the Filtro cluster (n min/n max, Modo Mask, Mask k/Mask Fit, IC1-6 Min/Max, Azar %
	// Mask), only drawn while Flt is on (filtOpen, computed above alongside GLOBAL_W). The raw
	// 12-bit pitch-class mask stays fs2setpick.js's piano-UI territory (a click-grid, not a knob).
	// Vector IC WAS left out of the original round (comment used to call it "composition-time, not
	// a live-performance knob") but the plan's Ola 5 overturns that: it is the one filter condition
	// Mask Fit cannot route around (the vector is transposition-invariant), so it belongs here.
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
		// Rows 3-8 -- IC1-6 Min|Max, side by side like n min/n max at row 0. A Min above its own Max
		// lets nothing through (the engine still just warns on the console instead of freezing the
		// sequence, see setvecmin/setvecmax's own comment) -- the plan calls this an alarm case, not
		// a dim case: it is actively lying about what will pass, not merely inert.
		var vdcw = (g4w - 2) / 2;
		var VEC_ROWS = [
			['vmin1', 'vmax1', 'vecMin1', 'vecMax1', 1], ['vmin2', 'vmax2', 'vecMin2', 'vecMax2', 2],
			['vmin3', 'vmax3', 'vecMin3', 'vecMax3', 3], ['vmin4', 'vmax4', 'vecMin4', 'vecMax4', 4],
			['vmin5', 'vmax5', 'vecMin5', 'vecMax5', 5], ['vmin6', 'vmax6', 'vecMin6', 'vecMax6', 6]
		];
		for (var vr = 0; vr < VEC_ROWS.length; vr++) {
			var vrow = VEC_ROWS[vr], vrowN = 3 + vr;
			if (!gFits(vrowN)) continue;
			var vAlarm = globalState[vrow[2]] > globalState[vrow[3]];
			globalChipGeo[vrow[0]] = { x: g4x, y: gRow(vrowN), w: vdcw, h: gChipH };
			globalChipGeo[vrow[1]] = { x: g4x + vdcw + 2, y: gRow(vrowN), w: vdcw, h: gChipH };
			drawChip(globalChipGeo[vrow[0]], 'i' + vrow[4] + 'n' + globalState[vrow[2]], false, false, undefined, vAlarm);
			drawChip(globalChipGeo[vrow[1]], 'i' + vrow[4] + 'x' + globalState[vrow[3]], false, false, undefined, vAlarm);
		}
		// Row 9 -- Azar % Mask (drag value) + its action button, the two panel widgets from the
		// plan's Ola 5 list. randomizemask() needs the Live API (rule 8) and posts to the console
		// instead of doing anything outside Live; the button here can't know that in advance.
		if (gFits(9)) {
			globalChipGeo.randmaskpct = { x: g4x, y: gRow(9), w: g4w, h: gChipH };
			drawChip(globalChipGeo.randmaskpct, 'Az%' + globalState.randMaskPct, false);
		}
		if (gFits(10)) {
			globalChipGeo.randmask = { x: g4x, y: gRow(10), w: g4w, h: gChipH };
			drawChip(globalChipGeo.randmask, 'Azar Mask', false);
		}
	}   // else: globalChipGeo.nmin/nmax/maskmode/maskk/maskfit/vmin*/vmax*/randmaskpct/randmask
		// simply stay unset (fresh {} above)

	// Column 5 -- Groove (Swing/Human, Rasg+Dir Rasg, Rat N+Rat A, Prob Rat+Caida), drawn while
	// grooveOpen (see its definition up top for why the gate is an OR of two different conditions).
	// Sub y Modo Toque, sus dos gates, NO viven aca sino en col 1: una columna no puede contener el
	// control que decide si existe. Nada se oculta dentro de la columna -- se ATENUA -- porque cada
	// una de estas es candidata a "la moví y no pasó nada": el usuario tiene que poder ver el valor
	// que puso y que esta ahi sin efecto, no que el control desaparecio.
	if (grooveOpen) {
		// Swing y Human no necesitan gate propio: su unica condicion es subDiv >= 2 y esa ya es la
		// de la columna entera, asi que si se ven, andan.
		if (gFits(0)) {
			globalChipGeo.swing = { x: g5x, y: gRow(0), w: g5w, h: gChipH };
			drawChip(globalChipGeo.swing, 'Sw ' + globalState.swing, false);
		}
		if (gFits(1)) {
			globalChipGeo.human = { x: g5x, y: gRow(1), w: g5w, h: gChipH };
			drawChip(globalChipGeo.human, 'Hu ' + globalState.human, false);
		}
		// Rasg + Dir Rasg: el unico par de la columna con un gate PROPIO, el acorde (strumOffset
		// devuelve 0 con n < 2), asi que se atenuan en Arpegio. Dir Rasg ademas no hace nada con
		// Rasg en 0. Atenuados, nunca ocultos: son justo los candidatos a "la movi y no paso nada".
		if (gFits(2)) {
			var rdcw = (g5w - 2) / 2;
			globalChipGeo.rasg = { x: g5x, y: gRow(2), w: rdcw, h: gChipH };
			globalChipGeo.dirrasg = { x: g5x + rdcw + 2, y: gRow(2), w: rdcw, h: gChipH };
			drawChip(globalChipGeo.rasg, 'R' + globalState.rasg, false, !chordLive);
			drawChip(globalChipGeo.dirrasg, DIR_RASG_ABBR[Math.round(globalState.dirRasg)] || '?', false,
				!chordLive || Math.round(globalState.rasg) <= 0);
		}
		// Rat N / Rat A: su otra condicion en scheduleBurst() (`subDiv < 2`) tambien es la de la
		// columna, asi que aca mandan ellas solas.
		if (gFits(3)) {
			var ndcw2 = (g5w - 2) / 2;
			globalChipGeo.ratn = { x: g5x, y: gRow(3), w: ndcw2, h: gChipH };
			globalChipGeo.rata = { x: g5x + ndcw2 + 2, y: gRow(3), w: ndcw2, h: gChipH };
			drawChip(globalChipGeo.ratn, 'N' + globalState.ratN, false);
			drawChip(globalChipGeo.rata, 'A' + globalState.ratA, false);
		}
		// Prob Rat y Caida necesitan que ALGUN grupo tenga ratchet: con Rat N y Rat A los dos en 1
		// no hay rafaga sobre la cual aplicar ni probabilidad ni caida.
		if (gFits(4)) {
			var ratOn = Math.round(globalState.ratN) > 1 || Math.round(globalState.ratA) > 1;
			var pdcw = (g5w - 2) / 2;
			globalChipGeo.ratprob = { x: g5x, y: gRow(4), w: pdcw, h: gChipH };
			globalChipGeo.ratcaida = { x: g5x + pdcw + 2, y: gRow(4), w: pdcw, h: gChipH };
			drawChip(globalChipGeo.ratprob, 'P' + globalState.ratProb, false, !ratOn);
			drawChip(globalChipGeo.ratcaida, 'C' + globalState.ratCaida, false, !ratOn);
		}
	}   // else: globalChipGeo.swing/human/rasg/dirrasg/ratn/rata/ratprob/ratcaida stay unset

	// Column 6 -- Acentos (Ciclo+Tie, Euclid+Pulsos+Giro, VelMin/VelMax/Figura x Normal/Acento).
	// No gate propio (accOpen is always true, see its definition up top) -- always drawn, FIXED
	// rows 0-5 like col 1/2. Ciclo dimmed while Tie is on (its value is ignored, see
	// articulationFor()); Pulsos/Giro HIDDEN (not just dimmed) while Euclid is off -- they carry no
	// reading at all then, same treatment as col 3/4's mutually-exclusive sub-rows.
	if (gFits(0)) {
		var cdcw = (g6w - 2) / 2;
		globalChipGeo.ciclo = { x: g6x, y: gRow(0), w: cdcw, h: gChipH };
		globalChipGeo.tie = { x: g6x + cdcw + 2, y: gRow(0), w: cdcw, h: gChipH };
		drawChip(globalChipGeo.ciclo, 'C' + globalState.accCiclo, false, !!globalState.accTie);
		drawChip(globalChipGeo.tie, 'Tie', !!globalState.accTie);
	}
	if (gFits(1)) {
		globalChipGeo.euc = { x: g6x, y: gRow(1), w: g6w, h: gChipH };
		drawChip(globalChipGeo.euc, 'Euclid', !!globalState.euclidOn);
	}
	if (globalState.euclidOn && gFits(2)) {
		var edcw = (g6w - 2) / 2;
		globalChipGeo.eupuls = { x: g6x, y: gRow(2), w: edcw, h: gChipH };
		globalChipGeo.eugir = { x: g6x + edcw + 2, y: gRow(2), w: edcw, h: gChipH };
		drawChip(globalChipGeo.eupuls, 'Pl' + globalState.euclidK, false);
		drawChip(globalChipGeo.eugir, 'Gi' + globalState.euclidRot, false);
	}
	if (gFits(3)) {
		var vndcw = (g6w - 2) / 2;
		globalChipGeo.velminn = { x: g6x, y: gRow(3), w: vndcw, h: gChipH };
		globalChipGeo.velmina = { x: g6x + vndcw + 2, y: gRow(3), w: vndcw, h: gChipH };
		drawChip(globalChipGeo.velminn, 'Vn' + globalState.velMinN, false);
		drawChip(globalChipGeo.velmina, 'Va' + globalState.velMinA, false);
	}
	if (gFits(4)) {
		var vxdcw = (g6w - 2) / 2;
		globalChipGeo.velmaxn = { x: g6x, y: gRow(4), w: vxdcw, h: gChipH };
		globalChipGeo.velmaxa = { x: g6x + vxdcw + 2, y: gRow(4), w: vxdcw, h: gChipH };
		drawChip(globalChipGeo.velmaxn, 'Xn' + globalState.velMaxN, false);
		drawChip(globalChipGeo.velmaxa, 'Xa' + globalState.velMaxA, false);
	}
	if (gFits(5)) {
		var fdcw = (g6w - 2) / 2;
		globalChipGeo.fign = { x: g6x, y: gRow(5), w: fdcw, h: gChipH };
		globalChipGeo.figa = { x: g6x + fdcw + 2, y: gRow(5), w: fdcw, h: gChipH };
		drawChip(globalChipGeo.fign, 'Fn' + globalState.figN, false);
		drawChip(globalChipGeo.figa, 'Fa' + globalState.figA, false);
	}

	// Column 7 -- Camino armonico (Tension+Curva+Modelo, Prog Favoritos+Solo Fav+Fav+Limpiar favs).
	// No gate propio (caminoOpen is always true, see its definition up top) -- always drawn, FIXED
	// rows 0-5 like col 1/2/6. This is the column where dimming is the whole point of the ola (see
	// plan): a control that LOOKS live but currently has no effect on advanceSet()'s outcome.
	if (gFits(0)) {
		globalChipGeo.tension = { x: g7x, y: gRow(0), w: g7w, h: gChipH };
		// Alarm (not dim) when the fav-progression trap is live: Prog Favoritos on with an empty
		// list falls through to advanceInOrder() silently, so Tension LOOKS inert for no visible
		// reason unless this chip itself says so.
		drawChip(globalChipGeo.tension, 'Tn ' + globalState.tension, false, favSeqActive, undefined, favSeqTrap);
	}
	if (gFits(1)) {
		globalChipGeo.curva = { x: g7x, y: gRow(1), w: g7w, h: gChipH };
		var gCurvaOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gcurva';
		// tensionAt() (inside advanceByTension()) is the only reader of tensShape -- dead at
		// Tension 0 regardless of Prog Favoritos, same as favSeqActive/Trap dim it for the same reason.
		drawChip(globalChipGeo.curva, CURVA_NAMES[Math.round(globalState.curva)] || '?', gCurvaOpen,
			favSeqActive || favSeqTrap || Math.round(globalState.tension) === 0);
		if (gCurvaOpen) pendingMenu = { v: -1, kind: 'gcurva', anchor: globalChipGeo.curva, items: CURVA_NAMES, cur: Math.round(globalState.curva) };
	}
	if (gFits(2)) {
		globalChipGeo.tensmodel = { x: g7x, y: gRow(2), w: g7w, h: gChipH };
		var gTensModelOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'gtensmodel';
		// Modelo does NOT dim with Tension at 0 -- settensmodel() always calls requestFilter() and
		// moves consLow/consHigh/Orden's own consonance ordering regardless of the curve being live.
		drawChip(globalChipGeo.tensmodel, TENSMODEL_NAMES[Math.round(globalState.tensmodel)] || '?', gTensModelOpen, favSeqActive || favSeqTrap);
		if (gTensModelOpen) pendingMenu = { v: -1, kind: 'gtensmodel', anchor: globalChipGeo.tensmodel, items: TENSMODEL_NAMES, cur: Math.round(globalState.tensmodel) };
	}
	if (gFits(3)) {
		var pfdcw = (g7w - 2) / 2;
		globalChipGeo.progfav = { x: g7x, y: gRow(3), w: pfdcw, h: gChipH };
		globalChipGeo.favonly = { x: g7x + pfdcw + 2, y: gRow(3), w: pfdcw, h: gChipH };
		// Alarm on the Prog Favoritos chip itself -- the trap is about THIS control looking on and
		// harmless while quietly killing Tension/Curva/Enlace next to it.
		drawChip(globalChipGeo.progfav, 'Fav Sq', !!globalState.progfav, false, undefined, favSeqTrap);
		drawChip(globalChipGeo.favonly, 'S.Fav', !!globalState.favonly);
	}
	if (gFits(4)) {
		globalChipGeo.fav = { x: g7x, y: gRow(4), w: g7w, h: gChipH };
		drawChip(globalChipGeo.fav, 'Fav', !!globalState.fav);
	}
	if (gFits(5)) {
		globalChipGeo.clearfavs = { x: g7x, y: gRow(5), w: g7w, h: gChipH };
		// Accion, no estado -- nunca "on" (rule 8), pero se apaga sola si no hay nada que limpiar.
		drawChip(globalChipGeo.clearfavs, 'Lim favs', false, globalState.favSeqLen === 0);
	}

	// Column 8 -- Modulacion (Ola 6), FIXED rows 0-3, one row per modulator -- the matrix the plan
	// asks for instead of 20 loose chips (see the file-header comment for the full rationale).
	// ROWTAG_W reserves a sliver on the left for the "M<k>" row label (plain text, not a clickable
	// chip); the rest splits into 5 narrow cells left to right -- Forma (dropdown) / Ciclo / Prof /
	// Fase (drag-scrub) / Dest (dropdown), same argument order setmodshape/setmodcycle/setmoddepth/
	// setmodphase/setmoddest take. Cells are prefixed the same way every other narrow numeric chip in
	// this sidebar already is ("n"+cardMin, "k"+maskK, "i1n"+val) instead of a separate field-header
	// row, which would not fit above only 4 rows.
	if (modOpen) {
		var ROWTAG_W = 12;
		var mCellW = (g8w - ROWTAG_W - 4) / 5;   // 4 = the four 1px gaps between 5 cells
		var MOD_ROWS = [
			['mod1shape', 'mod1cycle', 'mod1depth', 'mod1phase', 'mod1dest', 1],
			['mod2shape', 'mod2cycle', 'mod2depth', 'mod2phase', 'mod2dest', 2],
			['mod3shape', 'mod3cycle', 'mod3depth', 'mod3phase', 'mod3dest', 3],
			['mod4shape', 'mod4cycle', 'mod4depth', 'mod4phase', 'mod4dest', 4]
		];
		for (var mr = 0; mr < MOD_ROWS.length; mr++) {
			if (!gFits(mr)) continue;
			var mRow = MOD_ROWS[mr];
			var fShape = mRow[0], fCycle = mRow[1], fDepth = mRow[2], fPhase = mRow[3], fDest = mRow[4], mk = mRow[5];
			var shapeV = globalState[fShape], cycleV = globalState[fCycle], depthV = globalState[fDepth],
				phaseV = globalState[fPhase], destV = globalState[fDest];
			var my = gRow(mr);
			mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
			mgraphics.set_font_size(8);
			mgraphics.move_to(g8x, my + gChipH - 5);
			mgraphics.show_text('M' + mk);

			// Toda la fila se apaga cuando plainly no hace nada: sin destino, o Prof 0 (modStep()'s
			// own `if (!dest || !modDepth[k]) continue`). Dos trampas mas angostas encima de esa:
			// Grado solo se lee en Arpegio (degreeAt() nunca corre en Acordes), y Swing/Rasgueo/
			// Ratchet necesitan Sub >= 2, la misma condicion que apaga la columna Groove (col 5).
			var rowDead = destV === 0 || depthV === 0;
			var destDegMoot = destV === MOD_DEST_GRADO && Math.round(globalState.mode) === MODE_CHORDS;
			var destRitmoMoot = (destV === MOD_DEST_SWING || destV === MOD_DEST_STRUM || destV === MOD_DEST_RATCHET) &&
				Math.round(globalState.sub) < 2;
			var mDim = (rowDead || destDegMoot || destRitmoMoot) ? 0.4 : 1.0;

			var cx = g8x + ROWTAG_W;
			globalChipGeo[fShape] = { x: cx, y: my, w: mCellW, h: gChipH };
			var mShapeOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'g' + fShape;
			drawChip(globalChipGeo[fShape], MOD_SHAPE_ABBR[Math.round(shapeV)] || '?', mShapeOpen, false, mDim);
			if (mShapeOpen) pendingMenu = { v: -1, kind: 'g' + fShape, anchor: globalChipGeo[fShape], items: MOD_SHAPE_NAMES, cur: Math.round(shapeV) };
			cx += mCellW + 1;

			globalChipGeo[fCycle] = { x: cx, y: my, w: mCellW, h: gChipH };
			drawChip(globalChipGeo[fCycle], 'C' + cycleV, false, false, mDim);
			cx += mCellW + 1;

			globalChipGeo[fDepth] = { x: cx, y: my, w: mCellW, h: gChipH };
			drawChip(globalChipGeo[fDepth], 'P' + depthV, false, false, mDim);
			cx += mCellW + 1;

			globalChipGeo[fPhase] = { x: cx, y: my, w: mCellW, h: gChipH };
			drawChip(globalChipGeo[fPhase], 'F' + phaseV, false, false, mDim);
			cx += mCellW + 1;

			globalChipGeo[fDest] = { x: cx, y: my, w: mCellW, h: gChipH };
			var mDestOpen = openMenu && openMenu.v === -1 && openMenu.kind === 'g' + fDest;
			drawChip(globalChipGeo[fDest], MOD_DEST_ABBR[Math.round(destV)] || '?', mDestOpen, false, mDim);
			if (mDestOpen) pendingMenu = { v: -1, kind: 'g' + fDest, anchor: globalChipGeo[fDest], items: MOD_DEST_NAMES, cur: Math.round(destV) };
		}
	}

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

	// --- the accent-cycle strip: read-only view of accentGrid (Ola 2) -- when Euclid is on this IS
	// the algorithm's output, not something to click here (see plan's show/hide rule); a clickable
	// version is a later ola. Only the leading accCiclo (or accTie's card-length equivalent, but the
	// engine already resolves that into accentGridUI before emitting -- see forteseq2.js's own
	// articulationFor() for the same accentTieToN branch) cells are lit, the rest dimmed as unused.
	var ay = headH + gridH + shapeH + ornH;
	mgraphics.set_source_rgba([0.09, 0.09, 0.10, 1]);
	mgraphics.rectangle(0, ay, W, accGridH);
	mgraphics.fill();
	mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
	mgraphics.set_font_size(8);
	mgraphics.move_to(4, ay + accGridH - 5);
	mgraphics.show_text('acentos');
	var acx = 48, acw = Math.max(4, Math.min(28, (W - acx - 8) / ACCENT_MAX_UI));
	for (var ai = 0; ai < ACCENT_MAX_UI; ai++) {
		var inCycle = ai < Math.round(globalState.accCiclo);
		var on = !!accentGridUI[ai];
		if (on) {
			mgraphics.set_source_rgba(inCycle ? [0.85, 0.55, 0.15, 1] : [0.85, 0.55, 0.15, 0.35]);
		} else {
			mgraphics.set_source_rgba(inCycle ? [0.3, 0.3, 0.33, 1] : [0.3, 0.3, 0.33, 0.35]);
		}
		mgraphics.rectangle(acx + ai * acw + 1, ay + 3, acw - 2, accGridH - 6);
		mgraphics.fill();
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
