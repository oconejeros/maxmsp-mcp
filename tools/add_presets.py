"""Add the Presets page, and the one cord that makes a recall audible.

    python tools/add_presets.py            dry run, writes nothing
    python tools/add_presets.py --apply    do it

Three buttons and a slot number. The interesting part is not on this page: it is the `initui` tag
appended to fs2_echo, wired to the three init messages the device already sends itself when a Live
set opens. Setting a parameter through the Live API changes what a control DISPLAYS without firing
its outlet, so without that cord a recall would move all 183 dials and leave the engine playing
what it was playing before.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
MERGED = os.path.join('forteseq', 'fs2pages.maxpat')
PITCH = 150.0
PAGE = 9
LABEL = 'Presets'

SLOT_ANN = (
    'En cual de los ocho slots trabajan Guardar, Cargar y Borrar. El slot mismo no entra en '
    'ningun preset: si entrara, cargar uno te moveria el slot y el click siguiente iria a parar a '
    'otro lado.')
SAVE_ANN = (
    'Lee el valor de todos los parametros del device y los escribe en el slot y en el archivo, en '
    'el acto. Quedan afuera Run, Bus, Trig, Pagina y Slot. Run es el transporte, y un preset que '
    'arranca o para la secuencia es un preset que no podes escuchar; Bus es una direccion y no un '
    'sonido; los otros son donde estas mirando y el boton que estas por apretar.')
LOAD_ANN = (
    'Pone esos valores de vuelta y despues le pide a los controles que hablen. Esa segunda mitad '
    'es todo el truco: escribir un parametro por la API de Live cambia lo que el control MUESTRA '
    'pero no dispara su salida, asi que el motor no se enteraria de nada. Es el mismo camino que '
    'corre solo cuando abris el set. Un slot guardado por una version anterior carga igual: los '
    'nombres que este device ya no tiene se saltean, y el resto entra.')
CLEAR_ANN = 'Vacia el slot y reescribe el archivo.'
LIST_ANN = 'Que slots tienen algo. Un guion es un slot vacio.'
NOTE = ('Los ocho slots viven en forteseq2_presets.txt, al lado del .amxd, y no adentro del set '
        'de Live. Eso los hace tuyos y no de la cancion: los mismos ocho te siguen a cualquier '
        'set, igual que los favoritos, y varias instancias del device comparten el archivo. Se '
        'escribe en cada Guardar y en cada Borrar, y se lee al cargar el device.')

BUTTONS = [
    ('Guardar', 54.0, 64.0, 'storepreset', 'pr_save', SAVE_ANN),
    ('Cargar', 124.0, 64.0, 'recallpreset', 'pr_load', LOAD_ANN),
    ('Borrar', 194.0, 64.0, 'clearpreset', 'pr_clear', CLEAR_ANN),
]


def main():
    apply_it = '--apply' in sys.argv
    pg = json.load(open(MERGED, encoding='utf-8'))['patcher']
    pb = {b['box']['id']: b['box'] for b in pg['boxes']}
    nxt = [max(int(i.split('-')[1]) for i in pb)]

    def fresh():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    xof = lambda i: pb[i]['patching_rect'][0]
    ins = sorted([i for i, b in pb.items() if b['maxclass'] == 'inlet'], key=xof)
    IN0, IN_ECHO = ins[0], ins[1]
    OUT0 = sorted([i for i, b in pb.items() if b['maxclass'] == 'outlet'], key=xof)[0]
    PY0, QY0 = PAGE * PITCH, 200.0 + PAGE * 700.0
    add, wire, params = [], [], {}

    def box(**kw):
        b = dict(kw)
        b.setdefault('id', fresh())
        add.append({'box': b})
        return b['id']

    def link(a, c, ao=0, ci=0):
        wire.append({'patchline': {'source': [a, ao], 'destination': [c, ci]}})

    def comment(text, x, y, w, h, qx, qy, **kw):
        return box(maxclass='comment', numinlets=1, numoutlets=0, text=text, presentation=1,
                   presentation_rect=[x, PY0 + y, w, h], patching_rect=[qx, qy, w, h], **kw)

    # Only the Slot number hangs off the init chain. The three buttons are momentary, and a device
    # that pressed Guardar for you every time a Live set opened would be a device that quietly
    # overwrote a slot on load.
    init = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''], varname='pr_init',
               patching_rect=[20.0, QY0, 70.0, 22.0], text='outputvalue')
    link(IN0, init)

    comment('Slot', 0.0, 0.0, 44.0, 18.0, 20.0, QY0 + 40.0)
    slot = box(maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
               parameter_enable=1, varname='pr_slot', annotation=SLOT_ANN, presentation=1,
               presentation_rect=[0.0, PY0 + 19.0, 44.0, 15.0],
               patching_rect=[20.0, QY0 + 70.0, 44.0, 15.0],
               saved_attribute_attributes={'valueof': {
                   'parameter_longname': 'Slot', 'parameter_shortname': 'Slot',
                   'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_modmode': 4,
                   'parameter_mmin': 1.0, 'parameter_mmax': 8.0,
                   'parameter_initial': [1], 'parameter_initial_enable': 1}})
    p = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
            text='prepend setpresetslot', patching_rect=[20.0, QY0 + 110.0, 150.0, 22.0])
    link(init, slot)
    link(slot, p)
    link(p, OUT0)
    params[slot] = ['Slot', 'Slot', 0]

    for n, (lab, x, w, verb, var, ann) in enumerate(BUTTONS):
        bid = box(maxclass='live.text', numinlets=1, numoutlets=2, outlettype=['', ''], mode=1,
                  text=lab, varname=var, parameter_enable=0, annotation=ann, presentation=1,
                  presentation_rect=[x, PY0 + 19.0, w, 18.0],
                  patching_rect=[200.0 + n * 200.0, QY0 + 70.0, w, 18.0])
        s = box(maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''], text='sel 1',
                patching_rect=[200.0 + n * 200.0, QY0 + 110.0, 50.0, 22.0])
        m = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''], text=verb,
                patching_rect=[200.0 + n * 200.0, QY0 + 145.0, 110.0, 22.0])
        link(bid, s)
        link(s, m)
        link(m, OUT0)

    # Which slots are filled. The engine resends this on every store and clear, so the readout
    # cannot drift out of step with the file.
    comment('Llenos', 0.0, 42.0, 54.0, 18.0, 20.0, QY0 + 190.0)
    lst = comment('- - - - - - - -', 56.0, 42.0, 202.0, 18.0, 120.0, QY0 + 230.0,
                  varname='pr_list', annotation=LIST_ANN)
    rt = box(maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
             varname='pr_echo', text='route presetslots',
             patching_rect=[120.0, QY0 + 190.0, 130.0, 22.0])
    st = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''], text='prepend set',
             patching_rect=[120.0, QY0 + 210.0, 90.0, 22.0])
    link(IN_ECHO, rt)
    link(rt, st)
    link(st, lst)

    comment(NOTE, 264.0, 2.0, 252.0, 130.0, 700.0, QY0 + 40.0, varname='pr_nota')

    pg['boxes'].extend(add)
    pg['lines'].extend(wire)
    pg['parameters'].update(params)
    h = max(b['box']['presentation_rect'][1] + b['box']['presentation_rect'][3]
            for b in add if b['box'].get('presentation')) - PY0
    wmax = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
               for b in add if b['box'].get('presentation'))
    print('pagina %s: %d cajas, %d cords, %d parametros, %.0f x %.0f (la ventana son 516 x 142)'
          % (LABEL, len(add), len(wire), len(params), wmax, h))
    assert h <= 142.0 and wmax <= 516.0, (h, wmax)

    # ---- the parent --------------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}
    BP = bv['fs2_pages']
    tab = bx[bv['fs2_pagina']]['saved_attribute_attributes']['valueof']
    assert LABEL not in tab['parameter_enum'], 'ya esta puesta'
    tab['parameter_enum'] = tab['parameter_enum'] + [LABEL]
    tab['parameter_mmax'] = len(tab['parameter_enum']) - 1
    selp = bx[bv['fs2_pagina_sel']]
    selp['text'] = 'sel ' + ' '.join(str(k) for k in range(len(tab['parameter_enum'])))
    selp['numoutlets'] = len(tab['parameter_enum']) + 1
    selp['outlettype'] = [''] * selp['numoutlets']
    this = [i for i, b in bx.items() if b.get('text') == 'thispatcher'][0]
    nid = [max(int(i.split('-')[1]) for i in bx)]

    def pfresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    mid = pfresh()
    P['boxes'].append({'box': {
        'id': mid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [300.0 + PAGE * 200.0, 785.0, 190.0, 22.0],
        'text': 'script sendbox fs2_pages offset 0 %d' % int(-PAGE * PITCH)}})
    P['lines'].append({'patchline': {'source': [selp['id'], PAGE], 'destination': [mid, 0]}})
    P['lines'].append({'patchline': {'source': [mid, 0], 'destination': [this, 0]}})

    # ---- initui: what makes a recall audible ---------------------------------------------------
    # The tag goes at the END of the route args on purpose. Every existing cord out of fs2_echo
    # refers to an outlet by index, so appending leaves all of them where they are, while
    # inserting anywhere else would silently move nineteen connections one place to the right.
    echo = bx[bv['fs2_echo']]
    assert 'initui' not in echo['text']
    tags = echo['text'].split()
    echo['text'] = echo['text'] + ' initui'
    echo['numoutlets'] += 1
    echo['outlettype'] = [''] * echo['numoutlets']
    out_initui = len(tags) - 1        # route's first arg is outlet 0, so tag k-1 of the split
    trig = pfresh()
    P['boxes'].append({'box': {
        'id': trig, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 3,
        'outlettype': ['bang', 'bang', 'bang'], 'varname': 'fs2_initui',
        'patching_rect': [2400.0, 3220.0, 80.0, 22.0], 'text': 't b b b'}})
    P['lines'].append({'patchline': {'source': [echo['id'], out_initui], 'destination': [trig, 0]}})
    # trigger fires right to left, so the pages go first and the top row last: Sub is set before
    # Rate reads it. Nothing here actually depends on that order -- the sub-clock re-bangs Rate
    # whenever it moves -- but an order you can name beats an order you would have to re-derive.
    for out, target in [(2, 'fs2_strip_init'), (1, 'fs2_harm_init'), (0, 'fs2_init')]:
        P['lines'].append({'patchline': {'source': [trig, out], 'destination': [bv[target], 0]}})

    PP = P['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    taken = {v[0] for k, v in PP.items() if k not in meta}
    taken |= {v['parameter_longname'] for v in PP['parameter_overrides'].values()}
    clash = sorted(v[0] for v in params.values() if v[0] in taken)
    assert not clash, 'esos nombres ya existen: %s' % clash
    for pid, val in params.items():
        PP['%s::%s' % (BP, pid)] = val
    assert not [(b['name'], p) for b in PP['parameterbanks'].values() for p in b['parameters']
                if p != '-' and p not in taken | {v[0] for v in params.values()}]
    print('padre: pestanas %s' % tab['parameter_enum'])
    print('       fs2_echo: %d args, initui en la salida %d' % (len(tags), out_initui))
    print('       top-level %d, anidados %d, total %d'
          % (len([k for k in PP if k not in meta and '::' not in k]),
             len([k for k in PP if '::' in k]), len([k for k in PP if k not in meta])))

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    with open(MERGED, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escritos %s y %s' % (MERGED, DEVICE))


main()
