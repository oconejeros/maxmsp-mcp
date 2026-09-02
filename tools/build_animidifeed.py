"""Build forteseq/ANIMIDIFeed.amxd -- the tiny "voice feeder" companion for ANIMIDI.

    python tools/build_animidifeed.py            dry run, writes nothing
    python tools/build_animidifeed.py --apply    do it

Drop one on every MIDI track (other than ANIMIDI's own) whose notes you want to see as a
separate voice in ANIMIDI. It forwards that track's notes onto the cross-device Max bus
`ANIMIDI_NOTE` tagged with the track's own Live index, so ANIMIDI can group by track --
which is what Live's per-track split of an imported multi-channel MIDI file forces.

Same build method as tools/build_midibounce.py: clone the near-stock MIDI-effect template
`forteseq/forteseqmidifilter.amxd` (keeps the binary AMPF/meta chunk that marks it a MIDI
effect, and the `project` block) and rewrite boxes / lines / parameters / dependency_cache.

Patch:

    midiin --> midiout                                        pass-through
    notein --> pack 0 0 --> prepend n --> js animidifeed.js
    js --> route feed --> pack 0 0 0 --> send ANIMIDI_NOTE     (pitch vel trackIdx)
    live.thisdevice --> js                                    (re-resolve the track index)
    live.numbox "Voz" --> prepend voz --> js                  (-1 = auto, >=0 = force)
    loadbang --> live.numbox                                  (re-emit stored value)

One parameter (Voz). Close the device in BOTH Max and Live before running with --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'forteseq', 'forteseqmidifilter.amxd')
DEVICE = os.path.join(ROOT, 'forteseq', 'ANIMIDIFeed.amxd')
JS = 'animidifeed.js'
BOOT = 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq'

VOZ_ANN = ('Indice de voz que este feeder reporta a ANIMIDI. -1 = automatico (el indice de '
           'la pista de Live donde esta este device). Ponelo a mano solo si el automatico '
           'sale mal (device dentro de un rack, pistas agrupadas, etc.).')


def voz_valueof():
    return {
        'parameter_longname': 'Voz', 'parameter_shortname': 'Voz',
        'parameter_type': 0, 'parameter_mmin': -1.0, 'parameter_mmax': 64.0,
        'parameter_modmode': 0, 'parameter_unitstyle': 0,
        'parameter_initial_enable': 1, 'parameter_initial': [-1.0],
    }


def build_boxes_lines():
    boxes, lines = [], []

    def box(**kw):
        boxes.append({'box': kw})

    def line(src, si, dst, di):
        lines.append({'patchline': {'source': [src, si], 'destination': [dst, di]}})

    # MIDI pass-through
    box(id='obj-1', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['int'],
        patching_rect=[24.0, 300.0, 40.0, 22.0], text='midiin', varname='af_midiin')
    box(id='obj-2', maxclass='newobj', numinlets=1, numoutlets=0,
        patching_rect=[24.0, 340.0, 47.0, 22.0], text='midiout', varname='af_midiout')
    line('obj-1', 0, 'obj-2', 0)

    # notein -> pack pitch vel -> prepend n -> js
    box(id='obj-3', maxclass='newobj', numinlets=1, numoutlets=3, outlettype=['', '', ''],
        patching_rect=[24.0, 40.0, 60.0, 22.0], text='notein', varname='af_notein')
    box(id='obj-4', maxclass='newobj', numinlets=2, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 80.0, 60.0, 22.0], text='pack 0 0', varname='af_pack')
    box(id='obj-5', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 110.0, 70.0, 22.0], text='prepend n', varname='af_prep_n')
    box(id='obj-10', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 150.0, 130.0, 22.0], text='js ' + JS, varname='af_engine',
        saved_object_attributes={'filename': JS, 'parameter_enable': 0})
    line('obj-3', 0, 'obj-4', 0)
    line('obj-3', 1, 'obj-4', 1)
    line('obj-4', 0, 'obj-5', 0)
    line('obj-5', 0, 'obj-10', 0)

    # js -> route feed -> pack 0 0 0 -> send ANIMIDI_NOTE
    box(id='obj-11', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['', ''],
        patching_rect=[24.0, 185.0, 90.0, 22.0], text='route feed', varname='af_route')
    box(id='obj-12', maxclass='newobj', numinlets=3, numoutlets=1, outlettype=[''],
        patching_rect=[24.0, 215.0, 90.0, 22.0], text='pack 0 0 0', varname='af_pack3')
    box(id='obj-13', maxclass='newobj', numinlets=1, numoutlets=0,
        patching_rect=[24.0, 245.0, 140.0, 22.0], text='send ANIMIDI_NOTE', varname='af_send')
    line('obj-10', 0, 'obj-11', 0)
    line('obj-11', 0, 'obj-12', 0)
    line('obj-12', 0, 'obj-13', 0)

    # live.thisdevice -> js (re-resolve track index on load)
    box(id='obj-20', maxclass='newobj', numinlets=1, numoutlets=2, outlettype=['bang', 'bang'],
        patching_rect=[200.0, 40.0, 110.0, 22.0], text='live.thisdevice', varname='af_thisdev')
    line('obj-20', 0, 'obj-10', 0)

    # Voz override
    box(id='obj-30', maxclass='live.numbox', numinlets=1, numoutlets=2, outlettype=['', 'float'],
        parameter_enable=1, patching_rect=[200.0, 90.0, 50.0, 15.0], presentation=1,
        presentation_rect=[96.0, 8.0, 44.0, 15.0], varname='af_voz', annotation=VOZ_ANN,
        saved_attribute_attributes={'valueof': voz_valueof()})
    box(id='obj-31', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
        patching_rect=[200.0, 120.0, 80.0, 22.0], text='prepend voz', varname='af_prep_voz')
    box(id='obj-32', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[8.0, 90.0, 180.0, 18.0], presentation=1,
        presentation_rect=[8.0, 8.0, 86.0, 18.0], fontsize=9.0,
        text='Voz (-1 = auto)', varname='af_voz_lbl')
    box(id='obj-33', maxclass='comment', numinlets=1, numoutlets=0,
        patching_rect=[8.0, 300.0, 220.0, 18.0], presentation=1,
        presentation_rect=[8.0, 30.0, 200.0, 30.0], fontsize=9.0,
        text='alimenta ANIMIDI: reenvia las notas de esta pista al bus, agrupadas por pista',
        varname='af_hint')
    line('obj-30', 0, 'obj-31', 0)
    line('obj-31', 0, 'obj-10', 0)

    # loadbang -> the numbox (bang-safe: re-emits its stored value)
    box(id='obj-40', maxclass='newobj', numinlets=1, numoutlets=1, outlettype=['bang'],
        patching_rect=[200.0, 160.0, 62.0, 22.0], text='loadbang', varname='af_init')
    line('obj-40', 0, 'obj-30', 0)

    return boxes, lines


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(TEMPLATE)
    P = doc['patcher']

    boxes, lines = build_boxes_lines()
    P['boxes'] = boxes
    P['lines'] = lines
    P['parameters'] = {
        'obj-30': ['Voz', 'Voz', 0],
        'parameterbanks': {
            '0': {'index': 0, 'name': '', 'parameters': ['Voz', '-', '-', '-', '-', '-', '-', '-']},
        },
        'inherited_shortname': 1,
    }
    P['dependency_cache'] = [{'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1}]
    P['rect'] = [140.0, 140.0, 360.0, 300.0]
    P['openinpresentation'] = 1

    # --- self-checks ------------------------------------------------------------------
    ids = [b['box']['id'] for b in P['boxes']]
    assert len(ids) == len(set(ids)), 'duplicate box id'
    known = set(ids)
    for ln in P['lines']:
        pl = ln['patchline']
        for tag, end in (('src', pl['source']), ('dst', pl['destination'])):
            bx = next((b['box'] for b in P['boxes'] if b['box']['id'] == end[0]), None)
            assert bx is not None, 'line to unknown box %s' % (end,)
            n = bx.get('numoutlets', 0) if tag == 'src' else bx.get('numinlets', 0)
            assert 0 <= end[1] < n, '%s %s idx %d /%d (%s)' % (
                tag, end[0], end[1], n, bx.get('text', ''))
    names = {v[0] for k, v in P['parameters'].items()
             if k not in ('parameterbanks', 'inherited_shortname')}
    assert names == {'Voz'}, names

    print('ANIMIDIFeed.amxd  (voice feeder for ANIMIDI)')
    print('  boxes   : %d' % len(P['boxes']))
    print('  lines   : %d' % len(P['lines']))
    print('  params  : %s' % ', '.join(sorted(names)))
    print('  js dep  : %s   (bootpath %s)' % (JS, BOOT))
    print('  bus     : send ANIMIDI_NOTE  (pitch vel trackIdx)')
    print('  amxdtype: %s (unchanged from template = MIDI effect)'
          % P.get('project', {}).get('amxdtype'))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    if os.path.exists(DEVICE):
        shutil.copyfile(DEVICE, DEVICE + '.before')
        print('  backup  : %s.before' % os.path.basename(DEVICE))
    shutil.copyfile(TEMPLATE, DEVICE)
    d2, s2, e2, _ = amxd.load(DEVICE)
    amxd.save(DEVICE, d2, s2, e2, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    assert len(back['boxes']) == len(P['boxes'])
    assert back['dependency_cache'][0]['name'] == JS
    print('\nwrote %s' % DEVICE)
    print('now: python tools/check_structure.py forteseq/ANIMIDIFeed.amxd')


main()
