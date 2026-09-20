"""Sub desde el popup no cambiaba la velocidad del metro (solo el motor).

Causa: el eco `gecho sub` llegaba al live.menu `fs2_sub_g` (obj-706) via `prepend set`, que solo
actualiza lo que el widget MUESTRA y no dispara su salida. Pero el cambio de velocidad del metro
no vive en el motor: cuelga de la salida del widget (sel -> fs2_sub_hold -> t b i i -> rate/note
value). Resultado: subDiv subia en el motor (corre la secuencia cada subDiv-esimo tick) pero el
metro seguia al ritmo de antes -> las notas salian subDiv veces mas lento.

Fix: el token `sub` de `route sub human` (obj-849) va DIRECTO al live.menu (sin prepend set), asi
re-emite y arrastra toda la cadena. No hay bucle: la salida llega a `setsub`, que ya vuelve sin
hacer nada si el valor no cambio (`if (n === subDiv) return`).

    python tools/fix_fs2_sub_echo_refire.py            dry run
    python tools/fix_fs2_sub_echo_refire.py --apply    (device cerrado en Max Y Live)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

PATH = os.path.join('forteseq', 'FORTESEQ2.amxd')


def main():
	apply_it = '--apply' in sys.argv
	data, start, end, doc = amxd.load(PATH)
	p = doc['patcher']
	ids = {b['box']['id']: b['box'] for b in p['boxes']}
	assert ids['obj-850']['text'] == 'prepend set' and ids['obj-849']['text'].startswith('route sub human')
	before = len(p['lines'])
	keep = []
	for l in p['lines']:
		pl = l['patchline']
		if pl['destination'][0] == 'obj-850' or pl['source'][0] == 'obj-850':
			continue
		keep.append(l)
	assert before - len(keep) == 2, before - len(keep)
	keep.append({'patchline': {'source': ['obj-849', 0], 'destination': ['obj-706', 0]}})
	p['lines'] = keep
	p['boxes'] = [b for b in p['boxes'] if b['box']['id'] != 'obj-850']
	print('sub: route -> live.menu directo; obj-850 (prepend set) eliminado')
	if apply_it:
		shutil.copy(PATH, PATH + '.before-subrefire')
		amxd.save(PATH, data, start, end, doc)
		print('escrito')


if __name__ == '__main__':
	main()
