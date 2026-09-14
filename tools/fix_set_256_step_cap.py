"""The real cause of the "Set only reaches 256" bug: Max hard-caps any INTEGER-type
(parameter_type=1) Live parameter nested inside a bpatcher at 256 discrete steps,
regardless of what parameter_mmax says. Confirmed live via the maxmsp MCP -- sending the
number 257 directly to the running fs2_set numbox (inside the fs2pages.maxpat bpatcher)
clamped it to 256 on the spot, while the same test on a TOP-LEVEL int numbox (Vel Arm,
mmax=260) worked fine. This repo already has the correct workaround in two other devices:
harmonograph.amxd's "NoteMs" (1-5000) and tonnetz.amxd's "HueC" (0-359) are both bpatcher-
nested with range > 256, and both use parameter_type=0 (float) + parameter_modmode=3
instead of type=1/modmode=4 (int) -- floats aren't subject to the 256-step table. The
numbox still displays whole numbers (parameter_unitstyle stays 0/"Int" display style);
only the underlying automation data type changes.

Fixes both places this bites: the global "Set" (fs2pages.maxpat obj-12, mmax already
351) and the 4 per-voice "V#N Set" (fs2voice_adv.maxpat obj-112, mmax already 351,
shared template instantiated x4 as V1..V4).

    python tools/fix_set_256_step_cap.py            dry run, writes nothing
    python tools/fix_set_256_step_cap.py --apply    do it (device closed in Max AND Live)
"""
import json
import os
import shutil
import sys

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
VOICE = os.path.join('forteseq', 'fs2voice_adv.maxpat')


def fix(path, box_id, expect_longname):
    pg = json.load(open(path, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    vo = bx[box_id]['saved_attribute_attributes']['valueof']
    assert vo.get('parameter_longname') == expect_longname, vo.get('parameter_longname')
    assert vo['parameter_type'] == 1 and vo['parameter_modmode'] == 4, \
        'ya no es type=1/modmode=4 -- reviso a mano (type=%r modmode=%r)' % (vo['parameter_type'], vo['parameter_modmode'])
    vo['parameter_type'] = 0
    vo['parameter_modmode'] = 3
    return pg, bx, vo


def main():
    apply_it = '--apply' in sys.argv

    pg1, bx1, vo1 = fix(PAGES, 'obj-12', 'Set')
    pg2, bx2, vo2 = fix(VOICE, 'obj-112', 'V#1 Set')

    print('%s (obj-12 "Set"): parameter_type 1->0, parameter_modmode 4->3' % PAGES)
    print('%s (obj-112 "V#1 Set", x4 instances): parameter_type 1->0, parameter_modmode 4->3' % VOICE)

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(PAGES, PAGES + '.before-stepcap')
    shutil.copyfile(VOICE, VOICE + '.before-stepcap')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg1}, f, indent=1)
    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg2}, f, indent=1)

    pgv1 = json.load(open(PAGES, encoding='utf-8'))['patcher']
    bxv1 = {b['box']['id']: b['box'] for b in pgv1['boxes']}
    got1 = bxv1['obj-12']['saved_attribute_attributes']['valueof']
    assert got1['parameter_type'] == 0 and got1['parameter_modmode'] == 3

    pgv2 = json.load(open(VOICE, encoding='utf-8'))['patcher']
    bxv2 = {b['box']['id']: b['box'] for b in pgv2['boxes']}
    got2 = bxv2['obj-112']['saved_attribute_attributes']['valueof']
    assert got2['parameter_type'] == 0 and got2['parameter_modmode'] == 3

    print('\nescrito %s y %s (.before-stepcap guardados). Sigue:' % (PAGES, VOICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: cerrar y reabrir el Live Set (o sacar/reinsertar el device)')


main()
