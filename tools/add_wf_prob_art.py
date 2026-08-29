"""Add the probability + per-step (Probfier-style) + articulation layers to forteseq/forteseqwf.amxd.

    python tools/add_wf_prob_art.py            dry run, writes nothing
    python tools/add_wf_prob_art.py --apply    do it

This runs AFTER tools/build_forteseqwf_presets.py (the preset/morph/marker build) -- it edits
the device as it stands now (186 boxes, obj-196 max id, the wf_uiroute / wf_ui_demux recall
stream already present). forteseqwf.js already grew the engine side (seeded xorshift RNG, the
pure helpers, the startCycle merge+decimate+roll+accent rewrite, and ~45 new config fields).

This wires the Max side:
  * ~45 new Live parameters -- 6 per-level probability, 6 per-level accent phase, Global Prob /
    Step Every / Seed, Art On / Accent Cycle / Tie / Euclid (+K/Rot), the two Normal/Accent
    velocity-figura-silence bands, and the 16-cell accent grid;
  * each -> `prepend set<verb>` -> wf_engine, per-level and per-group indices baked into the
    prepend text; the 16 grid toggles -> `pak` -> `prepend setaccentgrid`;
  * extends wf_ui_demux (obj-161) with the 29 new scalar/per-level `ui` tokens + a
    `wf_ppset_<tok>` `prepend set` per token, so recall repaints them;
  * extends wf_uiroute (obj-160) with an `accentgrid` outlet -> `unpack` -> 16 `prepend set`
    -> the grid toggles (echo on recall / on Euclid regen, without the toggles re-firing);
  * loadbang bangs the new numboxes; the `outputvalue` fan gains the new toggles.

Device edited IN PLACE. Close it in BOTH Max and Live first.
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')
JS = os.path.join(ROOT, 'forteseq', 'forteseqwf.js')

ENGINE = 'obj-6'
LOADBANG = 'obj-37'
OUTPUTVALUE = 'obj-43'
UIROUTE = 'obj-160'      # route ui presetslots presetname markertag
UI_DEMUX = 'obj-161'     # route r m n ... p6   (30 tokens, outlets 0..29 wired, 30 = reject)

ROW_Y = [9.0, 35.0, 61.0, 87.0, 113.0, 139.0]   # level-table presentation rows

# 29 new `ui` demux tokens, in order -- token k lands on demux outlet 30 + k.
UI_NEW = (['gprob', 'pstep', 'seed', 'arton', 'acyc', 'atie', 'aeuc', 'aeuck', 'aeucr',
           'nvmin', 'nvmax', 'nfig', 'nsil', 'avmin', 'avmax', 'afig', 'asil']
          + ['lprob%d' % i for i in range(1, 7)]
          + ['aphase%d' % i for i in range(1, 7)])


def numbox_vo(longname, shortname, mmin, mmax, initial, modmode):
    return {
        'parameter_initial': [initial], 'parameter_initial_enable': 1,
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_mmin': float(mmin), 'parameter_mmax': float(mmax),
        'parameter_modmode': modmode, 'parameter_type': 1, 'parameter_unitstyle': 0,
    }


def toggle_vo(longname, shortname):
    return {
        'parameter_enum': ['off', 'on'], 'parameter_initial': [0], 'parameter_initial_enable': 1,
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_mmax': 1, 'parameter_modmode': 0, 'parameter_type': 2,
    }


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes, lines = P['boxes'], P['lines']
    bx = {b['box']['id']: b['box'] for b in boxes}
    byvn = {b['box'].get('varname'): b['box'] for b in boxes}
    PP = P['parameters']
    n_boxes_before, n_lines_before = len(boxes), len(lines)
    n_params_before = len([k for k in PP if k not in ('parameterbanks', 'inherited_shortname')])

    assert byvn['wf_uiroute']['id'] == UIROUTE and byvn['wf_ui_demux']['id'] == UI_DEMUX
    assert byvn['wf_uiroute']['text'] == 'route ui presetslots presetname markertag'
    assert byvn['wf_ui_demux']['numoutlets'] == 31

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def box(**kw):
        boxes.append({'box': kw})
        return kw['id']

    def link(src, si, dst, di):
        lines.append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    pnid = [0]        # patching-view y cursor, far from everything else

    def patch_rect(w=40.0):
        pnid[0] += 1
        return [2500.0 + (pnid[0] % 8) * 170.0, 200.0 + (pnid[0] // 8) * 24.0, w, 20.0]

    param_ids = {}      # token -> box id  (for the demux repaint wiring)
    param_order = []    # (id, longname, shortname) for registry 2

    def add_numbox(varname, longname, shortname, mmin, mmax, initial, modmode, verb, token,
                   presx, presy, presw, annotation):
        bid = box(id=fresh(), maxclass='live.numbox', numinlets=1, numoutlets=2,
                  outlettype=['', 'float'], parameter_enable=1, varname=varname,
                  annotation=annotation, patching_rect=patch_rect(60.0),
                  presentation=1, presentation_rect=[presx, presy, presw, 15.0],
                  saved_attribute_attributes={'valueof': numbox_vo(longname, shortname, mmin, mmax, initial, modmode)})
        PP[bid] = [longname, shortname, 0]
        param_order.append((bid, longname, shortname))
        pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                 patching_rect=patch_rect(160.0), text='prepend ' + verb)
        link(bid, 0, pp, 0)
        link(pp, 0, ENGINE, 0)
        if token is not None:
            param_ids[token] = bid
        link(LOADBANG, 0, bid, 0)      # bang a live.numbox -> re-emits its stored value on load
        return bid

    def add_toggle(varname, longname, shortname, verb, token, presx, presy, annotation):
        bid = box(id=fresh(), maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
                  parameter_enable=1, varname=varname, annotation=annotation,
                  patching_rect=patch_rect(15.0),
                  presentation=1, presentation_rect=[presx, presy, 15.0, 15.0],
                  saved_attribute_attributes={'valueof': toggle_vo(longname, shortname)})
        PP[bid] = [longname, shortname, 0]
        param_order.append((bid, longname, shortname))
        pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                 patching_rect=patch_rect(160.0), text='prepend ' + verb)
        link(bid, 0, pp, 0)
        link(pp, 0, ENGINE, 0)
        if token is not None:
            param_ids[token] = bid
        link(OUTPUTVALUE, 0, bid, 0)   # outputvalue re-emits a toggle's state without flipping it
        return bid

    lbl_n = [0]

    def lbl(text, px, py, w):
        lbl_n[0] += 1
        box(id=fresh(), maxclass='comment', numinlets=1, numoutlets=0, text=text,
            patching_rect=patch_rect(max(w, 30.0)),
            presentation=1, presentation_rect=[px, py, w, 14.0], varname='wf_pal_lbl%d' % lbl_n[0])

    # ---------------------------------------------------------------- per-level columns
    lbl('Prb', 645.0, -5.0, 34.0)
    lbl('Ph', 686.0, -5.0, 24.0)
    for i in range(6):
        add_numbox('wf_lprob%d' % (i + 1), 'Lvl%d Prob' % (i + 1), 'L%d Prb' % (i + 1),
                   0, 100, 100, 3, 'setlevelprob %d' % (i + 1), 'lprob%d' % (i + 1),
                   645.0, ROW_Y[i], 38.0,
                   'Lvl %d Prob: %% chance each onset of level %d plays. Multiplies with Global Prob.' % (i + 1, i + 1))
        add_numbox('wf_aphase%d' % (i + 1), 'Lvl%d Phase' % (i + 1), 'L%d Ph' % (i + 1),
                   0, 15, 0, 0, 'setlevelphase %d' % (i + 1), 'aphase%d' % (i + 1),
                   686.0, ROW_Y[i], 32.0,
                   'Lvl %d Phase: offset into the accent-grid read for level %d, so levels do not accent in lockstep.' % (i + 1, i + 1))

    # ---------------------------------------------------------------- globals column (x 725)
    lbl('GProb', 725.0, 9.0, 46.0)
    add_numbox('wf_gprob', 'Global Prob', 'GProb', 0, 100, 100, 3, 'setglobalprob', 'gprob',
               775.0, 9.0, 40.0, 'Global Prob: master %% chance any onset plays. Multiplies with each level\'s Prob.')
    lbl('Step', 725.0, 28.0, 46.0)
    add_numbox('wf_pstep', 'Step Every', 'Step', 1, 8, 1, 3, 'setstepevery', 'pstep',
               775.0, 28.0, 40.0, 'Step Every N: keep only 1 of every N onsets (over the whole bar, time-ordered). 1 = keep all.')
    lbl('Seed', 725.0, 47.0, 46.0)
    add_numbox('wf_seed', 'Seed', 'Seed', 0, 999999, 1, 0, 'setseed', 'seed',
               775.0, 47.0, 55.0, 'Seed: same Seed + same settings reproduce the exact same drop / accent sequence (restarts on Run).')
    lbl('ArtOn', 725.0, 66.0, 46.0)
    add_toggle('wf_arton', 'Art On', 'Art On', 'setarton', 'arton',
               775.0, 66.0, 'Art On: apply the Normal / Accent velocity + figura + silence bands. Off = velocity / length as set per level.')
    lbl('Cycle', 725.0, 85.0, 46.0)
    add_numbox('wf_acyc', 'Accent Cycle', 'A Cyc', 1, 16, 4, 0, 'setaccentcycle', 'acyc',
               775.0, 85.0, 34.0, 'Accent Cycle: how many accent-grid cells are read before wrapping (1-16).')
    lbl('Tie', 815.0, 85.0, 22.0)
    add_toggle('wf_atie', 'Accent Tie Word', 'A Tie', 'setaccenttie', 'atie',
               837.0, 85.0, 'Accent Tie Word: read length follows the base word length M+N instead of Accent Cycle.')
    lbl('Euclid', 725.0, 104.0, 46.0)
    add_toggle('wf_aeuc', 'Accent Euclid', 'A Euc', 'seteuclid', 'aeuc',
               775.0, 104.0, 'Accent Euclid: fill the accent grid with a Euclidean pattern E(K, Cycle) rotated by Rot.')
    add_numbox('wf_aeuck', 'Accent Euclid K', 'A EucK', 0, 16, 4, 0, 'seteuclidk', 'aeuck',
               795.0, 104.0, 30.0, 'Accent Euclid K: pulse count for the Euclidean accent pattern.')
    add_numbox('wf_aeucr', 'Accent Euclid Rot', 'A EucR', 0, 15, 0, 0, 'seteuclidrot', 'aeucr',
               827.0, 104.0, 30.0, 'Accent Euclid Rot: rotation of the Euclidean accent pattern.')

    # ---------------------------------------------------------------- Normal / Accent bands
    lbl('NORMAL', 850.0, -5.0, 44.0)
    for j, (vn, ln_, sn, mn, mx, iv, verb, tok) in enumerate([
            ('wf_nvmin', 'Normal Vel Min', 'N VMin', 1, 127, 55, 'setgroupvelmin 0', 'nvmin'),
            ('wf_nvmax', 'Normal Vel Max', 'N VMax', 1, 127, 80, 'setgroupvelmax 0', 'nvmax'),
            ('wf_nfig', 'Normal Figura', 'N Fig', 1, 32, 16, 'setgroupfigura 0', 'nfig'),
            ('wf_nsil', 'Normal Silence', 'N Sil', 0, 100, 0, 'setgroupsilence 0', 'nsil')]):
        add_numbox(vn, ln_, sn, mn, mx, iv, 0, verb, tok, 850.0, 9.0 + j * 19.0, 40.0,
                   ln_ + ': Normal-group articulation value.')
    lbl('ACCENT', 900.0, -5.0, 44.0)
    for j, (vn, ln_, sn, mn, mx, iv, verb, tok) in enumerate([
            ('wf_avmin', 'Accent Vel Min', 'A VMin', 1, 127, 95, 'setgroupvelmin 1', 'avmin'),
            ('wf_avmax', 'Accent Vel Max', 'A VMax', 1, 127, 115, 'setgroupvelmax 1', 'avmax'),
            ('wf_afig', 'Accent Figura', 'A Fig', 1, 32, 8, 'setgroupfigura 1', 'afig'),
            ('wf_asil', 'Accent Silence', 'A Sil', 0, 100, 0, 'setgroupsilence 1', 'asil')]):
        add_numbox(vn, ln_, sn, mn, mx, iv, 0, verb, tok, 900.0, 9.0 + j * 19.0, 40.0,
                   ln_ + ': Accent-group articulation value.')

    # ---------------------------------------------------------------- 16-cell accent grid + pak
    lbl('Accent Grid', 850.0, 88.0, 90.0)
    GRID_PAK = box(id=fresh(), maxclass='newobj', numinlets=16, numoutlets=1, outlettype=[''],
                   patching_rect=patch_rect(260.0), text='pak ' + ' '.join(['0'] * 16), varname='wf_acc_pak')
    GRID_PREP = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                    patching_rect=patch_rect(160.0), text='prepend setaccentgrid', varname='wf_pp_accgrid')
    link(GRID_PAK, 0, GRID_PREP, 0)
    link(GRID_PREP, 0, ENGINE, 0)
    grid_ids = []
    for i in range(16):
        col, rowy = i % 8, (100.0 if i < 8 else 118.0)
        bid = box(id=fresh(), maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
                  parameter_enable=1, varname='wf_acc%d' % (i + 1),
                  annotation='Accent cell %d: 1 = this step reads the Accent group, 0 = Normal.' % (i + 1),
                  patching_rect=patch_rect(13.0),
                  presentation=1, presentation_rect=[850.0 + col * 15.0, rowy, 13.0, 13.0],
                  saved_attribute_attributes={'valueof': toggle_vo('Acc %d' % (i + 1), 'Acc%d' % (i + 1))})
        PP[bid] = ['Acc %d' % (i + 1), 'Acc%d' % (i + 1), 0]
        param_order.append((bid, 'Acc %d' % (i + 1), 'Acc%d' % (i + 1)))
        link(bid, 0, GRID_PAK, i)
        link(OUTPUTVALUE, 0, bid, 0)
        grid_ids.append(bid)

    # ---------------------------------------------------------------- extend wf_ui_demux
    demux = byvn['wf_ui_demux']
    demux['text'] = demux['text'] + ' ' + ' '.join(UI_NEW)
    demux['numinlets'] = demux['numoutlets'] = 31 + len(UI_NEW)      # 60
    demux['outlettype'] = [''] * demux['numoutlets']
    for k, tok in enumerate(UI_NEW):
        target = param_ids[tok]
        pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                 patching_rect=patch_rect(90.0), text='prepend set', varname='wf_ppset_' + tok)
        link(UI_DEMUX, 30 + k, pp, 0)     # outlet 30 was the old reject; tokens now occupy 30..58
        link(pp, 0, target, 0)

    # ---------------------------------------------------------------- extend wf_uiroute + grid echo
    uir = byvn['wf_uiroute']
    uir['text'] = uir['text'] + ' accentgrid'
    uir['numinlets'] = uir['numoutlets'] = 6
    uir['outlettype'] = [''] * 6
    GRID_UNPACK = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=16,
                      outlettype=[''] * 16, patching_rect=patch_rect(260.0),
                      text='unpack ' + ' '.join(['0'] * 16), varname='wf_accgrid_unpack')
    link(UIROUTE, 4, GRID_UNPACK, 0)      # outlet 4 = the new "accentgrid" match (old reject was 4, unwired)
    for i in range(16):
        pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                 patching_rect=patch_rect(90.0), text='prepend set', varname='wf_ppset_acc%d' % (i + 1))
        link(GRID_UNPACK, i, pp, 0)
        link(pp, 0, grid_ids[i], 0)       # `set 0/1` -> display only, no outlet -> no feedback into pak

    # ================================================================ self-checks
    ids = [b['box']['id'] for b in boxes]
    assert len(ids) == len(set(ids)), 'duplicate box id'
    idx = {b['box']['id']: b['box'] for b in boxes}
    for ln in lines:
        pl = ln['patchline']
        for lab, end in (('source', pl['source']), ('destination', pl['destination'])):
            assert isinstance(end[0], str) and end[0] in idx, (lab, end)
            b = idx[end[0]]
            nn = b.get('numoutlets', 0) if lab == 'source' else b.get('numinlets', 0)
            assert isinstance(end[1], int) and 0 <= end[1] < nn, \
                ('%s %s idx %r out of 0..%d on %s (%s)' % (lab, end[0], end[1], nn - 1, b.get('text', b.get('maxclass')), b.get('varname')))

    # registry 1 == registry 2, no leftover live.toggle[N]
    vo_names = {}
    for b in boxes:
        bb = b['box']
        vo = (bb.get('saved_attribute_attributes') or {}).get('valueof')
        if vo and bb.get('parameter_enable'):
            vo_names[bb['id']] = vo['parameter_longname']
    pp_names = {k: v[0] for k, v in PP.items() if k not in ('parameterbanks', 'inherited_shortname')}
    assert set(vo_names) == set(pp_names), set(vo_names) ^ set(pp_names)
    for k in vo_names:
        assert vo_names[k] == pp_names[k], (k, vo_names[k], pp_names[k])
    assert not any(str(nm).startswith('live.toggle') for nm in pp_names.values())

    n_new_params = len(param_order)
    assert n_new_params == 45, n_new_params
    assert len(pp_names) == n_params_before + 45, (len(pp_names), n_params_before)

    # demux repaint parity: one wf_ppset_<tok> and one demux patchline per new token
    new_ppset = [b for b in boxes if b['box'].get('varname', '') in ('wf_ppset_' + t for t in UI_NEW)]
    assert len(new_ppset) == len(UI_NEW) == 29, len(new_ppset)
    demux_new_lines = [ln for ln in lines if ln['patchline']['source'][0] == UI_DEMUX
                       and ln['patchline']['source'][1] >= 30]
    assert len(demux_new_lines) == 29, len(demux_new_lines)
    assert demux['numoutlets'] == 60

    # every new presentation_rect inside the locked panel (y in [-5, 165])
    for b in boxes:
        pr = b['box'].get('presentation_rect')
        if pr and b['box']['id'] not in bx:
            assert pr[1] >= -5.0 and pr[1] + pr[3] <= 165.0, (b['box'].get('varname'), pr)

    # presentation extent (device widens)
    right = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
               for b in boxes if b['box'].get('presentation_rect'))

    print('forteseqwf.amxd  probability + per-step + articulation build')
    print('  boxes   : %d -> %d  (+%d)' % (n_boxes_before, len(boxes), len(boxes) - n_boxes_before))
    print('  lines   : %d -> %d  (+%d)' % (n_lines_before, len(lines), len(lines) - n_lines_before))
    print('  params  : %d -> %d  (+45)' % (n_params_before, len(pp_names)))
    print('  demux   : 30 -> %d tokens' % (demux['numoutlets'] - 1))
    print('  pres.   : right edge now x %.0f (device widens)' % right)

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-probart')
    print('  backup  : %s.before-probart' % os.path.basename(DEVICE))
    amxd.save(DEVICE, data, s, e, doc)

    d2, s2, e2, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    assert len(P2['boxes']) == len(boxes) and len(P2['lines']) == len(lines)
    back = {k: v[0] for k, v in P2['parameters'].items() if k not in ('parameterbanks', 'inherited_shortname')}
    assert set(back.values()) == set(pp_names.values()), set(back.values()) ^ set(pp_names.values())
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
