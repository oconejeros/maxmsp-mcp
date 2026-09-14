"""Fix a real wiring bug found while investigating a later Horizonte-popup wave: obj-26 in
fs2voice_adv.maxpat (the Min/Span register-clamp control) is wired as "prepend setvoicerange"
-- missing the "#1" that substitutes this bpatcher instance's voice index. setvoicerange(v, min,
span) expects 3 args; without "#1" the message only carries 2 (min, span), so `min` lands in the
`v` parameter and `span` lands in `min` -- Min/Span on the panel has never addressed the right
voice or the right fields.

    python tools/fix_fs2_voicerange_index.py            dry run, writes nothing
    python tools/fix_fs2_voicerange_index.py --apply    do it (device closed in Max AND Live)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VOICE_ADV = os.path.join('forteseq', 'fs2voice_adv.maxpat')
BOX_ID = 'obj-26'
OLD_TEXT = 'prepend setvoicerange'
NEW_TEXT = 'prepend setvoicerange #1'


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    b = bx[BOX_ID]
    assert b['text'] == OLD_TEXT, '%s: texto inesperado %r (ya aplicado?)' % (BOX_ID, b['text'])
    b['text'] = NEW_TEXT

    print('%s: %r -> %r' % (BOX_ID, OLD_TEXT, NEW_TEXT))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(VOICE_ADV, VOICE_ADV + '.before-voicerangefix')
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    pg2 = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx2 = {bb['box']['id']: bb['box'] for bb in pg2['boxes']}
    assert bx2[BOX_ID]['text'] == NEW_TEXT

    print('\nescrito %s (.before-voicerangefix guardado). Sigue:' % VOICE_ADV)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice_adv.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
