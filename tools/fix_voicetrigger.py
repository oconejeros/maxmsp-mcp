"""Make forteseqvoicetrigger.amxd able to trigger something again.

    python tools/fix_voicetrigger.py            dry run, writes nothing
    python tools/fix_voicetrigger.py --apply    do it

The device was written for v1 and never updated. It sends a bare voice number to FORTESEQ_TRIGGER;
the v2 engine listens on FORTESEQ_TRIG and expects (bus, voice). Wrong symbol AND wrong payload, so
it has been a device that does nothing at all -- silently, because a send with no matching receive
is not an error in Max.

Three things change. It gains a Bus, it packs the pair the way the Hub already does, and its one
parameter stops being called "live.numbox" -- the default name, which is not mappable in any
useful way and would collide with the next device that also left it alone.

Close the device in BOTH Max and Live first.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'forteseqvoicetrigger.amxd')
BLURB = ('FORTESEQ Voice Trigger: cada nota entrante dispara una voz del motor que escuche en ese '
         'bus, tomando la nota que le toque del acorde actual. Es la alternativa liviana al Hub en '
         'modo Enviar cuando queres una pista de MIDI por voz. La altura de la nota entrante no '
         'importa: solo cuenta cuando llega.')
VOICE_ANN = ('Que voz del motor dispara esta pista. Dos devices sobre el mismo bus y la misma voz '
             'disparan al mismo receptor dos veces.')
BUS_ANN = ('A que bus le habla. Es la misma direccion que el dial Bus del motor: si no coinciden, '
           'el trigger se descarta sin decir nada, porque todos los motores del set ven todos los '
           'triggers y avisar inundaria la consola a velocidad de nota.')


def numbox(bid, name, ann, lo, hi, px, py, qx, qy):
    return {'box': {
        'id': bid, 'maxclass': 'live.numbox', 'numinlets': 1, 'numoutlets': 2,
        'outlettype': ['', 'float'], 'parameter_enable': 1, 'varname': 'vt_' + name.lower(),
        'annotation': ann, 'presentation': 1, 'presentation_rect': [px, py, 44.0, 15.0],
        'patching_rect': [qx, qy, 44.0, 15.0],
        'saved_attribute_attributes': {'valueof': {
            'parameter_longname': name, 'parameter_shortname': name,
            'parameter_type': 1, 'parameter_unitstyle': 0, 'parameter_modmode': 4,
            'parameter_mmin': lo, 'parameter_mmax': hi,
            'parameter_initial': [1], 'parameter_initial_enable': 1}}}}


def main():
    apply_it = '--apply' in sys.argv
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    bv = {b.get('varname'): i for i, b in bx.items() if b.get('varname')}
    PP = P['parameters']

    send = bx[bv['send_trigger']]
    assert send['text'] == 'send FORTESEQ_TRIGGER', send['text']
    send['text'] = 'send FORTESEQ_TRIG'

    nid = [max(int(i.split('-')[1]) for i in bx if i.split('-')[1].isdigit())]

    def fresh():
        nid[0] += 1
        return 'obj-%d' % nid[0]

    # --- the voice numbox it already had ------------------------------------------------------
    voice = bx[bv['voice_select']]
    vo = voice.setdefault('saved_attribute_attributes', {}).setdefault('valueof', {})
    assert vo.get('parameter_longname') in (None, 'live.numbox'), vo.get('parameter_longname')
    vo.update({'parameter_longname': 'Voz', 'parameter_shortname': 'Voz', 'parameter_type': 1,
               'parameter_unitstyle': 0, 'parameter_modmode': 4,
               'parameter_mmin': 1.0, 'parameter_mmax': 16.0,
               'parameter_initial': [1], 'parameter_initial_enable': 1})
    voice['annotation'] = VOICE_ANN
    PP[voice['id']] = ['Voz', 'Voz', 0]
    bx[bv['voice_select_label']]['text'] = 'Voz a disparar'
    bx[bv['voice_select_label']]['presentation_rect'] = [54.0, 10.0, 195.0, 18.0]

    # --- the bus it never had -----------------------------------------------------------------
    bus = fresh()
    P['boxes'].append(numbox(bus, 'Bus', BUS_ANN, 1.0, 16.0, 10.0, 30.0, 150.0, 340.0))
    PP[bus] = ['Bus', 'Bus', 1]
    blbl = fresh()
    P['boxes'].append({'box': {
        'id': blbl, 'maxclass': 'comment', 'numinlets': 1, 'numoutlets': 0,
        'text': 'Bus del motor', 'presentation': 1,
        'presentation_rect': [54.0, 32.0, 195.0, 18.0],
        'patching_rect': [150.0, 390.0, 195.0, 18.0]}})

    # --- the pair, packed the way the Hub packs it --------------------------------------------
    # Bus through the hot inlet, voice sitting cold in the right one, so a note produces exactly
    # one (bus, voice) message in that order. Same shape as hub_send_bus_int -> hub_trig_pack,
    # deliberately: two ways of building the same message is one way too many.
    pack = fresh()
    P['boxes'].append({'box': {
        'id': pack, 'maxclass': 'newobj', 'numinlets': 2, 'numoutlets': 1, 'outlettype': [''],
        'varname': 'vt_pack', 'patching_rect': [0.0, 440.0, 70.0, 20.0], 'text': 'pack 1 1'}})

    # The [int] it already had held the voice and shouted it straight at the send. It now holds
    # the bus, which is what has to arrive first.
    bint = bx[bv['vt_voice_int']]
    bint['varname'] = 'vt_bus_int'
    bint['text'] = 'int 1'
    bint['patching_rect'] = [0.0, 390.0, 40.0, 20.0]

    keep = []
    dropped = 0
    for l in P['lines']:
        pl = l['patchline']
        touches = bint['id'] in (pl['source'][0], pl['destination'][0])
        if touches:
            dropped += 1
            continue
        keep.append(l)
    P['lines'] = keep

    for a, ao, b, bi in [
        (bv['note_bang'], 0, bint['id'], 0),      # una nota -> saca el bus
        (bus, 0, bint['id'], 1),                  # el dial Bus se guarda en frio
        (bint['id'], 0, pack, 0),                 # el bus entra por la caliente
        (voice['id'], 0, pack, 1),                # la voz espera en la fria
        (pack, 0, send['id'], 0),
        (bv['vt_init_bang'], 0, bus, 0),          # bang a un numbox = que diga su valor
    ]:
        P['lines'].append({'patchline': {'source': [a, ao], 'destination': [b, bi]}})

    bx[bv['device_label']]['text'] = BLURB

    banks = PP.get('parameterbanks')
    if banks:
        b0 = banks['0']
        if not b0['name']:
            b0['name'] = 'Trigger'
        for i, n in enumerate(['Voz', 'Bus']):
            b0['parameters'][i] = n

    print('send: FORTESEQ_TRIGGER -> FORTESEQ_TRIG')
    print('parametros: %s' % sorted(v[0] for k, v in PP.items()
                                    if k not in {'parameterbanks', 'inherited_shortname',
                                                 'parameter_overrides'}))
    print('cordones viejos del [int] retirados: %d, nuevos: 6' % dropped)
    print('banco: %s' % ' '.join(banks['0']['parameters']) if banks else '(sin bancos)')

    orders = sorted(v[2] for k, v in PP.items()
                    if k not in {'parameterbanks', 'inherited_shortname', 'parameter_overrides'})
    assert orders == list(range(len(orders))), orders

    if not apply_it:
        print('')
        print('(dry run: no se escribio nada -- corre con --apply)')
        return
    amxd.save(DEVICE, data, s, e, doc)
    print('')
    print('escrito %s' % DEVICE)


main()
