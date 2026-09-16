"""Bump the oversized canvas of the floating "Proximos 16 pasos" popup so it comfortably
covers any real monitor, not just monitors up to 2600x1500.

    python tools/fix_fs2horizon_popup_size.py            dry run, writes nothing
    python tools/fix_fs2horizon_popup_size.py --apply    do it (device closed in Max AND Live)

## The bug

fs2horizon.js / fs2setpick.js can't write box.rect from inside the M4L popup (read-only there --
see the comment at the top of fs2horizon.js), so the jsui boxes that back that floating window
are deliberately left OVERSIZED and paint() draws within viewportWH(), which follows the real
window size (SELF.patcher.wind.size). That only works as long as the real window never exceeds
the oversized box. It was set to 2600x1500 -- comfortably bigger than the device's usual laptop-
screen use, but smaller than a maximized window on a 4K/ultrawide second monitor. When the real
window exceeds that, paint() lays out content (the "forma" bar, the per-voice columns) against a
canvas bigger than what the jsui box can actually show, and the excess area is never repainted --
Windows leaves stale/duplicated content from the previous frame there, which is the ghosting the
user saw on a second-monitor maximize.

## The fix

Bump presentation_rect for both jsui boxes in that popup (fs2hz_ui = fs2horizon.js, fs2sp_ui =
fs2setpick.js -- the two views are mutually exclusive but share the same window, so both need
headroom) to 7680x4320 (8K). No real monitor gets anywhere near that, so this is a practical
ceiling rather than true dynamic resizing -- see the max-bpatcher-paging memory note for the
`script sendbox` approach that could make this genuinely dynamic later.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
POPUP_TITLE = 'FORTESEQ2 - Proximos 16 pasos'
NEW_W, NEW_H = 7680.0, 4320.0
TARGET_VARNAMES = ('fs2hz_ui', 'fs2sp_ui')


def find_popup(patcher):
    if patcher.get('title') == POPUP_TITLE:
        return patcher
    for box in patcher.get('boxes', []):
        sub = box.get('box', {}).get('patcher')
        if sub:
            found = find_popup(sub)
            if found:
                return found
    return None


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    popup = find_popup(doc['patcher'])
    assert popup is not None, 'no se encontro el subpatcher popup %r' % POPUP_TITLE

    targets = {b['box']['varname']: b['box'] for b in popup['boxes']
               if b['box'].get('varname') in TARGET_VARNAMES}
    assert set(targets) == set(TARGET_VARNAMES), 'faltan cajas: %r' % (set(TARGET_VARNAMES) - set(targets))

    for varname, box in targets.items():
        rect = box['presentation_rect']
        print('%s presentation_rect: %r -> [%.1f, %.1f, %.1f, %.1f]' % (varname, rect, rect[0], rect[1], NEW_W, NEW_H))
        rect[2] = NEW_W
        rect[3] = NEW_H

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    popup2 = find_popup(doc2['patcher'])
    for b in popup2['boxes']:
        if b['box'].get('varname') in TARGET_VARNAMES:
            assert b['box']['presentation_rect'][2] == NEW_W
            assert b['box']['presentation_rect'][3] == NEW_H

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  en Max/Live: recarga el device completo (cerrar y reabrir)')


main()
