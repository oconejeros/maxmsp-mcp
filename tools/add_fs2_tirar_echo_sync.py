"""Tirar (col 9, Sesion): eco inverso para los tres toggles Rnd Set / Rnd Sil / Rnd Acc.

forteseq2.js manda `gecho rndset|rndsil|rndacc` desde setrndset/setrndsil/setrndacc (su efecto vive
en el motor: randomizeall() los lee), asi que `prepend set` alcanza -- no como Sub, cuyo efecto
cuelga de la salida del widget. Receptor NUEVO en el patcher raiz (no se toca ningun route).
(Rnd Sil sortea la MASCARA; el nombre del panel es historico.)

    python tools/add_fs2_tirar_echo_sync.py            dry run
    python tools/add_fs2_tirar_echo_sync.py --apply    (device cerrado en Max Y Live)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

# (token, id, varname, longname esperado)
TARGETS = [
	('rndset', 'obj-728', 'fs2_obj-728', 'Rnd Set'),
	('rndsil', 'obj-726', 'fs2_obj-726', 'Rnd Sil'),
	('rndacc', 'obj-727', 'fs2_obj-727', 'Rnd Acc'),
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
	assert not any(b['box'].get('varname') == 'fs2_tirar_echo_rx' for b in P['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_tirar_echo_rx', 'patching_rect': [1500.0, 1670.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1
	route_id = fresh()
	P['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_tirar_echo_route',
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

	shutil.copyfile(DEVICE, DEVICE + '.before-tirarechosync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-tirarechosync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
