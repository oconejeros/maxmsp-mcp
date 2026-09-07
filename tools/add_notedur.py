"""Give multichord + invertedprism a parametrizable note DURATION instead of held/stuck notes.

invertedprism already plays chords through [makenote 90 800] -> noteout (with `flush` on every
new chord), which is why it never sticks -- but the 800 ms was hardcoded. multichord's engine
managed its own noteoff/noteon pairs in JS and could leave notes on forever (loadbang burst,
hot-reload, a colour-path throw).

This script:
  * multichord.amxd -- adds the invertedprism-style MIDI tail in the MAIN patcher:
        route ... shiftmoves chord
        route[chord] -> [t l b] -> (b) [flush] + (l) [iter] -> [makenote 90 1000] -> [noteout]
        [loadbang] -> [deferlow] -> [flush]        (kill any ring left over on device load)
    and a `NoteDur` param (subpatcher live.numbox -> new subpatcher outlet -> makenote inlet 2).
    (multichord.js already changed separately: voiceAndEmit now emits `chord <pitches...>`.)
  * invertedprism.amxd -- just adds the `NoteDur` param (subpatcher live.numbox -> new
    subpatcher outlet -> the existing [makenote 90 800] inlet 2).

Run with both devices closed in Max and Live. Timestamped .bak each; self-checks +
check_structure.py + node --check.
"""
import copy
import datetime
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def by_id(boxes, bid):
    for e in boxes:
        if e.get('box', {}).get('id') == bid:
            return e['box']
    raise KeyError(bid)


def find_sub(p):
    for e in p.get('boxes', []):
        b = e.get('box', {})
        if 'patcher' in b:
            return b
    raise RuntimeError('no subpatcher')


def add_line(lines, s, so, d, di, hidden=True):
    pl = {'source': [s, so], 'destination': [d, di]}
    if hidden:
        pl['hidden'] = 1
    lines.append({'patchline': pl})


def clone_numbox(src, new_id, varname, rect, longname, shortname, mmin, mmax,
                 unitstyle, initial, order=None):
    nb = copy.deepcopy(src)
    nb['id'] = new_id
    nb['varname'] = varname
    nb['patching_rect'] = list(rect)
    nb['presentation_rect'] = list(rect)
    vo = nb['saved_attribute_attributes']['valueof']
    vo['parameter_longname'] = longname
    vo['parameter_shortname'] = shortname
    vo['parameter_mmin'] = mmin
    vo['parameter_mmax'] = mmax
    vo['parameter_unitstyle'] = unitstyle
    vo['parameter_initial_enable'] = 1
    vo['parameter_initial'] = [initial]
    if order is not None:
        vo['parameter_order'] = order
    elif 'parameter_order' in vo:
        del vo['parameter_order']
    return nb


def clone_comment(src, new_id, varname, text, rect):
    c = copy.deepcopy(src)
    c['id'] = new_id
    if varname:
        c['varname'] = varname
    elif 'varname' in c:
        del c['varname']
    c['text'] = text
    c['patching_rect'] = list(rect)
    if 'presentation_rect' in c:
        c['presentation_rect'] = list(rect)
    return c


def outlet_box(new_id, rect):
    return {'box': {'id': new_id, 'maxclass': 'outlet', 'numinlets': 1, 'numoutlets': 0,
                    'patching_rect': list(rect), 'comment': ''}}


def newobj(new_id, text, rect, varname=None):
    b = {'id': new_id, 'maxclass': 'newobj', 'text': text,
         'patching_rect': list(rect), 'numinlets': 1, 'numoutlets': 1}
    if varname:
        b['varname'] = varname
    return {'box': b}


def msgbox(new_id, text, rect, varname=None):
    b = {'id': new_id, 'maxclass': 'message', 'text': text,
         'patching_rect': list(rect), 'numinlets': 2, 'numoutlets': 1}
    if varname:
        b['varname'] = varname
    return {'box': b}


def verify(path, checks):
    _, _, _, d = amxd.load(path)
    r = d['patcher']
    checks(r)
    cs = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'check_structure.py'), path],
                        capture_output=True, text=True)
    print('   check_structure: ' + (cs.stdout.strip() or cs.stderr.strip()))
    assert cs.returncode == 0, cs.stdout + cs.stderr


