"""Collapse FORTESEQ2's page bpatchers into one, behind a live.tab.

The four pages were migrated one at a time, each keeping the rect its panel used, so the device
never changed shape while the parameters moved. This is the step that cashes that in: the pages
are stacked vertically inside a single patcher, one bpatcher shows a 142 px window onto it, and
the tab slides that window with `script sendbox fs2_pages offset 0 -N`.

    python tools/collapse_pages.py            dry run, writes nothing
    python tools/collapse_pages.py --apply    do it

One bpatcher, not four superposed. A bpatcher swallows the click over its whole rect even where
it draws nothing, so four stacked on one spot would always answer with the topmost one no matter
which page was scrolled into view. With a single bpatcher the question does not arise.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
MERGED = 'fs2pages.maxpat'

# tab order is the order you would touch them in: what set, what may be chosen, how it speaks,
# how it moves. Tiempo joins as a fifth later.
PAGES = [('armonia', 'Armonia'), ('teoria', 'Teoria'),
         ('artic', 'Artic'), ('musical', 'Musical')]

PITCH = 150.0                      # vertical distance between pages inside the merged patcher
WIN = [570.0, 5.0, 516.0, 142.0]   # the window the bpatcher shows, in the parent's presentation
TAB = [504.0, 5.0, 62.0, 142.0]    # taller than wide, which is all a live.tab needs to stack
ROW = 149.0                        # the readout strip, which stays visible on every page
READOUTS = [('fs2_lbl_notas', 504.0), ('fs2_disp_notes', 548.0),
            ('fs2_lbl_midi', 846.0), ('fs2_disp_mon', 890.0)]

INLET_LABELS = ['init', 'eco (salida 4 del js)', 'salida 1 del js', 'salida 7 del js']


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    box = {b['box']['id']: b['box'] for b in P['boxes']}
    byvar = {b.get('varname'): i for i, b in box.items() if b.get('varname')}
    gen, init_box = byvar['fs2_gen'], byvar['fs2_harm_init']

    # ---- merge the four page patchers into one tall one -------------------------------------
    mboxes, mlines, mparams = [], [], {}
    IN = ['obj-1', 'obj-2', 'obj-3', 'obj-4']
    OUT = 'obj-5'
    for k, iid in enumerate(IN):
        mboxes.append({'box': {'id': iid, 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1,
                               'outlettype': [''], 'comment': INLET_LABELS[k],
                               'patching_rect': [20.0 + k * 70.0, 20.0, 30.0, 30.0]}})
    mboxes.append({'box': {'id': OUT, 'maxclass': 'outlet', 'numinlets': 1, 'numoutlets': 0,
                           'comment': 'mensajes hacia [js forteseq2.js]',
                           'patching_rect': [20.0, 90.0, 30.0, 30.0]}})

    nid = [5]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    tall = 0.0
    for k, (key, _) in enumerate(PAGES):
        pg = json.load(open(os.path.join('forteseq', 'fs2page_%s.maxpat' % key),
                            encoding='utf-8'))['patcher']
        pb = {b['box']['id']: b['box'] for b in pg['boxes']}
        pin = sorted([i for i, b in pb.items() if b['maxclass'] == 'inlet'],
                     key=lambda i: pb[i]['patching_rect'][0])
        pout = [i for i, b in pb.items() if b['maxclass'] == 'outlet']
        assert len(pin) <= len(IN) and len(pout) == 1, (key, len(pin), len(pout))
        pout = pout[0]

        mp = {}
        for i, b in pb.items():
            if b['maxclass'] in ('inlet', 'outlet'):
                continue
            b = json.loads(json.dumps(b))
            b['id'] = mp.setdefault(i, fresh())
            b['patching_rect'][1] += 200.0 + k * 700.0
            r = b.get('presentation_rect')
            if b.get('presentation') and r:
                r[1] += k * PITCH
                tall = max(tall, r[1] + r[3])
            mboxes.append({'box': b})
            if i in pg['parameters']:
                mparams[b['id']] = pg['parameters'][i]

        def to(i, port, pin=pin, pout=pout, mp=mp):
            if i in pin:
                return [IN[pin.index(i)], 0]
            if i == pout:
                return [OUT, 0]
            return [mp[i], port]

        for l in pg['lines']:
            a, b2 = l['patchline']['source'], l['patchline']['destination']
            mlines.append({'patchline': {'source': to(a[0], a[1]),
                                         'destination': to(b2[0], b2[1])}})
        print('%-9s pagina %d en y=%-4.0f  %2d cajas  %2d cords  %2d params  %d entradas'
              % (key, k, k * PITCH, len(pb) - len(pin) - 1, len(pg['lines']),
                 len(pg['parameters']), len(pin)))

    merged = {'patcher': {
        'fileversion': 1,
        'appversion': {'major': 9, 'minor': 0, 'revision': 7, 'architecture': 'x64',
                       'modernui': 1},
        'classnamespace': 'box', 'rect': [100.0, 100.0, 1100.0, 800.0],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial Bold',
        'gridsize': [8.0, 8.0], 'boxes': mboxes, 'lines': mlines, 'parameters': mparams,
        'dependency_cache': [], 'autosave': 0}}
    print('')
    print('fundido    %d cajas, %d cords, %d parametros, %.0f px de alto (ventana %.0f)'
          % (len(mboxes), len(mlines), len(mparams), tall, WIN[3]))
    assert tall <= len(PAGES) * PITCH, tall

    # ---- the parent -------------------------------------------------------------------------
    old = [i for i, b in box.items() if str(b.get('varname')).startswith('fs2_page_')]
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in old]
    P['lines'] = [l for l in P['lines'] if l['patchline']['source'][0] not in old
                  and l['patchline']['destination'][0] not in old]

    nxt = [max(int(i.split('-')[1]) for i in box)]

    def newid():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    BP, TABID, SEL, THIS = newid(), newid(), newid(), newid()

    P['boxes'].append({'box': {
        'id': BP, 'maxclass': 'bpatcher', 'name': MERGED, 'varname': 'fs2_pages',
        'numinlets': len(IN), 'numoutlets': 1, 'outlettype': [''], 'offset': [0.0, 0.0],
        'patching_rect': [WIN[0], 700.0, WIN[2], WIN[3]],
        'presentation': 1, 'presentation_rect': list(WIN)}})
    P['boxes'].append({'box': {
        'id': TABID, 'maxclass': 'live.tab', 'varname': 'fs2_pagina',
        'numinlets': 1, 'numoutlets': 3, 'outlettype': ['', '', 'float'], 'parameter_enable': 1,
        'annotation': 'Que panel se ve. Los controles de las paginas ocultas siguen activos: '
                      'la pagina no apaga nada, solo elige que mirar.',
        'patching_rect': [300.0, 700.0, 100.0, 20.0],
        'presentation': 1, 'presentation_rect': list(TAB),
        'saved_attribute_attributes': {'valueof': {
            'parameter_enum': [lab for _, lab in PAGES],
            'parameter_mmax': len(PAGES) - 1, 'parameter_modmode': 0, 'parameter_type': 2,
            'parameter_unitstyle': 9, 'parameter_initial': [0], 'parameter_initial_enable': 1,
            'parameter_longname': 'Pagina', 'parameter_shortname': 'Pagina'}}}})
    P['boxes'].append({'box': {
        'id': SEL, 'maxclass': 'newobj', 'varname': 'fs2_pagina_sel',
        'numinlets': 1, 'numoutlets': len(PAGES) + 1, 'outlettype': [''] * (len(PAGES) + 1),
        'patching_rect': [300.0, 740.0, 120.0, 22.0],
        'text': 'sel ' + ' '.join(str(k) for k in range(len(PAGES)))}})
    P['boxes'].append({'box': {
        'id': THIS, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 2,
        'outlettype': ['', ''], 'patching_rect': [300.0, 830.0, 80.0, 22.0],
        'text': 'thispatcher'}})

    def mk(a, b2, c, d):
        return {'patchline': {'source': [a, b2], 'destination': [c, d]}}

    for k in range(len(PAGES)):
        mid = newid()
        P['boxes'].append({'box': {
            'id': mid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
            'patching_rect': [300.0 + k * 200.0, 785.0, 190.0, 22.0],
            'text': 'script sendbox fs2_pages offset 0 %d' % int(-k * PITCH)}})
        P['lines'].append(mk(SEL, k, mid, 0))
        P['lines'].append(mk(mid, 0, THIS, 0))
    P['lines'].append(mk(TABID, 0, SEL, 0))
    P['lines'].append(mk(init_box, 0, TABID, 0))
    P['lines'].append(mk(init_box, 0, BP, 0))
    P['lines'].append(mk(gen, 4, BP, 1))
    P['lines'].append(mk(gen, 1, BP, 2))
    P['lines'].append(mk(gen, 7, BP, 3))
    P['lines'].append(mk(BP, 0, gen, 0))

    for var, x in READOUTS:
        r = box[byvar[var]]['presentation_rect']
        r[0], r[1] = x, ROW

    # ---- parameters -------------------------------------------------------------------------
    PP = P['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    for key in [k for k in PP if '::' in k and k.split('::')[0] in old]:
        del PP[key]
    for pid, val in mparams.items():
        PP['%s::%s' % (BP, pid)] = val
    PP[TABID] = ['Pagina', 'Pagina', 0]
    top = [k for k in PP if k not in meta and '::' not in k]
    run = byvar['fs2_run']
    ordered = sorted([k for k in top if k != run],
                     key=lambda k: 1e9 if k == TABID else PP[k][2]) + [run]
    now = {b['box']['id']: b['box'] for b in P['boxes']}
    for rank, k in enumerate(ordered):
        PP[k][2] = rank
        now[k]['saved_attribute_attributes']['valueof']['parameter_order'] = rank
    print('top-level  %d parametros (%s), anidados %d, total %d'
          % (len(top), ' '.join(PP[k][0] for k in ordered),
             len([k for k in PP if '::' in k]), len([k for k in PP if k not in meta])))
    names = {v[0] for k, v in PP.items() if k not in meta}
    assert not [(b['name'], p) for b in PP['parameterbanks'].values()
                for p in b['parameters'] if p != '-' and p not in names]

    dc = P.setdefault('dependency_cache', [])
    sib = next(x for x in dc if x['name'] == 'fs2voice.maxpat')
    P['dependency_cache'] = [x for x in dc if not x['name'].startswith('fs2page_')]
    P['dependency_cache'].append({'name': MERGED, 'bootpath': sib['bootpath'],
                                  'type': 'JSON', 'implicit': 1})

    width = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
                for b in P['boxes']
                if b['box'].get('presentation') and b['box'].get('presentation_rect'))
    print('ancho de la presentacion: 1442 -> %.0f px' % width)

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    with open(os.path.join('forteseq', MERGED), 'w', encoding='utf-8', newline='') as f:
        json.dump(merged, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escritos forteseq/%s y %s' % (MERGED, DEVICE))


main()
