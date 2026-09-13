"""Add per-voice own-key/tonality controls (TonProp/Set/Raiz for THIS voice) as a new "Voces 4"
page -- Bitonal / Polytonal Scales & Arpeggios (Thesaurus, Level 2).

    python tools/add_voice_key.py            dry run, writes nothing
    python tools/add_voice_key.py --apply    do it (device closed in Max AND Live)

forteseq2.js already carries the engine side (this session): voiceKeyOwn[]/voiceSetIndex[]/
voiceRootOffset[] + setvoicekeyown/setvoicesetindex/setvoicerootoffset, read by voicePcsFor()/
voiceRootFor() from the two self-cursored paths (triggervoice, emitVoicesIndependent) and mirrored
in peekVoiceNote() for the horizon/colmon lookahead. With TonProp on, a voice ignores the shared
setIndex/effRoot() and plays its OWN set at its OWN crude root transpose -- a genuinely different
key sounding alongside the shared harmony. The shared-clock Arpegio/Acordes path (emitVoices())
still hands every voice the SAME resolved note by design, so TonProp only does anything under
Voces Indep or an external trigger, exactly like Propia (Lectura) and the per-voice ornament shape
before it.

## Why a 4th page instead of fitting into "Voces 3"

Same reasoning as Voces 3 itself: "Voces 1"/"Voces 2" tile the bpatcher's fixed-width viewport
edge to edge, and Voces 3's own 3 controls (OrnTipo/OrnNotas/OrnBase) already fill the strip that
opens up right after them (local x 412-488). Appending TonProp/Set/Raiz there would need a wider
shared window, which pans the SAME canvas for every page -- widening it always reveals whatever
sits in the newly exposed strip, for every existing offset. A 4th page/offset keeps Voces 1-3
byte-identical.

## What changes, file by file

**forteseq/fs2voice_adv.maxpat** (shared, x4 instances): 1 `live.toggle` ("V#1 TonProp") + 2
`live.numbox` ("V#1 Set" 1-351, "V#1 Raiz" -24..24) -- each -> its own `prepend setvoice... #1`
-> the bpatcher's outlet (`obj-102`), restored on load via the bpatcher's own `outputvalue` fan
(`obj-101`), exactly like every existing control in this strip.

**forteseq/FORTESEQ2.amxd**:
  * "Pagina" (`obj-485`) gains an 11th item, "Voces 4", appended after "Voces 3" (not inserted
    earlier) so nothing before it needs renumbering.
  * `obj-486` (`sel 0..9`, routes `fs2_pages`'s scroll offset per tab) grows to `sel 0..10`; the
    new match (value 10) reuses the existing "park fs2_pages off-screen" message (`obj-581`).
  * `obj-582` (`sel 6 7 9`, the actual Voces1/2/3 <-> fs2_pages swap) grows to `sel 6 7 9 10`. This
    is an insert before the reject outlet again, so its reject wire (-> `obj-723`) moves from
    outlet 3 to outlet 4 -- the one place an existing wire's outlet index is re-pointed.
  * A new activation message parks `fs2_pages`, shows/fronts `vadv1..4` at `offset -510 0` (the 3
    new columns start at local x=510 -- 22px after Voces 3's own content, which stops at 488, same
    gap Voces 3 itself left after Voces 2), hides every existing vah label and shows 3 new ones
    (`vah20..22`, "Ton"/"Set"/"Raiz"). `obj-723` gains 3 more `script hide vah20/21/22` clauses.
  * 12 new nested params (3 controls x 4 bpatcher instances) get explicit `parameter_overrides`
    with clean "V1 TonProp".."V4 Raiz" naming, same precedent as Voces 3's Orn controls.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE = os.path.join('forteseq', 'fs2voice_adv.maxpat')

PAGINA_ID = 'obj-485'
SEL_PAGE_ID = 'obj-486'     # sel 0..9, routes fs2_pages' own scroll offset
SEL_VOCES_ID = 'obj-582'    # sel 6 7 9, the actual Voces1/2/3 <-> fs2_pages swap
PARK_MSG_ID = 'obj-581'     # script sendbox fs2_pages offset 0 -900 (shared by 6/7/9 already)
DEFAULT_MSG_ID = 'obj-723'  # script show fs2_pages, hide vadv1-4, hide every vah label
THISPATCHER_ID = 'obj-487'
BPATCHER_IDS = ['obj-577', 'obj-578', 'obj-579', 'obj-580']   # V1..V4 instances of fs2voice_adv.maxpat

NEW_OFFSET = -510.0
VAH_LABELS = [('Ton', 20.0), ('Set', 20.0), ('Raiz', 24.0)]
VAH_Y = 35.0
VAH_X0 = 484.0   # same absolute slot every vah page-label already shares -- mutually exclusive by show/hide


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2voice_adv.maxpat -------------------------------------------------------------
    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx = {b['box']['id']: b['box'] for b in pg['boxes']}
    ppp = pg['parameters']
    assert pbx['obj-105']['saved_attribute_attributes']['valueof']['parameter_longname'] == 'V#1 OrnTipo'
    assert not any(b['box'].get('saved_attribute_attributes', {}).get('valueof', {})
                   .get('parameter_longname') == 'V#1 TonProp' for b in pg['boxes']), 'ya aplicado'

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

    def numbox(longname, annotation, prect, mmin, mmax, initial=0):
        nid = pfresh()
        vo = {'parameter_longname': longname, 'parameter_shortname': longname.split(' ', 1)[1],
              'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_modmode': 4,
              'parameter_mmin': float(mmin), 'parameter_mmax': float(mmax),
              'parameter_initial': [initial], 'parameter_initial_enable': 1}
        pg['boxes'].append({'box': {
            'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2, 'outlettype': ['', 'float'],
            'parameter_enable': 1, 'varname': 'v_' + longname.split(' ', 1)[1].lower(),
            'annotation': annotation,
            'patching_rect': [400.0, 44.0 + 26.0 * len(pg['boxes']), 34.0, 15.0],
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

    ANN_SUFFIX = (' cuando esta voz tiene TonProp; el resto del tiempo esta voz sigue la armonia '
                  'compartida (setIndex/Raiz globales).')
    c_ton = toggle('V#1 TonProp', 'Si esta prendido, esta voz deja de mirar el Set/Raiz globales y '
                    'toca en su PROPIA clave (Bitonal/Polytonal) -- solo tiene efecto bajo Voces '
                    'Indep o disparo externo, igual que LecProp. Apagado (por defecto) es '
                    'exactamente el comportamiento de siempre.', [510.0, 3.0, 14.0, 14.0])
    c_set = numbox('V#1 Set', 'Set propio (1-351) de esta voz,' + ANN_SUFFIX,
                    [528.0, 3.0, 32.0, 15.0], mmin=1, mmax=351, initial=1)
    c_raiz = numbox('V#1 Raiz', 'Transposicion cruda (semitonos) propia de esta voz,' + ANN_SUFFIX,
                     [564.0, 3.0, 26.0, 15.0], mmin=-24, mmax=24, initial=0)
    p_ton = prepend('setvoicekeyown')
    p_set = prepend('setvoicesetindex')
    p_raiz = prepend('setvoicerootoffset')

    for ctrl, prep in [(c_ton, p_ton), (c_set, p_set), (c_raiz, p_raiz)]:
        pg['lines'].append({'patchline': {'source': [ctrl, 0], 'destination': [prep, 0]}})
        pg['lines'].append({'patchline': {'source': [prep, 0], 'destination': ['obj-102', 0]}})
        pg['lines'].append({'patchline': {'source': ['obj-101', 0], 'destination': [ctrl, 0]}})

    # ---- FORTESEQ2.amxd -------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    pag = bx[PAGINA_ID]['saved_attribute_attributes']['valueof']
    assert pag['parameter_enum'][-1] == 'Voces 3' and pag['parameter_mmax'] == 9, pag
    sel_page = bx[SEL_PAGE_ID]
    assert sel_page['text'] == 'sel 0 1 2 3 4 5 6 7 8 9', sel_page['text']
    sel_voces = bx[SEL_VOCES_ID]
    assert sel_voces['text'] == 'sel 6 7 9', sel_voces['text']
    default_msg = bx[DEFAULT_MSG_ID]
    assert 'vah20' not in default_msg['text'], 'ya aplicado'

    pag['parameter_enum'] = pag['parameter_enum'] + ['Voces 4']
    pag['parameter_mmax'] = 10

    sel_page['text'] = 'sel 0 1 2 3 4 5 6 7 8 9 10'
    sel_page['numinlets'] = 12
    sel_page['numoutlets'] = 12
    sel_page['outlettype'] = ['bang'] * 11 + ['']

    sel_voces['text'] = 'sel 6 7 9 10'
    sel_voces['numinlets'] = 5
    sel_voces['numoutlets'] = 5
    sel_voces['outlettype'] = ['bang', 'bang', 'bang', 'bang', '']

    # move the one existing wire whose outlet index actually shifts (reject: 3 -> 4)
    moved = False
    for l in P['lines']:
        pl = l['patchline']
        if pl['source'] == [SEL_VOCES_ID, 3] and pl['destination'] == [DEFAULT_MSG_ID, 0]:
            pl['source'] = [SEL_VOCES_ID, 4]
            moved = True
    assert moved, 'no se encontro el cable de reject de obj-582 para reubicar'

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    x = VAH_X0
    vah_names = []
    for i, (label, w) in enumerate(VAH_LABELS):
        vid = fresh()
        P['boxes'].append({'box': {
            'id': vid, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
            'fontsize': 8.0, 'text': label, 'varname': 'vah%d' % (20 + i),
            'patching_rect': [2600.0, 2500.0 + 20.0 * i, 60.0, 18.0],
            'presentation': 1, 'presentation_rect': [x, VAH_Y, w, 18.0]}})
        vah_names.append('vah%d' % (20 + i))
        x += w + 2.0

    voces4_lines = ['script hide fs2_pages']
    for b in ['vadv1', 'vadv2', 'vadv3', 'vadv4']:
        voces4_lines.append('script show ' + b)
    for b in ['vadv1', 'vadv2', 'vadv3', 'vadv4']:
        voces4_lines.append('script front ' + b)
    for b in ['vadv1', 'vadv2', 'vadv3', 'vadv4']:
        voces4_lines.append('script sendbox %s offset %g 0' % (b, NEW_OFFSET))
    for i in range(1, 17):
        voces4_lines.append('script hide vah%d' % i)
    for i in range(17, 20):
        voces4_lines.append('script hide vah%d' % i)
    for name in vah_names:
        voces4_lines.append('script show ' + name)
    voces4_msg_text = ', '.join(voces4_lines)

    voces4_msg = fresh()
    P['boxes'].append({'box': {
        'id': voces4_msg, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'linecount': 9, 'patching_rect': [1250.0, 1330.0, 970.0, 145.0], 'text': voces4_msg_text}})

    default_msg['text'] = default_msg['text'] + ''.join(', script hide ' + n for n in vah_names)

    P['lines'].append({'patchline': {'source': [SEL_PAGE_ID, 10], 'destination': [PARK_MSG_ID, 0]}})
    P['lines'].append({'patchline': {'source': [SEL_VOCES_ID, 3], 'destination': [voces4_msg, 0]}})
    P['lines'].append({'patchline': {'source': [voces4_msg, 0], 'destination': [THISPATCHER_ID, 0]}})

    # nested params: 3 new controls x 4 bpatcher instances, clean V1..V4 naming
    ov = PP['parameter_overrides']
    inner_by_longname = {'V#1 TonProp': c_ton, 'V#1 Set': c_set, 'V#1 Raiz': c_raiz}
    for vi, bp_id in enumerate(BPATCHER_IDS):
        for raw_longname, inner in inner_by_longname.items():
            clean = 'V%d %s' % (vi + 1, raw_longname.split(' ', 1)[1])
            key = '%s::%s' % (bp_id, inner)
            PP[key] = [clean, clean, 0]
            ov[key] = {'parameter_longname': clean}

    print('Pagina: enum 10 -> 11 (+Voces 4), mmax 9 -> 10')
    print('sel 0..9 -> sel 0..10 (nuevo outlet 10 -> %s)' % PARK_MSG_ID)
    print('sel 6 7 9 -> sel 6 7 9 10 (reject reubicado outlet 3 -> 4, nuevo outlet 3 -> %s)' % voces4_msg)
    print('%s: +3 clausulas hide vah20/21/22' % DEFAULT_MSG_ID)
    print('fs2voice_adv.maxpat: +3 controles (%s %s %s), +3 prepends' % (c_ton, c_set, c_raiz))
    print('parametros anidados nuevos: %d (3 controles x 4 voces)' % (3 * len(BPATCHER_IDS)))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    pg2 = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert c_ton in pbx2 and c_set in pbx2 and c_raiz in pbx2

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    pag2 = bx2[PAGINA_ID]['saved_attribute_attributes']['valueof']
    assert pag2['parameter_enum'][-1] == 'Voces 4' and pag2['parameter_mmax'] == 10
    assert bx2[SEL_PAGE_ID]['text'] == 'sel 0 1 2 3 4 5 6 7 8 9 10'
    assert bx2[SEL_VOCES_ID]['text'] == 'sel 6 7 9 10'
    for bp_id in BPATCHER_IDS:
        for inner in (c_ton, c_set, c_raiz):
            assert ('%s::%s' % (bp_id, inner)) in P2['parameters'], (bp_id, inner)

    print('\nescrito %s y %s (.before del .amxd guardado). Sigue:' % (VOICE, DEVICE))
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, el device completo, script stop/start')


main()
