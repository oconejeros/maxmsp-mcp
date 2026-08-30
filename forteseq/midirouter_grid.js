// midirouter_grid.js -- jsui: piano + grilla drum-rack para Midirouter (pestana Mapa).
//
// PIANO (arriba): teclas de notas de ENTRADA. Verde = asignada a algun pad. Ambar = sonando.
//   Click en tecla verde -> desasigna. Click en tecla blanca con un pad armado -> asigna.
// GRILLA (abajo): 16 x 4 = 64 pads. Pad 0 = abajo-izquierda = nota `base`. Cada pad muestra
//   su nombre de nota y, si esta ruteado, el nombre de la nota fuente (1:1). Ambar al sonar.
//   Contorno brillante = pad armado. Pads >= Rango atenuados.
//   Click -> arma / desarma. Shift/Ctrl + click -> borra la ruta del pad.
//
// outlet 0 -> js midirouter.js:   arm <pad> | clearpad <pad> | keyclick <nota> | refresh
// entradas desde el motor (nunca disparan outlet):
//   padroutes <128> | padbase <n> | padspan <n> | padarmed <pad> | padactive <pad> <0|1>
//   pianoassigned <notas...> | noteon <nota> <0|1>
//
// idiom jsui del repo: wf_levelviz.js / tonnetz.js.

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var COLS = 16, ROWS = 4, NPAD = 64, NSRC = 128;
var GAP = 3;
var PIANO_LO = 24, PIANO_HI = 96;   // C1..C6, ambos blancos (evita media tecla negra colgando)
var WHITE_PC = { 0: 1, 2: 1, 4: 1, 5: 1, 7: 1, 9: 1, 11: 1 };

var routes = [];        // routes[nota] = pad | -1
var active = [];        // active[pad] = 0/1  (pad sonando)
var srcOfPad = [];      // srcOfPad[pad] = nota | -1  (1:1)
var assigned = [];      // assigned[nota] = 0/1  (tiene ruteo)
var noteOn = [];        // noteOn[nota] = 0/1  (entrada sonando)
var armed = -1;
var padBase = 36;
var padSpan = 64;

var i;
for (i = 0; i < NSRC; i++) { routes[i] = -1; assigned[i] = 0; noteOn[i] = 0; }
for (i = 0; i < NPAD; i++) { active[i] = 0; srcOfPad[i] = -1; }

// -- piano: notas blancas / negras en el rango --
var whiteNotes = [], blackNotes = [];
for (i = PIANO_LO; i <= PIANO_HI; i++) {
    if (WHITE_PC[((i % 12) + 12) % 12]) whiteNotes.push(i);
    else blackNotes.push(i);
}
var NWHITE = whiteNotes.length;
function whiteIdxBefore(n) {
    var c = 0;
    for (var k = 0; k < whiteNotes.length; k++) if (whiteNotes[k] < n) c++;
    return c;
}

var NN = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
function noteName(n) {
    n = n | 0;
    return NN[((n % 12) + 12) % 12] + (Math.floor(n / 12) - 2);
}
function padIndex(col, rowFromTop) { return col + (ROWS - 1 - rowFromTop) * COLS; }

function pianoHeight(h) {
    var p = Math.round(h * 0.22);
    return p < 22 ? 22 : (p > 34 ? 34 : p);
}

function rebuildSrcOfPad() {
    for (var p = 0; p < NPAD; p++) srcOfPad[p] = -1;
    for (var s = 0; s < NSRC; s++) {
        var pd = routes[s];
        if (pd >= 0 && pd < NPAD) srcOfPad[pd] = s;
    }
}

// ---- mensajes desde el motor (nunca llaman outlet) -------------------------
function padroutes() {
    var a = arrayfromargs(arguments);
    for (var k = 0; k < NSRC; k++) routes[k] = (k < a.length) ? (a[k] | 0) : -1;
    rebuildSrcOfPad();
    mgraphics.redraw();
}
function padactive(p, s) {
    p = p | 0;
    if (p >= 0 && p < NPAD) { active[p] = s ? 1 : 0; mgraphics.redraw(); }
}
function padbase(n) {
    padBase = n | 0;
    for (var k = 0; k < NPAD; k++) active[k] = 0;
    mgraphics.redraw();
}
function padspan(n) { padSpan = n | 0; mgraphics.redraw(); }
function padarmed(p) { armed = p | 0; mgraphics.redraw(); }
function pianoassigned() {
    var a = arrayfromargs(arguments);
    for (var k = 0; k < NSRC; k++) assigned[k] = 0;
    for (var j = 0; j < a.length; j++) {
        var n = a[j] | 0;
        if (n >= 0 && n < NSRC) assigned[n] = 1;
    }
    mgraphics.redraw();
}
function noteon(n, s) {
    n = n | 0;
    if (n >= 0 && n < NSRC) { noteOn[n] = s ? 1 : 0; mgraphics.redraw(); }
}

function loadbang() { outlet(0, "refresh"); }
function onresize() { mgraphics.redraw(); }

// ---- interaccion --------------------------------------------------------
function keyAt(x, y, w, ph) {
    var ww = w / NWHITE;
    var bw = ww * 0.62, bh = ph * 0.62;
    for (var k = 0; k < blackNotes.length; k++) {
        var n = blackNotes[k];
        var cx = whiteIdxBefore(n) * ww;
        var bx = cx - bw / 2;
        if (x >= bx && x <= bx + bw && y <= bh) return n;
    }
    var wi = Math.floor(x / ww);
    if (wi < 0) wi = 0;
    if (wi >= NWHITE) wi = NWHITE - 1;
    return whiteNotes[wi];
}

