"""Let the Horizonte popup's per-voice chips (Ext/Art/Lec/Ton/Fijar) jump the main device to the
"Pagina" tab where that control actually lives, whenever a click turns the chip ON (off does
nothing -- user request: only surface where a control lives when you're turning it on, not when
turning it off).

    python tools/add_fs2_gotopage.py            dry run, writes nothing
    python tools/add_fs2_gotopage.py --apply    do it (device closed in Max AND Live)

## Where each chip's control actually lives (confirmed by reading presentation_rect x-positions
## in fs2voice_adv.maxpat against the per-page pan offsets already in FORTESEQ2.amxd -- obj-721/
## 722/800/804, "script sendbox vadv# offset <x> 0" for Voces1/2/3/4 respectively: 0, -204, -412,
## -620, each revealing a ~206px-wide slice of the shared vadv1..4 bpatcher's internal canvas):

    Ext    (obj-3,   x=110) -> slice [0,206)    -> Voces 1  (Pagina value 6)
    Art    (obj-39,  x=308) -> slice [204,410)  -> Voces 2  (Pagina value 7)
    Lec    (obj-44,  x=324) -> slice [204,410)  -> Voces 2  (Pagina value 7)
    Ton    (obj-111, x=620) -> slice [620,826)  -> Voces 4  (Pagina value 10)
    Fijar  (obj-117, x=712) -> slice [620,826)  -> Voces 4  (Pagina value 10)

Note this does NOT match the user's own example ("art o lec -> Voces 1") -- they were
illustrating the *pattern* they wanted, not asserting the exact tab; the real x-positions place
Art/Lec on Voces 2. Went with the measured positions since the point is to actually reveal the
control, and a wrong tab would defeat that.

The "On" chip (mute) has no page to jump to: its control (obj-51..54 in fs2voice.maxpat, the
"essential" row) is never show/hidden by the Pagina router (no script targets its varnames
anywhere in FORTESEQ2.amxd) -- it's permanently on the main panel regardless of tab, same
promoted-to-main-panel treatment as Indep/Filtro/Lock (see [[forteseq2_ui_reorg]]). So the "On"
chip's click keeps doing exactly what it does today (mute toggle only), nothing added.

## Mechanism

fs2_pagina (obj-485, the live.tab) already fires its own outlet-0/1/2 chain (obj-486 sel 0..10,
obj-582 sel 6 7 8 9 10 -> obj-721/722/800/804 show/hide+offset chains) on ANY plain number sent to
its hot inlet -- not just real clicks; live.toggle's `set N` is the only message that stays
silent, and this is a bare number, not `set`. So all this needs is to get the right integer into
obj-485's inlet 0.

The popup already has exactly one path out to the engine: fs2horizon.js's jsui (inside the
[p fs2_window] subpatcher, obj-751) -> outlet(0) -> obj-2 -> obj-4 (the subpatcher's own outlet
box) -> at the top level, obj-751's outlet -> obj-23 (js forteseq2.js). Reusing that path for
"gotopage" and letting it reach the ENGINE would just error (forteseq2.js has no `gotopage`
function) -- so this inserts a `route gotopage` at the TOP level, between obj-751 and obj-23:
matched ("gotopage <n>", i.e. the popup's own outlet(0) list) strips to a bare `<n>` on outlet 0,
which goes straight to obj-485; everything else (every existing setvoice*/setmask/setlockindex/...
message, on the reject outlet) continues to obj-23 exactly as before -- zero behavior change for
the rest of the popup/selector traffic.

## What changes

**forteseq/FORTESEQ2.amxd**: 1 new box (`route gotopage`, obj-819) spliced into the existing
obj-751->obj-23 patchline (removed, replaced by obj-751->obj-819, obj-819 outlet0->obj-485,
obj-819 outlet1 (reject)->obj-23).

**forteseq/fs2horizon.js**: onclick() sends one extra `outlet(0, ['gotopage', N])` right after the
existing setvoice* send, only on the four ext/art/lec transitions to ON and the two ton/fijar
transitions to ON (fijar's click already requires keyOwn, so no extra ext ON-guard needed there).
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
JS = os.path.join('forteseq', 'fs2horizon.js')

ROUTE_ID = 'obj-819'

JS_OLD = """	if (cg.art && ptIn(cg.art, x, y)) { vk.artOwn = !vk.artOwn; outlet(0, ['setvoiceartown', v + 1, vk.artOwn ? 1 : 0]); mgraphics.redraw(); return; }
	if (cg.lec && ptIn(cg.lec, x, y)) { vk.readOwn = !vk.readOwn; outlet(0, ['setvoicereadown', v + 1, vk.readOwn ? 1 : 0]); mgraphics.redraw(); return; }
	if (cg.ton && ptIn(cg.ton, x, y)) {
		vk.keyOwn = !vk.keyOwn;
		if (!vk.keyOwn) vk.keyLock = 0;   // Fijar has no effect without TonProp -- keep it from looking "already on" if TonProp comes back
		outlet(0, ['setvoicekeyown', v + 1, vk.keyOwn ? 1 : 0]); mgraphics.redraw(); return;
	}
	if (cg.fijar && vk.keyOwn && ptIn(cg.fijar, x, y)) { var nl = vk.keyLock === 1 ? 0 : 1; vk.keyLock = nl; outlet(0, ['setvoicekeylock', v + 1, nl]); mgraphics.redraw(); return; }"""

JS_NEW = """	if (cg.art && ptIn(cg.art, x, y)) {
		vk.artOwn = !vk.artOwn;
		outlet(0, ['setvoiceartown', v + 1, vk.artOwn ? 1 : 0]);
		if (vk.artOwn) outlet(0, ['gotopage', PAGE_VOCES2]);
		mgraphics.redraw(); return;
	}
	if (cg.lec && ptIn(cg.lec, x, y)) {
		vk.readOwn = !vk.readOwn;
		outlet(0, ['setvoicereadown', v + 1, vk.readOwn ? 1 : 0]);
		if (vk.readOwn) outlet(0, ['gotopage', PAGE_VOCES2]);
		mgraphics.redraw(); return;
	}
	if (cg.ton && ptIn(cg.ton, x, y)) {
		vk.keyOwn = !vk.keyOwn;
		if (!vk.keyOwn) vk.keyLock = 0;   // Fijar has no effect without TonProp -- keep it from looking "already on" if TonProp comes back
		outlet(0, ['setvoicekeyown', v + 1, vk.keyOwn ? 1 : 0]);
		if (vk.keyOwn) outlet(0, ['gotopage', PAGE_VOCES4]);
		mgraphics.redraw(); return;
	}
	if (cg.fijar && vk.keyOwn && ptIn(cg.fijar, x, y)) {
		var nl = vk.keyLock === 1 ? 0 : 1; vk.keyLock = nl;
		outlet(0, ['setvoicekeylock', v + 1, nl]);
		if (nl) outlet(0, ['gotopage', PAGE_VOCES4]);
		mgraphics.redraw(); return;
	}"""

JS_EXT_OLD = "	if (ptIn(cg.ext, x, y)) { vk.ext = !vk.ext; outlet(0, ['setvoiceexternal', v + 1, vk.ext ? 1 : 0]); mgraphics.redraw(); return; }"
JS_EXT_NEW = """	if (ptIn(cg.ext, x, y)) {
		vk.ext = !vk.ext;
		outlet(0, ['setvoiceexternal', v + 1, vk.ext ? 1 : 0]);
		if (vk.ext) outlet(0, ['gotopage', PAGE_VOCES1]);
		mgraphics.redraw(); return;
	}"""

JS_CONST_ANCHOR = "var rowGeo = null;\nvar chipGeo = [];"
JS_CONST_NEW = JS_CONST_ANCHOR + """

