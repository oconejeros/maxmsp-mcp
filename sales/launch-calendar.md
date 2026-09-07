# Calendario de lanzamiento

Cuatro olas, ~1 mes entre cada una (era 3 antes de sumar Harmonograph al catálogo). Las
fechas son relativas a **D = día de la Ola 1** (fijar cuando FORTESEQ pase todas las
precondiciones). Modelo en [go-to-market.md](go-to-market.md), tienda en
[payhip-setup.md](payhip-setup.md).

---

## Ola 1 — FORTESEQ + los 2 imanes gratis (D)

**Contenido:** `FORTESEQ Lite` (gratis, correo) + `FORTESEQ` (Premium) en Payhip ·
`ANIMIDI` y `Prism` gratis y sin límites en maxforlive.com · `midibounce` gratis en
maxforlive.com.

**Precondiciones (todas deben cumplirse):**

- [ ] En Ableton Live: probar la **salida local** (toggle "Salida local"): FORTESEQ solo
      en una pista MIDI, sin Hub, Run ON → suena; toggle OFF → silencio; con Hub + toggle
      OFF → no duplica. El Hub viaja igual en el `.zip` para ruteo multipista.
- [ ] **Pasada visual de la UI reorganizada** (10→6 pestañas: Armonía/Filtro/Artic/Tiempo/
      Modul/Sesión) — sin solapes ni controles cortados; Indep/Filtro/Lock funcionan desde
      el panel principal; los menús M1–M4 Dest muestran Human y Caída.
- [ ] `python tools/make_lite.py forteseq/FORTESEQ2.amxd --apply` produce una Lite que
      **carga en Live** y **carece** de: guardar/cargar presets, favoritos, "Random All",
      bancos Push, patrones > 8 pasos, cambio de nº de voces.
- [ ] La Premium conserva **todo** (comparar con `device_backup/FORTESEQ_v2.validated.amxd`
      y correr `forteseq/test/harness.js` contra `golden.txt`).
- [ ] `python tools/check_structure.py` + `python tools/check_params3.py` limpios.
- [ ] `python tools/package_release.py FORTESEQ` → `.zip` probado en carpeta de usuario
      Max/Live limpia; no contiene PDFs / `*.before*` / `device_backup/` / `test/`.
- [ ] `python tools/package_release.py Prism` → probado igual; **Prism ya está
      Live-verificado** (usuario dio el visto bueno 2026-09-04), solo falta el empaquetado.
- [ ] Payhip: productos creados, correo obligatorio en la Lite, license keys en la Premium,
      compra de prueba en test mode OK.
- [ ] Video de demo (30–60 s) + 4 capturas para FORTESEQ; 1 video corto para Prism
      (el gesto de arrastrar color → acorde es muy visual, vale un clip propio) y otro
      para ANIMIDI.
- [ ] `sales/store-copy/forteseq.md` pegado en Payhip; `prism.md` y `animidi.md` pegados
      en sus fichas de maxforlive.com.

**Emails:** T-3 aviso · T-0 lanzamiento (cupón `LANZAMIENTO` 20 %, 72 h) · T+5 cierre.

---

## Ola 2 — EVENFLOW (D + ~30 días)

**Contenido:** `EVENFLOW Lite` + `EVENFLOW` (Premium) en Payhip.

**Precondiciones:**

- [ ] EVENFLOW Lite/Premium verificadas en Live; morph A/B y los 20 slots OK en la
      Premium; la Lite queda en 8 slots y sin morph.
- [ ] `make_lite.py` + `check_structure.py` + `package_release.py` OK para EVENFLOW.
- [ ] `.zip` probado en carpeta limpia.
- [ ] Payhip: productos + license keys + prueba en test mode.
- [ ] Cupón `WF-PARA-TI` (30 %) creado.
- [ ] `sales/store-copy/evenflow.md` pegado.
- [ ] Video + capturas.

**Emails:** a compradores de la Ola 1 → cupón `WF-PARA-TI`. Broadcast general T-3 / T-0 / T+5.

---

