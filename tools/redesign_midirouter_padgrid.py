"""Midirouter: reemplaza el matrixctrl 128x64 (`mr_xygrid`, que renderiza a ~1500x600 px
con autosize y tapa todo el device) por una grilla drum-rack 16x4 (`mr_padgrid`, 64 pads,
~224x56 px) + piano clickable para elegir la nota entrante.

Nuevo flujo de edicion:
  - `mr_mon_map` (kslider) deja de ser ignoreclick: click en una tecla -> `prepend setedit`
    -> `mr_engine` fija editNote. Tocar una nota tambien la selecciona (via el JS).
  - `mr_padgrid` (matrixctrl 16 col x 4 fila, autosize, SIN one/matrix): click en un pad ->
    lista cruda `[col row val]` -> `mr_echo_gate` -> `mr_cell_pre (prepend cell)` -> engine
    `cell()` -> map[editNote] = pad. El JS mantiene el invariante de 1 pad prendido.
  - feedback de repintado igual que antes: engine outlet 1 -> `route gate gridclear cell`
    -> gate anti-eco + "clear" + set de la celda activa, ahora hacia `mr_padgrid`.

Cambios:
  - borra box `mr_xygrid` + sus 3 cords.
  - agrega `mr_padgrid` (matrixctrl) con los 3 cords equivalentes.
  - agrega `mr_setedit_pre` (prepend setedit); cord `mr_mon_map:0 -> mr_setedit_pre:0 -> mr_engine:0`.
  - `mr_mon_map`: quita `ignoreclick`.
  - `mr_tab_m0` / `mr_tab_m1`: `mr_xygrid` -> `mr_padgrid` en las listas de show/hide.

    python tools/redesign_midirouter_padgrid.py            dry run
    python tools/redesign_midirouter_padgrid.py --apply    escribe (backup .before-padgrid)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

PADGRID = {
    'maxclass': 'matrixctrl',
    'numinlets': 1,
    'numoutlets': 2,
    'outlettype': ['list', 'list'],
    'parameter_enable': 0,
    'autosize': 1,
    'columns': 16,
    'rows': 4,
    'hidden': 1,
    'patching_rect': [900.0, 420.0, 224.0, 56.0],
    'presentation': 1,
    'presentation_rect': [0.0, 44.0, 224.0, 56.0],
}


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    v = {b['box'].get('varname'): b['box'] for b in P['boxes'] if b['box'].get('varname')}

    if 'mr_padgrid' in v:
        print('mr_padgrid ya existe -- nada que hacer')
        return
    for need in ('mr_xygrid', 'mr_echo_gate', 'mr_cell_pre', 'mr_engine', 'mr_grid_clr',
                 'mr_fb_route', 'mr_mon_map', 'mr_tab_m0', 'mr_tab_m1'):
        assert need in v, 'falta %s' % need

    xy = v['mr_xygrid']['id']
    echo = v['mr_echo_gate']['id']
    engine = v['mr_engine']['id']
    gridclr = v['mr_grid_clr']['id']
    fbroute = v['mr_fb_route']['id']
    monmap = v['mr_mon_map']['id']

    nid = max(int(b['box']['id'].split('-')[1]) for b in P['boxes'])
    pad_id = 'obj-%d' % (nid + 1)
    se_id = 'obj-%d' % (nid + 2)

    padbox = dict(PADGRID)
    padbox['id'] = pad_id
    padbox['varname'] = 'mr_padgrid'
    P['boxes'].append({'box': padbox})
    P['boxes'].append({'box': {
        'id': se_id, 'maxclass': 'newobj', 'varname': 'mr_setedit_pre',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [700.0, 360.0, 110.0, 20.0], 'text': 'prepend setedit'}})

    # drop mr_xygrid box + its cords
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] != xy]
    P['lines'] = [l for l in P['lines']
                  if xy not in (l['patchline']['source'][0], l['patchline']['destination'][0])]

    def add(a, ai, b, bi):
        P['lines'].append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    add(pad_id, 0, echo, 1)        # click crudo -> gate anti-eco (dato)
    add(gridclr, 0, pad_id, 0)     # "clear" -> grilla
    add(fbroute, 2, pad_id, 0)     # "cell c r 1" -> grilla
    add(monmap, 0, se_id, 0)       # click/nota en el piano -> setedit
    add(se_id, 0, engine, 0)

    # mr_mon_map clickable
    v['mr_mon_map'].pop('ignoreclick', None)

    # tab show/hide: mr_xygrid -> mr_padgrid
    for m in ('mr_tab_m0', 'mr_tab_m1'):
        t = v[m]['text']
        assert 'mr_xygrid' in t, ('%s no menciona mr_xygrid' % m, t)
        v[m]['text'] = t.replace('mr_xygrid', 'mr_padgrid')

    # ---- checks ----
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    ids = list(allbx)
    assert len(ids) == len(set(ids)), 'ids duplicados'
    assert xy not in allbx, 'mr_xygrid sigue'
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            n = b['numoutlets'] if end == 'source' else b['numinlets']
            assert 0 <= eidx < n, ('outlet/inlet fuera de rango', pl, end, n)
    g = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P['lines']}
    for pair in [(pad_id, echo), (gridclr, pad_id), (fbroute, pad_id),
                 (monmap, se_id), (se_id, engine)]:
        assert pair in g, ('cord nuevo falta', pair)
    pres = [b['box'] for b in P['boxes'] if b['box'].get('presentation')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    print('borrado mr_xygrid (%s); nuevo mr_padgrid %s (matrixctrl 16x4)' % (xy, pad_id))
    print('nuevo mr_setedit_pre %s (prepend setedit) <- mr_mon_map (ahora clickable)' % se_id)
    print('tabs: mr_xygrid -> mr_padgrid')
    print('boxes: %d  lines: %d  presentacion bottom: %.0f' % (len(P['boxes']), len(P['lines']), bottom))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-padgrid')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert 'mr_padgrid' in bv and 'mr_xygrid' not in bv, 'readback: padgrid/xygrid'
    assert 'ignoreclick' not in bv['mr_mon_map'], 'readback: mon_map sigue ignoreclick'
    assert 'mr_padgrid' in bv['mr_tab_m1']['text'], 'readback: tab m1'
    g2 = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_mon_map']['id'], bv['mr_setedit_pre']['id']) in g2, 'readback: mon_map->setedit'
    assert (bv['mr_setedit_pre']['id'], bv['mr_engine']['id']) in g2, 'readback: setedit->engine'
    assert (bv['mr_padgrid']['id'], bv['mr_echo_gate']['id']) in g2, 'readback: padgrid->echo'
    print('\nescrito %s  (backup: %s.before-padgrid)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
