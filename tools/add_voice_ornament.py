"""Add per-voice ornament shape controls (Orn Tipo/Notas/Base for THIS voice) as a new "Voces 3"
page, plus the 3 engine-side setters' Live surface.

    python tools/add_voice_ornament.py            dry run, writes nothing
    python tools/add_voice_ornament.py --apply    do it (device closed in Max AND Live)

forteseq2.js already carries the engine side (this session, same as Quadritonal/Serie before it):
voiceOrnType[]/voiceOrnCount[]/voiceOrnBase[] + setvoiceorntype/setvoiceorncount/setvoiceornbase,
read by voiceOrnamentPitchAt() whenever a voice has Propia on AND its own Patron is Ornamento --
otherwise every voice keeps reading the shared ornament exactly as before. This fixes the actual
scope of the old "per-voice ornament" backlog item, corrected earlier this session: the per-voice
Patron/Dir override (voiceReadOwn/voiceReadMode/voiceReadDir) was ALREADY built and wired, in
fs2voice_adv.maxpat -- only the ornament SHAPE (Tipo/Notas/Base) was still global. The base LAYOUT
(Orn Base Modo/Paso/Cuarteto/Serie) stays shared on purpose -- out of scope, see the Fase 2 backlog
note in forteseq_slonimsky_ornament.md.

## Why a new page instead of fitting into "Voces 1"/"Voces 2"

Those two already tile the bpatcher's fixed-width viewport edge to edge (8 columns each, 0-202 /
204-390 in the bpatcher's own coordinate space, panned into view via `script sendbox vadv# offset
...` on the SAME shared window width). Widening that shared width to fit 3 more columns would leak
into both existing views (the viewport is a pan+width window over ONE canvas -- widening it always
reveals whatever sits in the newly exposed strip, for every offset). Appending the new controls
further right and giving them their own page/offset keeps "Voces 1"/"Voces 2" byte-identical.

## What changes, file by file

**forteseq/fs2voice_adv.maxpat** (one shared file, instantiated x4 in the device -- one edit
reaches all four voices): 3 new `live.numbox`es -- "V#1 OrnTipo" (enum, mmax 5, like the global
Orn Tipo menu), "V#1 OrnNotas" (1-4), "V#1 OrnBase" (1-14) -- each -> its own `prepend
setvoiceorn... #1` -> the bpatcher's outlet (`obj-102`, "-> fs2_gen"), restored on load via the
bpatcher's own `outputvalue` fan (`obj-101`, `va_init_msg`) exactly like every existing control in
this strip.

**forteseq/FORTESEQ2.amxd**:
  * "Pagina" (`obj-485`) gains a 10th item, "Voces 3", APPENDED after "Globales" (not inserted
    between "Voces 2" and "Globales") specifically so `obj-617`'s existing `sel 8` (Globales) needs
    no renumbering -- purely additive at the tab-selector level.
  * `obj-486` (`sel 0..8`, routes `fs2_pages`'s scroll offset per tab) grows to `sel 0..9`; the new
    match (value 9) reuses the existing "park fs2_pages off-screen" message (`obj-581`) that values
    6/7 already share -- Voces 3, like Voces 1/2, replaces `fs2_pages` with the voice grid.
  * `obj-582` (`sel 6 7`, the ONE place that actually swaps in the voice-advanced grid) grows to
    `sel 6 7 9`. This IS an insert before the reject outlet, so its existing reject wire (->
    `obj-723`, the "restore fs2_pages" default) moves from outlet 2 to outlet 3 -- the one place in
    this whole change where an existing wire's outlet index has to be explicitly re-pointed rather
    than just adding a new one.
  * A new activation message parks `fs2_pages`, shows `vadv1..4` at `offset -412 0` (the 3 new
    columns start at local x=412 -- right after "Voces 2"'s own content, which already stops at
    390, leaving a clean 22px gap before the new page even starts), hides every existing vah label
    (`vah1..16`) and shows the 3 new ones (`vah17..19`, "Tipo"/"Notas"/"Base" -- same shorthand the
    global Ornamento column already uses). `obj-723` (shown for every OTHER tab) gains 3 more
    `script hide vah17/18/19` clauses so leaving Voces 3 correctly clears them too.
  * The 12 new nested params (3 controls x 4 bpatcher instances) get explicit `parameter_overrides`
    with clean "V1 OrnTipo".."V4 OrnTipo" naming -- mirroring the GOOD precedent already in this
    file (`V1 Oct`..`V4 Oct`), not the messier auto-disambiguated "[N]" suffix that a couple of
    older per-voice controls ended up with because nobody set an explicit override for them.

Run `tools/fix_device_height.py` first if it has not already landed (unrelated bug, but the two
change the same file this session) -- this script does not touch `openrect`.
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
SEL_PAGE_ID = 'obj-486'     # sel 0..8, routes fs2_pages' own scroll offset
SEL_VOCES_ID = 'obj-582'    # sel 6 7, the actual Voces1/2 <-> fs2_pages swap
PARK_MSG_ID = 'obj-581'     # script sendbox fs2_pages offset 0 -900 (shared by 6 and 7 already)
DEFAULT_MSG_ID = 'obj-723'  # script show fs2_pages, hide vadv1-4, hide vah1-16
THISPATCHER_ID = 'obj-487'
BPATCHER_IDS = ['obj-577', 'obj-578', 'obj-579', 'obj-580']   # V1..V4 instances of fs2voice_adv.maxpat

NEW_OFFSET = -412.0
VAH_LABELS = [('Tipo', 24.0), ('Notas', 30.0), ('Base', 24.0)]   # matches the global Ornamento column's shorthand
VAH_Y = 35.0
VAH_X0 = 484.0   # same absolute slot vah1/vah6/vah14 already share -- mutually exclusive by show/hide


def main():
    apply_it = '--apply' in sys.argv

    # ---- fs2voice_adv.maxpat -------------------------------------------------------------
    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx = {b['box']['id']: b['box'] for b in pg['boxes']}
    ppp = pg['parameters']
    assert pbx['obj-45']['saved_attribute_attributes']['valueof']['parameter_longname'] == 'V#1 Patron'
    assert not any(b['box'].get('saved_attribute_attributes', {}).get('valueof', {})
                   .get('parameter_longname') == 'V#1 OrnTipo' for b in pg['boxes']), 'ya aplicado'

    pnid = [max(int(i.split('-')[1]) for i in pbx)]

    def pfresh():
        pnid[0] += 1
        return 'obj-%d' % pnid[0]

    def numbox(longname, annotation, prect, enum=None, mmin=None, mmax=None, initial=0):
        nid = pfresh()
        vo = {'parameter_longname': longname, 'parameter_shortname': longname.split(' ', 1)[1],
              'parameter_type': 2 if enum else 1, 'parameter_unitstyle': 9 if enum else 0,
              'parameter_modmode': 0 if enum else 4,
              'parameter_initial': [initial], 'parameter_initial_enable': 1}
        if enum:
            vo['parameter_enum'] = list(enum)
            vo['parameter_mmax'] = len(enum) - 1
        else:
            vo['parameter_mmin'] = float(mmin)
            vo['parameter_mmax'] = float(mmax)
        pg['boxes'].append({'box': {
            'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2, 'outlettype': ['', 'float'],
            'parameter_enable': 1, 'varname': 'v_' + longname.split(' ', 1)[1].lower(),
            'annotation': annotation,
            'patching_rect': [400.0, 44.0 + 26.0 * len(pg['boxes']), 30.0, 15.0],
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

    ORN_TYPE_ENUM = ['Interp', 'Infra', 'Ultra', 'Infra-Inter', 'Infra-Ultra', 'Inf-Int-Ult']
    ANN_SUFFIX = ' cuando esta voz tiene Propia + Patron = Ornamento; el resto del tiempo se ignora.'
    c_tipo = numbox('V#1 OrnTipo', 'Tipo de ornamento propio de esta voz,' + ANN_SUFFIX,
                     [412.0, 3.0, 24.0, 15.0], enum=ORN_TYPE_ENUM)
    c_notas = numbox('V#1 OrnNotas', 'Notas de ornamento (1-4) propias de esta voz,' + ANN_SUFFIX,
                      [438.0, 3.0, 24.0, 15.0], mmin=1, mmax=4, initial=1)
    c_base = numbox('V#1 OrnBase', 'Intervalo base (1-14 st) propio de esta voz,' + ANN_SUFFIX,
                     [464.0, 3.0, 24.0, 15.0], mmin=1, mmax=14, initial=4)
    p_tipo = prepend('setvoiceorntype')
    p_notas = prepend('setvoiceorncount')
    p_base = prepend('setvoiceornbase')

    for ctrl, prep in [(c_tipo, p_tipo), (c_notas, p_notas), (c_base, p_base)]:
        pg['lines'].append({'patchline': {'source': [ctrl, 0], 'destination': [prep, 0]}})
        pg['lines'].append({'patchline': {'source': [prep, 0], 'destination': ['obj-102', 0]}})
        pg['lines'].append({'patchline': {'source': ['obj-101', 0], 'destination': [ctrl, 0]}})

    # ---- FORTESEQ2.amxd -------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    PP = P['parameters']

    pag = bx[PAGINA_ID]['saved_attribute_attributes']['valueof']
    assert pag['parameter_enum'][-1] == 'Globales' and pag['parameter_mmax'] == 8, pag
    sel_page = bx[SEL_PAGE_ID]
    assert sel_page['text'] == 'sel 0 1 2 3 4 5 6 7 8', sel_page['text']
    sel_voces = bx[SEL_VOCES_ID]
    assert sel_voces['text'] == 'sel 6 7', sel_voces['text']
    default_msg = bx[DEFAULT_MSG_ID]
    assert 'vah17' not in default_msg['text'], 'ya aplicado'

    pag['parameter_enum'] = pag['parameter_enum'] + ['Voces 3']
    pag['parameter_mmax'] = 9

    sel_page['text'] = 'sel 0 1 2 3 4 5 6 7 8 9'
    sel_page['numinlets'] = 11
    sel_page['numoutlets'] = 11
    sel_page['outlettype'] = ['bang'] * 10 + ['']

    sel_voces['text'] = 'sel 6 7 9'
    sel_voces['numinlets'] = 4
    sel_voces['numoutlets'] = 4
    sel_voces['outlettype'] = ['bang', 'bang', 'bang', '']

    # move the one existing wire whose outlet index actually shifts (reject: 2 -> 3)
    moved = False
    for l in P['lines']:
        pl = l['patchline']
        if pl['source'] == [SEL_VOCES_ID, 2] and pl['destination'] == [DEFAULT_MSG_ID, 0]:
            pl['source'] = [SEL_VOCES_ID, 3]
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
            'fontsize': 8.0, 'text': label, 'varname': 'vah%d' % (17 + i),
            'patching_rect': [2600.0, 2400.0 + 20.0 * i, 60.0, 18.0],
            'presentation': 1, 'presentation_rect': [x, VAH_Y, w, 18.0]}})
        vah_names.append('vah%d' % (17 + i))
        x += w + 2.0

    voces3_lines = ['script hide fs2_pages']
    for b in ['vadv1', 'vadv2', 'vadv3', 'vadv4']:
        voces3_lines.append('script show ' + b)
    for b in ['vadv1', 'vadv2', 'vadv3', 'vadv4']:
        voces3_lines.append('script front ' + b)
    for b in ['vadv1', 'vadv2', 'vadv3', 'vadv4']:
        voces3_lines.append('script sendbox %s offset %g 0' % (b, NEW_OFFSET))
    for i in range(1, 17):
        voces3_lines.append('script hide vah%d' % i)
    for name in vah_names:
        voces3_lines.append('script show ' + name)
    voces3_msg_text = ', '.join(voces3_lines)

    voces3_msg = fresh()
    P['boxes'].append({'box': {
        'id': voces3_msg, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'linecount': 8, 'patching_rect': [1250.0, 1180.0, 970.0, 130.0], 'text': voces3_msg_text}})

    default_msg['text'] = default_msg['text'] + ''.join(', script hide ' + n for n in vah_names)

    P['lines'].append({'patchline': {'source': [SEL_PAGE_ID, 9], 'destination': [PARK_MSG_ID, 0]}})
    P['lines'].append({'patchline': {'source': [SEL_VOCES_ID, 2], 'destination': [voces3_msg, 0]}})
    P['lines'].append({'patchline': {'source': [voces3_msg, 0], 'destination': [THISPATCHER_ID, 0]}})

    # nested params: 3 new controls x 4 bpatcher instances, clean V1..V4 naming (not the "[N]"
    # auto-disambiguation quirk a couple of older controls ended up with)
    ov = PP['parameter_overrides']
    inner_by_longname = {'V#1 OrnTipo': c_tipo, 'V#1 OrnNotas': c_notas, 'V#1 OrnBase': c_base}
    for vi, bp_id in enumerate(BPATCHER_IDS):
        for raw_longname, inner in inner_by_longname.items():
            clean = 'V%d %s' % (vi + 1, raw_longname.split(' ', 1)[1])
            key = '%s::%s' % (bp_id, inner)
            PP[key] = [clean, clean, 0]
            ov[key] = {'parameter_longname': clean}

    print('Pagina: enum 9 -> 10 (+Voces 3), mmax 8 -> 9')
    print('sel 0..8 -> sel 0..9 (nuevo outlet 9 -> %s)' % PARK_MSG_ID)
    print('sel 6 7 -> sel 6 7 9 (reject reubicado outlet 2 -> 3, nuevo outlet 2 -> %s)' % voces3_msg)
    print('%s: +3 clausulas hide vah17/18/19' % DEFAULT_MSG_ID)
    print('fs2voice_adv.maxpat: +3 controles (%s %s %s), +3 prepends' % (c_tipo, c_notas, c_base))
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
    assert c_tipo in pbx2 and c_notas in pbx2 and c_base in pbx2

    _, _, _, doc2 = amxd.load(DEVICE)
    P2 = doc2['patcher']
    bx2 = {b['box']['id']: b['box'] for b in P2['boxes']}
    pag2 = bx2[PAGINA_ID]['saved_attribute_attributes']['valueof']
    assert pag2['parameter_enum'][-1] == 'Voces 3' and pag2['parameter_mmax'] == 9
    assert bx2[SEL_PAGE_ID]['text'] == 'sel 0 1 2 3 4 5 6 7 8 9'
    assert bx2[SEL_VOCES_ID]['text'] == 'sel 6 7 9'
    for bp_id in BPATCHER_IDS:
        for inner in (c_tipo, c_notas, c_base):
            assert ('%s::%s' % (bp_id, inner)) in P2['parameters'], (bp_id, inner)

    print('\nescrito %s y %s (.before del .amxd guardado). Sigue:' % (VOICE, DEVICE))
    print('  python tools/check_structure.py')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, el device completo, script stop/start')


main()
