"""Build forteseq/midibounce.amxd -- the MIDI Bounce device shell around midibounce.js.

    python tools/build_midibounce.py            dry run, writes nothing
    python tools/build_midibounce.py --apply    do it

There is no MCP path for this (the maxmsp server wasn't up when it was written and the
device is trivially small anyway), so the .amxd is assembled the way the other tools/*.py
scripts assemble their edits: copy a known-good device and rewrite its patcher JSON.

The template is forteseq/forteseqmidifilter.amxd -- a near-stock "Untitled" MIDI-effect
device. Copying its bytes keeps the binary AMPF/meta chunk (which is what marks the file
as a MIDI effect, amxdtype 'midf') and the whole `project` block; we only swap `boxes`,
`lines`, `parameters` and `dependency_cache`.

The patch itself:

    live.text "BOUNCE" (button) --> js inlet 0
    live.toggle "999 BPM"  --> [prepend fast]     --> js inlet 1
    live.toggle "Disable FX after" --> [prepend disablefx] --> js inlet 1
    live.numbox "Length (bars)" --> [prepend lenbars] --> js inlet 1   (0 = clip length)
    loadbang --> [outputvalue( x2 --> each toggle   (initial state -> js; `outputvalue`
                                                    and NOT a bang, which would invert it)
    loadbang --> live.numbox                        (bang is safe on live.numbox -> re-emits)
    midiin --> midiout                              (explicit MIDI pass-through)

Four parameters, registered in all three places that must agree (box valueof,
patcher.parameters, parameterbanks) -- see the amxd-parameter-registries note.

Close the device in BOTH Max and Live before running with --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'forteseq', 'forteseqmidifilter.amxd')
DEVICE = os.path.join(ROOT, 'forteseq', 'midibounce.amxd')
JS = 'midibounce.js'

# --- parameter attribute blocks -----------------------------------------------------------
BTN_ANN = ('Bounce: crea un track MIDI a la derecha, rutea su entrada del Post-FX de este '
           'track, y graba el clip seleccionado (a 999 BPM si el toggle esta activo) como '
           'notas MIDI planas en el track nuevo. Mapeable a MIDI/KEY/Push.')
FAST_ANN = ('999 BPM: con esto activo el bounce sube el tempo a 999 para capturar en ~1 s. '
            'Apagalo para grabar a tempo real y poder mover los controles de los efectos '
            'MIDI mientras graba.')
DFX_ANN = ('Disable FX after: al terminar, pone Device On en 0 en cada efecto MIDI de este '
           'track (reversible -- no borra nada). Apagado por defecto.')
LEN_ANN = ('Length (bars): 0 = usa el largo del clip seleccionado. Mayor a 0 = graba esa '
           'cantidad de compases (con el compas del set); si el clip fuente es mas corto, '
           'loopea durante la captura.')


def btn_valueof():
    return {
        'parameter_longname': 'Bounce',
        'parameter_shortname': 'Bounce',
        'parameter_type': 2,
        'parameter_enum': ['off', 'on'],
        'parameter_mmax': 1,
        'parameter_modmode': 0,
        'parameter_initial_enable': 1,
        'parameter_initial': [0],
    }


def toggle_valueof(longname, initial):
    return {
        'parameter_longname': longname,
        'parameter_shortname': longname,
        'parameter_type': 2,
        'parameter_enum': ['off', 'on'],
        'parameter_mmax': 1,
        'parameter_modmode': 0,
        'parameter_initial_enable': 1,
        'parameter_initial': [initial],
    }


def lenbars_valueof():
    return {
        'parameter_longname': 'LengthBars',
        'parameter_shortname': 'Length',
        'parameter_type': 0,
        'parameter_mmin': 0.0,
        'parameter_mmax': 64.0,
        'parameter_modmode': 3,
        'parameter_unitstyle': 0,
        'parameter_initial_enable': 1,
        'parameter_initial': [0.0],
    }


def build_boxes_lines():
    boxes = []
    lines = []

    def box(**kw):
        boxes.append({'box': kw})

    def line(src, si, dst, di):
        lines.append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    # -- MIDI pass-through --------------------------------------------------------------
    box(id='obj-1', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['int'],
        patching_rect=[24.0, 300.0, 40.0, 22.0], text='midiin', varname='mb_midiin')
    box(id='obj-2', maxclass='newobj', numinlets=1, numoutlets=0,
        patching_rect=[24.0, 350.0, 47.0, 22.0], text='midiout', varname='mb_midiout')
    line('obj-1', 0, 'obj-2', 0)

    # -- the engine ------------------------------------------------------------------
    box(id='obj-10', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 210.0, 120.0, 22.0], text='js ' + JS, varname='mb_engine',
        saved_object_attributes={'filename': JS, 'parameter_enable': 0})

    # -- the button ---------------------------------------------------------------
    box(id='obj-20', maxclass='live.text', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=1, mode=1, text='BOUNCE', texton='BOUNCE',
        patching_rect=[200.0, 20.0, 90.0, 24.0], presentation=1,
        presentation_rect=[8.0, 8.0, 96.0, 24.0], varname='mb_button', annotation=BTN_ANN,
        saved_attribute_attributes={'valueof': btn_valueof()})
    line('obj-20', 0, 'obj-10', 0)

    # -- 999 BPM toggle ----------------------------------------------------------
    box(id='obj-30', maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=1, patching_rect=[200.0, 70.0, 15.0, 15.0], presentation=1,
        presentation_rect=[92.0, 40.0, 15.0, 15.0], varname='mb_fast', annotation=FAST_ANN,
        saved_attribute_attributes={'valueof': toggle_valueof('Fast999', 1)})
    box(id='obj-31', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[240.0, 70.0, 80.0, 18.0], presentation=1,
        presentation_rect=[8.0, 40.0, 80.0, 18.0], text='999 BPM', varname='mb_fast_lbl')
    box(id='obj-32', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[200.0, 120.0, 80.0, 22.0], text='prepend fast', varname='mb_fast_prep')
    line('obj-30', 0, 'obj-32', 0)
    line('obj-32', 0, 'obj-10', 1)

    # -- Disable FX toggle -------------------------------------------------------
    box(id='obj-40', maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=1, patching_rect=[340.0, 70.0, 15.0, 15.0], presentation=1,
        presentation_rect=[120.0, 62.0, 15.0, 15.0], varname='mb_dfx', annotation=DFX_ANN,
        saved_attribute_attributes={'valueof': toggle_valueof('DisableFX', 0)})
    box(id='obj-41', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[360.0, 70.0, 110.0, 18.0], presentation=1,
        presentation_rect=[8.0, 62.0, 108.0, 18.0], text='Disable FX after',
        varname='mb_dfx_lbl')
    box(id='obj-42', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[340.0, 120.0, 100.0, 22.0], text='prepend disablefx',
        varname='mb_dfx_prep')
    line('obj-40', 0, 'obj-42', 0)
    line('obj-42', 0, 'obj-10', 1)

    # -- Length (bars) --------------------------------------------------------------
    box(id='obj-60', maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
        parameter_enable=1, patching_rect=[440.0, 70.0, 44.0, 15.0], presentation=1,
        presentation_rect=[92.0, 84.0, 44.0, 15.0], varname='mb_lenbars', annotation=LEN_ANN,
        saved_attribute_attributes={'valueof': lenbars_valueof()})
    box(id='obj-61', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[440.0, 90.0, 110.0, 18.0], presentation=1,
        presentation_rect=[8.0, 84.0, 80.0, 18.0], text='Length (bars)', varname='mb_len_lbl')
    box(id='obj-62', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[440.0, 120.0, 100.0, 22.0], text='prepend lenbars',
        varname='mb_len_prep')
    line('obj-60', 0, 'obj-62', 0)
    line('obj-62', 0, 'obj-10', 1)

    # -- initial state -> engine ------------------------------------------------
    # `outputvalue` makes a live.toggle re-emit what it holds WITHOUT flipping it; a bang
    # here would invert both toggles every time a Live set opened (see add_mon.py).
    box(id='obj-50', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[200.0, 150.0, 62.0, 22.0], text='loadbang', varname='mb_init')
    box(id='obj-51', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[200.0, 180.0, 74.0, 22.0], text='outputvalue', varname='mb_out_fast')
    box(id='obj-52', maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[300.0, 180.0, 74.0, 22.0], text='outputvalue', varname='mb_out_dfx')
    line('obj-50', 0, 'obj-51', 0)
    line('obj-50', 0, 'obj-52', 0)
    line('obj-50', 0, 'obj-60', 0)   # bang is safe on live.numbox: re-emits its stored value
    line('obj-51', 0, 'obj-30', 0)
    line('obj-52', 0, 'obj-40', 0)

    return boxes, lines


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(TEMPLATE)
    P = doc['patcher']

    boxes, lines = build_boxes_lines()
    P['boxes'] = boxes
    P['lines'] = lines
    P['parameters'] = {
        'obj-20': ['Bounce', 'Bounce', 0],
        'obj-30': ['Fast999', 'Fast999', 1],
        'obj-40': ['DisableFX', 'DisableFX', 2],
        'obj-60': ['LengthBars', 'Length', 3],
        'parameterbanks': {
            '0': {'index': 0, 'name': '',
                  'parameters': ['Bounce', 'Fast999', 'DisableFX', 'LengthBars',
                                 '-', '-', '-', '-']},
        },
        'inherited_shortname': 1,
    }
    P['dependency_cache'] = [{
        'name': JS,
        'bootpath': '~/PycharmProjects/maxmsp-mcp/forteseq',
        'type': 'TEXT',
        'implicit': 1,
    }]
    P['rect'] = [140.0, 140.0, 520.0, 400.0]
    P['openinpresentation'] = 1

    # --- self-checks (same class of trap check_structure.py enforces) --------------------
    ids = [b['box']['id'] for b in P['boxes']]
    assert len(ids) == len(set(ids)), 'duplicate box id'
    known = set(ids)
    for ln in P['lines']:
        pl = ln['patchline']
        assert pl['source'][0] in known and pl['destination'][0] in known, pl
    names = {v[0] for k, v in P['parameters'].items()
             if k not in ('parameterbanks', 'inherited_shortname')}
    assert names == {'Bounce', 'Fast999', 'DisableFX', 'LengthBars'}, names
    bank = P['parameters']['parameterbanks']['0']['parameters']
    for nm in names:
        assert nm in bank, ('%s missing from parameterbank' % nm)

    print('midibounce.amxd')
    print('  boxes   : %d' % len(P['boxes']))
    print('  lines   : %d' % len(P['lines']))
    print('  params  : %s' % ', '.join(sorted(names)))
    print('  js dep  : %s' % JS)
    print('  amxdtype: %s (unchanged from template = MIDI effect)'
          % P['project'].get('amxdtype'))

    if not apply_it:
        print('')
        print('(dry run -- nothing written; re-run with --apply)')
        return

    if os.path.exists(DEVICE):
        shutil.copyfile(DEVICE, DEVICE + '.before')
        print('  backup  : %s.before' % os.path.basename(DEVICE))
    # start from a byte copy of the template so the AMPF header + meta chunk come along,
    # then let amxd.save() rewrite the ptch length for our new JSON.
    shutil.copyfile(TEMPLATE, DEVICE)
    d2, s2, e2, _ = amxd.load(DEVICE)
    amxd.save(DEVICE, d2, s2, e2, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    assert len(back['boxes']) == len(P['boxes'])
    assert back['dependency_cache'][0]['name'] == JS
    print('')
    print('wrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/midibounce.amxd')


main()
