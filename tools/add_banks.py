"""Put the 52 unbanked parameters onto Push, in eight new banks.

    python tools/add_banks.py            dry run, writes nothing
    python tools/add_banks.py --apply    do it

Everything from Tiempo onward was built as a page in the Live UI and never given a bank, so on
Push those 52 controls did not exist at all. The banks appended here close that.

They are NOT a copy of the tab layout. On Push the bank name is only the page label -- each
encoder shows its own parameter name -- so grouping by what you turn together beats grouping by
where the control happens to live in the window. That is why the four modulation depths share a
bank with the four cycles, instead of each modulator getting a bank of its own: reaching for four
depths at once is the gesture, and four encoders in a row is what makes it one.

Left out on purpose: Pagina, which chooses a page of a window Push never shows, and Slot, which
would sit there alone because the Guardar / Cargar / Borrar buttons are not parameters and cannot
be reached from Push at all.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

# A control Push cannot use, or cannot use alone.
SKIP = ['Pagina', 'Slot']

BANKS = [
    # The nine global time controls do not fit in eight, so Dir Rasg -- a four-way choice you set
    # once and leave -- goes next door with the per-voice offsets, and the eight that reward a
    # turn stay together.
    ('Tiempo', ['Sub', 'Swing', 'Human', 'Rasg', 'Rat N', 'Rat A', 'Prob Rat', 'Caida']),
    ('Desfase', ['Dir Rasg', 'V1 Desf', 'V2 Desf', 'V3 Desf', 'V4 Desf']),
    # Two voices per bank, the shape the Octavas and Registro banks already established.
    ('Ritmo V1-V2', ['V1 Larg', 'V1 Puls', 'V1 Gir', 'V2 Larg', 'V2 Puls', 'V2 Gir']),
    ('Ritmo V3-V4', ['V3 Larg', 'V3 Puls', 'V3 Gir', 'V4 Larg', 'V4 Puls', 'V4 Gir']),
    # Two pages in one bank because they answer one question -- who decides where the harmony goes
    # next -- and because seven parameters do not deserve two pages of paging on Push.
    ('Camino', ['Enlace', 'Tension', 'Curva', 'Prog', 'Escuchar', 'Emitir', 'Seguir']),
    # Modulation by property rather than by modulator. Depth and cycle are what you move while
    # listening; destination and shape are what you set before you start; phase is the trim.
    ('Mod Prof', ['M1 Prof', 'M2 Prof', 'M3 Prof', 'M4 Prof',
                  'M1 Ciclo', 'M2 Ciclo', 'M3 Ciclo', 'M4 Ciclo']),
    ('Mod Dest', ['M1 Dest', 'M2 Dest', 'M3 Dest', 'M4 Dest',
                  'M1 Forma', 'M2 Forma', 'M3 Forma', 'M4 Forma']),
    ('Mod Fase', ['M1 Fase', 'M2 Fase', 'M3 Fase', 'M4 Fase']),
]
SLOTS = 8


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    PP = doc['patcher']['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    ov = PP['parameter_overrides']

    # The name Live and Push actually see: the override when a bpatcher instance resolves #1,
    # the registry tuple otherwise.
    names = set()
    for k, v in PP.items():
        if k in meta:
            continue
        names.add(ov[k]['parameter_longname'] if k in ov else v[0])

    banks = PP['parameterbanks']
    before = {p for b in banks.values() for p in b['parameters'] if p != '-'}

    unknown = sorted(p for _, ps in BANKS for p in ps if p not in names)
    assert not unknown, 'estos nombres no existen en el device: %s' % unknown
    already = sorted(p for _, ps in BANKS for p in ps if p in before)
    assert not already, 'estos ya estaban en un banco: %s' % already
    over = [(n, len(ps)) for n, ps in BANKS if len(ps) > SLOTS]
    assert not over, 'estos bancos no entran en %d encoders: %s' % (SLOTS, over)
    taken = sorted(n for n, _ in BANKS if n in {b['name'] for b in banks.values()})
    assert not taken, 'esos nombres de banco ya existen: %s' % taken

    nxt = max(int(k) for k in banks) + 1
    for i, (name, ps) in enumerate(BANKS):
        banks[str(nxt + i)] = {'index': nxt + i, 'name': name,
                               'parameters': ps + ['-'] * (SLOTS - len(ps))}

    after = {p for b in banks.values() for p in b['parameters'] if p != '-'}
    orphan = sorted(n for n in names if n not in after and n not in SKIP)
    print('bancos: %d -> %d' % (len(banks) - len(BANKS), len(banks)))
    for i, (name, ps) in enumerate(BANKS):
        print('  %2d  %-13s %d/%d  %s' % (nxt + i, name, len(ps), SLOTS, ' '.join(ps)))
    print('')
    print('parametros: %d en total, %d en algun banco (antes %d)' % (len(names), len(after), len(before)))
    print('fuera de banco a proposito: %s' % ', '.join(SKIP))
    print('fuera de banco sin querer: %s' % (', '.join(orphan) if orphan else 'ninguno'))
    assert not orphan, orphan

    # An index that is not a dense 0..N-1 run is how a bank goes missing from the device without
    # anything reporting an error.
    idx = sorted(b['index'] for b in banks.values())
    assert idx == list(range(len(banks))), idx
    assert sorted(int(k) for k in banks) == idx, 'las claves y los index no coinciden'
    assert all(len(b['parameters']) == SLOTS for b in banks.values())

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
