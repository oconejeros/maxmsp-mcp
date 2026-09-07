# Conejeros Devices — Go-to-Market

Estrategia de venta del catálogo Max for Live bajo la marca **Conejeros Devices**, con
tienda en **Payhip**, versiones **Lite/gratis** como imán de correos y **Premium** de
pago. Documento vivo — se actualiza al cerrar cada ola. **Re-evaluado 2026-09-05** tras
sumarse 3 devices nuevos (Harmonograph, Prism, Chordscape) al catálogo.

Relacionados: [payhip-setup.md](payhip-setup.md) · [launch-calendar.md](launch-calendar.md) ·
[store-copy/](store-copy/)

---

## 1. Catálogo real (9 devices vendibles)

| Dispositivo | Rol | Estado |
|---|---|---|
| **FORTESEQ** (+ Hub, español) | Flagship #1. Secuenciador generativo por clases de conjunto (351 clases Tn): hasta 16 voces, ritmo Euclidiano por voz, disonancia McKay, máscara/acento, modo Drum Rack, 20 presets + favoritos, bancos Push, 6 pestañas de UI | Salida local (standalone sin Hub) agregada; UI reorganizada a 6 pestañas; falta probar en Live |
| **EVENFLOW** (ex-forteseqwf) | Flagship #2. Ritmos Well-Formed / Moment-of-Symmetry: 20 slots de preset, morph entre slots, catálogo de marcadores r | Iterado; falta verificación formal en Live |
| **Harmonograph** *(nuevo)* | Flagship #3. Ritmos Perfectly-Balanced (8 capas-péndulo) dibujados como curva de Lissajous, con cometa y anillo de arrastre; probabilidad + moduladores cuantizados de rotación/peso; 20 presets con nombre | **Núcleo confirmado en Live** (PB, sync, ventana, presets con outlet dedicado); cometa/Decay/menú Axis/anillo de arrastre sin re-verificar tras el último cambio estructural |
| **Color Theory** (ex-tonnetz) | Visualizador maduro (v13): Tonnetz generalizado, círculos, conducción de voces, piano, guitarra, Tonnetz diatónico, Tonnetz 3-D de Gollin, modo estudio sobre las 351 clases | Sin verificar en Live |
| **Chordscape** (ex-multichord) *(nuevo)* | Explorador navegable del espacio de acordes: modos Nearest (los 4095 acordes concretos por distancia de conducción de voces) / Steps (movimientos elementales dentro de una escala fija), vistas Rings/Spiral, transposición escalar | **Núcleo confirmado en Live** (navegación anillo + MIDI + registro); vista Spiral y los botones ◂/▸ del último build sin recargar en Live |
| **ANIMIDI** (+ ANIMIDIFeed) | Visualizador: score de barras que se desplaza estilo Music Animation Machine, lee transporte/tempo de Live, bus por pista | Vista Barras OK; Espiral y Dodecaedro son stubs |
| **Prism** (ex-invertedprism) *(nuevo)* | Puntos de color arrastrables → mezcla → acorde; polychord por hasta 4 grupos; reharmonizador nota→color en vivo | **Confirmado en Live** — el usuario dio el visto bueno completo 2026-09-04 (makenote, blend, polychords, panel reharmonizador) |
| **midibounce** | Utilidad: un botón, crea pista MIDI y graba el clip como MIDI plano (opción 999 BPM) | Clon "sidebrain", sin verificar en Live |
| **Midirouter** | Remapeador de notas 8×8 con MIDI-learn + presets | Fase 2 (pattrstorage + persistencia del mapa) hecha. Entra al bundle / utilidad de pago; falta verificar en Live |
| **FORTESEQ v1** (`pcset351.js`) | Legacy | Fuera del catálogo de venta |

