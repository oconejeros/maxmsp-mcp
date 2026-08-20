"""Move one panel of FORTESEQ2's presentation into a bpatcher page.

Generalised from the one-off that moved the Musical block (601bf27). Each migration is
deliberately invisible: the bpatcher takes the exact presentation rect the panel occupied and its
offset stays [0,0], so the device looks identical in Live. Collapsing the pages onto one position
behind a live.tab is a separate, later step -- and by then it is pure geometry, with no parameter
churn left to get wrong.

    python tools/migrate_page.py <pagina>            dry run, writes nothing
    python tools/migrate_page.py <pagina> --apply    do it

Close the device in BOTH Max and Live first; whichever saves last wins.

Everything the panel needs is discovered from the patch rather than listed here, so the config
below is only a name and a rectangle:

  * HELPERS -- the prepends and action messages downstream of the panel. Asserted to be fed ONLY
    from inside it, which is what lets the whole panel leave through a single outlet.
  * ADOPTED -- boxes outside the rectangle that serve nothing but it: the accent-grid and vector
    `unpack`s hanging off fs2_echo, and the `prepend set` that drives a readout comment.
  * EXTRA INLETS -- anything else in the parent that still has to reach inside (the js outlets that
    feed the readouts). One inlet per source outlet, placed left to right, because a bpatcher
    orders its inlets by the horizontal position of the `inlet` objects.
  * The echo map -- read off fs2_echo's own arguments and cords, so the page's internal route gets
    exactly the tags that reached this panel before and no others. fs2_echo keeps its arguments;
    the outlets the page took over simply stop having anything wired to them.
  * The init fan-out -- copied from whatever fs2_harm_init already fed. That matters: some
    controls are deliberately NOT on it (Fav describes what is sounding; Rango and Preset Silencio
    write other parameters), and deriving the list keeps those exclusions without restating them.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

PAGES = {
    # name: (file, x_min, x_max_excl, y_min, y_max_excl, page width, page height)
    'musical': ('fs2page_musical.maxpat', 1130.0, 1e9,   -1e9, 1e9,  312.0, 159.0),
    'artic':   ('fs2page_artic.maxpat',    856.0, 1125.0, -1e9, 146.0, 258.0, 159.0),
    'teoria':  ('fs2page_teoria.maxpat',   756.0, 1e9,    140.0, 1e9,  365.0,  18.0),
    'armonia': ('fs2page_armonia.maxpat',  512.0, 856.0, -1e9, 126.0, 340.0, 119.0),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PAGES:
        print('paginas: ' + ', '.join(sorted(PAGES)))
        return
    key = sys.argv[1]
    apply_it = '--apply' in sys.argv
    fname, xmin, xmax, ymin, ymax, PW, PH = PAGES[key]
    page_path = os.path.join('forteseq', fname)

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    box = {b['box']['id']: b['box'] for b in P['boxes']}
    byvar = {b.get('varname'): i for i, b in box.items() if b.get('varname')}
    cords = [l['patchline'] for l in P['lines']]
    nm = lambda i: box[i].get('varname') or i

    region = set()
    for i, b in box.items():
        if b.get('maxclass') == 'bpatcher':
            continue                       # a page already
        r = b.get('presentation_rect')
        if b.get('presentation') and r and xmin <= r[0] < xmax and ymin <= r[1] < ymax:
            region.add(i)
    assert region, 'the rectangle caught nothing'

    echo = byvar['fs2_echo']
    echo_args = box[echo]['text'].split()[1:]

    init_box = byvar['fs2_harm_init']

    # boxes upstream of the panel that serve nothing else: the unpacks hanging off fs2_echo, and
    # the `prepend set` that drives a readout. Grown to a fixed point so a chain comes along whole.
    adopted = set()
    while True:
        grew = False
        for mid in box:
            if mid in region or mid in adopted or mid in (echo, init_box):
                continue
            outs = {x['destination'][0] for x in cords if x['source'][0] == mid}
            if outs and outs <= region | adopted:
                adopted.add(mid)
                grew = True
        if not grew:
            break

    # Downstream helpers: a box comes along when everything feeding it is already inside. Grown to
    # a fixed point, because these run in chains -- a `pak` of toggles feeds the `prepend` that
    # names the message, and taking only the first hop leaves the prepend orphaned in the parent
    # while the page shouts a bare list at the js. (That is exactly what happened to the accent
    # grid in 545da81.) Whatever the page still reaches afterwards is its real boundary, and the
    # only thing it is allowed to be is the js itself.
    helpers = set()
    while True:
        inside = region | adopted | helpers
        grew = False
        for c in cords:
            sid, did = c['source'][0], c['destination'][0]
            if sid in inside and did not in inside:
                feeders = {x['source'][0] for x in cords if x['destination'][0] == did}
                if feeders <= inside:
                    helpers.add(did)
                    grew = True
        if not grew:
            break
    inside = region | adopted | helpers
    boundary = {c['destination'][0] for c in cords
                if c['source'][0] in inside and c['destination'][0] not in inside}
    assert boundary <= {byvar['fs2_gen']}, \
        'la pagina sale hacia %s, que no es el js' % [nm(i) for i in boundary]

    moving = region | adopted | helpers
    params_moving = [i for i in moving
                     if (box[i].get('saved_attribute_attributes') or {}).get('valueof')]

    # whatever else in the parent still has to reach inside: one extra inlet per source outlet
    extern = []
    for c in cords:
        sid, so = c['source']
        if c['destination'][0] in moving and sid not in moving and sid not in (echo, init_box):
            if (sid, so) not in extern:
                extern.append((sid, so))

    X0 = min(box[i]['presentation_rect'][0] for i in region)
    Y0 = min(box[i]['presentation_rect'][1] for i in region)

    print('%-11s %3d cajas en el rectangulo' % (key, len(region)))
    print('adoptadas   %3d (entre fs2_echo y el panel)   %s'
          % (len(adopted), ', '.join(sorted(nm(i) for i in adopted)) or '-'))
    print('auxiliares  %3d (prepends y mensajes aguas abajo)' % len(helpers))
    print('se mudan    %3d cajas, de las cuales %d son parametros' % (len(moving), len(params_moving)))
    print('entradas    %3d extra: %s'
          % (len(extern), ', '.join('%s out%d' % (nm(s), o) for s, o in extern) or '-'))
    print('origen      x=%.0f y=%.0f, pagina de %.0fx%.0f' % (X0, Y0, PW, PH))

    # ---- build the page ---------------------------------------------------------------------
    newid, order = {}, []
    n = 4
    for old in sorted(moving, key=lambda i: (box[i].get('presentation_rect') or [9e9])[0]):
        n += 1
        newid[old] = 'obj-%d' % n
        order.append(old)
    rt = 'obj-%d' % (n + 1)

    tags, echo_dst = [], {}
    for c in cords:
        if c['source'][0] == echo and c['destination'][0] in newid:
            tag = echo_args[c['source'][1]]
            tags.append(tag)
            echo_dst[tag] = newid[c['destination'][0]]
    print('eco         %d tags: %s' % (len(tags), ' '.join(tags)))

    boxes, lines, params = [], [], {}
    add = lambda b: boxes.append({'box': b})
    add({'id': 'obj-1', 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
         'patching_rect': [20.0, 20.0, 30.0, 30.0],
         'comment': 'init: re-emite el estado de los controles hacia el motor'})
    add({'id': 'obj-2', 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
         'patching_rect': [90.0, 20.0, 30.0, 30.0],
         'comment': 'eco: la salida 4 del js, cruda; el route de abajo toma lo suyo'})
    add({'id': 'obj-3', 'maxclass': 'outlet', 'numinlets': 1, 'numoutlets': 0,
         'patching_rect': [20.0, 620.0, 30.0, 30.0],
         'comment': 'mensajes hacia [js forteseq2.js]'})
    add({'id': 'obj-4', 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
         'patching_rect': [20.0, 70.0, 70.0, 22.0], 'text': 'outputvalue', 'varname': 'pg_init'})
    lines.append({'patchline': {'source': ['obj-1', 0], 'destination': ['obj-4', 0]}})
    if tags:
        add({'id': rt, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': len(tags) + 1,
             'outlettype': [''] * (len(tags) + 1), 'patching_rect': [90.0, 70.0, 520.0, 22.0],
             'text': 'route ' + ' '.join(tags), 'varname': 'pg_echo'})
        lines.append({'patchline': {'source': ['obj-2', 0], 'destination': [rt, 0]}})

    xin = {}
    for k, (sid, so) in enumerate(extern):
        iid = 'obj-%d' % (n + 2 + k)
        add({'id': iid, 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
             'patching_rect': [160.0 + k * 70.0, 20.0, 30.0, 30.0],
             'comment': '%s, salida %d' % (nm(sid), so)})
        xin[(sid, so)] = iid

    for k, old in enumerate(order):
        b = json.loads(json.dumps(box[old]))
        b['id'] = newid[old]
        r = b.get('presentation_rect')
        if b.get('presentation') and r:
            b['presentation_rect'] = [r[0] - X0, r[1] - Y0, r[2], r[3]]
            b['patching_rect'] = [r[0] - X0 + 20.0, r[1] - Y0 + 150.0, r[2], r[3]]
        else:
            b['patching_rect'] = [20.0 + (k % 8) * 96.0, 340.0 + (k // 8) * 40.0, 92.0, 22.0]
        b.pop('presentation_position', None)
        b.pop('patching_position', None)
        add(b)
        vo = (b.get('saved_attribute_attributes') or {}).get('valueof')
        if vo:
            vo.pop('parameter_order', None)   # inside a bpatcher the order is local and unused
            params[b['id']] = [vo['parameter_longname'], vo['parameter_longname'], 0]

    for c in cords:
        sid, so = c['source']
        did, di = c['destination']
        if sid in newid and did in newid:
            lines.append({'patchline': {'source': [newid[sid], so], 'destination': [newid[did], di]}})

    for old in order:
        if any(c['source'][0] == old and c['destination'][0] not in newid for c in cords):
            lines.append({'patchline': {'source': [newid[old], 0], 'destination': ['obj-3', 0]}})

    init = [newid[c['destination'][0]] for c in cords
            if c['source'][0] == byvar['fs2_harm_init'] and c['destination'][0] in newid]
    for t in init:
        lines.append({'patchline': {'source': ['obj-4', 0], 'destination': [t, 0]}})
    for k, tag in enumerate(tags):
        lines.append({'patchline': {'source': [rt, k], 'destination': [echo_dst[tag], 0]}})
    for c in cords:
        key_ = (c['source'][0], c['source'][1])
        if key_ in xin and c['destination'][0] in newid:
            lines.append({'patchline': {'source': [xin[key_], 0],
                                        'destination': [newid[c['destination'][0]], c['destination'][1]]}})
    print('init        %d controles reciben el outputvalue de %d parametros'
          % (len(init), len(params_moving)))

    page = {'patcher': {
        'fileversion': 1,
        'appversion': {'major': 9, 'minor': 0, 'revision': 7, 'architecture': 'x64', 'modernui': 1},
        'classnamespace': 'box', 'rect': [100.0, 100.0, 960.0, 700.0],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial Bold',
        'gridsize': [8.0, 8.0], 'boxes': boxes, 'lines': lines, 'parameters': params,
        'dependency_cache': [], 'autosave': 0}}
    print('pagina      %d cajas, %d cords, %d parametros anidados'
          % (len(boxes), len(lines), len(params)))

    # ---- the parent -------------------------------------------------------------------------
    bpid = 'obj-%d' % (max(int(i.split('-')[1]) for i in box) + 1)
    kept = [l for l in P['lines']
            if l['patchline']['source'][0] not in moving
            and l['patchline']['destination'][0] not in moving]
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in moving]
    P['boxes'].append({'box': {
        'id': bpid, 'maxclass': 'bpatcher', 'name': fname,
        'numinlets': 2 + len(extern), 'numoutlets': 1, 'outlettype': [''], 'offset': [0.0, 0.0],
        'varname': 'fs2_page_' + key,
        'patching_rect': [X0, 560.0, PW, PH],
        'presentation': 1, 'presentation_rect': [X0, Y0, PW, PH]}})
    mk = lambda a, b_, c, d: {'patchline': {'source': [a, b_], 'destination': [c, d]}}
    kept.append(mk(init_box, 0, bpid, 0))
    kept.append(mk(byvar['fs2_gen'], 4, bpid, 1))
    kept.append(mk(bpid, 0, byvar['fs2_gen'], 0))
    for k, (sid, so) in enumerate(extern):
        kept.append(mk(sid, so, bpid, 2 + k))

    PP = P['parameters']
    for i in params_moving:
        assert i in PP, i
        del PP[i]
    for old, new in newid.items():
        if old in params_moving:
            PP['%s::%s' % (bpid, new)] = page['patcher']['parameters'][new]

    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    top = [k for k in PP if k not in meta and '::' not in k]
    for rank, k in enumerate(sorted(top, key=lambda k: PP[k][2])):
        PP[k][2] = rank
        box[k]['saved_attribute_attributes']['valueof']['parameter_order'] = rank
    print('top-level   %d parametros, renumerados 0..%d' % (len(top), len(top) - 1))

    dc = P.setdefault('dependency_cache', [])
    if not any(x.get('name') == fname for x in dc):
        sib = next(x for x in dc if x['name'].endswith('.maxpat'))
        dc.append({'name': fname, 'bootpath': sib['bootpath'], 'type': 'JSON', 'implicit': 1})

    names = {v[0] for k, v in PP.items() if k not in meta}
    missing = [(b['name'], p) for b in PP['parameterbanks'].values()
               for p in b['parameters'] if p != '-' and p not in names]
    assert not missing, missing
    print('cajas       %d -> %d   cords %d -> %d'
          % (len(box), len(P['boxes']), len(cords), len(kept)))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return
    P['lines'] = kept
    with open(page_path, 'w', encoding='utf-8', newline='') as f:
        json.dump(page, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('\nescritos %s y %s' % (page_path, DEVICE))


main()
