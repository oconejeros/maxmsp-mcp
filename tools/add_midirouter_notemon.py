"""Give Midirouter a two-lane piano monitor of the notes going through it.

The device is a pitch gate: midiin -> midiparse -> [gate driven by mr_pitchtable] ->
stripnote -> makenote -> noteout. The only thing in presentation is the mr_pitchkeys
kslider you click to pick the allowed pitches; there is no view of what is actually
arriving or what the filter is letting past. Nularseq solves the same problem with a
hand-built drum-rack grid of ~64 light-up cells; this does the piano-keyboard version
of that idea with two stacked mode-0 ksliders directly under the existing filter:

  mr_mon_in   (amber)  <- midiparse note outlet     every note that reaches the device
  mr_mon_pass (green)  <- gate outlet               only the notes the filter passes

A note the filter blocks lights amber on the top lane and stays dark on the bottom one,
so "blocked" reads as amber-only and "passed" reads as amber+green in the same column.
Both ksliders are ignoreclick 1 and parameter_enable 0 -- they are indicators, not
controls, and not Live parameters, so none of the parameter-registry bookkeeping applies.

    python tools/add_midirouter_notemon.py            dry run, writes nothing
    python tools/add_midirouter_notemon.py --apply    do it (backup: .before-notemon)

Feeds are parallel cords off outlets that already fan out (midiparse:0 -> t l l, gate:0
-> stripnote), so nothing downstream changes. One known cosmetic edge: if you disable a
pitch while a note of that pitch is held, its note-off is gated out and that key stays
lit green until the next note-off for it. Close the device in Max AND Live first.
Idempotent.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'forteseq', 'Midirouter.amxd')

AMBER = [1.0, 0.709803921568627, 0.196078431372549, 1.0]
GREEN = [0.278431372549020, 0.788235294117647, 0.376470588235294, 1.0]

# 88-key piano span, A0..C8. Notes outside it are rare on a MIDI FX and a monitor that
# quietly ignores them is fine.
OFFSET, RANGE = 21, 88


def kslider(bid, varname, hkeycolor, pres_rect, patch_rect):
    return {'box': {
        'id': bid, 'maxclass': 'kslider', 'varname': varname,
        'numinlets': 2, 'numoutlets': 2, 'outlettype': ['int', 'int'],
        'mode': 0, 'ignoreclick': 1, 'parameter_enable': 0,
        'offset': OFFSET, 'range': RANGE, 'hkeycolor': hkeycolor,
        'presentation': 1, 'presentation_rect': pres_rect,
        'patching_rect': patch_rect}}


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}

    if 'mr_mon_in' in bv:
        print('mr_mon_in already present -- nothing to do')
        return

    midiparse = bv['mr_midiparse']          # obj-8, outlet 0 = note (pitch velocity) list
    gate = bv['mr_gate']                    # obj-11, outlet 0 = passed note list
    filt = bx[bv['mr_pitchkeys']]           # obj-6, the click-to-pick filter kslider
    fr = filt['presentation_rect']          # [0, 0, 392, 60]
    x, w = fr[0], fr[2]
    y0 = fr[1] + fr[3] + 2.0                # first lane starts just under the filter

    nid = max(int(i.split('-')[1]) for i in bx)
    mon_in, mon_pass, legend = 'obj-%d' % (nid + 1), 'obj-%d' % (nid + 2), 'obj-%d' % (nid + 3)

    P['boxes'].append(kslider(mon_in, 'mr_mon_in', AMBER,
                              [x, y0, w, 22.0], [780.0, 60.0, 380.0, 40.0]))
    P['boxes'].append(kslider(mon_pass, 'mr_mon_pass', GREEN,
                              [x, y0 + 23.0, w, 22.0], [780.0, 120.0, 380.0, 40.0]))
    P['boxes'].append({'box': {
        'id': legend, 'maxclass': 'live.comment', 'varname': 'mr_mon_legend',
        'numinlets': 1, 'numoutlets': 0, 'fontsize': 8.0,
        'text': 'in → amber   passed to Live → green',
        'presentation': 1, 'presentation_rect': [x + 2.0, y0 + 46.0, w - 4.0, 14.0],
        'patching_rect': [780.0, 180.0, 300.0, 18.0]}})

    P['lines'].append({'patchline': {'source': [midiparse, 0], 'destination': [mon_in, 0]}})
    P['lines'].append({'patchline': {'source': [gate, 0], 'destination': [mon_pass, 0]}})

    bottom = y0 + 60.0
    edge = max(b['box']['presentation_rect'][0] + b['box']['presentation_rect'][2]
               for b in P['boxes'] if b['box'].get('presentation'))
    print('mr_mon_in  %s  amber  <- %s (midiparse) outlet 0' % (mon_in, midiparse))
    print('mr_mon_pass %s green  <- %s (gate) outlet 0' % (mon_pass, gate))
    print('lanes span presentation y %.0f..%.0f  (device height 169)' % (fr[1] + fr[3], bottom))
    print('presentation right edge: %.0f px  (filter kslider is %.0f wide)' % (edge, w))
    assert bottom <= 169.0, bottom

    if not apply_it:
        print('\n(dry run -- re-run with --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-notemon')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    b2 = {b['box']['id']: b['box'] for b in back['boxes']}
    assert any(b.get('varname') == 'mr_mon_in' for b in b2.values()), 'readback: mr_mon_in missing'
    assert any(b.get('varname') == 'mr_mon_pass' for b in b2.values()), 'readback: mr_mon_pass missing'
    got = {(ln['patchline']['source'][0], ln['patchline']['destination'][0]) for ln in back['lines']}
    assert (midiparse, mon_in) in got and (gate, mon_pass) in got, 'readback: feed cords missing'
    print('\nwrote %s  (backup: %s.before-notemon)' % (DEVICE, os.path.basename(DEVICE)))
    print('now: python tools/check_structure.py forteseq/Midirouter.amxd')


main()
