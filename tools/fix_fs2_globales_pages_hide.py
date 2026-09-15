"""Fix: selecting the Globales tab leaves stale content from whatever page was showing before
visible underneath/behind it (reported live: numbers and column headers from another tab bleeding
through under the Globales row).

Root cause, found by tracing the Pagina (tab) switch logic: THREE independent `sel` objects, all
fed by the same live.tab (obj-485), split the page-switch job three ways --

  obj-486  `sel 0 1 2 3 4 5 6 7 8 9 10`  -- scrolls fs2_pages (the paging bpatcher) to each page's
           own vertical offset. Globales(8) -> obj-720 -> "script sendbox fs2_pages offset 0 -900".
  obj-582  `sel 6 7 8 9 10`  -- shows/hides the per-voice "advanced strip" overlay (vadv1-4 +
           vah1-23 labels) that Voces 1-4 use instead of fs2_pages; its REJECT outlet (values 0-5,
           i.e. every non-voice page) fires obj-723: "script SHOW fs2_pages, script hide vadv1-4,
           script hide vah1-23" -- the normal "go back to fs2_pages, make sure the voice overlay is
           off" cleanup. Globales(8), despite not being a voice page, is caught by this sel's MATCH
           side instead of its reject side, and fires its own message, obj-808.
  obj-617  `sel 8`  -- shows/hides Globales' own 5 controls (fs2_clockmode/rate2/bus/nvoices/
           trigmode), which live outside fs2_pages entirely. Wired correctly, not the bug.

obj-808 (Globales' obj-582 branch) reads:
    script hide fs2_pages, script hide vadv1, ..., script hide vah23
Every sibling branch that should behave the same way (obj-723, the reject/"normal page" case) reads:
    script SHOW fs2_pages, script hide vadv1, ..., script hide vah23
Same list of vadv/vah hides (correct -- Globales isn't a per-voice page, so those should stay off),
but the FIRST word is flipped: hide vs show fs2_pages. That's the bug -- almost certainly a
copy/paste from obj-800/obj-804 (Voces 3/4's own branches, which correctly say "hide fs2_pages"
because THEY show vadv1-4 in its place) with the vadv show->hide flip made but the fs2_pages
hide->show flip forgotten. With fs2_pages left hidden, selecting Globales does show its own 5
controls (obj-618, via the separate `sel 8`) but leaves whatever fs2_pages was last scrolled to
during the PREVIOUS page visible underneath -- exactly the reported overlap.

Fix: obj-808's first script command, "script hide fs2_pages", becomes "script show fs2_pages".
Nothing else in the message changes; no outlet renumbering needed (obj-582's own `sel` token list
and wiring are untouched, so this carries none of the route/sel outlet-index risk documented in
maxmsp-route-outlet-offbyone -- it's a single word inside an existing message box's text).

    python tools/fix_fs2_globales_pages_hide.py            dry run, writes nothing
    python tools/fix_fs2_globales_pages_hide.py --apply    do it (device closed in Max AND Live)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
TARGET_ID = 'obj-808'

OLD_PREFIX = 'script hide fs2_pages, script hide vadv1'
NEW_PREFIX = 'script show fs2_pages, script hide vadv1'


def main():
	apply_it = '--apply' in sys.argv

	data, s, e, doc = amxd.load(DEVICE)
	P = doc['patcher']
	bx = {b['box']['id']: b['box'] for b in P['boxes']}

	assert TARGET_ID in bx, 'no se encontro %s' % TARGET_ID
	text = bx[TARGET_ID]['text']
	assert text.startswith(OLD_PREFIX), 'el texto de %s no es el esperado:\n%s' % (TARGET_ID, text)

	new_text = NEW_PREFIX + text[len(OLD_PREFIX):]
	print('%s texto actual:\n  %s...' % (TARGET_ID, text[:70]))
	print('%s texto nuevo:\n  %s...' % (TARGET_ID, new_text[:70]))

	if not apply_it:
		print('\n(dry run: no se escribio nada -- corre con --apply)')
		return

	bx[TARGET_ID]['text'] = new_text

	shutil.copyfile(DEVICE, DEVICE + '.before-globalespageshide')
	amxd.save(DEVICE, data, s, e, doc)

	_, _, _, doc2 = amxd.load(DEVICE)
	bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
	assert bx2[TARGET_ID]['text'] == new_text

	print('\nescrito %s (.before-globalespageshide guardado). Sigue:' % DEVICE)
	print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
	print('  en Max: CERRAR el device en Live, volver a abrirlo, probar la pestana Globales')


main()
