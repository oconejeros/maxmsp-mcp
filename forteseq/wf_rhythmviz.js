// wf_rhythmviz.js -- jsui for EVENFLOW's floating "Ritmos" window: how the Well-Formed / MoS
// rhythms are behaving, one lane per hierarchy level, plus a radial "necklace" view.
//
// Fed by forteseqwf.js's `viz <selector> ...` stream on its single outlet, split off by
// `route viz` (wf_vizroute) -- dispatched here by selector name, fs2 style, no [route] in the jsui:
//   vcycle  <cycleIndex>
//   vperiod <periodMs>
//   vmorph  <engaged 0|1> <morphA> <morphB> <morphX>
//   viso    <isoLevel> <isoPulses> <isoCapped 0|1>
//   vgrid   <c0..c15>                          accent grid
//   vreadlen <accentReadLen>
//   vlevel  <lv> <on> <uc> <step> <group> <channel> <pitch> <pc> <r> <wordLen> <mkFam|-> <mkLvl|-1> <phase>
//   vword   <lv> <n> <b0..b(n-1)>              1 = long interval, 0 = short
//   vonsets <lv> 0 <nFull> <t0..>             all onsets, ms
//   vonsets <lv> 1 <nKept> <t0 a0 t1 a1..>    after U/C + Step; a = accent flag (0 Normal / 1 Accent)
//   vonsets <lv> 2 <nDrop> <t0..>             onsets removed by Step -> ghosted
//   vend    <levelCount>                       swap the buffered frame in, redraw once
//   vpulse  <lv>                               a note just fired on that level -> flash
//
// The metro re-queries ~8 Hz so this keeps drawing with the transport stopped. Sends back on
// outlet 0 -> subpatcher outlet -> js forteseqwf.js inlet 0. Each lane in the lanes view carries a
// compact per-level control block in the gutter: "G" toggles the level on/off (setlevelon), "▸"
// cycles its output group (setlevelgroup), "U/C" toggles complemented reading (setleveluc), "pas"
// cycles the reading step 1..8 (setlevelstep), "gir" cycles the phase 0..15 (setlevelphase), and
// "♪-/♪+" nudge the level pitch (setlevelpitch). The
// sidebar also drives setm/setn/setlevels/setglobalprob/setseed/setsynctempo/setbeatsperperiod
// (the "globales" steppers), setmorph/setmorpha/setmorphb/clearmorphtouched (the morph block),
// and setr via the pulse-ordered rhythm selector (click a cell, the family / "solo alcanzables"
// chips, the prev/next arrows, or drag the pulse-target number). The engine's setr snaps to the
// marker and echoes the R control, so a pick is just `setr <r>`.
//
// The MOS catalog feed (forteseqwf.js emitCatalog, same `route viz` arm; sent on vizon and again
// whenever M or N change while the popup is open):
//   vcatmeta <count> <m> <n>      open a fresh buffer; (m,n) the pulse counts are computed at
//   vcat <idx> <r> <family> <isoLevel> <pulses> <capped> <mkLevel>   one row, already sorted
//                                family in n|phi|delta|sigma; isoLevel/pulses = -1 when capped
//   vcatend <count>               swap buffer in, refilter, redraw
//
// Morph preview (only while Morph A or B point at a slot):
//   vmorphprev off | <0=A|1=B|2=blend> <r> <m> <n> <levels> <nOnsets> <t0..>   -- blend ring is the
//                                A<->B lerp WITH your per-field overrides, i.e. what a cycle plays
//   vmorphx <x> <rLinear 0|1> <slotA> <slotB>
//   vmorphover <count> <field..>  -- fields you edited since the morph began; they hold still while
//                                the rest of the morph keeps moving (a rhythm pick = an R override)
//   vslots <count> <slot..>       -- slots that hold a preset; the sidebar's Morph A / B pickers
//                                send `setmorpha` / `setmorphb <slot>` back on outlet 0
//   vglob <m> <n> <levels> <gprob> <seed> <sync 0|1> <beats> <r>   -- editable globals; the
//                                sidebar steppers send setm / setn / setlevels / setglobalprob /
//                                setseed / setsynctempo / setbeatsperperiod / setr back on outlet 0
//
// jsui idiom from the repo: fs2horizon.js (window-follow scaffolding, pulse decay), fs2setpick.js
// (geo hit-test cache + outlet writes), pccolor.js (pitch-class swatch).

include('pccolor.js');

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var SELF = this;
var MAXLV = 6;
var NN = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

// --- follow the floating window (box.rect is unreliable in the M4L popup; read wind.size) -----
var PAD = 8;
function windSize() {
	try {
		var s = SELF.patcher.wind.size;
		if (s && s[0] > 60 && s[1] > 60) return s;
	} catch (e) {}
	return null;
}
function viewportWH() {
	var s = windSize();
	if (s) return [Math.max(360, Math.round(s[0]) - PAD * 2), Math.max(180, Math.round(s[1]) - PAD * 2)];
	return [1000, 560];
}
function fitToWindow() {
	var s = windSize();
	if (s) {
		var r = [PAD, PAD, Math.max(PAD + 300, Math.round(s[0]) - PAD),
			Math.max(PAD + 160, Math.round(s[1]) - PAD)];
		try {
			var b = box.rect;
			if (b[0] != r[0] || b[1] != r[1] || b[2] != r[2] || b[3] != r[3]) { try { box.rect = r; } catch (e2) {} }
		} catch (e3) {}
	}
	mgraphics.redraw();
}
var _fit = new Task(fitToWindow, SELF);
_fit.interval = 250;
_fit.repeat();
fitToWindow();
function onresize() { fitToWindow(); }

// --- per-level colour: a monotone warm->cool ramp reads instantly as hierarchy depth ---------
var LV_RGB = [];
for (var _i = 0; _i < MAXLV; _i++) {
	var t = _i / (MAXLV - 1);
	// warm amber (30) -> cool cyan-blue (205)
	var hh = 30 + t * 175;
	var rgb = (typeof hslToRgb === 'function') ? hslToRgb(hh, 0.55, 0.55) : { r: 0.6, g: 0.6, b: 0.7 };
	LV_RGB.push([rgb.r, rgb.g, rgb.b]);
}
function pcSwatch(pc) {
	var c = pcToColor(((pc % 12) + 12) % 12, { baseHue: 0, sat: 0.62, lum: 0.52 });
	return [c.r, c.g, c.b];
}

// --- frame state ---------------------------------------------------------------------------
function freshFrame() {
	return {
		cycle: 0, period: 2000, morph: [0, 0, 0, 0], iso: [-1, -1, 0],
		grid: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], readLen: 4,
		count: 0, lv: []
	};
}
function freshLevel(i) {
	return {
		lv: i, on: 1, uc: 0, step: 1, group: i + 1, channel: i + 1, pitch: 60, pc: 0,
		r: 1.5, wordLen: 0, mkFam: '-', mkLvl: -1, phase: 0,
		word: [], full: [], kept: [], drop: []
	};
}

var frame = freshFrame();
var scratch = freshFrame();
var pulse = [];
for (_i = 0; _i < MAXLV; _i++) pulse.push(0);

var vizmode = 0;              // 0 = lanes, 1 = radial necklaces
var phaseMs = 0;
var lastCycle = -999999;
var geo = { tab: null, lanes: [], cat: [], catFam: [], catReach: null,
	catPrev: null, catNext: null, catNum: null, morphTrack: null, mSlot: [], morphClear: null,
	glob: [], sideTab: [], catStrip: null, pset: [], psetStrip: null };

// The sidebar is TABBED so its sections never overlap on a short window: 0 = Ritmos (compact
// filters + pulse row + a 2-row drag-scroll MOS grid), 1 = Morph (A/B steppers, a scrollable
// preset strip, the horizontal morphX slider). Global (M/N/niveles/prob/semilla/R/sync/beats) is
// a fixed band pinned above the accent strip, always visible.
var sideTab = 0;
var catScroll = 0;           // px pan offset of the MOS grid strip
var _catDrag = 0, _catDragX0 = 0, _catScroll0 = 0, _catDragCell = -1;
var _catSnappedSel = -999;   // last catSel the grid auto-scrolled into view (so a hand-pan stays put)
var psetScroll = 0;          // px pan offset of the Morph-tab preset strip
var _psetDrag = 0, _psetDragX0 = 0, _psetScroll0 = 0, _psetDragCell = -999;

var PRESET_SLOTS = 64;       // mirrors forteseqwf.js; only used to clamp the A/B slot steppers
var slotsFilled = [];        // slot numbers that hold a preset (viz vslots)
var slotTarget = 'a';        // a preset-strip pick assigns to Morph A or Morph B
var glob = { m: 3, n: 5, levels: 2, gprob: 100, seed: 1, sync: 0, beats: 4, r: 1.5 };  // viz vglob
var R_STEPS = [0.001, 0.005, 0.01, 0.05, 0.1, 0.25];
var rStep = 0.05;            // click increment for the Global-band R stepper
var _morphFocus = 0;         // the horizontal morph slider has keyboard focus (arrow keys move it)
var SIDE_TABS = ['Ritmos', 'Morph'];

// --- pulse-ordered MOS catalog (the "Ritmos" selector) ----------------------------------------
// cat[] is the engine's already-sorted list (fewest onsets first, metallic last). catView[] is
// the indices that pass the family + reachable filters -- what the strip draws. catSel indexes
// cat[]. The engine's setr snaps to the marker anyway, so a pick just sends `setr <r>`.
var cat = [];
var catScratch = [];
var catMN = [3, 5];
var catFam = 'todas';        // todas | n | phi | delta | sigma  (Spanish tokens map in catfilter)
var catReachOnly = 0;        // 1 -> hide capped (metallic) rows
var catSel = 0;
var catView = [];
var catTarget = 0;           // "pulsos objetivo" -- the isochrony onset count to steer toward
var _dragActive = 0, _dragBase = 0, _dragY0 = 0;
var _morphDrag = 0;          // dragging the morph column to move morphX

