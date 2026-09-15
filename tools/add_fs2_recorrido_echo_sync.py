"""Ola 4, segunda mitad: eco inverso para Drum/Pad/Rotacion/Rotar x Cambio/Salto Coprimo -- los
cinco controles de la columna 1 (fs2horizon.js, filas 10-13) cuyo widget vive en fs2pages.maxpat.
Sec Raiz/Oct Maestra van en tools/add_fs2_registro_echo_sync.py (FORTESEQ2.amxd, patcher raiz) --
la division es por ARCHIVO porque un `receive` no puede entregar a un `prepend set` que este en
otro patcher.

forteseq2.js ya manda `outlet(4, ["gecho", <token>, <valor>])` al final de setdrum/setdrumbase/
setshape/setcoprime, y `emitRotationReadout()` (llamada desde setrotation()) convierte lo que
antes era un mensaje bare "rotation" muerto (caia en el reject de obj-403 sin consumidor, ver el
audit de la Ola 4) al mismo canal gecho -- token "rotacion", reutilizando el debounce que ya
existia en vez de sumar un tercer tracker en querynext().

Ya existe en este archivo un `route drum drumbase harmrate rootseq voicing voicelead fav favonly
vecmin vecmax` (obj-138) cableado DIRECTO -- sin `prepend set` -- desde el inlet de eco del propio
bpatcher (obj-2, "eco (salida 4 del js)") hasta fs2_drum/fs2_pad. Es el mismo borrador abandonado
que la Ola 2 encontro del lado del patcher raiz (obj-403): el motor nunca manda los tokens bare
"drum"/"drumbase" que ese route espera, asi que queda muerto a proposito -- no se reutiliza (mandar
un valor RAW en vez de "prepend set" re-dispara el outlet del widget, ver regla 3 del plan).

    python tools/add_fs2_recorrido_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_recorrido_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only)

New `receive FS2_G_ECHO` -> `route drum pad rotacion rotarx salto` -> 5x `prepend set` ->
  drum     -> obj-144 (fs2_drum,      live.toggle "Drum",             0/1)
  pad      -> obj-146 (fs2_pad,       live.numbox "Pad",              0-115)
  rotacion -> obj-403 (fs2p_rotacion, live.numbox "Rotacion",         0-11, wrap mod cardinalidad)
  rotarx   -> obj-406 (fs2p_rotarx,   live.toggle "Rotar x Cambio",   0/1)
  salto    -> obj-400 (fs2p_salto,    live.numbox "Salto Coprimo",    1-11)

Receptor NUEVO e independiente, no un token agregado al `route` de otro receptor (ni al obj-138
muerto de arriba): agregar un token corre todos los indices posteriores y el reject deja de ser el
ultimo (maxmsp-route-outlet-offbyone).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

# (token, id, varname, longname esperado, mmax esperado, mmin esperado o None)
TARGETS = [
	('drum', 'obj-144', 'fs2_drum', 'Drum', 1, None),
	('pad', 'obj-146', 'fs2_pad', 'Pad', 115.0, None),
	('rotacion', 'obj-403', 'fs2p_rotacion', 'Rotacion', 11.0, None),
	('rotarx', 'obj-406', 'fs2p_rotarx', 'Rotar x Cambio', 1, None),
	('salto', 'obj-400', 'fs2p_salto', 'Salto Coprimo', 11.0, 1.0),
]


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}

	# regla 5 del plan: verificar el widget real antes de cablear.
	for tok, tid, varname, longname, mmax, mmin in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s)' % (tid, tok)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
		assert sa.get('parameter_mmax') == mmax, '%s: mmax %r != %r' % (tok, sa.get('parameter_mmax'), mmax)
		if mmin is not None:
			assert sa.get('parameter_mmin') == mmin, '%s: mmin %r != %r' % (tok, sa.get('parameter_mmin'), mmin)
	assert not any(b['box'].get('varname') == 'fs2_recorrido_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_recorrido_echo_rx', 'patching_rect': [1080.0, 4560.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_recorrido_echo_route',
		'patching_rect': [1080.0, 4590.0, 300.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mx, _mn) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1080.0 + 150.0 * i, 4620.0, 140.0, 22.0],
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

	shutil.copyfile(PAGES, PAGES + '.before-recorridoechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-recorridoechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
