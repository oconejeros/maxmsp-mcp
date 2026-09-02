"""Build forteseq/ANIMIDI.amxd -- the shell around animidi.js (the Music-Animation-Machine
scrolling bar-graph score jsui).

    python tools/build_animidi.py            dry run, writes nothing
    python tools/build_animidi.py --apply    do it

Method: same as tools/build_tonnetz.py / tools/build_midibounce.py, but the template IS the
device. The user created forteseq/ANIMIDI.amxd as a stock Max 9 MIDI-effect device ("Build
your MIDI effect here"); this script loads it, replaces `boxes` / `lines` / `parameters` /
`dependency_cache`, and writes it back in place (a .before backup is taken first). Editing
in place keeps the binary AMPF / meta chunk and the `project` block (amxdtype = MIDI
effect) exactly as Max wrote them -- amxd.save() only rewrites the ptch length header.

LAYOUT (mirrors tonnetz.amxd, but simpler). The Live device panel holds one "ANIMIDI"
button. The jsui and every control live in an inline subpatcher `[p animidi_window]` that
opens as its OWN floating window (outside the rack) via `[pcontrol]`; `live.thisdevice`
opens it on load and also arms the Live-API feeds. The subpatcher opens in PRESENTATION
view (`openinpresentation 1`) so the popup is always locked/interactive -- even with the
Max editor open (patching view opens UNLOCKED then, and the controls can't be clicked --
that was the first bug). The jsui stretches to fill the floating window -- a Task in
animidi.js matches its box.rect to the window size (box.rect == the presentation rect in
presentation view). A 3-row control strip sits above it. The scroll animation is driven
BOTH by a JS Task in animidi.js AND by `metro 33 -> jsui bang()`, belt and suspenders.

    top patcher:
      notein --> pack 0 0 0 --> prepend note --> [p animidi_window] inlet 0
      midiin --> midiout                                            MIDI pass-through
      live.thisdevice --> t b b 1
                          |  1 --> metro 50 --> transport --> (tick) --> / 480. --> prepend songpos --> [win]
                          |  b --> live.path live_set --> live.observer is_playing / tempo (target)
                          |  b --> bang those observers (emit current)
                          |        is_playing --> prepend transport --> [win]
                          |        tempo      --> prepend tempo     --> [win]
      live.thisdevice --> open --> pcontrol --> [p animidi_window] inlet 0
      live.text "ANIMIDI" (Abrir) --> open --> pcontrol

    inside [p animidi_window]:
      inlet --> jsui animidi.js            (note / transport / tempo / songpos land here directly)
      control strip (10 live.* controls) --> prepend <sel> --> jsui
      loadbang --> re-emit the bang-safe controls; outputvalue the Grid toggle (a bang inverts it)

21 parameters (Abrir + 20). The button is a top-level param (key "obj-20"); the controls
inside the subpatcher are registered on the TOP patcher with "obj-10::<innerid>" keys AND in
the subpatcher's own local `parameters` block -- the nesting scheme tonnetz.amxd /
fs2voice use. Three Push banks (8 + 6 + 7).

Close the device in BOTH Max and Live before running with --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'ANIMIDI.amxd')
JS = 'animidi.js'
BOOT = 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq'
SUB = 'obj-10'                       # box id of the [p animidi_window] subpatcher

TIME_MODES  = ['Tiempo real', 'Lookahead']
COLOR_MODES = ['Nota', 'Voz', 'Fijo']
RANGE_MODES = ['Auto', 'Fijo']
VIEW_MODES  = ['Barras', 'Espiral', 'Dodecaedro', 'Práctica']
VOICE_MODES = ['Off', 'Figura', 'Carriles']
SPIN_MODES  = ['Pulso', 'Notas']

ANN = {
    'Abrir':     'Abre / trae al frente la ventana de ANIMIDI (flota fuera del rack).',
    'TimeMode':  ('Modelo de tiempo. Tiempo real: las notas aparecen en la linea "ahora" y '
                 'se van hacia la izquierda (reloj de pared, congelado si el transporte esta '
                 'detenido). Lookahead: todo el clip esta en pantalla y las notas entran '
                 'desde la derecha antes de sonar (lee el clip por la Live API; posicion en '
                 'compases + tempo de Live).'),
    'Scale':     'Escala horizontal en pixeles por segundo (20-400). En Lookahead se convierte a px por pulso con el tempo.',
    'ColorMode': 'De donde sale el color de las barras: Nota = clase de altura (rueda de quintas, tipo tonnetz; HueC/sat/lum la ajustan). Voz = un color por pista. Fijo = un solo color.',
    'RangeMode': 'Eje vertical: Auto se ajusta al ambito de la musica; Fijo usa RangeLo..RangeHi.',
    'RangeLo':   'Nota MIDI mas grave del eje vertical cuando RangeMode = Fijo (0-127).',
    'RangeHi':   'Nota MIDI mas aguda del eje vertical cuando RangeMode = Fijo (0-127).',
    'Grid':      'Lineas de octava (cada Do) y lineas de pulso / compas (4/4).',
    'Piano':     ('Barras: muestra un teclado de piano en el borde izquierdo; las teclas se '
                 'encienden con las notas que suenan. (En Practica el teclado va abajo y '
                 'siempre esta; en Carriles se oculta.)'),
    'Fps':       'Cuadros por segundo del redibujado (15-60).',
    'ReadClip':  'Lookahead: vuelve a leer las notas del clip seleccionado en la vista de clip de Live. Tambien se relee solo al arrancar el transporte.',
    'Clear':     'Borra todos los eventos dibujados y las notas de clip en cache.',
    'HueC':      'Tono (matiz, 0-359 grados) que se le da a la nota Do. Toda la rueda de color rota con el: cada nota conserva su distancia relativa (una quinta = 30 grados). Solo afecta a ColorMode = Nota. Azul ~= 220.',
    'PalSat':    'Saturacion de la paleta de nota (0-100). Solo con ColorMode = Nota.',
    'PalLum':    'Luminosidad de la paleta de nota (0-100). Solo con ColorMode = Nota.',
    'ViewMode':  ('Visualizacion: Barras (score de piano-roll que se desplaza), Espiral '
                 '(helice de altura), Dodecaedro (solido de 12 caras), o Practica (rollo MIDI '
                 'que cae sobre un teclado abajo, estilo Synthesia; sirve en Tiempo real y en '
                 'Lookahead). Espiral y Dodecaedro trazan la melodia reciente con estela.'),
    'VoiceMode': 'Solo en Barras: como se distinguen las voces (= pistas de Live). Off = todas iguales. Figura = cada pista una figura de barra distinta. Carriles = cada pista en su propia banda horizontal, sin solaparse. El COLOR es aparte, en ColorMode.',
    'TraceLen':  'Espiral / Dodecaedro: cuantos ataques recientes conserva la estela melodica (2-64).',
    'Spin':      'Espiral / Dodecaedro: ganancia de rotacion (0 = estatico). Con SpinMode = Pulso gira mas rapido; con Notas, ataques mas fuertes empujan mas.',
    'SpinMode':  ('Espiral / Dodecaedro: de que depende el giro. Pulso = rota con el pulso '
                 '(lo de antes). Notas = cada nota que entra da un empujon al giro y luego '
                 'frena; la direccion sigue el contorno melodico (sube / baja).'),
    'RingGap':   'Espiral: separacion en pixeles entre anillos de octava (8-60).',
}

# (longname, shortname, innerid, maxclass, selector, kind)
#   kind: 'ctl' normal control -> prepend selector -> jsui
#         'btn' live.text button -> sel 1 -> message <selector> -> jsui
CTRL = [
    ('TimeMode',  'TimeMode',  'obj-120', 'live.tab',     'timemode',  'ctl'),
    ('ColorMode', 'ColorMode', 'obj-121', 'live.menu',    'colormode', 'ctl'),
    ('RangeMode', 'RangeMode', 'obj-122', 'live.tab',     'rangemode', 'ctl'),
    ('Grid',      'Grid',      'obj-123', 'live.toggle',  'grid',      'ctl'),
    ('Scale',     'Scale',     'obj-124', 'live.numbox',  'pxpersec',  'ctl'),
    ('RangeLo',   'RangeLo',   'obj-125', 'live.numbox',  'rangelo',   'ctl'),
    ('RangeHi',   'RangeHi',   'obj-126', 'live.numbox',  'rangehi',   'ctl'),
    ('Fps',       'Fps',       'obj-127', 'live.numbox',  'fps',       'ctl'),
    ('HueC',      'HueC',      'obj-130', 'live.numbox',  'basehue',   'ctl'),
    ('PalSat',    'PalSat',    'obj-131', 'live.numbox',  'basesat',   'ctl'),
    ('PalLum',    'PalLum',    'obj-132', 'live.numbox',  'baselum',   'ctl'),
    ('ViewMode',  'ViewMode',  'obj-133', 'live.tab',     'viewmode',  'ctl'),
    ('VoiceMode', 'VoiceMode', 'obj-134', 'live.menu',    'voicemode', 'ctl'),
    ('TraceLen',  'TraceLen',  'obj-135', 'live.numbox',  'tracelen',  'ctl'),
    ('Spin',      'Spin',      'obj-136', 'live.numbox',  'spin',      'ctl'),
    ('SpinMode',  'SpinMode',  'obj-138', 'live.menu',    'spinmode',  'ctl'),
    ('RingGap',   'RingGap',   'obj-137', 'live.numbox',  'ringgap',   'ctl'),
    ('Piano',     'Piano',     'obj-139', 'live.toggle',  'piano',     'ctl'),
    ('ReadClip',  'ReadClip',  'obj-128', 'live.text',    'readclip',  'btn'),
    ('Clear',     'Clear',     'obj-129', 'live.text',    'clear',     'btn'),
]
# controls that safely re-emit their stored value on a bare bang (NOT live.toggle, which
# inverts -- see the max_live_toggle_bang_inverts memory)
BANG_SAFE = ['obj-120', 'obj-121', 'obj-122', 'obj-124', 'obj-125', 'obj-126', 'obj-127',
             'obj-130', 'obj-131', 'obj-132', 'obj-133', 'obj-134', 'obj-135', 'obj-136',
             'obj-137', 'obj-138']

BANKS = [
    ('Vista',    ['TimeMode', 'Scale', 'ColorMode', 'RangeMode', 'RangeLo', 'RangeHi', 'Grid', 'Fps']),
    ('Paleta',   ['HueC', 'PalSat', 'PalLum', 'ReadClip', 'Clear', 'Abrir']),
    ('Vistas 2', ['ViewMode', 'VoiceMode', 'Piano', 'TraceLen', 'Spin', 'SpinMode', 'RingGap']),
]


# ---- parameter valueof blocks (copied from build_tonnetz.py) ---------------------------
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
    'TimeMode':  enum_vo('TimeMode', 'TimeMode', TIME_MODES, 0),
    'ColorMode': enum_vo('ColorMode', 'ColorMode', COLOR_MODES, 0),
    'RangeMode': enum_vo('RangeMode', 'RangeMode', RANGE_MODES, 0),
    'Grid':      toggle_vo('Grid', 1),
    'Scale':     num_vo('Scale', 'Scale', 20, 400, 90),
    'RangeLo':   num_vo('RangeLo', 'RangeLo', 0, 127, 36),
    'RangeHi':   num_vo('RangeHi', 'RangeHi', 0, 127, 96),
    'Fps':       num_vo('Fps', 'Fps', 15, 60, 30),
    'HueC':      num_vo('HueC', 'HueC', 0, 359, 0),
    'PalSat':    num_vo('PalSat', 'PalSat', 0, 100, 62),
    'PalLum':    num_vo('PalLum', 'PalLum', 0, 100, 55),
    'ViewMode':  enum_vo('ViewMode', 'ViewMode', VIEW_MODES, 0),
    'VoiceMode': enum_vo('VoiceMode', 'VoiceMode', VOICE_MODES, 0),
    'TraceLen':  num_vo('TraceLen', 'TraceLen', 2, 64, 16),
    'Spin':      num_vo('Spin', 'Spin', 0, 100, 20),
    'SpinMode':  enum_vo('SpinMode', 'SpinMode', SPIN_MODES, 0),
    'RingGap':   num_vo('RingGap', 'RingGap', 8, 60, 24),
    'Piano':     toggle_vo('Piano', 1),
    'ReadClip':  enum_vo('ReadClip', 'ReadClip', ['off', 'on'], 0),
    'Clear':     enum_vo('Clear', 'Clear', ['off', 'on'], 0),
}


def mkbox(bl, **kw):
    bl[0].append({'box': kw})


def mkline(bl, src, si, dst, di):
    bl[1].append({'patchline': {'source': [src, si], 'destination': [dst, di]}})


# ---- the popup subpatcher -------------------------------------------------------------
def build_subpatcher(appversion):
    bl = ([], [])
    B, L = bl
    HID = {'hidden': 1}
    PLUMB_Y = 700.0

    def hline(src, si, dst, di):
        L.append({'patchline': {'source': [src, si], 'destination': [dst, di], 'hidden': 1}})

    def plumb(oid, text, x, y, w, var, **extra):
        kw = dict(id=oid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                  patching_rect=[x, y, w, 22.0], text=text, varname=var, **HID)
        kw.update(extra)
        mkbox(bl, **kw)

    # note / transport / tempo / songpos all arrive already tagged from the top patcher and
    # go straight to the jsui.
    mkbox(bl, id='obj-100', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
          patching_rect=[16.0, PLUMB_Y, 24.0, 24.0], varname='aw_in', **HID)
    hline('obj-100', 0, 'obj-101', 0)

    prep_y = [PLUMB_Y + 40]

    def control(longname, innerid, maxcls, sel, kind, strip_rect):
        r = [float(x) for x in strip_rect]
        kw = dict(id=innerid, maxclass=maxcls, numinlets=1,
                  numoutlets=(2 if maxcls == 'live.numbox' else 1),
                  outlettype=(['', 'float'] if maxcls == 'live.numbox' else ['']),
                  parameter_enable=1, patching_rect=r, presentation=1, presentation_rect=r,
                  varname='aw_' + longname.lower(), annotation=ANN[longname],
                  saved_attribute_attributes={'valueof': VO[longname]})
        if maxcls == 'live.text':
            kw.update(mode=1, text=longname, texton=longname)
        mkbox(bl, **kw)
        if kind == 'btn':
            sid, mid = innerid + 's', innerid + 'm'
            plumb(sid, 'sel 1', 16.0, prep_y[0], 60.0, 'aw_sel_' + sel, numinlets=2,
                  numoutlets=2, outlettype=['bang', ''])
            mkbox(bl, id=mid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
                  patching_rect=[90.0, prep_y[0], 90.0, 22.0], text=sel,
                  varname='aw_msg_' + sel, **HID)
            prep_y[0] += 24
            hline(innerid, 0, sid, 0)
            hline(sid, 0, mid, 0)
            hline(mid, 0, 'obj-101', 0)
        else:
            pid = innerid + 'p'
            plumb(pid, 'prepend ' + sel, 16.0, prep_y[0], 130.0, 'aw_pp_' + sel)
            prep_y[0] += 24
            hline(innerid, 0, pid, 0)
            hline(pid, 0, 'obj-101', 0)

    def label(x, y, w, txt):
        mkbox(bl, id='obj-l%d_%d' % (int(x), int(y)), maxclass='comment', numinlets=1,
              numoutlets=0, patching_rect=[float(x), float(y), float(w), 15.0],
              presentation=1, presentation_rect=[float(x), float(y), float(w), 15.0],
              fontsize=9.0, text=txt, varname='aw_lb%d_%d' % (int(x), int(y)))

    # row 1 (y 8): the mode controls
    control('TimeMode',  'obj-120', 'live.tab',  'timemode',  'ctl', [8.0, 8.0, 150.0, 20.0])
    control('ColorMode', 'obj-121', 'live.menu', 'colormode', 'ctl', [168.0, 8.0, 130.0, 20.0])
    control('RangeMode', 'obj-122', 'live.tab',  'rangemode', 'ctl', [308.0, 8.0, 96.0, 20.0])
    control('Grid',      'obj-123', 'live.toggle', 'grid',    'ctl', [416.0, 9.0, 16.0, 16.0])
    label(436.0, 10.0, 30.0, 'Grid')

    # row 2 (y 40): scales + range bounds + fps + actions
    label(8.0, 42.0, 34.0, 'px/s')
    control('Scale',   'obj-124', 'live.numbox', 'pxpersec', 'ctl', [44.0, 40.0, 44.0, 18.0])
    label(100.0, 42.0, 24.0, 'lo')
    control('RangeLo', 'obj-125', 'live.numbox', 'rangelo',  'ctl', [122.0, 40.0, 38.0, 18.0])
    label(168.0, 42.0, 24.0, 'hi')
    control('RangeHi', 'obj-126', 'live.numbox', 'rangehi',  'ctl', [190.0, 40.0, 38.0, 18.0])
    label(236.0, 42.0, 24.0, 'fps')
    control('Fps',     'obj-127', 'live.numbox', 'fps',      'ctl', [260.0, 40.0, 38.0, 18.0])
    control('ReadClip', 'obj-128', 'live.text', 'readclip',  'btn', [312.0, 40.0, 76.0, 20.0])
    control('Clear',    'obj-129', 'live.text', 'clear',     'btn', [396.0, 40.0, 60.0, 20.0])
    # palette: hue given to C (rotates the whole wheel), + saturation / luminosity
    label(468.0, 42.0, 24.0, 'C')
    control('HueC',   'obj-130', 'live.numbox', 'basehue', 'ctl', [484.0, 40.0, 40.0, 18.0])
    label(532.0, 42.0, 22.0, 'sat')
    control('PalSat', 'obj-131', 'live.numbox', 'basesat', 'ctl', [554.0, 40.0, 34.0, 18.0])
    label(596.0, 42.0, 24.0, 'lum')
    control('PalLum', 'obj-132', 'live.numbox', 'baselum', 'ctl', [620.0, 40.0, 34.0, 18.0])

    # row 3 (y 70): view selector + voice grouping + spiral/dodeca knobs
    label(8.0, 72.0, 30.0, 'vista')
    control('ViewMode',  'obj-133', 'live.tab',  'viewmode',  'ctl', [40.0, 70.0, 180.0, 20.0])
    control('VoiceMode', 'obj-134', 'live.menu', 'voicemode', 'ctl', [228.0, 70.0, 130.0, 20.0])
    label(366.0, 72.0, 30.0, 'traza')
    control('TraceLen', 'obj-135', 'live.numbox', 'tracelen', 'ctl', [398.0, 70.0, 34.0, 18.0])
    label(440.0, 72.0, 24.0, 'giro')
    control('Spin',     'obj-136', 'live.numbox', 'spin',     'ctl', [468.0, 70.0, 34.0, 18.0])
    label(510.0, 72.0, 36.0, 'anillo')
    control('RingGap',  'obj-137', 'live.numbox', 'ringgap',  'ctl', [548.0, 70.0, 34.0, 18.0])
    label(590.0, 72.0, 34.0, 'segun')
    control('SpinMode', 'obj-138', 'live.menu', 'spinmode', 'ctl', [626.0, 70.0, 104.0, 20.0])
    label(740.0, 72.0, 34.0, 'piano')
    control('Piano', 'obj-139', 'live.toggle', 'piano', 'ctl', [776.0, 71.0, 16.0, 16.0])

    # the canvas -- initial size only; animidi.js then stretches its box.rect to fill the
    # floating window every ~300 ms (presentation view keeps the popup locked even with the
    # Max editor open). x/y/pad here must match STRIP_H / VP_PAD in animidi.js.
    CANVAS = [8.0, 96.0, 1304.0, 656.0]
    mkbox(bl, id='obj-101', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=CANVAS, presentation=1, presentation_rect=CANVAS,
          parameter_enable=0, filename=JS, varname='aw_ui')

    # initial state -> jsui (hidden loadbang chain). Bang-safe controls re-emit; the Grid /
    # Piano toggles need `outputvalue` (a bare bang would invert them).
    plumb('obj-199', 'loadbang', 8.0, PLUMB_Y + 320, 62.0, 'aw_init', outlettype=['bang'])
    for dst in BANG_SAFE:
        hline('obj-199', 0, dst, 0)
    mkbox(bl, id='obj-198', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[90.0, PLUMB_Y + 350, 74.0, 22.0], text='outputvalue',
          varname='aw_ov_tgl', **HID)
    hline('obj-199', 0, 'obj-198', 0)
    hline('obj-198', 0, 'obj-123', 0)   # Grid
    hline('obj-198', 0, 'obj-139', 0)   # Piano

    local_params = {cid: [ln, sn, i] for i, (ln, sn, cid, _mc, _s, _k) in enumerate(CTRL)}
    local_params['inherited_shortname'] = 1

    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': [60.0, 60.0, 1320.0, 760.0], 'openrect': [0.0, 0.0, 1320.0, 760.0],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'ANIMIDI',
        'boxes': B, 'lines': L, 'parameters': local_params,
        'dependency_cache': [{'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1}],
        'autosave': 0,
    }


# ---- the device (top patcher) -------------------------------------------------------
def build_top(appversion):
    bl = ([], [])

    # MIDI pass-through
    mkbox(bl, id='obj-1', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['int'],
          patching_rect=[24.0, 320.0, 40.0, 22.0], text='midiin', varname='an_midiin')
    mkbox(bl, id='obj-2', maxclass='newobj', numinlets=1, numoutlets=0,
          patching_rect=[24.0, 360.0, 47.0, 22.0], text='midiout', varname='an_midiout')
    mkline(bl, 'obj-1', 0, 'obj-2', 0)

    # notein -> pack pitch vel chan -> prepend note -> subpatcher
    mkbox(bl, id='obj-3', maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['', '', ''],
          patching_rect=[24.0, 40.0, 90.0, 22.0], text='notein', varname='an_notein')
    mkbox(bl, id='obj-4', maxclass='newobj', numinlets=3, numoutlets=1, outlettype=[''],
          patching_rect=[24.0, 80.0, 90.0, 22.0], text='pack 0 0 0', varname='an_pack')
    mkbox(bl, id='obj-5', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[24.0, 110.0, 90.0, 22.0], text='prepend note', varname='an_prep_note')
    mkline(bl, 'obj-3', 0, 'obj-4', 0)
    mkline(bl, 'obj-3', 1, 'obj-4', 1)
    mkline(bl, 'obj-3', 2, 'obj-4', 2)
    mkline(bl, 'obj-4', 0, 'obj-5', 0)

    sub = build_subpatcher(appversion)
    mkbox(bl, id=SUB, maxclass='newobj', numinlets=1, numoutlets=0,
          patching_rect=[24.0, 150.0, 130.0, 22.0], text='p animidi_window',
          varname='an_window', patcher=sub)
    mkline(bl, 'obj-5', 0, SUB, 0)

    # the device-panel button + floating window opener
    mkbox(bl, id='obj-20', maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
          parameter_enable=1, mode=1, text='ANIMIDI', texton='ANIMIDI',
          patching_rect=[220.0, 40.0, 96.0, 24.0], presentation=1,
          presentation_rect=[8.0, 8.0, 120.0, 24.0], varname='an_open_btn',
          annotation=ANN['Abrir'], saved_attribute_attributes={'valueof': VO['Abrir']})
    mkbox(bl, id='obj-21', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[220.0, 100.0, 48.0, 22.0], text='open', varname='an_msg_open')
    mkbox(bl, id='obj-22', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[220.0, 140.0, 56.0, 22.0], text='pcontrol', varname='an_pcontrol')
    mkbox(bl, id='obj-23', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['bang', 'bang'],
          patching_rect=[360.0, 40.0, 110.0, 22.0], text='live.thisdevice', varname='an_thisdev')
    mkbox(bl, id='obj-24', maxclass='comment', numinlets=1, numoutlets=0,
          patching_rect=[8.0, 300.0, 220.0, 18.0], presentation=1,
          presentation_rect=[8.0, 36.0, 200.0, 18.0], fontsize=9.0,
          text='ventana flotante, fuera del rack', varname='an_hint')
    mkline(bl, 'obj-20', 0, 'obj-21', 0)
    mkline(bl, 'obj-23', 0, 'obj-21', 0)
    mkline(bl, 'obj-21', 0, 'obj-22', 0)
    mkline(bl, 'obj-22', 0, SUB, 0)

    # ---- Live-API feeds: play state, tempo, and song position in beats ----------------
    # t b b 1 off live.thisdevice: 1 -> start metro; b -> resolve live.path; b -> bang the
    # observers so they emit the current value (RTL order: metro, then path, then bang).
    mkbox(bl, id='obj-25', maxclass='newobj', numinlets=1, numoutlets=3,
          outlettype=['bang', 'bang', ''], patching_rect=[360.0, 80.0, 70.0, 22.0],
          text='t b b 1', varname='an_boot')
    mkbox(bl, id='obj-26', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['bang'],
          patching_rect=[360.0, 120.0, 70.0, 22.0], text='metro 33', varname='an_metro')
    mkbox(bl, id='obj-27', maxclass='newobj', numinlets=1, numoutlets=4,
          outlettype=['', '', '', ''], patching_rect=[360.0, 160.0, 80.0, 22.0],
          text='transport', varname='an_transport')
    mkbox(bl, id='obj-28', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[360.0, 200.0, 50.0, 22.0], text='/ 480.', varname='an_ticks2beats')
    mkbox(bl, id='obj-29', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[360.0, 230.0, 110.0, 22.0], text='prepend songpos',
          varname='an_pp_songpos')
    mkbox(bl, id='obj-30', maxclass='newobj', numinlets=1, numoutlets=3,
          outlettype=['', '', ''], patching_rect=[490.0, 80.0, 110.0, 22.0],
          text='live.path live_set', varname='an_livepath')
    mkbox(bl, id='obj-31', maxclass='newobj', numinlets=2, numoutlets=2, outlettype=['', ''],
          patching_rect=[490.0, 120.0, 150.0, 22.0], text='live.observer is_playing',
          varname='an_obs_play')
    mkbox(bl, id='obj-32', maxclass='newobj', numinlets=2, numoutlets=2, outlettype=['', ''],
          patching_rect=[490.0, 160.0, 150.0, 22.0], text='live.observer tempo',
          varname='an_obs_tempo')
    mkbox(bl, id='obj-34', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[490.0, 200.0, 120.0, 22.0], text='prepend transport',
          varname='an_pp_transport')
    mkbox(bl, id='obj-35', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[490.0, 230.0, 100.0, 22.0], text='prepend tempo',
          varname='an_pp_tempo')

    mkline(bl, 'obj-23', 0, 'obj-25', 0)
    mkline(bl, 'obj-25', 2, 'obj-26', 0)      # "1" -> start metro
    mkline(bl, 'obj-25', 1, 'obj-30', 0)      # b  -> resolve live.path
    mkline(bl, 'obj-25', 0, 'obj-31', 0)      # b  -> bang is_playing observer
    mkline(bl, 'obj-25', 0, 'obj-32', 0)      # b  -> bang tempo observer
    mkline(bl, 'obj-30', 0, 'obj-31', 1)      # live_set id -> observer target
    mkline(bl, 'obj-30', 0, 'obj-32', 1)
    mkline(bl, 'obj-26', 0, 'obj-27', 0)      # metro -> bang transport
    mkline(bl, 'obj-26', 0, SUB, 0)           # metro -> jsui bang() -> redraw (patch-driven anim clock)
    mkline(bl, 'obj-27', 0, 'obj-28', 0)      # ticks -> / 480.
    mkline(bl, 'obj-28', 0, 'obj-29', 0)
    mkline(bl, 'obj-29', 0, SUB, 0)
    mkline(bl, 'obj-31', 0, 'obj-34', 0)
    mkline(bl, 'obj-34', 0, SUB, 0)
    mkline(bl, 'obj-32', 0, 'obj-35', 0)
    mkline(bl, 'obj-35', 0, SUB, 0)

    # ---- cross-device voice bus: notes forwarded from ANIMIDIFeed devices on other tracks
    # ANIMIDI_NOTE payload = exactly 3 ints (pitch vel trackIdx), one message per note.
    mkbox(bl, id='obj-40', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[660.0, 80.0, 130.0, 22.0], text='receive ANIMIDI_NOTE',
          varname='an_bus_rx')
    mkbox(bl, id='obj-41', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[660.0, 110.0, 110.0, 22.0], text='prepend busnote',
          varname='an_bus_prep')
    mkline(bl, 'obj-40', 0, 'obj-41', 0)
    mkline(bl, 'obj-41', 0, SUB, 0)

    return bl


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    appversion = P['appversion']

    boxes, lines = build_top(appversion)
    P['boxes'] = boxes
    P['lines'] = lines

    params = {'obj-20': ['Abrir', 'Abrir', 0]}
    for i, (ln, sn, cid, _mc, _s, _k) in enumerate(CTRL):
        params['%s::%s' % (SUB, cid)] = [ln, sn, i + 1]
    banks = {}
    for bi, (bname, plist) in enumerate(BANKS):
        banks[str(bi)] = {'index': bi, 'name': bname,
                          'parameters': plist + ['-'] * (8 - len(plist))}
    params['parameterbanks'] = banks
    params['inherited_shortname'] = 1
    P['parameters'] = params

    P['dependency_cache'] = [{'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1}]
    P['rect'] = [140.0, 140.0, 480.0, 360.0]
    P['openinpresentation'] = 1

    # ---- self-checks (same class of trap tools/check_structure.py enforces) ------------
    all_names = ['Abrir'] + [c[0] for c in CTRL]

    def check_patcher(pp, where):
        by_id = {}
        for b in pp.get('boxes', []):
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
        for b in pp.get('boxes', []):
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

    print('ANIMIDI.amxd  (Music Animation Machine scrolling bar-graph score)')
    print('  top boxes : %d   sub boxes: %d' % (n_top, n_sub))
    print('  top lines : %d   sub lines: %d' % (len(P['lines']), len(subbox['patcher']['lines'])))
    print('  params (%d): %s' % (len(all_names), ', '.join(all_names)))
    print('  banks     : %s' % ' | '.join('%s[%d]' % (n, len(p)) for n, p in BANKS))
    print('  js dep    : %s   (bootpath %s)' % (JS, BOOT))
    print('  amxdtype  : %s (untouched = MIDI effect)'
          % P.get('project', {}).get('amxdtype'))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    print('  backup    : %s.before' % os.path.basename(DEVICE))
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    assert len(back['boxes']) == n_top
    bb = next(b['box'] for b in back['boxes'] if b['box']['id'] == SUB)
    assert bb.get('patcher') and len(bb['patcher']['boxes']) == n_sub, 'subpatcher lost on roundtrip'
    assert back['dependency_cache'][0]['name'] == JS
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/ANIMIDI.amxd')


main()
