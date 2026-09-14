"""Undo the harmrate leg of add_fs2_global_echo_sync.py -- obj-480 ("Vel Arm" live.numbox) turned
out to be the WRONG target: its Live parameter range is 5-260, while the engine's harmRate is
clamped 0-64. Every gecho echo landed out of range, the parameter-bound numbox rejected it and
re-asserted its own value back out its own outlet, which fed straight back through the existing
"prepend setharmrate" -> engine -> gecho -> ... chain -- a live bidirectional bounce, confirmed by
a live console flooded with "live.numbox: bad arguments for message set" with nothing else
interleaved, and a report that even the previously-working Set sync broke (the engine was likely
saturated servicing the bounce instead of other messages).

There is no other known panel widget for harmRate (same situation as Patron/readMode -- no
"prepend setharmrate" box exists anywhere else in the file), so this just removes the mistaken
wiring rather than repointing it. The other 9 gecho targets (Indep/Filtro/Lock/Dir/Root/OrnTipo/
OrnNotas/OrnBase/OrnBaseModo) were checked against their own parameter_mmin/mmax and all match the
engine variable's own clamp range -- only this one was wrong.

    python tools/fix_fs2_harmrate_echo_mismatch.py            dry run, writes nothing
    python tools/fix_fs2_harmrate_echo_mismatch.py --apply    do it (device closed in Max AND Live)

## What changes (FORTESEQ2.amxd only)

Removes obj-829 (the "prepend set" box add_fs2_global_echo_sync.py put on the harmrate leg) and
its 2 patchlines (obj-823 outlet 5 -> obj-829, obj-829 -> obj-480). obj-823's `route ... harmrate
...` keeps the argument (renumbering the other 9 outlets would be far riskier than leaving one
outlet unconnected) -- the harmrate leg just dead-ends there now, harmless.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

PREPEND_ID = 'obj-829'
ROUTE_ID = 'obj-823'
TARGET_ID = 'obj-480'


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}
	assert PREPEND_ID in bx, 'ya aplicado (obj-829 no existe)'
	assert bx[PREPEND_ID]['text'] == 'prepend set'

	old_lines = [
		{'source': [ROUTE_ID, 5], 'destination': [PREPEND_ID, 0]},
		{'source': [PREPEND_ID, 0], 'destination': [TARGET_ID, 0]},
	]
	lines = [l['patchline'] for l in P['lines']]
	for ol in old_lines:
		assert ol in lines, 'linea no encontrada: %r' % (ol,)

	P['boxes'] = [b for b in P['boxes'] if b['box']['id'] != PREPEND_ID]
	P['lines'] = [l for l in P['lines'] if l['patchline'] not in old_lines]

	print('FORTESEQ2.amxd: removido %s (prepend set) y sus 2 cables (%s outlet 5 -> ... -> %s)'
		  % (PREPEND_ID, ROUTE_ID, TARGET_ID))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(DEVICE, DEVICE + '.before-harmratefix')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert PREPEND_ID not in bx2

	print('\nescrito %s (.before-harmratefix guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
