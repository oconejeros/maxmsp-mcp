"""Build forteseq/tonnetz.amxd -- the shell around tonnetz.js (the Tonnetz jsui) and
pcsetinfo.js (the set-class analyser).

    python tools/build_tonnetz.py            dry run, writes nothing
    python tools/build_tonnetz.py --apply    do it

Same method as tools/build_midibounce.py: the maxmsp MCP server is not reachable, so the
.amxd is assembled by copying a known-good MIDI-effect device
(forteseq/forteseqmidifilter.amxd) and rewriting boxes / lines / parameters /
dependency_cache. Copying the template's bytes keeps the binary AMPF/meta chunk that marks
the file as a MIDI effect ('midf') and the whole `project` block.

LAYOUT (v5). The Live device panel is nearly empty: a single "Tonnetz" button. The big
jsui, every control and the analyser live in an inline subpatcher `[p tonnetz_window]` that
opens as its OWN floating window (outside the rack) via `[pcontrol]`; `live.thisdevice`
opens it on load. The subpatcher opens in PATCHING view (not presentation) so tonnetz.js's
fitToWindow() -- which sets its own box rect from `this.patcher.wind.size` -- actually
resizes the canvas as the window is dragged. A 4-row control strip sits at the top; the
jsui fills the rest and draws five views -- Tonnetz, chromatic circle, fifths circle, piano
keyboard, guitar fretboard -- either one at a time or all at once ("Todo", stacked in rows).

    top patcher:
      notein --> pack (pitch vel) --> [p tonnetz_window] inlet 0
      midiin --> midiout                                   MIDI pass-through
      live.text "Tonnetz" --\
      live.thisdevice -------+-- open --> pcontrol --> [p tonnetz_window] inlet 0

    inside [p tonnetz_window]:
      inlet --> prepend note --> jsui tonnetz.js
                             \--> js pcsetinfo.js --outlet 0--> jsui   (`info <text>`)
                                                  --outlet 1--> send ---tonnetzinfo
      live.tab  "View"      --> prepend view      --> jsui   (Todo / Tonnetz / Cromatico / Quintas)
      live.menu "Preset"    --> prepend preset    --> jsui
      live.numbox A/B/C     --> pak 3 4 5 --> prepend abc --> jsui
      live.dial "Radius"    --> prepend radius    --> jsui
      live.toggle Trace/Harmonize/Faces/Labels/ChordPoly/TracePath/Colors --> prepend <sel> --> jsui
      live.numbox TraceLen  --> prepend tracelen  --> jsui
      live.tab PianoMode/GuitarMode + live.menu Tuning + live.numbox Frets/Zoom + live.dial Pan --> prepend <sel> --> jsui
      live.toggle Plr/XfPrev + live.tab XfMode + live.numbox Xpose/InvC --> prepend <sel> --> jsui
      loadbang --> bang the bang-safe controls; outputvalue the toggles (a bang inverts them)

26 parameters. The button is a top-level param (key "obj-20"); the 25 controls inside the
subpatcher are registered on the TOP patcher with "obj-10::<innerid>" keys AND in the
subpatcher's own local `parameters` block -- the nesting scheme FORTESEQ2 uses for its
fs2voice/fs2pages bpatchers. See the amxd-parameter-registries note. Four Push banks (8 + 8 + 4 + 6).

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
BOOT = 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq'
SUB = 'obj-10'                      # box id of the [p tonnetz_window] subpatcher

VIEWS = ['Todo', 'Tonnetz', 'Cromatico', 'Quintas', 'Piano', 'Guitarra']
# must match PRESETS[] in tonnetz.js
PRESETS = ['3 4 5  classic', '1 1 10  chromatic', '2 2 8  whole-tone', '1 4 7', '2 3 7',
           '1 2 9', '3 3 6', '4 4 4  augmented', '1 5 6', '2 5 5']
# must match TUNINGS[] in tonnetz.js
GUITAR_TUNINGS = ['Estandar', 'Drop D', 'DADGAD', 'Bajo 4', 'Bajo 5', 'Ukelele']

ANN = {
    'Abrir': 'Abre / trae al frente la ventana del Tonnetz (flota fuera del rack).',
    'View': 'Vista: Todo (las 5 a la vez, en 3 filas) o una sola -- Tonnetz, cromatico, quintas, piano, guitarra.',
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
}

# (longname, shortname, innerid, maxclass, prepend-selector or None)
CTRL = [
    ('View',       'View',      'obj-120', 'live.tab',     'view'),
    ('Preset',     'Preset',    'obj-130', 'live.menu',    'preset'),
    ('TonA',       'TonA',      'obj-140', 'live.numbox',  None),
    ('TonB',       'TonB',      'obj-141', 'live.numbox',  None),
    ('TonC',       'TonC',      'obj-142', 'live.numbox',  None),
    ('Radius',     'Radius',    'obj-150', 'live.dial',    'radius'),
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
    ('Pan',        'Pan',       'obj-250', 'live.dial',    'pan'),
    ('Plr',        'Plr',       'obj-260', 'live.toggle',  'plr'),
    ('XfPrev',     'XfPrev',    'obj-262', 'live.toggle',  'xfprev'),
    ('XfMode',     'XfMode',    'obj-264', 'live.tab',     'xfmode'),
    ('Xpose',      'Xpose',     'obj-266', 'live.numbox',  'xpose'),
    ('InvC',       'InvC',      'obj-268', 'live.numbox',  'invc'),
]
TOGGLES = ['Trace', 'Harmonize', 'Faces', 'Labels', 'ChordPoly', 'TracePath', 'Colors',
           'Plr', 'XfPrev']
BANG_SAFE = ['obj-120', 'obj-130', 'obj-140', 'obj-141', 'obj-142', 'obj-150', 'obj-162',
             'obj-240', 'obj-242', 'obj-244', 'obj-246', 'obj-248', 'obj-250',
             'obj-264', 'obj-266', 'obj-268']

BANKS = [
    ('Tonnetz',   ['Abrir', 'View', 'Preset', 'TonA', 'TonB', 'TonC', 'Radius', 'Trace']),
    ('Tonnetz 2', ['TraceLen', 'Harmonize', 'Faces', 'Labels', 'ChordPoly', 'TracePath', 'Colors', 'Plr']),
    ('Transform', ['XfPrev', 'XfMode', 'Xpose', 'InvC']),
    ('Piano/Guit', ['PianoMode', 'GuitarMode', 'Tuning', 'Frets', 'Zoom', 'Pan']),
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
    'View':      enum_vo('View', 'View', VIEWS, 0),
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
    hline('obj-110', 0, 'obj-111', 0)
    hline('obj-111', 0, 'obj-100', 0)      # note <p> <v> -> jsui
    hline('obj-111', 0, 'obj-105', 0)      # note <p> <v> -> analyser
    hline('obj-105', 0, 'obj-100', 0)      # info <text> -> jsui
    hline('obj-105', 1, 'obj-112', 0)      # tagged fields -> send ---tonnetzinfo

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

    # --- control strip: three rows so it survives a narrow window (fits ~480 px wide) -----
    # row 1 (y 6): View | Preset | a b c | Radio | n
    control('View',   'obj-120', 'live.tab',  'view',   [8.0, 6.0, 196.0, 22.0])
    control('Preset', 'obj-130', 'live.menu', 'preset', [212.0, 6.0, 150.0, 22.0])
    label(372.0, 0.0, 40.0, 'a  b  c')
    control('TonA', 'obj-140', 'live.numbox', None, [372.0, 14.0, 30.0, 18.0])
    control('TonB', 'obj-141', 'live.numbox', None, [406.0, 14.0, 30.0, 18.0])
    control('TonC', 'obj-142', 'live.numbox', None, [440.0, 14.0, 30.0, 18.0])
    plumb('obj-145', 'pak 3 4 5', 372.0, PLUMB_Y + 300, 60.0, 'tzw_pak',
          numinlets=3, numoutlets=1)
    plumb('obj-146', 'prepend abc', 372.0, PLUMB_Y + 326, 90.0, 'tzw_pp_abc')
    hline('obj-140', 0, 'obj-145', 0)
    hline('obj-141', 0, 'obj-145', 1)
    hline('obj-142', 0, 'obj-145', 2)
    hline('obj-145', 0, 'obj-146', 0)
    hline('obj-146', 0, 'obj-100', 0)

    label(478.0, 0.0, 40.0, 'Radio')
    control('Radius', 'obj-150', 'live.dial', 'radius', [480.0, 12.0, 24.0, 24.0])
    label(512.0, 0.0, 16.0, 'n')
    control('TraceLen', 'obj-162', 'live.numbox', 'tracelen', [510.0, 14.0, 30.0, 18.0])

    # row 2 (y 38): the seven toggles, each labelled
    tog = [('Trace', 'obj-160', 'trace', 'Rastro'), ('Harmonize', 'obj-170', 'harm', 'Vecinos'),
           ('Faces', 'obj-180', 'faces', 'Caras'), ('Labels', 'obj-190', 'labels', 'Nombres'),
           ('ChordPoly', 'obj-210', 'chordpoly', 'Poligono'),
           ('TracePath', 'obj-212', 'tracepath', 'Camino'), ('Colors', 'obj-214', 'colors', 'Color')]
    tx = 8.0
    for longname, cid, sel, word in tog:
        control(longname, cid, 'live.toggle', sel, [tx, 40.0, 16.0, 16.0])
        label(tx + 18, 41.0, 52.0, word)
        tx += 74.0

    # row 3 (y 66): piano / guitar controls
    control('PianoMode',  'obj-240', 'live.tab',    'pianomode',  [8.0, 66.0, 100.0, 20.0])
    control('GuitarMode', 'obj-242', 'live.tab',    'guitarmode', [116.0, 66.0, 120.0, 20.0])
    control('Tuning',     'obj-244', 'live.menu',   'tuning',     [244.0, 66.0, 96.0, 20.0])
    label(348.0, 58.0, 34.0, 'Trast')
    control('Frets', 'obj-246', 'live.numbox', 'frets', [348.0, 70.0, 28.0, 18.0])
    label(384.0, 58.0, 32.0, 'Zoom')
    control('Zoom', 'obj-248', 'live.numbox', 'zoom', [386.0, 70.0, 30.0, 18.0])
    label(424.0, 58.0, 24.0, 'Pan')
    control('Pan', 'obj-250', 'live.dial', 'pan', [446.0, 64.0, 22.0, 22.0])

    # row 4 (y 92): neo-Riemannian arrows + transformation preview
    control('Plr', 'obj-260', 'live.toggle', 'plr', [8.0, 94.0, 16.0, 16.0])
    label(26.0, 95.0, 40.0, 'P/L/R')
    control('XfPrev', 'obj-262', 'live.toggle', 'xfprev', [70.0, 94.0, 16.0, 16.0])
    label(88.0, 95.0, 34.0, 'Prev')
    control('XfMode', 'obj-264', 'live.tab', 'xfmode', [126.0, 92.0, 130.0, 20.0])
    label(262.0, 84.0, 16.0, 'T')
    control('Xpose', 'obj-266', 'live.numbox', 'xpose', [262.0, 96.0, 30.0, 18.0])
    label(298.0, 84.0, 24.0, 'eje')
    control('InvC', 'obj-268', 'live.numbox', 'invc', [298.0, 96.0, 30.0, 18.0])

    # the canvas -- oversized; tonnetz.js draws only within the real window size and keeps
    # its own box rect matched to it. Added last so it sits on top in patching view.
    # y must match BOX_TOP in tonnetz.js (four-row strip).
    mkbox(bl, id='obj-100', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[8.0, 118.0, 1600.0, 1100.0], parameter_enable=0,
          filename=JS, varname='tzw_ui')

    # initial state -> jsui (hidden loadbang chain)
    plumb('obj-199', 'loadbang', 8.0, PLUMB_Y + 400, 62.0, 'tzw_init', outlettype=['bang'])
    for dst in BANG_SAFE:
        hline('obj-199', 0, dst, 0)
    for i, longname in enumerate(TOGGLES):
        cid = dict((c[0], c[2]) for c in CTRL)[longname]
        mid = 'obj-2%02d' % (30 + i)
        mkbox(bl, id=mid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
              patching_rect=[90.0 + i * 84.0, PLUMB_Y + 400, 74.0, 22.0], text='outputvalue',
              varname='tzw_ov%d' % (i + 1), **HID)
        hline('obj-199', 0, mid, 0)
        hline(mid, 0, cid, 0)

    local_params = {cid: [ln, sn, i] for i, (ln, sn, cid, _mc, _s) in enumerate(CTRL)}
    local_params['inherited_shortname'] = 1

    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': [140.0, 110.0, 1040.0, 690.0], 'openrect': [0.0, 0.0, 1040.0, 690.0],
        'openinpresentation': 0, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'Tonnetz',
        'boxes': B, 'lines': L, 'parameters': local_params,
        'dependency_cache': [
            {'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
            {'name': JS_INFO, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
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

    print('tonnetz.amxd  (v5: + simplicial closure, P/L/R, transform preview)')
    print('  top boxes    : %d   sub boxes: %d' % (n_top, n_sub))
    print('  top lines    : %d   sub lines: %d' % (len(P['lines']), len(subbox['patcher']['lines'])))
    print('  params (%d)   : %s' % (len(all_names), ', '.join(all_names)))
    print('  banks        : %s' % ' | '.join('%s[%d]' % (n, len(p)) for n, p in BANKS))
    print('  js deps      : %s, %s' % (JS, JS_INFO))
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
    assert {d['name'] for d in back['dependency_cache']} == {JS, JS_INFO}
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/tonnetz.amxd')


main()
