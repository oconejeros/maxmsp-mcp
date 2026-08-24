"""Add the two Azar (randomize) buttons for Mask and Acentos, plus their density numboxes.

    python tools/add_randomize.py            dry run, writes nothing
    python tools/add_randomize.py --apply    do it

forteseq2.js now has randomizemask()/randomizeaccents() (pattern generation is pure and tested in
harness.js's checkRandomize(); the write itself reuses presetScan()/presetApi, the same Live-API
mechanism the preset system already proved). This wires the two message-box buttons (same pattern
as the existing 'apilar'/'unisono' action buttons: a bare message, no parameter, straight to the
engine) and two new live.numbox density parameters (0-100), each `prepend setrand*pct` into the
engine like every other numbox in this file.

'Azar % Mask' goes into bank 21 "Mascara"'s one remaining empty slot; 'Azar % Acentos' goes into
bank 13 "Artic Acento", which has four. Both rows already have confirmed free space on their own
page: the Mask row (presentation y=150) is clear from x=365 on, the Artic Acento row (y=341) is
clear from x=244 on -- read directly off fs2pages.maxpat earlier in this session, not guessed.

Run this AFTER tools/regroup_banks.py --apply (it asserts the bank contents that script leaves
behind).

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
BPATCHER_ID = 'obj-484'
OUTLET_ID = 'obj-5'


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))
	P = pg['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}
	PP = P['parameters']

	assert bx[OUTLET_ID]['maxclass'] == 'outlet', bx[OUTLET_ID]
	assert bx[OUTLET_ID].get('comment', '').startswith('mensajes hacia'), bx[OUTLET_ID]

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	def add_numbox(varname, longname, px, py, sx, sy, annotation):
		nb = fresh()
		P['boxes'].append({'box': {
			'id': nb, 'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2,
			'outlettype': ['', 'float'], 'parameter_enable': 1, 'varname': varname,
			'annotation': annotation,
			'patching_rect': [px, py, 40.0, 15.0],
			'presentation': 1, 'presentation_rect': [sx, sy, 40.0, 15.0],
			'saved_attribute_attributes': {'valueof': {
				'parameter_mmin': 0.0, 'parameter_mmax': 100.0, 'parameter_modmode': 4,
				'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_initial': [50],
				'parameter_initial_enable': 1, 'parameter_longname': longname,
				'parameter_shortname': longname}}}})
		prep = fresh()
		msg = 'prepend set' + varname.replace('fs2_', '')
		P['boxes'].append({'box': {
			'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'patching_rect': [px, py + 40.0, 150.0, 22.0], 'text': msg}})
		P['lines'].append({'patchline': {'source': [nb, 0], 'destination': [prep, 0]}})
		P['lines'].append({'patchline': {'source': [prep, 0], 'destination': [OUTLET_ID, 0]}})
		PP[nb] = [longname, longname, 0]
		return nb

	def add_button(text, px, py, sx, sy):
		mb = fresh()
		P['boxes'].append({'box': {
			'id': mb, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
			'text': text,
			'patching_rect': [px, py, 70.0, 18.0],
			'presentation': 1, 'presentation_rect': [sx, sy, 70.0, 18.0]}})
		P['lines'].append({'patchline': {'source': [mb, 0], 'destination': [OUTLET_ID, 0]}})
		return mb

	PATCH_Y = 4500.0   # free area of the non-visual canvas, well past every other box here

	mask_pct = add_numbox('fs2_randmaskpct', 'Azar % Mask', 380.0, PATCH_Y, 390.0, 150.0,
		'Que porcentaje de las 12 celdas de Mascara enciende Azar Mascara -- minimo 1 celda, para '
		'no vaciar el filtro de mascara sin querer.')
	mask_btn = add_button('randomizemask', 380.0, PATCH_Y + 80.0, 440.0, 150.0)

	acc_pct = add_numbox('fs2_randaccentpct', 'Azar % Acentos', 380.0, PATCH_Y + 160.0, 269.0, 341.0,
		'Que porcentaje de las celdas dentro del Ciclo Acentos actual enciende Azar Acentos -- las '
		'celdas fuera del ciclo se apagan.')
	acc_btn = add_button('randomizeaccents', 380.0, PATCH_Y + 240.0, 344.0, 341.0)

	print('fs2pages.maxpat: agregados Azar %% Mask (%s), Azar Mascara (%s), '
		'Azar %% Acentos (%s), Azar Acentos (%s)' % (mask_pct, mask_btn, acc_pct, acc_btn))

	for label, sx, w in [('Azar % Mask', 390.0, 40.0), ('Azar Mascara', 440.0, 70.0),
			('Azar % Acentos', 269.0, 40.0), ('Azar Acentos', 344.0, 70.0)]:
		edge = sx + w
		print('  borde derecho de %s: %.0f px (limite 516)' % (label, edge))
		assert edge <= 516.0, (label, edge)

	data, s, e, doc = amxd.load(DEVICE)
	D = doc['patcher']
	DP = D['parameters']
	banks = DP['parameterbanks']

	for k, v in ('obj-484::' + mask_pct, 'Azar % Mask'), ('obj-484::' + acc_pct, 'Azar % Acentos'):
		assert k not in DP, 'ya esta puesto: %s' % k
		DP[k] = [v, v, 0]

	mascara = [b for b in banks.values() if b['name'] == 'Mascara'][0]
	assert mascara['parameters'][-1] == '-', mascara['parameters']
	mascara['parameters'][-1] = 'Azar % Mask'

	artic_a = [b for b in banks.values() if b['name'] == 'Artic Acento'][0]
	assert artic_a['parameters'][4] == '-', artic_a['parameters']
	artic_a['parameters'][4] = 'Azar % Acentos'

	print('')
	print('FORTESEQ2.amxd: registrado Azar % Mask -> banco Mascara, Azar % Acentos -> banco Artic Acento')

	if not apply_it:
		print('')
		print('(dry run: no se escribio nada -- corre con --apply)')
		return

	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump(pg, f, indent=1)
	amxd.save(DEVICE, data, s, e, doc)
	print('')
	print('escrito %s y %s' % (PAGES, DEVICE))


main()
