// Midirouter -- motor de remapeo de notas. Editor = grilla drum-rack jsui (midirouter_grid.js).
//
// map[inNota 0..127] = padIndex 0..63, o -1 = sin ruteo (la nota pasa igual).
// Salida ruteada = Base + (pad mod Rango), recortada 0..127. El note-off sale por held[]
// (el destino que abrio el note-on) asi cancela exacto aunque Base/Rango se hayan movido.
//
// Modelo 1:1 -- una nota por pad. Al armar un pad y aprender una nota, el pad suelta su
// nota anterior; si la nota estaba en otro pad, se mueve.
//
// inlet 0:
//   [pitch velocity]   nota del filtro  -> outlet 0: [pitch velocity] a noteout
//   arm <pad>          arma un pad para MIDI-learn (o -1 para desarmar)
//   keyclick <nota>    click en el piano de arriba: si la nota esta asignada -> la desasigna,
//                      si no -> la liga al pad armado (si hay uno)
//   clearpad <pad>     borra la ruta de ese pad
//   clearall           borra todo
//   setbase / setspan  Base / Rango
//   refresh / bang     re-emitir estado a la grilla
// outlet 1 -> grilla jsui:
//   padroutes <128 ints>   mapa completo (nota -> pad, o -1)
//   padbase <n>            nota del pad 0
//   padspan <n>            Rango (la grilla atenua pads >= span)
//   padarmed <pad>         pad armado, o -1
//   padactive <pad> <0|1>  encender / apagar un pad (note on/off)
//   pianoassigned <notas>  lista de notas de entrada asignadas (el piano las pinta verde)
//   noteon <nota> <0|1>    nota de entrada sonando (el piano la pinta ambar)

autowatch = 1;
inlets = 1;
outlets = 2;

var DEBUG = 1;                       // "debug 0" lo apaga
function DBG() {
    if (!DEBUG) return;
    var s = "";
    for (var i = 0; i < arguments.length; i++) s += (i ? " " : "") + arguments[i];
    post("[mr] " + s + "\n");
}

var SIZE = 128;
var PADS = 64;
var map = [];
var held = [];
var padHeld = [];                    // conteo de note-ons por pad (anti-parpadeo)
var base = 36;
var span = 64;
var armedPad = -1;

for (var _i = 0; _i < SIZE; _i++) { map[_i] = -1; held[_i] = -1; }
for (var _p = 0; _p < PADS; _p++) { padHeld[_p] = 0; }

DBG("cargado. base", base, "span", span);

function debug(v) { DEBUG = v | 0; DBG("DEBUG =", DEBUG); }

function clampi(v, lo, hi) {
    v = Math.round(v);
    return v < lo ? lo : (v > hi ? hi : v);
}

function foldOut(p) {
    if (map[p] < 0) return p;
    var s = span < 1 ? 1 : span;
    return clampi(base + (((map[p] % s) + s) % s), 0, 127);
}

// ---- MIDI entrante: lista [pitch velocity] ------------------------------------
function list() {
    var a = arrayfromargs(arguments);
    if (!a.length) return;
    var p = a[0] | 0;
    var v = (a.length > 1 ? a[1] : 0) | 0;
    if (p < 0 || p >= SIZE) { outlet(0, p, v); return; }

    if (v > 0 && armedPad >= 0) bindNote(p);   // MIDI-learn: consume el arm ANTES del fold

    var out;
    if (v > 0) { out = foldOut(p); held[p] = out; }
    else       { out = (held[p] >= 0 ? held[p] : p); held[p] = -1; }
    outlet(0, out, v);
    emitActive(out - base, v > 0 ? 1 : 0);
    outlet(1, "noteon", p, v > 0 ? 1 : 0);     // piano de la grilla: nota entrante sonando
}
function msg_int(p) { list(p | 0, 0); }

