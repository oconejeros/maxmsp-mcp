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
//   setpresetslot <n> / storepreset / recallpreset / clearpreset / setpresetname <txt>
//   loadpresets        leer el archivo sidecar (arranque)
// outlet 1 -> grilla jsui (+ route presetname/presetslots que va a la UI de Presets):
//   padroutes <128 ints>   mapa completo (nota -> pad, o -1)
//   padbase <n>            nota del pad 0
//   padspan <n>            Rango (la grilla atenua pads >= span)
//   padarmed <pad>         pad armado, o -1
//   padactive <pad> <0|1>  encender / apagar un pad (note on/off)
//   pianoassigned <notas>  lista de notas de entrada asignadas (el piano las pinta verde)
//   noteon <nota> <0|1>    nota de entrada sonando (el piano la pinta ambar)
//   presetname <txt> / presetslots <"1 - 3 - ...">   estado de la pestana Presets
//
// Presets: archivo sidecar `midirouter_presets.txt` junto al .amxd (mismo mecanismo que
// forteseqwf). 16 slots con nombre + una linea `current` que se auto-guarda con debounce
// en cada cambio y se restaura al instanciar el device.

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
    saveCurrent();
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
        saveCurrent();
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
    saveCurrent();
}
function clearall() {
    for (var i = 0; i < SIZE; i++) map[i] = -1;
    armedPad = -1;
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;
    DBG("clearall");
    pushgrid();
    saveCurrent();
}

