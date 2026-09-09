"""Give forteseqwf (EVENFLOW) a floating "Ritmos" window: how the WF rhythms are behaving, per level.

Models tools/add_fs2_horizon.py exactly -- an inline subpatcher [p wf_rhythmwin] opened as a floating
window by a live.text button (the one new Live param), fed ~8 Hz by a free metro so it keeps drawing
with the transport stopped, and a return path so the popup's group controls reach the engine.

Runs after tools/reshape_wf_perlevel.py; independent of tools/add_wf_voicegroups.py (disjoint regions)
but best run AFTER it so the jsui's per-lane Grp/Canal labels have real data.

  top patcher, new boxes (all hidden except the button):
    BTN    live.text  "Ritmos"        -- the ONE new Live parameter
    OPEN   message    "open"
    PCTRL  pcontrol
    VIZON  [prepend vizon]            -- turns the engine's viz feed on/off with the button
    QRY    message    "querycycle"
    MET    metro 120
    TB1    t 1
    THISD  live.thisdevice            -- device-loaded bang starts the metro (window stays shut)
    VROUTE [route viz]                -- new 5th consumer of wf_engine's single outlet
    SUB    [p wf_rhythmwin]           -- inline subpatcher, opens as a floating window
    LBL    comment (hidden)

  new lines:
    BTN:0  -> OPEN:0        BTN:0 -> VIZON:0        VIZON:0 -> wf_engine:0
    OPEN:0 -> PCTRL:0       PCTRL:0 -> SUB:0
    THISD:0-> TB1:0         TB1:0  -> MET:0         MET:0  -> QRY:0     QRY:0 -> wf_engine:0
    wf_engine:0 -> VROUTE:0     VROUTE:0 -> SUB:0
    SUB:0  -> wf_engine:0                            (popup group edits back to the engine)

  inside [p wf_rhythmwin]:
    inlet -> jsui wf_rhythmviz.js -> outlet          (parameter_enable 0 -- not a Live param)

Registries touched: only the button (its box valueof + P['parameters'][BTN]; wf convention has no
parameter_order and no parameterbanks entry needed).

Idempotent: re-running does nothing once the SUB box (varname wf_rhythmwin) is present.
Close forteseqwf in BOTH Max and Live before --apply.

    python tools/add_wf_rhythmviz.py            dry run, writes nothing
    python tools/add_wf_rhythmviz.py --apply    write forteseq/forteseqwf.amxd (+ .before-rhythmviz)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'forteseqwf.amxd')
BOOT = 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq'

ENGINE = 'obj-6'          # js forteseqwf.js
WIN_VAR = 'wf_rhythmwin'  # idempotency marker (the [p wf_rhythmwin] box)
JS = 'wf_rhythmviz.js'

PARAM_LONG = 'Ritmos'
PARAM_SHORT = 'Ritmos'

# floating window / canvas geometry
CANVAS = [8.0, 8.0, 2600.0, 1500.0]        # jsui deliberately oversized; it paints inside wind.size
WIN_RECT = [140.0, 140.0, 1160.0, 640.0]

ANN_BTN = ('Abre / trae al frente la ventana flotante con los ritmos por nivel: onsets en el tiempo, '
           'estructura L/S, r y marcador, U/C, decimacion, acentos, cabezal y morph. Vista lineal o '
           'collares (click en la pestana). Se actualiza aunque el transporte este parado.')


def mkbox(P, **kw):
    P['boxes'].append({'box': kw})


def mkline(P, src, so, dst, di):
    P['lines'].append({'patchline': {'source': [src, so], 'destination': [dst, di]}})


def build_subpatcher(appversion):
    """[p wf_rhythmwin]: inlet -> jsui wf_rhythmviz.js -> outlet, opens as its own floating window."""
    boxes = [
        {'box': dict(id='obj-1', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
                     patching_rect=[8.0, 8.0, 24.0, 24.0], varname='wfrv_in', hidden=1)},
        {'box': dict(id='obj-2', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
                     parameter_enable=0, filename=JS, varname='wfrv_ui',
                     patching_rect=list(CANVAS), presentation=1, presentation_rect=list(CANVAS))},
        {'box': dict(id='obj-3', maxclass='outlet', numinlets=1, numoutlets=0,
                     patching_rect=[8.0, 40.0, 24.0, 24.0], varname='wfrv_out', hidden=1)},
    ]
    lines = [
        {'patchline': {'source': ['obj-1', 0], 'destination': ['obj-2', 0]}},
        {'patchline': {'source': ['obj-2', 0], 'destination': ['obj-3', 0]}},
    ]
    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': list(WIN_RECT), 'openrect': [0.0, 0.0, WIN_RECT[2], WIN_RECT[3]],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'EVENFLOW - Ritmos',
        'boxes': boxes, 'lines': lines,
        'parameters': {'inherited_shortname': 1},
        'dependency_cache': [
            {'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
            {'name': 'pccolor.js', 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        ],
        'autosave': 0,
    }


def build(apply_it):
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    appversion = P.get('appversion')

    by_var = {b['box'].get('varname'): b['box'] for b in P['boxes']}
    if WIN_VAR in by_var:
        print('already patched (%s present) -- nothing to do' % WIN_VAR)
        return

    ids = {b['box']['id'] for b in P['boxes']}
    assert ENGINE in ids, 'engine box %s not found' % ENGINE
    n_boxes_before, n_lines_before = len(P['boxes']), len(P['lines'])
    n_params_before = len([k for k in P['parameters']
                           if k not in ('parameterbanks', 'inherited_shortname')])

    n = max(int(i[4:]) for i in ids if i[4:].isdigit())
    BTN, OPEN, PCTRL, VIZON, QRY, MET, TB1, THISD, VROUTE, SUB, LBL = \
        ['obj-%d' % (n + k) for k in range(1, 12)]

    vo = {
        'parameter_longname': PARAM_LONG, 'parameter_shortname': PARAM_SHORT,
        'parameter_type': 2, 'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
        'parameter_modmode': 0, 'parameter_unitstyle': 9,
        'parameter_initial_enable': 1, 'parameter_initial': [0],
    }

    X, Y = 200.0, 6000.0
    mkbox(P, id=BTN, maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
          parameter_enable=1, mode=1, text='Ritmos', texton='Ritmos',
          patching_rect=[X, Y, 90.0, 24.0],
          presentation=1, presentation_rect=[0.0, 92.0, 60.0, 20.0],
          varname='wf_rhythmviz_btn', annotation=ANN_BTN,
          saved_attribute_attributes={'valueof': vo})
    mkbox(P, id=LBL, maxclass='comment', numinlets=1, numoutlets=0,
          patching_rect=[X + 260, Y, 240.0, 18.0],
          text='ventana flotante: ritmos WF por nivel', varname='wf_rhythmviz_lbl', hidden=1)
    mkbox(P, id=OPEN, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[X, Y + 30, 48.0, 22.0], text='open',
          varname='wf_rhythmviz_open', hidden=1)
    mkbox(P, id=PCTRL, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[X, Y + 60, 56.0, 22.0], text='pcontrol',
          varname='wf_rhythmviz_pctrl', hidden=1)
    mkbox(P, id=VIZON, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[X + 100, Y, 90.0, 22.0], text='prepend vizon',
          varname='wf_rhythmviz_vizon', hidden=1)
    mkbox(P, id=QRY, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[X + 100, Y + 60, 90.0, 22.0], text='querycycle',
          varname='wf_rhythmviz_qry', hidden=1)
    mkbox(P, id=MET, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['bang'],
          patching_rect=[X + 100, Y + 30, 70.0, 22.0], text='metro 120',
          varname='wf_rhythmviz_metro', hidden=1)
    mkbox(P, id=TB1, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[X + 100, Y - 30, 30.0, 22.0], text='t 1',
          varname='wf_rhythmviz_tb', hidden=1)
    mkbox(P, id=THISD, maxclass='live.thisdevice', numinlets=1, numoutlets=3,
          outlettype=['bang', 'bang', ''],
          patching_rect=[X + 100, Y - 60, 100.0, 22.0], text='live.thisdevice',
          varname='wf_rhythmviz_thisdev', hidden=1)
    mkbox(P, id=VROUTE, maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
          patching_rect=[X + 260, Y + 30, 70.0, 22.0], text='route viz',
          varname='wf_vizroute', hidden=1)

    sub = build_subpatcher(appversion)
    mkbox(P, id=SUB, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[X + 260, Y + 60, 130.0, 22.0], text='p wf_rhythmwin',
          varname=WIN_VAR, patcher=sub)

    mkline(P, BTN, 0, OPEN, 0)           # click -> open the window
    mkline(P, BTN, 0, VIZON, 0)          # click 0/1 -> engine vizon (starts/stops the viz feed)
    mkline(P, VIZON, 0, ENGINE, 0)
    mkline(P, OPEN, 0, PCTRL, 0)
    mkline(P, PCTRL, 0, SUB, 0)          # "open" -> floating window
    mkline(P, THISD, 0, TB1, 0)          # device fully loaded -> start the metro (window stays shut)
    mkline(P, TB1, 0, MET, 0)
    mkline(P, MET, 0, QRY, 0)            # ~8 Hz
    mkline(P, QRY, 0, ENGINE, 0)         # querycycle -> js forteseqwf.js inlet 0
    mkline(P, ENGINE, 0, VROUTE, 0)      # 5th consumer of the multiplexed outlet
    mkline(P, VROUTE, 0, SUB, 0)         # viz frame feed
    mkline(P, SUB, 0, ENGINE, 0)         # popup group edits (setlevelgroup / setgroupchannel) back in

    P['parameters'][BTN] = [PARAM_LONG, PARAM_SHORT, 0]

    # --- self-check: same class of trap check_structure.py enforces --------------------
    def check(pp, where='root'):
        by = {}
        for b in pp.get('boxes', []):
            bx = b['box']
            assert bx['id'] not in by, '%s: dup id %s' % (where, bx['id'])
            by[bx['id']] = bx
        for ln in pp.get('lines', []):
            pl = ln['patchline']
            for tag, end in (('src', pl['source']), ('dst', pl['destination'])):
                bx = by.get(end[0])
                assert bx, '%s: %s -> unknown box %s' % (where, tag, end)
                cnt = bx.get('numoutlets', 0) if tag == 'src' else bx.get('numinlets', 0)
                assert 0 <= end[1] < cnt, '%s: %s %s idx %d not in 0..%d (%s)' % (
                    where, tag, end[0], end[1], cnt - 1, bx.get('text', bx.get('maxclass')))
        for b in pp.get('boxes', []):
            if b['box'].get('patcher'):
                check(b['box']['patcher'], where + '::' + b['box']['id'])
    check(P)

    pp_names = {k: v[0] for k, v in P['parameters'].items()
               if k not in ('parameterbanks', 'inherited_shortname')}
    assert len(pp_names) == n_params_before + 1
    assert len(set(pp_names.values())) == len(pp_names), 'duplicate parameter longname'

    print('add_wf_rhythmviz  ->  forteseq/forteseqwf.amxd')
    print('  boxes : %d -> %d  (+%d)' % (n_boxes_before, len(P['boxes']),
                                         len(P['boxes']) - n_boxes_before))
    print('  lines : %d -> %d  (+%d)' % (n_lines_before, len(P['lines']),
                                         len(P['lines']) - n_lines_before))
    print('  subpatcher: [p wf_rhythmwin] -> jsui %s -> outlet   (window %s)' % (JS, WIN_RECT))
    print('  new param : "%s" key %s' % (PARAM_LONG, BTN))
    print('  feed  : %s:0 -> route viz -> SUB   trigger: metro 120 -> [querycycle] -> %s:0' % (ENGINE, ENGINE))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-rhythmviz')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    win = next((b['box'] for b in back['boxes'] if b['box'].get('varname') == WIN_VAR), None)
    assert win and win.get('patcher'), 'subpatcher lost'
    inner = win['patcher']['boxes']
    assert any(b['box'].get('maxclass') == 'jsui' and b['box'].get('filename') == JS
               for b in inner), 'jsui wf_rhythmviz.js lost'
    assert back['parameters'].get(BTN, [None])[0] == PARAM_LONG, 'param not registered'
    btnbox = next(b['box'] for b in back['boxes'] if b['box']['id'] == BTN)
    assert btnbox['saved_attribute_attributes']['valueof']['parameter_longname'] == PARAM_LONG
    print('\nwrote %s  (backup %s.before-rhythmviz)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/forteseqwf.amxd')


if __name__ == '__main__':
    build('--apply' in sys.argv)