// morph preview: slot A / slot B / the current blend, each a normalised onset ring of the top
// active level, refreshed ~8 Hz by the engine while a morph is engaged (see emitMorphPreview).
var mprev = { on: 0, x: 0, lin: 0, a: 0, b: 0, s: [null, null, null], over: [] };

var FAM_ES = { n: 'n', phi: 'oro', delta: 'plata', sigma: 'bronce' };
// config field name -> short Spanish label for the "held fixed while morphing" readout
var OVER_ES = {
	r: 'R', m: 'M', n: 'N', levels: 'niveles', period: 'periodo', sync: 'sync', beats: 'beats',
	on: 'on/off', uc: 'U/C', lr: 'reversa', pitch: 'tono', vel: 'vel', dur: 'dur', lstep: 'step',
	lprob: 'prob', gprob: 'prob global', seed: 'semilla', lgroup: 'grupo', gchan: 'canal',
	arton: 'acentos', agrid: 'rejilla', acyc: 'ciclo ac', atie: 'atar', aeuc: 'euclid',
	aeuck: 'euclid k', aeucr: 'euclid rot', aphase: 'fase', nvmin: 'vel min', nvmax: 'vel max',
	nfig: 'figura', nsil: 'silencio', avmin: 'ac vmin', avmax: 'ac vmax', afig: 'ac fig', asil: 'ac sil'
};
var FAM_RGB = {
	n:     [0.32, 0.55, 0.78],
	phi:   [0.85, 0.68, 0.26],
	delta: [0.62, 0.64, 0.72],
	sigma: [0.74, 0.52, 0.34]
};

function catPulseRange() {
	var lo = 1e9, hi = 0;
	for (var i = 0; i < cat.length; i++) {
		if (cat[i].capped) continue;
		if (cat[i].pulses < lo) lo = cat[i].pulses;
		if (cat[i].pulses > hi) hi = cat[i].pulses;
	}
	if (lo > hi) { lo = 1; hi = 1; }
	return [lo, hi];
}

function rebuildCatView() {
	catView = [];
	for (var i = 0; i < cat.length; i++) {
		var row = cat[i];
		if (catReachOnly && row.capped) continue;
		if (catFam !== 'todas' && row.family !== catFam) continue;
		catView.push(i);
	}
	if (catView.length) {
		if (catSel < 0) catSel = 0;
		// keep catSel inside the view -- snap to the nearest visible row if it was filtered out
		if (catView.indexOf(catSel) < 0) {
			var best = catView[0], bd = 1e9;
			for (var j = 0; j < catView.length; j++) {
				var d = Math.abs(catView[j] - catSel);
				if (d < bd) { bd = d; best = catView[j]; }
			}
			catSel = best;
		}
	}
	var sr = cat[catSel];
	if (sr && !sr.capped && !catTarget) catTarget = sr.pulses;
}

function applySel() {
	if (!cat.length || catSel < 0 || catSel >= cat.length) return;
	if (!cat[catSel].capped) catTarget = cat[catSel].pulses;
	outlet(0, 'setr', cat[catSel].r);
	mgraphics.redraw();
}

// Walk the view to the reachable row whose isochrony onset count is nearest `p`
// (ties -> the lower hierarchy level, then the lower r).
function selectNearestPulses(p) {
	if (!isFinite(p) || !catView.length) return;
	var best = -1, bd = 1e18;
	for (var i = 0; i < catView.length; i++) {
		var row = cat[catView[i]];
		if (row.capped) continue;
		var d = Math.abs(row.pulses - p);
		if (d < bd - 1e-9 || (Math.abs(d - bd) < 1e-9 && best >= 0 && row.isoLevel < cat[best].isoLevel)) {
			bd = d; best = catView[i];
		}
	}
	if (best >= 0) { catSel = best; applySel(); }
}

function ensureLv(buf, i) {
	if (!(i >= 0 && i < MAXLV)) return null;
	while (buf.lv.length <= i) buf.lv.push(freshLevel(buf.lv.length));
	return buf.lv[i];
}

// --- inlet messages ----------------------------------------------------------------------
function vcycle(c) {
	scratch = freshFrame();
	scratch.cycle = Math.round(c);
}
function vperiod(p) { scratch.period = Math.max(1, Number(p) || 2000); }
function vmorph(eng, a, b, x) { scratch.morph = [Math.round(eng) ? 1 : 0, Math.round(a), Math.round(b), Number(x) || 0]; }
function viso(lvl, pulses, capped) { scratch.iso = [Math.round(lvl), Math.round(pulses), Math.round(capped) ? 1 : 0]; }
function vgrid() {
	var a = arrayfromargs(arguments);
	for (var k = 0; k < 16; k++) scratch.grid[k] = (k < a.length && a[k]) ? 1 : 0;
}
function vreadlen(n) { scratch.readLen = Math.max(1, Math.min(16, Math.round(n))); }

function vlevel() {
	var a = arrayfromargs(arguments);
	var L = ensureLv(scratch, Math.round(a[0]));
	if (!L) return;
	L.on = a[1] ? 1 : 0;
	L.uc = a[2] ? 1 : 0;
	L.step = Math.max(1, Math.round(a[3]));
	L.group = Math.max(1, Math.min(MAXLV, Math.round(a[4])));
	L.channel = Math.max(1, Math.min(16, Math.round(a[5])));
	L.pitch = Math.round(a[6]);
	L.pc = ((Math.round(a[7]) % 12) + 12) % 12;
	L.r = Number(a[8]) || 1;
	L.wordLen = Math.round(a[9]);
	L.mkFam = (a[10] === undefined) ? '-' : String(a[10]);
	L.mkLvl = Math.round(a[11]);
	L.phase = Math.round(a[12]) || 0;
}
function vword() {
	var a = arrayfromargs(arguments);
	var L = ensureLv(scratch, Math.round(a[0]));
	if (!L) return;
	var n = Math.max(0, Math.round(a[1]));
	L.word = [];
	for (var k = 0; k < n; k++) L.word.push(a[2 + k] ? 1 : 0);
}
function vonsets() {
	var a = arrayfromargs(arguments);
	var L = ensureLv(scratch, Math.round(a[0]));
	if (!L) return;
	var kind = Math.round(a[1]);
	var n = Math.max(0, Math.round(a[2]));
	if (kind === 0) {
		L.full = [];
		for (var k = 0; k < n; k++) L.full.push(Number(a[3 + k]) || 0);
	} else if (kind === 1) {
		L.kept = [];
		for (var k = 0; k < n; k++) L.kept.push([Number(a[3 + 2 * k]) || 0, a[4 + 2 * k] ? 1 : 0]);
	} else if (kind === 2) {
		L.drop = [];
		for (var k = 0; k < n; k++) L.drop.push(Number(a[3 + k]) || 0);
	}
}
function vend(count) {
	scratch.count = Math.max(0, Math.min(MAXLV, Math.round(count)));
	frame = scratch;
	if (frame.cycle !== lastCycle) { phaseMs = 0; lastCycle = frame.cycle; }
	mgraphics.redraw();
}
function vpulse(lv) {
	lv = Math.round(lv);
	if (lv >= 0 && lv < MAXLV) { pulse[lv] = 1; startDecay(); }
}

// --- MOS catalog frames ---------------------------------------------------------------------
function vcatmeta(count, m, n) {
	catScratch = [];
	catMN = [Math.round(m) || 0, Math.round(n) || 0];
}
function vcat() {
	var a = arrayfromargs(arguments);
	catScratch.push({
		r: Number(a[1]) || 1,
		family: (a[2] === undefined) ? 'n' : String(a[2]),
		isoLevel: Math.round(a[3]),
		pulses: Math.round(a[4]),
		capped: a[5] ? 1 : 0,
		mkLevel: Math.round(a[6])
	});
}
function vcatend() {
	cat = catScratch;
	if (catSel >= cat.length) catSel = cat.length ? cat.length - 1 : 0;
	rebuildCatView();
	mgraphics.redraw();
}

// --- morph preview frames -----------------------------------------------------------------
function vmorphprev() {
	var g = arrayfromargs(arguments);
	if (g[0] === 'off') {
		mprev.a = 0; mprev.b = 0;
		if (mprev.on) { mprev.on = 0; mprev.over = []; mgraphics.redraw(); }
		return;
	}
	var s = Math.round(g[0]);
	if (s < 0 || s > 2) return;
	var cnt = Math.max(0, Math.round(g[5]));
	var ons = [];
	for (var k = 0; k < cnt; k++) ons.push(Number(g[6 + k]) || 0);
	mprev.s[s] = { r: Number(g[1]) || 1, m: Math.round(g[2]), n: Math.round(g[3]),
		levels: Math.round(g[4]), ons: ons };
	mprev.on = 1;
}
function vmorphx(x, lin, a, b) {
	mprev.x = Number(x) || 0;
	mprev.lin = Math.round(lin) ? 1 : 0;
	mprev.a = Math.round(a); mprev.b = Math.round(b);
	mgraphics.redraw();
}
// fields the user edited since the morph began -> shown as "held fixed" and, for r, flags the
// picked rhythm cell as an override on top of the running morph (not a preset swap).
function vmorphover() {
	var a = arrayfromargs(arguments);
	var n = Math.max(0, Math.round(a[0]));
	mprev.over = [];
	for (var k = 0; k < n; k++) mprev.over.push(String(a[1 + k]));
	mgraphics.redraw();
}
function vslots() {
	var a = arrayfromargs(arguments);
	var n = Math.max(0, Math.round(a[0]));
	slotsFilled = [];
	for (var k = 0; k < n; k++) slotsFilled.push(Math.round(a[1 + k]));
	mgraphics.redraw();
}
function vglob(m, n, levels, gprob, seed, sync, beats, r) {
	glob.m = Math.round(m); glob.n = Math.round(n); glob.levels = Math.round(levels);
	glob.gprob = Math.round(gprob); glob.seed = Math.round(seed);
	glob.sync = Math.round(sync) ? 1 : 0; glob.beats = Number(beats) || 4;
	glob.r = Number(r) || 1.5;
}

