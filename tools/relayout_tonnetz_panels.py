"""Adaptive per-view control strip for tonnetz.amxd (ANIMIDI pattern, multi-panel case).

tonnetz's floating window had a fixed 6-row / ~182 px control strip showing every control
for all 9 visual panels at once.  This rebuilds it as a 2-row always-visible header
(y 8 panel/mode toggles, y 38 globals) plus per-view groups that show only while their
panel is on.  A new [js tonnetzpanel.js] combinator, fed by taps off each toggle's existing
[prepend <sel>] helper, sends `script show|hide|move` to a new [thispatcher] and `striph N`
to the jsui so tonnetz.js's BOX_TOP (canvas top) follows the packed-row count.

NO parameter is added / removed / reordered -- only box patching_rect/presentation_rect,
box `hidden`, three new plumbing boxes and 15 hidden cords.  tonnetz.js is edited separately
(BOX_TOP 182 -> 98, new striph() handler); this script only verifies that landed.

Run with tonnetz.amxd closed in BOTH Max and Live.  Timestamped .bak of the .amxd first;
re-reads and self-checks, then runs check_structure.py + `node --check` on both js files.
"""
import copy
import datetime
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'forteseq', 'tonnetz.amxd')
JS = os.path.join(ROOT, 'forteseq', 'tonnetz.js')
PANEL_JS = os.path.join(ROOT, 'forteseq', 'tonnetzpanel.js')

WIN_W = 1200.0

