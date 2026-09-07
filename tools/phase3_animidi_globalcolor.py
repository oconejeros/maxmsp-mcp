"""Phase 3 of the ANIMIDI control reorg (user feedback on the Phase-2 screenshots):

  * colour params (HueC / PalSat / PalLum) + AnWin are GLOBAL -- promote them out of the
    hideable panel into the always-visible header (row 2).
  * fold everything into a 3-row header at the top; drop the separate lower panel.
    row 1 = selectors, row 2 = range + colour + AnWin + Clear + Panel toggle,
    row 3 = the per-view controls, auto-swapped by ViewMode/TimeMode (animidipanel.js),
    hidden as a block by the Panel toggle.
  * AnWin + HarmLane were effectively invisible in the cramped Phase-2 panel -- the new
    layout gives them real slots (AnWin now always visible in row 2; HarmLane in the
    Barras row-3 group).
  * remove the BARRAS/CURVAS/CLIP/COLOR section-header comments (the jsui already prints
    the active view); animidipanel.js GROUPS lose the `color` group and the headers.

animidipanel.js is rewritten separately (already done).  This script only re-lays-out
ANIMIDI.amxd, un-hides the colour block, deletes the 4 section headers, relabels two
comments, sets the Panel toggle default ON, and drops STRIP_H to 58 in animidi.js.

Run with ANIMIDI.amxd closed in BOTH Max and Live.  Timestamped .bak of the .amxd and the
.js; re-reads and self-checks; runs check_structure.py + `node --check` on both js files.
"""
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
PANEL_JS = os.path.join(ROOT, 'forteseq', 'animidipanel.js')

STRIP_LO = 58   # animidi.js STRIP_H default (row 3 hidden); animidipanel.js sends 84 when shown

# varname -> [x, y, w, h]   (patching_rect == presentation_rect)
LAYOUT = {
    # ---- row 1 : selectors (always visible) --------------------------------------
    'aw_lb8_72':    (8,   10, 30, 17),   # "vista"
    'aw_viewmode':  (40,   8, 196, 20),
    'aw_lb_tiempo': (244, 10, 42, 17),
    'aw_timemode':  (288,  8, 116, 20),
    'aw_lb_color':  (412, 11, 34, 17),
    'aw_colormode': (448,  9, 120, 15),
    'aw_lb_voces':  (576, 11, 38, 17),
    'aw_voicemode': (616,  9, 120, 15),
    'aw_lb_rango':  (744, 10, 40, 17),
    'aw_rangemode': (786,  8, 96, 20),
    # ---- row 2 : range + colour + AnWin + Clear + Panel toggle (always visible) --
    'aw_lb100_42':  (8,   36, 16, 17),   # "lo"
    'aw_rangelo':   (26,  34, 40, 15),
    'aw_lb168_42':  (72,  36, 16, 17),   # "hi"
    'aw_rangehi':   (90,  34, 40, 15),
    'aw_lb236_42':  (138, 36, 22, 17),   # "fps"
    'aw_fps':       (162, 34, 40, 15),
    'aw_lb468_42':  (214, 36, 26, 17),   # "hue"  (was "C")
    'aw_huec':      (240, 34, 40, 15),
    'aw_lb532_42':  (286, 36, 22, 17),   # "sat"
    'aw_palsat':    (310, 34, 34, 15),
    'aw_lb596_42':  (350, 36, 24, 17),   # "lum"
    'aw_pallum':    (376, 34, 34, 15),
    'aw_lb956_72':  (416, 36, 24, 17),   # "win"  (was "an")
    'aw_anwin':     (442, 34, 44, 15),
    'aw_clear':     (500, 34, 56, 20),
    'aw_settings':  (566, 34, 18, 18),
    'aw_lb_panel':  (588, 36, 30, 17),   # "panel"
    # ---- row 3 : per-view, auto-swapped, hidden:1 ------------------------------
    # Barras group
    'aw_lb436_10':  (8,   60, 26, 17),   # "grid"
    'aw_grid':      (36,  59, 16, 16),
    'aw_lb740_72':  (140, 60, 34, 17),   # "piano"
    'aw_piano':     (176, 59, 16, 16),
    'aw_lb800_72':  (198, 60, 20, 17),   # "vel"
    'aw_vellane':   (220, 59, 16, 16),
    'aw_lb846_72':  (240, 60, 34, 17),   # "notas"
    'aw_notetags':  (276, 59, 16, 16),
    'aw_lb906_72':  (298, 60, 24, 17),   # "arm"
    'aw_harmlane':  (324, 59, 16, 16),
    # scale group (Barras + Practica)
    'aw_lb8_42':    (60,  60, 30, 17),   # "px/s"
    'aw_scale':     (94,  58, 40, 15),
    # Curvas group
    'aw_lb440_72':  (8,   60, 24, 17),   # "giro"
    'aw_spin':      (34,  58, 34, 15),
    'aw_lb590_72':  (78,  60, 34, 17),   # "segun"
    'aw_spinmode':  (114, 58, 100, 15),
    'aw_lb510_72':  (222, 60, 36, 17),   # "anillo"
    'aw_ringgap':   (260, 58, 34, 15),
    'aw_lb366_72':  (300, 60, 30, 17),   # "traza"
    'aw_tracelen':  (332, 58, 34, 15),
    # Clip group (Lookahead only) -- far right so it never collides with the above
    'aw_readclip':  (700, 58, 76, 20),
}

RELABEL = {'aw_lb468_42': 'hue', 'aw_lb956_72': 'win', 'aw_lb436_10': 'grid'}

