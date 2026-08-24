"""Add McKay's Natural Harmonic Procession (quintal prime form) as a sixth Orden mode, and widen
the Forte/vector readout again so the new Z-relation field fits.

    python tools/add_order_natural.py            dry run, writes nothing
    python tools/add_order_natural.py --apply    do it

Chapters 18-23 of forteseq/Harmonic-Processions-Dosia-McKay.pdf describe a set's "quintal prime
form": pack it as tight as possible along the circle of fifths instead of the chromatic circle.
forteseq2.js now computes this via setNP[] (npOffsets()/npEntryOf(), reusing the same
zeroedNormalOrder() search Forte prime forms already use, just fed fifths/fourths positions
instead of semitones) -- verified against three of the book's own worked entry numbers. This adds
it as ORDER_NAT = 5 in the existing Orden menu, next to McKay's dissonance order added earlier.

Chapters 36-38 (Z-relation, modal heptachords/hexachords/pentachords, tritone substitution) turned
out to be locked to the printed edition in this copy of the PDF. Z-relation itself is standard set
theory (Allen Forte's own term, not specific to this book) and forteClass already carried enough
data to expose it cheaply -- zMateOf(), wired onto the same outlet 7 readout as the McKay percent.
Tritone substitution is not added: FORTESEQ2 already has a tritone step in Sec Raiz (the root
sequence generator), so a separate "tritone sub" control would just duplicate it.

No new Live parameter this time -- both edits extend controls add_order_mckay.py already put in
place (fs2_orden's enum, fs2_disp_forte's width), so there is nothing new to register.

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
    assert vo['parameter_enum'] == ['Card', 'Forte', 'Cons', 'Vec', 'McKay'], vo['parameter_enum']
    vo['parameter_enum'] = vo['parameter_enum'] + ['Natural']
    assert vo['parameter_mmax'] == 4, vo['parameter_mmax']
    vo['parameter_mmax'] = 5
    orden['annotation'] = (orden['annotation'] +
        ' Natural: la Procesion Armonica Natural del libro (capitulos 18-23) -- del set mas '
        'compacto sobre el circulo de quintas (su propia forma prima quintal) al cromatico '
        'completo. No tiene nada que ver con la disonancia: ordena por CERCANIA en quintas, asi '
        'que agrupa familias modales en vez de tension.')

    disp = bx[bv['fs2_disp_forte']]
    for key in ('patching_rect', 'presentation_rect'):
        r = disp[key]
        assert r[2] == 160.0, r
        disp[key] = [r[0], r[1], 260.0, r[3]]

    print('fs2pages.maxpat: Orden -> 6 opciones (+Natural), fs2_disp_forte 160 -> 260 px')

    # Nada debe sobresalir del borde derecho visible del bpatcher (516 px).
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
