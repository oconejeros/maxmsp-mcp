"""Wire the reverse echo for the Orn Base sub-mode parameters (Esquema Cuarteto, Paso, and the 3
Orn Serie fields) -- forteseq2.js's setornquadscheme()/setornbasestep()/setornseriesstart()/
setornseriesstep()/setornseriespeak() already got outlet(4, ["gecho", tok, value]) echoes added
(same round that added the Horizonte popup's col 3 mode-specific rows), but no `route` in the
.amxd ever catches those 5 tokens -- they were silently dropped, so a click in the popup updated
globalState (and the popup's own chip) but never reached the real panel widget. This script closes
that gap.

A separate `receive FS2_G_ECHO` rather than extending an existing route (obj-823, the indep/
filtro/.../patron receiver, or obj-835, the orden/rango/silpre one): multiple receives with the
same name all get a copy of every send, so this adds a fully independent small chain instead of
risking a repeat of the outlet-index mistake documented in maxmsp-route-outlet-offbyone by editing
an already-verified-working route.

    python tools/add_fs2_ornbase_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_ornbase_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (FORTESEQ2.amxd only, root patcher)

New `receive FS2_G_ECHO` -> `route ornquad ornstep ornserstart ornserstep ornserpeak`
  (5 args/6 outlets) -> 5x `prepend set` ->
  ornquad    -> obj-775 (fs2_obj_775, live.menu   "Orn Base Cuarteto",  range 0-2)
  ornstep    -> obj-771 (fs2_obj_771, live.numbox "Orn Base Paso",      range 1-4)
  ornserstart -> obj-778 (fs2_obj_778, live.numbox "Orn Serie Inicio",  range 1-6)
  ornserstep  -> obj-780 (fs2_obj_780, live.numbox "Orn Serie Paso",    range 1-4)
  ornserpeak  -> obj-782 (fs2_obj_782, live.numbox "Orn Serie Pico",    range 1-8)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

TARGETS = [
	('ornquad', 'obj-775', 'Orn Base Cuarteto'),
	('ornstep', 'obj-771', 'Orn Base Paso'),
	('ornserstart', 'obj-778', 'Orn Serie Inicio'),
	('ornserstep', 'obj-780', 'Orn Serie Paso'),
	('ornserpeak', 'obj-782', 'Orn Serie Pico'),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	for tok, tid, label in TARGETS:
		assert tid in bx, 'falta el widget %s (%s / %s)' % (tid, tok, label)
	assert not any(b['box'].get('varname') == 'fs2_ornbase_echo_rx' for b in P['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_ornbase_echo_rx', 'patching_rect': [3220.0, 3520.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(tok for tok, _, _ in TARGETS)
	route_id = fresh()
	P['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': 6, 'numoutlets': 6,
		'outlettype': ['', '', '', '', '', ''], 'varname': 'fs2_ornbase_echo_route',
		'patching_rect': [3220.0, 3550.0, 320.0, 20.0], 'text': 'route ' + route_toks}})
	P['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, label) in enumerate(TARGETS):
		pid = fresh()
		P['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [3220.0 + 150.0 * i, 3580.0, 140.0, 22.0],
			'text': 'prepend set'}})
		P['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
		P['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new_ids.append((tok, pid, target, label))

	print('FORTESEQ2.amxd: +%s (receive FS2_G_ECHO) -> +%s (route %s)' % (recv_id, route_id, route_toks))
	for tok, pid, target, label in new_ids:
		print('  %s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, label))
	print('  boxes nuevos: %d' % (2 + len(new_ids)))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-ornbaseechosync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-ornbaseechosync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
