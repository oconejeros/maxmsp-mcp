"""One-off: aw_anwin (the "an" AnWin control in ANIMIDI.amxd's control strip) was added during
a live MCP-edit session (the device could not be closed at the time). Its position/wiring landed
fine, but the Live-parameter attributes (parameter_longname/mmin/mmax/initial) never actually
stuck -- the box was left with generic defaults (parameter_longname "live.numbox", no mmin/mmax),
so Live fell back to its default 0-127 range for the unmapped parameter. animidi.js's own
`anwin(v)` handler already clamps to 0..10 seconds, so the control should match that range
instead of 0-127 -- same idea as tonnetz.amxd's own AnWin numbox (tzw_anwin: 0-30s, since
tonnetz.js's own clamp is wider).

Run with ANIMIDI.amxd closed in both Max and Live.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'forteseq', 'ANIMIDI.amxd')


def find_box(boxes, varname):
    for entry in boxes:
        b = entry.get('box', {})
        if b.get('varname') == varname:
            return b
    raise KeyError(varname)


def find_subpatcher(boxes, varname):
    for entry in boxes:
        b = entry.get('box', {})
        if b.get('varname') == varname:
            return b.get('patcher')
    raise KeyError(varname)


def main():
    data, start, end, doc = amxd.load(PATH)
    root = doc['patcher']
    win = find_subpatcher(root['boxes'], 'an_window')

    box = find_box(win['boxes'], 'aw_anwin')
    vo = box['saved_attribute_attributes']['valueof']
    vo['parameter_longname'] = 'AnWin'
    vo['parameter_shortname'] = 'AnWin'
    vo['parameter_type'] = 0
    vo['parameter_mmin'] = 0.0
    vo['parameter_mmax'] = 10.0
    vo['parameter_unitstyle'] = 0
    vo['parameter_initial_enable'] = 1
    vo['parameter_initial'] = [1.2]
    vo.pop('parameter_modmode', None)

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    _, _, _, doc2 = amxd.load(PATH)
    win2 = find_subpatcher(doc2['patcher']['boxes'], 'an_window')
    box2 = find_box(win2['boxes'], 'aw_anwin')
    vo2 = box2['saved_attribute_attributes']['valueof']
    assert vo2['parameter_longname'] == 'AnWin', vo2
    assert vo2['parameter_mmin'] == 0.0 and vo2['parameter_mmax'] == 10.0, vo2
    assert vo2['parameter_initial'] == [1.2], vo2
    print('OK: aw_anwin now AnWin, range 0-10s, initial 1.2s.')


if __name__ == '__main__':
    main()
