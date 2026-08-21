"""Diagnostic: rename Rate's identity to test whether the stuck 260 ceiling is keyed on it.

2ff447a rebuilt the fs2_rate box with a fresh id and the fix did not take. It flagged the one
handle that survived that rebuild unchanged: the parameter's own name. This changes both the
long/short name AND the varname, so nothing about the parameter's identity matches what it was
called before.

This is a probe, not a guaranteed fix -- and it costs something: it breaks any existing Push
mapping or automation lane keyed to "Rate". Safe here because forteseq-engine has never been
pushed and no Live set references this device (see forteseq-v2-architecture memory).

    python tools/rename_rate.py            dry run, writes nothing
    python tools/rename_rate.py --apply    do it
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
NEW_VAR = 'fs2_rate2'
NEW_NAME = 'Vel Arm'


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}
    old_id = bv['fs2_rate']
    box = bx[old_id]
    vo = box['saved_attribute_attributes']['valueof']
    print('antes: varname=%s  longname=%s  mmax=%s' % (box['varname'], vo['parameter_longname'], vo['parameter_mmax']))

    box['varname'] = NEW_VAR
    vo['parameter_longname'] = NEW_NAME
    vo['parameter_shortname'] = NEW_NAME

    PP = P['parameters']
    key = [k for k, v in PP.items() if k == old_id][0]
    assert PP[key][0] == 'Rate', PP[key]
    PP[key] = [NEW_NAME, NEW_NAME, PP[key][2]]

    for b in PP['parameterbanks'].values():
        b['parameters'] = [NEW_NAME if p == 'Rate' else p for p in b['parameters']]

    print('despues: varname=%s  longname=%s  mmax=%s' % (box['varname'], vo['parameter_longname'], vo['parameter_mmax']))

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
