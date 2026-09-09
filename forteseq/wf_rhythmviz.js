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
// outlet 0 -> subpatcher outlet -> js forteseqwf.js inlet 0:  setlevelgroup <lv1> <g>  /
// setgroupchannel <g> <ch>  -- click a lane's "G" / "ch" label to reassign it.
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
var geo = { tab: null, lanes: [] };

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

// --- interaction: click a lane's G / ch label to reassign routing --------------------------
function ptIn(r, x, y) { return r && x >= r.x && y >= r.y && x < r.x + r.w && y < r.y + r.h; }

function onclick(x, y, but) {
	if (!but) return;
	if (ptIn(geo.tab, x, y)) { vizmode ^= 1; mgraphics.redraw(); return; }
	for (var i = 0; i < geo.lanes.length; i++) {
		var g = geo.lanes[i];
		if (ptIn(g.grp, x, y)) {
			var L = frame.lv[g.idx];
			var ng = (L.group % MAXLV) + 1;
			L.group = ng;
			outlet(0, 'setlevelgroup', g.idx + 1, ng);
			mgraphics.redraw();
			return;
		}
		if (ptIn(g.ch, x, y)) {
			var L2 = frame.lv[g.idx];
			var nc = (L2.channel % 16) + 1;
			for (var j = 0; j < frame.lv.length; j++) if (frame.lv[j].group === L2.group) frame.lv[j].channel = nc;
			outlet(0, 'setgroupchannel', L2.group, nc);
			mgraphics.redraw();
			return;
		}
	}
}

// --- paint --------------------------------------------------------------------------------
function fmtR(r) { return (Math.abs(r - 1) < 1e-6) ? 'iso' : ('r' + r.toFixed(2)); }
function markerText(L) {
	if (L.mkFam && L.mkFam !== '-' && L.mkLvl >= 0) return L.mkFam + ' L' + L.mkLvl;
	return '';
}

function paintHeader(W, hy) {
	mgraphics.set_source_rgba([0.09, 0.09, 0.10, 1]);
	mgraphics.rectangle(0, 0, W, hy);
	mgraphics.fill();
	mgraphics.select_font_face('Arial');
	mgraphics.set_font_size(9);
	mgraphics.set_source_rgba([0.66, 0.66, 0.72, 1]);
	mgraphics.move_to(4, 12);
	var iso = frame.iso;
	var isoTxt = (iso[2] || iso[0] < 0) ? 'no iso' : ('iso L' + iso[0] + ' / ' + iso[1] + ' pulsos');
	var txt = 'ciclo ' + frame.cycle + '    periodo ' + Math.round(frame.period) + ' ms   ' + isoTxt;
	if (frame.morph[0]) txt += '   morph ' + frame.morph[1] + '→' + frame.morph[2] + '  x=' + frame.morph[3].toFixed(2);
	mgraphics.show_text(txt);

	// mode tab (top-right, clickable)
	var tw = 132, th = 15;
	geo.tab = { x: W - tw - 4, y: 3, w: tw, h: th };
	mgraphics.set_source_rgba([0.16, 0.16, 0.18, 1]);
	mgraphics.rectangle(geo.tab.x, geo.tab.y, tw, th);
	mgraphics.fill();
	mgraphics.set_font_size(9);
	mgraphics.set_source_rgba(vizmode === 0 ? [1, 1, 1, 1] : [0.5, 0.5, 0.55, 1]);
	mgraphics.move_to(geo.tab.x + 8, geo.tab.y + 11);
	mgraphics.show_text('carriles');
	mgraphics.set_source_rgba(vizmode === 1 ? [1, 1, 1, 1] : [0.5, 0.5, 0.55, 1]);
	mgraphics.move_to(geo.tab.x + 68, geo.tab.y + 11);
	mgraphics.show_text('collares');
}

function paintAccentStrip(W, y, h) {
	var n = 16, cw = W / n;
	for (var k = 0; k < n; k++) {
		var on = frame.grid[k];
		if (k < frame.readLen) mgraphics.set_source_rgba(on ? [0.95, 0.55, 0.2, 1] : [0.28, 0.28, 0.3, 1]);
		else mgraphics.set_source_rgba(on ? [0.5, 0.32, 0.16, 1] : [0.16, 0.16, 0.17, 1]);
		mgraphics.rectangle(k * cw + 0.5, y, Math.max(1, cw - 1), h);
		mgraphics.fill();
	}
	mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
	mgraphics.set_font_size(8);
	mgraphics.move_to(4, y - 2);
	mgraphics.show_text('acentos  (lectura ' + frame.readLen + ')');
	// readLen boundary
	mgraphics.set_source_rgba([1, 1, 1, 0.5]);
	mgraphics.set_line_width(1);
	mgraphics.move_to(frame.readLen * cw, y);
	mgraphics.line_to(frame.readLen * cw, y + h);
	mgraphics.stroke();
}

