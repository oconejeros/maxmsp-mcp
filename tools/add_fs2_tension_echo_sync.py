"""Ola 3, primera mitad: eco inverso para Tension/Curva Tension/Modelo Tension -- los tres controles
de la columna Camino (fs2horizon.js) cuyo widget vive en fs2pages.maxpat. Prog Favoritos/Solo Fav/
Fav van en tools/add_fs2_favoritos_echo_sync.py (FORTESEQ2.amxd, patcher raiz) -- la division es por
ARCHIVO porque un `receive` no puede entregar a un `prepend set` que este en otro patcher.

forteseq2.js ya manda `outlet(4, ["gecho", <token>, <valor>])` al final de settension/settenshape/
settensmodel; esto cablea el lado que hace que un arrastre/click en el popup mueva el widget real
del panel.

Curva y Modelo son los dos casos simples: sus live.menu tienen el INDICE = VALOR (a diferencia de
Sub, ver add_fs2_subhuman_echo_sync.py), asi que el token viaja tal cual.

    python tools/add_fs2_tension_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_tension_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only)

New `receive FS2_G_ECHO` -> `route tension curva tensmodel` -> 3x `prepend set` ->
  tension    -> obj-387 (fs2p_tension,   live.numbox "Tension",        0-16)
  curva      -> obj-389 (fs2p_curva,     live.menu   "Curva Tension",  Sube/Baja/Arco)
  tensmodel  -> obj-391 (fs2p_tensmodel, live.menu   "Modelo Tension", Huron/McKay)

Receptor NUEVO e independiente, no un token agregado al `route` de otro receptor: agregar un token
corre todos los indices posteriores y el reject deja de ser el ultimo (maxmsp-route-outlet-offbyone).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

# (token, id, varname, longname esperado, mmax esperado, enum esperado o None)
TARGETS = [
	('tension', 'obj-387', 'fs2p_tension', 'Tension', 16.0, None),
	('curva', 'obj-389', 'fs2p_curva', 'Curva Tension', 2, ['Sube', 'Baja', 'Arco']),
	('tensmodel', 'obj-391', 'fs2p_tensmodel', 'Modelo Tension', 1, ['Huron', 'McKay']),
]


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}

	# regla 5 del plan: verificar el widget real antes de cablear. Cablear al equivocado no da
	# error, simplemente no funciona (fue lo que paso con Vel Arm vs Ritmo Arm).
	for tok, tid, varname, longname, mmax, enum in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s)' % (tid, tok)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
		assert sa.get('parameter_mmax') == mmax, '%s: mmax %r != %r' % (tok, sa.get('parameter_mmax'), mmax)
		if enum is not None:
			assert sa.get('parameter_enum') == enum, '%s: enum %r != %r' % (tok, sa.get('parameter_enum'), enum)
	assert not any(b['box'].get('varname') == 'fs2_tension_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_tension_echo_rx', 'patching_rect': [1080.0, 4460.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_tension_echo_route',
		'patching_rect': [1080.0, 4490.0, 260.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mx, _en) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1080.0 + 150.0 * i, 4520.0, 140.0, 22.0],
			'text': 'prepend set'}})
		pg['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
		pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, longname))

	print('fs2pages.maxpat: +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, route_id, route_toks))
	for tok, pid, target, longname in new_ids:
		print('  %-9s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, longname))
	print('  boxes nuevos: %d' % (2 + len(new_ids)))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(PAGES, PAGES + '.before-tensionechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-tensionechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
