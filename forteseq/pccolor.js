// pccolor.js -- the shared colour <-> harmony module for the forteseq suite. Pure functions +
// a `node pccolor.js --check` harness. Meant to be `include("pccolor.js")`-d by a Max `js`
// object (functions are global on purpose) and `require`-d by node tests.
//
// The base map is the circle-of-fifths HSL wheel already used by tonnetz (v13) and ANIMIDI:
// hue given to C is `baseHue` (~220, blue), and each fifth advances the hue by 30 degrees, so
// hue = baseHue + ((pc*7) mod 12) * 30. Everything else is built on that:
//
//   pcToColor(pc, opts)        pitch class      -> {h,s,l, r,g,b}
//   mixColors(colors, model)   a stack of pc-colours -> one resultant colour   (sub|add|oklab)
//   colorToHarmony(color,opts) a colour -> {root, base, intervals, notes, dissonancePct, ...}
//   harmonyToColor(pcs, opts)  a set of pitch classes -> its blended colour signature
//   splitColor(target,k,model) a target colour  -> the k pitch classes whose blend is closest
//
// "sub" = per-channel multiply (pigment; complementary hues -> black = most dissonant).
// "add" = screen, 1 - prod(1 - c) (light; complementary hues -> white).
// "oklab" = average in OKLab (the honest perceptual mean; the legible default for a canvas).
//
// Dissonance % is Dosia McKay's model, identical to forteseq2.js / tonnetz: the raw
// interval-vector sum weighted by IC_DISSONANCE_MCKAY, as a percentage of the 12-tone set's 23.4.

var NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
var IC_DISSONANCE_MCKAY = [1 / 2, 1 / 5, 1 / 4, 1 / 3, 1 / 6, 1];   // ic1..ic6; sum for 12-tone = 23.4
var TWELVE_TONE_DISS = 23.4;

var _cbrt = Math.cbrt || function (x) { return x < 0 ? -Math.pow(-x, 1 / 3) : Math.pow(x, 1 / 3); };
function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
function mod(n, m) { return ((n % m) + m) % m; }
function noteName(pc) { return NOTE_NAMES[mod(Math.round(pc), 12)]; }

// --- HSL <-> RGB (all channels 0..1, hue in degrees) ---------------------------------------

function hue2rgb(p, q, t) {
	if (t < 0) t += 1;
	if (t > 1) t -= 1;
	if (t < 1 / 6) return p + (q - p) * 6 * t;
	if (t < 1 / 2) return q;
	if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
	return p;
}

function hslToRgb(h, s, l) {
	h = mod(h, 360) / 360;
	if (s === 0) return { r: l, g: l, b: l };
	var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
	var p = 2 * l - q;
	return { r: hue2rgb(p, q, h + 1 / 3), g: hue2rgb(p, q, h), b: hue2rgb(p, q, h - 1 / 3) };
}

function rgbToHsl(r, g, b) {
	var mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, h, s;
	if (mx === mn) { h = 0; s = 0; }
	else {
		var d = mx - mn;
		s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
		if (mx === r) h = (g - b) / d + (g < b ? 6 : 0);
		else if (mx === g) h = (b - r) / d + 2;
		else h = (r - g) / d + 4;
		h /= 6;
	}
	return { h: h * 360, s: s, l: l };
}

// --- sRGB <-> linear <-> OKLab (Bjorn Ottosson's matrices) --------------------------------

