"""Phase B: put everything that feeds the set-filter on ONE page.

    python tools/consolidate_filter.py            dry run
    python tools/consolidate_filter.py --apply    write fs2pages.maxpat + FORTESEQ2.amxd (+ .before)

The "Teoria" page currently only holds the Mask row. `n min` / `n max` (cardinality window,
-> setcardmin/setcardmax) live on Armonia; the IC vector min/max bank (-> setvecmin/setvecmax
1..6) lives on Musical. All three -- mask, cardinality, IC vector -- are `requestFilter()`
inputs, so they belong together. This renames the page **"Filtro"** and moves the cardinality
+ IC-vector controls onto its band (internal presentation y 150..292).

Nothing but `presentation_rect` moves in fs2pages.maxpat (patching-view wiring, the
`prepend set…` helpers and every registry entry are untouched -- a control shows on page N
purely because its presentation_rect.y is in [150N, 150N+142]). The only .amxd edit is the
`Pagina` live.tab enum string "Teoria" -> "Filtro".

Leaves gaps on Armonia (n min/n max) and Musical (IC bank) -- closed by the Phase C reflow.
Idempotent (bails if the Pagina enum already says "Filtro"). Close in Max AND Live first.
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
PAGINA = 'obj-485'      # the Pagina live.tab in FORTESEQ2.amxd

# box id -> new presentation_rect  (band 1 = "Filtro", internal y 150..292)
MOVES = {
    'obj-31':  [14.0, 170.0, 34.0, 12.0],   # "n min" label
    'obj-32':  [14.0, 184.0, 34.0, 15.0],   # n min  -> setcardmin
    'obj-35':  [52.0, 170.0, 34.0, 12.0],   # "n max" label
    'obj-36':  [52.0, 184.0, 34.0, 15.0],   # n max  -> setcardmax
    'obj-151': [92.0, 170.0, 90.0, 12.0],   # "Vector min" label
    'obj-157': [92.0, 184.0, 26.0, 15.0],   # IC1 Min
    'obj-159': [120.0, 184.0, 26.0, 15.0],  # IC2 Min
    'obj-163': [148.0, 184.0, 26.0, 15.0],  # IC3 Min
    'obj-167': [176.0, 184.0, 26.0, 15.0],  # IC4 Min
    'obj-169': [204.0, 184.0, 26.0, 15.0],  # IC5 Min
    'obj-170': [232.0, 184.0, 26.0, 15.0],  # IC6 Min
    'obj-154': [92.0, 202.0, 90.0, 12.0],   # "Vector max" label
    'obj-153': [92.0, 216.0, 26.0, 15.0],   # IC1 Max
    'obj-158': [120.0, 216.0, 26.0, 15.0],  # IC2 Max
    'obj-162': [148.0, 216.0, 26.0, 15.0],  # IC3 Max
    'obj-166': [176.0, 216.0, 26.0, 15.0],  # IC4 Max
    'obj-168': [204.0, 216.0, 26.0, 15.0],  # IC5 Max
    'obj-171': [232.0, 216.0, 26.0, 15.0],  # IC6 Max
}


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(AMXD)
    P = doc['patcher']
    tabbox = next(b['box'] for b in P['boxes'] if b['box']['id'] == PAGINA)
    enum = tabbox['saved_attribute_attributes']['valueof']['parameter_enum']
    if 'Filtro' in enum and 'Teoria' not in enum:
        print('already consolidated (Pagina enum has "Filtro") -- nothing to do'); return
    ti = enum.index('Teoria')

    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
    by = {b['box']['id']: b['box'] for b in pg['boxes']}
    missing = [k for k in MOVES if k not in by]
    assert not missing, 'boxes not found in fs2pages: %s' % missing

    print('consolidate_filter')
    print('  FORTESEQ2.amxd : Pagina enum[%d] "Teoria" -> "Filtro"' % ti)
    print('  fs2pages.maxpat: %d presentation_rect moves onto band 1 (y 150..292)' % len(MOVES))
    for k, r in MOVES.items():
        vo = (by[k].get('saved_attribute_attributes') or {}).get('valueof', {})
        name = vo.get('parameter_longname') or repr(by[k].get('text', ''))
        print('     %-8s %-12s %s -> %s' % (k, name, by[k].get('presentation_rect'), r))

    # overlap sanity within band 1
    rects = [(k, MOVES[k]) for k in MOVES] + \
            [(b['box']['id'], b['box']['presentation_rect']) for b in pg['boxes']
             if b['box'].get('presentation_rect')
             and 145 <= b['box']['presentation_rect'][1] < 295
             and b['box']['id'] not in MOVES
             and b['box'].get('maxclass') not in ('comment',)]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            (ka, a), (kb, b2) = rects[i], rects[j]
            if (a[0] < b2[0] + b2[2] and b2[0] < a[0] + a[2] and
                    a[1] < b2[1] + b2[3] and b2[1] < a[1] + a[3]):
                print('     !! overlap %s %s  vs  %s %s' % (ka, a, kb, b2))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    enum[ti] = 'Filtro'
    for k, r in MOVES.items():
        by[k]['presentation_rect'] = list(r)

    shutil.copyfile(PAGES, PAGES + '.before')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    shutil.copyfile(AMXD, AMXD + '.before')
    amxd.save(AMXD, data, s, e, doc)

    back = amxd.load(AMXD)[3]['patcher']
    bt = next(b['box'] for b in back['boxes'] if b['box']['id'] == PAGINA)
    assert 'Filtro' in bt['saved_attribute_attributes']['valueof']['parameter_enum']
    bp = {b['box']['id']: b['box'] for b in json.load(open(PAGES, encoding='utf-8'))['patcher']['boxes']}
    assert bp['obj-157']['presentation_rect'][1] == 184.0
    print('\nwrote both files (+ .before). now: check_structure + check_params3')


if __name__ == '__main__':
    main()
