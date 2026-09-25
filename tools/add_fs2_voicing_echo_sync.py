"""Ola 9: eco inverso para Voicing y Conduccion (col. 2 filas 9-10 del popup).

forteseq2.js setvoicing()/setvoicelead() ahora mandan `outlet(4, ["gecho", "voicing"|"cond", <valor>])`;
esto cablea el lado que hace que un click en el popup mueva el widget real del panel. NO se reusa el
outlet `voicing`/`voicelead` de obj-403 -> obj-138 (route -> el widget directo): un live.menu que recibe
un int SALE por su outlet, y ese camino volveria a llamar setvoicing (lazo). `prepend set` no re-dispara.

Reparto (`stackmode`) es una accion sin estado (regla 8): el motor ya ecoa v#grado por onecho y el
popup lo lee de `vkey`, asi que no necesita receptor.

    python tools/add_fs2_voicing_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_voicing_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only)

New `receive FS2_G_ECHO` -> `route voicing cond` -> 2x `prepend set` ->
  voicing -> obj-139 (fs2_voic, live.menu "Voicing", Extendido/Cerrado/Drop 2/Drop 3/Drop 2+4/Abierto)
  cond    -> obj-150 (fs2_cond,  live.toggle "Conduccion")

Receptor NUEVO e independiente, no un token agregado al `route` de otro receptor (regla 1,
maxmsp-route-outlet-offbyone).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

# (token, id, varname, longname esperado, mmax esperado, enum esperado o None)
TARGETS = [
	('voicing', 'obj-139', 'fs2_voic', 'Voicing', 5, ['Extendido', 'Cerrado', 'Drop 2', 'Drop 3', 'Drop 2+4', 'Abierto']),
	('cond', 'obj-150', 'fs2_cond', 'Conduccion', 1, None),
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
	assert not any(b['box'].get('varname') == 'fs2_voicing_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_voicing_echo_rx', 'patching_rect': [1080.0, 6650.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_voicing_echo_route',
		'patching_rect': [1080.0, 6680.0, 260.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mx, _en) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1080.0 + 150.0 * i, 6710.0, 140.0, 22.0],
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

	shutil.copyfile(PAGES, PAGES + '.before-voicingechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-voicingechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
