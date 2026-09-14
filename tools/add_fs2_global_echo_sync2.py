"""Redo of add_fs2_global_echo_sync.py (reverted by revert_fs2_global_echo_sync.py after a console
flood). The technique itself is sound -- forteseq/forteseqwf.amxd already uses the identical
pattern successfully (engine setter -> outlet(0, "ui", tok, val) -> route demux -> prepend set ->
parameter-bound live.numbox/live.toggle) -- the flood was a plain off-by-one in the FIRST script's
own wiring: it appended "gecho" as obj-403's 31st token but wired the new `send FS2_G_ECHO` box to
outlet 31 (the REJECT outlet) instead of outlet 30 (gecho's real match outlet), so FS2_G_ECHO
received a firehose of unrelated traffic from that shared dispatcher instead of clean gecho
messages. See tools/maxmsp_route_outlet_offbyone.md-equivalent note in memory
(maxmsp-route-outlet-offbyone) for the full incident writeup.

This version also adds Patron (readMode), wrongly excluded the first time: setpermmode() looked
like a separate, narrower function from a skim but is actually a one-line alias that calls
setreadmode() directly -- the panel's RunLec menu (fs2_patlect, live.menu, range 0-7, matches
READ_MAX) is a real, working target for it.

    python tools/add_fs2_global_echo_sync2.py            dry run, writes nothing
    python tools/add_fs2_global_echo_sync2.py --apply    do it (device closed in Max AND Live)

## What changes (FORTESEQ2.amxd only, all in the root patcher)

  * obj-403 (the top-level `route`, currently 30 args/31 outlets ending in `...onecho advecho
    rtecho`, back to this state after the revert) gains one more arg, `gecho` (31 args/32
    outlets) -- new match outlet is index 30 (= the PRE-addition arg count), NOT 31 (numoutlets-1,
    the reject outlet -- that's the bug this script fixes). Wired to a new `send FS2_G_ECHO` box.
  * New `receive FS2_G_ECHO` -> `route indep filtro lock dir root orntype orncount ornbase
    ornbasemode patron` (10 args/11 outlets) -> 10x `prepend set` -> the widget each token
    targets (verified against each widget's own parameter_mmin/mmax this time, not just its
    label):
      indep       -> obj-565 (fs2_g_indep,  live.toggle "Indep")
      filtro      -> obj-569 (fs2_g_filtro, live.toggle "Filtro")
      lock        -> obj-573 (fs2_g_lock,   live.toggle "Lock")
      dir         -> obj-398 (fs2_dir,      live.menu "Dir", range 0-2)
      root        -> obj-700 (fs2_root_g,   live.numbox "Root", range -24..24)
      orntype     -> obj-762 (fs2_obj_762,  live.menu "Tipo", range 0-5)
      orncount    -> obj-764 (fs2_obj_764,  live.numbox "Notas", range 1-4)
      ornbase     -> obj-760 (fs2_obj_760,  live.numbox "Base", range 1-14)
      ornbasemode -> obj-769 (fs2_obj_769,  live.menu "B.Modo", range 0-3)
      patron      -> obj-636 (fs2_patlect,  live.menu "RunLec", range 0-7 -- setpermmode() alias)

R.Arm (harmRate) stays excluded: no real panel widget exists for it (obj-480 "Vel Arm" turned out
to be a different concept, "rate in ms" via wf_rate_ms-equivalent downstream, range 5-260 vs
harmRate's 0-64).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

ROUTE_ID = 'obj-403'

TARGETS = [
	('indep', 'obj-565', 'Indep'),
	('filtro', 'obj-569', 'Filtro'),
	('lock', 'obj-573', 'Lock'),
	('dir', 'obj-398', 'Dir'),
	('root', 'obj-700', 'Root'),
	('orntype', 'obj-762', 'Orn Tipo'),
	('orncount', 'obj-764', 'Orn Notas'),
	('ornbase', 'obj-760', 'Orn Base'),
	('ornbasemode', 'obj-769', 'Orn B.Modo'),
	('patron', 'obj-636', 'Patron (RunLec)'),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	route403 = bx[ROUTE_ID]
	assert route403['text'].split()[-1] != 'gecho', 'ya aplicado'
	assert route403['numoutlets'] == 31, 'esperaba 31 outlets (v1range..rtecho), encontre %d' % route403['numoutlets']
	old_arg_count = len(route403['text'].split()) - 1   # -1 for the "route" keyword itself

	for tok, tid, label in TARGETS:
		assert tid in bx, 'falta el widget %s (%s / %s)' % (tid, tok, label)

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	# --- obj-403: +1 arg, +1 outlet. New token's MATCH outlet = old_arg_count (0-indexed count of
	# args that existed before this addition) -- NOT new_numoutlets-1, which is the reject outlet.
	# This is exactly the bug the first attempt at this had; see maxmsp-route-outlet-offbyone.
	route403['text'] = route403['text'] + ' gecho'
	route403['numoutlets'] = 32
	route403['numinlets'] = 31
	gecho_outlet = old_arg_count
	assert gecho_outlet == 30, 'outlet inesperado: %d (revisar conteo de args)' % gecho_outlet

	send_id = fresh()
	P['boxes'].append({'box': {
		'id': send_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
		'patching_rect': [3040.0, 3300.0, 140.0, 20.0], 'text': 'send FS2_G_ECHO'}})
	P['lines'].append({'patchline': {'source': [ROUTE_ID, gecho_outlet], 'destination': [send_id, 0]}})

	# --- receive + route + 10x prepend set -> the 10 panel widgets --------------------------
	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_g_echo_rx2', 'patching_rect': [3040.0, 3340.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(tok for tok, _, _ in TARGETS)
	vroute_id = fresh()
	P['boxes'].append({'box': {
		'id': vroute_id, 'maxclass': 'newobj', 'numinlets': 11, 'numoutlets': 11,
		'outlettype': [''] * 11, 'varname': 'fs2_g_echo_route2',
		'patching_rect': [3040.0, 3370.0, 460.0, 20.0], 'text': 'route ' + route_toks}})
	P['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [vroute_id, 0]}})

	new_ids = []
	for i, (tok, target, label) in enumerate(TARGETS):
		pid = fresh()
		P['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_g_%s_setrx2' % tok,
			'patching_rect': [3040.0 + 150.0 * i, 3400.0, 140.0, 22.0],
			'text': 'prepend set'}})
		P['lines'].append({'patchline': {'source': [vroute_id, i], 'destination': [pid, 0]}})
		P['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, label))

	print('FORTESEQ2.amxd: %s -> "%s" (31->32 outlets), gecho match outlet = %d'
		  % (ROUTE_ID, route403['text'], gecho_outlet))
	print('  +%s (send FS2_G_ECHO), sourced from %s outlet %d' % (send_id, ROUTE_ID, gecho_outlet))
	print('  +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, vroute_id, route_toks))
	for tok, pid, target, label in new_ids:
		print('    %s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, label))
	print('  boxes nuevos: %d' % (2 + len(new_ids)))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-gechosync2')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert bx2[ROUTE_ID]['numoutlets'] == 32
	assert send_id in bx2
	assert recv_id in bx2 and vroute_id in bx2
	lines2 = [l['patchline'] for l in doc2['patcher']['lines']]
	assert {'source': [ROUTE_ID, gecho_outlet], 'destination': [send_id, 0]} in lines2

	print('\nescrito %s (.before-gechosync2 guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
