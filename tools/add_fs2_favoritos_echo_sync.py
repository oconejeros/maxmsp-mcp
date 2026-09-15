"""Ola 3, segunda mitad: eco inverso para Prog Favoritos/Solo Fav/Fav -- los tres controles de la
columna Camino (fs2horizon.js) cuyo widget vive en el patcher RAIZ (FORTESEQ2.amxd), no en
fs2pages.maxpat. Tension/Curva/Modelo van en tools/add_fs2_tension_echo_sync.py; la division es por
ARCHIVO porque un `receive` no puede entregar a un `prepend set` que este en otro patcher.

forteseq2.js ya manda `outlet(4, ["gecho", <token>, <valor>])` al final de setfavseq/setfavonly/
setfav (este ultimo tanto desde el click explicito como desde el repintado automatico cuando el set
que suena cambia -- ver emitSetReadouts() en forteseq2.js). El motor tenia YA un token bare "fav" en
outlet 4 (obj-403 reserva un outlet de route para el, investigado en la ronda anterior y encontrado
SIN CABLEAR mas alla) -- forteseq2.js lo convirtio a gecho-wrapped en esta misma ola en vez de
cablear ese slot reservado, siguiendo la regla que la auditoria dejo escrita: los tokens reservados
de obj-403 (fav/favonly/harmrate/rootseq/voicing/voicelead/vecmin/vecmax) quedan sin usar a proposito,
todo lo nuevo entra por el canal gecho generico.

    python tools/add_fs2_favoritos_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_favoritos_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/FORTESEQ2.amxd only)

New `receive FS2_G_ECHO` -> `route progfav favonly fav` -> 3x `prepend set` ->
  progfav -> obj-625 (fs2_progfav, live.toggle "Prog Favoritos")
  favonly -> obj-627 (fs2_favonly, live.toggle "Solo Fav")
  fav     -> obj-623 (fs2_fav,     live.toggle "Fav")

Receptor NUEVO e independiente: el patcher raiz ya tiene varios `receive FS2_G_ECHO` propios
(add_fs2_global_echo_sync.py, add_fs2_subhuman_echo_sync.py, add_fs2_rarm_echo_sync.py, ...) y a
NINGUNO se le toca el `route` -- agregar un token a uno existente corre todos los indices
posteriores y el reject deja de ser el ultimo (maxmsp-route-outlet-offbyone, el incidente que
inundo la consola). Varios `receive` con el mismo nombre reciben todos una copia.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

# (token, id, varname, longname esperado)
TARGETS = [
	('progfav', 'obj-625', 'fs2_progfav', 'Prog Favoritos'),
	('favonly', 'obj-627', 'fs2_favonly', 'Solo Fav'),
	('fav', 'obj-623', 'fs2_fav', 'Fav'),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	for tok, tid, varname, longname in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s)' % (tid, tok)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
		assert sa.get('parameter_mmax') == 1, '%s: mmax %r != 1' % (tok, sa.get('parameter_mmax'))
	assert not any(b['box'].get('varname') == 'fs2_favoritos_echo_rx' for b in P['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_favoritos_echo_rx', 'patching_rect': [1500.0, 1670.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1
	route_id = fresh()
	P['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_favoritos_echo_route',
		'patching_rect': [1500.0, 1700.0, 220.0, 20.0], 'text': 'route ' + route_toks}})
	P['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname) in enumerate(TARGETS):
		pid = fresh()
		P['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1500.0 + 170.0 * i, 1730.0, 150.0, 22.0],
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

	shutil.copyfile(DEVICE, DEVICE + '.before-favoritosechosync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-favoritosechosync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
