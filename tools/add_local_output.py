"""Give FORTESEQ2 a built-in MIDI output so it sounds WITHOUT a Hub.

    python tools/add_local_output.py            dry run
    python tools/add_local_output.py --apply    write forteseq/FORTESEQ2.amxd (+ .before)

Why: the v2 engine (js forteseq2.js, obj-23) only does `send FORTESEQ_NOTES` -- five-atom
messages [bus voice vel dur pitch] on the shared bus. Nothing reaches the track's MIDI out
unless a forteseqhub.amxd on some track does `receive FORTESEQ_NOTES` -> makenote -> midiout.
So with Run on and no Hub the engine advances silently.

This taps obj-23 outlet 0 (in parallel with the existing obj-23 -> obj-24 send) into a
local makenote -> midiformat -> midiout chain, gated by a new Live toggle "Salida local"
(default ON). The chain mirrors the Hub's receive path (unpack 0. x5, pitch parked in [int]
and released last so makenote's velocity/duration inlets are already loaded), minus the
(bus, voice) filter -- locally we play every note the engine makes. `unpack` fires
right-to-left, so its leftmost outlet (the bus atom) is last; [t b] turns that into the
bang that clocks the parked pitch out of [int].

Trade-off (the reason it is a toggle, not automatic): with "Salida local" ON *and* a Hub
also receiving the bus, every note plays twice. Turn the toggle OFF on the FORTESEQ2 that
feeds a Hub. Idempotent: re-running does nothing once obj-23 already feeds the local gate.

Close FORTESEQ2 in Max AND Live before --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'FORTESEQ2.amxd')

ENGINE = 'obj-23'        # js forteseq2.js
MIDIOUT = 'obj-2'        # newobj midiout  (the pass-through sink)
LOADBANG = 'obj-31'      # newobj loadbang
GATE_VAR = 'fs2_localout_gate'    # idempotency marker
PARAM_LONG = 'Salida local'
PARAM_SHORT = 'Sal loc'


def mkbox(P, **kw):
    P['boxes'].append({'box': kw})


def mkline(P, src, so, dst, di):
    P['lines'].append({'patchline': {'source': [src, so], 'destination': [dst, di]}})


def next_order(P):
    top = 0
    for k, v in P['parameters'].items():
        if isinstance(v, list) and len(v) >= 3 and isinstance(v[2], int):
            top = max(top, v[2])
    return top + 1


def build(apply_it):
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']

    by_var = {b['box'].get('varname'): b['box'] for b in P['boxes']}
    if GATE_VAR in by_var:
        print('already patched (%s present) -- nothing to do' % GATE_VAR)
        return
    ids = {b['box']['id'] for b in P['boxes']}
    for need in (ENGINE, MIDIOUT, LOADBANG):
        assert need in ids, 'expected box %s not found' % need

    n = max(int(i[4:]) for i in ids if i[4:].isdigit())
    TOG, LBL, OV, GATE, UNP, MK, PK, FMT, PIT, TB = ['obj-%d' % (n + k) for k in range(1, 11)]

    order = next_order(P)
    vo = {
        'parameter_longname': PARAM_LONG, 'parameter_shortname': PARAM_SHORT,
        'parameter_type': 2, 'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
        'parameter_modmode': 0, 'parameter_initial_enable': 1, 'parameter_initial': [1],
        'parameter_order': order,
    }

    # --- new boxes -------------------------------------------------------------------
    mkbox(P, id=TOG, maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
          parameter_enable=1, varname=GATE_VAR,
          annotation=('Deja que este FORTESEQ2 toque directamente en la pista, sin Hub '
                      '(encendido por defecto). Apagalo si un forteseqhub ya recibe el bus '
                      'de este motor, o cada nota sonaria dos veces.'),
          patching_rect=[220.0, 636.0, 15.0, 15.0],
          presentation=1, presentation_rect=[560.0, 24.0, 15.0, 15.0],
          saved_attribute_attributes={'valueof': vo})
    mkbox(P, id=LBL, maxclass='comment', numinlets=1, numoutlets=0,
          patching_rect=[240.0, 636.0, 90.0, 18.0], text='Salida local',
          presentation=1, presentation_rect=[560.0, 5.0, 90.0, 18.0], varname='fs2_localout_lbl')
    mkbox(P, id=OV, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[220.0, 606.0, 70.0, 18.0], text='outputvalue',
          varname='fs2_localout_ov', hidden=1)
    mkbox(P, id=GATE, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[220.0, 726.0, 40.0, 20.0], text='gate 1',
          varname=GATE_VAR + '_g', hidden=1)
    mkbox(P, id=UNP, maxclass='newobj', numinlets=1, numoutlets=5,
          outlettype=['float', 'float', 'float', 'float', 'float'],
          patching_rect=[220.0, 756.0, 120.0, 20.0], text='unpack 0. 0. 0. 0. 0.',
          varname='fs2_localout_unp', hidden=1)
    mkbox(P, id=MK, maxclass='newobj', numinlets=3, numoutlets=2, outlettype=['float', 'float'],
          patching_rect=[220.0, 816.0, 180.0, 20.0], text='makenote 100 200 @repeatmode 1',
          varname='fs2_localout_mk', hidden=1)
    mkbox(P, id=PK, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[220.0, 846.0, 60.0, 20.0], text='pack 0. 0.',
          varname='fs2_localout_pk', hidden=1)
    mkbox(P, id=FMT, maxclass='newobj', numinlets=7, numoutlets=2, outlettype=['int', ''],
          patching_rect=[220.0, 876.0, 80.0, 20.0], text='midiformat 1',
          varname='fs2_localout_fmt', hidden=1)
    mkbox(P, id=PIT, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['int'],
          patching_rect=[350.0, 786.0, 40.0, 20.0], text='int',
          varname='fs2_localout_pit', hidden=1)
    mkbox(P, id=TB, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
          patching_rect=[300.0, 786.0, 24.0, 20.0], text='t b',
          varname='fs2_localout_tb', hidden=1)

    # --- wiring --------------------------------------------------------------------
    mkline(P, LOADBANG, 0, OV, 0)         # loadbang -> outputvalue -> toggle (respects saved state)
    mkline(P, OV, 0, TOG, 0)
    mkline(P, TOG, 0, GATE, 0)            # toggle -> gate control inlet
    mkline(P, ENGINE, 0, GATE, 1)        # NEW tap: engine note bus -> gate data inlet
    mkline(P, GATE, 0, UNP, 0)
    mkline(P, UNP, 4, PIT, 1)            # pitch -> parked in [int] (right inlet, no output)
    mkline(P, UNP, 3, MK, 2)            # duration -> makenote
    mkline(P, UNP, 2, MK, 1)            # velocity -> makenote
    mkline(P, UNP, 0, TB, 0)            # bus atom fires last -> [t b]
    mkline(P, TB, 0, PIT, 0)            # bang releases the parked pitch
    mkline(P, PIT, 0, MK, 0)            # pitch -> makenote trigger
    mkline(P, MK, 0, PK, 0)
    mkline(P, MK, 1, PK, 1)
    mkline(P, PK, 0, FMT, 0)
    mkline(P, FMT, 0, MIDIOUT, 0)

    P['parameters'][TOG] = [PARAM_LONG, PARAM_SHORT, order]

    # --- self-check (same class of trap check_structure.py enforces) -------------
    def check(pp, where='root'):
        by = {}
        for b in pp.get('boxes', []):
            bx = b['box']
            assert bx['id'] not in by, '%s: dup id %s' % (where, bx['id'])
            by[bx['id']] = bx
        for ln in pp.get('lines', []):
            pl = ln['patchline']
            for tag, end in (('src', pl['source']), ('dst', pl['destination'])):
                bx = by.get(end[0])
                assert bx, '%s: %s -> unknown box %s' % (where, tag, end)
                n = bx.get('numoutlets', 0) if tag == 'src' else bx.get('numinlets', 0)
                assert 0 <= end[1] < n, '%s: %s %s idx %d not in 0..%d (%s)' % (
                    where, tag, end[0], end[1], n - 1, bx.get('text', bx.get('maxclass')))
        for b in pp.get('boxes', []):
            if b['box'].get('patcher'):
                check(b['box']['patcher'], where + '::' + b['box']['id'])
    check(P)

    print('add_local_output  ->  forteseq/FORTESEQ2.amxd')
    print('  new boxes : %s' % ', '.join([TOG, LBL, OV, GATE, UNP, MK, PK, FMT, PIT, TB]))
    print('  new param : "%s" (order %d) key %s' % (PARAM_LONG, order, TOG))
    print('  tap       : %s outlet 0 -> %s (gate) -> makenote -> midiformat 1 -> %s'
          % (ENGINE, GATE, MIDIOUT))
    print('  toggle    : default ON; loadbang -> outputvalue -> %s' % TOG)

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    assert any(b['box'].get('varname') == GATE_VAR for b in back['boxes']), 'toggle lost'
    assert back['parameters'].get(TOG, [None])[0] == PARAM_LONG, 'param not registered'
    print('\nwrote %s  (backup %s.before)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/FORTESEQ2.amxd')


if __name__ == '__main__':
    build('--apply' in sys.argv)
