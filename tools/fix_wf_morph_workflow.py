"""Wire the engine's morph repaint selectors so the popup / bake path can move the Live controls.

forteseqwf.js emits these on its single outlet:
    morpha <n> / morphb <n>   -- Morph A / B numbox repaint (bake + disengage push them to 0)
    morphx <x>                 -- Morph knob repaint (setmorph, incl. the popup's morph wheel)
    morphnote <text>           -- a status readout string

This adds the matching arms on wf_uiroute (obj-160):
    route ui presetslots presetname markertag accentgrid
        -> ... morpha morphb morphnote morphx
    new  wf_ppset_morpha / _morphb / _morphx  [prepend set]  -> wf_morpha (obj-124) /
         wf_morphb (obj-125) / wf_morph (obj-123)
    new  wf_morphnote_readout   comment (presentation, by the Morph controls)

`prepend set` so the numbox only repaints (no outlet re-fire back into setmorph*).

Additive + idempotent: re-running adds only the tokens/boxes that are missing (an earlier version
of this script added morpha/morphb/morphnote but not morphx). Close forteseqwf in BOTH Max and Live
before --apply.

    python tools/fix_wf_morph_workflow.py            dry run
    python tools/fix_wf_morph_workflow.py --apply    write (+ .before-morphworkflow)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')

UIROUTE = 'obj-160'
BASE_TOKENS = ['ui', 'presetslots', 'presetname', 'markertag', 'accentgrid']
# token -> (target varname, target box id, ppset varname)  or  (readout comment)
WANT = [
    ('morpha', 'wf_morpha', 'obj-124', 'wf_ppset_morpha'),
    ('morphb', 'wf_morphb', 'obj-125', 'wf_ppset_morphb'),
    ('morphnote', None, None, 'wf_morphnote_readout'),
    ('morphx', 'wf_morph', 'obj-123', 'wf_ppset_morphx'),
]


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes, lines = P['boxes'], P['lines']
    byvn = {b['box'].get('varname'): b['box'] for b in boxes}
    idx = {b['box']['id']: b['box'] for b in boxes}

    ur = idx[UIROUTE]
    assert byvn.get('wf_uiroute', {}).get('id') == UIROUTE
    toks = ur['text'].split()[1:]
    assert toks[:5] == BASE_TOKENS, toks
    n_out_before = ur['numoutlets']
    assert n_out_before == len(toks) + 1

    missing = [w for w in WANT if w[0] not in toks]
    if not missing:
        print('already patched (uiroute has %s) -- nothing to do' % ' '.join(t[0] for t in WANT))
        return
    for w in missing:
        if w[1]:
            assert byvn.get(w[1], {}).get('id') == w[2], (w[1], w[2])

    n_boxes_before, n_lines_before = len(boxes), len(lines)
    nid = [max(int(b['box']['id'][4:]) for b in boxes if b['box']['id'][4:].isdigit())]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def box(**kw):
        boxes.append({'box': kw})
        return kw['id']

    def link(src, so, dst, di):
        lines.append({'patchline': {'source': [src, so], 'destination': [dst, di]}})

    SX, SY = 1500.0, 5200.0
    dy = [0]

    # append the missing tokens, giving each its own new outlet just past the current set
    for tok, tgt_vn, tgt_id, pp_vn in missing:
        out_i = len(toks)                       # index of the outlet this token will own
        toks.append(tok)
        if pp_vn == 'wf_morphnote_readout':
            note = box(id=fresh(), maxclass='comment', numinlets=1, numoutlets=0,
                       varname='wf_morphnote_readout', text='-', presentation=1,
                       presentation_rect=[420.0, 126.0, 208.0, 14.0],
                       patching_rect=[SX, SY + dy[0], 240.0, 18.0])
            link(UIROUTE, out_i, note, 0)
        else:
            pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                     varname=pp_vn, patching_rect=[SX, SY + dy[0], 90.0, 20.0], text='prepend set')
            link(UIROUTE, out_i, pp, 0)
            link(pp, 0, tgt_id, 0)
        dy[0] += 26

    ur['text'] = 'route ' + ' '.join(toks)
    ur['numinlets'] = ur['numoutlets'] = len(toks) + 1
    ur['outlettype'] = [''] * ur['numoutlets']

    def check(pp, where='root'):
        by = {}
        for b in pp.get('boxes', []):
            bx = b['box']
            assert bx['id'] not in by, '%s dup id %s' % (where, bx['id'])
            by[bx['id']] = bx
        for ln in pp.get('lines', []):
            pl = ln['patchline']
            for tag, end in (('src', pl['source']), ('dst', pl['destination'])):
                bx = by.get(end[0])
                assert bx, '%s %s -> unknown %s' % (where, tag, end)
                cnt = bx.get('numoutlets', 0) if tag == 'src' else bx.get('numinlets', 0)
                assert 0 <= end[1] < cnt, '%s %s %s idx %d not in 0..%d' % (where, tag, end[0], end[1], cnt - 1)
        for b in pp.get('boxes', []):
            if b['box'].get('patcher'):
                check(b['box']['patcher'], where + '::' + b['box']['id'])
    check(P)

    print('fix_wf_morph_workflow  ->  forteseq/forteseqwf.amxd')
    print('  added tokens : %s' % ' '.join(t[0] for t in missing))
    print('  wf_uiroute   : %s  (%d -> %d outlets)' % (ur['text'], n_out_before, ur['numoutlets']))
    print('  boxes : %d -> %d   lines : %d -> %d'
          % (n_boxes_before, len(boxes), n_lines_before, len(lines)))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-morphworkflow')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    for w in WANT:
        assert w[0] in b2['wf_uiroute']['text'].split(), w[0]
    assert b2['wf_ppset_morphx']['text'] == 'prepend set'
    print('\nwrote %s  (backup %s.before-morphworkflow)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