// ---- parametros ---------------------------------------------------------------
function setbase(v) {
    base = clampi(v, 0, 127);
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;   // los pads iluminados dejan de tener sentido
    DBG("setbase", base);
    pushgrid();
    saveCurrent();
}
function setspan(v) {
    span = clampi(v, 1, 128);
    if (armedPad >= span) armedPad = -1;
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;
    DBG("setspan", span);
    pushgrid();
    saveCurrent();
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

// ---- presets: archivo sidecar junto al .amxd (mismo mecanismo que forteseqwf) -----------
var PRESET_FILE = "midirouter_presets.txt";
var PRESET_SLOTS = 16;
var presetSlot = 1;
var presetBank = [];                 // 1..16 -> {base,span,map[,__name]} | null ; indice 0 sin uso
var saveTask = new Task(function () { savepresets(); }, this);   // debounce del auto-guardado

// Junto al .amxd, no donde ande el cwd de Max (un nombre pelado solo resuelve por search path
// al LEER, escribirlo cae en cualquier lado). Copiado de forteseqwf.js.
function devPath(file) {
    var fp = "";
    try { fp = this.patcher.filepath; } catch (e) { fp = ""; }
    if (!fp) return file;
    var cut = fp.lastIndexOf("/");
    if (cut < 0) cut = fp.lastIndexOf("\\");
    return cut >= 0 ? fp.slice(0, cut + 1) + file : file;
}

function configFromCurrent() { return { base: base, span: span, map: map.slice(0) }; }

function applyConfig(c) {
    if (!c) return;
    base = clampi(c.base, 0, 127);
    span = clampi(c.span, 1, 128);
    for (var i = 0; i < SIZE; i++) map[i] = (c.map && c.map.length > i) ? (c.map[i] | 0) : -1;
    armedPad = -1;
    for (var j = 0; j < PADS; j++) padHeld[j] = 0;
    pushgrid();
}

function configToLine(c) { return c.base + "\t" + c.span + "\t" + c.map.join(" "); }

// parts = campos despues del <slot> (o "current"); el "__name=" lo saca el caller
function configFromParts(parts) {
    var f = [];
    for (var i = 0; i < parts.length; i++)
        if (parts[i].slice(0, 7) !== "__name=") f.push(parts[i]);
    var c = { base: 36, span: 64, map: [] };
    if (f.length >= 3) {
        c.base = parseInt(f[0], 10);
        c.span = parseInt(f[1], 10);
        var mm = f[2].split(" ");
        for (var k = 0; k < SIZE; k++) c.map[k] = (k < mm.length) ? (parseInt(mm[k], 10) | 0) : -1;
    } else {
        for (var z = 0; z < SIZE; z++) c.map[z] = -1;
    }
    return c;
}

function saveCurrent() { saveTask.cancel(); saveTask.schedule(400); }

function slotOf(slot) {
    var s = (slot === undefined || slot === null) ? presetSlot : Math.round(slot);
    if (!(s >= 1 && s <= PRESET_SLOTS)) { DBG("slot fuera de rango:", s); return -1; }
    return s;
}
function setpresetslot(n) {
    n = Math.round(n);
    if (!isFinite(n) || n < 1) n = 1;
    if (n > PRESET_SLOTS) n = PRESET_SLOTS;
    presetSlot = n;
    sendPresetName(n);
}
function storepreset(slot) {
    var s = slotOf(slot); if (s < 0) return;
    var c = configFromCurrent();
    var old = presetBank[s] && presetBank[s].__name;
    if (old) c.__name = old;                 // re-guardar sobre un slot con nombre lo conserva
    presetBank[s] = c;
    savepresets();
    sendPresetList(); sendPresetName(s);
    DBG("slot", s, "guardado");
}
function recallpreset(slot) {
    var s = slotOf(slot); if (s < 0) return;
    var c = presetBank[s];
    if (!c) { DBG("slot", s, "vacio"); return; }
    applyConfig({ base: c.base, span: c.span, map: c.map });
    saveCurrent();                            // el slot cargado pasa a ser el `current`
    DBG("slot", s, "cargado");
}
function clearpreset(slot) {
    var s = slotOf(slot); if (s < 0) return;
    presetBank[s] = null;
    savepresets();
    sendPresetList(); sendPresetName(s);
    DBG("slot", s, "borrado");
}
function setpresetname() {
    var name = arrayfromargs(arguments).join(" ");
    var s = presetSlot;
    if (!presetBank[s]) presetBank[s] = configFromCurrent();
    presetBank[s].__name = name;
    savepresets();
    sendPresetName(s);
}
function sendPresetName(s) {
    var c = presetBank[s];
    outlet(1, "presetname", (c && c.__name) ? c.__name : "-");
}
function sendPresetList() {
    var s = "";
    for (var i = 1; i <= PRESET_SLOTS; i++) s += (i > 1 ? " " : "") + (presetBank[i] ? i : "-");
    outlet(1, "presetslots", s);
}

function savepresets() {
    if (typeof File === "undefined") return;
    var f = new File(devPath(PRESET_FILE), "write", "TEXT");
    if (!f.isopen) { DBG("no pude escribir", devPath(PRESET_FILE)); return; }
    try {
        f.eof = 0; f.position = 0;
        f.writeline("midirouter presets 1");
        f.writeline("current\t" + configToLine(configFromCurrent()));
        for (var s = 1; s <= PRESET_SLOTS; s++) {
            var c = presetBank[s];
            if (!c) continue;
            var line = "" + s;
            if (c.__name) line += "\t__name=" + c.__name;
            line += "\t" + configToLine(c);
            f.writeline(line);
        }
    } catch (e) { DBG("fallo al guardar presets:", e); }
    f.close();
}
function loadpresets() {
    if (typeof File === "undefined") return;
    var f = new File(devPath(PRESET_FILE), "read", "TEXT");
    if (!f.isopen) { DBG("sin archivo de presets (primera vez)"); return; }
    presetBank = [];
    var n = 0, curr = null;
    try {
        f.readline(200);   // header
        while (f.position < f.eof) {
            var line = "" + f.readline(65536);
            if (!line) continue;
            var parts = line.split("\t");
            var head = parts[0];
            var rest = parts.slice(1);
            if (head === "current") { curr = configFromParts(rest); continue; }
            var s = Math.round(parseFloat(head));
            if (!(s >= 1 && s <= PRESET_SLOTS)) continue;
            var nm = null;
            for (var i = 0; i < rest.length; i++)
                if (rest[i].slice(0, 7) === "__name=") { nm = rest[i].slice(7); break; }
            var cc = configFromParts(rest);
            if (nm !== null) cc.__name = nm;
            presetBank[s] = cc; n++;
        }
    } catch (e) { DBG("fallo al leer presets:", e); }
    f.close();
    if (curr) applyConfig(curr);
    sendPresetList();
    sendPresetName(presetSlot);
    DBG(n, "slots leidos; current", curr ? "restaurado" : "no habia");
}
