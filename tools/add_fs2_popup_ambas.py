"""Add a third "Ambas" item to FORTESEQ2's floating-popup "Vista Popup" tab, so Horizonte
(fs2horizon.js) and Selector (fs2setpick.js) can be shown together, side by side, without giving
up the exclusive Horizonte/Selector tabs added by tools/add_fs2_popup_tabs.py (which exist so
Rollo/Presets can each get their own tab later without the window growing without bound).

    python tools/add_fs2_popup_ambas.py            dry run, writes nothing
    python tools/add_fs2_popup_ambas.py --apply    do it (device closed in Max AND Live)

## Why a third tab item instead of reverting to always-side-by-side

tools/add_fs2_popup_tabs.py deliberately replaced the original always-side-by-side layout
(tools/add_fs2_setpick.py) with exclusive tabs because two panels sharing one window does not
scale to N views. Re-merging them unconditionally would undo that. Instead "Ambas" is a third,
opt-in state: Horizonte and Selector stay independent tabs (and still make room for future ones),
and this one additional item recreates the old combined view on demand.

## What changes, file by file

**forteseq/fs2horizon.js**: reintroduces a `leftMargin()` that is 0 by default (same as today,
under Horizonte-alone or Selector-alone) and `PICKER_W` (388 = fs2setpick.js's PANEL_W 380 + its
own GAP 8) when the jsui receives a new `bothview 1` message straight to its inlet (mirrors how
the old `solovoices` message worked pre-tabs) -- `bothview 0` restores full width. fs2setpick.js
needs no change: its width was already a fixed PANEL_W regardless of what else is on screen, and
it is already listed after fs2hz_ui in the popup subpatcher's box list, so it paints on top of
fs2horizon.js's now-unused left margin exactly like the pre-tabs layout did.

**forteseq/FORTESEQ2.amxd**, inside `obj-751`'s subpatcher ([p fs2_window]):
  * `obj-806` (the "Vista Popup" live.tab)'s enum grows from ["Horizonte", "Selector"] to
    ["Horizonte", "Selector", "Ambas"]; `parameter_mmax` 1 -> 2.
  * `obj-11` (`sel 0 1`) becomes `sel 0 1 2` (3 match outlets + reject, was 2 + reject).
  * New message `script show fs2hz_ui, script show fs2sp_ui` on the new outlet 2, alongside the
    existing `obj-6`/`obj-7` messages, all -> `obj-8` (thispatcher), unchanged wiring pattern.
  * Two new messages, `bothview 1` and `bothview 0`, sent straight to `obj-2` (fs2hz_ui)'s own
    inlet -- NOT through `obj-5`'s reject outlet (that one still only carries the shared querynext
    data feed to both jsui, untouched). `bothview 1` fires only from the new Ambas outlet;
    `bothview 0` fires from both the Horizonte and Selector outlets, so leaving Ambas by any path
    resets the margin.
  * No boxes removed, no params removed -- 1 param's enum/mmax changed (still counts as 1 param).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
HORIZON_JS = os.path.join('forteseq', 'fs2horizon.js')

WIN_ID = 'obj-751'      # [p fs2_window]
TAB_ID = 'obj-806'      # "Vista Popup" live.tab
SEL_ID = 'obj-11'       # sel 0 1 (inside the subpatcher)
HZ_UI_ID = 'obj-2'      # fs2hz_ui jsui (inside the subpatcher)
HZ_MSG_ID = 'obj-6'     # existing Horizonte message
SP_MSG_ID = 'obj-7'     # existing Selector message
THISPATCHER_ID = 'obj-8'


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2horizon.js ---------------------------------------------------------------------
    hz = open(HORIZON_JS, encoding='utf-8').read()
    assert 'function bothview(' not in hz, 'ya aplicado'
    assert "function leftMargin() { return 0; }" in hz, \
        'el bloque esperado no calzo -- reviso fs2horizon.js a mano (post add_fs2_popup_tabs.py?)'

    hz2 = hz.replace(
        "function leftMargin() { return 0; }",
        "function leftMargin() { return bothVisible ? PICKER_W : 0; }")
    assert hz2 != hz

    OLD_VAR = "var WPAD = 8;\n"
    NEW_VAR = ("var WPAD = 8, PICKER_W = 388;   // PICKER_W = PANEL_W(380) + GAP(8) de fs2setpick.js\n"
               "var bothVisible = 0;\n"
               "function bothview(flag) {\n"
               "\tbothVisible = flag ? 1 : 0;\n"
               "\tmgraphics.redraw();\n"
               "}\n")
    assert OLD_VAR in hz2, 'no encontre "var WPAD = 8;" a solas -- reviso fs2horizon.js a mano'
    hz2 = hz2.replace(OLD_VAR, NEW_VAR)

    OLD_FALLBACK = "\treturn [844, 284];   // sin lectura de ventana\n"
    NEW_FALLBACK = "\treturn [844 + (bothVisible ? PICKER_W : 0), 284];   // sin lectura de ventana\n"
    assert OLD_FALLBACK in hz2
    hz2 = hz2.replace(OLD_FALLBACK, NEW_FALLBACK)

    # ---- FORTESEQ2.amxd ---------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}

    win = bx[WIN_ID]
    subP = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in subP['boxes']}
    assert sbx[SEL_ID]['text'] == 'sel 0 1', sbx[SEL_ID]['text']
    assert bx[TAB_ID]['saved_attribute_attributes']['valueof']['parameter_longname'] == 'Vista Popup'

    vo = bx[TAB_ID]['saved_attribute_attributes']['valueof']
    assert vo['parameter_enum'] == ['Horizonte', 'Selector']
    vo['parameter_enum'] = ['Horizonte', 'Selector', 'Ambas']
    vo['parameter_mmax'] = 2

    sbx[SEL_ID]['text'] = 'sel 0 1 2'
    sbx[SEL_ID]['numoutlets'] = 4
    sbx[SEL_ID]['outlettype'] = ['bang', 'bang', 'bang', '']

    sub_ids = [int(i.split('-')[1]) for i in sbx]
    nid = [max(sub_ids)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    ambas_msg = fresh()
    both_on = fresh()
    both_off = fresh()

    sel_rect = sbx[SEL_ID]['patching_rect']
    subP['boxes'].append({'box': {
        'id': ambas_msg, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [sel_rect[0] + 250.0, sel_rect[1] + 67.0, 260.0, 31.0],
        'text': 'script show fs2hz_ui, script show fs2sp_ui'}})
    subP['boxes'].append({'box': {
        'id': both_on, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [sel_rect[0] + 250.0, sel_rect[1] + 110.0, 70.0, 20.0],
        'text': 'bothview 1'}})
    subP['boxes'].append({'box': {
        'id': both_off, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [sel_rect[0] + 340.0, sel_rect[1] + 110.0, 70.0, 20.0],
        'text': 'bothview 0'}})

    subP['lines'].append({'patchline': {'source': [SEL_ID, 2], 'destination': [ambas_msg, 0]}})
    subP['lines'].append({'patchline': {'source': [ambas_msg, 0], 'destination': [THISPATCHER_ID, 0]}})
    subP['lines'].append({'patchline': {'source': [SEL_ID, 2], 'destination': [both_on, 0]}})
    subP['lines'].append({'patchline': {'source': [both_on, 0], 'destination': [HZ_UI_ID, 0]}})
    subP['lines'].append({'patchline': {'source': [SEL_ID, 0], 'destination': [both_off, 0]}})
    subP['lines'].append({'patchline': {'source': [SEL_ID, 1], 'destination': [both_off, 0]}})
    subP['lines'].append({'patchline': {'source': [both_off, 0], 'destination': [HZ_UI_ID, 0]}})

    print('fs2horizon.js: bothview()/PICKER_W added, leftMargin() gated on bothVisible')
    print('FORTESEQ2.amxd: %s enum -> Horizonte/Selector/Ambas (mmax 2)' % TAB_ID)
    print('  %s: sel 0 1 -> sel 0 1 2' % SEL_ID)
    print('  new outlet 2 -> %s (script show both) + %s (bothview 1 -> %s)' %
          (ambas_msg, both_on, HZ_UI_ID))
    print('  outlets 0/1 also -> %s (bothview 0 -> %s)' % (both_off, HZ_UI_ID))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    open(HORIZON_JS, 'w', encoding='utf-8', newline='\n').write(hz2)
    shutil.copyfile(DEVICE, DEVICE + '.before-popupambas')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    win2 = bx2[WIN_ID]['patcher']
    sbx2 = {b['box']['id']: b['box'] for b in win2['boxes']}
    assert sbx2[SEL_ID]['text'] == 'sel 0 1 2'
    assert ambas_msg in sbx2 and both_on in sbx2 and both_off in sbx2
    assert bx2[TAB_ID]['saved_attribute_attributes']['valueof']['parameter_enum'] == \
        ['Horizonte', 'Selector', 'Ambas']

    print('\nescrito %s y %s (.before-popupambas del .amxd guardado). Sigue:' % (HORIZON_JS, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, la fs2horizon jsui, el device completo, script stop/start')
    print('  en Live: probar las 3 vistas del "Vista Popup" (Horizonte / Selector / Ambas)')


main()
