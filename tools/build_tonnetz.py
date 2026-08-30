"""Build forteseq/tonnetz.amxd -- the shell around tonnetz.js (the Tonnetz jsui) and
pcsetinfo.js (the set-class analyser).

    python tools/build_tonnetz.py            dry run, writes nothing
    python tools/build_tonnetz.py --apply    do it

Same method as tools/build_midibounce.py: the maxmsp MCP server is not reachable, so the
.amxd is assembled by copying a known-good MIDI-effect device
(forteseq/forteseqmidifilter.amxd) and rewriting boxes / lines / parameters /
dependency_cache. Copying the template's bytes keeps the binary AMPF/meta chunk that marks
the file as a MIDI effect ('midf') and the whole `project` block.

LAYOUT (v6). The Live device panel is nearly empty: a single "Tonnetz" button. The big
jsui, every control and the analyser live in an inline subpatcher `[p tonnetz_window]` that
opens as its OWN floating window (outside the rack) via `[pcontrol]`; `live.thisdevice`
opens it on load. The subpatcher opens in PATCHING view (not presentation) so tonnetz.js's
fitToWindow() -- which sets its own box rect from `this.patcher.wind.size` -- actually
resizes the canvas as the window is dragged. A 5-row control strip sits at the top; the
jsui fills the rest and draws eight panels -- Tonnetz, chromatic circle, fifths circle,
voice-leading space, piano keyboard, guitar fretboard, diatonic Tonnetz, and Gollin's 3-D
Tonnetz (4-note chords as tetrahedra, isometric projection). Each has its own on/off toggle
in row 1 (pick panels a dedo); whatever is on is packed into an auto-grid whose short last
row is centred at the common cell width. Row 6 is a study mode: dial in a Forte class +
rotation + tonic and the set is shown on every panel with the MIDI frozen out.

    top patcher:
      notein --> pack (pitch vel) --> [p tonnetz_window] inlet 0
      midiin --> midiout                                   MIDI pass-through
      live.text "Tonnetz" --\
      live.thisdevice -------+-- open --> pcontrol --> [p tonnetz_window] inlet 0

    inside [p tonnetz_window]:
      inlet --> prepend note --> jsui tonnetz.js
                             |--> js pcsetinfo.js  --0--> jsui  (`info` / `setclass`)
                             |                     --1--> send ---tonnetzinfo
                             \--> js tonnetzfit.js --0--> jsui  (`bestfit <a b c>`)
                                                   --1--> send ---tonnetzfit
      live.toggle Vw* (8)  --> prepend v{ton,chr,fif,voc,pno,gtr,dia,tet} --> jsui  (panel on/off)
      live.menu "Key" + live.tab "KeyMode" --> prepend keyroot/keymode --> jsui  (diatonic panel)
      live.menu "Preset" / "TetPreset" --> prepend preset / tetpreset --> jsui
      live.numbox A/B/C    <-> pak 3 4 5 / prepend abc <-> jsui   (Preset <-> a/b/c stay in sync
                               via jsui outlet 0: `abc a b c` -> numboxes, `presetsel i` -> menu)
      live.numbox Radius/TraceLen --> prepend radius / tracelen --> jsui
      live.toggle Trace/Harmonize/Faces/Labels/ChordPoly/TracePath/Colors/RegTrace --> prepend <sel> --> jsui
      live.tab PianoMode/GuitarMode + live.menu Tuning + live.numbox Frets/Zoom/Pan --> prepend <sel> --> jsui
      live.toggle Plr/XfPrev/AutoFit + live.tab XfMode + live.numbox Xpose/InvC --> prepend <sel> --> jsui
      live.toggle Study --> t b i i --> prepend studymode --> jsui  (freeze MIDI)
                                    \-> gate ctrl, \-> bang the study pak
      StudyCard/Idx/Rot/Tonic/Inv --> pak --> prepend studyset --> [gate] --> js pcsetinfo.js
                                    (pcsetinfo builds the set, sends it back as `list` --> jsui)
      loadbang --> bang the bang-safe controls; outputvalue the toggles (a bang inverts them)

44 parameters. The button is a top-level param (key "obj-20"); the 43 controls inside the
subpatcher are registered on the TOP patcher with "obj-10::<innerid>" keys AND in the
subpatcher's own local `parameters` block -- the nesting scheme FORTESEQ2 uses for its
fs2voice/fs2pages bpatchers. See the amxd-parameter-registries note. Seven Push banks (8 + 8 + 8 + 8 + 4 + 2 + 6).

Close the device in BOTH Max and Live before running with --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'forteseq', 'forteseqmidifilter.amxd')
DEVICE = os.path.join(ROOT, 'forteseq', 'tonnetz.amxd')
JS = 'tonnetz.js'
JS_INFO = 'pcsetinfo.js'
JS_FIT = 'tonnetzfit.js'
BOOT = 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq'
SUB = 'obj-10'                      # box id of the [p tonnetz_window] subpatcher

# seven panels, each an on/off toggle (VwTonnetz..VwDiat); no single "view" selector anymore
# must match PRESETS[] in tonnetz.js
PRESETS = ['3 4 5  classic', '1 1 10  chromatic', '2 2 8  whole-tone', '1 4 7', '2 3 7',
           '1 2 9', '3 3 6', '4 4 4  augmented', '1 5 6', '2 5 5']
# must match TET_PRESETS[] in tonnetz.js -- the 3-D (Gollin) Tonnetz 4-note chord classes
TET_PRESET_NAMES = ['dom7 / hd7', 'm7', 'maj7', 'dim7', 'mM7', 'aug7']
# must match TUNINGS[] in tonnetz.js
GUITAR_TUNINGS = ['Estandar', 'Drop D', 'DADGAD', 'Bajo 4', 'Bajo 5', 'Ukelele']

ANN = {
    'Abrir': 'Abre / trae al frente la ventana del Tonnetz (flota fuera del rack).',
    'VwTonnetz': 'Muestra u oculta el panel del Tonnetz cromatico generalizado.',
    'VwChrom': 'Muestra u oculta el circulo cromatico.',
    'VwFifths': 'Muestra u oculta el circulo de quintas.',
    'VwVoice': 'Muestra u oculta el espacio de conduccion de voces (las 12 tricordes).',
    'VwPiano': 'Muestra u oculta el teclado de piano.',
    'VwGuitar': 'Muestra u oculta el mastil de guitarra.',
    'VwDiat': 'Muestra u oculta el Tonnetz diatonico (solo las 7 notas de la tonalidad Key).',
    'VwTet': 'Muestra u oculta el Tonnetz 3D de Gollin: acordes de 4 notas (7as) como tetraedros en proyeccion isometrica plana.',
    'TetPreset': 'Clase de acorde de 4 notas del Tonnetz 3D: 7a de dominante/semidism, menor 7, mayor 7, dism 7, menor-mayor 7 o 7 aumentada. Define los ejes del complejo K[a,b,c,d].',
    'Key': 'Tonica del Tonnetz diatonico.',
    'KeyMode': 'Escala del Tonnetz diatonico: Mayor o menor natural.',
    'Preset': 'Vector de clases de intervalo [a,b,c] de las aristas del triangulo. 3 4 5 = Tonnetz clasico. Mover A/B/C lo sobrescribe.',
    'TonA': 'a: paso del eje x de la reticula, en semitonos.',
    'TonB': 'b: la arista diagonal; el eje y avanza a+b semitonos.',
    'TonC': 'c: la tercera arista (implicita, a+b+c = 12). Solo informativa.',
    'Radius': 'Separacion de la reticula en pixeles (zoom del Tonnetz).',
    'Trace': 'Deja encendidas las notas soltadas recientemente.',
    'TraceLen': 'Cuantos ataques recuerda el rastro.',
    'Harmonize': 'Enciende los vecinos de reticula de las notas que suenan (solo Tonnetz).',
    'Faces': 'Rellena un triangulo del Tonnetz cuando suenan sus tres notas.',
    'Labels': 'Nombres de nota (activado) o numeros de clase de altura (desactivado).',
    'Colors': 'Colorea por nota (rueda de quintas, tipo sidebrain) vs azul uniforme.',
    'ChordPoly': 'Une las notas que suenan en un poligono sobre los circulos (aum = triangulo, dism7 = cuadrado).',
    'TracePath': 'Dibuja el rastro como un camino cronologico con desvanecido sobre los circulos.',
    'PianoMode': 'Piano: Octava = una sola octava por clase de altura. Completo = todo el rango MIDI 0-127, nota por nota.',
    'GuitarMode': 'Guitarra: Repetidas = todas las posiciones del mastil de cada nota que suena. Suena = solo la altura exacta.',
    'Tuning': 'Afinacion de la guitarra (cuerdas al aire).',
    'Frets': 'Numero de trastes de la guitarra (12-24).',
    'Zoom': 'Zoom horizontal del piano y la guitarra (1-8x).',
    'Pan': 'Desplazamiento horizontal del piano / guitarra cuando el zoom excede el panel (0-1).',
    'Plr': 'Flechas P (paralela), L (tono de sensible) y R (relativa) desde la triada mayor/menor que suena a sus tres triangulos vecinos (solo Tonnetz).',
    'XfPrev': 'Previsualiza una transformacion dibujando el acorde resultante como aros fantasma magenta. NO cambia el MIDI.',
    'XfMode': 'Modo de la previsualizacion: Transponer (sube Xpose semitonos) o Invertir (refleja alrededor de la clase de altura InvC).',
    'Xpose': 'Semitonos de transposicion para la previsualizacion (0-11).',
    'InvC': 'Centro de inversion (clase de altura 0-11) para la previsualizacion.',
    'RegTrace': 'Dibuja la trayectoria como un camino de regiones (triangulos/aristas) en el Tonnetz, desvanecido por edad.',
    'AutoFit': 'Deja que el analisis de complejo mas compacto (tonnetzfit.js) fije el vector a/b/c en vivo.',
    'Study': 'Modo estudio: muestra el conjunto elegido con Forte/rotacion/tonica e IGNORA el MIDI entrante. Apagarlo vuelve al MIDI.',
    'StudyCard': 'Cardinalidad del conjunto a estudiar (2-9 notas).',
    'StudyIdx': 'Que clase de conjunto de esa cardinalidad, en orden de Forte (1..N, se recorta al maximo disponible).',
    'StudyRot': 'Rota el collar de intervalos: 0 = forma prima; cada paso arranca en la nota siguiente (los modos de la forma).',
    'StudyTonic': 'Nota a la que se ancla el conjunto (transposicion).',
    'StudyInv': 'Usa la inversion de la forma en vez de la forma prima.',
}

# (longname, shortname, innerid, maxclass, prepend-selector or None)
CTRL = [
    ('VwTonnetz',  'VwTon',     'obj-120', 'live.toggle',  'vton'),
    ('VwChrom',    'VwChr',     'obj-121', 'live.toggle',  'vchr'),
    ('VwFifths',   'VwFif',     'obj-122', 'live.toggle',  'vfif'),
    ('VwVoice',    'VwVoc',     'obj-123', 'live.toggle',  'vvoc'),
    ('VwPiano',    'VwPno',     'obj-124', 'live.toggle',  'vpno'),
    ('VwGuitar',   'VwGtr',     'obj-125', 'live.toggle',  'vgtr'),
    ('VwDiat',     'VwDia',     'obj-126', 'live.toggle',  'vdia'),
    ('VwTet',      'VwTet',     'obj-127', 'live.toggle',  'vtet'),
    ('Key',        'Key',       'obj-128', 'live.menu',    'keyroot'),
    ('KeyMode',    'KeyMode',   'obj-129', 'live.tab',     'keymode'),
    ('Preset',     'Preset',    'obj-130', 'live.menu',    'preset'),
    ('TetPreset',  'TetPre',    'obj-131', 'live.menu',    'tetpreset'),
    ('TonA',       'TonA',      'obj-140', 'live.numbox',  None),
    ('TonB',       'TonB',      'obj-141', 'live.numbox',  None),
    ('TonC',       'TonC',      'obj-142', 'live.numbox',  None),
    ('Radius',     'Radius',    'obj-150', 'live.numbox',  'radius'),
    ('Trace',      'Trace',     'obj-160', 'live.toggle',  'trace'),
    ('TraceLen',   'TraceLen',  'obj-162', 'live.numbox',  'tracelen'),
    ('Harmonize',  'Harmonize', 'obj-170', 'live.toggle',  'harm'),
    ('Faces',      'Faces',     'obj-180', 'live.toggle',  'faces'),
    ('Labels',     'Labels',    'obj-190', 'live.toggle',  'labels'),
    ('ChordPoly',  'ChordPoly', 'obj-210', 'live.toggle',  'chordpoly'),
    ('TracePath',  'TracePath', 'obj-212', 'live.toggle',  'tracepath'),
    ('Colors',     'Colors',    'obj-214', 'live.toggle',  'colors'),
    ('PianoMode',  'PianoMode', 'obj-240', 'live.tab',     'pianomode'),
    ('GuitarMode', 'GuitarMd',  'obj-242', 'live.tab',     'guitarmode'),
    ('Tuning',     'Tuning',    'obj-244', 'live.menu',    'tuning'),
    ('Frets',      'Frets',     'obj-246', 'live.numbox',  'frets'),
    ('Zoom',       'Zoom',      'obj-248', 'live.numbox',  'zoom'),
    ('Pan',        'Pan',       'obj-250', 'live.numbox',  'pan'),
    ('Plr',        'Plr',       'obj-260', 'live.toggle',  'plr'),
    ('XfPrev',     'XfPrev',    'obj-262', 'live.toggle',  'xfprev'),
    ('XfMode',     'XfMode',    'obj-264', 'live.tab',     'xfmode'),
    ('Xpose',      'Xpose',     'obj-266', 'live.numbox',  'xpose'),
    ('InvC',       'InvC',      'obj-268', 'live.numbox',  'invc'),
    ('RegTrace',   'RegTrace',  'obj-270', 'live.toggle',  'regtrace'),
    ('AutoFit',    'AutoFit',   'obj-272', 'live.toggle',  'autofit'),
    ('Study',      'Study',     'obj-300', 'live.toggle',  None),   # wired by hand (studymode + gate + pak)
    ('StudyCard',  'StudyCard', 'obj-301', 'live.numbox',  None),
    ('StudyIdx',   'StudyIdx',  'obj-302', 'live.numbox',  None),
    ('StudyRot',   'StudyRot',  'obj-303', 'live.numbox',  None),
    ('StudyTonic', 'StudyTon',  'obj-304', 'live.menu',    None),
    ('StudyInv',   'StudyInv',  'obj-305', 'live.toggle',  None),
]
TOGGLES = ['VwTonnetz', 'VwChrom', 'VwFifths', 'VwVoice', 'VwPiano', 'VwGuitar', 'VwDiat', 'VwTet',
           'Trace', 'Harmonize', 'Faces', 'Labels', 'ChordPoly', 'TracePath', 'Colors',
           'Plr', 'XfPrev', 'RegTrace', 'AutoFit', 'Study', 'StudyInv']
BANG_SAFE = ['obj-128', 'obj-129', 'obj-130', 'obj-131', 'obj-140', 'obj-141', 'obj-142', 'obj-150',
             'obj-162', 'obj-240', 'obj-242', 'obj-244', 'obj-246', 'obj-248', 'obj-250',
             'obj-264', 'obj-266', 'obj-268']

BANKS = [
    ('Vistas',    ['VwTonnetz', 'VwChrom', 'VwFifths', 'VwVoice', 'VwPiano', 'VwGuitar', 'VwDiat', 'VwTet']),
    ('Tonnetz',   ['Preset', 'TonA', 'TonB', 'TonC', 'Radius', 'Key', 'KeyMode', 'Harmonize']),
    ('Rastro',    ['Trace', 'TraceLen', 'RegTrace', 'Faces', 'Labels', 'ChordPoly', 'TracePath', 'Colors']),
    ('Transform', ['XfPrev', 'XfMode', 'Xpose', 'InvC', 'Plr', 'AutoFit', 'PianoMode', 'GuitarMode']),
    ('Piano/Guit', ['Tuning', 'Frets', 'Zoom', 'Pan']),
    ('Mas',       ['Abrir', 'TetPreset']),
    ('Estudio',   ['Study', 'StudyCard', 'StudyIdx', 'StudyRot', 'StudyTonic', 'StudyInv']),
]


def enum_vo(longname, shortname, enum, initial):
    return {
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_type': 2, 'parameter_enum': enum, 'parameter_mmax': len(enum) - 1,
        'parameter_modmode': 0, 'parameter_unitstyle': 9,
        'parameter_initial_enable': 1, 'parameter_initial': [initial],
    }


def num_vo(longname, shortname, mmin, mmax, initial):
    return {
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_type': 0, 'parameter_mmin': float(mmin), 'parameter_mmax': float(mmax),
        'parameter_modmode': 0, 'parameter_unitstyle': 0,
        'parameter_initial_enable': 1, 'parameter_initial': [float(initial)],
    }


def toggle_vo(longname, initial):
    return enum_vo(longname, longname, ['off', 'on'], initial)


VO = {
    'Abrir':     enum_vo('Abrir', 'Abrir', ['off', 'on'], 0),
    'VwTonnetz': toggle_vo('VwTonnetz', 1),
    'VwChrom':   toggle_vo('VwChrom', 1),
    'VwFifths':  toggle_vo('VwFifths', 1),
    'VwVoice':   toggle_vo('VwVoice', 0),
    'VwPiano':   toggle_vo('VwPiano', 0),
    'VwGuitar':  toggle_vo('VwGuitar', 0),
    'VwDiat':    toggle_vo('VwDiat', 0),
    'VwTet':     toggle_vo('VwTet', 0),
    'TetPreset': enum_vo('TetPreset', 'TetPre', TET_PRESET_NAMES, 0),
    'Key':       enum_vo('Key', 'Key',
                         ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'], 0),
    'KeyMode':   enum_vo('KeyMode', 'KeyMode', ['Mayor', 'Menor'], 0),
    'Preset':    enum_vo('Preset', 'Preset', PRESETS, 0),
    'TonA':      num_vo('TonA', 'TonA', 1, 11, 3),
    'TonB':      num_vo('TonB', 'TonB', 1, 11, 4),
    'TonC':      num_vo('TonC', 'TonC', 1, 11, 5),
    'Radius':    num_vo('Radius', 'Radius', 24, 120, 46),
    'Trace':     toggle_vo('Trace', 1),
    'TraceLen':  num_vo('TraceLen', 'TraceLen', 1, 24, 8),
    'Harmonize': toggle_vo('Harmonize', 1),
    'Faces':     toggle_vo('Faces', 1),
    'Labels':    toggle_vo('Labels', 1),
    'ChordPoly': toggle_vo('ChordPoly', 1),
    'TracePath': toggle_vo('TracePath', 0),
    'Colors':    toggle_vo('Colors', 1),
    'PianoMode': enum_vo('PianoMode', 'PianoMode', ['Octava', 'Completo'], 0),
    'GuitarMode':enum_vo('GuitarMode', 'GuitarMd', ['Repetidas', 'Suena'], 0),
    'Tuning':    enum_vo('Tuning', 'Tuning', GUITAR_TUNINGS, 0),
    'Frets':     num_vo('Frets', 'Frets', 12, 24, 22),
    'Zoom':      num_vo('Zoom', 'Zoom', 1, 8, 1),
    'Pan':       num_vo('Pan', 'Pan', 0, 1, 0.5),
    'Plr':       toggle_vo('Plr', 0),
    'XfPrev':    toggle_vo('XfPrev', 0),
    'XfMode':    enum_vo('XfMode', 'XfMode', ['Transponer', 'Invertir'], 0),
    'Xpose':     num_vo('Xpose', 'Xpose', 0, 11, 0),
    'InvC':      num_vo('InvC', 'InvC', 0, 11, 0),
    'RegTrace':  toggle_vo('RegTrace', 0),
    'AutoFit':   toggle_vo('AutoFit', 0),
    'Study':     toggle_vo('Study', 0),
    'StudyCard': num_vo('StudyCard', 'StudyCard', 2, 9, 3),
    'StudyIdx':  num_vo('StudyIdx', 'StudyIdx', 1, 50, 1),
    'StudyRot':  num_vo('StudyRot', 'StudyRot', 0, 11, 0),
    'StudyTonic': enum_vo('StudyTonic', 'StudyTon',
                          ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'], 0),
    'StudyInv':  toggle_vo('StudyInv', 0),
}


def mkbox(bl, **kw):
    bl[0].append({'box': kw})


def mkline(bl, src, si, dst, di):
    bl[1].append({'patchline': {'source': [src, si], 'destination': [dst, di]}})


# ---- the popup subpatcher ---------------------------------------------------------------
# The window opens in patching view (so tonnetz.js can resize its own box). Everything that
# is not a control or the canvas -- the inlet, the prepend/pak plumbing, js pcsetinfo, the
# loadbang chain -- is marked `hidden` so it and its patch cords do not show in the locked
# popup. Only the top control strip and the jsui are visible.
def build_subpatcher(appversion):
    bl = ([], [])
    B, L = bl
    HID = {'hidden': 1}
    PLUMB_Y = 800.0            # hidden plumbing lives well below the visible area

    # every cord in this subpatcher is plumbing -> mark the patchline itself hidden, which
    # (unlike box `hidden`) reliably keeps it out of the locked popup.
    def hline(src, si, dst, di):
        L.append({'patchline': {'source': [src, si], 'destination': [dst, di], 'hidden': 1}})

    def plumb(oid, text, x, y, w, var, **extra):
        kw = dict(id=oid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                  patching_rect=[x, y, w, 22.0], text=text, varname=var, **HID)
        kw.update(extra)
        mkbox(bl, **kw)

    # note feed in + analyser
    mkbox(bl, id='obj-110', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
          patching_rect=[16.0, PLUMB_Y, 24.0, 24.0], varname='tzw_in', **HID)
    plumb('obj-111', 'prepend note', 16.0, PLUMB_Y + 26, 90.0, 'tzw_prep_note')
    mkbox(bl, id='obj-105', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
          patching_rect=[120.0, PLUMB_Y + 52, 110.0, 22.0], text='js ' + JS_INFO,
          varname='tzw_pcinfo', saved_object_attributes={'filename': JS_INFO, 'parameter_enable': 0},
          **HID)
    plumb('obj-112', 'send ---tonnetzinfo', 120.0, PLUMB_Y + 78, 140.0, 'tzw_sendinfo')
    mkbox(bl, id='obj-106', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
          patching_rect=[250.0, PLUMB_Y + 52, 120.0, 22.0], text='js ' + JS_FIT,
          varname='tzw_fit', saved_object_attributes={'filename': JS_FIT, 'parameter_enable': 0},
          **HID)
    plumb('obj-113', 'send ---tonnetzfit', 250.0, PLUMB_Y + 78, 140.0, 'tzw_sendfit')
    hline('obj-110', 0, 'obj-111', 0)
    hline('obj-111', 0, 'obj-100', 0)      # note <p> <v> -> jsui
    hline('obj-111', 0, 'obj-105', 0)      # note <p> <v> -> set-class analyser
    hline('obj-111', 0, 'obj-106', 0)      # note <p> <v> -> compactness analyser
    hline('obj-105', 0, 'obj-100', 0)      # info / setclass -> jsui
    hline('obj-105', 1, 'obj-112', 0)      # tagged fields -> send ---tonnetzinfo
    hline('obj-106', 0, 'obj-100', 0)      # bestfit -> jsui
    hline('obj-106', 1, 'obj-113', 0)      # fit lists -> send ---tonnetzfit

    prep_y = [PLUMB_Y + 110]

    def control(longname, innerid, maxcls, sel, strip_rect):
        r = [float(x) for x in strip_rect]
        mkbox(bl, id=innerid, maxclass=maxcls, numinlets=1,
              numoutlets=(2 if maxcls == 'live.numbox' else 1),
              outlettype=(['', 'float'] if maxcls == 'live.numbox' else ['']),
              parameter_enable=1, patching_rect=r, presentation=1, presentation_rect=r,
              varname='tzw_' + longname.lower(), annotation=ANN[longname],
              saved_attribute_attributes={'valueof': VO[longname]})
        if sel:
            pid = innerid + 'p'
            plumb(pid, 'prepend ' + sel, 16.0, prep_y[0], 120.0, 'tzw_pp_' + sel)
            prep_y[0] += 24
            hline(innerid, 0, pid, 0)
            hline(pid, 0, 'obj-100', 0)

    def label(x, y, w, txt):
        mkbox(bl, id='obj-l%d_%d' % (int(x), int(y)), maxclass='comment', numinlets=1,
              numoutlets=0, patching_rect=[float(x), float(y), float(w), 15.0],
              presentation=1, presentation_rect=[float(x), float(y), float(w), 15.0],
              fontsize=9.0, text=txt, varname='tzw_lb%d_%d' % (int(x), int(y)))

    # --- control strip: five 30px rows, fits ~510 px wide; inline labels so nothing overlaps -
    # row 1 (y 8): pick panels a dedo -- one toggle per view -- + the diatonic key
    vtog = [('VwTonnetz', 'obj-120', 'vton', 'Ton'), ('VwChrom', 'obj-121', 'vchr', 'Cro'),
            ('VwFifths', 'obj-122', 'vfif', 'Qui'), ('VwVoice', 'obj-123', 'vvoc', 'Voc'),
            ('VwPiano', 'obj-124', 'vpno', 'Pno'), ('VwGuitar', 'obj-125', 'vgtr', 'Gtr'),
            ('VwDiat', 'obj-126', 'vdia', 'Dia'), ('VwTet', 'obj-127', 'vtet', '3D')]
    vx = 8.0
    for longname, cid, sel, word in vtog:
        control(longname, cid, 'live.toggle', sel, [vx, 8.0, 14.0, 14.0])
        label(vx + 16, 8.0, 20.0, word)
        vx += 40.0
    control('Key',     'obj-128', 'live.menu', 'keyroot', [330.0, 6.0, 54.0, 20.0])
    control('KeyMode', 'obj-129', 'live.tab',  'keymode', [390.0, 6.0, 84.0, 20.0])

    # row 2 (y 38): Tonnetz shape -- preset, a/b/c vector, spacing, trace length
    control('Preset', 'obj-130', 'live.menu', 'preset', [8.0, 37.0, 140.0, 20.0])
    label(154.0, 40.0, 30.0, 'a b c')
    control('TonA', 'obj-140', 'live.numbox', None, [186.0, 40.0, 26.0, 18.0])
    control('TonB', 'obj-141', 'live.numbox', None, [214.0, 40.0, 26.0, 18.0])
    control('TonC', 'obj-142', 'live.numbox', None, [242.0, 40.0, 26.0, 18.0])
    plumb('obj-145', 'pak 3 4 5', 372.0, PLUMB_Y + 300, 60.0, 'tzw_pak',
          numinlets=3, numoutlets=1)
    plumb('obj-146', 'prepend abc', 372.0, PLUMB_Y + 326, 90.0, 'tzw_pp_abc')
    hline('obj-140', 0, 'obj-145', 0)
    hline('obj-141', 0, 'obj-145', 1)
    hline('obj-142', 0, 'obj-145', 2)
    hline('obj-145', 0, 'obj-146', 0)
    hline('obj-146', 0, 'obj-100', 0)
    # Preset <-> a/b/c sync: the jsui's outlet 0 carries `abc a b c` (after a preset pick)
    # and `presetsel i` (when a/b/c equals a preset). route them back to the numboxes / menu.
    plumb('obj-147', 'route abc presetsel', 372.0, PLUMB_Y + 352, 140.0, 'tzw_route_sync',
          numoutlets=3, outlettype=['', '', ''])
    plumb('obj-148', 'unpack 0 0 0', 372.0, PLUMB_Y + 378, 90.0, 'tzw_unpack_abc',
          numoutlets=3, outlettype=['', '', ''])
    plumb('obj-149', 'prepend set', 520.0, PLUMB_Y + 378, 70.0, 'tzw_prep_setmenu')
    hline('obj-100', 0, 'obj-147', 0)
    hline('obj-147', 0, 'obj-148', 0)      # `abc a b c` -> unpack -> the a/b/c numboxes
    hline('obj-148', 0, 'obj-140', 0)
    hline('obj-148', 1, 'obj-141', 0)
    hline('obj-148', 2, 'obj-142', 0)
    hline('obj-147', 1, 'obj-149', 0)      # `presetsel i` -> set the Preset menu (no re-output)
    hline('obj-149', 0, 'obj-130', 0)
    label(276.0, 40.0, 32.0, 'radio')
    control('Radius', 'obj-150', 'live.numbox', 'radius', [312.0, 40.0, 34.0, 18.0])
    label(352.0, 40.0, 34.0, 'traza')
    control('TraceLen', 'obj-162', 'live.numbox', 'tracelen', [388.0, 40.0, 28.0, 18.0])
    label(420.0, 40.0, 16.0, '3D')
    control('TetPreset', 'obj-131', 'live.menu', 'tetpreset', [436.0, 40.0, 74.0, 18.0])

    # row 3 (y 68): the seven analysis toggles, each labelled
    tog = [('Trace', 'obj-160', 'trace', 'Rastro'), ('Harmonize', 'obj-170', 'harm', 'Vecinos'),
           ('Faces', 'obj-180', 'faces', 'Estruct'), ('Labels', 'obj-190', 'labels', 'Nombres'),
           ('ChordPoly', 'obj-210', 'chordpoly', 'Poligono'),
           ('TracePath', 'obj-212', 'tracepath', 'Camino'), ('Colors', 'obj-214', 'colors', 'Color')]
    tx = 8.0
    for longname, cid, sel, word in tog:
        control(longname, cid, 'live.toggle', sel, [tx, 68.0, 15.0, 15.0])
        label(tx + 18, 68.0, 52.0, word)
        tx += 70.0

    # row 4 (y 98): piano / guitar controls
    control('PianoMode',  'obj-240', 'live.tab',  'pianomode',  [8.0, 98.0, 88.0, 20.0])
    control('GuitarMode', 'obj-242', 'live.tab',  'guitarmode', [102.0, 98.0, 98.0, 20.0])
    control('Tuning',     'obj-244', 'live.menu', 'tuning',     [206.0, 98.0, 84.0, 20.0])
    label(296.0, 100.0, 30.0, 'trast')
    control('Frets', 'obj-246', 'live.numbox', 'frets', [328.0, 100.0, 26.0, 18.0])
    label(360.0, 100.0, 30.0, 'zoom')
    control('Zoom', 'obj-248', 'live.numbox', 'zoom', [392.0, 100.0, 26.0, 18.0])
    label(424.0, 100.0, 24.0, 'pan')
    control('Pan', 'obj-250', 'live.numbox', 'pan', [450.0, 100.0, 34.0, 18.0])

    # row 5 (y 128): neo-Riemannian arrows + transformation preview + region trace / autofit
    control('Plr', 'obj-260', 'live.toggle', 'plr', [8.0, 128.0, 15.0, 15.0])
    label(26.0, 128.0, 38.0, 'P/L/R')
    control('XfPrev', 'obj-262', 'live.toggle', 'xfprev', [68.0, 128.0, 15.0, 15.0])
    label(86.0, 128.0, 30.0, 'prev')
    control('XfMode', 'obj-264', 'live.tab', 'xfmode', [118.0, 128.0, 112.0, 18.0])
    label(236.0, 128.0, 30.0, 'trans')
    control('Xpose', 'obj-266', 'live.numbox', 'xpose', [268.0, 128.0, 26.0, 18.0])
    label(298.0, 128.0, 20.0, 'eje')
    control('InvC', 'obj-268', 'live.numbox', 'invc', [320.0, 128.0, 26.0, 18.0])
    control('RegTrace', 'obj-270', 'live.toggle', 'regtrace', [356.0, 128.0, 15.0, 15.0])
    label(374.0, 128.0, 52.0, 'Regiones')
    control('AutoFit', 'obj-272', 'live.toggle', 'autofit', [434.0, 128.0, 15.0, 15.0])
    label(452.0, 128.0, 44.0, 'Ajuste')

    # row 6 (y 158): study mode -- dial in a Forte class / rotation / tonic, MIDI frozen out.
    # These 5 value controls feed a pak -> `prepend studyset` -> pcsetinfo, gated by Study.
    control('Study', 'obj-300', 'live.toggle', None, [8.0, 158.0, 15.0, 15.0])
    label(26.0, 158.0, 44.0, 'Estudio')
    label(74.0, 158.0, 30.0, 'forte')
    control('StudyCard', 'obj-301', 'live.numbox', None, [106.0, 158.0, 26.0, 18.0])
    label(136.0, 158.0, 10.0, '#')
    control('StudyIdx', 'obj-302', 'live.numbox', None, [148.0, 158.0, 32.0, 18.0])
    label(184.0, 158.0, 20.0, 'rot')
    control('StudyRot', 'obj-303', 'live.numbox', None, [206.0, 158.0, 26.0, 18.0])
    label(236.0, 158.0, 22.0, 'ton')
    control('StudyTonic', 'obj-304', 'live.menu', None, [260.0, 158.0, 54.0, 20.0])
    control('StudyInv', 'obj-305', 'live.toggle', None, [322.0, 158.0, 15.0, 15.0])
    label(340.0, 158.0, 58.0, 'inv forma')

    # study plumbing: 5 controls -> pak -> prepend studyset -> gate -> pcsetinfo (obj-105).
    # Study toggle: t b i i  -- studymode to jsui first, then open the gate, then bang the pak.
    plumb('obj-310', 'pak 3 1 0 0 0', 372.0, PLUMB_Y + 470, 90.0, 'tzw_study_pak',
          numinlets=5, numoutlets=1)
    plumb('obj-311', 'prepend studyset', 372.0, PLUMB_Y + 496, 110.0, 'tzw_study_prep')
    plumb('obj-312', 't b i i', 16.0, PLUMB_Y + 470, 60.0, 'tzw_study_trig',
          numinlets=1, numoutlets=3, outlettype=['', '', ''])
    plumb('obj-318', 'prepend studymode', 16.0, PLUMB_Y + 496, 120.0, 'tzw_pp_studymode')
    plumb('obj-319', 'gate 1 0', 372.0, PLUMB_Y + 548, 50.0, 'tzw_study_gate',
          numinlets=2, numoutlets=1)
    hline('obj-300', 0, 'obj-312', 0)
    hline('obj-312', 2, 'obj-318', 0)      # rightmost i (fires first): studymode -> jsui
    hline('obj-318', 0, 'obj-100', 0)
    hline('obj-312', 1, 'obj-319', 0)      # middle i: open/close the gate
    hline('obj-312', 0, 'obj-310', 0)      # b (fires last): re-emit the pak
    hline('obj-301', 0, 'obj-310', 0)      # StudyCard -> pak inlet 0 (hot)
    for k, cid in enumerate(('obj-302', 'obj-303', 'obj-304', 'obj-305')):
        tid = 'obj-31%d' % (4 + k)         # obj-314..317
        plumb(tid, 't b i', 90.0 + k * 70, PLUMB_Y + 522, 40.0, 'tzw_study_t%d' % k,
              numinlets=1, numoutlets=2, outlettype=['', ''])
        hline(cid, 0, tid, 0)
        hline(tid, 1, 'obj-310', k + 1)    # value -> pak cold inlet k+1
        hline(tid, 0, 'obj-310', 0)        # bang -> pak hot inlet (re-emit)
    hline('obj-310', 0, 'obj-311', 0)
    hline('obj-311', 0, 'obj-319', 1)      # studyset list -> gate data inlet
    hline('obj-319', 0, 'obj-105', 0)      # gate open -> pcsetinfo builds + emits

    # the canvas -- oversized; tonnetz.js draws only within the real window size and keeps
    # its own box rect matched to it. Added last so it sits on top in patching view.
    # y must match BOX_TOP in tonnetz.js (six 30px rows + margin).
    mkbox(bl, id='obj-100', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[8.0, 182.0, 1600.0, 1100.0], parameter_enable=0,
          filename=JS, varname='tzw_ui')

    # initial state -> jsui (hidden loadbang chain)
    plumb('obj-199', 'loadbang', 8.0, PLUMB_Y + 400, 62.0, 'tzw_init', outlettype=['bang'])
    for dst in BANG_SAFE:
        hline('obj-199', 0, dst, 0)
    for i, longname in enumerate(TOGGLES):
        cid = dict((c[0], c[2]) for c in CTRL)[longname]
        mid = 'obj-ov%d' % i
        mkbox(bl, id=mid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
              patching_rect=[90.0 + i * 84.0, PLUMB_Y + 440, 74.0, 22.0], text='outputvalue',
              varname='tzw_ov%d' % (i + 1), **HID)
        hline('obj-199', 0, mid, 0)
        hline(mid, 0, cid, 0)

    local_params = {cid: [ln, sn, i] for i, (ln, sn, cid, _mc, _s) in enumerate(CTRL)}
    local_params['inherited_shortname'] = 1

    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': [140.0, 110.0, 1040.0, 770.0], 'openrect': [0.0, 0.0, 1040.0, 770.0],
        'openinpresentation': 0, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'Tonnetz',
        'boxes': B, 'lines': L, 'parameters': local_params,
        'dependency_cache': [
            {'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
            {'name': JS_INFO, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
            {'name': JS_FIT, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        ],
        'autosave': 0,
    }


# ---- the device (top patcher) ---------------------------------------------------------
def build_top(appversion):
    bl = ([], [])

    mkbox(bl, id='obj-1', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['int'],
          patching_rect=[24.0, 300.0, 40.0, 22.0], text='midiin', varname='tz_midiin')
    mkbox(bl, id='obj-2', maxclass='newobj', numinlets=1, numoutlets=0,
          patching_rect=[24.0, 340.0, 47.0, 22.0], text='midiout', varname='tz_midiout')
    mkline(bl, 'obj-1', 0, 'obj-2', 0)

    mkbox(bl, id='obj-3', maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['', '', ''],
          patching_rect=[24.0, 40.0, 60.0, 22.0], text='notein', varname='tz_notein')
    mkbox(bl, id='obj-4', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[24.0, 80.0, 60.0, 22.0], text='pack 0 0', varname='tz_pack')
    mkline(bl, 'obj-3', 0, 'obj-4', 0)
    mkline(bl, 'obj-3', 1, 'obj-4', 1)

    sub = build_subpatcher(appversion)
    mkbox(bl, id=SUB, maxclass='newobj', numinlets=1, numoutlets=0,
          patching_rect=[24.0, 140.0, 130.0, 22.0], text='p tonnetz_window',
          varname='tz_window', patcher=sub)
    mkline(bl, 'obj-4', 0, SUB, 0)

    mkbox(bl, id='obj-20', maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
          parameter_enable=1, mode=1, text='Tonnetz', texton='Tonnetz',
          patching_rect=[200.0, 40.0, 96.0, 24.0], presentation=1,
          presentation_rect=[8.0, 8.0, 120.0, 24.0], varname='tz_open_btn',
          annotation=ANN['Abrir'], saved_attribute_attributes={'valueof': VO['Abrir']})
    mkbox(bl, id='obj-21', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[200.0, 90.0, 48.0, 22.0], text='open', varname='tz_msg_open')
    mkbox(bl, id='obj-22', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[200.0, 130.0, 56.0, 22.0], text='pcontrol', varname='tz_pcontrol')
    mkbox(bl, id='obj-23', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['bang', 'bang'],
          patching_rect=[320.0, 40.0, 110.0, 22.0], text='live.thisdevice', varname='tz_thisdev')
    mkbox(bl, id='obj-24', maxclass='comment', numinlets=1, numoutlets=0,
          patching_rect=[8.0, 300.0, 200.0, 18.0], presentation=1,
          presentation_rect=[8.0, 36.0, 190.0, 18.0], fontsize=9.0,
          text='ventana flotante, fuera del rack', varname='tz_hint')
    mkline(bl, 'obj-20', 0, 'obj-21', 0)
    mkline(bl, 'obj-23', 0, 'obj-21', 0)
    mkline(bl, 'obj-21', 0, 'obj-22', 0)
    mkline(bl, 'obj-22', 0, SUB, 0)

    return bl


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(TEMPLATE)
    P = doc['patcher']
    appversion = P['appversion']

    boxes, lines = build_top(appversion)
    P['boxes'] = boxes
    P['lines'] = lines

    params = {'obj-20': ['Abrir', 'Abrir', 0]}
    for i, (ln, sn, cid, _mc, _s) in enumerate(CTRL):
        params['%s::%s' % (SUB, cid)] = [ln, sn, i + 1]
    banks = {}
    for bi, (bname, plist) in enumerate(BANKS):
        banks[str(bi)] = {'index': bi, 'name': bname,
                          'parameters': plist + ['-'] * (8 - len(plist))}
    params['parameterbanks'] = banks
    params['inherited_shortname'] = 1
    P['parameters'] = params

    P['dependency_cache'] = [
        {'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        {'name': JS_INFO, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        {'name': JS_FIT, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
    ]
    P['rect'] = [140.0, 140.0, 480.0, 400.0]
    P['openinpresentation'] = 1

    # --- self-checks ------------------------------------------------------------------
    all_names = ['Abrir'] + [c[0] for c in CTRL]

    def boxes_of(pp):
        return pp.get('boxes', [])

    def check_patcher(pp, where):
        by_id = {}
        for b in boxes_of(pp):
            bx = b['box']
            assert bx['id'] not in by_id, '%s: dup id %s' % (where, bx['id'])
            by_id[bx['id']] = bx
        for ln in pp.get('lines', []):
            pl = ln['patchline']
            for tag, end in (('src', pl['source']), ('dst', pl['destination'])):
                bx = by_id.get(end[0])
                assert bx is not None, '%s: %s to unknown box %s' % (where, tag, end)
                n = bx.get('numoutlets', 0) if tag == 'src' else bx.get('numinlets', 0)
                assert 0 <= end[1] < n, '%s: %s %s idx %d out of 0..%d (%s %s)' % (
                    where, tag, end[0], end[1], n - 1, bx.get('maxclass'), bx.get('text', ''))
        for b in boxes_of(pp):
            if b['box'].get('patcher'):
                check_patcher(b['box']['patcher'], where + '::' + b['box']['id'])

    check_patcher(P, 'root')
    reg_names = {v[0] for k, v in params.items()
                 if k not in ('parameterbanks', 'inherited_shortname')}
    assert reg_names == set(all_names), set(all_names) ^ reg_names
    bank_union = {p for b in banks.values() for p in b['parameters'] if p != '-'}
    assert bank_union == set(all_names), set(all_names) ^ bank_union

    subbox = next(b['box'] for b in P['boxes'] if b['box']['id'] == SUB)
    sub_local = {v[0] for k, v in subbox['patcher']['parameters'].items()
                 if k != 'inherited_shortname'}
    assert sub_local == {c[0] for c in CTRL}, sub_local
    n_top, n_sub = len(P['boxes']), len(subbox['patcher']['boxes'])

    print('tonnetz.amxd  (v9: study mode -- pick Forte class / rotation / tonic, no MIDI)')
    print('  top boxes    : %d   sub boxes: %d' % (n_top, n_sub))
    print('  top lines    : %d   sub lines: %d' % (len(P['lines']), len(subbox['patcher']['lines'])))
    print('  params (%d)   : %s' % (len(all_names), ', '.join(all_names)))
    print('  banks        : %s' % ' | '.join('%s[%d]' % (n, len(p)) for n, p in BANKS))
    print('  js deps      : %s, %s, %s' % (JS, JS_INFO, JS_FIT))
    print('  amxdtype     : %s (unchanged = MIDI effect)' % P['project'].get('amxdtype'))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    if os.path.exists(DEVICE):
        shutil.copyfile(DEVICE, DEVICE + '.before')
        print('  backup       : %s.before' % os.path.basename(DEVICE))
    shutil.copyfile(TEMPLATE, DEVICE)
    d2, s2, e2, _ = amxd.load(DEVICE)
    amxd.save(DEVICE, d2, s2, e2, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    assert len(back['boxes']) == n_top
    bb = next(b['box'] for b in back['boxes'] if b['box']['id'] == SUB)
    assert bb.get('patcher') and len(bb['patcher']['boxes']) == n_sub, 'subpatcher lost on roundtrip'
    assert {d['name'] for d in back['dependency_cache']} == {JS, JS_INFO, JS_FIT}
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/tonnetz.amxd')


main()
