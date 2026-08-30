"""Midirouter pestana Mapa, refinamiento de la visualizacion:

- la GRILLA vuelve a mostrar SOLO el pad de la nota editada (un mapeo, sin ambiguedad).
- el PIANO EDITOR (`mr_edit_keys`) pasa a `mode 2` (poli) y el JS lo usa como panorama:
  se iluminan todas las notas de entrada que tienen reasignacion. Sigue clickable para
  elegir la nota a editar.
- feedback: engine outlet 1 "srckey N v" -> `mr_fb_route` -> `prepend set` -> kslider
  (`set N v` no re-emite, no hay loop). Se saca el match "editnote" (ya no se usa).

`mr_edit_set` (prepend set) se renombra `mr_srckey_set` y se recablea a la salida "srckey".
`mr_fb_route`: `route gate gridclear cell editnote readout` -> `route gate gridclear cell readout srckey`.

    python tools/refine_midirouter_mapviz.py            dry run
    python tools/refine_midirouter_mapviz.py --apply    escribe (backup .before-mapviz2)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

OLD_ROUTE = 'route gate gridclear cell editnote readout'
NEW_ROUTE = 'route gate gridclear cell readout srckey'


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    v = {b['box'].get('varname'): b['box'] for b in P['boxes'] if b['box'].get('varname')}

    for need in ('mr_fb_route', 'mr_edit_keys', 'mr_edit_set', 'mr_readout_set'):
        assert need in v, 'falta %s' % need
    fb = v['mr_fb_route']
    if fb['text'] == NEW_ROUTE:
        print('ya aplicado -- nada que hacer')
        return
    assert fb['text'] == OLD_ROUTE, ('mr_fb_route inesperado', fb['text'])

    fb_id = fb['id']
    editset_id = v['mr_edit_set']['id']
    readoutset_id = v['mr_readout_set']['id']
    editkeys_id = v['mr_edit_keys']['id']

    # 1) piano editor -> mode 2 (panorama poli)
    v['mr_edit_keys']['mode'] = 2

    # 2) route nuevo: gate(0) gridclear(1) cell(2) readout(3) srckey(4) + reject(5)
    fb['text'] = NEW_ROUTE
    fb['numoutlets'] = 6
    fb['outlettype'] = [''] * 6

    # 3) renombrar la caja prepend set
    v['mr_edit_set']['varname'] = 'mr_srckey_set'

    # 4) recablear salidas de mr_fb_route
    def is_line(l, si, dst):
        pl = l['patchline']
        return pl['source'][0] == fb_id and pl['source'][1] == si and pl['destination'][0] == dst

    removed = added = 0
    kept = []
    for l in P['lines']:
        if is_line(l, 3, editset_id):          # viejo "editnote" -> edit_set : se elimina
            removed += 1
            continue
        if is_line(l, 4, readoutset_id):       # viejo "readout" en :4 -> ahora :3
            l['patchline']['source'][1] = 3
        kept.append(l)
    P['lines'] = kept
    assert removed == 1, ('no se quito la linea editnote->edit_set', removed)

    # nueva: "srckey" (:4) -> mr_srckey_set:0   (la linea mr_srckey_set:0 -> mr_edit_keys:0 ya existe)
    P['lines'].append({'patchline': {'source': [fb_id, 4], 'destination': [editset_id, 0]}})
    added += 1

    # ---- checks ----
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            cnt = b['numoutlets'] if end == 'source' else b['numinlets']
            assert 0 <= eidx < cnt, ('outlet/inlet fuera de rango', pl, end, cnt)
    g = {(l['patchline']['source'][0], l['patchline']['source'][1],
          l['patchline']['destination'][0]) for l in P['lines']}
    assert (fb_id, 3, readoutset_id) in g, 'readout debe salir por :3'
    assert (fb_id, 4, editset_id) in g, 'srckey debe salir por :4'
    assert (editset_id, 0, editkeys_id) in {(l['patchline']['source'][0], l['patchline']['source'][1],
                                             l['patchline']['destination'][0]) for l in P['lines']}, \
        'srckey_set -> edit_keys falta'
    assert not any(is_line(l, 3, editset_id) for l in P['lines']), 'linea vieja editnote sigue'

    print('mr_edit_keys -> mode 2 (panorama poli de notas con reasignacion)')
    print('mr_fb_route -> %s' % NEW_ROUTE)
    print('mr_edit_set -> mr_srckey_set ; alimentado por salida "srckey" (:4)')
    print('lineas: -%d +%d ; total %d' % (removed, added, len(P['lines'])))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-mapviz2')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert bv['mr_edit_keys']['mode'] == 2, 'readback: mode'
    assert bv['mr_fb_route']['text'] == NEW_ROUTE, 'readback: route'
    assert 'mr_srckey_set' in bv, 'readback: rename'
    g2 = {(l['patchline']['source'][0], l['patchline']['source'][1],
           l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_fb_route']['id'], 4, bv['mr_srckey_set']['id']) in g2, 'readback: srckey cord'
    assert (bv['mr_fb_route']['id'], 3, bv['mr_readout_set']['id']) in g2, 'readback: readout cord'
    print('\nescrito %s  (backup: %s.before-mapviz2)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
