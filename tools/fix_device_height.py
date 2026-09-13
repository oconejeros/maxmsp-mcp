"""Fix the device's clipped presentation height: several recent additions render below the
window's actual visible bottom edge in Live.

    python tools/fix_device_height.py            dry run, writes nothing
    python tools/fix_device_height.py --apply    do it (device closed in Max AND Live)

## The bug

FORTESEQ2.amxd opens directly in presentation mode (`openinpresentation: 1`) at a FIXED size
given by `openrect` -- `[0, 0, 0, 169.0]` before this fix. Width 0 lets Max auto-size to content,
but the height, 169, is a hard ceiling: any presentation-mode box whose bottom edge falls below
y=169 is silently clipped -- not scrolled, not visible, just gone from the rendered device, even
though it is perfectly well-formed in the file and passes every structural check.

Two things added earlier in this same integration arc already crossed that line and have been
invisible in Live ever since, without anyone noticing because nothing LOOKS broken -- the device
just quietly ends a few rows short:
  * "Orn Serie Pico" (added with the rest of the Intervallic Series controls) sits at y 174-188.
  * "Ocultar Tabs" (this session) sits at y 180-195.

check_structure.py / check_params3.py both operate on the JSON graph and have no notion of a
render viewport, so neither caught this -- it only shows up by actually opening the device in
Live, which is exactly the step this whole integration has been waiting on the user for.

## The fix

Bump `openrect`'s height to comfortably clear the current lowest content (y=195) plus the same
margin the file already carried before this session (169 vs a ~155 max at the time -- about 14px):
195 + 15 = 210.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
OLD_HEIGHT = 169.0
NEW_HEIGHT = 210.0


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']

    max_extent = max(b['box']['presentation_rect'][1] + b['box']['presentation_rect'][3]
                      for b in P['boxes']
                      if b['box'].get('presentation') and b['box'].get('presentation_rect'))
    assert P['openrect'] == [0.0, 0.0, 0.0, OLD_HEIGHT], P['openrect']
    assert max_extent <= NEW_HEIGHT, 'el contenido actual (%.0f) ya no cabe en %.0f' % (max_extent, NEW_HEIGHT)

    print('contenido mas bajo actual: y+h = %.0f' % max_extent)
    print('openrect height: %.0f -> %.0f' % (OLD_HEIGHT, NEW_HEIGHT))

    P['openrect'][3] = NEW_HEIGHT

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    assert doc2['patcher']['openrect'][3] == NEW_HEIGHT

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  en Max: recarga el device completo (cerrar y reabrir en Live)')


main()
