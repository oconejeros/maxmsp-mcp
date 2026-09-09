"""Give FORTESEQ2 a floating "Próximos 16 pasos" window: a 16-step-ahead note horizon per voice.

    python tools/add_fs2_horizon.py            dry run, writes nothing
    python tools/add_fs2_horizon.py --apply    write forteseq/FORTESEQ2.amxd (+ .before)

Why: the inline fs2colmon.js strip is glanceable but only 2 steps ahead, only updates while the
transport runs, and caps at 8 voice rows. This adds a floating window (the ANIMIDI / tonnetz
"Abrir" pattern) that shows the next 16 steps for every voice and keeps updating with the
transport stopped. The small strip is left untouched.

What it does, modelled on tools/add_local_output.py + tools/build_animidi.py:353-462:

  top patcher, new boxes (all hidden except the button):
    BTN   live.text  "Próximos 16"   -- the ONE new Live parameter (parameter_order = next)
    MOPEN message   "open"
    PCTRL pcontrol
    MQRY  message   "querynext 16"
    MET   metro 120
    TB1   t 1
    SUB   [p fs2_window]              -- inline subpatcher, opens as a floating window

  top patcher, new lines:
    BTN:0  -> MOPEN:0      BTN:0 -> MQRY:0        (click opens the window AND forces a refresh)
    MOPEN:0-> PCTRL:0      PCTRL:0 -> SUB:0       (the open path)
    obj-121:0 -> TB1:0     TB1:0 -> MET:0         (live.thisdevice load bang starts the metro)
    MET:0  -> MQRY:0                              (~8 Hz re-query; engine-side debounce keeps it cheap)
    MQRY:0 -> obj-23:0                            (query trigger into js forteseq2.js)
    obj-23:3 -> SUB:0                             (horizon feed, parallel to obj-23:3 -> obj-660)
    obj-663:0 -> SUB:0                            (the "Color Monitor" toggle tints the popup too)

  inside [p fs2_window]:
    inlet -> jsui fs2horizon.js                   (parameter_enable 0 -- not a Live param)

Registries touched: only the button. Its box valueof, P['parameters'][BTN], and (optional, on by
default) the free '-' slot of Push bank 9 "Engine". Nothing inside the subpatcher is a Live param,
so the subpatcher keeps only {'inherited_shortname': 1}.

Idempotent: re-running does nothing once the SUB box (varname fs2_horizon_win) is present.
Close FORTESEQ2 in BOTH Max and Live before --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'FORTESEQ2.amxd')
BOOT = 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq'

ENGINE = 'obj-23'          # js forteseq2.js
THISDEV = 'obj-121'        # live.thisdevice (outlet 0 = device fully loaded)
COLMON = 'obj-660'         # jsui fs2colmon.js (existing outlet-3 consumer)
COLPREP = 'obj-663'        # [prepend color] fed by the "Color Monitor" toggle

WIN_VAR = 'fs2_horizon_win'          # idempotency marker (the [p fs2_window] box)
JS = 'fs2horizon.js'
# ASCII param names, matching the device's house style ("Rotacion", "Teoria" -- no accents)
PARAM_LONG = 'Proximos 16'
PARAM_SHORT = 'Prox16'
ADD_TO_BANK = True                   # drop the button into Push bank 9's free slot

# floating window / canvas geometry: 16 columns need room for a note name + octave digit
CANVAS = [8.0, 8.0, 844.0, 284.0]
WIN_RECT = [140.0, 140.0, 868.0, 316.0]

ANN_BTN = ('Abre / trae al frente la ventana con los proximos 16 pasos por voz '
           '(flota fuera del rack; se actualiza aunque el transporte este parado).')


def mkbox(P, **kw):
    P['boxes'].append({'box': kw})


def mkline(P, src, so, dst, di):
    P['lines'].append({'patchline': {'source': [src, so], 'destination': [dst, di]}})


def next_order(P):
    top = 0
    for v in P['parameters'].values():
        if isinstance(v, list) and len(v) >= 3 and isinstance(v[2], int):
            top = max(top, v[2])
    return top + 1


def build_subpatcher(appversion):
    """The [p fs2_window] patcher dict: one inlet -> one jsui, opens as its own floating window."""
    boxes, lines = [], []
    boxes.append({'box': dict(
        id='obj-1', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
        patching_rect=[8.0, 8.0, 24.0, 24.0], varname='fs2hz_in', hidden=1)})
    boxes.append({'box': dict(
        id='obj-2', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=0, filename=JS, varname='fs2hz_ui',
        patching_rect=list(CANVAS), presentation=1, presentation_rect=list(CANVAS))})
    lines.append({'patchline': {'source': ['obj-1', 0], 'destination': ['obj-2', 0]}})
    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': list(WIN_RECT), 'openrect': [0.0, 0.0, WIN_RECT[2], WIN_RECT[3]],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'FORTESEQ2 - Proximos 16 pasos',
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
    for need in (ENGINE, THISDEV, COLMON, COLPREP):
        assert need in ids, 'expected box %s not found' % need

    n = max(int(i[4:]) for i in ids if i[4:].isdigit())
    BTN, MOPEN, PCTRL, MQRY, MET, TB1, SUB, LBL = ['obj-%d' % (n + k) for k in range(1, 9)]

    order = next_order(P)
    vo = {
        'parameter_longname': PARAM_LONG, 'parameter_shortname': PARAM_SHORT,
        'parameter_type': 2, 'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
        'parameter_modmode': 0, 'parameter_unitstyle': 9,
        'parameter_initial_enable': 1, 'parameter_initial': [0],
        'parameter_order': order,
    }

    Y = 5400.0
    mkbox(P, id=BTN, maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
          parameter_enable=1, mode=1, text='Proximos 16', texton='Proximos 16',
          patching_rect=[40.0, Y, 110.0, 24.0],
          presentation=1, presentation_rect=[313.0, 146.0, 98.0, 18.0],
          varname='fs2_horizon_btn', annotation=ANN_BTN,
          saved_attribute_attributes={'valueof': vo})
    mkbox(P, id=LBL, maxclass='comment', numinlets=1, numoutlets=0,
          patching_rect=[160.0, Y, 220.0, 18.0],
          text='ventana flotante: proximos 16 pasos por voz', varname='fs2_horizon_lbl',
          hidden=1)
    mkbox(P, id=MOPEN, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[40.0, Y + 30, 48.0, 22.0], text='open',
          varname='fs2_horizon_open', hidden=1)
    mkbox(P, id=PCTRL, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[40.0, Y + 60, 56.0, 22.0], text='pcontrol',
          varname='fs2_horizon_pctrl', hidden=1)
    mkbox(P, id=MQRY, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[120.0, Y + 60, 90.0, 22.0], text='querynext 16',
          varname='fs2_horizon_qry', hidden=1)
    mkbox(P, id=MET, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['bang'],
          patching_rect=[120.0, Y + 30, 70.0, 22.0], text='metro 120',
          varname='fs2_horizon_metro', hidden=1)
    mkbox(P, id=TB1, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
          patching_rect=[120.0, Y, 30.0, 22.0], text='t 1',
          varname='fs2_horizon_tb', hidden=1)

    sub = build_subpatcher(appversion)
    mkbox(P, id=SUB, maxclass='newobj', numinlets=1, numoutlets=0,
          patching_rect=[240.0, Y + 30, 130.0, 22.0], text='p fs2_window',
          varname=WIN_VAR, patcher=sub)

    mkline(P, BTN, 0, MOPEN, 0)          # click -> open the window
    mkline(P, BTN, 0, MQRY, 0)           # click -> force an immediate recompute
    mkline(P, MOPEN, 0, PCTRL, 0)
    mkline(P, PCTRL, 0, SUB, 0)          # "open" as a floating window
    mkline(P, THISDEV, 0, TB1, 0)        # device fully loaded -> start the metro (window stays shut)
    mkline(P, TB1, 0, MET, 0)
    mkline(P, MET, 0, MQRY, 0)           # ~8 Hz re-query
    mkline(P, MQRY, 0, ENGINE, 0)        # querynext -> js forteseq2.js inlet 0
    mkline(P, ENGINE, 3, SUB, 0)         # horizon feed, parallel to ENGINE:3 -> COLMON
    mkline(P, COLPREP, 0, SUB, 0)        # "Color Monitor" toggle tints the popup too

    P['parameters'][BTN] = [PARAM_LONG, PARAM_SHORT, order]

    if ADD_TO_BANK:
        banks = P['parameters'].get('parameterbanks', {})
        b9 = banks.get('9')
        if b9 and isinstance(b9.get('parameters'), list) and '-' in b9['parameters']:
            b9['parameters'][b9['parameters'].index('-')] = PARAM_LONG
            print('  bank 9 "Engine": free slot -> "%s"' % PARAM_LONG)
        else:
            print('  bank 9 has no free slot; skipped (Push binding only, not required)')

    # --- self-check: same class of trap check_structure.py enforces ---------------------
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

    print('add_fs2_horizon  ->  forteseq/FORTESEQ2.amxd')
    print('  new boxes : %s' % ', '.join([BTN, LBL, MOPEN, PCTRL, MQRY, MET, TB1, SUB]))
    print('  subpatcher: [p fs2_window]  ->  jsui %s   (window %s)' % (JS, WIN_RECT))
    print('  new param : "%s" (order %d) key %s' % (PARAM_LONG, order, BTN))
    print('  feed      : %s:3 -> %s   trigger: %s -> %s:0 (metro 120)' % (ENGINE, SUB, MQRY, ENGINE))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    win = next((b['box'] for b in back['boxes'] if b['box'].get('varname') == WIN_VAR), None)
    assert win and win.get('patcher'), 'subpatcher lost'
    inner = win['patcher']['boxes']
    assert any(b['box'].get('maxclass') == 'jsui' and b['box'].get('filename') == JS
               for b in inner), 'jsui fs2horizon.js lost'
    assert back['parameters'].get(BTN, [None])[0] == PARAM_LONG, 'param not registered'
    btnbox = next(b['box'] for b in back['boxes'] if b['box']['id'] == BTN)
    assert btnbox['saved_attribute_attributes']['valueof']['parameter_longname'] == PARAM_LONG
    print('\nwrote %s  (backup %s.before)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('     python tools/check_params3.py')


if __name__ == '__main__':
    build('--apply' in sys.argv)
