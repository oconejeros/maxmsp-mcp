"""Add "V#n R.Raiz" -- per-voice Ritmo Raiz, a live.numbox (0-64) giving each voice its own clock
for the shared root walk (Sec Raiz), so V1 can modulate every 4 steps while V3 modulates every 7.

    python tools/add_voice_root_rate.py            dry run, writes nothing
    python tools/add_voice_root_rate.py --apply    do it (device closed in Max AND Live)

forteseq2.js already carries the engine side (this session): voiceRootRate/voiceRootCount/
voiceRootSeqPos/voiceRootSeqOffset, setvoicerootrate(), voiceRootSeqAdvance(), voiceRootStep()
called from step() right after rootStep(), and voiceEffRoot() substituting this voice's own offset
for the shared rootSeqOffset inside voiceRootFor(). Only the CLOCK is per voice -- the sequence
itself stays the shared rootSeqIdx -- so the voices are the same journey at different speeds.
Rate 0 (the default) leaves a voice on the shared walk, which is what makes the whole thing additive.

What is missing before this script is the Live-savable/automatable widget.

## Why it fits on the existing "Voces 4" page, with no new page

fs2voice_adv.maxpat is ONE row 726px wide; the device pages it by panning a 206px-wide bpatcher
(`script sendbox vadv1 offset ...`, see the "Paginar una UI de M4L" memory). Current offsets are
0 / -204 / -412 / -620, so Voces 4 shows local x 620..826 and today stops at `v_fijar` (712..726).
There are ~96px free after it. That matters: widening a page's viewport pans the SAME canvas for
every page and leaks content between tabs (see the forteseq2_voice_split memory, where Voces 3 and
Voces 4 were both added as new pages precisely to avoid that). Appending inside an existing page's
already-visible strip has neither problem.

Local x maps to device x as `296 + (local - 620)` on this page, which is where the vah25 header
label's coordinate comes from.

## What changes, file by file

**forteseq/fs2voice_adv.maxpat** (shared, x4 instances):
  * `v_rrate` (live.numbox, 0-64, longname "V#1 R.Raiz") at local presentation x=738.
  * `v_rrate` -> `prepend setvoicerootrate #1` -> `obj-102` (the bpatcher's outlet).
  * `obj-101` (the init `outputvalue` fan) -> `v_rrate`, so the saved value re-fires into the
    engine on load, like every sibling control in this strip.
  * A DEDICATED `receive FS2_ADV_ECHO` -> `route #1` -> `route rrate` -> `prepend set` -> `v_rrate`.
    Deliberately NOT a new token on the existing `route evn orng pasos oct min span raiz`
    (obj-223): inserting a token into a route shifts every later match outlet and pushes reject off
    the end -- see the maxmsp_route_outlet_offbyone memory.

**forteseq/FORTESEQ2.amxd**:
  * A new `vah25` header comment ("R.Raiz"), shown by the Voces 4 message (obj-804) and hidden by
    every other page message. Every page message here already hides each vah it does not show, so
    the new one is added to all of them or it would bleed across tabs.
  * 4 nested params (1 control x 4 bpatcher instances) with `parameter_overrides` giving clean
    "V1 R.Raiz".."V4 R.Raiz" names, same precedent as the Voces 3 / Voces 4 controls.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE = os.path.join('forteseq', 'fs2voice_adv.maxpat')

INIT_MSG_ID = 'obj-101'     # va_init_msg -- the load-time `outputvalue` fan
OUTLET_ID = 'obj-102'       # the bpatcher's outlet toward [js forteseq2.js]
FIJAR_ID = 'obj-117'        # v_fijar, the last control on the Voces 4 page today
BPATCHER_IDS = ['obj-577', 'obj-578', 'obj-579', 'obj-580']   # V1..V4 instances of fs2voice_adv

VOCES4_MSG_ID = 'obj-804'   # the page message that shows vah20..23 and offsets vadv* by -620
# Every page message that must LEARN to hide the new label. obj-874 hides no vah at all (it is the
# Voces parent tab, which delegates to the per-page messages) and is deliberately left alone.
HIDE_MSG_IDS = ['obj-721', 'obj-722', 'obj-800',
                'obj-869', 'obj-870', 'obj-871', 'obj-872', 'obj-873',
                'obj-875', 'obj-876', 'obj-877']

LOCAL_X = 738.0             # local presentation x inside fs2voice_adv.maxpat
PAGE_LOCAL_ORIGIN = 620.0   # what local x the Voces 4 offset puts at the left edge
PAGE_DEVICE_ORIGIN = 296.0  # the vadv bpatchers' own presentation x in the device
VAH_Y = 35.0

ANNOTATION = (
    'Ritmo Raiz propio de esta voz: cada cuantos pasos avanza SU camino de raiz. En 0 (por '
    'defecto) esta voz sigue el camino compartido, como siempre. Con cualquier otro valor tiene '
    'su propio reloj, asi que dos voces con ritmos distintos recorren la misma secuencia de Sec '
    'Raiz desfasadas, en canon. La secuencia (Cuartas, Quintas, Azar...) sigue siendo la global: '
    'lo propio de cada voz es el reloj, no el camino. Ojo: con TonProp prendido y la voz sin '
    'seguir la raiz compartida, la voz tiene clave fija y esto no la mueve.')


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2voice_adv.maxpat -------------------------------------------------------------
    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx = {b['box']['id']: b['box'] for b in pg['boxes']}
    ppp = pg['parameters']

    assert pbx[INIT_MSG_ID]['text'] == 'outputvalue', pbx[INIT_MSG_ID].get('text')
    assert pbx[OUTLET_ID]['maxclass'] == 'outlet', pbx[OUTLET_ID]['maxclass']
    fij = pbx[FIJAR_ID]['saved_attribute_attributes']['valueof']
    assert fij['parameter_longname'] == 'V#1 Fijar', fij
    # the new control must land to the RIGHT of Fijar and still inside the 206px page window
    fij_r = pbx[FIJAR_ID]['presentation_rect']
    assert LOCAL_X >= fij_r[0] + fij_r[2], 'se solaparia con v_fijar'
    assert LOCAL_X + 26.0 <= PAGE_LOCAL_ORIGIN + 206.0, 'se saldria de la ventana de Voces 4'
    assert not any(b['box'].get('varname') == 'v_rrate' for b in pg['boxes']), 'ya aplicado'

    pnid = [max(int(i.split('-')[1]) for i in pbx)]

    def pfresh():
        pnid[0] += 1
        return 'obj-%d' % pnid[0]

    ctrl = pfresh()
    pg['boxes'].append({'box': {
        'id': ctrl, 'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2,
        'outlettype': ['', 'float'], 'parameter_enable': 1, 'varname': 'v_rrate',
        'annotation': ANNOTATION,
        'patching_rect': [400.0, 1000.0, 34.0, 15.0],
        'presentation': 1, 'presentation_rect': [LOCAL_X, 3.0, 26.0, 15.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_modmode': 4,
            'parameter_mmin': 0.0, 'parameter_mmax': 64.0,
            'parameter_initial': [0], 'parameter_initial_enable': 1,
            'parameter_longname': 'V#1 R.Raiz', 'parameter_shortname': 'R.Raiz'}}}})
    ppp[ctrl] = ['V#1 R.Raiz', 'V#1 R.Raiz', 0]

    prep = pfresh()
    pg['boxes'].append({'box': {
        'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_rootrate_prep', 'patching_rect': [400.0, 1030.0, 220.0, 22.0],
        'text': 'prepend setvoicerootrate #1'}})
    pg['lines'].append({'patchline': {'source': [ctrl, 0], 'destination': [prep, 0]}})
    pg['lines'].append({'patchline': {'source': [prep, 0], 'destination': [OUTLET_ID, 0]}})
    pg['lines'].append({'patchline': {'source': [INIT_MSG_ID, 0], 'destination': [ctrl, 0]}})

    # dedicated echo chain -- see the module docstring for why this is not a new route token
    rx = pfresh()
    pg['boxes'].append({'box': {
        'id': rx, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_rrate_echo_rx', 'patching_rect': [760.0, 1000.0, 160.0, 22.0],
        'text': 'receive FS2_ADV_ECHO'}})
    rt_v = pfresh()
    pg['boxes'].append({'box': {
        'id': rt_v, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2, 'outlettype': ['', ''],
        'varname': 'v_rrate_echo_route1', 'patching_rect': [760.0, 1030.0, 160.0, 22.0],
        'text': 'route #1'}})
    rt_k = pfresh()
    pg['boxes'].append({'box': {
        'id': rt_k, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2, 'outlettype': ['', ''],
        'varname': 'v_rrate_echo_route', 'patching_rect': [760.0, 1060.0, 160.0, 22.0],
        'text': 'route rrate'}})
    setrx = pfresh()
    pg['boxes'].append({'box': {
        'id': setrx, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_rrate_echo_setrx', 'patching_rect': [760.0, 1090.0, 160.0, 22.0],
        'text': 'prepend set'}})
    pg['lines'].append({'patchline': {'source': [rx, 0], 'destination': [rt_v, 0]}})
    pg['lines'].append({'patchline': {'source': [rt_v, 0], 'destination': [rt_k, 0]}})
    pg['lines'].append({'patchline': {'source': [rt_k, 0], 'destination': [setrx, 0]}})
    pg['lines'].append({'patchline': {'source': [setrx, 0], 'destination': [ctrl, 0]}})

    # ---- FORTESEQ2.amxd -------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert not any((b['box'].get('varname') or '') == 'vah25' for b in P['boxes']), 'ya aplicado'
    v4 = bx[VOCES4_MSG_ID]
    assert 'script show vah23' in v4['text'], 'obj-804 no es el mensaje de Voces 4'
    assert 'offset -620 0' in v4['text'], 'el offset de Voces 4 ya no es -620'
    # Each page message already accounts for every vah it does not show, so vah24 (the newest one
    # before this script) appearing in each of them -- as hide, or as show in Voces 3, which owns
    # it -- is the check that this list is still the complete set of pages.
    for mid in HIDE_MSG_IDS:
        assert 'vah24' in bx[mid]['text'], '%s no menciona vah24' % mid
        assert 'script show vah25' not in bx[mid]['text'], '%s ya muestra vah25' % mid

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    vah = fresh()
    dev_x = PAGE_DEVICE_ORIGIN + (LOCAL_X - PAGE_LOCAL_ORIGIN) - 2.0
    P['boxes'].append({'box': {
        'id': vah, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
        'fontsize': 8.0, 'text': 'R.Raiz', 'varname': 'vah25',
        'patching_rect': [2600.0, 2620.0, 60.0, 18.0],
        'presentation': 1, 'presentation_rect': [dev_x, VAH_Y, 34.0, 16.0]}})

    v4['text'] = v4['text'] + ', script show vah25'
    for mid in HIDE_MSG_IDS:
        bx[mid]['text'] = bx[mid]['text'] + ', script hide vah25'

    ov = PP['parameter_overrides']
    for vi, bp_id in enumerate(BPATCHER_IDS):
        clean = 'V%d R.Raiz' % (vi + 1)
        key = '%s::%s' % (bp_id, ctrl)
        assert key not in PP, 'ya aplicado en FORTESEQ2.amxd'
        PP[key] = [clean, clean, 0]
        ov[key] = {'parameter_longname': clean}

    print('fs2voice_adv.maxpat: +%s (v_rrate, live.numbox 0-64, local x=%g)' % (ctrl, LOCAL_X))
    print('  +%s (prepend setvoicerootrate #1) -> %s (outlet)' % (prep, OUTLET_ID))
    print('  %s (init outputvalue) -> %s' % (INIT_MSG_ID, ctrl))
    print('  +%s (receive FS2_ADV_ECHO) -> +%s (route #1) -> +%s (route rrate) -> +%s (prepend set) -> %s'
          % (rx, rt_v, rt_k, setrx, ctrl))
    print('FORTESEQ2.amxd: +%s (vah25 "R.Raiz" en x=%g), show en %s, hide en %d mensajes'
          % (vah, dev_x, VOCES4_MSG_ID, len(HIDE_MSG_IDS)))
    print('  parametros anidados nuevos: %d (V1..V4 R.Raiz)' % len(BPATCHER_IDS))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(VOICE, VOICE + '.before-rrate')
    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    shutil.copyfile(DEVICE, DEVICE + '.before-rrate')
    amxd.save(DEVICE, data, s, e, doc)

    pg2 = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert all(i in pbx2 for i in (ctrl, prep, rx, rt_v, rt_k, setrx))
    assert ctrl in pg2['parameters']

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert 'script show vah25' in bx2[VOCES4_MSG_ID]['text']
    for mid in HIDE_MSG_IDS:
        assert 'script hide vah25' in bx2[mid]['text'], mid
    for bp_id in BPATCHER_IDS:
        assert ('%s::%s' % (bp_id, ctrl)) in P2['parameters'], bp_id

    print('\nescrito %s y %s (.before-rrate guardado en ambos). Sigue:' % (VOICE, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice_adv.maxpat')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, el device completo, script stop/start')


main()
