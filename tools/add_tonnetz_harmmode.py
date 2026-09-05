"""One-off: add a HarmMode toggle to tonnetz.amxd, next to AnWin/Reset.

HarmMode (tonnetz.js, see forteseq_project_state / this session's work) paints every
sounding pitch class the SAME colour -- the AnWin-windowed McKay dissonance band
(disoBand(), the same one already driving the "diso NN%" meter) -- instead of each pc's
own hue. It's a pure read of state tonnetz.js already computes; this script only adds the
Live-facing control.

Wired exactly like Colors (tzw_colors): own dedicated `outputvalue` message box (this
device gives every toggle its own, unlike ANIMIDI's shared one) driven by the same
loadbang (obj-199 / tzw_init) that already fans out to every other control, so it inits
without inverting on a raw bang -- toggle -> prepend harmmode -> the jsui (obj-100).

Touches all four registries (see amxd-parameter-registries note):
  1. the new box's own saved_attribute_attributes.valueof                  (local)
  2. the tz_window subpatcher's own `parameters` dict                     (local, obj-215)
  3. the top-level tonnetz.amxd `parameters` dict, composite obj-10::obj-215 key
  4. `parameterbanks` bank 5 ("Mas"), which already carries AnWin/Reset and has 2 free "-" slots

Run with the device closed in both Max and Live. Takes a .before backup first.
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

    # --- 1. clone tzw_colors -> tzw_harmmode (live.toggle), placed after Reset --------
    colors = find_box(win_boxes, 'tzw_colors')
    harmmode = copy.deepcopy(colors)
    harmmode['id'] = 'obj-215'
    harmmode['varname'] = 'tzw_harmmode'
    harmmode['patching_rect'] = [888.0, 68.0, 15.0, 15.0]
    harmmode['patching_position'] = [888.0, 68.0]
    harmmode['presentation_rect'] = [888.0, 68.0, 15.0, 15.0]
    harmmode['presentation_position'] = [888.0, 68.0]
    harmmode['annotation'] = (
        'Modo armonia: pinta TODAS las notas sonando del mismo color -- la banda de '
        'disonancia McKay ya usada por el medidor "diso NN%" (ventana AnWin) -- en vez '
        'de la rueda por clase de altura. Lectura de "que tan consonante es esto" en vez '
        'de "que nota es esta", en todos los paneles a la vez.'
    )
    hvo = harmmode['saved_attribute_attributes']['valueof']
    hvo['parameter_longname'] = 'HarmMode'
    hvo['parameter_shortname'] = 'HarmMode'
    hvo['parameter_initial'] = [0]   # default off -- don't change the calibrated default look
    win_boxes.append({'box': harmmode})

    # --- 2. the "arm" label, right after Reset (which ends at x=856) -----------------
    lb_color = find_box(win_boxes, 'tzw_lb376_68')
    lb_harmmode = copy.deepcopy(lb_color)
    lb_harmmode['id'] = 'obj-l862_69'
    lb_harmmode['varname'] = 'tzw_lb862_69'
    lb_harmmode['text'] = 'arm'
    lb_harmmode['patching_rect'] = [862.0, 69.0, 24.0, 15.0]
    lb_harmmode['patching_position'] = [862.0, 69.0]
    lb_harmmode['presentation_rect'] = [862.0, 69.0, 24.0, 15.0]
    lb_harmmode['presentation_position'] = [862.0, 69.0]
    win_boxes.append({'box': lb_harmmode})

    # --- 3. clone tzw_pp_colors -> tzw_pp_harmmode (hidden "prepend harmmode") --------
    pp_colors = find_box(win_boxes, 'tzw_pp_colors')
    pp_harmmode = copy.deepcopy(pp_colors)
    pp_harmmode['id'] = 'obj-215p'
    pp_harmmode['varname'] = 'tzw_pp_harmmode'
    pp_harmmode['text'] = 'prepend harmmode'
    pp_harmmode['patching_rect'] = [16.0, 1650.0, 130.0, 22.0]
    pp_harmmode['patching_position'] = [16.0, 1650.0]
    win_boxes.append({'box': pp_harmmode})

    # --- 4. this device gives every toggle its OWN outputvalue box (unlike ANIMIDI) --
    ov1 = find_box(win_boxes, 'tzw_ov1')
    ov_new = copy.deepcopy(ov1)
    ov_new['id'] = 'obj-ov22'
    ov_new['varname'] = 'tzw_ov23'
    ov_new['patching_rect'] = [200.0, 1650.0, 74.0, 22.0]
    ov_new['patching_position'] = [200.0, 1650.0]
    win_boxes.append({'box': ov_new})

    # --- 5. wiring: tzw_init -> tzw_ov23 -> tzw_harmmode -> tzw_pp_harmmode -> tzw_ui -
    win['lines'].append({'patchline': {'source': ['obj-199', 0], 'destination': ['obj-ov22', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-ov22', 0], 'destination': ['obj-215', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-215', 0], 'destination': ['obj-215p', 0]}})
    win['lines'].append({'patchline': {'source': ['obj-215p', 0], 'destination': ['obj-100', 0]}})

    # --- 6. registry 2 (local to tz_window) + registry 4 (top-level, composite key) --
    assert win_params['obj-308'] == ['StudyMove', 'StudyMove', 51], win_params['obj-308']
    win_params['obj-215'] = ['HarmMode', 'HarmMode', 52]

    top_params = root['parameters']
    assert top_params['obj-10::obj-308'] == ['StudyMove', 'StudyMove', 52], top_params['obj-10::obj-308']
    top_params['obj-10::obj-215'] = ['HarmMode', 'HarmMode', 53]

    # --- 7. parameterbanks bank 5 ("Mas") already has AnWin/Reset + 2 free "-" slots -
    bank5 = top_params['parameterbanks']['5']
    assert bank5['name'] == 'Mas', bank5['name']
    assert 'AnWin' in bank5['parameters'] and 'Reset' in bank5['parameters'], bank5['parameters']
    idx = bank5['parameters'].index('-')
    bank5['parameters'][idx] = 'HarmMode'

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # --- verify by reading the file back ---------------------------------------------
    _, _, _, doc2 = amxd.load(PATH)
    win2 = find_box(doc2['patcher']['boxes'], 'tz_window')['patcher']
    hm2 = find_box(win2['boxes'], 'tzw_harmmode')
    vo2 = hm2['saved_attribute_attributes']['valueof']
    assert vo2['parameter_longname'] == 'HarmMode'
    assert vo2['parameter_initial'] == [0]
    local_orders = sorted(v[2] for k, v in win2['parameters'].items() if k != 'inherited_shortname')
    assert local_orders == list(range(53)), local_orders
    top2 = doc2['patcher']['parameters']
    top_orders = sorted(v[2] for k, v in top2.items()
                         if k not in ('parameterbanks', 'inherited_shortname', 'parameter_overrides'))
    assert top_orders == list(range(54)), top_orders
    assert 'HarmMode' in top2['parameterbanks']['5']['parameters']
    print('OK: toggle, wiring targets, and both order registries verified.')


if __name__ == '__main__':
    main()
