"""Achica el viewport del bpatcher `fs2_pages` en las tabs donde el device dibuja controles PROPIOS
encima de el, porque ahi el bpatcher se come los clicks y esos controles quedan muertos.

    python tools/fix_pages_viewport.py            dry run, no escribe nada
    python tools/fix_pages_viewport.py --apply    lo hace (device cerrado en Max Y en Live)

## El sintoma

Reportado 2026-09-25: en el device, la mitad derecha de algunas tabs no responde -- en Armonia son
Root / Sub / Oct M / Raiz sec, en Artic son Preset Silencio / S.Nor / S.Ac / Hum. Los controles del
MEDIO de esas mismas tabs si funcionan, y los de la izquierda (RunLec / Ord / Rng) y los de la
derecha del todo (Proximos 16 / Vista) tambien.

## Por que es el bpatcher

`fs2_pages` (obj-484) ocupa x 294..660 en presentation. El esquema de 9 tabs superpone controles del
patcher RAIZ encima de esa zona y los trae al frente con `script front`. Se dibujan bien -- se ven
en pantalla -- pero no reciben el click: el bpatcher captura el mouse sobre todo su rectangulo, y
`script front` no lo cambia.

La correlacion cierra sin excepciones sobre las 9 tabs:

    tab       fs2_pages   controles del padre encima   responde
    Armonia   VISIBLE     Root/Sub/OctM/RaizSec        NO
    Filtro    VISIBLE     ninguno                      si
    Artic     VISIBLE     PresetSil/S.Nor/S.Ac/Hum     NO
    Tiempo    VISIBLE     ninguno                      si
    Modul     VISIBLE     ninguno                      si
    Voces     oculto      (tiras de voz)               si
    Ornam     oculto      racimo Ornamento             si
    Sesion    VISIBLE     Fav/ProgFav/Reparto/...      NO
    Global    oculto      Clock/Bus/Voces/...          si

Las tabs que andan o esconden el bpatcher, o no le ponen nada encima. Las tres que fallan son las
tres que hacen las dos cosas a la vez. (No era el `parameter_order`, que se reparo aparte en
tools/fix_param_order_dense.py: RunLec/Ord/Rng estaban en aquel grupo roto y siempre respondieron,
porque estan a la izquierda del bpatcher.)

## El arreglo, y por que es gratis

El contenido propio de `fs2pages.maxpat` termina ANTES de donde arrancan los controles superpuestos,
en las tres tabs con conflicto: Armonia usa 211 px de los 222 disponibles, Artic 261 de 266, Sesion
264 de 272. Asi que alcanza con que cada tab fije el ancho del viewport justo antes del primer
control del padre, y no se pierde nada de lo que hoy se ve.

Cada mensaje de tab recibe una clausula `script sendbox fs2_pages presentation_rect <x> <y> <w> <h>`
-- mismo idioma que el `script sendbox fs2_pages offset` que esas mismas mensajes ya usan para
paginar (ver la memoria max-bpatcher-paging: esa familia funciona aunque el doc de Max no la liste).
Las tabs sin conflicto reciben la clausula con el ancho COMPLETO, para que el viewport vuelva a
abrirse al salir de una tab angosta.

Si `presentation_rect` por sendbox no tomara, el sintoma seria que nada cambia (ni error ni panel en
blanco): el plan B es encoger el bpatcher de forma permanente a 272 px, lo que arregla las tres tabs
y le recorta 38 px a Tiempo, la unica que necesita mas.
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

DEVICE = os.path.join('forteseq', 'FORTESEQ2.amxd')
PAGES_ID = 'obj-484'
PAGES_VAR = 'fs2_pages'
TABS = [('Armonia', 'obj-869'), ('Filtro', 'obj-870'), ('Artic', 'obj-871'), ('Tiempo', 'obj-872'),
        ('Modul', 'obj-873'), ('Voces', 'obj-874'), ('Ornam', 'obj-875'), ('Sesion', 'obj-876'),
        ('Global', 'obj-877')]
CLAUSE = re.compile(r',?\s*script sendbox ' + PAGES_VAR + r' presentation_rect [-\d. ]+')


def main():
    apply_it = '--apply' in sys.argv

    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']
    bx = {b['box']['id']: b['box'] for b in P['boxes']}
    VX, VY, VW, VH = bx[PAGES_ID]['presentation_rect']
    assert bx[PAGES_ID]['maxclass'] == 'bpatcher' and bx[PAGES_ID].get('varname') == PAGES_VAR

    print('viewport de %s: x %g..%g (ancho %g), y %g..%g\n' % (PAGES_VAR, VX, VX + VW, VW, VY, VY + VH))
    print('%-9s %-9s %-9s %s' % ('tab', 'ancho', 'padre en', 'que se hace'))

    edits = {}
    for name, mid in TABS:
        t = bx[mid]['text']
        # En las tabs que ESCONDEN el bpatcher (Voces, Ornam, Global) no hay conflicto posible y
        # achicarlo no tendria sentido: ahi los controles del padre ocupan toda la zona a proposito.
        # Se les pone el ancho COMPLETO igual, para que el viewport quede restaurado al volver a una
        # tab que si lo muestra -- el atributo es del box, no de la tab, y persiste entre cambios.
        if ('script show ' + PAGES_VAR) not in t:
            edits[mid] = VW
            print('%-9s %-9g %-9s %s' % (name, VW, '-', 'bpatcher oculto en esta tab: ancho completo'))
            continue
        # el control del PADRE mas a la izquierda que esta tab muestra encima del viewport
        minpx = None
        for b in P['boxes']:
            b = b['box']
            vn = b.get('varname') or b['id']
            if b['id'] == PAGES_ID or not b.get('presentation'):
                continue
            if vn.startswith(('vadv', 'vah')):
                continue                       # tiras de voz: solo en Voces, donde el bpatcher se oculta
            if ('script show ' + vn) not in t:
                continue
            q = b['presentation_rect']
            if q[0] + q[2] > VX and q[0] < VX + VW and q[1] + q[3] > VY and q[1] < VY + VH:
                minpx = q[0] if minpx is None else min(minpx, q[0])

        w = VW if minpx is None else (minpx - VX)
        edits[mid] = w
        print('%-9s %-9g %-9s %s' % (name, w, minpx if minpx is not None else '-',
                                     'completo' if w == VW else 'se corta antes del primer control'))

    # el contenido que cada tab muestra tiene que caber en el ancho que le toca
    import json
    pg = json.load(open(os.path.join('forteseq', 'fs2pages.maxpat'), encoding='utf-8'))['patcher']
    pbs = [b['box']['presentation_rect'] for b in pg['boxes'] if b['box'].get('presentation')]
    print()
    for name, mid in TABS:
        t = bx[mid]['text']
        if ('script show ' + PAGES_VAR) not in t:
            continue          # no se ve: no hay contenido que recortar
        offs = re.findall(r'sendbox ' + PAGES_VAR + r' offset ([-\d.]+) ([-\d.]+)', t)
        oy = float(offs[0][1]) if offs else 0.0
        lo, hi = -oy, -oy + VH
        used = [r for r in pbs if r[1] + r[3] > lo and r[1] < hi]
        maxx = max((r[0] + r[2] for r in used), default=0)
        assert maxx <= edits[mid], \
            '%s: el contenido llega a %g pero el viewport quedaria en %g' % (name, maxx, edits[mid])
        print('  %-9s contenido hasta %-6g <= viewport %-6g  ok' % (name, maxx, edits[mid]))

    for mid, w in edits.items():
        t = CLAUSE.sub('', bx[mid]['text'])          # idempotente: saca la clausula previa si la hay
        bx[mid]['text'] = t + ', script sendbox %s presentation_rect %g %g %g %g' % (PAGES_VAR, VX, VY, w, VH)

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
        return 0

    shutil.copyfile(DEVICE, DEVICE + '.before-viewport')
    amxd.save(DEVICE, data, s, e, doc)

    _, _, _, doc2 = amxd.load(DEVICE)
    bx2 = {b['box']['id']: b['box'] for b in doc2['patcher']['boxes']}
    for name, mid in TABS:
        want = 'script sendbox %s presentation_rect %g %g %g %g' % (PAGES_VAR, VX, VY, edits[mid], VH)
        assert want in bx2[mid]['text'], name

    print('\nescrito %s (.before-viewport guardado). Sigue:' % DEVICE)
    print('  python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('  recarga el device ENTERO en Live (sacarlo de la pista y volver a ponerlo)')
    print('  probá Root/Sub en Armonia, Preset Silencio en Artic, Fav/Reparto en Sesion')
    return 0


sys.exit(main())
