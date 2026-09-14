"""Extend the "essential" per-voice strip's echo sync to Grado/Div, and turn its "on"-only echo
channel into a shared multi-token one -- same evolution fs2voice_adv.maxpat already went through
this session (add_fs2_voice_patron_sync.py etc.), applied here for the first time.

forteseq2.js's setvoicemute() used to send `["onecho", idx+1, <value>]` with no token (the only
thing ever echoed on this channel); it now sends `["onecho", idx+1, "on", <value>]`, and
setvoicedegoffset()/setvoicediv() send `["onecho", idx+1, "grado"/"div", <value>]` alongside it.
This script wires the receiving side in fs2voice.maxpat to match.

    python tools/add_fs2_voice_ess_sync.py            dry run, writes nothing
    python tools/add_fs2_voice_ess_sync.py --apply    do it (device closed in Max AND Live)

## What changes

**forteseq/fs2voice.maxpat** only (no FORTESEQ2.amxd changes -- obj-403's top-level route
already forwards the "onecho" bucket whole, regardless of what is inside it; send FS2_ON_ECHO /
receive FS2_ON_ECHO / route #1 -- obj-100/obj-102 -- are untouched):

  * New `route on grado div` (3 args/4 outlets, same numinlets==numoutlets convention as every
    other route in this codebase) spliced between obj-102 (`route #1`) and the existing obj-101
    (`prepend set` -> obj-2 v_on): obj-102's outlet 0 now feeds the new route's inlet instead of
    obj-101 directly; the new route's "on" outlet takes over feeding obj-101 (unchanged
    on-screen effect), and its "grado"/"div" outlets feed 2 new `prepend set` boxes wired to
    obj-30 (v_grado) / obj-32 (v_div) -- the exact live.numbox objects the panel's own forward-
    path boxes (obj-31 `prepend setvoicedegoffset #1`, obj-33 `prepend setvoicediv #1`) already
    write to.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VOICE = os.path.join('forteseq', 'fs2voice.maxpat')

ROUTE1_ID = 'obj-102'      # route #1
ONVAL_ID = 'obj-101'       # prepend set -> obj-2 (v_on), pre-existing
TARGETS = [('grado', 'obj-30'), ('div', 'obj-32')]


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert bx[ROUTE1_ID]['text'] == 'route #1'
    assert bx[ONVAL_ID]['text'] == 'prepend set'
    old_line = {'source': [ROUTE1_ID, 0], 'destination': [ONVAL_ID, 0]}
    lines = [l['patchline'] for l in pg['lines']]
    assert old_line in lines, 'ya aplicado o cableado inesperado'

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    route2_id = fresh()
    pg['boxes'].append({'box': {
        'id': route2_id, 'maxclass': 'newobj', 'numinlets': 4, 'numoutlets': 4,
        'outlettype': ['', '', '', ''], 'varname': 'v_ess_ui_route',
        'patching_rect': [240.0, 20.0, 160.0, 20.0], 'text': 'route on grado div'}})

    pg['lines'] = [l for l in pg['lines'] if l['patchline'] != old_line]
    pg['lines'].append({'patchline': {'source': [ROUTE1_ID, 0], 'destination': [route2_id, 0]}})
    pg['lines'].append({'patchline': {'source': [route2_id, 0], 'destination': [ONVAL_ID, 0]}})

    new_ids = []
    for i, (tok, target) in enumerate(TARGETS):
        pid = fresh()
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'varname': 'v_%s_setrx' % tok,
            'patching_rect': [420.0, 400.0 + 30.0 * i, 200.0, 22.0],
            'text': 'prepend set'}})
        pg['lines'].append({'patchline': {'source': [route2_id, 1 + i], 'destination': [pid, 0]}})
        pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
        new_ids.append(pid)

    print('fs2voice.maxpat: %s -> %s ("route on grado div") -> {%s (on, existing), %s}'
          % (ROUTE1_ID, route2_id, ONVAL_ID, ', '.join(new_ids)))
    for (tok, target), pid in zip(TARGETS, new_ids):
        print('  outlet %s -> %s (prepend set) -> %s' % (tok, pid, target))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(VOICE, VOICE + '.before-esssync')
    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    pg2 = json.load(open(VOICE, encoding='utf-8'))['patcher']
    bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert bx2[route2_id]['text'] == 'route on grado div'
    for pid in new_ids:
        assert pid in bx2 and bx2[pid]['maxclass'] == 'newobj'

    print('\nescrito %s (.before-esssync guardado). Sigue:' % VOICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
