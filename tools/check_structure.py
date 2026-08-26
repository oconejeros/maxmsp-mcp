"""Validate the low-level structural integrity of an .amxd/.maxpat patcher tree: every box id is
unique, every patchline's source/destination is an id STRING that actually resolves to a box (not
an accidentally-embedded box dict -- the exact bug that crashed Live on forteseqhub.amxd, 2026-08-24:
a script's `link()` helper was handed a full box dict instead of its id), and every outlet/inlet
index a patchline uses is within that box's declared numoutlets/numinlets. This is exactly the
class of malformed JSON Max's native patcher loader has no obligation to survive.

    python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/forteseqhub.amxd ...
    python tools/check_structure.py forteseq/fs2pages.maxpat forteseq/fs2voice.maxpat ...

Recurses into nested subpatchers (boxes with their own "patcher"). Exits nonzero if anything fails.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd


def load_any(path):
    if path.endswith('.amxd'):
        _data, _s, _e, doc = amxd.load(path)
        return doc['patcher']
    return json.load(open(path, encoding='utf-8'))['patcher']


def check_patcher(p, path, where, errors):
    boxes = {}
    for entry in p.get('boxes', []):
        b = entry.get('box', {})
        bid = b.get('id')
        if not isinstance(bid, str):
            errors.append('%s %s: box id is not a string: %r' % (path, where, bid))
            continue
        if bid in boxes:
            errors.append('%s %s: duplicate box id %s' % (path, where, bid))
        boxes[bid] = b

    for entry in p.get('lines', []):
        pl = entry.get('patchline', {})
        src, dst = pl.get('source'), pl.get('destination')
        for label, end in (('source', src), ('destination', dst)):
            if not (isinstance(end, list) and len(end) >= 2):
                errors.append('%s %s: patchline %s is not [id, index]: %r' % (path, where, label, end))
                continue
            eid, eidx = end[0], end[1]
            if not isinstance(eid, str):
                errors.append('%s %s: patchline %s id is a %s, not a string -- %r'
                              % (path, where, label, type(eid).__name__, eid))
                continue
            if eid not in boxes:
                errors.append('%s %s: patchline %s references unknown box %s' % (path, where, label, eid))
                continue
            b = boxes[eid]
            n = b.get('numoutlets', 0) if label == 'source' else b.get('numinlets', 0)
            if not isinstance(eidx, int) or not (0 <= eidx < n):
                errors.append('%s %s: patchline %s %s outlet/inlet %r out of range (0..%d) on %s (%s)'
                              % (path, where, label, eid, eidx, n - 1, b.get('maxclass'), b.get('text', '')))

    for entry in p.get('boxes', []):
        b = entry.get('box', {})
        if b.get('patcher'):
            check_patcher(b['patcher'], path, where + '::' + b.get('id', '?'), errors)


def main():
    paths = sys.argv[1:]
    if not paths:
        print('uso: python tools/check_structure.py <archivo.amxd|.maxpat> [...]')
        sys.exit(2)
    errors = []
    for path in paths:
        p = load_any(path)
        before = len(errors)
        check_patcher(p, path, 'root', errors)
        if len(errors) == before:
            print('OK   %s' % path)
    if errors:
        print('')
        print('FALLAS (%d):' % len(errors))
        for e in errors:
            print(' -', e)
        sys.exit(1)


main()
