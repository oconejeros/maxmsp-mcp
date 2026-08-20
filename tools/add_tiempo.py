"""Add the Tiempo page and hand the clock over to the sub-clock.

The JS half of this landed in 4487734: the metro is meant to beat subDiv times per step, bang()
only calls step() on the beats that are steps, and emitNote() schedules into a ring buffer so
swing, humanize, strum and ratchet are all just offsets in sub-ticks. Nothing on the Max side
ever divided the metro, so subDiv stayed at 1 and all of it was dormant. This wires it up.

    python tools/add_tiempo.py            dry run, writes nothing
    python tools/add_tiempo.py --apply    do it

Two halves:

  * A fifth page inside fs2pages.maxpat with the nine global controls, and a second outlet on
    the page carrying the raw divisor -- because Sub is the one control on a page that has to
    reach something other than the js.

  * The clock. Libre went from `expr 60000./$f1` to `expr 60000./($f1*$f2)`; Sync's fixed `4n`
    message became six notevalues chosen by the divisor. Both paths are recomputed in a fixed
    order by [t b i i]: the cold inlet first, then the notevalue, then the bang that recomputes
    the milliseconds. Order matters here -- banging the rate before its own multiplier is set
    would compute the interval from the previous Sub.

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
PAGE = 4                                  # Tiempo is the fifth page
DIVS = [1, 2, 3, 4, 6, 8]
NOTEVALUES = ['4n', '8n', '8nt', '16n', '16nt', '32n']

A_SUB = ('Cuantas veces late el reloj por paso. Es la resolucion de todo lo demas de esta '
         'pagina: en Sub 1 no hay ningun lugar entre un paso y el siguiente, asi que Swing, '
         'Humaniz y Ratchet no tienen donde caer y no hacen nada. Sub 4 da cuatro lugares.')
A_SWING = ('50 es recto. 66 es tresillo, el pulso par cae a dos tercios del camino. 75 es un '
           'balanceo con puntillo. Solo se mueve en sub-ticks enteros, asi que cuanto mas alto '
           'el Sub, mas fino el swing.')
A_HUMAN = ('Corrimiento al azar, sorteado por nota y no por paso, asi que dos voces en el mismo '
           'paso no se mueven juntas. Esa independencia es casi todo lo que lo hace sonar a '
           'gente y no a una grilla movida.')
A_RASG = ('Sub-ticks entre una nota y la siguiente de un mismo acorde. Con 0 el acorde se '
          'ataca junto. Ojo: se mide en sub-ticks, asi que en Sub 1 un rasgueo de 2 reparte el '
          'acorde en dos pasos enteros.')
A_DIRR = 'Desde que nota se abre el acorde. Alterna cambia de sentido en cada paso.'
A_RATN = ('Cuantas veces se repite una nota del grupo normal dentro de su paso. Necesita Sub '
          'mayor que 1: las repeticiones se reparten en los sub-ticks del paso.')
A_RATA = ('Lo mismo para el grupo acento. Como la reja de 16 celdas decide que paso es acento, '
          'el redoble cae en las celdas que dibujaste y no en todas.')
A_PROB = 'Cada cuanto el ratchet realmente dispara. En 100 siempre; en 30 uno de cada tres.'
A_CAIDA = 'Cuanta velocidad pierde el redoble entre la primera repeticion y la ultima.'

# label, varname, long name, width, kind, spec, annotation
GLOBALS = [
    (0.0,   0.0, 'Sub',   'fs2_sub',     'Sub',      56.0, 'menu', [str(d) for d in DIVS], A_SUB),
    (64.0,  0.0, 'Swing', 'fs2_swing',   'Swing',    40.0, 'num',  (50.0, 75.0, 50), A_SWING),
    (112.0, 0.0, 'Human', 'fs2_human',   'Human',    44.0, 'num',  (0.0, 100.0, 0), A_HUMAN),
    (168.0, 0.0, 'Rasg',  'fs2_rasg',    'Rasg',     38.0, 'num',  (0.0, 8.0, 0), A_RASG),
    (216.0, 0.0, 'Dir R', 'fs2_dirrasg', 'Dir Rasg', 150.0, 'tab',
     ['Arriba', 'Abajo', 'Azar', 'Alt'], A_DIRR),
    (0.0,   41.0, 'Rat N', 'fs2_ratn',    'Rat N',    38.0, 'num', (1.0, 4.0, 1), A_RATN),
    (48.0,  41.0, 'Rat A', 'fs2_rata',    'Rat A',    38.0, 'num', (1.0, 4.0, 1), A_RATA),
    (96.0,  41.0, 'Prob',  'fs2_ratprob', 'Prob Rat', 40.0, 'num', (0.0, 100.0, 100), A_PROB),
    (148.0, 41.0, 'Caida', 'fs2_ratcaida', 'Caida',   40.0, 'num', (0.0, 100.0, 0), A_CAIDA),
]
VERBS = {'fs2_swing': 'setswing', 'fs2_human': 'sethumanize', 'fs2_rasg': 'setstrum',
         'fs2_dirrasg': 'setstrumdir', 'fs2_ratn': 'setratchet 0', 'fs2_rata': 'setratchet 1',
         'fs2_ratprob': 'setratchetprob', 'fs2_ratcaida': 'setratchetdecay'}


def main():
    apply_it = '--apply' in sys.argv
    pg = json.load(open(MERGED, encoding='utf-8'))['patcher']
    pbox = {b['box']['id']: b['box'] for b in pg['boxes']}
    nxt = [max(int(i.split('-')[1]) for i in pbox)]

    def fresh():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    IN0 = sorted([i for i, b in pbox.items() if b['maxclass'] == 'inlet'],
                 key=lambda i: b_x(pbox[i]))[0]
    OUT0 = sorted([i for i, b in pbox.items() if b['maxclass'] == 'outlet'],
                  key=lambda i: b_x(pbox[i]))[0]
    PY0 = PAGE * PITCH
    QY0 = 200.0 + PAGE * 700.0
    add, wire = [], []

    def box(**kw):
        b = dict(kw)
        b.setdefault('id', fresh())
        add.append({'box': b})
        return b['id']

    def link(a, ao, c, ci=0):
        wire.append({'patchline': {'source': [a, ao], 'destination': [c, ci]}})

    # ---- the second outlet: Sub is the one control that must reach past the js ---------------
    OUT1 = box(maxclass='outlet', numinlets=1, numoutlets=0,
               comment='el divisor de Sub, hacia el reloj',
               patching_rect=[90.0, 90.0, 30.0, 30.0])

    # ---- the page ----------------------------------------------------------------------------
    init = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''], varname='tp_init',
               patching_rect=[20.0, QY0, 70.0, 22.0], text='outputvalue')
    link(IN0, 0, init)

    ctl = {}
    for k, (x, y, lab, var, long, w, kind, spec, ann) in enumerate(GLOBALS):
        box(maxclass='comment', numinlets=1, numoutlets=0, varname='tp_lbl_' + var[4:],
            text=lab, presentation=1,
            presentation_rect=[x, PY0 + y, max(w, 38.0), 18.0],
            patching_rect=[20.0 + x, QY0 + 40.0 + y, max(w, 38.0), 18.0])
        vo = {'parameter_longname': long, 'parameter_shortname': long,
              'parameter_initial_enable': 1}
        if kind == 'num':
            lo, hi, ini = spec
            vo.update({'parameter_mmin': lo, 'parameter_mmax': hi, 'parameter_modmode': 4,
                       'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_initial': [ini]})
            cls, no, ot, h = 'live.numbox', 2, ['', 'float'], 15.0
        else:
            vo.update({'parameter_enum': spec, 'parameter_mmax': len(spec) - 1,
                       'parameter_modmode': 0, 'parameter_type': 2, 'parameter_unitstyle': 9,
                       'parameter_initial': [0]})
            cls, no, ot, h = ('live.menu' if kind == 'menu' else 'live.tab'), 3, ['', '', 'float'], 18.0
        ctl[var] = box(maxclass=cls, numinlets=1, numoutlets=no, outlettype=ot,
                       parameter_enable=1, varname=var, annotation=ann, presentation=1,
                       presentation_rect=[x, PY0 + y + 19.0, w, h],
                       patching_rect=[20.0 + x, QY0 + 60.0 + y, w, h],
                       saved_attribute_attributes={'valueof': vo})
        link(init, 0, ctl[var])

    box(maxclass='comment', numinlets=1, numoutlets=0, varname='tp_nota', presentation=1,
        text='Sub 1 deja el reloj exactamente como estaba: sin lugar entre un paso y el '
             'siguiente, Swing, Humaniz y Ratchet no hacen nada.',
        presentation_rect=[0.0, PY0 + 86.0, 500.0, 32.0],
        patching_rect=[20.0, QY0 + 150.0, 500.0, 32.0])

    for var, verb in VERBS.items():
        p = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                text='prepend ' + verb,
                patching_rect=[20.0 + 150.0 * (list(VERBS).index(var) % 4),
                               QY0 + 200.0 + 30.0 * (list(VERBS).index(var) // 4), 140.0, 22.0])
        link(ctl[var], 0, p)
        link(p, 0, OUT0)

    # Sub: the menu hands out an index, so turn it into the divisor before anyone sees it.
    sel = box(maxclass='newobj', numinlets=1, numoutlets=len(DIVS) + 1,
              outlettype=[''] * (len(DIVS) + 1), varname='tp_sub_sel',
              text='sel ' + ' '.join(str(k) for k in range(len(DIVS))),
              patching_rect=[20.0, QY0 + 280.0, 160.0, 22.0])
    link(ctl['fs2_sub'], 0, sel)
    # [t i i]: the js hears setsub first, then the clock is handed the same number.
    tri = box(maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
              varname='tp_sub_t', text='t i i',
              patching_rect=[20.0, QY0 + 340.0, 60.0, 22.0])
    for k, d in enumerate(DIVS):
        m = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
                patching_rect=[20.0 + k * 50.0, QY0 + 310.0, 40.0, 22.0], text=str(d))
        link(sel, k, m)
        link(m, 0, tri)
    prep = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
               text='prepend setsub', patching_rect=[20.0, QY0 + 370.0, 100.0, 22.0])
    link(tri, 1, prep)
    link(prep, 0, OUT0)
    link(tri, 0, OUT1)

    pg['boxes'].extend(add)
    pg['lines'].extend(wire)
    for g in GLOBALS:
        pg['parameters'][ctl[g[3]]] = [g[4], g[4], 0]
    print('pagina Tiempo: %d cajas, %d cords, %d parametros, en y=%.0f'
          % (len(add), len(wire), len(GLOBALS), PY0))
    ph = max(b['box']['presentation_rect'][1] + b['box']['presentation_rect'][3]
             for b in add if b['box'].get('presentation'))
    print('               alto %.0f px (la ventana son 142)' % (ph - PY0))
    assert ph - PY0 <= 142.0, ph - PY0

    # ---- the parent ---------------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    box2 = {b['box']['id']: b['box'] for b in P['boxes']}
    byvar = {b.get('varname'): i for i, b in box2.items() if b.get('varname')}
    nx2 = [max(int(i.split('-')[1]) for i in box2)]

    def fresh2():
        nx2[0] += 1
        return 'obj-%d' % nx2[0]

    BP = byvar['fs2_pages']
    box2[BP]['numoutlets'] = 2
    box2[BP]['outlettype'] = ['', '']

    tab = box2[byvar['fs2_pagina']]
    vo = tab['saved_attribute_attributes']['valueof']
    vo['parameter_enum'] = vo['parameter_enum'] + ['Tiempo']
    vo['parameter_mmax'] = len(vo['parameter_enum']) - 1
    selp = box2[byvar['fs2_pagina_sel']]
    selp['text'] = 'sel ' + ' '.join(str(k) for k in range(len(vo['parameter_enum'])))
    selp['numoutlets'] = len(vo['parameter_enum']) + 1
    selp['outlettype'] = [''] * selp['numoutlets']
    this = [i for i, b in box2.items() if b.get('text') == 'thispatcher'][0]

    def add2(**kw):
        b = dict(kw)
        b.setdefault('id', fresh2())
        P['boxes'].append({'box': b})
        return b['id']

    def link2(a, ao, c, ci=0):
        P['lines'].append({'patchline': {'source': [a, ao], 'destination': [c, ci]}})

    m = add2(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
             patching_rect=[300.0 + PAGE * 200.0, 785.0, 190.0, 22.0],
             text='script sendbox fs2_pages offset 0 %d' % int(-PAGE * PITCH))
    link2(selp['id'], PAGE, m)
    link2(m, 0, this)

    # Libre: the interval is now the step divided by Sub.
    rate_ms = box2[byvar['fs2_rate_ms']]
    assert rate_ms['text'] == 'expr 60000./$f1', rate_ms['text']
    rate_ms['text'] = 'expr 60000./($f1*$f2)'
    rate_ms['numinlets'] = 2

    # Sync: the fixed 4n becomes one of six notevalues.
    sync = byvar['fs2_sync_msg']
    assert box2[sync]['text'] == '4n', box2[sync]['text']
    sw = byvar['fs2_clock_switch']
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] != sync]
    P['lines'] = [l for l in P['lines'] if sync not in (l['patchline']['source'][0],
                                                        l['patchline']['destination'][0])]
    hold = add2(maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
                varname='fs2_sub_hold', text='int 1',
                patching_rect=[900.0, 700.0, 40.0, 22.0])
    tr = add2(maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['', '', ''],
              varname='fs2_sub_t', text='t b i i',
              patching_rect=[900.0, 740.0, 80.0, 22.0])
    note = add2(maxclass='newobj', numinlets=1, numoutlets=len(DIVS) + 1,
                outlettype=[''] * (len(DIVS) + 1), varname='fs2_sub_note',
                text='sel ' + ' '.join(str(d) for d in DIVS),
                patching_rect=[900.0, 780.0, 160.0, 22.0])
    link2(BP, 1, hold)
    link2(hold, 0, tr)
    link2(tr, 2, byvar['fs2_rate_ms'], 1)
    link2(tr, 1, note)
    link2(tr, 0, byvar['fs2_rate'], 0)

    # The metro's own @quantize has to follow the notevalue. Whether it aligns only the first
    # tick or every one, aligning it to the grid the metro is actually beating is right either
    # way -- leaving it at 4n while the metro runs at 16n can only be wrong. [t s s] sends the
    # quantize first, so the interval never lands against a stale grid.
    tq = add2(maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
              varname='fs2_sub_nv', text='t s s', patching_rect=[900.0, 860.0, 60.0, 22.0])
    qp = add2(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
              text='prepend quantize', patching_rect=[1000.0, 900.0, 120.0, 22.0])
    link2(tq, 1, qp)
    link2(qp, 0, byvar['fs2_clock'], 0)
    link2(tq, 0, sw, 2)
    for k, nv in enumerate(NOTEVALUES):
        mm = add2(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
                  patching_rect=[900.0 + k * 60.0, 820.0, 50.0, 22.0], text=nv)
        link2(note, k, mm)
        link2(mm, 0, tq)

    # expr's right inlet is cold and starts at zero, which would make the first interval a
    # division by zero if the clock mode is restored before Sub is. One loadmess costs nothing.
    lm = add2(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
              text='loadmess 1', patching_rect=[1100.0, 700.0, 80.0, 22.0])
    link2(lm, 0, byvar['fs2_rate_ms'], 1)

    # The mode switch has to re-state Sub as well, so leaving Sync recomputes the milliseconds
    # with the right multiplier. [t b b b i]: selector, Sub, rate, run.
    mt = box2[byvar['fs2_mode_trig']]
    assert mt['text'] == 't b b i', mt['text']
    mt['text'] = 't b b b i'
    mt['numoutlets'] = 4
    mt['outlettype'] = ['', '', '', '']
    for l in P['lines']:
        pl = l['patchline']
        if pl['source'][0] == mt['id'] and pl['source'][1] == 2:
            pl['source'][1] = 3
    link2(mt['id'], 2, hold)

    PP = P['parameters']
    for g in GLOBALS:
        PP['%s::%s' % (BP, ctl[g[3]])] = [g[4], g[4], 0]
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    print('parametros: top-level %d, anidados %d, total %d'
          % (len([k for k in PP if k not in meta and '::' not in k]),
             len([k for k in PP if '::' in k]), len([k for k in PP if k not in meta])))
    names = {v[0] for k, v in PP.items() if k not in meta}
    assert len(names) == len([k for k in PP if k not in meta]), 'nombres repetidos'
    assert not [(b['name'], p) for b in PP['parameterbanks'].values()
                for p in b['parameters'] if p != '-' and p not in names]

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    with open(MERGED, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escritos %s y %s' % (MERGED, DEVICE))


def b_x(b):
    return b['patching_rect'][0]


main()
