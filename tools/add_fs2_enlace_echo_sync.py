"""Wire the reverse echo for the global Enlace control (Enlace Tonos / linkMin) -- added to the
Horizonte popup's sidebar column 1 alongside Ind/Flt/Lck. setlink() in forteseq2.js now sends
`outlet(4, ["gecho", "enlace", linkMin])` on the same FS2_G_ECHO channel the rest of the sidebar
echo already uses. Like Set before it, the real widget (`fs2p_enlace`, live.numbox, range 0-6,
longname "Enlace Tonos") lives INSIDE fs2pages.maxpat (obj-385, reached from FORTESEQ2.amxd's root
as the bpatcher path "obj-484::obj-385"), not the root patcher -- so this needs its OWN `receive
FS2_G_ECHO` inside that file, same shape as add_fs2_set_echo_sync.py's fs2_set receiver.

    python tools/add_fs2_enlace_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_enlace_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only -- no FORTESEQ2.amxd change needed)

New `receive FS2_G_ECHO` -> `route enlace` -> `prepend set` -> `fs2p_enlace` (obj-385).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
TARGET_ID = 'obj-385'   # fs2p_enlace


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}
	assert TARGET_ID in bx and bx[TARGET_ID].get('varname') == 'fs2p_enlace'
	assert not any(b['box'].get('varname') == 'fs2_enlace_gecho_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_enlace_gecho_rx', 'patching_rect': [900.0, 4050.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
		'outlettype': ['', ''], 'varname': 'fs2_enlace_gecho_route',
		'patching_rect': [900.0, 4080.0, 160.0, 20.0], 'text': 'route enlace'}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	prep_id = fresh()
	pg['boxes'].append({'box': {
		'id': prep_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_enlace_gecho_setrx', 'patching_rect': [900.0, 4110.0, 160.0, 22.0],
		'text': 'prepend set'}})
	pg['lines'].append({'patchline': {'source': [route_id, 0], 'destination': [prep_id, 0]}})
	pg['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': [TARGET_ID, 0]}})

	print('fs2pages.maxpat: +%s (receive FS2_G_ECHO) -> +%s (route enlace) -> +%s (prepend set) -> %s (fs2p_enlace)'
		  % (recv_id, route_id, prep_id, TARGET_ID))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(PAGES, PAGES + '.before-enlaceechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2 and prep_id in bx2

	print('\nescrito %s (.before-enlaceechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
