"""forteseq2.amxd: add the 8th Orden mode ("Vector") to the Live-facing parameter's enum.

The engine (forteseq2.js, ORDER_VECDIST) and the horizon popup (fs2horizon.js's own
ORDER_NAMES, used only for the floating-window chip) both already know about the 8th
order. But the device's actual Live parameter -- a `live.menu` (obj-645, varname
fs2_orden, longname "Orden") sitting on the main panel -- carries its own separate
`parameter_enum` list, hardcoded to the original 7 entries, with `parameter_mmax: 6`.
That is why cycling Orden from the popup worked (it just calls setorder() directly) but
the Live parameter/automation view never offered "Vector": Live clamps a live.menu to
its own enum, so the 8th value was reachable engine-side but invisible as a parameter.

Dry-run by default; --apply writes the file (after a .before backup).
"""
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else __file__.rsplit('\\', 1)[0])
import amxd

PATH = 'forteseq/forteseq2.amxd'
NEW_ITEM = 'Vector'


def find_box(boxes, box_id):
    for b in boxes:
        box = b.get('box', b)
        if box.get('id') == box_id:
            return box
        pat = box.get('patcher')
        if pat:
            r = find_box(pat.get('boxes', []), box_id)
            if r:
                return r
    return None


def main():
    apply = '--apply' in sys.argv
    data, start, end, doc = amxd.load(PATH)

    box = find_box(doc['patcher']['boxes'], 'obj-645')
    assert box is not None, 'obj-645 (Orden live.menu) not found'
    assert box.get('varname') == 'fs2_orden', box.get('varname')

    vo = box['saved_attribute_attributes']['valueof']
    enum = vo['parameter_enum']
    print('antes :', enum, 'mmax =', vo.get('parameter_mmax'))

    if NEW_ITEM in enum:
        print('ya tiene', NEW_ITEM, '-- nada que hacer')
        return

    enum.append(NEW_ITEM)
    vo['parameter_mmax'] = len(enum) - 1
    box['annotation'] = box['annotation'].rstrip() + (
        ' Vector: recorre el catalogo por distancia entre vectores interValicos '
        '<ic1..ic6> (menor diferencia entre sets primero), no por notas compartidas '
        'como Vec.'
    )

    print('despues:', enum, 'mmax =', vo['parameter_mmax'])

    if not apply:
        print('\n(dry-run -- pasa --apply para escribir)')
        return

    backup = PATH + '.before'
    with open(backup, 'wb') as f:
        f.write(data)
    print('backup ->', backup)

    amxd.save(PATH, data, start, end, doc)
    print('escrito ->', PATH)

    # Releer y confirmar
    _, _, _, doc2 = amxd.load(PATH)
    box2 = find_box(doc2['patcher']['boxes'], 'obj-645')
    vo2 = box2['saved_attribute_attributes']['valueof']
    assert vo2['parameter_enum'] == enum
    assert vo2['parameter_mmax'] == len(enum) - 1
    print('verificado: parameter_enum y parameter_mmax quedaron como se esperaba')


if __name__ == '__main__':
    main()
