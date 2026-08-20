"""Add the Camino page: how the harmony chooses where to go next.

Four controls over the three rules that landed in be95e60. They are on a page of their own and
not scattered among the pages that own the parameters they interact with, because what matters
about them is that they OVERRIDE each other -- Prog beats Tension beats the plain walk -- and a
precedence you cannot see all at once is a precedence you will misremember.

    python tools/add_camino.py            dry run, writes nothing
    python tools/add_camino.py --apply    do it

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
PAGE = 6
LABEL = 'Camino'

CTRL = [
    ('Enlace', 'fs2_enlace', 'Enlace', 0.0, 44.0, 'num', (0.0, 6.0, 0), 'setlink',
     'Cuantas notas, como minimo, tiene que compartir el set que viene con el que suena. Es el '
     'camino armonico clasico: en 0 el catalogo se recorre como siempre; en 3 o 4 la armonia se '
     'mueve por tonos comunes y deja de saltar. Si en una vuelta entera nadie cumple -- un set '
     'de dos notas no puede compartir cuatro con nadie -- pasa al siguiente igual: una regla que '
     'puede congelar la secuencia es peor que una que cede.'),
    ('Tension', 'fs2_tension', 'Tension', 60.0, 44.0, 'num', (0.0, 16.0, 0), 'settension',
     'Largo del ciclo de tension, en cambios de set. En 0 no hay curva. Con 8, la armonia recorre '
     'una forma completa cada ocho cambios: en vez de tomar el que sigue, toma el set cuya '
     'consonancia mas se acerca a la que la curva pide en ese punto. Los extremos entre los que '
     'barre son los que el FILTRO deja pasar, asi que "lo mas aspero posible" quiere decir lo mas '
     'aspero que quedo en el catalogo.'),
    ('Curva', 'fs2_curva', 'Curva', 120.0, 130.0, 'tab', ['Sube', 'Baja', 'Arco'], 'settenshape',
     'La forma del ciclo. Sube: arranca consonante y se tensa. Baja: arranca tensa y afloja. '
     'Arco: va y vuelve dentro del mismo ciclo.'),
    ('Prog', 'fs2_progfav', 'Prog', 262.0, 15.0, 'tog', None, 'setfavseq',
     'Toca los favoritos en el orden en que los marcaste, y no en el del catalogo. Eso convierte '
     'una lista corta en una progresion de acordes. Manda sobre Enlace y sobre Tension, y tampoco '
     'consulta el filtro: los elegiste a mano, discutirtelos seria impertinente. Para mover uno al '
     'final de la progresion, desmarcalo y volve a marcarlo. Con la lista vacia no hace nada.'),
]
NOTE = ('Las tres reglas se pisan en este orden: Prog manda sobre Tension, y Tension sobre el '
        'recorrido normal del catalogo. Enlace se aplica a las dos ultimas pero nunca a Prog. '
        'Ninguna de las tres hace nada mientras la armonia no se mueva, asi que se escuchan sobre '
        'todo con Ritmo Arm. -- en la pagina Musical -- o con pasadas cortas.')


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

    init = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''], varname='cm_init',
               patching_rect=[20.0, QY0, 70.0, 22.0], text='outputvalue')
    link(IN0, init)

    for k, (lab, var, name, x, w, kind, spec, verb, ann) in enumerate(CTRL):
        box(maxclass='comment', numinlets=1, numoutlets=0, text=lab, presentation=1,
            presentation_rect=[x, PY0, max(w, 44.0), 18.0],
            patching_rect=[20.0 + x, QY0 + 40.0, max(w, 44.0), 18.0])
        vo = {'parameter_longname': name, 'parameter_shortname': name,
              'parameter_initial_enable': 1}
        if kind == 'num':
            lo, hi, ini = spec
            vo.update({'parameter_mmin': lo, 'parameter_mmax': hi, 'parameter_modmode': 4,
                       'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_initial': [ini]})
            cls, no, ot, h = 'live.numbox', 2, ['', 'float'], 15.0
        elif kind == 'tog':
            vo.update({'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
                       'parameter_modmode': 0, 'parameter_type': 2, 'parameter_initial': [0]})
            cls, no, ot, h = 'live.toggle', 1, [''], 15.0
        else:
            vo.update({'parameter_enum': spec, 'parameter_mmax': len(spec) - 1,
                       'parameter_modmode': 0, 'parameter_type': 2, 'parameter_unitstyle': 9,
                       'parameter_initial': [0]})
            cls, no, ot, h = 'live.tab', 3, ['', '', 'float'], 18.0
        cid = box(maxclass=cls, numinlets=1, numoutlets=no, outlettype=ot, parameter_enable=1,
                  varname=var, annotation=ann, presentation=1,
                  presentation_rect=[x, PY0 + 19.0, w, h],
                  patching_rect=[20.0 + x, QY0 + 60.0, w, h],
                  saved_attribute_attributes={'valueof': vo})
        p = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                text='prepend ' + verb,
                patching_rect=[20.0 + k * 160.0, QY0 + 120.0, 150.0, 22.0])
        link(init, cid)
        link(cid, p)
        link(p, OUT0)
        params[cid] = [name, name, 0]

    box(maxclass='comment', numinlets=1, numoutlets=0, varname='cm_nota', text=NOTE,
        presentation=1, presentation_rect=[0.0, PY0 + 44.0, 512.0, 90.0],
        patching_rect=[20.0, QY0 + 170.0, 512.0, 90.0])

    pg['boxes'].extend(add)
    pg['lines'].extend(wire)
    pg['parameters'].update(params)
    h = max(b['box']['presentation_rect'][1] + b['box']['presentation_rect'][3]
            for b in add if b['box'].get('presentation')) - PY0
    w = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
            for b in add if b['box'].get('presentation'))
    print('pagina %s: %d cajas, %d cords, %d parametros, %.0f x %.0f (ventana 516 x 142)'
          % (LABEL, len(add), len(wire), len(params), w, h))
    assert h <= 142.0 and w <= 516.0, (h, w)

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
    taken = {v[0] for k, v in PP.items() if k not in meta}
    taken |= {v['parameter_longname'] for v in PP['parameter_overrides'].values()}
    clash = sorted(v[0] for v in params.values() if v[0] in taken)
    assert not clash, 'esos nombres ya existen: %s' % clash
    for pid, val in params.items():
        PP['%s::%s' % (BP, pid)] = val
    assert not [(b['name'], p) for b in PP['parameterbanks'].values() for p in b['parameters']
                if p != '-' and p not in taken | {v[0] for v in params.values()}]
    print('padre: pestanas %s | top-level %d, anidados %d, total %d'
          % (tab['parameter_enum'], len([k for k in PP if k not in meta and '::' not in k]),
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
