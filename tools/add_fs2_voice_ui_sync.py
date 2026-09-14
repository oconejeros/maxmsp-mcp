"""Bidirectional sync for the 6 per-voice toggles (On/Ext/Art/Lec/Ton/Fijar): until now the popup
"Horizonte"'s chips (added by add_fs2_voice_controls.py) could WRITE these -- click a chip, the
engine state changes, the popup's own optimistic redraw looks right -- but the "Voces N" tabs'
live.toggle objects in the main panel never repainted, so the device visibly disagreed with the
popup. Same recipe as forteseq/forteseqwf.js's uiEcho()/wf_ui_demux: every setter also echoes the
new value back out; that echo is routed to a `prepend set` wired straight into the matching
live.toggle. `set` repaints a live.* control WITHOUT firing its own outlet, so there is no feedback
loop with the live.toggle's own "click -> setvoice*" wire -- popup and panel now drive the same
state through the same setters, and both repaint from the same echo.

    python tools/add_fs2_voice_ui_sync.py            dry run, writes nothing
    python tools/add_fs2_voice_ui_sync.py --apply    do it (device closed in Max AND Live)

## What changes, file by file

**forteseq/forteseq2.js**: the 6 setters (setvoicemute, setvoiceexternal, setvoiceartown,
setvoicereadown, setvoicekeyown, setvoicekeylock) each gain one `outlet(4, [...])` call at the end,
reusing outlet 4 -- already FORTESEQ2's general per-parameter UI-echo bus (see fs2_echo/obj-403,
e.g. the existing v1grado..v4grado echoes). "On" gets its own token per voice (v<n>onecho, a bare
0/1); the other 5 share one token per voice (v<n>advecho) carrying a [tag, value] pair, demuxed at
the destination -- fewer new route args than one token per (voice, parameter) pair.

**forteseq/fs2voice.maxpat** (essential tab, x4 instances): +1 inlet (2 -> 3) feeding
`prepend set` -> v_on. **forteseq/fs2voice_adv.maxpat** (advanced tabs, x4 instances): +1 inlet
(2 -> 3) feeding `route ext art lec ton fij` -> 5x `prepend set` -> v_ext/v_artown/v_readown/
v_tonprop/v_fijar.

**forteseq/FORTESEQ2.amxd**: obj-403 (fs2_echo, a `route` whose declared numinlets/numoutlets this
codebase always saves equal to each other -- confirmed against obj-673/obj-740) gains 8 args
(v1..v4 onecho, v1..v4 advecho) at the END of its arg list, so none of its EXISTING outlet indices
move (only the reject outlet, which nothing was wired to, shifts further right). 8 new patchlines
route those 8 new outlets into inlet 2 of the matching voice's essential/advanced bpatcher instance
(obj-51..54, obj-577..580), whose numinlets bump from 2 to 3 to match.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
ENGINE_JS = os.path.join('forteseq', 'forteseq2.js')
VOICE_ESS = os.path.join('forteseq', 'fs2voice.maxpat')
VOICE_ADV = os.path.join('forteseq', 'fs2voice_adv.maxpat')

ESS_IDS = ['obj-51', 'obj-52', 'obj-53', 'obj-54']       # V1..V4 fs2voice.maxpat instances
ADV_IDS = ['obj-577', 'obj-578', 'obj-579', 'obj-580']   # V1..V4 fs2voice_adv.maxpat instances

NEW_ROUTE_ARGS = ['v1onecho', 'v2onecho', 'v3onecho', 'v4onecho',
                   'v1advecho', 'v2advecho', 'v3advecho', 'v4advecho']


# ============================================================================================
# forteseq2.js -- 6 setters gain a UI-echo call
# ============================================================================================

ENGINE_EDITS = [
    ('setvoicemute', '''function setvoicemute(v, m) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceMute[idx] = m ? 1 : 0;
}''', '''function setvoicemute(v, m) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceMute[idx] = m ? 1 : 0;
	// repaint the "On" live.toggle (inverted: On=1 means NOT muted) without re-firing it -- see
	// fs2_echo (obj-403) -> this voice's essential bpatcher inlet 2 -> prepend set -> v_on.
	outlet(4, ["v" + (idx + 1) + "onecho", voiceMute[idx] ? 0 : 1]);
}'''),

    ('setvoiceexternal', '''function setvoiceexternal(v, e) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceExternal[idx] = e ? 1 : 0;
	// The clock no longer refreshes this voice's monitor cell, so give it a defined "--" until
	// its first trigger lands (monScratch starts at a sentinel that is neither a note nor
	// MON_SILENT). Turning it back off costs nothing: the next clock step overwrites it.
	monScratch[idx] = MON_SILENT;
}''', '''function setvoiceexternal(v, e) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceExternal[idx] = e ? 1 : 0;
	// The clock no longer refreshes this voice's monitor cell, so give it a defined "--" until
	// its first trigger lands (monScratch starts at a sentinel that is neither a note nor
	// MON_SILENT). Turning it back off costs nothing: the next clock step overwrites it.
	monScratch[idx] = MON_SILENT;
	// repaint the "Ext" live.toggle without re-firing it -- see fs2_echo -> this voice's advanced
	// bpatcher inlet 2 -> route ext/art/lec/ton/fij -> prepend set -> the matching v_* toggle.
	outlet(4, ["v" + (idx + 1) + "advecho", "ext", voiceExternal[idx]]);
}'''),

    ('setvoiceartown', '''function setvoiceartown(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceArtOwn[idx] = flag ? 1 : 0;
}''', '''function setvoiceartown(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceArtOwn[idx] = flag ? 1 : 0;
	outlet(4, ["v" + (idx + 1) + "advecho", "art", voiceArtOwn[idx]]);
}'''),

    ('setvoicereadown', '''function setvoicereadown(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceReadOwn[idx] = flag ? 1 : 0;
}''', '''function setvoicereadown(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceReadOwn[idx] = flag ? 1 : 0;
	outlet(4, ["v" + (idx + 1) + "advecho", "lec", voiceReadOwn[idx]]);
}'''),

    ('setvoicekeyown', '''function setvoicekeyown(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceKeyOwn[idx] = flag ? 1 : 0;
}''', '''function setvoicekeyown(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceKeyOwn[idx] = flag ? 1 : 0;
	outlet(4, ["v" + (idx + 1) + "advecho", "ton", voiceKeyOwn[idx]]);
}'''),

    ('setvoicekeylock', '''function setvoicekeylock(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceKeyLock[idx] = flag ? 1 : 0;
}''', '''function setvoicekeylock(v, flag) {
	var idx = Math.round(v) - 1;
	if (idx < 0 || idx >= NUM_VOICES) return;
	voiceKeyLock[idx] = flag ? 1 : 0;
	outlet(4, ["v" + (idx + 1) + "advecho", "fij", voiceKeyLock[idx]]);
}'''),
]


def apply_engine(content):
    for label, old, new in ENGINE_EDITS:
        n = content.count(old)
        assert n == 1, 'forteseq2.js: %s no calzo (%d matches, esperaba 1)' % (label, n)
        content = content.replace(old, new, 1)
    return content


# ============================================================================================
# fs2voice.maxpat -- +1 inlet -> prepend set -> v_on (obj-2)
# ============================================================================================

def patch_voice_essential(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert 'obj-2' in bx and bx['obj-2']['varname'] == 'v_on'
    assert not any(b['box'].get('varname') == 'v_on_ui_in' for b in pg['boxes']), 'ya aplicado'

    in_id, prep_id = 'obj-100', 'obj-101'
    assert in_id not in bx and prep_id not in bx

    pg['boxes'].append({'box': {
        'id': in_id, 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'comment': 'on: el motor repinta el toggle sin re-disparar (via prepend set)',
        'varname': 'v_on_ui_in', 'patching_rect': [250.0, 20.0, 30.0, 30.0]}})
    pg['boxes'].append({'box': {
        'id': prep_id, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_on_setrx', 'patching_rect': [250.0, 70.0, 70.0, 22.0], 'text': 'prepend set'}})
    pg['lines'].append({'patchline': {'source': [in_id, 0], 'destination': [prep_id, 0]}})
    pg['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': ['obj-2', 0]}})
    return in_id


# ============================================================================================
# fs2voice_adv.maxpat -- +1 inlet -> route ext art lec ton fij -> 5x prepend set
# ============================================================================================

def patch_voice_advanced(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    targets = {'ext': 'obj-3', 'art': 'obj-39', 'lec': 'obj-44', 'ton': 'obj-111', 'fij': 'obj-117'}
    for tid in targets.values():
        assert tid in bx
    assert not any(b['box'].get('varname') == 'v_adv_ui_in' for b in pg['boxes']), 'ya aplicado'

    in_id, route_id = 'obj-200', 'obj-201'
    prep_ids = {'ext': 'obj-202', 'art': 'obj-203', 'lec': 'obj-204', 'ton': 'obj-205', 'fij': 'obj-206'}
    assert in_id not in bx and route_id not in bx and all(pid not in bx for pid in prep_ids.values())

    pg['boxes'].append({'box': {
        'id': in_id, 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'comment': 'ui: el motor repinta Ext/Art/Lec/Ton/Fijar sin re-disparar (route + prepend set)',
        'varname': 'v_adv_ui_in', 'patching_rect': [200.0, 4.0, 18.0, 18.0]}})
    pg['boxes'].append({'box': {
        'id': route_id, 'maxclass': 'newobj', 'numinlets': 6, 'numoutlets': 6,
        'outlettype': ['', '', '', '', '', ''], 'varname': 'v_adv_ui_route',
        'patching_rect': [200.0, 1900.0, 240.0, 20.0], 'text': 'route ext art lec ton fij'}})
    pg['lines'].append({'patchline': {'source': [in_id, 0], 'destination': [route_id, 0]}})

    tags = ['ext', 'art', 'lec', 'ton', 'fij']
    for i, tag in enumerate(tags):
        pid = prep_ids[tag]
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
            'varname': 'v_%s_setrx' % tag, 'patching_rect': [200.0 + 90.0 * i, 1940.0, 70.0, 22.0],
            'text': 'prepend set'}})
        pg['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
        pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [targets[tag], 0]}})
    return in_id


def main():
    apply_it = '--apply' in sys.argv

    engine_src = open(ENGINE_JS, encoding='utf-8').read()
    engine_new = apply_engine(engine_src)

    pg_ess = json.load(open(VOICE_ESS, encoding='utf-8'))['patcher']
    patch_voice_essential(pg_ess)

    pg_adv = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    patch_voice_advanced(pg_adv)

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    echo = bx['obj-403']
    assert echo['varname'] == 'fs2_echo'
    assert not any(a in echo['text'] for a in NEW_ROUTE_ARGS), 'obj-403 ya tiene los args -- ya aplicado?'
    old_n = echo['numoutlets']
    assert echo['numinlets'] == old_n, 'obj-403: se esperaba numinlets == numoutlets (%d != %d)' % (echo['numinlets'], old_n)

    # append the 8 new args just before the implicit reject outlet -- every EXISTING match outlet
    # index is unaffected (they're earlier in the arg list); only the reject outlet index moves,
    # and nothing is wired to it today (checked: no patchline sources at the old reject index).
    old_reject = old_n - 1
    assert not any(l['patchline']['source'] == ['obj-403', old_reject] for l in P['lines']), \
        'algo esta cableado al outlet de rechazo actual -- revisar a mano'
    echo['text'] = echo['text'] + ' ' + ' '.join(NEW_ROUTE_ARGS)
    new_n = old_n + len(NEW_ROUTE_ARGS)
    echo['numoutlets'] = new_n
    echo['numinlets'] = new_n
    echo['outlettype'] = [''] * new_n

    for bid in ESS_IDS + ADV_IDS:
        assert bx[bid]['numinlets'] == 2, '%s: numinlets inesperado %r' % (bid, bx[bid]['numinlets'])
        bx[bid]['numinlets'] = 3

    for i, bid in enumerate(ESS_IDS):
        P['lines'].append({'patchline': {'source': ['obj-403', old_reject + 1 + i], 'destination': [bid, 2]}})
    for i, bid in enumerate(ADV_IDS):
        P['lines'].append({'patchline': {'source': ['obj-403', old_reject + 5 + i], 'destination': [bid, 2]}})

    print('forteseq2.js: 6 setters ganan outlet(4, [...]) de UI-echo')
    print('fs2voice.maxpat: +inlet 2 -> prepend set -> v_on')
    print('fs2voice_adv.maxpat: +inlet 2 -> route ext/art/lec/ton/fij -> 5x prepend set')
    print('FORTESEQ2.amxd: obj-403 %d -> %d outlets (+%d), numinlets bumped to match' % (old_n, new_n, len(NEW_ROUTE_ARGS)))
    print('  8 nuevas patchlines -> inlet 2 de %s' % ', '.join(ESS_IDS + ADV_IDS))
    print('  numinlets 2->3 en %s' % ', '.join(ESS_IDS + ADV_IDS))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-voiceuisync')
    open(ENGINE_JS, 'w', encoding='utf-8', newline='\n').write(engine_new)
    with open(VOICE_ESS, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_ess}, f, indent=1)
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_adv}, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    assert bx2['obj-403']['numoutlets'] == new_n
    for bid in ESS_IDS + ADV_IDS:
        assert bx2[bid]['numinlets'] == 3

    print('\nescrito %s, %s, %s, %s (.before-voiceuisync del .amxd guardado). Sigue:' %
          (ENGINE_JS, VOICE_ESS, VOICE_ADV, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice.maxpat forteseq/fs2voice_adv.maxpat')
    print('  python tools/check_params3.py')
    print('  en Max: recarga js forteseq2.js, el device completo, script stop/start')


main()
