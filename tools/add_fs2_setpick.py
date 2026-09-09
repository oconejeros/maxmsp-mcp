"""Panel IZQUIERDO del popup "Proximos 16" de FORTESEQ2: piano de mascara cromatica + rejilla de
sets por color.

    python tools/add_fs2_setpick.py            dry run, no escribe nada
    python tools/add_fs2_setpick.py --apply    escribe forteseq/FORTESEQ2.amxd (+ .before)

Por que: el popup solo mostraba el horizonte de pasos (fs2horizon.js). Este panel anade a su
IZQUIERDA un jsui interactivo (fs2setpick.js) con dos zonas:
  - piano de 12 teclas tenidas por el color de circulo de quintas -> click arma/desarma la celda
    de la mascara del Filtro (setmask + setfilter 1);
  - rejilla de swatches, uno por set que pasa el filtro, coloreado con harmonyToColor() ->
    click fija ese set (setlockindex + setlock 1).

El motor ya tiene toda la API de entrada; en forteseq2.js solo se anadio un emisor por outlet 3
(filtclear / filtinfo / filtset / maskecho) que la ventana consume via querynext() (el metro que
ya la mantiene viva con el transporte parado) y via un disparo de `queryfiltsets` desde el boton
al abrir. fs2horizon.js y fs2colmon.js no-opean esos cuatro selectores.

Que toca, modelado en tools/add_fs2_horizon.py:

  subpatcher [p fs2_window] (obj-751):
    - la caja pasa a numoutlets 1 + outlettype ['']  (hoy no tiene outlet)
    - rect / openrect ensanchan L+GAP  (868 -> 1256)
    - el jsui fs2horizon.js se corre a x = 8 + L + GAP  (8 -> 396)
    - nuevo jsui fs2setpick.js en x=8, w=L  (parameter_enable 0 -- no es parametro Live)
    - nueva caja outlet; lineas  inlet -> fs2setpick  y  fs2setpick -> outlet
    - fs2setpick.js entra al dependency_cache del subpatcher

  patcher superior:
    - nueva message "queryfiltsets" (oculta): del boton obj-745 al motor obj-23
    - nueva linea  obj-751:0 -> obj-23:0   (los mensajes del panel llegan al motor)

La ventana es redimensionable: fs2setpick.js y fs2horizon.js siguen a SELF.patcher.wind.size
(patron tonnetz/animidi) y calzan su box.rect -- el panel izquierdo con ancho fijo (380), el
horizonte ocupa el resto. Los rects estaticos que escribe esta herramienta son solo el fallback
para cuando el tamano de la ventana no se puede leer.

Sin parametros Live nuevos (no se toca P['parameters'] ni parameterbanks).

Idempotente: no hace nada si ya hay un jsui fs2setpick.js dentro del subpatcher -- esto tambien
evita re-ensanchar la ventana. Por lo mismo NO sirve para cambiar L despues: para ajustar el
ancho hay que editar a mano en FORTESEQ2.amxd  rect[2], openrect[2], el ancho del jsui
fs2setpick y la x del jsui fs2horizon.

Cerrar FORTESEQ2 en Max Y Live antes de --apply.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amxd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEVICE = os.path.join(ROOT, 'forteseq', 'FORTESEQ2.amxd')
BOOT = 'C:/Users/conej/PycharmProjects/maxmsp-mcp/forteseq'

ENGINE = 'obj-23'                 # js forteseq2.js
BTN = 'obj-745'                   # live.text "Proximos 16" (ya existente)
WIN_VAR = 'fs2_horizon_win'       # la caja [p fs2_window] = obj-751
JS = 'fs2setpick.js'
HORIZON_JS = 'fs2horizon.js'

L = 380.0                         # ancho del panel izquierdo (FIJO)
GAP = 8.0
# Las cajas jsui se dejan SOBREDIMENSIONADAS: el popup se puede agrandar y jsui solo pinta dentro
# de la caja, asi que la caja tiene que cubrir cualquier tamano de ventana razonable. Cada .js
# pinta dentro de viewportWH() (tamano real de la ventana), no del box.rect. Patron tonnetz.js.
BIG_W = 2600.0                    # ancho generoso para fs2horizon (cubre monitores grandes)
BIG_H = 1500.0                    # alto generoso para ambos


def mkbox(P, **kw):
    P['boxes'].append({'box': kw})


def mkline(P, src, so, dst, di):
    P['lines'].append({'patchline': {'source': [src, so], 'destination': [dst, di]}})


def check(pp, where='root'):
    """Misma clase de trampa que enforce check_structure.py."""
    by = {}
    for b in pp.get('boxes', []):
        bx = b['box']
        assert bx['id'] not in by, '%s: id duplicado %s' % (where, bx['id'])
        by[bx['id']] = bx
    for ln in pp.get('lines', []):
        pl = ln['patchline']
        for tag, end in (('src', pl['source']), ('dst', pl['destination'])):
            bx = by.get(end[0])
            assert bx, '%s: %s -> caja desconocida %s' % (where, tag, end)
            cnt = bx.get('numoutlets', 0) if tag == 'src' else bx.get('numinlets', 0)
            assert 0 <= end[1] < cnt, '%s: %s %s idx %d fuera de 0..%d (%s)' % (
                where, tag, end[0], end[1], cnt - 1, bx.get('text', bx.get('maxclass')))
    for b in pp.get('boxes', []):
        if b['box'].get('patcher'):
            check(b['box']['patcher'], where + '::' + b['box']['id'])


def build(apply_it):
    data, s, e, doc = amxd.load(DEVICE)
    P = doc['patcher']

    by_var = {b['box'].get('varname'): b['box'] for b in P['boxes']}
    win = by_var.get(WIN_VAR)
    assert win and win.get('patcher'), 'no encuentro el subpatcher %s' % WIN_VAR
    sub = win['patcher']

    if any(b['box'].get('filename') == JS for b in sub['boxes']):
        print('ya parcheado (jsui %s presente en %s) -- nada que hacer' % (JS, WIN_VAR))
        return

    ids = {b['box']['id'] for b in P['boxes']}
    for need in (ENGINE, BTN):
        assert need in ids, 'falta la caja %s' % need
    WIN_ID = win['id']

    # --- 1. la caja del subpatcher: gana un outlet -------------------------------------------
    win['numoutlets'] = 1
    win['outlettype'] = ['']

    # --- 2. geometria del subpatcher ------------------------------------------------------
    sub['rect'][2] += L + GAP
    sub['openrect'][2] += L + GAP

    hz = next((b['box'] for b in sub['boxes'] if b['box'].get('filename') == HORIZON_JS), None)
    assert hz, 'no encuentro el jsui %s dentro del subpatcher' % HORIZON_JS
    hz['patching_rect'] = [8.0 + L + GAP, 8.0, BIG_W, BIG_H]        # sobredimensionada: cubre la ventana agrandada
    hz['presentation_rect'] = [8.0 + L + GAP, 8.0, BIG_W, BIG_H]

    # --- 3. cajas nuevas dentro del subpatcher ------------------------------------------
    sub_ids = {b['box']['id'] for b in sub['boxes']}
    sn = max(int(i[4:]) for i in sub_ids if i[4:].isdigit())
    NEWJS, NEWOUT = 'obj-%d' % (sn + 1), 'obj-%d' % (sn + 2)

    sub['boxes'].append({'box': dict(
        id=NEWJS, maxclass='jsui', numinlets=1, numoutlets=1, outlettype=[''],
        parameter_enable=0, filename=JS, varname='fs2sp_ui',
        patching_rect=[8.0, 8.0, L, BIG_H], presentation=1,   # ancho fijo L, alto sobredimensionado
        presentation_rect=[8.0, 8.0, L, BIG_H])})
    sub['boxes'].append({'box': dict(
        id=NEWOUT, maxclass='outlet', numinlets=1, numoutlets=0,
        patching_rect=[8.0, BIG_H + 16.0, 24.0, 24.0],
        varname='fs2sp_out', comment='', hidden=1)})

    sub['lines'].append({'patchline': {'source': ['obj-1', 0], 'destination': [NEWJS, 0]}})
    sub['lines'].append({'patchline': {'source': [NEWJS, 0], 'destination': [NEWOUT, 0]}})

    dep = sub.setdefault('dependency_cache', [])
    if not any(d.get('name') == JS for d in dep):
        dep.append({'name': JS, 'bootpath': BOOT, 'type': 'TEXT', 'implicit': 1})

    # --- 4. patcher superior: message queryfiltsets + linea del panel al motor ----------
    tn = max(int(i[4:]) for i in ids if i[4:].isdigit())
    MQF = 'obj-%d' % (tn + 1)
    mkbox(P, id=MQF, maxclass='message', numinlets=2, numoutlets=1, outlettype=[''],
          patching_rect=[240.0, 5490.0, 90.0, 22.0], text='queryfiltsets',
          varname='fs2_filt_qry', hidden=1)

    mkline(P, WIN_ID, 0, ENGINE, 0)   # obj-751:0 -> obj-23:0  (setmask / setlockindex / setlock)
    mkline(P, BTN, 0, MQF, 0)         # el boton "Proximos 16" fuerza un refresco al abrir
    mkline(P, MQF, 0, ENGINE, 0)      # queryfiltsets -> motor

    check(P)

    print('add_fs2_setpick  ->  forteseq/FORTESEQ2.amxd')
    print('  subpatcher %s : rect/openrect %g -> %g, %s -> x %g, + jsui %s (x 8, w %g) + outlet %s'
          % (WIN_ID, sub['rect'][2] - L - GAP, sub['rect'][2], HORIZON_JS,
             hz['patching_rect'][0], JS, L, NEWOUT))
    print('  patcher sup   : %s "queryfiltsets" (de %s), linea %s:0 -> %s:0'
          % (MQF, BTN, WIN_ID, ENGINE))

    if not apply_it:
        print('\n(dry run -- no se escribio nada; re-corre con --apply)')
        return

    shutil.copyfile(DEVICE, DEVICE + '.before')
    amxd.save(DEVICE, data, s, e, doc)

    back = amxd.load(DEVICE)[3]['patcher']
    bv = {b['box'].get('varname'): b['box'] for b in back['boxes']}
    w2 = bv[WIN_VAR]
    assert w2.get('numoutlets') == 1, 'numoutlets del subpatcher no quedo en 1'
    s2 = w2['patcher']
    assert abs(s2['rect'][2] - (868.0 + L + GAP)) < 0.5, 'rect no ensancho'
    assert abs(s2['openrect'][2] - (868.0 + L + GAP)) < 0.5, 'openrect no ensancho'
    js2 = [b['box'] for b in s2['boxes'] if b['box'].get('maxclass') == 'jsui']
    assert any(b.get('filename') == JS for b in js2), 'jsui %s perdido' % JS
    hz2 = next(b for b in js2 if b.get('filename') == HORIZON_JS)
    assert abs(hz2['patching_rect'][0] - (8.0 + L + GAP)) < 0.5, '%s no se corrio' % HORIZON_JS
    assert abs(hz2['presentation_rect'][0] - (8.0 + L + GAP)) < 0.5, '%s presr no se corrio' % HORIZON_JS
    assert any(d.get('name') == JS for d in s2.get('dependency_cache', [])), 'dep_cache sin %s' % JS
    tl = [(l['patchline']['source'], l['patchline']['destination']) for l in back['lines']]
    assert [WIN_ID, 0] in [src for src, dst in tl if dst == [ENGINE, 0]], 'falta %s:0 -> %s:0' % (WIN_ID, ENGINE)
    mqf = next((b['box'] for b in back['boxes'] if b['box'].get('text') == 'queryfiltsets'), None)
    assert mqf, 'falta la message queryfiltsets'
    assert [BTN, 0] in [src for src, dst in tl if dst == [mqf['id'], 0]], 'queryfiltsets no viene de %s' % BTN
    assert [mqf['id'], 0] in [src for src, dst in tl if dst == [ENGINE, 0]], 'queryfiltsets no va al motor'

    print('\nescrito %s  (backup %s.before)' % (DEVICE, os.path.basename(DEVICE)))
    print('ahora: python tools/check_structure.py forteseq/FORTESEQ2.amxd')
    print('       python tools/check_params3.py')
    print('       node forteseq/test/harness.js')


if __name__ == '__main__':
    build('--apply' in sys.argv)
