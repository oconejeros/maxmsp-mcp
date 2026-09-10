"""Add READ_ORNAMENT (Patron Lectura -> "Ornamento") and its three controls to FORTESEQ2.amxd.

    python tools/add_read_ornament.py            dry run, writes nothing
    python tools/add_read_ornament.py --apply    do it (device closed in Max AND Live)

Phase 1 of the Slonimsky Thesaurus integration. forteseq2.js already carries the engine side:
a new reading order READ_ORNAMENT (value 7) that builds a "base" of principal tones by stepping
the root by a FIXED interval and stamps a fixed infra/inter/ultrapolation ornament on each -- so
the notes it plays are deliberately NOT members of the current set, which none of the other
reading orders can do. This script is the Live surface for it:

  * obj-636 "Patron Lectura" gets an eighth item, "Ornamento" (mmax 6 -> 7).
  * Three new top-level parameters, wired straight to the engine js (obj-23) through their own
    `prepend set...` and restored by the existing obj-631 (loadbang -> outputvalue) fan, exactly
    like obj-636 itself:
        Orn Base   live.numbox  1..14 st   -> prepend setornbaseinterval
        Orn Tipo   live.menu    6 items    -> prepend setorntype
        Orn Notas  live.numbox  1..4       -> prepend setorncount
  * A new Push bank "Ornamento" groups them with Patron Lectura + Dir Lectura (index 48; the
    existing banks 7/12/20 that carry Patron Lectura are all full).

Placement: the always-visible rows are packed, so the cluster is a small vertical stack in the
empty column to the right of the fs2_pages bpatcher (presentation x>=772, y 6..92 -- verified
clear). openrect width is 0, so Live re-sizes the panel to fit.

The reorg to 6 tabs already pulled Patron Lectura and Dir Lectura out of fs2pages.maxpat into the
top-level patcher, so this is the plain three-registry case: box valueof + P['parameters'] +
parameterbanks, all in FORTESEQ2.amxd. No fs2pages.maxpat edit.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PATLECT_ID = 'obj-636'   # live.menu "Patron Lectura"
ENGINE_ID = 'obj-23'     # js forteseq2.js
RESTORE_ID = 'obj-631'   # message "outputvalue", fed by loadbang (obj-31)

ANN_EXTRA = (' Ornamento: la receta de las primeras doce secciones del Thesaurus de Slonimsky. '
             'Arma una base de tonos principales subiendo la raiz por un intervalo fijo (Orn Base '
             'en semitonos: 4 = Ditone/aumentada, 7 = Diapente/ciclo de quintas, 14 = Septitone) '
             'y estampa en cada tono el mismo ornamento (Orn Tipo x Orn Notas). Las notas que '
             'suenan NO son del set: interpolacion rellena cromatico entre un tono y el siguiente, '
             'infrapolacion agrega notas por debajo, ultrapolacion por encima del siguiente tono '
             '-- las dos ultimas doblan la linea en zigzag. Solo en modo Arpegio.')

ORN_TIPO_ENUM = ['Interpol', 'Infrapol', 'Ultrapol', 'Infra+Inter', 'Infra+Ultra', 'In+Int+Ult']

# presentation column to the right of the fs2_pages bpatcher (obj-484 ends at x=767)
PX = 772.0


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    # --- 1. Patron Lectura gets an eighth item ------------------------------------------------
    vo = bx[PATLECT_ID]['saved_attribute_attributes']['valueof']
    assert vo['parameter_enum'] == ['Normal', 'Super', 'Minima', 'Modos', 'Coprimo', 'Zigzag', 'Urna'], vo['parameter_enum']
    assert vo['parameter_mmax'] == 6, vo['parameter_mmax']
    vo['parameter_enum'] = vo['parameter_enum'] + ['Ornamento']
    vo['parameter_mmax'] = 7
    ann = bx[PATLECT_ID].get('annotation', '')
    assert 'Ornamento' not in ann, 'ya aplicado'
    bx[PATLECT_ID]['annotation'] = ann + ANN_EXTRA

    assert bx[ENGINE_ID]['text'].startswith('js forteseq2.js'), bx[ENGINE_ID]['text']
    assert bx[RESTORE_ID]['text'] == 'outputvalue', bx[RESTORE_ID]['text']

    # --- 2. fresh ids ----------------------------------------------------------------------
    nid = [max(int(i.split('-')[1]) for i in bx)]
    py = [1780.0]   # patching-view y, stepped per box -- clear band well right of everything

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
            'patching_rect': [2760.0, step_y(), 180.0, 22.0], 'text': 'prepend ' + msg}})
        return pid

    comment('Ornamento', [PX, 6.0, 74.0, 16.0])
    comment('Base', [PX, 24.0, 28.0, 15.0])
    c_base = numbox('Orn Base', 1, 14, 4, [PX + 32, 24.0, 28.0, 15.0])
    comment('Tipo', [PX, 42.0, 28.0, 15.0])
    c_tipo = menu('Orn Tipo', ORN_TIPO_ENUM, 0, [PX, 58.0, 96.0, 15.0])
    comment('Notas', [PX, 76.0, 34.0, 15.0])
    c_notas = numbox('Orn Notas', 1, 4, 1, [PX + 36, 76.0, 24.0, 15.0])

    p_base = prepend('setornbaseinterval')
    p_tipo = prepend('setorntype')
    p_notas = prepend('setorncount')

    # --- 3. wiring: control -> prepend -> js, and restore fan -> control ---------------------
    for ctrl, prep in [(c_base, p_base), (c_tipo, p_tipo), (c_notas, p_notas)]:
        P['lines'].append({'patchline': {'source': [ctrl, 0], 'destination': [prep, 0]}})
        P['lines'].append({'patchline': {'source': [prep, 0], 'destination': [ENGINE_ID, 0]}})
        P['lines'].append({'patchline': {'source': [RESTORE_ID, 0], 'destination': [ctrl, 0]}})

    # --- 4. registries ---------------------------------------------------------------------
    PP[c_base] = ['Orn Base', 'Orn Base', 0]
    PP[c_tipo] = ['Orn Tipo', 'Orn Tipo', 0]
    PP[c_notas] = ['Orn Notas', 'Orn Notas', 0]

    banks = PP['parameterbanks']
    assert '48' not in banks, banks.keys()
    banks['48'] = {
        'index': 48, 'name': 'Ornamento',
        'parameters': ['Patron Lectura', 'Orn Base', 'Orn Tipo', 'Orn Notas',
                       'Dir Lectura', '-', '-', '-'],
        'buttons': ['-'] * 8}

    print('Patron Lectura: enum 7 -> 8 (+Ornamento), mmax 6 -> 7')
    print('nuevos controles: %s Orn Base, %s Orn Tipo, %s Orn Notas' % (c_base, c_tipo, c_notas))
    print('nuevo banco Push 48 "Ornamento": %s' % ' '.join(banks['48']['parameters']))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    # read back and assert
    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    vo2 = bx2[PATLECT_ID]['saved_attribute_attributes']['valueof']
    assert vo2['parameter_enum'][-1] == 'Ornamento' and vo2['parameter_mmax'] == 7, vo2
    for cid, ln in [(c_base, 'Orn Base'), (c_tipo, 'Orn Tipo'), (c_notas, 'Orn Notas')]:
        assert cid in bx2, cid
        assert P2['parameters'][cid][0] == ln, P2['parameters'][cid]
    assert P2['parameters']['parameterbanks']['48']['name'] == 'Ornamento'
    srcs = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P2['lines']}
    for ctrl, prep, msg in [(c_base, p_base, 'setornbaseinterval'), (c_tipo, p_tipo, 'setorntype'),
                            (c_notas, p_notas, 'setorncount')]:
        assert (ctrl, prep) in srcs and (prep, ENGINE_ID) in srcs and (RESTORE_ID, ctrl) in srcs, msg

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  node forteseq/test/harness.js --check')
    print('  en Max: recarga js forteseq2.js, script stop/start node.script')


main()
