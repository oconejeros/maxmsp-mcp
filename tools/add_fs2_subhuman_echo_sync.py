"""Ola 1, segunda mitad: eco inverso para Sub y Human -- los dos unicos controles de la columna
Groove cuyo widget vive en el patcher RAIZ (FORTESEQ2.amxd) y no en fs2pages.maxpat. Los otros
ocho van en tools/add_fs2_groove_echo_sync.py; la division es por ARCHIVO porque un `receive` no
puede entregar a un `prepend set` que este en otro patcher.

## El caso raro: Sub es un live.menu cuyo INDICE no es su valor

`fs2_sub_g` (obj-706) es un live.menu con enum ['1','2','3','4','6','8'] -- valores 0-5. Su salida
pasa por un `sel` + seis message boxes que traducen indice -> divisor antes del `prepend setsub`,
asi que el MOTOR guarda el divisor (1/2/3/4/6/8) y el WIDGET guarda el indice (0-5).

O sea que el eco tiene que ir en indice, no en divisor: mandarle `set 6` al menu seleccionaria un
septimo item que no existe en vez de "sextillo". La conversion la hace setsub() en forteseq2.js
(SUB_MENU/subMenuIndex); este script solo cablea el token `sub` a obj-706 y confia en eso. Es el
primer caso indice != valor del sidebar -- rule 7 del plan.

Human no tiene ninguna vuelta: live.numbox 0-100, mismo valor de los dos lados.

    python tools/add_fs2_subhuman_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_subhuman_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/FORTESEQ2.amxd only)

New `receive FS2_G_ECHO` -> `route sub human` -> 2x `prepend set` ->
  sub   -> obj-706 (fs2_sub_g,   live.menu   "Sub",   enum 1/2/3/4/6/8, INDICE 0-5)
  human -> obj-716 (fs2_human_g, live.numbox "Human", 0-100)

Receptor NUEVO e independiente: el patcher raiz ya tiene un `receive FS2_G_ECHO` con su propio
`route` largo (add_fs2_global_echo_sync.py) y NO se le tocan los tokens -- agregar uno corre todos
los indices posteriores y el reject deja de ser el ultimo (maxmsp-route-outlet-offbyone, el
incidente que inundo la consola). Varios `receive` con el mismo nombre reciben todos una copia.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

# (token, id, varname, longname esperado, mmax esperado)
TARGETS = [
	('sub', 'obj-706', 'fs2_sub_g', 'Sub', 5),
	('human', 'obj-716', 'fs2_human_g', 'Human', 100.0),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	for tok, tid, varname, longname, mmax in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s)' % (tid, tok)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
		assert sa.get('parameter_mmax') == mmax, '%s: mmax %r != %r' % (tok, sa.get('parameter_mmax'), mmax)
	# el enum de Sub es la razon de que el eco vaya en indice; si alguna vez cambia, este assert
	# avisa antes de que el popup empiece a seleccionar el item equivocado en silencio.
	sub_enum = bx['obj-706']['saved_attribute_attributes']['valueof'].get('parameter_enum')
	assert sub_enum == ['1', '2', '3', '4', '6', '8'], 'el enum de Sub cambio: %r' % (sub_enum,)
	assert not any(b['box'].get('varname') == 'fs2_subhuman_echo_rx' for b in P['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_subhuman_echo_rx', 'patching_rect': [1500.0, 1580.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1
	route_id = fresh()
	P['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_subhuman_echo_route',
		'patching_rect': [1500.0, 1610.0, 180.0, 20.0], 'text': 'route ' + route_toks}})
	P['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mx) in enumerate(TARGETS):
		pid = fresh()
		P['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1500.0 + 170.0 * i, 1640.0, 150.0, 22.0],
			'text': 'prepend set'}})
		P['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
		P['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, longname))

	print('FORTESEQ2.amxd: +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, route_id, route_toks))
	for tok, pid, target, longname in new_ids:
		print('  %-6s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, longname))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-subhumanechosync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-subhumanechosync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
