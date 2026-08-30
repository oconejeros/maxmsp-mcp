"""Arreglo Fase 1b: `matrixctrl` re-emite por su salida cuando se le escribe una celda por
MENSAJE (no solo con el mouse). El repintado de la grilla al elegir una nota entrante
disparaba la salida de `mr_padgrid` -> manejador de clic -> repinta -> ... hasta que
`trigger` corta con "stack overflow -- outlets are disabled".

Corte del lazo: un `gate` en la SALIDA de `mr_padgrid` que se cierra mientras el patch
repinta la grilla y se reabre despues.

  mr_padgrid:0 --> mr_click_gate:1 (dato) --> mr_click_gate:0 --> mr_pg_up  (manejador de clic)
  mr_selin:0   --> mr_rd_go (t 1 i 0):
        :2 "0" (RTL 1o) --> mr_click_gate:0   (cierra)
        :1  i  (2o)     --> mr_map_rd:0       (fija indice + lee -> repinta; el eco cae en el gate cerrado)
        :0 "1" (3o)     --> mr_click_gate:0   (abre)
  mr_loadbang:0 --> "1" --> mr_click_gate:0   (arranca abierto)

    python tools/fix_midirouter_padgrid_loop.py            dry run
    python tools/fix_midirouter_padgrid_loop.py --apply    escribe (backup .before-loopfix)

Cerrar el device en Max y Live antes de --apply. Idempotente.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): b['box']['id'] if False else b for b in bx.values() if b.get('varname')}
    v = {vn: b['id'] for vn, b in bv.items()}

    if 'mr_click_gate' in v:
        print('mr_click_gate ya existe -- nada que hacer')
        return
    for need in ('mr_padgrid', 'mr_pg_up', 'mr_selin', 'mr_map_rd', 'mr_loadbang'):
        assert need in v, 'falta %s -- correr build_midirouter_remap.py primero' % need

    padgrid, pg_up = v['mr_padgrid'], v['mr_pg_up']
    selin, map_rd, loadbang = v['mr_selin'], v['mr_map_rd'], v['mr_loadbang']

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def nxt():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    cgate, rdgo, ci = nxt(), nxt(), nxt()
    P['boxes'].append({'box': {
        'id': cgate, 'maxclass': 'newobj', 'varname': 'mr_click_gate',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [900.0, 815.0, 60.0, 20.0], 'text': 'gate 1 1'}})
    P['boxes'].append({'box': {
        'id': rdgo, 'maxclass': 'newobj', 'varname': 'mr_rd_go',
        'numinlets': 1, 'numoutlets': 3, 'outlettype': ['int', 'int', 'int'],
        'patching_rect': [900.0, 740.0, 60.0, 20.0], 'text': 't 1 i 0'}})
    P['boxes'].append({'box': {
        'id': ci, 'maxclass': 'message', 'varname': 'mr_click_init',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [1000.0, 780.0, 32.0, 20.0], 'text': '1'}})

    def drop(src, dst):
        n0 = len(P['lines'])
        P['lines'][:] = [l for l in P['lines']
                         if not (l['patchline']['source'][0] == src
                                 and l['patchline']['destination'][0] == dst)]
        assert len(P['lines']) < n0, 'no encontre el cord %s -> %s' % (src, dst)

    def add(a, ai, b, bi):
        P['lines'].append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    drop(padgrid, pg_up)                 # mr_padgrid:0 -> mr_pg_up:0
    drop(selin, map_rd)                  # mr_selin:0 -> mr_map_rd:0

    add(padgrid, 0, cgate, 1)           # salida de la grilla = dato del gate
    add(cgate, 0, pg_up, 0)             # solo pasa cuando NO estamos repintando
    add(selin, 0, rdgo, 0)
    add(rdgo, 2, cgate, 0)             # "0" (RTL 1o) -> cierra
    add(rdgo, 1, map_rd, 0)            # indice -> lee + repinta (eco bloqueado)
    add(rdgo, 0, cgate, 0)             # "1" (3o) -> abre
    add(loadbang, 0, ci, 0)
    add(ci, 0, cgate, 0)              # arranca abierto

    # --- chequeos ---
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            n = b['numoutlets'] if end == 'source' else b['numinlets']
            assert 0 <= eidx < n, ('fuera de rango', pl, end, n)
    got = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P['lines']}
    assert (padgrid, pg_up) not in got and (selin, map_rd) not in got, 'cords viejos siguen'
    assert (cgate, pg_up) in got and (rdgo, map_rd) in got, 'cords nuevos faltan'

    print('mr_click_gate %s  (gate 1 1 en la salida de mr_padgrid)' % cgate)
    print('mr_rd_go %s  (t 1 i 0: cierra -> lee/repinta -> abre)' % rdgo)
    print('mr_click_init %s  (loadbang -> abre)' % ci)

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-loopfix')
    amxd.save(DEVICE, data, s, e, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box'].get('varname') for b in back['boxes']}
    assert 'mr_click_gate' in b2 and 'mr_rd_go' in b2, 'readback: objetos faltan'
    g2 = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in back['lines']}
    assert (padgrid, pg_up) not in g2, 'readback: cord viejo sigue'
    print('\nescrito %s  (backup: %s.before-loopfix)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
