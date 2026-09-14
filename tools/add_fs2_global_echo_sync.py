"""Wire a reverse echo for the "global" (no per-voice index) parameters the Horizonte popup's
fixed left sidebar can now write to: Ind, Filtro, Lock, Dir, Root, R.Arm (harmRate), Orn Tipo,
Orn Notas (count), Orn Base (interval), Orn Base Modo. forteseq2.js's setvoiceindep()/setfilter()/
setlock()/setreaddir()/setroot()/setharmrate()/setorntype()/setorncount()/setornbaseinterval()/
setornbasemode() already got a new outlet(4, ["gecho", "<token>", value]) echo added this session
-- this script wires the RECEIVING side in FORTESEQ2.amxd so the corresponding PANEL widget
(live.toggle/live.numbox/live.menu) updates too, not just the popup.

Root cause this fixes: these setters already had a proven, working panel->engine path (a real
live.toggle/live.numbox/live.menu already sends "prepend setX" into the engine) -- but NOTHING
sent the engine's current value back OUT to that same widget. So the panel's own control driving
itself always looked right (native widget behavior needs no echo), while the SAME setter called
from the popup changed the engine (and the sound) correctly but left the panel widget stale --
exactly the "works from device to popup, not popup to device" asymmetry reported after testing.
This mirrors the onecho/advecho/rtecho per-voice echoes already in this codebase, just for
globals (no voice index) and pointed at the PANEL widgets instead of a popup jsui.

    python tools/add_fs2_global_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_global_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (FORTESEQ2.amxd only, all in the root patcher)

  * obj-403 (the big top-level `route`, currently 30 args/31 outlets ending in
    `...onecho advecho rtecho`) gains one more arg, `gecho` (31 args/32 outlets), wired to a new
    `send FS2_G_ECHO` box (mirrors obj-817/818/820).
  * New `receive FS2_G_ECHO` -> `route indep filtro lock dir root harmrate orntype orncount
    ornbase ornbasemode` (10 args/11 outlets) -> 10x `prepend set` -> the widget each token
    targets:
      indep       -> obj-565 (fs2_g_indep,  live.toggle "Indep")
      filtro      -> obj-569 (fs2_g_filtro, live.toggle "Filtro")
      lock        -> obj-573 (fs2_g_lock,   live.toggle "Lock")
      dir         -> obj-398 (fs2_dir,      live.menu "Dir")
      root        -> obj-700 (fs2_root_g,   live.numbox "Root")
      harmrate    -> obj-480 (fs2_rate2,    live.numbox "Vel Arm" / R.Arm)
      orntype     -> obj-762 (fs2_obj_762,  live.menu "Tipo")
      orncount    -> obj-764 (fs2_obj_764,  live.numbox "Notas")
      ornbase     -> obj-760 (fs2_obj_760,  live.numbox "Base")
      ornbasemode -> obj-769 (fs2_obj_769,  live.menu "B.Modo")
    "prepend set" -> a UI object silently updates its display without re-firing its own outlet
    (same safe convention already proven by every onecho/advecho/rtecho receiver in this file),
    so this cannot loop back into the engine.

Patron (readMode) and Set are deliberately NOT included: Patron's panel control (fs2_patlect)
turns out to drive setpermmode (a different, narrower thing), not setreadmode -- there is no
proven panel widget for the global reading order to sync to. Set already previews immediately via
setlockindex()'s own emitSetReadouts() call and was confirmed working bidirectionally already.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

ROUTE_ID = 'obj-403'

# token -> (target box id, target box's own on-screen label, just for the printed summary)
TARGETS = [
	('indep', 'obj-565', 'Indep'),
	('filtro', 'obj-569', 'Filtro'),
	('lock', 'obj-573', 'Lock'),
	('dir', 'obj-398', 'Dir'),
	('root', 'obj-700', 'Root'),
	('harmrate', 'obj-480', 'R.Arm'),
	('orntype', 'obj-762', 'Orn Tipo'),
	('orncount', 'obj-764', 'Orn Notas'),
	('ornbase', 'obj-760', 'Orn Base'),
	('ornbasemode', 'obj-769', 'Orn B.Modo'),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	route403 = bx[ROUTE_ID]
	assert route403['text'].split()[-1] != 'gecho', 'ya aplicado'
	assert route403['numoutlets'] == 31, 'esperaba 31 outlets (v1range..rtecho), encontre %d' % route403['numoutlets']

	for tok, tid, label in TARGETS:
		assert tid in bx, 'falta el widget %s (%s / %s)' % (tid, tok, label)

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	# --- obj-403: +1 arg, +1 outlet (and +1 inlet, matching this file's established route
	# convention from onecho/advecho/rtecho -- Max re-derives the real route inlet/outlet count
	# from the object text at load time regardless of the saved numinlets/numoutlets hint) -------
	route403['text'] = route403['text'] + ' gecho'
	route403['numoutlets'] = 32
	route403['numinlets'] = 31

	send_id = fresh()
	P['boxes'].append({'box': {
		'id': send_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
		'patching_rect': [2880.0, 3300.0, 140.0, 20.0], 'text': 'send FS2_G_ECHO'}})
	P['lines'].append({'patchline': {'source': [ROUTE_ID, 31], 'destination': [send_id, 0]}})

	# --- receive + route + 10x prepend set -> the 10 panel widgets --------------------------
	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_g_echo_rx', 'patching_rect': [2880.0, 3340.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(tok for tok, _, _ in TARGETS)
	vroute_id = fresh()
	P['boxes'].append({'box': {
		'id': vroute_id, 'maxclass': 'newobj', 'numinlets': 11, 'numoutlets': 11,
		'outlettype': [''] * 11, 'varname': 'fs2_g_echo_route',
		'patching_rect': [2880.0, 3370.0, 420.0, 20.0], 'text': 'route ' + route_toks}})
	P['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [vroute_id, 0]}})

	new_ids = []
	for i, (tok, target, label) in enumerate(TARGETS):
		pid = fresh()
		P['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_g_%s_setrx' % tok,
			'patching_rect': [2880.0 + 150.0 * i, 3400.0, 140.0, 22.0],
			'text': 'prepend set'}})
		P['lines'].append({'patchline': {'source': [vroute_id, i], 'destination': [pid, 0]}})
		P['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, label))

	print('FORTESEQ2.amxd: %s -> "%s" (31->32 outlets), +%s (send FS2_G_ECHO)' % (ROUTE_ID, route403['text'], send_id))
	print('  +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, vroute_id, route_toks))
	for tok, pid, target, label in new_ids:
		print('    %s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, label))
	print('  boxes nuevos: %d' % (2 + len(new_ids)))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-gechosync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert bx2[ROUTE_ID]['numoutlets'] == 32
	assert send_id in bx2
	assert recv_id in bx2 and vroute_id in bx2

	print('\nescrito %s (.before-gechosync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