**Lectura del catálogo ampliado**: ya no son "2 motores + 2 visualizadores", son **3 motores
generativos flagship** (FORTESEQ, EVENFLOW, Harmonograph — cada uno con su propio Lite,
Premium y ola de lanzamiento) + **2 pares temáticos de herramientas de exploración
armónica**: {ANIMIDI / Prism} gratis y {Color Theory / Chordscape} exclusivas del bundle.
Esa simetría (un par de "color↔armonía": Color Theory + Prism comparten la rueda de
quintas coloreada; un par de "espacio navegable": Chordscape es el análogo activo de
Color Theory) es una narrativa de marca aprovechable en el marketing ("los tres motores +
los cuatro modos de ver la armonía").

---

## 2. Modelo de tiers

**Lite = un `.amxd` genuinamente recortado**, no una versión bloqueada. El código de las
features Premium no está presente o no se ejecuta (guard `lite`). Sin DRM: un usuario
decidido podría reconstruir funciones en el editor de Max — costo aceptado. La Lite debe ser
**completamente útil por sí sola** y dejar ganas de automatizar / expandir. Harmonograph
sigue la misma receta que FORTESEQ/EVENFLOW: **capar cantidad** (capas/slots) y **quitar lo
que agrega variación/memoria** (presets, randomización, modulación) — no capar lo que hace
que suene o se vea bien.

| Producto | Lite (gratis, pide correo) | Premium |
|---|---|---|
| **FORTESEQ** | máx. 8 pasos de patrón · sin guardar/cargar presets ni favoritos · sin "Random All" · sin bancos Push · 4 voces fijas | pasos largos · presets + favoritos en disco · randomización por probabilidad · lock/freeze · Drum Rack completo · Push · hasta 16 voces |
| **EVENFLOW** | 8 slots de preset · sin Morph A/B · sin Quantize R | 20 slots · morph A/B · catálogo de marcadores r · quantize |
| **Harmonograph** | motor PB completo (curva, cometa, anillo de arrastre) · **4 capas** · sin probabilidad ni moduladores · sin presets | 8 capas · probabilidad por capa + global · 2 moduladores cuantizados (Rotación, Peso) · 20 presets con nombre |
| **ANIMIDI** | gratis y completo en maxforlive.com (vista Barras; Espiral/Dodecaedro ocultas) | Pro dentro del bundle: paleta rotable, vistas extra, agrupación por carriles |
| **Prism** | gratis y completo en maxforlive.com (los 3 modelos de mezcla, polychord, reharmonizador) | — (no hay features adicionales identificadas todavía; ver §7) |
| **Color Theory** | no se distribuye suelto | exclusivo del bundle: modo estudio (351), Tonnetz 3-D, paleta rotable |
| **Chordscape** | no se distribuye suelto | exclusivo del bundle |
| **midibounce** | gratis en maxforlive.com | — |

**Por qué Harmonograph SÍ tiene Lite y Prism NO**: Harmonograph tiene profundidad real que
sostiene un tier pago (8 capas + presets + moduladores es mucho más que 4 capas simples);
Prism es más chico (un canvas + 4 parámetros) — parecido en alcance a ANIMIDI, que también
se regala entero. Forzarle un Lite/Premium a Prism sería inventar una restricción artificial.

---

## 3. Precios

| Ítem | Precio |
|---|---|
| Cualquier Lite / device gratis | **$0** (Lite pide correo; ANIMIDI y Prism en maxforlive.com no piden nada) |
| FORTESEQ individual — PWYW básico (sin updates) | mín. **$5** |
| FORTESEQ individual — con lifetime updates | **$15–$19** |
| EVENFLOW individual — PWYW básico | mín. **$5** |
| EVENFLOW individual — con lifetime updates | **$12–$15** |
| Harmonograph individual — PWYW básico | mín. **$5** |
| Harmonograph individual — con lifetime updates | **$15–$19** |
| **Conejeros MIDI Creative Pack** (3 motores + Color Theory + Chordscape + ANIMIDI Pro + midibounce + Midirouter, lifetime updates) | **$39** (subido de $29 — ver razón abajo) |

**Por qué subir el bundle de $29 a $39**: cuando se fijó $29 el pack tenía 2 motores +
2 herramientas. Con 3 motores flagship + 2 exclusivos de bundle + Midirouter, comprar todo
suelto con updates ya suma **~$47–$53** — a $39 el pack sigue siendo un alivio de bolsillo
claro (ahorra ~$10–15) sin regalar tanto que devalúe el trabajo de Harmonograph/Chordscape,
y no ancla el precio de la marca demasiado bajo para cuando se sumen más devices.

---

## 4. Forma del funnel

**No se construye un sitio propio como funnel del día 1.** Se arranca lean y se suma la
landing recién en la ola del bundle.

| Capa | Olas 1–3 (motores) | Ola 4 (bundle) |
|---|---|---|
| Tienda / checkout | Storefront Payhip (`payhip.com/conejerosdevices`) | + botones Payhip embebidos en la landing |
| Tope de funnel | **2 devices gratis y sin límites en maxforlive.com** (ANIMIDI + Prism) + demos en Instagram / TikTok / YouTube Shorts | + landing propia (`landing/`) con SEO y videos |
| Captura de correo | producto Lite a $0 en Payhip con **correo obligatorio** (feature nativa) | + formulario en la landing (Payhip o MailerLite free) |
| Cross-sell | cupones de Payhip por email a compradores previos | igual |
| Prueba de compra | license keys de Payhip por comprador (agradecimiento / soporte; **no** se validan dentro del device) | igual |

**Dos imanes gratis en vez de uno**: ANIMIDI (ritmo/visual, apela a productores) y Prism
(color/armonía, gancho fuerte para redes — "convertí color en acordes" es un ángulo de
contenido distinto al de ANIMIDI). Dos ángulos de contenido = más alcance sin costo
adicional; ninguno de los dos resigna una feature "premium" real (ver §2).

**Por qué Payhip primero:** ya trae storefront, checkout, gate de correo en descargas
gratis, cupones, license keys y analítica; su comisión en el plan gratis es **5%** (vs. 10%
de Gumroad). Una landing propia agrega control de marca y SEO pero es otra cosa que
mantener; rinde recién cuando hay un bundle grande y varios videos que enlazar.

**maxforlive.com** es el canal de descubrimiento más importante para M4L: los 2 devices
gratis viven ahí, sin restricciones, cada uno enlazando a la tienda Payhip.

> Nota técnica: la landing va en `landing/` (no `site/`, que está en `.gitignore`).

---

## 5. Lanzamiento evolutivo — individual → pack (4 olas, no 3)

No se lanza todo junto en un pack gigante. Se construye expectativa y se recolecta correo
paso a paso — y ahora hay un motor más antes del bundle.

1. **Ola 1 — FORTESEQ** individual (Lite + Premium, español) **+ ambos imanes gratis**
   (ANIMIDI y Prism) **+ midibounce** gratis, todos en maxforlive.com. Arma la lista de
   correos con el impacto más grande posible del día 1 (3 productos gratis a la vez).
2. **Ola 2 — EVENFLOW** individual (Lite + Premium), ~1 mes después. Cupón a compradores
   de la Ola 1.
3. **Ola 3 — Harmonograph** individual (Lite + Premium), ~1 mes después. El video de
   demo de este device (la curva + cometa) es probablemente el mejor activo de marketing
   de todo el catálogo — vale la pena invertir tiempo extra en ese contenido. Cupón a
   compradores de las Olas 1–2.
4. **Ola 4 — Conejeros MIDI Creative Pack** ($39, lifetime): los 3 motores Premium +
   Color Theory + Chordscape + ANIMIDI Pro + midibounce + Midirouter. Se publica la
   landing. Cupón `COMPLETA-EL-PACK` a todos los compradores previos.

Detalle de fechas y precondiciones en [launch-calendar.md](launch-calendar.md).

---

## 6. Métricas a mirar

| Métrica | Dónde | Meta inicial |
|---|---|---|
| Altas de correo vía Lite | Payhip → contactos | — (línea base en Ola 1) |
| Descargas de ANIMIDI vs. Prism (¿cuál trae más tráfico?) | maxforlive.com | — (decide dónde poner más esfuerzo de contenido después) |
| Conversión Lite → Premium | descargas Lite vs. ventas Premium del mismo device | 3–8 % |
| Ingreso por ola | Payhip → analítica | — |
| Tráfico maxforlive.com → Payhip | UTM en el enlace de la descripción | — |
| Uso del cupón de cross-sell (Olas 2–3) | Payhip → cupones | > 15 % de los compradores de la ola anterior |
| Adjunto medio (PWYW) | Payhip → ventas | > $8 |

---

## 7. Riesgos y decisiones abiertas

- **Tooling de Lite para Harmonograph no existe todavía** — `tools/make_lite.py` solo cubre
  FORTESEQ2/forteseqwf. Falta un script equivalente para Harmonograph (capar a 4 capas,
  ocultar/desactivar Prob + los 2 lanes de modulación + Slot/Save/Load/Clear/picker,
  inyectar el guard `lite` en `harmonograph.js`). Bloquea la Ola 3.
- **Prism sin features Premium identificadas** — si más adelante se agregan (ej. export de
  MIDI, modelos de mezcla extra, más de 4 grupos), recién ahí evaluar un Prism Pro dentro
  del bundle; hoy no hay nada que gatear.
- **FORTESEQ standalone** — RESUELTO: toggle "Salida local" (ON por defecto). El Hub se
  incluye igual para ruteo multipista. Falta probar en Live.
- **UI de FORTESEQ reorganizada** (10→6 pestañas) — falta la pasada visual del usuario en
  Live antes de dar la Ola 1 por lista.
- **Midirouter** — Fase 2 hecha; entra al bundle (Ola 4) y/o como utilidad de pago suelta;
  falta verificar en Live y traducir la ayuda.
- **Harmonograph / Chordscape — pasos sin re-verificar en Live** tras los últimos cambios
  estructurales (ver tabla del catálogo); cada uno necesita un "delete y re-arrastrar
  fresco" del device en Live antes de darlo por listo para vender.
- **Versión mínima de Live/Max** — confirmar (los devices se hicieron en Max 9 / Live 12) y
  ponerlo en cada README y ficha de Payhip.
- **Licencia de uso** — definir (personal + comercial, sin reventa ni redistribución) y
  ponerla en cada `LICENSE.txt` del release.
- **Reembolsos / impuestos** — definir política en [payhip-setup.md](payhip-setup.md).
- **PDFs académicos** (`forteseq/`, Bigo/McKay/Tymoczko) — nunca se empaquetan (el
  whitelist de `tools/package_release.py` los excluye por extensión); se citan como
  respaldo teórico, no se redistribuyen.
