"""Fix "Globales" tab bleeding Armonia's content over its own controls.

Root cause: two independent routers disagree about what "Globales" (Pagina index 8) is.
obj-486 ("sel 0..10 12", the fs2_pages vertical-pan router) treats it like a Voces tab and
parks fs2_pages off-screen at offset [0,-900] -- fine on its own. But obj-582 ("sel 6 7 9
10", the vadv-strip show/hide router) does NOT list 8 among its matches, so Globales falls
through to its REJECT outlet -> obj-723, the message meant for the six real fs2_pages tabs
(Armonia/Filtro/Artic/Tiempo/Modul/Sesion): "script show fs2_pages, script hide vadv1..4,
script hide vah1..23". That re-shows the fs2_pages bpatcher box on top of Globales' own
(always-visible, unrelated to Pagina) Clock/Rate/Bus/Voces/Trig controls -- panned out of
view via obj-486, but visible again via obj-582's mistaken "show".

This is the same "Globales sits between Voces 2 and Voces 3, and things forget it" gap
already hit twice on this device (the click-to-jump feature's page-index list, and
add_voice_key_lock.py's MISSING_HIDES fix for vah17-22).

Fix: give obj-582 a fifth match ("sel 6 7 8 9 10") wired to a NEW message that keeps
fs2_pages hidden (Globales has no vadv/vah content of its own to show, so it's obj-723's
message with "show fs2_pages" flipped to "hide fs2_pages") -- and re-point the existing
9/10/reject wires at their new outlet indices (sel gains one outlet in the middle).

    python tools/fix_globales_tab_overlap.py            dry run, writes nothing
    python tools/fix_globales_tab_overlap.py --apply    do it (device closed in Max AND Live)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
SEL_ID = 'obj-582'


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}

    sel = bx[SEL_ID]
    assert sel['text'] == 'sel 6 7 9 10', sel['text']
    assert sel['numoutlets'] == 5

    default_msg = bx['obj-723']['text']
    assert default_msg.startswith('script show fs2_pages, ')
    globales_msg = 'script hide fs2_pages, ' + default_msg[len('script show fs2_pages, '):]

    # sel's outlet map before: 0=6->obj-721, 1=7->obj-722, 2=9->obj-800, 3=10->obj-804, 4=reject->obj-723
    old_lines = {}
    for l in P['lines']:
        pl = l['patchline']
        if pl['source'][0] == SEL_ID:
            old_lines[pl['source'][1]] = pl['destination']
    assert old_lines == {0: ['obj-721', 0], 1: ['obj-722', 0], 2: ['obj-800', 0],
                          3: ['obj-804', 0], 4: ['obj-723', 0]}, old_lines

    nid = max(int(i.split('-')[1]) for i in bx) + 1
    new_msg_id = 'obj-%d' % nid
    P['boxes'].append({'box': {
        'id': new_msg_id, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [2600.0, 2900.0, 700.0, 20.0], 'text': globales_msg}})

    sel['text'] = 'sel 6 7 8 9 10'
    sel['numoutlets'] = 6
    sel['outlettype'] = ['bang', 'bang', 'bang', 'bang', 'bang', '']

    P['lines'] = [l for l in P['lines'] if l['patchline']['source'][0] != SEL_ID]
    new_map = {0: ['obj-721', 0], 1: ['obj-722', 0], 2: [new_msg_id, 0],
               3: ['obj-800', 0], 4: ['obj-804', 0], 5: ['obj-723', 0]}
    for outlet, dest in new_map.items():
        P['lines'].append({'patchline': {'source': [SEL_ID, outlet], 'destination': dest}})

    print('%s: "sel 6 7 9 10" -> "sel 6 7 8 9 10" (+1 outlet)' % SEL_ID)
    print('new message %s (Globales, index 8): %s' % (new_msg_id, globales_msg))
    print('rewired outlets: %s' % new_map)

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-globalesfix')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert bx2[SEL_ID]['text'] == 'sel 6 7 8 9 10'
    assert new_msg_id in bx2 and bx2[new_msg_id]['text'] == globales_msg
    lines2 = {l['patchline']['source'][1]: l['patchline']['destination']
              for l in P2['lines'] if l['patchline']['source'][0] == SEL_ID}
    assert lines2 == new_map, lines2

    print('\nescrito %s (.before-globalesfix guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  python tools/check_params3.py')
    print('  en Max: cerrar y reabrir el Live Set (o sacar/reinsertar el device)')


main()
