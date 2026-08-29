"""One-line fix: the marker umenu -> coll patchline was taking the umenu's MIDDLE outlet
(the item label as a symbol) instead of the LEFT outlet (the item number as an int). coll
was being handed 'n_1.800_L5' as an address, had no such key, and emitted nothing -- so
picking a marker never moved R.

    python tools/fix_wf_markermenu_outlet.py            dry run
    python tools/fix_wf_markermenu_outlet.py --apply    flip source outlet 1 -> 0

Close forteseqwf.amxd in Max and Live first. Idempotent.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'forteseqwf.amxd')


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    menu = next(i for i, b in bx.items() if b.get('varname') == 'wf_markermenu')
    coll = next(i for i, b in bx.items() if b.get('varname') == 'wf_markers')

    hits = [ln['patchline'] for ln in P['lines']
            if ln['patchline']['source'][0] == menu and ln['patchline']['destination'][0] == coll]
    assert len(hits) == 1, hits
    pl = hits[0]
    print('wf_markermenu(%s) outlet %d -> wf_markers(%s) inlet %d' % (menu, pl['source'][1], coll, pl['destination'][1]))
    if pl['source'][1] == 0:
        print('already fixed -- nothing to do')
        return
    pl['source'][1] = 0
    print('-> changed source outlet to 0 (item number)')

    if not apply_it:
        print('\n(dry run -- re-run with --apply)')
        return
    shutil.copyfile(DEVICE, DEVICE + '.before-menufix')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box']['id']: b['box'] for b in back['boxes']}
    m2 = next(i for i, b in b2.items() if b.get('varname') == 'wf_markermenu')
    ok = [ln for ln in back['lines'] if ln['patchline']['source'] == [m2, 0]
          and b2[ln['patchline']['destination'][0]].get('varname') == 'wf_markers']
    assert ok, 'readback: fixed patchline not found'
    print('\nwrote %s  (backup: %s.before-menufix)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
