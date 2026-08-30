"""Midirouter: mueve el piano DENTRO del jsui (`mr_grid`).

El `kslider` `mr_mon_map` no obedecia bien el `set` programatico para pintar teclas verdes.
El jsui ya dibuja todo, asi que el piano pasa a ser una franja arriba del propio jsui, con
control total de color (verde = nota asignada, ambar = sonando).

Quita: mr_mon_map (kslider), mr_kroute (route srckey), mr_kset (prepend set),
       mr_keyclick_pre (prepend keyclick), y todas sus lineas.
Agrega: `mr_engine:1 -> mr_grid:0` directo (el jsui recibe padroutes/.../pianoassigned/noteon).
        (`mr_grid:0 -> mr_engine:0` ya existe: arm/clearpad/keyclick/refresh.)
Relayout: `mr_grid` ocupa toda el area de Mapa (x0..344), Base/Rango/Borrar en columna
          derecha x348.
Pestanas: se saca `mr_mon_map` de las listas show/hide.

    python tools/midirouter_piano_into_jsui.py            dry run
    python tools/midirouter_piano_into_jsui.py --apply    escribe (backup .before-pianojsui)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

DEL = ['mr_mon_map', 'mr_kroute', 'mr_kset', 'mr_keyclick_pre']

FILTRO = ['mr_pitchkeys', 'mr_mon_in', 'mr_mon_pass', 'mr_mon_legend']
MAPA = ['mr_grid', 'mr_base', 'mr_span', 'mr_base_lbl', 'mr_span_lbl', 'mr_map_clr']

RELAYOUT = {
    'mr_grid':     [0.0, 17.0, 344.0, 150.0],
    'mr_base_lbl': [348.0, 40.0, 44.0, 12.0],
    'mr_base':     [348.0, 53.0, 42.0, 16.0],
    'mr_span_lbl': [348.0, 78.0, 44.0, 12.0],
    'mr_span':     [348.0, 91.0, 42.0, 16.0],
    'mr_map_clr':  [347.0, 116.0, 45.0, 40.0],
}


def sb(members, hidden):
    return ['script sendbox %s hidden %d' % (m, hidden) for m in members]


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes, lines = P['boxes'], P['lines']
    v = {b['box'].get('varname'): b['box'] for b in boxes if b['box'].get('varname')}

    if 'mr_mon_map' not in v:
        print('mr_mon_map ya no existe -- nada que hacer')
        return
    for n in DEL + ['mr_engine', 'mr_grid', 'mr_tab_m0', 'mr_tab_m1', 'mr_base', 'mr_span']:
        assert n in v, 'falta %s' % n

    engine = v['mr_engine']['id']
    grid = v['mr_grid']['id']
    del_ids = {v[n]['id'] for n in DEL}

    boxes[:] = [b for b in boxes if b['box']['id'] not in del_ids]
    lines[:] = [l for l in lines
                if l['patchline']['source'][0] not in del_ids
                and l['patchline']['destination'][0] not in del_ids]

    # engine:1 -> grid directo (si no esta ya)
    have = {(l['patchline']['source'][0], l['patchline']['source'][1],
             l['patchline']['destination'][0]) for l in lines}
    if (engine, 1, grid) not in have:
        lines.append({'patchline': {'source': [engine, 1], 'destination': [grid, 0]}})

    byid = {b['box']['id']: b['box'] for b in boxes}
    for vn, rect in RELAYOUT.items():
        byid[v[vn]['id']]['presentation_rect'] = rect

    v['mr_tab_m0']['text'] = ', '.join(sb(FILTRO, 0) + sb(MAPA, 1))
    v['mr_tab_m1']['text'] = ', '.join(sb(FILTRO, 1) + sb(MAPA, 0))

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
    for vn in DEL:
        assert v[vn]['id'] not in allbx, 'quedo %s' % vn
    g = {(l['patchline']['source'][0], l['patchline']['source'][1],
          l['patchline']['destination'][0]) for l in lines}
    assert (engine, 1, grid) in g, 'falta engine:1 -> grid'
    assert (grid, 0, engine) in g, 'falta grid -> engine'
    eng1 = [l for l in lines if l['patchline']['source'] == [engine, 1]]
    assert len(eng1) == 1, 'mr_engine:1 debe ir solo a mr_grid'
    for m in ('mr_tab_m0', 'mr_tab_m1'):
        t = v[m]['text']
        assert 'mr_grid' in t and 'mr_mon_map' not in t, '%s mal' % m
    pres = [b['box'] for b in boxes if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)
    assert right <= 392.0, ('presentacion pasa x392', right)

    print('borrados: %s' % ', '.join(DEL))
    print('mr_engine:1 -> mr_grid:0 directo ; mr_grid ocupa [0,17,344,150]')
    print('boxes: %d  lines: %d  bottom %.0f  right %.0f' % (len(boxes), len(lines), bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-pianojsui')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    for vn in DEL:
        assert vn not in bv, 'readback: quedo %s' % vn
    g2 = {(l['patchline']['source'][0], l['patchline']['source'][1],
           l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_engine']['id'], 1, bv['mr_grid']['id']) in g2, 'readback: engine:1->grid'
    assert (bv['mr_grid']['id'], 0, bv['mr_engine']['id']) in g2, 'readback: grid->engine'
    assert 'mr_mon_map' not in bv['mr_tab_m1']['text'], 'readback: tab'
    print('\nescrito %s  (backup: %s.before-pianojsui)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