def do_multichord():
    path = os.path.join(ROOT, 'forteseq', 'multichord.amxd')
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(path, path + '.bak-' + ts)
    data, start, end, doc = amxd.load(path)
    root = doc['patcher']
    RB, RL = root['boxes'], root['lines']

    route = by_id(RB, 'obj-11')
    assert route['text'].endswith('shiftmoves'), \
        'not a clean pre-change multichord.amxd (route=%r) -- restore from a .bak first' % route['text']
    route['text'] = route['text'] + ' chord'          # -> new outlet index 9

    # MIDI tail (invertedprism model), reuse existing noteout obj-18
    RB.append(newobj('obj-50', 't l b', [520.0, 300.0, 40.0, 22.0], 'mc_chord_trig'))
    RB.append(msgbox('obj-51', 'flush', [520.0, 332.0, 44.0, 22.0], 'mc_flush'))
    RB.append(newobj('obj-52', 'iter', [580.0, 332.0, 40.0, 22.0], 'mc_iter_chord'))
    RB.append(newobj('obj-53', 'makenote 90 1000', [520.0, 364.0, 120.0, 22.0], 'mc_makenote'))
    RB.append(newobj('obj-54', 'loadbang', [700.0, 300.0, 62.0, 22.0], 'mc_dl_loadbang'))
    RB.append(newobj('obj-55', 'deferlow', [700.0, 332.0, 60.0, 22.0], 'mc_dl_defer'))
    by_id(RB, 'obj-53')['numinlets'] = 3
    by_id(RB, 'obj-53')['numoutlets'] = 2
    by_id(RB, 'obj-50')['numoutlets'] = 2

    add_line(RL, 'obj-11', 9, 'obj-50', 0)
    add_line(RL, 'obj-50', 1, 'obj-51', 0)     # bang (fires first) -> flush old chord
    add_line(RL, 'obj-50', 0, 'obj-52', 0)     # list -> iter new pitches
    add_line(RL, 'obj-51', 0, 'obj-53', 0)
    add_line(RL, 'obj-52', 0, 'obj-53', 0)
    add_line(RL, 'obj-53', 0, 'obj-18', 0)
    add_line(RL, 'obj-53', 1, 'obj-18', 1)
    add_line(RL, 'obj-54', 0, 'obj-55', 0)
    add_line(RL, 'obj-55', 0, 'obj-51', 0)     # flush anything ringing on device load
    add_line(RL, 'obj-40', 1, 'obj-53', 2)     # NoteDur (subpatcher outlet 1) -> makenote duration

    # --- subpatcher: NoteDur numbox + label + new outlet ---
    subbox = find_sub(root)
    subbox['numoutlets'] = 2                 # keep the container box in sync with the new outlet
    sub = subbox['patcher']
    SB, SL = sub['boxes'], sub['lines']
    reglum = by_id(SB, 'obj-230')
    label = by_id(SB, 'obj-l43')

    SB.append(outlet_box('obj-2b', [60.0, 688.0, 30.0, 30.0]))
    SB.append({'box': clone_numbox(reglum, 'obj-231', 'c_obj_231', [590.0, 56.0, 52.0, 15.0],
                                   'NoteDur', 'Dur', 10.0, 16000.0, 0, 1000.0, order=15)})
    SB.append({'box': clone_comment(label, 'obj-l46', 'c_l46', 'Dur', [590.0, 40.0, 52.0, 16.0])})
    add_line(SL, 'obj-231', 0, 'obj-2b', 0)
    add_line(SL, 'obj-9', 0, 'obj-231', 0)

    # --- registries ---
    tp = root['parameters']
    tp['obj-40::obj-231'] = ['NoteDur', 'Dur', 15]
    bank = tp['parameterbanks']['1']
    assert bank['name'] == 'Steps mode', bank['name']
    bank['parameters'][bank['parameters'].index('-')] = 'NoteDur'

    amxd.save(path, data, start, end, doc)

    def checks(r):
        rb = r['boxes']
        assert by_id(rb, 'obj-11')['text'].endswith(' chord')
        sp = find_sub(r)['patcher']
        nb = by_id(sp['boxes'], 'obj-231')
        vo = nb['saved_attribute_attributes']['valueof']
        assert vo['parameter_longname'] == 'NoteDur' and vo['parameter_order'] == 15
        assert r['parameters']['obj-40::obj-231'] == ['NoteDur', 'Dur', 15]
        assert 'NoteDur' in r['parameters']['parameterbanks']['1']['parameters']
        edges = {(l['patchline']['source'][0], l['patchline']['source'][1],
                  l['patchline']['destination'][0], l['patchline']['destination'][1])
                 for l in r['lines']}
        for e in [('obj-11', 9, 'obj-50', 0), ('obj-50', 1, 'obj-51', 0), ('obj-50', 0, 'obj-52', 0),
                  ('obj-51', 0, 'obj-53', 0), ('obj-52', 0, 'obj-53', 0), ('obj-53', 0, 'obj-18', 0),
                  ('obj-53', 1, 'obj-18', 1), ('obj-54', 0, 'obj-55', 0), ('obj-55', 0, 'obj-51', 0),
                  ('obj-40', 1, 'obj-53', 2)]:
            assert e in edges, ('missing main line', e)
        sedges = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in sp['lines']}
        assert ('obj-231', 'obj-2b') in sedges and ('obj-9', 'obj-231') in sedges
        orders = sorted(v[2] for k, v in r['parameters'].items()
                        if k not in ('parameterbanks', 'inherited_shortname', 'parameter_overrides')
                        and isinstance(v, list))
        assert orders == list(range(16)), orders
        print('   multichord OK: route+chord, makenote tail, NoteDur order 15, %d params 0..15' % len(orders))

    verify(path, checks)


