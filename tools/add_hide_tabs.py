"""Add a global "Ocultar Tabs" toggle to FORTESEQ2.amxd: collapse the whole tab area (the
vertical page selector "Pagina" + whichever content pane it is showing) so the panel is
dominated by whatever else is always visible -- chiefly the essential voice strip.

    python tools/add_hide_tabs.py            dry run, writes nothing
    python tools/add_hide_tabs.py --apply    do it (device closed in Max AND Live)

## What "the tab area" actually is

The 9-item vertical page list (obj-485, varname `fs2_pagina`, longname "Pagina": Armonia / Filtro
/ Artic / Tiempo / Modul / Sesion / Voces 1 / Voces 2 / Globales) drives three `sel` routers that
already juggle FIVE different scripted panels sharing the same screen real estate:
  * obj-486 `sel 0..8` scrolls `fs2_pages` (the Armonia..Sesion bpatcher, obj-484) via
    `script sendbox fs2_pages offset ...` -- one wide bpatcher, different vertical offset per tab.
  * obj-582 `sel 6 7` swaps to the per-voice advanced grid instead: hides `fs2_pages`, shows
    `vadv1..vadv4` (the fs2voice_adv.maxpat bpatchers, obj-577..580) at one of two horizontal
    offsets ("Voces 1" / "Voces 2" = left half / right half of that grid's columns). Its reject
    outlet (obj-723) is what puts `fs2_pages` back for every OTHER tab.
  * obj-617 `sel 8` additionally reveals five extra "Globales" controls (`fs2_clockmode` and
    friends) that stay hidden the rest of the time.

None of that hides the PAGE LIST itself, or gives a way to collapse the whole region -- it always
shows one of those five things. This script adds a toggle that hides all of it at once (the list
+ whichever pane is currently showing) and, on the way back, replays the list's own stored value
(the same `outputvalue` trick the load-time restore fan already uses) so whatever tab was active
reappears exactly as it was, not reset to page 0.

## Wiring

    Ocultar Tabs (live.toggle, off by default) -> sel 1
      outlet 0 (=1, hide) -> ONE message with every `script hide ...` above, -> thispatcher (obj-487)
      outlet 1 (=0, show) -> t b b -> script show fs2_pagina -> thispatcher
                                   -> bang obj-220 (the existing "outputvalue" message already
                                      wired to fs2_pagina) -- re-fires its stored index through the
                                      SAME obj-486/582/617 routers, restoring the exact prior view.

Restored on load like every other control here: obj-631 (RESTORE_ID) also feeds the new toggle's
inlet, so a set saved with tabs hidden reopens with them hidden.

Placement: directly under the page list itself (x 419-476, y 168+) -- the list ends at y=164 and
nothing else occupies that column below it (the "Pasa" comment at x=432 ends at y=166, just above
the 2px gap). The column just left of the list (x 386-418) looks free at a glance but is not: the
"Raiz"/"Col" pitch-class jsui (obj-660) spans x=313-411 y=30-142, right through it.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PAGINA_ID = 'obj-485'       # live.tab "Pagina"
RESTORE_ID = 'obj-631'      # message "outputvalue", fed by loadbang -- global restore fan
PAGINA_RESTORE_ID = 'obj-220'   # message "outputvalue", wired straight to fs2_pagina + 2 others
THISPATCHER_ID = 'obj-487'  # newobj "thispatcher" -- every "script ..." message targets this

HIDE_MSG = (
    'script hide fs2_pagina, script hide fs2_pages, '
    'script hide vadv1, script hide vadv2, script hide vadv3, script hide vadv4, '
    'script hide fs2_clockmode, script hide fs2_rate2, script hide fs2_bus, '
    'script hide fs2_nvoices, script hide fs2_trigmode, '
    'script hide tlbl_clk, script hide tlbl_rate, script hide tlbl_bus, '
    'script hide tlbl_voces, script hide tlbl_trig'
)
SHOW_MSG = 'script show fs2_pagina'

PX = 419.0   # directly under the "Pagina" tab list, which occupies this same x column


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert bx[PAGINA_ID]['varname'] == 'fs2_pagina', bx[PAGINA_ID].get('varname')
    assert bx[RESTORE_ID]['text'] == 'outputvalue', bx[RESTORE_ID]['text']
    assert bx[PAGINA_RESTORE_ID]['text'] == 'outputvalue', bx[PAGINA_RESTORE_ID]['text']
    assert bx[THISPATCHER_ID]['text'] == 'thispatcher', bx[THISPATCHER_ID]['text']
    assert not any(isinstance(v, list) and v and v[0] == 'Ocultar Tabs' for v in PP.values()), 'ya aplicado'

    nid = [max(int(i.split('-')[1]) for i in bx)]
    py = [2300.0]   # patching-view y, clear band well right of everything

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def step_y(h=26.0):
        py[0] += h
        return py[0]

    def comment(text, prect):
        cid = fresh()
        P['boxes'].append({'box': {
            'id': cid, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
            'fontsize': 8.0, 'text': text,
            'patching_rect': [2600.0, step_y(), 60.0, 18.0],
            'presentation': 1, 'presentation_rect': list(prect)}})
        return cid

    def toggle(longname, prect):
        tg = fresh()
        P['boxes'].append({'box': {
            'id': tg, 'maxclass': 'live.toggle', 'numinlets': 1, 'numoutlets': 1,
            'outlettype': ['int'], 'parameter_enable': 1,
            'varname': 'fs2_' + tg.replace('-', '_'),
            'patching_rect': [2600.0, step_y(), 15.0, 15.0],
            'presentation': 1, 'presentation_rect': list(prect),
            'saved_attribute_attributes': {'valueof': {
                'parameter_enum': ['off', 'on'], 'parameter_initial': [0],
                'parameter_initial_enable': 1, 'parameter_longname': longname,
                'parameter_shortname': longname, 'parameter_mmax': 1,
                'parameter_modmode': 0, 'parameter_type': 2}}}})
        return tg

    def newobj(text, numinlets, outlettype):
        oid = fresh()
        P['boxes'].append({'box': {
            'id': oid, 'maxclass': 'newobj', 'numinlets': numinlets, 'numoutlets': len(outlettype),
            'outlettype': outlettype, 'patching_rect': [2760.0, step_y(), 220.0, 22.0], 'text': text}})
        return oid

    def message(text, lines=1):
        mid = fresh()
        P['boxes'].append({'box': {
            'id': mid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
            'linecount': lines, 'patching_rect': [3000.0, step_y(22.0 * lines), 500.0, 20.0 * lines],
            'text': text}})
        return mid

    comment('Tabs', [PX, 168.0, 50.0, 10.0])
    c_hide = toggle('Ocultar Tabs', [PX, 180.0, 15.0, 15.0])
    p_sel = newobj('sel 1', 2, ['bang', 'bang'])
    p_hide = message(HIDE_MSG, lines=6)
    p_trig = newobj('t b b', 1, ['bang', 'bang'])
    p_show = message(SHOW_MSG)

    # wiring
    P['lines'].append({'patchline': {'source': [RESTORE_ID, 0], 'destination': [c_hide, 0]}})
    P['lines'].append({'patchline': {'source': [c_hide, 0], 'destination': [p_sel, 0]}})
    P['lines'].append({'patchline': {'source': [p_sel, 0], 'destination': [p_hide, 0]}})
    P['lines'].append({'patchline': {'source': [p_hide, 0], 'destination': [THISPATCHER_ID, 0]}})
    P['lines'].append({'patchline': {'source': [p_sel, 1], 'destination': [p_trig, 0]}})
    P['lines'].append({'patchline': {'source': [p_trig, 0], 'destination': [p_show, 0]}})
    P['lines'].append({'patchline': {'source': [p_show, 0], 'destination': [THISPATCHER_ID, 0]}})
    P['lines'].append({'patchline': {'source': [p_trig, 1], 'destination': [PAGINA_RESTORE_ID, 0]}})

    # registry
    PP[c_hide] = ['Ocultar Tabs', 'Ocultar Tabs', 0]

    print('nuevo control: %s Ocultar Tabs' % c_hide)
    print('hide message: %s' % HIDE_MSG)
    print('show message: %s + bang a %s (refire fs2_pagina)' % (SHOW_MSG, PAGINA_RESTORE_ID))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert c_hide in bx2 and P2['parameters'][c_hide][0] == 'Ocultar Tabs', c_hide
    srcs = {(l['patchline']['source'][0], l['patchline']['destination'][0], l['patchline']['source'][1])
            for l in P2['lines']}
    assert (RESTORE_ID, c_hide, 0) in srcs
    assert (c_hide, p_sel, 0) in srcs
    assert (p_sel, p_hide, 0) in srcs
    assert (p_hide, THISPATCHER_ID, 0) in srcs
    assert (p_sel, p_trig, 1) in srcs
    assert (p_trig, p_show, 0) in srcs
    assert (p_show, THISPATCHER_ID, 0) in srcs
    assert (p_trig, PAGINA_RESTORE_ID, 1) in srcs

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  en Max: recarga el device, script stop/start node.script')


main()
