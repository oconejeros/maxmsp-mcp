"""Wire the reverse echo for Orden/Rango/Preset Silencio -- new global fields for the Horizonte
popup's second sidebar column, added on user request alongside Set/Root/R.Arm. forteseq2.js's
setorder()/setrangetemplate()/setsilencepreset() already got outlet(4, ["gecho", tok, value])
echoes added (orderMode already existed as persistent state; rangeTemplateIndex/
silencePresetIndex are new "what was last applied" records added alongside them, since these two
setters previously had nothing to echo -- see their own comments in forteseq2.js).

A separate `receive FS2_G_ECHO` rather than extending the existing route823 (obj-823, the
indep/filtro/lock/dir/root/orntype/orncount/ornbase/ornbasemode/patron receiver added by
add_fs2_global_echo_sync2.py): multiple receives with the same name all get a copy of every send,
so this adds a fully independent small chain instead of risking a repeat of the outlet-index
mistake documented in maxmsp-route-outlet-offbyone by editing an already-verified-working route.

    python tools/add_fs2_setup_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_setup_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (FORTESEQ2.amxd only, root patcher)

New `receive FS2_G_ECHO` -> `route orden rango silpre` (3 args/4 outlets) -> 3x `prepend set` ->
  orden -> obj-645 (fs2_orden,   live.menu "Orden", range 0-6)
  rango -> obj-620 (fs2_rango,   live.menu "Rango", range 0-8)
  silpre -> obj-703 (fs2_silpre_g, live.menu "Preset Silencio", range 0-5)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

TARGETS = [
	('orden', 'obj-645', 'Orden'),
	('rango', 'obj-620', 'Rango'),
	('silpre', 'obj-703', 'Preset Silencio'),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	for tok, tid, label in TARGETS:
		assert tid in bx, 'falta el widget %s (%s / %s)' % (tid, tok, label)
	assert not any(b['box'].get('varname') == 'fs2_setup_echo_rx' for b in P['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	P['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_setup_echo_rx', 'patching_rect': [3220.0, 3300.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_toks = ' '.join(tok for tok, _, _ in TARGETS)
	route_id = fresh()
	P['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': 4, 'numoutlets': 4,
		'outlettype': ['', '', '', ''], 'varname': 'fs2_setup_echo_route',
		'patching_rect': [3220.0, 3330.0, 200.0, 20.0], 'text': 'route ' + route_toks}})
	P['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	new_ids = []
	for i, (tok, target, label) in enumerate(TARGETS):
		pid = fresh()
		P['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'fs2_%s_setrx' % tok,
			'patching_rect': [3220.0 + 150.0 * i, 3360.0, 140.0, 22.0],
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

	shutil.copyfile(DEVICE, DEVICE + '.before-setupechosync')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert recv_id in bx2 and route_id in bx2

	print('\nescrito %s (.before-setupechosync guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
