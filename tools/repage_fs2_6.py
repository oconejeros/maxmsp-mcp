"""Phase F: FORTESEQ2 Pagina 8 -> 6 tabs.

    python tools/repage_fs2_6.py            dry run
    python tools/repage_fs2_6.py --apply    write FORTESEQ2.amxd + fs2pages.maxpat (+ .before)

New order (150 px per band):
    0 Armonia  1 Filtro  2 Artic  3 Tiempo  4 Modul  5 Sesion

- **Musical is dissolved.** Its 21 boxes redistribute:
    Voicing / Conduccion / Sec Raiz / Rotacion  -> Armonia  (harmony shaping)
    Drum / Pad / Ritmo Arm                       -> Tiempo   (rhythmic output)
    Fav / Solo Fav / apilar / unisono / limpiar  -> Sesion   (next to Presets / favourites)
- **Ritmo + Modul share one page ("Modul", band 4).** Ritmo is compacted 4 rows -> 2
  (V1|V2 then V3|V4, each voice's Larg/Puls/Gir in line); Modul's four rows sit below it.
  The two help-note comments (rt_nota obj-267, md_nota obj-346) are hidden (kept in patch).
- Tiempo shifts band 4->3, Sesion shifts band 7->5 (whole-band presentation_rect deltas).

.amxd: obj-485 enum -> 6, parameter_mmax 5; obj-486 `sel 0..5` (7 outlets); drop
sel-outlet 6/7 wires and the orphan `offset 0 -900 / -1050` messages (obj-507/obj-508).
Push banks untouched (name params by longname). Assumes the 8-tab state from repage_fs2.py.
Idempotent (bails if the Pagina enum no longer contains "Musical").
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMXD = os.path.join(ROOT, 'forteseq', 'FORTESEQ2.amxd')
PAGES = os.path.join(ROOT, 'forteseq', 'fs2pages.maxpat')

NEW_ENUM = ['Armonia', 'Filtro', 'Artic', 'Tiempo', 'Modul', 'Sesion']

# whole-band presentation_rect.y shifts  (y_lo, y_hi, dy)
BAND_SHIFT = [
    (598.0, 720.0, -150.0),     # Tiempo  band 4 -> 3
    (1050.0, 1196.0, -300.0),   # Sesion  band 7 -> 5
]

# explicit new presentation_rect [x, y, w, h] for every relocated / re-laid box
EXPLICIT = {
    # --- Musical -> Armonia (band 0), on the y=19 row, right of "Orden" ---
    'obj-140': [220.0, 3.0, 40.0, 12.0], 'obj-139': [220.0, 19.0, 90.0, 18.0],   # Voicing
    'obj-149': [316.0, 3.0, 40.0, 12.0], 'obj-150': [318.0, 19.0, 15.0, 15.0],   # Conduccion
    'obj-142': [340.0, 3.0, 50.0, 12.0], 'obj-143': [340.0, 19.0, 90.0, 18.0],   # Sec Raiz
    'obj-382': [436.0, 3.0, 50.0, 12.0], 'obj-383': [436.0, 19.0, 38.0, 15.0],   # Rotacion

    # --- Musical -> Tiempo (band 3 after shift, y 450..592), on the y=491 row ---
    'obj-141': [220.0, 473.0, 30.0, 12.0], 'obj-144': [220.0, 491.0, 15.0, 15.0],  # Drum
    'obj-145': [250.0, 473.0, 26.0, 12.0], 'obj-146': [250.0, 491.0, 38.0, 15.0],  # Pad
    'obj-147': [296.0, 473.0, 40.0, 12.0], 'obj-148': [296.0, 491.0, 38.0, 15.0],  # Ritmo Arm

    # --- Musical -> Sesion (band 5 after shift, y 750..890) ---
    'obj-155': [360.0, 786.0, 26.0, 12.0], 'obj-156': [360.0, 802.0, 15.0, 15.0],  # Fav
    'obj-160': [395.0, 786.0, 30.0, 12.0], 'obj-161': [395.0, 802.0, 15.0, 15.0],  # Solo Fav
    'obj-165': [430.0, 802.0, 60.0, 16.0],                                          # limpiar
    'obj-152': [270.0, 834.0, 58.0, 16.0],                                          # apilar
    'obj-164': [332.0, 834.0, 60.0, 16.0],                                          # unisono

    # --- Ritmo compacted to 2 rows, band 4 (y 600..742) ---
    'obj-236': [30.0, 596.0, 26.0, 10.0], 'obj-237': [62.0, 596.0, 26.0, 10.0],
    'obj-238': [94.0, 596.0, 26.0, 10.0],
    'obj-239': [10.0, 608.0, 18.0, 12.0], 'obj-246': [124.0, 608.0, 18.0, 12.0],
    'obj-253': [10.0, 628.0, 18.0, 12.0], 'obj-260': [124.0, 628.0, 18.0, 12.0],
    'obj-240': [30.0, 608.0, 28.0, 15.0], 'obj-242': [62.0, 608.0, 28.0, 15.0], 'obj-244': [94.0, 608.0, 28.0, 15.0],
    'obj-247': [144.0, 608.0, 28.0, 15.0], 'obj-249': [176.0, 608.0, 28.0, 15.0], 'obj-251': [208.0, 608.0, 28.0, 15.0],
    'obj-254': [30.0, 628.0, 28.0, 15.0], 'obj-256': [62.0, 628.0, 28.0, 15.0], 'obj-258': [94.0, 628.0, 28.0, 15.0],
    'obj-261': [144.0, 628.0, 28.0, 15.0], 'obj-263': [176.0, 628.0, 28.0, 15.0], 'obj-265': [208.0, 628.0, 28.0, 15.0],

    # --- Modul rows below Ritmo, band 4 ---
    'obj-297': [24.0, 642.0, 60.0, 12.0], 'obj-298': [100.0, 642.0, 40.0, 12.0],
    'obj-299': [146.0, 642.0, 40.0, 12.0], 'obj-300': [196.0, 642.0, 40.0, 12.0],
    'obj-301': [242.0, 642.0, 80.0, 12.0],
    'obj-302': [0.0, 651.0, 22.0, 12.0], 'obj-303': [24.0, 650.0, 72.0, 18.0],
    'obj-305': [100.0, 652.0, 42.0, 15.0], 'obj-307': [146.0, 652.0, 46.0, 15.0],
    'obj-309': [196.0, 652.0, 42.0, 15.0], 'obj-311': [242.0, 650.0, 80.0, 18.0],
    'obj-313': [0.0, 674.0, 22.0, 12.0], 'obj-314': [24.0, 673.0, 72.0, 18.0],
    'obj-316': [100.0, 675.0, 42.0, 15.0], 'obj-318': [146.0, 675.0, 46.0, 15.0],
    'obj-320': [196.0, 675.0, 42.0, 15.0], 'obj-322': [242.0, 673.0, 80.0, 18.0],
    'obj-324': [0.0, 697.0, 22.0, 12.0], 'obj-325': [24.0, 696.0, 72.0, 18.0],
    'obj-327': [100.0, 698.0, 42.0, 15.0], 'obj-329': [146.0, 698.0, 46.0, 15.0],
    'obj-331': [196.0, 698.0, 42.0, 15.0], 'obj-333': [242.0, 696.0, 80.0, 18.0],
    'obj-335': [0.0, 720.0, 22.0, 12.0], 'obj-336': [24.0, 719.0, 72.0, 18.0],
    'obj-338': [100.0, 721.0, 42.0, 15.0], 'obj-340': [146.0, 721.0, 46.0, 15.0],
    'obj-342': [196.0, 721.0, 42.0, 15.0], 'obj-344': [242.0, 719.0, 80.0, 18.0],
}
HIDE = ['obj-267', 'obj-346']       # rt_nota / md_nota


def check(P, where='root'):
    by = {}
    for e in P.get('boxes', []):
        b = e['box']
        assert b['id'] not in by, '%s dup id %s' % (where, b['id'])
        by[b['id']] = b
    for ln in P.get('lines', []):
        pl = ln['patchline']
        for tag, end in (('s', pl['source']), ('d', pl['destination'])):
            b = by.get(end[0])
            assert b, '%s %s dangling -> %s' % (where, tag, end)
            m = b.get('numoutlets', 0) if tag == 's' else b.get('numinlets', 0)
            assert 0 <= end[1] < m, '%s %s %s idx %d /%d (%s)' % (
                where, tag, end[0], end[1], m, b.get('text', b.get('maxclass')))
    for e in P.get('boxes', []):
        if e['box'].get('patcher'):
            check(e['box']['patcher'], where + '::' + e['box']['id'])


def patch_amxd(doc):
    P = doc['patcher']
    by = {b['box']['id']: b['box'] for b in P['boxes']}
    vo = by['obj-485']['saved_attribute_attributes']['valueof']
    if 'Musical' not in vo['parameter_enum']:
        return None
    vo['parameter_enum'] = list(NEW_ENUM)
    vo['parameter_mmax'] = len(NEW_ENUM) - 1
    sel = by['obj-486']
    sel['text'] = 'sel ' + ' '.join(str(i) for i in range(len(NEW_ENUM)))
    sel['numoutlets'] = len(NEW_ENUM) + 1
    if isinstance(sel.get('outlettype'), list):
        sel['outlettype'] = [''] * (len(NEW_ENUM) + 1)
    drop = {'obj-507', 'obj-508'}
    P['lines'] = [ln for ln in P['lines']
                  if ln['patchline']['source'][0] not in drop
                  and ln['patchline']['destination'][0] not in drop]
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in drop]
    return True


def patch_pages(pg):
    by = {b['box']['id']: b['box'] for b in pg['boxes']}
    shifted = 0
    for b in pg['boxes']:
        pr = b['box'].get('presentation_rect')
        if not pr or b['box']['id'] in EXPLICIT:
            continue
        for lo, hi, dy in BAND_SHIFT:
            if lo <= pr[1] < hi:
                pr[1] += dy
                shifted += 1
                break
    for bid, rect in EXPLICIT.items():
        assert bid in by, 'missing %s' % bid
        by[bid]['presentation_rect'] = list(rect)
    for bid in HIDE:
        by[bid].pop('presentation', None)
        by[bid].pop('presentation_rect', None)
    return shifted


def overlaps(pg):
    hits = []
    bands = [(0.0, 142.0), (450.0, 592.0), (600.0, 742.0), (750.0, 892.0)]
    rects = [(b['box']['id'], b['box'].get('maxclass'), b['box'].get('presentation_rect'))
             for b in pg['boxes'] if b['box'].get('presentation_rect')]
    for lo, hi in bands:
        R = [(i, r) for i, mc, r in rects if lo <= r[1] < hi and mc != 'comment']
        for a in range(len(R)):
            for c in range(a + 1, len(R)):
                (ia, ra), (ic, rc) = R[a], R[c]
                if (ra[0] < rc[0] + rc[2] and rc[0] < ra[0] + ra[2] and
                        ra[1] < rc[1] + rc[3] and rc[1] < ra[1] + ra[3]):
                    hits.append('%s %s  vs  %s %s' % (ia, ra, ic, rc))
    return hits


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(AMXD)
    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']

    if patch_amxd(doc) is None:
        print('already 6-tab (no "Musical" in Pagina enum) -- nothing to do'); return
    shifted = patch_pages(pg)
    check(doc['patcher'], 'amxd')
    check(pg, 'fs2pages')

    print('repage_fs2_6')
    print('  Pagina: 8 -> 6 tabs  %s' % NEW_ENUM)
    print('  sel 0..5 (7 outlets); dropped obj-507/obj-508 + their lines')
    print('  fs2pages: %d boxes band-shifted; %d boxes re-placed explicitly; hid %s'
          % (shifted, len(EXPLICIT), HIDE))
    for h in overlaps(pg):
        print('  !! overlap ' + h)

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(AMXD, AMXD + '.before')
    shutil.copyfile(PAGES, PAGES + '.before')
    amxd.save(AMXD, data, s, e, doc)
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    back = amxd.load(AMXD)[3]['patcher']
    bt = next(b['box'] for b in back['boxes'] if b['box']['id'] == 'obj-485')
    assert bt['saved_attribute_attributes']['valueof']['parameter_enum'] == NEW_ENUM
    assert not any(b['box']['id'] in ('obj-507', 'obj-508') for b in back['boxes'])
    bp = {b['box']['id']: b['box'] for b in json.load(open(PAGES, encoding='utf-8'))['patcher']['boxes']}
    assert bp['obj-204']['presentation_rect'][1] == 469.0, bp['obj-204']['presentation_rect']
    assert bp['obj-303']['presentation_rect'][1] == 650.0
    assert 'presentation_rect' not in bp['obj-267']
    print('\nwrote both files (+ .before). now: check_structure + check_params3 + harness --check')


if __name__ == '__main__':
    main()
