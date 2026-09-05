"""One-off: add a ninth view toggle to tonnetz.amxd -- "Col", the AnWin colour-blend panel
(vcol in tonnetz.js) -- placed right after the existing "3D" (VwTet) checkbox in the Vistas row.

This is a SEPARATE control from HarmMode ("arm", added by add_tonnetz_harmmode.py): HarmMode's
swatch is the McKay dissonance BAND colour (same as the diso meter); vcol is an OKLab BLEND of
the actual AnWin-windowed pitch classes' own hues (pcToColor/mixColors) -- a different number
that can disagree with HarmMode on purpose. See tonnetz.js's `anwinset`/`paintAnwinColor`.

Wired exactly like the other view toggles (VwTet/tzw_vwtet): own dedicated `outputvalue`
message box fed by the shared loadbang (obj-199 / tzw_init), toggle -> prepend vcol -> jsui.

Touches all four registries (see amxd-parameter-registries note):
  1. the new box's own saved_attribute_attributes.valueof                  (local)
  2. the tz_window subpatcher's own `parameters` dict                     (local, obj-216)
  3. the top-level tonnetz.amxd `parameters` dict, composite obj-10::obj-216 key
  4. `parameterbanks` bank 5 ("Mas"), which has 1 free "-" slot left after HarmMode took the other

Run with the device closed in both Max and Live. Takes a .before backup first (skipped if one
from an earlier script run already exists).
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'forteseq', 'tonnetz.amxd')


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

    tz_window = find_box(root['boxes'], 'tz_window')
    win = tz_window['patcher']
    win_boxes = win['boxes']
    win_params = win['parameters']

    # --- 1. clone tzw_vwtet -> tzw_vcol (live.toggle), placed right after "3D" -------
    vwtet = find_box(win_boxes, 'tzw_vwtet')
    vcol = copy.deepcopy(vwtet)
    vcol['id'] = 'obj-216'
    vcol['varname'] = 'tzw_vcol'
    vcol['patching_rect'] = [330.0, 8.0, 14.0, 14.0]
    vcol['patching_position'] = [330.0, 8.0]
    vcol['presentation_rect'] = [330.0, 8.0, 14.0, 14.0]
    vcol['presentation_position'] = [330.0, 8.0]
    vcol['annotation'] = (
        'Muestra u oculta el panel "Color (AnWin)": una mezcla OKLab de los propios colores '
        'de las clases de altura consideradas por AnWin (pcToColor + mixColors, igual que '
        'invertedprism/multichord). Distinto del swatch de HarmMode -- ese es la banda de '
        'disonancia McKay, no una mezcla de las notas mismas.'
    )
    vvo = vcol['saved_attribute_attributes']['valueof']
    vvo['parameter_longname'] = 'VwColor'
    vvo['parameter_shortname'] = 'VwColor'
    vvo['parameter_initial'] = [0]
    win_boxes.append({'box': vcol})

    # --- 2. the "Col" label, right after the "3D" label (which ends at x=324) --------
    lb_3d = find_box(win_boxes, 'tzw_lb304_8')
    lb_col = copy.deepcopy(lb_3d)
    lb_col['id'] = 'obj-l346_8'
    lb_col['varname'] = 'tzw_lb346_8'
    lb_col['text'] = 'Col'
    lb_col['patching_rect'] = [346.0, 8.0, 24.0, 15.0]
    lb_col['patching_position'] = [346.0, 8.0]
    lb_col['presentation_rect'] = [346.0, 8.0, 24.0, 15.0]
    lb_col['presentation_position'] = [346.0, 8.0]
    win_boxes.append({'box': lb_col})

    # --- 3. clone tzw_pp_vtet -> tzw_pp_vcol (hidden "prepend vcol") -----------------
    pp_vtet = find_box(win_boxes, 'tzw_pp_vtet')
    pp_vcol = copy.deepcopy(pp_vtet)
    pp_vcol['id'] = 'obj-216p'
    pp_vcol['varname'] = 'tzw_pp_vcol'
    pp_vcol['text'] = 'prepend vcol'
    pp_vcol['patching_rect'] = [16.0, 1674.0, 130.0, 22.0]
    pp_vcol['patching_position'] = [16.0, 1674.0]
    win_boxes.append({'box': pp_vcol})

    # --- 4. this device gives every toggle its OWN outputvalue box -------------------
    ov1 = find_box(win_boxes, 'tzw_ov1')
    ov_new = copy.deepcopy(ov1)
    ov_new['id'] = 'obj-ov23'
    ov_new['varname'] = 'tzw_ov24'
    ov_new['patching_rect'] = [300.0, 1674.0, 74.0, 22.0]
    ov_new['patching_position'] = [300.0, 1674.0]
    win_boxes.append({'box': ov_new})

    # --- 5. wiring: tzw_init -> tzw_ov24 -> tzw_vcol -> tzw_pp_vcol -> tzw_ui --------
    win['lines'].append({'patchline': {'source': ['obj-199', 0], 'destination': ['obj-ov23', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-ov23', 0], 'destination': ['obj-216', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-216', 0], 'destination': ['obj-216p', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-216p', 0], 'destination': ['obj-100', 0]}})

    # --- 6. registry 2 (local to tz_window) + registry 4 (top-level, composite key) --
    assert win_params['obj-215'] == ['HarmMode', 'HarmMode', 52], win_params['obj-215']
    win_params['obj-216'] = ['VwColor', 'VwColor', 53]

    top_params = root['parameters']
    assert top_params['obj-10::obj-215'] == ['HarmMode', 'HarmMode', 53], top_params['obj-10::obj-215']
    top_params['obj-10::obj-216'] = ['VwColor', 'VwColor', 54]

    # --- 7. parameterbanks bank 5 ("Mas") has 1 free "-" slot left after HarmMode ----
    bank5 = top_params['parameterbanks']['5']
    assert bank5['name'] == 'Mas', bank5['name']
    assert 'HarmMode' in bank5['parameters'], bank5['parameters']
    idx = bank5['parameters'].index('-')
    bank5['parameters'][idx] = 'VwColor'

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # --- verify by reading the file back ---------------------------------------------
    _, _, _, doc2 = amxd.load(PATH)
    win2 = find_box(doc2['patcher']['boxes'], 'tz_window')['patcher']
    vc2 = find_box(win2['boxes'], 'tzw_vcol')
    vo2 = vc2['saved_attribute_attributes']['valueof']
    assert vo2['parameter_longname'] == 'VwColor'
    assert vo2['parameter_initial'] == [0]
    local_orders = sorted(v[2] for k, v in win2['parameters'].items() if k != 'inherited_shortname')
    assert local_orders == list(range(54)), local_orders
    top2 = doc2['patcher']['parameters']
    top_orders = sorted(v[2] for k, v in top2.items()
                         if k not in ('parameterbanks', 'inherited_shortname', 'parameter_overrides'))
    assert top_orders == list(range(55)), top_orders
    assert 'VwColor' in top2['parameterbanks']['5']['parameters']
    print('OK: toggle, wiring targets, and both order registries verified.')


if __name__ == '__main__':
    main()
