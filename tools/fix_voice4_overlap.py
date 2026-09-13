"""Fix "Voces 4" bleeding into "Voces 3": the per-voice bpatcher (vadv1-4) is shown through a
FIXED 206px-wide window (obj-577's own presentation_rect, unchanged since the Voces1/Voces2 split)
-- `script sendbox vadv# offset <x> 0` just PANS that window over the shared canvas, it does not
resize it. Voces 3's own offset is -412, so its window reveals local canvas range [412, 618], not
just the 76px its own 3 controls (OrnTipo/OrnNotas/OrnBase, x 412-488) actually occupy. Voces 4's
controls landed at x 510-590 -- squarely INSIDE that [412,618] range -- so switching to "Voces 3"
already revealed "Voces 4"'s TonProp/Set/Raiz controls too, and "Voces 4" showed nothing that
wasn't already visible on "Voces 3". Reported by the user from a screenshot: "los controles de
voces 4 son los mismos de voice 3".

Root cause of the miscalculation: Voces 3 was placed 22px past where Voces 2's own CONTROLS end
(x=390), which happened to work because nothing else occupied the rest of Voces 3's 206px window.
Voces 4 needs to clear Voces 3's whole WINDOW (ends at 618), not just its controls -- the same
rule that (barely) held for Voces1->Voces2->Voces3 by accident of small margins holds here with a
much bigger, clearly visible violation.

Fix: shift TonProp/Set/Raiz from x 510/528/564 to x 620/638/674 (+110, clearing Voces 3's window
with a 2px margin) and update Voces 4's activation message (the `script sendbox vadv# offset -510
0` clauses) to -620 to match. No other box, wire, or parameter changes.

    python tools/fix_voice4_overlap.py            dry run, writes nothing
    python tools/fix_voice4_overlap.py --apply    do it (device closed in Max AND Live)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE = os.path.join('forteseq', 'fs2voice_adv.maxpat')

SHIFT = 110.0
OLD_OFFSET = -510.0
NEW_OFFSET = -620.0
CONTROL_IDS = ['obj-111', 'obj-112', 'obj-113']   # V#1 TonProp / Set / Raiz
VOCES4_MSG_ID = 'obj-804'


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx = {b['box']['id']: b['box'] for b in pg['boxes']}
    for oid in CONTROL_IDS:
        vo = pbx[oid]['saved_attribute_attributes']['valueof']
        assert vo['parameter_longname'] in ('V#1 TonProp', 'V#1 Set', 'V#1 Raiz'), (oid, vo)
    rect = pbx[CONTROL_IDS[0]]['presentation_rect']
    assert rect[0] == 510.0, 'ya aplicado (obj-111 x=%s)' % rect[0]

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    msg = bx[VOCES4_MSG_ID]
    assert msg['text'].count('offset -510 0') == 4, msg['text']

    for oid in CONTROL_IDS:
        r = pbx[oid]['presentation_rect']
        old_x = r[0]
        r[0] = old_x + SHIFT
        print('%s: x %g -> %g' % (oid, old_x, r[0]))

    msg['text'] = msg['text'].replace('offset -510 0', 'offset -620 0')
    print('%s: offset -510 0 -> offset -620 0 (x4)' % VOCES4_MSG_ID)

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    pg2 = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert pbx2['obj-111']['presentation_rect'][0] == 620.0

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert bx2[VOCES4_MSG_ID]['text'].count('offset -620 0') == 4

    print('\nescrito %s y %s (.before del .amxd guardado). Sigue:' % (VOICE, DEVICE))
    print('  python tools/check_structure.py')
    print('  en Max: recarga el device completo, script stop/start')


main()
