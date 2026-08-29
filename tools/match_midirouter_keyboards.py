"""Make Midirouter's three keyboards identical: same key span and same size.

After add_midirouter_notemon the filter kslider (mr_pitchkeys) still had its default
key span while the two monitors were an explicit 88-key A0..C8, so the columns didn't
line up and the filter looked bigger. This sets all three to offset 21 / range 88 and
the same presentation rect, restacked to fit the device's fixed 169 px height:

  mr_pitchkeys  y  2..50    filter (click to pick allowed pitches)
  mr_mon_in     y 52..100   amber : every note in
  mr_mon_pass   y102..150   green : notes passed to Live
  legend        y152..166

Widening the filter's span only adds clickable pitches (the pitch table is 128 slots
either way); nothing below note 21 was reachable by ear anyway. Close the device in
Max AND Live first. Idempotent.

    python tools/match_midirouter_keyboards.py            dry run
    python tools/match_midirouter_keyboards.py --apply    do it (backup: .before-kbmatch)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

OFFSET, RANGE = 21, 88
X, W, H, GAP = 0.0, 392.0, 48.0, 2.0
TOP = 2.0


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): b for b in bx.values() if b.get('varname')}

    filt = bv['mr_pitchkeys']
    mon_in = bv['mr_mon_in']
    mon_pass = bv['mr_mon_pass']
    legend = bv['mr_mon_legend']

    rows = [(filt, TOP), (mon_in, TOP + H + GAP), (mon_pass, TOP + 2 * (H + GAP))]
    for box, y in rows:
        box['offset'] = OFFSET
        box['range'] = RANGE
        box['presentation_rect'] = [X, y, W, H]
    filt['patching_rect'] = [400.0, 50.0, W, H]
    mon_in['patching_rect'] = [780.0, 60.0, W, H]
    mon_pass['patching_rect'] = [780.0, 120.0, W, H]

    leg_y = TOP + 3 * (H + GAP)
    legend['presentation_rect'] = [X + 2.0, leg_y, W - 4.0, 14.0]
    bottom = leg_y + 14.0

    print('all three keyboards: offset %d, range %d, size %.0f x %.0f' % (OFFSET, RANGE, W, H))
    for box, y in rows:
        print('  %-13s y %.0f..%.0f' % (box['varname'], y, y + H))
    print('  %-13s y %.0f..%.0f' % (legend['varname'], leg_y, bottom))
    print('device height 169  ->  content ends at %.0f' % bottom)
    assert bottom <= 169.0, bottom

    if not apply_it:
        print('\n(dry run -- re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-kbmatch')
    amxd.save(DEVICE, data, s, e, doc)

    back = {b['box']['id']: b['box'] for b in amxd.load(DEVICE)[3]['patcher']['boxes']}
    for vn in ('mr_pitchkeys', 'mr_mon_in', 'mr_mon_pass'):
        b = next(x for x in back.values() if x.get('varname') == vn)
        assert b.get('range') == RANGE and b.get('offset') == OFFSET, (vn, b.get('offset'), b.get('range'))
        assert b['presentation_rect'][2:] == [W, H], (vn, b['presentation_rect'])
    print('\nwrote %s  (backup: %s.before-kbmatch)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
