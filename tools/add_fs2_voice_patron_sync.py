"""Extend the popup<->panel echo sync (fix_fs2_voice_ui_sync_prepend_maxclass.py's mechanism) to
the 3 new per-voice reading controls the Horizonte popup now exposes when Lec (LecProp) is on:
Patron, Dir, and (only while Patron is Ornamento) OrnTipo. forteseq2.js's setvoicereadmode/
setvoicereaddir/setvoiceorntype already got their outlet(4, ["advecho", idx+1, "<tok>", val])
echoes added this session (see the forteseq2.js diff) -- this script wires the RECEIVING side in
fs2voice_adv.maxpat, same route/prepend-set/live.numbox pattern as ext/art/lec/ton/fij already use.

    python tools/add_fs2_voice_patron_sync.py            dry run, writes nothing
    python tools/add_fs2_voice_patron_sync.py --apply    do it (device closed in Max AND Live)

## What changes

**forteseq/fs2voice_adv.maxpat** only (no FORTESEQ2.amxd changes -- the shared FS2_ADV_ECHO
send/receive/route #1 demux already forwards any "advecho <idx> <token> <val>" regardless of
token, that plumbing does not care how many tokens exist downstream of it):

  * obj-201 (`route ext art lec ton fij`, 5 args/6 outlets) -> `route ext art lec ton fij patron
    dir ornt` (8 args/9 outlets). Same numinlets==numoutlets convention already used for obj-201
    itself and obj-207 (`route #1`) in this file.
  * 3 new `prepend set` (newobj, NOT message -- see fix_fs2_voice_ui_sync_prepend_maxclass.py for
    why that distinction matters) boxes, wired from the 3 new outlets to obj-45 (v_patron),
    obj-46 (v_dir), obj-105 (v_orntipo) -- the exact same live.numbox objects the panel's own
    "prepend setvoicereadmode/readdir/orntype #1" forward-path boxes (obj-49/50/108) already
    read from, so a click in either place ends up moving the same on-screen control.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VOICE_ADV = os.path.join('forteseq', 'fs2voice_adv.maxpat')

ROUTE_ID = 'obj-201'
TARGETS = [('patron', 'obj-45'), ('dir', 'obj-46'), ('ornt', 'obj-105')]


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    route = bx[ROUTE_ID]
    assert route['text'] == 'route ext art lec ton fij', 'ya aplicado o texto inesperado: %r' % route['text']
    assert route['numoutlets'] == 6

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    route['text'] = 'route ext art lec ton fij patron dir ornt'
    route['numoutlets'] = 9
    route['numinlets'] = 9   # this codebase's route boxes keep numinlets == numoutlets, see amxd_parameter_registries note
    route['outlettype'] = [''] * 9

    new_ids = []
    for i, (tok, target) in enumerate(TARGETS):
        pid = fresh()
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'varname': 'v_%s_setrx' % tok,
            'patching_rect': [500.0, 460.0 + 30.0 * i, 200.0, 22.0],
            'text': 'prepend set'}})
        pg['lines'].append({'patchline': {'source': [ROUTE_ID, 5 + i], 'destination': [pid, 0]}})
        pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
        new_ids.append(pid)

    print('fs2voice_adv.maxpat: %s -> "%s" (6->9 outlets)' % (ROUTE_ID, route['text']))
    for (tok, target), pid in zip(TARGETS, new_ids):
        print('  outlet %s -> %s (prepend set) -> %s' % (tok, pid, target))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(VOICE_ADV, VOICE_ADV + '.before-patronsync')
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    pg2 = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert bx2[ROUTE_ID]['numoutlets'] == 9
    for pid in new_ids:
        assert pid in bx2 and bx2[pid]['maxclass'] == 'newobj'

    print('\nescrito %s (.before-patronsync guardado). Sigue:' % VOICE_ADV)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice_adv.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