function onclick(x, y, but, cmd, shift, capslock, option, ctrl) {
    if (!but) return;
    var w = box.rect[2] - box.rect[0];
    var h = box.rect[3] - box.rect[1];
    var ph = pianoHeight(h);

    if (y < ph) {
        var note = keyAt(x, y, w, ph);
        if (note >= 0) outlet(0, "keyclick", note);
        return;
    }

    var gridTop = ph + GAP;
    var gh = h - gridTop;
    if (gh <= 0) return;
    var cw = w / COLS, ch = gh / ROWS;
    var col = Math.floor(x / cw);
    var rowT = Math.floor((y - gridTop) / ch);
    if (col < 0 || col >= COLS || rowT < 0 || rowT >= ROWS) return;
    var pad = padIndex(col, rowT);
    if (pad < 0 || pad >= NPAD) return;

    var mod = shift || cmd || ctrl || option;
    if (mod) outlet(0, "clearpad", pad);
    else outlet(0, "arm", (armed === pad) ? -1 : pad);
    mgraphics.redraw();
}

// ---- dibujo -----------------------------------------------------------
var C_WHITE = [0.85, 0.85, 0.85, 1];
var C_BLACK = [0.13, 0.13, 0.13, 1];
var C_GREEN = [0.35, 0.80, 0.42, 1];
var C_AMBER = [1.0, 0.71, 0.196, 1.0];

function keyColor(n, isBlack) {
    if (noteOn[n]) return C_AMBER;
    if (assigned[n]) return C_GREEN;
    return isBlack ? C_BLACK : C_WHITE;
}

function paint() {
    var w = box.rect[2] - box.rect[0];
    var h = box.rect[3] - box.rect[1];
    var ph = pianoHeight(h);

    mgraphics.set_source_rgba([0.09, 0.09, 0.09, 1]);
    mgraphics.rectangle(0, 0, w, h);
    mgraphics.fill();
    mgraphics.select_font_face("Arial");

    // ---- piano ----
    var ww = w / NWHITE;
    var wi, x, n;
    for (wi = 0; wi < NWHITE; wi++) {
        n = whiteNotes[wi];
        x = wi * ww;
        mgraphics.set_source_rgba(keyColor(n, false));
        mgraphics.rectangle(x + 0.5, 0, ww - 1, ph);
        mgraphics.fill();
        mgraphics.set_source_rgba([0.25, 0.25, 0.25, 1]);
        mgraphics.set_line_width(1);
        mgraphics.rectangle(x + 0.5, 0, ww - 1, ph);
        mgraphics.stroke();
    }
    var bw = ww * 0.62, bh = ph * 0.62;
    for (var bk = 0; bk < blackNotes.length; bk++) {
        n = blackNotes[bk];
        var cx = whiteIdxBefore(n) * ww;
        mgraphics.set_source_rgba(keyColor(n, true));
        mgraphics.rectangle(cx - bw / 2, 0, bw, bh);
        mgraphics.fill();
    }
    // separador
    mgraphics.set_source_rgba([0.03, 0.03, 0.03, 1]);
    mgraphics.rectangle(0, ph, w, GAP);
    mgraphics.fill();

    // ---- grilla ----
    var gridTop = ph + GAP;
    var gh = h - gridTop;
    if (gh <= 0) return;
    var cw = w / COLS, ch = gh / ROWS;

    for (var rowT = 0; rowT < ROWS; rowT++) {
        for (var col = 0; col < COLS; col++) {
            var pad = padIndex(col, rowT);
            var px = col * cw, py = gridTop + rowT * ch;
            var note = padBase + pad;
            var band = (Math.floor(pad / COLS) % 2);
            var isActive = active[pad];
            var isArmed = (armed === pad);
            var inSpan = (pad < padSpan);
            var src = srcOfPad[pad];

            if (isActive) mgraphics.set_source_rgba(C_AMBER);
            else mgraphics.set_source_rgba(band ? [0.17, 0.17, 0.17, 1] : [0.13, 0.13, 0.13, 1]);
            mgraphics.rectangle(px + 1, py + 1, cw - 2, ch - 2);
            mgraphics.fill();

            if (!inSpan) {
                mgraphics.set_source_rgba([0, 0, 0, 0.5]);
                mgraphics.rectangle(px + 1, py + 1, cw - 2, ch - 2);
                mgraphics.fill();
            }
            if (isArmed) {
                mgraphics.set_source_rgba([1.0, 0.92, 0.45, 1.0]);
                mgraphics.set_line_width(2);
                mgraphics.rectangle(px + 2, py + 2, cw - 4, ch - 4);
                mgraphics.stroke();
            }

            mgraphics.set_source_rgba(isActive ? [0.1, 0.1, 0.1, 1] : (inSpan ? [0.62, 0.62, 0.62, 1] : [0.4, 0.4, 0.4, 1]));
            mgraphics.set_font_size(9);
            mgraphics.move_to(px + 3, py + 11);
            mgraphics.show_text(noteName(note));

            if (src >= 0) {
                mgraphics.set_source_rgba(isActive ? [0.1, 0.1, 0.1, 1] : C_GREEN);
                mgraphics.set_font_size(8);
                mgraphics.move_to(px + 3, py + ch - 4);
                mgraphics.show_text(noteName(src));
            }
        }
    }
}
