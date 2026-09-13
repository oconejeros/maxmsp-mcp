"""Add "Orn Base Cuarteto" + extend "Orn Base Modo" to FORTESEQ2.amxd (Fase 2 -- Quadritonal
Arpeggios).

    python tools/add_orn_quadritone.py            dry run, writes nothing
    python tools/add_orn_quadritone.py --apply    do it (device closed in Max AND Live)

forteseq2.js already carries the engine side: READ_ORNAMENT's base gained a THIRD layout.
ornBaseMode 2 (ORN_BASE_QUADRITONE) walks a flat 12-note partition of the chromatic total into
four mutually exclusive triads -- Slonimsky's Quadritonal Arpeggios (Thesaurus pp. 178-181; Liszt's
Faust theme is four augmented triads, Slonimsky's own Moto Perpetuo No. 1255 walks the same idea).
quadritonalPartition(scheme) picks which of the three printed partitions:

    0 = 4 Aumentadas       (four disjoint augmented triads)
    1 = Aum+May+men+dim    (one augmented, one major, one minor, one diminished)
    2 = 2dim+May+men       (two diminished, one major, one minor)

The ornament (Orn Tipo x Orn Notas) is stamped on top exactly as in the other two base modes.

This script is the Live surface:
  * "Orn Base Modo" (obj-769, added in the Base=Grados script) gets a third item, "Cuarteto"
    (mmax 1 -> 2).
  * One new top-level parameter, wired straight to obj-23 through its own `prepend
    setornquadscheme` and restored by the existing obj-631 fan:
        Orn Base Cuarteto   live.menu   3 items   -> prepend setornquadscheme
  * The Push bank "Ornamento" (index 48)'s last free "-" slot takes the new name.

Placement: a third compact row under the Base=Grados cluster (presentation x >= 772, y 126..140).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
ENGINE_ID = 'obj-23'       # js forteseq2.js
RESTORE_ID = 'obj-631'     # message "outputvalue", fed by loadbang (obj-31)
BASEMODE_ID = 'obj-769'    # live.menu "Orn Base Modo", added by add_orn_basemode.py

ANN_EXTRA = (' Orn Base Modo = Cuarteto: la base recorre una particion de las 12 notas en 4 '
             'triadas mutuamente excluyentes (Orn Base Cuarteto elige cual: 4 Aumentadas, '
             'Aum+Mayor+menor+disminuida, o 2 disminuidas+Mayor+menor) y las arpegia una tras '
             'otra -- las Quadritonal Arpeggios del Thesaurus (el tema del Fausto de Liszt son 4 '
             'triadas aumentadas). El ornamento se sigue estampando igual encima.')

QUAD_ENUM = ['4 Aumentadas', 'Aum+May+men+dim', '2dim+May+men']

PX = 772.0   # presentation column to the right of the fs2_pages bpatcher


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert bx[ENGINE_ID]['text'].startswith('js forteseq2.js'), bx[ENGINE_ID]['text']
    assert bx[RESTORE_ID]['text'] == 'outputvalue', bx[RESTORE_ID]['text']

    # --- 1. "Orn Base Modo" gets a third item -------------------------------------------------
    vo = bx[BASEMODE_ID]['saved_attribute_attributes']['valueof']
    assert vo['parameter_longname'] == 'Orn Base Modo', vo['parameter_longname']
    assert vo['parameter_enum'] == ['Intervalo', 'Grados'], vo['parameter_enum']
    assert vo['parameter_mmax'] == 1, vo['parameter_mmax']
    vo['parameter_enum'] = vo['parameter_enum'] + ['Cuarteto']
    vo['parameter_mmax'] = 2

    pl = bx['obj-636']
    assert 'Orn Base Cuarteto' not in pl.get('annotation', ''), 'ya aplicado'
    pl['annotation'] = pl.get('annotation', '') + ANN_EXTRA

    banks = PP['parameterbanks']
    b48 = banks['48']['parameters']
    assert b48[:7] == ['Patron Lectura', 'Orn Base', 'Orn Tipo', 'Orn Notas', 'Dir Lectura',
                        'Orn Base Modo', 'Orn Base Paso'], b48
    assert b48[7] == '-', 'el slot 8 del banco 48 ya esta ocupado: %r' % b48

    # --- 2. fresh ids ------------------------------------------------------------------------
    nid = [max(int(i.split('-')[1]) for i in bx)]
    py = [2100.0]   # patching-view y, clear band well right of everything

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

    comment('B.Cuar', [PX, 126.0, 36.0, 14.0])
    c_quad = menu('Orn Base Cuarteto', QUAD_ENUM, 0, [PX + 38, 126.0, 92.0, 14.0])
    p_quad = prepend('setornquadscheme')

    # --- 3. wiring: control -> prepend -> js, and restore fan -> control ---------------------
    P['lines'].append({'patchline': {'source': [c_quad, 0], 'destination': [p_quad, 0]}})
    P['lines'].append({'patchline': {'source': [p_quad, 0], 'destination': [ENGINE_ID, 0]}})
    P['lines'].append({'patchline': {'source': [RESTORE_ID, 0], 'destination': [c_quad, 0]}})

    # --- 4. registries -----------------------------------------------------------------------
    PP[c_quad] = ['Orn Base Cuarteto', 'Orn Base Cuarteto', 0]
    b48[7] = 'Orn Base Cuarteto'

    print('Orn Base Modo: enum 2 -> 3 (+Cuarteto), mmax 1 -> 2')
    print('nuevo control: %s Orn Base Cuarteto' % c_quad)
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
    vo2 = bx2[BASEMODE_ID]['saved_attribute_attributes']['valueof']
    assert vo2['parameter_enum'][-1] == 'Cuarteto' and vo2['parameter_mmax'] == 2, vo2
    assert c_quad in bx2 and P2['parameters'][c_quad][0] == 'Orn Base Cuarteto', c_quad
    b48b = P2['parameters']['parameterbanks']['48']['parameters']
    assert b48b[7] == 'Orn Base Cuarteto', b48b
    srcs = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P2['lines']}
    assert (c_quad, p_quad) in srcs and (p_quad, ENGINE_ID) in srcs and (RESTORE_ID, c_quad) in srcs

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  node forteseq/test/harness.js --check')
    print('  en Max: recarga js forteseq2.js + el jsui fs2horizon, script stop/start node.script')


main()
