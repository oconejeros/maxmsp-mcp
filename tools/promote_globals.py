"""Phase A: move Voces Indep / Filtro / Lock out of the fs2_pages bpatcher onto the
FORTESEQ2 main device panel.

    python tools/promote_globals.py            dry run
    python tools/promote_globals.py --apply    write FORTESEQ2.amxd + fs2pages.maxpat (+ .before)

These three toggles are the most-reached-for globals and are currently buried on the
"Armonia" page. This inverts what tools/migrate_page.py does: pull a control from the child
bpatcher up into the parent .amxd.

Per control it:
  fs2pages.maxpat  -- deletes the live.toggle, its `prepend set<x>`, the label comment, the
                      3 patchlines (toggle->prepend, prepend->outlet obj-5, obj-6->toggle),
                      and the local `parameters[<id>]` entry.
  FORTESEQ2.amxd   -- deletes parameters["obj-484::<id>"]; adds a new live.toggle
                      (parameter_enable, presentation on the y=24 global row, order 10/11/12)
                      + `prepend set<x>` -> js forteseq2.js (obj-23) + a loadbang ->
                      [outputvalue] -> toggle restore chain (the "Salida local" pattern) +
                      a label comment.

Push banks are NOT touched: they name params by longname ("Voces Indep" / "Filtro" /
"Lock"), which is preserved, so bank membership still resolves.

Leaves small gaps on the Armonia page where the toggles were -- cleaned up by the later
re-page / reflow pass. Idempotent (bails if fs2_g_indep already exists in the .amxd).
Close the device in Max AND Live before --apply.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMXD = os.path.join(ROOT, 'forteseq', 'FORTESEQ2.amxd')
PAGES = os.path.join(ROOT, 'forteseq', 'fs2pages.maxpat')

ENGINE = 'obj-23'        # js forteseq2.js  (in FORTESEQ2.amxd)
LOADBANG = 'obj-31'      # loadbang         (in FORTESEQ2.amxd)
BP = 'obj-484'           # the fs2_pages bpatcher id (parameters key prefix)

# (fs2pages toggle id, fs2pages prepend id, fs2pages label id, longname, shortname,
#  selector, new .amxd varname, toggle prect, label prect)
SPEC = [
    ('obj-10', 'obj-46', 'obj-8',  'Voces Indep', 'Indep',  'setvoiceindep',
     'fs2_g_indep',  [664.0, 24.0, 15.0, 15.0], [650.0, 5.0, 44.0, 15.0]),
    ('obj-27', 'obj-38', 'obj-28', 'Filtro',      'Filtro', 'setfilter',
     'fs2_g_filtro', [712.0, 24.0, 15.0, 15.0], [694.0, 5.0, 44.0, 15.0]),
    ('obj-18', 'obj-49', 'obj-15', 'Lock',        'Lock',   'setlock',
     'fs2_g_lock',   [760.0, 24.0, 15.0, 15.0], [744.0, 5.0, 40.0, 15.0]),
]


def toggle_valueof(longname, shortname, order):
    return {
        'parameter_longname': longname, 'parameter_shortname': shortname,
        'parameter_type': 2, 'parameter_enum': ['off', 'on'], 'parameter_mmax': 1,
        'parameter_modmode': 0, 'parameter_initial_enable': 1, 'parameter_initial': [0],
        'parameter_order': order,
    }


def strip_pages(doc_pages):
    P = doc_pages['patcher']
    kill_boxes = set()
    for tid, pid, lid, *_ in SPEC:
        kill_boxes.update([tid, pid, lid])
    P['boxes'] = [b for b in P['boxes'] if b['box'].get('id') not in kill_boxes]
    P['lines'] = [ln for ln in P['lines']
                  if ln['patchline']['source'][0] not in kill_boxes
                  and ln['patchline']['destination'][0] not in kill_boxes]
    prm = P.get('parameters', {})
    for tid, *_ in SPEC:
        prm.pop(tid, None)
    return sorted(kill_boxes)


def patch_amxd(doc):
    P = doc['patcher']
    ids = {b['box']['id'] for b in P['boxes']}
    n = max(int(i[4:]) for i in ids if i.startswith('obj-') and i[4:].isdigit())

    prm = P['parameters']
    base_order = 1 + max(v[2] for k, v in prm.items()
                         if isinstance(v, list) and len(v) >= 3 and '::' not in k
                         and k not in ('parameterbanks', 'parameter_overrides', 'inherited_shortname'))

    def mkbox(**kw):
        P['boxes'].append({'box': kw})

    def mkline(src, so, dst, di):
        P['lines'].append({'patchline': {'source': [src, so], 'destination': [dst, di]}})

    made = []
    for i, (tid, pid, lid, longname, shortname, sel, var, tprect, lprect) in enumerate(SPEC):
        prm.pop('%s::%s' % (BP, tid), None)
        order = base_order + i
        TOG = 'obj-%d' % (n + 1); PRE = 'obj-%d' % (n + 2)
        OV = 'obj-%d' % (n + 3);  LBL = 'obj-%d' % (n + 4)
        n += 4
        py = 380.0 + i * 44
        mkbox(id=TOG, maxclass='live.toggle', numinlets=1, numoutlets=1, outlettype=[''],
              parameter_enable=1, varname=var,
              patching_rect=[950.0, py, 15.0, 15.0],
              presentation=1, presentation_rect=tprect,
              saved_attribute_attributes={'valueof': toggle_valueof(longname, shortname, order)})
        mkbox(id=PRE, maxclass='newobj', numinlets=1, numoutlets=1, outlettype=[''],
              patching_rect=[1120.0, py, 150.0, 22.0], text='prepend ' + sel,
              varname=var + '_pp', hidden=1)
        mkbox(id=OV, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
              patching_rect=[950.0, py + 22, 74.0, 22.0], text='outputvalue',
              varname=var + '_ov', hidden=1)
        mkbox(id=LBL, maxclass='comment', numinlets=1, numoutlets=0,
              patching_rect=[950.0, py - 16, 90.0, 18.0], text=shortname,
              presentation=1, presentation_rect=lprect, varname=var + '_lbl', fontsize=9.0)
        mkline(TOG, 0, PRE, 0)
        mkline(PRE, 0, ENGINE, 0)
        mkline(LOADBANG, 0, OV, 0)
        mkline(OV, 0, TOG, 0)
        prm[TOG] = [longname, shortname, order]
        made.append((var, TOG, longname, order))
    return made


def check(P, where='root'):
    by = {}
    for e in P.get('boxes', []):
        b = e['box']
        assert b['id'] not in by, '%s dup id %s' % (where, b['id'])
        by[b['id']] = b
    for ln in P.get('lines', []):
        pl = ln['patchline']
        for tag, end in (('s', pl['source']), ('d', pl['destination'])):
            b = by.get(end[0])
            assert b, '%s %s dangling -> %s' % (where, tag, end)
            m = b.get('numoutlets', 0) if tag == 's' else b.get('numinlets', 0)
            assert 0 <= end[1] < m, '%s %s %s idx %d /%d (%s)' % (
                where, tag, end[0], end[1], m, b.get('text', b.get('maxclass')))
    for e in P.get('boxes', []):
        if e['box'].get('patcher'):
            check(e['box']['patcher'], where + '::' + e['box']['id'])


def main():
    apply_it = '--apply' in sys.argv
    pdoc = {'patcher': json.load(open(PAGES, encoding='utf-8'))['patcher']}
    if any(b['box'].get('varname') == 'fs2_g_indep' for b in amxd.load(AMXD)[3]['patcher']['boxes']):
        print('already promoted (fs2_g_indep exists) -- nothing to do'); return

    killed = strip_pages(pdoc)
    check(pdoc['patcher'], 'fs2pages')

    data, s, e, doc = amxd.load(AMXD)
    made = patch_amxd(doc)
    check(doc['patcher'], 'amxd')

    print('promote_globals')
    print('  fs2pages.maxpat: removed boxes %s + their lines + local params' % ', '.join(killed))
    print('  FORTESEQ2.amxd : dropped obj-484::{obj-10,obj-27,obj-18}; added:')
    for var, tid, longname, order in made:
        print('     %-14s %s  "%s"  order %d  -> prepend -> %s' % (var, tid, longname, order, ENGINE))

    if not apply_it:
        print('\n(dry run -- nothing written; re-run with --apply)')
        return

    shutil.copyfile(PAGES, PAGES + '.before')
    with open(PAGES, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pdoc['patcher']}, f, indent=1)
    shutil.copyfile(AMXD, AMXD + '.before')
    amxd.save(AMXD, data, s, e, doc)

    # round-trip
    back = amxd.load(AMXD)[3]['patcher']
    assert any(b['box'].get('varname') == 'fs2_g_lock' for b in back['boxes'])
    assert 'obj-484::obj-10' not in back['parameters']
    bp = json.load(open(PAGES, encoding='utf-8'))['patcher']
    assert not any(b['box'].get('id') == 'obj-10' for b in bp['boxes'])
    print('\nwrote both files (+ .before). now:')
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd forteseq/fs2pages.maxpat')
    print('  python tools/check_params3.py')


if __name__ == '__main__':
    main()
