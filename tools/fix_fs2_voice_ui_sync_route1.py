"""Replace the per-voice send/receive NAMES (`receive FS2_ON_ECHO#1`, one #1-substituted name per
voice) with a single SHARED send/receive per group, demuxed by a `route #1` right after -- the
same whitespace-delimited "#1 as its own token" shape already proven to work everywhere else in
this file (`prepend setvoicemute #1`, `prepend setvoiceexternal #1`, etc.).

## Why

User confirmed: clicking a popup chip DOES change the engine (audible), so the forward path
(popup -> engine) and the panel->popup echo (vkey, unrelated to this) both work. Only the
newly-added engine->panel echo silently does nothing, with a clean Max console (no error). The one
part of that echo path this project has NO proven precedent for is `#1` concatenated directly onto
a send/receive NAME with no surrounding whitespace (`FS2_ON_ECHO#1`) -- every other `#1` use in
this codebase is its own separate, space-delimited argument (`prepend X #1`, and now `route #1`
below). Rather than leave that untested, this fix removes it: one shared send/receive name per
group (no #1 in the name at all), with the per-voice filtering done by `route #1` immediately
after receiving -- unambiguously the same substitution shape already proven throughout this device.

    python tools/fix_fs2_voice_ui_sync_route1.py            dry run, writes nothing
    python tools/fix_fs2_voice_ui_sync_route1.py --apply    do it (device closed in Max AND Live)

## What changes, file by file

**forteseq/forteseq2.js**: the 6 setters' echo calls change shape -- voice index moves from being
baked into the token name (`"v"+(idx+1)+"onecho"`) to being the first argument of a shared token
(`["onecho", idx+1, ...]`), matching the new demux-by-route-of-#1 downstream.

**forteseq/fs2voice.maxpat**: `receive FS2_ON_ECHO#1` -> `receive FS2_ON_ECHO` (one shared name for
all 4 instances) followed by a new `route #1` (per-instance voice filter) before the existing
`prepend set` -> v_on.

**forteseq/fs2voice_adv.maxpat**: `receive FS2_ADV_ECHO#1` -> `receive FS2_ADV_ECHO` followed by a
new `route #1` before the existing `route ext art lec ton fij` -> 5x `prepend set` chain.

**forteseq/FORTESEQ2.amxd**: obj-403 (fs2_echo) drops the 8 per-voice args (v1onecho..v4advecho)
added by add_fs2_voice_ui_sync.py, replaced by 2 shared args ("onecho", "advecho"). The 8
per-voice `send` objects fix_fs2_voice_ui_sync_send.py added are removed, replaced by 2 shared
`send` objects (FS2_ON_ECHO, FS2_ADV_ECHO).
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

OLD_PER_VOICE_ARGS = ['v1onecho', 'v2onecho', 'v3onecho', 'v4onecho',
                      'v1advecho', 'v2advecho', 'v3advecho', 'v4advecho']
NEW_SHARED_ARGS = ['onecho', 'advecho']


# ============================================================================================
# forteseq2.js -- 6 setters: per-voice token -> shared token + explicit voice-index arg
# ============================================================================================

ENGINE_EDITS = [
    ('setvoicemute echo', 'outlet(4, ["v" + (idx + 1) + "onecho", voiceMute[idx] ? 0 : 1]);',
     'outlet(4, ["onecho", idx + 1, voiceMute[idx] ? 0 : 1]);'),
    ('setvoiceexternal echo', 'outlet(4, ["v" + (idx + 1) + "advecho", "ext", voiceExternal[idx]]);',
     'outlet(4, ["advecho", idx + 1, "ext", voiceExternal[idx]]);'),
    ('setvoiceartown echo', 'outlet(4, ["v" + (idx + 1) + "advecho", "art", voiceArtOwn[idx]]);',
     'outlet(4, ["advecho", idx + 1, "art", voiceArtOwn[idx]]);'),
    ('setvoicereadown echo', 'outlet(4, ["v" + (idx + 1) + "advecho", "lec", voiceReadOwn[idx]]);',
     'outlet(4, ["advecho", idx + 1, "lec", voiceReadOwn[idx]]);'),
    ('setvoicekeyown echo', 'outlet(4, ["v" + (idx + 1) + "advecho", "ton", voiceKeyOwn[idx]]);',
     'outlet(4, ["advecho", idx + 1, "ton", voiceKeyOwn[idx]]);'),
    ('setvoicekeylock echo', 'outlet(4, ["v" + (idx + 1) + "advecho", "fij", voiceKeyLock[idx]]);',
     'outlet(4, ["advecho", idx + 1, "fij", voiceKeyLock[idx]]);'),
]


def apply_engine(content):
    for label, old, new in ENGINE_EDITS:
        n = content.count(old)
        assert n == 1, 'forteseq2.js: %s no calzo (%d matches, esperaba 1)' % (label, n)
        content = content.replace(old, new, 1)
    return content


def fix_voice_essential(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert bx['obj-100']['text'] == 'receive FS2_ON_ECHO#1', 'obj-100 no tiene el texto esperado -- ya aplicado?'
    bx['obj-100']['text'] = 'receive FS2_ON_ECHO'

    route1_id = 'obj-102'
    assert route1_id not in bx
    pg['boxes'].append({'box': {
        'id': route1_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
        'outlettype': ['', ''], 'varname': 'v_on_ui_route1',
        'patching_rect': [250.0, 45.0, 60.0, 20.0], 'text': 'route #1'}})

    # splice: obj-100 -> route1 -> obj-101 (was obj-100 -> obj-101 directly)
    pg['lines'] = [l for l in pg['lines']
                   if not (l['patchline']['source'] == ['obj-100', 0] and l['patchline']['destination'] == ['obj-101', 0])]
    pg['lines'].append({'patchline': {'source': ['obj-100', 0], 'destination': [route1_id, 0]}})
    pg['lines'].append({'patchline': {'source': [route1_id, 0], 'destination': ['obj-101', 0]}})


def fix_voice_advanced(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert bx['obj-200']['text'] == 'receive FS2_ADV_ECHO#1', 'obj-200 no tiene el texto esperado -- ya aplicado?'
    bx['obj-200']['text'] = 'receive FS2_ADV_ECHO'

    route1_id = 'obj-207'
    assert route1_id not in bx
    pg['boxes'].append({'box': {
        'id': route1_id, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
        'outlettype': ['', ''], 'varname': 'v_adv_ui_route1',
        'patching_rect': [200.0, 20.0, 60.0, 20.0], 'text': 'route #1'}})

    pg['lines'] = [l for l in pg['lines']
                   if not (l['patchline']['source'] == ['obj-200', 0] and l['patchline']['destination'] == ['obj-201', 0])]
    pg['lines'].append({'patchline': {'source': ['obj-200', 0], 'destination': [route1_id, 0]}})
    pg['lines'].append({'patchline': {'source': [route1_id, 0], 'destination': ['obj-201', 0]}})


def main():
    apply_it = '--apply' in sys.argv

    engine_src = open(ENGINE_JS, encoding='utf-8').read()
    engine_new = apply_engine(engine_src)

    pg_ess = json.load(open(VOICE_ESS, encoding='utf-8'))['patcher']
    fix_voice_essential(pg_ess)

    pg_adv = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    fix_voice_advanced(pg_adv)

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    echo = bx['obj-403']
    args = echo['text'].split()[1:]
    for a in OLD_PER_VOICE_ARGS:
        assert a in args, '%s no esta en obj-403 -- ya aplicado?' % a
    old_outlets = {a: args.index(a) for a in OLD_PER_VOICE_ARGS}

    # find + remove the 8 send objects fix_fs2_voice_ui_sync_send.py created (by their exact text)
    old_send_texts = {'send FS2_ON_ECHO1', 'send FS2_ON_ECHO2', 'send FS2_ON_ECHO3', 'send FS2_ON_ECHO4',
                       'send FS2_ADV_ECHO1', 'send FS2_ADV_ECHO2', 'send FS2_ADV_ECHO3', 'send FS2_ADV_ECHO4'}
    old_send_ids = {b['box']['id'] for b in P['boxes']
                    if b['box'].get('maxclass') == 'newobj' and b['box'].get('text') in old_send_texts}
    assert len(old_send_ids) == 8, 'se esperaban 8 send objects viejos, se encontraron %d' % len(old_send_ids)

    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in old_send_ids]
    P['lines'] = [l for l in P['lines']
                  if l['patchline']['source'][0] not in old_send_ids
                  and l['patchline']['destination'][0] not in old_send_ids]

    # rebuild obj-403's arg list: keep everything except the 8 old per-voice args, append 2 shared
    core_args = [a for a in args if a not in OLD_PER_VOICE_ARGS]
    new_args = core_args + NEW_SHARED_ARGS
    echo['text'] = 'route ' + ' '.join(new_args)
    new_n = len(new_args) + 1
    echo['numoutlets'] = new_n
    echo['numinlets'] = new_n
    echo['outlettype'] = [''] * new_n

    onecho_outlet = new_args.index('onecho')
    advecho_outlet = new_args.index('advecho')

    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    on_send_id = fresh()
    P['boxes'].append({'box': {
        'id': on_send_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
        'patching_rect': [2400.0, 3300.0, 140.0, 20.0], 'text': 'send FS2_ON_ECHO'}})
    P['lines'].append({'patchline': {'source': ['obj-403', onecho_outlet], 'destination': [on_send_id, 0]}})

    adv_send_id = fresh()
    P['boxes'].append({'box': {
        'id': adv_send_id, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
        'patching_rect': [2560.0, 3300.0, 140.0, 20.0], 'text': 'send FS2_ADV_ECHO'}})
    P['lines'].append({'patchline': {'source': ['obj-403', advecho_outlet], 'destination': [adv_send_id, 0]}})

    print('forteseq2.js: 6 echo calls -> token + explicit voice-index arg')
    print('fs2voice.maxpat: receive FS2_ON_ECHO (compartido) -> route #1 -> prepend set -> v_on')
    print('fs2voice_adv.maxpat: receive FS2_ADV_ECHO (compartido) -> route #1 -> route ext/art/lec/ton/fij -> ...')
    print('FORTESEQ2.amxd: obj-403 %d args (-8 +2) -> %d outlets' % (len(new_args), new_n))
    print('  -8 send objects viejos: %s' % ', '.join(sorted(old_send_ids)))
    print('  +2 send objects nuevos: %s (onecho), %s (advecho)' % (on_send_id, adv_send_id))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-uisyncroute1')
    open(ENGINE_JS, 'w', encoding='utf-8', newline='\n').write(engine_new)
    with open(VOICE_ESS, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_ess}, f, indent=1)
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_adv}, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    assert bx2['obj-403']['numoutlets'] == new_n
    assert on_send_id in bx2 and adv_send_id in bx2

    print('\nescrito %s, %s, %s, %s (.before-uisyncroute1 del .amxd guardado). Sigue:' %
          (ENGINE_JS, VOICE_ESS, VOICE_ADV, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice.maxpat forteseq/fs2voice_adv.maxpat')
    print('  python tools/check_params3.py')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
