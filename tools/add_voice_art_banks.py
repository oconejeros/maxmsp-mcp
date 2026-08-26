"""Bank the 32 parameters add_voice_art.py just added -- 8 per voice (VelMin/VelMax/Figura/
Silencio, ArtProp/LecProp/Patron/Dir) times 4 voices -- so they reach Push. Same grouping
convention the device already uses for a 3-per-voice group (Octavas V1-V2/V3-V4, Ritmo V1-V2/
V3-V4): two voices per bank, values first. Both new groups happen to be exactly 4 values, so two
voices fill a bank at 8/8 with nothing left over.

    python tools/add_voice_art_banks.py            dry run, writes nothing
    python tools/add_voice_art_banks.py --apply    do it

Appended at the end (indices 44-47), same technique add_dependency_banks.py used for its own 8:
no renumbering of the 44 banks that already exist.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
SLOTS = 8

BANKS = [
    ('Articulacion V1-V2', ['V1 VelMin', 'V1 VelMax', 'V1 Figura', 'V1 Silencio',
        'V2 VelMin', 'V2 VelMax', 'V2 Figura', 'V2 Silencio']),
    ('Articulacion V3-V4', ['V3 VelMin', 'V3 VelMax', 'V3 Figura', 'V3 Silencio',
        'V4 VelMin', 'V4 VelMax', 'V4 Figura', 'V4 Silencio']),
    ('Selectores V1-V2', ['V1 ArtProp', 'V1 LecProp', 'V1 Patron', 'V1 Dir',
        'V2 ArtProp', 'V2 LecProp', 'V2 Patron', 'V2 Dir']),
    ('Selectores V3-V4', ['V3 ArtProp', 'V3 LecProp', 'V3 Patron', 'V3 Dir',
        'V4 ArtProp', 'V4 LecProp', 'V4 Patron', 'V4 Dir']),
]


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    PP = doc['patcher']['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    ov = PP['parameter_overrides']

    names = set()
    for k, v in PP.items():
        if k in meta:
            continue
        names.add(ov[k]['parameter_longname'] if k in ov else v[0])

    banks = PP['parameterbanks']
    unknown = sorted(p for _n, ps in BANKS for p in ps if p not in names)
    assert not unknown, 'estos nombres no existen en el device: %s' % unknown
    over = [(n, len(ps)) for n, ps in BANKS if len(ps) != SLOTS]
    assert not over, 'estos bancos no tienen exactamente %d parametros: %s' % (SLOTS, over)
    taken = sorted(n for n, _ in BANKS if n in {b['name'] for b in banks.values()})
    assert not taken, 'esos nombres de banco ya existen: %s' % taken

    nxt = max(int(k) for k in banks) + 1
    for i, (name, ps) in enumerate(BANKS):
        banks[str(nxt + i)] = {'index': nxt + i, 'name': name, 'parameters': ps}

    print('bancos: %d -> %d' % (len(banks) - len(BANKS), len(banks)))
    for i, (name, ps) in enumerate(BANKS):
        print('  %2d  %-20s %s' % (nxt + i, name, ' '.join(ps)))

    idx = sorted(b['index'] for b in banks.values())
    assert idx == list(range(len(banks))), idx
    assert sorted(int(k) for k in banks) == idx, 'las claves y los index no coinciden'

    # Coverage check: every parameter but the two deliberate exceptions (Pagina, Slot) should
    # now be in at least one bank.
    banked = {p for b in banks.values() for p in b['parameters'] if p != '-'}
    missing = sorted(names - banked)
    expected = ['Pagina', 'Slot']
    assert missing == expected, 'cobertura inesperada, faltan: %s (se esperaba solo %s)' % (
        missing, expected)
    print('')
    print('cobertura: %d/%d parametros bankeados, afuera a proposito: %s' %
          (len(banked), len(names), missing))

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
