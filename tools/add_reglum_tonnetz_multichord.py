"""Add a `RegLum` parameter (register-responsive luminosity, replicating invertedprism's
registerMode / ANIMIDI's RegLum) to tonnetz.amxd and multichord.amxd.

JS side is already done (tonnetz.js `reglum` handler + refreshRegPalette; multichord.js
`setreglum` + register-adjusted paletteOpts). This only adds the control + plumbing:
  * clone the PalLum live.numbox -> RegLum (init 0 = unchanged behaviour)
  * clone its `prepend <x>` helper -> `prepend reglum` / `prepend setreglum`
  * wire: RegLum -> prepend -> (jsui | subpatcher outlet); loadbang -> RegLum
  * registries: box valueof order, top-level parameters composite key, a free bank slot

Run with both devices closed in Max and Live. Timestamped .bak each; re-reads + self-checks
+ check_structure.py + node --check.
"""
import copy
import datetime
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEVICES = {
    'multichord': dict(
        amxd=os.path.join(ROOT, 'forteseq', 'multichord.amxd'),
        js=os.path.join(ROOT, 'forteseq', 'multichord.js'),
        subprefix='obj-40',                 # composite key prefix  obj-40::<id>
        pallum_id='obj-206', pp_id='p_obj-206',
        new_id='obj-230', new_pp_id='p_obj-230',
        new_varname='c_obj_230', new_pp_varname='p_obj-230',
        prepend_text='prepend setreglum',
        pp_dest='obj-2',                    # prepend setpallum feeds this (subpatcher outlet)
        loadbang_id='obj-9',
        numbox_rect=[460.0, 56.0, 52.0, 15.0],
        label=dict(id='obj-l43', varname='c_l43', clone='obj-l19',
                   text='RegL', rect=[460.0, 40.0, 64.0, 16.0]),
        mmin=0.0, mmax=1.0, unitstyle=1, initial=0.0, order=14,
        bank='1', bank_name='Steps mode',
    ),
    'tonnetz': dict(
        amxd=os.path.join(ROOT, 'forteseq', 'tonnetz.amxd'),
        js=os.path.join(ROOT, 'forteseq', 'tonnetz.js'),
        subprefix='obj-10',
        pallum_id='obj-158', pp_id='obj-158p',
        new_id='obj-338', new_pp_id='obj-338p',
        new_varname='tzw_reglum', new_pp_varname='tzw_pp_reglum',
        prepend_text='prepend reglum',
        pp_dest='obj-100',                  # prepend pallum feeds the jsui directly
        loadbang_id='obj-199',
        numbox_rect=[718.0, 70.0, 40.0, 18.0],
        label=None,                         # tonnetz's palette row has no per-control comments
        mmin=0.0, mmax=100.0, unitstyle=0, initial=0.0, order=55,
        bank='7', bank_name='Paleta',
    ),
}


def find_sub_with_jsui(p):
    for e in p.get('boxes', []):
        b = e.get('box', {})
        if 'patcher' in b:
            if any(e2.get('box', {}).get('maxclass') == 'jsui' for e2 in b['patcher'].get('boxes', [])):
                return b
            r = find_sub_with_jsui(b['patcher'])
            if r:
                return r
    return None


def by_id(boxes, bid):
    for e in boxes:
        if e.get('box', {}).get('id') == bid:
            return e['box']
    raise KeyError(bid)


