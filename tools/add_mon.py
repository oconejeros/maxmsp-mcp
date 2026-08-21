"""Add the Mon toggle, so the per-voice readout can be switched off.

    python tools/add_mon.py            dry run, writes nothing
    python tools/add_mon.py --apply    do it

setmonitor() has existed since the hot-path work and nothing in the device could reach it, so the
readout has been repainting a comment at note rate with no way to stop it. In Node that looks
cheap; in Live it is GUI work on the interface thread, once per step in Arpegio.

It goes in the bottom strip next to the readout it governs rather than on a page, because a switch
you cannot see next to the thing it switches is a switch you will not remember exists.

Two things this has to get right, both of them traps this project has already been bitten by:

  * A BANG into a live.toggle INVERTS it. That is why fs2_run exists behind an `outputvalue`
    message instead of hanging off the loadbang like every other top-level control, and the same
    applies here.
  * A new top-level parameter has to be written into all three registries, and Run has to stay
    LAST in parameter_order -- the whole reason that order was set is that the metro must start
    only after everything else has been configured.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
NAME = 'Mon'
ANN = ('Muestra que nota esta tocando cada voz. Apagalo y el device deja de repintar ese texto: '
       'no es solo el calculo, es que cada repintado es trabajo de interfaz de Live, y en Arpegio '
       'ocurre en cada paso. A velocidad de nota igual no se alcanza a leer.')


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}
    PP = P['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}

    assert NAME not in {v[0] for k, v in PP.items() if k not in meta}, 'ya esta puesto'

    # --- the room it goes in ------------------------------------------------------------------
    mon = bx[bv['fs2_disp_mon']]
    r = mon['presentation_rect']
    right = r[0] + r[2]
    mon['presentation_rect'] = [r[0], r[1], 148.0, r[3]]
    lbl_x = r[0] + 148.0 + 2.0
    tog_x = right - 17.0
    assert lbl_x + 26.0 <= tog_x, (lbl_x, tog_x)

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    lbl = fresh()
    P['boxes'].append({'box': {
        'id': lbl, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'text': NAME,
        'presentation': 1, 'presentation_rect': [lbl_x, r[1], 26.0, 18.0],
        'patching_rect': [1700.0, 1160.0, 26.0, 18.0]}})

    tog = fresh()
    P['boxes'].append({'box': {
        'id': tog, 'maxclass': 'live.toggle', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'parameter_enable': 1, 'varname': 'fs2_mon', 'annotation': ANN,
        'presentation': 1, 'presentation_rect': [tog_x, r[1] + 1.0, 15.0, 15.0],
        'patching_rect': [1700.0, 1240.0, 15.0, 15.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_longname': NAME, 'parameter_shortname': NAME,
            'parameter_enum': ['off', 'on'], 'parameter_mmax': 1, 'parameter_modmode': 0,
            'parameter_type': 2, 'parameter_initial': [1], 'parameter_initial_enable': 1}}}})

    # An `outputvalue` message and not a cord from the loadbang: a bang into a live.toggle flips
    # it, so wiring it the way every numbox and tab here is wired would turn the monitor OFF every
    # time a Live set opened. fs2_run_out is the same shape for the same reason.
    out = fresh()
    P['boxes'].append({'box': {
        'id': out, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_mon_out', 'patching_rect': [1700.0, 1200.0, 70.0, 22.0],
        'text': 'outputvalue'}})

    prep = fresh()
    P['boxes'].append({'box': {
        'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_mon_prep', 'patching_rect': [1700.0, 1280.0, 140.0, 22.0],
        'text': 'prepend setmonitor'}})

    for a, b in [(bv['fs2_init'], out), (out, tog), (tog, prep), (prep, bv['fs2_gen'])]:
        P['lines'].append({'patchline': {'source': [a, 0], 'destination': [b, 0]}})

    # --- the registry -------------------------------------------------------------------------
    # Run keeps the last order it has always had. Everything else stays where it is, so no
    # automation lane in a saved set moves.
    run_key = [k for k, v in PP.items() if k not in meta and v[0] == 'Run'][0]
    tops = {k: v for k, v in PP.items() if k not in meta and '::' not in k}
    orders = sorted(v[2] for v in tops.values())
    assert orders == list(range(len(orders))), orders
    assert PP[run_key][2] == max(orders), ('Run no estaba ultimo', PP[run_key][2], max(orders))
    PP[tog] = [NAME, NAME, PP[run_key][2]]
    PP[run_key] = [PP[run_key][0], PP[run_key][1], PP[run_key][2] + 1]

    tops = {k: v for k, v in PP.items() if k not in meta and '::' not in k}
    orders = sorted(v[2] for v in tops.values())
    assert orders == list(range(len(orders))), orders
    assert PP[run_key][2] == max(orders), 'Run tiene que quedar ultimo'

    bank = [b for b in PP['parameterbanks'].values() if b['name'] == 'Engine'][0]
    free = bank['parameters'].index('-')
    bank['parameters'][free] = NAME

    print('%s: parametro %d de nivel superior, orden %d (Run pasa a %d, sigue ultimo)'
          % (NAME, len(tops), PP[tog][2], PP[run_key][2]))
    print('banco Engine: %s' % ' '.join(bank['parameters']))
    print('franja de abajo: fs2_disp_mon %.0f -> 148 px, etiqueta en x=%.0f, toggle en x=%.0f'
          % (r[2], lbl_x, tog_x))
    print('total de parametros: %d' % len([k for k in PP if k not in meta]))

    # Nothing may stick out past the right edge of the presentation.
    edge = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
               for b in P['boxes'] if b['box'].get('presentation'))
    print('borde derecho de la presentacion: %.0f px' % edge)
    assert edge <= 1124.0, edge

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
