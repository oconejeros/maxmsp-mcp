"""In tempo-sync mode, forteseqwf only runs while the Live transport is playing.

Free-running mode (Sync off) is unchanged -- it ignores the transport, as before.

Design: the metro is left ALONE. It keeps free-running on wall-clock ms whenever Run is on
(a plain `metro 2000`, never transport-quantized, so it can never stall / fail to restart --
see the max_metro_transport_stall note). The gate lives entirely in the engine: startCycle()
checks shouldRunCycle(running, sync, transportPlaying) and silently drops the cycle when the
transport is stopped. When the transport starts again the very next metro tick plays -- no need
to re-toggle Run.

So this script only feeds the engine the transport state:
  * wf_playobs       live.observer is_playing   -- targeted off the existing wf_livepath
                     (live.path live_set) and banged by the existing wf_tempoinit trigger,
                     exactly like the tempo observer beside it;
  * wf_pp_transport  prepend settransport -> wf_engine.

No parameters, no presentation, no registry change, no existing wiring touched.
forteseqwf.js already has the engine side (transportPlaying, settransport, shouldRunCycle,
the startCycle gate, checkRunGate).

Device edited IN PLACE. Close it in BOTH Max and Live first.

    python tools/add_wf_transport_gate.py            dry run
    python tools/add_wf_transport_gate.py --apply    do it
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')

ENGINE = 'obj-6'
LIVEPATH = 'obj-86'      # live.path live_set   (outlet 0 = the live_set id)
TEMPOINIT = 'obj-94'     # trigger b b : outlet 1 -> livepath (fires first, RTL), outlet 0 -> observer bang


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes, lines = P['boxes'], P['lines']
    bx = {b['box']['id']: b['box'] for b in boxes}
    byvn = {b['box'].get('varname'): b['box'] for b in boxes}
    n_boxes_before, n_lines_before = len(boxes), len(lines)

    for i in (ENGINE, LIVEPATH, TEMPOINIT):
        assert i in bx, i
    assert bx[LIVEPATH]['text'] == 'live.path live_set'
    assert bx[TEMPOINIT]['text'] == 'trigger b b'
    assert 'wf_playobs' not in byvn, 'already applied?'
    # sanity: the tempo observer next door is wired exactly the way we are about to wire ours
    def has(src, so, dst, di):
        return any(l['patchline']['source'] == [src, so] and l['patchline']['destination'] == [dst, di]
                   for l in lines)
    assert has(LIVEPATH, 0, 'obj-89', 1) and has(TEMPOINIT, 0, 'obj-89', 0), 'tempo observer wiring not as expected'

    nid = [max(int(b['box']['id'].split('-')[1]) for b in boxes)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    px = [1120.0]

    def box(text, nin, nout, varname, w=150.0):
        px[0] += 170.0
        boxes.append({'box': {
            'id': fresh(), 'maxclass': 'newobj', 'text': text,
            'numinlets': nin, 'numoutlets': nout, 'outlettype': [''] * nout,
            'patching_rect': [px[0], 1440.0, w, 20.0], 'varname': varname,
        }})
        return boxes[-1]['box']['id']

    def link(src, so, dst, di):
        lines.append({'patchline': {'source': [src, so], 'destination': [dst, di]}})

    OBS = box('live.observer is_playing', 2, 2, 'wf_playobs')
    PPT = box('prepend settransport', 1, 1, 'wf_pp_transport')

    link(LIVEPATH, 0, OBS, 1)     # live_set id -> observer target   (set before the bang: trigger is RTL)
    link(TEMPOINIT, 0, OBS, 0)    # init bang -> emit current is_playing
    link(OBS, 0, PPT, 0)
    link(PPT, 0, ENGINE, 0)

    # ---- self-checks
    ids = [b['box']['id'] for b in boxes]
    assert len(ids) == len(set(ids)), 'dup id'
    idx = {b['box']['id']: b['box'] for b in boxes}
    for l in lines:
        pl = l['patchline']
        for lab, end in (('source', pl['source']), ('destination', pl['destination'])):
            b = idx[end[0]]
            nn = b.get('numoutlets', 0) if lab == 'source' else b.get('numinlets', 0)
            assert 0 <= end[1] < nn, ('%s %s idx %d /%d  %s' % (lab, end[0], end[1], nn, b.get('text')))
    assert has(OBS, 0, PPT, 0) and has(PPT, 0, ENGINE, 0)

    print('forteseqwf.amxd  sync mode -> transport-gated (engine gate; metro untouched)')
    print('  boxes : %d -> %d  (+%d)' % (n_boxes_before, len(boxes), len(boxes) - n_boxes_before))
    print('  lines : %d -> %d  (+%d)' % (n_lines_before, len(lines), len(lines) - n_lines_before))
    print('  new   : wf_playobs (live.observer is_playing) -> wf_pp_transport -> wf_engine')

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-transportgate')
    print('  backup: %s.before-transportgate' % os.path.basename(DEVICE))
    amxd.save(DEVICE, data, s, e, doc)

    d2, s2, e2, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    assert len(P2['boxes']) == len(boxes) and len(P2['lines']) == len(lines)
    b2 = {b['box'].get('varname'): b['box'] for b in P2['boxes']}
    assert b2['wf_playobs']['text'] == 'live.observer is_playing'
    assert b2['wf_pp_transport']['text'] == 'prepend settransport'
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