// --- selector messages (also reachable from Max, but the strip UI drives them directly) -------
function catfilter(sym) {
	var s = String(sym).toLowerCase();
	var map = { todas: 'todas', n: 'n', oro: 'phi', phi: 'phi', plata: 'delta', delta: 'delta',
		bronce: 'sigma', sigma: 'sigma' };
	catFam = map[s] || 'todas';
	rebuildCatView();
	mgraphics.redraw();
}
function catreach(v) {
	catReachOnly = v ? 1 : 0;
	rebuildCatView();
	mgraphics.redraw();
}
function cattarget(p) {
	p = Math.round(Number(p));
	var rng = catPulseRange();
	catTarget = Math.max(rng[0], Math.min(rng[1], p));
	selectNearestPulses(catTarget);
}
function catstep(d) {
	d = Math.round(d) || 0;
	if (!catView.length) return;
	var vp = catView.indexOf(catSel);
	if (vp < 0) vp = 0;
	vp = Math.max(0, Math.min(catView.length - 1, vp + d));
	catSel = catView[vp];
	applySel();
}
function catpick(i) {
	i = Math.round(i);
	if (i >= 0 && i < catView.length) { catSel = catView[i]; applySel(); }
}

function clear() { frame = freshFrame(); scratch = freshFrame(); mgraphics.redraw(); }
function color() {}                 // shared-outlet selector from the other panels; not ours
function anything() {}              // any stray selector (pcontrol 'open', colmon, ...) -- ignore
function bang() { mgraphics.redraw(); }

// --- playhead + pulse animation --------------------------------------------------------------
var _tick = new Task(function () {
	phaseMs += 30;
	if (frame.period > 0 && phaseMs >= frame.period) phaseMs -= frame.period;
	mgraphics.redraw();
}, SELF);
_tick.interval = 30;
_tick.repeat();

var decayTask = null;
function startDecay() {
	if (decayTask) return;
	decayTask = new Task(function () {
		var any = 0;
		for (var k = 0; k < MAXLV; k++) {
			if (pulse[k] > 0) { pulse[k] *= 0.72; if (pulse[k] < 0.03) pulse[k] = 0; else any = 1; }
		}
		mgraphics.redraw();
		if (!any && decayTask) { decayTask.cancel(); decayTask = null; }
	}, SELF);
	decayTask.interval = 33;
	decayTask.repeat();
}

// --- interaction ------------------------------------------------------------------------------
function ptIn(r, x, y) { return r && x >= r.x && y >= r.y && x < r.x + r.w && y < r.y + r.h; }

