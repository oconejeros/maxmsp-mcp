"""Wire the reverse echo for the global Set control -- the one thing the user tested repeatedly
and reported as "only the display moves, not the actual parameter." Root cause, found by tracing
outlet 1 of the engine (js forteseq2.js) all the way through: emitSetReadouts()'s
`outlet(1, setIndex + 1)` reaches a `prepend set` -> a plain COMMENT box (fs2_disp_idx_top,
display only) at the top level, AND separately feeds inlet 2 of the fs2_pages bpatcher -- but
INSIDE fs2pages.maxpat that inlet (obj-3) has zero outgoing connections. The real, interactive
Set widget (`fs2_set`, live.numbox, range 1-351, longname "Set") lives inside fs2pages.maxpat's
Armonia page and was never told about engine-side changes at all.

setlockindex() in forteseq2.js now also sends `outlet(4, ["gecho", "set", idx + 1])` on the same
channel the rest of the global sidebar echo (FS2_G_ECHO) already uses. Because fs2_set lives
INSIDE a bpatcher (fs2pages.maxpat), not the root patcher, this needs its OWN `receive
FS2_G_ECHO` inside that file -- send/receive match by name regardless of patcher nesting, so this
does not require touching the existing root-level `route` (obj-823) at all; it is a second,
independent receiver of the same broadcast, same shape as add_fs2_euclid_sync.py's rtecho
receiver in this same file.

    python tools/add_fs2_set_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_set_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only -- no FORTESEQ2.amxd change needed)

New `receive FS2_G_ECHO` -> `route set` -> `prepend set` -> `fs2_set` (obj-12).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
TARGET_ID = 'obj-12'   # fs2_set


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}
	assert TARGET_ID in bx and bx[TARGET_ID].get('varname') == 'fs2_set'
	assert not any(b['box'].get('text') == 'receive FS2_G_ECHO' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_set_gecho_rx', 'patching_rect': [900.0, 3900.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
		'outlettype': ['', ''], 'varname': 'fs2_set_gecho_route',
		'patching_rect': [900.0, 3930.0, 160.0, 20.0], 'text': 'route set'}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	prep_id = fresh()
	pg['boxes'].append({'box': {
		'id': prep_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_set_gecho_setrx', 'patching_rect': [900.0, 3960.0, 160.0, 22.0],
		'text': 'prepend set'}})
	pg['lines'].append({'patchline': {'source': [route_id, 0], 'destination': [prep_id, 0]}})
	pg['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': [TARGET_ID, 0]}})

	print('fs2pages.maxpat: +%s (receive FS2_G_ECHO) -> +%s (route set) -> +%s (prepend set) -> %s (fs2_set)'
		  % (recv_id, route_id, prep_id, TARGET_ID))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(PAGES, PAGES + '.before-setechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2 and prep_id in bx2

	print('\nescrito %s (.before-setechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
