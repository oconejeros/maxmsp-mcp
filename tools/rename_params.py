"""Rename ten parameters whose longname is ambiguous once it's outside its own bank -- the worst
case being 'Perm' (which set of NOTES to read, inside the current set) vs 'Orden' (which SET comes
next in the catalogue), two completely different selectors with names that invite confusion.

    python tools/rename_params.py            dry run, writes nothing
    python tools/rename_params.py --apply    do it

Only parameter_longname / parameter_shortname change -- the underlying id, value, and automation
identity are untouched, so this is purely a display-label fix. Nine of the ten live inside
fs2pages.maxpat (a FILE bpatcher, see [[amxd-parameter-registries]]) and therefore have a SECOND
copy of the same two fields in FORTESEQ2.amxd under "obj-484::<id>"; both copies are updated so
they can't drift apart. The tenth ('Dir') is a top-level box directly inside FORTESEQ2.amxd
(obj-398), with no second copy to keep in sync.

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

# varname -> (old longname, new longname, new shortname)
RENAMES = {
	'fs2_mode':      ('Modo',     'Modo Toque',    'Modo Tq'),
	'fs2_perm':      ('Perm',     'Patron Lectura', 'PatrLect'),
	'fs2_salto':     ('Salto',    'Salto Coprimo', 'SaltoCop'),
	'fs2_rot':       ('Rotacion', 'Rotar x Cambio', 'Rot'),
	'fs2_indep':     ('Indep',    'Voces Indep',   'Indep'),
	'fs2_curva':     ('Curva',    'Curva Tension', 'Curva Tn'),
	'fs2_progfav':   ('Prog',     'Prog Favoritos', 'Prog Fav'),
	'fs2_tensmodel': ('Modelo',   'Modelo Tension', 'TensMod'),
	'fs2_enlace':    ('Enlace',   'Enlace Tonos',  'Enl Ton'),
}
# top-level box inside FORTESEQ2.amxd itself, id -> (old, new, new short)
TOPLEVEL_RENAME = {'obj-398': ('Dir', 'Dir Lectura', 'Dir Lec')}


def main():
	apply_it = '--apply' in sys.argv

	pg = json.load(open(PAGES, encoding='utf-8'))
	P = pg['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}
	bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}

	touched = []
	for vn, (old, new, short) in RENAMES.items():
		box = bx[bv[vn]]
		vo = box['saved_attribute_attributes']['valueof']
		assert vo['parameter_longname'] == old, (vn, vo['parameter_longname'])
		vo['parameter_longname'] = new
		vo['parameter_shortname'] = short
		touched.append((vn, box['id'], old, new))

	print('fs2pages.maxpat:')
	for vn, bid, old, new in touched:
		print('  %-14s (%s): %r -> %r' % (vn, bid, old, new))

	data, s, e, doc = amxd.load(DEVICE)
	D = doc['patcher']
	DP = D['parameters']

	print('')
	print('FORTESEQ2.amxd (registro obj-484::<id>):')
	for vn, bid, old, new in touched:
		key = '%s::%s' % (BPATCHER_ID, bid)
		short = RENAMES[vn][2]
		assert key in DP, key
		assert DP[key][0] == old, (key, DP[key])
		DP[key][0] = new
		DP[key][1] = short
		print('  %-14s: %r -> %r' % (key, old, new))

	print('')
	print('FORTESEQ2.amxd (top-level):')
	for bid, (old, new, short) in TOPLEVEL_RENAME.items():
		assert bid in DP, bid
		assert DP[bid][0] == old, (bid, DP[bid])
		DP[bid][0] = new
		DP[bid][1] = short
		print('  %-14s: %r -> %r' % (bid, old, new))
		def find(patcher, target):
			for b in patcher.get('boxes', []):
				box = b['box']
				if box.get('id') == target:
					return box
				if 'patcher' in box:
					r = find(box['patcher'], target)
					if r:
						return r
			return None
		topbox = find(D, bid)
		assert topbox is not None, bid
		topvo = topbox['saved_attribute_attributes']['valueof']
		assert topvo['parameter_longname'] == old, topvo
		topvo['parameter_longname'] = new
		topvo['parameter_shortname'] = short

	# parameterbanks stores each member as a bare name STRING, not a reference to the parameter --
	# so every bank that lists one of these ten by its old name has to be updated too, or it would
	# point at a name that no longer exists anywhere.
	all_renames = dict([(old, new) for (old, new, _short) in RENAMES.values()] +
		[(old, new) for (old, new, _short) in TOPLEVEL_RENAME.values()])
	banks = DP['parameterbanks']
	print('')
	print('bancos que referencian alguno de estos nombres:')
	for bid, bank in banks.items():
		changed = False
		params = bank['parameters']
		for i, p in enumerate(params):
			if p in all_renames:
				print('  banco %s "%s": %r -> %r' % (bid, bank['name'], p, all_renames[p]))
				params[i] = all_renames[p]
				changed = True
		if not changed:
			continue

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
