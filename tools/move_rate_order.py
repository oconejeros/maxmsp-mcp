"""Diagnostic: move Vel Arm's parameter_order, the one variable never touched across three
previous probes (a fresh id, a full Max restart, and a renamed identity), all of which left the
device still showing 5-260 in Max's own inspector for a file that plainly says 5-480.

    python tools/move_rate_order.py            dry run, writes nothing
    python tools/move_rate_order.py --apply    do it

Moves Vel Arm from order 0 to order 5 (the middle of the row), shifting Clock/Bus/Voces/Trig/Dir
down by one to close the gap. Pagina, Mon and Run keep their relative position at the end, with
Run staying last -- that ordering exists so the metro only starts after everything else is
configured, and nothing about this probe should disturb it.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
NEW_ORDER = 5


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    PP = P['parameters']
    meta = {'inherited_shortname', 'parameter_overrides', 'parameterbanks'}
    bx = {b['box']['id']: b['box'] for b in P['boxes']}

    tops = {k: v for k, v in PP.items() if k not in meta and '::' not in k}
    old = sorted((v[2], k) for k, v in tops.items())
    order_by_key = {k: o for o, k in old}
    rate_key = [k for k, v in tops.items() if v[0] == 'Vel Arm'][0]
    assert order_by_key[rate_key] == 0, order_by_key[rate_key]

    others = [k for o, k in old if k != rate_key]
    new_seq = others[:NEW_ORDER] + [rate_key] + others[NEW_ORDER:]
    assert len(new_seq) == len(old)

    print('orden anterior:')
    for o, k in old:
        print('  %d  %-10s %s' % (o, k, tops[k][0]))

    for i, k in enumerate(new_seq):
        PP[k] = [PP[k][0], PP[k][1], i]
        vo = bx[k]['saved_attribute_attributes']['valueof']
        if 'parameter_order' in vo:
            vo['parameter_order'] = i

    tops2 = {k: v for k, v in PP.items() if k not in meta and '::' not in k}
    new = sorted((v[2], k) for k, v in tops2.items())
    print('')
    print('orden nuevo:')
    for o, k in new:
        print('  %d  %-10s %s' % (o, k, tops2[k][0]))

    orders = sorted(v[2] for v in tops2.values())
    assert orders == list(range(len(orders))), orders
    run_key = [k for k, v in tops2.items() if v[0] == 'Run'][0]
    assert tops2[run_key][2] == max(orders), 'Run tiene que seguir ultimo'

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
