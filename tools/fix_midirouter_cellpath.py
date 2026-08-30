"""Midirouter: reemplaza la cadena unpack/expr/pack entre la grilla y el motor por un
`prepend cell` directo al `js`. Esa cadena dependia de que Max disparara los outlets de
`unpack 0 0 0` en el orden exacto (der->izq) para que `expr` y `pack` compusieran
`[col row]` antes de mandar `setmap` -- fragil y sin traza. Ahora el matrixctrl manda su
lista cruda `[col row val]` y el JS (`function cell`) resuelve el mapeo, con DEBUG que lo
loguea al Max Console.

  mr_xygrid:0 -> mr_echo_gate:1  (dato, sin cambios)
  mr_echo_gate:0 -> mr_cell_pre (prepend cell) -> mr_engine:0   [NUEVO]
  se borran mr_xy_up (unpack 0 0 0), mr_xy_e (expr), mr_xy_pk (pack 0 0) y sus cords.
  mr_setmap_pre (prepend setmap) se reusa como mr_cell_pre (prepend cell).

    python tools/fix_midirouter_cellpath.py            dry run
    python tools/fix_midirouter_cellpath.py --apply    escribe (backup .before-cellpath)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

DROP_VARS = ['mr_xy_up', 'mr_xy_e', 'mr_xy_pk']


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    v = {b['box'].get('varname'): b['box'] for b in P['boxes'] if b['box'].get('varname')}

    if 'mr_cell_pre' in v:
        print('mr_cell_pre ya existe -- nada que hacer')
        return
    for need in ('mr_xygrid', 'mr_echo_gate', 'mr_engine', 'mr_setmap_pre',
                 'mr_xy_up', 'mr_xy_e', 'mr_xy_pk'):
        assert need in v, 'falta %s' % need

    drop_ids = {v[n]['id'] for n in DROP_VARS}
    engine = v['mr_engine']['id']
    echo = v['mr_echo_gate']['id']
    pre = v['mr_setmap_pre']

    # repurpose prepend setmap -> prepend cell
    assert pre['text'] == 'prepend setmap', pre['text']
    pre['text'] = 'prepend cell'
    pre['varname'] = 'mr_cell_pre'
    preid = pre['id']

    # remove the 3 glue boxes
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in drop_ids]

    # drop every line touching a removed box, plus the old pack->prepend feed
    def touches(pl):
        return pl['source'][0] in drop_ids or pl['destination'][0] in drop_ids

    kept = []
    for l in P['lines']:
        pl = l['patchline']
        if touches(pl):
            continue
        kept.append(l)
    P['lines'] = kept

    # new direct path: echo_gate:0 -> mr_cell_pre:0 -> mr_engine:0
    have = {(l['patchline']['source'][0], l['patchline']['source'][1],
             l['patchline']['destination'][0], l['patchline']['destination'][1])
            for l in P['lines']}
    for src, si, dst, di in [(echo, 0, preid, 0), (preid, 0, engine, 0)]:
        if (src, si, dst, di) not in have:
            P['lines'].append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    # ---- checks ----
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    ids = [b['box']['id'] for b in P['boxes']]
    assert len(ids) == len(set(ids)), 'ids duplicados'
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            n = b['numoutlets'] if end == 'source' else b['numinlets']
            assert 0 <= eidx < n, ('outlet/inlet fuera de rango', pl, end, n)
    g = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P['lines']}
    assert (echo, preid) in g and (preid, engine) in g, 'cords nuevos faltan'
    for did in drop_ids:
        assert not any(did in (l['patchline']['source'][0], l['patchline']['destination'][0])
                       for l in P['lines']), 'quedo un cord a un box borrado'

    print('borrados: mr_xy_up, mr_xy_e, mr_xy_pk (%s)' % ', '.join(sorted(drop_ids)))
    print('mr_setmap_pre -> mr_cell_pre  (text: prepend cell)')
    print('cadena: mr_echo_gate:0 -> mr_cell_pre:0 -> mr_engine:0')
    print('boxes: %d   lines: %d' % (len(P['boxes']), len(P['lines'])))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-cellpath')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert 'mr_cell_pre' in bv and bv['mr_cell_pre']['text'] == 'prepend cell', 'readback: cell_pre'
    assert 'mr_xy_up' not in bv, 'readback: mr_xy_up sigue'
    g2 = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_echo_gate']['id'], bv['mr_cell_pre']['id']) in g2, 'readback: echo->cell_pre'
    assert (bv['mr_cell_pre']['id'], bv['mr_engine']['id']) in g2, 'readback: cell_pre->engine'
    print('\nescrito %s  (backup: %s.before-cellpath)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
