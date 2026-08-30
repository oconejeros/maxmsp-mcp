"""Midirouter pestana Mapa: reemplaza el editor (matrixctrl 16x4 de puntos + 2 pianos +
readout + panels + ~9 objetos de glue) por UNA grilla `jsui` drum-rack
(`forteseq/midirouter_grid.js`) con MIDI-learn por pad. Neto: ~12 objetos menos, 0 params.

Ver el plan: C:/Users/conej/.claude/plans/midi-note-mapper-evalua-zazzy-floyd.md

Borra: mr_padgrid, mr_edit_keys, mr_setedit_pre, mr_srckey_set, mr_readout, mr_readout_set,
       mr_rackzone, mr_rack_lbl, mr_echo_gate, mr_cell_pre, mr_fb_route, mr_grid_clr
Mantiene: mr_clr_sel (sel 1 -- mr_map_clr es live.text mode 1 = toggle, emite 0 y 1),
          mr_clrall_msg, mr_mon_map (adaptado).
Agrega:  mr_grid (jsui), mr_monmap_set (prepend set), mr_setlearn_pre (prepend setlearn).
Recablea: mr_engine:1 -> mr_grid:0 ; mr_grid:0 -> mr_engine:0 ;
          mr_gate:0 -> mr_monmap_set:0 -> mr_mon_map:0  (antes gate -> mon_map directo) ;
          mr_mon_map:0 -> mr_setlearn_pre:0 -> mr_engine:0  (edicion silenciosa).
mr_mon_map: quita ignoreclick, mode 0 -> 2.
Reubica Base/Rango/Borrar en una fila bajo la grilla. Reconstruye mr_tab_m0/m1.
Agrega dependency_cache de midirouter_grid.js.

    python tools/rebuild_midirouter_jsui_grid.py            dry run
    python tools/rebuild_midirouter_jsui_grid.py --apply    escribe (backup .before-jsuigrid)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

DEL = ['mr_padgrid', 'mr_edit_keys', 'mr_setedit_pre', 'mr_srckey_set', 'mr_readout',
       'mr_readout_set', 'mr_rackzone', 'mr_rack_lbl', 'mr_echo_gate', 'mr_cell_pre',
       'mr_fb_route', 'mr_grid_clr']

FILTRO = ['mr_pitchkeys', 'mr_mon_in', 'mr_mon_pass', 'mr_mon_legend']
MAPA = ['mr_mon_map', 'mr_grid', 'mr_base', 'mr_span', 'mr_base_lbl', 'mr_span_lbl', 'mr_map_clr']

RELAYOUT = {
    'mr_mon_map':  [0.0, 17.0, 392.0, 22.0],
    'mr_grid':     [0.0, 40.0, 392.0, 100.0],
    'mr_base_lbl': [4.0, 143.0, 32.0, 12.0],
    'mr_base':     [38.0, 141.0, 40.0, 15.0],
    'mr_span_lbl': [86.0, 143.0, 40.0, 12.0],
    'mr_span':     [128.0, 141.0, 40.0, 15.0],
    'mr_map_clr':  [180.0, 141.0, 90.0, 16.0],
}


def sendbox(members, hidden):
    return ['script sendbox %s hidden %d' % (m, hidden) for m in members]


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes = P['boxes']
    lines = P['lines']
    v = {b['box'].get('varname'): b['box'] for b in boxes if b['box'].get('varname')}

    if 'mr_grid' in v:
        print('mr_grid ya existe -- nada que hacer')
        return
    need = DEL + ['mr_engine', 'mr_gate', 'mr_mon_map', 'mr_tab_m0', 'mr_tab_m1',
                  'mr_clr_sel', 'mr_clrall_msg', 'mr_base', 'mr_span']
    for n in need:
        assert n in v, 'falta %s' % n

    # sanity: mr_map_clr sigue siendo toggle -> mantener mr_clr_sel
    assert v['mr_map_clr']['maxclass'] == 'live.text' and v['mr_map_clr'].get('mode') == 1, \
        'mr_map_clr cambio de tipo -- revisar si mr_clr_sel sigue haciendo falta'

    del_ids = {v[n]['id'] for n in DEL}
    engine = v['mr_engine']['id']
    gate = v['mr_gate']['id']
    monmap_id = v['mr_mon_map']['id']

    nid = max(int(b['box']['id'].split('-')[1]) for b in boxes)
    grid_id = 'obj-%d' % (nid + 1)
    mms_id = 'obj-%d' % (nid + 2)
    slp_id = 'obj-%d' % (nid + 3)

    # -- borrar boxes + sus patchlines --
    boxes[:] = [b for b in boxes if b['box']['id'] not in del_ids]
    lines[:] = [l for l in lines
                if l['patchline']['source'][0] not in del_ids
                and l['patchline']['destination'][0] not in del_ids]

    # -- adaptar mr_mon_map: clickable + poli, y cortar el feed directo del gate --
    mm = v['mr_mon_map']
    mm.pop('ignoreclick', None)
    mm['mode'] = 2
    lines[:] = [l for l in lines
                if not (l['patchline']['source'][0] == gate
                        and l['patchline']['destination'][0] == monmap_id)]

    # -- nuevos boxes --
    boxes.append({'box': {
        'id': grid_id, 'maxclass': 'jsui', 'varname': 'mr_grid',
        'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'parameter_enable': 0, 'filename': 'midirouter_grid.js',
        'patching_rect': [900.0, 1100.0, 392.0, 100.0],
        'presentation': 1, 'presentation_rect': list(RELAYOUT['mr_grid'])}})
    boxes.append({'box': {
        'id': mms_id, 'maxclass': 'newobj', 'varname': 'mr_monmap_set',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [700.0, 640.0, 90.0, 20.0], 'text': 'prepend set'}})
    boxes.append({'box': {
        'id': slp_id, 'maxclass': 'newobj', 'varname': 'mr_setlearn_pre',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [700.0, 730.0, 110.0, 20.0], 'text': 'prepend setlearn'}})

    def add(a, ai, b, bi):
        lines.append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    add(engine, 1, grid_id, 0)          # motor -> grilla (padroutes/padbase/padspan/padarmed/padactive)
    add(grid_id, 0, engine, 0)          # grilla -> motor (arm / clearpad / refresh)
    add(gate, 0, mms_id, 0)             # gate -> prepend set -> mon_map (muestra sin re-emitir)
    add(mms_id, 0, monmap_id, 0)
    add(monmap_id, 0, slp_id, 0)        # click real en el piano -> setlearn
    add(slp_id, 0, engine, 0)

    # -- relayout --
    byid = {b['box']['id']: b['box'] for b in boxes}
    for vn, rect in RELAYOUT.items():
        (v[vn] if vn in v else byid[grid_id])['presentation_rect'] = rect

    # -- reconstruir pestanas (m0 = Filtro visible, m1 = Mapa visible) --
    v['mr_tab_m0']['text'] = ', '.join(sendbox(FILTRO, 0) + sendbox(MAPA, 1))
    v['mr_tab_m1']['text'] = ', '.join(sendbox(FILTRO, 1) + sendbox(MAPA, 0))

    # -- dependency_cache --
    dc = P.setdefault('dependency_cache', [])
    if not any(d.get('name') == 'midirouter_grid.js' for d in dc):
        dc.append({'name': 'midirouter_grid.js',
                   'bootpath': '~/PycharmProjects/maxmsp-mcp/forteseq',
                   'type': 'TEXT', 'implicit': 1})

    # ---- checks ----
    allbx = {b['box']['id']: b['box'] for b in boxes}
    ids = list(allbx)
    assert len(ids) == len(set(ids)), 'ids duplicados'
    for vn in DEL:
        assert v[vn]['id'] not in allbx, 'quedo %s' % vn
    for l in lines:
        pl = l['patchline']
        for endk in ('source', 'destination'):
            eid, eidx = pl[endk]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            cnt = b['numoutlets'] if endk == 'source' else b['numinlets']
            assert 0 <= eidx < cnt, ('outlet/inlet fuera de rango', pl, endk, cnt)
    g = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in lines}
    for a, b in [(engine, grid_id), (grid_id, engine), (gate, mms_id), (mms_id, monmap_id),
                 (monmap_id, slp_id), (slp_id, engine)]:
        assert (a, b) in g, ('cord nuevo falta', a, b)
    # nadie mas consume mr_engine outlet 1
    eng_out1 = [l for l in lines if l['patchline']['source'] == [engine, 1]]
    assert len(eng_out1) == 1 and eng_out1[0]['patchline']['destination'][0] == grid_id, \
        'mr_engine:1 debe ir solo a mr_grid'
    # presentacion dentro de 168 / 392
    pres = [b['box'] for b in boxes if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)
    assert right <= 392.0, ('presentacion pasa x392', right)
    for m in ('mr_tab_m0', 'mr_tab_m1'):
        t = v[m]['text']
        assert 'mr_grid' in t, '%s sin mr_grid' % m
        for vn in DEL:
            assert vn not in t, '%s menciona %s borrado' % (m, vn)
    assert any(d.get('name') == 'midirouter_grid.js' for d in P['dependency_cache'])
    assert 'ignoreclick' not in v['mr_mon_map'] and v['mr_mon_map']['mode'] == 2

    print('borrados (%d): %s' % (len(DEL), ', '.join(DEL)))
    print('mr_grid %s (jsui midirouter_grid.js)  mr_monmap_set %s  mr_setlearn_pre %s'
          % (grid_id, mms_id, slp_id))
    print('mr_mon_map: -ignoreclick, mode 2')
    print('boxes: %d  lines: %d  presentacion bottom %.0f right %.0f'
          % (len(boxes), len(lines), bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-jsuigrid')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert 'mr_grid' in bv and bv['mr_grid']['maxclass'] == 'jsui', 'readback: mr_grid'
    assert bv['mr_grid'].get('filename') == 'midirouter_grid.js', 'readback: filename'
    assert bv['mr_grid'].get('presentation') == 1, 'readback: presentation'
    for vn in DEL:
        assert vn not in bv, 'readback: quedo %s' % vn
    assert 'ignoreclick' not in bv['mr_mon_map'] and bv['mr_mon_map']['mode'] == 2, 'readback: mon_map'
    g2 = {(l['patchline']['source'][0], l['patchline']['source'][1],
           l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_engine']['id'], 1, bv['mr_grid']['id']) in g2, 'readback: engine:1->grid'
    assert (bv['mr_grid']['id'], 0, bv['mr_engine']['id']) in g2, 'readback: grid->engine'
    assert (bv['mr_setlearn_pre']['id'], 0, bv['mr_engine']['id']) in g2, 'readback: setlearn->engine'
    assert any(d.get('name') == 'midirouter_grid.js' for d in back.get('dependency_cache', [])), \
        'readback: dependency_cache'
    print('\nescrito %s  (backup: %s.before-jsuigrid)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
