"""Assemble the Payhip upload folders under release/ from the devices in forteseq/.

    python tools/package_release.py                 dry run: list every product and its files
    python tools/package_release.py --apply         write release/<Product>/ trees
    python tools/package_release.py --apply --zip   also write release/zips/<Product>.zip
    python tools/package_release.py FORTESEQ2        just that product (any --flags still apply)

Why this exists: a .amxd resolves `js foo.js` / bpatcher `foo.maxpat` from its OWN folder
first (see CLAUDE.md "The FORTESEQ devices"), so a shippable device is just the .amxd plus
the .js / .maxpat files it names, all in one flat folder. This script reads each device's
`dependency_cache` AND scans its patcher boxes for js/jsui/v8/v8ui/bpatcher filenames
(forteseqwf.amxd has an empty dependency_cache, so the box scan is not optional), copies
exactly those files next to the .amxd, drops in README.txt / LICENSE.txt, and zips it.

STRICT WHITELIST: only the .amxd, its resolved deps, README.txt and LICENSE.txt ever land
in a product folder. The academic PDFs in forteseq/, the *.amxd.before* backups,
device_backup/ and test/ are never copied -- there is an assertion that re-checks this on
the finished tree.

Lite variants: their .amxd is produced by tools/make_lite.py into release/_stage/ first.
If a Lite source is missing this script warns and skips that product rather than failing.
"""
import os
import re
import sys
import json
import shutil
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORTESEQ = os.path.join(ROOT, 'forteseq')
STAGE = os.path.join(ROOT, 'release', '_stage')      # make_lite.py output
OUT = os.path.join(ROOT, 'release')
COPY = os.path.join(ROOT, 'sales', 'store-copy')

LICENSE_TEXT = """Conejeros Devices -- Licencia de uso

(c) Conejeros Devices. Todos los derechos reservados.

Se concede una licencia personal e intransferible para usar este dispositivo en
producciones musicales propias, comerciales o no. NO se permite revender, redistribuir,
sublicenciar ni incluir los archivos (.amxd / .js / .maxpat) en otro producto, pack o
biblioteca, gratuita o de pago.

Los archivos PDF de referencia academica citados en la documentacion NO forman parte de
esta distribucion y conservan los derechos de sus autores.

EL SOFTWARE SE ENTREGA "TAL CUAL", SIN GARANTIA DE NINGUN TIPO. Probá la version Lite
gratuita antes de comprar para confirmar compatibilidad con tu sistema.
"""

