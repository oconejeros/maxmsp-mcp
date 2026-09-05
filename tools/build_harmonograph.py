"""Build forteseq/harmonograph.amxd -- the PB (perfectly-balanced) rhythm device.

    python tools/build_harmonograph.py            dry run, writes nothing
    python tools/build_harmonograph.py --apply    do it

Same method as build_tonnetz.py / build_midibounce.py: copy the near-stock
forteseqmidifilter.amxd (keeps the AMPF/meta chunk that marks the file a MIDI effect) and
rewrite boxes / lines / parameters / dependency_cache.

Layout (step 4): the device panel in the rack is just a Run toggle, a Period numbox and an
"OPEN" button. Everything else -- 8 layers x {Sides, Rot, Weight, Pitch, Axis}, the four
engine globals and the harmonograph jsui -- lives in an inline subpatcher `[p hg_window]`
that opens as its own floating window via `[pcontrol]`, exactly the tonnetz.amxd scheme.
`live.thisdevice` opens it on load.

    top patcher:
      metronome:  Run --> metro   AND  [prepend setrun]  --> js
                  Period --> metro inlet 1  AND  [prepend setperiod] --> js
      js outlet --> route n ms curve marks hit
          "n"  (pitch vel dur)  --> makenote 100 200 1 --> noteout
          "ms" (synced period)  --> metro inlet 1
          "curve"/"marks"/"hit" --> [prepend <tag>] --> [p hg_window] inlet 0 --> jsui
      live.path live_set --> live.observer tempo / is_playing --> [prepend set*] --> js
      OPEN button / live.thisdevice --> open --> pcontrol --> [p hg_window]

    [p hg_window]:
      inlet --> jsui harmonograph_ui.js
      each control --> [prepend <msg>] (hidden) --> outlet --> (top) js inlet 0
      loadbang --> bang each numbox / outputvalue each menu+toggle  (Live restores the
                   value but does NOT fire the outlet -- see the setnumber-quirk note)

Nested params are registered BOTH in the subpatcher's own `parameters` block AND on the
top patcher as `<SUBID>::<innerid>` keys -- the FORTESEQ2 / tonnetz nesting scheme. Push
banks group by field (Sides / Rotation / Weight / Pitch / Axis) -- "what you turn together".

Close the device in BOTH Max and Live before running with --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'forteseq', 'forteseqmidifilter.amxd')
DEVICE = os.path.join(ROOT, 'forteseq', 'harmonograph.amxd')
BOOT = '~/PycharmProjects/maxmsp-mcp/forteseq'
JS = 'harmonograph.js'
UI_JS = 'harmonograph_ui.js'
SUB = 'obj-50'                       # box id of the [p hg_window] subpatcher on the top patcher

AXIS_ITEMS = ['X', 'Y', 'XY', 'Rot']
KDEF = [3, 4, 5, 3, 4, 5, 3, 4]
PDEF = [48, 52, 55, 59, 62, 64, 67, 71]
NLAYERS = 8
MOD_LANE_SIZE = 8      # must match harmonograph.js's MOD_LANE_SIZE
MOD_LEVELS = 8          # must match harmonograph.js's MOD_LEVELS (quantized step values 0..7)
PRESET_SLOTS = 20       # must match harmonograph.js's PRESET_SLOTS
NGLOBALS = 7            # Sync, Beats, Vel, NoteMs, Layers, Decay, Prob
NPRESET = 1             # Slot (Save/Load/Clear/the preset menu are hand-built, not real params)
NMOD = 2 * MOD_LANE_SIZE + 2   # RotStep x8 + RotSteps, WeightStep x8 + WeightSteps

ANN_RUN = 'Run: start / stop the internal clock.'
ANN_PERIOD = 'Period (ms): loop length when Sync is off. When Sync is on the period is beats x host tempo instead.'
ANN_OPEN = 'Open the harmonograph window (floating, outside the rack).'
ANN_SYNC = ('Sync tempo: lock the loop to the Live transport -- period = Beats x host tempo, and '
            'the device only plays while Live is playing.')
ANN_BEATS = 'Beats / period: loop length in beats of the host tempo (Sync on).'
ANN_VEL = 'Velocity of every onset. Onsets where several polygons coincide get a small bump on top.'
ANN_NOTE = 'Note length in ms.'
ANN_LAYERS = 'How many polygon layers are active (1-8).'
ANN_SIDES = 'Sides (K): how many evenly-spaced onsets this layer contributes -- a K-gon on the loop.'
ANN_ROT = ('Rotation in turns (0-1): spin this layer around the loop. It never changes the count '
           'or spacing, only where the set sits vs the pulse and the other layers. Fractional = '
           'off-grid, still perfectly balanced.')
ANN_WT = 'Weight: this layer\'s swing size in the DRAWING (pendulum amplitude). It does not change the rhythm.'
ANN_PITCH = 'Pitch this layer\'s onsets play.'
ANN_AXIS = 'Which axis this layer\'s pendulum drives in the drawing: X, Y, both, or a rotary (circular) term.'
ANN_PROB_G = 'Overall density: an extra probability gate applied on top of every layer\'s own Prob.'
ANN_LAYER_PROB = 'This layer\'s onsets each have this %% chance to sound -- rolled independently, every cycle.'
ANN_ROTDEPTH = 'How hard the shared quantized Rot modulator pushes this layer\'s rotation. 0 = no effect.'
ANN_WEIGHTDEPTH = 'How hard the shared quantized Weight modulator pushes this layer\'s weight. 0 = no effect.'
ANN_ROTSTEP = 'One quantized step (0-7) of the shared Rot modulator lane. Advances one step every harmonograph cycle.'
ANN_WEIGHTSTEP = 'One quantized step (0-7) of the shared Weight modulator lane. Advances one step every harmonograph cycle.'
ANN_ROTSTEPS_N = 'How many of the 8 Rot modulator steps loop (2-8).'
ANN_WEIGHTSTEPS_N = 'How many of the 8 Weight modulator steps loop (2-8).'
ANN_SLOT = ('Which of the %d in-device pattern slots Save/Load/Clear act on. Independent of Live\'s '
            'own device presets -- these slots live in harmonograph_presets.txt next to the .amxd.' % PRESET_SLOTS)
ANN_PRESET_BTN = {
    'storepreset': 'Save every layer/mod/probability control into the current Slot (see Slot).',
    'recallpreset': 'Load the current Slot back into every layer/mod/probability control.',
    'clearpreset': 'Empty the current Slot.',
}


# --- parameter attribute blocks -------------------------------------------------------------

def tog_vo(longname, shortname, initial):
    return {'parameter_longname': longname, 'parameter_shortname': shortname,
            'parameter_type': 2, 'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
            'parameter_modmode': 0, 'parameter_initial_enable': 1, 'parameter_initial': [initial]}


def menu_vo(longname, shortname, items, initial):
    return {'parameter_longname': longname, 'parameter_shortname': shortname,
            'parameter_type': 2, 'parameter_enum': list(items), 'parameter_range': list(items),
            'parameter_mmax': len(items) - 1, 'parameter_modmode': 0,
            'parameter_initial_enable': 1, 'parameter_initial': [initial]}


def nb_vo(longname, shortname, mn, mx, initial, unitstyle=0):
    return {'parameter_longname': longname, 'parameter_shortname': shortname,
            'parameter_type': 0, 'parameter_mmin': float(mn), 'parameter_mmax': float(mx),
            'parameter_modmode': 3, 'parameter_unitstyle': unitstyle,
            'parameter_initial_enable': 1, 'parameter_initial': [float(initial)]}


# --- the control table for the subpatcher ---------------------------------------------------
# (innerid, longname, shortname, kind, prepend, valueof)  kind in num|toggle|menu
def control_table():
    ctl = []
    nid = [200]

    def newid():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def add(longname, shortname, kind, prepend, vo):
        ctl.append((newid(), longname, shortname, kind, prepend, vo))

    add('SyncTempo', 'Sync', 'toggle', 'setsync', tog_vo('SyncTempo', 'Sync', 0))
    add('BeatsPerPeriod', 'Beats', 'num', 'setbeats', nb_vo('BeatsPerPeriod', 'Beats', 0.25, 64, 4, 1))
    add('Velocity', 'Vel', 'num', 'setvel', nb_vo('Velocity', 'Vel', 1, 127, 100))
    add('NoteMs', 'Note ms', 'num', 'setdur', nb_vo('NoteMs', 'Note ms', 1, 5000, 120))
    add('Layers', 'Layers', 'num', 'setnumlayers', nb_vo('Layers', 'Layers', 1, NLAYERS, 2))
    add('Decay', 'Decay', 'num', 'setdecay', nb_vo('Decay', 'Decay', 0, 4, 0, 1))
    add('Prob', 'Prob', 'num', 'setglobalprob', nb_vo('Prob', 'Prob', 0, 100, 100))
    # NGLOBALS = 7 -- keep in sync with build_subpatcher's slice.

    add('Slot', 'Slot', 'num', 'setpresetslot', nb_vo('Slot', 'Slot', 1, PRESET_SLOTS, 1))
    # NPRESET = 1 -- keep in sync with build_subpatcher's slice.

    # Shared quantized modulator lanes (MiniSteps-style): one Rot lane, one Weight lane, each an
    # 8-slot step array (fixed size -- Live params are fixed slots) plus a Steps count (2-8) that
    # says how many of the 8 are actually looped over. Depth into each lane is a PER-LAYER knob,
    # added below with the rest of that layer's fields.
    for k in range(MOD_LANE_SIZE):
        add('RotStep%d' % k, 'RS%d' % k, 'num', 'setrotstep %d' % k,
            nb_vo('RotStep%d' % k, 'RS%d' % k, 0, MOD_LEVELS - 1, 4))
    add('RotSteps', 'RotStN', 'num', 'setrotsteps', nb_vo('RotSteps', 'RotStN', 2, MOD_LANE_SIZE, MOD_LANE_SIZE))
    for k in range(MOD_LANE_SIZE):
        add('WeightStep%d' % k, 'WS%d' % k, 'num', 'setweightstep %d' % k,
            nb_vo('WeightStep%d' % k, 'WS%d' % k, 0, MOD_LEVELS - 1, 4))
    add('WeightSteps', 'WtStN', 'num', 'setweightsteps', nb_vo('WeightSteps', 'WtStN', 2, MOD_LANE_SIZE, MOD_LANE_SIZE))
    # NMOD = 2*MOD_LANE_SIZE + 2 = 18 -- keep in sync with build_subpatcher's slice.

    for i in range(NLAYERS):
        n = i + 1
        add('L%d Sides' % n, 'L%d K' % n, 'num', 'setlayerk %d' % i,
            nb_vo('L%d Sides' % n, 'L%d K' % n, 2, 12, KDEF[i]))
        add('L%d Rot' % n, 'L%d Rot' % n, 'num', 'setlayerrot %d' % i,
            nb_vo('L%d Rot' % n, 'L%d Rot' % n, 0, 1, 0, 1))
        add('L%d Weight' % n, 'L%d Wt' % n, 'num', 'setlayerweight %d' % i,
            nb_vo('L%d Weight' % n, 'L%d Wt' % n, 0, 2, 1, 1))
        add('L%d Pitch' % n, 'L%d Pch' % n, 'num', 'setlayerpitch %d' % i,
            nb_vo('L%d Pitch' % n, 'L%d Pch' % n, 0, 127, PDEF[i]))
        add('L%d Axis' % n, 'L%d Ax' % n, 'menu', 'setlayeraxis %d' % i,
            menu_vo('L%d Axis' % n, 'L%d Ax' % n, AXIS_ITEMS, [0, 1, 2, 0, 1, 2, 0, 1][i]))
        add('L%d Prob' % n, 'L%d Prob' % n, 'num', 'setlayerprob %d' % i,
            nb_vo('L%d Prob' % n, 'L%d Prob' % n, 0, 100, 100))
        add('L%d RotDepth' % n, 'L%d RotDp' % n, 'num', 'setlayerrotdepth %d' % i,
            nb_vo('L%d RotDepth' % n, 'L%d RotDp' % n, 0, 100, 0))
        add('L%d WeightDepth' % n, 'L%d WtDp' % n, 'num', 'setlayerweightdepth %d' % i,
            nb_vo('L%d WeightDepth' % n, 'L%d WtDp' % n, 0, 100, 0))
    return ctl


ANN_DECAY = ('Decay: pendulum damping (drawing only). 0 = no damping; higher = the pen spirals in '
             'toward the centre over the loop.')
ANN = {
    'SyncTempo': ANN_SYNC, 'BeatsPerPeriod': ANN_BEATS, 'Velocity': ANN_VEL,
    'NoteMs': ANN_NOTE, 'Layers': ANN_LAYERS, 'Decay': ANN_DECAY, 'Prob': ANN_PROB_G,
    'RotSteps': ANN_ROTSTEPS_N, 'WeightSteps': ANN_WEIGHTSTEPS_N, 'Slot': ANN_SLOT,
}
for _k in range(MOD_LANE_SIZE):
    ANN['RotStep%d' % _k] = ANN_ROTSTEP
    ANN['WeightStep%d' % _k] = ANN_WEIGHTSTEP
for _i in range(NLAYERS):
    _n = _i + 1
    ANN['L%d Sides' % _n] = ANN_SIDES
    ANN['L%d Rot' % _n] = ANN_ROT
    ANN['L%d Weight' % _n] = ANN_WT
    ANN['L%d Pitch' % _n] = ANN_PITCH
    ANN['L%d Axis' % _n] = ANN_AXIS
    ANN['L%d Prob' % _n] = ANN_LAYER_PROB
    ANN['L%d RotDepth' % _n] = ANN_ROTDEPTH
    ANN['L%d WeightDepth' % _n] = ANN_WEIGHTDEPTH


# --- the floating window -------------------------------------------------------------------

def build_subpatcher(appversion, ctl):
    boxes, lines = [], []
    HID = {'hidden': 1}

    def box(**kw):
        boxes.append({'box': kw})

    def line(src, si, dst, di, hide=True):
        pl = {'source': [src, si], 'destination': [dst, di]}
        if hide:
            pl['hidden'] = 1
        lines.append({'patchline': pl})

    # data in -> jsui. inlet 0 = the tagged stream (curve/marks/hit/cyc/lay), straight to the jsui
    # exactly like Step 3-7 -- no filtering needed here anymore (see inlet 1 below).
    box(id='obj-1', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
        patching_rect=[20.0, 8.0, 30.0, 30.0], **HID)
    box(id='obj-2', maxclass='outlet', numinlets=1, numoutlets=0,
        patching_rect=[20.0, 640.0, 30.0, 30.0], **HID)
    JSUI_Y = 292.0   # below the preset toolbar (y44) + mod lanes (y78/104) + 8-row layer grid (y130..274)
    JSUI_H = 396.0
    box(id='obj-3', maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=0, filename=UI_JS,
        patching_rect=[8.0, JSUI_Y, 648.0, JSUI_H],
        presentation=1, presentation_rect=[8.0, JSUI_Y, 648.0, JSUI_H], varname='hgw_ui')
    line('obj-1', 0, 'obj-3', 0)
    # inlet 1 (Step 8 hardening): the dedicated preset-menu channel from hg_engine's outlet 1,
    # straight to the umenu below -- no tag, no route, no prepend (see harmonograph.js's
    # `outlets = 2` note for why the old tagged-and-filtered version was replaced).
    box(id='obj-5', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
        patching_rect=[60.0, 8.0, 30.0, 30.0], **HID)
    # inlet 2 (name-sync bugfix): the dedicated name-box channel from hg_engine's outlet 2,
    # straight to the name textedit below (wired near its definition). Must sit to the right of
    # obj-1/obj-5 -- Max numbers a subpatcher's inlets by the x position of its [inlet] objects,
    # not creation order.
    box(id='obj-6', maxclass='inlet', numinlets=0, numoutlets=1, outlettype=[''],
        patching_rect=[100.0, 8.0, 30.0, 30.0], **HID)

    # --- controls -----------------------------------------------------------------------
    # globals across the top; then the preset toolbar; then the modulator lanes; then the layer grid.
    GX = [8.0, 96.0, 184.0, 272.0, 360.0, 448.0, 536.0]
    globals_ = ctl[:NGLOBALS]
    presetctl = ctl[NGLOBALS:NGLOBALS + NPRESET]
    modctl = ctl[NGLOBALS + NPRESET:NGLOBALS + NPRESET + NMOD]
    layers = ctl[NGLOBALS + NPRESET + NMOD:]

    def place_label(x, y, w, text):
        box(id='obj-l%d' % (len(boxes)), maxclass='comment', numinlets=1, numoutlets=0,
            patching_rect=[x, y, w, 18.0], presentation=1,
            presentation_rect=[x, y, w, 16.0], fontsize=9.0, text=text)

    def place_ctrl(cid, kind, vo, ann, px, py, w=48.0):
        common = dict(id=cid, parameter_enable=1, varname='c_' + cid.replace('-', '_'),
                      presentation=1, annotation=ann,
                      saved_attribute_attributes={'valueof': vo})
        if kind == 'toggle':
            box(maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
                patching_rect=[px, py, 15.0, 15.0], presentation_rect=[px, py, 15.0, 15.0],
                **common)
        elif kind == 'menu':
            box(maxclass='live.menu', numinlets=1, numoutlets=3, outlettype=['', '', ''],
                patching_rect=[px, py, 62.0, 15.0], presentation_rect=[px, py, 62.0, 15.0],
                **common)
        else:
            box(maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
                patching_rect=[px, py, w, 15.0], presentation_rect=[px, py, w, 15.0], **common)

    # global row
    for k, (cid, longn, shortn, kind, prep, vo) in enumerate(globals_):
        gx = GX[k]
        place_label(gx, 8.0, 76.0, shortn)
        place_ctrl(cid, kind, vo, ANN[longn], gx, 24.0)

    # preset toolbar (Step 8): Slot, Save/Load/Clear, and a name-aware picker all in one row, so
    # "manage patterns" reads as one place instead of Slot living in the global row while
    # Save/Load/Clear sat elsewhere. Save/Load/Clear are momentary, so (like Step 7) they're
    # hand-built rather than run through control_table()'s value-restoring loadbang loop -- a
    # click has no value to restore. PRESET_SKIP in harmonograph.js keeps Slot out of every slot.
    PRESET_Y = 44.0
    slot_cid, slot_longn, slot_shortn, slot_kind, slot_prep, slot_vo = presetctl[0]
    place_label(8.0, PRESET_Y - 10.0, 30.0, 'Slot')
    place_ctrl(slot_cid, slot_kind, slot_vo, ANN[slot_longn], 8.0, PRESET_Y, w=30.0)

    def preset_button(label, msg, x, y, w=48.0):
        bid = 'pb_' + msg
        # mode=0 (momentary): Save/Load/Clear fire once and release. mode=1 (the Step 7/8
        # default) is a latching toggle -- it stayed visually pressed after every click, which
        # is the "los botones no se desclickean" report.
        box(id=bid, maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
            mode=0, text=label,
            patching_rect=[x, y, w, 18.0], presentation=1, presentation_rect=[x, y, w, 15.0],
            varname='c_' + bid, annotation=ANN_PRESET_BTN[msg])
        mid = 'pbm_' + msg
        box(id=mid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
            patching_rect=[x, y + 24.0, w, 22.0], text=msg, **HID)
        line(bid, 0, mid, 0)
        line(mid, 0, 'obj-2', 0)
        return bid

    save_bid = preset_button('Save', 'storepreset', 42.0, PRESET_Y)
    preset_button('Load', 'recallpreset', 94.0, PRESET_Y)
    preset_button('Clear', 'clearpreset', 146.0, PRESET_Y)

    # the preset picker: a plain umenu (not live.menu -- its item list has to be rebuildable at
    # runtime as slots are saved/cleared, and live.menu's enum is meant to be fixed Live-parameter
    # metadata). harmonograph.js drives it, via the dedicated inlet 1 (obj-5 above, no tag, no
    # routing), with "clear" / "append <label>" / "set <index>" -- messages a stock umenu already
    # understands natively. Picking an item feeds back into the Slot numbox (single source of
    # truth, same idiom as the drag ring) rather than recalling directly -- browsing names should
    # not by itself overwrite the current pattern.
    box(id='obj-presetmenu', maxclass='umenu', numinlets=1, numoutlets=3,
        outlettype=['int', '', ''], patching_rect=[202.0, PRESET_Y, 226.0, 18.0],
        presentation=1, presentation_rect=[202.0, PRESET_Y, 226.0, 18.0],
        varname='hgw_presetmenu',
        annotation='Every pattern slot by name -- pick one to move Slot there (does not itself load).')
    line('obj-5', 0, 'obj-presetmenu', 0)
    box(id='obj-presetmenu-inc', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['int'],
        patching_rect=[202.0, PRESET_Y + 24.0, 40.0, 22.0], text='+ 1', **HID)
    line('obj-presetmenu', 0, 'obj-presetmenu-inc', 0)
    line('obj-presetmenu-inc', 0, slot_cid, 0)

    # name entry: types into the CURRENT slot (setpresetname always acts on presetSlot, same
    # "act on the current slot" default as Save/Load/Clear). Two bugs fixed together here:
    # (1) a bare textedit with no `text` defaults its buffer to the literal word "text", which
    # was then coming out as a preset's name -- explicit text='' starts it genuinely empty, and
    # since '' is falsy, presetLabel()'s (vals.__name || '(vacio)') falls back correctly even if
    # it round-trips through setpresetname untouched. (2) keymode=0 (the default) means Enter
    # does nothing -- only Tab (tabmode's default) submitted, contradicting the annotation below;
    # keymode=1 makes Enter/Return actually submit, as documented.
    box(id='obj-nameedit', maxclass='textedit', numinlets=1, numoutlets=1, outlettype=[''],
        text='', keymode=1,
        patching_rect=[436.0, PRESET_Y, 180.0, 18.0], presentation=1,
        presentation_rect=[436.0, PRESET_Y, 180.0, 18.0], varname='hgw_nameedit',
        annotation='Type a name (Enter/Return also works, but Save captures it either way).')
    box(id='obj-nameedit-prep', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[436.0, PRESET_Y + 24.0, 150.0, 22.0], text='prepend setpresetname', **HID)
    line('obj-nameedit', 0, 'obj-nameedit-prep', 0)
    line('obj-nameedit-prep', 0, 'obj-2', 0)
    # Real bug found live 2026-09-04: typing a name and clicking Save WITHOUT pressing Enter
    # first left the old name in place -- storepreset() only preserves whatever __name is
    # already in presetBank, and nothing had told the textedit to submit its (uncommitted)
    # buffer. `textedit`'s default bangmode (0, "Bang Outputs Typed Text") means a bare bang
    # outputs whatever is CURRENTLY typed, submitted or not -- so banging it from the same
    # click that fires Save makes "whatever's in the box right now" always become the name,
    # with no dependency on the user remembering to press Enter first.
    line(save_bid, 0, 'obj-nameedit', 0)
    # Companion fix: with Save now capturing whatever sits in the box, a name left over from a
    # PREVIOUS slot (never edited to match the new one) would otherwise get silently stamped
    # onto whichever slot is current when Save is next clicked. inlet 2 -> `set <name>` (no
    # output) keeps the box showing the truth for whichever slot is selected.
    line('obj-6', 0, 'obj-nameedit', 0)

    # shared quantized modulator lanes (MiniSteps-style): 8 step boxes + a Steps count, one row
    # each for Rot and Weight. modctl order: RotStep0..7, RotSteps, WeightStep0..7, WeightSteps.
    rot_lane = modctl[:MOD_LANE_SIZE]
    rot_steps_ctl = modctl[MOD_LANE_SIZE]
    weight_lane = modctl[MOD_LANE_SIZE + 1:2 * MOD_LANE_SIZE + 1]
    weight_steps_ctl = modctl[2 * MOD_LANE_SIZE + 1]

    def place_lane(label, lane, steps_ctl, y):
        place_label(8.0, y, 54.0, label)
        sx = 64.0
        for cid, longn, shortn, kind, prep, vo in lane:
            place_ctrl(cid, kind, vo, ANN[longn], sx, y, w=22.0)
            sx += 26.0
        cid, longn, shortn, kind, prep, vo = steps_ctl
        place_label(sx + 4.0, y - 10.0, 40.0, 'Steps')
        place_ctrl(cid, kind, vo, ANN[longn], sx + 4.0, y, w=28.0)

    place_lane('RotMod', rot_lane, rot_steps_ctl, 78.0)
    place_lane('WtMod', weight_lane, weight_steps_ctl, 104.0)

    # layer grid header
    COLX = [8.0, 34.0, 86.0, 138.0, 190.0, 242.0, 306.0, 350.0, 394.0]
    FIELDS = ['Sides', 'Rot', 'Weight', 'Pitch', 'Axis', 'Prob', 'RotDp', 'WtDp']
    GRID_Y0 = 130.0
    for cx, txt in zip(COLX[1:], FIELDS):
        place_label(cx, GRID_Y0 - 14.0, 56.0, txt)
    for i in range(NLAYERS):
        ry = GRID_Y0 + i * 18.0
        place_label(COLX[0], ry, 22.0, 'L%d' % (i + 1))
        row = layers[i * len(FIELDS):(i + 1) * len(FIELDS)]
        for c, (cid, longn, shortn, kind, prep, vo) in enumerate(row):
            place_ctrl(cid, kind, vo, ANN[longn], COLX[c + 1], ry, w=44.0)
    GRID_BOTTOM = GRID_Y0 + NLAYERS * 18.0

    # --- hidden plumbing: each control -> prepend -> outlet ----------------------------
    py = 700.0
    for cid, longn, shortn, kind, prep, vo in ctl:
        pid = 'p_' + cid
        box(id=pid, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
            patching_rect=[8.0, py, 150.0, 22.0], text='prepend ' + prep, **HID)
        line(cid, 0, pid, 0)
        line(pid, 0, 'obj-2', 0)
        py += 26.0

    # --- loadbang: re-emit stored values on load -------------------------------------
    box(id='obj-9', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[200.0, 700.0, 62.0, 22.0], text='loadbang', **HID)
    ov_x = 280.0
    for cid, longn, shortn, kind, prep, vo in ctl:
        if kind == 'num':
            line('obj-9', 0, cid, 0)                    # bang re-emits a live.numbox
        else:
            oid = 'ov_' + cid
            box(id=oid, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
                patching_rect=[ov_x, 700.0, 74.0, 22.0], text='outputvalue', **HID)
            line('obj-9', 0, oid, 0)
            line(oid, 0, cid, 0)
            ov_x += 80.0

    # --- drag ring: jsui "drag <layer> <rot> <wt>" -> that layer's Rot / Weight numboxes ------
    box(id='obj-7', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
        patching_rect=[8.0, 660.0, 90.0, 22.0], text='route drag', **HID)
    box(id='obj-8', maxclass='newobj', numinlets=1, numoutlets=NLAYERS + 1,
        outlettype=[''] * (NLAYERS + 1), patching_rect=[8.0, 668.0, 200.0, 22.0],
        text='route ' + ' '.join(str(i) for i in range(NLAYERS)), **HID)
    line('obj-3', 0, 'obj-7', 0)
    line('obj-7', 0, 'obj-8', 0)
    for i in range(NLAYERS):
        rot_cid = layers[i * len(FIELDS) + 1][0]   # ctl layer block: [Sides, Rot, Weight, Pitch, Axis, Prob, RotDp, WtDp]
        wt_cid = layers[i * len(FIELDS) + 2][0]
        uid = 'u_%d' % i
        box(id=uid, maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['float', 'float'],
            patching_rect=[8.0 + i * 62.0, 676.0, 70.0, 22.0], text='unpack 0. 0.', **HID)
        line('obj-8', i, uid, 0)
        line(uid, 0, rot_cid, 0)               # rot -> L#Rot numbox (sets + fires -> engine + display)
        line(uid, 1, wt_cid, 0)                # weight -> L#Weight numbox

    local_params = {cid: [longn, shortn, i] for i, (cid, longn, shortn, _k, _p, _vo) in enumerate(ctl)}
    local_params['inherited_shortname'] = 1

    win_h = JSUI_Y + JSUI_H + 20.0
    return {
        'fileversion': 1, 'appversion': appversion, 'classnamespace': 'box',
        'rect': [120.0, 100.0, 672.0, win_h], 'openrect': [0.0, 0.0, 672.0, win_h],
        'openinpresentation': 1, 'default_fontsize': 10.0, 'default_fontname': 'Arial',
        'gridsize': [8.0, 8.0], 'toolbarvisible': 0, 'enablehscroll': 0, 'enablevscroll': 0,
        'title': 'harmonograph',
        'boxes': boxes, 'lines': lines, 'parameters': local_params,
        'dependency_cache': [{'name': UI_JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1}],
        'autosave': 0,
    }


# --- the device (top patcher) -----------------------------------------------------------

def build_top(sub):
    boxes, lines = [], []

    def box(**kw):
        boxes.append({'box': kw})

    def line(src, si, dst, di):
        lines.append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    # engine. Outlet 1 (Step 8 hardening) is a dedicated, untagged channel for the preset-menu
    # UI protocol (clear/append/set) straight to the umenu -- see harmonograph.js's `outlets = 2`
    # note. It replaced a "presetmenu"-tagged message sharing outlet 0, round-tripped through
    # route/prepend/route to reach the umenu without also hitting the jsui; that round trip was
    # empirically observed, live, to occasionally mangle the tag into a stray small integer
    # (confirmed with a print object sniffing the raw signal -- a freshly-built identical prepend
    # object never reproduced it, only the one wired into the real chain did, repeatedly, even
    # after being individually recreated in place). A dedicated outlet/inlet pair needs no tag, no
    # route, no prepend: nothing left in the path that could mangle it.
    # outlet 2 (bugfix, same day as the dedicated outlet 1 above): pushes the CURRENT slot's
    # stored name into the name textedit on every slot change (setpresetslot/loadpresets/
    # clearing the current slot) via `set <name>` (textedit's silent-set method). Needed once
    # Save started auto-capturing whatever's in the name box (see obj-nameedit below) -- without
    # this, switching slots could leave a PREVIOUS slot's typed name sitting in the box, and the
    # next Save would silently stamp it onto the wrong slot.
    box(id='obj-10', maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['', '', ''],
        patching_rect=[40.0, 300.0, 150.0, 22.0], text='js ' + JS, varname='hg_engine',
        saved_object_attributes={'filename': JS, 'parameter_enable': 0})

    # clock
    box(id='obj-11', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=['bang'],
        patching_rect=[40.0, 240.0, 74.0, 22.0], text='metro 2000', varname='hg_metro')
    line('obj-11', 0, 'obj-10', 0)

    # "lay" joined the tag list here -- it was ALWAYS emitted by the engine's emitCurve() (per-
    # layer rot/weight/pitch, feeding the jsui's drag-ring handles) but was never in this selector
    # list, so it silently fell into route's unwired reject outlet and the drag ring never
    # received live layer data. ("presetmenu" is gone from this route entirely now -- it moved to
    # its own dedicated outlet 1 / inlet 1, see hg_engine above.)
    box(id='obj-12', maxclass='newobj', numinlets=1, numoutlets=8,
        outlettype=['', '', '', '', '', '', '', ''],
        patching_rect=[40.0, 350.0, 260.0, 22.0], text='route n ms curve marks hit cyc lay',
        varname='hg_route')
    line('obj-10', 0, 'obj-12', 0)

    box(id='obj-13', maxclass='newobj', numinlets=4, numoutlets=3,
        outlettype=['float', 'float', 'float'],
        patching_rect=[40.0, 400.0, 120.0, 22.0], text='makenote 100 200 1', varname='hg_makenote')
    box(id='obj-14', maxclass='newobj', numinlets=3, numoutlets=0,
        patching_rect=[40.0, 440.0, 47.0, 22.0], text='noteout', varname='hg_noteout')
    line('obj-12', 0, 'obj-13', 0)
    line('obj-12', 1, 'obj-11', 1)
    line('obj-13', 0, 'obj-14', 0)
    line('obj-13', 1, 'obj-14', 1)
    line('obj-13', 2, 'obj-14', 2)

    # jsui feed: re-tag (route stripped the selector) then into the window
    box(id='obj-16', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[260.0, 400.0, 90.0, 22.0], text='prepend curve', varname='hg_tag_curve')
    box(id='obj-17', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[360.0, 400.0, 90.0, 22.0], text='prepend marks', varname='hg_tag_marks')
    box(id='obj-18', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[460.0, 400.0, 80.0, 22.0], text='prepend hit', varname='hg_tag_hit')
    box(id='obj-19', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[550.0, 400.0, 80.0, 22.0], text='prepend cyc', varname='hg_tag_cyc')
    box(id='obj-27', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[650.0, 400.0, 80.0, 22.0], text='prepend lay', varname='hg_tag_lay')
    line('obj-12', 2, 'obj-16', 0)
    line('obj-12', 3, 'obj-17', 0)
    line('obj-12', 4, 'obj-18', 0)
    line('obj-12', 5, 'obj-19', 0)
    line('obj-12', 6, 'obj-27', 0)

    # the window subpatcher. 3 inlets now: 0 = the tagged stream (curve/marks/hit/cyc/lay), same
    # as always; 1 = the dedicated preset-menu channel straight from hg_engine's outlet 1, no tag,
    # no route, wired directly to the umenu inside (see build_subpatcher); 2 = the dedicated
    # name-sync channel from outlet 2, wired straight to the name textedit.
    box(id=SUB, maxclass='newobj', numinlets=3, numoutlets=1, outlettype=[''],
        patching_rect=[300.0, 300.0, 120.0, 22.0], text='p hg_window', varname='hg_window',
        patcher=sub)
    line('obj-16', 0, SUB, 0)
    line('obj-17', 0, SUB, 0)
    line('obj-18', 0, SUB, 0)
    line('obj-19', 0, SUB, 0)
    line('obj-27', 0, SUB, 0)
    line('obj-10', 1, SUB, 1)               # hg_engine outlet 1 -> the window's dedicated 2nd inlet
    line('obj-10', 2, SUB, 2)               # hg_engine outlet 2 -> the window's dedicated 3rd inlet
    line(SUB, 0, 'obj-10', 0)               # every windowed control -> engine

    # tempo / transport observers (transcribed from forteseqwf.amxd)
    box(id='obj-20', maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['', '', ''],
        patching_rect=[420.0, 200.0, 110.0, 22.0], text='live.path live_set', varname='hg_livepath')
    box(id='obj-21', maxclass='newobj', numinlets=2, numoutlets=2, outlettype=['', ''],
        patching_rect=[420.0, 240.0, 120.0, 22.0], text='live.observer tempo', varname='hg_tempoobs')
    box(id='obj-22', maxclass='newobj', numinlets=2, numoutlets=2, outlettype=['', ''],
        patching_rect=[560.0, 240.0, 130.0, 22.0], text='live.observer is_playing', varname='hg_playobs')
    box(id='obj-23', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[420.0, 160.0, 62.0, 22.0], text='loadbang', varname='hg_tempoinit')
    box(id='obj-24', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['bang', 'bang'],
        patching_rect=[420.0, 185.0, 32.0, 22.0], text='t b b', varname='hg_tempoinit_t')
    box(id='obj-25', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[420.0, 280.0, 110.0, 22.0], text='prepend settempo', varname='hg_tempoprep')
    box(id='obj-26', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[560.0, 280.0, 120.0, 22.0], text='prepend settransport', varname='hg_transprep')
    line('obj-23', 0, 'obj-24', 0)
    line('obj-24', 1, 'obj-20', 0)
    line('obj-24', 0, 'obj-21', 0)
    line('obj-24', 0, 'obj-22', 0)
    line('obj-20', 0, 'obj-21', 1)
    line('obj-20', 0, 'obj-22', 1)
    line('obj-21', 0, 'obj-25', 0)
    line('obj-22', 0, 'obj-26', 0)
    line('obj-25', 0, 'obj-10', 0)
    line('obj-26', 0, 'obj-10', 0)

    # panel: Run, Period, OPEN button
    box(id='obj-30', maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=1, patching_rect=[40.0, 40.0, 15.0, 15.0], presentation=1,
        presentation_rect=[8.0, 8.0, 15.0, 15.0], varname='hg_run', annotation=ANN_RUN,
        saved_attribute_attributes={'valueof': tog_vo('Run', 'Run', 0)})
    box(id='obj-31', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[60.0, 40.0, 40.0, 18.0], presentation=1,
        presentation_rect=[28.0, 8.0, 40.0, 16.0], text='Run', varname='hg_run_lbl')
    box(id='obj-32', maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
        parameter_enable=1, patching_rect=[40.0, 70.0, 46.0, 15.0], presentation=1,
        presentation_rect=[8.0, 30.0, 46.0, 15.0], varname='hg_period', annotation=ANN_PERIOD,
        saved_attribute_attributes={'valueof': nb_vo('Period', 'Per ms', 50, 60000, 2000)})
    box(id='obj-33', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[92.0, 70.0, 80.0, 18.0], presentation=1,
        presentation_rect=[58.0, 30.0, 80.0, 16.0], text='Period (ms)', varname='hg_period_lbl')
    box(id='obj-34', maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=1, mode=1, text='OPEN', texton='OPEN',
        patching_rect=[40.0, 100.0, 90.0, 24.0], presentation=1,
        presentation_rect=[8.0, 52.0, 100.0, 22.0], varname='hg_open_btn', annotation=ANN_OPEN,
        saved_attribute_attributes={'valueof': {
            'parameter_longname': 'Open', 'parameter_shortname': 'Open', 'parameter_type': 2,
            'parameter_enum': ['off', 'on'], 'parameter_mmax': 1, 'parameter_modmode': 0,
            'parameter_initial_enable': 1, 'parameter_initial': [0]}})
    box(id='obj-35', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[40.0, 140.0, 48.0, 22.0], text='open', varname='hg_msg_open')
    box(id='obj-36', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[40.0, 170.0, 56.0, 22.0], text='pcontrol', varname='hg_pcontrol')
    box(id='obj-37', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['bang', 'bang'],
        patching_rect=[160.0, 40.0, 110.0, 22.0], text='live.thisdevice', varname='hg_thisdev')
    box(id='obj-38', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[200.0, 100.0, 130.0, 22.0], text='prepend setrun', varname='hg_run_prep')
    box(id='obj-39', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[200.0, 130.0, 130.0, 22.0], text='prepend setperiod', varname='hg_period_prep')
    box(id='obj-40', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[560.0, 40.0, 62.0, 22.0], text='loadbang', varname='hg_panel_init')
    box(id='obj-41', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[560.0, 70.0, 74.0, 22.0], text='outputvalue', varname='hg_run_ov')

    line('obj-30', 0, 'obj-11', 0)          # Run -> metro
    line('obj-30', 0, 'obj-38', 0)          # Run -> prepend setrun -> engine
    line('obj-38', 0, 'obj-10', 0)
    line('obj-32', 0, 'obj-11', 1)          # Period -> metro inlet 1
    line('obj-32', 0, 'obj-39', 0)          # Period -> prepend setperiod -> engine
    line('obj-39', 0, 'obj-10', 0)
    line('obj-34', 0, 'obj-35', 0)          # OPEN button -> open
    line('obj-37', 0, 'obj-35', 0)          # live.thisdevice -> open (on load)
    line('obj-35', 0, 'obj-36', 0)
    line('obj-36', 0, SUB, 0)               # pcontrol -> the subpatcher (opens its window)
    line('obj-40', 0, 'obj-41', 0)
    line('obj-41', 0, 'obj-30', 0)          # loadbang -> outputvalue -> Run toggle
    line('obj-40', 0, 'obj-32', 0)          # loadbang -> bang Period (safe on live.numbox)

    return boxes, lines


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(TEMPLATE)
    P = doc['patcher']
    appversion = P['appversion']

    ctl = control_table()
    sub = build_subpatcher(appversion, ctl)
    boxes, lines = build_top(sub)
    P['boxes'] = boxes
    P['lines'] = lines

    params = {
        'obj-30': ['Run', 'Run', 0],
        'obj-32': ['Period', 'Per ms', 1],
        'obj-34': ['Open', 'Open', 2],
    }
    for i, (cid, longn, shortn, _k, _p, _vo) in enumerate(ctl):
        params['%s::%s' % (SUB, cid)] = [longn, shortn, i + 3]

    def bank(name, names):
        return {'name': name, 'parameters': list(names) + ['-'] * (8 - len(names))}

    def col(field):
        return ['L%d %s' % (n + 1, field) for n in range(NLAYERS)]

    def steps(prefix, n):
        return ['%s%d' % (prefix, k) for k in range(n)]

    banks_list = [
        bank('Clock', ['Run', 'Period', 'SyncTempo', 'BeatsPerPeriod', 'Velocity', 'NoteMs', 'Layers', 'Slot']),
        bank('Decay/Prob', ['Decay', 'Prob']),
        bank('ModCount', ['RotSteps', 'WeightSteps']),
        bank('Sides', col('Sides')),
        bank('Rotation', col('Rot')),
        bank('Weight', col('Weight')),
        bank('Pitch', col('Pitch')),
        bank('Axis', col('Axis')),
        bank('Prob', col('Prob')),
        bank('RotDepth', col('RotDepth')),
        bank('WeightDepth', col('WeightDepth')),
        bank('RotMod', steps('RotStep', MOD_LANE_SIZE)),
        bank('WeightMod', steps('WeightStep', MOD_LANE_SIZE)),
    ]
    banks = {}
    for bi, b in enumerate(banks_list):
        b['index'] = bi
        banks[str(bi)] = b
    params['parameterbanks'] = banks
    params['inherited_shortname'] = 1
    P['parameters'] = params

    P['dependency_cache'] = [
        {'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
        {'name': UI_JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1},
    ]
    P['rect'] = [140.0, 140.0, 720.0, 520.0]
    P['openinpresentation'] = 1

    # --- self-checks ------------------------------------------------------------------
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
                    errors.append('%s: %s line endpoint %r unknown' % (where, lab, end))
        for b in p['boxes']:
            if b['box'].get('patcher'):
                check_patcher(b['box']['patcher'], where + '::' + b['box']['id'], errors)

    errors = []
    check_patcher(P, 'root', errors)
    subbox = [b['box'] for b in P['boxes'] if b['box']['id'] == SUB][0]
    top_names = {v[0] for k, v in params.items() if k not in ('parameterbanks', 'inherited_shortname')}
    sub_local = {v[0] for k, v in subbox['patcher']['parameters'].items() if k != 'inherited_shortname'}
    for b in banks_list:
        for nm in b['parameters']:
            if nm != '-' and nm not in top_names:
                errors.append('bank %s lists unknown param %r' % (b['name'], nm))
    nested = {v[0] for k, v in params.items() if '::' in k}
    if nested != sub_local:
        errors.append('nested top params != subpatcher local params: %r' % (nested ^ sub_local))
    if errors:
        for er in errors:
            print(' -', er)
        raise SystemExit('self-checks failed')

    print('harmonograph.amxd  (floating window; 8 layers x {Sides,Rot,Weight,Pitch,Axis,Prob,RotDp,WtDp}; '
          'Decay + phosphor comet; global Prob; shared quantized RotMod/WeightMod lanes)')
    print('  top boxes  : %d   sub boxes : %d' % (len(P['boxes']), len(subbox['patcher']['boxes'])))
    print('  top lines  : %d   sub lines : %d' % (len(P['lines']), len(subbox['patcher']['lines'])))
    print('  params     : %d top + %d nested = %d' % (len(top_names) - len(nested), len(nested), len(top_names)))
    print('  banks      : %s' % ', '.join(b['name'] for b in banks_list))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    if os.path.exists(DEVICE):
        shutil.copyfile(DEVICE, DEVICE + '.before')
        print('  backup     : %s.before' % os.path.basename(DEVICE))
    shutil.copyfile(TEMPLATE, DEVICE)
    d2, s2, e2, _ = amxd.load(DEVICE)
    amxd.save(DEVICE, d2, s2, e2, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    bb = [b['box'] for b in back['boxes'] if b['box']['id'] == SUB][0]
    assert bb.get('patcher') and len(bb['patcher']['boxes']) == len(subbox['patcher']['boxes']), 'subpatcher lost on roundtrip'
    assert back['dependency_cache'][0]['name'] == JS
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/harmonograph.amxd')


main()
