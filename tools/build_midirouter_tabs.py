"""FASE 1a del rediseno de Midirouter (ver el plan midi-note-mapper): mete la infraestructura
de pestanas y crea los PRIMEROS parametros de Live del device -- hoy no tiene ninguno
(`patcher.parameters` ni existe).

Que hace este script, y NADA mas (el motor de remapeo, el editor Mapa y Base/Rango van en
la Fase 1b):

  - agrega `mr_tab` (live.tab, parametro `Pestana`, enum ["Filtro","Mapa"]) en una franja
    de 15 px arriba de la columna de 392 px;
  - `mr_tab -> mr_tab_sel (sel 0 1) -> mr_tab_m0 / mr_tab_m1` (mensajes con lista
    `script sendbox <var> hidden 0|1` separada por comas, idiom verificado en devices
    comerciales) -> `mr_thispatcher` (obj-19, ya existe);
  - `mr_loadbang` (obj-16) -> `mr_tab_m0` para arrancar mostrando Filtro;
  - baja los 3 teclados del filtro 16 px y los achica 48->44 (gap 1) para hacerle lugar a
    la franja de pestanas; abajo total y=167 <= 168 (altura del device fija en 169);
  - crea los 3 registros de parametros desde cero (box valueof + patcher.parameters +
    parameterbanks + inherited_shortname), como en build_midibounce.py, solo para `Pestana`.

Verificacion en Live tras --apply (el device cerrado en Max y Live): carga sin error, en el
panel de parametros aparece `Pestana`, la pestana conmuta entre la vista del filtro (3
teclados) y una vista Mapa vacia. check_structure.py debe dar OK.

    python tools/build_midirouter_tabs.py            dry run
    python tools/build_midirouter_tabs.py --apply    escribe (backup .before-tabs)

Idempotente (sale si `mr_tab` ya esta).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

FILTRO = ['mr_pitchkeys', 'mr_mon_in', 'mr_mon_pass', 'mr_mon_legend']

# Reapilado de los teclados del filtro: [x, y, w, h] en presentacion.
RESTACK = {
    'mr_pitchkeys':  [0.0, 18.0, 392.0, 44.0],
    'mr_mon_in':     [0.0, 63.0, 392.0, 44.0],
    'mr_mon_pass':   [0.0, 108.0, 392.0, 44.0],
    'mr_mon_legend': [2.0, 153.0, 388.0, 14.0],
}


def sendbox_list(varnames, hidden):
    return ', '.join('script sendbox %s hidden %d' % (v, hidden) for v in varnames)


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): b for b in bx.values() if b.get('varname')}

    if 'mr_tab' in bv:
        print('mr_tab ya existe -- nada que hacer')
        return
    assert 'parameters' not in P or P['parameters'] is None, \
        'el device ya tiene un bloque parameters; revisar antes de crear uno nuevo'

    thispatcher = next(i for i, b in bx.items() if b.get('varname') == 'mr_thispatcher')
    loadbang = next(i for i, b in bx.items() if b.get('varname') == 'mr_loadbang')

    nid = max(int(i.split('-')[1]) for i in bx)
    tab, tsel, tm0, tm1 = ('obj-%d' % (nid + k) for k in (1, 2, 3, 4))

    tab_valueof = {
        'parameter_enum': ['Filtro', 'Mapa'],
        'parameter_initial': [0],
        'parameter_initial_enable': 1,
        'parameter_longname': 'Pestana',
        'parameter_mmax': 1,
        'parameter_modmode': 0,
        'parameter_order': 0,
        'parameter_shortname': 'Pest',
        'parameter_type': 2,
        'parameter_unitstyle': 9,
    }

    P['boxes'].append({'box': {
        'id': tab, 'maxclass': 'live.tab', 'varname': 'mr_tab',
        'numinlets': 1, 'numoutlets': 3, 'outlettype': ['', '', 'float'],
        'parameter_enable': 1,
        'patching_rect': [900.0, 40.0, 160.0, 20.0],
        'presentation': 1, 'presentation_rect': [0.0, 0.0, 392.0, 15.0],
        'saved_attribute_attributes': {'valueof': tab_valueof},
    }})
    P['boxes'].append({'box': {
        'id': tsel, 'maxclass': 'newobj', 'varname': 'mr_tab_sel',
        'numinlets': 2, 'numoutlets': 3, 'outlettype': ['bang', 'bang', ''],
        'patching_rect': [900.0, 80.0, 60.0, 20.0], 'text': 'sel 0 1',
    }})
    P['boxes'].append({'box': {
        'id': tm0, 'maxclass': 'message', 'varname': 'mr_tab_m0',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [900.0, 120.0, 640.0, 22.0],
        'text': sendbox_list(FILTRO, 0),
    }})
    P['boxes'].append({'box': {
        'id': tm1, 'maxclass': 'message', 'varname': 'mr_tab_m1',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [900.0, 150.0, 640.0, 22.0],
        'text': sendbox_list(FILTRO, 1),
    }})

    for ln in [
        {'source': [tab, 0], 'destination': [tsel, 0]},
        {'source': [tsel, 0], 'destination': [tm0, 0]},
        {'source': [tsel, 1], 'destination': [tm1, 0]},
        {'source': [tm0, 0], 'destination': [thispatcher, 0]},
        {'source': [tm1, 0], 'destination': [thispatcher, 0]},
        {'source': [loadbang, 0], 'destination': [tm0, 0]},
    ]:
        P['lines'].append({'patchline': ln})

    for vn, rect in RESTACK.items():
        bv[vn]['presentation_rect'] = rect

    P['parameters'] = {
        tab: ['Pestana', 'Pest', 0],
        'parameterbanks': {'0': {'index': 0, 'name': '',
                                 'parameters': ['Pestana', '-', '-', '-', '-', '-', '-', '-']}},
        'inherited_shortname': 1,
    }

    # --- auto-chequeos (misma clase que check_structure.py / build_midibounce.py) ---------
    ids = [b['box']['id'] for b in P['boxes']]
    assert len(ids) == len(set(ids)), 'id de box duplicado'
    known = set(ids)
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert isinstance(eid, str) and eid in known, pl
            b = bx.get(eid) or next(x['box'] for x in P['boxes'] if x['box']['id'] == eid)
            n = b['numoutlets'] if end == 'source' else b['numinlets']
            assert 0 <= eidx < n, (pl, end, n)
    pnames = {v[0] for k, v in P['parameters'].items()
              if k not in ('parameterbanks', 'inherited_shortname')}
    assert pnames == {'Pestana'}, pnames
    for nm in pnames:
        assert nm in P['parameters']['parameterbanks']['0']['parameters'], nm
    pres = [b['box'] for b in P['boxes'] if b['box'].get('presentation')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)
    assert right == 392.0, ('borde derecho != 392', right)

    print('mr_tab %s  (Pestana: primer parametro de Live del device)' % tab)
    print('  %s -> mr_tab_sel -> mr_tab_m0/m1 -> %s (thispatcher)' % (tab, thispatcher))
    print('  loadbang %s -> mr_tab_m0  (arranca en Filtro)' % loadbang)
    print('  teclados del filtro reapilados: y 18 / 63 / 108, legend 153..167')
    print('  presentacion: bottom %.0f, borde derecho %.0f' % (bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-tabs')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box']['id']: b['box'] for b in back['boxes']}
    assert any(b.get('varname') == 'mr_tab' for b in b2.values()), 'readback: mr_tab falta'
    assert back['parameters'][tab][0] == 'Pestana', 'readback: registro Pestana falta'
    got = {(p['patchline']['source'][0], p['patchline']['destination'][0]) for p in back['lines']}
    assert (tab, tsel) in got and (tm0, thispatcher) in got and (loadbang, tm0) in got, 'readback: cords faltan'
    print('\nescrito %s  (backup: %s.before-tabs)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