function srgbToLinear(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
function linearToSrgb(c) {
	c = c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(Math.max(0, c), 1 / 2.4) - 0.055;
	return clamp01(c);
}

function rgbToOklab(r, g, b) {
	var lr = srgbToLinear(r), lg = srgbToLinear(g), lb = srgbToLinear(b);
	var l = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb;
	var m = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb;
	var s = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb;
	var l_ = _cbrt(l), m_ = _cbrt(m), s_ = _cbrt(s);
	return {
		L: 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
		a: 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
		b: 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
	};
}

function oklabToRgb(o) {
	var l_ = o.L + 0.3963377774 * o.a + 0.2158037573 * o.b;
	var m_ = o.L - 0.1055613458 * o.a - 0.0638541728 * o.b;
	var s_ = o.L - 0.0894841775 * o.a - 1.2914855480 * o.b;
	var l = l_ * l_ * l_, m = m_ * m_ * m_, s = s_ * s_ * s_;
	return {
		r: linearToSrgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
		g: linearToSrgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
		b: linearToSrgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
	};
}

function oklabDist(c1, c2) {
	var a = rgbToOklab(c1.r, c1.g, c1.b), b = rgbToOklab(c2.r, c2.g, c2.b);
	var dL = a.L - b.L, da = a.a - b.a, db = a.b - b.b;
	return Math.sqrt(dL * dL + da * da + db * db);
}

// --- pitch class -> colour ----------------------------------------------------------------

// opts: { baseHue: 220, sat: 0.62, lum: 0.55 }. C gets baseHue; each fifth adds 30 degrees.
function pcToColor(pc, opts) {
	opts = opts || {};
	var baseHue = opts.baseHue == null ? 220 : opts.baseHue;
	var sat = opts.sat == null ? 0.62 : opts.sat;
	var lum = opts.lum == null ? 0.55 : opts.lum;
	var k = mod(Math.round(pc) * 7, 12);            // circle-of-fifths index
	var h = mod(baseHue + k * 30, 360);
	var rgb = hslToRgb(h, sat, lum);
	return { h: h, s: sat, l: lum, r: rgb.r, g: rgb.g, b: rgb.b };
}

// --- mixing -----------------------------------------------------------------------------

function mixColors(cols, model) {
	if (!cols || !cols.length) return { r: 0.5, g: 0.5, b: 0.5 };
	var n = cols.length, i;
	if (n === 1) return { r: cols[0].r, g: cols[0].g, b: cols[0].b };

	if (model === 'add') {                          // screen blend: 1 - prod(1 - c)
		var R = 1, G = 1, B = 1;
		for (i = 0; i < n; i++) { R *= 1 - cols[i].r; G *= 1 - cols[i].g; B *= 1 - cols[i].b; }
		return { r: clamp01(1 - R), g: clamp01(1 - G), b: clamp01(1 - B) };
	}
	if (model === 'oklab') {                        // perceptual mean
		var L = 0, A = 0, Bb = 0;
		for (i = 0; i < n; i++) { var o = rgbToOklab(cols[i].r, cols[i].g, cols[i].b); L += o.L; A += o.a; Bb += o.b; }
		return oklabToRgb({ L: L / n, a: A / n, b: Bb / n });
	}
	// 'sub' (default): per-channel multiply -- pigment; complementary hues collapse to black.
	var r = 1, g = 1, b = 1;
	for (i = 0; i < n; i++) { r *= cols[i].r; g *= cols[i].g; b *= cols[i].b; }
	return { r: clamp01(r), g: clamp01(g), b: clamp01(b) };
}

// --- interval vector + McKay dissonance -------------------------------------------------

function intervalVector(pcs) {
	var v = [0, 0, 0, 0, 0, 0], s = [], i, j;
	for (i = 0; i < pcs.length; i++) s.push(mod(pcs[i], 12));
	for (i = 0; i < s.length; i++) {
		for (j = i + 1; j < s.length; j++) {
			var d = mod(s[i] - s[j], 12);
			var ic = Math.min(d, 12 - d);
			if (ic >= 1 && ic <= 6) v[ic - 1]++;
		}
	}
	return v;
}

function dissonancePct(iv) {
	var sum = 0;
	for (var i = 0; i < 6; i++) sum += iv[i] * IC_DISSONANCE_MCKAY[i];
	return sum / TWELVE_TONE_DISS * 100;
}

// --- dissonance -> banded colour (threshold levels, for a discrete "how dissonant right now"
// readout rather than a continuous gradient) --------------------------------------------------

var DEFAULT_DISS_THRESHOLDS = [15, 35, 55, 75];   // dissonancePct breakpoints -> 5 bands (0..4)

// pcs -> { pct, band, nBands }. opts.thresholds overrides DEFAULT_DISS_THRESHOLDS.
function dissonanceBand(pcs, opts) {
	opts = opts || {};
	var thresholds = opts.thresholds || DEFAULT_DISS_THRESHOLDS;
	var pct = dissonancePct(intervalVector(pcs || []));
	var band = 0;
	for (var i = 0; i < thresholds.length; i++) if (pct >= thresholds[i]) band = i + 1;
	return { pct: pct, band: band, nBands: thresholds.length + 1 };
}

// band index (0 = most consonant .. nBands-1 = most dissonant) -> a colour sweeping hue from
// opts.consonantHue (default 200, cool) to opts.dissonantHue (default 20, warm).
function bandColor(band, nBands, opts) {
	opts = opts || {};
	var consonantHue = opts.consonantHue == null ? 200 : opts.consonantHue;
	var dissonantHue = opts.dissonantHue == null ? 20 : opts.dissonantHue;
	var sat = opts.sat == null ? 0.62 : opts.sat;
	var lum = opts.lum == null ? 0.55 : opts.lum;
	var t = nBands > 1 ? clamp01(band / (nBands - 1)) : 0;
	var h = mod(consonantHue + t * (dissonantHue - consonantHue), 360);
	var rgb = hslToRgb(h, sat, lum);
	return { h: h, s: sat, l: lum, r: rgb.r, g: rgb.g, b: rgb.b };
}

// --- colour -> harmony ----------------------------------------------------------------

// Consonance ladder, most consonant first. Saturation picks the rung: a pure resultant colour
// -> an open voicing; a muddy one -> a cluster. (dissonancePct rises monotonically down the list.)
var CHORD_LADDER = [
	{ ivs: [0, 7], name: '5' },
	{ ivs: [0, 4, 7], name: 'maj' },
	{ ivs: [0, 3, 7], name: 'min' },
	{ ivs: [0, 4, 7, 11], name: 'maj7' },
	{ ivs: [0, 3, 7, 10], name: 'm7' },
	{ ivs: [0, 5, 10], name: 'quartal' },
	{ ivs: [0, 2, 6, 9], name: 'add9 open' },
	{ ivs: [0, 1, 5, 8], name: 'tense' },
	{ ivs: [0, 1, 2, 3], name: 'cluster' }
];

// color: {r,g,b} 0..1.  opts.baseHue must match whatever produced the colour.
//  -> { root, base, octave, intervals, notes, name, intervalVector, dissonancePct }
function colorToHarmony(color, opts) {
	opts = opts || {};
	var baseHue = opts.baseHue == null ? 220 : opts.baseHue;
	var hsl = rgbToHsl(color.r, color.g, color.b);

	var k = mod(Math.round((hsl.h - baseHue) / 30), 12);   // circle-of-fifths index
	var root = mod(k * 7, 12);                              // inverse of pc -> k (7 is its own inverse mod 12)

	var idx = Math.round((1 - clamp01(hsl.s)) * (CHORD_LADDER.length - 1));
	var chord = CHORD_LADDER[idx];

	var octave = Math.round(2 + clamp01(hsl.l) * 5);        // 2..7
	var base = root + octave * 12;
	var notes = [];
	for (var i = 0; i < chord.ivs.length; i++) notes.push(base + chord.ivs[i]);

	var iv = intervalVector(chord.ivs);
	return {
		root: root, base: base, octave: octave,
		intervals: chord.ivs.slice(), notes: notes,
		name: noteName(root) + ' ' + chord.name,
		intervalVector: iv, dissonancePct: dissonancePct(iv)
	};
}

// --- harmony -> colour ----------------------------------------------------------------

function harmonyToColor(pcs, opts, model) {
	if (!pcs || !pcs.length) return { r: 0.5, g: 0.5, b: 0.5 };
	var cols = [];
	for (var i = 0; i < pcs.length; i++) cols.push(pcToColor(pcs[i], opts));
	return mixColors(cols, model || 'oklab');
}

// --- the inverse: which pitch classes blend to a target colour -----------------------

function combinations(n, k) {
	var out = [], idx = [];
	for (var i = 0; i < k; i++) idx.push(i);
	while (true) {
		out.push(idx.slice());
		var p = k - 1;
		while (p >= 0 && idx[p] === n - k + p) p--;
		if (p < 0) break;
		idx[p]++;
		for (var q = p + 1; q < k; q++) idx[q] = idx[q - 1] + 1;
	}
	return out;
}

// target: {r,g,b}.  -> { pcs:[...], color:{r,g,b}, dist } for the closest k-pc blend (OKLab distance).
function splitColor(target, k, model, opts) {
	k = Math.max(2, Math.min(6, Math.round(k || 3)));
	var best = null, bestD = Infinity;
	var combos = combinations(12, k);
	for (var i = 0; i < combos.length; i++) {
		var cols = [];
		for (var j = 0; j < k; j++) cols.push(pcToColor(combos[i][j], opts));
		var blend = mixColors(cols, model || 'oklab');
		var d = oklabDist(blend, target);
		if (d < bestD) { bestD = d; best = { pcs: combos[i].slice(), color: blend, dist: d }; }
	}
	return best;
}

if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		hslToRgb: hslToRgb, rgbToHsl: rgbToHsl, rgbToOklab: rgbToOklab, oklabToRgb: oklabToRgb,
		oklabDist: oklabDist, pcToColor: pcToColor, mixColors: mixColors,
		intervalVector: intervalVector, dissonancePct: dissonancePct,
		dissonanceBand: dissonanceBand, bandColor: bandColor,
		colorToHarmony: colorToHarmony, harmonyToColor: harmonyToColor, splitColor: splitColor,
		noteName: noteName, CHORD_LADDER: CHORD_LADDER
	};
}

