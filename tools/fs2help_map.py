"""Resolution half of the jsui help generator: which Live parameter (and therefore which Spanish
annotation) each drawn chip of fs2horizon.js corresponds to.

Imported by tools/gen_fs2_help.py. Kept separate because it is the part with a verifiable answer --
it can be re-run to CHECK the mapping after the UI changes, independently of the English prose.

The join is mechanical: every spec in fs2horizon.js's DRAG_SPECS/TOGGLE_SPECS fires
`outlet(0, ['set<something>', ...])`, and every `live.*` widget in the device is wired to a
`prepend set<something>`. Matching on that setter name resolves 134 of the 135 chips. Where one
setter serves several parameters (four numboxes feeding one `pak`, the six interval-vector pairs,
the four modulation slots) AMBIGUOUS below picks the right one by hand.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

FORTESEQ = 'forteseq'
DEVICE = os.path.join(FORTESEQ, 'FORTESEQ2.amxd')
MAXPATS = ['fs2pages.maxpat', 'fs2voice.maxpat', 'fs2voice_adv.maxpat']
HORIZON = os.path.join(FORTESEQ, 'fs2horizon.js')

# globalChipGeo name -> spec key, for the three that are not simply 'g' + the geo name.
GEO_ALIAS = {'eugir': 'geurot', 'eupuls': 'geuck', 'raizrate': 'graiz'}

# Chips whose setter serves more than one Live parameter: the parameter's longname, chosen by hand.
# "V#1 X" names live in fs2voice_adv.maxpat / fs2voice.maxpat and stand for all four instances.
AMBIGUOUS = {
    'octbase': 'V#1 Oct', 'octevery': 'V#1 Ev.N', 'octrange': 'V#1 O.Rng', 'octsteps': 'V#1 Pasos',
    'rgmin': 'V#1 Min', 'rgspan': 'V#1 Span',
    'euclen': 'V#1 EucLargo', 'euck': 'V#1 EucPulsos', 'eucrot': 'V#1 EucGiro',
    'artvmin': 'V#1 VelMin', 'artvmax': 'V#1 VelMax', 'artdur': 'V#1 Figura', 'artsil': 'V#1 Silencio',
    'gsilnorm': 'Silencio Normal', 'gsilacc': 'Silencio Acento',
    'gratn': 'Rat Normal', 'grata': 'Rat Acento',
    'gvelminn': 'Vel Min Normal', 'gvelmina': 'Vel Min Acento',
    'gvelmaxn': 'Vel Max Normal', 'gvelmaxa': 'Vel Max Acento',
    'gfign': 'Figura Normal', 'gfiga': 'Figura Acento',
}
for _i in range(1, 7):
    AMBIGUOUS['gvmin%d' % _i] = 'Vec%d min' % _i
    AMBIGUOUS['gvmax%d' % _i] = 'Vec%d max' % _i
for _i in range(1, 5):
    AMBIGUOUS['gmod%dcycle' % _i] = 'Mod%d Ciclo' % _i
    AMBIGUOUS['gmod%ddepth' % _i] = 'Mod%d Prof' % _i
    AMBIGUOUS['gmod%dphase' % _i] = 'Mod%d Fase' % _i
    AMBIGUOUS['gmod%dshape' % _i] = 'Mod%d Forma' % _i
    AMBIGUOUS['gmod%ddest' % _i] = 'Mod%d Dest' % _i


def _obj_literal(src, start):
    """Return the {...} literal that begins at or after `start`."""
    i = src.index('{', start)
    depth, j = 0, i
    while True:
        if src[j] == '{':
            depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
        j += 1


def parse_specs(src):
    """{spec key: [setter names it fires]} for both spec tables of fs2horizon.js."""
    out = {}
    for name in ('DRAG_SPECS', 'TOGGLE_SPECS'):
        block = _obj_literal(src, src.index('var ' + name))
        hits = list(re.finditer(r'^\t(\w+):\s*\{', block, re.M))
        for n, m in enumerate(hits):
            end = hits[n + 1].start() if n + 1 < len(hits) else len(block)
            body = block[m.start():end]
            out[m.group(1)] = sorted(set(re.findall(r"outlet\(0,\s*\[\s*'([a-z0-9_]+)'", body)))
    return out


def geo_keys(src, var_name):
    """The distinct property names assigned on a geometry table (cg.* or globalChipGeo.*)."""
    return sorted(set(re.findall(r'\b' + var_name + r'\.(\w+)', src)))


def _patchers():
    _, _, _, doc = amxd.load(DEVICE)
    yield os.path.basename(DEVICE), doc['patcher']
    for f in MAXPATS:
        yield f, json.load(open(os.path.join(FORTESEQ, f), encoding='utf-8'))['patcher']


def param_index():
    """Two indexes over every Live parameter in the device tree:
    by longname -> annotation (or ''), and setter name -> set of longnames it drives."""
    by_longname, by_setter = {}, {}
    for fn, P in _patchers():
        bx = {b['box']['id']: b['box'] for b in P['boxes']}
        adj = {}
        for l in P.get('lines', []):
            adj.setdefault(l['patchline']['source'][0], []).append(l['patchline']['destination'][0])
        for bid, b in bx.items():
            if not b.get('parameter_enable'):
                continue
            ln = b.get('saved_attribute_attributes', {}).get('valueof', {}).get('parameter_longname')
            if not ln:
                continue
            by_longname[ln] = b.get('annotation', '') or ''
            # walk downstream a few hops for the `prepend set*` this widget drives
            seen, frontier, found = set(), [bid], None
            for _ in range(4):
                nxt = []
                for n in frontier:
                    for d in adj.get(n, []):
                        if d in seen:
                            continue
                        seen.add(d)
                        nxt.append(d)
                        m = re.match(r'(?:prepend|message)\s+(set[a-z0-9_]+)', bx.get(d, {}).get('text', '') or '')
                        if m:
                            found = m.group(1)
                if found:
                    break
                frontier = nxt
            if found:
                by_setter.setdefault(found, set()).add(ln)
    return by_longname, by_setter


def resolve():
    """[(help key, spec key, longname or None, spanish annotation or '')] for every drawn chip."""
    src = open(HORIZON, encoding='utf-8').read()
    specs = parse_specs(src)
    by_longname, by_setter = param_index()

    rows = []
    for geo in geo_keys(src, 'cg'):
        rows.append(('v:' + geo, geo))
    for geo in geo_keys(src, 'globalChipGeo'):
        rows.append(('g:' + geo, GEO_ALIAS.get(geo, 'g' + geo)))

    out = []
    for help_key, spec_key in rows:
        longname = AMBIGUOUS.get(spec_key)
        if not longname:
            for setter in specs.get(spec_key, []):
                names = by_setter.get(setter)
                if names and len(names) == 1:
                    longname = list(names)[0]
                    break
        out.append((help_key, spec_key, longname, by_longname.get(longname, '') if longname else ''))
    return out


if __name__ == '__main__':
    for help_key, spec_key, longname, ann in resolve():
        print('%-22s %-16s %-20s %s' % (help_key, spec_key, longname or '-',
                                        (ann[:120] + '...') if len(ann) > 120 else (ann or '(sin anotacion)')))
