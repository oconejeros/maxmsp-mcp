"""Fix the REAL root cause behind "Armonia always shows on top of every tab":
the fs2pages.maxpat bpatcher box (obj-484) has varname "obj-238" -- but every single
"script show/hide/sendbox fs2_pages ..." message in the device (14 of them, across
obj-486's page-pan router and obj-582/obj-721/722/800/804/723's show/hide chains) targets
the scripting name "fs2_pages", which matches NO box in the file. Confirmed by counting:
zero boxes have varname=="fs2_pages" while the literal string appears 14 times as a
`script` message target. Every one of those messages has therefore always been a silent
no-op against a dead reference -- the bpatcher never actually pans or hides, so it just
sits wherever it was last left (offset [0,0] = Armonia), visible regardless of which
Pagina tab is selected. This is why the Globales-specific router fix (obj-582) alone
didn't help: the underlying "fs2_pages" target doesn't exist for ANY tab, not just
Globales -- Voces 1-4 only "worked" because their own vadv1-4 boxes are brought to front
on top of the still-stuck-visible fs2_pages, masking it rather than actually hiding it.

Fix: restore obj-484's varname to "fs2_pages" (the name every message already expects),
rather than rewriting 14 message boxes to the auto-generated "obj-238".

    python tools/fix_fs2_pages_varname.py            dry run, writes nothing
    python tools/fix_fs2_pages_varname.py --apply    do it (device closed in Max AND Live)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
BPATCHER_ID = 'obj-484'


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}

    b = bx[BPATCHER_ID]
    assert b['maxclass'] == 'bpatcher' and b['name'] == 'fs2pages.maxpat'
    assert b['varname'] == 'obj-238', b['varname']
    assert not any(bo['box'].get('varname') == 'fs2_pages' for bo in P['boxes']), 'ya existe otra caja con ese varname'

    n_targets = sum(bo['box'].get('text', '').count('fs2_pages') for bo in P['boxes'] if bo['box'].get('maxclass') == 'message')
    print('mensajes que apuntan a "fs2_pages":', n_targets)

    b['varname'] = 'fs2_pages'
    print('%s: varname "obj-238" -> "fs2_pages"' % BPATCHER_ID)

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-pagesvarname')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {bo['box']['id']: bo['box'] for bo in doc2['patcher']['boxes']}
    assert bx2[BPATCHER_ID]['varname'] == 'fs2_pages'

    print('\nescrito %s (.before-pagesvarname guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: cerrar y reabrir el Live Set (o sacar/reinsertar el device)')


main()
