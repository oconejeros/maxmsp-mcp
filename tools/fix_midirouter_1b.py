"""Dos arreglos de la Fase 1b de Midirouter, en un solo paso:

1) CENTINELA "sin mapa" 255 -> 127. El offset de pad va 0..63 (grilla 8x8), asi que
   cualquier valor 64..127 sirve de centinela y NO depende de que la `table` acepte
   range 256 (si queda en el default 128, 255 se clampa a 127 y `sel 255` no matchea
   nunca -> toda nota "sin mapa" caia igual en el fold y salia transpuesta). Con 127 y
   range 128 (default) no hay ambiguedad.
     - mr_maptable: table_data 129x255 -> 129x127 ; saved_object_attributes.range 256->128
     - mr_heldmap : saved_object_attributes.range 256 -> 128  (guarda pitches 0..127)
     - mr_sentsel / mr_rdsel : `sel 255` -> `sel 127`
     - mr_clr_t : `t b b 255` -> `t b b 127`

2) TECLADO DE NOTAS ENTRANTES en la vista Mapa (pedido del usuario). `mr_mon_map`
   (kslider mode 0, ignoreclick, ambar) alimentado de `mr_midiparse:0` -- lo mismo que
   `mr_mon_in` de la pestana Filtro, para ver que se toca mientras se arma el mapeo.
   Reacomoda la vista Mapa para que entre:
     mr_map_in  [0,17,392,30]   (selector editable)
     mr_mon_map [0,48,392,22]   (monitor entrante, NUEVO)
     mr_padgrid [0,72,96,96]    (12 px por celda)
     Base/Rango/Borrar a la derecha de la grilla (x>=104)
   y suma `mr_mon_map` a los mensajes de pestana mr_tab_m0 / mr_tab_m1.

    python tools/fix_midirouter_1b.py            dry run
    python tools/fix_midirouter_1b.py --apply    escribe (backup .before-1bfix)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

FILTRO = ['mr_pitchkeys', 'mr_mon_in', 'mr_mon_pass', 'mr_mon_legend']
MAPA = ['mr_map_in', 'mr_mon_map', 'mr_padgrid', 'mr_base', 'mr_span', 'mr_base_lbl',
        'mr_span_lbl', 'mr_map_clr']

RELAYOUT = {
    'mr_map_in':   [0.0, 17.0, 392.0, 30.0],
    'mr_padgrid':  [0.0, 72.0, 96.0, 96.0],
    'mr_base':     [104.0, 74.0, 40.0, 15.0],
    'mr_base_lbl': [148.0, 74.0, 44.0, 15.0],
    'mr_span':     [104.0, 96.0, 40.0, 15.0],
    'mr_span_lbl': [148.0, 96.0, 44.0, 15.0],
    'mr_map_clr':  [104.0, 120.0, 60.0, 16.0],
}


def sendbox_list(pairs):
    return ', '.join('script sendbox %s hidden %d' % (v, h) for v, h in pairs)


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    v = {b.get('varname'): b for b in bx.values() if b.get('varname')}

    if 'mr_mon_map' in v:
        print('mr_mon_map ya existe -- nada que hacer')
        return
    for need in ('mr_maptable', 'mr_sentsel', 'mr_rdsel', 'mr_clr_t', 'mr_heldmap',
                 'mr_midiparse', 'mr_tab_m0', 'mr_tab_m1', 'mr_map_in'):
        assert need in v, 'falta %s' % need

    # -------- 1) centinela 255 -> 127 --------------------------------------------------
    mt = v['mr_maptable']
    assert set(mt['table_data']) == {255}, ('table_data inesperada', set(mt['table_data']))
    mt['table_data'] = [127] * len(mt['table_data'])
    mt['saved_object_attributes']['range'] = 128
    v['mr_heldmap']['saved_object_attributes']['range'] = 128
    assert v['mr_sentsel']['text'] == 'sel 255'
    v['mr_sentsel']['text'] = 'sel 127'
    assert v['mr_rdsel']['text'] == 'sel 255'
    v['mr_rdsel']['text'] = 'sel 127'
    assert v['mr_clr_t']['text'] == 't b b 255'
    v['mr_clr_t']['text'] = 't b b 127'

    # -------- 2) teclado de notas entrantes en la vista Mapa -------------------------
    midiparse = v['mr_midiparse']['id']
    nid = max(int(i.split('-')[1]) for i in bx)
    mon = 'obj-%d' % (nid + 1)
    P['boxes'].append({'box': {
        'id': mon, 'maxclass': 'kslider', 'varname': 'mr_mon_map',
        'numinlets': 2, 'numoutlets': 2, 'outlettype': ['int', 'int'],
        'mode': 0, 'ignoreclick': 1, 'parameter_enable': 0, 'offset': 21, 'range': 88,
        'hkeycolor': [1.0, 0.709803921568627, 0.196078431372549, 1.0], 'hidden': 1,
        'patching_rect': [900.0, 690.0, 392.0, 22.0],
        'presentation': 1, 'presentation_rect': [0.0, 48.0, 392.0, 22.0],
    }})
    P['lines'].append({'patchline': {'source': [midiparse, 0], 'destination': [mon, 0]}})

    for vn, rect in RELAYOUT.items():
        v[vn]['presentation_rect'] = rect

    v['mr_tab_m0']['text'] = sendbox_list([(x, 0) for x in FILTRO] + [(x, 1) for x in MAPA])
    v['mr_tab_m1']['text'] = sendbox_list([(x, 1) for x in FILTRO] + [(x, 0) for x in MAPA])

    # -------- chequeos --------------------------------------------------------------
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            n = b['numoutlets'] if end == 'source' else b['numinlets']
            assert 0 <= eidx < n, ('fuera de rango', pl, end, n)
    assert set(allbx[mt['id']]['table_data']) == {127}
    pres = [b['box'] for b in P['boxes'] if b['box'].get('presentation')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)
    assert right == 392.0, ('borde derecho != 392', right)

    print('1) centinela sin-mapa: 255 -> 127 (mr_maptable range 128, table_data 129x127)')
    print('   mr_sentsel/mr_rdsel -> sel 127 ; mr_clr_t -> t b b 127')
    print('2) mr_mon_map %s  kslider monitor entrante <- mr_midiparse, vista Mapa' % mon)
    print('   vista Mapa: map_in y17..47, mon_map y48..70, grilla y72..168, Base/Rango x>=104')
    print('   presentacion: bottom %.0f, borde derecho %.0f' % (bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-1bfix')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    assert 'mr_mon_map' in b2, 'readback: mr_mon_map falta'
    assert b2['mr_sentsel']['text'] == 'sel 127', 'readback: sentsel'
    assert set(b2['mr_maptable']['table_data']) == {127}, 'readback: table_data'
    g2 = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in back['lines']}
    assert (v['mr_midiparse']['id'], b2['mr_mon_map']['id']) in g2, 'readback: cord monitor falta'
    print('\nescrito %s  (backup: %s.before-1bfix)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
