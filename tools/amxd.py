"""Read and write the AMPF container that a Max for Live .amxd is.

Some things about a device are unreachable from the MCP and have to be edited on disk:
Live's parameter metadata (names, ranges, initial values, bank membership), the
presentation flags that decide whether the device draws anything at all, a comment's
text, and the "annotation" key that becomes Live's hover help. This module is what those
patch scripts import.

Layout: magic 'ampf' at 0, 'meta' at 12, 'ptch' at 24 with a 4-byte little-endian length
at offset 28 that must equal filesize - 32. Plaintext JSON starts at 32 and is followed
by CRLF + NUL. save() rewrites that length header, which is the step that turns a
working edit into a file Max refuses to open if you skip it.

Edit with the device closed in BOTH Max and Live -- whichever saves last silently
overwrites the other. Typical use:

    import amxd
    data, start, end, doc = amxd.load(PATH)
    ...mutate doc['patcher']['boxes'] / ['lines'] / ['parameters']...
    amxd.save(PATH, data, start, end, doc)
    amxd.load(PATH)   # read it back and assert what you meant to change

Parameters live in three registries that must agree; see the amxd-parameter-registries
note. Take a .before copy first -- a malformed device fails silently in Live.
"""
import json

def load(path):
    data = open(path, 'rb').read()
    start = data.find(b'"patcher"')
    while data[start] != 0x7b:
        start -= 1
    backslash, dquote, obrace, cbrace = 0x5c, 0x22, 0x7b, 0x7d
    depth = 0; in_str = False; esc = False; end = None
    for i in range(start, len(data)):
        b = data[i]
        if in_str:
            if esc: esc = False
            elif b == backslash: esc = True
            elif b == dquote: in_str = False
            continue
        if b == dquote: in_str = True
        elif b == obrace: depth += 1
        elif b == cbrace:
            depth -= 1
            if depth == 0:
                end = i + 1; break
    doc = json.loads(data[start:end].decode('utf-8'))
    return data, start, end, doc

def save(path, data, start, end, doc):
    """Rewrite the file, patching the ptch chunk length header."""
    body = json.dumps(doc, indent=1, separators=(',', ' : ')).encode('utf-8')
    body = body.replace(b'\n', b'\r\n')
    trailer = data[end:]              # bytes after the JSON (CRLF + NUL)
    head = bytearray(data[:start])
    chunk_len = len(body) + len(trailer)
    # 'ptch' magic sits at start-8; its 4-byte LE length at start-4
    assert bytes(head[start - 8:start - 4]) == b'ptch', bytes(head[start - 8:start - 4])
    head[start - 4:start] = chunk_len.to_bytes(4, 'little')
    open(path, 'wb').write(bytes(head) + body + trailer)
    return len(body)

def params(doc):
    """varname -> the valueof dict that holds the parameter attributes."""
    out = {}
    def walk(p):
        for box in p.get('boxes', []):
            b = box.get('box', {})
            vo = (b.get('saved_attribute_attributes') or {}).get('valueof')
            if vo is not None and b.get('varname'):
                out[b['varname']] = vo
            if b.get('patcher'):
                walk(b['patcher'])
    walk(doc['patcher'])
    return out
