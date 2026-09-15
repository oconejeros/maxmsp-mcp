"""Wire Run (obj-18, live.toggle, "Arranca y detiene el motor") into the Horizonte popup's
global sidebar, column 1 row 0 -- the one control that bypasses forteseq2.js entirely. Unlike
every other global mirrored in the sidebar (Ind/Filtro/Lock/Dir/Patron/Set/Root/...), Run never
reaches the js engine: obj-18 drives obj-19 (fs2_clock, the metro) and obj-44 (fs2_trig_or)
directly at the Max-patching level. So it needs its own independent read+write path instead of
the usual gecho (engine echo) / querynext (engine->popup) pair.

WRITE (popup click -> the real toggle, not a "set"-only display mirror): there is no engine-side
state that already committed the change, so unlike every gecho target this must actually FIRE
obj-18, the same as a manual click/drag would. A new `route run` is fed by a SECOND cable off the
SAME source (obj-751, the `p fs2_window` box) that already feeds obj-819 (`route gotopage`) -- a
parallel fan-out, not an edit to that already-verified route (see the off-by-one incident recorded
in maxmsp-route-outlet-offbyone: rewiring an EXISTING route's outlet indices is exactly the mistake
to avoid). Its match outlet forwards the raw value straight into obj-18's inlet 0.

READ (obj-18's own state, whether it changed via the panel or via the write path above -- both
loop back here so the popup always shows the truth): a NEW `send FS2_RUN_STATE` off a SECOND cable
from obj-18's outlet 0 (alongside its existing wires to obj-19/obj-44), received INSIDE
`[p fs2_window]` by a NEW `receive FS2_RUN_STATE` -> `prepend hrun` -> fs2hz_ui (obj-2 in that
subpatcher, fs2horizon.js)'s inlet 0. fs2horizon.js's hrun(v) handler mirrors it into
globalState.run, same idiom as hstatus/groot/etc.

    python tools/add_fs2_run_sync.py            dry run, writes nothing
    python tools/add_fs2_run_sync.py --apply    do it (device closed in Max AND Live)

## What changes (FORTESEQ2.amxd only)

Root patcher:
  new `route run`  (fed from obj-751 outlet 0, alongside its existing wire to obj-819)
      match outlet 0 -> obj-18 (fs2_run, "Run" toggle) inlet 0
  new `send FS2_RUN_STATE`  (fed from obj-18 outlet 0, alongside its existing wires to obj-19/obj-44)

Inside `p fs2_window` (obj-751's embedded patcher):
  new `receive FS2_RUN_STATE` -> `prepend hrun` -> obj-2 (fs2hz_ui / fs2horizon.js) inlet 0
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

ROOT_RUN_TOGGLE = 'obj-18'    # fs2_run, live.toggle "Run"
ROOT_WINDOW_BOX = 'obj-751'   # p fs2_window (holds fs2horizon.js + fs2setpick.js)
SUB_JSUI = 'obj-2'            # fs2hz_ui, fs2horizon.js, inside p fs2_window


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	assert ROOT_RUN_TOGGLE in bx and bx[ROOT_RUN_TOGGLE].get('varname') == 'fs2_run'
	assert ROOT_WINDOW_BOX in bx and bx[ROOT_WINDOW_BOX].get('text') == 'p fs2_window'
	win_patcher = bx[ROOT_WINDOW_BOX]['patcher']
	sub_boxes = win_patcher['boxes']
	sub_bx = {b['box']['id']: b['box'] for b in sub_boxes}
	assert SUB_JSUI in sub_bx and sub_bx[SUB_JSUI].get('filename') == 'fs2horizon.js'
	assert not any(b['box'].get('varname') == 'fs2_run_route' for b in P['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	# --- write path: root level, `route run` fed in parallel off obj-751's own outlet ---------
	route_id = fresh()
	P['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
		'outlettype': ['', ''], 'varname': 'fs2_run_route',
		'patching_rect': [2400.0, 3450.0, 100.0, 20.0], 'text': 'route run'}})
	P['lines'].append({'patchline': {'source': [ROOT_WINDOW_BOX, 0], 'destination': [route_id, 0]}})
	P['lines'].append({'patchline': {'source': [route_id, 0], 'destination': [ROOT_RUN_TOGGLE, 0]}})

	# --- read path: root level, `send FS2_RUN_STATE` fed in parallel off obj-18's own outlet ---
	send_id = fresh()
	P['boxes'].append({'box': {
		'id': send_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
		'varname': 'fs2_run_state_tx', 'patching_rect': [2400.0, 3480.0, 130.0, 20.0],
		'text': 'send FS2_RUN_STATE'}})
	P['lines'].append({'patchline': {'source': [ROOT_RUN_TOGGLE, 0], 'destination': [send_id, 0]}})

	# --- read path: inside [p fs2_window], receive + prepend hrun -> fs2hz_ui inlet 0 ----------
	nid_sub = [max(int(i.split('-')[1]) for i in sub_bx)]

	def fresh_sub():
		nid_sub[0] += 1
		return 'obj-%d' % nid_sub[0]

	recv_id = fresh_sub()
	sub_boxes.append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_run_state_rx', 'patching_rect': [900.0, 5150.0, 150.0, 20.0],
		'text': 'receive FS2_RUN_STATE'}})
	prep_id = fresh_sub()
	sub_boxes.append({'box': {
		'id': prep_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_run_state_prep', 'patching_rect': [900.0, 5180.0, 100.0, 20.0],
		'text': 'prepend hrun'}})
	win_patcher['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [prep_id, 0]}})
	win_patcher['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': [SUB_JSUI, 0]}})

	print('FORTESEQ2.amxd (root): +%s (route run, fed from %s outlet 0 alongside obj-819) -> %s (fs2_run toggle)'
		  % (route_id, ROOT_WINDOW_BOX, ROOT_RUN_TOGGLE))
	print('FORTESEQ2.amxd (root): +%s (send FS2_RUN_STATE, fed from %s outlet 0 alongside obj-19/obj-44)'
		  % (send_id, ROOT_RUN_TOGGLE))
	print('FORTESEQ2.amxd (p fs2_window): +%s (receive FS2_RUN_STATE) -> +%s (prepend hrun) -> %s (fs2hz_ui)'
		  % (recv_id, prep_id, SUB_JSUI))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-runsync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert route_id in bx2 and send_id in bx2

	print('\nescrito %s (.before-runsync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