# now always visible (colour is global) -- clear hidden:1
UNHIDE = ['aw_lb468_42', 'aw_huec', 'aw_lb532_42', 'aw_palsat',
          'aw_lb596_42', 'aw_pallum', 'aw_lb956_72', 'aw_anwin']

# row-3 boxes that animidipanel.js shows/hides per view -- must stay hidden:1
ROW3 = ['aw_lb436_10', 'aw_grid', 'aw_lb740_72', 'aw_piano', 'aw_lb800_72', 'aw_vellane',
        'aw_lb846_72', 'aw_notetags', 'aw_lb906_72', 'aw_harmlane',
        'aw_lb8_42', 'aw_scale',
        'aw_lb440_72', 'aw_spin', 'aw_lb590_72', 'aw_spinmode',
        'aw_lb510_72', 'aw_ringgap', 'aw_lb366_72', 'aw_tracelen',
        'aw_readclip']

DROP = {'obj-sc1', 'obj-sc2', 'obj-sc3', 'obj-sc4'}   # section headers


def find_box(boxes, vn):
    for entry in boxes:
        if entry.get('box', {}).get('varname') == vn:
            return entry['box']
    raise KeyError(vn)


def main():
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    for p in (PATH, JS):
        shutil.copy(p, p + '.bak-' + ts)
    print('backups: *.bak-' + ts)

    data, start, end, doc = amxd.load(PATH)
    root = doc['patcher']
    win = find_box(root['boxes'], 'an_window')['patcher']
    B = win['boxes']

    # 1. drop the section-header comments (no patchlines reference them)
    n0 = len(B)
    B[:] = [e for e in B if e.get('box', {}).get('id') not in DROP]
    assert len(B) == n0 - 4, len(B)

    # 2. relayout
    for vn, (x, y, w, h) in LAYOUT.items():
        b = find_box(B, vn)
        b['patching_rect'] = [float(x), float(y), float(w), float(h)]
        b['presentation_rect'] = [float(x), float(y), float(w), float(h)]
        b['presentation'] = 1

    # 3. relabel
    for vn, txt in RELABEL.items():
        find_box(B, vn)['text'] = txt

    # 4. colour block is global now -- un-hide
    for vn in UNHIDE:
        find_box(B, vn).pop('hidden', None)
    # 5. row 3 stays hidden:1 (animidipanel.js drives it)
    for vn in ROW3:
        find_box(B, vn)['hidden'] = 1

    # 6. Panel toggle defaults ON (row 3 visible on load)
    tvo = find_box(B, 'aw_settings')['saved_attribute_attributes']['valueof']
    tvo['parameter_initial'] = [1]
    tvo['parameter_initial_enable'] = 1

    # 7. canvas top when row 3 hidden
    ui = find_box(B, 'aw_ui')
    ui['patching_rect'] = [8.0, float(STRIP_LO), 1312.0, 752.0]
    ui['presentation_rect'] = [8.0, float(STRIP_LO), 1312.0, 752.0]

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # 8. animidi.js STRIP_H default 62 -> 58
    src = open(JS, encoding='utf-8').read()
    old = ('var STRIP_H = 62;   // jsui y / control-strip height -- panel collapsed; '
           'striph() sets it (open ~118). reorg_animidi_controls.py')
    new = ('var STRIP_H = %d;   // jsui y -- row 3 hidden; striph() sets it (row 3 shown ~84). '
           'phase3_animidi_globalcolor.py' % STRIP_LO)
    assert old in src, 'STRIP_H line not found verbatim in animidi.js'
    open(JS, 'w', encoding='utf-8', newline='\n').write(src.replace(old, new, 1))
    print('patched: ' + JS)

    # 9. verify
    _, _, _, d2 = amxd.load(PATH)
    w2 = find_box(d2['patcher']['boxes'], 'an_window')['patcher']
    b2 = w2['boxes']
    ids = {e['box']['id'] for e in b2}
    assert not (DROP & ids), DROP & ids
    for vn in UNHIDE:
        assert find_box(b2, vn).get('hidden') is None, 'still hidden: ' + vn
    for vn in ROW3:
        assert find_box(b2, vn).get('hidden') == 1, 'row-3 box not hidden: ' + vn
    assert find_box(b2, 'aw_settings')['saved_attribute_attributes']['valueof'][
        'parameter_initial'] == [1]
    assert find_box(b2, 'aw_lb468_42')['text'] == 'hue'
    assert find_box(b2, 'aw_lb956_72')['text'] == 'win'

    import re
    grouped = set(re.findall(r'"(aw_[a-z0-9_]+)"', open(PANEL_JS, encoding='utf-8').read()))
    hidden = {e['box']['varname'] for e in b2
              if e['box'].get('hidden') == 1 and (e['box'].get('varname') or '').startswith('aw_')
              and e['box'].get('maxclass') in
              ('live.tab', 'live.menu', 'live.numbox', 'live.toggle', 'live.text', 'comment')}
    assert grouped == hidden, ('GROUPS vs hidden mismatch\n  only js: %s\n  only hidden: %s'
                               % (sorted(grouped - hidden), sorted(hidden - grouped)))
    assert ('var STRIP_H = %d;' % STRIP_LO) in open(JS, encoding='utf-8').read()
    print('OK: colour block global (row 2), %d row-3 boxes == GROUPS, sections dropped, '
          'Panel default ON, STRIP_H=%d.' % (len(hidden), STRIP_LO))

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
