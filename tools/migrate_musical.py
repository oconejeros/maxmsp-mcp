"""Move the Musical block (presentation x >= 1130) of FORTESEQ2 into a bpatcher page.

This is the first of the page migrations. It deliberately changes NOTHING about how the device
looks: the bpatcher sits exactly where the block sat and its offset stays [0, 0], so the only
thing that moves is where those objects live in the file. Paging proper -- a live.tab driving
`script sendbox <bp> offset 0 -164` -- comes after this one is confirmed in Live.

What makes the block a clean first candidate: all 23 of its helper objects (the `prepend`s and
the action messages) are fed ONLY by boxes inside the block, so the whole thing collapses to a
single outlet. Incoming there are four sources, which become two inlets:

    inlet 0  the `outputvalue` init bang, fanned to every parameter except Fav -- Fav describes
             what is sounding rather than holding state of its own, so it must not be re-emitted
             at load (see the forteseq-engine-roadmap note).
    inlet 1  the raw tagged stream from js outlet 4, routed inside the page for its own tags.
             Fed straight from the js rather than from fs2_echo's outlets, because extending or
             renumbering that 25-argument route would move every cord already attached to it.
             fs2_echo keeps its arguments and simply stops having anything wired to the ten
             outlets this page took over.

    python tools/migrate_musical.py           dry run: prints the plan, writes nothing
    python tools/migrate_musical.py --apply   do it

Close the device in BOTH Max and Live first; whichever saves last wins.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PAGE = os.path.join('forteseq', 'fs2page_musical.maxpat')
X0, Y0 = 1130.0, 5.0          # where the block starts in the parent's presentation
PAGE_W, PAGE_H = 312.0, 159.0

# The tags this page owns on js outlet 4. Everything else keeps going to fs2_echo.
ECHO_TAGS = ['drum', 'drumbase', 'harmrate', 'rootseq', 'voicing',
             'voicelead', 'fav', 'favonly', 'vecmin', 'vecmax']


def load():
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    box = {b['box']['id']: b['box'] for b in P['boxes']}
    return data, s, e, doc, P, box


def collect(P, box):
    """The block, its helpers, and the two unpacks that serve only it."""
    region = {i for i, b in box.items()
              if b.get('presentation') and b.get('presentation_rect')
              and b['presentation_rect'][0] >= X0}
    cords = [l['patchline'] for l in P['lines']]

    helpers = set()
    for c in cords:
        sid, did = c['source'][0], c['destination'][0]
        if sid in region and did not in region:
            feeders = {x['source'][0] for x in cords if x['destination'][0] == did}
            assert feeders <= region, 'helper %s also fed from outside' % did
            helpers.add(did)

    unpacks = {i for i, b in box.items()
               if b.get('varname') in ('fs2_vecmin_unp', 'fs2_vecmax_unp')}
    return region, helpers, unpacks, cords


def is_param(b):
    return bool((b.get('saved_attribute_attributes') or {}).get('valueof'))


def build_page(box, moving, region, cords):
    """The new .maxpat. Ids are renumbered; old id -> new id is returned for the cord rewrite."""
    boxes, lines, params = [], [], {}
    newid, order = {}, []
    n = 4                                   # 1..3 are the inlets and the outlet

    for old in sorted(moving, key=lambda i: (box[i].get('presentation_rect') or [9e9])[0]):
        n += 1
        newid[old] = 'obj-%d' % n
        order.append(old)

    def add(b):
        boxes.append({'box': b})

    add({'id': 'obj-1', 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1,
         'outlettype': [''], 'patching_rect': [20.0, 20.0, 30.0, 30.0],
         'comment': 'init: re-emite el estado de los controles hacia el motor'})
    add({'id': 'obj-2', 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1,
         'outlettype': [''], 'patching_rect': [90.0, 20.0, 30.0, 30.0],
         'comment': 'eco: la salida 4 del js, cruda; el route de abajo toma lo suyo'})
    add({'id': 'obj-3', 'maxclass': 'outlet', 'numinlets': 1, 'numoutlets': 0,
         'patching_rect': [20.0, 620.0, 30.0, 30.0],
         'comment': 'mensajes hacia [js forteseq2.js]'})
    add({'id': 'obj-4', 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1,
         'outlettype': [''], 'patching_rect': [20.0, 70.0, 70.0, 22.0],
         'text': 'outputvalue', 'varname': 'pg_init'})
    lines.append({'patchline': {'source': ['obj-1', 0], 'destination': ['obj-4', 0]}})

    rt = 'obj-%d' % (n + 1)
    add({'id': rt, 'maxclass': 'newobj', 'numinlets': 1,
         'numoutlets': len(ECHO_TAGS) + 1, 'outlettype': [''] * (len(ECHO_TAGS) + 1),
         'patching_rect': [90.0, 70.0, 520.0, 22.0],
         'text': 'route ' + ' '.join(ECHO_TAGS), 'varname': 'pg_echo'})
    lines.append({'patchline': {'source': ['obj-2', 0], 'destination': [rt, 0]}})

    # the moved boxes, presentation shifted so the block's top-left becomes the page's
    for k, old in enumerate(order):
        b = json.loads(json.dumps(box[old]))         # deep copy
        b['id'] = newid[old]
        if b.get('presentation') and b.get('presentation_rect'):
            r = b['presentation_rect']
            b['presentation_rect'] = [r[0] - X0, r[1] - Y0, r[2], r[3]]
            b['patching_rect'] = [r[0] - X0 + 20.0, r[1] - Y0 + 140.0, r[2], r[3]]
        else:
            b['patching_rect'] = [20.0 + (k % 8) * 96.0, 330.0 + (k // 8) * 40.0, 92.0, 22.0]
        b.pop('presentation_position', None)
        b.pop('patching_position', None)
        add(b)
        vo = (b.get('saved_attribute_attributes') or {}).get('valueof')
        if vo:
            # Inside a bpatcher a parameter's order is local and irrelevant, so 0 for all of them,
            # exactly as fs2voice.maxpat has it. The long name carries no #1 here, so the resolved
            # name and the template name are the same string and no override is needed.
            vo.pop('parameter_order', None)
            nm = vo['parameter_longname']
            params[b['id']] = [nm, nm, 0]

    # every cord that lived entirely inside what moved
    for c in cords:
        sid, so = c['source']
        did, di = c['destination']
        if sid in newid and did in newid:
            lines.append({'patchline': {'source': [newid[sid], so],
                                        'destination': [newid[did], di]}})

    # helpers and action messages now report to the outlet
    for old in order:
        b = box[old]
        if old in region:
            continue
        if any(c['source'][0] == old and c['destination'][0] not in newid for c in cords):
            lines.append({'patchline': {'source': [newid[old], 0], 'destination': ['obj-3', 0]}})

    # init fan-out, and the echo route back to each control
    init_targets, echo_map = [], {}
    for c in cords:
        sid, did = c['source'][0], c['destination'][0]
        src = box[sid].get('varname')
        if did in newid:
            if src == 'fs2_harm_init':
                init_targets.append(newid[did])
            elif src == 'fs2_echo':
                echo_map[c['source'][1]] = newid[did]
    for t in init_targets:
        lines.append({'patchline': {'source': ['obj-4', 0], 'destination': [t, 0]}})

    ECHO_OUT = {'drum': 'fs2_drum', 'drumbase': 'fs2_pad', 'harmrate': 'fs2_rarm',
                'rootseq': 'fs2_rseq', 'voicing': 'fs2_voic', 'voicelead': 'fs2_cond',
                'fav': 'fs2_fav', 'favonly': 'fs2_favonly',
                'vecmin': 'fs2_vecmin_unp', 'vecmax': 'fs2_vecmax_unp'}
    byvar = {b.get('varname'): i for i, b in box.items() if b.get('varname')}
    for k, tag in enumerate(ECHO_TAGS):
        dst = newid[byvar[ECHO_OUT[tag]]]
        lines.append({'patchline': {'source': [rt, k], 'destination': [dst, 0]}})

    page = {'patcher': {
        'fileversion': 1,
        'appversion': {'major': 9, 'minor': 0, 'revision': 7,
                       'architecture': 'x64', 'modernui': 1},
        'classnamespace': 'box',
        'rect': [100.0, 100.0, 960.0, 700.0],
        'openinpresentation': 1,
        'default_fontsize': 10.0,
        'default_fontname': 'Arial Bold',
        'gridsize': [8.0, 8.0],
        'boxes': boxes,
        'lines': lines,
        'parameters': params,
        'dependency_cache': [],
        'autosave': 0}}
    return page, newid, init_targets


def main():
    apply = '--apply' in sys.argv
    data, s, e, doc, P, box = load()
    region, helpers, unpacks, cords = collect(P, box)
    moving = region | helpers | unpacks
    params_moving = [i for i in region if is_param(box[i])]

    print('bloque      %3d cajas' % len(region))
    print('auxiliares  %3d (prepends y mensajes, alimentados solo por el bloque)' % len(helpers))
    print('unpacks     %3d' % len(unpacks))
    print('se mudan    %3d cajas en total, de las cuales %d son parametros'
          % (len(moving), len(params_moving)))

    page, newid, init_targets = build_page(box, moving, region, cords)
    print('pagina      %d cajas, %d cords, %d parametros anidados'
          % (len(page['patcher']['boxes']), len(page['patcher']['lines']),
             len(page['patcher']['parameters'])))
    print('init        %d controles reciben el outputvalue (Fav queda afuera a proposito)'
          % len(init_targets))

    # ---- the parent -------------------------------------------------------------------------
    bpid = 'obj-%d' % (max(int(i.split('-')[1]) for i in box) + 1)
    kept_lines = [l for l in P['lines']
                  if l['patchline']['source'][0] not in moving
                  and l['patchline']['destination'][0] not in moving]
    byvar = {b.get('varname'): i for i, b in box.items() if b.get('varname')}

    newboxes = [b for b in P['boxes'] if b['box']['id'] not in moving]
    newboxes.append({'box': {
        'id': bpid, 'maxclass': 'bpatcher', 'name': 'fs2page_musical.maxpat',
        'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'offset': [0.0, 0.0], 'varname': 'fs2_page_musical',
        'patching_rect': [1130.0, 560.0, PAGE_W, PAGE_H],
        'presentation': 1, 'presentation_rect': [X0, Y0, PAGE_W, PAGE_H]}})
    mk = lambda a, b, c, d: {'patchline': {'source': [a, b], 'destination': [c, d]}}
    kept_lines.append(mk(byvar['fs2_harm_init'], 0, bpid, 0))
    kept_lines.append(mk(byvar['fs2_gen'], 4, bpid, 1))
    kept_lines.append(mk(bpid, 0, byvar['fs2_gen'], 0))

    # registries: the moved parameters leave the top level and reappear nested
    PP = P['parameters']
    for i in params_moving:
        assert i in PP, i
        del PP[i]
    for old, new in newid.items():
        if old in params_moving:
            PP['%s::%s' % (bpid, new)] = page['patcher']['parameters'][new]

    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    top = [k for k in PP if k not in meta and '::' not in k]
    ordered = sorted(top, key=lambda k: PP[k][2])
    for rank, k in enumerate(ordered):
        PP[k][2] = rank
        vo = box[k]['saved_attribute_attributes']['valueof']
        vo['parameter_order'] = rank
    # Max keeps an implicit dependency entry per referenced file. The page is a sibling of the
    # .amxd so Max would resolve it from the patcher's own folder anyway, but declaring it keeps
    # the cache honest and matches how forteseq2.js and fs2voice.maxpat are already listed.
    dc = P.setdefault('dependency_cache', [])
    if not any(x.get('name') == 'fs2page_musical.maxpat' for x in dc):
        sib = next(x for x in dc if x['name'] == 'fs2voice.maxpat')
        dc.append({'name': 'fs2page_musical.maxpat', 'bootpath': sib['bootpath'],
                   'type': 'JSON', 'implicit': 1})

    print('top-level   %d parametros, renumerados 0..%d' % (len(top), len(top) - 1))
    print('anidados    %d nuevos bajo %s' % (len(params_moving), bpid))
    print('cords       %d -> %d' % (len(P['lines']), len(kept_lines)))
    print('cajas       %d -> %d' % (len(P['boxes']), len(newboxes)))

    if not apply:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    P['boxes'] = newboxes
    P['lines'] = kept_lines
    with open(PAGE, 'w', encoding='utf-8', newline='') as f:
        json.dump(page, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('\nescritos %s y %s' % (PAGE, DEVICE))


main()
