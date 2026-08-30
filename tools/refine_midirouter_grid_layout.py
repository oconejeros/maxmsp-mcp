"""Midirouter pestana Mapa, refinamiento pedido por el usuario:

1) El piano de arriba (`mr_mon_map`) deja de mostrar la entrada en vivo y pasa a mostrar
   las NOTAS ASIGNADAS en VERDE. Click en una tecla verde -> desasigna (queda blanca).
   Click en una tecla blanca con un pad armado -> la asigna a ese pad.
   - `hkeycolor` -> verde.
   - feed: `mr_engine:1 -> mr_kroute (route srckey)`; `:0 -> mr_kset (prepend set) ->
     mr_mon_map` (verde/blanco vía `set`, sin re-emitir); `:1 (resto) -> mr_grid`.
   - click: `mr_mon_map:0 -> mr_keyclick_pre (prepend keyclick) -> mr_engine`.
   - se quitan `mr_monmap_set` y `mr_setlearn_pre` (el strip ya no monitorea la entrada).

2) Grilla más grande: se angosta a x0..338 y se hace más alta; Base/Rango/Borrar pasan a
   una columna a la derecha (x344..391).

    python tools/refine_midirouter_grid_layout.py            dry run
    python tools/refine_midirouter_grid_layout.py --apply    escribe (backup .before-gridlayout)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

GREEN = [0.40, 0.85, 0.45, 1.0]

RELAYOUT = {
    'mr_mon_map':  [0.0, 17.0, 392.0, 20.0],
    'mr_grid':     [0.0, 38.0, 338.0, 128.0],
    'mr_base_lbl': [344.0, 40.0, 46.0, 12.0],
    'mr_base':     [344.0, 53.0, 44.0, 16.0],
    'mr_span_lbl': [344.0, 78.0, 46.0, 12.0],
    'mr_span':     [344.0, 91.0, 44.0, 16.0],
    'mr_map_clr':  [343.0, 116.0, 48.0, 34.0],
}


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes = P['boxes']
    lines = P['lines']
    v = {b['box'].get('varname'): b['box'] for b in boxes if b['box'].get('varname')}

    if 'mr_kroute' in v:
        print('mr_kroute ya existe -- nada que hacer')
        return
    for n in ('mr_engine', 'mr_grid', 'mr_mon_map', 'mr_monmap_set', 'mr_setlearn_pre',
              'mr_gate', 'mr_base', 'mr_span', 'mr_base_lbl', 'mr_span_lbl', 'mr_map_clr'):
        assert n in v, 'falta %s' % n

    engine = v['mr_engine']['id']
    grid = v['mr_grid']['id']
    monmap = v['mr_mon_map']['id']
    del_ids = {v['mr_monmap_set']['id'], v['mr_setlearn_pre']['id']}

    nid = max(int(b['box']['id'].split('-')[1]) for b in boxes)
    kr_id = 'obj-%d' % (nid + 1)   # route srckey
    ks_id = 'obj-%d' % (nid + 2)   # prepend set
    kc_id = 'obj-%d' % (nid + 3)   # prepend keyclick

    # -- borrar glue viejo del strip + sus lineas + la vieja engine:1 -> grid --
    boxes[:] = [b for b in boxes if b['box']['id'] not in del_ids]
    lines[:] = [l for l in lines
                if l['patchline']['source'][0] not in del_ids
                and l['patchline']['destination'][0] not in del_ids
                and not (l['patchline']['source'] == [engine, 1]
                         and l['patchline']['destination'][0] == grid)]

    # -- nuevos objetos --
    boxes.append({'box': {
        'id': kr_id, 'maxclass': 'newobj', 'varname': 'mr_kroute',
        'numinlets': 1, 'numoutlets': 2, 'outlettype': ['', ''],
        'patching_rect': [880.0, 900.0, 90.0, 20.0], 'text': 'route srckey'}})
    boxes.append({'box': {
        'id': ks_id, 'maxclass': 'newobj', 'varname': 'mr_kset',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [880.0, 930.0, 90.0, 20.0], 'text': 'prepend set'}})
    boxes.append({'box': {
        'id': kc_id, 'maxclass': 'newobj', 'varname': 'mr_keyclick_pre',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [700.0, 690.0, 110.0, 20.0], 'text': 'prepend keyclick'}})

    def add(a, ai, b, bi):
        lines.append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    add(engine, 1, kr_id, 0)
    add(kr_id, 0, ks_id, 0)          # "srckey N v" -> "set N v"
    add(ks_id, 0, monmap, 0)         # verde/blanco en el piano, sin re-emitir
    add(kr_id, 1, grid, 0)           # el resto (padroutes/padbase/padspan/padarmed/padactive) -> jsui
    add(monmap, 0, kc_id, 0)         # click real -> keyclick
    add(kc_id, 0, engine, 0)

    # -- piano verde --
    v['mr_mon_map']['hkeycolor'] = list(GREEN)

    # -- relayout --
    byid = {b['box']['id']: b['box'] for b in boxes}
    for vn, rect in RELAYOUT.items():
        (v[vn] if vn in v else byid[grid])['presentation_rect'] = rect

    # ---- checks ----
    allbx = {b['box']['id']: b['box'] for b in boxes}
    assert len(allbx) == len(boxes), 'ids duplicados'
    for l in lines:
        pl = l['patchline']
        for endk in ('source', 'destination'):
            eid, eidx = pl[endk]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            cnt = b['numoutlets'] if endk == 'source' else b['numinlets']
            assert 0 <= eidx < cnt, ('outlet/inlet fuera de rango', pl, endk, cnt)
    g = {(l['patchline']['source'][0], l['patchline']['source'][1],
          l['patchline']['destination'][0]) for l in lines}
    for a, ai, b in [(engine, 1, kr_id), (kr_id, 0, ks_id), (ks_id, 0, monmap),
                     (kr_id, 1, grid), (monmap, 0, kc_id), (kc_id, 0, engine)]:
        assert (a, ai, b) in g, ('cord nuevo falta', a, ai, b)
    assert not any(l['patchline']['source'] == [engine, 1]
                   and l['patchline']['destination'][0] == grid for l in lines), \
        'quedo el viejo engine:1 -> grid directo'
    eng1 = [l for l in lines if l['patchline']['source'] == [engine, 1]]
    assert len(eng1) == 1 and eng1[0]['patchline']['destination'][0] == kr_id, \
        'mr_engine:1 debe ir solo a mr_kroute'
    for vn in ('mr_monmap_set', 'mr_setlearn_pre'):
        assert v[vn]['id'] not in allbx, 'quedo %s' % vn
    pres = [b['box'] for b in boxes if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)
    assert right <= 392.0, ('presentacion pasa x392', right)

    print('mr_kroute %s (route srckey)  mr_kset %s (prepend set)  mr_keyclick_pre %s' % (kr_id, ks_id, kc_id))
    print('mr_mon_map hkeycolor -> verde ; borrados mr_monmap_set, mr_setlearn_pre')
    print('grilla [0,38,338,128] ; Base/Rango/Borrar a la derecha x344')
    print('boxes: %d  lines: %d  bottom %.0f  right %.0f' % (len(boxes), len(lines), bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-gridlayout')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert 'mr_kroute' in bv and 'mr_monmap_set' not in bv and 'mr_setlearn_pre' not in bv, 'readback: boxes'
    assert bv['mr_mon_map']['hkeycolor'][1] > 0.7 and bv['mr_mon_map']['hkeycolor'][0] < 0.6, 'readback: verde'
    g2 = {(l['patchline']['source'][0], l['patchline']['source'][1],
           l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_engine']['id'], 1, bv['mr_kroute']['id']) in g2, 'readback: engine:1->kroute'
    assert (bv['mr_kroute']['id'], 1, bv['mr_grid']['id']) in g2, 'readback: kroute:1->grid'
    assert (bv['mr_keyclick_pre']['id'], 0, bv['mr_engine']['id']) in g2, 'readback: keyclick->engine'
    print('\nescrito %s  (backup: %s.before-gridlayout)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
