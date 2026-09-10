"""EVENFLOW ships talking to the NOTES->TRIG bridge out of the box.

`forteseqwftrig.amxd` (tools/build_wf_trig.py) listens on "Bus EVENFLOW" = 2 by default, but
EVENFLOW's own `wf_bus` ("Bus del motor") started at 1 and `wf_buson` ("Bus On") started off, so a
fresh pair of devices was silent until both were nudged by hand. This bumps EVENFLOW's defaults:

    wf_bus   (obj-375)  parameter_initial  1 -> 2
    wf_buson (obj-377)  parameter_initial  0 -> 1

`parameter_initial_enable` is already 1 on both. The engine-var fallbacks in forteseqwf.js
(`busId` / `busOn`) were changed to match; loadbang re-emits the param values on load regardless.

    python tools/fix_wf_bus_default.py            dry run
    python tools/fix_wf_bus_default.py --apply    write (+ .before-busdefault)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')

WANT = {'wf_bus': 2, 'wf_buson': 1}


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    byvn = {b['box'].get('varname'): b['box'] for b in P['boxes']}

    for vn in WANT:
        assert vn in byvn, 'expected %s -- run add_wf_voicegroups.py first' % vn

    changed = []
    for vn, want in WANT.items():
        vo = byvn[vn]['saved_attribute_attributes']['valueof']
        cur = vo.get('parameter_initial')
        assert vo.get('parameter_initial_enable') == 1, '%s: parameter_initial_enable not 1' % vn
        if cur == [want]:
            continue
        changed.append('%s (%s): parameter_initial %s -> [%d]' % (vn, byvn[vn]['id'], cur, want))
        vo['parameter_initial'] = [want]

    if not changed:
        print('already patched (wf_bus initial [2], wf_buson initial [1]) -- nothing to do')
        return

    for line in changed:
        print('  ' + line)

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-busdefault')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    for vn, want in WANT.items():
        got = b2[vn]['saved_attribute_attributes']['valueof']['parameter_initial']
        assert got == [want], (vn, got)
    print('\nwrote %s  (backup %s.before-busdefault)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
