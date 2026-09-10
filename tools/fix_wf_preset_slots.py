"""Raise EVENFLOW's preset-slot count from 20 to 64.

The bank is a sparse array and startCycle() never touches it, so the only cost of more slots is on
disk save/load (once) and one small string on Store/Recall/Clear -- there is no per-cycle / audio
cost. forteseqwf.js's `PRESET_SLOTS` is already 64; this widens the three `live.numbox` ranges that
still cap at 20:

    wf_presetslot (obj-126)  "Preset Slot"  parameter_mmax 20 -> 64
    wf_morpha     (obj-124)  "Morph A"      parameter_mmax 20 -> 64
    wf_morphb     (obj-125)  "Morph B"      parameter_mmax 20 -> 64

tools/build_forteseqwf_presets.py's PRESET_SLOTS constant was bumped for rebuild parity.
Idempotent. Close forteseqwf in BOTH Max and Live before --apply.

    python tools/fix_wf_preset_slots.py            dry run
    python tools/fix_wf_preset_slots.py --apply    write (+ .before-presetslots)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')

NEW_MAX = 64
TARGETS = ['wf_presetslot', 'wf_morpha', 'wf_morphb']


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    byvn = {b['box'].get('varname'): b['box'] for b in P['boxes']}

    changed = []
    for vn in TARGETS:
        assert vn in byvn, 'expected %s -- run build_forteseqwf_presets.py first' % vn
        vo = byvn[vn]['saved_attribute_attributes']['valueof']
        cur = vo.get('parameter_mmax')
        if int(cur) == NEW_MAX:
            continue
        changed.append('%s (%s): parameter_mmax %s -> %d' % (vn, byvn[vn]['id'], cur, NEW_MAX))
        vo['parameter_mmax'] = NEW_MAX

    if not changed:
        print('already patched (all three parameter_mmax == %d) -- nothing to do' % NEW_MAX)
        return
    for line in changed:
        print('  ' + line)

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-presetslots')
    amxd.save(DEVICE, data, s, e, doc)

    back = {b['box'].get('varname'): b['box'] for b in amxd.load(DEVICE)[3]['patcher']['boxes']}
    for vn in TARGETS:
        assert int(back[vn]['saved_attribute_attributes']['valueof']['parameter_mmax']) == NEW_MAX
    print('\nwrote %s  (backup %s.before-presetslots)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
