"""Phase E: add "Human" and "Caida" to the M1..M4 Dest menus in fs2pages.maxpat.

    python tools/extend_mod_dests.py            dry run
    python tools/extend_mod_dests.py --apply    write fs2pages.maxpat (+ .before)

The modulator destination list is hard-coded in the `parameter_enum` of the four
`md_m1_dest`..`md_m4_dest` live.menu boxes (obj-311/322/333/344). The JS side
(MOD_DEST_NAMES / MOD_SPAN / D_HUMAN / D_DECAY + the modAt() reads in humanizeOffset() and
scheduleBurst()) is edited by hand in forteseq2.js -- **index order is the contract**, so
the two must be appended in the same order.

  index 10 -> "Human"  (humanizePct, span 50)
  index 11 -> "Caida"  (ratchetDecay, span 50)

Only fs2pages.maxpat changes: the .amxd mirror of these params is `[longname, shortname,
order]` with no enum, and they have no parameter_overrides entry. Idempotent.
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, 'forteseq', 'fs2pages.maxpat')

DEST_MENUS = ['obj-311', 'obj-322', 'obj-333', 'obj-344']   # M1..M4 Dest
ADD = ['Human', 'Caida']
EXPECT_BASE = ['-', 'Raiz', 'Octava', 'Vel', 'Largo', 'Silencio', 'Swing', 'Rasgueo',
               'Ratchet', 'Grado']


def main():
    apply_it = '--apply' in sys.argv
    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
    by = {b['box']['id']: b['box'] for b in pg['boxes']}

    done = 0
    for mid in DEST_MENUS:
        b = by[mid]
        vo = b['saved_attribute_attributes']['valueof']
        enum = vo['parameter_enum']
        ln = vo.get('parameter_longname')
        if enum[-len(ADD):] == ADD:
            print('  %s (%s) already extended' % (mid, ln)); done += 1; continue
        assert enum == EXPECT_BASE, '%s enum unexpected: %s' % (mid, enum)
        new = enum + ADD
        print('  %s (%s): %d -> %d items, mmax %s -> %d'
              % (mid, ln, len(enum), len(new), vo.get('parameter_mmax'), len(new) - 1))
        if apply_it:
            vo['parameter_enum'] = new
            vo['parameter_mmax'] = len(new) - 1

    if done == len(DEST_MENUS):
        print('nothing to do'); return
    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)'); return

    shutil.copyfile(PAGES, PAGES + '.before')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    back = {b['box']['id']: b['box'] for b in json.load(open(PAGES, encoding='utf-8'))['patcher']['boxes']}
    for mid in DEST_MENUS:
        e = back[mid]['saved_attribute_attributes']['valueof']['parameter_enum']
        assert e[-2:] == ADD and len(e) == 12, e
    print('\nwrote %s (+ .before)' % os.path.relpath(PAGES, ROOT))
    print('paired JS edit in forteseq2.js: MOD_DEST_NAMES / MOD_SPAN / D_HUMAN,D_DECAY +'
          ' modAt() in humanizeOffset() and scheduleBurst()')


if __name__ == '__main__':
    main()