def do_device(name, cfg):
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(cfg['amxd'], cfg['amxd'] + '.bak-' + ts)

    data, start, end, doc = amxd.load(cfg['amxd'])
    root = doc['patcher']
    sb = find_sub_with_jsui(root)
    assert sb['id'] == cfg['subprefix'], (name, sb['id'], cfg['subprefix'])
    P = sb['patcher']
    B, L = P['boxes'], P['lines']

    pallum = by_id(B, cfg['pallum_id'])
    pp = by_id(B, cfg['pp_id'])

    # --- RegLum numbox (clone PalLum) --------------------------------------------------
    nb = copy.deepcopy(pallum)
    nb['id'] = cfg['new_id']
    nb['varname'] = cfg['new_varname']
    nb['patching_rect'] = list(cfg['numbox_rect'])
    nb['presentation_rect'] = list(cfg['numbox_rect'])
    nb['annotation'] = ('Luminosidad por registro (RegLum): tira la luz de la rueda hacia '
                        'octaveToLum(octava) -- agudo mas claro, grave mas oscuro (igual que '
                        'el registerMode de invertedprism). 0 = plano / sin efecto.')
    vo = nb['saved_attribute_attributes']['valueof']
    vo['parameter_longname'] = 'RegLum'
    vo['parameter_shortname'] = 'RegL'
    vo['parameter_mmin'] = cfg['mmin']
    vo['parameter_mmax'] = cfg['mmax']
    vo['parameter_unitstyle'] = cfg['unitstyle']
    vo['parameter_initial'] = [cfg['initial']]
    vo['parameter_initial_enable'] = 1
    vo['parameter_order'] = cfg['order']
    B.append({'box': nb})

    # --- prepend helper (clone PalLum's) --------------------------------------------
    npp = copy.deepcopy(pp)
    npp['id'] = cfg['new_pp_id']
    npp['varname'] = cfg['new_pp_varname']
    npp['text'] = cfg['prepend_text']
    pr = list(pp.get('patching_rect', [16.0, 1400.0, 120.0, 22.0]))
    pr[1] = pr[1] + 26.0
    npp['patching_rect'] = pr
    npp['hidden'] = 1
    B.append({'box': npp})

    # --- optional label comment ---------------------------------------------------
    if cfg['label']:
        lc = copy.deepcopy(by_id(B, cfg['label']['clone']))
        lc['id'] = cfg['label']['id']
        lc['varname'] = cfg['label']['varname']
        lc['text'] = cfg['label']['text']
        lc['patching_rect'] = list(cfg['label']['rect'])
        lc['presentation_rect'] = list(cfg['label']['rect'])
        B.append({'box': lc})

    # --- wiring -----------------------------------------------------------------
    def link(s, d, hidden=True):
        pl = {'source': [s, 0], 'destination': [d, 0]}
        if hidden:
            pl['hidden'] = 1
        L.append({'patchline': pl})

    link(cfg['new_id'], cfg['new_pp_id'])
    link(cfg['new_pp_id'], cfg['pp_dest'])
    link(cfg['loadbang_id'], cfg['new_id'])

    # --- registries -----------------------------------------------------------
    tp = root['parameters']
    key = cfg['subprefix'] + '::' + cfg['new_id']
    tp[key] = ['RegLum', 'RegL', cfg['order']]
    bank = tp['parameterbanks'][cfg['bank']]
    assert bank['name'] == cfg['bank_name'], (name, bank['name'])
    slot = bank['parameters'].index('-')
    bank['parameters'][slot] = 'RegLum'

    amxd.save(cfg['amxd'], data, start, end, doc)

    # --- verify -----------------------------------------------------------
    _, _, _, d2 = amxd.load(cfg['amxd'])
    r2 = d2['patcher']
    P2 = find_sub_with_jsui(r2)['patcher']
    nb2 = by_id(P2['boxes'], cfg['new_id'])
    assert nb2['saved_attribute_attributes']['valueof']['parameter_longname'] == 'RegLum'
    assert r2['parameters'][key] == ['RegLum', 'RegL', cfg['order']]
    assert 'RegLum' in r2['parameters']['parameterbanks'][cfg['bank']]['parameters']
    edges = {(e['patchline']['source'][0], e['patchline']['destination'][0]) for e in P2['lines']}
    for pair in ((cfg['new_id'], cfg['new_pp_id']), (cfg['new_pp_id'], cfg['pp_dest']),
                 (cfg['loadbang_id'], cfg['new_id'])):
        assert pair in edges, (name, 'missing line', pair)
    orders = sorted(v[2] for k, v in r2['parameters'].items()
                    if k not in ('parameterbanks', 'inherited_shortname', 'parameter_overrides')
                    and isinstance(v, list))
    assert orders == list(range(cfg['order'] + 1)), (name, orders[-5:])
    print('%-11s OK: RegLum order %d, bank %s, wired, %d params 0..%d'
          % (name, cfg['order'], cfg['bank_name'], len(orders), cfg['order']))

    cs = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'check_structure.py'), cfg['amxd']],
                        capture_output=True, text=True)
    print('   ' + (cs.stdout.strip() or cs.stderr.strip()))
    assert cs.returncode == 0
    nc = subprocess.run(['node', '--check', cfg['js']], capture_output=True, text=True)
    print('   node --check %s: %s' % (os.path.basename(cfg['js']),
                                      'OK' if nc.returncode == 0 else nc.stderr.strip()))
    assert nc.returncode == 0


def main():
    for name, cfg in DEVICES.items():
        do_device(name, cfg)


if __name__ == '__main__':
    main()
