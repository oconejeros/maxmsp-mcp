"""Add the "Rotacion" dial: manual control over which note of the current pitch-class set starts
the chord or the arpeggio -- C-E-G rotated to E-G-C to G-C-E, on demand rather than only via the
existing auto-advancing "Rotar x Cambio".

    python tools/add_rotation_control.py            dry run, writes nothing
    python tools/add_rotation_control.py --apply    do it

forteseq2.js already gained setrotation(n), backed by a NEW variable `manualRot` kept deliberately
separate from the existing auto-incrementing `rotation` (see the comment at its declaration) --
chordFor() and the arpeggio degree formula both read it additively, so it is a no-op at its
default of 0. This script only wires up the UI half: a live.numbox on the page that already holds
Voicing/Conduccion, sending `prepend setrotation` to the engine.

fs2pages.maxpat is a FILE bpatcher (referenced by name, not embedded), so it keeps its own
'parameters' registry, and FORTESEQ2.amxd keeps a second copy of the same three fields under
"obj-484::<id>" (obj-484 is the fs2_pages bpatcher instance) -- confirmed by cross-referencing both
files' registries for the existing Voicing/Conduccion controls before writing this. The "Musical"
parameterbank (FORTESEQ2.amxd, index 24) already has 2 free '-' slots, so no bank reorganization is
needed.

"Rotacion" is free as a longname: rotShape used to be called that before the 2026-08-24 rename to
"Rotar x Cambio", specifically because it was ambiguous with the concept this control implements.

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
NAME = 'Rotacion'
ANN = ('Gira el set actual: que nota lo empieza. En Acordes elige la inversion (C-E-G, E-G-C, '
       'G-C-E, ...); en Arpegio se suma a la rotacion automatica de "Rotar x Cambio" en vez de '
       'pelearla. Envuelve por la cardinalidad del set que suena -- en una triada, 3 vale lo '
       'mismo que 0. En Acordes, Conduccion sigue ganando cuando esta prendida, igual que ya '
       'gana sobre "Rotar x Cambio".')


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

    # Incidental fix, found while checking for a name collision: the 2026-08-24 rename
    # (Rotacion -> Rotar x Cambio, tools/rename_params.py) updated the box attribute and
    # FORTESEQ2.amxd's own registries (both obj-484::obj-21 and every parameterbank), but never
    # touched fs2pages.maxpat's OWN 'parameters' dict -- a registry that file keeps for itself,
    # separate from the mirrored copy FORTESEQ2.amxd carries under "obj-484::<id>". Left stale it
    # would have collided with the name this script wants to use, and is wrong on its own terms.
    stale = bx.get('obj-21')
    if stale and stale.get('varname') == 'fs2_rot' and PP.get('obj-21') == ['Rotacion', 'Rotacion', 0]:
        PP['obj-21'] = ['Rotar x Cambio', 'Rot', 0]
        print('fs2pages.maxpat: corregido registro obj-21 (Rotacion -> Rotar x Cambio, rename '
              'de 2026-08-24 que no habia tocado este archivo)')

    assert NAME not in {v[0] for k, v in PP.items()}, 'ya esta puesto'

    # Same tab as Voicing (obj-139, presentation y=509) and Conduccion (obj-150, y=469): the
    # Vector min/max grid on this page tops out at x=311, and the page's own right edge is 516
    # (fs2_disp_forte's width elsewhere on the file), so x=330 clears both with room to spare.
    voic = bx[bv['fs2_voic']]
    assert voic['presentation_rect'][:2] == [0.0, 509.0], voic['presentation_rect']
    edge = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
               for b in P['boxes'] if b['box'].get('presentation')
               and 400 <= b['box']['presentation_rect'][1] <= 560)
    assert edge <= 311.0, ('el hueco esperado ya no esta libre', edge)

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    lbl = fresh()
    P['boxes'].append({'box': {
        'id': lbl, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'text': 'Rotacion',
        'patching_rect': [330.0, 2870.0, 60.0, 18.0],
        'presentation': 1, 'presentation_rect': [330.0, 450.0, 60.0, 18.0]}})

    num = fresh()
    P['boxes'].append({'box': {
        'id': num, 'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2,
        'outlettype': ['', 'float'], 'parameter_enable': 1, 'varname': 'fs2_rotman',
        'annotation': ANN,
        'patching_rect': [330.0, 2890.0, 38.0, 15.0],
        'presentation': 1, 'presentation_rect': [330.0, 469.0, 38.0, 15.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_longname': NAME, 'parameter_shortname': NAME,
            'parameter_mmin': 0.0, 'parameter_mmax': 11.0, 'parameter_modmode': 4,
            'parameter_type': 1, 'parameter_unitstyle': 0,
            'parameter_initial': [0], 'parameter_initial_enable': 1}}}})

    prep = fresh()
    P['boxes'].append({'box': {
        'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_rotman_prep', 'patching_rect': [330.0, 2920.0, 110.0, 22.0],
        'text': 'prepend setrotation'}})

    for a, b in [(num, prep), (prep, OUTLET_ID)]:
        P['lines'].append({'patchline': {'source': [a, 0], 'destination': [b, 0]}})

    PP[num] = [NAME, NAME, 0]

    print('fs2pages.maxpat: agregado %s (%s), etiqueta en x=330 y=450, numbox en x=330 y=469'
          % (NAME, num))

    # --- FORTESEQ2.amxd --------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    D = doc['patcher']
    DP = D['parameters']
    nested_key = '%s::%s' % (BPATCHER_ID, num)
    assert nested_key not in DP, 'ya esta puesto'
    DP[nested_key] = [NAME, NAME, 0]

    bank = [b for b in DP['parameterbanks'].values() if b['name'] == 'Musical'][0]
    free = bank['parameters'].index('-')
    bank['parameters'][free] = NAME

    print('FORTESEQ2.amxd: registrado %s, banco Musical -> %s'
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