// "Pagina" (fs2_pagina) values for the tabs each advanced chip's real control lives on -- see
// add_fs2_gotopage.py for how these were measured. On/mute (cg.on) has no page: its control is
// always on the main panel, never gated by Pagina.
var PAGE_VOCES1 = 6, PAGE_VOCES2 = 7, PAGE_VOCES4 = 10;"""


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    assert ROUTE_ID not in bx, 'ya aplicado (amxd)'

    old_line = {'source': ['obj-751', 0], 'destination': ['obj-23', 0]}
    assert old_line in [l['patchline'] for l in P['lines']], 'no se encontro obj-751->obj-23'

    P['boxes'].append({'box': {
        'id': ROUTE_ID, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 2,
        'outlettype': ['', ''], 'varname': 'fs2_gotopage_route',
        'patching_rect': [2400.0, 3400.0, 120.0, 20.0], 'text': 'route gotopage'}})

    P['lines'] = [l for l in P['lines'] if l['patchline'] != old_line]
    P['lines'].append({'patchline': {'source': ['obj-751', 0], 'destination': [ROUTE_ID, 0]}})
    P['lines'].append({'patchline': {'source': [ROUTE_ID, 0], 'destination': ['obj-485', 0]}})
    P['lines'].append({'patchline': {'source': [ROUTE_ID, 1], 'destination': ['obj-23', 0]}})

    src = open(JS, encoding='utf-8').read()
    assert src.count(JS_CONST_ANCHOR) == 1
    assert src.count(JS_EXT_OLD) == 1
    assert src.count(JS_OLD) == 1
    src2 = src.replace(JS_CONST_ANCHOR, JS_CONST_NEW, 1)
    src2 = src2.replace(JS_EXT_OLD, JS_EXT_NEW, 1)
    src2 = src2.replace(JS_OLD, JS_NEW, 1)

    print('FORTESEQ2.amxd: +1 box (%s route gotopage), obj-751->obj-23 reemplazado por '
          'obj-751->%s->{obj-485, obj-23}' % (ROUTE_ID, ROUTE_ID))
    print('fs2horizon.js: +PAGE_VOCES1/2/4 consts, +gotopage sends en ext/art/lec/ton/fijar (solo al pasar a ON)')

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before-gotopage')
    amxd.save(DEVICE, data, s, e, doc)

    with open(JS, 'w', encoding='utf-8', newline='') as f:
        f.write(src2)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    assert ROUTE_ID in bx2
    src3 = open(JS, encoding='utf-8').read()
    assert 'PAGE_VOCES1' in src3 and 'PAGE_VOCES2' in src3 and 'PAGE_VOCES4' in src3

    print('\nescrito %s y %s (.before-gotopage del .amxd guardado). Sigue:' % (DEVICE, JS))
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  en Max: CERRAR el device en Live, volver a abrirlo')


main()
