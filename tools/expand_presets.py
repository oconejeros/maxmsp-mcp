"""Grow the Presets page from 8 to 20 slots, and add the readout that actually identifies a
slot: its name. `sendPresetName()`/`__name` already exist on the engine side (forteseq2.js,
checkPresetNames() in the harness) -- this is the other half, the UI that shows it.

    python tools/expand_presets.py            dry run, writes nothing
    python tools/expand_presets.py --apply    do it

The "Llenos" dash-list stays where it is (its column is boxed in by pr_nota's text block on the
right, confirmed by reading both boxes' rects -- there is no room to widen it without either
moving pr_nota or risking an overlap this script cannot verify visually), just at a smaller font
so 20 dashes fit instead of 8. The real identification path is the new Nombre readout below the
Slot/Guardar row, in a column confirmed empty from y=65 to the page bottom.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

# fs2pages.maxpat is a file bpatcher: parameter_mmax and the two new comments below are entirely
# its own concern (registry #1, the box's own saved_attribute_attributes) -- FORTESEQ2.amxd's
# nested obj-484::* copy only holds name/order (registry #2), untouched here since neither
# changes. No need to open the parent device at all for this one.
MERGED = os.path.join('forteseq', 'fs2pages.maxpat')
PAGE = 9
PITCH = 150.0
PY0 = PAGE * PITCH

NAME_ANN = ('El nombre del slot que Slot esta apuntando ahora mismo, si tiene uno. Los presets '
            'de fabrica (Azar Presets, mas abajo) ya vienen con nombre; guardar uno propio no '
            'pone nombre salvo que el slot ya tuviera uno de antes, que se conserva.')


def main():
    apply_it = '--apply' in sys.argv
    pg = json.load(open(MERGED, encoding='utf-8'))['patcher']
    pb = {b['box']['id']: b['box'] for b in pg['boxes']}
    byvar = {b.get('varname'): i for i, b in pb.items() if b.get('varname')}

    slot = pb[byvar['pr_slot']]
    va = slot['saved_attribute_attributes']['valueof']
    assert va['parameter_mmax'] == 8.0, 'ya esta corrido a %s' % va['parameter_mmax']
    va['parameter_mmax'] = 20.0

    lst = pb[byvar['pr_list']]
    lst['fontsize'] = 7.0

    ann_slot = slot.get('annotation', '')
    assert 'ocho' in ann_slot
    slot['annotation'] = ann_slot.replace('ocho', 'veinte')
    nota = pb[byvar['pr_nota']]
    assert 'ocho' in nota['text']
    nota['text'] = nota['text'].replace('ocho', 'veinte')

    # ---- the name readout, in the confirmed-empty column below Slot/Guardar -------------------
    assert 'pr_name' not in byvar, 'ya esta puesto'
    echo_src = None
    pr_echo_id = byvar['pr_echo']
    for l in pg['lines']:
        pl = l['patchline']
        if pl['destination'][0] == pr_echo_id:
            echo_src = pl['source'][0]
            break
    assert echo_src, 'no encontre que alimenta pr_echo'

    nxt = [max(int(i.split('-')[1]) for i in pb)]

    def fresh():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    add, wire = [], []

    def box(**kw):
        b = dict(kw)
        b.setdefault('id', fresh())
        add.append({'box': b})
        return b['id']

    def link(a, c, ao=0, ci=0):
        wire.append({'patchline': {'source': [a, ao], 'destination': [c, ci]}})

    y0 = 70.0   # confirmed empty: pr_nota starts at x=264, this column (x<258) is free from y=65
    lbl = box(maxclass='comment', numinlets=1, numoutlets=0, text='Nombre',
             varname='pr_name_lbl', presentation=1, presentation_rect=[0.0, PY0 + y0, 54.0, 18.0],
             patching_rect=[20.0, 6900.0, 54.0, 18.0])
    disp = box(maxclass='comment', numinlets=1, numoutlets=0, text='-', varname='pr_name',
              annotation=NAME_ANN, presentation=1,
              presentation_rect=[56.0, PY0 + y0, 200.0, 18.0],
              patching_rect=[120.0, 6930.0, 200.0, 18.0])
    rt = box(maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
             varname='pr_name_echo', text='route presetname',
             patching_rect=[120.0, 6960.0, 120.0, 22.0])
    st = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''], text='prepend set',
             patching_rect=[120.0, 6990.0, 90.0, 22.0])
    link(echo_src, rt)
    link(rt, st)
    link(st, disp)

    pg['boxes'].extend(add)
    pg['lines'].extend(wire)

    R = [b['box']['presentation_rect'] for b in pg['boxes']
         if b['box'].get('presentation') and b['box'].get('presentation_rect')
         and PY0 <= b['box']['presentation_rect'][1] < PY0 + PITCH]
    w = max(r[0] + r[2] for r in R)
    h = max(r[1] + r[3] - PY0 for r in R)
    bad = [(a, b) for a in R for b in R if a is not b
           and a[0] < b[0] + b[2] and b[0] < a[0] + a[2]
           and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]]
    assert not bad, bad
    print('pagina Presets: %.0f x %.0f px (limite 516 x 142), sin solapamientos' % (w, h))
    assert w <= 516.0 and h <= 142.0, (w, h)

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    with open(MERGED, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    print('escrito %s' % MERGED)


main()
