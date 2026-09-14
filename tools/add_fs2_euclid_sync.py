"""Wire panel sync for the new per-voice Euclidean rhythm scrub controls (Largo/Pulsos/Giro) the
Horizonte popup now exposes unconditionally (no "Propia" gate -- these are always active,
matching how their panel controls have no gate either). forteseq2.js's setvoiceeuclen()/
setvoiceeuck()/setvoiceeucrot() already got their outlet(4, ["rtecho", idx+1, "<tok>", val])
echoes added this session, on a NEW dedicated channel (not onecho/advecho) because the receiving
side lives in a different architecture: fs2pages.maxpat is ONE shared bpatcher (not instanced
per voice via a bpatcher `#1` argument like fs2voice.maxpat/fs2voice_adv.maxpat), so there is no
"#1" to substitute -- the receiver has to demux on voice number explicitly instead.

    python tools/add_fs2_euclid_sync.py            dry run, writes nothing
    python tools/add_fs2_euclid_sync.py --apply    do it (device closed in Max AND Live)

## What changes

**forteseq/FORTESEQ2.amxd**: obj-403 (the big top-level `route`, currently 29 args/30 outlets,
last one already carrying `onecho`/`advecho`) gains one more arg, `rtecho` (30 args/31 outlets),
wired to 1 new box: `send FS2_RT_ECHO` (mirrors obj-817 `send FS2_ON_ECHO` / obj-818
`send FS2_ADV_ECHO`, same pattern, new dedicated channel).

**forteseq/fs2pages.maxpat**: new `receive FS2_RT_ECHO` -> `route 1 2 3 4` (demux by voice
number -- there is no bpatcher `#1` here, so this is an explicit routing layer the other files
didn't need) -> per voice, a `route larg puls gir` (3 args/4 outlets) -> 3 `prepend set` boxes
each -> the 12 existing live.numbox objects (`rt_v1_larg`..`rt_v4_gir`), same ones the panel's
own forward-path (`prepend setvoiceeuclen/euck/eucrot #1` boxes, already in this file) already
writes from.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PAGES = os.path.join('forteseq', 'fs2pages.maxpat')

SEND_ID = 'obj-820'

# voice (1-based) -> {token: target box id in fs2pages.maxpat}
VOICE_TARGETS = {
    1: {'larg': 'obj-240', 'puls': 'obj-242', 'gir': 'obj-244'},
    2: {'larg': 'obj-247', 'puls': 'obj-249', 'gir': 'obj-251'},
    3: {'larg': 'obj-254', 'puls': 'obj-256', 'gir': 'obj-258'},
    4: {'larg': 'obj-261', 'puls': 'obj-263', 'gir': 'obj-265'},
}


def main():
    apply_it = '--apply' in sys.argv

    # ---- FORTESEQ2.amxd: obj-403 +1 arg, +1 send box --------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    route403 = bx['obj-403']
    assert route403['text'].split()[-1] != 'rtecho', 'ya aplicado (amxd)'
    assert route403['numoutlets'] == 30
    assert SEND_ID not in bx

    route403['text'] = route403['text'] + ' rtecho'
    route403['numoutlets'] = 31

    P['boxes'].append({'box': {
        'id': SEND_ID, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
        'patching_rect': [2720.0, 3300.0, 140.0, 20.0], 'text': 'send FS2_RT_ECHO'}})
    P['lines'].append({'patchline': {'source': ['obj-403', 29], 'destination': [SEND_ID, 0]}})

    # ---- fs2pages.maxpat: receive -> route 1 2 3 4 -> per-voice route larg puls gir -------
    pg = json.load(open(PAGES, encoding='utf-8'))['patcher']
    pbx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert not any(b['box'].get('text') == 'receive FS2_RT_ECHO' for b in pg['boxes']), 'ya aplicado (pages)'
    for voice, toks in VOICE_TARGETS.items():
        for tok, tid in toks.items():
            assert tid in pbx, 'falta %s (voz %d %s)' % (tid, voice, tok)

    pnid = [max(int(i.split('-')[1]) for i in pbx)]

    def pfresh():
        pnid[0] += 1
        return 'obj-%d' % pnid[0]

    recv_id = pfresh()
    pg['boxes'].append({'box': {
        'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'rt_echo_rx', 'patching_rect': [900.0, 3600.0, 160.0, 20.0],
        'text': 'receive FS2_RT_ECHO'}})

    vroute_id = pfresh()
    pg['boxes'].append({'box': {
        'id': vroute_id, 'maxclass': 'newobj', 'numinlets': 5, 'numoutlets': 5,
        'outlettype': ['', '', '', '', ''], 'varname': 'rt_echo_vroute',
        'patching_rect': [900.0, 3630.0, 200.0, 20.0], 'text': 'route 1 2 3 4'}})
    pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [vroute_id, 0]}})

    new_ids = []
    for vi, voice in enumerate((1, 2, 3, 4)):
        troute_id = pfresh()
        pg['boxes'].append({'box': {
            'id': troute_id, 'maxclass': 'newobj', 'numinlets': 4, 'numoutlets': 4,
            'outlettype': ['', '', '', ''], 'varname': 'rt_echo_v%d_troute' % voice,
            'patching_rect': [900.0 + 220.0 * vi, 3660.0, 160.0, 20.0], 'text': 'route larg puls gir'}})
        pg['lines'].append({'patchline': {'source': [vroute_id, vi], 'destination': [troute_id, 0]}})
        new_ids.append(troute_id)

        for ti, tok in enumerate(('larg', 'puls', 'gir')):
            pid = pfresh()
            target = VOICE_TARGETS[voice][tok]
            pg['boxes'].append({'box': {
                'id': pid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
                'varname': 'rt_v%d_%s_setrx' % (voice, tok),
                'patching_rect': [900.0 + 220.0 * vi, 3690.0 + 30.0 * ti, 160.0, 22.0],
                'text': 'prepend set'}})
            pg['lines'].append({'patchline': {'source': [troute_id, ti], 'destination': [pid, 0]}})
            pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [target, 0]}})
            new_ids.append(pid)

    print('FORTESEQ2.amxd: obj-403 -> "%s" (30->31 outlets), +%s (send FS2_RT_ECHO)' % (route403['text'], SEND_ID))
    print('fs2pages.maxpat: +%s (receive FS2_RT_ECHO) -> +%s (route 1 2 3 4) -> 4x route larg puls gir -> 12x prepend set' % (recv_id, vroute_id))
    print('  boxes nuevos: %d' % (2 + len(new_ids)))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-euclidsync')
    amxd.save(DEVICE, data, s, e, doc)

    shutil.copyfile(PAGES, PAGES + '.before-euclidsync')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    assert bx2['obj-403']['numoutlets'] == 31
    assert SEND_ID in bx2

    pg2 = json.load(open(PAGES, encoding='utf-8'))['patcher']
    pbx2 = {b['box']['id']: b['box'] for b in pg2['boxes']}
    assert recv_id in pbx2 and vroute_id in pbx2

    print('\nescrito %s y %s (.before-euclidsync guardados). Sigue:' % (DEVICE, PAGES))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