// ---- MIDI-learn -----------------------------------------------------------------
function bindNote(pitch) {
    pitch = pitch | 0;
    if (armedPad < 0 || pitch < 0 || pitch >= SIZE) return;
    for (var i = 0; i < SIZE; i++) if (map[i] === armedPad) map[i] = -1;  // 1:1: el pad suelta su nota
    map[pitch] = armedPad;                                                // (si pitch estaba en otro pad, se mueve)
    DBG("bind: nota", pitch, "-> pad", armedPad);
    armedPad = -1;
    pushgrid();
}
function arm(p) {
    p = p | 0;
    var s = span < 1 ? 1 : span;
    armedPad = (p >= 0 && p < PADS && p < s) ? p : -1;
    DBG("arm", armedPad);
    outlet(1, "padarmed", armedPad);
}
// click en una tecla del piano de arriba
function keyclick(p) {
    p = p | 0;
    if (p < 0 || p >= SIZE) return;
    if (map[p] >= 0) {                 // asignada -> desasignar
        map[p] = -1;
        DBG("keyclick: desasigno nota", p);
        pushgrid();
    } else {                          // libre -> ligar al pad armado (si hay)
        bindNote(p);
    }
}

function clearpad(p) {
    p = p | 0;
    var n = 0;
    for (var i = 0; i < SIZE; i++) if (map[i] === p) { map[i] = -1; n++; }
    DBG("clearpad", p, "(" + n + ")");
    pushgrid();
}
function clearall() {
    for (var i = 0; i < SIZE; i++) map[i] = -1;
    armedPad = -1;
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;
    DBG("clearall");
    pushgrid();
}

// ---- parametros ---------------------------------------------------------------
function setbase(v) {
    base = clampi(v, 0, 127);
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;   // los pads iluminados dejan de tener sentido
    DBG("setbase", base);
    pushgrid();
}
function setspan(v) {
    span = clampi(v, 1, 128);
    if (armedPad >= span) armedPad = -1;
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;
    DBG("setspan", span);
    pushgrid();
}

function refresh() { pushgrid(); }
function bang() { pushgrid(); }
function loadbang() { DBG("loadbang"); pushgrid(); }

function dump() {
    var n = 0;
    for (var i = 0; i < SIZE; i++) if (map[i] >= 0) { DBG("  nota", i, "-> pad", map[i]); n++; }
    DBG("dump:", n, "rutas; base", base, "span", span, "armed", armedPad);
}

// ---- feedback a la grilla ---------------------------------------------------
function emitActive(idx, on) {
    idx = idx | 0;
    if (idx < 0 || idx >= PADS) return;
    if (on) {
        if (padHeld[idx]++ === 0) outlet(1, "padactive", idx, 1);
    } else {
        if (padHeld[idx] > 0 && --padHeld[idx] === 0) outlet(1, "padactive", idx, 0);
    }
}
function pushgrid() {
    var a = ["padroutes"];
    for (var i = 0; i < SIZE; i++) a.push(map[i] >= 0 ? map[i] : -1);
    outlet(1, a);
    outlet(1, "padbase", base);
    outlet(1, "padspan", span);
    outlet(1, "padarmed", armedPad);
    pushPiano();
}
// piano de la grilla: lista de notas asignadas (se dibujan en verde)
function pushPiano() {
    var a = ["pianoassigned"];
    for (var i = 0; i < SIZE; i++) if (map[i] >= 0) a.push(i);
    outlet(1, a);
}

// ---- persistencia (Fase 2: pattrstorage) -----------------------------------
function getstate() {
    var a = ["state", base, span];
    for (var i = 0; i < SIZE; i++) a.push(map[i]);
    outlet(1, a);
}
function setstate() {
    var a = arrayfromargs(arguments);
    if (a.length < 2 + SIZE) return;
    base = clampi(a[0], 0, 127);
    span = clampi(a[1], 1, 128);
    for (var i = 0; i < SIZE; i++) map[i] = a[2 + i] | 0;
    armedPad = -1;
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;
    pushgrid();
}
