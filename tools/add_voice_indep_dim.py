"""Dim Div/Grado on the essential voice strip (fs2voice.maxpat) to reflect when they actually do
nothing, instead of leaving the user to guess from a stale tooltip.

## Why this exists

Div (obj-32) really is gated by "Voces Indep": voiceDiv is only read inside
emitVoicesIndependent() (forteseq2.js). Its annotation already says so correctly.

Grado (obj-30) is NOT gated by Indep the way its annotation claims ("Solo actua con Indep
encendido"). Reading emitVoices()/emitVoicesIndependent() in forteseq2.js:
  - Indep ON: voiceDegOffset is added unconditionally (~line 4873), in both Acordes and Arpegio.
  - Indep OFF: emitVoices() only adds it when haveCtx is true (~line 4205-4221), which is every
    Arpegio read (ctxPcs/ctxDeg are passed) but never Acordes (chordFor() hands emitVoices() a bare
    array with no ctx). See the comment right above emitVoices(): "instead of the offset being
    inert with Ind off" -- that fix predates this script and made the annotation stale.
  - So Grado is inert only when BOTH Indep is off AND mode is Acordes; any other combination works.
This script also rewrites obj-30's annotation to say that, instead of just adding a dial that
contradicts its own tooltip.

## Signal path

forteseq2.js already broadcasts both flags on every change, unconditionally, on outlet 4:
  setvoiceindep(x)  -> outlet(4, ["gecho", "indep", voiceIndep])   (forteseq2.js:2455-2457)
  setmode(m)        -> outlet(4, ["gecho", "mode", mode])          (forteseq2.js:1782-1786)

Both are already routed today, just not sent anywhere useful:
  - FORTESEQ2.amxd: obj-823 "route indep filtro lock dir root orntype orncount ornbase
    ornbasemode patron" -- outlet 0 fires the bare 0/1 for indep, currently wired only to
    obj-824 (prepend set -> the Indep toggle's own redisplay).
  - fs2pages.maxpat: obj-781 "route mode swing rasg dirrasg ratn rata ratprob ratcaida" --
    outlet 0 fires the bare 0/1 for mode, currently wired only to obj-782 (prepend set -> the
    Modo tab's own redisplay).

This script adds ONE new patchline off each of those EXISTING outlets (not a new route arg --
that would shift every later outlet index, see maxmsp-route-outlet-offbyone) into a new global
`send`: FS2_VOXINDEP / FS2_VOXMODE. fs2voice.maxpat (the per-voice bpatcher, instantiated x4 as
V1..V4) receives both globally -- the flags are device-wide, not per-voice, so every instance
reacts identically.

Inside fs2voice.maxpat: `sel 0 1` on the indep flag directly drives Div's overlay. Grado's
overlay needs indep OR mode, and both flags update asynchronously, so it uses the standard
Max idiom for combining two independently-updated values: two `+ 0` objects, each summing the
CURRENT value of both flags but triggered by a different one (so an update to either flag
recomputes the sum), feeding one shared `sel 0` (sum 0 = both off = inert = dim on; sum 1 or 2 =
active = dim off).

The dim itself is a `panel` (bgcolor grey, alpha ~0.55, ignoreclick 1 so it never blocks the
control underneath) sized exactly over the target's presentation_rect, toggled with
`thispatcher` "script show/hide <varname>" -- same mechanism already used elsewhere in this
device for tab paging (see add_hide_tabs.py), just scoped to fs2voice.maxpat's own patcher
instead of the parent's.

Deliberately NOT done here (out of scope, user confirmed): Largo/Pulso/Giro are not gated by
anything -- see forteseq2.js:4218 and :4848, both read via voiceSoundsAt() regardless of Indep --
so they get no overlay. What looked like them "not working" under Indep is fs2pages.maxpat (the
bpatcher holding Larg/Puls/Gir) being hidden by the Voces 1-4 tab's own `script hide fs2_pages`,
not an engine gate; FORTESEQ2.amxd:1713 says as much ("la pagina no apaga nada, solo elige que
mirar"). That's a separate, unresolved paging issue, not a dimming case.

    python tools/add_voice_indep_dim.py            dry run, writes nothing
    python tools/add_voice_indep_dim.py --apply    do it (device closed in Max AND Live)
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PAGES = os.path.join('forteseq', 'fs2pages.maxpat')
VOICE_ESS = os.path.join('forteseq', 'fs2voice.maxpat')

INDEP_ROUTE_ID = 'obj-823'   # FORTESEQ2.amxd: "route indep filtro lock dir root ..."
MODE_ROUTE_ID = 'obj-781'    # fs2pages.maxpat: "route mode swing rasg dirrasg ..."

DIV_ID = 'obj-32'     # fs2voice.maxpat: live.numbox "V#1 Div", varname v_div
GRADO_ID = 'obj-30'   # fs2voice.maxpat: live.numbox "V#1 Grado", varname v_grado

OLD_GRADO_ANNOTATION = (
    "Cuantos GRADOS del set queda esta voz por encima de su propia lectura. 0,1,2,3 en cuatro "
    "voces da un acorde a cuatro partes; negativo la pone debajo. Solo actua con Indep encendido."
)
NEW_GRADO_ANNOTATION = (
    "Cuantos GRADOS del set queda esta voz por encima de su propia lectura. 0,1,2,3 en cuatro "
    "voces da un acorde a cuatro partes; negativo la pone debajo. Actua siempre en Arpegio, y en "
    "Acordes solo si Indep esta encendido; con Acordes e Indep apagado queda inerte."
)


def patch_indep_tap(P):
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    route = bx[INDEP_ROUTE_ID]
    assert route['text'].startswith('route indep '), route['text']
    assert not any(l['patchline']['source'] == [INDEP_ROUTE_ID, 0]
                   and bx.get(l['patchline']['destination'][0], {}).get('text') == 'send FS2_VOXINDEP'
                   for l in P['lines']), 'ya aplicado'

    nid = max(int(i.split('-')[1]) for i in bx) + 1
    send_id = 'obj-%d' % nid
    P['boxes'].append({'box': {
        'id': send_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
        'varname': 'fs2_voxindep_tx', 'patching_rect': [3040.0, 3460.0, 140.0, 22.0],
        'text': 'send FS2_VOXINDEP'}})
    P['lines'].append({'patchline': {'source': [INDEP_ROUTE_ID, 0], 'destination': [send_id, 0]}})
    return send_id


def patch_mode_tap(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    route = bx[MODE_ROUTE_ID]
    assert route['text'].startswith('route mode '), route['text']
    assert not any(b['box'].get('varname') == 'fs2_voxmode_tx' for b in pg['boxes']), 'ya aplicado'

    nid = max(int(i.split('-')[1]) for i in bx) + 1
    send_id = 'obj-%d' % nid
    pg['boxes'].append({'box': {
        'id': send_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
        'varname': 'fs2_voxmode_tx', 'patching_rect': [900.0, 4470.0, 140.0, 22.0],
        'text': 'send FS2_VOXMODE'}})
    pg['lines'].append({'patchline': {'source': [MODE_ROUTE_ID, 0], 'destination': [send_id, 0]}})
    return send_id


def patch_voice_dim(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert bx[DIV_ID]['varname'] == 'v_div', bx[DIV_ID].get('varname')
    assert bx[GRADO_ID]['varname'] == 'v_grado', bx[GRADO_ID].get('varname')
    assert bx[GRADO_ID]['annotation'] == OLD_GRADO_ANNOTATION, 'anotacion de Grado ya cambio'
    assert not any(b['box'].get('varname') == 'v_dim_scripter' for b in pg['boxes']), 'ya aplicado'

    bx[GRADO_ID]['annotation'] = NEW_GRADO_ANNOTATION

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    py = [700.0]

    def step_y(h=26.0):
        py[0] += h
        return py[0]

    def newobj(text, numinlets, outlettype, x=700.0):
        oid = fresh()
        pg['boxes'].append({'box': {
            'id': oid, 'maxclass': 'newobj', 'numinlets': numinlets, 'numoutlets': len(outlettype),
            'outlettype': outlettype, 'patching_rect': [x, step_y(), 160.0, 22.0], 'text': text}})
        return oid

    def message(text, x=900.0):
        mid = fresh()
        pg['boxes'].append({'box': {
            'id': mid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
            'patching_rect': [x, step_y(), 180.0, 20.0], 'text': text}})
        return mid

    def dim_panel(varname, prect):
        pid = fresh()
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'panel', 'numinlets': 1, 'numoutlets': 0,
            'varname': varname, 'ignoreclick': 1, 'bgcolor': [0.5, 0.5, 0.5, 0.55],
            'border': 0.0, 'hidden': 0,
            'patching_rect': [1100.0, step_y(60.0), prect[2], prect[3]],
            'presentation': 1, 'presentation_rect': list(prect)}})
        return pid

    r_indep = newobj('receive FS2_VOXINDEP', 0, [''])
    r_mode = newobj('receive FS2_VOXMODE', 0, [''])

    # Div: gated by indep alone.
    sel_indep = newobj('sel 0 1', 1, ['bang', 'bang', ''])
    msg_div_show = message('script show v_div_dim')   # indep == 0 -> Div inert -> dim on
    msg_div_hide = message('script hide v_div_dim')    # indep == 1 -> Div active -> dim off

    # Grado: gated by (indep OR mode). Two `+` objects so either flag changing recomputes the
    # sum with the other flag's latest value -- the standard Max idiom for OR-ing two
    # asynchronously-updated values without a dedicated state object.
    plus_a = newobj('+ 0', 2, [''])   # hot=indep, cold=mode
    plus_b = newobj('+ 0', 2, [''])   # hot=mode, cold=indep
    sel_grado = newobj('sel 0', 1, ['bang', ''])
    msg_grado_show = message('script show v_grado_dim')   # sum == 0 -> inert -> dim on
    msg_grado_hide = message('script hide v_grado_dim')    # sum >= 1 -> active -> dim off

    scripter = fresh()
    pg['boxes'].append({'box': {
        'id': scripter, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
        'varname': 'v_dim_scripter', 'patching_rect': [700.0, step_y(), 100.0, 22.0],
        'text': 'thispatcher'}})

    dim_div = dim_panel('v_div_dim', bx[DIV_ID]['presentation_rect'])
    dim_grado = dim_panel('v_grado_dim', bx[GRADO_ID]['presentation_rect'])

    L = pg['lines']
    L.append({'patchline': {'source': [r_indep, 0], 'destination': [sel_indep, 0]}})
    L.append({'patchline': {'source': [sel_indep, 0], 'destination': [msg_div_show, 0]}})
    L.append({'patchline': {'source': [sel_indep, 1], 'destination': [msg_div_hide, 0]}})
    L.append({'patchline': {'source': [msg_div_show, 0], 'destination': [scripter, 0]}})
    L.append({'patchline': {'source': [msg_div_hide, 0], 'destination': [scripter, 0]}})

    L.append({'patchline': {'source': [r_indep, 0], 'destination': [plus_a, 0]}})
    L.append({'patchline': {'source': [r_mode, 0], 'destination': [plus_a, 1]}})
    L.append({'patchline': {'source': [r_mode, 0], 'destination': [plus_b, 0]}})
    L.append({'patchline': {'source': [r_indep, 0], 'destination': [plus_b, 1]}})
    L.append({'patchline': {'source': [plus_a, 0], 'destination': [sel_grado, 0]}})
    L.append({'patchline': {'source': [plus_b, 0], 'destination': [sel_grado, 0]}})
    L.append({'patchline': {'source': [sel_grado, 0], 'destination': [msg_grado_show, 0]}})
    L.append({'patchline': {'source': [sel_grado, 1], 'destination': [msg_grado_hide, 0]}})
    L.append({'patchline': {'source': [msg_grado_show, 0], 'destination': [scripter, 0]}})
    L.append({'patchline': {'source': [msg_grado_hide, 0], 'destination': [scripter, 0]}})

    return dim_div, dim_grado


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    indep_send = patch_indep_tap(doc['patcher'])

    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
    mode_send = patch_mode_tap(pg)

    pg_ess = json.load(open(VOICE_ESS, encoding='utf-8'))['patcher']
    dim_div, dim_grado = patch_voice_dim(pg_ess)

    print('FORTESEQ2.amxd: %s outlet 0 -> +%s (send FS2_VOXINDEP)' % (INDEP_ROUTE_ID, indep_send))
    print('fs2pages.maxpat: %s outlet 0 -> +%s (send FS2_VOXMODE)' % (MODE_ROUTE_ID, mode_send))
    print('fs2voice.maxpat: +%s (dim over Div), +%s (dim over Grado)' % (dim_div, dim_grado))
    print('fs2voice.maxpat: Grado annotation corrected (no longer claims Indep-only)')

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-voxdim')
    shutil.copyfile(PAGES, PAGES + '.before-voxdim')
    shutil.copyfile(VOICE_ESS, VOICE_ESS + '.before-voxdim')

    amxd.save(DEVICE, data, s, e, doc)
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    with open(VOICE_ESS, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_ess}, f, indent=1)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    assert indep_send in bx2

    print('\nescrito %s, %s, %s (.before-voxdim guardados). Sigue:' % (DEVICE, PAGES, VOICE_ESS))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat forteseq/fs2voice.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo (bpatchers no recargan solos)')
    print('  probar: Indep off = Div ensombrecido; Acordes+Indep off = Grado ensombrecido; cualquier otra combinacion, ambos activos')


main()
