"""Build forteseq/multichord.amxd -- the annular voice-leading space device.

    python tools/build_multichord.py            dry run
    python tools/build_multichord.py --apply    do it

Same method as build_harmonograph.py / build_invertedprism.py: copy forteseqmidifilter.amxd
(keeps the AMPF/meta chunk that marks it a MIDI effect) and rewrite boxes / lines /
parameters / dependency_cache.

Panel: an OPEN button. Floating window `[p mc_window]` (pcontrol scheme, like invertedprism),
two control rows above the jsui canvas:
    row 1 (always relevant): Root / ChordIdx / Nav / HueC / PalSat / PalLum / Span
    row 2 (Steps-mode config + View): Mode / ScaleIdx / ScaleRoot / MinSize / MaxSize / View

View picks Rings-vs-Spiral drawing independently of Mode -- either exploration mode can be looked
at either way. It's a local jsui display setting (message goes straight to the jsui, not through
the engine): see multichord_ui.js's view() handler.
Two exploration modes, picked by `Mode` (multichord.js's computeRankList()):
    Nearest -- rank every transposed chord in the whole 351-class universe by total circular
               voice-leading distance (any chord type may be a close neighbour). The original mode.
    Steps   -- stay inside one fixed scale (ScaleIdx/ScaleRoot) and move exactly one voice by one
               scale-step at a time (Callender/Quinn/Tymoczko generalized voice-leading spaces,
               madmusicalscience.com/cs.html), OR drop/add a voice to modulate to a differently
               sized chord, bounded to [MinSize, MaxSize] -- MinSize also seeds how many scale
               degrees a Steps-mode chord starts with. Steps-mode neighbours still resolve back
               through the engine's UNIVERSE_BY_MASK, so the wire format to the jsui (and
               Nav/click navigation) is identical either way -- Mode only changes how the
               neighbour list is generated.

    top patcher:
      js multichord.js  outlet --> route center ringinfo nodes noteoff noteon dialsync scale voices
          center/ringinfo/nodes/scale/voices --> prepend <tag> --> [p mc_window] inlet 0 --> jsui
              (scale/voices always sent -- chromatic-12 stands in for the scale in Nearest mode --
              so the jsui's Spiral view has something valid to draw regardless of Mode)
          noteoff --> iter --> pack 0 0  --> noteout   (sustained until the next recentre)
          noteon  --> iter --> pack 0 90 --> noteout
          dialsync --> prepend set --> [p mc_window] inlet 1 --> Nav's own inlet
              (resyncs the physical numbox's display after a node click or a Root/ChordIdx/
              Mode change WITHOUT re-firing dial() -- a plain "set" message to a UI object's
              inlet updates its display without triggering its outlet)
      midiin --> midiout                                   (pass-through)
      OPEN / live.thisdevice --> open --> pcontrol --> [p mc_window]

    [p mc_window]:
      inlet 0 --> jsui multichord_ui.js
      inlet 1 --> Nav (dialsync resync)
      jsui outlet (selectrank) --> outlet --> (top) js
      every control --> [prepend set*] --> outlet
      loadbang --> bang HueC/PalSat/PalLum/Span directly (order-independent); --> [t b b b]:
          rightmost (fires 1st) bangs Root/ChordIdx/ScaleIdx/ScaleRoot/MinSize/MaxSize (any
          order among themselves), middle (2nd) bangs Mode (validates/reseeds against whichever
          centre + scale those just restored), leftmost (3rd, last) bangs Nav (applies its
          restored rank against the neighbour list Mode just rebuilt).

13 nested params (Root, ChordIdx, Nav, HueC, PalSat, PalLum, Span, Mode, ScaleIdx, ScaleRoot,
MinSize, MaxSize, View) + Open on the panel. Two Push banks ("Multichord", "Steps mode").

pccolor.js is a THIRD dependency: multichord.js and multichord_ui.js both `include("pccolor.js")`.
Close the device in Max + Live before --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'forteseq', 'forteseqmidifilter.amxd')
DEVICE = os.path.join(ROOT, 'forteseq', 'multichord.amxd')
BOOT = '~/PycharmProjects/maxmsp-mcp/forteseq'
JS = 'multichord.js'
UI_JS = 'multichord_ui.js'
PC_JS = 'pccolor.js'
SUB = 'obj-40'

ANN_OPEN = 'Open the annular voice-leading space (floating window).'
ANN_ROOT = 'Starting root pitch class (0=C .. 11=B) for the chord picker.'
ANN_CHORDIDX = ('Starting chord type: index 0-350 into the 351 Forte Tn-classes (0 = single note, '
                 '350 = full chromatic aggregate), sorted by cardinality then value.')
ANN_NAV = ('Explore: each step recentres the space on the next-ranked voice-leading neighbour of '
            'wherever you currently are. Click a node in the window to jump straight there.')
ANN_HUEC = 'Base hue given to C on the circle-of-fifths colour wheel (0-359).'
ANN_PALSAT = 'Palette saturation of the chord-colour wheel (0-1).'
ANN_PALLUM = 'Palette lightness of the chord-colour wheel (0-1).'
ANN_SPAN = ('How far apart the voicing spreads (0-48 semitones). 0 collapses every note onto the '
            'same reference pitch (closed); higher values open the chord across a wider register.')
ANN_REGUP = 'Shift the current voicing up an octave.'
ANN_REGDOWN = 'Shift the current voicing down an octave.'
ANN_SCALARUP = ('Scalar transposition up: shift EVERY voice by the same scale-step at once, '
                 'preserving the chord\'s shape/position relative to the scale -- unlike Nav, '
                 'which jumps to a nearby chord that may not share that shape at all.')
ANN_SCALARDOWN = 'Scalar transposition down: the same, one scale-step lower.'
ANN_MODE = ('Nearest: rank every transposed chord in the whole 351-class universe by total '
            'voice-leading distance (any chord type may be a close neighbour). Steps: stay inside '
            'one fixed scale and move exactly one voice by one scale-step at a time (Callender/'
            'Quinn/Tymoczko generalized voice-leading spaces, madmusicalscience.com/cs.html).')
ANN_SCALEIDX = ('Steps mode only: which of the 351 Forte Tn-classes to use as the scale (default: '
                 'the major scale).')
ANN_SCALEROOT = 'Steps mode only: root pitch class of the scale (0=C .. 11=B).'
ANN_MINSIZE = ('Steps mode only: smallest chord size allowed. A chord starts here and can grow up '
               'to MaxSize (or shrink back down) via drop/add-a-voice moves during exploration.')
ANN_MAXSIZE = 'Steps mode only: largest chord size drop/add-a-voice moves are allowed to grow to.'
ANN_VIEW = ('How to draw the space -- independent of Mode, either exploration mode can be viewed '
            'either way. Rings: neighbours laid out by distance from the centre, click to jump. '
            'Spiral: madmusicalscience.com/cs.html-style single winding curve through the current '
            "chord's own voices (chord size = winding count, scale size = points per winding; "
            'chromatic-12 stands in for the scale in Nearest mode). Read-only.')


def nb_vo(ln, sn, mn, mx, init, unit=0):
    return {'parameter_longname': ln, 'parameter_shortname': sn, 'parameter_type': 0,
            'parameter_mmin': float(mn), 'parameter_mmax': float(mx), 'parameter_modmode': 3,
            'parameter_unitstyle': unit, 'parameter_initial_enable': 1, 'parameter_initial': [float(init)]}


def menu_vo(ln, sn, items, init):
    return {'parameter_longname': ln, 'parameter_shortname': sn, 'parameter_type': 2,
            'parameter_enum': list(items), 'parameter_range': list(items),
            'parameter_mmax': len(items) - 1, 'parameter_modmode': 0,
            'parameter_initial_enable': 1, 'parameter_initial': [init]}


# --- replica of multichord.js's buildClasses(), just to compute the default ChordIdx for
# [0,4,7] (C major) so the ChordIdx numbox's stored default matches what the engine actually
# centres on at load. Kept intentionally tiny -- this is NOT the device's chord-universe logic,
# that lives only in multichord.js.
def _rotate12(x):
    return ((x << 1) | (x >> 11)) & 0xFFF


def _build_classes():
    seen = set()
    canon = []
    for n in range(1, 4096):
        best = n
        cur = n
        for _ in range(11):
            cur = _rotate12(cur)
            if cur < best:
                best = cur
        if best not in seen:
            seen.add(best)
            canon.append(best)
    canon.sort(key=lambda b: (bin(b).count('1'), b))
    classes = []
    for bits in canon:
        classes.append([p for p in range(12) if bits & (1 << p)])
    return classes


def _bitmask(pcs):
    m = 0
    for pc in pcs:
        m |= (1 << pc)
    return m


def _identify_pcs(pcs):
    """Which Forte class `pcs` belongs to AND at what transposition -- not just when `pcs`
    happens to already be its class's own canonical (minimal-bitmask) rotation. [0,4,7] is by
    luck already canonical (t=0); [0,2,4,5,7,9,11] (major scale) is not."""
    target = _bitmask(pcs)
    for ci, c in enumerate(_CLASSES):
        for t in range(12):
            if _bitmask(sorted((p + t) % 12 for p in c)) == target:
                return ci, t
    raise ValueError('no Forte class matches %r at any transposition' % (pcs,))


_CLASSES = _build_classes()
assert len(_CLASSES) == 351, 'buildClasses replica drifted from multichord.js: got %d classes' % len(_CLASSES)
DEFAULT_CHORDIDX, DEFAULT_ROOT = _identify_pcs([0, 4, 7])
DEFAULT_SCALEIDX, DEFAULT_SCALEROOT = _identify_pcs([0, 2, 4, 5, 7, 9, 11])

MODE_ITEMS = ['Nearest', 'Steps']
VIEW_ITEMS = ['Rings', 'Spiral']

# Controls whose message goes straight to the jsui (obj-3, in-subpatcher) instead of up through
# the engine's `js` object -- purely local display settings, not engine state.
JSUI_TARGET_CONTROLS = {'View'}

# Row 1 -- always relevant. (innerid, longname, shortname, kind, prepend, valueof, annotation)
CTL = [
    ('obj-201', 'Root', 'Root', 'num', 'setroot', nb_vo('Root', 'Root', 0, 11, DEFAULT_ROOT), ANN_ROOT),
    ('obj-202', 'ChordIdx', 'Chord', 'num', 'setchordidx', nb_vo('ChordIdx', 'Chord', 0, 350, DEFAULT_CHORDIDX), ANN_CHORDIDX),
    ('obj-203', 'Nav', 'Nav', 'num', 'dial', nb_vo('Nav', 'Nav', 0, 47, 0), ANN_NAV),
    ('obj-204', 'HueC', 'Hue', 'num', 'sethuec', nb_vo('HueC', 'Hue', 0, 359, 220), ANN_HUEC),
    ('obj-205', 'PalSat', 'Sat', 'num', 'setpalsat', nb_vo('PalSat', 'Sat', 0, 1, 0.62, 1), ANN_PALSAT),
    ('obj-206', 'PalLum', 'Lum', 'num', 'setpallum', nb_vo('PalLum', 'Lum', 0, 1, 0.55, 1), ANN_PALLUM),
    ('obj-207', 'Span', 'Span', 'num', 'setspan', nb_vo('Span', 'Span', 0, 48, 24), ANN_SPAN),
]

# Row 2 -- Steps-mode configuration (Mode itself lives here too, since it's what decides whether
# the rest of the row matters) plus View, which applies to either mode.
ROW2_CTL = [
    ('obj-220', 'Mode', 'Mode', 'menu', 'setmode', menu_vo('Mode', 'Mode', MODE_ITEMS, 0), ANN_MODE),
    ('obj-221', 'ScaleIdx', 'Scale', 'num', 'setscaleidx', nb_vo('ScaleIdx', 'Scale', 0, 350, DEFAULT_SCALEIDX), ANN_SCALEIDX),
    ('obj-222', 'ScaleRoot', 'ScRoot', 'num', 'setscaleroot', nb_vo('ScaleRoot', 'ScRoot', 0, 11, DEFAULT_SCALEROOT), ANN_SCALEROOT),
    ('obj-223', 'MinSize', 'Min', 'num', 'setminsize', nb_vo('MinSize', 'Min', 1, 12, 3), ANN_MINSIZE),
    ('obj-224', 'MaxSize', 'Max', 'num', 'setmaxsize', nb_vo('MaxSize', 'Max', 1, 12, 7), ANN_MAXSIZE),
    ('obj-225', 'View', 'View', 'menu', 'view', menu_vo('View', 'View', VIEW_ITEMS, 0), ANN_VIEW),
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
    box(id='obj-1b', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
        patching_rect=[60.0, 8.0, 30.0, 30.0], **HID)
    box(id='obj-2', maxclass='outlet', numinlets=1, numoutlets=0,
        patching_rect=[20.0, 688.0, 30.0, 30.0], **HID)
    # jsui sits below BOTH control rows (row 1 ends y=39, row 2 ends y=71)
    box(id='obj-3', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=0, filename=UI_JS,
        patching_rect=[8.0, 88.0, 640.0, 560.0],
        presentation=1, presentation_rect=[8.0, 88.0, 640.0, 560.0], varname='mcw_ui')
    line('obj-1', 0, 'obj-3', 0)         # tagged center/ringinfo/nodes messages -> jsui (auto-dispatched by selector)
    line('obj-3', 0, 'obj-2', 0)         # jsui "selectrank" -> engine

    def label(x, y, txt):
        box(id='obj-l%d' % len(boxes), maxclass='comment', numinlets=1, numoutlets=0,
            patching_rect=[x, y, 64.0, 18.0], presentation=1,
            presentation_rect=[x, y, 64.0, 16.0], fontsize=9.0, text=txt)

    ctl_id = {}   # longname -> box id, for cross-references below (Nav, dialsync target)
    hidden_y = [628.0]   # shared cursor for the hidden prepend/hookup boxes below the window

    def ctl_row(ctl_list, gx, label_y, ctrl_y):
        for k, (cid, ln, sn, kind, prep, vo, ann) in enumerate(ctl_list):
            ctl_id[ln] = cid
            label(gx[k], label_y, sn)
            common = dict(id=cid, parameter_enable=1, varname='c_' + cid.replace('-', '_'),
                          presentation=1, annotation=ann,
                          saved_attribute_attributes={'valueof': vo})
            if kind == 'menu':
                box(maxclass='live.menu', numinlets=1, numoutlets=3, outlettype=['', '', ''],
                    patching_rect=[gx[k], ctrl_y, 76.0, 15.0], presentation_rect=[gx[k], ctrl_y, 76.0, 15.0], **common)
            else:
                box(maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
                    patching_rect=[gx[k], ctrl_y, 52.0, 15.0], presentation_rect=[gx[k], ctrl_y, 52.0, 15.0], **common)
            pid = 'p_' + cid
            box(id=pid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
                patching_rect=[8.0, hidden_y[0], 140.0, 22.0], text='prepend ' + prep, **HID)
            hidden_y[0] += 26.0
            line(cid, 0, pid, 0)
            # jsui-targeted controls (View) are a local display setting -- send straight to the
            # in-subpatcher jsui (obj-3), not up through obj-2 to the engine.
            line(pid, 0, 'obj-3' if ln in JSUI_TARGET_CONTROLS else 'obj-2', 0)

    gx1 = [8.0, 68.0, 132.0, 216.0, 280.0, 344.0, 408.0]
    ctl_row(CTL, gx1, 8.0, 24.0)
    gx2 = [8.0, 100.0, 172.0, 244.0, 296.0, 376.0]
    ctl_row(ROW2_CTL, gx2, 40.0, 56.0)

    # dialsync resync: inlet 1 -> "set <rank>" straight into Nav's own inlet. A plain "set"
    # message to a UI object's inlet updates its displayed value without firing its outlet, so
    # this can't loop back into dial().
    line('obj-1b', 0, ctl_id['Nav'], 0)

    # Action buttons (not Live params -- same pattern as invertedprism's Split/Clear): fire a
    # fixed message straight into the engine, independent of any numbox/menu state.
    def action(bx_id, x, txt, msg, ann, y=24.0):
        box(id=bx_id, maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
            parameter_enable=0, mode=1, text=txt, texton=txt,
            patching_rect=[x, y, 30.0, 15.0], presentation=1,
            presentation_rect=[x, y, 30.0, 18.0], varname='c_' + bx_id.replace('-', '_'),
            annotation=ann)
        sid = 's_' + bx_id
        mid = 'm_' + bx_id
        box(id=sid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
            patching_rect=[x, hidden_y[0], 40.0, 22.0], text='sel 1', **HID)
        box(id=mid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
            patching_rect=[x, hidden_y[0] + 26.0, 50.0, 22.0], text=msg, **HID)
        line(bx_id, 0, sid, 0)
        line(sid, 0, mid, 0)
        line(mid, 0, 'obj-2', 0)

    # Register nudge: shift the CURRENT voicing an octave up/down in place, independent of Span.
    action('obj-210', 472.0, '▲', 'regup', ANN_REGUP)
    action('obj-211', 504.0, '▼', 'regdown', ANN_REGDOWN)
    # Scalar transposition: shift the WHOLE chord by one scale-step, preserving its shape --
    # row 2 (alongside Mode/Scale/View, since it depends on whichever scale is configured there).
    action('obj-212', 460.0, '◂', 'scalardown', ANN_SCALARDOWN, y=56.0)
    action('obj-213', 492.0, '▸', 'scalarup', ANN_SCALARUP, y=56.0)
    hidden_y[0] += 52.0

    # loadbang: HueC/PalSat/PalLum/Span order doesn't matter (recolor() just redraws the current
    # centre). The rest is a strict chain: Root/ChordIdx/ScaleIdx/ScaleRoot/MinSize/MaxSize (any order
    # among themselves) must ALL land before Mode checks/reseeds against them, and Mode must land
    # before Nav applies its restored rank against the neighbour list Mode just rebuilt. [t b b b]
    # fires right-to-left (documented, deterministic -- unlike relying on multi-cord fan-out
    # order): rightmost = the group-of-5, middle = Mode, leftmost = Nav (fires last).
    box(id='obj-9', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[200.0, hidden_y[0], 62.0, 22.0], text='loadbang', **HID)
    box(id='obj-9t', maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['bang', 'bang', 'bang'],
        patching_rect=[280.0, hidden_y[0], 60.0, 22.0], text='t b b b', **HID)
    line('obj-9', 0, 'obj-9t', 0)
    for ln in ('Root', 'ChordIdx', 'ScaleIdx', 'ScaleRoot', 'MinSize', 'MaxSize', 'View'):
        line('obj-9t', 2, ctl_id[ln], 0)    # fires 1st (rightmost) -- restore-only group
    line('obj-9t', 1, ctl_id['Mode'], 0)    # fires 2nd -- Mode (reseeds/validates against the above)
    line('obj-9t', 0, ctl_id['Nav'], 0)     # fires 3rd (leftmost, last) -- Nav
    line('obj-9', 0, ctl_id['HueC'], 0)
    line('obj-9', 0, ctl_id['PalSat'], 0)
    line('obj-9', 0, ctl_id['PalLum'], 0)
    line('obj-9', 0, ctl_id['Span'], 0)

    local_params = {cid: [ln, sn, i] for i, (cid, ln, sn, _k, _p, _vo, _a) in enumerate(CTL)}
    for i, (cid, ln, sn, _k, _p, _vo, _a) in enumerate(ROW2_CTL):
        local_params[cid] = [ln, sn, len(CTL) + i]
    local_params['inherited_shortname'] = 1

    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': [120.0, 100.0, 664.0, 728.0], 'openrect': [0.0, 0.0, 664.0, 728.0],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'multichord',
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
        patching_rect=[24.0, 300.0, 40.0, 22.0], text='midiin', varname='mc_midiin')
    box(id='obj-2', maxclass='newobj', numinlets=1, numoutlets=0,
        patching_rect=[24.0, 340.0, 47.0, 22.0], text='midiout', varname='mc_midiout')
    line('obj-1', 0, 'obj-2', 0)

    box(id='obj-10', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 120.0, 150.0, 22.0], text='js ' + JS, varname='mc_engine',
        saved_object_attributes={'filename': JS, 'parameter_enable': 0})

    # scale/voices/shiftmoves appended at the END so existing outlet indices (noteoff=3, noteon=4,
    # dialsync=5) stay untouched; they're always sent now (see multichord.js's emitState()).
    # route's outlet count is (number of match arguments) + 1 -- the trailing outlet passes
    # through anything that matches none of them (unwired here, but must still exist: every other
    # `route` box in this codebase follows the same N+1 convention, e.g. build_invertedprism.py's
    # `route chord clusters harm points heardcolor split` -> numoutlets=7 for 6 arguments).
    ROUTE_TAGS = ['center', 'ringinfo', 'nodes', 'noteoff', 'noteon', 'dialsync', 'scale', 'voices', 'shiftmoves']
    box(id='obj-11', maxclass='newobj', numinlets=1, numoutlets=len(ROUTE_TAGS) + 1,
        outlettype=[''] * (len(ROUTE_TAGS) + 1), patching_rect=[24.0, 160.0, 460.0, 22.0],
        text='route ' + ' '.join(ROUTE_TAGS), varname='mc_route')
    line('obj-10', 0, 'obj-11', 0)

    # noteoff / noteon: pitch-only lists -> iter -> pack (fixed velocity) -> noteout. Sustained
    # (not auto-released) -- the noteoff for the PREVIOUS voicing is emitted right before the
    # noteon for the new one on every recentre, see multichord.js's voiceAndEmit().
    box(id='obj-13', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 200.0, 40.0, 22.0], text='iter', varname='mc_iter_off')
    box(id='obj-14', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 230.0, 70.0, 22.0], text='pack 0 0', varname='mc_pack_off')
    box(id='obj-15', maxclass='newobj', numinlets=3, numoutlets=0,
        patching_rect=[24.0, 260.0, 47.0, 22.0], text='noteout', varname='mc_noteout_off')
    line('obj-11', 3, 'obj-13', 0)
    line('obj-13', 0, 'obj-14', 0)
    line('obj-14', 0, 'obj-15', 0)

    box(id='obj-16', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[120.0, 200.0, 40.0, 22.0], text='iter', varname='mc_iter_on')
    box(id='obj-17', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[120.0, 230.0, 70.0, 22.0], text='pack 0 90', varname='mc_pack_on')
    box(id='obj-18', maxclass='newobj', numinlets=3, numoutlets=0,
        patching_rect=[120.0, 260.0, 47.0, 22.0], text='noteout', varname='mc_noteout_on')
    line('obj-11', 4, 'obj-16', 0)
    line('obj-16', 0, 'obj-17', 0)
    line('obj-17', 0, 'obj-18', 0)

    # tags -> window inlet 0 (center/ringinfo/nodes/scale/voices/shiftmoves)
    tags = [('obj-21', 'center', 0), ('obj-22', 'ringinfo', 1), ('obj-23', 'nodes', 2),
            ('obj-25', 'scale', 6), ('obj-26', 'voices', 7), ('obj-27', 'shiftmoves', 8)]
    for bid, tag, outn in tags:
        box(id=bid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
            patching_rect=[220.0 + outn * 90.0, 200.0 + outn * 22.0, 110.0, 22.0],
            text='prepend ' + tag, varname='mc_tag_' + tag)
        line('obj-11', outn, bid, 0)
        line(bid, 0, SUB, 0)

    # dialsync -> window inlet 1 (Nav's own inlet, resync display without re-firing dial())
    box(id='obj-24', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[500.0, 288.0, 90.0, 22.0], text='prepend set', varname='mc_tag_dialsync')
    line('obj-11', 5, 'obj-24', 0)
    line('obj-24', 0, SUB, 1)

    box(id=SUB, maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[300.0, 120.0, 120.0, 22.0], text='p mc_window', varname='mc_window',
        patcher=sub)
    line(SUB, 0, 'obj-10', 0)           # jsui "selectrank" -> engine

    # panel: OPEN
    box(id='obj-30', maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=1, mode=1, text='OPEN', texton='OPEN',
        patching_rect=[24.0, 40.0, 90.0, 24.0], presentation=1,
        presentation_rect=[8.0, 8.0, 100.0, 22.0], varname='mc_open_btn', annotation=ANN_OPEN,
        saved_attribute_attributes={'valueof': {
            'parameter_longname': 'Open', 'parameter_shortname': 'Open', 'parameter_type': 2,
            'parameter_enum': ['off', 'on'], 'parameter_mmax': 1, 'parameter_modmode': 0,
            'parameter_initial_enable': 1, 'parameter_initial': [0]}})
    box(id='obj-31', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 76.0, 48.0, 22.0], text='open', varname='mc_msg_open')
    box(id='obj-32', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 100.0, 56.0, 22.0], text='pcontrol', varname='mc_pcontrol')
    box(id='obj-33', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['bang', 'bang'],
        patching_rect=[140.0, 40.0, 110.0, 22.0], text='live.thisdevice', varname='mc_thisdev')
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
    idx = 1
    for cid, ln, sn, _k, _p, _vo, _a in CTL + ROW2_CTL:
        params['%s::%s' % (SUB, cid)] = [ln, sn, idx]
        idx += 1
    params['parameterbanks'] = {
        '0': {'index': 0, 'name': 'Multichord',
              'parameters': ['Root', 'ChordIdx', 'Nav', 'HueC', 'PalSat', 'PalLum', 'Span', 'View']},
        '1': {'index': 1, 'name': 'Steps mode',
              'parameters': ['Mode', 'ScaleIdx', 'ScaleRoot', 'MinSize', 'MaxSize', '-', '-', '-']},
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
    known_names = {v[0] for k, v in params.items() if k not in ('parameterbanks', 'inherited_shortname')}
    for bank in params['parameterbanks'].values():
        for nm in bank['parameters']:
            if nm != '-' and nm not in known_names:
                errors.append('bank %r lists unknown %r' % (bank['name'], nm))
    if not (0 <= DEFAULT_CHORDIDX <= 350):
        errors.append('DEFAULT_CHORDIDX out of range: %r' % DEFAULT_CHORDIDX)
    if not (0 <= DEFAULT_SCALEIDX <= 350):
        errors.append('DEFAULT_SCALEIDX out of range: %r' % DEFAULT_SCALEIDX)
    if errors:
        for er in errors:
            print(' -', er)
        raise SystemExit('self-checks failed')

    print('multichord.amxd')
    print('  top boxes : %d   sub boxes : %d' % (len(P['boxes']), len(subbox['patcher']['boxes'])))
    print('  top lines : %d   sub lines : %d' % (len(P['lines']), len(subbox['patcher']['lines'])))
    print('  params    : Open + %s' % ', '.join(v[0] for k, v in params.items() if '::' in k))
    print('  default   : ChordIdx=%d (C major, [0,4,7])   ScaleIdx=%d (major scale, [0,2,4,5,7,9,11])'
          % (DEFAULT_CHORDIDX, DEFAULT_SCALEIDX))
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
    print('now: python tools/check_structure.py forteseq/multichord.amxd')


main()