# product -> spec. 'devices' are paths; a plain name means forteseq/<name>, a name with a
# "_stage/" prefix means release/_stage/<name> (a make_lite.py output). 'ship_as' renames the
# .amxd ON COPY (source basename -> shipped basename): the source file keeps its dev name
# (`tonnetz.amxd` loading `js tonnetz.js` by bare name), only the packaged copy is renamed
# to the sale name. The .js/.maxpat travel unchanged and resolve from the folder.
PRODUCTS = {
    'FORTESEQ': {
        'devices': ['FORTESEQ2.amxd', 'forteseqhub.amxd'],
        'ship_as': {'FORTESEQ2.amxd': 'FORTESEQ.amxd'},
        'copy': 'forteseq.md',
        'blurb': 'FORTESEQ (Premium, español) + Hub. Secuenciador generativo por clases de conjunto.',
    },
    'FORTESEQ Lite': {
        'devices': ['_stage/FORTESEQ2 Lite.amxd', 'forteseqhub.amxd'],
        'ship_as': {'FORTESEQ2 Lite.amxd': 'FORTESEQ Lite.amxd'},
        'copy': 'forteseq.md',
        'blurb': 'FORTESEQ Lite (gratis, español) + Hub.',
    },
    'EVENFLOW': {
        'devices': ['forteseqwf.amxd'],
        'ship_as': {'forteseqwf.amxd': 'EVENFLOW.amxd'},
        'copy': 'evenflow.md',
        'blurb': 'EVENFLOW (Premium). Well-formed / moment-of-symmetry rhythm generator.',
    },
    'EVENFLOW Lite': {
        'devices': ['_stage/forteseqwf Lite.amxd'],
        'ship_as': {'forteseqwf Lite.amxd': 'EVENFLOW Lite.amxd'},
        'copy': 'evenflow.md',
        'blurb': 'EVENFLOW Lite (free).',
    },
    'ANIMIDI': {
        'devices': ['ANIMIDI.amxd', 'ANIMIDIFeed.amxd'],
        'copy': 'animidi.md',
        'blurb': 'ANIMIDI + ANIMIDIFeed. Animated score (Music Animation Machine). Free.',
    },
    'midibounce': {
        'devices': ['midibounce.amxd'],
        'copy': None,
        'blurb': 'midibounce. One button: records the clip as flat MIDI. Free.',
    },
    'Midirouter': {
        'devices': ['Midirouter.amxd'],
        'copy': None,
        'blurb': 'Midirouter. 8x8 note remapper with per-pad MIDI-learn + presets.',
    },
    'Harmonograph': {
        'devices': ['harmonograph.amxd'],
        'copy': 'harmonograph.md',
        'blurb': 'Harmonograph (Premium). 8-layer perfectly-balanced pendulum rhythms, drawn as a Lissajous curve.',
    },
    'Harmonograph Lite': {
        # not built yet -- needs its own make_lite variant (cap 4 layers, no presets, no
        # probability/mod lanes); this entry will SKIP with a clear message until then.
        'devices': ['_stage/harmonograph Lite.amxd'],
        'copy': 'harmonograph.md',
        'blurb': 'Harmonograph Lite (free).',
    },
    'Prism': {
        'devices': ['invertedprism.amxd'],
        'ship_as': {'invertedprism.amxd': 'Prism.amxd'},
        'copy': 'prism.md',
        'blurb': 'Prism (ex-invertedprism). Colour <-> harmony playground. Free.',
    },
    'Chordscape': {
        'devices': ['multichord.amxd'],
        'ship_as': {'multichord.amxd': 'Chordscape.amxd'},
        'copy': 'chordscape.md',
        'blurb': 'Chordscape (ex-multichord). Navigable chord-space explorer. Bundle-exclusive.',
    },
    'Conejeros MIDI Creative Pack': {
        'devices': ['FORTESEQ2.amxd', 'forteseqhub.amxd', 'forteseqwf.amxd',
                    'tonnetz.amxd', 'ANIMIDI.amxd', 'ANIMIDIFeed.amxd', 'midibounce.amxd',
                    'Midirouter.amxd', 'harmonograph.amxd', 'invertedprism.amxd',
                    'multichord.amxd'],
        'ship_as': {'FORTESEQ2.amxd': 'FORTESEQ.amxd', 'forteseqwf.amxd': 'EVENFLOW.amxd',
                    'tonnetz.amxd': 'Color Theory.amxd', 'invertedprism.amxd': 'Prism.amxd',
                    'multichord.amxd': 'Chordscape.amxd'},
        'copy': 'bundle.md',
        'blurb': 'El pack completo: 3 motores (FORTESEQ/EVENFLOW/Harmonograph) + Color Theory + Chordscape + ANIMIDI + Prism + midibounce + Midirouter.',
    },
}

# filenames that must never appear in a product folder even if something references them
FORBIDDEN = re.compile(r'\.pdf$|\.amxd\.before|(^|[\\/])device_backup([\\/]|$)|'
                       r'(^|[\\/])test([\\/]|$)|_favs\.txt$|_presets\.txt$', re.I)

DEP_BOX_RE = re.compile(r'\b(?:js|jsui|v8|v8ui|bpatcher)\b')


def _scan_patcher(p, names):
    for box in p.get('boxes', []):
        b = box.get('box', {})
        txt = b.get('text', '') or ''
        if DEP_BOX_RE.match(txt.strip()):
            for tok in txt.split()[1:]:
                if re.search(r'\.(js|maxpat|mxo|json)$', tok, re.I):
                    names.add(tok)
        # bpatcher / jsui often carry the file in an attribute, not text
        for key in ('name', 'filename', 'patchername'):
            v = b.get(key)
            if isinstance(v, str) and re.search(r'\.(js|maxpat|json)$', v, re.I):
                names.add(v)
        if b.get('patcher'):
            _scan_patcher(b['patcher'], names)


