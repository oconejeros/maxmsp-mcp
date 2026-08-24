"""Add McKay's Modal Harmonic Procession as a seventh Orden mode, and widen the Forte/vector readout
once more so the two new outlet-7 fields (modality name, mirror set) fit.

    python tools/add_order_modal.py            dry run, writes nothing
    python tools/add_order_modal.py --apply    do it

Chapter 26 of forteseq/Harmonic-Processions-Dosia-McKay.pdf ("Modalities and the Modal Harmonic
Procession") groups the 351 sets into 36 named families -- Suspended Triad, Quartal, Pentatonic,
Ionian Hexachord, Diatonic, Mixolydian/Lydian, Mystic/Enigmatic, Blues, Diminished,
Hungarian/Romanian, Augmented, several "Chromatic X Y Z" families, Whole-Tone, Octatonic, 12-Tone --
determined by a set's own span on the circle of fifths (already computed inside npOffsets() for the
Natural order added earlier) plus, for spans 9-11, which extra offsets beyond the diatonic envelope
are also present. forteseq2.js now computes this via modalityOf()/modalityNameOf(), and exposes each
set's mirror image (chapter 21, the sharp/flat counterpart with the same entry number and dissonance
level but a different modality) via mirrorOf()/mirrorForteOf() -- both verified against five of the
book's own worked classifications and its two named mirror pairs. This adds the grouping as
ORDER_MODAL = 6 in the existing Orden menu, and both new fields onto outlet 7 alongside the Forte
label, vector, McKay percentage, and Z-mate that were already there.

No new Live parameter this time -- same as add_order_natural.py, this only extends controls that
add_order_mckay.py already put in place (fs2_orden's enum, fs2_disp_forte's width), so there is
nothing new to register in FORTESEQ2.amxd.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(PAGES, encoding='utf-8'))
    P = pg['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}

    orden = bx[bv['fs2_orden']]
    vo = orden['saved_attribute_attributes']['valueof']
    assert vo['parameter_enum'] == ['Card', 'Forte', 'Cons', 'Vec', 'McKay', 'Natural'], vo['parameter_enum']
    vo['parameter_enum'] = vo['parameter_enum'] + ['Modal']
    assert vo['parameter_mmax'] == 5, vo['parameter_mmax']
    vo['parameter_mmax'] = 6
    orden['annotation'] = (orden['annotation'] +
        ' Modal: agrupa por las 36 modalidades del libro (capitulo 26) -- Suspended Triad, '
        'Quartal, Pentatonic, Ionian Hexachord, Diatonic, Mixolydian/Lydian, Mystic/Enigmatic, '
        'Blues, Diminished, Hungarian/Romanian, Augmented, varias Chromatic, Whole-Tone, '
        'Octatonic y 12-Tone -- y recien dentro de cada una ordena por Natural.')

    disp = bx[bv['fs2_disp_forte']]
    for key in ('patching_rect', 'presentation_rect'):
        r = disp[key]
        assert r[2] == 260.0, r
        disp[key] = [r[0], r[1], 280.0, r[3]]

    print('fs2pages.maxpat: Orden -> 7 opciones (+Modal), fs2_disp_forte 260 -> 280 px')

    edge = disp['presentation_rect'][0] + disp['presentation_rect'][2]
    print('borde derecho del readout: %.0f px (limite 516)' % edge)
    assert edge <= 516.0, edge

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return

    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump(pg, f, indent=1)
    print('')
    print('escrito %s' % PAGES)


main()
