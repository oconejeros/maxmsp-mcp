"""Every tag the engine sends out of outlet 4 has to land on a connected route outlet.

This is B4, asked properly. The old count -- "19 of 48 tags recognised" -- was taken before the
panels moved into the page bpatcher, where most of the return path now lives.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
sys.path.insert(0, 'tools')
import amxd

# --- what the engine actually sends ------------------------------------------------------------
src = open(os.path.join('forteseq', 'forteseq2.js'), encoding='utf-8').read()
sent = set()
lines = src.split(chr(10))
for ln, line in enumerate(lines):
    i = line.find('outlet(4,')
    if i < 0:
        continue
    arg = line[i + 9:]
    # outlet(4, l) -- the tag is in the array the variable was built from a few lines up.
    bare = re.match(r'\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)', arg)
    if bare:
        back = chr(10).join(lines[max(0, ln - 15):ln])
        m = re.search(re.escape(bare.group(1)) + r'\s*=\s*\[\s*"([a-zA-Z0-9]+)"', back)
        if m:
            sent.add(m.group(1))
            continue
    # The first atom is the tag. Either a literal, or "v" + (v + 1) + "grado" and its siblings.
    m = re.match(r'\s*\[?\s*"([a-zA-Z0-9]+)"\s*(\+)?', arg)
    if not m:
        sent.add('?? ' + line.strip()[:60])
        continue
    if not m.group(2):
        sent.add(m.group(1))
        continue
    suf = re.search(r'\+\s*"([a-zA-Z0-9]+)"', arg[m.end():])
    pre = m.group(1)
    rng = {'v': range(1, 5), 'm': range(1, 5), 'g': range(0, 2)}.get(pre)
    if suf and rng:
        for k in rng:
            sent.add(pre + str(k) + suf.group(1))
    else:
        sent.add('?? ' + line.strip()[:60])

# --- what the patcher listens for --------------------------------------------------------------
heard = {}


def scan(patcher, where, boxes_by_id):
    for b in patcher['boxes']:
        bb = b['box']
        text = str(bb.get('text', ''))
        if not text.startswith('route '):
            continue
        args = text.split()[1:]
        wired = {l['patchline']['source'][1] for l in patcher['lines']
                 if l['patchline']['source'][0] == bb['id']}
        for i, a in enumerate(args):
            if i in wired:
                heard.setdefault(a, []).append(where)


data, s, e, doc = amxd.load(os.path.join('forteseq', 'FORTESEQ2.amxd'))
scan(doc['patcher'], 'padre', None)
pg = json.load(open(os.path.join('forteseq', 'fs2pages.maxpat'), encoding='utf-8'))['patcher']
scan(pg, 'paginas', None)
for name in ('fs2voice.maxpat',):
    p = os.path.join('forteseq', name)
    if os.path.exists(p):
        scan(json.load(open(p, encoding='utf-8'))['patcher'], name, None)

missing = sorted(t for t in sent if t not in heard)
unused = sorted(t for t in heard if t not in sent)
print('el motor manda %d etiquetas por la salida 4' % len(sent))
print('el patcher escucha %d, conectadas' % len(heard))
print('')
print('SIN DESTINO (%d): %s' % (len(missing), ', '.join(missing) if missing else 'ninguna'))
print('')
print('escuchadas y nunca mandadas (%d): %s' % (len(unused), ', '.join(unused)))
