"""Add a per-voice "Fijar" toggle (voiceKeyLock) next to TonProp/Set/Raiz on the "Voces 4" page.

    python tools/add_voice_key_lock.py            dry run, writes nothing
    python tools/add_voice_key_lock.py --apply    do it (device closed in Max AND Live)

forteseq2.js already carries the engine side (this session): voiceKeyLock[] + setvoicekeylock(),
consulted by advanceVoiceKeys() (`if (voiceKeyOwn[v] && !voiceKeyLock[v]) advanceVoiceOrder(v);`).
With TonProp on, a voice normally steps its own set once per shared-harmony change, following
whichever Orden (Cardinal/Forte/.../McKay Natural) is globally selected -- see
[[forteseq_slonimsky_ornament]]/[[forteseq_engine_roadmap]]. Fijar freezes JUST that stepping for
this one voice, without touching TonProp itself: the voice keeps sounding its own key (root,
register, cursor all still its own), just pinned at whichever set it is currently on, while other
TonProp voices keep walking their own procession. Independent of the global hard lock
(fs2setpick.js's swatch click / `locked`), which freezes the SHARED setIndex and is unaffected by
this flag either way.

## Why one more control on the EXISTING "Voces 4" page instead of a new page

Unlike Voces 3 and Voces 4 themselves (which needed a new page because the previous page's local
viewport was already full edge to edge), Voces 4's own content (TonProp 620, Set 638, Raiz 674-700)
leaves the rest of its 206px-wide viewport (up to absolute x=826) empty -- there is room for one
more small control without panning anything or touching Pagina/sel routers at all.

## What changes, file by file

**forteseq/fs2voice_adv.maxpat** (shared, x4 instances): 1 `live.toggle` ("V#1 Fijar") ->
`prepend setvoicekeylock #1` -> the bpatcher's outlet (obj-102), restored on load via the
bpatcher's own outputvalue fan (obj-101) -- same wiring convention add_voice_key.py used for
TonProp/Set/Raiz.

**forteseq/FORTESEQ2.amxd**: no Pagina/sel changes -- "Voces 4" already exists.
  * 1 new vah-style label ("Fij", vah23) shown only by obj-804 (Voces 4's own activation message).
  * obj-804 gains ", script show vah23".
  * obj-721 (Voces1), obj-722 (Voces2), obj-800 (Voces3) and obj-723 (every-other-tab default)
    gain ", script hide vah23" each. While doing this, also CLOSES a pre-existing gap found in the
    same message boxes: obj-721/obj-722 never got "hide vah17..22" when Voces3/Voces4 were built
    (checked directly -- those two strings simply do not contain "vah17".."vah22" at all), and
    obj-800 never got "hide vah20..22" when Voces4 was built. Left alone, switching FROM Voces3/4
    TO Voces1/2 (or from Voces4 to Voces3) would leave the newer tab's labels visibly stuck on
    screen, overlapping the older tab's own controls -- exactly the kind of voice-state-clarity bug
    this pass is meant to fix, and cheap to close while these exact boxes are already open.
  * 4 new nested params (1 control x 4 bpatcher instances), clean "V1 Fijar".."V4 Fijar" naming,
    same precedent as every previous Voces-N addition.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE = os.path.join('forteseq', 'fs2voice_adv.maxpat')

BPATCHER_IDS = ['obj-577', 'obj-578', 'obj-579', 'obj-580']   # V1..V4 instances of fs2voice_adv.maxpat
VOCES4_MSG_ID = 'obj-804'    # Voces 4's own activation message (shows vah20/21/22)
OTHER_TAB_MSG_IDS = ['obj-721', 'obj-722', 'obj-800', 'obj-723']   # Voces1, Voces2, Voces3, default/reject

NEW_TOGGLE_PRECT = [712.0, 3.0, 14.0, 14.0]   # 12px after Raiz (674+26=700), same row
NEW_VAH_ID = 'vah23'
NEW_VAH_LABEL = 'Fij'
NEW_VAH_PRECT = [554.0, 35.0, 24.0, 18.0]     # continues the vah20/21/22 (484/506/528, +2 gaps) sequence

# The pre-existing gap (see docstring): these two tabs never learned to hide vah17..22 when
# Voces3/Voces4 were added after them.
MISSING_HIDES = {
    'obj-721': ['vah17', 'vah18', 'vah19', 'vah20', 'vah21', 'vah22'],
    'obj-722': ['vah17', 'vah18', 'vah19', 'vah20', 'vah21', 'vah22'],
    'obj-800': ['vah20', 'vah21', 'vah22'],
}


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2voice_adv.maxpat -------------------------------------------------------------
    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx = {b['box']['id']: b['box'] for b in pg['boxes']}
    ppp = pg['parameters']
    assert pbx['obj-111']['saved_attribute_attributes']['valueof']['parameter_longname'] == 'V#1 TonProp'
    assert not any(b['box'].get('saved_attribute_attributes', {}).get('valueof', {})
                   .get('parameter_longname') == 'V#1 Fijar' for b in pg['boxes']), 'ya aplicado'

    pnid = [max(int(i.split('-')[1]) for i in pbx)]

    def pfresh():
        pnid[0] += 1
        return 'obj-%d' % pnid[0]

    def toggle(longname, annotation, prect):
        nid = pfresh()
        vo = {'parameter_longname': longname, 'parameter_shortname': longname.split(' ', 1)[1],
              'parameter_type': 2, 'parameter_modmode': 0, 'parameter_enum': ['off', 'on'],
              'parameter_mmax': 1, 'parameter_initial': [0], 'parameter_initial_enable': 1}
        pg['boxes'].append({'box': {
            'maxclass': 'live.toggle', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'parameter_enable': 1, 'varname': 'v_' + longname.split(' ', 1)[1].lower(),
            'annotation': annotation,
            'patching_rect': [400.0, 44.0 + 26.0 * len(pg['boxes']), 15.0, 14.0],
            'presentation': 1, 'presentation_rect': list(prect),
            'saved_attribute_attributes': {'valueof': vo}, 'id': nid}})
        ppp[nid] = [longname, longname, 0]
        return nid

    def prepend(msg):
        pid = pfresh()
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'varname': 'v_' + msg.split(' ')[0][3:] + '_prep',
            'patching_rect': [500.0, 410.0 + 30.0 * len(pg['boxes']), 220.0, 22.0],
            'text': 'prepend ' + msg + ' #1'}})
        return pid

    c_fij = toggle('V#1 Fijar', 'Si esta prendido, esta voz deja de avanzar su propio set (TonProp) en '
                    'cada cambio de armonia -- se queda sonando en el set que tiene ahora, en su propia '
                    'clave, mientras las demas voces con TonProp siguen su procesion. No apaga TonProp: '
                    'para volver a la armonia compartida hay que apagar TonProp, no Fijar. Independiente '
                    'del lock global (Fijar/Set del popup selector), que congela el set COMPARTIDO.',
                    NEW_TOGGLE_PRECT)
    p_fij = prepend('setvoicekeylock')

    pg['lines'].append({'patchline': {'source': [c_fij, 0], 'destination': [p_fij, 0]}})
    pg['lines'].append({'patchline': {'source': [p_fij, 0], 'destination': ['obj-102', 0]}})
    pg['lines'].append({'patchline': {'source': ['obj-101', 0], 'destination': [c_fij, 0]}})

    # ---- FORTESEQ2.amxd -------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    assert 'vah22' in bx[VOCES4_MSG_ID]['text'] and NEW_VAH_ID not in bx[VOCES4_MSG_ID]['text'], 'ya aplicado'

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    vah_id = fresh()
    P['boxes'].append({'box': {
        'id': vah_id, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
        'fontsize': 8.0, 'text': NEW_VAH_LABEL, 'varname': NEW_VAH_ID,
        'patching_rect': [2600.0, 2600.0, 60.0, 18.0],
        'presentation': 1, 'presentation_rect': list(NEW_VAH_PRECT)}})

    for mid, extra in MISSING_HIDES.items():
        bx[mid]['text'] = bx[mid]['text'] + ''.join(', script hide ' + v for v in extra)

    for mid in OTHER_TAB_MSG_IDS:
        bx[mid]['text'] = bx[mid]['text'] + ', script hide ' + NEW_VAH_ID
    bx[VOCES4_MSG_ID]['text'] = bx[VOCES4_MSG_ID]['text'] + ', script show ' + NEW_VAH_ID

    # nested params: 1 new control x 4 bpatcher instances, clean V1..V4 naming
    ov = PP['parameter_overrides']
    for vi, bp_id in enumerate(BPATCHER_IDS):
        clean = 'V%d Fijar' % (vi + 1)
        key = '%s::%s' % (bp_id, c_fij)
        PP[key] = [clean, clean, 0]
        ov[key] = {'parameter_longname': clean}

    print('fs2voice_adv.maxpat: +1 control (%s), +1 prepend (%s)' % (c_fij, p_fij))
    print('FORTESEQ2.amxd: +1 label (%s "%s")' % (vah_id, NEW_VAH_LABEL))
    print('%s: +", script show %s"' % (VOCES4_MSG_ID, NEW_VAH_ID))
    for mid in OTHER_TAB_MSG_IDS:
        extra = MISSING_HIDES.get(mid, [])
        print('%s: +", script hide %s"%s' % (
            mid, NEW_VAH_ID, (' + gap fix (hide %s)' % ', '.join(extra)) if extra else ''))
    print('parametros anidados nuevos: %d (1 control x 4 voces)' % len(BPATCHER_IDS))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    shutil.copyfile(DEVICE, DEVICE + '.before-voicekeylock')
    amxd.save(DEVICE, data, s, e, doc)

    pg2 = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert c_fij in pbx2

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    assert NEW_VAH_ID in bx2[VOCES4_MSG_ID]['text']
    for mid in OTHER_TAB_MSG_IDS:
        assert ('hide ' + NEW_VAH_ID) in bx2[mid]['text'], mid
    for bp_id in BPATCHER_IDS:
        assert ('%s::%s' % (bp_id, c_fij)) in P2['parameters'], bp_id

    print('\nescrito %s y %s (.before-voicekeylock del .amxd guardado). Sigue:' % (VOICE, DEVICE))
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, el device completo, script stop/start')


main()
