"""Add a per-voice Salto Coprimo ("Salto" numbox, 1-11) to the "Voces 3" page.

    python tools/add_voice_coprime.py            dry run, writes nothing
    python tools/add_voice_coprime.py --apply    do it (device closed in Max AND Live)

Engine side (forteseq2.js) already carries voiceCoprimeSkip[] + setvoicecoprime, read by degreeAt()
only while the voice has Lec propia and its own Patron is Coprimo; otherwise the shared
coprimeSkip applies as before. The Horizonte popup (fs2horizon.js) shows the chip only in that case.

fs2voice_adv.maxpat (one file, instantiated x4): + live.numbox "V#1 CopSalto" -> `prepend
setvoicecoprime #1` -> obj-102, restored on load by obj-101 (outputvalue fan), and the popup's echo
("copsk") appended as the LAST token of `route` obj-201 (new match outlet = 15, the old reject) ->
`prepend set` -> the numbox. Appended, not inserted, so no existing outlet index shifts.

FORTESEQ2.amxd: + comment "vah24" ("Salto"), shown by the Voces 3 activation message (obj-800) and
hidden by every other one; + 4 nested params with clean "V1 CopSalto".."V4 CopSalto" names.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE = os.path.join('forteseq', 'fs2voice_adv.maxpat')
BPATCHER_IDS = ['obj-577', 'obj-578', 'obj-579', 'obj-580']
VOCES3_MSG = 'obj-800'
ROUTE_ID = 'obj-201'
LONGNAME = 'V#1 CopSalto'


def main():
    apply_it = '--apply' in sys.argv

    pg = json.load(open(VOICE, encoding='utf-8'))['patcher']
    pbx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert 'copsk' not in pbx[ROUTE_ID]['text'], 'ya aplicado'
    assert pbx[ROUTE_ID]['text'].endswith('artdur artsil') and pbx[ROUTE_ID]['numoutlets'] == 16
    assert not any(l['patchline']['source'] == [ROUTE_ID, 15] for l in pg['lines']), 'reject cableado'
    nid = max(int(i.split('-')[1]) for i in pbx)

    def fresh():
        nonlocal nid
        nid += 1
        return 'obj-%d' % nid

    num = fresh()
    vo = {'parameter_longname': LONGNAME, 'parameter_shortname': 'CopSalto', 'parameter_type': 1,
          'parameter_unitstyle': 0, 'parameter_modmode': 4, 'parameter_initial': [2],
          'parameter_initial_enable': 1, 'parameter_mmin': 1.0, 'parameter_mmax': 11.0}
    pg['boxes'].append({'box': {
        'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2, 'outlettype': ['', 'float'],
        'parameter_enable': 1, 'varname': 'v_copsalto',
        'annotation': 'Salto coprimo propio de esta voz (1-11, se ajusta al coprimo mas cercano de la '
                      'cardinalidad), cuando esta voz tiene Propia + Patron = Coprimo; el resto del '
                      'tiempo se usa el Salto global.',
        'patching_rect': [400.0, 1010.0, 30.0, 15.0],
        'presentation': 1, 'presentation_rect': [494.0, 3.0, 24.0, 15.0],
        'saved_attribute_attributes': {'valueof': vo}, 'id': num}})
    pg['parameters'][num] = [LONGNAME, LONGNAME, 0]
    prep = fresh()
    pg['boxes'].append({'box': {
        'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_voicecoprime_prep', 'patching_rect': [500.0, 1610.0, 220.0, 22.0],
        'text': 'prepend setvoicecoprime #1'}})
    rx = fresh()
    pg['boxes'].append({'box': {
        'id': rx, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_copsk_setrx', 'patching_rect': [500.0, 640.0, 200.0, 22.0], 'text': 'prepend set'}})
    pg['lines'] += [
        {'patchline': {'source': [num, 0], 'destination': [prep, 0]}},
        {'patchline': {'source': [prep, 0], 'destination': ['obj-102', 0]}},
        {'patchline': {'source': ['obj-101', 0], 'destination': [num, 0]}},
        {'patchline': {'source': [ROUTE_ID, 15], 'destination': [rx, 0]}},
        {'patchline': {'source': [rx, 0], 'destination': [num, 0]}}]
    r = pbx[ROUTE_ID]
    r['text'] += ' copsk'
    r['numinlets'] = 17
    r['numoutlets'] = 17
    r['outlettype'] = [''] * 17

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    assert not any(b.get('varname') == 'vah24' for b in bx.values()), 'ya aplicado'
    dn = max(int(i.split('-')[1]) for i in bx)
    vah = 'obj-%d' % (dn + 1)
    P['boxes'].append({'box': {
        'fontsize': 8.0, 'hidden': 1, 'id': vah, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
        'patching_rect': [2600.0, 2800.0, 60.0, 16.0], 'presentation': 1,
        'presentation_rect': [571.0, 35.0, 26.0, 16.0], 'text': 'Salto', 'varname': 'vah24'}})
    n = 0
    for b in bx.values():
        t = b.get('text', '')
        if b.get('maxclass') == 'message' and 'script hide vah23' in t.replace('script show vah23', 'script hide vah23') and 'vah22' in t:
            b['text'] = t + (', script show vah24' if b['id'] == VOCES3_MSG else ', script hide vah24')
            n += 1
    assert n >= 5, n
    ov = P['parameters']['parameter_overrides']
    for i, bp in enumerate(BPATCHER_IDS):
        clean = 'V%d CopSalto' % (i + 1)
        key = '%s::%s' % (bp, num)
        P['parameters'][key] = [clean, clean, 0]
        ov[key] = {'parameter_longname': clean}

    print('fs2voice_adv: +numbox %s +prepend %s +echo %s; route -> 17 outlets (copsk = outlet 15)' % (num, prep, rx))
    print('FORTESEQ2: +vah24 %s, %d mensajes tocados, +4 params' % (vah, n))
    if not apply_it:
        print('\n(dry run)')
        return
    with open(VOICE, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)
    print('escrito. Sigue: check_structure.py y check_params3.py')


main()
