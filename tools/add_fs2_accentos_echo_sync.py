"""Ola 2: eco inverso para la columna Acentos del sidebar del popup Horizonte (Ciclo/Tie, Euclid+
Pulsos+Giro, VelMin/VelMax/Figura Normal+Acento) -- vive entero en fs2pages.maxpat, como toda la
columna Groove de la Ola 1.

forteseq2.js ya manda `outlet(4, ["gecho", <token>, <valor>])` al final de setaccentcycle/
setaccenttie/seteuclid/seteuclidk/seteuclidrot/setgroupvelmin/setgroupvelmax/setgroupdur; esto
cablea el lado que hace que un arrastre/click en el popup mueva el widget real del panel.

Receptor NUEVO e independiente, no un token agregado al `route` de otro receptor: agregar un token
corre todos los indices posteriores y el reject deja de ser el ultimo (maxmsp-route-outlet-offbyone).

    python tools/add_fs2_accentos_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_accentos_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only)

New `receive FS2_G_ECHO` -> `route ciclo tie euc eupuls eugir velminn velmina velmaxn velmaxa fign figa` ->
  11x `prepend set` ->
  ciclo    -> obj-80  (fs2_ciclo,   live.numbox "Ciclo Acentos", 1-16)
  tie      -> obj-90  (fs2_tie,     live.toggle "Ciclo igual a n")
  euc      -> obj-99  (fs2_euc,     live.toggle "Euclid")
  eupuls   -> obj-108 (fs2_puls,    live.numbox "Pulsos",  0-16)
  eugir    -> obj-115 (fs2_gir,     live.numbox "Giro",    0-15)
  velminn  -> obj-87  (fs2_vmin_n,  live.numbox "Vel Min Normal")
  velmina  -> obj-86  (fs2_vmin_a,  live.numbox "Vel Min Acento")
  velmaxn  -> obj-94  (fs2_vmax_n,  live.numbox "Vel Max Normal")
  velmaxa  -> obj-95  (fs2_vmax_a,  live.numbox "Vel Max Acento")
  fign     -> obj-104 (fs2_fig_n,   live.numbox "Figura Normal", 1-32)
  figa     -> obj-105 (fs2_fig_a,   live.numbox "Figura Acento", 1-32)

setgroupvelmin/setgroupvelmax/setgroupdur toman el indice de grupo como primer argumento, asi que
su eco usa UN TOKEN POR INDICE (velminn/velmina, velmaxn/velmaxa, fign/figa) -- el canal gecho es
"un token, un valor" y no sabe de argumentos extra. Mismo precedente que g0silence/g1silence/
ratn/rata.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

# (token, id, varname, longname esperado, mmin o None, mmax o None)
TARGETS = [
	('ciclo', 'obj-80', 'fs2_ciclo', 'Ciclo Acentos', 1.0, 16.0),
	('tie', 'obj-90', 'fs2_tie', 'Ciclo igual a n', None, 1),
	('euc', 'obj-99', 'fs2_euc', 'Euclid', None, 1),
	('eupuls', 'obj-108', 'fs2_puls', 'Pulsos', None, 16.0),
	('eugir', 'obj-115', 'fs2_gir', 'Giro', None, 15.0),
	('velminn', 'obj-87', 'fs2_vmin_n', 'Vel Min Normal', 1.0, None),
	('velmina', 'obj-86', 'fs2_vmin_a', 'Vel Min Acento', 1.0, None),
	('velmaxn', 'obj-94', 'fs2_vmax_n', 'Vel Max Normal', 1.0, None),
	('velmaxa', 'obj-95', 'fs2_vmax_a', 'Vel Max Acento', 1.0, None),
	('fign', 'obj-104', 'fs2_fig_n', 'Figura Normal', 1.0, 32.0),
	('figa', 'obj-105', 'fs2_fig_a', 'Figura Acento', 1.0, 32.0),
]


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}

	# regla 5 del plan: verificar el widget real antes de cablear. Cablear al equivocado no da
	# error, simplemente no funciona (fue lo que paso con Vel Arm vs Ritmo Arm).
	for tok, tid, varname, longname, mmin, mmax in TARGETS:
		assert tid in bx and bx[tid].get('varname') == varname, 'no coincide %s (%s)' % (tid, tok)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
		if mmin is not None:
			assert sa.get('parameter_mmin') == mmin, '%s: mmin %r != %r' % (tok, sa.get('parameter_mmin'), mmin)
		if mmax is not None:
			assert sa.get('parameter_mmax') == mmax, '%s: mmax %r != %r' % (tok, sa.get('parameter_mmax'), mmax)
	assert not any(b['box'].get('varname') == 'fs2_accentos_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_accentos_echo_rx', 'patching_rect': [1080.0, 4350.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_accentos_echo_route',
		'patching_rect': [1080.0, 4380.0, 560.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mn, _mx) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1080.0 + 150.0 * i, 4410.0, 140.0, 22.0],
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

	shutil.copyfile(PAGES, PAGES + '.before-accentosechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-accentosechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
