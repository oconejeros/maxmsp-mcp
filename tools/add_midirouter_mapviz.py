"""Midirouter pestana Mapa: hace visible lo mapeado y destaca la zona del drum rack.

1) La grilla ya muestra TODOS los mapeos (cambio en midirouter.js: pushpad recorre map[]).
2) `mr_readout` (comment) muestra la asignacion de la nota seleccionada:
   "C3 -> pad 4  nota 40 (E1)"  /  "C3 -> sin asignar".
   engine outlet 1 "readout ..." -> mr_fb_route (nuevo match) -> `prepend set` -> comment.
3) `mr_mon_map` (piano ambar de arriba) pasa a mostrar la senal POST-filtro
   (`mr_gate:0` en vez de `mr_midiparse:0`): asi en la vista Mapa ves exactamente que
   notas dejo pasar el filtro y hay que remapear.
4) Zona drum rack: la fila inferior de la grilla = pads 0..15 = notas 36..51 (banco base).
   `mr_rackzone` (panel ambar translucido detras de esa fila) + `mr_rack_lbl` (comment).

    python tools/add_midirouter_mapviz.py            dry run
    python tools/add_midirouter_mapviz.py --apply    escribe (backup .before-mapviz)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

# fila inferior de la grilla: presentation_rect padgrid = [0,66,224,56] -> 4 filas de 14 px
RACKZONE_RECT = [0.0, 108.0, 224.0, 15.0]
READOUT_RECT = [0.0, 125.0, 300.0, 13.0]
RACKLBL_RECT = [0.0, 140.0, 260.0, 12.0]

NEW_UI = ['mr_rackzone', 'mr_readout', 'mr_rack_lbl']   # sumar a las pestanas


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes = P['boxes']
    v = {b['box'].get('varname'): b['box'] for b in boxes if b['box'].get('varname')}

    if 'mr_readout' in v:
        print('mr_readout ya existe -- nada que hacer')
        return
    for need in ('mr_fb_route', 'mr_gate', 'mr_midiparse', 'mr_mon_map', 'mr_padgrid',
                 'mr_tab_m0', 'mr_tab_m1'):
        assert need in v, 'falta %s' % need

    fbroute = v['mr_fb_route']
    fb_id = fbroute['id']
    gate = v['mr_gate']['id']
    midiparse = v['mr_midiparse']['id']
    monmap = v['mr_mon_map']['id']

    nid = max(int(b['box']['id'].split('-')[1]) for b in boxes)
    rz_id = 'obj-%d' % (nid + 1)   # panel zona rack
    ro_id = 'obj-%d' % (nid + 2)   # comment readout
    rl_id = 'obj-%d' % (nid + 3)   # comment rotulo rack
    rs_id = 'obj-%d' % (nid + 4)   # prepend set del readout

    # panel al FRENTE del array = detras en z-order (la grilla se dibuja encima)
    boxes.insert(0, {'box': {
        'id': rz_id, 'maxclass': 'panel', 'varname': 'mr_rackzone',
        'numinlets': 1, 'numoutlets': 0, 'mode': 0, 'rounded': 0, 'border': 0,
        'bgcolor': [1.0, 0.709803921568627, 0.196078431372549, 0.22],
        'hidden': 1,
        'patching_rect': [480.0, 300.0, 224.0, 15.0],
        'presentation': 1, 'presentation_rect': list(RACKZONE_RECT)}})

    boxes.append({'box': {
        'id': ro_id, 'maxclass': 'comment', 'varname': 'mr_readout',
        'numinlets': 1, 'numoutlets': 0, 'fontsize': 10.0,
        'text': 'nota -> pad', 'hidden': 1,
        'patching_rect': [480.0, 330.0, 300.0, 18.0],
        'presentation': 1, 'presentation_rect': list(READOUT_RECT)}})

    boxes.append({'box': {
        'id': rl_id, 'maxclass': 'comment', 'varname': 'mr_rack_lbl',
        'numinlets': 1, 'numoutlets': 0, 'fontsize': 9.0,
        'text': 'fila inferior = 16 pads del rack (nota 36-51)', 'hidden': 1,
        'patching_rect': [480.0, 355.0, 260.0, 16.0],
        'presentation': 1, 'presentation_rect': list(RACKLBL_RECT)}})

    boxes.append({'box': {
        'id': rs_id, 'maxclass': 'newobj', 'varname': 'mr_readout_set',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [480.0, 380.0, 100.0, 20.0], 'text': 'prepend set'}})

    # mr_fb_route: agregar match "readout"
    assert fbroute['text'] == 'route gate gridclear cell editnote', fbroute['text']
    fbroute['text'] = 'route gate gridclear cell editnote readout'
    fbroute['numoutlets'] = 6
    fbroute['outlettype'] = [''] * 6

    def add(a, ai, b, bi):
        P['lines'].append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    add(fb_id, 4, rs_id, 0)      # "readout ..." -> prepend set
    add(rs_id, 0, ro_id, 0)      # set ... -> comment

    # repuntar mon_map a POST-filtro
    n0 = len(P['lines'])
    P['lines'] = [l for l in P['lines']
                  if not (l['patchline']['source'][0] == midiparse
                          and l['patchline']['destination'][0] == monmap)]
    assert len(P['lines']) == n0 - 1, 'no encontre mr_midiparse -> mr_mon_map'
    add(gate, 0, monmap, 0)

    # pestanas: sumar los 3 nuevos UI (panel + 2 comments)
    for m, hid in (('mr_tab_m0', 1), ('mr_tab_m1', 0)):
        t = v[m]['text']
        for vn in NEW_UI:
            if vn not in t:
                t += ', script sendbox %s hidden %d' % (vn, hid)
        v[m]['text'] = t

    # ---- checks ----
    allbx = {b['box']['id']: b['box'] for b in boxes}
    ids = list(allbx)
    assert len(ids) == len(set(ids)), 'ids duplicados'
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            cnt = b['numoutlets'] if end == 'source' else b['numinlets']
            assert 0 <= eidx < cnt, ('outlet/inlet fuera de rango', pl, end, cnt)
    g = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P['lines']}
    assert (fb_id, rs_id) in g and (rs_id, ro_id) in g, 'cords readout faltan'
    assert (gate, monmap) in g and (midiparse, monmap) not in g, 'repunte mon_map mal'
    pres = [b['box'] for b in boxes if b['box'].get('presentation')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)

    print('mr_rackzone %s  panel ambar translucido detras de la fila inferior' % rz_id)
    print('mr_readout %s  comment "nota -> pad ..." <- mr_fb_route:4' % ro_id)
    print('mr_rack_lbl %s  comment "16 pads del rack (36-51)"' % rl_id)
    print('mr_readout_set %s  prepend set' % rs_id)
    print('mr_mon_map repuntado: mr_midiparse -> mr_gate (post-filtro)')
    print('mr_fb_route -> route gate gridclear cell editnote readout (6 outlets)')
    print('boxes: %d  lines: %d  presentacion bottom %.0f' % (len(boxes), len(P['lines']), bottom))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-mapviz')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    for vn in ('mr_rackzone', 'mr_readout', 'mr_rack_lbl', 'mr_readout_set'):
        assert vn in bv, 'readback: falta %s' % vn
    assert bv['mr_fb_route']['text'].endswith('editnote readout'), 'readback: fb_route'
    g2 = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_gate']['id'], bv['mr_mon_map']['id']) in g2, 'readback: gate->mon_map'
    assert (bv['mr_midiparse']['id'], bv['mr_mon_map']['id']) not in g2, 'readback: midiparse->mon_map sigue'
    assert 'mr_readout' in bv['mr_tab_m1']['text'], 'readback: tab m1'
    print('\nescrito %s  (backup: %s.before-mapviz)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
