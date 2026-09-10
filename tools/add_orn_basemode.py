"""Add "Orn Base Modo" + "Orn Base Paso" to FORTESEQ2.amxd (Fase 2 -- base por grados del set).

    python tools/add_orn_basemode.py            dry run, writes nothing
    python tools/add_orn_basemode.py --apply    do it (device closed in Max AND Live)

forteseq2.js already carries the engine side: READ_ORNAMENT gained a second base layout. Today the
principal tones are stepped by a fixed interval (ornBaseInterval) -- Slonimsky's equal division,
which always yields a scale symmetric at that interval. With ornBaseMode = 1 (Grados) the principal
tones become the DEGREES of the current set, ornBaseStep at a time (1 = consecutive, 2 = thirds),
so the base can be any arpeggio and the resulting scale need not be symmetric -- Slonimsky's
Heptatonic Arpeggios / Cochrane Part III. The ornament (Orn Tipo x Orn Notas) is stamped exactly
as before; ornBaseInterval still governs the ornament's chromatic reach.

This script is the Live surface: two new top-level parameters, wired straight to obj-23 through
their own `prepend set...` and restored by the existing obj-631 (loadbang -> outputvalue) fan,
exactly like the three Fase 1 controls (Orn Base / Orn Tipo / Orn Notas):

    Orn Base Modo   live.menu   [Intervalo, Grados]   -> prepend setornbasemode
    Orn Base Paso   live.numbox 1..4                  -> prepend setornbasestep

Placement: two compact rows just under the Fase 1 ornament cluster (presentation x >= 772, y
94..124). openrect width is 0, so Live re-sizes the panel to fit. The Push bank "Ornamento"
(index 48, added in Fase 1) has two free "-" slots -- they take the two new names.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
ENGINE_ID = 'obj-23'     # js forteseq2.js
RESTORE_ID = 'obj-631'   # message "outputvalue", fed by loadbang (obj-31)

ANN_EXTRA = (' Orn Base Modo: Intervalo (division igual, la de siempre -- siempre da una escala '
             'simetrica al intervalo) o Grados (los tonos principales son los grados del set, '
             'Orn Base Paso a la vez: 1 = consecutivos, 2 = terceras) -- ahi la base puede ser '
             'cualquier arpegio y la escala resultante no tiene que ser simetrica. En modo Grados '
             'Orn Base solo fija el alcance cromatico del ornamento.')

PX = 772.0   # presentation column to the right of the fs2_pages bpatcher


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert bx[ENGINE_ID]['text'].startswith('js forteseq2.js'), bx[ENGINE_ID]['text']
    assert bx[RESTORE_ID]['text'] == 'outputvalue', bx[RESTORE_ID]['text']

    # Fase 1 must already be applied: the "Ornamento" bank and the Orn Base control.
    banks = PP['parameterbanks']
    assert '48' in banks and banks['48']['name'] == 'Ornamento', 'falta la Fase 1 (banco 48)'
    b48 = banks['48']['parameters']
    assert b48[:5] == ['Patron Lectura', 'Orn Base', 'Orn Tipo', 'Orn Notas', 'Dir Lectura'], b48
    assert b48[5] == '-' and b48[6] == '-', 'los slots 6-7 del banco 48 ya estan ocupados: %r' % b48
    assert not any(v[0] == 'Orn Base Modo' for v in PP.values() if isinstance(v, list)), 'ya aplicado'

    # extend the Patron Lectura annotation (obj-636), same box the Fase 1 note lives on
    pl = bx['obj-636']
    if 'Orn Base Modo' not in pl.get('annotation', ''):
        pl['annotation'] = pl.get('annotation', '') + ANN_EXTRA

    nid = [max(int(i.split('-')[1]) for i in bx)]
    py = [1980.0]   # patching-view y, clear band well right of everything

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def step_y():
        py[0] += 26.0
        return py[0]

    def comment(text, prect):
        cid = fresh()
        P['boxes'].append({'box': {
            'id': cid, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
            'fontsize': 8.0, 'text': text,
            'patching_rect': [2600.0, step_y(), 60.0, 18.0],
            'presentation': 1, 'presentation_rect': list(prect)}})
        return cid

    def numbox(longname, mmin, mmax, initial, prect):
        nb = fresh()
        P['boxes'].append({'box': {
            'id': nb, 'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2,
            'outlettype': ['', 'float'], 'parameter_enable': 1, 'fontsize': 8.0,
            'varname': 'fs2_' + nb.replace('-', '_'),
            'patching_rect': [2600.0, step_y(), 42.0, 13.0],
            'presentation': 1, 'presentation_rect': list(prect),
            'saved_attribute_attributes': {'valueof': {
                'parameter_initial': [initial], 'parameter_initial_enable': 1,
                'parameter_longname': longname, 'parameter_shortname': longname,
                'parameter_mmin': mmin, 'parameter_mmax': mmax,
                'parameter_modmode': 0, 'parameter_type': 1, 'parameter_unitstyle': 0}}}})
        return nb

    def menu(longname, enum, initial, prect):
        mn = fresh()
        P['boxes'].append({'box': {
            'id': mn, 'maxclass': 'live.menu', 'numinlets': 1, 'numoutlets': 3,
            'outlettype': ['', '', 'float'], 'parameter_enable': 1, 'fontsize': 8.0,
            'varname': 'fs2_' + mn.replace('-', '_'),
            'patching_rect': [2600.0, step_y(), 90.0, 15.0],
            'presentation': 1, 'presentation_rect': list(prect),
            'saved_attribute_attributes': {'valueof': {
                'parameter_enum': list(enum), 'parameter_initial': [initial],
                'parameter_initial_enable': 1, 'parameter_longname': longname,
                'parameter_shortname': longname, 'parameter_mmax': len(enum) - 1,
                'parameter_modmode': 0, 'parameter_type': 2, 'parameter_unitstyle': 9}}}})
        return mn

    def prepend(msg):
        pid = fresh()
        P['boxes'].append({'box': {
            'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'patching_rect': [2760.0, step_y(), 190.0, 22.0], 'text': 'prepend ' + msg}})
        return pid

    comment('B.Modo', [PX, 94.0, 36.0, 14.0])
    c_bmode = menu('Orn Base Modo', ['Intervalo', 'Grados'], 0, [PX + 38, 94.0, 76.0, 14.0])
    comment('B.Paso', [PX, 110.0, 36.0, 14.0])
    c_bstep = numbox('Orn Base Paso', 1, 4, 1, [PX + 38, 110.0, 24.0, 14.0])

    p_bmode = prepend('setornbasemode')
    p_bstep = prepend('setornbasestep')

    # wiring: control -> prepend -> js, and restore fan -> control
    for ctrl, prep in [(c_bmode, p_bmode), (c_bstep, p_bstep)]:
        P['lines'].append({'patchline': {'source': [ctrl, 0], 'destination': [prep, 0]}})
        P['lines'].append({'patchline': {'source': [prep, 0], 'destination': [ENGINE_ID, 0]}})
        P['lines'].append({'patchline': {'source': [RESTORE_ID, 0], 'destination': [ctrl, 0]}})

    # registries
    PP[c_bmode] = ['Orn Base Modo', 'Orn Base Modo', 0]
    PP[c_bstep] = ['Orn Base Paso', 'Orn Base Paso', 0]
    b48[5] = 'Orn Base Modo'
    b48[6] = 'Orn Base Paso'

    print('nuevos controles: %s Orn Base Modo, %s Orn Base Paso' % (c_bmode, c_bstep))
    print('banco Push 48 "Ornamento": %s' % ' '.join(b48))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    # read back and assert
    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    for cid, ln in [(c_bmode, 'Orn Base Modo'), (c_bstep, 'Orn Base Paso')]:
        assert cid in bx2, cid
        assert P2['parameters'][cid][0] == ln, P2['parameters'][cid]
    b48b = P2['parameters']['parameterbanks']['48']['parameters']
    assert b48b[5] == 'Orn Base Modo' and b48b[6] == 'Orn Base Paso', b48b
    srcs = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P2['lines']}
    for ctrl, prep in [(c_bmode, p_bmode), (c_bstep, p_bstep)]:
        assert (ctrl, prep) in srcs and (prep, ENGINE_ID) in srcs and (RESTORE_ID, ctrl) in srcs, ctrl

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  node forteseq/test/harness.js --check')
    print('  en Max: recarga js forteseq2.js + el jsui fs2horizon, script stop/start node.script')


main()
