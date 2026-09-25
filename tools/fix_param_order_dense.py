"""Repara los parameter_order top-level de FORTESEQ2: 30 de los 44 parametros comparten el orden 0,
y esos 30 son exactamente los que no responden en Live.

    python tools/fix_param_order_dense.py            dry run, no escribe nada
    python tools/fix_param_order_dense.py --apply    lo hace (device cerrado en Max Y en Live)

## El sintoma y por que es este el motivo

Reportado 2026-09-25: en el device, Root / Sub / Oct M / Raiz sec (y en general todo el racimo
promovido) no responden al click, mientras que Bus, Voces, Trig, Dir Lectura, Vel Arm, Pagina, Mon,
Run, Salida local, Voces Indep, Filtro, Lock, Proximos 16 y Pasar MIDI si funcionan.

Esos dos conjuntos son EXACTAMENTE los dos grupos del registro:

  * los 14 que funcionan tienen parameter_order 1..14, cada uno el suyo;
  * los 30 que no responden tienen todos parameter_order 0.

Los ordenes de los parametros top-level tienen que ser una permutacion densa de 0..N-1, sin huecos
ni repetidos -- ver la memoria amxd-parameter-registries, donde ya costo una tarde descubrirlo la
primera vez. Con 44 parametros y solo los valores 0..14 presentes, el registro es invalido, y Live
deja de atender a los que colisionan.

De donde salio: `tools/promote_globals.py` (y los scripts del racimo Ornamento) agregaron parametros
al patcher raiz sin asignarles un orden. Max omite los atributos que valen su default, asi que
`parameter_order` simplemente no aparece en el box, y ausente SIGNIFICA 0 -- por eso el archivo se
ve limpio y el problema no se nota hasta abrirlo en Live.

## Que hace este script

Reasigna 0..43 preservando el orden relativo que hay hoy, en dos bloques:

  1. los 30 que hoy estan en 0 -> 0..29, en orden de id de objeto (determinista, y aproximadamente
     el orden en que se fueron agregando);
  2. los 14 que hoy estan en 1..14 -> 30..43, en su mismo orden relativo.

El bloque 1 va PRIMERO a proposito: hoy esos 30 ya restauran antes que Run (que esta en 8), y
mandarlos al final invertiria eso -- el motor arrancaria con Root/Sub en su default y recibiria los
valores despues. Esta reparticion deja el orden de restauracion tal como esta funcionando.

Escribe los DOS registros en la misma pasada (el `parameters` del patcher y el `parameter_order`
dentro de `saved_attribute_attributes.valueof` de cada box), que es la condicion que la memoria
marca como no negociable. `parameterbanks` referencia por nombre largo y aca no se renombra nada,
asi que los bancos no se tocan. La automatizacion de Live tampoco: identifica por nombre, no por
orden.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
NOT_PARAMS = ('parameterbanks', 'parameter_overrides', 'inherited_shortname')


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    PP = P['parameters']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}

    top = [k for k in PP if k not in NOT_PARAMS and '::' not in k]
    # orden actual segun el registro del patcher, que es el que Live lee
    cur = {}
    for k in top:
        v = PP[k]
        cur[k] = v[2] if len(v) > 2 else 0

    n = len(top)
    collided = sorted([k for k in top if cur[k] == 0], key=lambda k: int(k.split('-')[1]))
    valid = sorted([k for k in top if cur[k] != 0], key=lambda k: cur[k])

    print('%d parametros top-level: %d colisionando en 0, %d con orden propio'
          % (n, len(collided), len(valid)))
    if not collided:
        print('nada que reparar: ya son una permutacion densa')
        return 0
    assert len(collided) + len(valid) == n

    new = {}
    for i, k in enumerate(collided):
        new[k] = i
    for j, k in enumerate(valid):
        new[k] = len(collided) + j

    # la condicion que hace valido el registro
    assert sorted(new.values()) == list(range(n)), 'la reasignacion no es una permutacion densa'

    print('\n%-9s %-22s %-26s %s' % ('id', 'varname', 'longname', 'orden'))
    for k in sorted(top, key=lambda k: new[k]):
        b = bx.get(k, {})
        print('%-9s %-22s %-26s %3d -> %d' % (k, (b.get('varname') or '')[:22], PP[k][0][:26],
                                              cur[k], new[k]))

    sin_valueof = []
    for k in top:
        PP[k] = [PP[k][0], PP[k][1], new[k]]              # registro (2): lo que Live lee
        vo = bx.get(k, {}).get('saved_attribute_attributes', {}).get('valueof')
        if vo is None:
            sin_valueof.append(k)
            continue
        vo['parameter_order'] = new[k]                     # registro (1): el atributo del box

    if sin_valueof:
        print('\nAVISO: %d box(es) sin saved_attribute_attributes.valueof, solo se les escribio el '
              'registro del patcher: %s' % (len(sin_valueof), ', '.join(sin_valueof)))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return 0

    shutil.copyfile(DEVICE, DEVICE + '.before-paramorder')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    PP2 = doc2['patcher']['parameters']
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    got = sorted(PP2[k][2] for k in top)
    assert got == list(range(n)), got
    for k in top:
        vo = bx2.get(k, {}).get('saved_attribute_attributes', {}).get('valueof')
        if vo is not None:
            assert vo.get('parameter_order') == PP2[k][2], (k, vo.get('parameter_order'), PP2[k][2])

    print('\nescrito %s (.before-paramorder guardado). Sigue:' % DEVICE)
    print('  python tools/check_params3.py')
    print('  abri el device en Live y probá Root / Sub / Oct M / Raiz sec')
    return 0


sys.exit(main())
