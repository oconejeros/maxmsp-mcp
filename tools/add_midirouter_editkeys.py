"""Midirouter: separa el piano en DOS en la pestana Mapa.

Problema: `mr_mon_map` era clickable Y estaba alimentado por `mr_midiparse` -> el kslider
re-emite lo que recibe por el inlet, asi cada nota entrante disparaba `setedit` y editNote
saltaba solo. Imposible fijar un pad con un clip corriendo.

Fix:
  - `mr_mon_map` vuelve a ser monitor puro (ignoreclick 1); se corta su cord a setedit.
  - `mr_edit_keys` (kslider mode 1, verde, clickable, NO alimentado por midiparse) = piano
    editor. Click en una tecla -> `mr_setedit_pre (prepend setedit)` -> engine fija editNote.
  - el engine refleja editNote de vuelta: outlet 1 "editnote N" -> `mr_fb_route` (nuevo 4to
    match) -> `mr_edit_set (prepend set)` -> `mr_edit_keys` (set no re-emite -> sin loop).
  - relayout Mapa: monitor y17, editor y41, grilla y66, Base/Rango/Borrar a la derecha.
  - `mr_edit_keys` sumado a las listas show/hide de las pestanas.

    python tools/add_midirouter_editkeys.py            dry run
    python tools/add_midirouter_editkeys.py --apply    escribe (backup .before-editkeys)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

RELAYOUT = {
    'mr_mon_map':  [0.0, 17.0, 392.0, 22.0],
    'mr_edit_keys': [0.0, 41.0, 392.0, 22.0],
    'mr_padgrid':  [0.0, 66.0, 224.0, 56.0],
    'mr_base_lbl': [306.0, 66.0, 60.0, 12.0],
    'mr_base':     [306.0, 80.0, 40.0, 15.0],
    'mr_span_lbl': [306.0, 98.0, 60.0, 12.0],
    'mr_span':     [306.0, 112.0, 40.0, 15.0],
    'mr_map_clr':  [306.0, 134.0, 78.0, 16.0],
}


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    v = {b['box'].get('varname'): b['box'] for b in P['boxes'] if b['box'].get('varname')}

    if 'mr_edit_keys' in v:
        print('mr_edit_keys ya existe -- nada que hacer')
        return
    for need in ('mr_mon_map', 'mr_setedit_pre', 'mr_engine', 'mr_fb_route',
                 'mr_tab_m0', 'mr_tab_m1'):
        assert need in v, 'falta %s' % need

    setedit = v['mr_setedit_pre']['id']
    engine = v['mr_engine']['id']
    monmap = v['mr_mon_map']['id']
    fbroute = v['mr_fb_route']

    nid = max(int(b['box']['id'].split('-')[1]) for b in P['boxes'])
    ek_id = 'obj-%d' % (nid + 1)
    es_id = 'obj-%d' % (nid + 2)

    # piano editor (verde, monofonico, clickable)
    P['boxes'].append({'box': {
        'id': ek_id, 'maxclass': 'kslider', 'varname': 'mr_edit_keys',
        'numinlets': 2, 'numoutlets': 2, 'outlettype': ['int', 'int'],
        'mode': 1, 'parameter_enable': 0, 'offset': 21, 'range': 88,
        'hkeycolor': [0.4, 0.8, 0.45, 1.0], 'hidden': 1,
        'patching_rect': [500.0, 320.0, 392.0, 22.0],
        'presentation': 1, 'presentation_rect': [0.0, 41.0, 392.0, 22.0]}})
    # prepend set para reflejar editNote sin re-emitir
    P['boxes'].append({'box': {
        'id': es_id, 'maxclass': 'newobj', 'varname': 'mr_edit_set',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [500.0, 290.0, 90.0, 20.0], 'text': 'prepend set'}})

    # mr_fb_route: agregar match "editnote"
    assert fbroute['text'] == 'route gate gridclear cell', fbroute['text']
    fbroute['text'] = 'route gate gridclear cell editnote'
    fbroute['numoutlets'] = 5
    fbroute['outlettype'] = ['', '', '', '', '']
    fb_id = fbroute['id']

    # cortar mon_map -> setedit ; restaurar ignoreclick
    P['lines'] = [l for l in P['lines']
                  if not (l['patchline']['source'][0] == monmap
                          and l['patchline']['destination'][0] == setedit)]
    v['mr_mon_map']['ignoreclick'] = 1

    def add(a, ai, b, bi):
        P['lines'].append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    add(ek_id, 0, setedit, 0)       # click en el piano editor -> setedit
    add(fb_id, 3, es_id, 0)         # "editnote N" -> prepend set
    add(es_id, 0, ek_id, 0)        # set N -> piano editor (sin re-emitir)

    byid = {b['box']['id']: b['box'] for b in P['boxes']}
    for vn, rect in RELAYOUT.items():
        box = v[vn] if vn in v else byid[ek_id]
        box['presentation_rect'] = rect

    # tabs: sumar mr_edit_keys (oculto en Filtro, visible en Mapa)
    m0 = v['mr_tab_m0']
    m1 = v['mr_tab_m1']
    if 'mr_edit_keys' not in m0['text']:
        m0['text'] = m0['text'] + ', script sendbox mr_edit_keys hidden 1'
    if 'mr_edit_keys' not in m1['text']:
        m1['text'] = m1['text'] + ', script sendbox mr_edit_keys hidden 0'

    # ---- checks ----
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    ids = list(allbx)
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
    assert (ek_id, setedit) in g and (fb_id, es_id) in g and (es_id, ek_id) in g, 'cords nuevos faltan'
    assert (monmap, setedit) not in g, 'cord mon_map->setedit sigue'
    pres = [b['box'] for b in P['boxes'] if b['box'].get('presentation')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)

    print('mr_edit_keys %s  kslider verde mode 1, clickable, NO alimentado por midiparse' % ek_id)
    print('mr_edit_set %s  (prepend set) <- mr_fb_route:3 "editnote"' % es_id)
    print('mr_mon_map -> ignoreclick 1 (monitor puro); cord a setedit cortado')
    print('mr_fb_route -> route gate gridclear cell editnote (5 outlets)')
    print('boxes: %d  lines: %d  presentacion bottom %.0f right %.0f' %
          (len(P['boxes']), len(P['lines']), bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-editkeys')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert 'mr_edit_keys' in bv and 'mr_edit_set' in bv, 'readback: boxes'
    assert bv['mr_mon_map'].get('ignoreclick') == 1, 'readback: mon_map ignoreclick'
    assert bv['mr_fb_route']['text'] == 'route gate gridclear cell editnote', 'readback: fb_route'
    assert 'mr_edit_keys' in bv['mr_tab_m1']['text'], 'readback: tab m1'
    g2 = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_edit_keys']['id'], bv['mr_setedit_pre']['id']) in g2, 'readback: editkeys->setedit'
    assert (bv['mr_fb_route']['id'], bv['mr_edit_set']['id']) in g2, 'readback: fbroute->editset'
    print('\nescrito %s  (backup: %s.before-editkeys)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
