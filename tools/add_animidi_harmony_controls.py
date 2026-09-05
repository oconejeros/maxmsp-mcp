"""One-off: add the ColorMode Acorde/Disonancia enum items and a HarmLane toggle to
ANIMIDI.amxd, by hand (the MCP live-edit path lost its edits when the device was closed
without saving -- .amxd changes made live in Max only persist on an explicit save, and
the device got reopened from the untouched file on disk).

Mirrors aw_vellane (VelLane) exactly -- same box shape, same outputvalue-bang wiring
(a live.toggle fed a raw bang inverts its state; see aw_ov_tgl) -- so the new HarmLane
toggle behaves identically to VelLane/NoteTags/Piano.

Touches all four registries that matter here (see amxd-parameter-registries note):
  1. the new box's own saved_attribute_attributes.valueof                  (local)
  2. the an_window subpatcher's own `parameters` dict                     (local, obj-14x)
  3. the top-level ANIMIDI.amxd `parameters` dict, composite obj-10::obj-14x key
  4. `parameterbanks` bank 3 ("Vistas 3"), which has two free "-" slots

Run with the device closed in both Max and Live. Takes a .before backup first.
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'forteseq', 'ANIMIDI.amxd')


def find_box(boxes, varname):
    for entry in boxes:
        b = entry.get('box', {})
        if b.get('varname') == varname:
            return b
    raise KeyError(varname)


def main():
    backup = PATH + '.before'
    if not os.path.exists(backup):
        with open(PATH, 'rb') as f:
            raw = f.read()
        with open(backup, 'wb') as f:
            f.write(raw)
        print('backup written: ' + backup)

    data, start, end, doc = amxd.load(PATH)
    root = doc['patcher']

    an_window = find_box(root['boxes'], 'an_window')
    win = an_window['patcher']
    win_boxes = win['boxes']
    win_params = win['parameters']

    # --- 1. ColorMode: add the two new enum items + bump parameter_mmax --------------
    colormode = find_box(win_boxes, 'aw_colormode')
    vo = colormode['saved_attribute_attributes']['valueof']
    assert vo['parameter_enum'] == ['Nota', 'Voz', 'Fijo'], vo['parameter_enum']
    vo['parameter_enum'] = ['Nota', 'Voz', 'Fijo', 'Acorde', 'Disonancia']
    vo['parameter_mmax'] = 4
    colormode['annotation'] = (
        'De donde sale el color de las barras: Nota = clase de altura (rueda de quintas, '
        'tipo tonnetz; HueC/sat/lum la ajustan). Voz = un color por pista. Fijo = un solo '
        'color. Acorde = mezcla OKLab del acorde sonando. Disonancia = McKay % del acorde, '
        'por niveles/threshold.'
    )

    # --- 2. clone aw_vellane -> aw_harmlane (live.toggle) -----------------------------
    vellane = find_box(win_boxes, 'aw_vellane')
    harmlane = copy.deepcopy(vellane)
    harmlane['id'] = 'obj-142'
    harmlane['varname'] = 'aw_harmlane'
    harmlane['patching_rect'] = [934.0, 71.0, 16.0, 16.0]
    harmlane['patching_position'] = [934.0, 71.0]
    harmlane['presentation_rect'] = [934.0, 71.0, 16.0, 16.0]
    harmlane['presentation_position'] = [934.0, 71.0]
    harmlane['annotation'] = (
        'Barras: agrega abajo un carril de espectro de color de armonia (bloques '
        'contiguos coloreados por disonancia McKay, en niveles/threshold) -- independiente '
        'del ColorMode, como el carril de velocity.'
    )
    hvo = harmlane['saved_attribute_attributes']['valueof']
    hvo['parameter_longname'] = 'HarmLane'
    hvo['parameter_shortname'] = 'HarmLane'
    win_boxes.append({'box': harmlane})

    # --- 3. clone aw_pp_vellane -> aw_pp_harmlane (hidden "prepend harmlane") ---------
    pp_vellane = find_box(win_boxes, 'aw_pp_vellane')
    pp_harmlane = copy.deepcopy(pp_vellane)
    pp_harmlane['id'] = 'obj-142p'
    pp_harmlane['varname'] = 'aw_pp_harmlane'
    pp_harmlane['text'] = 'prepend harmlane'
    pp_harmlane['patching_rect'] = [16.0, 1268.0, 130.0, 22.0]
    pp_harmlane['patching_position'] = [16.0, 1268.0]
    win_boxes.append({'box': pp_harmlane})

    # --- 4. the "arm" label next to the new toggle (mirrors the "vel"/"notas" labels) -
    lb_vellane = find_box(win_boxes, 'aw_lb800_72')
    lb_harmlane = copy.deepcopy(lb_vellane)
    lb_harmlane['id'] = 'obj-l906_72'
    lb_harmlane['varname'] = 'aw_lb906_72'
    lb_harmlane['text'] = 'arm'
    lb_harmlane['patching_rect'] = [906.0, 72.0, 24.0, 15.0]
    lb_harmlane['patching_position'] = [906.0, 72.0]
    lb_harmlane['presentation_rect'] = [906.0, 72.0, 24.0, 15.0]
    lb_harmlane['presentation_position'] = [906.0, 72.0]
    win_boxes.append({'box': lb_harmlane})

    # --- 5. wiring: aw_ov_tgl -> aw_harmlane -> aw_pp_harmlane -> aw_ui ---------------
    win['lines'].append({'patchline': {'source': ['obj-198', 0], 'destination': ['obj-142', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-142', 0], 'destination': ['obj-142p', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-142p', 0], 'destination': ['obj-101', 0]}})

    # --- 6. registry 2 (local to an_window) + registry 4 (top-level, composite key) --
    assert win_params['obj-129'] == ['Clear', 'Clear', 21], win_params['obj-129']
    win_params['obj-142'] = ['HarmLane', 'HarmLane', 22]

    top_params = root['parameters']
    assert top_params['obj-10::obj-129'] == ['Clear', 'Clear', 22], top_params['obj-10::obj-129']
    top_params['obj-10::obj-142'] = ['HarmLane', 'HarmLane', 23]

    # --- 7. parameterbanks: bank 3 ("Vistas 3") has two free "-" slots ---------------
    bank3 = top_params['parameterbanks']['3']
    assert bank3['name'] == 'Vistas 3', bank3['name']
    idx = bank3['parameters'].index('-')
    bank3['parameters'][idx] = 'HarmLane'

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # --- verify by reading the file back ---------------------------------------------
    _, _, _, doc2 = amxd.load(PATH)
    win2 = find_box(doc2['patcher']['boxes'], 'an_window')['patcher']
    cm2 = find_box(win2['boxes'], 'aw_colormode')['saved_attribute_attributes']['valueof']
    assert cm2['parameter_enum'] == ['Nota', 'Voz', 'Fijo', 'Acorde', 'Disonancia']
    assert cm2['parameter_mmax'] == 4
    hl2 = find_box(win2['boxes'], 'aw_harmlane')
    assert hl2['saved_attribute_attributes']['valueof']['parameter_longname'] == 'HarmLane'
    local_orders = sorted(v[2] for k, v in win2['parameters'].items() if k != 'inherited_shortname')
    assert local_orders == list(range(23)), local_orders
    top2 = doc2['patcher']['parameters']
    top_orders = sorted(v[2] for k, v in top2.items()
                         if k not in ('parameterbanks', 'inherited_shortname', 'parameter_overrides'))
    assert top_orders == list(range(24)), top_orders
    assert top2['parameterbanks']['3']['parameters'][2] == 'HarmLane'
    print('OK: enum, mmax, box, wiring targets, and both order registries verified.')


if __name__ == '__main__':
    main()
