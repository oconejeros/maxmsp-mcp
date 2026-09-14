"""Fix the same class of bug as fix_fs2_pages_varname.py, this time for the 4 "Voces N"
advanced-strip bpatcher instances. obj-577/578/579/580 (the fs2voice_adv.maxpat instances
for V1..V4) currently have varnames "obj-156"/"obj-155"/"obj-154"/"obj-153" -- but every
"script show/hide/front/sendbox vadv1..4 ..." message in the device (obj-721/722/800/804's
Voces-tab activation chains) targets the scripting names "vadv1".."vadv4", which match no
box in the file. Confirmed live: after fixing fs2_pages' own varname, the user reported
ALL FOUR Voces tabs now show nothing under their column headers (reproduced after a full
Ableton restart, so not a stale-reload artifact). vah1..23 (the per-tab label toggles)
correctly default to hidden=1 with their scripting name matching their varname exactly,
confirming "start hidden, `script show` reveals" is this device's normal working pattern
-- vadv1-4's hidden=1 default is fine as-is; only the varname mismatch is the bug.

Unclear when this drifted (this device has been saved from both Max and Live many times
across sessions; a "closed-device" resave can silently rename an object's varname to its
auto-generated id if something about it doesn't round-trip cleanly) -- what matters is the
file's CURRENT state doesn't match what the 12 messages expect. Same fix as fs2_pages:
rename the boxes back to what the messages already say, rather than rewrite 12 messages
to auto-generated ids.

    python tools/fix_vadv_varnames.py            dry run, writes nothing
    python tools/fix_vadv_varnames.py --apply    do it (device closed in Max AND Live)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
RENAMES = {'obj-577': 'vadv1', 'obj-578': 'vadv2', 'obj-579': 'vadv3', 'obj-580': 'vadv4'}


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}

    current = {}
    for bid, target in RENAMES.items():
        b = bx[bid]
        assert b['maxclass'] == 'bpatcher' and b['name'] == 'fs2voice_adv.maxpat'
        current[bid] = b['varname']
        assert not any(bo['box'].get('varname') == target for bo in P['boxes']), \
            'ya existe otra caja con varname %s' % target

    print('varnames actuales:', current)

    for bid, target in RENAMES.items():
        bx[bid]['varname'] = target
    print('renombrado:', RENAMES)

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-vadvvarname')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {bo['box']['id']: bo['box'] for bo in doc2['patcher']['boxes']}
    for bid, target in RENAMES.items():
        assert bx2[bid]['varname'] == target, (bid, bx2[bid]['varname'])

    print('\nescrito %s (.before-vadvvarname guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: cerrar y reabrir el Live Set (o sacar/reinsertar el device)')


main()
