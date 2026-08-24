"""Add eight Quickstart banks (a showcase over parameters that already live in another bank -- none
of these 64 slots are new controls) and renumber so they show up FIRST when paging banks on Push.

    python tools/add_quickstart_banks.py            dry run, writes nothing
    python tools/add_quickstart_banks.py --apply    do it

Run this AFTER tools/rename_params.py --apply and tools/regroup_banks.py --apply -- it references
the new names (Modo Toque, Patron Lectura, ...) and expects bank 14 already gone (regroup_banks.py
folded it into "Seleccion"), so it can renumber the remaining 27 banks into a clean run.

Push orders banks by ascending numeric id (each bank dict carries an explicit "index" field that
always matches its own key -- checked against the current 28 banks before writing this). There is
no other place that id is used: it is the shelf order in Push's bank pager, not something Live
tracks per Live Set, so renumbering is safe -- no automation lane depends on it, only on the
parameter itself. The 27 existing banks (after the merge) keep their relative order and simply
shift from ids 0-27 (with the 14 gap) to 8-34; the eight new ones take 0-7.

Chosen for the four the user asked for (registro de voz, pitch-set, raiz, orden) plus one axis of
the device each: Registro/Ritmo/Voces+Camino/Timbre/Tiempo/Lectura+Grado/Vivo. The 12 Mask toggles
and 16 Acento toggles are deliberately left OUT of Quickstart -- they are grids, not
quick-turnaround controls, which is what tools/add_randomize.py is for instead.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

QUICKSTART = [
	('Quick 1 - Armonia', ['Set', 'Root', 'Orden', 'Modo Toque', 'Lock', 'Filtro', 'n min', 'n max']),
	('Quick 2 - Registro', ['Rango', 'V1 Min', 'V2 Min', 'V3 Min', 'V4 Min', 'Voicing', 'Conduccion',
		'Sec Raiz']),
	('Quick 3 - Ritmo', ['Ciclo Acentos', 'Figura Normal', 'Figura Acento', 'Silencio Normal',
		'Silencio Acento', 'Euclid', 'Pulsos', 'Giro']),
	('Quick 4 - Voces y Camino', ['V1 On', 'V2 On', 'V3 On', 'V4 On', 'Tension', 'Curva Tension',
		'Prog Favoritos', 'Enlace Tonos']),
	('Quick 5 - Timbre', ['Drum', 'Pad', 'Ritmo Arm', 'Voces', 'Vel Arm', 'Oct Maestra',
		'Rotar x Cambio', 'Modo Mask']),
	('Quick 6 - Tiempo', ['Sub', 'Swing', 'Human', 'Rasg', 'Rat N', 'Rat A', 'Prob Rat', 'Caida']),
	('Quick 7 - Lectura y Grado', ['Patron Lectura', 'Dir Lectura', 'Salto Coprimo', 'V1 Grado',
		'V2 Grado', 'V3 Grado', 'V4 Grado', 'Voces Indep']),
	('Quick 8 - Vivo', ['Escuchar', 'Emitir', 'Seguir', 'Fav', 'Solo Fav', 'Preset Silencio', 'Bus',
		'Run']),
]


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	DP = doc['patcher']['parameters']
	banks = DP['parameterbanks']

	assert '14' not in banks, 'banco 14 todavia existe -- corre regroup_banks.py --apply primero'
	assert banks['3']['name'] == 'Armonia' and 'Rotar x Cambio' not in banks['3']['parameters'], \
		'banco 3 no tiene la forma esperada -- corre regroup_banks.py --apply primero'

	# Every name used in QUICKSTART has to already exist as a real parameter somewhere.
	known = set()
	for b in banks.values():
		known.update(p for p in b['parameters'] if p != '-')
	missing = sorted(set(n for _name, params in QUICKSTART for n in params) - known)
	assert not missing, 'estos nombres de QUICKSTART no existen en ningun banco: %s' % missing

	old_ids = sorted(banks.keys(), key=int)
	remap = dict((old, str(8 + i)) for i, old in enumerate(old_ids))

	new_banks = {}
	for old, new in remap.items():
		bank = banks[old]
		bank['index'] = int(new)
		new_banks[new] = bank

	for i, (name, params) in enumerate(QUICKSTART):
		assert len(params) == 8, (name, len(params))
		new_banks[str(i)] = {'index': i, 'name': name, 'parameters': params}

	DP['parameterbanks'] = new_banks

	print('bancos Quickstart (0-7):')
	for i, (name, params) in enumerate(QUICKSTART):
		print('  %d %-24s %s' % (i, name, params))
	print('')
	print('bancos existentes corridos de 0-27 (con hueco en 14) a 8-34, mismo orden relativo.')
	print('total bancos: %d' % len(new_banks))

	if not apply_it:
		print('')
		print('(dry run: no se escribio nada -- corre con --apply)')
		return

	amxd.save(DEVICE, data, s, e, doc)
	print('')
	print('escrito %s' % DEVICE)


main()