# varname -> [x, y, w, h]   (patching_rect == presentation_rect)
LAYOUT = {
    # ============ header row 1 (y 8) : panel + mode toggles -- always visible ==========
    'tzw_vwtonnetz': (8, 8, 14, 14),   'tzw_lb24_8':  (24, 8, 20, 15),
    'tzw_vwchrom':   (48, 8, 14, 14),  'tzw_lb64_8':  (64, 8, 20, 15),
    'tzw_vwfifths':  (88, 8, 14, 14),  'tzw_lb104_8': (104, 8, 20, 15),
    'tzw_vwvoice':   (128, 8, 14, 14), 'tzw_lb144_8': (144, 8, 20, 15),
    'tzw_vwpiano':   (168, 8, 14, 14), 'tzw_lb184_8': (184, 8, 20, 15),
    'tzw_vwguitar':  (208, 8, 14, 14), 'tzw_lb224_8': (224, 8, 20, 15),
    'tzw_vwdiat':    (248, 8, 14, 14), 'tzw_lb264_8': (264, 8, 20, 15),
    'tzw_vwtet':     (288, 8, 14, 14), 'tzw_lb304_8': (304, 8, 16, 15),
    'tzw_study':     (332, 8, 14, 14), 'tzw_lb26_158': (350, 8, 46, 15),   # "Estudio"
    'tzw_vcol':      (404, 8, 14, 14), 'tzw_lb346_8': (420, 8, 40, 15),    # -> "Color"
    'tzw_harmmode':  (470, 8, 14, 14), 'tzw_lb862_69': (486, 8, 54, 15),   # -> "Armonia"
    'tzw_xfprev':    (548, 8, 14, 14), 'tzw_lb86_128': (564, 8, 30, 15),   # -> "Prev"
    # ============ header row 2 (y 38) : globals -- always visible ======================
    'tzw_trace':   (8, 38, 15, 15),   'tzw_lb26_68':  (26, 40, 46, 15),   # "Rastro"
    'tzw_labels':  (78, 38, 15, 15),  'tzw_lb236_68': (96, 40, 52, 15),   # "Nombres"
    'tzw_colors':  (154, 38, 15, 15), 'tzw_lb376_68': (172, 40, 46, 15),  # "Color"
    'tzw_lb276_40': (224, 40, 32, 15), 'tzw_radius':   (258, 40, 34, 18), # "radio"
    'tzw_lb352_40': (298, 40, 32, 15), 'tzw_tracelen': (332, 40, 28, 18), # "traza"
    'tzw_lb520_70': (368, 40, 32, 15), 'tzw_huec':     (402, 40, 38, 18), # "DoHue"
    'tzw_lb598_70': (446, 40, 20, 15), 'tzw_palsat':   (468, 40, 32, 18), # "sat"
    'tzw_lb658_70': (506, 40, 20, 15), 'tzw_pallum':   (528, 40, 32, 18), # "lum"
    'tzw_l_reglum': (566, 40, 34, 15), 'tzw_reglum':   (602, 40, 44, 18), # "RegL"
    # ============ dynamic slot 0 (authored y 68) ======================================
    'tzw_preset':    (8, 68, 140, 20),
    'tzw_lb154_40':  (152, 70, 28, 15),
    'tzw_tona':      (182, 70, 26, 18),
    'tzw_tonb':      (210, 70, 26, 18),
    'tzw_tonc':      (238, 70, 26, 18),
    'tzw_harmonize': (276, 68, 15, 15), 'tzw_lb96_68':   (294, 70, 52, 15),
    'tzw_faces':     (350, 68, 15, 15), 'tzw_lb166_68':  (368, 70, 50, 15),
    'tzw_plr':       (424, 68, 15, 15), 'tzw_lb26_128':  (442, 70, 40, 15),
    'tzw_regtrace':  (488, 68, 15, 15), 'tzw_lb374_128': (506, 70, 54, 15),
    'tzw_autofit':   (566, 68, 15, 15), 'tzw_lb452_128': (584, 70, 44, 15),
    'tzw_lb_conex':  (636, 70, 34, 15),
    'tzw_conex':     (672, 68, 76, 20),
    'tzw_tracepath': (752, 68, 15, 15), 'tzw_lb306_68':  (770, 70, 52, 15),
    'tzw_lb420_40':  (830, 70, 16, 15),
    'tzw_tetpreset': (848, 68, 74, 20),
    # ============ dynamic slot 1 (authored y 98) ======================================
    'tzw_pianomode':  (8, 98, 88, 20),
    'tzw_guitarmode': (100, 98, 98, 20),
    'tzw_tuning':     (202, 98, 84, 20),
    'tzw_lb296_100':  (290, 100, 30, 15), 'tzw_frets': (322, 100, 26, 18),
    'tzw_lb360_100':  (352, 100, 30, 15), 'tzw_zoom':  (384, 100, 26, 18),
    'tzw_lb424_100':  (414, 100, 24, 15), 'tzw_pan':   (440, 100, 34, 18),
    'tzw_key':        (486, 98, 54, 20),
    'tzw_keymode':    (544, 98, 84, 20),
    'tzw_keyauto':    (632, 98, 14, 14),  'tzw_lb497_8': (648, 100, 34, 15),
    'tzw_lb726_70':   (694, 100, 36, 15), 'tzw_anwin':   (732, 100, 34, 18),
    'tzw_reset':      (772, 98, 52, 20),
    'tzw_xfmode':     (836, 98, 112, 18),
    'tzw_lb236_128':  (952, 100, 30, 15), 'tzw_xpose': (984, 100, 26, 18),
    'tzw_lb298_128':  (1014, 100, 20, 15), 'tzw_invc': (1036, 100, 26, 18),
    # ============ dynamic slot 2 (authored y 128) : study =============================
    'tzw_lb72_158':  (8, 130, 28, 15),   'tzw_studycard':  (38, 130, 24, 18),
    'tzw_lb128_158': (64, 130, 8, 15),   'tzw_studyidx':   (74, 130, 30, 18),
    'tzw_lb174_158': (108, 130, 18, 15), 'tzw_studyrot':   (128, 130, 24, 18),
    'tzw_lb222_158': (156, 130, 20, 15), 'tzw_studytonic': (178, 128, 48, 20),
    'tzw_studyinv':  (232, 128, 15, 15), 'tzw_lb316_158':  (250, 130, 20, 15),
    'tzw_disssort':  (276, 128, 15, 15), 'tzw_lb360_158':  (294, 130, 18, 15),
    'tzw_studytrav': (318, 128, 120, 20),
    'tzw_lb508_158': (442, 130, 24, 15), 'tzw_studymove':  (468, 128, 96, 20),
}

RELABEL = {'tzw_lb346_8': 'Color', 'tzw_lb862_69': 'Armonia', 'tzw_lb86_128': 'Prev'}