def scan_deps(doc):
    """Union of dependency_cache names and js/jsui/v8/bpatcher filenames in the boxes,
    following referenced .maxpat files one level (fs2pages -> fs2voice -> ...)."""
    names = set()
    for d in doc['patcher'].get('dependency_cache', []):
        if d.get('name'):
            names.add(d['name'])
    _scan_patcher(doc['patcher'], names)

    # chase referenced .maxpat files for their own js/bpatcher deps
    pending = [n for n in names if n.lower().endswith('.maxpat')]
    seen = set(pending)
    while pending:
        mp = os.path.join(FORTESEQ, pending.pop())
        if not os.path.isfile(mp):
            continue
        try:
            sub = json.load(open(mp, encoding='utf-8'))
        except (ValueError, OSError):
            continue
        found = set()
        _scan_patcher(sub.get('patcher', sub), found)
        for f in found:
            if f not in names:
                names.add(f)
                if f.lower().endswith('.maxpat') and f not in seen:
                    seen.add(f)
                    pending.append(f)
    return names


def resolve_dep(name):
    """A dep is resolved from forteseq/ (the folder the shipped .amxd will sit in)."""
    cand = os.path.join(FORTESEQ, name)
    return cand if os.path.isfile(cand) else None


def device_path(spec_entry):
    if spec_entry.startswith('_stage/'):
        return os.path.join(STAGE, spec_entry[len('_stage/'):])
    return os.path.join(FORTESEQ, spec_entry)


def build_product(name, spec, apply_it, do_zip):
    folder = os.path.join(OUT, name)
    files = []                       # (src_abs, arcname)
    missing = []
    ship_as = spec.get('ship_as', {})
    for entry in spec['devices']:
        dev = device_path(entry)
        if not os.path.isfile(dev):
            missing.append(entry)
            continue
        base = os.path.basename(dev)
        files.append((dev, ship_as.get(base, base)))
        data, s, e, doc = amxd.load(dev)
        for dep in sorted(scan_deps(doc)):
            src = resolve_dep(dep)
            if src is None:
                print('    !! %s references %s -- not found in forteseq/' % (os.path.basename(dev), dep))
                continue
            files.append((src, os.path.basename(src)))

    if missing:
        print('  [%s] SKIP -- missing source(s): %s' % (name, ', '.join(missing)))
        if any(m.startswith('_stage/') for m in missing):
            print('       run  python tools/make_lite.py  first')
        return None

    # dedupe by arcname, keep first
    seen = {}
    for src, arc in files:
        seen.setdefault(arc, src)
    manifest = sorted(seen.items())

    # README + LICENSE
    readme_txt = None
    if spec.get('copy'):
        cp = os.path.join(COPY, spec['copy'])
        if os.path.isfile(cp):
            readme_txt = open(cp, encoding='utf-8').read()

    print('  [%s]' % name)
    for arc, src in manifest:
        assert not FORBIDDEN.search(src), 'FORBIDDEN file slipped in: %s' % src
        print('     %-28s <- %s' % (arc, os.path.relpath(src, ROOT)))
    print('     README.txt   %s' % ('(from sales/store-copy/%s)' % spec['copy'] if readme_txt else '(none)'))
    print('     LICENSE.txt')

    if not apply_it:
        return folder

    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    for arc, src in manifest:
        shutil.copyfile(src, os.path.join(folder, arc))
    if readme_txt:
        open(os.path.join(folder, 'README.txt'), 'w', encoding='utf-8').write(readme_txt)
    open(os.path.join(folder, 'LICENSE.txt'), 'w', encoding='utf-8').write(LICENSE_TEXT)

    # re-check the finished tree
    for f in os.listdir(folder):
        assert not FORBIDDEN.search(f), 'FORBIDDEN file in %s: %s' % (folder, f)

    if do_zip:
        zdir = os.path.join(OUT, 'zips')
        os.makedirs(zdir, exist_ok=True)
        zpath = os.path.join(zdir, name + '.zip')
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(folder)):
                z.write(os.path.join(folder, f), os.path.join(name, f))
        print('     -> %s' % os.path.relpath(zpath, ROOT))
    return folder


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply_it = '--apply' in sys.argv
    do_zip = '--zip' in sys.argv
    which = args or list(PRODUCTS)

    unknown = [w for w in which if w not in PRODUCTS]
    if unknown:
        sys.exit('unknown product(s): %s\nknown: %s' % (', '.join(unknown), ', '.join(PRODUCTS)))

    print('package_release  (%s)' % ('APPLY' if apply_it else 'dry run'))
    print('output: %s\n' % os.path.relpath(OUT, ROOT))
    for name in which:
        build_product(name, PRODUCTS[name], apply_it, do_zip)
        print()
    if not apply_it:
        print('(dry run -- nothing written; re-run with --apply [--zip])')


if __name__ == '__main__':
    main()
