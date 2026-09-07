"""Follow-up tweak to relayout_tonnetz_panels.py: tighten header row 1 so the four mode
toggles (Study / Color / Armonia / Prev) and their labels never crowd, and shorten the
"Armonia" comment to "Arm" (it overflowed its 54px box onto the XfPrev checkbox).

Re-runnable: only sets patching_rect/presentation_rect + one comment text.  Run with
tonnetz.amxd CLOSED in Max and Live, then FULLY reopen the device (a save from here does
not reach an already-open instance).
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

# varname -> [x, y, w, h]
TWEAK = {
    'tzw_study':    (332, 8, 14, 14), 'tzw_lb26_158': (350, 8, 48, 15),   # "Estudio"
    'tzw_vcol':     (410, 8, 14, 14), 'tzw_lb346_8':  (428, 8, 36, 15),   # "Color"
    'tzw_harmmode': (476, 8, 14, 14), 'tzw_lb862_69': (494, 8, 26, 15),   # "Arm"
    'tzw_xfprev':   (534, 8, 14, 14), 'tzw_lb86_128': (552, 8, 30, 15),   # "Prev"
}


def find_sub_with_jsui(p):
    for e in p.get('boxes', []):
        b = e.get('box', {})
        if 'patcher' in b:
            if any(e2.get('box', {}).get('maxclass') == 'jsui'
                   for e2 in b['patcher'].get('boxes', [])):
                return b
            r = find_sub_with_jsui(b['patcher'])
            if r:
                return r
    return None


def by_vn(boxes, vn):
    for e in boxes:
        if e.get('box', {}).get('varname') == vn:
            return e['box']
    raise KeyError(vn)


def by_id(boxes, bid):
    for e in boxes:
        if e.get('box', {}).get('id') == bid:
            return e['box']
    raise KeyError(bid)


def main():
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(PATH, PATH + '.bak-' + ts)
    print('backup: ' + PATH + '.bak-' + ts)

    data, start, end, doc = amxd.load(PATH)
    sub = find_sub_with_jsui(doc['patcher'])
    P = sub['patcher']
    B = P['boxes']

    for bid in ('obj-panel', 'obj-thisp', 'obj-lconex'):
        by_id(B, bid)  # assert relayout already ran

    for vn, (x, y, w, h) in TWEAK.items():
        b = by_vn(B, vn)
        b['patching_rect'] = [float(x), float(y), float(w), float(h)]
        b['presentation_rect'] = [float(x), float(y), float(w), float(h)]
    by_vn(B, 'tzw_lb862_69')['text'] = 'Arm'

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    _, _, _, d2 = amxd.load(PATH)
    P2 = find_sub_with_jsui(d2['patcher'])['patcher']
    for vn, (x, y, w, h) in TWEAK.items():
        assert by_vn(P2['boxes'], vn)['patching_rect'] == [float(x), float(y), float(w), float(h)]
    assert by_vn(P2['boxes'], 'tzw_lb862_69')['text'] == 'Arm'
    print('OK: row 1 tightened, "Armonia" -> "Arm".')

    cs = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'check_structure.py'), PATH],
                        capture_output=True, text=True)
    print(cs.stdout.strip() or cs.stderr.strip())
    sys.exit(cs.returncode)


if __name__ == '__main__':
    main()
