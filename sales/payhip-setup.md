# Payhip — guía de configuración

Pasos concretos para montar la tienda **Conejeros Devices** en Payhip. Ver el modelo en
[go-to-market.md](go-to-market.md) y el calendario en [launch-calendar.md](launch-calendar.md).

---

## 0. Cuenta y marca

1. Crear cuenta en payhip.com. Plan **Free** para empezar (comisión 5 % por venta; sin
   costo fijo). Evaluar el plan **Plus** ($29/mes, comisión 2 %) recién cuando el ingreso
   mensual supere ~$600.
2. **Store URL**: `payhip.com/conejerosdevices`.
3. Branding: logo, color de acento, banner. Bio corta: "Dispositivos Max for Live para
   composición generativa y visualización MIDI en Ableton Live."
4. **Payout**: conectar PayPal y/o Stripe. Verificar el país fiscal.
5. **Impuestos**: activar *Settings → Taxes → EU VAT / worldwide tax* para que Payhip actúe
   como recaudador donde corresponde. Guardar los reportes trimestrales.
6. **Legales**: pegar en *Settings → Legal* los términos y la política de reembolso
   (abajo).

---

## 1. Productos a crear

Un "producto" de Payhip por cada SKU. Tipo: **Digital product** (archivo descargable).

| Producto Payhip | Archivo | Precio | Correo obligatorio | License keys |
|---|---|---|---|---|
| `FORTESEQ Lite` | `release/zips/FORTESEQ Lite.zip` | $0 | **Sí** | No |
| `FORTESEQ` | `release/zips/FORTESEQ.zip` | PWYW, mínimo $5, sugerido $15 | — | Sí |
| `EVENFLOW Lite` | `release/zips/EVENFLOW Lite.zip` | $0 | **Sí** | No |
| `EVENFLOW` | `release/zips/EVENFLOW.zip` | PWYW, mínimo $5, sugerido $12 | — | Sí |
| `Harmonograph Lite` | `release/zips/Harmonograph Lite.zip` | $0 | **Sí** | No |
| `Harmonograph` | `release/zips/Harmonograph.zip` | PWYW, mínimo $5, sugerido $15 | — | Sí |
| `Conejeros MIDI Creative Pack` | `release/zips/Conejeros MIDI Creative Pack.zip` | **$39** fijo | — | Sí |

`midibounce`, `ANIMIDI` y `Prism` (gratis) se publican en **maxforlive.com**, no como
producto Payhip — cada ficha en maxforlive.com enlaza a la tienda.

### Configuración por producto

- **PWYW**: *Pricing → "Let customers pay what they want"*, con *minimum price* $5 y
  *suggested price* al valor "con lifetime updates". En la descripción, dejar claro:
  *"$5–$11 = versión actual sin actualizaciones. $12+ = actualizaciones de por vida."*
  (Payhip no separa tiers dentro de un PWYW; se comunica por texto y se honra al enviar
  updates solo a quienes pagaron el umbral — se filtra por monto en la lista de ventas.)
- **Alternativa más limpia a PWYW**: dos productos fijos, `FORTESEQ (versión actual)` a $7
  y `FORTESEQ (lifetime updates)` a $17. Menos ambigüedad, más clics. **Recomendado.**
- **Correo obligatorio** (solo Lite): *Settings del producto → "Require email before
  download"* (o precio $0 con *collect email*). Ese correo entra a *Payhip → Customers* y es
  la lista para los emails de lanzamiento.
- **License keys** (solo pagos): *Product → Software licensing → Generate license keys*. No
  se validan dentro del `.amxd` (M4L no tiene DRM real); sirven como comprobante y para
  soporte. Incluir la key en el email de entrega.
- **Archivo**: subir el `.zip` generado por `python tools/package_release.py`. Al publicar
  una versión nueva, reemplazar el archivo y usar *"Notify existing customers"*.
- **Límite de descargas**: 5 por comprador; sin expiración.

---

## 2. Página de producto

Estructura (usar el copy de [store-copy/](store-copy/)):

