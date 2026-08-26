"""Add a "Resumen" bank in front of everything, so Push's very first page is Run plus the controls
that matter most when you sit down at the hardware: master octave, bus address, the first three
voices on/off, and the two generator-mode switches (Voces Indep, Drum).

    python tools/add_overview_bank.py            dry run, writes nothing
    python tools/add_overview_bank.py --apply    do it

Every one of the 8 names already exists as a parameter somewhere else -- a parameter can sit in
more than one bank today (Set/Lock/Modo Toque are each in three already), so this is a new
vantage point on existing controls, not a migration. Renumbers the 43 existing banks up by one
(0..42 -> 1..43) and inserts this one at 0, same technique add_quickstart_banks.py already used
once: `index` always tracks its own dict key, and no Live automation depends on a bank id.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')

NAME = 'Resumen'
PARAMS = ['Run', 'Oct Maestra', 'Bus', 'V1 On', 'V2 On', 'V3 On', 'Voces Indep', 'Drum']


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']['parameters']
    banks = P['parameterbanks']

    assert len(PARAMS) == 8, len(PARAMS)
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    ov = P['parameter_overrides']
    known = {v[0] for k, v in P.items() if k not in meta}
    known |= {v['parameter_longname'] for v in ov.values()}
    missing = sorted(set(PARAMS) - known)
    assert not missing, 'no encontre estos parametros: %s' % missing
    assert not any(b['name'] == NAME for b in banks.values()), 'ya existe un banco "%s"' % NAME

    new_banks = {}
    for k in sorted(banks, key=int):
        i = int(k) + 1
        b = banks[k]
        b['index'] = i
        new_banks[str(i)] = b
    new_banks['0'] = {'index': 0, 'name': NAME, 'parameters': list(PARAMS)}
    P['parameterbanks'] = new_banks

    for k, b in new_banks.items():
        assert b['index'] == int(k), (k, b['index'])
    print('bancos: %d (era %d), "%s" en 0, el resto corrido a 1..%d' %
          (len(new_banks), len(new_banks) - 1, NAME, len(new_banks) - 1))

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
