"""Full revert of add_fs2_global_echo_sync.py (partially already undone by
fix_fs2_harmrate_echo_mismatch.py for the harmrate leg only). The whole approach turned out to be
broken, not just the harmrate range mismatch: the 9 remaining targets (Indep/Filtro/Lock/Dir/Root/
OrnTipo/OrnNotas/OrnBase/OrnBaseModo) are genuine Live device PARAMETERS (parameter_enable=1),
and a live console left open on the running device showed a CONTINUOUS, ongoing flood of
"live.numbox: bad arguments for message set" that persisted even after the harmrate leg alone was
removed -- meaning a parameter-bound live.numbox/live.toggle/live.menu re-fires its outlet on a
plain "set" message (unlike a non-parameter UI object, which the per-voice onecho/advecho/rtecho
echoes target and which do NOT re-fire). That turns every one of these 9 remaining legs into the
same engine -> gecho -> widget -> widget's own pre-existing "prepend setX" -> engine -> gecho -> ...
loop the harmrate leg hit, just without necessarily an out-of-range value to make it visibly error
every cycle -- confirmed as an ACTIVE, ongoing loop on the live device, not a load-time-only burst.

This removes the entire mechanism rather than trying to fix it: reverse-syncing a Live-parameter-
bound widget needs a different approach (likely the Live API / live.object, not a raw "set"
message) -- out of scope for this fix, whose only goal is to get back to a stable, non-looping
device.

    python tools/revert_fs2_global_echo_sync.py            dry run, writes nothing
    python tools/revert_fs2_global_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (FORTESEQ2.amxd only)

  * obj-403: drops the trailing " gecho" token, numoutlets 32->31, numinlets 31->30 (back to the
    rtecho-terminated state from before add_fs2_global_echo_sync.py).
  * Removes obj-821 (send FS2_G_ECHO), obj-822 (receive FS2_G_ECHO), obj-823 (the route
    indep/filtro/lock/dir/root/.../ornbasemode), and the remaining "prepend set" relay boxes
    (obj-824..828, obj-830..833 -- obj-829/harmrate is already gone) plus every patchline touching
    them.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

ROUTE_ID = 'obj-403'
REMOVE_IDS = {
	'obj-821', 'obj-822', 'obj-823',
	'obj-824', 'obj-825', 'obj-826', 'obj-827', 'obj-828',
	'obj-830', 'obj-831', 'obj-832', 'obj-833',
}


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	route403 = bx[ROUTE_ID]
	assert route403['text'].split()[-1] == 'gecho', 'ya aplicado (obj-403 no termina en gecho)'
	present = [i for i in REMOVE_IDS if i in bx]
	assert present, 'ya aplicado (ninguna de las cajas gecho existe)'

	route403['text'] = route403['text'].rsplit(' ', 1)[0]
	route403['numoutlets'] = 31
	route403['numinlets'] = 30

	P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in REMOVE_IDS]
	before_lines = len(P['lines'])
	P['lines'] = [l for l in P['lines']
		if l['patchline']['source'][0] not in REMOVE_IDS
		and l['patchline']['destination'][0] not in REMOVE_IDS]
	removed_lines = before_lines - len(P['lines'])

	print('FORTESEQ2.amxd: %s -> "%s" (32->31 outlets)' % (ROUTE_ID, route403['text']))
	print('  removidas %d cajas: %s' % (len(present), ', '.join(sorted(present))))
	print('  removidos %d cables' % removed_lines)

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-gechorevert')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert bx2[ROUTE_ID]['numoutlets'] == 31
	for i in REMOVE_IDS:
		assert i not in bx2

	print('\nescrito %s (.before-gechorevert guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, remover el device de la pista y volver a arrastrarlo')


main()
