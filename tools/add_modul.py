"""Add the Modul page: four modulators, one destination each.

    python tools/add_modul.py            dry run, writes nothing
    python tools/add_modul.py --apply    do it

One row per modulator and one column per property, rather than four little panels. The reason is
the same as the one behind the Ritmo page: what you choose here you choose by comparing the four
against each other -- two cycles that do not divide one another, one shape sweeping while another
holds -- and a layout that makes you read them one at a time hides exactly the relationship you
are trying to set up.

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
PAGE = 8
LABEL = 'Modul'
MODS = 4

SHAPES = ['Seno', 'Triang', 'Diente', 'Cuadr', 'Azar', 'Paseo']
DESTS = ['-', 'Raiz', 'Octava', 'Vel', 'Largo', 'Silencio', 'Swing', 'Rasgueo', 'Ratchet', 'Grado']

COLS = [
    # label, x, width, kind, spec, verb, annotation
    ('Forma', 24.0, 72.0, 'menu', SHAPES, 'setmodshape',
     'La curva que recorre el modulador. Seno y Triang barren; Diente vuelve de golpe al empezar '
     'cada ciclo; Cuadr salta entre los dos extremos y no pasa por el medio; Azar saca un valor '
     'nuevo por ciclo y lo sostiene; Paseo se mueve un poco desde donde ya estaba, asi que se '
     'aleja de a poco en vez de saltar, y rebota en los bordes en lugar de quedarse pegado a '
     'ellos.'),
    ('Ciclo', 100.0, 42.0, 'num', (1.0, 64.0, 8), 'setmodcycle',
     'Cuantos PASOS dura un ciclo, no cuantos milisegundos. Ocho pasos son ocho pasos a cualquier '
     'tempo y siempre caen en la reja, mientras que un LFO en hertz se corre contra ella. Para '
     'Azar y Paseo es cuanto sostiene cada valor. Ciclos que no se dividen entre si -- 8 contra '
     '5 -- tardan 40 pasos en volver a coincidir, que es como se consigue que la modulacion no '
     'se oiga como un bucle.'),
    ('Prof', 146.0, 46.0, 'num', (-100.0, 100.0, 0), 'setmoddepth',
     'Cuanto abre el barrido, y hacia donde. Todas las formas son bipolares, asi que el dial del '
     'destino queda en el CENTRO del barrido: en 0 el destino vale exactamente lo que dice su '
     'dial, y subir la profundidad lo abre parejo hacia los dos lados. Una profundidad negativa '
     'da vuelta la forma, que es como se enfrentan dos moduladores puestos en el mismo destino.'),
    ('Fase', 196.0, 42.0, 'num', (0.0, 100.0, 0), 'setmodphase',
     'Desde que punto del ciclo arranca, en porcentaje. Es lo unico que separa a dos moduladores '
     'con la misma forma y el mismo ciclo: en 25 quedan en cuadratura, en 50 opuestos. Para Azar '
     'y Paseo corre tambien el momento en que sacan el valor nuevo, asi que dos de ellos dejan '
     'de saltar juntos.'),
    ('Dest', 242.0, 80.0, 'menu', DESTS, 'setmoddest',
     'Que mueve este modulador. Ninguno escribe el parametro: el dial sigue diciendo lo que vos '
     'pusiste y el modulador suma encima al momento de leerlo, asi que apagarlo devuelve el '
     'numero exacto que estas viendo. Silencio y Ratchet arrancan en la punta de su rango, asi '
     'que conviene bajar el dial a mitad de camino antes de modularlos o la mitad del barrido se '
     'pierde contra el tope. Grado corre el grado que se lee del set: se escucha en Arpegio y con '
     'Indep, no en Acordes. Swing, Rasgueo y Ratchet necesitan Sub 2 o mas para tener donde caer.'),
]
NOTE = ('Cuatro moduladores, uno por fila. Dos apuntados al mismo destino se suman. Ninguno '
        'escribe el parametro: el dial sigue diciendo lo tuyo y esto suma encima al leer, asi '
        'que Prof en 0 devuelve el numero exacto. Avanzan por paso, no por reloj: con la '
        'secuencia detenida no se mueven.')


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

    init = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''], varname='md_init',
               patching_rect=[20.0, QY0, 70.0, 22.0], text='outputvalue')
    link(IN0, init)

    for lab, x, w, _, _, _, _ in COLS:
        box(maxclass='comment', numinlets=1, numoutlets=0, text=lab, presentation=1,
            presentation_rect=[x, PY0, w, 18.0],
            patching_rect=[20.0 + x, QY0 + 40.0, w, 18.0])

    for k in range(1, MODS + 1):
        y = PY0 + 20.0 + (k - 1) * 25.0
        qy = QY0 + 80.0 + (k - 1) * 26.0
        box(maxclass='comment', numinlets=1, numoutlets=0, text='M%d' % k, presentation=1,
            presentation_rect=[0.0, y + 1.0, 24.0, 18.0],
            patching_rect=[20.0, qy, 24.0, 18.0])
        for c, (lab, x, w, kind, spec, verb, ann) in enumerate(COLS):
            name = 'M%d %s' % (k, lab)
            vo = {'parameter_longname': name, 'parameter_shortname': name,
                  'parameter_initial_enable': 1}
            if kind == 'num':
                lo, hi, ini = spec
                vo.update({'parameter_mmin': lo, 'parameter_mmax': hi, 'parameter_modmode': 4,
                           'parameter_type': 1, 'parameter_unitstyle': 0,
                           'parameter_initial': [ini]})
                cls, no, ot, h, dy = 'live.numbox', 2, ['', 'float'], 15.0, 2.0
            else:
                vo.update({'parameter_enum': spec, 'parameter_mmax': len(spec) - 1,
                           'parameter_modmode': 0, 'parameter_type': 2, 'parameter_unitstyle': 9,
                           'parameter_initial': [0]})
                cls, no, ot, h, dy = 'live.menu', 3, ['', '', 'float'], 18.0, 0.0
            cid = box(maxclass=cls, numinlets=1, numoutlets=no, outlettype=ot, parameter_enable=1,
                      varname='md_m%d_%s' % (k, lab.lower()), annotation=ann, presentation=1,
                      presentation_rect=[x, y + dy, w, h],
                      patching_rect=[20.0 + x, qy, w, h],
                      saved_attribute_attributes={'valueof': vo})
            p = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                    text='prepend %s %d' % (verb, k),
                    patching_rect=[20.0 + c * 200.0, QY0 + 220.0 + k * 30.0, 190.0, 22.0])
            link(init, cid)
            link(cid, p)
            link(p, OUT0)
            params[cid] = [name, name, 0]

    box(maxclass='comment', numinlets=1, numoutlets=0, varname='md_nota', text=NOTE,
        presentation=1, presentation_rect=[328.0, PY0 + 2.0, 188.0, 130.0],
        patching_rect=[900.0, QY0 + 40.0, 188.0, 130.0])

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
    taken = {v[0] for k, v in PP.items() if k not in meta}
    taken |= {v['parameter_longname'] for v in PP['parameter_overrides'].values()}
    clash = sorted(v[0] for v in params.values() if v[0] in taken)
    assert not clash, 'esos nombres ya existen: %s' % clash
    for pid, val in params.items():
        PP['%s::%s' % (BP, pid)] = val
    assert not [(b['name'], p) for b in PP['parameterbanks'].values() for p in b['parameters']
                if p != '-' and p not in taken | {v[0] for v in params.values()}]
    print('padre: pestanas %s' % tab['parameter_enum'])
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