// ================================================================================================
// node --check harness
// ================================================================================================

if (typeof require !== 'undefined' && typeof process !== 'undefined') {
	(function () {
		var failures = 0;
		function eq(got, want, label) {
			if (got !== want) { console.error('FAIL ' + label + ': got ' + got + ', want ' + want); failures++; }
		}
		function approxEq(got, want, label, eps) {
			eps = eps === undefined ? 1e-9 : eps;
			if (!(Math.abs(got - want) <= eps)) {
				console.error('FAIL ' + label + ': got ' + got + ', want ' + want + ' (diff ' + Math.abs(got - want) + ')');
				failures++;
			}
		}

		function checkWheel() {
			var f0 = failures;
			var opts = { baseHue: 220, sat: 0.6, lum: 0.55 };
			approxEq(pcToColor(0, opts).h, 220, 'C -> baseHue');
			approxEq(pcToColor(7, opts).h, 250, 'G (one fifth) -> baseHue + 30');
			approxEq(pcToColor(2, opts).h, 280, 'D (two fifths) -> baseHue + 60');
			approxEq(pcToColor(5, opts).h, 190, 'F (a fifth below C) -> baseHue - 30 (wraps)');
			// 12 distinct hues, 30 apart, covering the circle
			var seen = {};
			for (var pc = 0; pc < 12; pc++) seen[Math.round(pcToColor(pc, opts).h)] = 1;
			eq(Object.keys(seen).length, 12, '12 pitch classes -> 12 distinct hues');
			if (failures === f0) console.log('OK   checkWheel: circle-of-fifths hue map, C at baseHue, 30 deg per fifth.');
		}

		function checkColorRoundTrips() {
			var f0 = failures;
			var samples = [{ r: 0.8, g: 0.2, b: 0.35 }, { r: 0.1, g: 0.6, b: 0.9 }, { r: 0.5, g: 0.5, b: 0.5 }, { r: 0.95, g: 0.9, b: 0.2 }];
			for (var i = 0; i < samples.length; i++) {
				var c = samples[i];
				var hsl = rgbToHsl(c.r, c.g, c.b);
				var back = hslToRgb(hsl.h, hsl.s, hsl.l);
				approxEq(back.r, c.r, 'hsl round-trip r[' + i + ']', 1e-6);
				approxEq(back.g, c.g, 'hsl round-trip g[' + i + ']', 1e-6);
				approxEq(back.b, c.b, 'hsl round-trip b[' + i + ']', 1e-6);
				var ok = rgbToOklab(c.r, c.g, c.b);
				var rgb2 = oklabToRgb(ok);
				approxEq(rgb2.r, c.r, 'oklab round-trip r[' + i + ']', 1e-4);
				approxEq(rgb2.g, c.g, 'oklab round-trip g[' + i + ']', 1e-4);
				approxEq(rgb2.b, c.b, 'oklab round-trip b[' + i + ']', 1e-4);
			}
			// white -> OKLab ~ (1, 0, 0)
			var w = rgbToOklab(1, 1, 1);
			approxEq(w.L, 1, 'white OKLab L', 1e-3);
			approxEq(w.a, 0, 'white OKLab a', 1e-3);
			approxEq(w.b, 0, 'white OKLab b', 1e-3);
			if (failures === f0) console.log('OK   checkColorRoundTrips: HSL and OKLab conversions invert; white is neutral in OKLab.');
		}

		function checkMix() {
			var f0 = failures;
			var red = { r: 1, g: 0, b: 0 }, cyan = { r: 0, g: 1, b: 1 };
			var add = mixColors([red, cyan], 'add');
			approxEq(add.r, 1, 'add red+cyan -> white r'); approxEq(add.g, 1, 'add g'); approxEq(add.b, 1, 'add b');
			var sub = mixColors([red, cyan], 'sub');
			approxEq(sub.r, 0, 'sub red*cyan -> black r'); approxEq(sub.g, 0, 'sub g'); approxEq(sub.b, 0, 'sub b');
			var ok = mixColors([{ r: 0, g: 0, b: 0 }, { r: 1, g: 1, b: 1 }], 'oklab');
			var okl = rgbToOklab(ok.r, ok.g, ok.b);
			approxEq(okl.L, 0.5, 'oklab mean of black+white -> L 0.5', 1e-6);
			// single colour passes through; empty -> neutral grey
			var one = mixColors([red], 'sub');
			eq(one.r, 1, 'single-colour mix passes through');
			eq(mixColors([], 'add').r, 0.5, 'empty mix -> grey');
			if (failures === f0) console.log('OK   checkMix: add screens to white, sub multiplies to black, oklab averages perceptually.');
		}

		function checkDissonance() {
			var f0 = failures;
			// same three anchors forteseq2.js / tonnetz assert against
			approxEq(dissonancePct(intervalVector([0, 4, 7])), 3.2051282, 'major triad 3-11B diss %', 1e-5);
			approxEq(dissonancePct(intervalVector([0, 2, 4, 5, 7, 9, 11])), 25.641026, 'diatonic 7-35 diss %', 1e-5);
			var chrom = [];
			for (var i = 0; i < 12; i++) chrom.push(i);
			approxEq(dissonancePct(intervalVector(chrom)), 100, 'chromatic 12-1 diss %', 1e-9);
			var iv = intervalVector([0, 4, 7]);
			eq(iv.join(','), '0,0,1,1,1,0', 'major triad interval vector');
			if (failures === f0) console.log('OK   checkDissonance: interval vector + McKay % match the forteseq2/tonnetz anchors.');
		}

		function checkDissonanceBand() {
				var f0 = failures;
				// same three anchors checkDissonance() uses, now bucketed against the default thresholds
				eq(dissonanceBand([0, 4, 7]).band, 0, 'major triad (3.2%) -> band 0 (below first threshold)');
				eq(dissonanceBand([0, 2, 4, 5, 7, 9, 11]).band, 1, 'diatonic 7-35 (25.6%) -> band 1');
				var chrom = [];
				for (var i = 0; i < 12; i++) chrom.push(i);
				eq(dissonanceBand(chrom).band, 4, 'chromatic 12-1 (100%) -> band 4 (most dissonant)');
				eq(dissonanceBand([0, 4, 7]).nBands, 5, 'default thresholds -> 5 bands');
				// monotonic: raising pct never lowers the band
				var prevBand = -1, monotonic = true;
				for (var pct = 0; pct <= 100; pct += 1) {
					var b = 0;
					for (var t = 0; t < DEFAULT_DISS_THRESHOLDS.length; t++) if (pct >= DEFAULT_DISS_THRESHOLDS[t]) b = t + 1;
					if (b < prevBand) monotonic = false;
					prevBand = b;
				}
				if (!monotonic) { console.error('FAIL dissonanceBand not monotonic across threshold sweep'); failures++; }
				eq(dissonanceBand([]).band, 0, 'empty set -> 0% -> band 0');
				if (failures === f0) console.log('OK   checkDissonanceBand: threshold buckets are monotonic and match the McKay anchors.');
			}

			function checkBandColor() {
				var f0 = failures;
				var opts = { consonantHue: 200, dissonantHue: 20 };
				approxEq(bandColor(0, 5, opts).h, 200, 'band 0 -> consonantHue');
				approxEq(bandColor(4, 5, opts).h, 20, 'last band -> dissonantHue');
				approxEq(bandColor(2, 5, opts).h, 110, 'middle band -> midpoint hue');
				var prevH = null, monotonic = true;
				for (var band = 0; band < 5; band++) {
					var h = bandColor(band, 5, opts).h;
					if (prevH !== null && h > prevH) monotonic = false;   // consonantHue(200) -> dissonantHue(20): decreasing
					prevH = h;
				}
				if (!monotonic) { console.error('FAIL bandColor hue sweep not monotonic'); failures++; }
				if (failures === f0) console.log('OK   checkBandColor: hue sweeps monotonically from consonantHue to dissonantHue.');
			}

			function checkColorToHarmony() {
			var f0 = failures;
			var opts = { baseHue: 220 };
			// a colour built FROM pc 0 at full saturation, bright -> should read back root 0
			var c0 = pcToColor(0, { baseHue: 220, sat: 0.9, lum: 0.55 });
			var h0 = colorToHarmony(c0, opts);
			eq(h0.root, 0, 'colour of C -> root 0');
			eq(colorToHarmony(hslToRgb(220, 0.99, 0.5), opts).intervals.join(','), '0,7', 'near-pure saturation -> the open-fifth rung');
			// pc 7 (G)
			eq(colorToHarmony(pcToColor(7, { baseHue: 220, sat: 0.9, lum: 0.5 }), opts).root, 7, 'colour of G -> root 7');
			// low saturation -> more notes + higher dissonance than high saturation
			var hi = colorToHarmony(hslToRgb(220, 0.95, 0.5), opts);
			var lo = colorToHarmony(hslToRgb(220, 0.05, 0.5), opts);
			if (!(lo.intervals.length >= hi.intervals.length)) { console.error('FAIL low-sat should not have fewer notes'); failures++; }
			if (!(lo.dissonancePct > hi.dissonancePct)) { console.error('FAIL low-sat should be more dissonant'); failures++; }
			// lightness -> register
			var dark = colorToHarmony(hslToRgb(220, 0.6, 0.12), opts);
			var light = colorToHarmony(hslToRgb(220, 0.6, 0.92), opts);
			if (!(light.base > dark.base)) { console.error('FAIL lighter colour should sit higher'); failures++; }
			if (failures === f0) console.log('OK   checkColorToHarmony: hue->root, saturation->density, lightness->register.');
		}

		function checkInverse() {
			var f0 = failures;
			var opts = { baseHue: 220, sat: 0.62, lum: 0.55 };
			// harmonyToColor of a single pc == pcToColor of that pc
			var a = harmonyToColor([4], opts), b = pcToColor(4, opts);
			approxEq(a.r, b.r, 'harmonyToColor single pc r'); approxEq(a.g, b.g, 'g'); approxEq(a.b, b.b, 'b');
			// splitColor recovers a blend close to the target, and mixing its pcs reproduces it
			var target = harmonyToColor([0, 4, 7], opts, 'oklab');
			var sp = splitColor(target, 3, 'oklab', opts);
			if (!(sp.dist < 0.02)) { console.error('FAIL splitColor dist too large: ' + sp.dist); failures++; }
			var reblend = harmonyToColor(sp.pcs, opts, 'oklab');
			if (!(oklabDist(reblend, target) < 0.02)) { console.error('FAIL splitColor reblend not close'); failures++; }
			eq(sp.pcs.length, 3, 'splitColor returns k pcs');
			if (failures === f0) console.log('OK   checkInverse: harmonyToColor / splitColor round-trip within OKLab tolerance.');
		}

		function main() {
			checkWheel();
			checkColorRoundTrips();
			checkMix();
			checkDissonance();
			checkDissonanceBand();
			checkBandColor();
			checkColorToHarmony();
			checkInverse();
			if (failures === 0) { console.log('ALL OK'); process.exitCode = 0; }
			else { console.error(failures + ' failure(s)'); process.exitCode = 1; }
		}

		if (process.argv.indexOf('--check') !== -1 && require.main === module) main();
		else if (require.main === module) console.error('usage: node forteseq/pccolor.js --check');
	})();
}
