"""Regroup three of the 28 existing Push banks so their empty slots hold parameters that actually
belong together, instead of leaving them idle. Only touches banks where a merge is genuinely
coherent -- the rest of the device's 39 empty slots are the unavoidable remainder of splitting 4
voices or 4 modulators across 8-slot banks, and forcing them together with an unrelated category
just to fill space would break the grouping this is supposed to improve.

    python tools/regroup_banks.py            dry run, writes nothing
    python tools/regroup_banks.py --apply    do it

Run this AFTER tools/rename_params.py --apply -- it references the new names (Modo Toque, Patron
Lectura, etc.), since the whole point of the merge into "Seleccion" is to put the disambiguated
reading-order controls next to the catalogue-order ones.

  * Bank 11 "Teoria" (4/8 filled) + bank 14 "Lectura" (3/8 filled) merge into bank 11, renamed
    "Seleccion": Orden, Filtro, n min, n max, Patron Lectura, Dir Lectura, Salto Coprimo,
    Rotar x Cambio -- everything that decides what plays next, at the catalogue level (which SET)
    and at the note level (which NOTE inside it). Bank 14 is deleted.
  * Bank 13 "Mask 9-12" (4/8 filled) absorbs Modo Mask / Mask k / Mask Fit, which used to sit in
    Teoria despite being mask controls -- renamed "Mascara", now 7/8.
  * Bank 3 "Armonia" loses Rotacion (moved into Seleccion): 7/8, one empty slot left for later.

This only edits FORTESEQ2.amxd's parameterbanks -- no parameter is created, renamed, or moved out
of any OTHER bank than these three, and Perm/Patron Lectura stays duplicated in Armonia exactly as
before. Bank ids are untouched here; tools/add_quickstart_banks.py does the final renumbering that
closes the gap left by deleting bank 14 and makes room for the eight new banks at the front.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	DP = doc['patcher']['parameters']
	banks = DP['parameterbanks']

	assert banks['3']['name'] == 'Armonia', banks['3']
	assert banks['3']['parameters'] == \
		['Set', 'Lock', 'Modo Toque', 'Patron Lectura', 'Root', 'Oct Maestra', 'Rotar x Cambio', 'Voces Indep'], \
		banks['3']['parameters']
	banks['3']['parameters'] = \
		['Set', 'Lock', 'Modo Toque', 'Patron Lectura', 'Root', 'Oct Maestra', 'Voces Indep', '-']

	assert banks['11']['name'] == 'Teoria', banks['11']
	assert banks['11']['parameters'] == \
		['Orden', 'Filtro', 'n min', 'n max', 'Modo Mask', 'Mask k', 'Mask Fit', '-'], \
		banks['11']['parameters']
	assert banks['14']['name'] == 'Lectura', banks['14']
	assert banks['14']['parameters'][:3] == ['Patron Lectura', 'Dir Lectura', 'Salto Coprimo'], \
		banks['14']['parameters']
	banks['11']['name'] = 'Seleccion'
	banks['11']['parameters'] = \
		['Orden', 'Filtro', 'n min', 'n max', 'Patron Lectura', 'Dir Lectura', 'Salto Coprimo',
			'Rotar x Cambio']
	del banks['14']

	assert banks['13']['name'] == 'Mask 9-12', banks['13']
	assert banks['13']['parameters'] == \
		['Mask 9', 'Mask 10', 'Mask 11', 'Mask 12', '-', '-', '-', '-'], banks['13']['parameters']
	banks['13']['name'] = 'Mascara'
	banks['13']['parameters'] = \
		['Mask 9', 'Mask 10', 'Mask 11', 'Mask 12', 'Modo Mask', 'Mask k', 'Mask Fit', '-']

	print('banco 3  "Armonia"  : %s' % banks['3']['parameters'])
	print('banco 11 "Seleccion": %s' % banks['11']['parameters'])
	print('banco 13 "Mascara"  : %s' % banks['13']['parameters'])
	print('banco 14 "Lectura"  : eliminado (fusionado en Seleccion)')
	print('bancos restantes: %d' % len(banks))

	if not apply_it:
		print('')
		print('(dry run: no se escribio nada -- corre con --apply)')
		return

	amxd.save(DEVICE, data, s, e, doc)
	print('')
	print('escrito %s' % DEVICE)


main()
