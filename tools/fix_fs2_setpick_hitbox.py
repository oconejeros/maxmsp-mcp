"""Fix: fs2setpick.js (obj-3, "Selector") stopped responding to clicks as soon as "Ambas"
(tools/add_fs2_popup_ambas.py) showed it side by side with fs2horizon.js -- found by the user
testing in Live.

    python tools/fix_fs2_setpick_hitbox.py            dry run, writes nothing
    python tools/fix_fs2_setpick_hitbox.py --apply    do it (device closed in Max AND Live)

## Root cause

Both `fs2hz_ui` (obj-2) and `fs2sp_ui` (obj-3) have `presentation_rect = [8, 8, 7680, 4320]` --
identical, and both dating from an earlier "fix popup canvas size on large monitors" commit that
applied one blanket oversized rect to both jsui uniformly. This is fine for `fs2hz_ui`: its own
content legitimately grows to fill the whole window on a big monitor, so its box needs to be that
big. It's wrong for `fs2sp_ui`: its content width is `PANEL_W = 380` FIXED, never dependent on
window size (`viewportWH()` returns `[PANEL_W, ...]` unconditionally) -- there is no reason for its
CLICKABLE AREA to extend 7680px wide.

While Selector was ever only shown ALONE (Horizonte hidden, exclusive tabs) this cost nothing --
nothing else was competing for clicks in that space. "Ambas" is the first time both jsui are
visible together with genuinely overlapping hit-rects, and Max gives click priority to whichever
box is listed last / drawn on top -- `fs2sp_ui`. With its rect covering the ENTIRE window, it
silently swallows every click anywhere in the popup (including ones meant for `fs2hz_ui`'s content
off to the right), and its own `onclick` correctly finds nothing at those coordinates (all its hit
geometry -- `maskGeo`/`zGeo`/`redGeo` -- lives within its own ~380px-wide drawn column), so nothing
happens at all: the reported "left side doesn't respond".

## Fix

Shrink `fs2sp_ui`'s `presentation_rect` width from 7680 to 420 (`PANEL_W` 380 + `PAD` 8 + a little
slack) -- just enough to cover its own drawn content with room to spare, ending well before
`fs2hz_ui`'s content starts at real x ~= 396 (`PICKER_W` = `PANEL_W` + `GAP`) in Ambas mode. Height
stays 4320 (unchanged) -- `fs2setpick.js`'s own height genuinely does track the window via
`viewportWH()`. `fs2hz_ui`'s rect is untouched.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

WIN_ID = 'obj-751'   # [p fs2_window]
SP_UI_ID = 'obj-3'   # fs2sp_ui jsui (inside the subpatcher)
NEW_W = 420.0


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    win = bx[WIN_ID]
    subP = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in subP['boxes']}

    sp = sbx[SP_UI_ID]
    assert sp['varname'] == 'fs2sp_ui', sp['varname']
    rect = sp['presentation_rect']
    assert rect == [8.0, 8.0, 7680.0, 4320.0], rect

    new_rect = [rect[0], rect[1], NEW_W, rect[3]]
    sp['presentation_rect'] = new_rect

    print('%s (fs2sp_ui) presentation_rect: %s -> %s' % (SP_UI_ID, rect, new_rect))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-setpickhitbox')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    sbx2 = {b['box']['id']: b['box'] for b in bx2[WIN_ID]['patcher']['boxes']}
    assert sbx2[SP_UI_ID]['presentation_rect'] == new_rect

    print('\nescrito %s (.before-setpickhitbox guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  en Max: recarga el device completo, script stop/start')
    print('  en Live: en "Ambas", clickear piano/sets/Z-pares/Red (izquierda) Y chips/dropdowns de')
    print('  Horizonte (derecha) -- ambos deberian responder ahora')


main()
