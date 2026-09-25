"""FORTESEQ2 device view: 11-item vertical page list -> 9 big horizontal tabs, only the essentials always visible.

    python tools/repage_fs2_tabs.py                    dry run: prints the plan, runs the layout checks
    python tools/repage_fs2_tabs.py --preview DIR      also writes one PNG per tab into DIR (needs Pillow)
    python tools/repage_fs2_tabs.py --apply            write FORTESEQ2.amxd (+ .before-tabs backup)
    (device closed in Max AND Live -- whichever saves last silently overwrites the other)

New Pagina enum (obj-485, fs2_pagina), horizontal bar along the top:

    0 Armonia  1 Filtro  2 Artic  3 Tiempo  4 Modul  5 Voces  6 Ornam  7 Sesion  8 Global

* Tabs 0-4 and 7 show the fs2_pages bpatcher scrolled to their 150px band (Armonia/Artic/Sesion also show a
  few loose top-level controls that used to sit all over the main panel).
* 5 Voces = the four fs2voice_adv bpatchers (vadv1-4) with a small non-parameter `tab` selector over their
  4 sub-pages (Disp/Artic/Orn/Tono = old Voces 1/2/3/4). 6 Ornam = the Ornamento block that used to be
  always visible. 8 Global = Clock/Rate/Bus/Voces/Trig + Dir/SalL/Pasa/Mon/Col/Ind/Flt/Lck.
* Always visible: Run, Lec/Ord/Rng, the four V strips, the colour monitor, the readouts, and the popup
  door (Proximos 16 + Vista Popup).

Mechanics -- everything is a plain presentation move + `script show/hide` (the same trick the old Globales
tab and vadv1-4 already used successfully in M4L presentation view). NO Live parameter is added, removed or
renamed, so the three parameter registries are untouched:

  obj-485 -> [sel 0..8] -> one message per tab (hide the other tabs' controls, show its own, `script front`
  them above the pages bpatcher, scroll fs2_pages) -> [thispatcher] obj-487.
  Tab 5 also pokes the Voces sub-selector so the current sub-page is applied.
  The old chain (obj-486 sel + its sendbox messages, obj-582, obj-617/618/619, obj-808, obj-723) is removed;
  the four sub-page messages obj-721/722/800/804 are kept and now hang off the sub-selector.

The floating popup sends `gotopage <n>`: 0..8 = a tab; 20..23 = Voces sub-page 0..3. obj-819's first outlet
now goes through [sel 20 21 22 23] (matches -> set the sub-selector + go to tab 5, reject -> obj-485).
fs2horizon.js's PAGE_VOCES1..4 must be 20..23 (done in the same commit).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'FORTESEQ2.amxd')
PAGES = os.path.join(ROOT, 'forteseq', 'fs2pages.maxpat')

TAB_NAMES = ['Armonia', 'Filtro', 'Artic', 'Tiempo', 'Modul', 'Voces', 'Ornam', 'Sesion', 'Global']
T_ARM, T_FIL, T_ART, T_TIE, T_MOD, T_VOC, T_ORN, T_SES, T_GLB = range(9)
BAND = {T_ARM: 0, T_FIL: 150, T_ART: 300, T_TIE: 450, T_MOD: 600, T_SES: 750}   # fs2_pages scroll offsets
PAGES_TABS = sorted(BAND)

DEVICE_H = 169.0            # openrect height -- nothing may reach below this
CX, CY, CW, CH = 294.0, 30.0, 366.0, 120.0     # content region (the fs2_pages viewport)
RIGHT_X = 664.0             # right column: popup door + readouts
DEVICE_W = 770.0

V_DX = -186.0               # vadv1-4 + vah* headers moved from x=482 to x=296

# ----------------------------------------------------------------------------------------------------
# Placement tables.  id -> (x, y) or (x, y, w, h).  Boxes not listed keep their rect.
# ----------------------------------------------------------------------------------------------------
ALWAYS = {
    'obj-660': (190, 30),                     # colour monitor jsui, next to the V strips
    'obj-234': (190, 143),                    # note-name readout, under it
    'obj-524': (294, 151),                    # forte readout, status strip
    'obj-745': (668, 32, 92, 22),             # Proximos 16
    'obj-793': (668, 58),                     # 'Vista' label
    'obj-806': (668, 72, 92, 18),             # Vista Popup
    'obj-521': (668, 96), 'obj-522': (694, 96, 66, 18),   # Set idx readout
    'obj-672': (668, 116), 'obj-671': (696, 116),         # root readout
    'obj-536': (722, 116), 'obj-535': (750, 116),         # bus colour chip
    'obj-485': (262, 3, 502, 24),             # the tab bar
    'obj-484': (CX, CY, CW, CH),              # fs2_pages viewport
}
# Untouched, always visible: Run/Lec/Ord/Rng + V strips
ALWAYS_KEEP = ['obj-37', 'obj-18', 'obj-638', 'obj-636', 'obj-647', 'obj-645', 'obj-622', 'obj-620',
               'obj-91', 'obj-528', 'obj-357', 'obj-529', 'obj-530', 'obj-51', 'obj-52', 'obj-53', 'obj-54',
               'obj-71', 'obj-72', 'obj-73', 'obj-74']

GROUPS = {
    T_ARM: {      # loose controls that belong with harmony, right of the page content
        'obj-702': (516, 33), 'obj-700': (516, 47),          # Root
        'obj-715': (566, 33), 'obj-706': (566, 46),          # Sub
        'obj-670': (516, 68), 'obj-668': (516, 82),          # Oct M
        'obj-667': (556, 68), 'obj-665': (556, 82),          # Raiz sec
    },
    T_ART: {
        'obj-705': (560, 33), 'obj-703': (560, 47),          # Preset Silencio
        'obj-738': (560, 68), 'obj-736': (560, 82),          # S.Nor
        'obj-739': (600, 68), 'obj-737': (600, 82),          # S.Ac
        'obj-718': (560, 104), 'obj-716': (560, 118),        # Human
    },
    T_SES: {
        'obj-632': (566, 33), 'obj-633': (584, 33), 'obj-634': (602, 33),    # F P S labels
        'obj-623': (566, 48), 'obj-625': (584, 48), 'obj-627': (602, 48),    # Fav / Prog Fav / Solo Fav
        'obj-724': (566, 82),                                 # Reparto
        'obj-726': (592, 118), 'obj-727': (618, 118), 'obj-728': (566, 118),  # Rnd Sil(mask) / Acc / Set
        'obj-732': (566, 138),                                # Tirar
    },
    T_ORN: {
        'obj-758': (296, 32),
        'obj-759': (296, 50), 'obj-760': (330, 52),          # Base
        'obj-761': (296, 70), 'obj-762': (330, 69),          # Tipo
        'obj-763': (296, 90), 'obj-764': (336, 92),          # Notas
        'obj-768': (436, 50), 'obj-769': (476, 49),          # B.Modo
        'obj-770': (436, 70), 'obj-771': (476, 72),          # B.Paso
        'obj-774': (436, 90), 'obj-775': (476, 89),          # B.Cuar
        'obj-777': (296, 112), 'obj-778': (334, 114),        # S.Inic
        'obj-779': (366, 112), 'obj-780': (404, 114),        # S.Paso
        'obj-781': (436, 112), 'obj-782': (474, 114),        # S.Pico
    },
    T_GLB: {
        'obj-38': (296, 33), 'obj-13': (296, 46),            # Clock
        'obj-39': (368, 33), 'obj-480': (368, 46),           # Rate
        'obj-40': (412, 33), 'obj-26': (412, 46),            # Bus
        'obj-41': (452, 33), 'obj-29': (452, 46),            # Voces
        'obj-45': (296, 66), 'obj-42': (296, 80),            # Trig
        'obj-397': (392, 66), 'obj-398': (392, 80),          # Dir
        'obj-754': (446, 80), 'obj-755': (464, 78),          # Pasa
        'obj-555': (296, 106), 'obj-556': (314, 104),        # SalL
        'obj-517': (362, 104), 'obj-518': (394, 106),        # Mon
        'obj-664': (428, 104), 'obj-662': (452, 106),        # Col
        'obj-565': (296, 128), 'obj-568': (314, 126),        # Ind
        'obj-569': (352, 128), 'obj-572': (370, 126),        # Flt
        'obj-573': (404, 128), 'obj-576': (422, 126),        # Lck
    },
}
VADV = ['obj-577', 'obj-578', 'obj-579', 'obj-580']
VAH = ['obj-586', 'obj-587', 'obj-588', 'obj-589', 'obj-590', 'obj-591', 'obj-592', 'obj-593', 'obj-594',
       'obj-595', 'obj-596', 'obj-597', 'obj-598', 'obj-657', 'obj-658', 'obj-659', 'obj-797', 'obj-798',
       'obj-799', 'obj-801', 'obj-802', 'obj-803', 'obj-805', 'obj-862']
SUBSEL = (510, 49, 150, 18)      # the Voces sub-page selector (new `tab`)

# labels the loose Sesion controls never had (Rnd toggles were bare; Reparto showed only its value)
NEW_LABELS = [   # (varname, text, tab, x, y, w, h)
    ('fs2g_lbl_reparto', 'Reparto', T_SES, 566, 68, 56, 16),
    ('fs2g_lbl_rnd_set', 'Set', T_SES, 566, 104, 24, 14),
    ('fs2g_lbl_rnd_msk', 'Msk', T_SES, 592, 104, 26, 14),
    ('fs2g_lbl_rnd_acc', 'Acc', T_SES, 618, 104, 26, 14),
]

# old sub-page messages (kept) -> new sub-selector outlets
SUB_MSGS = ['obj-721', 'obj-722', 'obj-800', 'obj-804']
OLD_CHAIN = ['obj-486', 'obj-488', 'obj-489', 'obj-490', 'obj-491', 'obj-492', 'obj-506', 'obj-581', 'obj-720',
             'obj-582', 'obj-617', 'obj-618', 'obj-619', 'obj-808', 'obj-723']
THISPATCHER = 'obj-487'
GOTO_ROUTE = 'obj-819'
TAB_BOX = 'obj-485'


def rect_of(b):
    return list(b['presentation_rect'])


def apply_rect(b, spec):
    r = rect_of(b)
    r[0], r[1] = float(spec[0]), float(spec[1])
    if len(spec) == 4:
        r[2], r[3] = float(spec[2]), float(spec[3])
    b['presentation_rect'] = r


def main():
    apply_it = '--apply' in sys.argv
    preview = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    boxes = {b['box']['id']: b['box'] for b in P['boxes']}

    assert boxes[TAB_BOX]['saved_attribute_attributes']['valueof']['parameter_enum'][0] == 'Armonia'
    assert len(boxes[TAB_BOX]['saved_attribute_attributes']['valueof']['parameter_enum']) == 11, \
        'ya aplicado (o el enum ya no es el de 11 items)'
    assert 'obj-486' in boxes, 'ya aplicado'

    # ---- coverage: every presentation box must be accounted for -------------------------------
    assigned = {}
    for i in ALWAYS_KEEP:
        assigned[i] = 'always'
    for i in ALWAYS:
        assigned[i] = 'always'
    for t, g in GROUPS.items():
        for i in g:
            assert i not in assigned, 'duplicado %s' % i
            assigned[i] = t
    for i in VADV:
        assigned[i] = T_VOC
    for i in VAH:
        assigned[i] = T_VOC
    missing = [i for i, b in boxes.items() if b.get('presentation') and i not in assigned]
    assert not missing, 'presentation boxes sin asignar: %s' % [(i, boxes[i].get('text') or boxes[i].get('varname')) for i in missing]
    ghosts = [i for i in assigned if i not in boxes]
    assert not ghosts, 'ids que no existen: %s' % ghosts
    for i in OLD_CHAIN + SUB_MSGS + [THISPATCHER, GOTO_ROUTE]:
        assert i in boxes, i

    # ---- new rects ---------------------------------------------------------------------------
    new_rect = {i: rect_of(b) for i, b in boxes.items() if b.get('presentation')}
    def put(i, spec):
        r = list(new_rect[i]); r[0], r[1] = float(spec[0]), float(spec[1])
        if len(spec) == 4:
            r[2], r[3] = float(spec[2]), float(spec[3])
        new_rect[i] = r
    for i, spec in ALWAYS.items():
        put(i, spec)
    for t, g in GROUPS.items():
        for i, spec in g.items():
            put(i, spec)
    for k, i in enumerate(VADV):
        r = list(new_rect[i]); r[0] += V_DX; new_rect[i] = r
    for i in VAH:
        r = list(new_rect[i]); r[0] += V_DX; new_rect[i] = r
    labels_rect = {}
    for (vn, text, t, x, y, w, h) in NEW_LABELS:
        labels_rect[vn] = [float(x), float(y), float(w), float(h)]

    # ---- layout checks ------------------------------------------------------------------------
    # which boxes are visible in which tab (rects), for overlap checking
    def visible_in(t):
        out = {}
        for i, tab in assigned.items():
            if tab == 'always':
                out[i] = new_rect[i]
        for i, r in new_rect.items():
            pass
        for i in GROUPS.get(t, {}):
            out[i] = new_rect[i]
        if t == T_VOC:
            for i in VADV:
                out[i] = new_rect[i]
        for (vn, text, tt, x, y, w, h) in NEW_LABELS:
            if tt == t:
                out['label:' + vn] = labels_rect[vn]
        if t == T_VOC:
            out['subsel'] = list(map(float, SUBSEL))
        if t in PAGES_TABS:
            out['pages'] = page_bbox(t)
        out.pop('obj-484', None)   # the viewport itself is not "content"
        return out
    def page_bbox(t):
        pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
        y0 = BAND[t]
        xs = []
        for b in pg['boxes']:
            b = b['box']
            if not b.get('presentation') or b.get('hidden'):
                continue
            x, y, w, h = b['presentation_rect']
            if y0 - 5 <= y < y0 + 150:
                xs.append((x, y - y0, x + w, y - y0 + h))
        return [CX + min(a[0] for a in xs), CY + min(a[1] for a in xs),
                max(a[2] for a in xs) - min(a[0] for a in xs), max(a[3] for a in xs) - min(a[1] for a in xs)]
    problems = []
    for t in range(9):
        vis = visible_in(t)
        items = list(vis.items())
        for k, (i, r) in enumerate(items):
            if r[1] + r[3] > DEVICE_H + 0.01:
                problems.append('T%d %s: sale por abajo (y+h=%.0f > %.0f)' % (t, i, r[1] + r[3], DEVICE_H))
            if r[0] + r[2] > DEVICE_W + 0.01:
                problems.append('T%d %s: sale por la derecha (x+w=%.0f > %.0f)' % (t, i, r[0] + r[2], DEVICE_W))
            if r[0] < -0.01 or r[1] < -0.01:
                problems.append('T%d %s: coordenada negativa %s' % (t, i, r[:2]))
            for (j, q) in items[k + 1:]:
                ox = min(r[0] + r[2], q[0] + q[2]) - max(r[0], q[0])
                oy = min(r[1] + r[3], q[1] + q[3]) - max(r[1], q[1])
                if i in ALWAYS_KEEP and j in ALWAYS_KEEP:
                    continue   # the untouched strip: its (pre-existing) layout is not ours to judge
                is_c = lambda k: (k.startswith('label:') or boxes.get(k, {}).get('maxclass') == 'comment')
                slack = 7.0 if (is_c(i) or is_c(j)) else 1.5   # comment boxes carry ~5px of empty padding
                if ox > slack and oy > slack:
                    problems.append('T%d %s (%s) solapa con %s (%s)  %.0fx%.0f px' % (
                        t, i, [round(v) for v in r], j, [round(v) for v in q], ox, oy))
    # the fs2_pages viewport is a window: page content past it is clipped
    for t in PAGES_TABS:
        b = page_bbox(t)
        if b[0] + b[2] > CX + CW + 0.01 or b[1] + b[3] > CY + CH + 0.01:
            problems.append('T%d: el contenido de la pagina (%s) no entra en el viewport %s' % (
                t, [round(v) for v in b], [CX, CY, CW, CH]))
    print('=== layout checks: %s' % ('OK' if not problems else '%d problema(s)' % len(problems)))
    for pr in problems:
        print('  ! ' + pr)

    if preview:
        make_previews(preview, visible_in)

    # ---- build the new patch logic -----------------------------------------------------------
    nid = [max(int(i.split('-')[1]) for i in boxes)]
    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    # unique scripting names for everything we show/hide/front
    from collections import Counter
    vcount = Counter(b.get('varname') for b in boxes.values() if b.get('varname'))
    def is_generic(vn):
        return vn is None or vn.startswith('obj-') or vcount[vn] > 1
    scriptname = {}
    def sname(i):
        if i in scriptname:
            return scriptname[i]
        b = boxes[i]
        vn = b.get('varname')
        scriptname[i] = ('fs2g_' + i) if is_generic(vn) else vn
        return scriptname[i]
    # (auto varnames like 'obj-115' are only renamed for boxes we actually script)
    tab_members = {t: [i for i in g] for t, g in GROUPS.items()}
    all_group_ids = [i for t in GROUPS for i in GROUPS[t]]
    for i in all_group_ids + VADV + VAH:
        sname(i)

    def tab_message(t):
        cmds = []
        # 1) hide everything that belongs to another tab (loose controls, and the whole Voces set)
        for tt in sorted(GROUPS):
            if tt == t:
                continue
            for i in GROUPS[tt]:
                cmds.append('script hide %s' % sname(i))
        for (vn, _txt, tt, *_r) in NEW_LABELS:
            if tt != t:
                cmds.append('script hide %s' % vn)
        if t != T_VOC:
            for i in VADV:
                cmds.append('script hide %s' % sname(i))
            for i in VAH:
                cmds.append('script hide %s' % sname(i))
            cmds.append('script hide fs2_vsub')
        # 2) show this tab's own
        if t in PAGES_TABS:
            cmds.append('script show fs2_pages')
            cmds.append('script sendbox fs2_pages offset 0 %d' % (-BAND[t]))
        else:
            cmds.append('script hide fs2_pages')
        for i in GROUPS.get(t, {}):
            cmds.append('script show %s' % sname(i))
        for (vn, _txt, tt, *_r) in NEW_LABELS:
            if tt == t:
                cmds.append('script show %s' % vn)
        if t == T_VOC:
            for i in VADV:
                cmds.append('script show %s' % sname(i))
            cmds.append('script show fs2_vsub')
        # 3) above the pages bpatcher, so its (transparent) area doesn't swallow the clicks
        for i in GROUPS.get(t, {}):
            cmds.append('script front %s' % sname(i))
        for (vn, _txt, tt, *_r) in NEW_LABELS:
            if tt == t:
                cmds.append('script front %s' % vn)
        if t == T_VOC:
            for i in VADV:
                cmds.append('script front %s' % sname(i))
            cmds.append('script front fs2_vsub')
        return ', '.join(cmds)

    new_boxes, new_lines = [], []
    def add_box(d):
        new_boxes.append({'box': d})
        return d['id']
    def add_line(src, so, dst, di, order=None):
        pl = {'source': [src, so], 'destination': [dst, di]}
        new_lines.append({'patchline': pl})

    # -- main sel + one message per tab
    sel_id = fresh()
    add_box({'id': sel_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 10, 'outlettype': [''] * 10,
             'patching_rect': [300.0, 740.0, 160.0, 20.0], 'text': 'sel 0 1 2 3 4 5 6 7 8', 'varname': 'fs2_tabs_sel'})
    add_line(TAB_BOX, 0, sel_id, 0)
    msg_ids = []
    for t in range(9):
        mid = fresh()
        msg_ids.append(mid)
        txt = tab_message(t)
        add_box({'id': mid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
                 'patching_rect': [300.0 + 40.0 * t, 790.0 + 24.0 * t, 260.0, 20.0], 'text': txt,
                 'varname': 'fs2_tab_msg_%d' % t})
        add_line(sel_id, t, mid, 0)
        add_line(mid, 0, THISPATCHER, 0)

    # -- Voces sub-selector: tab -> [int] -> [sel 0 1 2 3] -> the four kept sub-page messages
    # [int] both stores the page (so entering the tab re-applies it: `bang` -> [int]) and passes it on.
    tab_id = fresh()
    sr = list(map(float, SUBSEL))
    add_box({'id': tab_id, 'maxclass': 'tab', 'numinlets': 1, 'numoutlets': 3, 'outlettype': ['int', '', 'float'],
             'tabs': ['Disp', 'Artic', 'Orn', 'Tono'], 'fontsize': 9.0, 'rounded': 0.0, 'hidden': 1,
             'patching_rect': [900.0, 740.0, 150.0, 20.0], 'presentation': 1, 'presentation_rect': sr,
             'varname': 'fs2_vsub', 'annotation': 'Sub-pagina de las voces: Disp (Ext/Oct/Ev.N/O.Rng/Pasos/Trig/Min/Span), '
             'Artic (Vel/Fig/Sil/Propia/Patr/Dir), Orn (Orn por voz), Tono (Ton/Set/Raiz/Fij).'})
    int_id = fresh()
    add_box({'id': int_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 1, 'outlettype': ['int'],
             'patching_rect': [900.0, 770.0, 40.0, 20.0], 'text': 'int', 'varname': 'fs2_vsub_mem'})
    vsel_id = fresh()
    add_box({'id': vsel_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 5, 'outlettype': [''] * 5,
             'patching_rect': [900.0, 800.0, 100.0, 20.0], 'text': 'sel 0 1 2 3', 'varname': 'fs2_vsub_sel'})
    add_line(tab_id, 0, int_id, 0)
    add_line(int_id, 0, vsel_id, 0)
    for k, m in enumerate(SUB_MSGS):
        add_line(vsel_id, k, m, 0)
    # entering Voces: re-apply the current sub-page  (tab 5 -> bang -> [int])
    bang_id = fresh()
    add_box({'id': bang_id, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
             'patching_rect': [900.0, 720.0, 40.0, 20.0], 'text': 'bang', 'varname': 'fs2_vsub_bang'})
    add_line(sel_id, T_VOC, bang_id, 0)
    add_line(bang_id, 0, int_id, 0)

    # -- gotopage: 0..8 = tab (unchanged path), 20..23 = Voces sub-page
    gsel = fresh()
    add_box({'id': gsel, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 5, 'outlettype': [''] * 5,
             'patching_rect': [2400.0, 3440.0, 130.0, 20.0], 'text': 'sel 20 21 22 23', 'varname': 'fs2_goto_sel'})
    add_line(GOTO_ROUTE, 0, gsel, 0)
    add_line(gsel, 4, TAB_BOX, 0)                 # reject = the plain 0..8 value -> the tab bar
    for k in range(4):
        m_int = fresh()   # k -> [int]: stores + applies the sub-page
        add_box({'id': m_int, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
                 'patching_rect': [2400.0 + 60.0 * k, 3480.0, 30.0, 20.0], 'text': str(k)})
        m_set = fresh()   # set k -> tab: moves the highlighted item without re-firing
        add_box({'id': m_set, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
                 'patching_rect': [2400.0 + 60.0 * k, 3520.0, 50.0, 20.0], 'text': 'set %d' % k})
        m_tab = fresh()   # 5 -> the tab bar
        add_box({'id': m_tab, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
                 'patching_rect': [2400.0 + 60.0 * k, 3560.0, 30.0, 20.0], 'text': str(T_VOC)})
        add_line(gsel, k, m_int, 0)
        add_line(gsel, k, m_set, 0)
        add_line(gsel, k, m_tab, 0)
        add_line(m_int, 0, int_id, 0)
        add_line(m_set, 0, tab_id, 0)
        add_line(m_tab, 0, TAB_BOX, 0)

    # -- new label comments
    for (vn, text, t, x, y, w, h) in NEW_LABELS:
        add_box({'id': fresh(), 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'text': text,
                 'patching_rect': [200.0, 3000.0 + 20.0 * len(new_boxes), w, h], 'presentation': 1,
                 'presentation_rect': [float(x), float(y), float(w), float(h)], 'hidden': 1, 'varname': vn,
                 'fontsize': 9.0})

    # ---- mutate the patcher ------------------------------------------------------------------
    old_gt_line = {'source': [GOTO_ROUTE, 0], 'destination': [TAB_BOX, 0]}
    assert old_gt_line in [l['patchline'] for l in P['lines']], 'no encuentro obj-819 -> obj-485'
    dead = set(OLD_CHAIN)
    n_lines_before = len(P['lines'])
    P['lines'] = [l for l in P['lines']
                  if l['patchline']['source'][0] not in dead and l['patchline']['destination'][0] not in dead
                  and l['patchline'] != old_gt_line]
    removed_lines = n_lines_before - len(P['lines'])
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in dead]
    P['boxes'].extend(new_boxes)
    P['lines'].extend(new_lines)

    # rects, hidden flags, varnames
    boxes = {b['box']['id']: b['box'] for b in P['boxes']}
    for i, r in new_rect.items():
        if i in boxes:
            boxes[i]['presentation_rect'] = r
    for i in all_group_ids + VADV + VAH:
        b = boxes[i]
        b['varname'] = sname(i)
        if i in VAH or i in VADV:
            b['hidden'] = 1
        else:
            # everything not on the default tab starts hidden; the load-time outputvalue re-applies the saved tab
            if assigned[i] == T_ARM:
                b.pop('hidden', None)
            else:
                b['hidden'] = 1
    # Global/Ornamento etc. members that were always-on before must now start hidden (handled above);
    # the two Armonia-default loose controls stay visible.
    tabbox = boxes[TAB_BOX]
    tv = tabbox['saved_attribute_attributes']['valueof']
    tv['parameter_enum'] = list(TAB_NAMES)
    tv['parameter_mmax'] = len(TAB_NAMES) - 1
    tabbox['num_lines_presentation'] = 1
    tabbox['annotation'] = ('Que panel se ve. Los controles de las paginas ocultas siguen activos: '
                            'la pagina no apaga nada, solo elige que mirar.')
    P['openrect'] = [0.0, 0.0, 0.0, DEVICE_H]

    print('\n=== cambios')
    print('  obj-485 (Pagina): enum %s' % TAB_NAMES)
    print('  cadena vieja eliminada: %d cajas, %d cables' % (len(OLD_CHAIN), removed_lines))
    print('  cajas nuevas: %d, cables nuevos: %d' % (len(new_boxes), len(new_lines)))
    for t in range(9):
        print('  M%d (%s): %d comandos' % (t, TAB_NAMES[t], tab_message(t).count(',') + 1))

    if problems:
        print('\nHAY PROBLEMAS DE LAYOUT -- no se aplica.')
        sys.exit(1)
    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-tabs')
    amxd.save(DEVICE, data, s, e, doc)
    d2 = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box']['id']: b['box'] for b in d2['boxes']}
    assert b2[TAB_BOX]['saved_attribute_attributes']['valueof']['parameter_enum'] == TAB_NAMES
    print('\nescrito %s (.before-tabs guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  en Live: cerrar y reabrir el device; recorrer las 9 tabs')


def make_previews(outdir, visible_in):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print('(sin Pillow: no hay preview)')
        return
    os.makedirs(outdir, exist_ok=True)
    S = 2
    for t in range(9):
        im = Image.new('RGB', (int(DEVICE_W) * S, int(DEVICE_H) * S), (40, 40, 44))
        d = ImageDraw.Draw(im)
        d.rectangle([CX * S, CY * S, (CX + CW) * S, (CY + CH) * S], outline=(80, 80, 90))
        for i, r in visible_in(t).items():
            col = (120, 170, 120) if i in ALWAYS or i in ALWAYS_KEEP else (200, 160, 90)
            if i == 'pages':
                col = (90, 120, 200)
            d.rectangle([r[0] * S, r[1] * S, (r[0] + r[2]) * S, (r[1] + r[3]) * S], outline=col)
            d.text((r[0] * S + 2, r[1] * S + 2), str(i).replace('obj-', ''), fill=col)
        d.line([0, DEVICE_H * S, DEVICE_W * S, DEVICE_H * S], fill=(200, 60, 60))
        d.text((6, 6), 'tab %d %s' % (t, TAB_NAMES[t]), fill=(255, 255, 255))
        im.save(os.path.join(outdir, 'tab%d_%s.png' % (t, TAB_NAMES[t])))
    print('previews en %s' % outdir)


main()
