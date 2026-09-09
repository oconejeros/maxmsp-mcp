"""Build forteseq/forteseqwftrig.amxd -- feed FORTESEQ2's ENGINE with EVENFLOW's WF rhythms.

The problem: EVENFLOW (`forteseqwf.amxd`) with `Bus On` broadcasts finished notes on
`FORTESEQ_NOTES` (`[bus, group, vel, dur, pitch]`). A `forteseqhub.amxd` in RECIBIR just PLAYS
that note; it never reaches FORTESEQ2's generator. FORTESEQ2's engine is driven by the OTHER bus,
`FORTESEQ_TRIG` (`[bus, voice]`), which `forteseq2.js`'s trig()/triggervoice() turns into a
generated note (pitch/harmony chosen by FORTESEQ2; the incoming pitch is irrelevant).

This device is the missing NOTES -> TRIG bridge, keyed on the EVENFLOW GROUP:

    receive FORTESEQ_NOTES -> unpack 0. 0. 0. 0. 0.
       bus   -> [== <Bus EVENFLOW>] -> [sel 1] --------------------┐  (bus fires LAST out of
       group -> [int]  (latched) <-------------------------------- ┘   unpack, so the compare
       (latched group) -> [sel 1 2 3 4 5 6] -> [gate]x6 <- Grupo1..6   is ready before release)
       any open gate -> [t b] -> [int <Bus FORTESEQ2>] -> [pack <busF2> <voz>] -> send FORTESEQ_TRIG

CRITICAL: it listens on one bus and triggers on ANOTHER. A triggered FORTESEQ2 voice re-broadcasts
its note on FORTESEQ_NOTES; if that landed on the bus this device listens to, it would feed back
(Max kills `trigger` with a "stack overflow" -- that was the first build's bug). So "Bus EVENFLOW"
(the one EVENFLOW's `Bus del motor` is set to) and "Bus FORTESEQ2" (the target engine's bus) MUST
be different numbers. Defaults 2 and 1.

One instance per FORTESEQ2 voice you want driven. Tick one or several "Grupo N" toggles to listen
to those EVENFLOW groups; grouped playback also still works at the source (several levels on one
group). "Voz a disparar" and the groups listened to are independent numbers.

Assembled the tools/*.py way (no MCP path, device is small): copy a known-good MIDI-effect device
(`forteseqvoicetrigger.amxd`, same `midf` AMPF/meta chunk) and rewrite boxes/lines/parameters.
Close it in BOTH Max and Live before --apply.

    python tools/build_wf_trig.py            dry run, writes nothing
    python tools/build_wf_trig.py --apply    do it
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'forteseq', 'forteseqvoicetrigger.amxd')
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwftrig.amxd')

DESC = ('EVENFLOW -> motor FORTESEQ2: escucha FORTESEQ_NOTES, y por cada onset de los grupos '
        'elegidos manda FORTESEQ_TRIG [bus, voz] para que FORTESEQ2 genere la nota (su motor '
        'elige altura/armonia; la altura entrante no cuenta). Una instancia por voz a disparar.')


def numbox_vo(longname, shortname, mmax, initial):
    return {
        'parameter_initial': [initial], 'parameter_initial_enable': 1,
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_mmin': 1.0, 'parameter_mmax': float(mmax),
        'parameter_modmode': 3, 'parameter_type': 1, 'parameter_unitstyle': 0,
    }


def toggle_vo(longname, initial):
    return {
        'parameter_initial': [initial], 'parameter_initial_enable': 1,
        'parameter_longname': longname, 'parameter_shortname': longname,
        'parameter_mmax': 1, 'parameter_enum': ['off', 'on'],
        'parameter_modmode': 0, 'parameter_type': 2, 'parameter_unitstyle': 9,
    }


def build_boxes_lines():
    boxes, lines = [], []

    def box(**kw):
        boxes.append({'box': kw})

    def line(src, si, dst, di):
        lines.append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    SX = 400.0   # patching-view x for the off-panel engine chain

    # -- MIDI pass-through (stock template behaviour) --------------------------------------
    box(id='obj-1', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['int'],
        patching_rect=[24.0, 520.0, 40.0, 22.0], text='midiin', varname='wt_midiin')
    box(id='obj-2', maxclass='newobj', numinlets=1, numoutlets=0,
        patching_rect=[24.0, 560.0, 47.0, 22.0], text='midiout', varname='wt_midiout')
    line('obj-1', 0, 'obj-2', 0)

    # -- Bus params (MUST differ -- see module docstring) + Voz -------------------------
    box(id='obj-10', maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
        parameter_enable=1, varname='wt_bus_in', patching_rect=[SX, 40.0, 44.0, 15.0],
        presentation=1, presentation_rect=[10.0, 8.0, 44.0, 15.0],
        annotation='Bus que ESCUCHA: el mismo numero que el "Bus del motor" de EVENFLOW. '
                   'DEBE ser distinto del bus de FORTESEQ2 de abajo, o hay realimentacion.',
        saved_attribute_attributes={'valueof': numbox_vo('Bus EVENFLOW', 'BusEF', 16, 2)})
    box(id='obj-11', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[SX + 50, 40.0, 220.0, 18.0], presentation=1,
        presentation_rect=[58.0, 10.0, 200.0, 18.0], text='Bus EVENFLOW (escuchar)',
        varname='wt_bus_in_lbl')
    box(id='obj-15', maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
        parameter_enable=1, varname='wt_bus_f2', patching_rect=[SX, 70.0, 44.0, 15.0],
        presentation=1, presentation_rect=[10.0, 30.0, 44.0, 15.0],
        annotation='Bus del FORTESEQ2 a disparar. DEBE ser distinto del Bus EVENFLOW de arriba.',
        saved_attribute_attributes={'valueof': numbox_vo('Bus FORTESEQ2', 'BusF2', 16, 1)})
    box(id='obj-16', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[SX + 50, 70.0, 220.0, 18.0], presentation=1,
        presentation_rect=[58.0, 32.0, 200.0, 18.0], text='Bus FORTESEQ2 (disparar)',
        varname='wt_bus_f2_lbl')
    box(id='obj-12', maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
        parameter_enable=1, varname='wt_voz', patching_rect=[SX, 100.0, 44.0, 15.0],
        presentation=1, presentation_rect=[10.0, 52.0, 44.0, 15.0],
        annotation='Que voz de FORTESEQ2 disparar (1-16). Independiente de los grupos que se '
                   'escuchan abajo.',
        saved_attribute_attributes={'valueof': numbox_vo('Voz a disparar', 'Voz', 16, 1)})
    box(id='obj-13', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[SX + 50, 100.0, 220.0, 18.0], presentation=1,
        presentation_rect=[58.0, 54.0, 200.0, 18.0], text='Voz FORTESEQ2 a disparar',
        varname='wt_voz_lbl')

    box(id='obj-14', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[SX, 120.0, 240.0, 18.0], presentation=1,
        presentation_rect=[10.0, 78.0, 240.0, 16.0], text='Grupos EVENFLOW a escuchar:',
        varname='wt_grp_hdr')

    # -- Grupo 1..6 toggles ------------------------------------------------------------
    tgl_ids = []
    for i in range(1, 7):
        gid = 'obj-%d' % (19 + i)                       # obj-20 .. obj-25
        tgl_ids.append(gid)
        box(id=gid, maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
            parameter_enable=1, varname='wt_grp%d' % i,
            patching_rect=[SX + (i - 1) * 40.0, 150.0, 18.0, 18.0],
            presentation=1, presentation_rect=[10.0 + (i - 1) * 40.0, 96.0, 18.0, 18.0],
            annotation='Escuchar el grupo %d de EVENFLOW.' % i,
            saved_attribute_attributes={'valueof': toggle_vo('Grupo %d' % i, 1 if i == 1 else 0)})
        box(id='obj-%d' % (29 + i), maxclass='comment', numinlets=1, numoutlets=0,
            patching_rect=[SX + (i - 1) * 40.0, 172.0, 24.0, 16.0], presentation=1,
            presentation_rect=[10.0 + (i - 1) * 40.0, 116.0, 24.0, 12.0],
            text='G%d' % i, varname='wt_grp%d_lbl' % i)

    box(id='obj-36', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[SX, 195.0, 460.0, 40.0], presentation=1,
        presentation_rect=[10.0, 131.0, 470.0, 32.0], text=DESC, varname='wt_desc')

    # -- engine chain: FORTESEQ_NOTES -> (bus & group) -> FORTESEQ_TRIG -------------------
    box(id='obj-40', maxclass='newobj', numinlets=0, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 40.0, 150.0, 22.0], text='receive FORTESEQ_NOTES', varname='wt_recv')
    box(id='obj-41', maxclass='newobj', numinlets=1, numoutlets=5,
        outlettype=['float', 'float', 'float', 'float', 'float'],
        patching_rect=[24.0, 80.0, 150.0, 22.0], text='unpack 0. 0. 0. 0. 0.', varname='wt_unpack')
    box(id='obj-42', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['int'],
        patching_rect=[80.0, 120.0, 32.0, 22.0], text='int', varname='wt_grp_hold')
    box(id='obj-43', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['int'],
        patching_rect=[24.0, 120.0, 40.0, 22.0], text='== 1', varname='wt_bus_eq')
    box(id='obj-44', maxclass='newobj', numinlets=2, numoutlets=2, outlettype=['bang', ''],
        patching_rect=[24.0, 150.0, 40.0, 22.0], text='sel 1', varname='wt_bus_sel')
    box(id='obj-45', maxclass='newobj', numinlets=1, numoutlets=7,
        outlettype=['bang', 'bang', 'bang', 'bang', 'bang', 'bang', ''],
        patching_rect=[80.0, 180.0, 130.0, 22.0], text='sel 1 2 3 4 5 6', varname='wt_grp_sel')

    gate_ids = []
    for i in range(1, 7):
        gid = 'obj-%d' % (45 + i)                       # obj-46 .. obj-51
        gate_ids.append(gid)
        box(id=gid, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
            patching_rect=[80.0 + (i - 1) * 40.0, 220.0, 32.0, 22.0], text='gate',
            varname='wt_gate%d' % i)
        line(tgl_ids[i - 1], 0, gid, 0)                 # toggle -> gate control (open/close)
        line('obj-45', i - 1, gid, 1)                   # sel outlet -> gate data (bang)
        line(gid, 0, 'obj-52', 0)                       # any open gate -> t b

    box(id='obj-52', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[80.0, 260.0, 24.0, 22.0], text='t b', varname='wt_bang')
    box(id='obj-53', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['int'],
        patching_rect=[80.0, 290.0, 32.0, 22.0], text='int', varname='wt_bus_out')
    box(id='obj-54', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[80.0, 320.0, 44.0, 22.0], text='pack 1 1', varname='wt_pack')
    box(id='obj-55', maxclass='newobj', numinlets=1, numoutlets=0,
        patching_rect=[80.0, 350.0, 150.0, 22.0], text='send FORTESEQ_TRIG', varname='wt_send')

    line('obj-40', 0, 'obj-41', 0)
    line('obj-41', 1, 'obj-42', 1)      # group -> int (latched, no output)
    line('obj-41', 0, 'obj-43', 0)      # bus  -> == (fires last out of unpack)
    line('obj-10', 0, 'obj-43', 1)      # Bus EVENFLOW -> == compare value (LISTEN bus)
    line('obj-43', 0, 'obj-44', 0)
    line('obj-44', 0, 'obj-42', 0)      # bus matched -> release the latched group
    line('obj-42', 0, 'obj-45', 0)
    line('obj-52', 0, 'obj-53', 0)      # bang -> emit held bus
    line('obj-15', 0, 'obj-53', 1)      # Bus FORTESEQ2 -> int (held)  (TRIGGER bus, != listen)
    line('obj-53', 0, 'obj-54', 0)
    line('obj-12', 0, 'obj-54', 1)      # Voz param -> pack right
    line('obj-54', 0, 'obj-55', 0)

    # -- init: re-emit stored parameter values on load --------------------------------
    box(id='obj-60', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[24.0, 400.0, 62.0, 22.0], text='loadbang', varname='wt_init')
    line('obj-60', 0, 'obj-10', 0)      # bang is safe on live.numbox (re-emits)
    line('obj-60', 0, 'obj-15', 0)
    line('obj-60', 0, 'obj-12', 0)
    for i in range(1, 7):
        mid = 'obj-%d' % (60 + i)                       # obj-61 .. obj-66
        box(id=mid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
            patching_rect=[120.0 + (i - 1) * 80.0, 400.0, 74.0, 22.0], text='outputvalue',
            varname='wt_out%d' % i)
        line('obj-60', 0, mid, 0)
        line(mid, 0, tgl_ids[i - 1], 0)                 # outputvalue: re-emit WITHOUT flipping

    return boxes, lines


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(TEMPLATE)
    P = doc['patcher']

    boxes, lines = build_boxes_lines()
    P['boxes'] = boxes
    P['lines'] = lines
    P['parameters'] = {
        'obj-10': ['Bus EVENFLOW', 'BusEF', 0],
        'obj-15': ['Bus FORTESEQ2', 'BusF2', 1],
        'obj-12': ['Voz a disparar', 'Voz', 2],
        'obj-20': ['Grupo 1', 'Grupo 1', 3],
        'obj-21': ['Grupo 2', 'Grupo 2', 4],
        'obj-22': ['Grupo 3', 'Grupo 3', 5],
        'obj-23': ['Grupo 4', 'Grupo 4', 6],
        'obj-24': ['Grupo 5', 'Grupo 5', 7],
        'obj-25': ['Grupo 6', 'Grupo 6', 8],
        'parameterbanks': {
            '0': {'index': 0, 'name': 'Trigger',
                  'parameters': ['Voz a disparar', 'Bus FORTESEQ2', 'Bus EVENFLOW', 'Grupo 1',
                                 'Grupo 2', 'Grupo 3', 'Grupo 4', 'Grupo 5']},
        },
        'inherited_shortname': 1,
    }
    P.pop('dependency_cache', None)
    P['rect'] = [140.0, 140.0, 520.0, 300.0]
    P['openinpresentation'] = 1

    # --- self-checks (same class of trap check_structure.py enforces) --------------------
    idx = {b['box']['id']: b['box'] for b in P['boxes']}
    ids = list(idx)
    assert len(ids) == len(set(ids)), 'duplicate box id'
    for ln in P['lines']:
        pl = ln['patchline']
        for lab, end in (('source', pl['source']), ('destination', pl['destination'])):
            assert end[0] in idx, (lab, end)
            b = idx[end[0]]
            nn = b.get('numoutlets', 0) if lab == 'source' else b.get('numinlets', 0)
            assert 0 <= end[1] < nn, (lab, end, b.get('text', b.get('maxclass')))

    pp_names = {k: v[0] for k, v in P['parameters'].items()
               if k not in ('parameterbanks', 'inherited_shortname')}
    vo_names = {}
    for b in P['boxes']:
        bb = b['box']
        vv = (bb.get('saved_attribute_attributes') or {}).get('valueof')
        if vv and bb.get('parameter_enable'):
            vo_names[bb['id']] = vv['parameter_longname']
    assert set(vo_names) == set(pp_names), set(vo_names) ^ set(pp_names)
    for k in vo_names:
        assert vo_names[k] == pp_names[k], (k, vo_names[k], pp_names[k])
    assert len(set(pp_names.values())) == len(pp_names), 'duplicate longname'
    bank = P['parameters']['parameterbanks']['0']['parameters']
    for sn in ('Voz a disparar', 'Bus FORTESEQ2', 'Bus EVENFLOW', 'Grupo 1'):
        assert sn in bank, sn
    assert all(nm in pp_names.values() for nm in bank), [nm for nm in bank if nm not in pp_names.values()]
    orders = sorted(v[2] for v in pp_names_iter(P))
    assert orders == list(range(len(orders))), orders

    print('build_wf_trig  ->  forteseq/forteseqwftrig.amxd   (template %s)'
          % os.path.basename(TEMPLATE))
    print('  boxes %d   lines %d   params %d' % (len(P['boxes']), len(P['lines']), len(pp_names)))
    print('  chain : receive FORTESEQ_NOTES -> (bus == BusEVENFLOW) & (group in Grupo1..6) -> '
          'pack [BusFORTESEQ2 Voz] -> send FORTESEQ_TRIG   (the two buses MUST differ)')

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    if os.path.exists(DEVICE):
        shutil.copyfile(DEVICE, DEVICE + '.before')
        print('  backup : %s.before' % os.path.basename(DEVICE))
    amxd.save(DEVICE, data, s, e, doc)

    d2, s2, e2, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    assert len(P2['boxes']) == len(boxes) and len(P2['lines']) == len(lines)
    b2 = {b['box'].get('varname'): b['box'] for b in P2['boxes']}
    assert b2['wt_recv']['text'] == 'receive FORTESEQ_NOTES'
    assert b2['wt_send']['text'] == 'send FORTESEQ_TRIG'
    back = {k: v[0] for k, v in P2['parameters'].items()
            if k not in ('parameterbanks', 'inherited_shortname')}
    assert set(back.values()) == set(pp_names.values()), set(back.values()) ^ set(pp_names.values())
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/forteseqwftrig.amxd')


def pp_names_iter(P):
    for k, v in P['parameters'].items():
        if k not in ('parameterbanks', 'inherited_shortname'):
            yield v


main()
