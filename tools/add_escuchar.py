"""Add the Escuchar page, the MIDI tap, and the FORTESEQ_SET bus.

Two things that were never true of this device before. It can be played -- hold a chord and the
engine identifies the Tn-class you are holding and takes it, in the key you played it in -- and
several engines can share one harmony, which closes the gap named in the v2 architecture note:
emitVoices() drives every voice from a single setIndex, so a second device was always a second
harmony rather than more voices of the same one.

    python tools/add_escuchar.py            dry run, writes nothing
    python tools/add_escuchar.py --apply    do it

Three wirings in the parent:

  * midiin already exists, feeding the template's thru cord to midiout. A midiparse hangs off it
    without touching that: outlet 0 is `pitch velocity` for note messages, and `prepend noteheard`
    hands both to the js, which keeps a count per pitch class so octave doublings behave.
  * fs2_echo grows one argument, `setbcast`, and that outlet goes straight to send FORTESEQ_SET.
    The js emits it from emitSetReadouts(), which is already memoised to fire once per harmonic
    change rather than once per note.
  * receive FORTESEQ_SET -> prepend followset -> js. An engine that follows never broadcasts, and
    followset() drops a message naming the set it is already on, so a device with both switches
    up cannot feed itself.

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
PAGE = 7
LABEL = 'Escuchar'
BUS_NAME = 'FORTESEQ_SET'
TAG = 'setbcast'

A_ESC = ('Off: el device no escucha. Sigue: mientras sostengas notas, la armonia es la clase que '
         'estas tocando, en el tono en que la tocaste, y la secuencia se queda quieta; al soltar '
         'vuelve exactamente donde estaba. Latch: la agarra y se queda con ella, y la secuencia '
         'sigue desde ahi. Cualquier acorde sirve: el catalogo tiene las 351 clases Tn, que por '
         'doce transposiciones son los 4095 conjuntos posibles, asi que identificar es una '
         'busqueda que no puede fallar.')
A_PAN = ('Suelta la mano a la fuerza. Los note-off no siempre llegan -- cambiaste de modo con el '
         'acorde apretado, o rearmaste la pista -- y sin esto el device se queda creyendo que '
         'seguis tocando.')
A_EMI = ('Difunde por que clase va este device, en su bus. Solo viaja CUAL set: la raiz, la '
         'octava, el voicing y el registro quedan de cada uno, porque dos motores en registros o '
         'tonos distintos sobre una misma armonia es justamente para lo que sirven dos.')
A_SEG = ('Toma la armonia del bus en vez de elegirla. Con esto encendido el reloj de este device '
         'ya no mueve el catalogo: manda el que difunde. Un motor que sigue nunca difunde, asi '
         'que no hay lazo posible.')
NOTE = ('Escuchar manda sobre todo lo de la pagina Camino: una mano en el teclado ES la armonia. '
        'Seguir tambien. Emitir y Seguir usan el mismo Bus que las notas, asi que dos motores en '
        'el bus 1 comparten armonia y dos en buses distintos se ignoran.')


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

    def link(a, c, ao=0):
        wire.append({'patchline': {'source': [a, ao], 'destination': [c, 0]}})

    def label(text, x, w, y=0.0):
        box(maxclass='comment', numinlets=1, numoutlets=0, text=text, presentation=1,
            presentation_rect=[x, PY0 + y, w, 18.0],
            patching_rect=[20.0 + x, QY0 + 40.0 + y, w, 18.0])

    def control(cls, var, name, x, w, h, vo, ann, verb):
        no, ot = (3, ['', '', 'float']) if cls != 'live.toggle' else (1, [''])
        cid = box(maxclass=cls, numinlets=1, numoutlets=no, outlettype=ot, parameter_enable=1,
                  varname=var, annotation=ann, presentation=1,
                  presentation_rect=[x, PY0 + 19.0, w, h],
                  patching_rect=[20.0 + x, QY0 + 60.0, w, h],
                  saved_attribute_attributes={'valueof': vo})
        p = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                text='prepend ' + verb,
                patching_rect=[20.0 + x * 2.0, QY0 + 120.0, 150.0, 22.0])
        link(init, cid)
        link(cid, p)
        link(p, OUT0)
        params[cid] = [name, name, 0]
        return cid

    init = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''], varname='es_init',
               patching_rect=[20.0, QY0, 70.0, 22.0], text='outputvalue')
    link(IN0, init)

    label('Escuchar', 0.0, 70.0)
    control('live.tab', 'fs2_escuchar', 'Escuchar', 0.0, 160.0, 18.0,
            {'parameter_enum': ['Off', 'Sigue', 'Latch'], 'parameter_mmax': 2,
             'parameter_modmode': 0, 'parameter_type': 2, 'parameter_unitstyle': 9,
             'parameter_initial': [0], 'parameter_initial_enable': 1,
             'parameter_longname': 'Escuchar', 'parameter_shortname': 'Escuchar'},
            A_ESC, 'setlisten')
    tog = {'parameter_enum': ['off', 'on'], 'parameter_mmax': 1, 'parameter_modmode': 0,
           'parameter_type': 2, 'parameter_initial': [0], 'parameter_initial_enable': 1}
    label('Emitir', 176.0, 50.0)
    control('live.toggle', 'fs2_emitir', 'Emitir', 176.0, 15.0, 15.0,
            dict(tog, parameter_longname='Emitir', parameter_shortname='Emitir'),
            A_EMI, 'setbroadcast')
    label('Seguir', 232.0, 50.0)
    control('live.toggle', 'fs2_seguir', 'Seguir', 232.0, 15.0, 15.0,
            dict(tog, parameter_longname='Seguir', parameter_shortname='Seguir'),
            A_SEG, 'setfollow')

    # The panic button is not a Live parameter: a live.* object registers as one unless told
    # otherwise, and eight silent duplicates of one is exactly the trap the voice strip hit.
    pan = box(maxclass='live.text', numinlets=1, numoutlets=2, outlettype=['', ''], mode=1,
              text='Panic', varname='fs2_lpanic', parameter_enable=0, annotation=A_PAN,
              presentation=1, presentation_rect=[292.0, PY0 + 19.0, 56.0, 18.0],
              patching_rect=[320.0, QY0 + 60.0, 56.0, 18.0])
    sel = box(maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
              text='sel 1', patching_rect=[320.0, QY0 + 90.0, 50.0, 22.0])
    msg = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
              text='listenpanic', patching_rect=[320.0, QY0 + 120.0, 90.0, 22.0])
    link(pan, sel)
    link(sel, msg)
    link(msg, OUT0)

    box(maxclass='comment', numinlets=1, numoutlets=0, varname='es_nota', text=NOTE,
        presentation=1, presentation_rect=[0.0, PY0 + 44.0, 512.0, 76.0],
        patching_rect=[20.0, QY0 + 170.0, 512.0, 76.0])

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
    BP, GEN = bv['fs2_pages'], bv['fs2_gen']
    nx2 = [max(int(i.split('-')[1]) for i in bx)]

    def add2(**kw):
        b = dict(kw)
        b.setdefault('id', 'obj-%d' % (nx2.__setitem__(0, nx2[0] + 1) or nx2[0]))
        P['boxes'].append({'box': b})
        return b['id']

    def link2(a, ao, c, ci=0):
        P['lines'].append({'patchline': {'source': [a, ao], 'destination': [c, ci]}})

    tab = bx[bv['fs2_pagina']]['saved_attribute_attributes']['valueof']
    assert LABEL not in tab['parameter_enum'], 'ya esta puesta'
    tab['parameter_enum'] = tab['parameter_enum'] + [LABEL]
    tab['parameter_mmax'] = len(tab['parameter_enum']) - 1
    selp = bx[bv['fs2_pagina_sel']]
    selp['text'] = 'sel ' + ' '.join(str(k) for k in range(len(tab['parameter_enum'])))
    selp['numoutlets'] = len(tab['parameter_enum']) + 1
    selp['outlettype'] = [''] * selp['numoutlets']
    this = [i for i, b in bx.items() if b.get('text') == 'thispatcher'][0]
    mid = add2(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
               patching_rect=[300.0 + PAGE * 200.0, 785.0, 190.0, 22.0],
               text='script sendbox fs2_pages offset 0 %d' % int(-PAGE * PITCH))
    link2(selp['id'], PAGE, mid, 0)
    link2(mid, 0, this, 0)

    # the MIDI tap, hung off the midiin that is already there
    midiin = [i for i, b in bx.items() if b.get('text') == 'midiin']
    assert len(midiin) == 1, midiin
    parse = add2(maxclass='newobj', numinlets=1, numoutlets=8, varname='fs2_midiparse',
                 outlettype=['', '', '', '', '', '', '', ''], text='midiparse',
                 patching_rect=[900.0, 960.0, 80.0, 22.0])
    heard = add2(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                 varname='fs2_heard_prep', text='prepend noteheard',
                 patching_rect=[900.0, 1000.0, 130.0, 22.0])
    link2(midiin[0], 0, parse, 0)
    link2(parse, 0, heard, 0)
    link2(heard, 0, GEN, 0)

    # the harmony bus, out and in
    echo = bx[bv['fs2_echo']]
    args = echo['text'].split()[1:]
    assert TAG not in args, 'ya esta'
    args.append(TAG)
    echo['text'] = 'route ' + ' '.join(args)
    echo['numoutlets'] = len(args) + 1
    echo['outlettype'] = [''] * echo['numoutlets']
    snd = add2(maxclass='newobj', numinlets=1, numoutlets=0, varname='fs2_set_send',
               text='send ' + BUS_NAME, patching_rect=[1100.0, 960.0, 160.0, 22.0])
    link2(echo['id'], len(args) - 1, snd, 0)
    rcv = add2(maxclass='newobj', numinlets=0, numoutlets=1, outlettype=[''],
               varname='fs2_set_recv', text='receive ' + BUS_NAME,
               patching_rect=[1100.0, 1000.0, 170.0, 22.0])
    fol = add2(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
               varname='fs2_follow_prep', text='prepend followset',
               patching_rect=[1100.0, 1040.0, 140.0, 22.0])
    link2(rcv, 0, fol, 0)
    link2(fol, 0, GEN, 0)

    PP = P['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    taken = {v[0] for k, v in PP.items() if k not in meta}
    taken |= {v['parameter_longname'] for v in PP['parameter_overrides'].values()}
    clash = sorted(v[0] for v in params.values() if v[0] in taken)
    assert not clash, 'esos nombres ya existen: %s' % clash
    for pid, val in params.items():
        PP['%s::%s' % (BP, pid)] = val
    print('padre: pestanas %s' % tab['parameter_enum'])
    print('       route del eco: %d salidas, la nueva es %s' % (echo['numoutlets'], TAG))
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
