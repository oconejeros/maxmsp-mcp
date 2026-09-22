"""Fix, round 2: fs2setpick.js (obj-3, "Selector") STILL didn't respond to clicks in "Ambas" mode
after tools/fix_fs2_setpick_hitbox.py -- confirmed by the user (Selector alone: fine; Horizonte's
side in Ambas: fine; only the overlap zone shared with Selector: dead), which rules out rect SIZE
as the cause (shrinking obj-3's rect changed nothing because obj-3 was never the one receiving
those clicks to begin with).

    python tools/fix_fs2_popup_hitorder.py            dry run, writes nothing
    python tools/fix_fs2_popup_hitorder.py --apply    do it (device closed in Max AND Live)

## Root cause (inferred from the symptom, no direct Max access this session -- re-verify in Live)

`fs2hz_ui` (obj-2) is listed BEFORE `fs2sp_ui` (obj-3) in the popup subpatcher's box array
(index 1 vs 2). Both have large, overlapping `presentation_rect`s in the x=8..~400 zone. The
evidence (right side always worked, left side never did, independent of obj-3's rect width) points
to Max giving click priority to whichever overlapping UI object is EARLIER in box-array order --
`fs2hz_ui` -- regardless of which one paints on top. This is the opposite of the naive "topmost
visually wins" assumption tools/fix_fs2_setpick_hitbox.py was built on, which is why that fix (rect
size only) had zero effect: `fs2hz_ui` was capturing the click before `fs2sp_ui`'s rect ever
mattered.

## Fix

1. Reorder the subpatcher's box array so `fs2sp_ui` (obj-3) comes BEFORE `fs2hz_ui` (obj-2) --
   only the array order changes, box ids/positions/wiring are untouched. This should hand Selector
   click priority in the shared zone. Visual rendering is unaffected either way: `fs2horizon.js`
   draws nothing in that zone regardless of paint order (`mgraphics.autofill = 0`, its own content
   is shifted right of `leftMargin()` via `translate()`), so Selector's content stays visible
   whichever box paints last.
2. `fs2sp_ui`'s `presentation_rect` width (420, from the previous fix) shrinks further to exactly
   388 (`PICKER_W` = `PANEL_W` 380 + `GAP` 8, the same constant `fs2horizon.js` uses for
   `leftMargin()`) -- now that Selector wins ties in its own rect, a wider rect than its real
   content would start stealing clicks meant for Horizonte's leftmost real columns (which begin at
   real x ~= 396 in Ambas mode).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

WIN_ID = 'obj-751'   # [p fs2_window]
HZ_UI_ID = 'obj-2'   # fs2hz_ui jsui
SP_UI_ID = 'obj-3'   # fs2sp_ui jsui
NEW_W = 388.0        # PICKER_W


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    win = bx[WIN_ID]
    subP = win['patcher']
    ids = [b['box']['id'] for b in subP['boxes']]
    i2, i3 = ids.index(HZ_UI_ID), ids.index(SP_UI_ID)
    assert i2 < i3, 'fs2hz_ui ya esta despues de fs2sp_ui -- reviso a mano'

    boxes = subP['boxes']
    boxes[i2], boxes[i3] = boxes[i3], boxes[i2]
    new_ids = [b['box']['id'] for b in boxes]
    assert new_ids.index(SP_UI_ID) < new_ids.index(HZ_UI_ID)

    sbx = {b['box']['id']: b['box'] for b in boxes}
    sp = sbx[SP_UI_ID]
    old_rect = sp['presentation_rect']
    new_rect = [old_rect[0], old_rect[1], NEW_W, old_rect[3]]
    sp['presentation_rect'] = new_rect

    print('subpatcher box order: %s <-> %s swapped (indices %d, %d)' % (HZ_UI_ID, SP_UI_ID, i2, i3))
    print('%s presentation_rect width: %s -> %s' % (SP_UI_ID, old_rect[2], NEW_W))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-hitorder')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    subP2 = bx2[WIN_ID]['patcher']
    ids2 = [b['box']['id'] for b in subP2['boxes']]
    assert ids2.index(SP_UI_ID) < ids2.index(HZ_UI_ID)
    sbx2 = {b['box']['id']: b['box'] for b in subP2['boxes']}
    assert sbx2[SP_UI_ID]['presentation_rect'][2] == NEW_W

    print('\nescrito %s (.before-hitorder guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  en Max: recarga el device completo, script stop/start')
    print('  en Live: en "Ambas", clickear piano/sets/Z-pares/Red (izquierda) -- deberia responder')
    print('  ahora. Tambien reverificar Horizonte (derecha) y Horizonte/Selector SOLOS (no deberian')
    print('  haber cambiado).')


main()