## Ola 3 — Harmonograph (D + ~60 días) — NUEVA

**Contenido:** `Harmonograph Lite` + `Harmonograph` (Premium) en Payhip.

**Precondiciones:**

- [ ] **Construir el tooling de Lite para Harmonograph** (no existe todavía — es distinto
      de `make_lite.py`, que solo cubre FORTESEQ2/forteseqwf): capar a **4 capas**, ocultar
      Prob global + Prob/RotDepth/WeightDepth por capa + los 2 lanes de modulación
      (RotStep/WeightStep) + Slot/Save/Load/Clear/picker de presets; inyectar un guard
      `lite` en `harmonograph.js` (mismo patrón que FORTESEQ2/EVENFLOW: no ejecutar lo que
      la UI no expone).
- [ ] **Delete + re-arrastrar fresco** el device en Live (regla de la memoria del proyecto
      para cualquier cambio estructural) y confirmar: PB suena, sync con el transporte,
      ventana flotante, cometa, Decay, menú Axis, anillo de arrastre, y presets (guardar/
      cargar/borrar/nombrar) — todo esto está construido pero varios pasos no se
      re-verificaron después del último cambio de outlets.
- [ ] `check_structure.py` + `check_params3.py` (adaptado a `harmonograph.amxd` si hace
      falta) limpios en Lite y Premium.
- [ ] `python tools/package_release.py Harmonograph` → `.zip` probado en carpeta limpia.
- [ ] Payhip: productos + license keys + prueba en test mode.
- [ ] Cupón de cross-sell a compradores de Olas 1–2 (crear, ej. `HG-PARA-TI`, 30 %).
- [ ] `sales/store-copy/harmonograph.md` pegado.
- [ ] **Video de demo de la curva + cometa** — es el mejor gancho visual del catálogo,
      justifica más tiempo de producción que los videos de las olas anteriores.

**Emails:** a compradores de las Olas 1–2 → cupón de cross-sell. Broadcast general T-3/T-0/T+5.

---

## Ola 4 — Conejeros MIDI Creative Pack (D + ~90 días)

**Contenido:** bundle **$39** lifetime updates (FORTESEQ + EVENFLOW + Harmonograph Premium
+ Color Theory + Chordscape + ANIMIDI Pro + midibounce + Midirouter) · **publicar la
landing** (`landing/`).

**Precondiciones:**

- [ ] **Color Theory verificado en Live** (hoy marcado *unverified*): los 8 paneles dibujan,
      el modo estudio recorre las 351 clases, no quedan regiones obsoletas.
- [ ] **Chordscape verificado en Live**: núcleo (Rings + navegación + MIDI) ya confirmado;
      falta la vista Spiral con los shift-ghosts y los botones ◂/▸ de transposición escalar
      (el build que los agrega no se recargó en Live todavía).
- [ ] **ANIMIDI Pro**: vista Barras + paleta rotable sólidas; Espiral y Dodecaedro pueden
      seguir ocultas si aún son stubs.
- [ ] FORTESEQ, EVENFLOW y Harmonograph sin bugs abiertos de las Olas 1–3.
- [ ] **Midirouter** verificado en Live (presets + persistencia del mapa) y ayuda en inglés.
- [ ] `python tools/package_release.py` regenera **todos** los `.zip`, incluido
      `Conejeros MIDI Creative Pack.zip` (ya probado en dry-run con los 3 devices nuevos).
- [ ] Landing (`landing/index.html`) actualizada con Harmonograph/Prism/Chordscape y el
      precio $39, revisada en local y en un deploy de preview de GitHub Pages; botones de
      compra Payhip funcionando; formulario de correo conectado.
- [ ] Payhip: producto del bundle a $39 + cupón `COMPLETA-EL-PACK` (descuento ≈ lo ya
      pagado por devices sueltos).
- [ ] `sales/store-copy/bundle.md`, `chordscape.md` pegados.

**Emails:** a **todos** los compradores previos → cupón `COMPLETA-EL-PACK`. Broadcast
general + push en redes con la landing como destino.
