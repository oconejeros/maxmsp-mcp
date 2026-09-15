"""Ola 6: eco inverso para la columna Modulacion del popup Horizonte -- 4 moduladores x 5 campos
(Forma/Ciclo/Prof/Fase/Dest), 20 widgets, todos en fs2pages.maxpat, mismo patron que Groove/Acentos/
IC vector.

forteseq2.js ya manda `outlet(4, ["gecho", "m<k><campo>", <valor>])` al final de setmodshape/
setmodcycle/setmoddepth/setmodphase/setmoddest; esto cablea el lado que hace que un arrastre o una
seleccion de dropdown en el popup mueva el widget real del panel.

Receptor NUEVO e independiente, no un token agregado al `route` de otro receptor: agregar un token
corre todos los indices posteriores y el reject deja de ser el ultimo (maxmsp-route-outlet-offbyone).

    python tools/add_fs2_mod_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_mod_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only)

New `receive FS2_G_ECHO` -> `route m1shape m1cycle m1depth m1phase m1dest m2shape m2cycle m2depth
  m2phase m2dest m3shape m3cycle m3depth m3phase m3dest m4shape m4cycle m4depth m4phase m4dest`
  (20 args/21 outlets) ->
  20x `prepend set` ->
  md_m1_forma..md_m4_dest (obj-303/305/307/309/311, obj-314/316/318/320/322,
  obj-325/327/329/331/333, obj-336/338/340/342/344)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

# (token, id, varname, longname esperado, mmax esperado)
TARGETS = [
	('m1shape', 'obj-303', 'md_m1_forma', 'M1 Forma', 5),
	('m1cycle', 'obj-305', 'md_m1_ciclo', 'M1 Ciclo', 64.0),
	('m1depth', 'obj-307', 'md_m1_prof', 'M1 Prof', 100.0),
	('m1phase', 'obj-309', 'md_m1_fase', 'M1 Fase', 100.0),
	('m1dest', 'obj-311', 'md_m1_dest', 'M1 Dest', 11),
	('m2shape', 'obj-314', 'md_m2_forma', 'M2 Forma', 5),
	('m2cycle', 'obj-316', 'md_m2_ciclo', 'M2 Ciclo', 64.0),
	('m2depth', 'obj-318', 'md_m2_prof', 'M2 Prof', 100.0),
	('m2phase', 'obj-320', 'md_m2_fase', 'M2 Fase', 100.0),
	('m2dest', 'obj-322', 'md_m2_dest', 'M2 Dest', 11),
	('m3shape', 'obj-325', 'md_m3_forma', 'M3 Forma', 5),
	('m3cycle', 'obj-327', 'md_m3_ciclo', 'M3 Ciclo', 64.0),
	('m3depth', 'obj-329', 'md_m3_prof', 'M3 Prof', 100.0),
	('m3phase', 'obj-331', 'md_m3_fase', 'M3 Fase', 100.0),
	('m3dest', 'obj-333', 'md_m3_dest', 'M3 Dest', 11),
	('m4shape', 'obj-336', 'md_m4_forma', 'M4 Forma', 5),
	('m4cycle', 'obj-338', 'md_m4_ciclo', 'M4 Ciclo', 64.0),
	('m4depth', 'obj-340', 'md_m4_prof', 'M4 Prof', 100.0),
	('m4phase', 'obj-342', 'md_m4_fase', 'M4 Fase', 100.0),
	('m4dest', 'obj-344', 'md_m4_dest', 'M4 Dest', 11),
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
		assert sa.get('parameter_mmax') == mmax, '%s: mmax %r != %r' % (tok, sa.get('parameter_mmax'), mmax)
	assert not any(b['box'].get('varname') == 'fs2_mod_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_mod_echo_rx', 'patching_rect': [1260.0, 4680.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_mod_echo_route',
		'patching_rect': [1260.0, 4710.0, 1180.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mx) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [1260.0 + 130.0 * i, 4740.0, 120.0, 22.0],
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

	shutil.copyfile(PAGES, PAGES + '.before-modechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-modechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
