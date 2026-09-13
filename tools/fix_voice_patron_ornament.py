"""Fix a stale enum: the per-voice "V#1 Patron" numbox in fs2voice_adv.maxpat never learned
about READ_ORNAMENT (added to the top-level "Patron Lectura" enum back in Fase 1 of the
Slonimsky integration).

    python tools/fix_voice_patron_ornament.py            dry run, writes nothing
    python tools/fix_voice_patron_ornament.py --apply    do it (device closed in Max AND Live)

## The bug this fixes

A previous session searched FORTESEQ2.amxd's own top-level boxes for a per-voice "Propia"
override for Patron/Dir Lectura, found none, and concluded the feature needed to be built from
scratch -- redirecting Fase 2 work to Quadritonal Arpeggios / Intervallic Series instead. That
search was incomplete: the per-voice override lives in a SEPARATE bpatcher file,
forteseq/fs2voice_adv.maxpat (the "Voces+" tab's advanced voice strip, instantiated four times as
obj-577..obj-580 in FORTESEQ2.amxd), not in FORTESEQ2.amxd's own boxes. It has been there all
along: "V#1 LecProp" (toggle) + "V#1 Patron" (numbox) + "V#1 Dir" (numbox), wired straight to the
engine's setvoicereadown/setvoicereadmode/setvoicereaddir -- fully functional, covered by the
harness ("Lectura por voz: Patron/Dir propios aislan una voz bajo Voces Indep").

The one real gap: "V#1 Patron"'s enum was frozen at 7 items (mmax 6, up to "Urna") from before
READ_ORNAMENT existed, so nothing in Live could dial a voice's own Patron to Ornamento even
though setvoicereadmode() has clamped to READ_MAX=7 since Fase 1. This script brings the enum up
to date with the top-level "Patron Lectura" (obj-636 in FORTESEQ2.amxd): + "Ornamento", mmax 6->7.

Once this lands, a voice with "V#1 LecProp" on and "V#1 Patron" = Ornamento independently walks
the SAME ornament (Orn Base/Tipo/Notas/Base Modo are still global -- shared across voices) from
its own cursor, while other voices keep reading however they are set. That is per-voice
ornament AS THE ENGINE ALREADY SUPPORTS IT; true per-voice ornament PARAMETERS (independent Orn
Tipo/Notas/Base per voice) remain a separate, larger feature (plan Fase 2 backlog).

fs2voice_adv.maxpat is a single file shared by all four bpatcher instances (obj-577..obj-580 in
FORTESEQ2.amxd), so one edit here reaches all four voices at once -- no changes to FORTESEQ2.amxd
itself are needed. Plain JSON .maxpat, so no `.before` backup (git already diffs it) -- same
convention as add_voice_art.py / add_desf.py, which edit this file's sibling fs2voice.maxpat the
same way.
"""
import json
import os
import sys

VOICE = os.path.join('forteseq', 'fs2voice_adv.maxpat')
PATRON_ID = 'obj-45'   # live.numbox "V#1 Patron"

OLD_ENUM = ['Normal', 'Super', 'Minima', 'Modos', 'Coprimo', 'Zigzag', 'Urna']
NEW_ENUM = OLD_ENUM + ['Ornamento']


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}

    vo = bx[PATRON_ID]['saved_attribute_attributes']['valueof']
    assert vo['parameter_longname'] == 'V#1 Patron', vo['parameter_longname']
    assert vo['parameter_enum'] == OLD_ENUM, 'ya aplicado o cambio de forma inesperada: %r' % vo['parameter_enum']
    assert vo['parameter_mmax'] == 6, vo['parameter_mmax']

    vo['parameter_enum'] = list(NEW_ENUM)
    vo['parameter_mmax'] = 7

    print('V#1 Patron: enum 7 -> 8 (+Ornamento), mmax 6 -> 7')
    print('alcanza a las 4 voces via obj-577..obj-580 en FORTESEQ2.amxd (misma fs2voice_adv.maxpat)')

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    pg2 = json.load(open(VOICE, encoding='utf-8'))['patcher']
    bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    vo2 = bx2[PATRON_ID]['saved_attribute_attributes']['valueof']
    assert vo2['parameter_enum'] == NEW_ENUM and vo2['parameter_mmax'] == 7, vo2

    print('\nescrito %s. Sigue:' % VOICE)
    print('  python tools/check_structure.py forteseq/fs2voice_adv.maxpat')
    print('  python tools/check_params3.py')
    print('  en Max: recarga el bpatcher (cerrar y volver a abrir el device alcanza), script stop/start')


main()
