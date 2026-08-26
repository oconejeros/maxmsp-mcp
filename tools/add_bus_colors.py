"""Color-code the BUS too, the same idea as add_voice_colors.py but for the address instead of
the voice slot. A bus can be 1-16 (Bus's own parameter range), read at runtime in both devices --
FORTESEQ2 broadcasts on whatever its own Bus numbox says, and a Hub matches whatever ITS Bus
numbox says -- so both chips are the sel-driven kind, unlike the voice chip's static half.

    python tools/add_bus_colors.py            dry run, writes nothing
    python tools/add_bus_colors.py --apply    do it

16 colors, generated (not hand-picked like the 4 voice colors -- 16 memorable distinct colors
isn't realistic) by stepping hue evenly around the color wheel at fixed saturation/value, so bus 1
and bus 9 are as far apart in hue as two buses can be.

Placement: FORTESEQ2's engine row (y<46) has a confirmed-empty gap from x=496 (end of the Dir tab)
to x=826 (start of the page tab strip) -- the chip goes there. The Hub's color row (y=66, from
add_voice_colors.py) has room after the voice chip (ends x=188) before hitting the row's own width
ceiling (262, set by row 1's Modo tab) -- the bus chip goes there, no further growth needed.

Close BOTH devices in Max and Live first.
"""
import colorsys
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

FORTESEQ2 = os.path.join('forteseq', 'FORTESEQ2.amxd')
HUB = os.path.join('forteseq', 'forteseqhub.amxd')
N_BUS = 16
NEUTRAL = [0.5, 0.5, 0.5, 1.0]


def bus_palette():
    pal = {}
    for bus in range(1, N_BUS + 1):
        h = (bus - 1) / N_BUS
        r, g, b = colorsys.hsv_to_rgb(h, 0.65, 0.85)
        pal[bus] = [round(r, 3), round(g, 3), round(b, 3), 1.0]
    return pal


PALETTE = bus_palette()


def add_bus_chip(doc, bus_ctl_id, chip_rect, lbl_rect, patch_xy, varname_prefix):
    P = doc['patcher']
    boxes = {b['box']['id']: b['box'] for b in P['boxes']}
    byvar = {b['box'].get('varname'): b['box']['id'] for b in P['boxes'] if b['box'].get('varname')}
    assert varname_prefix + '_chip' not in byvar, 'ya esta puesto'
    nxt = [max(int(i.split('-')[1]) for i in boxes)]

    def fresh():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    def box(**kw):
        b = dict(kw)
        b.setdefault('id', fresh())
        P['boxes'].append({'box': b})
        return b['id']

    def link(a, c, ao=0, ci=0):
        P['lines'].append({'patchline': {'source': [a, ao], 'destination': [c, ci]}})

    px, py = patch_xy
    chip = box(maxclass='comment', numinlets=1, numoutlets=0, text='', varname=varname_prefix + '_chip',
               annotation='Color de este Bus (1-%d). Gris: Bus fuera de ese rango.' % N_BUS,
               patching_rect=[px, py, chip_rect[2], chip_rect[3]],
               presentation=1, presentation_rect=list(chip_rect), bgcolor=list(NEUTRAL))
    box(maxclass='comment', numinlets=1, numoutlets=0, text='Bus', varname=varname_prefix + '_lbl',
        patching_rect=[px, py - 30.0, lbl_rect[2], lbl_rect[3]],
        presentation=1, presentation_rect=list(lbl_rect))

    sel_args = ' '.join(str(i) for i in range(1, N_BUS + 1))
    sel = box(maxclass='newobj', numinlets=1, numoutlets=N_BUS + 1,
              outlettype=[''] * (N_BUS + 1), varname=varname_prefix + '_sel',
              patching_rect=[px, py + 30.0, 260.0, 22.0], text='sel ' + sel_args)
    link(bus_ctl_id, sel)
    for i in range(1, N_BUS + 1):
        r, g, b_, a = PALETTE[i]
        msg = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
                  patching_rect=[px + i * 70.0, py + 60.0, 130.0, 22.0],
                  text='bgcolor %.3f %.3f %.3f %.3f' % (r, g, b_, a))
        link(sel, msg, ao=i - 1)
        link(msg, chip)
    r, g, b_, a = NEUTRAL
    dflt = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
              patching_rect=[px + (N_BUS + 1) * 70.0, py + 60.0, 130.0, 22.0],
              text='bgcolor %.3f %.3f %.3f %.3f' % (r, g, b_, a))
    link(sel, dflt, ao=N_BUS)
    link(dflt, chip)

    R = [b['box']['presentation_rect'] for b in P['boxes']
         if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    bad = [(a2, b2) for a2 in R for b2 in R if a2 is not b2
           and a2[0] < b2[0] + b2[2] and b2[0] < a2[0] + a2[2]
           and a2[1] < b2[1] + b2[3] and b2[1] < a2[1] + a2[3]]
    assert not bad, bad
    return max(r[0] + r[2] for r in R), max(r[1] + r[3] for r in R)


def do_forteseq2(apply_it):
    data, s, e, doc = amxd.load(FORTESEQ2)
    w, h = add_bus_chip(doc, 'obj-26', [506.0, 24.0, 16.0, 15.0], [506.0, 5.0, 34.0, 18.0],
                         (2600.0, 700.0), 'fs2_bus_color')
    print('FORTESEQ2: chip de bus agregado, %.0f x %.0f px, sin solapamientos' % (w, h))
    if apply_it:
        amxd.save(FORTESEQ2, data, s, e, doc)
        print('escrito %s' % FORTESEQ2)


def do_hub(apply_it):
    data, s, e, doc = amxd.load(HUB)
    w, h = add_bus_chip(doc, 'obj-30', [216.0, 66.0, 16.0, 15.0], [216.0, 48.0, 34.0, 18.0],
                         (170.0, 1000.0), 'hub_bus_color')
    print('Hub: chip de bus agregado, %.0f x %.0f px, sin solapamientos' % (w, h))
    if apply_it:
        amxd.save(HUB, data, s, e, doc)
        print('escrito %s' % HUB)


def main():
    apply_it = '--apply' in sys.argv
    if '--skip-forteseq2' not in sys.argv:
        do_forteseq2(apply_it)
    if '--skip-hub' not in sys.argv:
        do_hub(apply_it)
    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')


if __name__ == '__main__':
    main()
