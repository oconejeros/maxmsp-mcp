"""Reflow the Hub's 5 parameters from one wide row into two, so the device takes less horizontal
room in Live's rack. Pure repositioning: no parameter is renamed, reordered, added or removed --
only `presentation_rect` moves. The height budget was almost untouched (45 of a ~169px ceiling),
so there was nothing to gain by shrinking controls, only by using the vertical room that was
already free.

    python tools/narrow_hub.py            dry run, writes nothing
    python tools/narrow_hub.py --apply    do it

Before: one row, Bus/Voz/Modo/Thru/Panic/monitor, 434px wide.
After: row 1 Bus/Voz/Modo, row 2 Thru/Panic/monitor, ~262px wide.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'forteseqhub.amxd')

# varname/id -> new presentation_rect. Widths/heights are unchanged from today's file; only x/y move.
ROW1_Y_LABEL, ROW1_Y_CTRL = 5.0, 24.0
ROW2_Y_LABEL, ROW2_Y_CTRL = 48.0, 66.0
LAYOUT = {
    'hub_bus':   [8.0, ROW1_Y_CTRL, 40.0, 15.0],
    'hub_voice': [58.0, ROW1_Y_CTRL, 40.0, 15.0],
    'hub_mode':  [112.0, ROW1_Y_CTRL, 150.0, 18.0],
    'hub_thru':  [8.0, ROW2_Y_CTRL, 15.0, 15.0],
    'hub_panic': [54.0, ROW2_Y_CTRL, 56.0, 18.0],
    'hub_monitor': [120.0, ROW2_Y_CTRL, 24.0, 24.0],
}
LABEL_LAYOUT = {
    'Bus':   [8.0, ROW1_Y_LABEL, 34.0, 18.0],
    'Voz':   [58.0, ROW1_Y_LABEL, 34.0, 18.0],
    'Modo':  [112.0, ROW1_Y_LABEL, 40.0, 18.0],
    'Thru':  [8.0, ROW2_Y_LABEL, 38.0, 18.0],
    'Datos': [120.0, ROW2_Y_LABEL, 44.0, 18.0],
}


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    byvar = {b['box'].get('varname'): b['box'] for b in P['boxes'] if b['box'].get('varname')}

    moved = 0
    for var, rect in LAYOUT.items():
        assert var in byvar, 'no encontre %s' % var
        byvar[var]['presentation_rect'] = list(rect)
        moved += 1

    # The plain `comment` labels above each control have no varname, only their text -- match by
    # that instead, and only among comments (the PANIC live.text also has matching text but is a
    # control, already handled above and excluded here by maxclass).
    comments = {b['box']['text']: b['box'] for b in P['boxes']
                if b['box']['maxclass'] == 'comment' and b['box'].get('text') in LABEL_LAYOUT}
    assert len(comments) == len(LABEL_LAYOUT), sorted(set(LABEL_LAYOUT) - set(comments))
    for text, rect in LABEL_LAYOUT.items():
        comments[text]['presentation_rect'] = list(rect)
        moved += 1

    R = [b['box']['presentation_rect'] for b in P['boxes']
         if b['box'].get('presentation') and b['box'].get('presentation_rect')]
    w = max(r[0] + r[2] for r in R)
    h = max(r[1] + r[3] for r in R)
    bad = [(a, b) for a in R for b in R if a is not b
           and a[0] < b[0] + b[2] and b[0] < a[0] + a[2]
           and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]]
    assert not bad, bad
    print('movidos %d objetos, %.0f x %.0f px (era 434 x 45), sin solapamientos' % (moved, w, h))

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
