"""Make the per-step layer per-level and regroup the panel.

Runs AFTER tools/add_wf_prob_art.py. Two changes:

  1. Per-level step. The single global "Step Every" (wf_pstep, verb setstepevery, one
     decimation over the whole time-sorted bar) becomes six per-level "Lvl N Step" numboxes
     (verb `setlevelstep N`, each decimating that level's own onsets). wf_pstep is renamed
     in place to wf_lstep1 (param slot + demux outlet reused); wf_lstep2..6 are new. The
     engine side (forteseqwf.js: config field `lstep` intA len 6, setlevelstep handler,
     per-level decimate in startCycle) is already done.

  2. Layout. Everything that is per-level -- On / U/C / L/R / Pitch and now Prb / Ph / Stp --
     sits together as one block of columns; PRESETS / MORPH shifts right of it; the globals
     strip and the Normal/Accent + grid block shift right to follow, and the now-empty
     global "Step" row is closed up.

Presentation rects only -- patching-view positions are untouched (they live in a scratch
region off-canvas). Device edited IN PLACE. Close it in BOTH Max and Live first.

    python tools/reshape_wf_perlevel.py            dry run, writes nothing
    python tools/reshape_wf_perlevel.py --apply    do it
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')

ENGINE = 'obj-6'
LOADBANG = 'obj-37'
UI_DEMUX = 'obj-161'

ROW_Y = [9.0, 35.0, 61.0, 87.0, 113.0, 139.0]

# per-level column geometry (headers on the y = -5 row)
PRB_X, PRB_W = 414.0, 34.0
PH_X, PH_W = 450.0, 26.0
STEP_X, STEP_W = 480.0, 24.0

DX_PRESET = 100.0     # PRESETS / MORPH block: shift right, clear of the new columns
DX_GLOB = 24.0        # globals strip: shift right; y also compresses (Step row removed)
DX_BAND = 44.0        # Normal / Accent + accent grid: shift right to follow

PRESET_VN = [
    'wf_lbl_presets', 'wf_lbl_slot', 'wf_presetname_readout', 'wf_slotfill_readout',
    'wf_lbl_ma', 'wf_lbl_morph', 'wf_morphrlin', 'wf_lbl_mrk', 'wf_quantr',
    'wf_lbl_rlin', 'wf_lbl_quant', 'wf_presetslot', 'wf_morph', 'wf_markermenu',
    'wf_morpha', 'wf_btn_store', 'wf_marker_readout', 'wf_lbl_mb', 'wf_morphb',
    'wf_btn_recall', 'wf_btn_clear',
]
GLOB_VN = [
    'wf_pal_lbl3', 'wf_pal_lbl5', 'wf_pal_lbl6', 'wf_pal_lbl7', 'wf_pal_lbl8', 'wf_pal_lbl9',
    'wf_gprob', 'wf_seed', 'wf_arton', 'wf_acyc', 'wf_atie', 'wf_aeuc', 'wf_aeuck', 'wf_aeucr',
]
BAND_VN = (['wf_pal_lbl10', 'wf_pal_lbl11', 'wf_pal_lbl12',
            'wf_nvmin', 'wf_nvmax', 'wf_nfig', 'wf_nsil',
            'wf_avmin', 'wf_avmax', 'wf_afig', 'wf_asil']
           + ['wf_acc%d' % i for i in range(1, 17)])


def numbox_vo(longname, shortname, mmin, mmax, initial, modmode):
    return {
        'parameter_initial': [initial], 'parameter_initial_enable': 1,
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_mmin': float(mmin), 'parameter_mmax': float(mmax),
        'parameter_modmode': modmode, 'parameter_type': 1, 'parameter_unitstyle': 0,
    }


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes, lines = P['boxes'], P['lines']
    byvn = {b['box'].get('varname'): b['box'] for b in boxes}
    PP = P['parameters']
    n_boxes_before, n_lines_before = len(boxes), len(lines)
    n_params_before = len([k for k in PP if k not in ('parameterbanks', 'inherited_shortname')])

    demux = byvn['wf_ui_demux']
    assert demux['id'] == UI_DEMUX
    demux_tokens = demux['text'].split()[1:]                 # route <tok...>
    n_demux_out_before = demux['numoutlets']
    assert 'pstep' in demux_tokens and n_demux_out_before == len(demux_tokens) + 1

    nid = [max(int(b['box']['id'].split('-')[1]) for b in boxes)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def box(**kw):
        boxes.append({'box': kw})
        return kw['id']

    def link(src, si, dst, di):
        lines.append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    pnid = [0]

    def patch_rect(w=40.0):
        pnid[0] += 1
        return [2600.0 + (pnid[0] % 8) * 170.0, 1400.0 + (pnid[0] // 8) * 24.0, w, 20.0]

    # ---------------------------------------------------------------- 1a. wf_pstep -> wf_lstep1
    pstep = byvn['wf_pstep']
    pstep_id = pstep['id']
    pstep['varname'] = 'wf_lstep1'
    pstep['annotation'] = ('Lvl 1 Step: keep only 1 of every N onsets of level 1 '
                           '(N resets each cycle). 1 = keep all.')
    pstep['presentation_rect'] = [STEP_X, ROW_Y[0], STEP_W, 15.0]
    vo = pstep['saved_attribute_attributes']['valueof']
    vo['parameter_longname'] = 'Lvl1 Step'
    vo['parameter_shortname'] = 'L1 Step'
    PP[pstep_id] = ['Lvl1 Step', 'L1 Step', 0]
    byvn['wf_lstep1'] = pstep

    for b in boxes:
        t = b['box'].get('text', '')
        if t == 'prepend setstepevery':
            b['box']['text'] = 'prepend setlevelstep 1'
    if byvn.get('wf_ppset_pstep'):
        byvn['wf_ppset_pstep']['varname'] = 'wf_ppset_lstep1'

    demux_tokens[demux_tokens.index('pstep')] = 'lstep1'

    # ---------------------------------------------------------------- 1b. wf_lstep2..6 (new)
    new_param_ids = []
    for i in range(2, 7):
        ln_, sn = 'Lvl%d Step' % i, 'L%d Step' % i
        bid = box(id=fresh(), maxclass='live.numbox', numinlets=1, numoutlets=2,
                  outlettype=['', 'float'], parameter_enable=1, varname='wf_lstep%d' % i,
                  annotation=('Lvl %d Step: keep only 1 of every N onsets of level %d '
                              '(N resets each cycle). 1 = keep all.' % (i, i)),
                  patching_rect=patch_rect(60.0),
                  presentation=1, presentation_rect=[STEP_X, ROW_Y[i - 1], STEP_W, 15.0],
                  saved_attribute_attributes={'valueof': numbox_vo(ln_, sn, 1, 8, 1, 3)})
        PP[bid] = [ln_, sn, 0]
        new_param_ids.append(bid)

        pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                 patching_rect=patch_rect(160.0), text='prepend setlevelstep %d' % i)
        link(bid, 0, pp, 0)
        link(pp, 0, ENGINE, 0)
        link(LOADBANG, 0, bid, 0)

        tok = 'lstep%d' % i
        demux_tokens.append(tok)
        ppset = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                    patching_rect=patch_rect(90.0), text='prepend set', varname='wf_ppset_' + tok)
        link(UI_DEMUX, n_demux_out_before - 1 + (i - 2), ppset, 0)   # fill from the old reject outlet on
        link(ppset, 0, bid, 0)

    demux['text'] = 'route ' + ' '.join(demux_tokens)
    demux['numinlets'] = demux['numoutlets'] = len(demux_tokens) + 1
    demux['outlettype'] = [''] * demux['numoutlets']

    # ---------------------------------------------------------------- 2. layout
    for i in range(1, 7):
        byvn['wf_lprob%d' % i]['presentation_rect'] = [PRB_X, ROW_Y[i - 1], PRB_W, 15.0]
        byvn['wf_aphase%d' % i]['presentation_rect'] = [PH_X, ROW_Y[i - 1], PH_W, 15.0]

    byvn['wf_pal_lbl1']['presentation_rect'] = [PRB_X, -5.0, PRB_W, 14.0]        # "Prb"
    byvn['wf_pal_lbl2']['presentation_rect'] = [PH_X, -5.0, PH_W, 14.0]          # "Ph"
    lbl4 = byvn['wf_pal_lbl4']                                                   # was "Step"
    lbl4['text'] = 'Stp'
    lbl4['presentation_rect'] = [STEP_X, -5.0, STEP_W, 14.0]

    for vn in PRESET_VN:
        pr = byvn[vn]['presentation_rect']
        pr[0] += DX_PRESET

    for vn in GLOB_VN:
        pr = byvn[vn]['presentation_rect']
        pr[0] += DX_GLOB
        if pr[1] > 10.0:
            pr[1] -= 19.0            # close the removed "Step" row (y 28); 47->28, 66->47, 85->66, 104->85

    for vn in BAND_VN:
        byvn[vn]['presentation_rect'][0] += DX_BAND

    # ================================================================ self-checks
    byvn = {b['box'].get('varname'): b['box'] for b in boxes}
    ids = [b['box']['id'] for b in boxes]
    assert len(ids) == len(set(ids)), 'duplicate box id'
    idx = {b['box']['id']: b['box'] for b in boxes}
    for l in lines:
        pl = l['patchline']
        for lab, end in (('source', pl['source']), ('destination', pl['destination'])):
            assert isinstance(end[0], str) and end[0] in idx, (lab, end)
            b = idx[end[0]]
            nn = b.get('numoutlets', 0) if lab == 'source' else b.get('numinlets', 0)
            assert isinstance(end[1], int) and 0 <= end[1] < nn, \
                ('%s %s idx %r out of 0..%d on %s (%s)'
                 % (lab, end[0], end[1], nn - 1, b.get('text', b.get('maxclass')), b.get('varname')))

    vo_names, pp_names = {}, {k: v[0] for k, v in PP.items()
                             if k not in ('parameterbanks', 'inherited_shortname')}
    for b in boxes:
        bb = b['box']
        vv = (bb.get('saved_attribute_attributes') or {}).get('valueof')
        if vv and bb.get('parameter_enable'):
            vo_names[bb['id']] = vv['parameter_longname']
    assert set(vo_names) == set(pp_names), set(vo_names) ^ set(pp_names)
    for k in vo_names:
        assert vo_names[k] == pp_names[k], (k, vo_names[k], pp_names[k])
    assert not any(str(nm).startswith('live.toggle') for nm in pp_names.values())
    assert len(set(pp_names.values())) == len(pp_names), 'duplicate parameter longname'

    assert len(pp_names) == n_params_before + 5, (len(pp_names), n_params_before)
    assert demux['numoutlets'] == n_demux_out_before + 5

    ppset_lstep = [b for b in boxes if b['box'].get('varname', '').startswith('wf_ppset_lstep')]
    assert len(ppset_lstep) == 6, [b['box']['varname'] for b in ppset_lstep]
    demux_lines = [l for l in lines if l['patchline']['source'][0] == UI_DEMUX]
    assert max(l['patchline']['source'][1] for l in demux_lines) == demux['numoutlets'] - 2

    for vn in ['wf_lstep%d' % i for i in range(1, 7)] + ['wf_lprob%d' % i for i in range(1, 7)] \
            + ['wf_aphase%d' % i for i in range(1, 7)] + PRESET_VN + GLOB_VN + BAND_VN \
            + ['wf_pal_lbl1', 'wf_pal_lbl2', 'wf_pal_lbl4']:
        pr = byvn[vn]['presentation_rect']
        assert pr[1] >= -6.0 and pr[1] + pr[3] <= 165.0, (vn, pr)

    right = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
               for b in boxes if b['box'].get('presentation_rect'))

    print('forteseqwf.amxd  per-level Step + panel regroup')
    print('  boxes   : %d -> %d  (+%d)' % (n_boxes_before, len(boxes), len(boxes) - n_boxes_before))
    print('  lines   : %d -> %d  (+%d)' % (n_lines_before, len(lines), len(lines) - n_lines_before))
    print('  params  : %d -> %d  (+5: wf_lstep2..6)' % (n_params_before, len(pp_names)))
    print('  demux   : %d -> %d outlets' % (n_demux_out_before, demux['numoutlets']))
    print('  pres.   : right edge now x %.0f' % right)

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-perlevelstep')
    print('  backup  : %s.before-perlevelstep' % os.path.basename(DEVICE))
    amxd.save(DEVICE, data, s, e, doc)

    d2, s2, e2, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    assert len(P2['boxes']) == len(boxes) and len(P2['lines']) == len(lines)
    back = {k: v[0] for k, v in P2['parameters'].items()
            if k not in ('parameterbanks', 'inherited_shortname')}
    assert set(back.values()) == set(pp_names.values()), set(back.values()) ^ set(pp_names.values())
    b2 = {b['box'].get('varname'): b['box'] for b in P2['boxes']}
    assert b2['wf_lstep1']['saved_attribute_attributes']['valueof']['parameter_longname'] == 'Lvl1 Step'
    assert 'lstep6' in b2['wf_ui_demux']['text'] and 'pstep' not in b2['wf_ui_demux']['text']
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
