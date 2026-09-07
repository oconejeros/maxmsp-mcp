"""Derive a feature-capped "Lite" .amxd from a full Conejeros Devices device.

    python tools/make_lite.py                       dry run, both devices, prints the plan
    python tools/make_lite.py forteseqwf --apply    write release/_stage/forteseqwf Lite.amxd
    python tools/make_lite.py FORTESEQ2 --apply

Model (see sales/go-to-market.md): the Lite is a genuinely reduced build, not a locked one.
This script does the part that is safe to do on the .amxd container:

  * delete every Push `parameterbanks` entry,
  * drop a named set of Premium parameters from all three registries (`parameters`,
    `parameter_overrides`, bank membership) so Live can't map/automate them,
  * for controls that live IN the .amxd (forteseqwf's Morph strip): also set
    `parameter_enable` 0 and `hidden` 1 on the box,
  * inject  loadbang -> [lite 1] -> <engine js>  so the running code knows it is Lite.

What it CANNOT do and you must still do by hand (the script prints this):

  * FORTESEQ2's Premium controls (Slot / Fav / Solo Fav / Prog Favoritos / the two Azar %
    knobs) live in forteseq/fs2pages.maxpat, a bpatcher file this script does not touch.
    After --apply they are unmapped from Live but the knobs still show in the popup. Hide
    them in fs2pages.maxpat, or rely on the JS guard below to make them inert.
  * The `lite` guard in forteseq/forteseq2.js and forteseq/forteseqwf.js: a handler that,
    on `lite 1`, makes storepreset / savepresets / randomize* / setnumvoices no-ops and
    caps pattern length (FORTESEQ2 -> 8 steps) / preset slots (forteseqwf -> 8). The same
    .js ships in both builds; only the Lite .amxd sends `lite 1`.

Always dry-run first and diff. Close the device in Max AND Live before --apply.
Output goes to release/_stage/ ; tools/package_release.py picks it up from there.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = os.path.join(ROOT, 'release', '_stage')

SPECS = {
    'forteseqwf': {
        'src': 'forteseq/forteseqwf.amxd',
        'out': 'forteseqwf Lite.amxd',
        'engine_box': 'obj-6',            # js forteseqwf.js
        'loadbang_box': 'obj-37',
        'drop_params': ['Morph', 'Morph A', 'Morph B', 'Quantize R', 'Morph R Linear'],
        # boxes for those params live in this .amxd -> also hide + disable them
        'hide_boxes': {'obj-123', 'obj-124', 'obj-125', 'obj-127', 'obj-128'},
        'lite_msgs': ['lite 1'],
        'note': 'Lite = 8 preset slots (JS guard), sin Morph A/B, sin Quantize R.',
    },
    'FORTESEQ2': {
        'src': 'forteseq/FORTESEQ2.amxd',
        'out': 'FORTESEQ2 Lite.amxd',
        'engine_box': 'obj-23',           # js forteseq2.js
        'loadbang_box': 'obj-31',
        'drop_params': ['Slot', 'Fav', 'Solo Fav', 'Prog Favoritos',
                        'Azar % Mask', 'Azar % Acentos'],
        'hide_boxes': set(),             # these controls are in fs2pages.maxpat, not here
        'lite_msgs': ['lite 1', 'setnumvoices 4'],
        'note': ('Lite = 8 pasos (JS guard), 4 voces, sin presets/favoritos, sin Random '
                 'All, sin Push. Los knobs de preset/azar siguen en fs2pages.maxpat: '
                 'ocultalos ahi o deja que el guard `lite` de forteseq2.js los anule.'),
    },
}


def strip_banks(P, log):
    prm = P.get('parameters', {})
    banks = prm.get('parameterbanks')
    if banks:
        log.append('  parameterbanks: remove %d bank(s) (Push)' % len(banks))
        prm['parameterbanks'] = {}


def drop_params(P, names, log):
    names = set(names)
    prm = P.get('parameters', {})
    # 1) which registry keys carry those longnames
    kill_keys = set()
    for k, v in list(prm.items()):
        if k in ('parameterbanks', 'inherited_shortname', 'parameter_overrides'):
            continue
        if isinstance(v, list) and v and v[0] in names:
            kill_keys.add(k)
    for k in kill_keys:
        prm.pop(k, None)
        log.append('  parameters: drop %s' % k)
    # 2) parameter_overrides
    ov = prm.get('parameter_overrides')
    if isinstance(ov, dict):
        for k in list(ov):
            ln = (ov[k] or {}).get('parameter_longname')
            if k in kill_keys or ln in names:
                ov.pop(k, None)
                log.append('  parameter_overrides: drop %s' % k)
    # 3) local subpatcher parameter blocks + bank membership everywhere
    def walk(p):
        pp = p.get('parameters')
        if isinstance(pp, dict):
            for k, v in list(pp.items()):
                if isinstance(v, list) and v and v[0] in names:
                    pp.pop(k, None)
                    log.append('  (sub) parameters: drop %s' % k)
            b = pp.get('parameterbanks')
            if isinstance(b, dict):
                for bk, bv in b.items():
                    bv['parameters'] = [x if x not in names else '-'
                                        for x in bv.get('parameters', [])]
        for box in p.get('boxes', []):
            if box['box'].get('patcher'):
                walk(box['box']['patcher'])
    walk(P)
    return kill_keys


def hide_boxes(P, ids, names, log):
    for box in P.get('boxes', []):
        b = box['box']
        if b.get('id') in ids:
            b['parameter_enable'] = 0
            b['hidden'] = 1
            sa = b.get('saved_attribute_attributes')
            if sa and 'valueof' in sa:
                sa['valueof'].pop('parameter_longname', None)
            log.append('  box %s: parameter_enable=0, hidden=1' % b.get('id'))


def inject_lite(P, spec, log):
    boxes = P['boxes']
    lines = P.setdefault('lines', [])
    have = {b['box'].get('id') for b in boxes}
    if spec['engine_box'] not in have:
        log.append('  !! engine box %s not found -- lite message NOT injected' % spec['engine_box'])
        return
    lb = spec['loadbang_box'] if spec['loadbang_box'] in have else None
    maxn = max((int(b['box']['id'][4:]) for b in boxes
                if b['box'].get('id', 'x')[4:].isdigit()), default=900)
    nid = maxn + 1
    if lb is None:
        lb = 'obj-%d' % nid; nid += 1
        boxes.append({'box': {'id': lb, 'maxclass': 'newobj', 'numinlets': 1,
                              'numoutlets': 1, 'outlettype': ['bang'],
                              'patching_rect': [12.0, 12.0, 62.0, 22.0],
                              'text': 'loadbang', 'hidden': 1}})
        log.append('  add loadbang %s' % lb)
    for i, msg in enumerate(spec['lite_msgs']):
        mid = 'obj-%d' % nid; nid += 1
        boxes.append({'box': {'id': mid, 'maxclass': 'message', 'numinlets': 2,
                              'numoutlets': 1, 'outlettype': [''],
                              'patching_rect': [12.0, 44.0 + 26 * i, 120.0, 22.0],
                              'text': msg, 'hidden': 1}})
        lines.append({'patchline': {'source': [lb, 0], 'destination': [mid, 0], 'hidden': 1}})
        lines.append({'patchline': {'source': [mid, 0],
                                    'destination': [spec['engine_box'], 0], 'hidden': 1}})
        log.append('  add message [%s] -> %s' % (msg, spec['engine_box']))


def process(key, spec, apply_it):
    src = os.path.join(ROOT, spec['src'])
    data, s, e, doc = amxd.load(src)
    P = doc['patcher']
    log = []

    strip_banks(P, log)
    drop_params(P, spec['drop_params'], log)
    if spec['hide_boxes']:
        hide_boxes(P, spec['hide_boxes'], set(spec['drop_params']), log)
    inject_lite(P, spec, log)

    print('=== %s  ->  release/_stage/%s' % (key, spec['out']))
    print('    %s' % spec['note'])
    for l in log:
        print(l)

    # sanity: every patchline still points at a real box/inlet
    def check(p, where='root'):
        by = {b['box']['id']: b['box'] for b in p.get('boxes', [])}
        for ln in p.get('lines', []):
            pl = ln['patchline']
            for tag, end in (('src', pl['source']), ('dst', pl['destination'])):
                bx = by.get(end[0])
                assert bx is not None, '%s: %s dangling -> %s' % (where, tag, end)
        for b in p.get('boxes', []):
            if b['box'].get('patcher'):
                check(b['box']['patcher'], where + '::' + b['box']['id'])
    check(P)

    if not apply_it:
        print('    (dry run)\n')
        return

    os.makedirs(STAGE, exist_ok=True)
    out = os.path.join(STAGE, spec['out'])
    amxd.save(out, data, s, e, doc)
    back = amxd.load(out)[3]['patcher']
    assert not back.get('parameters', {}).get('parameterbanks'), 'banks survived'
    print('    wrote %s' % os.path.relpath(out, ROOT))
    print('    NEXT: add the `lite` guard to %s, then'
          % os.path.basename(spec['src']).replace('.amxd', '.js'))
    print('          python tools/check_structure.py "%s"' % os.path.relpath(out, ROOT))
    print('          python tools/package_release.py "%s Lite"\n'
          % (key if key != 'FORTESEQ2' else 'FORTESEQ2'))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply_it = '--apply' in sys.argv
    which = args or list(SPECS)
    bad = [w for w in which if w not in SPECS]
    if bad:
        sys.exit('unknown: %s  (known: %s)' % (', '.join(bad), ', '.join(SPECS)))
    print('make_lite  (%s)\n' % ('APPLY' if apply_it else 'dry run'))
    for k in which:
        process(k, SPECS[k], apply_it)
    if not apply_it:
        print('re-run with --apply to write release/_stage/*.amxd')


if __name__ == '__main__':
    main()
