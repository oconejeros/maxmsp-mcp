"""Put Set actual and Forte in the strip that every tab can see.

    python tools/move_readouts.py            dry run, writes nothing
    python tools/move_readouts.py --apply    do it

Which set is playing is the single most useful thing the device says, and until now it only said
it on the Armonia page. The strip along the bottom of the parent is the only real estate that
survives a change of tab, so that is where it belongs.

The strip is 582 px wide and full. Measured over all 351 classes, the four readouts want:

    Set actual   "100"                                        30 px
    Forte        "4-Z15A <111111>"                           112 px
    Notas        "C4 C#4 D4 D#4 E4 F4 F#4 G4 G#4 A4 A#4 B4"  290 px
    MIDI         "V1:C3 V2:C3 V3:C3 V4:C3"                   168 px

With labels and gaps that is 805 px. Something had to leave, and it is the per-voice monitor:
it is the one readout that does not describe the harmony -- it describes what sounded one step
ago -- and it is the only one already fitted with an off switch, which is a statement about how
essential it is. It moves to the bottom row of the Armonia page, where it gets 478 px instead of
the 148 it had been squeezed into, so it stops clipping at four voices and stays readable to about
eleven.

Even after that the arithmetic is 26 px short, so the word "Notas" goes. It is the one label of
the four whose readout identifies itself: a row of note names needs no sign saying note names, and
a clipped readout looks broken in a way a missing label does not.

Close the device in BOTH Max and Live first.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
MERGED = os.path.join('forteseq', 'fs2pages.maxpat')
STRIP_Y = 147.0
MON_ANN = ('Que nota tiene sonando cada voz en este momento. Un guion es una voz muteada, externa '
           'o en silencio. El toggle Mon, en la franja de abajo, lo apaga: repintar este texto es '
           'trabajo de interfaz de Live y a velocidad de nota no se alcanza a leer igual.')
IDX_ANN = 'Cual de las 351 clases Tn esta sonando, por su numero en el catalogo.'
FORTE_ANN = ('El nombre Forte de la clase que suena y su vector interválico entre < >. El vector '
             'cuenta cuantas veces aparece cada intervalo: <222121> tiene dos semitonos, dos '
             'tonos, dos terceras menores, una mayor, dos cuartas y una vez el tritono.')


def main():
    apply_it = '--apply' in sys.argv

    # ---- the page that takes in the monitor ----------------------------------------------------
    pg = json.load(open(MERGED, encoding='utf-8'))['patcher']
    pb = {b['box']['id']: b['box'] for b in pg['boxes']}
    nxt = [max(int(i.split('-')[1]) for i in pb)]

    def fresh():
        nxt[0] += 1
        return 'obj-%d' % nxt[0]

    xof = lambda i: pb[i]['patching_rect'][0]
    ins = sorted([i for i, b in pb.items() if b['maxclass'] == 'inlet'], key=xof)
    assert len(ins) == 4, len(ins)
    # A bpatcher orders its inlets by where the inlet objects sit horizontally, so the new one has
    # to be placed to the RIGHT of every existing one or it would renumber the other four and
    # every cord in the parent would land somewhere else.
    right = max(pb[i]['patching_rect'][0] for i in ins)
    new_in = fresh()
    pg['boxes'].append({'box': {
        'id': new_in, 'maxclass': 'inlet', 'numinlets': 0, 'numoutlets': 1, 'outlettype': [''],
        'comment': 'salida 5 del js (monitor por voz)',
        'patching_rect': [right + 70.0, 20.0, 30.0, 30.0]}})

    prep = fresh()
    pg['boxes'].append({'box': {
        'id': prep, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'fs2_disp_mon_prep', 'patching_rect': [right + 70.0, 70.0, 90.0, 22.0],
        'text': 'prepend set'}})

    # Bottom row of the Armonia page, which is page 0 and stops at y = 119.
    lbl = fresh()
    pg['boxes'].append({'box': {
        'id': lbl, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'text': 'MIDI',
        'presentation': 1, 'presentation_rect': [0.0, 121.0, 34.0, 18.0],
        'patching_rect': [right + 70.0, 110.0, 34.0, 18.0]}})
    disp = fresh()
    pg['boxes'].append({'box': {
        'id': disp, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'text': '--',
        'varname': 'fs2_disp_mon', 'annotation': MON_ANN,
        'presentation': 1, 'presentation_rect': [38.0, 121.0, 478.0, 18.0],
        'patching_rect': [right + 70.0, 140.0, 478.0, 18.0]}})
    pg['lines'].append({'patchline': {'source': [new_in, 0], 'destination': [prep, 0]}})
    pg['lines'].append({'patchline': {'source': [prep, 0], 'destination': [disp, 0]}})

    used = max(b['box']['presentation_rect'][1] + b['box']['presentation_rect'][3]
               for b in pg['boxes']
               if b['box'].get('presentation') and b['box']['presentation_rect'][1] < 150.0)
    print('pagina Armonia: el monitor entra en y 121..139, alto usado %.0f de 142' % used)
    assert used <= 142.0, used

    # ---- the parent ----------------------------------------------------------------------------
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}
    nid = [max(int(i.split('-')[1]) for i in bx)]

    def pfresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    BP, GEN = bv['fs2_pages'], bv['fs2_gen']
    P['lines'].append({'patchline': {'source': [GEN, 5], 'destination': [BP, 4]}})

    # Out with the copies the parent used to own: the readout, its label and its formatter.
    doomed = {bv['fs2_disp_mon'], bv['fs2_lbl_midi'], bv['fs2_disp_mon_prep']}
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] not in doomed]
    before = len(P['lines'])
    P['lines'] = [l for l in P['lines']
                  if not (doomed & {l['patchline']['source'][0], l['patchline']['destination'][0]})]
    print('padre: %d cajas retiradas, %d cordones' % (len(doomed), before - len(P['lines'])))

    # The word "Notas" goes; see the module docstring. Its readout keeps its full width.
    P['boxes'] = [b for b in P['boxes'] if b['box']['id'] != bv['fs2_lbl_notas']]

    def comment(text, x, w, **kw):
        cid = pfresh()
        b = {'id': cid, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0, 'text': text,
             'presentation': 1, 'presentation_rect': [x, STRIP_Y, w, 18.0],
             'patching_rect': [2400.0, 3300.0 + x, w, 18.0]}
        b.update(kw)
        P['boxes'].append({'box': b})
        return cid

    #  Set  80   Forte  5-Z12 <222121>   C4 E4 G4 ...              Mon [x]
    comment('Set', 542.0, 26.0)
    idx = comment('1', 572.0, 30.0, varname='fs2_disp_idx_top', annotation=IDX_ANN)
    comment('Forte', 608.0, 38.0)
    forte = comment('--', 650.0, 112.0, varname='fs2_disp_forte_top', annotation=FORTE_ANN)
    bx[bv['fs2_disp_notes']]['presentation_rect'] = [770.0, STRIP_Y, 290.0, 18.0]
    # The Mon label was never given a varname, so it is found by its text.
    for b in P['boxes']:
        bb = b['box']
        if bb.get('text') == 'Mon' and bb.get('presentation'):
            bb['presentation_rect'] = [1068.0, STRIP_Y, 26.0, 18.0]
    bx[bv['fs2_mon']]['presentation_rect'] = [1097.0, STRIP_Y + 1.0, 15.0, 15.0]

    for out, dest in [(1, idx), (7, forte)]:
        p = pfresh()
        P['boxes'].append({'box': {
            'id': p, 'maxclass': 'newobj', 'numinlets': 1, 'numoutlets': 1, 'outlettype': [''],
            'patching_rect': [2400.0, 3260.0 + out * 26.0, 90.0, 22.0], 'text': 'prepend set'}})
        P['lines'].append({'patchline': {'source': [GEN, out], 'destination': [p, 0]}})
        P['lines'].append({'patchline': {'source': [p, 0], 'destination': [dest, 0]}})

    # Nothing in the strip may overlap anything else in it, and nothing may run past the edge.
    strip = sorted([b['box']['presentation_rect'] for b in P['boxes']
                    if b['box'].get('presentation')
                    and b['box']['presentation_rect'][1] >= 145.0])
    print('la franja, de izquierda a derecha:')
    prev = 0.0
    for r in strip:
        txt = [b['box'].get('varname') or str(b['box'].get('text', ''))[:14]
               for b in P['boxes'] if b['box'].get('presentation_rect') == r][0]
        print('   x %6.1f..%7.1f  %s' % (r[0], r[0] + r[2], txt))
        assert r[0] >= prev, 'se pisan en x=%.1f' % r[0]
        prev = r[0] + r[2]
    print('borde derecho: %.1f de 1124' % prev)
    assert prev <= 1124.0, prev

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    with open(MERGED, 'w', encoding='utf-8', newline='') as f:
        json.dump({'patcher': pg}, f, indent=1)
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escritos %s y %s' % (MERGED, DEVICE))


main()
