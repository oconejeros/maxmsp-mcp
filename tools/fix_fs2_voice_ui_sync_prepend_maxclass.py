"""Fix the actual root cause of the UI-sync not working: the 6 "prepend set" boxes added by
add_fs2_voice_ui_sync.py (and recreated identically by the two follow-up fix scripts) were built
as MESSAGE boxes (`maxclass: message`), not the `prepend` OBJECT (`maxclass: newobj`). A message
box just outputs its own literal stored text on any input -- it does not use the incoming value at
all -- so these six boxes have been firing the literal two-symbol message "prepend set" straight
into their live.toggle every time, instead of "set <value>". Confirmed live via the Max console
(read through the maxmsp MCP with the device open): `live.toggle: doesn't understand prepend` x4.

    python tools/fix_fs2_voice_ui_sync_prepend_maxclass.py            dry run, writes nothing
    python tools/fix_fs2_voice_ui_sync_prepend_maxclass.py --apply    do it (device closed in Max AND Live)

## What changes

**forteseq/fs2voice.maxpat**: obj-101 (`v_on_setrx`) maxclass `message` -> `newobj` (text stays
"prepend set", now interpreted as the `prepend` object with argument "set").

**forteseq/fs2voice_adv.maxpat**: obj-202..obj-206 (`v_ext_setrx`/`v_art_setrx`/`v_lec_setrx`/
`v_ton_setrx`/`v_fij_setrx`), same fix.

No FORTESEQ2.amxd or forteseq2.js changes -- the bug was entirely local to these 6 boxes.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VOICE_ESS = os.path.join('forteseq', 'fs2voice.maxpat')
VOICE_ADV = os.path.join('forteseq', 'fs2voice_adv.maxpat')

ESS_IDS = ['obj-101']
ADV_IDS = ['obj-202', 'obj-203', 'obj-204', 'obj-205', 'obj-206']


def fix(pg, ids):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    fixed = []
    for bid in ids:
        b = bx[bid]
        assert b['text'] == 'prepend set', '%s: texto inesperado %r' % (bid, b.get('text'))
        assert b['maxclass'] == 'message', '%s: ya no es message (maxclass=%r) -- ya aplicado?' % (bid, b['maxclass'])
        b['maxclass'] = 'newobj'
        fixed.append(bid)
    return fixed


def main():
    apply_it = '--apply' in sys.argv

    pg_ess = json.load(open(VOICE_ESS, encoding='utf-8'))['patcher']
    fixed_ess = fix(pg_ess, ESS_IDS)

    pg_adv = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    fixed_adv = fix(pg_adv, ADV_IDS)

    print('fs2voice.maxpat: message -> newobj en %s' % ', '.join(fixed_ess))
    print('fs2voice_adv.maxpat: message -> newobj en %s' % ', '.join(fixed_adv))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    with open(VOICE_ESS, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_ess}, f, indent=1)
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_adv}, f, indent=1)

    pg_ess2 = json.load(open(VOICE_ESS, encoding='utf-8'))['patcher']
    bx_ess2 = {b['box']['id']: b['box'] for b in pg_ess2['boxes']}
    assert bx_ess2['obj-101']['maxclass'] == 'newobj'
    pg_adv2 = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx_adv2 = {b['box']['id']: b['box'] for b in pg_adv2['boxes']}
    for bid in ADV_IDS:
        assert bx_adv2[bid]['maxclass'] == 'newobj'

    print('\nescrito %s, %s. Sigue:' % (VOICE_ESS, VOICE_ADV))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice.maxpat forteseq/fs2voice_adv.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
