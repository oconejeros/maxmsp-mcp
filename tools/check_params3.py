"""Cross-check that FORTESEQ2's three parameter registries agree.

    python tools/check_params3.py                       # FORTESEQ2 + its bpatchers
    python tools/check_params3.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat ...

A Live parameter in this device is described in up to three places that must stay in sync:

  1. the box's  saved_attribute_attributes.valueof  (parameter_longname / _shortname /
     _enum / _mmax / _order) -- lives in whatever patcher the box lives in;
  2. the owning patcher's  parameters  dict -- `[longname, shortname, order]`, keyed by
     box id (top-level) or `<bpatcher-id>::<box-id>` (nested, in FORTESEQ2.amxd);
  3. `parameters.parameterbanks` (FORTESEQ2.amxd) -- 8-wide banks that name params by
     longname string.

check_structure.py validates none of this. This script reports:
  - box has parameter_enable + valueof but no `parameters` entry (or vice-versa);
  - longname disagreement between the valueof and the `parameters` mirror;
  - `.amxd parameters` key that resolves to no box;
  - duplicate / gap in top-level parameter_order;
  - bank references a longname that no live parameter provides;
  - nested param registered in the .amxd but missing from the bpatcher's own `parameters`.

Exit non-zero on any hard failure; longname/shortname divergences are warnings (the repo
already ships one: fs2pages local `parameters` says "Indep", the .amxd mirror says
"Voces Indep").
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECIAL = {'parameterbanks', 'parameter_overrides', 'inherited_shortname',
           'parameter_invisible', 'parameterlist'}


def load_patcher(path):
    if path.endswith('.amxd'):
        return amxd.load(path)[3]['patcher']
    return json.load(open(path, encoding='utf-8'))['patcher']


def boxes_of(patcher):
    """id -> box, recursing into inline subpatchers (not bpatcher file refs)."""
    out = {}
    def walk(p):
        for e in p.get('boxes', []):
            b = e.get('box', {})
            if b.get('id'):
                out[b['id']] = b
            if b.get('patcher'):
                walk(b['patcher'])
    walk(patcher)
    return out


def valueof(b):
    return (b.get('saved_attribute_attributes') or {}).get('valueof')


def main():
    args = sys.argv[1:]
    amxd_path = next((a for a in args if a.endswith('.amxd')), 'forteseq/FORTESEQ2.amxd')
    amxd_path = amxd_path if os.path.isabs(amxd_path) else os.path.join(ROOT, amxd_path)
    P = load_patcher(amxd_path)
    top_boxes = boxes_of(P)
    params = P.get('parameters', {})
    banks = params.get('parameterbanks', {})
    overrides = params.get('parameter_overrides', {})

    def eff_longname(key, raw):
        """The longname Live actually uses: parameter_overrides wins (the voice bpatchers
        register raw `V#1 VelMin` and remap per instance to `V1 VelMin` .. `V4 VelMin`)."""
        ov = overrides.get(key)
        if isinstance(ov, dict) and ov.get('parameter_longname'):
            return ov['parameter_longname']
        return raw

    errors, warnings = [], []

    # --- map bpatcher id -> loaded child patcher + its own parameters -----------------
    child = {}     # bpatcher-box-id -> (child_patcher, child_params, child_boxes)
    for bid, b in top_boxes.items():
        if b.get('maxclass') == 'bpatcher' and b.get('name', '').endswith('.maxpat'):
            cpath = os.path.join(os.path.dirname(amxd_path), b['name'])
            if os.path.isfile(cpath):
                cp = load_patcher(cpath)
                child[bid] = (cp, cp.get('parameters', {}), boxes_of(cp))

    # --- 1. every parameters key resolves to a box, longname agrees ------------------
    provided = {}          # longname -> where
    for key, val in params.items():
        if key in SPECIAL:
            continue
        if not (isinstance(val, list) and len(val) >= 2):
            errors.append('parameters[%r] is not [longname, shortname, order]: %r' % (key, val))
            continue
        longname = eff_longname(key, val[0])
        if '::' in key:
            bp_id, inner = key.split('::', 1)
            if bp_id not in child:
                errors.append('parameters[%r]: bpatcher %s not found/loaded' % (key, bp_id))
                continue
            _cp, cprm, cbx = child[bp_id]
            if inner not in cbx:
                errors.append('parameters[%r]: box %s absent from %s'
                              % (key, inner, top_boxes[bp_id].get('name')))
                continue
            vo = valueof(cbx[inner])
            if vo is None:
                errors.append('parameters[%r]: box %s has no valueof' % (key, inner))
            elif key not in overrides and vo.get('parameter_longname') not in (longname, val[1]):
                warnings.append('parameters[%r] longname %r != valueof %r'
                                % (key, longname, vo.get('parameter_longname')))
            if inner not in cprm:
                errors.append('parameters[%r]: %s missing from %s own parameters dict'
                              % (key, inner, top_boxes[bp_id].get('name')))
            provided[longname] = key
        else:
            if key not in top_boxes:
                errors.append('parameters[%r]: no box with that id' % key)
                continue
            vo = valueof(top_boxes[key])
            if vo is None:
                errors.append('parameters[%r]: box has no valueof' % key)
            elif vo.get('parameter_longname') not in (longname, val[1]):
                warnings.append('parameters[%r] longname %r != valueof %r'
                                % (key, longname, vo.get('parameter_longname')))
            if not top_boxes[key].get('parameter_enable'):
                warnings.append('parameters[%r]: box parameter_enable is not set' % key)
            provided[longname] = key

    # --- 2. every parameter_enable box is registered -------------------------------
    for bid, b in top_boxes.items():
        if b.get('parameter_enable') and valueof(b) and bid not in params:
            errors.append('box %s (%s) has parameter_enable+valueof but no parameters[%s]'
                          % (bid, valueof(b).get('parameter_longname'), bid))
    for bp_id, (_cp, cprm, cbx) in child.items():
        for ib, b in cbx.items():
            if b.get('parameter_enable') and valueof(b):
                if ('%s::%s' % (bp_id, ib)) not in params:
                    errors.append('%s box %s (%s) enabled but not in .amxd parameters'
                                  % (top_boxes[bp_id].get('name'), ib,
                                     valueof(b).get('parameter_longname')))
                if ib not in cprm:
                    warnings.append('%s box %s enabled but not in its own parameters dict'
                                    % (top_boxes[bp_id].get('name'), ib))

    # --- 3. top-level parameter_order distinct & gapless --------------------------
    orders = []
    for key, val in params.items():
        if key in SPECIAL or '::' in key or not isinstance(val, list) or len(val) < 3:
            continue
        orders.append((val[2], key))
    seen = {}
    for o, key in orders:
        if o in seen:
            errors.append('duplicate top-level parameter_order %d: %s and %s' % (o, seen[o], key))
        seen[o] = key
    if orders:
        want = set(range(len(orders)))
        got = {o for o, _ in orders}
        if got != want:
            warnings.append('top-level parameter_order not 0..%d contiguous: got %s'
                            % (len(orders) - 1, sorted(got)))

    # --- 4. bank longnames resolve ----------------------------------------------
    for bidx, bank in sorted(banks.items(), key=lambda kv: kv[1].get('index', 0)):
        for lname in bank.get('parameters', []):
            if lname == '-' or not lname:
                continue
            if lname not in provided:
                errors.append('bank %s %r references unknown parameter %r'
                              % (bidx, bank.get('name'), lname))

    # --- report ---------------------------------------------------------------
    for w in warnings:
        print('WARN  ' + w)
    for e in errors:
        print('FAIL  ' + e)
    print('\n%s  (%d params, %d banks, %d warnings, %d failures)'
          % ('OK' if not errors else 'FAILED', len(provided), len(banks),
             len(warnings), len(errors)))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
