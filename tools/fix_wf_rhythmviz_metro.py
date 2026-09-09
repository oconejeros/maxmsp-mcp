"""Make the "Ritmos" popup refresh in real time.

add_wf_rhythmviz.py drove the ~8 Hz re-query metro from `live.thisdevice`'s device-loaded bang.
That bang does not fire on a JS-only reload (and a script-added live.thisdevice is unreliable), so
the popup only refreshed when the button's `vizon` handler called querycycle() once by hand.

This rewires the metro to the button toggle itself: `wf_rhythmviz_btn` (live.text mode 1) outputs
1 when the popup opens and 0 when it closes -> metro left inlet -> starts / stops. The
live.thisdevice + `t 1` boxes and their two cords are removed.

    python tools/fix_wf_rhythmviz_metro.py            dry run
    python tools/fix_wf_rhythmviz_metro.py --apply    write (+ .before-rhythmviz-metro)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    byvn = {b['box'].get('varname'): b['box'] for b in P['boxes']}

    for vn in ('wf_rhythmviz_btn', 'wf_rhythmviz_metro'):
        assert vn in byvn, 'expected %s -- run add_wf_rhythmviz.py first' % vn
    BTN = byvn['wf_rhythmviz_btn']['id']
    MET = byvn['wf_rhythmviz_metro']['id']
    TB1 = byvn.get('wf_rhythmviz_tb', {}).get('id')
    THISD = byvn.get('wf_rhythmviz_thisdev', {}).get('id')

    def has_line(src, si, dst, di):
        for l in P['lines']:
            pl = l['patchline']
            if pl['source'] == [src, si] and pl['destination'] == [dst, di]:
                return True
        return False

    if has_line(BTN, 0, MET, 0):
        print('already fixed (wf_rhythmviz_btn -> wf_rhythmviz_metro present) -- nothing to do')
        return

    n_lines_before, n_boxes_before = len(P['lines']), len(P['boxes'])
    drop_ids = set(x for x in (TB1, THISD) if x)

    # drop the old start chain: any line touching t 1 / live.thisdevice
    P['lines'] = [l for l in P['lines']
                  if l['patchline']['source'][0] not in drop_ids
                  and l['patchline']['destination'][0] not in drop_ids]
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in drop_ids]

    # button toggle (1 open / 0 close) starts and stops the metro
    P['lines'].append({'patchline': {'source': [BTN, 0], 'destination': [MET, 0]}})

    # ---- structural self-check (same class as check_structure.py) --------------------------
    idx = {b['box']['id']: b['box'] for b in P['boxes']}
    ids = list(idx)
    assert len(ids) == len(set(ids)), 'dup id'
    for l in P['lines']:
        pl = l['patchline']
        for lab, end in (('source', pl['source']), ('destination', pl['destination'])):
            assert end[0] in idx, (lab, end)
            b = idx[end[0]]
            nn = b.get('numoutlets', 0) if lab == 'source' else b.get('numinlets', 0)
            assert 0 <= end[1] < nn, (lab, end, b.get('text', b.get('maxclass')))

    print('fix_wf_rhythmviz_metro  ->  forteseq/forteseqwf.amxd')
    print('  removed boxes : %s' % (', '.join(sorted(drop_ids)) or '(none)'))
    print('  lines : %d -> %d   boxes : %d -> %d'
          % (n_lines_before, len(P['lines']), n_boxes_before, len(P['boxes'])))
    print('  new cord : %s:0 (Ritmos toggle) -> %s:0 (metro 120)' % (BTN, MET))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-rhythmviz-metro')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bidx = {b['box']['id']: b['box'] for b in back['boxes']}
    assert BTN in bidx and MET in bidx and not (drop_ids & set(bidx))
    assert any(l['patchline']['source'] == [BTN, 0] and l['patchline']['destination'] == [MET, 0]
               for l in back['lines'])
    print('\nwrote %s  (backup %s.before-rhythmviz-metro)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
