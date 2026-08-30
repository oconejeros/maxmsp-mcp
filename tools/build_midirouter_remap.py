"""FASE 1b del rediseno de Midirouter (ver el plan midi-note-mapper). Corre DESPUES de
build_midirouter_tabs.py.

Convierte el device de "gate por pitch" a REMAPEADOR de notas:

  - quita `mr_stripnote` y `mr_makenote` (hoy fuerzan vel 100 / 200 ms) -> se pasa la
    velocidad tocada y el note-off real;
  - `mr_maptable` (table nueva, @size 128 @range 256 @embed 1, 129x255): por cada nota
    entrante guarda un offset 0..63 = notaDestino-36, o 255 = "sin mapa";
  - motor: gate:0 -> unpack -> [note-on: lookup -> sentinela? pitch original : Base+(off mod
    Rango)] -> noteout ; note-off: relee `mr_heldmap` (latch de 128) para cancelar EXACTO
    el pad que abrio el note-on, aunque Base/Rango se hayan movido mientras sonaba;
  - `Base` / `Rango` (live.numbox, params nuevos, int, 36 / 64);
  - editor en la pestana Mapa: `mr_map_in` kslider (elegi la nota entrante) + `mr_padgrid`
    matrixctrl 8x8 @one/matrix (elegi el pad destino) + `Borrar`;
  - extiende `mr_tab_m0/m1` para mostrar/ocultar el grupo Mapa.

NOTA: en esta fase `mr_maptable` NO es parametro de Live todavia -- el mapa NO persiste al
recargar el set (solo queda el default embebido). La persistencia y los presets llegan en
la Fase 2 (pattrstorage). Para verificar 1b basta una sola sesion.

    python tools/build_midirouter_remap.py            dry run
    python tools/build_midirouter_remap.py --apply    escribe (backup .before-remap)

Cerrar el device en Max y Live antes de --apply. Idempotente (sale si `mr_maptable` esta).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

FILTRO = ['mr_pitchkeys', 'mr_mon_in', 'mr_mon_pass', 'mr_mon_legend']
MAPA = ['mr_map_in', 'mr_padgrid', 'mr_base', 'mr_span', 'mr_base_lbl', 'mr_span_lbl',
        'mr_map_clr']


def sendbox_list(pairs):
    return ', '.join('script sendbox %s hidden %d' % (v, h) for v, h in pairs)


def num_valueof(longname, short, mmin, mmax, initial, order):
    return {
        'parameter_initial': [initial],
        'parameter_initial_enable': 1,
        'parameter_longname': longname,
        'parameter_mmax': float(mmax),
        'parameter_mmin': float(mmin),
        'parameter_modmode': 4,
        'parameter_order': order,
        'parameter_shortname': short,
        'parameter_type': 1,
        'parameter_unitstyle': 0,
    }


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): b for b in bx.values() if b.get('varname')}

    if 'mr_maptable' in bv:
        print('mr_maptable ya existe -- nada que hacer')
        return
    for need in ('mr_tab', 'mr_tab_m0', 'mr_tab_m1', 'mr_gate', 'mr_noteout', 'mr_loadbang'):
        assert need in bv, 'falta %s -- correr build_midirouter_tabs.py primero' % need

    gate = bv['mr_gate']['id']            # obj-11, outlet 0 = lista pitch vel (post-filtro)
    noteout = bv['mr_noteout']['id']      # obj-15
    loadbang = bv['mr_loadbang']['id']    # obj-16
    stripnote = bv['mr_stripnote']['id']  # obj-12  (a borrar)
    makenote = bv['mr_makenote']['id']    # obj-13  (a borrar)
    tm0, tm1 = bv['mr_tab_m0']['id'], bv['mr_tab_m1']['id']

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def nxt():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    new_boxes = []
    new_lines = []

    def box(**kw):
        new_boxes.append({'box': kw})
        return kw['id']

    def line(a, ai, b, bi):
        new_lines.append({'patchline': {'source': [a, ai], 'destination': [b, bi]}})

    # ---------------------------------------------------------------- tablas ---------------
    maptable = box(id=nxt(), maxclass='newobj', varname='mr_maptable',
                   numinlets=2, numoutlets=2, outlettype=['int', 'bang'],
                   patching_rect=[420.0, 250.0, 160.0, 20.0],
                   text='table mr_maptable 128', embed=1, size=128, showeditor=0,
                   editor_rect=[100.0, 100.0, 300.0, 300.0],
                   saved_object_attributes={'name': 'mr_maptable', 'parameter_enable': 0,
                                            'parameter_mappable': 0, 'range': 256,
                                            'showeditor': 0, 'size': 128},
                   table_data=[255] * 129)
    heldmap = box(id=nxt(), maxclass='newobj', varname='mr_heldmap',
                  numinlets=2, numoutlets=2, outlettype=['int', 'bang'],
                  patching_rect=[620.0, 250.0, 160.0, 20.0],
                  text='table mr_heldmap 128', embed=0, size=128, showeditor=0,
                  saved_object_attributes={'name': 'mr_heldmap', 'parameter_enable': 0,
                                           'parameter_mappable': 0, 'range': 256,
                                           'showeditor': 0, 'size': 128})
    map_rd = box(id=nxt(), maxclass='newobj', varname='mr_map_rd',
                 numinlets=2, numoutlets=2, outlettype=['int', 'bang'],
                 patching_rect=[420.0, 620.0, 120.0, 20.0], text='table mr_maptable')

    # ---------------------------------------------------------------- motor ---------------
    rx = box(id=nxt(), maxclass='newobj', varname='mr_rx', numinlets=1, numoutlets=2,
             outlettype=['int', 'int'], patching_rect=[900.0, 210.0, 74.0, 20.0],
             text='unpack 0 0')
    offdet = box(id=nxt(), maxclass='newobj', varname='mr_offdet', numinlets=2, numoutlets=2,
                 outlettype=['bang', ''], patching_rect=[1000.0, 245.0, 40.0, 20.0],
                 text='sel 0')
    go_off = box(id=nxt(), maxclass='message', varname='mr_go_off', numinlets=2, numoutlets=1,
                 outlettype=[''], patching_rect=[1000.0, 275.0, 32.0, 20.0], text='1')
    go_on = box(id=nxt(), maxclass='message', varname='mr_go_on', numinlets=2, numoutlets=1,
                outlettype=[''], patching_rect=[1050.0, 275.0, 32.0, 20.0], text='2')
    pgate = box(id=nxt(), maxclass='newobj', varname='mr_pgate', numinlets=2, numoutlets=2,
                outlettype=['', ''], patching_rect=[900.0, 310.0, 50.0, 20.0], text='gate 2')
    pt = box(id=nxt(), maxclass='newobj', varname='mr_pt', numinlets=1, numoutlets=3,
             outlettype=['int', 'int', 'int'], patching_rect=[960.0, 345.0, 50.0, 20.0],
             text='t i i i')
    sentsel = box(id=nxt(), maxclass='newobj', varname='mr_sentsel', numinlets=2, numoutlets=2,
                  outlettype=['bang', ''], patching_rect=[960.0, 410.0, 60.0, 20.0],
                  text='sel 255')
    fold = box(id=nxt(), maxclass='newobj', varname='mr_fold', numinlets=3, numoutlets=1,
               outlettype=['int'], patching_rect=[960.0, 445.0, 220.0, 20.0],
               text='expr $i2 + ((($i1 % $i3) + $i3) % $i3)')
    passint = box(id=nxt(), maxclass='newobj', varname='mr_passint', numinlets=2, numoutlets=1,
                  outlettype=['int'], patching_rect=[900.0, 445.0, 40.0, 20.0], text='int')
    o = box(id=nxt(), maxclass='newobj', varname='mr_o', numinlets=2, numoutlets=1,
            outlettype=['int'], patching_rect=[930.0, 490.0, 40.0, 20.0], text='int')
    o_t = box(id=nxt(), maxclass='newobj', varname='mr_o_t', numinlets=1, numoutlets=2,
              outlettype=['bang', 'int'], patching_rect=[1000.0, 490.0, 40.0, 20.0],
              text='t b i')
    inhold = box(id=nxt(), maxclass='newobj', varname='mr_inhold', numinlets=2, numoutlets=1,
                 outlettype=['int'], patching_rect=[1060.0, 400.0, 40.0, 20.0], text='int')
    hm_pack = box(id=nxt(), maxclass='newobj', varname='mr_hm_pack', numinlets=2, numoutlets=1,
                  outlettype=['list'], patching_rect=[1000.0, 530.0, 60.0, 20.0],
                  text='pack 0 0')

    # ------------------------------------------------------------ Base / Rango ------------
    base = box(id=nxt(), maxclass='live.numbox', varname='mr_base', numinlets=1, numoutlets=2,
               outlettype=['', 'float'], parameter_enable=1, hidden=1,
               patching_rect=[900.0, 590.0, 44.0, 15.0],
               presentation=1, presentation_rect=[128.0, 20.0, 44.0, 15.0],
               saved_attribute_attributes={'valueof': num_valueof('Base', 'Base', 0, 127, 36, 1)})
    span = box(id=nxt(), maxclass='live.numbox', varname='mr_span', numinlets=1, numoutlets=2,
               outlettype=['', 'float'], parameter_enable=1, hidden=1,
               patching_rect=[900.0, 620.0, 44.0, 15.0],
               presentation=1, presentation_rect=[128.0, 44.0, 44.0, 15.0],
               saved_attribute_attributes={'valueof': num_valueof('Rango', 'Rango', 1, 128, 64, 2)})
    base_lbl = box(id=nxt(), maxclass='comment', varname='mr_base_lbl', numinlets=1, numoutlets=0,
                   hidden=1, patching_rect=[960.0, 590.0, 60.0, 18.0],
                   presentation=1, presentation_rect=[178.0, 20.0, 56.0, 15.0], text='Base')
    span_lbl = box(id=nxt(), maxclass='comment', varname='mr_span_lbl', numinlets=1, numoutlets=0,
                   hidden=1, patching_rect=[960.0, 620.0, 60.0, 18.0],
                   presentation=1, presentation_rect=[178.0, 44.0, 56.0, 15.0], text='Rango')

    # -------------------------------------------------------------- editor Mapa -----------
    map_in = box(id=nxt(), maxclass='kslider', varname='mr_map_in', numinlets=2, numoutlets=2,
                 outlettype=['int', 'int'], mode=1, offset=21, range=88, parameter_enable=0,
                 hidden=1, patching_rect=[900.0, 660.0, 392.0, 40.0],
                 presentation=1, presentation_rect=[0.0, 18.0, 392.0, 40.0])
    selin = box(id=nxt(), maxclass='newobj', varname='mr_selin', numinlets=2, numoutlets=1,
                outlettype=['int'], patching_rect=[900.0, 710.0, 40.0, 20.0], text='int')
    # latch aparte SOLO para el indice de escritura: si mr_selin alimentara el pack de
    # store, elegir una nota entrante (que hace output de mr_selin para releer) dispararia
    # una escritura basura con el valor viejo del inlet frio.
    selidx = box(id=nxt(), maxclass='newobj', varname='mr_selidx', numinlets=2, numoutlets=1,
                 outlettype=['int'], patching_rect=[960.0, 710.0, 40.0, 20.0], text='int')
    padgrid = box(id=nxt(), maxclass='matrixctrl', varname='mr_padgrid', numinlets=1, numoutlets=2,
                  outlettype=['list', 'list'], parameter_enable=0, autosize=1, rows=8, columns=8,
                  hidden=1, patching_rect=[900.0, 740.0, 104.0, 104.0],
                  presentation=1, presentation_rect=[0.0, 62.0, 104.0, 104.0])
    new_boxes[-1]['box']['one/matrix'] = 1   # una sola celda encendida en toda la grilla
    pg_up = box(id=nxt(), maxclass='newobj', varname='mr_pg_up', numinlets=1, numoutlets=3,
                outlettype=['int', 'int', 'int'], patching_rect=[900.0, 855.0, 90.0, 20.0],
                text='unpack 0 0 0')
    pg_idx = box(id=nxt(), maxclass='newobj', varname='mr_pg_idx', numinlets=2, numoutlets=1,
                 outlettype=['int'], patching_rect=[900.0, 885.0, 120.0, 20.0],
                 text='expr $i1 + $i2 * 8')
    pg_gate = box(id=nxt(), maxclass='newobj', varname='mr_pg_gate', numinlets=2, numoutlets=1,
                  outlettype=[''], patching_rect=[900.0, 915.0, 50.0, 20.0], text='gate 1')
    pgi_t = box(id=nxt(), maxclass='newobj', varname='mr_pgi_t', numinlets=1, numoutlets=3,
                outlettype=['bang', 'bang', 'int'], patching_rect=[900.0, 945.0, 50.0, 20.0],
                text='t b b i')
    setmap_pk = box(id=nxt(), maxclass='newobj', varname='mr_setmap_pk', numinlets=2, numoutlets=1,
                    outlettype=['list'], patching_rect=[900.0, 975.0, 60.0, 20.0], text='pack 0 0')

    rdsel = box(id=nxt(), maxclass='newobj', varname='mr_rdsel', numinlets=2, numoutlets=2,
                outlettype=['bang', ''], patching_rect=[420.0, 655.0, 60.0, 20.0], text='sel 255')
    rd_t = box(id=nxt(), maxclass='newobj', varname='mr_rd_t', numinlets=1, numoutlets=2,
               outlettype=['int', 'int'], patching_rect=[420.0, 685.0, 40.0, 20.0], text='t i i')
    rd_col = box(id=nxt(), maxclass='newobj', varname='mr_rd_col', numinlets=1, numoutlets=1,
                 outlettype=['int'], patching_rect=[420.0, 715.0, 90.0, 20.0], text='expr $i1 % 8')
    rd_row = box(id=nxt(), maxclass='newobj', varname='mr_rd_row', numinlets=1, numoutlets=1,
                 outlettype=['int'], patching_rect=[520.0, 715.0, 110.0, 20.0],
                 text='expr int($i1 / 8)')
    rd_pk = box(id=nxt(), maxclass='newobj', varname='mr_rd_pk', numinlets=3, numoutlets=1,
                outlettype=['list'], patching_rect=[420.0, 745.0, 90.0, 20.0], text='pack 0 0 1')
    rd_clr = box(id=nxt(), maxclass='message', varname='mr_rd_clr', numinlets=2, numoutlets=1,
                 outlettype=[''], patching_rect=[560.0, 685.0, 50.0, 20.0], text='clear')

    map_clr = box(id=nxt(), maxclass='live.text', varname='mr_map_clr', numinlets=1, numoutlets=1,
                  outlettype=[''], mode=1, parameter_enable=0, text='Borrar', texton='Borrar',
                  hidden=1, patching_rect=[900.0, 1010.0, 60.0, 20.0],
                  presentation=1, presentation_rect=[128.0, 70.0, 60.0, 16.0])
    clr_sel = box(id=nxt(), maxclass='newobj', varname='mr_clr_sel', numinlets=2, numoutlets=2,
                  outlettype=['bang', ''], patching_rect=[900.0, 1040.0, 40.0, 20.0], text='sel 1')
    clr_t = box(id=nxt(), maxclass='newobj', varname='mr_clr_t', numinlets=1, numoutlets=3,
                outlettype=['bang', 'bang', 'int'], patching_rect=[900.0, 1070.0, 60.0, 20.0],
                text='t b b 255')

    # ---------------------------------------------------------------- cords ----------------
    # motor: rama de velocidad (unpack tira RTL -> vel sale y propaga ANTES que pitch)
    line(gate, 0, rx, 0)
    line(rx, 1, noteout, 1)          # velocidad real (0 en note-off) a noteout
    line(rx, 1, offdet, 0)
    line(offdet, 0, go_off, 0)       # vel==0 -> note-off
    line(offdet, 1, go_on, 0)        # vel!=0 -> note-on
    line(go_off, 0, pgate, 0)        # control 1 -> outlet 0 (rama note-off)
    line(go_on, 0, pgate, 0)         # control 2 -> outlet 1 (rama note-on)
    line(rx, 0, pgate, 1)            # pitch = dato del gate

    # rama note-off: relee heldmap y saca EXACTO lo que abrio el note-on
    line(pgate, 0, heldmap, 0)
    line(heldmap, 0, noteout, 0)

    # rama note-on
    line(pgate, 1, pt, 0)
    line(pt, 2, inhold, 1)           # (1o RTL) latch pitch crudo, sin salida
    line(pt, 1, passint, 1)          # (2o) latch pitch crudo, sin salida
    line(pt, 0, maptable, 0)         # (3o) lookup -> offset / 255
    line(maptable, 0, sentsel, 0)
    line(sentsel, 0, passint, 0)     # ==255: bang -> saca el pitch crudo (sin mapa)
    line(sentsel, 1, fold, 0)        # !=255: offset -> $i1
    line(base, 0, fold, 1)           # Base -> $i2 (frio)
    line(span, 0, fold, 2)           # Rango -> $i3 (frio)
    line(passint, 0, o, 0)
    line(fold, 0, o, 0)
    line(o, 0, noteout, 0)           # emite la note-on
    line(o, 0, o_t, 0)
    line(o_t, 1, hm_pack, 1)         # (1o) valor = pitch de salida
    line(o_t, 0, inhold, 0)          # (2o) bang -> pitch crudo como indice
    line(inhold, 0, hm_pack, 0)
    line(hm_pack, 0, heldmap, 0)     # lista [indice valor] -> store silencioso

    # loadbang -> Base / Rango re-emiten su valor guardado (bang es seguro en live.numbox)
    line(loadbang, 0, base, 0)
    line(loadbang, 0, span, 0)

    # editor: elegir nota entrante -> latch de lectura + latch de indice de escritura
    line(map_in, 0, selin, 0)        # mr_selin hace output -> relee el mapeo (repinta)
    line(map_in, 0, selidx, 1)       # mr_selidx frio: guarda el indice para escribir, sin salida
    line(selin, 0, map_rd, 0)
    line(selidx, 0, setmap_pk, 0)    # el indice de escritura SOLO sale por aca
    line(map_rd, 0, rdsel, 0)
    line(rdsel, 0, rd_clr, 0)        # 255 -> limpiar grilla
    line(rd_clr, 0, padgrid, 0)
    line(rdsel, 1, rd_t, 0)
    line(rd_t, 1, rd_row, 0)         # (1o RTL) fila
    line(rd_row, 0, rd_pk, 1)
    line(rd_t, 0, rd_col, 0)         # (2o) columna -> dispara
    line(rd_col, 0, rd_pk, 0)
    line(rd_pk, 0, padgrid, 0)       # [col fila 1] -> prende esa celda (one/matrix limpia el resto)

    # editor: clic en un pad -> guardar offset en mr_maptable[selin]
    line(padgrid, 0, pg_up, 0)
    line(pg_up, 2, pg_gate, 0)       # (1o RTL) val -> control del gate (abre si !=0)
    line(pg_up, 1, pg_idx, 1)        # (2o) fila -> $i2 (frio)
    line(pg_up, 0, pg_idx, 0)        # (3o) columna -> $i1 -> col + fila*8 = offset
    line(pg_idx, 0, pg_gate, 1)
    line(pg_gate, 0, pgi_t, 0)       # t b b i, RTL
    line(pgi_t, 2, setmap_pk, 1)     # (1o) valor = offset (frio)
    line(pgi_t, 1, selidx, 0)        # (2o) bang -> indice de escritura -> setmap_pk hot -> store
    line(pgi_t, 0, selin, 0)         # (3o) bang -> relee -> repinta la grilla con el mapeo nuevo
    line(setmap_pk, 0, maptable, 0)  # [indice offset] -> store silencioso

    # editor: Borrar -> mr_maptable[selidx] = 255
    line(map_clr, 0, clr_sel, 0)
    line(clr_sel, 0, clr_t, 0)       # t b b 255, RTL
    line(clr_t, 2, setmap_pk, 1)     # (1o) 255 (frio)
    line(clr_t, 1, selidx, 0)        # (2o) bang -> indice -> store [idx 255]
    line(clr_t, 0, selin, 0)         # (3o) bang -> relee (255 -> limpia la grilla)

    # ------------------------------------------------------------ aplicar al doc -----------
    keep_boxes = [b for b in P['boxes'] if b['box']['id'] not in (stripnote, makenote)]
    keep_lines = [l for l in P['lines']
                  if l['patchline']['source'][0] not in (stripnote, makenote)
                  and l['patchline']['destination'][0] not in (stripnote, makenote)]
    P['boxes'] = keep_boxes + new_boxes
    P['lines'] = keep_lines + new_lines

    # extender los mensajes de pestana para incluir el grupo Mapa
    bv['mr_tab_m0']['text'] = sendbox_list([(v, 0) for v in FILTRO] + [(v, 1) for v in MAPA])
    bv['mr_tab_m1']['text'] = sendbox_list([(v, 1) for v in FILTRO] + [(v, 0) for v in MAPA])

    # registrar Base y Rango en los 3 registros (Pestana ya esta en orden 0)
    PP = P['parameters']
    PP[base] = ['Base', 'Base', 1]
    PP[span] = ['Rango', 'Rango', 2]
    bankp = PP['parameterbanks']['0']['parameters']
    for i, nm in ((bankp.index('-'), 'Base'),):
        bankp[i] = nm
    bankp[bankp.index('-')] = 'Rango'

    # --- auto-chequeos ------------------------------------------------------------------
    allbx = {b['box']['id']: b['box'] for b in P['boxes']}
    ids = list(allbx)
    assert len(ids) == len(set(ids)), 'id duplicado'
    for l in P['lines']:
        pl = l['patchline']
        for end in ('source', 'destination'):
            eid, eidx = pl[end]
            assert eid in allbx, ('endpoint desconocido', pl)
            b = allbx[eid]
            n = b['numoutlets'] if end == 'source' else b['numinlets']
            assert isinstance(eidx, int) and 0 <= eidx < n, ('outlet/inlet fuera de rango', pl, end, n)
    assert allbx[stripnote] if False else stripnote not in allbx, 'stripnote no se borro'
    assert makenote not in allbx, 'makenote no se borro'
    pnames = {v[0] for k, v in PP.items() if k not in ('parameterbanks', 'inherited_shortname')}
    assert pnames == {'Pestana', 'Base', 'Rango'}, pnames
    orders = sorted(v[2] for k, v in PP.items() if k not in ('parameterbanks', 'inherited_shortname'))
    assert orders == [0, 1, 2], orders
    for nm in pnames:
        assert nm in bankp, ('%s no esta en el parameterbank' % nm)
    assert len(allbx[maptable]['table_data']) == 129, 'table_data mal'
    pres = [b['box'] for b in P['boxes'] if b['box'].get('presentation')]
    bottom = max(r['presentation_rect'][1] + r['presentation_rect'][3] for r in pres)
    right = max(r['presentation_rect'][0] + r['presentation_rect'][2] for r in pres)
    assert bottom <= 168.0, ('presentacion pasa y168', bottom)
    assert right == 392.0, ('borde derecho != 392', right)

    print('FASE 1b -- remapeo + Base/Rango + editor Mapa')
    print('  quitados: mr_stripnote (%s), mr_makenote (%s)' % (stripnote, makenote))
    print('  nuevos objetos: %d   nuevos cords: %d' % (len(new_boxes), len(new_lines)))
    print('  tablas: mr_maptable %s (embed, 129x255), mr_heldmap %s, mr_map_rd %s'
          % (maptable, heldmap, map_rd))
    print('  params: Pestana=0, Base=1, Rango=2   banco: %s' % ' '.join(bankp))
    print('  presentacion: bottom %.0f, borde derecho %.0f' % (bottom, right))

    if not apply_it:
        print('\n(dry run -- correr con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-remap')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box']['id']: b['box'] for b in back['boxes']}
    bv2 = {b.get('varname'): b for b in b2.values() if b.get('varname')}
    assert 'mr_maptable' in bv2 and 'mr_heldmap' in bv2 and 'mr_fold' in bv2, 'readback: motor falta'
    assert 'mr_stripnote' not in bv2 and 'mr_makenote' not in bv2, 'readback: stripnote/makenote siguen'
    assert back['parameters'][bv2['mr_base']['id']][0] == 'Base', 'readback: Base sin registrar'
    got = {(p['patchline']['source'][0], p['patchline']['destination'][0]) for p in back['lines']}
    assert (bv2['mr_o']['id'], noteout) in got, 'readback: mr_o -> noteout falta'
    assert (bv2['mr_heldmap']['id'], noteout) in got, 'readback: heldmap -> noteout falta'
    print('\nescrito %s  (backup: %s.before-remap)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
