"""Build forteseq/invertedprism.amxd -- the colour -> harmony device.

    python tools/build_invertedprism.py            dry run
    python tools/build_invertedprism.py --apply    do it

Same method as build_harmonograph.py / build_tonnetz.py: copy forteseqmidifilter.amxd
(keeps the AMPF/meta chunk that marks it a MIDI effect) and rewrite boxes / lines /
parameters / dependency_cache.

Panel: an OPEN button. Floating window `[p ip_window]` (pcontrol scheme, like harmonograph):
the jsui canvas + Model / BaseHue / Sat / Split / Clear.

    top patcher:
      js invertedprism.js  outlet --> route chord clusters harm points heardcolor split
          chord --> [t l b] : b -> [flush( -> makenote ;  l -> [iter] -> makenote 90 800 -> noteout
          clusters/harm/points/heardcolor --> [prepend <tag>] --> [p ip_window] inlet
      notein --> pack 0 0 --> prepend note --> js engine       (live reharmoniser feed)
      midiin --> midiout                                   (pass-through)
      OPEN / live.thisdevice --> open --> pcontrol --> [p ip_window]

    [p ip_window]:
      inlet --> jsui invertedprism_ui.js
      jsui outlet (addpoint/setpoint/rempoint) --> outlet --> (top) js
      Model menu / BaseHue / Sat --> [prepend set*] --> outlet
      Split / Clear (live.text mode 1) --> [sel 1] --> [split( / [clear( --> outlet
      loadbang --> outputvalue Model ; bang BaseHue / Sat

3 nested params (Model, BaseHue, Sat) + Open on the panel. One Push bank.

pccolor.js is a THIRD dependency: both invertedprism.js and invertedprism_ui.js
`include("pccolor.js")`. Close the device in Max + Live before --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'forteseq', 'forteseqmidifilter.amxd')
DEVICE = os.path.join(ROOT, 'forteseq', 'invertedprism.amxd')
BOOT = '~/PycharmProjects/maxmsp-mcp/forteseq'
JS = 'invertedprism.js'
UI_JS = 'invertedprism_ui.js'
PC_JS = 'pccolor.js'
SUB = 'obj-40'

MODEL_ITEMS = ['sub', 'add', 'oklab']
ANN_OPEN = 'Open the inverted-prism canvas (floating window).'
ANN_MODEL = ('Mix model: sub = pigment (complementary hues -> dark, muddy = dissonant); '
             'add = light (complementary -> white); oklab = perceptual average (the neutral default).')
ANN_HUE = 'Base hue given to C on the circle-of-fifths colour wheel (0-359).'
ANN_SAT = 'Palette saturation of the fundamental colours (0-1).'
ANN_SPLIT = 'Split: solve for the fundamentals whose blend matches the current resultant colour, and drop them as new points.'
ANN_CLEAR = 'Clear all points.'


def tog_vo(ln, sn, init):
    return {'parameter_longname': ln, 'parameter_shortname': sn, 'parameter_type': 2,
            'parameter_enum': ['off', 'on'], 'parameter_mmax': 1, 'parameter_modmode': 0,
            'parameter_initial_enable': 1, 'parameter_initial': [init]}


def menu_vo(ln, sn, items, init):
    return {'parameter_longname': ln, 'parameter_shortname': sn, 'parameter_type': 2,
            'parameter_enum': list(items), 'parameter_range': list(items),
            'parameter_mmax': len(items) - 1, 'parameter_modmode': 0,
            'parameter_initial_enable': 1, 'parameter_initial': [init]}


def nb_vo(ln, sn, mn, mx, init, unit=0):
    return {'parameter_longname': ln, 'parameter_shortname': sn, 'parameter_type': 0,
            'parameter_mmin': float(mn), 'parameter_mmax': float(mx), 'parameter_modmode': 3,
            'parameter_unitstyle': unit, 'parameter_initial_enable': 1, 'parameter_initial': [float(init)]}


# (innerid, longname, shortname, kind, prepend-or-None, valueof, annotation)
CTL = [
    ('obj-201', 'PrismModel', 'Model', 'menu', 'setmodel', menu_vo('PrismModel', 'Model', MODEL_ITEMS, 2), ANN_MODEL),
    ('obj-202', 'BaseHue', 'Hue', 'num', 'setbasehue', nb_vo('BaseHue', 'Hue', 0, 359, 220), ANN_HUE),
    ('obj-203', 'PalSat', 'Sat', 'num', 'setsat', nb_vo('PalSat', 'Sat', 0, 1, 0.62, 1), ANN_SAT),
]


def build_subpatcher(appversion):
    boxes, lines = [], []
    HID = {'hidden': 1}

    def box(**kw):
        boxes.append({'box': kw})

    def line(src, si, dst, di, hide=True):
        pl = {'source': [src, si], 'destination': [dst, di]}
        if hide:
            pl['hidden'] = 1
        lines.append({'patchline': pl})

    box(id='obj-1', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
        patching_rect=[20.0, 8.0, 30.0, 30.0], **HID)
    box(id='obj-2', maxclass='outlet', numinlets=1, numoutlets=0,
        patching_rect=[20.0, 520.0, 30.0, 30.0], **HID)
    box(id='obj-3', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=0, filename=UI_JS,
        patching_rect=[8.0, 60.0, 468.0, 420.0],
        presentation=1, presentation_rect=[8.0, 60.0, 468.0, 420.0], varname='ipw_ui')
    line('obj-3', 0, 'obj-2', 0)        # jsui mouse messages (addpoint/setpoint/rempoint) -> engine

    # controls across the top of the window
    def label(x, txt):
        box(id='obj-l%d' % len(boxes), maxclass='comment', numinlets=1, numoutlets=0,
            patching_rect=[x, 8.0, 60.0, 18.0], presentation=1,
            presentation_rect=[x, 8.0, 60.0, 16.0], fontsize=9.0, text=txt)

    # reharmoniser swatch: pulled out of the jsui and up into the control row, bigger. "heardcolor
    # r g b a" is filtered off the inlet before it reaches the jsui -- only that tag drives the
    # swatch, everything else (points/clusters/harm) passes through to the jsui unchanged.
    box(id='obj-230', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
        patching_rect=[20.0, 500.0, 100.0, 22.0], text='route heardcolor', **HID)
    box(id='obj-231', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[20.0, 700.0, 90.0, 22.0], text='prepend bgcolor', **HID)
    label(404.0, 'Heard')
    box(id='obj-232', maxclass='panel', numinlets=1, numoutlets=0,
        patching_rect=[404.0, 24.0, 72.0, 34.0], presentation=1,
        presentation_rect=[404.0, 20.0, 72.0, 34.0], varname='ipw_heard',
        bgcolor=[0.1, 0.1, 0.12, 1.0])
    line('obj-1', 0, 'obj-230', 0)
    line('obj-230', 1, 'obj-3', 0)      # everything except heardcolor -> jsui, as before
    line('obj-230', 0, 'obj-231', 0)    # heardcolor r g b a (tag stripped) -> prepend bgcolor
    line('obj-231', 0, 'obj-232', 0)

    gx = [8.0, 96.0, 168.0]
    for k, (cid, ln, sn, kind, prep, vo, ann) in enumerate(CTL):
        label(gx[k], sn)
        common = dict(id=cid, parameter_enable=1, varname='c_' + cid.replace('-', '_'),
                      presentation=1, annotation=ann,
                      saved_attribute_attributes={'valueof': vo})
        if kind == 'menu':
            box(maxclass='live.menu', numinlets=1, numoutlets=3, outlettype=['', '', ''],
                patching_rect=[gx[k], 24.0, 76.0, 15.0], presentation_rect=[gx[k], 24.0, 76.0, 15.0], **common)
        else:
            box(maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
                patching_rect=[gx[k], 24.0, 52.0, 15.0], presentation_rect=[gx[k], 24.0, 52.0, 15.0], **common)
        pid = 'p_' + cid
        box(id=pid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
            patching_rect=[8.0, 540.0 + k * 26.0, 140.0, 22.0], text='prepend ' + prep, **HID)
        line(cid, 0, pid, 0)
        line(pid, 0, 'obj-2', 0)

    # Split / Clear action buttons (not params)
    def action(bx_id, x, txt, msg):
        box(id=bx_id, maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
            parameter_enable=0, mode=1, text=txt, texton=txt,
            patching_rect=[x, 24.0, 60.0, 15.0], presentation=1,
            presentation_rect=[x, 24.0, 60.0, 18.0], varname='c_' + bx_id.replace('-', '_'),
            annotation=(ANN_SPLIT if msg == 'split' else ANN_CLEAR))
        sid = 's_' + bx_id
        mid = 'm_' + bx_id
        box(id=sid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
            patching_rect=[x, 640.0, 40.0, 22.0], text='sel 1', **HID)
        box(id=mid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
            patching_rect=[x, 668.0, 50.0, 22.0], text=msg, **HID)
        line(bx_id, 0, sid, 0)
        line(sid, 0, mid, 0)
        line(mid, 0, 'obj-2', 0)

    action('obj-210', 260.0, 'Split', 'split')
    action('obj-211', 330.0, 'Clear', 'clear')

    # loadbang: re-emit stored control values
    box(id='obj-9', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[200.0, 540.0, 62.0, 22.0], text='loadbang', **HID)
    box(id='obj-9m', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[280.0, 540.0, 74.0, 22.0], text='outputvalue', **HID)
    line('obj-9', 0, 'obj-9m', 0)
    line('obj-9m', 0, 'obj-201', 0)     # Model menu
    line('obj-9', 0, 'obj-202', 0)      # bang the numboxes
    line('obj-9', 0, 'obj-203', 0)

    local_params = {cid: [ln, sn, i] for i, (cid, ln, sn, _k, _p, _vo, _a) in enumerate(CTL)}
    local_params['inherited_shortname'] = 1

    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': [120.0, 100.0, 492.0, 500.0], 'openrect': [0.0, 0.0, 492.0, 500.0],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'inverted prism',
        'boxes': boxes, 'lines': lines, 'parameters': local_params,
        'dependency_cache': [
            {'name': UI_JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
            {'name': PC_JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        ],
        'autosave': 0,
    }


def build_top(sub):
    boxes, lines = [], []

    def box(**kw):
        boxes.append({'box': kw})

    def line(src, si, dst, di):
        lines.append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    box(id='obj-1', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['int'],
        patching_rect=[24.0, 300.0, 40.0, 22.0], text='midiin', varname='ip_midiin')
    box(id='obj-2', maxclass='newobj', numinlets=1, numoutlets=0,
        patching_rect=[24.0, 340.0, 47.0, 22.0], text='midiout', varname='ip_midiout')
    line('obj-1', 0, 'obj-2', 0)

    # live reharmoniser feed: held notes -> "note <pitch> <vel>" -> js engine's note() tracker
    # -> heardcolor swatch. Independent of the midiin/midiout pass-through above.
    box(id='obj-3', maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['', '', ''],
        patching_rect=[24.0, 380.0, 60.0, 22.0], text='notein', varname='ip_notein')
    box(id='obj-4', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 420.0, 60.0, 22.0], text='pack 0 0', varname='ip_pack')
    box(id='obj-5', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 460.0, 70.0, 22.0], text='prepend note', varname='ip_prepend_note')
    line('obj-3', 0, 'obj-4', 0)
    line('obj-3', 1, 'obj-4', 1)
    line('obj-4', 0, 'obj-5', 0)
    line('obj-5', 0, 'obj-10', 0)

    box(id='obj-10', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 120.0, 150.0, 22.0], text='js ' + JS, varname='ip_engine',
        saved_object_attributes={'filename': JS, 'parameter_enable': 0})

    box(id='obj-11', maxclass='newobj', numinlets=1, numoutlets=7,
        outlettype=[''] * 7, patching_rect=[24.0, 160.0, 320.0, 22.0],
        text='route chord clusters harm points heardcolor split', varname='ip_route')
    line('obj-10', 0, 'obj-11', 0)

    # chord path: flush the old chord, then play the new notes
    box(id='obj-12', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', 'bang'],
        patching_rect=[24.0, 200.0, 40.0, 22.0], text='t l b', varname='ip_trig')
    box(id='obj-13', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[120.0, 200.0, 44.0, 22.0], text='flush', varname='ip_flush')
    box(id='obj-14', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 230.0, 34.0, 22.0], text='iter', varname='ip_iter')
    # makenote here is 2-out on this Max build (note number, velocity) -- NOT 3 like the
    # `makenote 100 200 1` in forteseqwf/harmonograph. Wiring a 3rd cord makes Max delete it
    # and log "patchcord outlet out of range" on every load.
    box(id='obj-15', maxclass='newobj', numinlets=3, numoutlets=2,
        outlettype=['int', 'int'],
        patching_rect=[24.0, 260.0, 100.0, 22.0], text='makenote 90 800', varname='ip_makenote')
    box(id='obj-16', maxclass='newobj', numinlets=3, numoutlets=0,
        patching_rect=[24.0, 300.0, 47.0, 22.0], text='noteout', varname='ip_noteout')
    line('obj-11', 0, 'obj-12', 0)
    line('obj-12', 1, 'obj-13', 0)      # b (fires first) -> flush
    line('obj-12', 0, 'obj-14', 0)      # l -> iter
    line('obj-13', 0, 'obj-15', 0)
    line('obj-14', 0, 'obj-15', 0)
    line('obj-15', 0, 'obj-16', 0)
    line('obj-15', 1, 'obj-16', 1)

    # tags -> window
    tags = [('obj-21', 'clusters', 1), ('obj-22', 'harm', 2),
            ('obj-23', 'points', 3), ('obj-24', 'heardcolor', 4)]
    for bid, tag, outn in tags:
        box(id=bid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
            patching_rect=[200.0 + outn * 20.0, 200.0 + outn * 22.0, 110.0, 22.0],
            text='prepend ' + tag, varname='ip_tag_' + tag)
        line('obj-11', outn, bid, 0)
        line(bid, 0, SUB, 0)

    box(id=SUB, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[300.0, 120.0, 120.0, 22.0], text='p ip_window', varname='ip_window',
        patcher=sub)
    line(SUB, 0, 'obj-10', 0)           # window controls + jsui mouse -> engine

    # panel: OPEN
    box(id='obj-30', maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=1, mode=1, text='OPEN', texton='OPEN',
        patching_rect=[24.0, 40.0, 90.0, 24.0], presentation=1,
        presentation_rect=[8.0, 8.0, 100.0, 22.0], varname='ip_open_btn', annotation=ANN_OPEN,
        saved_attribute_attributes={'valueof': {
            'parameter_longname': 'Open', 'parameter_shortname': 'Open', 'parameter_type': 2,
            'parameter_enum': ['off', 'on'], 'parameter_mmax': 1, 'parameter_modmode': 0,
            'parameter_initial_enable': 1, 'parameter_initial': [0]}})
    box(id='obj-31', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 76.0, 48.0, 22.0], text='open', varname='ip_msg_open')
    box(id='obj-32', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 100.0, 56.0, 22.0], text='pcontrol', varname='ip_pcontrol')
    box(id='obj-33', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['bang', 'bang'],
        patching_rect=[140.0, 40.0, 110.0, 22.0], text='live.thisdevice', varname='ip_thisdev')
    line('obj-30', 0, 'obj-31', 0)
    line('obj-33', 0, 'obj-31', 0)
    line('obj-31', 0, 'obj-32', 0)
    line('obj-32', 0, SUB, 0)

    return boxes, lines


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(TEMPLATE)
    P = doc['patcher']
    appversion = P['appversion']

    sub = build_subpatcher(appversion)
    boxes, lines = build_top(sub)
    P['boxes'] = boxes
    P['lines'] = lines

    params = {'obj-30': ['Open', 'Open', 0]}
    for i, (cid, ln, sn, _k, _p, _vo, _a) in enumerate(CTL):
        params['%s::%s' % (SUB, cid)] = [ln, sn, i + 1]
    params['parameterbanks'] = {
        '0': {'index': 0, 'name': 'Prism',
              'parameters': ['PrismModel', 'BaseHue', 'PalSat', '-', '-', '-', '-', '-']},
    }
    params['inherited_shortname'] = 1
    P['parameters'] = params

    P['dependency_cache'] = [
        {'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        {'name': UI_JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        {'name': PC_JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
    ]
    P['rect'] = [140.0, 140.0, 540.0, 420.0]
    P['openinpresentation'] = 1

    # self-checks
    def check_patcher(p, where, errors):
        ids = [b['box']['id'] for b in p['boxes']]
        for x in ids:
            if ids.count(x) > 1:
                errors.append('%s: duplicate id %s' % (where, x))
        known = set(ids)
        for ln in p['lines']:
            pl = ln['patchline']
            for lab, end in (('src', pl['source']), ('dst', pl['destination'])):
                if not (isinstance(end[0], str) and end[0] in known):
                    errors.append('%s: %s endpoint %r unknown' % (where, lab, end))
        for b in p['boxes']:
            if b['box'].get('patcher'):
                check_patcher(b['box']['patcher'], where + '::' + b['box']['id'], errors)

    errors = []
    check_patcher(P, 'root', errors)
    subbox = [b['box'] for b in P['boxes'] if b['box']['id'] == SUB][0]
    nested = {v[0] for k, v in params.items() if '::' in k}
    sub_local = {v[0] for k, v in subbox['patcher']['parameters'].items() if k != 'inherited_shortname'}
    if nested != sub_local:
        errors.append('nested != subpatcher-local params: %r' % (nested ^ sub_local))
    for nm in params['parameterbanks']['0']['parameters']:
        if nm != '-' and nm not in {v[0] for k, v in params.items() if k not in ('parameterbanks', 'inherited_shortname')}:
            errors.append('bank lists unknown %r' % nm)
    if errors:
        for er in errors:
            print(' -', er)
        raise SystemExit('self-checks failed')

    print('invertedprism.amxd')
    print('  top boxes : %d   sub boxes : %d' % (len(P['boxes']), len(subbox['patcher']['boxes'])))
    print('  top lines : %d   sub lines : %d' % (len(P['lines']), len(subbox['patcher']['lines'])))
    print('  params    : Open + %s' % ', '.join(v[0] for k, v in params.items() if '::' in k))
    print('  js deps   : %s, %s, %s' % (JS, UI_JS, PC_JS))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    if os.path.exists(DEVICE):
        shutil.copyfile(DEVICE, DEVICE + '.before')
        print('  backup    : %s.before' % os.path.basename(DEVICE))
    shutil.copyfile(TEMPLATE, DEVICE)
    d2, s2, e2, _ = amxd.load(DEVICE)
    amxd.save(DEVICE, d2, s2, e2, doc)
    back = amxd.load(DEVICE)[3]['patcher']
    bb = [b['box'] for b in back['boxes'] if b['box']['id'] == SUB][0]
    assert bb.get('patcher') and len(bb['patcher']['boxes']) == len(subbox['patcher']['boxes'])
    assert back['dependency_cache'][0]['name'] == JS
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/invertedprism.amxd')


main()
