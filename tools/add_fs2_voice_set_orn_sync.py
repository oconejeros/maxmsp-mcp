"""Extend the popup<->panel echo sync (same mechanism as add_fs2_voice_patron_sync.py) to the 3
new numeric scrub controls the Horizonte popup now exposes: Set (setIdx, only when TonProp/keyOwn
is on) and OrnNotas/OrnBase (only when Patron is Ornamento). forteseq2.js's setvoicesetindex/
setvoiceorncount/setvoiceornbase already got their outlet(4, ["advecho", idx+1, "<tok>", val])
echoes added this session -- this script wires the RECEIVING side in fs2voice_adv.maxpat.

    python tools/add_fs2_voice_set_orn_sync.py            dry run, writes nothing
    python tools/add_fs2_voice_set_orn_sync.py --apply    do it (device closed in Max AND Live)

## What changes

**forteseq/fs2voice_adv.maxpat** only (no FORTESEQ2.amxd changes -- same reasoning as
add_fs2_voice_patron_sync.py: the shared FS2_ADV_ECHO send/receive/route #1 demux already forwards
any "advecho <idx> <token> <val>" regardless of token):

  * obj-201 (`route ext art lec ton fij patron dir ornt`, 8 args/9 outlets) -> adds `setidx ornn
    ornb` (11 args/12 outlets). Same numinlets==numoutlets convention as before.
  * 3 new `prepend set` (newobj) boxes, wired from the 3 new outlets to obj-112 (v_set), obj-106
    (v_ornnotas), obj-107 (v_ornbase) -- the exact live.numbox objects the panel's own forward-path
    boxes (obj-115 `prepend setvoicesetindex #1`, obj-109 `prepend setvoiceorncount #1`) already
    write to, so a scrub in either place ends up moving the same on-screen control.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VOICE_ADV = os.path.join('forteseq', 'fs2voice_adv.maxpat')

ROUTE_ID = 'obj-201'
OLD_TEXT = 'route ext art lec ton fij patron dir ornt'
NEW_TEXT = 'route ext art lec ton fij patron dir ornt setidx ornn ornb'
TARGETS = [('setidx', 'obj-112'), ('ornn', 'obj-106'), ('ornb', 'obj-107')]


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    route = bx[ROUTE_ID]
    assert route['text'] == OLD_TEXT, 'ya aplicado o texto inesperado: %r' % route['text']
    assert route['numoutlets'] == 9

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    route['text'] = NEW_TEXT
    route['numoutlets'] = 12
    route['numinlets'] = 12
    route['outlettype'] = [''] * 12

    new_ids = []
    for i, (tok, target) in enumerate(TARGETS):
        pid = fresh()
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'varname': 'v_%s_setrx' % tok,
            'patching_rect': [500.0, 550.0 + 30.0 * i, 200.0, 22.0],
            'text': 'prepend set'}})
        pg['lines'].append({'patchline': {'source': [ROUTE_ID, 8 + i], 'destination': [pid, 0]}})
        pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
        new_ids.append(pid)

    print('fs2voice_adv.maxpat: %s -> "%s" (9->12 outlets)' % (ROUTE_ID, route['text']))
    for (tok, target), pid in zip(TARGETS, new_ids):
        print('  outlet %s -> %s (prepend set) -> %s' % (tok, pid, target))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(VOICE_ADV, VOICE_ADV + '.before-setornsync')
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    pg2 = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert bx2[ROUTE_ID]['numoutlets'] == 12
    for pid in new_ids:
        assert pid in bx2 and bx2[pid]['maxclass'] == 'newobj'

    print('\nescrito %s (.before-setornsync guardado). Sigue:' % VOICE_ADV)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice_adv.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
