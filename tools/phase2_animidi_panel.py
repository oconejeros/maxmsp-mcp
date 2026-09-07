"""Phase 2 of the ANIMIDI control reorg: make the hideable panel show only the sections
that apply to the active view / time model, instead of all-or-nothing.

Replaces the Phase-1 show/hide plumbing (a `sel 0 1` -> two giant comma-joined
`script show .../hide ...` messages -> thispatcher, plus two `striph` messages) with a
single `[js animidipanel.js]` combinator that holds the group -> box-name map and reacts
to `panel` / `viewmode` / `timemode`. See forteseq/animidipanel.js.

Removes: aw_sel_panel, aw_msg_show, aw_msg_hide, aw_msg_sh_hi, aw_msg_sh_lo (+ their lines).
Adds:    aw_pp_panel  (prepend panel)
         aw_js_panel  (js animidipanel.js, 1 in / 2 out)
Wires:   aw_settings -> [prepend panel] -> js
         aw_pp_viewmode / aw_pp_timemode -> js      (tap the already-prepended stream)
         js:0 -> thispatcher      js:1 -> jsui (obj-101)
         loadbang (obj-199) -> js  (safety re-apply)
The obj-198 `outputvalue` fan -> aw_settings stays (restores saved Panel state on load).
animidi.js already has the `striph` handler from Phase 1 -- no js change here.

Run with ANIMIDI.amxd closed in BOTH Max and Live.  Timestamped .bak first; re-reads and
self-checks, then runs check_structure.py + `node --check` on both js files.
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
PANEL_JS = os.path.join(ROOT, 'forteseq', 'animidipanel.js')

REMOVE_IDS = {'obj-selp', 'obj-msgshow', 'obj-msghide', 'obj-shhi', 'obj-shlo'}


def find_box(boxes, vn):
    for entry in boxes:
        if entry.get('box', {}).get('varname') == vn:
            return entry['box']
    raise KeyError(vn)


def main():
    assert os.path.exists(PANEL_JS), 'forteseq/animidipanel.js must exist first'

    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(PATH, PATH + '.bak-' + ts)
    print('backup: ' + PATH + '.bak-' + ts)

    data, start, end, doc = amxd.load(PATH)
    root = doc['patcher']
    win = find_box(root['boxes'], 'an_window')['patcher']
    B = win['boxes']
    L = win['lines']

    # --- 1. drop the Phase-1 all-or-nothing plumbing --------------------------------
    before_b, before_l = len(B), len(L)
    B[:] = [e for e in B if e.get('box', {}).get('id') not in REMOVE_IDS]
    L[:] = [e for e in L
            if e['patchline']['source'][0] not in REMOVE_IDS
            and e['patchline']['destination'][0] not in REMOVE_IDS]
    print('removed %d boxes, %d lines' % (before_b - len(B), before_l - len(L)))

    # --- 2. new boxes: prepend panel + js combinator -------------------------------
    pp_base = copy.deepcopy(find_box(B, 'aw_pp_grid'))       # a newobj
    for k in ('saved_attribute_attributes', 'annotation'):
        pp_base.pop(k, None)
    pp_base.pop('presentation', None)
    pp_base.pop('presentation_rect', None)

    pp = copy.deepcopy(pp_base)
    pp.update(id='obj-pppanel', varname='aw_pp_panel', text='prepend panel',
              numinlets=1, numoutlets=1, outlettype=[''], hidden=1,
              patching_rect=[16.0, 1120.0, 100.0, 22.0])
    B.append({'box': pp})

    js = copy.deepcopy(pp_base)
    js.update(id='obj-jspanel', varname='aw_js_panel', text='js animidipanel.js',
              numinlets=1, numoutlets=2, outlettype=['', ''], hidden=1,
              patching_rect=[16.0, 1150.0, 130.0, 22.0])
    B.append({'box': js})

    # --- 3. wiring ----------------------------------------------------------------
    def link(s, so, d, di):
        L.append({'patchline': {'source': [s, so], 'destination': [d, di], 'hidden': 1}})

    link('obj-set', 0, 'obj-pppanel', 0)      # Panel toggle -> prepend panel
    link('obj-pppanel', 0, 'obj-jspanel', 0)
    link('obj-133p', 0, 'obj-jspanel', 0)     # "viewmode N" (already prepended)
    link('obj-120p', 0, 'obj-jspanel', 0)     # "timemode N"
    link('obj-jspanel', 0, 'obj-thisp', 0)    # script show/hide -> thispatcher
    link('obj-jspanel', 1, 'obj-101', 0)      # striph N -> jsui
    link('obj-199', 0, 'obj-jspanel', 0)      # loadbang safety re-apply

    amxd.save(PATH, data, start, end, doc)
    print('saved: ' + PATH)

    # --- 4. verify --------------------------------------------------------------
    _, _, _, d2 = amxd.load(PATH)
    w2 = find_box(d2['patcher']['boxes'], 'an_window')['patcher']
    b2, l2 = w2['boxes'], w2['lines']
    ids = {e['box']['id'] for e in b2}
    assert not (REMOVE_IDS & ids), REMOVE_IDS & ids
    for vn in ('aw_pp_panel', 'aw_js_panel'):
        find_box(b2, vn)
    edges = {(e['patchline']['source'][0], e['patchline']['source'][1],
              e['patchline']['destination'][0], e['patchline']['destination'][1]) for e in l2}
    for e in (('obj-set', 0, 'obj-pppanel', 0), ('obj-pppanel', 0, 'obj-jspanel', 0),
              ('obj-133p', 0, 'obj-jspanel', 0), ('obj-120p', 0, 'obj-jspanel', 0),
              ('obj-jspanel', 0, 'obj-thisp', 0), ('obj-jspanel', 1, 'obj-101', 0),
              ('obj-199', 0, 'obj-jspanel', 0)):
        assert e in edges, 'missing line ' + repr(e)
    for eid in REMOVE_IDS:
        assert not any(eid in (s, d) for s, _, d, _ in edges), 'dangling line to ' + eid

    # union of animidipanel.js GROUPS must still equal the hidden panel-box set
    src = open(PANEL_JS, encoding='utf-8').read()
    import re
    grouped = set(re.findall(r'"(aw_[a-z0-9_]+)"', src))
    hidden = {e['box']['varname'] for e in b2
              if e['box'].get('hidden') == 1 and e['box'].get('varname', '').startswith('aw_')
              and e['box'].get('maxclass') in
              ('live.tab', 'live.menu', 'live.numbox', 'live.toggle', 'live.text', 'comment')}
    assert grouped == hidden, ('GROUPS vs hidden mismatch\n  only in js: %s\n  only hidden: %s'
                               % (sorted(grouped - hidden), sorted(hidden - grouped)))
    print('OK: plumbing swapped, 7 lines wired, GROUPS == %d hidden panel boxes.' % len(hidden))

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
