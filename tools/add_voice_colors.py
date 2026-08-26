"""Color-code voices so the generator and every Hub agree on what "voice 2" looks like, not just
what it is called. Same bus (in the sense the user means it: which of the 4 voice channels), same
color, in both devices -- so a device chain in Live reads at a glance instead of by numbox value.

    python tools/add_voice_colors.py            dry run, writes nothing
    python tools/add_voice_colors.py --apply    do it

Two different mechanisms, because the two devices know different things at build time:

- FORTESEQ2 always has exactly voices 1-4 in fixed strips, so their color is static: `bgcolor` set
  directly on the existing V1..V4 labels (fs2_vlbl1..4). `comment` is a plain Max object, not a
  `live.*` one, so Live's automatic light/dark theming has no say over it -- verified via
  get_object_doc before choosing this over a live.* control's color.
- A Hub instance can point at ANY voice depending on how the user set "Voz", so its color has to
  be read at runtime: a new small `comment` chip next to Voz, recolored by a `sel 1 2 3 4` off
  hub_voice's own outlet sending it a `bgcolor r g b a` message. Voice 0/5+ (silence, or a range
  the strips don't cover) falls through sel's last outlet to a neutral grey, not one of the four
  voice colors -- that combination isn't wired to anything real.

Close BOTH devices in Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

FORTESEQ2 = os.path.join('forteseq', 'FORTESEQ2.amxd')
HUB = os.path.join('forteseq', 'forteseqhub.amxd')

# One color per voice, RGBA 0-1 -- distinguishable from each other and from the device's own grey
# background at a glance, not tuned for anything beyond that.
PALETTE = {
    1: [0.85, 0.25, 0.25, 1.0],
    2: [0.25, 0.45, 0.85, 1.0],
    3: [0.30, 0.70, 0.35, 1.0],
    4: [0.85, 0.65, 0.20, 1.0],
}
NEUTRAL = [0.5, 0.5, 0.5, 1.0]


def do_forteseq2(apply_it):
    data, s, e, doc = amxd.load(FORTESEQ2)
    P = doc['patcher']
    byvar = {b['box'].get('varname'): b['box'] for b in P['boxes'] if b['box'].get('varname')}
    n = 0
    for v in range(1, 5):
        var = 'fs2_vlbl%d' % v
        assert var in byvar, 'no encontre %s' % var
        assert 'bgcolor' not in byvar[var], '%s ya tiene bgcolor' % var
        byvar[var]['bgcolor'] = list(PALETTE[v])
        n += 1
    print('FORTESEQ2: %d etiquetas de voz coloreadas' % n)
    if apply_it:
        amxd.save(FORTESEQ2, data, s, e, doc)
        print('escrito %s' % FORTESEQ2)


def do_hub(apply_it):
    data, s, e, doc = amxd.load(HUB)
    P = doc['patcher']
    boxes = {b['box']['id']: b['box'] for b in P['boxes']}
    byvar = {b['box'].get('varname'): b['box'] for b in P['boxes'] if b['box'].get('varname')}
    assert 'hub_color_chip' not in byvar, 'ya esta puesto'
    voz = byvar['hub_voice']['id']   # link() needs the id string, not the box dict
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

    chip = box(maxclass='comment', numinlets=1, numoutlets=0, text='', varname='hub_color_chip',
               annotation='El color de la voz que este Hub esta escuchando ahora mismo. Gris: '
                          'ninguna de las 4 (Voz en 0 o mayor a 4).',
               patching_rect=[170.0, 900.0, 16.0, 15.0],
               presentation=1, presentation_rect=[172.0, 66.0, 16.0, 15.0],
               bgcolor=list(NEUTRAL))
    lbl = box(maxclass='comment', numinlets=1, numoutlets=0, text='Color',
              varname='hub_color_lbl', patching_rect=[170.0, 870.0, 40.0, 18.0],
              presentation=1, presentation_rect=[172.0, 48.0, 40.0, 18.0])

    sel = box(maxclass='newobj', numinlets=1, numoutlets=5, outlettype=['', '', '', '', ''],
              varname='hub_color_sel', patching_rect=[170.0, 800.0, 150.0, 22.0], text='sel 1 2 3 4')
    link(voz, sel)
    for i in range(1, 5):
        r, g, b_, a = PALETTE[i]
        msg = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
                  patching_rect=[170.0 + i * 90.0, 840.0, 130.0, 22.0],
                  text='bgcolor %.2f %.2f %.2f %.2f' % (r, g, b_, a))
        link(sel, msg, ao=i - 1)
        link(msg, chip)
    r, g, b_, a = NEUTRAL
    dflt = box(maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
              patching_rect=[170.0 + 5 * 90.0, 840.0, 130.0, 22.0],
              text='bgcolor %.2f %.2f %.2f %.2f' % (r, g, b_, a))
    link(sel, dflt, ao=4)
    link(dflt, chip)

    R = [b['box']['presentation_rect'] for b in P['boxes']
         if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    w = max(r[0] + r[2] for r in R)
    h = max(r[1] + r[3] for r in R)
    bad = [(a2, b2) for a2 in R for b2 in R if a2 is not b2
           and a2[0] < b2[0] + b2[2] and b2[0] < a2[0] + a2[2]
           and a2[1] < b2[1] + b2[3] and b2[1] < a2[1] + a2[3]]
    assert not bad, bad
    print('Hub: chip + sel de color agregados, %.0f x %.0f px, sin solapamientos' % (w, h))
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
