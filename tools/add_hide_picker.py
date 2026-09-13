"""Add a "Solo Voces" toggle that hides the set-picker (left half) of the floating "Proximos 16
pasos" popup, sliding the per-voice horizon grid (right half) into the vacated space so it
dominates the window.

    python tools/add_hide_picker.py            dry run, writes nothing
    python tools/add_hide_picker.py --apply    do it (device closed in Max AND Live)

## What the popup is made of

The floating window is a subpatcher, `p fs2_window` (obj-751, varname `fs2_horizon_win`, title
"FORTESEQ2 - Proximos 16 pasos", 1256 x 316). Inside it:
  * obj-3 `fs2sp_ui` (fs2setpick.js) -- the LEFT half, x 8-388: the "Mascara cromatica" pitch-class
    picker + the swatch grid of sets passing the current filter.
  * obj-2 `fs2hz_ui` (fs2horizon.js) -- the RIGHT half, x 396-1248: the per-voice next-16-steps
    horizon -- "las voces" the user actually asked to see predominantly.
  * obj-1 (inlet) fans every engine message straight to BOTH jsui's; obj-3 also feeds obj-4
    (outlet), carrying clicks back out to the main patcher (setmask/setlockindex).

868 (1256 - 388) is not a guess: it is the window's own width from BEFORE `add_fs2_setpick.py`
widened it to fit the picker (see that script's own comment, "868 -> 1256"), so sliding
`fs2hz_ui` left by exactly the picker's width (380 + 8px gap = 388) lines it up with where it
used to sit full-width, before the picker existed.

## Wiring

Main patcher: a new `live.toggle` "Solo Voces" (off by default, restored on load via the existing
`obj-631` fan) -> `sel 1` -> one of two bare messages ("hidepicker" / "showpicker") -> straight
into `obj-751`'s inlet (same entry point `obj-23`/`prepend color`/`pcontrol` already use).

Inside the subpatcher: a new `route hidepicker showpicker` is spliced between `obj-1` and the two
jsui's -- its reject outlet keeps forwarding every other message to both jsui's unchanged; its two
match outlets each fire one message into a new local `thispatcher`:
  * "hidepicker" -> `script hide fs2sp_ui, script sendbox fs2hz_ui offset -388 0`
  * "showpicker" -> `script sendbox fs2hz_ui offset 388 0, script show fs2sp_ui`

The window itself is deliberately NOT resized (no `thispatcher rect ...`) -- that would also
reposition it if the user had dragged it, which nothing here can safely undo. The picker
collapsing and the horizon grid sliding into its place is enough to make the grid the dominant,
front-and-left content; the freed strip on the right stays blank rather than risk moving the
window.

Run `tools/fix_device_height.py --apply` FIRST if it has not already been applied this session --
unrelated to this change, but the two are landing together.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
WINDOW_ID = 'obj-751'    # newobj "p fs2_window"
RESTORE_ID = 'obj-631'   # message "outputvalue", fed by loadbang -- global restore fan

HIDE_MSG = 'script hide fs2sp_ui, script sendbox fs2hz_ui offset -388 0'
SHOW_MSG = 'script sendbox fs2hz_ui offset 388 0, script show fs2sp_ui'

PX = 723.0   # under the "Proximos 16" button (obj-745, x738) / "Mon" toggle (obj-518, x723)


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    win = bx[WINDOW_ID]
    assert win['text'] == 'p fs2_window', win['text']
    assert bx[RESTORE_ID]['text'] == 'outputvalue', bx[RESTORE_ID]['text']
    assert not any(isinstance(v, list) and v and v[0] == 'Solo Voces' for v in PP.values()), 'ya aplicado'

    sub = win['patcher']
    sbx = {b['box']['id']: b['box'] for b in sub['boxes']}
    assert sbx['obj-1']['maxclass'] == 'inlet' and sbx['obj-1']['varname'] == 'fs2hz_in'
    assert sbx['obj-2']['filename'] == 'fs2horizon.js' and sbx['obj-2']['varname'] == 'fs2hz_ui'
    assert sbx['obj-3']['filename'] == 'fs2setpick.js' and sbx['obj-3']['varname'] == 'fs2sp_ui'
    old_lines = sub['lines']
    fan = [l for l in old_lines if l['patchline']['source'] == ['obj-1', 0]]
    assert {tuple(l['patchline']['destination']) for l in fan} == {('obj-2', 0), ('obj-3', 0)}, fan
    assert not any(b['box'].get('text') == 'thispatcher' for b in sub['boxes']), 'ya aplicado'

    # --- ids: subpatcher box ids are scoped to the subpatcher, main patcher's to itself --------
    snid = [max(int(i.split('-')[1]) for i in sbx)]

    def sfresh():
        snid[0] += 1
        return 'obj-%d' % snid[0]

    # --- 1. inside the subpatcher: splice a route between the inlet and the two jsui's --------
    r_route = sfresh()
    sub['boxes'].append({'box': {
        'id': r_route, 'maxclass': 'newobj', 'numinlets': 3, 'numoutlets': 3,
        'outlettype': ['bang', 'bang', ''],
        'patching_rect': [400.0, 1516.0, 220.0, 20.0], 'text': 'route hidepicker showpicker'}})

    m_hide = sfresh()
    sub['boxes'].append({'box': {
        'id': m_hide, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'linecount': 2, 'patching_rect': [400.0, 1550.0, 400.0, 36.0], 'text': HIDE_MSG}})

    m_show = sfresh()
    sub['boxes'].append({'box': {
        'id': m_show, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'linecount': 2, 'patching_rect': [650.0, 1550.0, 400.0, 36.0], 'text': SHOW_MSG}})

    p_this = sfresh()
    sub['boxes'].append({'box': {
        'id': p_this, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 2,
        'outlettype': ['', ''], 'patching_rect': [400.0, 1600.0, 80.0, 20.0],
        'text': 'thispatcher', 'save': ['#N', 'thispatcher', ';', '#Q', 'end', ';']}})

    new_lines = [l for l in old_lines if l['patchline']['source'] != ['obj-1', 0]]
    new_lines.append({'patchline': {'source': ['obj-1', 0], 'destination': [r_route, 0]}})
    new_lines.append({'patchline': {'source': [r_route, 2], 'destination': ['obj-2', 0]}})
    new_lines.append({'patchline': {'source': [r_route, 2], 'destination': ['obj-3', 0]}})
    new_lines.append({'patchline': {'source': [r_route, 0], 'destination': [m_hide, 0]}})
    new_lines.append({'patchline': {'source': [r_route, 1], 'destination': [m_show, 0]}})
    new_lines.append({'patchline': {'source': [m_hide, 0], 'destination': [p_this, 0]}})
    new_lines.append({'patchline': {'source': [m_show, 0], 'destination': [p_this, 0]}})
    sub['lines'] = new_lines

    # --- 2. main patcher: the toggle + its router -------------------------------------------
    nid = [max(int(i.split('-')[1]) for i in bx)]
    py = [2400.0]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    def step_y():
        py[0] += 26.0
        return py[0]

    c_toggle = fresh()
    P['boxes'].append({'box': {
        'id': c_toggle, 'maxclass': 'live.toggle', 'numinlets': 1, 'numoutlets': 1,
        'outlettype': ['int'], 'parameter_enable': 1, 'varname': 'fs2_' + c_toggle.replace('-', '_'),
        'patching_rect': [2600.0, step_y(), 15.0, 15.0],
        'presentation': 1, 'presentation_rect': [PX, 175.0, 15.0, 15.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_enum': ['off', 'on'], 'parameter_initial': [0],
            'parameter_initial_enable': 1, 'parameter_longname': 'Solo Voces',
            'parameter_shortname': 'Solo Voces', 'parameter_mmax': 1,
            'parameter_modmode': 0, 'parameter_type': 2}}}})

    c_label = fresh()
    P['boxes'].append({'box': {
        'id': c_label, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
        'fontsize': 8.0, 'text': 'Voces',
        'patching_rect': [2600.0, step_y(), 60.0, 18.0],
        'presentation': 1, 'presentation_rect': [PX, 163.0, 45.0, 10.0]}})

    p_sel = fresh()
    P['boxes'].append({'box': {
        'id': p_sel, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
        'outlettype': ['bang', 'bang'], 'patching_rect': [2760.0, step_y(), 220.0, 22.0], 'text': 'sel 1'}})

    m_hide_top = fresh()
    P['boxes'].append({'box': {
        'id': m_hide_top, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [2760.0, step_y(), 100.0, 20.0], 'text': 'hidepicker'}})

    m_show_top = fresh()
    P['boxes'].append({'box': {
        'id': m_show_top, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'patching_rect': [2900.0, step_y(), 100.0, 20.0], 'text': 'showpicker'}})

    P['lines'].append({'patchline': {'source': [RESTORE_ID, 0], 'destination': [c_toggle, 0]}})
    P['lines'].append({'patchline': {'source': [c_toggle, 0], 'destination': [p_sel, 0]}})
    P['lines'].append({'patchline': {'source': [p_sel, 0], 'destination': [m_hide_top, 0]}})
    P['lines'].append({'patchline': {'source': [p_sel, 1], 'destination': [m_show_top, 0]}})
    P['lines'].append({'patchline': {'source': [m_hide_top, 0], 'destination': [WINDOW_ID, 0]}})
    P['lines'].append({'patchline': {'source': [m_show_top, 0], 'destination': [WINDOW_ID, 0]}})

    PP[c_toggle] = ['Solo Voces', 'Solo Voces', 0]

    print('nuevo control: %s Solo Voces (main patcher)' % c_toggle)
    print('subpatcher fs2_window: route %s, thispatcher %s, msgs %s/%s' % (r_route, p_this, m_hide, m_show))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert c_toggle in bx2 and P2['parameters'][c_toggle][0] == 'Solo Voces', c_toggle
    win2 = bx2[WINDOW_ID]['patcher']
    sbx2 = {b['box']['id']: b['box'] for b in win2['boxes']}
    assert sbx2[r_route]['text'] == 'route hidepicker showpicker'
    assert sbx2[m_hide]['text'] == HIDE_MSG and sbx2[m_show]['text'] == SHOW_MSG
    ssrcs = {(l['patchline']['source'][0], l['patchline']['source'][1], l['patchline']['destination'][0])
             for l in win2['lines']}
    assert ('obj-1', 0, r_route) in ssrcs
    assert (r_route, 2, 'obj-2') in ssrcs and (r_route, 2, 'obj-3') in ssrcs
    assert (r_route, 0, m_hide) in ssrcs and (r_route, 1, m_show) in ssrcs
    assert (m_hide, 0, p_this) in ssrcs and (m_show, 0, p_this) in ssrcs
    assert ('obj-1', 0, 'obj-2') not in ssrcs and ('obj-1', 0, 'obj-3') not in ssrcs
    srcs = {(l['patchline']['source'][0], l['patchline']['source'][1], l['patchline']['destination'][0])
            for l in P2['lines']}
    assert (RESTORE_ID, 0, c_toggle) in srcs
    assert (c_toggle, 0, p_sel) in srcs
    assert (p_sel, 0, m_hide_top) in srcs and (p_sel, 1, m_show_top) in srcs
    assert (m_hide_top, 0, WINDOW_ID) in srcs and (m_show_top, 0, WINDOW_ID) in srcs

    print('\nescrito %s (.before guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  en Max: recarga el device completo, script stop/start node.script')


main()
