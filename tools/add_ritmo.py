"""Add the Ritmo page: one Euclidean pattern per voice.

The accent grid decides how loud a voice speaks. This decides whether it speaks at all. Each
voice carries its own E(k, n) -- Larg is n, Puls is k, Gir turns it -- and is silent on the cells
that are not onsets.

    python tools/add_ritmo.py            dry run, writes nothing
    python tools/add_ritmo.py --apply    do it

It is a page and not three more columns in the voice strip for two reasons. The strip has no
width left, and more importantly you choose these numbers by looking at all four voices at once:
lengths that share no factor are the entire point, and 3 / 5 / 7 / 8 is a thing you see rather
than a thing you compute one strip at a time.

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
PAGE = 5
LABEL = 'Ritmo'
VOICES = 4

COLS = [
    # label, x, width, verb, min, max, initial, annotation
    ('Larg', 40.0, 44.0, 'setvoiceeuclen', 0.0, 16.0, 0,
     'Largo del patron de esta voz, en pasos. En 0 no hay patron y la voz suena en cada paso '
     'que le toca, que es lo que hacia antes de que esto existiera. Los largos que no comparten '
     'divisor son el punto: 3 contra 5 contra 7 contra 8 recien vuelve a alinearse a los 840 '
     'pasos, y hasta ahi cada paso es una combinacion distinta de quien habla.'),
    ('Puls', 100.0, 44.0, 'setvoiceeuck', 0.0, 16.0, 1,
     'Cuantos golpes se reparten en esos pasos, lo mas parejo que el largo permita. E(3,8) es el '
     'tresillo cubano y E(5,8) el cinquillo. Con Puls en 0 la voz calla; con Puls igual o mayor '
     'que Larg suena en todos los pasos.'),
    ('Gir', 160.0, 44.0, 'setvoiceeucrot', 0.0, 15.0, 0,
     'Desde que celda arranca el patron. Es lo que separa dos voces que llevan el mismo ritmo: '
     'el mismo E(3,8) girado 2 no cae nunca junto al sin girar.'),
]
NOTE = ('Cada voz lleva su propio E(Puls, Larg). La reja de acentos decide con cuanta fuerza '
        'habla una voz; esto decide si habla. Una celda apagada es una compuerta, no una pausa: '
        'el cursor de la voz igual avanza, asi que la voz guarda su lugar en la armonia en vez '
        'de tocar una melodia mas lenta. Con Indep encendido el patron se lee contra los pasos '
        'que el divisor le entrega a la voz, no contra el reloj, para que un divisor y un patron '
        'no puedan caer en celdas distintas y callarla para siempre.')


def main():
    apply_it = '--apply' in sys.argv
    pg = json.load(open(MERGED, encoding='utf-8'))['patcher']
    pb = {b['box']['id']: b['box'] for b in pg['boxes']}
    nxt = [max(int(i.split('-')[1]) for i in pb)]

    def fresh():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    xof = lambda i: pb[i]['patching_rect'][0]
    IN0 = sorted([i for i, b in pb.items() if b['maxclass'] == 'inlet'], key=xof)[0]
    OUT0 = sorted([i for i, b in pb.items() if b['maxclass'] == 'outlet'], key=xof)[0]
    PY0, QY0 = PAGE * PITCH, 200.0 + PAGE * 700.0
    add, wire, params = [], [], {}

    def box(**kw):
        b = dict(kw)
        b.setdefault('id', fresh())
        add.append({'box': b})
        return b['id']

    def link(a, c):
        wire.append({'patchline': {'source': [a, 0], 'destination': [c, 0]}})

    init = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''], varname='rt_init',
               patching_rect=[20.0, QY0, 70.0, 22.0], text='outputvalue')
    link(IN0, init)

    for lab, x, w, _, _, _, _, _ in COLS:
        box(maxclass='comment', numinlets=1, numoutlets=0, text=lab, presentation=1,
            presentation_rect=[x, PY0, w, 18.0],
            patching_rect=[20.0 + x, QY0 + 40.0, w, 18.0])
    for v in range(1, VOICES + 1):
        y = PY0 + v * 22.0 - 3.0
        box(maxclass='comment', numinlets=1, numoutlets=0, text='V%d' % v, presentation=1,
            presentation_rect=[0.0, y, 30.0, 18.0],
            patching_rect=[20.0, QY0 + 80.0 + v * 22.0, 30.0, 18.0])
        for lab, x, w, verb, lo, hi, ini, ann in COLS:
            name = 'V%d %s' % (v, lab)
            nid = box(maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
                      parameter_enable=1, varname='rt_v%d_%s' % (v, lab.lower()), annotation=ann,
                      presentation=1, presentation_rect=[x, y + 1.0, w, 15.0],
                      patching_rect=[20.0 + x, QY0 + 80.0 + v * 22.0, w, 15.0],
                      saved_attribute_attributes={'valueof': {
                          'parameter_longname': name, 'parameter_shortname': name,
                          'parameter_type': 1, 'parameter_initial': [ini],
                          'parameter_initial_enable': 1, 'parameter_mmin': lo,
                          'parameter_mmax': hi, 'parameter_modmode': 4,
                          'parameter_unitstyle': 0}})
            p = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                    text='prepend %s %d' % (verb, v),
                    patching_rect=[20.0 + x * 4.0, QY0 + 200.0 + v * 30.0, 220.0, 22.0])
            link(init, nid)
            link(nid, p)
            link(p, OUT0)
            params[nid] = [name, name, 0]

    box(maxclass='comment', numinlets=1, numoutlets=0, varname='rt_nota', text=NOTE,
        presentation=1, presentation_rect=[220.0, PY0 + 2.0, 292.0, 110.0],
        patching_rect=[600.0, QY0 + 40.0, 292.0, 110.0])

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
    mid = 'obj-%d' % (max(int(i.split('-')[1]) for i in bx) + 1)
    P['boxes'].append({'box': {
        'id': mid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [300.0 + PAGE * 200.0, 785.0, 190.0, 22.0],
        'text': 'script sendbox fs2_pages offset 0 %d' % int(-PAGE * PITCH)}})
    P['lines'].append({'patchline': {'source': [selp['id'], PAGE], 'destination': [mid, 0]}})
    P['lines'].append({'patchline': {'source': [mid, 0], 'destination': [this, 0]}})

    PP = P['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    # The four voice strips are four instances of one bpatcher, so the registry holds the literal
    # `V#1 Div` four times over and the real names live in parameter_overrides. Only the names
    # this page adds have to be new.
    taken = {v[0] for k, v in PP.items() if k not in meta}
    taken |= {v['parameter_longname'] for v in PP['parameter_overrides'].values()}
    clash = sorted(v[0] for v in params.values() if v[0] in taken)
    assert not clash, 'esos nombres ya existen: %s' % clash
    for pid, val in params.items():
        PP['%s::%s' % (BP, pid)] = val
    names = [v[0] for k, v in PP.items() if k not in meta]
    assert not [(b['name'], p) for b in PP['parameterbanks'].values()
                for p in b['parameters'] if p != '-' and p not in set(names)]
    print('padre: pestanas %s | top-level %d, anidados %d, total %d'
          % (tab['parameter_enum'], len([k for k in PP if k not in meta and '::' not in k]),
             len([k for k in PP if '::' in k]), len(names)))

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
