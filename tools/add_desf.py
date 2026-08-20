"""Give every voice its own Desf: a fixed shove in sub-ticks.

The nine controls on the Tiempo page are global -- they describe a feel the whole device has.
Desf is the one timing control that is per voice, which is what turns four voices playing the
same rhythm into an ensemble that is not quite together. It belongs in the voice strip next to
Fase, because Fase offsets which accent cell a voice reads and Desf offsets when it sounds, and
having them apart would invite confusing one for the other.

    python tools/add_desf.py            dry run, writes nothing
    python tools/add_desf.py --apply    do it

The strip has no room left, so this costs 38 px: the strip grows, and the tab, the page window
and the readout row all slide right by the same amount. 1086 -> 1124, against the 1442 it was.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE = os.path.join('forteseq', 'fs2voice.maxpat')
GROW = 38.0                 # what the strip takes, and therefore what everything right of it moves
COL_X = 462.0               # where Desf sits inside the strip
ANN = ('Corrimiento fijo de esta voz, en sub-ticks: cuanto sale tarde respecto del paso. Es lo '
       'que convierte cuatro voces tocando el mismo ritmo en un conjunto que no esta del todo '
       'junto. Distinto de Fase, que corre que celda de la reja lee la voz y no cuando suena. '
       'Necesita Sub mayor que 1.')
SHIFT = ['fs2_pagina', 'fs2_pages', 'fs2_lbl_notas', 'fs2_disp_notes',
         'fs2_lbl_midi', 'fs2_disp_mon']


def main():
    apply_it = '--apply' in sys.argv

    # ---- the strip ---------------------------------------------------------------------------
    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pb = {b['box']['id']: b['box'] for b in pg['boxes']}
    byvar = {b.get('varname'): i for i, b in pb.items() if b.get('varname')}
    assert 'v_desf' not in byvar, 'ya esta puesto'
    out = [i for i, b in pb.items() if b['maxclass'] == 'outlet'][0]
    init = byvar['v_init_msg']
    nxt = max(int(i.split('-')[1]) for i in pb)

    num, prep = 'obj-%d' % (nxt + 1), 'obj-%d' % (nxt + 2)
    pg['boxes'].append({'box': {
        'id': num, 'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2,
        'outlettype': ['', 'float'], 'parameter_enable': 1, 'varname': 'v_desf',
        'annotation': ANN,
        'patching_rect': [530.0, 380.0, 44.0, 15.0],
        'presentation': 1, 'presentation_rect': [COL_X, 4.0, 30.0, 15.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_longname': 'V#1 Desf', 'parameter_shortname': 'Desf',
            'parameter_type': 1, 'parameter_initial': [0], 'parameter_initial_enable': 1,
            'parameter_mmin': 0.0, 'parameter_mmax': 7.0,
            'parameter_modmode': 4, 'parameter_unitstyle': 0}}}})
    pg['boxes'].append({'box': {
        'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_desf_prep', 'patching_rect': [500.0, 510.0, 240.0, 22.0],
        'text': 'prepend setvoicetimeoffset #1'}})
    for a, c in ((init, num), (num, prep), (prep, out)):
        pg['lines'].append({'patchline': {'source': [a, 0], 'destination': [c, 0]}})
    pg['parameters'][num] = ['V#1 Desf', 'V#1 Desf', 0]
    right = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
                for b in pg['boxes'] if b['box'].get('presentation'))
    print('tira: %d parametros, el contenido llega a x=%.0f' % (len(pg['parameters']), right))

    # ---- the parent --------------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    box = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in box.items() if b.get('varname')}

    strips = [b['box'] for b in P['boxes']
              if b['box']['maxclass'] == 'bpatcher' and b['box'].get('name') == 'fs2voice.maxpat']
    assert len(strips) == 4, len(strips)
    for b in strips:
        b['presentation_rect'][2] += GROW
        b['patching_rect'][2] += GROW
    x0 = strips[0]['presentation_rect'][0]
    assert x0 + right <= x0 + strips[0]['presentation_rect'][2], 'la tira quedo corta'

    hdr = box[bv['fs2_hdr12']]
    nx = max(int(i.split('-')[1]) for i in box) + 1
    P['boxes'].append({'box': {
        'id': 'obj-%d' % nx, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
        'varname': 'fs2_hdr13', 'text': 'Desf',
        'patching_rect': [hdr['patching_rect'][0] + 40.0] + hdr['patching_rect'][1:],
        'presentation': 1, 'presentation_rect': [x0 + COL_X, hdr['presentation_rect'][1],
                                                 30.0, hdr['presentation_rect'][3]]}})
    for v in SHIFT:
        box[bv[v]]['presentation_rect'][0] += GROW

    PP = P['parameters']
    ov = PP['parameter_overrides']
    for b in strips:
        ov['%s::%s' % (b['id'], num)] = {'parameter_longname': 'V%d Desf' % b['args'][0]}
        PP['%s::%s' % (b['id'], num)] = ['V#1 Desf', 'V#1 Desf', 0]
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    print('padre: top-level %d, anidados %d, total %d, overrides %d'
          % (len([k for k in PP if k not in meta and '::' not in k]),
             len([k for k in PP if '::' in k]), len([k for k in PP if k not in meta]), len(ov)))

    R = [(b['box'].get('varname') or b['box']['id'], b['box']['presentation_rect'])
         for b in P['boxes'] if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    bad = [(a, c) for a, ra in R for c, rc in R if a < c
           and ra[0] < rc[0] + rc[2] and rc[0] < ra[0] + ra[2]
           and ra[1] < rc[1] + rc[3] and rc[1] < ra[1] + ra[3]]
    assert not bad, bad
    print('presentacion: %.0f x %.0f px, sin solapamientos'
          % (max(r[0] + r[2] for _, r in R), max(r[1] + r[3] for _, r in R)))

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escritos %s y %s' % (VOICE, DEVICE))


main()
