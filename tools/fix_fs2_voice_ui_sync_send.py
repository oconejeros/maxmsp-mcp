"""Replace add_fs2_voice_ui_sync.py's "new bpatcher inlet" delivery with named send/receive.

The user reports the UI-echo added by add_fs2_voice_ui_sync.py doesn't work in Live -- not even
Ext, the simplest case. Suspected cause, and the one this fix removes: fs2voice.maxpat /
fs2voice_adv.maxpat are BPATCHERS (separate files, 4 instances each), and that script gave each
one a brand-new 3rd inlet by editing JSON directly (bumping the bpatcher box's numinlets 2->3 and
adding a new `inlet` object inside the file). Unlike a plain subpatcher's inlet order (determined
by x-position, reliable), a bpatcher's inlet/outlet wiring into its PARENT patcher is something
Max computes/caches when the bpatcher is placed or edited from its own UI -- a numinlets edit made
entirely outside Max is not guaranteed to be honored by an already-serialized bpatcher box the same
way, so messages sent to the "new" inlet 2 can silently go nowhere until the box is touched from
inside Max itself. There is no way to verify this from outside Max, so this fix sidesteps the
whole question: instead of a new inlet, it uses `send`/`receive` (s/r), which cross a bpatcher
boundary the same way regardless of when/how the box was last edited -- the same mechanism this
device already uses in at least one place (`send FORTESEQ_SET`, obj-511).

Each bpatcher instance already gets a per-voice creation argument (`args: [1]`..`[4]` on
obj-51..54/obj-577..580), the same one `prepend setvoicemute #1` already relies on -- so a
`receive NAME#1` inside the bpatcher file resolves to a distinct, per-voice name in each of the 4
instances (`FS2_ON_ECHO1`..`FS2_ON_ECHO4`) without needing 4 separate receive objects.

    python tools/fix_fs2_voice_ui_sync_send.py            dry run, writes nothing
    python tools/fix_fs2_voice_ui_sync_send.py --apply    do it (device closed in Max AND Live)

## What changes, file by file

**forteseq/fs2voice.maxpat**: removes the inlet/prepend-set pair add_fs2_voice_ui_sync.py added
(obj-100, obj-101); adds `receive FS2_ON_ECHO#1` -> `prepend set` -> v_on (obj-2).

**forteseq/fs2voice_adv.maxpat**: removes obj-200..obj-206; adds `receive FS2_ADV_ECHO#1` ->
`route ext art lec ton fij` -> 5x `prepend set` -> v_ext/v_artown/v_readown/v_tonprop/v_fijar.

**forteseq/FORTESEQ2.amxd**: removes the 8 patchlines from obj-403 (fs2_echo) into inlet 2 of
obj-51..54/obj-577..580, and reverts those 8 bpatchers' numinlets 3 -> 2 (undoing the previous
script's inlet addition entirely). obj-403 itself (its route text, its 8 v*onecho/v*advecho
outlets) is UNCHANGED -- only where those 8 outlets go changes: 8 new `send` objects
(FS2_ON_ECHO1..4, FS2_ADV_ECHO1..4) take their place, one per outlet, addressed by name instead of
by wire.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
VOICE_ESS = os.path.join('forteseq', 'fs2voice.maxpat')
VOICE_ADV = os.path.join('forteseq', 'fs2voice_adv.maxpat')

ESS_IDS = ['obj-51', 'obj-52', 'obj-53', 'obj-54']
ADV_IDS = ['obj-577', 'obj-578', 'obj-579', 'obj-580']

ON_NAMES = ['FS2_ON_ECHO1', 'FS2_ON_ECHO2', 'FS2_ON_ECHO3', 'FS2_ON_ECHO4']
ADV_NAMES = ['FS2_ADV_ECHO1', 'FS2_ADV_ECHO2', 'FS2_ADV_ECHO3', 'FS2_ADV_ECHO4']


def fix_voice_essential(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    assert 'obj-100' in bx and 'obj-101' in bx, 'add_fs2_voice_ui_sync.py no esta aplicado -- nada que arreglar'
    pg['boxes'] = [b for b in pg['boxes'] if b['box']['id'] not in ('obj-100', 'obj-101')]
    pg['lines'] = [l for l in pg['lines']
                   if l['patchline']['source'][0] not in ('obj-100', 'obj-101')
                   and l['patchline']['destination'][0] not in ('obj-100', 'obj-101')]

    recv_id, prep_id = 'obj-100', 'obj-101'   # reuse the same ids, now for the send/receive path
    pg['boxes'].append({'box': {
        'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_on_ui_recv', 'patching_rect': [250.0, 20.0, 140.0, 22.0],
        'text': 'receive FS2_ON_ECHO#1'}})
    pg['boxes'].append({'box': {
        'id': prep_id, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_on_setrx', 'patching_rect': [250.0, 70.0, 70.0, 22.0], 'text': 'prepend set'}})
    pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [prep_id, 0]}})
    pg['lines'].append({'patchline': {'source': [prep_id, 0], 'destination': ['obj-2', 0]}})


def fix_voice_advanced(pg):
    bx = {b['box']['id']: b['box'] for b in pg['boxes']}
    old_ids = {'obj-200', 'obj-201', 'obj-202', 'obj-203', 'obj-204', 'obj-205', 'obj-206'}
    assert old_ids <= set(bx), 'add_fs2_voice_ui_sync.py no esta aplicado -- nada que arreglar'
    pg['boxes'] = [b for b in pg['boxes'] if b['box']['id'] not in old_ids]
    pg['lines'] = [l for l in pg['lines']
                   if l['patchline']['source'][0] not in old_ids
                   and l['patchline']['destination'][0] not in old_ids]

    recv_id, route_id = 'obj-200', 'obj-201'
    prep_ids = {'ext': 'obj-202', 'art': 'obj-203', 'lec': 'obj-204', 'ton': 'obj-205', 'fij': 'obj-206'}
    targets = {'ext': 'obj-3', 'art': 'obj-39', 'lec': 'obj-44', 'ton': 'obj-111', 'fij': 'obj-117'}

    pg['boxes'].append({'box': {
        'id': recv_id, 'maxclass': 'newobj', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'v_adv_ui_recv', 'patching_rect': [200.0, 4.0, 150.0, 22.0],
        'text': 'receive FS2_ADV_ECHO#1'}})
    pg['boxes'].append({'box': {
        'id': route_id, 'maxclass': 'newobj', 'numinlets': 6, 'numoutlets': 6,
        'outlettype': ['', '', '', '', '', ''], 'varname': 'v_adv_ui_route',
        'patching_rect': [200.0, 40.0, 240.0, 20.0], 'text': 'route ext art lec ton fij'}})
    pg['lines'].append({'patchline': {'source': [recv_id, 0], 'destination': [route_id, 0]}})

    tags = ['ext', 'art', 'lec', 'ton', 'fij']
    for i, tag in enumerate(tags):
        pid = prep_ids[tag]
        pg['boxes'].append({'box': {
            'id': pid, 'maxclass': 'message', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
            'varname': 'v_%s_setrx' % tag, 'patching_rect': [200.0 + 90.0 * i, 80.0, 70.0, 22.0],
            'text': 'prepend set'}})
        pg['lines'].append({'patchline': {'source': [route_id, i], 'destination': [pid, 0]}})
        pg['lines'].append({'patchline': {'source': [pid, 0], 'destination': [targets[tag], 0]}})


def main():
    apply_it = '--apply' in sys.argv

    pg_ess = json.load(open(VOICE_ESS, encoding='utf-8'))['patcher']
    fix_voice_essential(pg_ess)

    pg_adv = json.load(open(VOICE_ADV, encoding='utf-8'))['patcher']
    fix_voice_advanced(pg_adv)

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    echo = bx['obj-403']
    assert echo['varname'] == 'fs2_echo'

    # locate the 8 outlets by arg position (unchanged since add_fs2_voice_ui_sync.py: appended at
    # the end of the arg list, so their index = position in the args, 0-based)
    args = echo['text'].split()[1:]   # drop the leading "route"
    onecho_args = ['v1onecho', 'v2onecho', 'v3onecho', 'v4onecho']
    advecho_args = ['v1advecho', 'v2advecho', 'v3advecho', 'v4advecho']
    for a in onecho_args + advecho_args:
        assert a in args, '%s no esta en obj-403 -- corre add_fs2_voice_ui_sync.py primero' % a
    onecho_outlets = [args.index(a) for a in onecho_args]
    advecho_outlets = [args.index(a) for a in advecho_args]

    # Remove the 8 old patchlines into bpatcher inlet 2. NOTE: add_fs2_voice_ui_sync.py had an
    # off-by-one bug computing these outlet indices (used old_reject+1+i / old_reject+5+i instead
    # of old_reject+i / old_reject+4+i), so the actual wires sit at outlets 28..35, not 27..34 --
    # confirmed by reading them back from the live file. Match by "any obj-403 outlet >= the first
    # new arg's index, landing on inlet 2 of a voice bpatcher" so this cleanup is correct
    # regardless of exactly where the bug put them.
    old_targets = set(ESS_IDS) | set(ADV_IDS)
    first_new_outlet = min(onecho_outlets)

    def is_old_echo_wire(l):
        pl = l['patchline']
        return (pl['source'][0] == 'obj-403' and pl['source'][1] >= first_new_outlet
                and pl['destination'][0] in old_targets and pl['destination'][1] == 2)

    before = len(P['lines'])
    P['lines'] = [l for l in P['lines'] if not is_old_echo_wire(l)]
    removed = before - len(P['lines'])
    assert removed == 8, 'se esperaban 8 patchlines viejas, se encontraron %d' % removed

    for bid in ESS_IDS + ADV_IDS:
        assert bx[bid]['numinlets'] == 3, '%s: numinlets inesperado %r' % (bid, bx[bid]['numinlets'])
        bx[bid]['numinlets'] = 2

    # 8 new send objects, wired from the SAME 8 obj-403 outlets
    nid = [max(int(i.split('-')[1]) for i in bx)]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    new_ids = []
    for i, (outlet_i, name) in enumerate(zip(onecho_outlets, ON_NAMES)):
        sid = fresh()
        P['boxes'].append({'box': {
            'id': sid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
            'patching_rect': [2400.0 + 150.0 * i, 3220.0, 140.0, 20.0], 'text': 'send ' + name}})
        P['lines'].append({'patchline': {'source': ['obj-403', outlet_i], 'destination': [sid, 0]}})
        new_ids.append(sid)
    for i, (outlet_i, name) in enumerate(zip(advecho_outlets, ADV_NAMES)):
        sid = fresh()
        P['boxes'].append({'box': {
            'id': sid, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 0,
            'patching_rect': [2400.0 + 150.0 * i, 3260.0, 140.0, 20.0], 'text': 'send ' + name}})
        P['lines'].append({'patchline': {'source': ['obj-403', outlet_i], 'destination': [sid, 0]}})
        new_ids.append(sid)

    print('fs2voice.maxpat: inlet -> receive FS2_ON_ECHO#1 -> prepend set -> v_on')
    print('fs2voice_adv.maxpat: inlet -> receive FS2_ADV_ECHO#1 -> route -> 5x prepend set')
    print('FORTESEQ2.amxd: -8 patchlines (obj-403 -> bpatcher inlet2), numinlets 3->2 en %s' % ', '.join(ESS_IDS + ADV_IDS))
    print('  +8 send objects: %s' % ', '.join(new_ids))

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-uisyncfix')
    with open(VOICE_ESS, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_ess}, f, indent=1)
    with open(VOICE_ADV, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg_adv}, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    for bid in ESS_IDS + ADV_IDS:
        assert bx2[bid]['numinlets'] == 2
    for sid in new_ids:
        assert sid in bx2

    print('\nescrito %s, %s, %s (.before-uisyncfix del .amxd guardado). Sigue:' % (VOICE_ESS, VOICE_ADV, DEVICE))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2voice.maxpat forteseq/fs2voice_adv.maxpat')
    print('  python tools/check_params3.py')
    print('  en Max: CERRAR el device en Live, volver a abrirlo (no alcanza con recargar js/script)')


main()