function laneColor(L, mul) {
	var c = LV_RGB[L.lv % MAXLV];
	return [c[0] * mul, c[1] * mul, c[2] * mul, 1];
}

function paintLanes(W, H, top) {
	var n = Math.max(1, frame.count);
	var gutter = 128;
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

		mgraphics.set_font_size(9);
		mgraphics.set_source_rgba([0.85 * dim + 0.1, 0.85 * dim + 0.1, 0.88 * dim + 0.1, 1]);
		mgraphics.move_to(18, y + 12);
		mgraphics.show_text('L' + (L.lv + 1) + '  ' + NN[L.pc] + '  ' + fmtR(L.r));
		var mk = markerText(L);
		mgraphics.set_source_rgba([0.55, 0.55, 0.62, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(18, y + 24);
		mgraphics.show_text((mk ? mk + '  ' : '') + (L.uc ? 'C' : 'U') + (L.step > 1 ? '  /' + L.step : ''));

		// clickable G<group> and ch<channel>
		var grpR = { x: 4, y: y + laneH - 16, w: 40, h: 14 };
		var chR = { x: 48, y: y + laneH - 16, w: 54, h: 14 };
		geo.lanes.push({ idx: i, grp: grpR, ch: chR });
		var gc = LV_RGB[(L.group - 1) % MAXLV];
		mgraphics.set_source_rgba([gc[0] * 0.5, gc[1] * 0.5, gc[2] * 0.5, 1]);
		mgraphics.rectangle(grpR.x, grpR.y, grpR.w, grpR.h);
		mgraphics.fill();
		mgraphics.set_source_rgba([0.95, 0.95, 0.97, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(grpR.x + 4, grpR.y + 11);
		mgraphics.show_text('G' + L.group);
		mgraphics.set_source_rgba([0.2, 0.2, 0.22, 1]);
		mgraphics.rectangle(chR.x, chR.y, chR.w, chR.h);
		mgraphics.fill();
		mgraphics.set_source_rgba([0.8, 0.8, 0.85, 1]);
		mgraphics.move_to(chR.x + 4, chR.y + 11);
		mgraphics.show_text('→ ch ' + L.channel);

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
		// clickable G / ch label at the ring's 3-o'clock edge
		var lx = cx + rr + 4, ly = cy - 7;
		var grpR = { x: lx, y: ly, w: 26, h: 14 };
		var chR = { x: lx + 28, y: ly, w: 46, h: 14 };
		geo.lanes.push({ idx: i, grp: grpR, ch: chR });
		var gc = LV_RGB[(L.group - 1) % MAXLV];
		mgraphics.set_source_rgba([gc[0] * 0.55, gc[1] * 0.55, gc[2] * 0.55, 1]);
		mgraphics.rectangle(grpR.x, grpR.y, grpR.w, grpR.h);
		mgraphics.fill();
		mgraphics.set_source_rgba([0.95, 0.95, 0.97, 1]);
		mgraphics.set_font_size(8);
		mgraphics.move_to(grpR.x + 3, grpR.y + 11);
		mgraphics.show_text('G' + L.group);
		mgraphics.set_source_rgba([0.22, 0.22, 0.24, 1]);
		mgraphics.rectangle(chR.x, chR.y, chR.w, chR.h);
		mgraphics.fill();
		mgraphics.set_source_rgba([0.8, 0.8, 0.85, 1]);
		mgraphics.move_to(chR.x + 3, chR.y + 11);
		mgraphics.show_text('ch ' + L.channel);
	}

	// playhead radius
	var pang = -Math.PI / 2 + 2 * Math.PI * (phaseMs / period);
	mgraphics.set_source_rgba([1, 1, 1, 0.8]);
	mgraphics.set_line_width(1.5);
	mgraphics.move_to(cx, cy);
	mgraphics.line_to(cx + (rOuter + 6) * Math.cos(pang), cy + (rOuter + 6) * Math.sin(pang));
	mgraphics.stroke();

	mgraphics.set_source_rgba([0.6, 0.6, 0.66, 1]);
	mgraphics.set_font_size(9);
	mgraphics.move_to(cx - 34, cy + 3);
	mgraphics.show_text(Math.round(frame.period) + ' ms');
}

function paint() {
	var wh = viewportWH();
	var W = wh[0], H = wh[1];

	mgraphics.set_source_rgba([0.11, 0.11, 0.12, 1]);
	mgraphics.rectangle(0, 0, W, H);
	mgraphics.fill();

	var hy = 18;
	paintHeader(W, hy);
	var accY = hy + 12, accH = 14;
	paintAccentStrip(W, accY, accH);
	var top = accY + accH + 6;

	if (frame.count === 0) {
		mgraphics.set_source_rgba([0.5, 0.5, 0.55, 1]);
		mgraphics.set_font_size(11);
		mgraphics.move_to(12, top + 24);
		mgraphics.show_text('Run on -> los ritmos por nivel apareceran aqui.');
		return;
	}
	if (vizmode === 0) paintLanes(W, H, top);
	else paintRadial(W, H, top);
}
