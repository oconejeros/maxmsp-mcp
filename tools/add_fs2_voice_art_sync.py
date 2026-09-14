"""Extend the popup<->panel echo sync (same mechanism as add_fs2_voice_patron_sync.py /
add_fs2_voice_set_orn_sync.py) to the 4 new per-voice Articulacion scrub controls the Horizonte
popup now exposes when Art (artOwn) is on: VelMin/VelMax/Figura/Silencio. forteseq2.js's
setvoicearticulation() already got its 4 outlet(4, ["advecho", idx+1, "<tok>", val]) echoes added
this session -- this script wires the RECEIVING side in fs2voice_adv.maxpat.

    python tools/add_fs2_voice_art_sync.py            dry run, writes nothing
    python tools/add_fs2_voice_art_sync.py --apply    do it (device closed in Max AND Live)

## What changes

**forteseq/fs2voice_adv.maxpat** only (no FORTESEQ2.amxd changes -- the shared FS2_ADV_ECHO
send/receive/route #1 demux already forwards any "advecho <idx> <token> <val>" regardless of
token):

  * obj-201 (`route ext art lec ton fij patron dir ornt setidx ornn ornb`, 11 args/12 outlets) ->
    adds `artvmin artvmax artdur artsil` (15 args/16 outlets). Same numinlets==numoutlets
    convention as before.
  * 4 new `prepend set` (newobj) boxes, wired from the 4 new outlets to obj-40 (v_velmin), obj-41
    (v_velmax), obj-42 (v_figura), obj-43 (v_silencio) -- the exact live.numbox objects the
    panel's own forward-path box (obj-52, `prepend setvoicearticulation #1`, fed by obj-51's
    `pak 55 80 16 0`) already reads from, so a scrub in either place ends up moving the same
    on-screen controls.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VOICE_ADV = os.path.join('forteseq', 'fs2voice_adv.maxpat')

ROUTE_ID = 'obj-201'
OLD_TEXT = 'route ext art lec ton fij patron dir ornt setidx ornn ornb'
NEW_TEXT = 'route ext art lec ton fij patron dir ornt setidx ornn ornb artvmin artvmax artdur artsil'
TARGETS = [('artvmin', 'obj-40'), ('artvmax', 'obj-41'), ('artdur', 'obj-42'), ('artsil', 'obj-43')]


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    route = bx[ROUTE_ID]
    assert route['text'] == OLD_TEXT, 'ya aplicado o texto inesperado: %r' % route['text']
    assert route['numoutlets'] == 12

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    route['text'] = NEW_TEXT
    route['numoutlets'] = 16
    route['numinlets'] = 16
    route['outlettype'] = [''] * 16

    new_ids = []
    for i, (tok, target) in enumerate(TARGETS):
        pid = fresh()
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'varname': 'v_%s_setrx' % tok,
            'patching_rect': [500.0, 650.0 + 30.0 * i, 200.0, 22.0],
            'text': 'prepend set'}})
        pg['lines'].append({'patchline': {'source': [ROUTE_ID, 11 + i], 'destination': [pid, 0]}})
        pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
        new_ids.append(pid)

    print('fs2voice_adv.maxpat: %s -> "%s" (12->16 outlets)' % (ROUTE_ID, route['text']))
    for (tok, target), pid in zip(TARGETS, new_ids):
        print('  outlet %s -> %s (prepend set) -> %s' % (tok, pid, target))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(VOICE_ADV, VOICE_ADV + '.before-artsync')
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    pg2 = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert bx2[ROUTE_ID]['numoutlets'] == 16
    for pid in new_ids:
        assert pid in bx2 and bx2[pid]['maxclass'] == 'newobj'

    print('\nescrito %s (.before-artsync guardado). Sigue:' % VOICE_ADV)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice_adv.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
