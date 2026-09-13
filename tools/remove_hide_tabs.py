"""Remove the "Ocultar Tabs" toggle -- user tested it and it doesn't do anything useful in Live,
asked to just delete it.

    python tools/remove_hide_tabs.py            dry run, writes nothing
    python tools/remove_hide_tabs.py --apply    do it (device closed in Max AND Live)

Reverts exactly what `tools/add_hide_tabs.py` added: 6 boxes (obj-786..791: the "Tabs" comment,
the toggle, `sel 1`, the hide message, `t b b`, the show message) and their 8 patchlines. Nothing
else in the device was touched when this landed (verified at the time: 0 pre-existing boxes
changed), so removing exactly these ids is a clean, total revert -- no leftover dangling wires or
orphaned `parameters` entries.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
REMOVE_IDS = {'obj-786', 'obj-787', 'obj-788', 'obj-789', 'obj-790', 'obj-791'}


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert bx['obj-787']['maxclass'] == 'live.toggle', bx['obj-787']
    assert PP.get('obj-787') and PP['obj-787'][0] == 'Ocultar Tabs', PP.get('obj-787')

    before_boxes = len(P['boxes'])
    before_lines = len(P['lines'])

    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in REMOVE_IDS]
    P['lines'] = [l for l in P['lines']
                  if l['patchline']['source'][0] not in REMOVE_IDS
                  and l['patchline']['destination'][0] not in REMOVE_IDS]
    del PP['obj-787']

    print('boxes: %d -> %d (-%d)' % (before_boxes, len(P['boxes']), before_boxes - len(P['boxes'])))
    print('lines: %d -> %d (-%d)' % (before_lines, len(P['lines']), before_lines - len(P['lines'])))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert not (REMOVE_IDS & set(bx2)), REMOVE_IDS & set(bx2)
    assert 'obj-787' not in P2['parameters']
    touching = [l for l in P2['lines']
                if l['patchline']['source'][0] in REMOVE_IDS or l['patchline']['destination'][0] in REMOVE_IDS]
    assert not touching, touching

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  en Max: recarga el device')


main()
