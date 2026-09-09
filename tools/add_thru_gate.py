"""Give FORTESEQ2 a switch that mutes the MIDI pass-through WITHOUT deafening the listener.

    python tools/add_thru_gate.py            dry run
    python tools/add_thru_gate.py --apply    write forteseq/FORTESEQ2.amxd (+ .before)

The top of FORTESEQ2.amxd fans `midiin` (obj-1) two ways:

    midiin -> midiout   (obj-2)      raw pass-through: the track's own MIDI, heard as-is
    midiin -> midiparse (obj-509) -> prepend noteheard -> js   the listener / harmony read

Modo Escuchar (setlisten) needs the second path: a hand on the keyboard IS the harmony.
But you do not always want that hand to *sound* -- you are outlining a chord for the
engine, not playing it. Today the only way to silence it is to stop sending the device
MIDI, which also blinds the listener.

This cuts the direct `midiin -> midiout` cord and re-routes it through a new `gate 1`
whose control inlet is a Live toggle **"Pasar MIDI"** (default ON = today's behaviour).
Turn it OFF and incoming notes stop at the gate: `midiparse` still gets every byte, so
Escuchar / noteheard keep working, while the engine's own notes (Salida local, obj-562 ->
midiout) are untouched and still sound.

Mirrors the pattern of `forteseqhub.amxd`'s "MIDI Thru" gate and of `add_local_output.py`
(loadbang -> outputvalue -> toggle so the saved state is restored). Idempotent: re-running
does nothing once `fs2_thru_gate` exists.

Caveat, same as the Hub: closing the gate on a held note can strand it (note-on passed,
note-off blocked). Release keys before toggling, or hit the track's own MIDI panic.

Close FORTESEQ2 in Max AND Live before --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'FORTESEQ2.amxd')

MIDIIN = 'obj-1'         # newobj midiin
MIDIOUT = 'obj-2'        # newobj midiout  (the pass-through sink)
LOADBANG = 'obj-31'      # newobj loadbang
TOG_VAR = 'fs2_thru_gate'        # idempotency marker (the toggle)
PARAM_LONG = 'Pasar MIDI'
PARAM_SHORT = 'Pasa'


def mkbox(P, **kw):
    P['boxes'].append({'box': kw})


def mkline(P, src, so, dst, di):
    P['lines'].append({'patchline': {'source': [src, so], 'destination': [dst, di]}})


def next_order(P):
    top = 0
    for v in P['parameters'].values():
        if isinstance(v, list) and len(v) >= 3 and isinstance(v[2], int):
            top = max(top, v[2])
    return top + 1


def build(apply_it):
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']

    by_var = {b['box'].get('varname'): b['box'] for b in P['boxes']}
    if TOG_VAR in by_var:
        print('already patched (%s present) -- nothing to do' % TOG_VAR)
        return
    ids = {b['box']['id'] for b in P['boxes']}
    for need in (MIDIIN, MIDIOUT, LOADBANG):
        assert need in ids, 'expected box %s not found' % need

    # the direct pass-through cord we are about to interrupt
    direct = [ln for ln in P['lines']
              if ln['patchline']['source'][:2] == [MIDIIN, 0]
              and ln['patchline']['destination'][:2] == [MIDIOUT, 0]]
    assert len(direct) == 1, 'expected exactly one %s -> %s cord, found %d' % (
        MIDIIN, MIDIOUT, len(direct))

    n = max(int(i[4:]) for i in ids if i[4:].isdigit())
    TOG, LBL, OV, GATE = ['obj-%d' % (n + k) for k in range(1, 5)]

    order = next_order(P)
    vo = {
        'parameter_longname': PARAM_LONG, 'parameter_shortname': PARAM_SHORT,
        'parameter_type': 2, 'parameter_enum': ['no pasa', 'pasa'], 'parameter_mmax': 1,
        'parameter_modmode': 0, 'parameter_initial_enable': 1, 'parameter_initial': [1],
        'parameter_order': order,
    }

    # --- new boxes -------------------------------------------------------------------
    mkbox(P, id=TOG, maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
          parameter_enable=1, varname=TOG_VAR,
          annotation=('Deja pasar a la salida el MIDI que entra a la pista (encendido por '
                      'defecto). Apagalo y las notas que toques ya no suenan, pero el modo '
                      'Escuchar las sigue viendo: la mano dibuja la armonia sin que se '
                      'oiga. No afecta lo que genera el propio motor.'),
          patching_rect=[210.0, 34.0, 15.0, 15.0],
          presentation=1, presentation_rect=[414.0, 148.0, 15.0, 15.0],
          saved_attribute_attributes={'valueof': vo})
    mkbox(P, id=LBL, maxclass='comment', numinlets=1, numoutlets=0,
          patching_rect=[210.0, 54.0, 44.0, 18.0], text='Pasa',
          presentation=1, presentation_rect=[432.0, 148.0, 44.0, 18.0], varname='fs2_thru_lbl')
    mkbox(P, id=OV, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[210.0, 74.0, 70.0, 18.0], text='outputvalue',
          varname='fs2_thru_ov', hidden=1)
    mkbox(P, id=GATE, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[120.0, 74.0, 40.0, 20.0], text='gate 1',
          varname='fs2_thru_gate_g', hidden=1)

    # --- wiring --------------------------------------------------------------------
    P['lines'].remove(direct[0])          # cut the raw midiin -> midiout cord
    mkline(P, LOADBANG, 0, OV, 0)         # loadbang -> outputvalue -> toggle (restores saved state)
    mkline(P, OV, 0, TOG, 0)
    mkline(P, TOG, 0, GATE, 0)            # toggle -> gate control inlet
    mkline(P, MIDIIN, 0, GATE, 1)        # raw MIDI -> gate data inlet
    mkline(P, GATE, 0, MIDIOUT, 0)       # gated pass-through -> midiout
    # midiin -> midiparse (obj-509) is left exactly as it was: the listener never loses input

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
                cnt = bx.get('numoutlets', 0) if tag == 'src' else bx.get('numinlets', 0)
                assert 0 <= end[1] < cnt, '%s: %s %s idx %d not in 0..%d (%s)' % (
                    where, tag, end[0], end[1], cnt - 1, bx.get('text', bx.get('maxclass')))
        for b in pp.get('boxes', []):
            if b['box'].get('patcher'):
                check(b['box']['patcher'], where + '::' + b['box']['id'])
    check(P)

    print('add_thru_gate  ->  forteseq/FORTESEQ2.amxd')
    print('  new boxes : %s' % ', '.join([TOG, LBL, OV, GATE]))
    print('  new param : "%s" (order %d) key %s' % (PARAM_LONG, order, TOG))
    print('  re-route  : %s -> %s  becomes  %s -> [gate 1] -> %s' % (MIDIIN, MIDIOUT, MIDIIN, MIDIOUT))
    print('  listener  : %s -> obj-509 (midiparse) untouched' % MIDIIN)
    print('  toggle    : default "pasa" (ON); loadbang -> outputvalue -> %s' % TOG)

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    assert any(b['box'].get('varname') == TOG_VAR for b in back['boxes']), 'toggle lost'
    assert back['parameters'].get(TOG, [None])[0] == PARAM_LONG, 'param not registered'
    assert not [ln for ln in back['lines']
                if ln['patchline']['source'][:2] == [MIDIIN, 0]
                and ln['patchline']['destination'][:2] == [MIDIOUT, 0]], 'direct cord still there'
    print('\nwrote %s  (backup %s.before)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/FORTESEQ2.amxd')


if __name__ == '__main__':
    build('--apply' in sys.argv)
