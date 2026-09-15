"""Ola 1: eco inverso para Modo Toque + la columna Groove del sidebar del popup Horizonte -- la
mitad que vive en fs2pages.maxpat (8 de los 10 controles).

forteseq2.js ya manda `outlet(4, ["gecho", <token>, <valor>])` al final de setmode/setswing/
setstrum/setstrumdir/setratchet/setratchetprob/setratchetdecay; esto cablea el lado que hace que
un arrastre en el popup mueva el widget real del panel.

Sub y Human viven en el patcher RAIZ (FORTESEQ2.amxd), no aca: van en su propio script,
tools/add_fs2_subhuman_echo_sync.py. Un `receive` no puede entregar a un `prepend set` que este
en otro archivo (send/receive cruza limites de patcher, el patchline no), asi que la division es
por archivo, no por familia.

Receptor NUEVO e independiente, no un token agregado al `route` de otro receptor: agregar un token
corre todos los indices posteriores y el reject deja de ser el ultimo (maxmsp-route-outlet-offbyone).

    python tools/add_fs2_groove_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_groove_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only)

New `receive FS2_G_ECHO` -> `route mode swing rasg dirrasg ratn rata ratprob ratcaida` ->
  8x `prepend set` ->
  mode     -> obj-19  (fs2_mode,      live.tab    "Modo",     enum Acordes/Arpegio)
  swing    -> obj-202 (fs2_swing,     live.numbox "Swing",    50-75)
  rasg     -> obj-206 (fs2_rasg,      live.numbox "Rasg",     0-8)
  dirrasg  -> obj-208 (fs2_dirrasg,   live.tab    "Dir Rasg", enum Arriba/Abajo/Azar/Alt)
  ratn     -> obj-210 (fs2_ratn,      live.numbox "Rat N",    1-4)
  rata     -> obj-212 (fs2_rata,      live.numbox "Rat A",    1-4)
  ratprob  -> obj-214 (fs2_ratprob,   live.numbox "Prob Rat", 0-100)
  ratcaida -> obj-216 (fs2_ratcaida,  live.numbox "Caida",    0-100)

setratchet(g, n) toma el indice de grupo como primer argumento, asi que su eco usa UN TOKEN POR
INDICE (ratn/rata) -- el canal gecho es "un token, un valor" y no sabe de argumentos extra. Mismo
precedente que g0silence/g1silence.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

# (token, id, varname, longname esperado, mmin o None, mmax o None)
TARGETS = [
	('mode', 'obj-19', 'fs2_mode', 'Modo', None, 1),
	('swing', 'obj-202', 'fs2_swing', 'Swing', 50.0, 75.0),
	('rasg', 'obj-206', 'fs2_rasg', 'Rasg', None, 8.0),
	('dirrasg', 'obj-208', 'fs2_dirrasg', 'Dir Rasg', None, 3),
	('ratn', 'obj-210', 'fs2_ratn', 'Rat N', 1.0, 4.0),
	('rata', 'obj-212', 'fs2_rata', 'Rat A', 1.0, 4.0),
	('ratprob', 'obj-214', 'fs2_ratprob', 'Prob Rat', None, 100.0),
	('ratcaida', 'obj-216', 'fs2_ratcaida', 'Caida', None, 100.0),
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
	assert not any(b['box'].get('varname') == 'fs2_groove_echo_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_groove_echo_rx', 'patching_rect': [900.0, 4350.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'fs2_groove_echo_route',
		'patching_rect': [900.0, 4380.0, 460.0, 20.0], 'text': 'route ' + route_toks}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, varname, longname, _mn, _mx) in enumerate(TARGETS):
		pid = fresh()
		pg['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [900.0 + 150.0 * i, 4410.0, 140.0, 22.0],
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

	shutil.copyfile(PAGES, PAGES + '.before-grooveechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-grooveechosync guardado). Sigue:' % PAGES)
	print('  python tools/add_fs2_subhuman_echo_sync.py --apply   (la otra mitad, en el patcher raiz)')
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
