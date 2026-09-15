"""Wire the reverse echo para R.Arm (Ritmo Arm / harmRate), la fila 2 de la columna 2 del sidebar
del popup Horizonte. Es deuda tecnica: R.Arm ya tiene LECTURA (`gharm` en querynext) desde hace
varias rondas, pero nunca tuvo eco inverso, asi que arrastrarlo en el popup cambia el motor y NO
mueve el widget del panel.

El motivo del olvido: son DOS parametros con nombres parecidos, y en su momento cablee el que no
era y despues saque el eco en vez de re-apuntarlo.

  Ritmo Arm  = harmRate, lo que el popup llama R.Arm
               `fs2_rarm`  obj-148, DENTRO de fs2pages.maxpat, live.numbox, rango 0-64,
               setter setharmrate(r)                                            <- este
  Vel Arm    = rate del reloj libre en ms
               `fs2_rate2` obj-480, en FORTESEQ2.amxd (patcher raiz), rango 5-260,
               sin setter en el motor (Max puro)                                <- NO este

setharmrate() en forteseq2.js ya manda `outlet(4, ["gecho", "rarm", harmRate])` por el mismo canal
FS2_G_ECHO que el resto del sidebar. Como el widget vive dentro del bpatcher, el receptor tiene que
vivir en ese MISMO archivo (`send`/`receive` cruza limites de patcher, `prepend set` -> destino no),
igual que add_fs2_enlace_echo_sync.py / add_fs2_filtro_echo_sync.py.

Receptor NUEVO e independiente, no un token agregado a un `route` existente: agregar un token corre
todos los indices posteriores y el reject deja de ser el ultimo (ver maxmsp-route-outlet-offbyone).
Varios `receive` con el mismo nombre reciben todos una copia, asi que esto es gratis.

    python tools/add_fs2_rarm_echo_sync.py            dry run, writes nothing
    python tools/add_fs2_rarm_echo_sync.py --apply    do it (device closed in Max AND Live)

## What changes (forteseq/fs2pages.maxpat only -- no FORTESEQ2.amxd change needed)

New `receive FS2_G_ECHO` -> `route rarm` -> `prepend set` -> `fs2_rarm` (obj-148).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
TARGET_ID = 'obj-148'   # fs2_rarm, live.numbox "Ritmo Arm", 0-64


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx = {b['box']['id']: b['box'] for b in pg['boxes']}
	assert TARGET_ID in bx and bx[TARGET_ID].get('varname') == 'fs2_rarm', \
		'no coincide %s (se esperaba varname fs2_rarm)' % TARGET_ID
	# regla 5 del plan: verificar el widget real antes de cablear -- rango y longname tienen que
	# coincidir con el clamp del motor (0-64 en setharmrate).
	sa = bx[TARGET_ID].get('saved_attribute_attributes', {}).get('valueof', {})
	assert sa.get('parameter_longname') == 'Ritmo Arm', 'longname inesperado: %r' % sa.get('parameter_longname')
	assert sa.get('parameter_mmax') == 64.0, 'rango inesperado: mmax=%r (se esperaba 64.0)' % sa.get('parameter_mmax')
	assert not any(b['box'].get('varname') == 'fs2_rarm_gecho_rx' for b in pg['boxes']), 'ya aplicado'

	nid = [max(int(i.split('-')[1]) for i in bx)]

	def fresh():
		nid[0] += 1
		return 'obj-%d' % nid[0]

	recv_id = fresh()
	pg['boxes'].append({'box': {
		'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_rarm_gecho_rx', 'patching_rect': [900.0, 4250.0, 160.0, 20.0],
		'text': 'receive FS2_G_ECHO'}})

	route_id = fresh()
	pg['boxes'].append({'box': {
		'id': route_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
		'outlettype': ['', ''], 'varname': 'fs2_rarm_gecho_route',
		'patching_rect': [900.0, 4280.0, 160.0, 20.0], 'text': 'route rarm'}})
	pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

	prep_id = fresh()
	pg['boxes'].append({'box': {
		'id': prep_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
		'varname': 'fs2_rarm_gecho_setrx', 'patching_rect': [900.0, 4310.0, 160.0, 22.0],
		'text': 'prepend set'}})
	pg['lines'].append({'patchline': {'source': [route_id, 0], 'destination': [prep_id, 0]}})
	pg['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': [TARGET_ID, 0]}})

	print('fs2pages.maxpat: +%s (receive FS2_G_ECHO) -> +%s (route rarm) -> +%s (prepend set) -> %s (fs2_rarm)'
		  % (recv_id, route_id, prep_id, TARGET_ID))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	shutil.copyfile(PAGES, PAGES + '.before-rarmechosync')
	with open(PAGES, 'w', encoding='utf-8', newline='') as f:
		json.dump({'patcher': pg}, f, indent=1)

	pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
	bx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
	assert recv_id in bx2 and route_id in bx2 and prep_id in bx2

	print('\nescrito %s (.before-rarmechosync guardado). Sigue:' % PAGES)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
	print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
