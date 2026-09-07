"""One-off: reorganise ANIMIDI.amxd's control strip into a compact always-visible row of
GLOBAL parameters plus a hideable panel that groups the per-view controls
(Barras / Curvas / Clip / Color).  Also fixes AnWin -- which was only half-registered
(box attributes set by fix_animidi_anwin_range.py, but the top-level parameters entry
still read "live.numbox" and shared order 0 with Abrir) -- and renumbers every parameter
0..N across all three registries so Live sees a clean, gap-free list.

Mechanism for the panel (verified precedent: forteseq2 voice split, [[forteseq2_voice_split]]):
a `live.toggle` "Panel" -> `sel 0 1` -> two big comma-separated `script show ... / script
hide ...` messages into a new `thispatcher`, plus `striph 62 / striph 118` into the jsui so
`animidi.js`'s `fitToWindow()` reclaims the panel's height for the canvas when it is closed.
The panel boxes are saved `hidden:1` so there is no flash on load; the loadbang
`outputvalue` fan (obj-198) re-emits the saved Panel state -> sel -> correct panel state.

Run with ANIMIDI.amxd closed in BOTH Max and Live.  Takes timestamped .bak copies of the
.amxd and the .js first.  Re-reads the file and self-checks; then run
`python tools/check_structure.py forteseq/ANIMIDI.amxd` and `node --check forteseq/animidi.js`.
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
PATH = os.path.join(ROOT, 'forteseq', 'ANIMIDI.amxd')
JS = os.path.join(ROOT, 'forteseq', 'animidi.js')

STRIP_LO = 62    # canvas top when the panel is collapsed  (must match animidi.js default)
STRIP_HI = 118   # canvas top when the panel is open


def find_box(boxes, vn):
    for entry in boxes:
        b = entry.get('box', {})
        if b.get('varname') == vn:
            return b
    raise KeyError(vn)


def find_by_id(boxes, bid):
    for entry in boxes:
        b = entry.get('box', {})
        if b.get('id') == bid:
            return b
    raise KeyError(bid)


# ---- new geometry -----------------------------------------------------------------------
# x, y, w, h  (patching_rect == presentation_rect for every control in this strip)
LAYOUT = {
    # visible row 1 (y=8) -- selectors / global
    'aw_lb8_72':    (8,   10, 30, 17),   # "vista"
    'aw_viewmode':  (40,   8, 196, 20),
    'aw_timemode':  (286,  8, 116, 20),
    'aw_colormode': (446,  9, 120, 15),
    'aw_voicemode': (614,  9, 120, 15),
    'aw_rangemode': (784,  8, 96, 20),
    # visible row 2 (y=36) -- range / clear / panel toggle
    'aw_lb100_42':  (8,   38, 16, 17),   # "lo"
    'aw_rangelo':   (26,  36, 40, 15),
    'aw_lb168_42':  (72,  38, 16, 17),   # "hi"
    'aw_rangehi':   (90,  36, 40, 15),
    'aw_lb236_42':  (138, 38, 22, 17),   # "fps"
    'aw_fps':       (162, 36, 40, 15),
    'aw_clear':     (214, 36, 60, 20),
    # ---- hideable panel row 1 (y=66) : BARRAS + CURVAS ----
    'aw_lb436_10':  (62,  68, 26, 17),   # "grid"  (was "Grid")
    'aw_grid':      (90,  67, 16, 16),
    'aw_lb8_42':    (112, 68, 30, 17),   # "px/s"
    'aw_scale':     (146, 66, 44, 15),
    'aw_lb740_72':  (196, 68, 34, 17),   # "piano"
    'aw_piano':     (232, 67, 16, 16),
    'aw_lb800_72':  (254, 68, 20, 17),   # "vel"
    'aw_vellane':   (276, 67, 16, 16),
    'aw_lb846_72':  (298, 68, 34, 17),   # "notas"
    'aw_notetags':  (334, 67, 16, 16),
    'aw_lb906_72':  (356, 68, 24, 17),   # "arm"
    'aw_harmlane':  (382, 67, 16, 16),
    'aw_lb440_72':  (470, 68, 24, 17),   # "giro"
    'aw_spin':      (496, 66, 34, 15),
    'aw_lb590_72':  (536, 68, 34, 17),   # "segun"
    'aw_spinmode':  (572, 66, 100, 15),
    'aw_lb510_72':  (678, 68, 36, 17),   # "anillo"
    'aw_ringgap':   (716, 66, 34, 15),
    'aw_lb366_72':  (756, 68, 30, 17),   # "traza"
    'aw_tracelen':  (788, 66, 34, 15),
    # ---- hideable panel row 2 (y=94) : CLIP + COLOR ----
    'aw_readclip':  (48,  94, 76, 20),
    'aw_lb468_42':  (190, 96, 14, 17),   # "C"
    'aw_huec':      (206, 94, 40, 15),
    'aw_lb532_42':  (252, 96, 22, 17),   # "sat"
    'aw_palsat':    (276, 94, 34, 15),
    'aw_lb596_42':  (316, 96, 24, 17),   # "lum"
    'aw_pallum':    (342, 94, 34, 15),
    'aw_lb956_72':  (382, 96, 18, 17),   # "an"
    'aw_anwin':     (402, 94, 44, 15),
}

# existing boxes that move into the hideable panel (get hidden:1)
PANEL_EXISTING = [
    'aw_lb436_10', 'aw_grid', 'aw_lb8_42', 'aw_scale',
    'aw_lb740_72', 'aw_piano', 'aw_lb800_72', 'aw_vellane',
    'aw_lb846_72', 'aw_notetags', 'aw_lb906_72', 'aw_harmlane',
    'aw_lb440_72', 'aw_spin', 'aw_lb590_72', 'aw_spinmode',
    'aw_lb510_72', 'aw_ringgap', 'aw_lb366_72', 'aw_tracelen',
    'aw_readclip',
    'aw_lb468_42', 'aw_huec', 'aw_lb532_42', 'aw_palsat',
    'aw_lb596_42', 'aw_pallum', 'aw_lb956_72', 'aw_anwin',
]
# section headers created by this script, also part of the panel
PANEL_SECTIONS = ['aw_sec_barras', 'aw_sec_curvas', 'aw_sec_clip', 'aw_sec_color']

# parameter order, bank-major -> (name, box id).  Abrir lives in the ROOT patcher (obj-20);
# everything else is nested in an_window (obj-10::<id>).
ORDER = [
    ('ViewMode', 'obj-133'), ('TimeMode', 'obj-120'), ('ColorMode', 'obj-121'),
    ('VoiceMode', 'obj-134'), ('RangeMode', 'obj-122'), ('RangeLo', 'obj-125'),
    ('RangeHi', 'obj-126'), ('Fps', 'obj-127'),
    ('Grid', 'obj-123'), ('Scale', 'obj-124'), ('Piano', 'obj-139'),
    ('VelLane', 'obj-140'), ('NoteTags', 'obj-141'), ('HarmLane', 'obj-142'),
    ('Clear', 'obj-129'), ('Abrir', 'obj-20'),
    ('Spin', 'obj-136'), ('SpinMode', 'obj-138'), ('RingGap', 'obj-137'),
    ('TraceLen', 'obj-135'),
    ('HueC', 'obj-130'), ('PalSat', 'obj-131'), ('PalLum', 'obj-132'),
    ('AnWin', 'obj-4'), ('ReadClip', 'obj-128'), ('Panel', 'obj-set'),
]
BANKS = [
    ('Global', ['ViewMode', 'TimeMode', 'ColorMode', 'VoiceMode',
                'RangeMode', 'RangeLo', 'RangeHi', 'Fps']),
    ('Barras', ['Grid', 'Scale', 'Piano', 'VelLane',
                'NoteTags', 'HarmLane', 'Clear', 'Abrir']),
    ('Curvas', ['Spin', 'SpinMode', 'RingGap', 'TraceLen', '-', '-', '-', '-']),
    ('Color/Clip', ['HueC', 'PalSat', 'PalLum', 'AnWin', 'ReadClip', 'Panel', '-', '-']),
]


def main():
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    for p in (PATH, JS):
        shutil.copy(p, p + '.bak-' + ts)
    print('backups: *.bak-' + ts)

    data, start, end, doc = amxd.load(PATH)
    root = doc['patcher']
    win = find_box(root['boxes'], 'an_window')['patcher']
    B = win['boxes']
    L = win['lines']

    # --- 1. relayout existing boxes ------------------------------------------------------
    for vn, (x, y, w, h) in LAYOUT.items():
        b = find_box(B, vn)
        b['patching_rect'] = [float(x), float(y), float(w), float(h)]
        b['presentation_rect'] = [float(x), float(y), float(w), float(h)]
        b['presentation'] = 1
    find_box(B, 'aw_lb436_10')['text'] = 'grid'

    # --- 2. hide the panel boxes (no flash on load) ------------------------------------
    for vn in PANEL_EXISTING:
        find_box(B, vn)['hidden'] = 1

    # --- 3. new comment labels --------------------------------------------------------
    lb_base = find_box(B, 'aw_lb8_72')

    def new_comment(vn, bid, text, x, y, w, h, hidden=False, fs=9.0):
        c = copy.deepcopy(lb_base)
        c['id'] = bid
        c['varname'] = vn
        c['text'] = text
        c['fontsize'] = float(fs)
        c['patching_rect'] = [float(x), float(y), float(w), float(h)]
        c['presentation_rect'] = [float(x), float(y), float(w), float(h)]
        c['presentation'] = 1
        c.pop('hidden', None)
        if hidden:
            c['hidden'] = 1
        B.append({'box': c})
        return c

    new_comment('aw_lb_tiempo', 'obj-r1a', 'tiempo', 244, 10, 42, 17)
    new_comment('aw_lb_color', 'obj-r1b', 'color', 410, 11, 34, 17)
    new_comment('aw_lb_voces', 'obj-r1c', 'voces', 574, 11, 38, 17)
    new_comment('aw_lb_rango', 'obj-r1d', 'rango', 742, 10, 40, 17)
    new_comment('aw_lb_panel', 'obj-setl', 'panel', 388, 38, 34, 17)
    new_comment('aw_sec_barras', 'obj-sc1', 'BARRAS', 8, 68, 50, 17, hidden=True)
    new_comment('aw_sec_curvas', 'obj-sc2', 'CURVAS', 416, 68, 50, 17, hidden=True)
    new_comment('aw_sec_clip', 'obj-sc3', 'CLIP', 8, 96, 36, 17, hidden=True)
    new_comment('aw_sec_color', 'obj-sc4', 'COLOR', 140, 96, 44, 17, hidden=True)

    # --- 4. aw_settings : live.toggle parameter "Panel" ------------------------------
    tg = copy.deepcopy(find_box(B, 'aw_grid'))
    tg['id'] = 'obj-set'
    tg['varname'] = 'aw_settings'
    tg['patching_rect'] = [356.0, 36.0, 18.0, 18.0]
    tg['presentation_rect'] = [356.0, 36.0, 18.0, 18.0]
    tg['presentation'] = 1
    tg.pop('hidden', None)
    tg['annotation'] = ('Muestra/oculta el panel de ajustes por vista '
                        '(BARRAS / CURVAS / CLIP / COLOR).')
    tvo = tg['saved_attribute_attributes']['valueof']
    tvo['parameter_longname'] = 'Panel'
    tvo['parameter_shortname'] = 'Panel'
    tvo['parameter_initial'] = [0]
    tvo['parameter_initial_enable'] = 1
    B.append({'box': tg})

    # --- 5. plumbing: thispatcher, sel, show/hide + striph messages -----------------
    pp_base = find_box(B, 'aw_pp_grid')      # a newobj
    msg_base = find_box(B, 'aw_msg_clear')   # a message

    def new_obj(vn, bid, text, x, y, w, h, nin, nout):
        o = copy.deepcopy(pp_base)
        o['id'] = bid
        o['varname'] = vn
        o['text'] = text
        o['numinlets'] = nin
        o['numoutlets'] = nout
        o['outlettype'] = [''] * nout
        o['patching_rect'] = [float(x), float(y), float(w), float(h)]
        o.pop('presentation', None)
        o.pop('presentation_rect', None)
        o['hidden'] = 1
        B.append({'box': o})
        return o

    def new_msg(vn, bid, text, x, y, w, h):
        m = copy.deepcopy(msg_base)
        m['id'] = bid
        m['varname'] = vn
        m['text'] = text
        m['numinlets'] = 2
        m['numoutlets'] = 1
        m['outlettype'] = ['']
        m['patching_rect'] = [float(x), float(y), float(w), float(h)]
        m.pop('presentation', None)
        m.pop('presentation_rect', None)
        m.pop('annotation', None)
        m.pop('saved_attribute_attributes', None)
        m.pop('parameter_enable', None)
        m['hidden'] = 1
        B.append({'box': m})
        return m

    new_obj('aw_thisp', 'obj-thisp', 'thispatcher', 16.0, 1180.0, 80.0, 22.0, 1, 1)
    new_obj('aw_sel_panel', 'obj-selp', 'sel 0 1', 16.0, 1148.0, 60.0, 22.0, 2, 3)

    panel_all = PANEL_SECTIONS + PANEL_EXISTING
    show_txt = ', '.join('script show %s' % v for v in panel_all)
    hide_txt = ', '.join('script hide %s' % v for v in panel_all)
    new_msg('aw_msg_show', 'obj-msgshow', show_txt, 100.0, 1210.0, 440.0, 22.0)
    new_msg('aw_msg_hide', 'obj-msghide', hide_txt, 100.0, 1240.0, 440.0, 22.0)
    new_msg('aw_msg_sh_hi', 'obj-shhi', 'striph %d' % STRIP_HI, 560.0, 1210.0, 80.0, 22.0)
    new_msg('aw_msg_sh_lo', 'obj-shlo', 'striph %d' % STRIP_LO, 560.0, 1240.0, 80.0, 22.0)

    def link(s, so, d, di):
        L.append({'patchline': {'source': [s, so], 'destination': [d, di], 'hidden': 1}})

    link('obj-set', 0, 'obj-selp', 0)
    link('obj-selp', 0, 'obj-msghide', 0)   # sel matched 0 -> hide
    link('obj-selp', 0, 'obj-shlo', 0)
    link('obj-selp', 1, 'obj-msgshow', 0)   # sel matched 1 -> show
    link('obj-selp', 1, 'obj-shhi', 0)
    link('obj-msgshow', 0, 'obj-thisp', 0)
    link('obj-msghide', 0, 'obj-thisp', 0)
    link('obj-shhi', 0, 'obj-101', 0)       # -> jsui
    link('obj-shlo', 0, 'obj-101', 0)
    link('obj-198', 0, 'obj-set', 0)        # loadbang outputvalue fan re-emits Panel

    # --- 6. parameter registries: renumber, banks, AnWin fix -----------------------
    tp = root['parameters']
    for i, (name, bid) in enumerate(ORDER):
        key = 'obj-20' if bid == 'obj-20' else 'obj-10::' + bid
        cur = tp.get(key)
        if isinstance(cur, list) and len(cur) >= 3:
            cur[0], cur[1], cur[2] = name, name, i
        else:
            tp[key] = [name, name, i]
        boxes = root['boxes'] if bid == 'obj-20' else B
        vo = find_by_id(boxes, bid).setdefault(
            'saved_attribute_attributes', {}).setdefault('valueof', {})
        vo['parameter_order'] = i
        if name == 'AnWin':
            vo['parameter_longname'] = 'AnWin'
            vo['parameter_shortname'] = 'AnWin'

    pb = tp['parameterbanks']
    for idx, (bank_name, params) in enumerate(BANKS):
        pb[str(idx)]['name'] = bank_name
        pb[str(idx)]['parameters'] = list(params)

    # --- 7. jsui initial rect (collapsed) -----------------------------------------
    ui = find_box(B, 'aw_ui')
    ui['patching_rect'] = [8.0, float(STRIP_LO), 1312.0, 752.0]
    ui['presentation_rect'] = [8.0, float(STRIP_LO), 1312.0, 752.0]

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # --- 8. animidi.js : mutable STRIP_H + striph() handler ----------------------
    src = open(JS, encoding='utf-8').read()
    old = 'var STRIP_H = 96;   // control-strip height / jsui y -- must match build_animidi.py'
    new = ('var STRIP_H = %d;   // jsui y / control-strip height -- panel collapsed; '
           'striph() sets it (open ~%d). reorg_animidi_controls.py' % (STRIP_LO, STRIP_HI))
    assert old in src, 'STRIP_H line not found verbatim in animidi.js'
    src = src.replace(old, new, 1)
    anchor = ('function refresh() { resolveMyVoice(); fitToWindow(); mgraphics.redraw(); }\n')
    assert anchor in src, 'refresh() anchor not found in animidi.js'
    handler = anchor + (
        '// panel toggle (aw_settings -> striph <canvasTop>): move the strip reserve so the\n'
        '// canvas reclaims the hideable panel height when it is closed.\n'
        'function striph(v) {\n'
        '\tv = Math.max(24, Math.round(v));\n'
        '\tif (v === STRIP_H) return;\n'
        '\tSTRIP_H = v;\n'
        '\tfitToWindow();\n'
        '\tmgraphics.redraw();\n'
        '}\n')
    src = src.replace(anchor, handler, 1)
    open(JS, 'w', encoding='utf-8', newline='\n').write(src)
    print('patched: ' + JS)

    # --- 9. verify --------------------------------------------------------------
    _, _, _, d2 = amxd.load(PATH)
    r2 = d2['patcher']
    w2 = find_box(r2['boxes'], 'an_window')['patcher']
    b2 = w2['boxes']

    meta = ('parameterbanks', 'inherited_shortname', 'parameter_overrides')
    orders = sorted(v[2] for k, v in r2['parameters'].items()
                    if k not in meta and isinstance(v, list))
    assert orders == list(range(len(ORDER))), orders

    names_in_reg = {v[0] for k, v in r2['parameters'].items()
                    if k not in meta and isinstance(v, list)}
    for bank_name, params in BANKS:
        for p in params:
            if p != '-':
                assert p in names_in_reg, 'bank %s references missing param %s' % (bank_name, p)

    aw = find_by_id(b2, 'obj-4')['saved_attribute_attributes']['valueof']
    assert aw['parameter_longname'] == 'AnWin' and aw['parameter_order'] == 23, aw
    assert r2['parameters']['obj-10::obj-4'][0] == 'AnWin', r2['parameters']['obj-10::obj-4']

    for vn in ('aw_settings', 'aw_thisp', 'aw_sel_panel', 'aw_msg_show', 'aw_msg_hide',
               'aw_msg_sh_hi', 'aw_msg_sh_lo') + tuple(PANEL_SECTIONS):
        find_box(b2, vn)
    for vn in PANEL_EXISTING + list(PANEL_SECTIONS):
        assert find_box(b2, vn).get('hidden') == 1, 'panel box not hidden: ' + vn
    assert find_box(b2, 'aw_settings').get('hidden') is None

    src2 = open(JS, encoding='utf-8').read()
    assert ('var STRIP_H = %d;' % STRIP_LO) in src2
    assert 'function striph(v) {' in src2
    print('OK: orders 0..%d, banks resolve, AnWin registered (order 23), '
          'panel boxes hidden, js patched.' % (len(ORDER) - 1))

    cs = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'check_structure.py'), PATH],
                        capture_output=True, text=True)
    print(cs.stdout.strip())
    if cs.returncode != 0:
        print(cs.stderr.strip())
        sys.exit(1)
    nc = subprocess.run(['node', '--check', JS], capture_output=True, text=True)
    print('node --check animidi.js: ' + ('OK' if nc.returncode == 0 else nc.stderr.strip()))
    if nc.returncode != 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
