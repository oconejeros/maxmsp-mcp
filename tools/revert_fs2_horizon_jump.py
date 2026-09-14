"""Revert add_fs2_horizon_jump.py: the "Voces N" tabs are NOT one-per-voice -- they are four
PARAMETER-GROUP pages (essential / advanced / articulacion / ornamento+tonalidad), and every
page always shows all 4 voices stacked together (obj-577..obj-580, one bpatcher instance per
voice, same "offset" pan applied to all four at once). A click on voice v's row in the popup
therefore has no single matching tab to jump to -- "jump to Voces 2" doesn't mean "show voice
2", it means "show a different parameter group, for every voice". Confirmed with the user
2026-09-13 after they found it made no sense in practice ("no tiene mucho sentido esto").

    python tools/revert_fs2_horizon_jump.py            dry run, writes nothing
    python tools/revert_fs2_horizon_jump.py --apply    do it (device closed in Max AND Live)

Undoes, file by file:
**forteseq/fs2horizon.js**: removes rowGeo/onclick()/VOCES_PAGE and the "rowGeo = {...}" line
added at the end of paint()'s row-geometry block.
**forteseq/FORTESEQ2.amxd**: removes obj-2 (fs2hz_ui) -> obj-4 wire inside obj-751; removes
obj-808 (route jumpvoice), obj-809 (sel 0 1 2 3), obj-810..813 (the 4 message boxes) and all
their patchlines; restores the direct obj-751 -> obj-23 wire.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
HORIZON_JS = os.path.join('forteseq', 'fs2horizon.js')

WIN_ID = 'obj-751'
ENGINE_ID = 'obj-23'
REMOVE_IDS = {'obj-808', 'obj-809', 'obj-810', 'obj-811', 'obj-812', 'obj-813'}

OLD_PAINT_SNIPPET = '''	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH);
	var rowH = gridH / nRows;
	rowGeo = { headH: headH, rowH: rowH, nRows: nRows };   // read by onclick() to find the row hit'''

NEW_PAINT_SNIPPET = '''	var nRows = Math.max(1, Math.min(MAXROWS, voices));
	var gridH = Math.max(1, H - headH - statusH - shapeH - ornH);
	var rowH = gridH / nRows;'''

ONCLICK_BLOCK = '''
// Geometry of the last paint(), so onclick() can tell which voice row a click landed on -- same
// "paint() records, onclick() reads" pattern fs2setpick.js already uses for its own `geo`.
var rowGeo = null;

// Click anywhere on a voice's row -> jump the main panel to that voice's "Voces N" tab. Pagina's
// own restore/jump plumbing (obj-486's sel router) does the rest; see add_fs2_horizon_jump.py.
var VOCES_PAGE = [6, 7, 9, 10];   // Pagina index for V1..V4
function onclick(x, y, but) {
	if (!but || !rowGeo) return;
	if (y < rowGeo.headH) return;
	var v = Math.floor((y - rowGeo.headH) / rowGeo.rowH);
	if (v < 0 || v >= rowGeo.nRows || v >= VOCES_PAGE.length) return;
	outlet(0, ['jumpvoice', v]);
}
'''


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2horizon.js ---------------------------------------------------------------------
    hz = open(HORIZON_JS, encoding='utf-8').read()
    assert 'function onclick' in hz and 'rowGeo' in hz, 'no esta aplicado -- nada que revertir'
    assert OLD_PAINT_SNIPPET in hz
    hz2 = hz.replace(OLD_PAINT_SNIPPET, NEW_PAINT_SNIPPET)
    assert ONCLICK_BLOCK in hz2
    hz2 = hz2.replace(ONCLICK_BLOCK + '\n', '', 1)
    assert 'rowGeo' not in hz2 and 'function onclick' not in hz2 and 'VOCES_PAGE' not in hz2

    # ---- FORTESEQ2.amxd ---------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    win = bx[WIN_ID]
    subP = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in subP['boxes']}
    assert all(rid in bx for rid in REMOVE_IDS), 'no esta aplicado -- nada que revertir'

    subP['lines'] = [l for l in subP['lines']
                      if not (l['patchline']['source'] == ['obj-2', 0] and l['patchline']['destination'] == ['obj-4', 0])]

    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in REMOVE_IDS]
    P['lines'] = [l for l in P['lines'] if l['patchline']['source'][0] not in REMOVE_IDS
                  and l['patchline']['destination'][0] not in REMOVE_IDS]
    P['lines'].append({'patchline': {'source': [WIN_ID, 0], 'destination': [ENGINE_ID, 0]}})

    print('fs2horizon.js: -onclick()/rowGeo/VOCES_PAGE')
    print('inside %s: removed obj-2 (fs2hz_ui) outlet -> obj-4' % WIN_ID)
    print('removed %s' % sorted(REMOVE_IDS))
    print('restored direct wire %s -> %s' % (WIN_ID, ENGINE_ID))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    open(HORIZON_JS, 'w', encoding='utf-8', newline='\n').write(hz2)
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert not any(rid in bx2 for rid in REMOVE_IDS)
    assert any(l['patchline']['source'] == [WIN_ID, 0] and l['patchline']['destination'] == [ENGINE_ID, 0]
               for l in P2['lines'])

    print('\nrevertido. Sigue:')
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')


main()
