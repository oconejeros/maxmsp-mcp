"""Ola 5: eco inverso para el fondo de la columna Filtro del popup Horizonte -- IC1-6 Min/Max (12
numboxes) + Azar % Mask -- vive entero en fs2pages.maxpat, mismo patron que Groove/Acentos.

forteseq2.js ya manda `outlet(4, ["gecho", <token>, <valor>])` al final de setvecmin/setvecmax/
setrandmaskpct; esto cablea el lado que hace que un arrastre en el popup mueva el widget real del
panel. randomizemask() (el boton "Azar Mask") es una accion (regla 8 del plan) y no necesita eco.

Receptor NUEVO e independiente, no un token agregado al `route` de otro receptor: agregar un token
corre todos los indices posteriores y el reject deja de ser el ultimo (maxmsp-route-outlet-offbyone).

    python tools/add_fs2_vecfilt_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_vecfilt_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only)

New `receive FS2_G_ECHO` -> `route vmin1 vmax1 vmin2 vmax2 vmin3 vmax3 vmin4 vmax4 vmin5 vmax5
  vmin6 vmax6 randmaskpct` (13 args/14 outlets) ->
  13x `prepend set` ->
  vmin1..vmin6      -> obj-157/159/163/167/169/170 (fs2_vmn1..fs2_vmn6, live.numbox "IC<k> Min")
  vmax1..vmax6      -> obj-153/158/162/166/168/171 (fs2_vmx1..fs2_vmx6, live.numbox "IC<k> Max")
  randmaskpct       -> obj-372 (fs2_randmaskpct, live.numbox "Azar % Mask", 0-100)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

# (token, id, varname, longname esperado, mmax esperado o None)
TARGETS = [
	('vmin1', 'obj-157', 'fs2_vmn1', 'IC1 Min', None),
	('vmax1', 'obj-153', 'fs2_vmx1', 'IC1 Max', 12.0),
	('vmin2', 'obj-159', 'fs2_vmn2', 'IC2 Min', None),
	('vmax2', 'obj-158', 'fs2_vmx2', 'IC2 Max', 12.0),
	('vmin3', 'obj-163', 'fs2_vmn3', 'IC3 Min', None),
	('vmax3', 'obj-162', 'fs2_vmx3', 'IC3 Max', 12.0),
	('vmin4', 'obj-167', 'fs2_vmn4', 'IC4 Min', None),
	('vmax4', 'obj-166', 'fs2_vmx4', 'IC4 Max', 12.0),
	('vmin5', 'obj-169', 'fs2_vmn5', 'IC5 Min', None),
	('vmax5', 'obj-168', 'fs2_vmx5', 'IC5 Max', 12.0),
	('vmin6', 'obj-170', 'fs2_vmn6', 'IC6 Min', None),
	('vmax6', 'obj-171', 'fs2_vmx6', 'IC6 Max', 12.0),
	('randmaskpct', 'obj-372', 'fs2_randmaskpct', 'Azar % Mask', 100.0),
]


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}

	# regla 5 del plan: verificar el widget real antes de cablear.
	for tok, tid, varname, longname, mmax in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s)' % (tid, tok)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
		if mmax is not None:
			assert sa.get('parameter_mmax') == mmax, '%s: mmax %r != %r' % (tok, sa.get('parameter_mmax'), mmax)
	assert not any(b['box'].get('varname') == 'fs2_vecfilt_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_vecfilt_echo_rx', 'patching_rect': [1260.0, 4350.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_vecfilt_echo_route',
		'patching_rect': [1260.0, 4380.0, 760.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mx) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1260.0 + 130.0 * i, 4410.0, 120.0, 22.0],
			'text': 'prepend set'}})
		pg['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
		pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, longname))

	print('fs2pages.maxpat: +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, route_id, route_toks))
	for tok, pid, target, longname in new_ids:
		print('  %-11s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, longname))
	print('  boxes nuevos: %d' % (2 + len(new_ids)))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(PAGES, PAGES + '.before-vecfiltechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-vecfiltechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
