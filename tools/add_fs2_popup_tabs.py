"""Turn the FORTESEQ2 floating popup (Proximos 16 / [p fs2_window]) from "Horizonte+Selector always
side by side, Solo Voces just widens Horizonte" into an EXCLUSIVE tab switcher: one view visible at
a time, chosen by a new "Vista Popup" live.tab (2 items today: Horizonte, Selector). Groundwork for
Fase 2 of the popup-UI plan -- Rollo and Presets get added later as one more tab item each, same
append-only convention as the main panel's "Voces N" pages, once those views actually exist.

    python tools/add_fs2_popup_tabs.py            dry run, writes nothing
    python tools/add_fs2_popup_tabs.py --apply    do it (device closed in Max AND Live)

## Why this changes the existing behaviour (confirmed with the user first)

Today Horizonte (fs2hz_ui) and Selector (fs2sp_ui) are both visible side by side inside the popup;
"Solo Voces" only widens Horizonte by hiding Selector. That two-panel layout does not extend to 4
views without the window growing without bound. The user picked exclusive tabs over keeping the
pair combined, so Solo Voces goes away and "Vista Popup" replaces it.

## What changes, file by file

**forteseq/fs2horizon.js**: removes `pickerVisible`/`solovoices()`/the conditional in `leftMargin()`
-- with exclusive tabs there is never a sibling sharing the window when Horizonte is shown, so the
margin-for-the-picker concept this existed for is gone. `leftMargin()` now always returns 0.
fs2setpick.js is untouched: its width was already a fixed PANEL_W regardless of Horizonte's
presence, so it needs no change to behave correctly under exclusive tabs.

**forteseq/FORTESEQ2.amxd**:
  * `obj-792` ("Solo Voces" live.toggle), `obj-794` (`sel 1`), `obj-795`/`obj-796` ("hidepicker"/
    "showpicker" messages) are removed.
  * New `live.tab` "Vista Popup" (enum ["Horizonte", "Selector"]) at the same screen position ->
    `prepend showview` -> into `obj-751` (the popup subpatcher)'s one inlet, same single-inlet
    multiplexing every other message into that subpatcher already uses.
  * `obj-793` (the "Voces" comment above the old toggle) is renamed "Vista".
  * Inside `obj-751`'s subpatcher: `obj-5` (`route hidepicker showpicker`) becomes `route showview`,
    followed by a new `sel 0 1` that drives two rewritten messages -- `obj-6` -> "script show
    fs2hz_ui, script hide fs2sp_ui" (Horizonte), `obj-7` -> "script hide fs2hz_ui, script show
    fs2sp_ui" (Selector) -- both still -> `thispatcher` (obj-8), unchanged. `obj-5`'s reject outlet
    keeps fanning every OTHER message (the whole querynext data feed on outlet 3) straight to both
    jsui's `obj-2`/`obj-3`, exactly as before -- only its outlet INDEX shifts (2 -> 1, since `route`
    with one keyword instead of two has one fewer outlet). `obj-9`/`obj-10` ("solovoices 1"/"0" into
    fs2hz_ui) are removed along with the handler they drove.
  * 1 top-level param removed (Solo Voces), 1 added (Vista Popup) -- net param count unchanged.
    Confirmed "Solo Voces" is not in any Push parameterbank (grepped the raw file), so nothing there
    needs updating.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
HORIZON_JS = os.path.join('forteseq', 'fs2horizon.js')

TOGGLE_ID = 'obj-792'
LABEL_ID = 'obj-793'
SEL_ID = 'obj-794'
HIDE_MSG_ID = 'obj-795'
SHOW_MSG_ID = 'obj-796'
WIN_ID = 'obj-751'          # [p fs2_window]
OLD_TOGGLE_PRECT = [894.0, 46.0, 15.0, 15.0]


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2horizon.js ---------------------------------------------------------------------
    hz = open(HORIZON_JS, encoding='utf-8').read()
    assert 'pickerVisible' in hz, 'ya aplicado (o el archivo cambio de forma inesperada)'

    OLD_BLOCK = '''// solovoices <0|1> -- NOT from outlet 3: sent directly from the main device panel's "Solo Voces"
//   toggle (tools/add_hide_picker.py), straight to this jsui's inlet. 1 = the set-picker
//   (fs2setpick.js, drawn on top of this box's left edge) is hidden -- stop reserving it a
//   margin and draw full-width. 0 = restore the margin.
//
// Colour = the circle-of-fifths wheel from pccolor.js, sat/lum matched to fs2colmon / tonnetz.

include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var SELF = this;   // capturado para .patcher.wind (seguir a la ventana flotante)

// Patron tonnetz.js / animidi.js: la caja jsui se deja SOBREDIMENSIONADA (add_fs2_setpick.py) y
// paint() pinta dentro de viewportWH() -- el tamano real de la ventana del subpatcher. NO se
// confia en escribir box.rect (de solo lectura en el popup M4L) -- fitToWindow() lo intenta igual
// como bonus inerte, pero el tamano/posicion real de la caja quedan fijos desde que la ventana
// abre, sea cual sea el valor que este archivo escriba.
//
// Por eso "Solo Voces" (tools/add_hide_picker.py) NO mueve NINGUNA caja: la caja de este jsui ya
// arranca en x=8 (superpuesta con fs2setpick.js, que se dibuja encima por venir despues en la
// lista de boxes) y esta funcion simplemente deja de reservarle margen a la izquierda cuando el
// picker esta oculto. PICKER_W = ancho del picker (380) + gap (8); WPAD = margen del propio jsui.
// pickerVisible arranca en 1 (estado por defecto del toggle) y cambia con el mensaje "solovoices".
var WPAD = 8, PICKER_W = 388;
var pickerVisible = 1;
function solovoices(flag) {
	pickerVisible = flag ? 0 : 1;
	mgraphics.redraw();
}
function windSize() {
	try {
		var s = SELF.patcher.wind.size;
		if (s && s[0] > 60 && s[1] > 60) return s;
	} catch (e) {}
	return null;
}
function leftMargin() { return pickerVisible ? PICKER_W : 0; }
function viewportWH() {
	var s = windSize();
	var margin = leftMargin();
	if (s) return [Math.max(300, Math.round(s[0]) - margin - WPAD * 2),
		Math.max(140, Math.round(s[1]) - WPAD * 2)];
	return [844 + (pickerVisible ? 0 : PICKER_W), 284];   // sin lectura de ventana
}'''

    NEW_BLOCK = '''// Colour = the circle-of-fifths wheel from pccolor.js, sat/lum matched to fs2colmon / tonnetz.

include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var SELF = this;   // capturado para .patcher.wind (seguir a la ventana flotante)

// Patron tonnetz.js / animidi.js: la caja jsui se deja SOBREDIMENSIONADA (add_fs2_setpick.py) y
// paint() pinta dentro de viewportWH() -- el tamano real de la ventana del subpatcher. NO se
// confia en escribir box.rect (de solo lectura en el popup M4L) -- fitToWindow() lo intenta igual
// como bonus inerte, pero el tamano/posicion real de la caja quedan fijos desde que la ventana
// abre, sea cual sea el valor que este archivo escriba.
//
// "Vista Popup" (tools/add_fs2_popup_tabs.py) hace a Horizonte y Selector EXCLUYENTES -- un
// "script show/hide" real sobre la caja del que no se ve, ya no una superposicion con margen
// reservado -- asi que este jsui ya no necesita reservarle espacio a nadie: cuando esta oculto,
// fs2setpick.js no dibuja nada encima.
var WPAD = 8;
function windSize() {
	try {
		var s = SELF.patcher.wind.size;
		if (s && s[0] > 60 && s[1] > 60) return s;
	} catch (e) {}
	return null;
}
function leftMargin() { return 0; }
function viewportWH() {
	var s = windSize();
	var margin = leftMargin();
	if (s) return [Math.max(300, Math.round(s[0]) - margin - WPAD * 2),
		Math.max(140, Math.round(s[1]) - WPAD * 2)];
	return [844, 284];   // sin lectura de ventana
}'''

    assert OLD_BLOCK in hz, 'el bloque esperado no calzo -- reviso fs2horizon.js a mano'
    hz2 = hz.replace(OLD_BLOCK, NEW_BLOCK)
    assert 'pickerVisible' not in hz2 and 'solovoices' not in hz2 and 'PICKER_W' not in hz2

    # ---- FORTESEQ2.amxd ---------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert bx[TOGGLE_ID]['saved_attribute_attributes']['valueof']['parameter_longname'] == 'Solo Voces'
    win = bx[WIN_ID]
    subP = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in subP['boxes']}
    assert sbx['obj-5']['text'] == 'route hidepicker showpicker', sbx['obj-5']['text']

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    # -- remove the old toggle + its router + messages, rename its label. Dropping only lines that
    # touch a removed box on either end leaves every OTHER feed into obj-751 (obj-23/obj-663/
    # obj-747, none of them removed) untouched automatically -- no need to single them out.
    removed_boxes = {TOGGLE_ID, SEL_ID, HIDE_MSG_ID, SHOW_MSG_ID}
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in removed_boxes]
    P['lines'] = [l for l in P['lines'] if l['patchline']['source'][0] not in removed_boxes
                  and l['patchline']['destination'][0] not in removed_boxes]

    del PP[TOGGLE_ID]
    bx[LABEL_ID]['text'] = 'Vista'

    tab_id = fresh()
    vo = {'parameter_longname': 'Vista Popup', 'parameter_shortname': 'Vista Popup',
          'parameter_type': 2, 'parameter_modmode': 0, 'parameter_enum': ['Horizonte', 'Selector'],
          'parameter_mmax': 1, 'parameter_initial': [0], 'parameter_initial_enable': 1,
          'parameter_unitstyle': 9}
    P['boxes'].append({'box': {
        'id': tab_id, 'maxclass': 'live.tab', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'parameter_enable': 1, 'varname': 'fs2_popupview',
        'annotation': 'Que vista muestra la ventana flotante "Proximos 16": Horizonte (lectura por '
                      'voz) o Selector (elegir/fijar un set Forte). Reemplaza a Solo Voces -- ahora '
                      'son excluyentes, no una al lado de la otra.',
        'patching_rect': [2600.0, 2700.0, 70.0, 18.0],
        'presentation': 1, 'presentation_rect': [OLD_TOGGLE_PRECT[0], OLD_TOGGLE_PRECT[1] - 2.0, 70.0, 18.0],
        'saved_attribute_attributes': {'valueof': vo}, 'id': tab_id}})
    PP[tab_id] = ['Vista Popup', 'Vista Popup', 0]

    prep_id = fresh()
    P['boxes'].append({'box': {
        'id': prep_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_popupview_prep',
        'patching_rect': [2600.0, 2730.0, 140.0, 20.0], 'text': 'prepend showview'}})

    P['lines'].append({'patchline': {'source': [tab_id, 0], 'destination': [prep_id, 0]}})
    P['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': [WIN_ID, 0]}})

    # -- rewire the popup subpatcher's own router
    sbx['obj-5']['text'] = 'route showview'
    sbx['obj-5']['numoutlets'] = 2
    sbx['obj-5']['outlettype'] = ['', '']
    sbx['obj-6']['text'] = 'script show fs2hz_ui, script hide fs2sp_ui'
    sbx['obj-7']['text'] = 'script hide fs2hz_ui, script show fs2sp_ui'

    new_sel = 'obj-11'
    assert new_sel not in sbx
    subP['boxes'].append({'box': {
        'id': new_sel, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 3,
        'outlettype': ['bang', 'bang', ''],
        'patching_rect': [400.0, 1483.0, 100.0, 20.0], 'text': 'sel 0 1'}})
    subP['boxes'] = [b for b in subP['boxes'] if b['box']['id'] not in ('obj-9', 'obj-10')]

    # obj-5's old 3 outgoing wires get replaced below with the new 2-outlet routing; obj-9/obj-10
    # (the "solovoices" messages) are being deleted along with the boxes themselves.
    subP['lines'] = [l for l in subP['lines'] if l['patchline']['source'][0] not in ('obj-5', 'obj-9', 'obj-10')]
    subP['lines'].append({'patchline': {'source': ['obj-5', 0], 'destination': [new_sel, 0]}})
    subP['lines'].append({'patchline': {'source': [new_sel, 0], 'destination': ['obj-6', 0]}})
    subP['lines'].append({'patchline': {'source': [new_sel, 1], 'destination': ['obj-7', 0]}})
    subP['lines'].append({'patchline': {'source': ['obj-5', 1], 'destination': ['obj-2', 0]}})
    subP['lines'].append({'patchline': {'source': ['obj-5', 1], 'destination': ['obj-3', 0]}})

    print('fs2horizon.js: removed pickerVisible/solovoices(), leftMargin() always 0')
    print('FORTESEQ2.amxd: removed %s/%s/%s/%s (Solo Voces + router)' %
          (TOGGLE_ID, SEL_ID, HIDE_MSG_ID, SHOW_MSG_ID))
    print('  new live.tab "Vista Popup" (%s) -> prepend showview (%s) -> %s' % (tab_id, prep_id, WIN_ID))
    print('  %s label -> "Vista"' % LABEL_ID)
    print('  inside %s: route hidepicker showpicker -> route showview + new sel 0 1 (%s)' % (WIN_ID, new_sel))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    open(HORIZON_JS, 'w', encoding='utf-8', newline='\n').write(hz2)
    shutil.copyfile(DEVICE, DEVICE + '.before-popuptabs')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert TOGGLE_ID not in bx2 and tab_id in bx2
    win2 = bx2[WIN_ID]['patcher']
    sbx2 = {b['box']['id']: b['box'] for b in win2['boxes']}
    assert sbx2['obj-5']['text'] == 'route showview'
    assert new_sel in sbx2 and 'obj-9' not in sbx2 and 'obj-10' not in sbx2

    print('\nescrito %s y %s (.before-popuptabs del .amxd guardado). Sigue:' % (HORIZON_JS, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, la fs2horizon jsui, el device completo, script stop/start')


main()
