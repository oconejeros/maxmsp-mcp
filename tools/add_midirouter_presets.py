"""Midirouter Fase 2: pestana Presets + persistencia por archivo sidecar.

El motor (`forteseq/midirouter.js`) ya tiene toda la logica de presets (mismo mecanismo que
`forteseqwf.js`: `new File(devPath("midirouter_presets.txt"))`, 16 slots con nombre + una
linea `current` auto-guardada con debounce y restaurada al instanciar).

Este script agrega en el `.amxd`:
  1. Tercer item "Presets" en el enum de `mr_tab` ; `mr_tab_sel` a `sel 0 1 2` ; `mr_tab_m2`.
  2. UI de la pestana Presets: numbox Slot, botones Store/Recall/Clear (live.text mode 1 ->
     `sel 1` -> mensaje), textedit Nombre, display de slots llenos, labels.
  3. `mr_pre_route` = `route presetname presetslots` insertado entre `mr_engine:1` y
     `mr_grid:0` (la UI toma esos dos; el resto sigue al jsui).
  4. Arranque diferido: `mr_loadbang -> deferlow -> message loadpresets -> mr_engine`.

    python tools/add_midirouter_presets.py            dry run
    python tools/add_midirouter_presets.py --apply    escribe (backup .before-presets)

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
MAPA = ['mr_grid', 'mr_base', 'mr_span', 'mr_base_lbl', 'mr_span_lbl', 'mr_map_clr']
PRESETS = ['mr_pre_title', 'mr_pre_slot_lbl', 'mr_pre_slot', 'mr_pre_slots_lbl',
           'mr_pre_store', 'mr_pre_recall', 'mr_pre_clear', 'mr_pre_name_lbl', 'mr_pre_name']


def sb(members, hidden):
    return ['script sendbox %s hidden %d' % (m, hidden) for m in members]


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes, lines = P['boxes'], P['lines']
    v = {b['box'].get('varname'): b['box'] for b in boxes if b['box'].get('varname')}

    if 'mr_pre_route' in v:
        print('mr_pre_route ya existe -- nada que hacer')
        return
    for n in ('mr_tab', 'mr_tab_sel', 'mr_tab_m0', 'mr_tab_m1', 'mr_thispatcher',
              'mr_loadbang', 'mr_engine', 'mr_grid'):
        assert n in v, 'falta %s' % n

    tab, tab_sel = v['mr_tab'], v['mr_tab_sel']
    thispatcher = v['mr_thispatcher']['id']
    loadbang = v['mr_loadbang']['id']
    engine = v['mr_engine']['id']
    grid = v['mr_grid']['id']

    # -- 1) enum de mr_tab a 3 items --
    vo = tab['saved_attribute_attributes']['valueof']
    assert vo['parameter_enum'] == ['Filtro', 'Mapa'], vo['parameter_enum']
    vo['parameter_enum'] = ['Filtro', 'Mapa', 'Presets']
    vo['parameter_mmax'] = 2
    assert tab_sel['text'].startswith('sel 0 1'), tab_sel['text']
    tab_sel['text'] = 'sel 0 1 2'

    nid = [max(int(b['box']['id'].split('-')[1]) for b in boxes)]

    def newid():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def add_box(varname, maxclass, text=None, rect=None, extra=None, ninlet=1, noutlet=1,
                otype=None, pres=False):
        bid = newid()
        bx = {'id': bid, 'maxclass': maxclass, 'varname': varname,
              'numinlets': ninlet, 'numoutlets': noutlet}
        if otype is not None:
            bx['outlettype'] = otype
        elif noutlet:
            bx['outlettype'] = [''] * noutlet
        if text is not None:
            bx['text'] = text
        bx['patching_rect'] = [1200.0, 100.0 + 30 * nid[0], 120.0, 20.0]
        if pres:
            bx['presentation'] = 1
            bx['presentation_rect'] = rect
        elif rect:
            bx['patching_rect'] = rect
        if extra:
            bx.update(extra)
        boxes.append({'box': bx})
        v[varname] = bx
        return bid

    def line(a, ai, b, bi):
        lines.append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    # -- 2) UI de la pestana Presets (presentation, hidden 1, x0..390, y17..167) --
    add_box('mr_pre_title', 'comment', text='PRESETS', rect=[6.0, 20.0, 120.0, 16.0],
            noutlet=0, extra={'fontsize': 11.0, 'hidden': 1}, pres=True)
    add_box('mr_pre_slot_lbl', 'comment', text='Slot', rect=[6.0, 44.0, 30.0, 14.0],
            noutlet=0, extra={'hidden': 1}, pres=True)
    add_box('mr_pre_slot', 'number', rect=[40.0, 42.0, 48.0, 18.0], noutlet=2,
            otype=['', 'bang'], extra={'minimum': 1, 'maximum': 16, 'hidden': 1}, pres=True)
    add_box('mr_pre_slots_lbl', 'comment', text='- - - - - - - - - - - - - - - -',
            rect=[96.0, 44.0, 290.0, 14.0], noutlet=0, extra={'hidden': 1}, pres=True)
    for lbl, vn in (('Store', 'mr_pre_store'), ('Recall', 'mr_pre_recall'), ('Clear', 'mr_pre_clear')):
        x = 6.0 + 90.0 * ('mr_pre_store mr_pre_recall mr_pre_clear'.split().index(vn))
        add_box(vn, 'live.text', rect=[x, 70.0, 82.0, 20.0],
                extra={'mode': 1, 'parameter_enable': 0, 'text': lbl, 'texton': lbl, 'hidden': 1},
                pres=True)
    add_box('mr_pre_name_lbl', 'comment', text='Nombre', rect=[6.0, 102.0, 46.0, 14.0],
            noutlet=0, extra={'hidden': 1}, pres=True)
    add_box('mr_pre_name', 'textedit', rect=[54.0, 100.0, 220.0, 20.0], ninlet=1, noutlet=2,
            otype=['', 'bang'], extra={'hidden': 1}, pres=True)

    # -- glue (sin presentation) --
    tab_m2 = add_box('mr_tab_m2', 'message', text='')
    slot_pre = add_box('mr_pre_slot_pre', 'newobj', text='prepend setpresetslot', ninlet=2)
    st_sel = add_box('mr_pre_store_sel', 'newobj', text='sel 1', ninlet=2, noutlet=2)
    st_msg = add_box('mr_pre_store_msg', 'message', text='storepreset', ninlet=2)
    rc_sel = add_box('mr_pre_recall_sel', 'newobj', text='sel 1', ninlet=2, noutlet=2)
    rc_msg = add_box('mr_pre_recall_msg', 'message', text='recallpreset', ninlet=2)
    cl_sel = add_box('mr_pre_clear_sel', 'newobj', text='sel 1', ninlet=2, noutlet=2)
    cl_msg = add_box('mr_pre_clear_msg', 'message', text='clearpreset', ninlet=2)
    name_pre = add_box('mr_pre_name_pre', 'newobj', text='prepend setpresetname', ninlet=2)
    pre_route = add_box('mr_pre_route', 'newobj', text='route presetname presetslots',
                        ninlet=1, noutlet=3)
    name_set = add_box('mr_pre_name_set', 'newobj', text='prepend set', ninlet=2)
    slots_set = add_box('mr_pre_slots_set', 'newobj', text='prepend set', ninlet=2)
    pre_defer = add_box('mr_pre_defer', 'newobj', text='deferlow', ninlet=1)
    load_msg = add_box('mr_pre_load_msg', 'message', text='loadpresets', ninlet=2)

    # -- 3) pestanas --
    tab_sel_id = tab_sel['id']
    line(tab_sel_id, 2, tab_m2, 0)
    line(tab_m2, 0, thispatcher, 0)
    v['mr_tab_m0']['text'] = ', '.join(sb(FILTRO, 0) + sb(MAPA, 1) + sb(PRESETS, 1))
    v['mr_tab_m1']['text'] = ', '.join(sb(FILTRO, 1) + sb(MAPA, 0) + sb(PRESETS, 1))
    v['mr_tab_m2']['text'] = ', '.join(sb(FILTRO, 1) + sb(MAPA, 1) + sb(PRESETS, 0))

    # -- 4) cableado UI -> motor --
    line(v['mr_pre_slot']['id'], 0, slot_pre, 0)
    line(slot_pre, 0, engine, 0)
    for btn, sel, msg in (('mr_pre_store', st_sel, st_msg), ('mr_pre_recall', rc_sel, rc_msg),
                          ('mr_pre_clear', cl_sel, cl_msg)):
        line(v[btn]['id'], 0, sel, 0)
        line(sel, 0, msg, 0)
        line(msg, 0, engine, 0)
    line(v['mr_pre_name']['id'], 0, name_pre, 0)
    line(name_pre, 0, engine, 0)

    # -- motor -> UI : route presetname presetslots, resto al jsui --
    n0 = len(lines)
    lines[:] = [l for l in lines
                if not (l['patchline']['source'] == [engine, 1]
                        and l['patchline']['destination'][0] == grid)]
    assert len(lines) == n0 - 1, 'no encontre mr_engine:1 -> mr_grid'
    line(engine, 1, pre_route, 0)
    line(pre_route, 0, name_set, 0)
    line(name_set, 0, v['mr_pre_name']['id'], 0)
    line(pre_route, 1, slots_set, 0)
    line(slots_set, 0, v['mr_pre_slots_lbl']['id'], 0)
    line(pre_route, 2, grid, 0)

    # -- arranque diferido --
    line(loadbang, 0, pre_defer, 0)
    line(pre_defer, 0, load_msg, 0)
    line(load_msg, 0, engine, 0)

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
            assert 0 <= eidx < cnt, ('outlet/inlet fuera de rango', pl, endk, cnt, b.get('varname'))
    g = {(l['patchline']['source'][0], l['patchline']['source'][1],
          l['patchline']['destination'][0]) for l in lines}
    assert (engine, 1, pre_route) in g, 'engine:1 debe ir a mr_pre_route'
    assert (pre_route, 2, grid) in g, 'mr_pre_route:2 debe seguir al jsui'
    eng1 = [l for l in lines if l['patchline']['source'] == [engine, 1]]
    assert len(eng1) == 1, 'mr_engine:1 debe salir una sola vez'
    pres = [b['box'] for b in boxes if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)
    assert right <= 392.0, ('presentacion pasa x392', right)
    assert v['mr_tab']['saved_attribute_attributes']['valueof']['parameter_enum'][-1] == 'Presets'

    print('mr_tab enum -> Filtro/Mapa/Presets ; mr_tab_sel -> sel 0 1 2')
    print('UI Presets: %d objetos ; glue: mr_pre_route + deferlow loadpresets' % len(PRESETS))
    print('boxes: %d  lines: %d  bottom %.0f  right %.0f' % (len(boxes), len(lines), bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-presets')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    for n in PRESETS + ['mr_pre_route', 'mr_tab_m2', 'mr_pre_defer']:
        assert n in bv, 'readback: falta %s' % n
    assert bv['mr_tab']['saved_attribute_attributes']['valueof']['parameter_enum'] == ['Filtro', 'Mapa', 'Presets']
    assert bv['mr_tab_sel']['text'] == 'sel 0 1 2'
    g2 = {(l['patchline']['source'][0], l['patchline']['source'][1],
           l['patchline']['destination'][0]) for l in back['lines']}
    assert (bv['mr_engine']['id'], 1, bv['mr_pre_route']['id']) in g2, 'readback: engine:1->route'
    assert (bv['mr_pre_route']['id'], 2, bv['mr_grid']['id']) in g2, 'readback: route:2->grid'
    assert 'mr_pre_title' in bv['mr_tab_m2']['text'] and 'mr_grid' in bv['mr_tab_m1']['text']
    print('\nescrito %s  (backup: %s.before-presets)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
