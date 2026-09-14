"""Fix the global "Set" numbox (Armonia tab, fs2pages.maxpat obj-12): its range has been
capped at parameter_mmax=256 since the 2026-09-07 colmon-panel restructuring (commit ba7f31c),
which rebuilt the box and copied the wrong ceiling. The engine has 351 Tn-classes
(forteseq2.js: `sets.length`, "built N Tn-classes over 224 Forte classes"), and the per-voice
"V#N Set" numboxes (fs2voice_adv.maxpat obj-112) already correctly go to 351 -- only this
shared control was ever wrong. Reported by the user testing Live: dialing/typing into Set
past 256 does nothing.

fs2pages.maxpat is a plain JSON .maxpat (not an AMPF-wrapped .amxd), so this uses plain
json.load/json.dump like add_voice_key_lock.py's fs2voice_adv.maxpat edit does, not
amxd.load/save (that module's save() assumes the 'ptch' chunk header, which a bare .maxpat
does not have).

    python tools/fix_global_set_range.py            dry run, writes nothing
    python tools/fix_global_set_range.py --apply    do it (device closed in Max AND Live)
"""
import json
import os
import shutil
import sys

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
BOX_ID = 'obj-12'


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    box = bx[BOX_ID]
    vo = box['saved_attribute_attributes']['valueof']
    assert vo.get('parameter_longname') == 'Set', vo.get('parameter_longname')
    assert vo['parameter_mmax'] == 256.0, 'ya no es 256.0 -- reviso a mano (vale %r)' % vo['parameter_mmax']

    vo['parameter_mmax'] = 351.0

    print('%s (%s "Set"): parameter_mmax 256.0 -> 351.0' % (PAGES, BOX_ID))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(PAGES, PAGES + '.before-setrange')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
    bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    got = bx2[BOX_ID]['saved_attribute_attributes']['valueof']['parameter_mmax']
    assert got == 351.0, got

    print('\nescrito %s (.before-setrange guardado). Sigue:' % PAGES)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: cierra y reabre el editor del device (o quita/vuelve a poner el device en Live)')


main()
