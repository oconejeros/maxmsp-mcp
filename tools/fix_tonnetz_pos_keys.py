"""Some boxes in tz_window (added by add_tonnetz_harmmode.py / add_tonnetz_vcol.py) carry
`patching_position` / `presentation_position` instead of `patching_rect` /
`presentation_rect`.  Max prefers `*_position` when both are present, so the relayout's
`*_rect` edits were silently ignored for those boxes (vcol / harmmode / their labels stayed
at the old spot).  This normalises every box to the `*_rect` form: where a `*_rect` already
holds the intended geometry, the stray `*_position` (+ `*_size`) key is dropped; otherwise
the rect is synthesised from position + size first.

Run with tonnetz.amxd CLOSED in Max and Live, then reopen the device.
"""
import datetime
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'forteseq', 'tonnetz.amxd')


def normalise(b):
    """Return True if the box was changed."""
    changed = False
    for pos_k, size_k, rect_k in (
            ('patching_position', 'patching_size', 'patching_rect'),
            ('presentation_position', 'presentation_size', 'presentation_rect')):
        if pos_k not in b:
            continue
        pos = b[pos_k]
        if rect_k in b and isinstance(b[rect_k], list) and len(b[rect_k]) == 4:
            pass  # rect already authoritative
        else:
            size = b.get(size_k) or b.get('patching_size') or [50.0, 20.0]
            b[rect_k] = [float(pos[0]), float(pos[1]), float(size[0]), float(size[1])]
        b.pop(pos_k, None)
        b.pop(size_k, None)
        changed = True
    return changed


def walk(boxes, hits):
    for e in boxes:
        b = e.get('box', {})
        if normalise(b):
            hits.append(b.get('varname') or b.get('id'))
        if 'patcher' in b:
            walk(b['patcher']['boxes'], hits)


def main():
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(PATH, PATH + '.bak-' + ts)
    print('backup: ' + PATH + '.bak-' + ts)

    data, start, end, doc = amxd.load(PATH)
    hits = []
    walk(doc['patcher']['boxes'], hits)
    print('normalised %d boxes: %s' % (len(hits), ', '.join(hits)))
    assert hits, 'nothing to fix?'

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    _, _, _, d2 = amxd.load(PATH)

    def check(boxes):
        for e in boxes:
            b = e.get('box', {})
            for k in ('patching_position', 'presentation_position'):
                assert k not in b, (b.get('id'), k, 'still present')
            if 'patcher' in b:
                check(b['patcher']['boxes'])
    check(d2['patcher']['boxes'])

    def hdr(boxes):
        for e in boxes:
            b = e.get('box', {})
            if b.get('varname') in ('tzw_vcol', 'tzw_lb346_8', 'tzw_harmmode', 'tzw_lb862_69'):
                print('  %-15s rect=%s text=%r' % (b['varname'], b.get('patching_rect'), b.get('text')))
            if 'patcher' in b:
                hdr(b['patcher']['boxes'])
    hdr(d2['patcher']['boxes'])
    print('OK: no *_position keys remain.')

    cs = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'check_structure.py'), PATH],
                        capture_output=True, text=True)
    print(cs.stdout.strip() or cs.stderr.strip())
    sys.exit(cs.returncode)


if __name__ == '__main__':
    main()
