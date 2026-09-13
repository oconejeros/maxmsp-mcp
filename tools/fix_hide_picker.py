"""Fix "Solo Voces": it hid the picker but did not visually reclaim the space -- confirmed by the
user's screenshot (blank grey strip on the left, horizon grid still flush right).

    python tools/fix_hide_picker.py            dry run, writes nothing
    python tools/fix_hide_picker.py --apply    do it (device closed in Max AND Live)

## Why the first cut didn't work

`add_hide_picker.py` tried to slide the horizon grid left with `script sendbox fs2hz_ui offset
-388 0`. That is the SAME class of operation ([[forteseq2_horizon_window]] already documents,
verbatim) that was already proven NOT to work inside this specific floating `openinpresentation:1`
popup: box position/size is fixed once the window opens, no matter which API tries to change it
afterwards -- a fact this very file's own `fitToWindow()` comment already warns about, which this
change should have checked against before writing a new `sendbox` call.

## The actual fix

Same trick this file already uses successfully for window-RESIZE (oversized box + internal
viewport math driven by `SELF.patcher.wind.size`, no box.rect writes): make the horizontal
overlap PERMANENT instead of trying to create it at runtime.

  * `.amxd`: `fs2hz_ui` (obj-2 inside `[p fs2_window]`, obj-751) already OVERLAPS `fs2sp_ui`
    (obj-3) once its presentation_rect X moves from 396 to 8 -- same left edge, same oversized
    canyon-sized box it already had. Z-order needs no change: obj-3 already comes after obj-2 in
    the box list, so the picker already draws ON TOP when both are visible.
  * `fs2horizon.js`: gets a new `solovoices(flag)` message handler. `pickerVisible` (default 1)
    controls a `leftMargin()` of 388px (PICKER_W) that `paint()` now `mgraphics.translate()`s by
    and `viewportWH()` subtracts -- so with the picker showing, the horizon grid draws exactly
    where it always has (as if still starting at x=396); with it hidden, the margin drops to 0 and
    the grid draws from the box's own left edge, filling the reclaimed space. No box ever moves.
  * `.amxd` subpatcher wiring: the existing `route hidepicker showpicker` (obj-5) gains two more
    destinations straight to `fs2hz_ui` -- "solovoices 1" alongside the existing `script hide
    fs2sp_ui`, "solovoices 0" alongside `script show fs2sp_ui`. The now-useless `script sendbox
    fs2hz_ui offset ...` clauses are dropped from both messages.

Run this AFTER pulling the matching `forteseq2/fs2horizon.js` change (this script only touches
the .amxd) and reload the js in Max (fs2horizon.js has no autowatch -- open+save in the js editor,
or reopen the device).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
WINDOW_ID = 'obj-751'
ROUTE_ID = 'obj-5'     # inside the subpatcher: route hidepicker showpicker
HIDE_MSG_ID = 'obj-6'  # message -> thispatcher, on the "hidepicker" match
SHOW_MSG_ID = 'obj-7'  # message -> thispatcher, on the "showpicker" match
HZ_UI_ID = 'obj-2'     # jsui fs2horizon.js

OLD_HIDE = 'script hide fs2sp_ui, script sendbox fs2hz_ui offset -388 0'
NEW_HIDE = 'script hide fs2sp_ui'
OLD_SHOW = 'script sendbox fs2hz_ui offset 388 0, script show fs2sp_ui'
NEW_SHOW = 'script show fs2sp_ui'


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    win = bx[WINDOW_ID]
    assert win['text'] == 'p fs2_window', win['text']
    sub = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in sub['boxes']}

    hz = sbx[HZ_UI_ID]
    assert hz.get('filename') == 'fs2horizon.js', hz
    assert hz['presentation_rect'][0] == 396.0, hz['presentation_rect']
    hz['presentation_rect'][0] = 8.0

    hide_msg = sbx[HIDE_MSG_ID]
    show_msg = sbx[SHOW_MSG_ID]
    assert hide_msg['text'] == OLD_HIDE, hide_msg['text']
    assert show_msg['text'] == OLD_SHOW, show_msg['text']
    hide_msg['text'] = NEW_HIDE
    show_msg['text'] = NEW_SHOW

    nid = [max(int(i.split('-')[1]) for i in sbx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    m_solo1 = fresh()
    sub['boxes'].append({'box': {
        'id': m_solo1, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [400.0, 1650.0, 100.0, 20.0], 'text': 'solovoices 1'}})
    m_solo0 = fresh()
    sub['boxes'].append({'box': {
        'id': m_solo0, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [650.0, 1650.0, 100.0, 20.0], 'text': 'solovoices 0'}})

    sub['lines'].append({'patchline': {'source': [ROUTE_ID, 0], 'destination': [m_solo1, 0]}})
    sub['lines'].append({'patchline': {'source': [ROUTE_ID, 1], 'destination': [m_solo0, 0]}})
    sub['lines'].append({'patchline': {'source': [m_solo1, 0], 'destination': [HZ_UI_ID, 0]}})
    sub['lines'].append({'patchline': {'source': [m_solo0, 0], 'destination': [HZ_UI_ID, 0]}})

    print('fs2hz_ui presentation_rect x: 396 -> 8')
    print('hide message: %r -> %r' % (OLD_HIDE, NEW_HIDE))
    print('show message: %r -> %r' % (OLD_SHOW, NEW_SHOW))
    print('nuevos: %s solovoices 1, %s solovoices 0 -> %s' % (m_solo1, m_solo0, HZ_UI_ID))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    win2 = bx2[WINDOW_ID]['patcher']
    sbx2 = {b['box']['id']: b['box'] for b in win2['boxes']}
    assert sbx2[HZ_UI_ID]['presentation_rect'][0] == 8.0
    assert sbx2[HIDE_MSG_ID]['text'] == NEW_HIDE and sbx2[SHOW_MSG_ID]['text'] == NEW_SHOW
    ssrcs = {(l['patchline']['source'][0], l['patchline']['source'][1], l['patchline']['destination'][0])
             for l in win2['lines']}
    assert (ROUTE_ID, 0, m_solo1) in ssrcs and (ROUTE_ID, 1, m_solo0) in ssrcs
    assert (m_solo1, 0, HZ_UI_ID) in ssrcs and (m_solo0, 0, HZ_UI_ID) in ssrcs

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  en Max: reabre el device (o abre+guarda fs2horizon.js en el editor de js -- no tiene autowatch)')


main()