def do_invertedprism():
    path = os.path.join(ROOT, 'forteseq', 'invertedprism.amxd')
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(path, path + '.bak-' + ts)
    data, start, end, doc = amxd.load(path)
    root = doc['patcher']
    RB, RL = root['boxes'], root['lines']

    mk = by_id(RB, 'obj-15')
    assert mk['text'].startswith('makenote'), mk['text']
    mk['numinlets'] = 3
    add_line(RL, 'obj-40', 1, 'obj-15', 2)     # NoteDur -> makenote duration

    subbox = find_sub(root)
    subbox['numoutlets'] = 2                   # keep the container box in sync with the new outlet
    sub = subbox['patcher']
    SB, SL = sub['boxes'], sub['lines']
    src = by_id(SB, 'obj-205')                 # PathSteps numbox (style donor)
    lbl = by_id(SB, 'obj-l19')                 # 'Steps' comment (style donor)

    SB.append(outlet_box('obj-2b', [60.0, 520.0, 30.0, 30.0]))
    SB.append({'box': clone_numbox(src, 'obj-206', 'c_obj_206', [312.0, 50.0, 52.0, 15.0],
                                   'NoteDur', 'Dur', 10.0, 16000.0, 0, 800.0, order=None)})
    SB.append({'box': clone_comment(lbl, 'obj-l22', None, 'Dur', [312.0, 34.0, 60.0, 18.0])})
    add_line(SL, 'obj-206', 0, 'obj-2b', 0)
    add_line(SL, 'obj-9', 0, 'obj-206', 0)

    tp = root['parameters']
    tp['obj-40::obj-206'] = ['NoteDur', 'Dur', 6]
    bank = tp['parameterbanks']['0']
    assert bank['name'] == 'Prism', bank['name']
    bank['parameters'][bank['parameters'].index('-')] = 'NoteDur'

    amxd.save(path, data, start, end, doc)

    def checks(r):
        sp = find_sub(r)['patcher']
        nb = by_id(sp['boxes'], 'obj-206')
        assert nb['saved_attribute_attributes']['valueof']['parameter_longname'] == 'NoteDur'
        assert r['parameters']['obj-40::obj-206'] == ['NoteDur', 'Dur', 6]
        assert 'NoteDur' in r['parameters']['parameterbanks']['0']['parameters']
        edges = {(l['patchline']['source'][0], l['patchline']['source'][1],
                  l['patchline']['destination'][0], l['patchline']['destination'][1])
                 for l in r['lines']}
        assert ('obj-40', 1, 'obj-15', 2) in edges
        sedges = {(l['patchline']['source'][0], l['patchline']['destination'][0]) for l in sp['lines']}
        assert ('obj-206', 'obj-2b') in sedges and ('obj-9', 'obj-206') in sedges
        orders = sorted(v[2] for k, v in r['parameters'].items()
                        if k not in ('parameterbanks', 'inherited_shortname', 'parameter_overrides')
                        and isinstance(v, list))
        assert orders == list(range(7)), orders
        print('   invertedprism OK: NoteDur order 6 -> makenote, %d params 0..6' % len(orders))

    verify(path, checks)


def main():
    do_multichord()
    do_invertedprism()
    for js in ('multichord.js', 'invertedprism.js'):
        nc = subprocess.run(['node', '--check', os.path.join(ROOT, 'forteseq', js)],
                            capture_output=True, text=True)
        print('node --check %s: %s' % (js, 'OK' if nc.returncode == 0 else nc.stderr.strip()))
        assert nc.returncode == 0


if __name__ == '__main__':
    main()
