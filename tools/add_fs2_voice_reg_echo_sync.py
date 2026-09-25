"""Ola 10: eco inverso por voz para Oct / Ev.N / O.Rng / Pasos, Min / Span y Raiz (segunda columna de
detalle de cada fila de voz del popup).

forteseq2.js setvoiceoctavesimple()/setvoicerange()/setvoicerootoffset() ahora mandan
`outlet(4, ["advecho", <voz>, "<token>", <valor>])`; esto cablea el lado que hace que arrastrar un chip
en el popup mueva el numbox real de esa voz en fs2voice_adv.maxpat.

  evn    -> obj-22  (v_evn,    "V#1 Ev.N",  1-16)
  orng   -> obj-23  (v_orange, "V#1 O.Rng", -4..4)
  pasos  -> obj-24  (v_osteps, "V#1 Pasos", 1-16)
  oct    -> obj-4   (v_oct,    "V#1 Oct",   -4..4)
  min    -> obj-20  (         "V#1 Min",    0-127)
  span   -> obj-21  (         "V#1 Span",   0-127)
  raiz   -> obj-113 (v_raiz,   "V#1 Raiz",  -24..24)

Los cuatro primeros y Min/Span alimentan un `pak` que sale a setvoiceoctavesimple/setvoicerange;
`prepend set` NO dispara la salida del numbox, asi que el eco no rebota (no hay lazo).

Receptor NUEVO e independiente (`receive FS2_ADV_ECHO` -> `route #1` -> `route <tokens>`), no un token
agregado al `route ext art lec ...` existente (regla 1 del plan de Olas: agregar un token corre los
indices y el reject deja de ser el ultimo -- maxmsp-route-outlet-offbyone). El `route #1` propio es
necesario: el canal lleva la voz como primer atomo y cada bpatcher se queda con la suya.

    python tools/add_fs2_voice_reg_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_voice_reg_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2voice_adv.maxpat only)
"""
import json
import os
import shutil
import sys

PATH = os.path.join('forteseq', 'fs2voice_adv.maxpat')

# (token, id, varname o None, longname esperado)
TARGETS = [
	('evn', 'obj-22', 'v_evn', 'V#1 Ev.N'),
	('orng', 'obj-23', 'v_orange', 'V#1 O.Rng'),
	('pasos', 'obj-24', 'v_osteps', 'V#1 Pasos'),
	('oct', 'obj-4', 'v_oct', 'V#1 Oct'),
	('min', 'obj-20', None, 'V#1 Min'),
	('span', 'obj-21', None, 'V#1 Span'),
	('raiz', 'obj-113', 'v_raiz', 'V#1 Raiz'),
]


def main():
	apply_it = '--apply' in sys.argv

	doc = json.load(open(PATH, encoding='utf-8'))
	p = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in p['boxes']}

	# regla 5: verificar el widget real antes de cablear -- cablear al equivocado no da error,
	# simplemente no funciona.
	for tok, tid, varname, longname in TARGETS:
		assert tid in bx, 'falta %s (%s)' % (tid, tok)
		assert bx[tid].get('varname') == varname, '%s: varname %r != %r' % (tok, bx[tid].get('varname'), varname)
		sa = bx[tid].get('saved_attribute_attributes', {}).get('valueof', {})
		assert sa.get('parameter_longname') == longname, \
			'%s: longname %r, se esperaba %r' % (tok, sa.get('parameter_longname'), longname)
	assert not any(b['box'].get('varname') == 'v_reg_echo_rx' for b in p['boxes']), 'ya aplicado'
	# el pak/prepend de salida de estos numboxes existe: sin eso `set` no tendria a quien avisar
	assert bx['obj-27']['text'] == 'pak 1 0 16 0' and bx['obj-25']['text'] == 'pak 40 17'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	p['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'v_reg_echo_rx', 'patching_rect': [900.0, 600.0, 160.0, 20.0],
		'text': 'receive FS2_ADV_ECHO'}})
	r1_id = fresh()
	p['boxes'].append({'box': {
		'id': r1_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2, 'outlettype': ['', ''],
		'varname': 'v_reg_echo_route1', 'patching_rect': [900.0, 630.0, 100.0, 20.0],
		'text': 'route #1'}})
	p['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [r1_id, 0]}})

	toks = ' '.join(t[0] for t in TARGETS)
	nout = len(TARGETS) + 1   # +1 = el reject, que queda sin cablear
	route_id = fresh()
	p['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': nout, 'numoutlets': nout,
		'outlettype': [''] * nout, 'varname': 'v_reg_echo_route',
		'patching_rect': [900.0, 660.0, 300.0, 20.0], 'text': 'route ' + toks}})
	p['lines'].append({'patchline': {'source': [r1_id, 0], 'destination': [route_id, 0]}})

	new = []
	for i, (tok, target, _vn, longname) in enumerate(TARGETS):
		pid = fresh()
		p['boxes'].append({'box': {
			'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
			'varname': 'v_%s_regsetrx' % tok,
			'patching_rect': [900.0 + 110.0 * i, 700.0, 100.0, 22.0], 'text': 'prepend set'}})
		p['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
		p['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
		new.append((tok, pid, target, longname))

	print('fs2voice_adv.maxpat: +%s (receive FS2_ADV_ECHO) -> +%s (route #1) -> +%s (route %s)'
		  % (recv_id, r1_id, route_id, toks))
	for tok, pid, target, longname in new:
		print('  %-6s -> %s (prepend set) -> %s (%s)' % (tok, pid, target, longname))
	print('  boxes nuevos: %d' % (3 + len(new)))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(PATH, PATH + '.before-regechosync')
	with open(PATH, 'w', encoding='utf-8', newline='') as f:
		json.dump(doc, f, indent=1)
	print('\nescrito %s (.before-regechosync guardado). Sigue:' % PATH)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice_adv.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
