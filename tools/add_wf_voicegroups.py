"""Give forteseqwf (EVENFLOW) an output-routing layer: send the levels separately and/or grouped.

Runs AFTER tools/reshape_wf_perlevel.py (and can run before or after add_wf_rhythmviz.py -- they
touch disjoint regions). The engine side (forteseqwf.js) is already done: config fields `lgroup`
(per-level group 1..6) and `gchan` (per-group MIDI channel 1..16), the setlevelgroup / setgroupchannel
/ setbus / setbuson handlers, group routing in fireNote, and the `notes <bus> <group> <vel> <dur>
<pitch>` broadcast.

What this adds to forteseqwf.amxd, all in the presentation panel + an off-canvas scratch region:

  14 Live parameters
    wf_lgroup1..6   live.numbox 1..6   "Lvl N Grp"   -> prepend setlevelgroup N -> wf_engine
    wf_gchan1..6    live.numbox 1..16  "Grupo N Canal"-> prepend setgroupchannel N -> wf_engine
                                                      AND -> wf_makenoteN inlet 3 (the real channel)
    wf_bus          live.numbox 1..16  "Bus del motor"-> prepend setbus    -> wf_engine
    wf_buson        live.toggle 0/1    "Bus On"       -> prepend setbuson   -> wf_engine

  bus plumbing
    wf_notesroute   [route notes]   fed from wf_engine:0, parallel to wf_route / wf_uiroute / wf_diag
    wf_notes_send   [send FORTESEQ_NOTES]   wf_notesroute:0 -> wf_notes_send:0

  recall repaint: `lgroup1..6 gchan1..6` appended to wf_ui_demux; each demux outlet -> [prepend set]
  -> its numbox, so a preset recall repaints without re-firing (same pattern as wf_lstep2..6).
  wf_bus / wf_buson are addresses, deliberately NOT in the preset store, so they get no demux path --
  only a loadbang init, like forteseq2's bus.

Defaults are the identity map (level N -> group N -> channel N): fireNote emits the same tag it did
before and every makenote channel loads to N, so with nothing touched the MIDI output is unchanged.

Presentation: two 6-row columns ("Grp", "Canal") + a Bus cell are appended at the right edge + gap;
nothing shifts left. Panel height stays within the 165 px budget. Device edited IN PLACE -- close it
in BOTH Max and Live first.

    python tools/add_wf_voicegroups.py            dry run, writes nothing
    python tools/add_wf_voicegroups.py --apply    do it
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')

ENGINE = 'obj-6'          # js forteseqwf.js
LOADBANG = 'obj-37'       # loadbang
UI_DEMUX = 'obj-161'      # route r m n ... (recall repaint demux)
MAKENOTE = {1: 'obj-35', 2: 'obj-104', 3: 'obj-106', 4: 'obj-108', 5: 'obj-110', 6: 'obj-112'}
MAKENOTE_CHAN_INLET = 3   # makenote inlets: 0 pitch, 1 vel, 2 dur, 3 channel

MARK_VN = 'wf_lgroup1'    # idempotency marker

ROW_Y = [9.0, 35.0, 61.0, 87.0, 113.0, 139.0]
GAP = 8.0
GRP_W = 26.0
CHAN_W = 32.0
BUS_W = 40.0


def numbox_vo(longname, shortname, mmin, mmax, initial):
    return {
        'parameter_initial': [initial], 'parameter_initial_enable': 1,
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_mmin': float(mmin), 'parameter_mmax': float(mmax),
        'parameter_modmode': 3, 'parameter_type': 1, 'parameter_unitstyle': 0,
    }


def toggle_vo(longname, shortname, initial=0):
    return {
        'parameter_initial': [initial], 'parameter_initial_enable': 1,
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_mmax': 1, 'parameter_enum': ['off', 'on'],
        'parameter_modmode': 0, 'parameter_type': 2, 'parameter_unitstyle': 9,
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

    if MARK_VN in byvn:
        print('already patched (%s present) -- nothing to do' % MARK_VN)
        return

    mk_vn = {1: 'wf_makenote', 2: 'wf_makenote2', 3: 'wf_makenote3',
             4: 'wf_makenote4', 5: 'wf_makenote5', 6: 'wf_makenote6'}
    for need_vn in ['wf_engine', 'wf_loadbang', 'wf_ui_demux', 'wf_route'] + list(mk_vn.values()):
        assert need_vn in byvn, 'expected box %s not found' % need_vn
    assert byvn['wf_engine']['id'] == ENGINE
    assert byvn['wf_ui_demux']['id'] == UI_DEMUX
    for g in range(1, 7):
        assert byvn[mk_vn[g]]['id'] == MAKENOTE[g], (g, byvn[mk_vn[g]]['id'])

    demux = byvn['wf_ui_demux']
    demux_tokens = demux['text'].split()[1:]                 # route <tok...>
    n_demux_out_before = demux['numoutlets']
    assert n_demux_out_before == len(demux_tokens) + 1
    assert 'lgroup1' not in demux_tokens

    right = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
               for b in boxes if b['box'].get('presentation_rect'))
    grp_x = round(right + GAP, 1)
    chan_x = round(grp_x + GRP_W + 6.0, 1)
    bus_x = round(chan_x + CHAN_W + 12.0, 1)

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

    def patch_rect(w=60.0):
        pnid[0] += 1
        return [2600.0 + (pnid[0] % 8) * 170.0, 2000.0 + (pnid[0] // 8) * 24.0, w, 20.0]

    new_param_ids = []

    def add_numbox(vn, longname, shortname, mmin, mmax, initial, verb, px, py, pw, ann,
                   also_to=None):
        bid = box(id=fresh(), maxclass='live.numbox', numinlets=1, numoutlets=2,
                  outlettype=['', 'float'], parameter_enable=1, varname=vn, annotation=ann,
                  patching_rect=patch_rect(), presentation=1,
                  presentation_rect=[px, py, pw, 15.0],
                  saved_attribute_attributes={'valueof': numbox_vo(longname, shortname, mmin, mmax, initial)})
        PP[bid] = [longname, shortname, 0]
        new_param_ids.append(bid)
        pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                 patching_rect=patch_rect(160.0), text='prepend %s' % verb)
        link(bid, 0, pp, 0)
        link(pp, 0, ENGINE, 0)
        link(LOADBANG, 0, bid, 0)
        if also_to is not None:
            link(bid, 0, also_to[0], also_to[1])
        return bid

    # ---- headers -------------------------------------------------------------------------------
    box(id=fresh(), maxclass='comment', numinlets=1, numoutlets=0, varname='wf_lbl_grp',
        patching_rect=patch_rect(40.0), text='Grp', presentation=1,
        presentation_rect=[grp_x, -5.0, GRP_W + 6.0, 14.0])
    box(id=fresh(), maxclass='comment', numinlets=1, numoutlets=0, varname='wf_lbl_chan',
        patching_rect=patch_rect(40.0), text='Canal', presentation=1,
        presentation_rect=[chan_x, -5.0, CHAN_W + 6.0, 14.0])
    box(id=fresh(), maxclass='comment', numinlets=1, numoutlets=0, varname='wf_lbl_bus',
        patching_rect=patch_rect(60.0), text='Salida por bus FORTESEQ', presentation=1,
        presentation_rect=[bus_x, -5.0, 150.0, 14.0])

    # ---- per-level group + per-group channel -------------------------------------------------
    for i in range(1, 7):
        add_numbox('wf_lgroup%d' % i, 'Lvl%d Grp' % i, 'L%d Grp' % i, 1, 6, i,
                   'setlevelgroup %d' % i, grp_x, ROW_Y[i - 1], GRP_W,
                   ('Lvl %d: grupo de salida (1-%d). Varios niveles en el mismo grupo se mezclan '
                    'en su salida/canal; grupos distintos salen por separado.' % (i, 6)))
        add_numbox('wf_gchan%d' % i, 'Grupo%d Canal' % i, 'G%d Ch' % i, 1, 16, i,
                   'setgroupchannel %d' % i, chan_x, ROW_Y[i - 1], CHAN_W,
                   ('Grupo %d: canal MIDI de salida (1-16). Comparte canal con otro grupo para '
                    'apilarlos en el mismo destino.' % i),
                   also_to=(MAKENOTE[i], MAKENOTE_CHAN_INLET))

    # ---- bus address + on/off -------------------------------------------------------------------
    # Default bus 2 + on: matches forteseqwftrig.amxd's "Bus EVENFLOW" = 2 so the NOTES->TRIG
    # bridge works with nothing touched (see tools/fix_wf_bus_default.py for the in-place patch).
    add_numbox('wf_bus', 'Bus del motor', 'Bus', 1, 16, 2, 'setbus', bus_x, ROW_Y[1], BUS_W,
               'Direccion del bus FORTESEQ (1-16) para la difusion send FORTESEQ_NOTES. '
               'Es una direccion, no se guarda con los presets.')
    bid = box(id=fresh(), maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
              parameter_enable=1, varname='wf_buson', presentation=1,
              patching_rect=patch_rect(24.0), presentation_rect=[bus_x + BUS_W + 8.0, ROW_Y[1], 18.0, 18.0],
              annotation=('Difunde cada onset por send FORTESEQ_NOTES como '
                          '[bus, grupo, vel, dur, pitch]; un device Hub en RECIBIR con Voz = numero '
                          'de grupo recoge ese grupo en otra pista. Encendido por defecto.'),
              saved_attribute_attributes={'valueof': toggle_vo('Bus On', 'Bus On', 1)})
    PP[bid] = ['Bus On', 'Bus On', 0]
    new_param_ids.append(bid)
    pp = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
             patching_rect=patch_rect(120.0), text='prepend setbuson')
    link(bid, 0, pp, 0)
    link(pp, 0, ENGINE, 0)
    link(LOADBANG, 0, bid, 0)
    box(id=fresh(), maxclass='comment', numinlets=1, numoutlets=0, varname='wf_lbl_buson',
        patching_rect=patch_rect(40.0), text='On', presentation=1,
        presentation_rect=[bus_x + BUS_W + 8.0, ROW_Y[1] - 18.0, 24.0, 12.0])

    # ---- send FORTESEQ_NOTES arm -------------------------------------------------------------
    notesroute = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
                     varname='wf_notesroute', patching_rect=patch_rect(120.0), text='route notes')
    notes_send = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=0,
                     varname='wf_notes_send', patching_rect=patch_rect(150.0), text='send FORTESEQ_NOTES')
    link(ENGINE, 0, notesroute, 0)
    link(notesroute, 0, notes_send, 0)

    # ---- recall repaint: append lgroup1..6 gchan1..6 to the demux ---------------------------
    id_by_vn = {b['box'].get('varname'): b['box']['id'] for b in boxes}
    for k, tok in enumerate(['lgroup%d' % i for i in range(1, 7)] + ['gchan%d' % i for i in range(1, 7)]):
        demux_tokens.append(tok)
        ppset = box(id=fresh(), maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                    patching_rect=patch_rect(90.0), text='prepend set', varname='wf_ppset_' + tok)
        link(UI_DEMUX, n_demux_out_before - 1 + k, ppset, 0)   # fill from the old reject outlet on
        link(ppset, 0, id_by_vn['wf_' + tok], 0)

    demux['text'] = 'route ' + ' '.join(demux_tokens)
    demux['numinlets'] = demux['numoutlets'] = len(demux_tokens) + 1
    demux['outlettype'] = [''] * demux['numoutlets']

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

    vo_names = {}
    pp_names = {k: v[0] for k, v in PP.items() if k not in ('parameterbanks', 'inherited_shortname')}
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
    assert len(pp_names) == n_params_before + 14, (len(pp_names), n_params_before)
    assert demux['numoutlets'] == n_demux_out_before + 12

    demux_lines = [l for l in lines if l['patchline']['source'][0] == UI_DEMUX]
    assert max(l['patchline']['source'][1] for l in demux_lines) == demux['numoutlets'] - 2

    for i in range(1, 7):
        for vn in ('wf_lgroup%d' % i, 'wf_gchan%d' % i):
            pr = byvn[vn]['presentation_rect']
            assert pr[1] >= -6.0 and pr[1] + pr[3] <= 165.0, (vn, pr)
        # each gchan numbox also feeds its makenote channel inlet
        gid = byvn['wf_gchan%d' % i]['id']
        assert any(l['patchline']['source'] == [gid, 0] and
                   l['patchline']['destination'] == [MAKENOTE[i], MAKENOTE_CHAN_INLET] for l in lines), i

    right2 = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
                for b in boxes if b['box'].get('presentation_rect'))

    print('add_wf_voicegroups  ->  forteseq/forteseqwf.amxd')
    print('  boxes  : %d -> %d  (+%d)' % (n_boxes_before, len(boxes), len(boxes) - n_boxes_before))
    print('  lines  : %d -> %d  (+%d)' % (n_lines_before, len(lines), len(lines) - n_lines_before))
    print('  params : %d -> %d  (+14: wf_lgroup1..6, wf_gchan1..6, wf_bus, wf_buson)'
          % (n_params_before, len(pp_names)))
    print('  demux  : %d -> %d outlets' % (n_demux_out_before, demux['numoutlets']))
    print('  pres.  : right edge  x %.0f -> %.0f  (Grp col x%.0f, Canal col x%.0f, Bus x%.0f)'
          % (right, right2, grp_x, chan_x, bus_x))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-voicegroups')
    print('  backup : %s.before-voicegroups' % os.path.basename(DEVICE))
    amxd.save(DEVICE, data, s, e, doc)

    d2, s2, e2, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    assert len(P2['boxes']) == len(boxes) and len(P2['lines']) == len(lines)
    back = {k: v[0] for k, v in P2['parameters'].items()
            if k not in ('parameterbanks', 'inherited_shortname')}
    assert set(back.values()) == set(pp_names.values()), set(back.values()) ^ set(pp_names.values())
    b2 = {b['box'].get('varname'): b['box'] for b in P2['boxes']}
    assert b2['wf_lgroup1']['saved_attribute_attributes']['valueof']['parameter_longname'] == 'Lvl1 Grp'
    assert 'gchan6' in b2['wf_ui_demux']['text'] and 'lgroup1' in b2['wf_ui_demux']['text']
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


main()
