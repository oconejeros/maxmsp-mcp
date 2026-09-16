"""Add "Ritmo Raiz" -- a Live-parameter live.numbox (0-64) that puts Sec Raiz's own root walk on
ITS OWN step-count clock, independent of Ritmo Arm / the harmony's own cadence. Same idiom as
Ritmo Arm (harmRate/fs2_rarm) end to end: forteseq2.js already carries the engine side this
session (rootRate/rootCount, setrootrate(), rootStep(), the rootSeqAdvanceOnHarmony() gate, and the
querynext() "graiz" echo) and fs2horizon.js already carries a drag-scrub chip for it in the
Horizonte popup's global sidebar (col 2, row 8, "RR"+rootRate). What is missing before this script
is the actual Live-savable/automatable widget: a live.numbox inside fs2pages.maxpat, same as
`fs2_rarm` (obj-148, "Ritmo Arm") is for harmRate.

    python tools/add_fs2_ritmo_raiz.py            dry run, writes nothing
    python tools/add_fs2_ritmo_raiz.py --apply    do it (device closed in Max AND Live)

## What changes, file by file

**forteseq/fs2pages.maxpat**: placed directly to the right of the existing R.Arm pair (obj-147/148,
presentation [196,522]/[196,536]), same page/row, free space confirmed at x=236-276 -- this bpatcher
pages by PANNING (`script sendbox fs2_pages offset ...`, see the "Paginar una UI de M4L" memory),
not by hide/show, so a box placed on this same absolute canvas region rides along with the R.Arm
row on whichever page reveals it; no FORTESEQ2.amxd paging script needs to change.

  * `fs2_lbl_rraiz` (comment "R.Raiz") + `fs2_rraiz` (live.numbox, 0-64, longname "Ritmo Raiz") --
    same shape as fs2_lbl_rarm/fs2_rarm.
  * `fs2_rraiz` -> `prepend setrootrate` -> obj-5 (the bpatcher's own outlet toward forteseq2.js),
    same as fs2_rarm -> obj-188 -> obj-5.
  * A new `outputvalue` message (varname `pg_init[4]`), fed by obj-1 (the bpatcher's inlet 0, which
    fans a single load-time bang into one `outputvalue` message per restorable control -- see
    pg_init/pg_init[1..3]/tp_init/rt_init/cm_init/es_init/md_init/pr_init) -> `fs2_rraiz` inlet 0,
    so the saved value re-fires into the engine on patch/device load exactly like every sibling.
  * A dedicated `receive FS2_G_ECHO` -> `route rraiz` -> `prepend set` -> `fs2_rraiz` chain, same
    precedent as add_fs2_rarm_echo_sync.py: setrootrate() in forteseq2.js emits
    `outlet(4, ["gecho","rraiz",rootRate])` down the same FS2_G_ECHO bus already carrying every
    other gecho token, so a Horizonte-popup drag (or a preset recall) moves the actual widget too,
    not just the engine's internal value. A dedicated receive is used rather than adding a token to
    an existing `route` -- see the route-outlet-off-by-one memory: inserting a token into a `route`
    shifts every later match outlet and moves reject off the end.

**forteseq/FORTESEQ2.amxd**: one new nested-parameter entry, `patcher.parameters["obj-484::obj-<id
of fs2_rraiz>"] = ["Ritmo Raiz", "Ritmo Raiz", 0]` -- obj-484 is fs2pages.maxpat's own bpatcher
instance (confirmed against the existing obj-484::obj-148 "Ritmo Arm" entry). Order 0 matches every
other nested parameter under this same bpatcher instance (all 115 of them are order 0 -- the dense
0..N-1 permutation rule applies to TOP-LEVEL parameters, not to a bpatcher's own nested ones, see
the amxd-parameter-registries memory).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

RARM_LABEL_ID = 'obj-147'
RARM_NUMBOX_ID = 'obj-148'
BPATCHER_OUTLET_ID = 'obj-5'    # "mensajes hacia [js forteseq2.js]"
BPATCHER_INLET_ID = 'obj-1'     # "init" -- fans a load-time bang into every pg_init/*_init message
NESTED_BPATCHER_ID = 'obj-484'  # fs2pages.maxpat's own instance inside FORTESEQ2.amxd


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2pages.maxpat -------------------------------------------------------------------
    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    ppg = pg['parameters']   # fs2pages.maxpat's OWN local registry -- bare id, not bpatcher-prefixed
    assert bx[RARM_NUMBOX_ID].get('varname') == 'fs2_rarm', 'obj-148 no es fs2_rarm'
    sa = bx[RARM_NUMBOX_ID]['saved_attribute_attributes']['valueof']
    assert sa['parameter_longname'] == 'Ritmo Arm' and sa['parameter_mmax'] == 64.0, sa
    assert bx[BPATCHER_OUTLET_ID]['maxclass'] == 'outlet'
    assert bx[BPATCHER_INLET_ID]['maxclass'] == 'inlet'
    assert not any(b['box'].get('varname') == 'fs2_rraiz' for b in pg['boxes']), 'ya aplicado'

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    label_id = fresh()
    pg['boxes'].append({'box': {
        'id': label_id, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'fontsize': 8.0,
        'varname': 'fs2_lbl_rraiz', 'text': 'R.Raiz',
        'patching_rect': [140.0, 2440.0, 40.0, 16.0],
        'presentation': 1, 'presentation_rect': [236.0, 522.0, 40.0, 16.0]}})

    numbox_id = fresh()
    pg['boxes'].append({'box': {
        'id': numbox_id, 'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2,
        'outlettype': ['', 'float'], 'parameter_enable': 1, 'varname': 'fs2_rraiz',
        'annotation': 'Cada cuantos pasos avanza Sec Raiz. En 0 el root walk sigue atado a la '
                       'armonia, como siempre (avanza cuando avanza el set -- ver Ritmo Arm). Con '
                       'cualquier otro valor Sec Raiz tiene su PROPIO reloj, independiente de '
                       'cuando (o si) cambia el set.',
        'patching_rect': [140.0, 2459.0, 38.0, 15.0],
        'presentation': 1, 'presentation_rect': [236.0, 536.0, 38.0, 15.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_modmode': 4,
            'parameter_mmin': 0.0, 'parameter_mmax': 64.0,
            'parameter_initial': [0], 'parameter_initial_enable': 1,
            'parameter_longname': 'Ritmo Raiz', 'parameter_shortname': 'Ritmo Raiz'}}}})
    ppg[numbox_id] = ['Ritmo Raiz', 'Ritmo Raiz', 0]   # fs2pages.maxpat's own local registry entry

    prep_id = fresh()
    pg['boxes'].append({'box': {
        'id': prep_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_rraiz_prep', 'patching_rect': [140.0, 2489.0, 150.0, 22.0],
        'text': 'prepend setrootrate'}})
    pg['lines'].append({'patchline': {'source': [numbox_id, 0], 'destination': [prep_id, 0]}})
    pg['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': [BPATCHER_OUTLET_ID, 0]}})

    init_id = fresh()
    pg['boxes'].append({'box': {
        'id': init_id, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'pg_init[4]', 'patching_rect': [140.0, 2519.0, 70.0, 22.0],
        'text': 'outputvalue'}})
    pg['lines'].append({'patchline': {'source': [BPATCHER_INLET_ID, 0], 'destination': [init_id, 0]}})
    pg['lines'].append({'patchline': {'source': [init_id, 0], 'destination': [numbox_id, 0]}})

    recv_id = fresh()
    pg['boxes'].append({'box': {
        'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_rraiz_gecho_rx', 'patching_rect': [900.0, 4350.0, 160.0, 20.0],
        'text': 'receive FS2_G_ECHO'}})

    route_id = fresh()
    pg['boxes'].append({'box': {
        'id': route_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
        'outlettype': ['', ''], 'varname': 'fs2_rraiz_gecho_route',
        'patching_rect': [900.0, 4380.0, 160.0, 20.0], 'text': 'route rraiz'}})
    pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

    setrx_id = fresh()
    pg['boxes'].append({'box': {
        'id': setrx_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_rraiz_gecho_setrx', 'patching_rect': [900.0, 4410.0, 160.0, 22.0],
        'text': 'prepend set'}})
    pg['lines'].append({'patchline': {'source': [route_id, 0], 'destination': [setrx_id, 0]}})
    pg['lines'].append({'patchline': {'source': [setrx_id, 0], 'destination': [numbox_id, 0]}})

    print('fs2pages.maxpat: +%s (R.Raiz label) +%s (fs2_rraiz live.numbox 0-64)' % (label_id, numbox_id))
    print('  +%s (prepend setrootrate) -> %s (bpatcher outlet)' % (prep_id, BPATCHER_OUTLET_ID))
    print('  +%s (pg_init[4] outputvalue) <- %s (bpatcher inlet)' % (init_id, BPATCHER_INLET_ID))
    print('  +%s (receive FS2_G_ECHO) -> +%s (route rraiz) -> +%s (prepend set) -> %s'
          % (recv_id, route_id, setrx_id, numbox_id))

    # ---- FORTESEQ2.amxd ---------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    PP = P['parameters']
    key = '%s::%s' % (NESTED_BPATCHER_ID, numbox_id)
    assert '%s::%s' % (NESTED_BPATCHER_ID, RARM_NUMBOX_ID) in PP, 'obj-484::obj-148 no encontrado'
    assert key not in PP, 'ya aplicado en FORTESEQ2.amxd'
    PP[key] = ['Ritmo Raiz', 'Ritmo Raiz', 0]
    print('\nFORTESEQ2.amxd: parameters["%s"] = %r' % (key, PP[key]))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(PAGES, PAGES + '.before-ritmoraiz')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    shutil.copyfile(DEVICE, DEVICE + '.before-ritmoraiz')
    amxd.save(DEVICE, data, s, e, doc)

    pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
    bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert all(i in bx2 for i in (label_id, numbox_id, prep_id, init_id, recv_id, route_id, setrx_id))

    _, _, _, doc2 = amxd.load(DEVICE)
    assert key in doc2['patcher']['parameters']

    print('\nescrito %s y %s (.before-ritmoraiz guardado en ambos). Sigue:' % (PAGES, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js y js fs2horizon.js, el device completo, script stop/start')


main()
