"""Add "Orn Serie Inicio/Paso/Pico" + extend "Orn Base Modo" to FORTESEQ2.amxd (Fase 2 --
Increasing and Diminishing Intervals).

    python tools/add_orn_series.py            dry run, writes nothing
    python tools/add_orn_series.py --apply    do it (device closed in Max AND Live)

forteseq2.js already carries the engine side: READ_ORNAMENT's base gained a FOURTH layout.
ornBaseMode 3 (ORN_BASE_SERIES) grows the interval BETWEEN principal tones arithmetically --
Orn Serie Inicio (the first leap, in semitones) growing by Orn Serie Paso for Orn Serie Pico
steps, then mirroring back down to the start before the arch repeats. Pitch keeps climbing the
whole time; only the SIZE of each leap grows then shrinks -- Slonimsky's "Increasing and
Diminishing Intervals" (Thesaurus, right after the Quadritonal Arpeggios). Pico=1 degenerates to
a constant interval, byte-identical to Base=Intervalo with that interval. The ornament (Orn Tipo
x Orn Notas) is stamped on top exactly as in the other three base modes.

This script is the Live surface:
  * "Orn Base Modo" (obj-769) gets a fourth item, "Serie" (mmax 2 -> 3).
  * Three new top-level parameters -- the "Ornamento" bank (48) is already full (8/8), so these
    land in a fresh bank, "Orn Serie" (49), wired straight to obj-23 through their own `prepend
    setornseries...` and restored by the existing obj-631 fan:
        Orn Serie Inicio   live.numbox 1..6   -> prepend setornseriesstart
        Orn Serie Paso     live.numbox 1..4   -> prepend setornseriesstep
        Orn Serie Pico     live.numbox 1..8   -> prepend setornseriespeak

Placement: three compact rows under the Base=Cuarteto row (presentation x >= 772, y 142..174).
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
ENGINE_ID = 'obj-23'       # js forteseq2.js
RESTORE_ID = 'obj-631'     # message "outputvalue", fed by loadbang (obj-31)
BASEMODE_ID = 'obj-769'    # live.menu "Orn Base Modo"

ANN_EXTRA = (' Orn Base Modo = Serie: la base recorre un arco de intervalos que crece '
             '(Orn Serie Inicio, +Orn Serie Paso por escalon, Orn Serie Pico escalones) y '
             'despues vuelve a bajar antes de repetir -- el tono sigue subiendo todo el tiempo, '
             'solo el TAMANO del salto sube y baja ("Increasing and Diminishing Intervals" del '
             'Thesaurus). Pico=1 da un intervalo constante, igual que Base=Intervalo.')

SLOTS = 8
BANK_NAME = 'Orn Serie'
BANK_PARAMS = ['Orn Serie Inicio', 'Orn Serie Paso', 'Orn Serie Pico']

PX = 772.0   # presentation column to the right of the fs2_pages bpatcher


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert bx[ENGINE_ID]['text'].startswith('js forteseq2.js'), bx[ENGINE_ID]['text']
    assert bx[RESTORE_ID]['text'] == 'outputvalue', bx[RESTORE_ID]['text']

    # --- 1. "Orn Base Modo" gets a fourth item ------------------------------------------------
    vo = bx[BASEMODE_ID]['saved_attribute_attributes']['valueof']
    assert vo['parameter_longname'] == 'Orn Base Modo', vo['parameter_longname']
    assert vo['parameter_enum'] == ['Intervalo', 'Grados', 'Cuarteto'], vo['parameter_enum']
    assert vo['parameter_mmax'] == 2, vo['parameter_mmax']
    vo['parameter_enum'] = vo['parameter_enum'] + ['Serie']
    vo['parameter_mmax'] = 3

    pl = bx['obj-636']
    assert 'Orn Serie' not in pl.get('annotation', ''), 'ya aplicado'
    pl['annotation'] = pl.get('annotation', '') + ANN_EXTRA

    banks = PP['parameterbanks']
    b48 = banks['48']['parameters']
    assert b48 == ['Patron Lectura', 'Orn Base', 'Orn Tipo', 'Orn Notas', 'Dir Lectura',
                   'Orn Base Modo', 'Orn Base Paso', 'Orn Base Cuarteto'], b48
    assert not any(k != 'parameterbanks' and isinstance(v, list) and v and v[0] in BANK_PARAMS
                   for k, v in PP.items()), 'ya aplicado'
    assert BANK_NAME not in {b['name'] for b in banks.values()}, 'el banco "%s" ya existe' % BANK_NAME

    # --- 2. fresh ids ------------------------------------------------------------------------
    nid = [max(int(i.split('-')[1]) for i in bx)]
    py = [2200.0]   # patching-view y, clear band well right of everything

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

    def prepend(msg):
        pid = fresh()
        P['boxes'].append({'box': {
            'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'patching_rect': [2760.0, step_y(), 190.0, 22.0], 'text': 'prepend ' + msg}})
        return pid

    comment('S.Inic', [PX, 142.0, 36.0, 14.0])
    c_start = numbox('Orn Serie Inicio', 1, 6, 1, [PX + 38, 142.0, 24.0, 14.0])
    comment('S.Paso', [PX, 158.0, 36.0, 14.0])
    c_step = numbox('Orn Serie Paso', 1, 4, 1, [PX + 38, 158.0, 24.0, 14.0])
    comment('S.Pico', [PX, 174.0, 36.0, 14.0])
    c_peak = numbox('Orn Serie Pico', 1, 8, 4, [PX + 38, 174.0, 24.0, 14.0])

    ctrls = [(c_start, 'setornseriesstart'), (c_step, 'setornseriesstep'), (c_peak, 'setornseriespeak')]
    preps = [(ctrl, prepend(msg)) for ctrl, msg in ctrls]

    # --- 3. wiring: control -> prepend -> js, and restore fan -> control ---------------------
    for ctrl, prep in preps:
        P['lines'].append({'patchline': {'source': [ctrl, 0], 'destination': [prep, 0]}})
        P['lines'].append({'patchline': {'source': [prep, 0], 'destination': [ENGINE_ID, 0]}})
        P['lines'].append({'patchline': {'source': [RESTORE_ID, 0], 'destination': [ctrl, 0]}})

    # --- 4. registries -----------------------------------------------------------------------
    PP[c_start] = ['Orn Serie Inicio', 'Orn Serie Inicio', 0]
    PP[c_step] = ['Orn Serie Paso', 'Orn Serie Paso', 0]
    PP[c_peak] = ['Orn Serie Pico', 'Orn Serie Pico', 0]

    nxt = max(int(k) for k in banks)
    bank_id = str(nxt + 1)
    banks[bank_id] = {'index': nxt + 1, 'name': BANK_NAME,
                       'parameters': list(BANK_PARAMS) + ['-'] * (SLOTS - len(BANK_PARAMS))}

    print('Orn Base Modo: enum 3 -> 4 (+Serie), mmax 2 -> 3')
    print('nuevos controles: %s Orn Serie Inicio, %s Orn Serie Paso, %s Orn Serie Pico' %
          (c_start, c_step, c_peak))
    print('nuevo banco Push %s "%s": %s' % (bank_id, BANK_NAME, ' '.join(banks[bank_id]['parameters'])))

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
    assert vo2['parameter_enum'][-1] == 'Serie' and vo2['parameter_mmax'] == 3, vo2
    for cid, ln in [(c_start, 'Orn Serie Inicio'), (c_step, 'Orn Serie Paso'), (c_peak, 'Orn Serie Pico')]:
        assert cid in bx2 and P2['parameters'][cid][0] == ln, cid
    bnb = P2['parameters']['parameterbanks'][bank_id]
    assert bnb['name'] == BANK_NAME and bnb['parameters'][:3] == BANK_PARAMS, bnb
    srcs = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in P2['lines']}
    for ctrl, prep in preps:
        assert (ctrl, prep) in srcs and (prep, ENGINE_ID) in srcs and (RESTORE_ID, ctrl) in srcs, ctrl

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  node forteseq/test/harness.js --check')
    print('  en Max: recarga js forteseq2.js + el jsui fs2horizon, script stop/start node.script')


main()
