"""Reemplaza el motor puro-Max de la Fase 1b (no remapeaba, imposible de depurar a ciegas)
Y el editor de grilla-de-pads 8x8 por el modelo de `Note Mapper.amxd` que el usuario
verifico que funciona: un `js` que tiene todo el mapa, y en la pestana Mapa una GRILLA X/Y
(X = nota MIDI entrante 0..127, Y = slot de pad 0..63) con @one/column, mas el monitor de
notas entrantes y Base/Rango.

QUITA todo el motor viejo + editor 8x8:
  mr_maptable mr_heldmap mr_map_rd mr_rx mr_offdet mr_go_off mr_go_on mr_pgate mr_pt
  mr_sentsel mr_fold mr_passint mr_o mr_o_t mr_inhold mr_hm_pack mr_selin mr_pg_gate
  mr_rdsel mr_rd_t mr_rd_go mr_map_in mr_selidx mr_padgrid mr_pg_up mr_pg_idx mr_pgi_t
  mr_setmap_pk mr_rd_col mr_rd_row mr_rd_pk mr_rd_clr mr_click_gate mr_click_init mr_clr_t

DEJA: pestanas, filtro, monitores, mr_mon_map, mr_base/mr_span (+labels), mr_map_clr
(pasa a "Borrar todo"), mr_clr_sel.

AGREGA:
  mr_engine (js midirouter.js)          mr_gate:0 -> mr_engine:0 -> mr_noteout:0
  mr_setbase_pre / mr_setspan_pre       mr_base/mr_span -> prepend -> mr_engine
  mr_xygrid (matrixctrl 128x64 @one/column)  <- clic -> [col fila?/-1] -> prepend setmap -> mr_engine
  mr_echo_gate (gate 1 1)               entre mr_xygrid:0 y el manejador, cerrado durante el repintado
  mr_fb_route (route gate gridclear cell)   mr_engine:1 -> repintado de la grilla
  mr_clrall_msg (clearall)             mr_map_clr -> sel 1 -> clearall -> mr_engine

    python tools/rebuild_midirouter_engine_js.py            dry run
    python tools/rebuild_midirouter_engine_js.py --apply    escribe (backup .before-jsengine)

Cerrar el device en Max y Live antes de --apply. `midirouter.js` ya esta en forteseq/.
Idempotente (sale si `mr_engine` ya esta).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

DROP = {
    'mr_maptable', 'mr_heldmap', 'mr_map_rd', 'mr_rx', 'mr_offdet', 'mr_go_off', 'mr_go_on',
    'mr_pgate', 'mr_pt', 'mr_sentsel', 'mr_fold', 'mr_passint', 'mr_o', 'mr_o_t', 'mr_inhold',
    'mr_hm_pack', 'mr_selin', 'mr_pg_gate', 'mr_rdsel', 'mr_rd_t', 'mr_rd_go', 'mr_map_in',
    'mr_selidx', 'mr_padgrid', 'mr_pg_up', 'mr_pg_idx', 'mr_pgi_t', 'mr_setmap_pk',
    'mr_rd_col', 'mr_rd_row', 'mr_rd_pk', 'mr_rd_clr', 'mr_click_gate', 'mr_click_init',
    'mr_clr_t',
}

FILTRO = ['mr_pitchkeys', 'mr_mon_in', 'mr_mon_pass', 'mr_mon_legend']
MAPA = ['mr_mon_map', 'mr_xygrid', 'mr_base', 'mr_span', 'mr_base_lbl', 'mr_span_lbl',
        'mr_map_clr']

RELAYOUT = {
    'mr_mon_map':  [0.0, 17.0, 392.0, 24.0],
    'mr_base':     [306.0, 58.0, 40.0, 15.0],
    'mr_base_lbl': [306.0, 44.0, 60.0, 12.0],
    'mr_span':     [306.0, 88.0, 40.0, 15.0],
    'mr_span_lbl': [306.0, 74.0, 60.0, 12.0],
    'mr_map_clr':  [306.0, 118.0, 78.0, 16.0],
}


def sendbox(pairs):
    return ', '.join('script sendbox %s hidden %d' % (v, h) for v, h in pairs)


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    v = {b.get('varname'): b for b in bx.values() if b.get('varname')}

    if 'mr_engine' in v:
        print('mr_engine ya existe -- nada que hacer')
        return
    for need in ('mr_gate', 'mr_noteout', 'mr_loadbang', 'mr_base', 'mr_span', 'mr_map_clr',
                 'mr_clr_sel', 'mr_mon_map', 'mr_tab_m0', 'mr_tab_m1'):
        assert need in v, 'falta %s' % need

    drop_ids = {v[n]['id'] for n in DROP if n in v}
    gate, noteout, loadbang = v['mr_gate']['id'], v['mr_noteout']['id'], v['mr_loadbang']['id']
    clrsel = v['mr_clr_sel']['id']
    mapclr = v['mr_map_clr']['id']

    # -- borrar motor viejo + editor 8x8, y toda linea que los toque ------------------
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in drop_ids]
    P['lines'] = [l for l in P['lines']
                  if l['patchline']['source'][0] not in drop_ids
                  and l['patchline']['destination'][0] not in drop_ids]

    # mr_map_clr pasa a "Borrar todo"
    v['mr_map_clr']['text'] = 'Borrar todo'
    if 'texton' in v['mr_map_clr']:
        v['mr_map_clr']['texton'] = 'Borrar todo'

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def nx():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def nb(vn, mc, ni, no, ot, x, y, w=110.0, h=20.0, **extra):
        i = nx()
        b = {'id': i, 'maxclass': mc, 'varname': vn, 'numinlets': ni, 'numoutlets': no,
             'outlettype': ot, 'patching_rect': [x, y, w, h]}
        b.update(extra)
        P['boxes'].append({'box': b})
        return i

    eng = nb('mr_engine', 'newobj', 1, 2, ['', ''], 900.0, 210.0, 130.0,
             text='js midirouter.js',
             saved_object_attributes={'filename': 'midirouter.js', 'parameter_enable': 0})
    sb = nb('mr_setbase_pre', 'newobj', 2, 1, [''], 900.0, 150.0, text='prepend setbase')
    sp = nb('mr_setspan_pre', 'newobj', 2, 1, [''], 1020.0, 150.0, text='prepend setspan')
    smap = nb('mr_setmap_pre', 'newobj', 2, 1, [''], 900.0, 470.0, text='prepend setmap')
    clrall = nb('mr_clrall_msg', 'message', 2, 1, [''], 1140.0, 150.0, w=70.0, text='clearall')
    fbr = nb('mr_fb_route', 'newobj', 1, 4, ['', '', '', ''], 900.0, 280.0, 190.0,
             text='route gate gridclear cell')
    egate = nb('mr_echo_gate', 'newobj', 2, 1, [''], 900.0, 380.0, 70.0, text='gate 1 1')
    gclr = nb('mr_grid_clr', 'message', 2, 1, [''], 1000.0, 320.0, w=50.0, text='clear')
    xyup = nb('mr_xy_up', 'newobj', 1, 3, ['int', 'int', 'int'], 900.0, 420.0, 90.0,
              text='unpack 0 0 0')
    xye = nb('mr_xy_e', 'newobj', 2, 1, ['int'], 900.0, 445.0, 150.0,
             text='expr ($i2 ? $i1 : -1)')
    xypk = nb('mr_xy_pk', 'newobj', 2, 1, ['list'], 1000.0, 445.0, 60.0, text='pack 0 0')

    xygrid = nx()
    P['boxes'].append({'box': {
        'id': xygrid, 'maxclass': 'matrixctrl', 'varname': 'mr_xygrid',
        'numinlets': 1, 'numoutlets': 2, 'outlettype': ['list', 'list'],
        'parameter_enable': 0, 'autosize': 1, 'columns': 128, 'rows': 64,
        'one/column': 1, 'hidden': 1,
        'patching_rect': [1100.0, 420.0, 260.0, 130.0],
        'presentation': 1, 'presentation_rect': [0.0, 43.0, 300.0, 120.0],
    }})

    def L(a, ai, b, bi):
        P['lines'].append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    # camino MIDI
    L(gate, 0, eng, 0)
    L(eng, 0, noteout, 0)
    # parametros
    L(v['mr_base']['id'], 0, sb, 0)
    L(sb, 0, eng, 0)
    L(v['mr_span']['id'], 0, sp, 0)
    L(sp, 0, eng, 0)
    L(loadbang, 0, eng, 0)
    # Borrar todo
    L(mapclr, 0, clrsel, 0)
    L(clrsel, 0, clrall, 0)
    L(clrall, 0, eng, 0)
    # clic en la grilla -> setmap
    L(xygrid, 0, egate, 1)
    L(egate, 0, xyup, 0)
    L(xyup, 2, xye, 1)                # val -> $i2  (RTL 1o)
    L(xyup, 1, xye, 0)               # fila -> $i1 (hot) -> val?fila:-1
    L(xye, 0, xypk, 1)              # dest -> frio
    L(xyup, 0, xypk, 0)             # col -> caliente -> [col dest]
    L(xypk, 0, smap, 0)
    L(smap, 0, eng, 0)
    # feedback del JS -> repintar (con el gate anti-eco)
    L(eng, 1, fbr, 0)
    L(fbr, 0, egate, 0)            # gate 0/1 -> control del gate anti-eco
    L(fbr, 1, gclr, 0)            # gridclear -> "clear"
    L(gclr, 0, xygrid, 0)
    L(fbr, 2, xygrid, 0)          # cell c r 1 -> prende celda

    # retab: grupo Mapa nuevo
    v['mr_tab_m0']['text'] = sendbox([(x, 0) for x in FILTRO] + [(x, 1) for x in MAPA])
    v['mr_tab_m1']['text'] = sendbox([(x, 1) for x in FILTRO] + [(x, 0) for x in MAPA])

    # relayout de presentacion
    for vn, r in RELAYOUT.items():
        v[vn]['presentation_rect'] = r

    # dependency_cache
    dc = P.setdefault('dependency_cache', [])
    if not any(d.get('name') == 'midirouter.js' for d in dc):
        dc.append({'name': 'midirouter.js',
                   'bootpath': '~/PycharmProjects/maxmsp-mcp/forteseq',
                   'type': 'TEXT', 'implicit': 1})

    # -- chequeos -----------------------------------------------------------------
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            n = b['numoutlets'] if end == 'source' else b['numinlets']
            assert isinstance(eidx, int) and 0 <= eidx < n, ('fuera de rango', pl, end, n, b.get('text'))
    names = {b['box'].get('varname') for b in P['boxes']}
    for vn in DROP:
        assert vn not in names, ('no se borro', vn)
    tbls = {str(b['box'].get('text', '')).split()[1] for b in P['boxes']
            if str(b['box'].get('text', '')).startswith('table ')}
    assert tbls == {'mr_pitchtable'}, ('tablas inesperadas', tbls)   # solo queda la del filtro
    pres = [b['box'] for b in P['boxes'] if b['box'].get('presentation')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0 and right == 392.0, (bottom, right)

    print('motor + editor -> forteseq/midirouter.js + grilla X/Y')
    print('  mr_engine %s   mr_xygrid %s (matrixctrl 128x64 @one/column)' % (eng, xygrid))
    print('  boxes: %d   lines: %d' % (len(P['boxes']), len(P['lines'])))
    print('  vista Mapa: mon_map y17..41, grilla y43..163, Base/Rango/Borrar todo x>=306')
    print('  dependency_cache: midirouter.js')

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-jsengine')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert 'mr_engine' in b2 and 'mr_xygrid' in b2 and 'mr_maptable' not in b2, 'readback'
    assert back['dependency_cache'][0]['name'] == 'midirouter.js', 'readback dep'
    g2 = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in back['lines']}
    assert (gate, b2['mr_engine']['id']) in g2 and (b2['mr_engine']['id'], noteout) in g2, 'readback cords'
    print('\nescrito %s  (backup: %s.before-jsengine)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd  y recargar en Live')


main()
