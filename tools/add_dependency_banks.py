"""Add eight new Push banks, in two sets, at the END of the device's bank list (indices
35-42) -- no renumbering of the existing 35.

    python tools/add_dependency_banks.py            dry run, writes nothing
    python tools/add_dependency_banks.py --apply    do it

Quickstart (banks 0-7) is a broad overview per area. The 27 category banks (8-34) are
mostly one category each. Neither captures the controls that live in DIFFERENT category
banks but get turned together for one task -- these eight do, chosen by tracing real
dependencies rather than by theme alone:

  Set 1 "Disparo y Dinamica" (playing live: which voice sounds, how loud, what feel)
    - Dinamica: the whole loudness chain, Engine's master down to per-articulation
      velocity ranges (Artic Normal/Acento) and mask randomization (Mascara).
    - Trigger Externo: the 4 per-voice Ext toggles with the global gate that decides
      whether an external trigger actually reaches a voice (Trig/Run/Bus/Clock) -- this
      is exactly the config that was walked through live for the voice-2 trigger issue.
    - Voces Activas: the 4 On toggles with the algorithm that distributes notes across
      whichever voices are on (Voicing/Conduccion/Sec Raiz) and the mode that decouples
      them (Voces Indep).
    - Desfases y Fases: both kinds of per-voice offset (Fase, Desf) in one bank -- same
      role, two different mechanisms.

  Set 2 "Seleccion y Repeticion" (what the generator picks, how often it repeats)
    - Tension y Filtro: the tension model (how far to move) next to the filter/order
      controls (what pool it moves within).
    - Favoritos: the favorites workflow, today split across three banks (Fav/Solo Fav
      sit in Vector Min as filler, Prog Favoritos in Camino, the actual set browsing in
      Armonia/Seleccion).
    - Compas: the global time base (Sub/Swing/Human/Rasg) next to the per-voice
      subdivision multiplier (V_ Div) that multiplies directly on top of it.
    - Repeticion: the two repeat-rate mechanisms that never share a bank today --
      ratchets and modulator cycle speed.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

SETS = [
    ('Disparo y Dinamica', [
        ('Dinamica', ['Vel Arm', 'Vel Min Normal', 'Vel Max Normal', 'Vel Min Acento',
            'Vel Max Acento', 'Azar % Acentos', 'Azar % Mask', 'Ciclo igual a n']),
        ('Trigger Externo', ['V1 Ext', 'V2 Ext', 'V3 Ext', 'V4 Ext', 'Trig', 'Run', 'Bus',
            'Clock']),
        ('Voces Activas', ['V1 On', 'V2 On', 'V3 On', 'V4 On', 'Voces Indep', 'Voicing',
            'Conduccion', 'Sec Raiz']),
        ('Desfases y Fases', ['V1 Fase', 'V2 Fase', 'V3 Fase', 'V4 Fase', 'V1 Desf',
            'V2 Desf', 'V3 Desf', 'V4 Desf']),
    ]),
    ('Seleccion y Repeticion', [
        ('Tension y Filtro', ['Tension', 'Curva Tension', 'Modelo Tension', 'Filtro',
            'Orden', 'n min', 'n max', 'Rotar x Cambio']),
        ('Favoritos', ['Fav', 'Solo Fav', 'Prog Favoritos', 'Set', 'Lock', 'Modo Toque',
            'Patron Lectura', 'Orden']),
        ('Compas', ['Sub', 'Swing', 'Human', 'Rasg', 'V1 Div', 'V2 Div', 'V3 Div',
            'V4 Div']),
        ('Repeticion', ['Rat N', 'Rat A', 'Prob Rat', 'Caida', 'M1 Ciclo', 'M2 Ciclo',
            'M3 Ciclo', 'M4 Ciclo']),
    ]),
]
BANKS = [b for _set_name, bs in SETS for b in bs]
SLOTS = 8


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
    assert len(banks) == 35, 'se esperaban 35 bancos existentes, hay %d' % len(banks)

    unknown = sorted(p for _n, ps in BANKS for p in ps if p not in names)
    assert not unknown, 'estos nombres no existen en el device: %s' % unknown
    over = [(n, len(ps)) for n, ps in BANKS if len(ps) != SLOTS]
    assert not over, 'estos bancos no tienen exactamente %d parametros: %s' % (SLOTS, over)
    taken = sorted(n for n, _ in BANKS if n in {b['name'] for b in banks.values()})
    assert not taken, 'esos nombres de banco ya existen: %s' % taken

    nxt = max(int(k) for k in banks) + 1
    assert nxt == 35, 'se esperaba que el siguiente indice fuera 35, es %d' % nxt
    for i, (name, ps) in enumerate(BANKS):
        banks[str(nxt + i)] = {'index': nxt + i, 'name': name, 'parameters': ps}

    print('bancos: %d -> %d' % (len(banks) - len(BANKS), len(banks)))
    for set_name, bs in SETS:
        print('Set: %s' % set_name)
        for name, ps in bs:
            i = nxt + BANKS.index((name, ps))
            print('  %2d  %-18s %s' % (i, name, ' '.join(ps)))
    print('')

    idx = sorted(b['index'] for b in banks.values())
    assert idx == list(range(len(banks))), idx
    assert sorted(int(k) for k in banks) == idx, 'las claves y los index no coinciden'
    assert all(len(b['parameters']) == SLOTS for b in banks.values())

    if not apply_it:
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('escrito %s' % DEVICE)


main()
