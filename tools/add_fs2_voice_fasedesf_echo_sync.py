"""Popup por voz: eco inverso para Fase y Desf (fs2horizon.js, fila 5 de cada voz).

forteseq2.js ya emite `outlet(4, ["onecho", v, "fase"|"desf", valor])` desde setvoicephase /
setvoicetimeoffset; el bpatcher fs2voice.maxpat ya recibe `FS2_ON_ECHO` -> `route #1` -> `route on
grado div`. Aca se AGREGAN dos tokens a ese segundo route y se cablean a los numboxes reales
(v_fase obj-5, v_desf obj-37) via `prepend set`, igual que grado/div (obj-104/105).

Off-by-one (maxmsp-route-outlet-offbyone): `route on grado div` tiene 3 tokens -> los nuevos son
las salidas 3 y 4; el reject pasa de la 3 a la 5. Se verifica que el reject (3) no tenga cables.

    python tools/add_fs2_voice_fasedesf_echo_sync.py            dry run
    python tools/add_fs2_voice_fasedesf_echo_sync.py --apply    (device cerrado en Max Y Live)
"""
import json
import os
import shutil
import sys

PATH = os.path.join('forteseq', 'fs2voice.maxpat')


def main():
	apply_it = '--apply' in sys.argv
	doc = json.load(open(PATH, encoding='utf-8'))
	p = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in p['boxes']}

	route = bx['obj-103']
	if route['text'] == 'route on grado div fase desf':
		print('ya aplicado'); return
	assert route['text'] == 'route on grado div', route['text']
	assert bx['obj-5']['varname'] == 'v_fase' and bx['obj-37']['varname'] == 'v_desf'
	for l in p['lines']:
		pl = l['patchline']
		assert not (pl['source'][0] == 'obj-103' and pl['source'][1] >= 3), 'el reject tiene cables'

	route['text'] = 'route on grado div fase desf'
	route['numoutlets'] = 6
	route['outlettype'] = [''] * 6

	new_boxes, new_lines = [], []
	for i, (tok, target) in enumerate((('fase', 'obj-5'), ('desf', 'obj-37'))):
		bid = 'obj-%d' % (120 + i)
		assert bid not in bx
		new_boxes.append({'box': {
			'id': bid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'v_%s_setrx' % tok, 'patching_rect': [420.0 + 210 * (i + 1), 400.0, 200.0, 22.0],
			'text': 'prepend set'}})
		new_lines.append({'patchline': {'source': ['obj-103', 3 + i], 'destination': [bid, 0]}})
		new_lines.append({'patchline': {'source': [bid, 0], 'destination': [target, 0]}})
	p['boxes'].extend(new_boxes)
	p['lines'].extend(new_lines)

	print('route ->', route['text'], '| +%d cajas, +%d cables' % (len(new_boxes), len(new_lines)))
	if apply_it:
		shutil.copy(PATH, PATH + '.before-fasedesfsync')
		json.dump(doc, open(PATH, 'w', encoding='utf-8'), indent=1)
		print('escrito (backup .before-fasedesfsync)')


if __name__ == '__main__':
	main()