1. **Título**: `FORTESEQ — Secuenciador generativo para Ableton Live`.
2. **Galería**: 1 video de 30–60 s (loop de demo) + 3–4 capturas.
3. **Descripción**: gancho en 2 líneas → qué hace → lista de features → qué trae la Lite y
   qué agrega la Premium → requisitos (Live 12+, Max for Live) → enlace a la Lite gratis.
4. **FAQ**: ¿necesito saber teoría? · ¿funciona sin Push? · ¿la Lite caduca? (no) ·
   ¿actualizaciones? · ¿reembolsos?
5. **Cross-link**: "¿Ritmos? Mira EVENFLOW y Harmonograph" / "Llévate todo con el Pack y
   ahorra". FORTESEQ y EVENFLOW también linkean a Prism/ANIMIDI ("gratis, mirá el resto").

---

## 3. Cupones (cross-sell)

*Marketing → Coupons*.

| Cupón | Aplica a | Descuento | Cuándo |
|---|---|---|---|
| `WF-PARA-TI` | `EVENFLOW` | 30 % | Email a compradores de FORTESEQ al lanzar la Ola 2 |
| `HG-PARA-TI` | `Harmonograph` | 30 % | Email a compradores de Olas 1–2 al lanzar la Ola 3 |
| `COMPLETA-EL-PACK` | `Conejeros MIDI Creative Pack` | monto = lo ya pagado por devices sueltos (aprox., 40 %) | Email a todos los compradores previos al lanzar la Ola 4 |
| `LANZAMIENTO` | device de la ola | 20 % | Primeras 72 h de cada ola, en redes |

---

## 4. Emails por lanzamiento (Payhip → Email o export a MailerLite)

Payhip *Email* sirve para broadcasts simples. Si se necesita automatización real (secuencia
de bienvenida, segmentación), exportar contactos a **MailerLite** (free hasta 1.000
suscriptores) y capturar ahí.

**Secuencia por ola (3 correos):**

1. **T-3 días — aviso**: "Se viene *EVENFLOW*. Esto es lo que hace." + GIF. Sin enlace de
   compra todavía.
2. **T-0 — lanzamiento**: enlace de compra + cupón `LANZAMIENTO` (20 %, 72 h) + a los
   compradores previos, su cupón de cross-sell.
3. **T+5 días — cierre**: caso de uso / demo larga + recordatorio de que el cupón vence +
   testimonios si ya hay.

**Bienvenida (al bajar cualquier Lite):** 1 correo inmediato — "Gracias, aquí va un
mini-tutorial de 2 minutos" + link a la versión Premium con `LANZAMIENTO` si la ola está
activa.

---

## 5. Política de reembolso (pegar en Legal y en cada FAQ)

> Los productos son archivos digitales descargables. Por su naturaleza no se ofrecen
> reembolsos una vez descargado el archivo, salvo que el dispositivo no cargue o no
> funcione según lo descrito y no logremos resolverlo por soporte en 7 días. Antes de
> comprar, probá la **versión Lite gratuita** para confirmar compatibilidad con tu sistema.
> Contacto de soporte: <correo>.

---

## 6. Checklist antes de publicar cada producto

- [ ] `python tools/package_release.py` regenerado; `.zip` sin PDFs, sin `*.before*`, sin
      `device_backup/`, sin `test/` (lo verifica el propio script).
- [ ] `.zip` probado en una carpeta de usuario Max/Live **limpia** (sin el repo en el path):
      el device resuelve su `.js` por nombre y arranca.
- [ ] Lite y Premium cargadas lado a lado en Live: la Lite **no** muestra los controles
      gateados y sus mensajes son no-op; la Premium funciona igual que antes.
- [ ] Video de demo subido; 3+ capturas.
- [ ] Copy desde `sales/store-copy/<device>.md`, con requisitos y enlace a la Lite.
- [ ] Precio, correo obligatorio (Lite) y license keys (pagos) configurados.
- [ ] Compra de prueba en **test mode**: llega el email de entrega, con la key, y el archivo
      abre.
- [ ] Cupones de la ola creados.
- [ ] Ficha en maxforlive.com (para el device gratis) con enlace UTM a Payhip.
