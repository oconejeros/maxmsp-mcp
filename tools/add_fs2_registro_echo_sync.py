"""Ola 4, primera mitad: eco inverso para Sec Raiz y Oct Maestra -- los dos controles de la nueva
columna 1 (fs2horizon.js, filas 9-10) cuyo widget vive en el patcher RAIZ (FORTESEQ2.amxd), no en
fs2pages.maxpat. Drum/Pad/Rotacion/Rotar x Cambio/Salto Coprimo van en
tools/add_fs2_recorrido_echo_sync.py (fs2pages.maxpat) -- la division es por ARCHIVO porque un
`receive` no puede entregar a un `prepend set` que este en otro patcher.

forteseq2.js ya manda `outlet(4, ["gecho", <token>, <valor>])` al final de setrootseq/
setmasteroctave; esto cablea el lado que hace que un arrastre/click en el popup mueva el widget
real del panel.

    python tools/add_fs2_registro_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_registro_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/FORTESEQ2.amxd only)

New `receive FS2_G_ECHO` -> `route rootseq octm` -> 2x `prepend set` ->
  rootseq -> obj-665 (fs2_rseq2, live.menu   "Sec Raiz",     Raiz fija/Cuartas/.../Azar)
  octm    -> obj-668 (fs2_octm,  live.numbox "Oct Maestra",  -5..5)

Receptor NUEVO e independiente: el patcher raiz ya tiene varios `receive FS2_G_ECHO` propios
(add_fs2_global_echo_sync.py, add_fs2_subhuman_echo_sync.py, add_fs2_rarm_echo_sync.py,
add_fs2_favoritos_echo_sync.py, ...) y a NINGUNO se le toca el `route` -- agregar un token a uno
existente corre todos los indices posteriores y el reject deja de ser el ultimo
(maxmsp-route-outlet-offbyone, el incidente que inundo la consola). Varios `receive` con el mismo
nombre reciben todos una copia.

Nota: `rootseq`/`octm` NO son los tokens bare reservados en obj-403 (`rootseq` SI esta reservado
ahi, sin cablear -- ver la auditoria de la Ola 2). Se ignora a proposito, mismo criterio que Ola 3
con `fav`: todo lo nuevo entra por el canal gecho generico, nunca por esos slots.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

ROOTSEQ_ENUM = ['Raiz fija', 'Cuartas', 'Quintas', '3as m', '3as M', 'Tonos', 'Cromatica',
	'Tritono', 'I IV V', 'Azar']

# (token, id, varname, longname esperado, mmax esperado, enum esperado o None)
TARGETS = [
	('rootseq', 'obj-665', 'fs2_rseq2', 'Sec Raiz', 9, ROOTSEQ_ENUM),
	('octm', 'obj-668', 'fs2_octm', 'Oct Maestra', 5.0, None),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	# regla 5 del plan: verificar el widget real antes de cablear.
	for tok, tid, varname, longname, mmax, enum in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s)' % (tid, tok)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
		assert sa.get('parameter_mmax') == mmax, '%s: mmax %r != %r' % (tok, sa.get('parameter_mmax'), mmax)
		if enum is not None:
			assert sa.get('parameter_enum') == enum, '%s: enum %r != %r' % (tok, sa.get('parameter_enum'), enum)
	assert not any(b['box'].get('varname') == 'fs2_registro_echo_rx' for b in P['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_registro_echo_rx', 'patching_rect': [1500.0, 1810.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	P['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_registro_echo_route',
		'patching_rect': [1500.0, 1840.0, 200.0, 20.0], 'text': 'route ' + route_toks}})
	P['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mx, _en) in enumerate(TARGETS):
		pid = fresh()
		P['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1500.0 + 170.0 * i, 1870.0, 150.0, 22.0],
			'text': 'prepend set'}})
		P['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
		P['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, longname))

	print('FORTESEQ2.amxd: +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, route_id, route_toks))
	for tok, pid, target, longname in new_ids:
		print('  %-8s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, longname))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-registroechosync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-registroechosync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
