"""Add Dosia McKay's dissonance-gradient model to the traversal Orden and to the tension curve.

    python tools/add_order_mckay.py            dry run, writes nothing
    python tools/add_order_mckay.py --apply    do it

Reading forteseq/Harmonic-Processions-Dosia-McKay.pdf (chapters 29-34) turned up two things worth
adding on top of what forteseq2.js already computes off setVec[]:

  * A fifth Orden mode -- dissonanceOf(), ascending -- so the catalogue can be walked from the
    most consonant set to the chromatic scale, the way the book's Dissonance-Gradient Harmonic
    Procession tables do.
  * A Modelo switch on the Camino tab (Huron / McKay) so the existing tension curve -- which
    already does exactly what chapter 34 describes, just with Huron's psychoacoustic weights --
    can run on the book's own weights instead. Orden's own Cons mode is untouched and stays Huron
    only, so golden.txt and anything already saved does not move unless Modelo is set by hand.

fs2pages.maxpat is a FILE bpatcher (referenced by name, not embedded), so it keeps its own
'parameters' registry, and FORTESEQ2.amxd keeps a second copy of the same three fields under
"obj-484::<id>" (obj-484 is the fs2_pages bpatcher instance) so Live can discover them without
opening the linked file -- confirmed by cross-referencing both files' registries for the existing
Orden and Tension controls before writing this. Only FORTESEQ2.amxd also needs a parameterbank
slot, since fs2pages.maxpat has none of its own; the Camino bank already has one free ('-').

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
BPATCHER_ID = 'obj-484'   # the fs2_pages bpatcher instance inside FORTESEQ2.amxd
OUTLET_ID = 'obj-5'       # fs2pages.maxpat's "mensajes hacia [js forteseq2.js]" outlet


def main():
    apply_it = '--apply' in sys.argv

    # --- fs2pages.maxpat -------------------------------------------------------------------
    pg = json.load(open(PAGES, encoding='utf-8'))
    P = pg['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}
    PP = P['parameters']

    assert bx[OUTLET_ID]['maxclass'] == 'outlet', bx[OUTLET_ID]
    assert bx[OUTLET_ID].get('comment', '').startswith('mensajes hacia'), bx[OUTLET_ID]

    # 1. Orden gets a fifth item.
    orden = bx[bv['fs2_orden']]
    vo = orden['saved_attribute_attributes']['valueof']
    assert vo['parameter_enum'] == ['Card', 'Forte', 'Cons', 'Vec'], vo['parameter_enum']
    vo['parameter_enum'] = vo['parameter_enum'] + ['McKay']
    assert vo['parameter_mmax'] == 3, vo['parameter_mmax']
    vo['parameter_mmax'] = 4
    orden['annotation'] = (orden['annotation'] +
        ' McKay: del set mas consonante al mas disonante segun el gradiente del libro Harmonic '
        'Processions (Dosia McKay) -- el peso de cada intervalo es el inverso de cuantas veces '
        'aparece en la escala diatonica, asi que P4 pesa 1/6 y el tritono pesa 1 entero.')

    # 2. Fresh ids for the new Modelo controls, placed on the Camino tab next to Prog (the row at
    # presentation y=900/919 has free space from x=330 to the right edge at 516).
    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    lbl = fresh()
    P['boxes'].append({'box': {
        'id': lbl, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'text': 'Modelo',
        'patching_rect': [330.0, 4400.0, 54.0, 18.0],
        'presentation': 1, 'presentation_rect': [330.0, 900.0, 54.0, 18.0]}})

    tab = fresh()
    ANN = ('Que pesos usa la curva de Tension para decidir que tan consonante es cada set. '
           'Huron: consonancia diadica empirica (Huron 1994), el modelo de siempre. McKay: el '
           'gradiente de disonancia del libro Harmonic Processions, un peso por intervalo segun '
           'su prevalencia en la escala diatonica. El modo Cons del Orden no cambia con esto, '
           'sigue siendo Huron puro.')
    P['boxes'].append({'box': {
        'id': tab, 'maxclass': 'live.tab', 'numinlets': 1, 'numoutlets': 3,
        'outlettype': ['', '', 'float'], 'parameter_enable': 1, 'varname': 'fs2_tensmodel',
        'annotation': ANN,
        'patching_rect': [330.0, 4420.0, 90.0, 18.0],
        'presentation': 1, 'presentation_rect': [330.0, 919.0, 90.0, 18.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_enum': ['Huron', 'McKay'], 'parameter_mmax': 1, 'parameter_modmode': 0,
            'parameter_type': 2, 'parameter_unitstyle': 9, 'parameter_initial': [0],
            'parameter_initial_enable': 1, 'parameter_longname': 'Modelo',
            'parameter_shortname': 'Modelo'}}}})

    prep = fresh()
    P['boxes'].append({'box': {
        'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [330.0, 4460.0, 150.0, 22.0], 'text': 'prepend settensmodel'}})

    for a, b in [(tab, prep), (prep, OUTLET_ID)]:
        P['lines'].append({'patchline': {'source': [a, 0], 'destination': [b, 0]}})

    PP[tab] = ['Modelo', 'Modelo', 0]

    # 3. Widen the Forte/vector readout so the new dissonance percentage fits next to it.
    disp = bx[bv['fs2_disp_forte']]
    for key in ('patching_rect', 'presentation_rect'):
        r = disp[key]
        disp[key] = [r[0], r[1], 160.0, r[3]]

    print('fs2pages.maxpat: Orden -> 5 opciones (+McKay), Modelo agregado (%s), '
          'fs2_disp_forte 112 -> 160 px' % tab)

    # --- FORTESEQ2.amxd --------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    D = doc['patcher']
    DP = D['parameters']
    nested_key = '%s::%s' % (BPATCHER_ID, tab)
    assert nested_key not in DP, 'ya esta puesto'
    DP[nested_key] = ['Modelo', 'Modelo', 0]

    bank = [b for b in DP['parameterbanks'].values() if b['name'] == 'Camino'][0]
    free = bank['parameters'].index('-')
    bank['parameters'][free] = 'Modelo'

    print('FORTESEQ2.amxd: registrado %s, banco Camino -> %s'
          % (nested_key, ' '.join(bank['parameters'])))

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return

    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump(pg, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s y %s' % (PAGES, DEVICE))


main()
