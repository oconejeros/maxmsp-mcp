"""Give every voice its own articulation selector, and its own reading order.

Both are per-voice overrides of something that used to be global only: articulation (Vel Min/Max,
Figura, Silencio) was two shared bands (Normal/Acento); reading order (Patron/Dir) was one shared
choice for the whole ensemble. Each gets a "Propia" toggle -- off by default, which is what makes
this a pure addition: with every voice on Grupo/Global the device sounds exactly as it did before
this script ran, verified by forteseq2.js's own regression harness (checkVoiceArt/checkVoiceReadOrder,
plus the untouched golden.txt).

    python tools/add_voice_art.py            dry run, writes nothing
    python tools/add_voice_art.py --apply    do it

Eight new controls land in fs2voice.maxpat's strip (so all four voices get them at once), which is
what pushes FORTESEQ2.amxd's voice-strip block wider and shoves the harmony/timbre pages the same
amount to the right -- the same growth pattern add_desf.py already used for Desf.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE = os.path.join('forteseq', 'fs2voice.maxpat')

READ_ENUM = ['Normal', 'Super', 'Minima', 'Modos', 'Coprimo', 'Zigzag', 'Urna']
DIR_ENUM = ['Adel', 'Atras', 'Alt']

ART_ANN = ('Si esta prendido, esta voz deja de mirar las bandas Normal/Acento y usa su propia '
           'velocidad, figura y silencio -- las cuatro de al lado. Apagado (por defecto) es '
           'exactamente el comportamiento de siempre.')
VELMIN_ANN = 'Velocidad minima de esta voz, cuando Propia esta prendido.'
VELMAX_ANN = 'Velocidad maxima de esta voz, cuando Propia esta prendido.'
FIGURA_ANN = ('Duracion de esta voz como denominador de figura (4=negra, 8=corchea, '
              '16=semicorchea), cuando Propia esta prendido.')
SILENCIO_ANN = 'Probabilidad de silencio de esta voz, en %, cuando Propia esta prendido.'
READOWN_ANN = ('Si esta prendido, esta voz deja de mirar Patron/Dir Lectura globales y usa los '
               'suyos propios -- solo tiene efecto bajo Voces Indep o disparo externo, que es '
               'donde cada voz ya tiene su propio cursor. Apagado (por defecto) es exactamente '
               'el comportamiento de siempre.')
PATRON_ANN = 'Orden de lectura propio de esta voz, cuando Propia esta prendido.'
DIR_ANN = 'Direccion de lectura propia de esta voz, cuando Propia esta prendido.'

# (varname, header label, width, header text-width, kind, longname, shortname, valueof extras)
# kind: 'toggle' | 'num' | 'enum'
CONTROLS = [
    ('v_artown', 'ArtP', 14.0, 26.0, 'toggle', 'V#1 ArtProp', 'ArtProp', ART_ANN, None),
    ('v_velmin', 'VMin', 34.0, 32.0, 'num', 'V#1 VelMin', 'VelMin', VELMIN_ANN, (1.0, 127.0, 55)),
    ('v_velmax', 'VMax', 34.0, 32.0, 'num', 'V#1 VelMax', 'VelMax', VELMAX_ANN, (1.0, 127.0, 80)),
    ('v_figura', 'Fig', 30.0, 24.0, 'num', 'V#1 Figura', 'Figura', FIGURA_ANN, (1.0, 32.0, 16)),
    ('v_silencio', 'Sil', 34.0, 24.0, 'num', 'V#1 Silencio', 'Silenc', SILENCIO_ANN, (0.0, 100.0, 0)),
    ('v_readown', 'LecP', 14.0, 26.0, 'toggle', 'V#1 LecProp', 'LecProp', READOWN_ANN, None),
    ('v_patron', 'Patr', 44.0, 28.0, 'enum', 'V#1 Patron', 'Patron', PATRON_ANN, READ_ENUM),
    ('v_dir', 'Dir', 34.0, 22.0, 'enum', 'V#1 Dir', 'Dir', DIR_ANN, DIR_ENUM),
]
GAP = 4.0
SETTERS = {
    'v_artown': 'setvoiceartown', 'v_readown': 'setvoicereadown',
    'v_patron': 'setvoicereadmode', 'v_dir': 'setvoicereaddir',
}


def main():
    apply_it = '--apply' in sys.argv

    # ---- the strip -----------------------------------------------------------------------------
    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pb = {b['box']['id']: b['box'] for b in pg['boxes']}
    byvar = {b.get('varname'): i for i, b in pb.items() if b.get('varname')}
    assert 'v_artown' not in byvar, 'ya esta puesto'
    out = [i for i, b in pb.items() if b['maxclass'] == 'outlet'][0]
    init = byvar['v_init_msg']
    right0 = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
                 for b in pg['boxes'] if b['box'].get('presentation'))
    nxt = [max(int(i.split('-')[1]) for i in pb)]

    def fresh():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    add, wire, params = [], [], {}

    def box(**kw):
        b = dict(kw)
        b.setdefault('id', fresh())
        add.append({'box': b})
        return b['id']

    def link(a, c, ao=0, ci=0):
        wire.append({'patchline': {'source': [a, ao], 'destination': [c, ci]}})

    x = right0 + GAP
    ids = {}
    y_ui, y_helper = 4.0, 380.0
    for i, (var, hdr, w, hw, kind, longname, shortname, ann, extra) in enumerate(CONTROLS):
        if kind == 'toggle':
            vid = box(maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
                      parameter_enable=1, varname=var, annotation=ann,
                      patching_rect=[500.0 + i * 40.0, y_ui + 60.0, w, w],
                      presentation=1, presentation_rect=[x, y_ui, w, w],
                      saved_attribute_attributes={'valueof': {
                          'parameter_longname': longname, 'parameter_shortname': shortname,
                          'parameter_type': 2, 'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
                          'parameter_modmode': 0, 'parameter_initial': [0],
                          'parameter_initial_enable': 1}})
        elif kind == 'num':
            mmin, mmax, initial = extra
            vid = box(maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
                      parameter_enable=1, varname=var, annotation=ann,
                      patching_rect=[500.0 + i * 40.0, y_ui + 60.0, w, 15.0],
                      presentation=1, presentation_rect=[x, y_ui, w, 15.0],
                      saved_attribute_attributes={'valueof': {
                          'parameter_longname': longname, 'parameter_shortname': shortname,
                          'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_modmode': 4,
                          'parameter_mmin': mmin, 'parameter_mmax': mmax,
                          'parameter_initial': [initial], 'parameter_initial_enable': 1}})
        else:  # enum, shown as a live.numbox with unit style 9 (name instead of number)
            enum = extra
            vid = box(maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
                      parameter_enable=1, varname=var, annotation=ann,
                      patching_rect=[500.0 + i * 40.0, y_ui + 60.0, w, 15.0],
                      presentation=1, presentation_rect=[x, y_ui, w, 15.0],
                      saved_attribute_attributes={'valueof': {
                          'parameter_longname': longname, 'parameter_shortname': shortname,
                          'parameter_type': 2, 'parameter_unitstyle': 9, 'parameter_enum': enum,
                          'parameter_mmax': len(enum) - 1, 'parameter_modmode': 0,
                          'parameter_initial': [0], 'parameter_initial_enable': 1}})
        ids[var] = vid
        params[vid] = [longname, longname, 0]
        link(init, vid)   # every control speaks on load, same as v_min/v_span both do today
        x += max(w, hw) + GAP   # the column pitch, wide enough for the header label too

    # Direct setters: the toggles and the two reading-order numboxes each send their own message.
    for var in ('v_artown', 'v_readown', 'v_patron', 'v_dir'):
        prep = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                   varname=var + '_prep', patching_rect=[500.0, y_helper, 220.0, 22.0],
                   text='prepend %s #1' % SETTERS[var])
        link(ids[var], prep)
        link(prep, out)
        y_helper += 30.0

    # Articulation: four values into one pak (any inlet re-outputs the whole set, so the four
    # dials don't need the trigger-order dance a pack would) -> one setter.
    pak = box(maxclass='newobj', numinlets=4, numoutlets=1, outlettype=[''],
              varname='v_art_pak', patching_rect=[500.0, y_helper, 150.0, 22.0],
              text='pak 55 80 16 0')
    art_prep = box(maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                   varname='v_art_prep', patching_rect=[500.0, y_helper + 30.0, 220.0, 22.0],
                   text='prepend setvoicearticulation #1')
    for inlet, var in enumerate(('v_velmin', 'v_velmax', 'v_figura', 'v_silencio')):
        link(ids[var], pak, ci=inlet)
    link(pak, art_prep)
    link(art_prep, out)

    pg['boxes'].extend(add)
    pg['lines'].extend(wire)
    pg['parameters'].update(params)
    right = x - GAP
    print('tira: %d parametros nuevos, contenido llega a x=%.0f (era %.0f)' %
          (len(params), right, right0))

    # ---- the parent ------------------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    box_ = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in box_.items() if b.get('varname')}

    strips = [b['box'] for b in P['boxes']
              if b['box']['maxclass'] == 'bpatcher' and b['box'].get('name') == 'fs2voice.maxpat']
    assert len(strips) == 4, len(strips)
    x0 = strips[0]['presentation_rect'][0]
    grow = (x0 + right) - (strips[0]['presentation_rect'][0] + strips[0]['presentation_rect'][2])
    if grow < 0:
        grow = 0.0   # the box already had slack; nothing to grow
    for b in strips:
        b['presentation_rect'][2] += grow
        b['patching_rect'][2] += grow
    assert x0 + right <= x0 + strips[0]['presentation_rect'][2], 'la tira quedo corta'

    # Header row: one short label per new control, at the same +4px offset the existing headers use.
    hdrs = [v for v in bv if v and v.startswith('fs2_hdr')]
    hdr_n = max(int(v.replace('fs2_hdr', '')) for v in hdrs)
    hdr_ref = box_[bv['fs2_hdr1']]
    nid = [max(int(i.split('-')[1]) for i in box_)]

    def pfresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    hx = x0 + right0 + GAP
    for i, (var, hdr, w, hw, kind, *_rest) in enumerate(CONTROLS):
        hdr_n += 1
        P['boxes'].append({'box': {
            'id': pfresh(), 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
            'varname': 'fs2_hdr%d' % hdr_n, 'text': hdr,
            'patching_rect': [hdr_ref['patching_rect'][0] + 40.0 * (12 + i)] + hdr_ref['patching_rect'][1:],
            'presentation': 1,
            'presentation_rect': [hx, hdr_ref['presentation_rect'][1], hw, hdr_ref['presentation_rect'][3]]}})
        hx += max(w, hw) + GAP

    # Everything to the right of the voice-strip block slides over by `grow` -- found by position,
    # not by a fixed varname list: several objects here (the index/Forte readouts under the
    # strips, the monitor toggle) carry no varname at all, and a hardcoded list from an earlier
    # layout (collapse_pages.py, move_readouts.py) is exactly the kind of thing that goes stale.
    strip_right = strips[0]['presentation_rect'][0] + (strips[0]['presentation_rect'][2] - grow)
    strip_ids = {b['id'] for b in strips}
    shifted = 0
    for b in P['boxes']:
        bx = b['box']
        pr = bx.get('presentation_rect')
        if not pr or not bx.get('presentation') or bx['id'] in strip_ids:
            continue
        if bx.get('varname', '').startswith('fs2_hdr'):
            continue   # the new headers were already placed at their final x
        if pr[0] >= strip_right - 2.0:
            pr[0] += grow
            shifted += 1

    PP = P['parameters']
    ov = PP['parameter_overrides']
    for b in strips:
        voice_n = b['args'][0]
        for var, *_r in CONTROLS:
            vid = ids[var]
            longname = params[vid][0]
            ov['%s::%s' % (b['id'], vid)] = {
                'parameter_longname': longname.replace('V#1', 'V%d' % voice_n)}
            PP['%s::%s' % (b['id'], vid)] = [longname, longname, 0]
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    print('padre: top-level %d, anidados %d, total %d, overrides %d, crecimiento %.0fpx'
          % (len([k for k in PP if k not in meta and '::' not in k]),
             len([k for k in PP if '::' in k]), len([k for k in PP if k not in meta]),
             len(ov), grow))

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
