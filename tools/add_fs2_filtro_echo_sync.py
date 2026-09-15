"""Wire the reverse echo for the Filtro cluster (n min/n max, Modo Mask, Mask k, Mask Fit) -- the
Horizonte popup's new sidebar column 4, drawn only while Flt is on. forteseq2.js's setcardmin()/
setcardmax()/setmaskmode()/setmaskk()/setmaskfit() already got outlet(4, ["gecho", tok, value])
echoes added; this script wires the write side so a click in the popup actually reaches the real
panel widgets.

All five real widgets live INSIDE fs2pages.maxpat (same as Set and Enlace before them, reached
from FORTESEQ2.amxd's root as bpatcher paths "obj-484::obj-32" etc.), not the root patcher -- so
this needs its own `receive FS2_G_ECHO` inside that file, same shape as
add_fs2_set_echo_sync.py / add_fs2_enlace_echo_sync.py.

    python tools/add_fs2_filtro_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_filtro_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only -- no FORTESEQ2.amxd change needed)

New `receive FS2_G_ECHO` -> `route nmin nmax maskmode maskk maskfit` (5 args/6 outlets) ->
  5x `prepend set` ->
  nmin     -> obj-32 (fs2_nmin,     live.numbox "n min",     range 1-12)
  nmax     -> obj-36 (fs2_nmax,     live.numbox "n max",     range 1-12)
  maskmode -> obj-66 (fs2_maskmode, live.tab    "Modo Mask", enum Sub/Con/Int)
  maskk    -> obj-67 (fs2_maskk,    live.numbox "Mask k",    range 1-12)
  maskfit  -> obj-68 (fs2_maskfit,  live.toggle "Mask Fit")
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

TARGETS = [
	('nmin', 'obj-32', 'fs2_nmin', 'n min'),
	('nmax', 'obj-36', 'fs2_nmax', 'n max'),
	('maskmode', 'obj-66', 'fs2_maskmode', 'Modo Mask'),
	('maskk', 'obj-67', 'fs2_maskk', 'Mask k'),
	('maskfit', 'obj-68', 'fs2_maskfit', 'Mask Fit'),
]


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}

	for tok, tid, varname, label in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s / %s)' % (tid, tok, label)
	assert not any(b['box'].get('varname') == 'fs2_filtro_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_filtro_echo_rx', 'patching_rect': [900.0, 4150.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(tok for tok, _, _, _ in TARGETS)
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': 6, 'numoutlets': 6,
		'outlettype': ['', '', '', '', '', ''], 'varname': 'fs2_filtro_echo_route',
		'patching_rect': [900.0, 4180.0, 320.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, label) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [900.0 + 150.0 * i, 4210.0, 140.0, 22.0],
			'text': 'prepend set'}})
		pg['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
		pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, label))

	print('fs2pages.maxpat: +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, route_id, route_toks))
	for tok, pid, target, label in new_ids:
		print('  %s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, label))
	print('  boxes nuevos: %d' % (2 + len(new_ids)))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(PAGES, PAGES + '.before-filtroechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-filtroechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
