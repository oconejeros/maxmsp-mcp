"""Add "Orden Inv" -- a live.toggle that walks the chosen Orden (Card/Forte/Cons/...) backwards.

Engine side is forteseq2.js setorderrev() (reverses order[] inside buildOrder(), echoes
"ordrev" on FS2_G_ECHO). This adds the widget, same idiom as add_fs2_ritmo_raiz.py: label +
live.toggle in fs2pages.maxpat next to R.Raiz (free at x=276), -> prepend setorderrev -> the
bpatcher outlet, a pg_init outputvalue so the saved value re-fires on load, and a dedicated
receive FS2_G_ECHO -> route ordrev -> prepend set chain. FORTESEQ2.amxd gets the nested
parameter entry (order 0, like every other parameter under bpatcher obj-484).

    python tools/add_fs2_orden_inverso.py            dry run
    python tools/add_fs2_orden_inverso.py --apply    do it (device closed in Max AND Live)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
BPATCHER_OUTLET_ID = 'obj-5'
BPATCHER_INLET_ID = 'obj-1'
NESTED_BPATCHER_ID = 'obj-484'
NOTE = ('Recorre el Orden elegido al reves: el siguiente set es el vecino anterior en vez del '
        'posterior (Card 12 -> 11 -> ..., Cons del mas tenso al mas consonante, etc). El set que '
        'suena ahora no cambia; solo cambia hacia donde avanza. Vale tambien para las voces con '
        'TonProp propio.')


def main():
    apply_it = '--apply' in sys.argv
    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert bx['obj-859'].get('varname') == 'fs2_rraiz'
    assert bx[BPATCHER_OUTLET_ID]['maxclass'] == 'outlet'
    assert bx[BPATCHER_INLET_ID]['maxclass'] == 'inlet'
    assert not any(b['box'].get('varname') == 'fs2_ordinv' for b in pg['boxes']), 'ya aplicado'
    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def add(box):
        pg['boxes'].append({'box': box})

    label_id = fresh()
    add({'id': label_id, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'fontsize': 8.0,
         'varname': 'fs2_lbl_ordinv', 'text': 'Inv',
         'patching_rect': [140.0, 2570.0, 30.0, 16.0],
         'presentation': 1, 'presentation_rect': [276.0, 522.0, 30.0, 16.0]})
    tog_id = fresh()
    add({'id': tog_id, 'maxclass': 'live.toggle', 'numinlets': 1, 'numoutlets': 1,
         'outlettype': [''], 'parameter_enable': 1, 'varname': 'fs2_ordinv', 'annotation': NOTE,
         'patching_rect': [140.0, 2590.0, 15.0, 15.0],
         'presentation': 1, 'presentation_rect': [276.0, 536.0, 15.0, 15.0],
         'saved_attribute_attributes': {'valueof': {
             'parameter_type': 2, 'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
             'parameter_modmode': 0, 'parameter_initial': [0], 'parameter_initial_enable': 1,
             'parameter_longname': 'Orden Inv', 'parameter_shortname': 'Orden Inv'}}})
    pg['parameters'][tog_id] = ['Orden Inv', 'Orden Inv', 0]
    prep_id = fresh()
    add({'id': prep_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
         'varname': 'fs2_ordinv_prep', 'patching_rect': [140.0, 2620.0, 150.0, 22.0],
         'text': 'prepend setorderrev'})
    pg['lines'].append({'patchline': {'source': [tog_id, 0], 'destination': [prep_id, 0]}})
    pg['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': [BPATCHER_OUTLET_ID, 0]}})
    init_id = fresh()
    add({'id': init_id, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1,
         'outlettype': [''], 'varname': 'pg_init[5]', 'patching_rect': [140.0, 2650.0, 70.0, 22.0],
         'text': 'outputvalue'})
    pg['lines'].append({'patchline': {'source': [BPATCHER_INLET_ID, 0], 'destination': [init_id, 0]}})
    pg['lines'].append({'patchline': {'source': [init_id, 0], 'destination': [tog_id, 0]}})
    recv_id = fresh()
    add({'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
         'varname': 'fs2_ordinv_gecho_rx', 'patching_rect': [900.0, 4460.0, 160.0, 20.0],
         'text': 'receive FS2_G_ECHO'})
    route_id = fresh()
    add({'id': route_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
         'outlettype': ['', ''], 'varname': 'fs2_ordinv_gecho_route',
         'patching_rect': [900.0, 4490.0, 160.0, 20.0], 'text': 'route ordrev'})
    pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})
    setrx_id = fresh()
    add({'id': setrx_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1,
         'outlettype': [''], 'varname': 'fs2_ordinv_gecho_setrx',
         'patching_rect': [900.0, 4520.0, 160.0, 22.0], 'text': 'prepend set'})
    pg['lines'].append({'patchline': {'source': [route_id, 0], 'destination': [setrx_id, 0]}})
    pg['lines'].append({'patchline': {'source': [setrx_id, 0], 'destination': [tog_id, 0]}})
    print('fs2pages.maxpat: +%s label, +%s live.toggle, chain %s/%s/%s/%s/%s' %
          (label_id, tog_id, prep_id, init_id, recv_id, route_id, setrx_id))

    data, s, e, doc = amxd.load(DEVICE)
    PP = doc['patcher']['parameters']
    key = '%s::%s' % (NESTED_BPATCHER_ID, tog_id)
    assert '%s::obj-859' % NESTED_BPATCHER_ID in PP and key not in PP
    PP[key] = ['Orden Inv', 'Orden Inv', 0]
    print('FORTESEQ2.amxd: parameters[%r] = %r' % (key, PP[key]))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return
    shutil.copyfile(PAGES, PAGES + '.before-ordinv')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    shutil.copyfile(DEVICE, DEVICE + '.before-ordinv')
    amxd.save(DEVICE, data, s, e, doc)
    print('\nescrito. Sigue: check_structure.py y check_params3.py')


main()
