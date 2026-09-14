"""Click a voice's row in the "Proximos 16 pasos" popup (Horizonte view) to jump the main panel
straight to that voice's "Voces N" tab -- Fase 3 interactivity from the popup-UI plan.

    python tools/add_fs2_horizon_jump.py            dry run, writes nothing
    python tools/add_fs2_horizon_jump.py --apply    do it (device closed in Max AND Live)

## Mechanism

fs2horizon.js's jsui box (obj-2) already has an outlet declared (numoutlets=1, unused until now --
fs2setpick.js's sibling jsui is the only one that has ever used its own). A new `onclick()` finds
which row was hit from `rowGeo` (headH/rowH/nRows, captured at the end of every paint() the same
way fs2setpick.js already captures `geo` for its own onclick()) and sends `outlet(0, ['jumpvoice',
v])`. That wire joins the existing one from fs2setpick.js into `obj-4` (the subpatcher's shared
outlet), which already reaches the engine (obj-23) at the top level -- a new `route jumpvoice`
spliced in front of obj-23 intercepts it there and reject-passes everything else through unchanged.

Getting from a voice index to a page jump is a lookup, not arithmetic: Pagina's enum has a gap
("Globales" sits between "Voces 2" and "Voces 3"), so V1..V4 map to page indices 6,7,9,10, not
6,7,8,9. A live.tab restored via a plain "set N" does not fire its own outlet (the same quirk that
makes `outputvalue` exist elsewhere in this device), so each of the 4 branches sends Pagina both
"set <page>" and "outputvalue" from ONE message box (comma-separated messages fire left to right),
which re-triggers the EXISTING obj-486 (`sel 0..10`) tab router exactly as a real click would --
no duplicate page-switching logic, just driving the one control that already owns it.

## What changes, file by file

**forteseq/fs2horizon.js**: new module state `rowGeo` (set at the end of `paint()`), new
`onclick(x, y, but)` + `VOCES_PAGE` lookup.

**forteseq/FORTESEQ2.amxd**:
  * Inside `obj-751` ([p fs2_window]): `obj-2` (fs2hz_ui) outlet 0 -> `obj-4` (the subpatcher's
    shared outlet), joining fs2setpick.js's existing wire there.
  * At the top level: `obj-751 -> obj-23` (straight into the engine) gets a `route jumpvoice`
    spliced in between -- reject still goes straight to `obj-23`, unchanged. The match (a voice
    index 0-3) goes through a `sel 0 1 2 3` into 4 message boxes ("set 6, outputvalue" .. "set 10,
    outputvalue") -> `obj-485` (Pagina).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
HORIZON_JS = os.path.join('forteseq', 'fs2horizon.js')

WIN_ID = 'obj-751'
ENGINE_ID = 'obj-23'
PAGINA_ID = 'obj-485'
VOCES_PAGE = [6, 7, 9, 10]   # Pagina index for V1..V4 (Globales sits between Voces 2 and Voces 3)

OLD_PAINT_SNIPPET = '''	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH);
	var rowH = gridH / nRows;'''

NEW_PAINT_SNIPPET = '''	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH);
	var rowH = gridH / nRows;
	rowGeo = { headH: headH, rowH: rowH, nRows: nRows };   // read by onclick() to find the row hit'''

ONCLICK_BLOCK = '''
// Geometry of the last paint(), so onclick() can tell which voice row a click landed on -- same
// "paint() records, onclick() reads" pattern fs2setpick.js already uses for its own `geo`.
var rowGeo = null;

// Click anywhere on a voice's row -> jump the main panel to that voice's "Voces N" tab. Pagina's
// own restore/jump plumbing (obj-486's sel router) does the rest; see add_fs2_horizon_jump.py.
var VOCES_PAGE = [6, 7, 9, 10];   // Pagina index for V1..V4
function onclick(x, y, but) {
	if (!but || !rowGeo) return;
	if (y < rowGeo.headH) return;
	var v = Math.floor((y - rowGeo.headH) / rowGeo.rowH);
	if (v < 0 || v >= rowGeo.nRows || v >= VOCES_PAGE.length) return;
	outlet(0, ['jumpvoice', v]);
}
'''


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2horizon.js ---------------------------------------------------------------------
    hz = open(HORIZON_JS, encoding='utf-8').read()
    assert 'rowGeo' not in hz and 'function onclick' not in hz, 'ya aplicado'
    assert OLD_PAINT_SNIPPET in hz, 'el bloque de paint() esperado no calzo -- reviso a mano'
    hz2 = hz.replace(OLD_PAINT_SNIPPET, NEW_PAINT_SNIPPET)
    assert hz2.count('function paint()') == 1
    hz2 = hz2.replace('function paint() {', ONCLICK_BLOCK + '\nfunction paint() {', 1)

    # ---- FORTESEQ2.amxd ---------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    win = bx[WIN_ID]
    subP = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in subP['boxes']}
    assert sbx['obj-2']['filename'] == 'fs2horizon.js' and sbx['obj-4']['maxclass'] == 'outlet'
    assert not any(l['patchline']['source'] == ['obj-2', 0] for l in subP['lines']), 'ya aplicado'

    subP['lines'].append({'patchline': {'source': ['obj-2', 0], 'destination': ['obj-4', 0]}})

    pag = bx[PAGINA_ID]['saved_attribute_attributes']['valueof']
    assert pag['parameter_enum'][6:11] == ['Voces 1', 'Voces 2', 'Globales', 'Voces 3', 'Voces 4'], pag['parameter_enum']

    assert any(l['patchline']['source'] == [WIN_ID, 0] and l['patchline']['destination'] == [ENGINE_ID, 0]
               for l in P['lines']), 'no encontre el cable obj-751 -> obj-23'
    P['lines'] = [l for l in P['lines'] if not (l['patchline']['source'] == [WIN_ID, 0] and
                                                 l['patchline']['destination'] == [ENGINE_ID, 0])]

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    route_id = fresh()
    P['boxes'].append({'box': {
        'id': route_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2, 'outlettype': ['', ''],
        'patching_rect': [2600.0, 2760.0, 140.0, 20.0], 'text': 'route jumpvoice'}})
    sel_id = fresh()
    P['boxes'].append({'box': {
        'id': sel_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 5,
        'outlettype': ['bang', 'bang', 'bang', 'bang', ''],
        'patching_rect': [2600.0, 2790.0, 140.0, 20.0], 'text': 'sel 0 1 2 3'}})

    P['lines'].append({'patchline': {'source': [WIN_ID, 0], 'destination': [route_id, 0]}})
    P['lines'].append({'patchline': {'source': [route_id, 1], 'destination': [ENGINE_ID, 0]}})
    P['lines'].append({'patchline': {'source': [route_id, 0], 'destination': [sel_id, 0]}})

    msg_ids = []
    for vi, page in enumerate(VOCES_PAGE):
        mid = fresh()
        P['boxes'].append({'box': {
            'id': mid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
            'patching_rect': [2600.0 + 150.0 * vi, 2820.0, 140.0, 35.0],
            'text': 'set %d, outputvalue' % page}})
        P['lines'].append({'patchline': {'source': [sel_id, vi], 'destination': [mid, 0]}})
        P['lines'].append({'patchline': {'source': [mid, 0], 'destination': [PAGINA_ID, 0]}})
        msg_ids.append(mid)

    print('fs2horizon.js: +onclick()/rowGeo/VOCES_PAGE')
    print('inside %s: obj-2 (fs2hz_ui) outlet -> obj-4 (joins fs2setpick.js\'s existing wire)' % WIN_ID)
    print('%s -> %s spliced with route jumpvoice (%s) + sel 0 1 2 3 (%s)' % (WIN_ID, ENGINE_ID, route_id, sel_id))
    print('4 jump messages -> %s: %s' % (PAGINA_ID, msg_ids))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    open(HORIZON_JS, 'w', encoding='utf-8', newline='\n').write(hz2)
    shutil.copyfile(DEVICE, DEVICE + '.before-horizonjump')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert route_id in bx2 and sel_id in bx2
    win2 = bx2[WIN_ID]['patcher']
    sbx2 = {b['box']['id']: b['box'] for b in win2['boxes']}
    assert any(l['patchline']['source'] == ['obj-2', 0] for l in win2['lines'])

    print('\nescrito %s y %s (.before-horizonjump del .amxd guardado). Sigue:' % (HORIZON_JS, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, la fs2horizon jsui, el device completo, script stop/start')


main()