# always visible -> ensure no `hidden` key
HEADER = [
    'tzw_vwtonnetz', 'tzw_lb24_8', 'tzw_vwchrom', 'tzw_lb64_8', 'tzw_vwfifths', 'tzw_lb104_8',
    'tzw_vwvoice', 'tzw_lb144_8', 'tzw_vwpiano', 'tzw_lb184_8', 'tzw_vwguitar', 'tzw_lb224_8',
    'tzw_vwdiat', 'tzw_lb264_8', 'tzw_vwtet', 'tzw_lb304_8', 'tzw_study', 'tzw_lb26_158',
    'tzw_vcol', 'tzw_lb346_8', 'tzw_harmmode', 'tzw_lb862_69', 'tzw_xfprev', 'tzw_lb86_128',
    'tzw_trace', 'tzw_lb26_68', 'tzw_labels', 'tzw_lb236_68', 'tzw_colors', 'tzw_lb376_68',
    'tzw_lb276_40', 'tzw_radius', 'tzw_lb352_40', 'tzw_tracelen', 'tzw_lb520_70', 'tzw_huec',
    'tzw_lb598_70', 'tzw_palsat', 'tzw_lb658_70', 'tzw_pallum', 'tzw_l_reglum', 'tzw_reglum',
]

# per-view -> hidden:1 (tonnetzpanel.js drives them).  Must equal the js GROUPS member union.
GROUP_MEMBERS = [
    # tonnetz
    'tzw_preset', 'tzw_lb154_40', 'tzw_tona', 'tzw_tonb', 'tzw_tonc', 'tzw_harmonize',
    'tzw_lb96_68', 'tzw_faces', 'tzw_lb166_68', 'tzw_plr', 'tzw_lb26_128', 'tzw_regtrace',
    'tzw_lb374_128', 'tzw_autofit', 'tzw_lb452_128',
    # circles
    'tzw_lb_conex', 'tzw_conex', 'tzw_tracepath', 'tzw_lb306_68',
    # tet
    'tzw_lb420_40', 'tzw_tetpreset',
    # pnogtr
    'tzw_pianomode', 'tzw_guitarmode', 'tzw_tuning', 'tzw_lb296_100', 'tzw_frets',
    'tzw_lb360_100', 'tzw_zoom', 'tzw_lb424_100', 'tzw_pan',
    # diat
    'tzw_key', 'tzw_keymode', 'tzw_keyauto', 'tzw_lb497_8',
    # colorharm
    'tzw_lb726_70', 'tzw_anwin', 'tzw_reset',
    # xform
    'tzw_xfmode', 'tzw_lb236_128', 'tzw_xpose', 'tzw_lb298_128', 'tzw_invc',
    # study
    'tzw_lb72_158', 'tzw_studycard', 'tzw_lb128_158', 'tzw_studyidx', 'tzw_lb174_158',
    'tzw_studyrot', 'tzw_lb222_158', 'tzw_studytonic', 'tzw_studyinv', 'tzw_lb316_158',
    'tzw_disssort', 'tzw_lb360_158', 'tzw_studytrav', 'tzw_lb508_158', 'tzw_studymove',
]

# toggle [prepend <sel>] helper ids to tap into tonnetzpanel.js (+ studymode + loadbang)
TAP_SRC = ['obj-120p', 'obj-121p', 'obj-122p', 'obj-123p', 'obj-124p', 'obj-125p',
           'obj-126p', 'obj-127p', 'obj-216p', 'obj-215p', 'obj-262p', 'obj-318', 'obj-199']

JS_ID, JS_VN = 'obj-panel', 'tzw_panel'
TP_ID, TP_VN = 'obj-thisp', 'tzw_thisp'
CONEX_ID, CONEX_VN = 'obj-lconex', 'tzw_lb_conex'

NEW_EDGES = ([(s, 0, JS_ID, 0) for s in TAP_SRC]
             + [(JS_ID, 0, TP_ID, 0), (JS_ID, 1, 'obj-100', 0)])


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


def by_id(boxes, bid):
    for e in boxes:
        if e.get('box', {}).get('id') == bid:
            return e['box']
    raise KeyError(bid)