// a compact [label ◀ value ▶] stepper in a box of width w; pushes two hit-rects onto `arr`
// tagged {step:-1|+1, tag}.
function stepper(arr, x, y, w, h, label, valTxt, tag) {
	mgraphics.set_source_rgba([0.62, 0.64, 0.72, 1]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(x, y + h - 4);
	mgraphics.show_text(label);
	var lw = 10 + label.length * 6;
	var mx = x + lw, rx = x + w - 16;
	chip(mx, y, 16, h, false, '◀', 10);
	arr.push({ x: mx, y: y, w: 16, h: h, step: -1, tag: tag });
	mgraphics.set_source_rgba([0.15, 0.15, 0.18, 1]);
	mgraphics.rectangle(mx + 18, y, rx - (mx + 18) - 2, h); mgraphics.fill();
	mgraphics.set_source_rgba([0.95, 0.95, 1, 1]); mgraphics.set_font_size(11);
	mgraphics.move_to(mx + 23, y + h - 4);
	mgraphics.show_text(valTxt);
	chip(rx, y, 16, h, false, '▶', 10);
	arr.push({ x: rx, y: y, w: 16, h: h, step: 1, tag: tag });
}

// arrow keys nudge the (horizontal) morph slider once it's been clicked. Max passes 28/29/30/31.
function key(k) {
	if (!_morphFocus || !mprev.on) return;
	k = Math.round(k);
	var d = 0;
	if (k === 28) d = -0.02; else if (k === 29) d = 0.02;
	else if (k === 31) d = -0.10; else if (k === 30) d = 0.10;
	if (!d) return;
	var t = Math.max(0, Math.min(1, mprev.x + d));
	mprev.x = t;
	outlet(0, 'setmorph', t);
	mgraphics.redraw();
}

// route a stepper hit (from geo.glob) to the engine
function globStep(tag, d) {
	if (tag === 'm') outlet(0, 'setm', Math.max(1, Math.min(24, glob.m + d)));
	else if (tag === 'n') outlet(0, 'setn', Math.max(0, Math.min(24, glob.n + d)));
	else if (tag === 'levels') outlet(0, 'setlevels', Math.max(1, Math.min(6, glob.levels + d)));
	else if (tag === 'gprob') outlet(0, 'setglobalprob', Math.max(0, Math.min(100, glob.gprob + d * 5)));
	else if (tag === 'seed') outlet(0, 'setseed', Math.max(1, glob.seed + d));
	else if (tag === 'beats') outlet(0, 'setbeatsperperiod', Math.max(1, Math.min(64, Math.round(glob.beats) + d)));
	else if (tag === 'r') outlet(0, 'setr', Math.max(1, Number((glob.r + d * rStep).toFixed(3))));
	mgraphics.redraw();
}

function onclick(x, y, but) {
	if (!but) return;
	if (ptIn(geo.tab, x, y)) { vizmode ^= 1; mgraphics.redraw(); return; }

	// sidebar tabs
	for (var si = 0; si < geo.sideTab.length; si++) {
		if (ptIn(geo.sideTab[si], x, y)) { sideTab = geo.sideTab[si].i; mgraphics.redraw(); return; }
	}

	// global steppers (M / N / niveles / prob / semilla / R / sync / beats) + the R step-size cycler
	for (var gi = 0; gi < geo.glob.length; gi++) {
		var ge = geo.glob[gi];
		if (!ptIn(ge, x, y)) continue;
		if (ge.step === undefined) {
			if (ge.tag === 'sync') outlet(0, 'setsynctempo', glob.sync ? 0 : 1);
			else if (ge.tag === 'rstep') rStep = R_STEPS[(R_STEPS.indexOf(rStep) + 1) % R_STEPS.length];
			mgraphics.redraw();
		} else {
			globStep(ge.tag, ge.step);
		}
		return;
	}

	// rhythm-selector strip: filter chips, reachable toggle, control row, then the cell grid
	for (var fi = 0; fi < geo.catFam.length; fi++) {
		if (ptIn(geo.catFam[fi], x, y)) { catfilter(geo.catFam[fi].val); return; }
	}
	if (ptIn(geo.catReach, x, y)) { catreach(catReachOnly ? 0 : 1); return; }
	if (ptIn(geo.catPrev, x, y)) { catstep(-1); return; }
	if (ptIn(geo.catNext, x, y)) { catstep(1); return; }
	if (ptIn(geo.catNum, x, y)) { _dragActive = 1; _dragBase = catTarget || 0; _dragY0 = y; return; }
	// MOS strip: mousedown starts a horizontal pan; a release that barely moved picks the cell
	if (ptIn(geo.catStrip, x, y)) {
		_catDrag = 1; _catDragX0 = x; _catScroll0 = catScroll; _catDragCell = -1;
		for (var ci = 0; ci < geo.cat.length; ci++) {
			if (ptIn(geo.cat[ci], x, y)) { _catDragCell = geo.cat[ci].view; break; }
		}
		return;
	}
	// click the "fijo, no morfea" readout -> drop all per-field overrides (back to pure A<->B)
	if (ptIn(geo.morphClear, x, y)) { outlet(0, 'clearmorphtouched'); mprev.over = []; mgraphics.redraw(); return; }
	// Morph tab: A/B ◀ ▶ steppers + the [→A]/[→B] target toggle
	for (var mi = 0; mi < geo.mSlot.length; mi++) {
		var ms = geo.mSlot[mi];
		if (!ptIn(ms, x, y)) continue;
		if (ms.tag === 'slotTarget') { slotTarget = ms.to; mgraphics.redraw(); return; }
		var mm = (frame.morph && frame.morph.length > 2) ? frame.morph : [0, mprev.a, mprev.b, 0];
		var cur = Math.round(ms.kind === 'a' ? mm[1] : mm[2]);
		var nv = Math.max(0, Math.min(PRESET_SLOTS, cur + ms.d));
		outlet(0, ms.kind === 'a' ? 'setmorpha' : 'setmorphb', nv);
		return;
	}
	// Morph tab preset strip: mousedown = pan; a release that barely moved assigns the cell's slot
	if (ptIn(geo.psetStrip, x, y)) {
		_psetDrag = 1; _psetDragX0 = x; _psetScroll0 = psetScroll; _psetDragCell = -999;
		for (var pi = 0; pi < geo.pset.length; pi++) {
			if (ptIn(geo.pset[pi], x, y)) { _psetDragCell = geo.pset[pi].slot; break; }
		}
		return;
	}
	if (mprev.on && ptIn(geo.morphTrack, x, y)) { _morphFocus = 1; _morphDrag = 1; applyMorphFromX(x); return; }

	_dragActive = 0; _morphDrag = 0; _morphFocus = 0;
	for (var i = 0; i < geo.lanes.length; i++) {
		var g = geo.lanes[i];
		if (ptIn(g.grp, x, y)) {                        // G box -> toggle the lane on / off
			var L = frame.lv[g.idx];
			L.on = L.on ? 0 : 1;
			outlet(0, 'setlevelon', g.idx + 1, L.on);
			mgraphics.redraw();
			return;
		}
		if (ptIn(g.grpCyc, x, y)) {                     // small chip -> cycle the level's group
			var L2 = frame.lv[g.idx];
			var ng = (L2.group % MAXLV) + 1;
			L2.group = ng;
			outlet(0, 'setlevelgroup', g.idx + 1, ng);
			mgraphics.redraw();
			return;
		}
		if (ptIn(g.uc, x, y)) {                         // U/C -> toggle complemented reading
			var L3 = frame.lv[g.idx];
			L3.uc = L3.uc ? 0 : 1;
			outlet(0, 'setleveluc', g.idx + 1, L3.uc);
			mgraphics.redraw();
			return;
		}
		if (ptIn(g.step, x, y)) {                       // pas -> cycle the reading step 1..8
			var L4 = frame.lv[g.idx];
			L4.step = L4.step >= 8 ? 1 : L4.step + 1;
			outlet(0, 'setlevelstep', g.idx + 1, L4.step);
			mgraphics.redraw();
			return;
		}
		if (ptIn(g.phase, x, y)) {                      // gir -> cycle the phase 0..15
			var L5 = frame.lv[g.idx];
			L5.phase = L5.phase >= 15 ? 0 : L5.phase + 1;
			outlet(0, 'setlevelphase', g.idx + 1, L5.phase);
			mgraphics.redraw();
			return;
		}
		if (ptIn(g.pitchDn, x, y) || ptIn(g.pitchUp, x, y)) {   // ♪-/♪+ -> nudge the level pitch
			var L6 = frame.lv[g.idx];
			var np = Math.max(0, Math.min(127, L6.pitch + (ptIn(g.pitchUp, x, y) ? 1 : -1)));
			L6.pitch = np; L6.pc = ((np % 12) + 12) % 12;
			outlet(0, 'setlevelpitch', g.idx + 1, np);
			mgraphics.redraw();
			return;
		}
	}
}

// drag: the "pulsos objetivo" readout scrubs the target count (vertical); the MOS strip pans
// (horizontal, tap = pick); the morph slider moves morphX (horizontal).
function ondrag(x, y, but) {
	if (_morphDrag) {
		if (!but) { _morphDrag = 0; mgraphics.redraw(); return; }
		applyMorphFromX(x);
		return;
	}
	if (_catDrag) {
		if (!but) {
			_catDrag = 0;
			if (Math.abs(x - _catDragX0) < 4 && _catDragCell >= 0) catpick(_catDragCell);
			mgraphics.redraw();
			return;
		}
		catScroll = _catScroll0 - (x - _catDragX0);
		mgraphics.redraw();
		return;
	}
	if (_psetDrag) {
		if (!but) {
			_psetDrag = 0;
			if (Math.abs(x - _psetDragX0) < 4 && _psetDragCell > -999) {
				outlet(0, slotTarget === 'a' ? 'setmorpha' : 'setmorphb', _psetDragCell);
			}
			mgraphics.redraw();
			return;
		}
		psetScroll = _psetScroll0 - (x - _psetDragX0);
		mgraphics.redraw();
		return;
	}
	if (!_dragActive) return;
	if (!but) { _dragActive = 0; return; }
	cattarget(_dragBase + Math.round((_dragY0 - y) / 4));
}

// --- paint --------------------------------------------------------------------------------
function fmtR(r) { return (Math.abs(r - 1) < 1e-6) ? 'iso' : ('r' + r.toFixed(2)); }
function markerText(L) {
	if (L.mkFam && L.mkFam !== '-' && L.mkLvl >= 0) return L.mkFam + ' L' + L.mkLvl;
	return '';
}

// ==============================================================================================
// Layout: a left SIDEBAR (compact info line -> tab bar -> the active tab's body -> accent strip)
// and a RIGHT area with the lanes / radial view. The sidebar is TABBED so its sections can't
// overlap on a short window: "Ritmos" (family chips + pulse row + a 2-row drag-scroll MOS grid),
// "Morph" (A/B steppers + a scrollable preset strip + the horizontal morphX slider), "Global"
// (M/N/niveles/prob/semilla/R + a paso cycler/sync/beats steppers).
// ==============================================================================================

var CAT_FAM_BTNS = [
	{ val: 'todas', label: 'Todas' }, { val: 'n', label: 'n' }, { val: 'phi', label: 'oro' },
	{ val: 'delta', label: 'plata' }, { val: 'sigma', label: 'bronce' }
];
function chip(x, y, w, hh, on, label, font) {
	mgraphics.set_source_rgba(on ? [0.30, 0.36, 0.46, 1] : [0.17, 0.17, 0.19, 1]);
	mgraphics.rectangle(x, y, w, hh);
	mgraphics.fill();
	mgraphics.set_source_rgba(on ? [1, 1, 1, 1] : [0.7, 0.7, 0.76, 1]);
	mgraphics.set_font_size(font || 10);
	mgraphics.move_to(x + 5, y + hh - Math.max(3, (hh - (font || 10)) / 2));
	mgraphics.show_text(label);
}

function paintModeTab(rx, rw) {
	var tw = 190, th = 20;
	geo.tab = { x: rx + rw - tw - 6, y: 6, w: tw, h: th };
	mgraphics.set_source_rgba([0.15, 0.15, 0.17, 1]);
	mgraphics.rectangle(geo.tab.x, geo.tab.y, tw, th);
	mgraphics.fill();
	mgraphics.select_font_face('Arial');
	mgraphics.set_font_size(11);
	mgraphics.set_source_rgba(vizmode === 0 ? [1, 1, 1, 1] : [0.5, 0.5, 0.55, 1]);
	mgraphics.move_to(geo.tab.x + 12, geo.tab.y + 14);
	mgraphics.show_text('carriles');
	mgraphics.set_source_rgba(vizmode === 1 ? [1, 1, 1, 1] : [0.5, 0.5, 0.55, 1]);
	mgraphics.move_to(geo.tab.x + 100, geo.tab.y + 14);
	mgraphics.show_text('collares');
}

// one compact line: cycle / ms / isochrony, plus a faint base-MOS line
function paintInfoBlock(x, w, y) {
	mgraphics.select_font_face('Arial');
	var iso = frame.iso;
	var isoTxt = (iso[2] || iso[0] < 0) ? 'sin iso' : ('iso L' + iso[0] + '·' + iso[1] + 'p');
	mgraphics.set_source_rgba([0.82, 0.82, 0.88, 1]);
	mgraphics.set_font_size(12);
	mgraphics.move_to(x, y + 12);
	mgraphics.show_text('ciclo ' + frame.cycle + '  ·  ' + Math.round(frame.period) + ' ms  ·  ' + isoTxt);
	mgraphics.set_source_rgba([0.5, 0.5, 0.56, 1]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(x, y + 25);
	mgraphics.show_text('MOS ' + catMN[0] + '/' + catMN[1] + '  ·  ' + catView.length + '/' + cat.length + ' ritmos');
	return y + 30;
}

// editable global controls (mirror the Live panel params). Values come from `viz vglob`; each
// stepper sends the matching set* to the engine. FIXED 3-row layout (the other two tabs are the
// ones that stretch to fill). R shows 3 decimals and steps by the `paso` cycler (0.001..0.25);
// Beats is integer-only.
function paintGlobals(x, w, y) {
	geo.glob = [];
	mgraphics.select_font_face('Arial');
	var rh = 24, gap = 6, cy = y + 4;
	var c3 = (w - 2 * gap) / 3;
	// row 1 — M · N · Niveles
	stepper(geo.glob, x, cy, c3, rh, 'M', '' + glob.m, 'm');
	stepper(geo.glob, x + c3 + gap, cy, c3, rh, 'N', '' + glob.n, 'n');
	stepper(geo.glob, x + 2 * (c3 + gap), cy, c3, rh, 'Niv', '' + glob.levels, 'levels');
	cy += rh + gap;
	// row 2 — Prob · R (+ paso cycler)
	var pasoW = 72;
	stepper(geo.glob, x, cy, c3, rh, 'Prob', glob.gprob + '%', 'gprob');
	stepper(geo.glob, x + c3 + gap, cy, w - c3 - gap - pasoW - gap, rh, 'R', glob.r.toFixed(3), 'r');
	chip(x + w - pasoW, cy, pasoW, rh, false, 'paso ' + rStep, 9);
	geo.glob.push({ x: x + w - pasoW, y: cy, w: pasoW, h: rh, tag: 'rstep' });
	cy += rh + gap;
	// row 3 — Semilla · Sync · Beats
	var syncW = 58;
	stepper(geo.glob, x, cy, c3, rh, 'Semilla', '' + glob.seed, 'seed');
	chip(x + c3 + gap, cy, syncW, rh, glob.sync, glob.sync ? 'sync●' : 'sync○', 10);
	geo.glob.push({ x: x + c3 + gap, y: cy, w: syncW, h: rh, tag: 'sync' });
	stepper(geo.glob, x + c3 + gap + syncW + gap, cy, w - c3 - gap - syncW - gap, rh, 'Beats', '' + Math.round(glob.beats), 'beats');
	return cy + rh + 6;
}

// one tight row: family chips + a compact "alcanz." toggle (hides the ∞ metallic rows)
function paintFilters(x, w, y) {
	geo.catFam = []; geo.catReach = null;
	mgraphics.select_font_face('Arial');
	var chH = 17, cx = x;
	for (var i = 0; i < CAT_FAM_BTNS.length; i++) {
		var b = CAT_FAM_BTNS[i];
		var cw = 12 + b.label.length * 6;
		chip(cx, y, cw, chH, catFam === b.val, b.label, 9);
		geo.catFam.push({ x: cx, y: y, w: cw, h: chH, val: b.val });
		cx += cw + 3;
	}
	var rw = 62;
	chip(cx, y, rw, chH, catReachOnly, 'alcanz.', 9);
	geo.catReach = { x: cx, y: y, w: rw, h: chH };
	return y + chH + 5;
}

function paintPulseRow(x, w, y) {
	geo.catPrev = geo.catNext = geo.catNum = null;
	var rh = 20;
	// ◀ ▶ walk the sorted list; the number box is the pulse-count target (click-drag to scrub).
	geo.catPrev = { x: x, y: y, w: 30, h: rh };
	chip(x, y, 30, rh, false, '◀', 12);
	geo.catNext = { x: x + 34, y: y, w: 30, h: rh };
	chip(x + 34, y, 30, rh, false, '▶', 12);

	var sr = cat[catSel];
	var pr = catPulseRange();
	var tgt = catTarget || (sr && !sr.capped ? sr.pulses : pr[0]);
	var nx = x + 74, nw = Math.min(200, x + w - nx);
	geo.catNum = { x: nx, y: y, w: nw, h: rh };
	mgraphics.set_source_rgba([0.14, 0.14, 0.16, 1]);
	mgraphics.rectangle(nx, y, nw, rh);
	mgraphics.fill();
	mgraphics.set_source_rgba([0.95, 0.95, 0.99, 1]);
	mgraphics.set_font_size(11);
	mgraphics.move_to(nx + 6, y + rh - 6);
	mgraphics.show_text(tgt + ' pulsos objetivo  (arrastra)');

	if (sr) {
		mgraphics.set_source_rgba([0.62, 0.62, 0.7, 1]);
		mgraphics.set_font_size(11);
		mgraphics.move_to(x, y + rh + 14);
		var famES = FAM_ES[sr.family] || sr.family;
		mgraphics.show_text('elegido:  ' + (sr.capped ? '∞  ' + famES : sr.pulses + ' pulsos  ·  ' + famES + ' L' + sr.isoLevel) + '   ·   r ' + sr.r.toFixed(3));
		if (mprev.on) {
			mgraphics.set_source_rgba([0.96, 0.76, 0.36, 1]);
			mgraphics.set_font_size(10);
			mgraphics.move_to(x, y + rh + 28);
			mgraphics.show_text('con morph activo: fija R encima de la mezcla (no cambia de preset)');
		}
	}
	return y + rh + (mprev.on ? 34 : 20);
}

// The MOS catalog as a 2-row grid (>= 10 cells per row), already sorted by shape (most
// isochronous -> least, metallic last). Fills column by column; drag it sideways to slide through
// all of them; ◀ ▶ / the pulse target move the selection and auto-scroll it into view.
function paintCatalogStrip(x, w, y, h) {
	geo.cat = [];
	geo.catStrip = { x: x, y: y, w: w, h: h };
	if (!catView.length) {
		mgraphics.set_source_rgba([0.45, 0.45, 0.5, 1]);
		mgraphics.set_font_size(11);
		mgraphics.move_to(x + 2, y + 18);
		mgraphics.show_text('(sin ritmos para este filtro)');
		return;
	}
	var ROWS = 2;
	var perRow = Math.max(10, Math.floor(w / 40));
	var cw = w / perRow;
	var ch = Math.max(28, Math.min(46, (h - 10) / ROWS));
	var cols = Math.ceil(catView.length / ROWS);
	var total = cols * cw;
	var maxScroll = Math.max(0, total - w);
	// scroll the selected cell into view ONCE, when the selection actually changes -- never on a
	// plain repaint, so a hand-pan stays exactly where the user left it (viz frames arrive ~8 Hz
	// and used to yank the strip back to the selected preset every frame).
	var selVp = catView.indexOf(catSel);
	if (selVp >= 0 && catSel !== _catSnappedSel && !_catDrag) {
		var scx = Math.floor(selVp / ROWS) * cw;
		if (scx < catScroll) catScroll = scx;
		else if (scx + cw > catScroll + w) catScroll = scx + cw - w;
		_catSnappedSel = catSel;
	}
	catScroll = Math.max(0, Math.min(maxScroll, catScroll));

	var numFont = Math.max(13, Math.min(22, Math.round(ch * 0.55)));
	for (var k = 0; k < catView.length; k++) {
		var col = Math.floor(k / ROWS), rw = k % ROWS;
		var cx = x + col * cw - catScroll;
		if (cx < x - 1 || cx + cw > x + w + 1) continue;     // off-strip / partial -> skip
		var cy = y + rw * ch;
		var row = cat[catView[k]];
		var tint = FAM_RGB[row.family] || [0.5, 0.5, 0.5];
		var mul = row.capped ? 0.42 : 0.72;
		mgraphics.set_source_rgba([tint[0] * mul, tint[1] * mul, tint[2] * mul, 1]);
		mgraphics.rectangle(cx + 0.5, cy + 0.5, cw - 2, ch - 2);
		mgraphics.fill();
		if (catView[k] === catSel) {
			var rPinned = (mprev.on && mprev.over && mprev.over.indexOf('r') >= 0);
			mgraphics.set_source_rgba(rPinned ? [0.96, 0.76, 0.36, 0.98] : [1, 1, 1, 0.97]);
			mgraphics.set_line_width(2);
			mgraphics.rectangle(cx + 1.5, cy + 1.5, cw - 4, ch - 4);
			mgraphics.stroke();
		}
		mgraphics.set_source_rgba([1, 1, 1, 1]);
		mgraphics.set_font_size(numFont);
		mgraphics.move_to(cx + 4, cy + ch - 13);
		mgraphics.show_text(row.capped ? '∞' : ('' + row.pulses));
		mgraphics.set_source_rgba([0.92, 0.92, 0.96, 0.75]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(cx + 4, cy + ch - 4);
		mgraphics.show_text('r' + row.r.toFixed(2));
		geo.cat.push({ x: cx, y: cy, w: cw - 2, h: ch, view: k });
	}
	if (maxScroll > 0) {
		var by = y + ROWS * ch + 3, bw = Math.max(24, w * w / total), bx = x + (w - bw) * (catScroll / maxScroll);
		mgraphics.set_source_rgba([0.2, 0.2, 0.23, 1]); mgraphics.rectangle(x, by, w, 4); mgraphics.fill();
		mgraphics.set_source_rgba([0.5, 0.5, 0.58, 1]); mgraphics.rectangle(bx, by, bw, 4); mgraphics.fill();
	}
}

function miniNecklace(cx, cy, rad, ons, col, glow) {
	mgraphics.set_line_width(1);
	mgraphics.set_source_rgba([0.32, 0.32, 0.37, 0.7]);
	mgraphics.arc(cx, cy, rad, 0, 2 * Math.PI);
	mgraphics.stroke();
	if (ons && ons.length > 1) {
		mgraphics.set_source_rgba([col[0], col[1], col[2], 0.5]);
		for (var k = 0; k < ons.length; k++) {
			var a = -Math.PI / 2 + 2 * Math.PI * ons[k];
			var xx = cx + rad * Math.cos(a), yy = cy + rad * Math.sin(a);
			if (k === 0) mgraphics.move_to(xx, yy); else mgraphics.line_to(xx, yy);
		}
		mgraphics.close_path();
		mgraphics.stroke();
	}
	for (var j = 0; j < (ons ? ons.length : 0); j++) {
		var a2 = -Math.PI / 2 + 2 * Math.PI * ons[j];
		mgraphics.set_source_rgba([col[0], col[1], col[2], 1]);
		mgraphics.ellipse(cx + rad * Math.cos(a2) - 1.6, cy + rad * Math.sin(a2) - 1.6, 3.2, 3.2);
		mgraphics.fill();
	}
	if (glow) {
		mgraphics.set_source_rgba([1, 1, 1, 0.5]);
		mgraphics.set_line_width(1.5);
		mgraphics.arc(cx, cy, rad + 2, 0, 2 * Math.PI);
		mgraphics.stroke();
	}
}

// The preset bank as a scrollable strip (same idea as the MOS grid): "act" (= current state /
// slot 0) then every filled slot as a cell. Drag to slide; a tap assigns the cell's slot to
// Morph A or B per the `slotTarget` toggle. Cells carrying the current A / B get a coloured ring.
function paintPresetStrip(x, y, w, h, curA, curB) {
	geo.pset = [];
	geo.psetStrip = { x: x, y: y, w: w, h: h };
	var items = [0];
	for (var i = 0; i < slotsFilled.length; i++) items.push(slotsFilled[i]);
	var cw = 40, total = items.length * cw, maxScroll = Math.max(0, total - w);
	psetScroll = Math.max(0, Math.min(maxScroll, psetScroll));
	for (var k = 0; k < items.length; k++) {
		var cx = x + k * cw - psetScroll;
		if (cx < x - 1 || cx + cw > x + w + 1) continue;
		var s = items[k];
		mgraphics.set_source_rgba(s === 0 ? [0.2, 0.2, 0.24, 1] : [0.24, 0.3, 0.4, 1]);
		mgraphics.rectangle(cx + 0.5, y + 0.5, cw - 2, h - 1);
		mgraphics.fill();
		if (s === curA) {
			mgraphics.set_source_rgba([0.5, 0.65, 0.98, 0.95]); mgraphics.set_line_width(2);
			mgraphics.rectangle(cx + 1.5, y + 1.5, cw - 4, h - 3); mgraphics.stroke();
		}
		if (s === curB) {
			mgraphics.set_source_rgba([0.98, 0.7, 0.5, 0.95]); mgraphics.set_line_width(2);
			mgraphics.rectangle(cx + 3.5, y + 3.5, cw - 8, h - 7); mgraphics.stroke();
		}
		mgraphics.set_source_rgba([1, 1, 1, 1]); mgraphics.set_font_size(s === 0 ? 11 : 14);
		mgraphics.move_to(cx + 5, y + h / 2 + 5);
		mgraphics.show_text(s === 0 ? 'act' : ('' + s));
		geo.pset.push({ x: cx, y: y, w: cw - 2, h: h, slot: s });
	}
	if (maxScroll > 0) {
		var by = y + h + 2, bw = Math.max(20, w * w / total), bx = x + (w - bw) * (psetScroll / maxScroll);
		mgraphics.set_source_rgba([0.2, 0.2, 0.23, 1]); mgraphics.rectangle(x, by, w, 3); mgraphics.fill();
		mgraphics.set_source_rgba([0.5, 0.5, 0.58, 1]); mgraphics.rectangle(bx, by, bw, 3); mgraphics.fill();
	}
}

// Pick the two ends of the morph (and start one) from the popup. Presets show as a scrollable
// strip like the Ritmos MOS grid: a "→A / →B" toggle says which end a cell assigns to. When a
// morph is armed it also draws the HORIZONTAL morphX slider (A left, B right, mezcla at morphX;
// click it, then arrow keys nudge it).
function paintMorphColumn(x, w, y, h) {
	mgraphics.select_font_face('Arial');
	geo.mSlot = []; geo.pset = []; geo.psetStrip = null;
	var mm = (frame.morph && frame.morph.length > 2) ? frame.morph : [0, mprev.a, mprev.b, 0];
	var curA = Math.round(mm[1]), curB = Math.round(mm[2]);

	mgraphics.set_source_rgba([0.6, 0.6, 0.68, 1]);
	mgraphics.set_font_size(11);
	mgraphics.move_to(x, y + 11);
	mgraphics.show_text(mprev.on
		? ('morfeando  A ⇄ B      x = ' + mprev.x.toFixed(2) + (mprev.lin ? '   (r lineal)' : ''))
		: 'morph  —  elige dos presets para A y B');

	// --- A / B value steppers (one row) --------------------------------------------------
	var rowH = 18, rowY = y + 17, cS = (w - 10) / 2;
	function slotStep(sx, kind, cur, col) {
		mgraphics.set_source_rgba(col); mgraphics.set_font_size(12);
		mgraphics.move_to(sx, rowY + rowH - 5);
		mgraphics.show_text(kind === 'a' ? 'A' : 'B');
		chip(sx + 14, rowY, 20, rowH, false, '◀', 11);
		geo.mSlot.push({ x: sx + 14, y: rowY, w: 20, h: rowH, kind: kind, d: -1 });
		mgraphics.set_source_rgba([0.16, 0.16, 0.19, 1]);
		mgraphics.rectangle(sx + 37, rowY, cS - 74, rowH); mgraphics.fill();
		mgraphics.set_source_rgba([0.96, 0.96, 1, 1]); mgraphics.set_font_size(12);
		mgraphics.move_to(sx + 44, rowY + rowH - 5);
		mgraphics.show_text(cur === 0 ? 'act' : ('' + cur));
		chip(sx + cS - 34, rowY, 20, rowH, false, '▶', 11);
		geo.mSlot.push({ x: sx + cS - 34, y: rowY, w: 20, h: rowH, kind: kind, d: 1 });
	}
	slotStep(x, 'a', curA, [0.68, 0.78, 0.98, 1]);
	slotStep(x + cS + 10, 'b', curB, [0.98, 0.78, 0.62, 1]);

	// --- preset strip: "→A / →B" toggle + a scrollable row of slot cells ------------------
	var tgY = rowY + rowH + 6, tgH = 15;
	mgraphics.set_source_rgba([0.55, 0.55, 0.62, 1]); mgraphics.set_font_size(10);
	mgraphics.move_to(x, tgY + tgH - 4); mgraphics.show_text('presets  →');
	chip(x + 62, tgY, 26, tgH, slotTarget === 'a', 'A', 10);
	geo.mSlot.push({ x: x + 62, y: tgY, w: 26, h: tgH, tag: 'slotTarget', to: 'a' });
	chip(x + 90, tgY, 26, tgH, slotTarget === 'b', 'B', 10);
	geo.mSlot.push({ x: x + 90, y: tgY, w: 26, h: tgH, tag: 'slotTarget', to: 'b' });

	var psY = tgY + tgH + 4, psH = 34;
	paintPresetStrip(x, psY, w, psH, curA, curB);

	if (!mprev.on) {
		mgraphics.set_source_rgba([0.5, 0.5, 0.56, 1]);
		mgraphics.set_font_size(10);
		mgraphics.move_to(x, psY + psH + 16);
		mgraphics.show_text(slotsFilled.length
			? 'toca un preset para ponerlo en ' + (slotTarget === 'a' ? 'A' : 'B') + '  ·  act = estado actual'
			: 'sin presets — guarda con «Guardar» en el panel del device');
		geo.morphTrack = null;
		geo.morphClear = null;
		return;
	}
	// --- the HORIZONTAL morphX slider (fixed band under the preset strip; the tab can be tall) --
	var overN = mprev.over.length ? 1 : 0;
	var bandTop = psY + psH + 22;
	var bandBot = Math.min(y + h - 20 - overN * 14, bandTop + 96);
	var rad = Math.max(12, Math.min(28, (bandBot - bandTop) / 2 - 6));
	var ty = bandTop + rad + 4;
	var ax = x + rad + 6, bx = x + w - rad - 6;
	var mx = ax + (bx - ax) * Math.max(0, Math.min(1, mprev.x));

	geo.morphTrack = { x: ax - rad - 4, y: ty - rad - 6, w: (bx - ax) + 2 * rad + 8,
		h: 2 * rad + 30, ax: ax, bx: bx };

	if (_morphFocus) {
		mgraphics.set_source_rgba([0.4, 0.6, 0.95, 0.5]); mgraphics.set_line_width(1);
		mgraphics.rectangle(geo.morphTrack.x, geo.morphTrack.y, geo.morphTrack.w, geo.morphTrack.h);
		mgraphics.stroke();
	}
	mgraphics.set_source_rgba([0.3, 0.3, 0.36, 1]);
	mgraphics.set_line_width(3);
	mgraphics.move_to(ax, ty); mgraphics.line_to(bx, ty); mgraphics.stroke();
	mgraphics.set_source_rgba([0.44, 0.44, 0.52, 1]);
	for (var t = 0; t <= 1.001; t += 0.25) {
		var tx = ax + (bx - ax) * t;
		var big = (t < 0.01 || t > 0.99 || Math.abs(t - 0.5) < 0.01);
		mgraphics.set_line_width(big ? 2 : 1);
		mgraphics.move_to(tx, ty - (big ? 8 : 4)); mgraphics.line_to(tx, ty + (big ? 8 : 4)); mgraphics.stroke();
	}

	if (mprev.s[0]) miniNecklace(ax, ty, rad, mprev.s[0].ons, [0.55, 0.7, 0.95], false);
	if (mprev.s[1]) miniNecklace(bx, ty, rad, mprev.s[1].ons, [0.95, 0.7, 0.5], false);
	if (mprev.s[2]) miniNecklace(mx, ty, rad + 4, mprev.s[2].ons, [1, 1, 1], true);
	mgraphics.set_source_rgba([1, 1, 1, _morphDrag ? 0.95 : 0.55]);
	mgraphics.set_line_width(_morphDrag ? 3 : 2);
	mgraphics.arc(mx, ty, rad + 9, 0, 2 * Math.PI);
	mgraphics.stroke();

	mgraphics.set_font_size(10);
	function endLbl(lx, right, tag, p, col) {
		mgraphics.set_source_rgba(col);
		var s = p ? (tag + '  r' + p.r.toFixed(2) + '  ' + p.m + '/' + p.n) : tag;
		mgraphics.move_to(right ? (lx - s.length * 5.4) : lx, ty + rad + 14);
		mgraphics.show_text(s);
	}
	endLbl(ax - rad, false, 'A·' + (curA === 0 ? 'act' : curA), mprev.s[0], [0.68, 0.78, 0.98, 1]);
	endLbl(bx + rad, true, 'B·' + (curB === 0 ? 'act' : curB), mprev.s[1], [0.98, 0.78, 0.62, 1]);
	mgraphics.set_source_rgba([1, 1, 1, 1]);
	mgraphics.move_to(x, ty - rad - 12);
	mgraphics.show_text('mezcla (suena)' + (mprev.s[2] ? '  r' + mprev.s[2].r.toFixed(2) : '') + '    ← → teclado');

	if (overN) {
		var names = [];
		for (var oi = 0; oi < mprev.over.length && names.length < 8; oi++) {
			names.push(OVER_ES[mprev.over[oi]] || mprev.over[oi]);
		}
		var otxt = 'fijo (clic = soltar):  ' + names.join(',  ');
		if (otxt.length > 52) otxt = otxt.slice(0, 51) + '…';
		var oy = ty + rad + 32;
		mgraphics.set_source_rgba([0.96, 0.76, 0.36, 1]);
		mgraphics.set_font_size(10);
		mgraphics.move_to(x, oy);
		mgraphics.show_text(otxt);
		geo.morphClear = { x: x, y: oy - 12, w: w, h: 16 };
	} else {
		geo.morphClear = null;
	}
}

function applyMorphFromX(xx) {
	var g = geo.morphTrack;
	if (!g) return;
	var t = (xx - g.ax) / Math.max(1, g.bx - g.ax);
	t = Math.max(0, Math.min(1, t));
	mprev.x = t;                 // instant local feedback; the engine echoes it back next frame
	outlet(0, 'setmorph', t);
	mgraphics.redraw();
}

function paintAccentStrip(x0, W, y, h) {
	var n = 16, cw = W / n;
	for (var k = 0; k < n; k++) {
		var on = frame.grid[k];
		if (k < frame.readLen) mgraphics.set_source_rgba(on ? [0.95, 0.55, 0.2, 1] : [0.28, 0.28, 0.3, 1]);
		else mgraphics.set_source_rgba(on ? [0.5, 0.32, 0.16, 1] : [0.16, 0.16, 0.17, 1]);
		mgraphics.rectangle(x0 + k * cw + 0.5, y, Math.max(1, cw - 1), h);
		mgraphics.fill();
	}
	mgraphics.set_source_rgba([0.55, 0.55, 0.6, 1]);
	mgraphics.set_font_size(10);
	mgraphics.move_to(x0 + 2, y - 3);
	mgraphics.show_text('acentos  (lectura ' + frame.readLen + ')');
	mgraphics.set_source_rgba([1, 1, 1, 0.5]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(x0 + frame.readLen * cw, y);
	mgraphics.line_to(x0 + frame.readLen * cw, y + h);
	mgraphics.stroke();
}

function paintSideTabs(x, w, y) {
	geo.sideTab = [];
	var tw = w / SIDE_TABS.length, th = 20;
	mgraphics.select_font_face('Arial');
	for (var i = 0; i < SIDE_TABS.length; i++) {
		var tx = x + i * tw, on = (sideTab === i);
		mgraphics.set_source_rgba(on ? [0.24, 0.28, 0.36, 1] : [0.14, 0.14, 0.16, 1]);
		mgraphics.rectangle(tx + 1, y, tw - 2, th);
		mgraphics.fill();
		mgraphics.set_source_rgba(on ? [1, 1, 1, 1] : [0.55, 0.55, 0.6, 1]);
		mgraphics.set_font_size(11);
		mgraphics.move_to(tx + 10, y + 14);
		mgraphics.show_text(SIDE_TABS[i]);
		geo.sideTab.push({ x: tx, y: y, w: tw, h: th, i: i });
	}
	return y + th + 5;
}

function paintSidebar(SBW, H) {
	mgraphics.set_source_rgba([0.10, 0.10, 0.115, 1]);
	mgraphics.rectangle(0, 0, SBW, H);
	mgraphics.fill();
	mgraphics.set_source_rgba([0.05, 0.05, 0.06, 1]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(SBW - 0.5, 0); mgraphics.line_to(SBW - 0.5, H); mgraphics.stroke();

	// every tab body repopulates only its own geo.* arrays -- clear all first so a hidden tab's
	// hit-rects never linger.
	geo.catFam = []; geo.catReach = null; geo.catPrev = null; geo.catNext = null; geo.catNum = null;
	geo.cat = []; geo.catStrip = null; geo.glob = []; geo.mSlot = [];
	geo.pset = []; geo.psetStrip = null; geo.morphTrack = null; geo.morphClear = null;

	if (sideTab > SIDE_TABS.length - 1) sideTab = 0;

	var PADX = 10, iw = SBW - PADX * 2;
	var accH = 16, botY = H - accH - 4;
	var cursor = paintInfoBlock(PADX, iw, 6);
	cursor = paintSideTabs(PADX, iw, cursor + 3);

	// Global is a fixed band pinned just above the accent strip -- always visible, not a tab.
	var GLOBH = 98;
	var globTop = botY - 6 - GLOBH;
	var bodyBot = globTop - 16;

	if (sideTab === 1) {
		paintMorphColumn(PADX, iw, cursor + 2, bodyBot - (cursor + 2));
	} else {
		cursor = paintFilters(PADX, iw, cursor + 2);
		cursor = paintPulseRow(PADX, iw, cursor + 4);
		paintCatalogStrip(PADX, iw, cursor + 4, bodyBot - (cursor + 4));
	}

	mgraphics.set_source_rgba([0.45, 0.45, 0.5, 1]);
	mgraphics.select_font_face('Arial'); mgraphics.set_font_size(8);
	mgraphics.move_to(PADX, globTop - 4); mgraphics.show_text('GLOBAL');
	mgraphics.set_source_rgba([0.05, 0.05, 0.06, 1]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(PADX + 44, globTop - 7); mgraphics.line_to(SBW - PADX, globTop - 7); mgraphics.stroke();
	paintGlobals(PADX, iw, globTop);
	paintAccentStrip(PADX, iw, botY, accH);
}

function laneColor(L, mul) {
	var c = LV_RGB[L.lv % MAXLV];
	return [c[0] * mul, c[1] * mul, c[2] * mul, 1];
}

function paintLanes(W, H, top) {
	var n = Math.max(1, frame.count);
	var gutter = 150;
	var laneH = Math.max(26, (H - top - 4) / n);
	var tlX = gutter + 6, tlW = Math.max(20, W - tlX - 8);
	var period = frame.period || 1;
	geo.lanes = [];

	for (var i = 0; i < n; i++) {
		var L = frame.lv[i] || freshLevel(i);
		var y = top + i * laneH;
		var dim = L.on ? 1 : 0.4;

		// gutter background + swatch
		mgraphics.set_source_rgba([0.13, 0.13, 0.145, 1]);
		mgraphics.rectangle(0, y, gutter, laneH - 1);
		mgraphics.fill();
		var sw = pcSwatch(L.pc);
		mgraphics.set_source_rgba([sw[0] * dim, sw[1] * dim, sw[2] * dim, 1]);
		mgraphics.rectangle(3, y + 3, 10, 10);
		mgraphics.fill();

		mgraphics.set_font_size(12);
		mgraphics.set_source_rgba([0.85 * dim + 0.1, 0.85 * dim + 0.1, 0.88 * dim + 0.1, 1]);
		mgraphics.move_to(18, y + 13);
		var noct = Math.floor(L.pitch / 12) - 1;
		mgraphics.show_text('L' + (L.lv + 1) + '  ' + NN[L.pc] + noct + '  ' + fmtR(L.r));
		var mk = markerText(L);
		if (mk) {
			mgraphics.set_source_rgba([0.58, 0.58, 0.65, 1]);
			mgraphics.set_font_size(9);
			mgraphics.move_to(18, y + 24);
			mgraphics.show_text(mk);
		}

		// --- compact per-level control block (all frame-backed, so the popup shows live values) ---
		var cH = 15;
		var r1y = y + laneH - cH - 3;              // bottom row : G on/off · ▸ group · U/C reading
		var r2y = r1y - cH - 3;                    // upper row  : pas step · gir phase · ♪-/♪+ pitch
		var two = (laneH >= 66);
		var cy2 = two ? r2y : r1y;
		var grpR    = { x: 4,   y: r1y, w: 34, h: cH };
		var grpCycR = { x: 40,  y: r1y, w: 16, h: cH };
		var ucR     = { x: 58,  y: r1y, w: 24, h: cH };
		var stepR   = { x: 4,   y: cy2, w: 42, h: cH };
		var phaseR  = { x: 48,  y: cy2, w: 42, h: cH };
		var pDnR    = { x: 92,  y: cy2, w: 16, h: cH };
		var pUpR    = { x: 110, y: cy2, w: 16, h: cH };
		geo.lanes.push({ idx: i, grp: grpR, grpCyc: grpCycR, uc: ucR,
			step: two ? stepR : null, phase: two ? phaseR : null,
			pitchDn: two ? pDnR : null, pitchUp: two ? pUpR : null });

		var gc = LV_RGB[(L.group - 1) % MAXLV];
		mgraphics.set_source_rgba(L.on ? [gc[0] * 0.55, gc[1] * 0.55, gc[2] * 0.55, 1] : [0.16, 0.16, 0.17, 1]);
		mgraphics.rectangle(grpR.x, grpR.y, grpR.w, grpR.h);
		mgraphics.fill();
		mgraphics.set_source_rgba(L.on ? [0.95, 0.95, 0.97, 1] : [0.5, 0.5, 0.54, 1]);
		mgraphics.set_font_size(10);
		mgraphics.move_to(grpR.x + 4, grpR.y + 11);
		mgraphics.show_text('G' + L.group + (L.on ? '' : '·x'));
		chip(grpCycR.x, grpCycR.y, grpCycR.w, cH, false, '▸', 10);
		chip(ucR.x, ucR.y, ucR.w, cH, L.uc, L.uc ? 'C' : 'U', 10);
		if (two) {
			chip(stepR.x, stepR.y, stepR.w, cH, L.step > 1, 'pas' + L.step, 9);
			chip(phaseR.x, phaseR.y, phaseR.w, cH, L.phase > 0, 'gir' + L.phase, 9);
			chip(pDnR.x, pDnR.y, pDnR.w, cH, false, '♪-', 9);
			chip(pUpR.x, pUpR.y, pUpR.w, cH, false, '♪+', 9);
		}

		// timeline background
		mgraphics.set_source_rgba([0.10, 0.10, 0.11, 1]);
		mgraphics.rectangle(tlX, y + 1, tlW, laneH - 3);
		mgraphics.fill();

		// L/S word strip along the bottom of the lane
		if (L.word.length) {
			var sh = 4, sy = y + laneH - 6;
			var swc = tlW / L.word.length;
			for (var wI = 0; wI < L.word.length; wI++) {
				mgraphics.set_source_rgba(L.word[wI] ? [0.4, 0.4, 0.46, 1] : [0.22, 0.22, 0.26, 1]);
				mgraphics.rectangle(tlX + wI * swc + 0.3, sy, Math.max(1, swc - 0.6), sh);
				mgraphics.fill();
			}
		}

		// full onsets: faint ticks
		mgraphics.set_line_width(1);
		mgraphics.set_source_rgba([0.32, 0.32, 0.36, dim]);
		for (var f = 0; f < L.full.length; f++) {
			var xf = tlX + (L.full[f] / period) * tlW;
			mgraphics.move_to(xf, y + laneH - 8);
			mgraphics.line_to(xf, y + laneH - 3);
			mgraphics.stroke();
		}
		// dropped-by-Step onsets: ghost
		mgraphics.set_source_rgba([0.5, 0.42, 0.5, 0.3 * dim]);
		for (var d = 0; d < L.drop.length; d++) {
			var xd = tlX + (L.drop[d] / period) * tlW;
			mgraphics.rectangle(xd - 1.5, y + 6, 3, laneH - 16);
			mgraphics.fill();
		}
		// kept onsets: solid, accent brighter/orange
		for (var kI = 0; kI < L.kept.length; kI++) {
			var xk = tlX + (L.kept[kI][0] / period) * tlW;
			var acc = L.kept[kI][1];
			var col = acc ? [1, 0.6, 0.2, dim] : laneColor(L, dim);
			mgraphics.set_source_rgba(col);
			mgraphics.rectangle(xk - 1.5, y + 5, 3, laneH - 14);
			mgraphics.fill();
		}
		// pulse flash: brighten the kept onset nearest the playhead
		if (pulse[L.lv] > 0 && L.kept.length) {
			var ph = (phaseMs / period) * tlW + tlX;
			var best = 0, bd = 1e9;
			for (var q = 0; q < L.kept.length; q++) {
				var xq = tlX + (L.kept[q][0] / period) * tlW;
				if (Math.abs(xq - ph) < bd) { bd = Math.abs(xq - ph); best = xq; }
			}
			mgraphics.set_source_rgba([1, 1, 1, pulse[L.lv] * 0.8]);
			mgraphics.rectangle(best - 2.5, y + 3, 5, laneH - 10);
			mgraphics.fill();
		}

		mgraphics.set_source_rgba([0, 0, 0, 0.5]);
		mgraphics.set_line_width(1);
		mgraphics.move_to(0, y);
		mgraphics.line_to(W, y);
		mgraphics.stroke();
	}

	// playhead sweep across all lanes
	var px = tlX + (phaseMs / period) * tlW;
	mgraphics.set_source_rgba([1, 1, 1, 0.75]);
	mgraphics.set_line_width(1.5);
	mgraphics.move_to(px, top);
	mgraphics.line_to(px, top + n * laneH);
	mgraphics.stroke();
}

function paintRadial(W, H, top) {
	var n = Math.max(1, frame.count);
	var cx = W / 2, cy = top + (H - top) / 2;
	var rOuter = Math.max(30, Math.min(W, H - top) / 2 - 24);
	var rInner = Math.max(12, rOuter * 0.28);
	var period = frame.period || 1;
	geo.lanes = [];

	for (var i = 0; i < n; i++) {
		var L = frame.lv[i] || freshLevel(i);
		var rr = rInner + (rOuter - rInner) * (n === 1 ? 1 : i / (n - 1));
		var dim = L.on ? 1 : 0.35;

		// ring
		mgraphics.set_source_rgba([0.3, 0.3, 0.34, 0.5 * dim]);
		mgraphics.set_line_width(1);
		mgraphics.arc(cx, cy, rr, 0, 2 * Math.PI);
		mgraphics.stroke();

		// polygon through kept onsets
		if (L.kept.length > 1) {
			mgraphics.set_source_rgba(laneColor(L, 0.7 * dim));
			mgraphics.set_line_width(1.5);
			for (var k = 0; k < L.kept.length; k++) {
				var ang = -Math.PI / 2 + 2 * Math.PI * (L.kept[k][0] / period);
				var xx = cx + rr * Math.cos(ang), yy = cy + rr * Math.sin(ang);
				if (k === 0) mgraphics.move_to(xx, yy); else mgraphics.line_to(xx, yy);
			}
			mgraphics.close_path();
			mgraphics.stroke();
		}
		// kept onset dots (accent = orange)
		for (var d = 0; d < L.kept.length; d++) {
			var a2 = -Math.PI / 2 + 2 * Math.PI * (L.kept[d][0] / period);
			var dx = cx + rr * Math.cos(a2), dy = cy + rr * Math.sin(a2);
			mgraphics.set_source_rgba(L.kept[d][1] ? [1, 0.6, 0.2, dim] : laneColor(L, dim));
			mgraphics.ellipse(dx - 3, dy - 3, 6, 6);
			mgraphics.fill();
		}
		// dropped onsets: small hollow marks
		mgraphics.set_source_rgba([0.55, 0.45, 0.55, 0.5 * dim]);
		for (var g = 0; g < L.drop.length; g++) {
			var a3 = -Math.PI / 2 + 2 * Math.PI * (L.drop[g] / period);
			mgraphics.ellipse(cx + rr * Math.cos(a3) - 2, cy + rr * Math.sin(a3) - 2, 4, 4);
			mgraphics.stroke();
		}
		// pulse: ring glow
		if (pulse[L.lv] > 0) {
			mgraphics.set_source_rgba([1, 1, 1, pulse[L.lv] * 0.5]);
			mgraphics.set_line_width(2.5);
			mgraphics.arc(cx, cy, rr, 0, 2 * Math.PI);
			mgraphics.stroke();
		}
		// G box (on/off toggle) + small ▸ group-cycle chip at the ring's 3-o'clock edge
		var lx = cx + rr + 5, ly = cy - 9;
		var grpR = { x: lx, y: ly, w: 52, h: 17 };
		var grpCycR = { x: lx + 55, y: ly, w: 18, h: 17 };
		geo.lanes.push({ idx: i, grp: grpR, grpCyc: grpCycR });
		var gc = LV_RGB[(L.group - 1) % MAXLV];
		mgraphics.set_source_rgba(L.on ? [gc[0] * 0.55, gc[1] * 0.55, gc[2] * 0.55, 1] : [0.16, 0.16, 0.17, 1]);
		mgraphics.rectangle(grpR.x, grpR.y, grpR.w, grpR.h);
		mgraphics.fill();
		mgraphics.set_source_rgba(L.on ? [0.95, 0.95, 0.97, 1] : [0.5, 0.5, 0.54, 1]);
		mgraphics.set_font_size(10);
		mgraphics.move_to(grpR.x + 4, grpR.y + 13);
		mgraphics.show_text('G' + L.group + (L.on ? '' : ' ·off'));
		mgraphics.set_source_rgba([0.22, 0.22, 0.25, 1]);
		mgraphics.rectangle(grpCycR.x, grpCycR.y, grpCycR.w, grpCycR.h);
		mgraphics.fill();
		mgraphics.set_source_rgba([0.7, 0.7, 0.78, 1]);
		mgraphics.move_to(grpCycR.x + 5, grpCycR.y + 13);
		mgraphics.show_text('▸');
	}

	// playhead radius
	var pang = -Math.PI / 2 + 2 * Math.PI * (phaseMs / period);
	mgraphics.set_source_rgba([1, 1, 1, 0.8]);
	mgraphics.set_line_width(1.5);
	mgraphics.move_to(cx, cy);
	mgraphics.line_to(cx + (rOuter + 6) * Math.cos(pang), cy + (rOuter + 6) * Math.sin(pang));
	mgraphics.stroke();

	mgraphics.set_source_rgba([0.6, 0.6, 0.66, 1]);
	mgraphics.set_font_size(11);
	mgraphics.move_to(cx - 20, cy + 4);
	mgraphics.show_text(Math.round(frame.period) + ' ms');
}

function paint() {
	var wh = viewportWH();
	var W = wh[0], H = wh[1];

	mgraphics.set_source_rgba([0.11, 0.11, 0.12, 1]);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();

	var SBW = Math.max(360, Math.min(700, Math.round(W * 0.46)));
	paintSidebar(SBW, H);

	var RX = SBW, RW = W - SBW;
	paintModeTab(RX, RW);
	var top = 34;
	geo.lanes = [];

	mgraphics.translate(RX, 0);
	if (frame.count === 0) {
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_font_size(12);
		mgraphics.move_to(16, top + 28);
		mgraphics.show_text('Run on → los ritmos por nivel apareceran aqui.');
	} else if (vizmode === 0) {
		paintLanes(RW, H, top);
	} else {
		paintRadial(RW, H, top);
	}
	mgraphics.translate(-RX, 0);

	// lane / radial hit-rects are built in right-area local coords -- shift them to window coords
	var LANE_HIT = ['grp', 'grpCyc', 'uc', 'step', 'phase', 'pitchDn', 'pitchUp'];
	for (var gi = 0; gi < geo.lanes.length; gi++) {
		for (var hf = 0; hf < LANE_HIT.length; hf++) {
			var hr = geo.lanes[gi][LANE_HIT[hf]];
			if (hr) hr.x += RX;
		}
	}
}
