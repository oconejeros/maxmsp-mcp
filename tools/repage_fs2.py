"""Phase C: re-page FORTESEQ2 from 10 tabs to 8.

    python tools/repage_fs2.py            dry run
    python tools/repage_fs2.py --apply    write FORTESEQ2.amxd + fs2pages.maxpat (+ .before)

New Pagina order (150 px per band):
    0 Armonia  1 Filtro  2 Artic  3 Musical  4 Tiempo  5 Ritmo  6 Modul  7 Sesion

- **Modul** moves band 8 -> band 6  (every presentation_rect on that band, y -= 300).
- **Sesion** (band 7) is the merge of the old Camino (band 6) + Escuchar (band 7) +
  Presets (band 9), re-laid onto three rows. The three long help-note comments are hidden
  from the Live view (presentation flag removed) but kept in the patch.

.amxd side:
- Pagina live.tab (obj-485) enum -> 8 items, parameter_mmax 9 -> 7.
- obj-486 `sel 0..9` -> `sel 0..7` (11 -> 9 outlets); drop the outlet-8/9 wires and the two
  now-orphan `script sendbox ... offset 0 -1200 / -1350` message boxes (obj-514/obj-515).
- obj-506/507/508 (`-750 / -900 / -1050`) already map Ritmo / Modul / Sesion on sel
  outlets 5/6/7, so no rewiring of the offsets.

Push banks are untouched (they name params by longname; bank NAMES like "32 Camino" are
cosmetic). Idempotent (bails if the Pagina enum already contains "Sesion").
Close in Max AND Live before --apply.
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

NEW_ENUM = ['Armonia', 'Filtro', 'Artic', 'Musical', 'Tiempo', 'Ritmo', 'Modul', 'Sesion']

MODUL_BAND = (1195.0, 1345.0)      # old band 8 -> shift by -300 to land on band 6
MODUL_DY = -300.0

# Sesion band 7 (y 1050..1192): explicit target y per box (x is kept)
SESSION_Y = {
    # --- Camino (was band 6) : row 1 ---
    'obj-269': 1052, 'obj-272': 1052, 'obj-275': 1052, 'obj-278': 1052, 'obj-369': 1052,
    'obj-270': 1066, 'obj-273': 1066, 'obj-276': 1066, 'obj-279': 1066, 'obj-370': 1066,
    # --- Escuchar (was band 7) : row 2 ---
    'obj-283': 1088, 'obj-286': 1088, 'obj-289': 1088,
    'obj-284': 1102, 'obj-287': 1102, 'obj-290': 1102, 'obj-292': 1102,
    # --- Presets (was band 9) : rows 3-5 ---
    'obj-348': 1120,
    'obj-349': 1134, 'obj-351': 1134, 'obj-354': 1134, 'obj-357': 1134,
    'obj-360': 1154, 'obj-361': 1154,
    'obj-378': 1172, 'obj-379': 1172,
}
NOTE_HIDE = ['obj-281', 'obj-295', 'obj-364']    # cm_nota / es_nota / pr_nota


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
    if 'Sesion' in vo['parameter_enum']:
        return None
    vo['parameter_enum'] = list(NEW_ENUM)
    vo['parameter_mmax'] = len(NEW_ENUM) - 1

    sel = by['obj-486']
    sel['text'] = 'sel ' + ' '.join(str(i) for i in range(len(NEW_ENUM)))
    sel['numoutlets'] = len(NEW_ENUM) + 1        # matches + passthrough
    if isinstance(sel.get('outlettype'), list):
        sel['outlettype'] = [''] * (len(NEW_ENUM) + 1)

    drop_boxes = {'obj-514', 'obj-515'}
    P['lines'] = [ln for ln in P['lines']
                  if ln['patchline']['source'][0] not in drop_boxes
                  and ln['patchline']['destination'][0] not in drop_boxes]
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in drop_boxes]
    return True


def patch_pages(pg):
    by = {b['box']['id']: b['box'] for b in pg['boxes']}
    moved_modul = 0
    for b in pg['boxes']:
        pr = b['box'].get('presentation_rect')
        if pr and MODUL_BAND[0] <= pr[1] < MODUL_BAND[1]:
            pr[1] += MODUL_DY
            moved_modul += 1
    for bid, y in SESSION_Y.items():
        assert bid in by, 'missing %s' % bid
        by[bid]['presentation_rect'][1] = float(y)
    for bid in NOTE_HIDE:
        b = by[bid]
        b.pop('presentation', None)
        b.pop('presentation_rect', None)
    return moved_modul


def overlaps(pg):
    """report presentation overlaps within the two rebuilt bands (skip comments)."""
    hits = []
    band6 = (900.0, 1046.0)
    band7 = (1050.0, 1194.0)
    rects = [(b['box']['id'], b['box'].get('maxclass'), b['box']['presentation_rect'])
             for b in pg['boxes'] if b['box'].get('presentation_rect')]
    for lo, hi in (band6, band7):
        R = [(i, r) for i, mc, r in rects if lo <= r[1] < hi and mc != 'comment']
        for a in range(len(R)):
            for b2 in range(a + 1, len(R)):
                (ia, ra), (ib, rb) = R[a], R[b2]
                if (ra[0] < rb[0] + rb[2] and rb[0] < ra[0] + ra[2] and
                        ra[1] < rb[1] + rb[3] and rb[1] < ra[1] + ra[3]):
                    hits.append('%s %s  vs  %s %s' % (ia, ra, ib, rb))
    return hits


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(AMXD)
    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']

    res = patch_amxd(doc)
    if res is None:
        print('already re-paged (Pagina enum has "Sesion") -- nothing to do'); return
    moved = patch_pages(pg)
    check(doc['patcher'], 'amxd')
    check(pg, 'fs2pages')

    print('repage_fs2')
    print('  Pagina: 10 -> 8 tabs  %s' % NEW_ENUM)
    print('  sel 0..7 (9 outlets); dropped obj-514/obj-515 + their lines')
    print('  fs2pages: Modul band shifted -300 (%d boxes); %d boxes re-placed on Sesion;'
          ' hid notes %s' % (moved, len(SESSION_Y), NOTE_HIDE))
    hits = overlaps(pg)
    for h in hits:
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
    assert not any(b['box']['id'] in ('obj-514', 'obj-515') for b in back['boxes'])
    bp = {b['box']['id']: b['box'] for b in json.load(open(PAGES, encoding='utf-8'))['patcher']['boxes']}
    assert bp['obj-303']['presentation_rect'][1] == 920.0, bp['obj-303']['presentation_rect']
    assert 'presentation_rect' not in bp['obj-281']
    print('\nwrote both files (+ .before). now: check_structure + check_params3 + harness --check')


if __name__ == '__main__':
    main()