def by_vn(boxes, vn):
    for e in boxes:
        if e.get('box', {}).get('varname') == vn:
            return e['box']
    raise KeyError(vn)


def rect(vn):
    x, y, w, h = LAYOUT[vn]
    return [float(x), float(y), float(w), float(h)]


def main():
    assert os.path.exists(PANEL_JS), 'forteseq/tonnetzpanel.js must exist first'
    print('Run this with tonnetz.amxd CLOSED in both Max and Live.')

    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(PATH, PATH + '.bak-' + ts)
    if not os.path.exists(PATH + '.before'):
        shutil.copy(PATH, PATH + '.before')
    print('backup: ' + PATH + '.bak-' + ts)

    data, start, end, doc = amxd.load(PATH)
    root = doc['patcher']
    sb = find_sub_with_jsui(root)
    assert sb['id'] == 'obj-10', sb['id']
    P = sb['patcher']
    B, L = P['boxes'], P['lines']

    # snapshots for the no-churn assertions ------------------------------------------
    import json as _json
    snap_top = _json.dumps(root['parameters'], sort_keys=True)
    snap_sub = _json.dumps(P['parameters'], sort_keys=True)
    snap_vo = {e['box']['id']: copy.deepcopy(e['box']['saved_attribute_attributes'])
               for e in B if 'saved_attribute_attributes' in e.get('box', {})}
    snap_dep = len(P['dependency_cache'])

    existing_ids = {e['box']['id'] for e in B}
    assert not ({JS_ID, TP_ID, CONEX_ID} & existing_ids), 'id collision'

    # 1. new [js tonnetzpanel.js] (clone the pcsetinfo js box) -----------------------
    js = copy.deepcopy(by_id(B, 'obj-105'))
    js.update(id=JS_ID, varname=JS_VN, text='js tonnetzpanel.js',
              numinlets=1, numoutlets=2, outlettype=['', ''], hidden=1,
              patching_rect=[16.0, 2400.0, 150.0, 22.0],
              saved_object_attributes={'filename': 'tonnetzpanel.js', 'parameter_enable': 0})
    B.append({'box': js})

    # 2. new [thispatcher] (clone a hidden prepend newobj) --------------------------
    tp = copy.deepcopy(by_id(B, 'obj-120p'))
    for k in ('saved_attribute_attributes', 'annotation'):
        tp.pop(k, None)
    tp.update(id=TP_ID, varname=TP_VN, text='thispatcher',
              numinlets=1, numoutlets=1, outlettype=[''], hidden=1,
              patching_rect=[16.0, 2430.0, 90.0, 22.0])
    B.append({'box': tp})

    # 3. new "conex" comment (clone an existing label) -----------------------------
    cc = copy.deepcopy(by_id(B, 'obj-l306_68'))
    cc.update(id=CONEX_ID, varname=CONEX_VN, text='conex', hidden=1,
              patching_rect=rect(CONEX_VN), presentation_rect=rect(CONEX_VN), presentation=1)
    B.append({'box': cc})

    # 4. wiring -- 15 hidden cords ------------------------------------------------
    for (s, so, d, di) in NEW_EDGES:
        by_id(B, s)  # assert source exists
        L.append({'patchline': {'source': [s, so], 'destination': [d, di], 'hidden': 1}})

    # 5. relayout every header + group box -------------------------------------
    for vn in LAYOUT:
        b = by_vn(B, vn)
        r = rect(vn)
        b['patching_rect'] = list(r)
        b['presentation_rect'] = list(r)
        b['presentation'] = 1

    # 6. relabel a few header comments --------------------------------------
    for vn, txt in RELABEL.items():
        by_vn(B, vn)['text'] = txt

    # 7. hidden flags ---------------------------------------------------
    for vn in HEADER:
        by_vn(B, vn).pop('hidden', None)
    for vn in GROUP_MEMBERS:
        by_vn(B, vn)['hidden'] = 1

    # 8. widen the floating window ----------------------------------------
    P['rect'] = [P['rect'][0], P['rect'][1], WIN_W, P['rect'][3]]
    P['openrect'] = [0.0, 0.0, WIN_W, P['openrect'][3]]
    assert P.get('openinpresentation') == 0, P.get('openinpresentation')

    # 9. dependency_cache -----------------------------------------------
    P['dependency_cache'].append({
        'name': 'tonnetzpanel.js',
        'bootpath': 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq',
        'type': 'TEXT', 'implicit': 1})

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # ---- verify ----------------------------------------------------------
    _, _, _, d2 = amxd.load(PATH)
    r2 = d2['patcher']
    P2 = find_sub_with_jsui(r2)['patcher']
    B2, L2 = P2['boxes'], P2['lines']

    for vn in HEADER:
        assert by_vn(B2, vn).get('hidden') is None, 'header still hidden: ' + vn
    for vn in GROUP_MEMBERS:
        assert by_vn(B2, vn).get('hidden') == 1, 'group box not hidden: ' + vn
    for bid in (JS_ID, TP_ID, CONEX_ID):
        by_id(B2, bid)
    edges = {(e['patchline']['source'][0], e['patchline']['source'][1],
              e['patchline']['destination'][0], e['patchline']['destination'][1])
             for e in L2}
    for e in NEW_EDGES:
        assert e in edges, 'missing line ' + repr(e)
    assert P2['rect'][2] == WIN_W and P2['openrect'][2] == WIN_W
    assert P2.get('openinpresentation') == 0
    assert any(d['name'] == 'tonnetzpanel.js' for d in P2['dependency_cache'])
    assert len(P2['dependency_cache']) == snap_dep + 1

    # GROUPS in tonnetzpanel.js == the hidden group-member set
    grouped = set(re.findall(r'"(tzw_[a-z0-9_]+)"', open(PANEL_JS, encoding='utf-8').read()))
    assert grouped == set(GROUP_MEMBERS), (
        'GROUPS vs GROUP_MEMBERS\n  only js: %s\n  only script: %s'
        % (sorted(grouped - set(GROUP_MEMBERS)), sorted(set(GROUP_MEMBERS) - grouped)))
    hidden_tzw = {e['box']['varname'] for e in B2
                  if e['box'].get('hidden') == 1
                  and (e['box'].get('varname') or '').startswith('tzw_')
                  and e['box'].get('maxclass') in
                  ('live.tab', 'live.menu', 'live.numbox', 'live.toggle', 'live.text', 'comment')}
    assert hidden_tzw == set(GROUP_MEMBERS), (
        'hidden tzw_* boxes vs GROUP_MEMBERS\n  only patch: %s\n  only script: %s'
        % (sorted(hidden_tzw - set(GROUP_MEMBERS)), sorted(set(GROUP_MEMBERS) - hidden_tzw)))

    # no-churn: parameters + valueof + banks untouched
    assert _json.dumps(r2['parameters'], sort_keys=True) == snap_top, 'top parameters changed'
    assert _json.dumps(P2['parameters'], sort_keys=True) == snap_sub, 'sub parameters changed'
    for bid, vo in snap_vo.items():
        assert by_id(B2, bid)['saved_attribute_attributes'] == vo, 'valueof changed: ' + bid

    # tonnetz.js already edited by hand -- just confirm
    jsrc = open(JS, encoding='utf-8').read()
    assert 'var BOX_TOP   = 98;' in jsrc, 'tonnetz.js BOX_TOP not set to 98'
    assert jsrc.count('function striph(') == 1, 'tonnetz.js striph() missing/duplicated'

    print('OK: header %d visible, %d group boxes hidden == GROUPS, 15 cords, window %d wide, '
          'no param churn.' % (len(HEADER), len(GROUP_MEMBERS), int(WIN_W)))

    cs = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'check_structure.py'), PATH],
                        capture_output=True, text=True)
    print(cs.stdout.strip() or cs.stderr.strip())
    if cs.returncode != 0:
        sys.exit(1)
    for j in (JS, PANEL_JS):
        nc = subprocess.run(['node', '--check', j], capture_output=True, text=True)
        print('node --check %s: %s' % (os.path.basename(j),
                                       'OK' if nc.returncode == 0 else nc.stderr.strip()))
        if nc.returncode != 0:
            sys.exit(1)


if __name__ == '__main__':
    main()
