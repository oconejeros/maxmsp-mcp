"""Corrective pass over the two previous one-offs (add_tonnetz_harmmode.py,
add_tonnetz_vcol.py):

1. Both scripts appended patchline dicts without the `"hidden": 1` flag every OTHER
   patchline into/out of these hidden utility chains carries in this file (loadbang ->
   outputvalue -> toggle -> prepend -> jsui). Without it, Max draws the cord as a real,
   visible line -- and since the utility objects sit far down the patcher (y ~1650) while
   the toggles sit at y=8, that cord is a long diagonal crossing the floating window's
   visible area. Confirmed by the user's screenshot (two stray diagonal lines pointing at
   the "arm" toggle). Fix: add "hidden": 1 to all 8 patchlines from both scripts.

2. tzw_vcol (the new "Col" toggle) was placed at x=330, directly on top of the existing
   `tzw_key` live.menu (the diatonic-panel root selector, also at x=330) -- so it was
   literally hidden behind another control. Confirmed by listing every box in the y<=30
   control row: the row actually runs Ton..3D (8..324), Key (330..384), KeyMode
   (390..474), KeyAuto (480..494) + its "Auto" label (497..531), THEN nothing -- x=531
   is the real end of the row. Fix: move tzw_vcol + its "Col" label there.

Run with tonnetz.amxd closed in both Max and Live.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'forteseq', 'tonnetz.amxd')

NEW_PATCHLINES = [
    ('obj-199', 0, 'obj-ov22', 0),
    ('obj-ov22', 0, 'obj-215', 0),
    ('obj-215', 0, 'obj-215p', 0),
    ('obj-215p', 0, 'obj-100', 0),
    ('obj-199', 0, 'obj-ov23', 0),
    ('obj-ov23', 0, 'obj-216', 0),
    ('obj-216', 0, 'obj-216p', 0),
    ('obj-216p', 0, 'obj-100', 0),
]


def find_box(boxes, varname):
    for entry in boxes:
        b = entry.get('box', {})
        if b.get('varname') == varname:
            return b
    raise KeyError(varname)


def main():
    data, start, end, doc = amxd.load(PATH)
    win = find_box(doc['patcher']['boxes'], 'tz_window')['patcher']

    # --- 1. hide the 8 patchlines the two prior scripts added ------------------------
    wanted = set(NEW_PATCHLINES)
    fixed = 0
    for entry in win['lines']:
        pl = entry.get('patchline', {})
        src, dst = pl.get('source'), pl.get('destination')
        if not src or not dst:
            continue
        key = (src[0], src[1], dst[0], dst[1])
        if key in wanted and not pl.get('hidden'):
            pl['hidden'] = 1
            fixed += 1
    assert fixed == len(NEW_PATCHLINES), 'expected to fix %d patchlines, fixed %d' % (len(NEW_PATCHLINES), fixed)

    # --- 2. move tzw_vcol + its label out from under tzw_key, to the real row end ----
    vcol = find_box(win['boxes'], 'tzw_vcol')
    vcol['patching_rect'] = [545.0, 8.0, 14.0, 14.0]
    vcol['patching_position'] = [545.0, 8.0]
    vcol['presentation_rect'] = [545.0, 8.0, 14.0, 14.0]
    vcol['presentation_position'] = [545.0, 8.0]

    lb_col = find_box(win['boxes'], 'tzw_lb346_8')
    lb_col['patching_rect'] = [561.0, 8.0, 24.0, 15.0]
    lb_col['patching_position'] = [561.0, 8.0]
    lb_col['presentation_rect'] = [561.0, 8.0, 24.0, 15.0]
    lb_col['presentation_position'] = [561.0, 8.0]

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # --- verify ------------------------------------------------------------------------
    _, _, _, doc2 = amxd.load(PATH)
    win2 = find_box(doc2['patcher']['boxes'], 'tz_window')['patcher']
    hidden_count = 0
    for entry in win2['lines']:
        pl = entry.get('patchline', {})
        src, dst = pl.get('source'), pl.get('destination')
        if src and dst and (src[0], src[1], dst[0], dst[1]) in wanted and pl.get('hidden') == 1:
            hidden_count += 1
    assert hidden_count == len(NEW_PATCHLINES), hidden_count
    vcol2 = find_box(win2['boxes'], 'tzw_vcol')
    assert vcol2['patching_rect'][0] == 545.0
    print('OK: all 8 patchlines hidden, tzw_vcol relocated to x=545 (clear of tzw_key).')


if __name__ == '__main__':
    main()
