// Regression harness for forteseq2.js.
//
// The engine is a Max `js` script: it has no exports, it talks to the world through a global
// `outlet()`, and it draws on `Math.random` in three places (velocity inside a group's band, the
// rest coin, and the urn shuffle). All three are what make a musical difference, so the harness
// does not stub them out -- it seeds them, and a seeded run is reproducible to the atom.
//
// Everything here runs in a `vm` context whose globals are the stubs Max would provide, so
// forteseq2.js is loaded UNMODIFIED. Nothing in the engine knows it is under test.
//
//   node forteseq/test/harness.js --write    regenerate forteseq/test/golden.txt
//   node forteseq/test/harness.js --check    compare against it
//
// --check reports two things separately, and the distinction is the whole point:
//
//   * OUTLET 0 is the note bus. A change there means the device SOUNDS different. Any refactor
//     that claims to be behaviour-preserving must leave these lines byte for byte identical.
//   * OUTLETS 1-7 are readouts and control echoes. Optimising the hot path is expected to remove
//     messages here (that is precisely the saving), so a difference is reported but not fatal
//     unless --strict is passed.

'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// --engine <ruta> points the harness at another build -- typically `git show HEAD:...` written to
// a temp file -- so the same scenario can be run against two versions and timed side by side.
const engineArg = process.argv.indexOf('--engine');
const ENGINE = engineArg >= 0
	? path.resolve(process.argv[engineArg + 1])
	: path.join(__dirname, '..', 'forteseq2.js');
const GOLDEN = path.join(__dirname, 'golden.txt');

// ---------------------------------------------------------------------------------------------
// A seeded PRNG standing in for Math.random. mulberry32: small, fast, and good enough that a
// velocity band still looks random to the ear. The seed is fixed so two runs of the same build
// produce the same file.
// ---------------------------------------------------------------------------------------------
function mulberry32(seed) {
	let a = seed >>> 0;
	return function () {
		a = (a + 0x6D2B79F5) | 0;
		let t = Math.imul(a ^ (a >>> 15), 1 | a);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

// ---------------------------------------------------------------------------------------------
// The Max side, reduced to what the engine actually touches.
// ---------------------------------------------------------------------------------------------
function makeEngine(seed) {
	const log = [];

	// Math with a seeded random. The prototype chain keeps floor/abs/imul/... intact, so only
	// the one method the engine's musical choices depend on is replaced.
	const seededMath = Object.create(Math);
	seededMath.random = mulberry32(seed);

	const sandbox = {
		Math: seededMath,
		// One line per outlet message. Lists are flattened the way Max flattens them, so the line
		// reads like what a [print] would show.
		// Array.isArray, not `instanceof Array`: an array built inside the vm context has that
		// context's Array as its constructor, so `instanceof` compares against the wrong realm
		// and reports false for every list the engine sends. isArray is realm-safe.
		outlet: function (n, value) {
			const atoms = Array.isArray(value) ? value : [value];
			log.push(n + ' | ' + atoms.join(' '));
		},
		// The engine posts warnings and progress. Not part of the golden: it is chatter, and
		// tying the file to it would make every message reword into a false regression.
		post: function () {},
		// `File` is deliberately absent. savefavs()/loadfavs() both begin with
		// `if (typeof File === "undefined") return;` precisely so the engine runs off Max, and
		// leaving it undefined keeps the harness from writing to the real favourites file.
	};
	sandbox.global = sandbox;

	const ctx = vm.createContext(sandbox);
	vm.runInContext(fs.readFileSync(ENGINE, 'utf8'), ctx, { filename: 'forteseq2.js' });

	return { ctx, log };
}

// ---------------------------------------------------------------------------------------------
// The scenario. Each block sets some state, then runs N clock steps. Between blocks the log gets
// a marker so a diff says WHICH musical situation moved, instead of just "line 2143 changed".
//
// Coverage aimed at the paths a refactor could plausibly break: every reading order, every
// direction, both emit paths (shared and independent), chords with and without voice leading,
// every voicing, the filter, the drum path, the harmonic clock and the root sequences.
//
// ADD NEW BLOCKS AT THE END. A block inserted in the middle shifts the state every later block
// inherits -- cursors, patternStep, the PRNG -- so all of them rewrite themselves in golden.txt
// and the diff stops being readable as "these notes changed". Appended, the diff is purely
// additive and a regression anywhere earlier is impossible to miss.
// ---------------------------------------------------------------------------------------------
function runScenario(e) {
	const c = e.ctx;
	const mark = (name) => e.log.push('## ' + name);
	const run = (n) => { for (let i = 0; i < n; i++) c.bang(); };

	// A known starting point. Four voices, all sounding, in distinct registers, so every block
	// below exercises all four rather than one plus three mutes.
	c.setnumvoices(4);
	c.setbpmtrack(120);
	for (let v = 1; v <= 4; v++) {
		c.setvoicemute(v, 0);
		c.setvoiceexternal(v, 0);
		c.setvoicerange(v, 36 + v * 8, 24);
		c.setvoiceoctavesimple(v, 4, 0, 1, 0);
		c.setvoicephase(v, 0);
		c.setvoicedegoffset(v, 0);
		c.setvoicediv(v, 1);
	}

	// --- reading orders, shared clock, arpeggio ---------------------------------------------
	// Locked on a five-note set: the superpermutation branches need n <= 5 to reach their
	// tabulated minimal sequence, and a small set keeps a full pass short enough to see.
	c.setmode(1);
	c.setlock(1);
	c.setlockindex(120);
	for (let rm = 0; rm <= 6; rm++) {
		c.setreadmode(rm);
		for (let dir = 0; dir <= 2; dir++) {
			c.setreaddir(dir);
			mark('read=' + rm + ' dir=' + dir);
			run(40);
		}
	}

	// --- the coprime skip, which snaps to a coprime of the cardinality -----------------------
	c.setreadmode(4);
	c.setreaddir(0);
	for (const k of [1, 2, 3, 5, 7]) {
		c.setcoprime(k);
		mark('coprime=' + k);
		run(24);
	}
	c.setcoprime(2);

	// --- chords: every voicing, then voice leading on top ------------------------------------
	c.setmode(0);
	c.setlock(0);
	c.setreadmode(0);
	for (let vc = 0; vc <= 5; vc++) {
		c.setvoicing(vc);
		mark('voicing=' + vc);
		run(30);
	}
	c.setvoicing(0);
	c.setvoicelead(1);
	mark('voicelead');
	run(120);
	c.setvoicelead(0);

	// --- independent voices: own cursor, degree offset, clock divider ------------------------
	c.setvoiceindep(1);
	c.setvoicedegoffset(1, 0); c.setvoicedegoffset(2, 1);
	c.setvoicedegoffset(3, 2); c.setvoicedegoffset(4, 3);
	c.setvoicediv(1, 1); c.setvoicediv(2, 2); c.setvoicediv(3, 3); c.setvoicediv(4, 4);
	mark('indep acordes');
	run(60);
	c.setmode(1);
	mark('indep arpegio');
	run(120);
	c.setvoiceindep(0);
	for (let v = 1; v <= 4; v++) { c.setvoicedegoffset(v, 0); c.setvoicediv(v, 1); }

	// --- articulation: the grid, the euclidean generator, the two groups ---------------------
	c.setgroupvelmin(0, 50); c.setgroupvelmax(0, 84);
	c.setgroupvelmin(1, 96); c.setgroupvelmax(1, 120);
	c.setgroupdur(0, 16); c.setgroupdur(1, 4);
	c.setaccentgrid(1, 0, 0, 1, 0, 0, 1, 0);
	c.setaccentcycle(8);
	mark('grid dibujada');
	run(48);
	c.seteuclid(1);
	for (const k of [3, 5, 7]) {
		c.seteuclidk(k);
		for (const r of [0, 2]) {
			c.seteuclidrot(r);
			mark('euclid k=' + k + ' rot=' + r);
			run(24);
		}
	}
	c.seteuclid(0);
	c.setaccenttie(1);
	mark('ciclo atado a n');
	run(32);
	c.setaccenttie(0);
	// The silence presets are the one articulation control that rewrites another parameter.
	for (let sp = 1; sp <= 5; sp++) {
		c.setsilencepreset(sp);
		mark('silencio=' + sp);
		run(24);
	}
	c.setsilencepreset(1);

	// --- register: per-voice phase, then the orchestral templates ----------------------------
	c.setvoicephase(1, 0); c.setvoicephase(2, 2); c.setvoicephase(3, 4); c.setvoicephase(4, 6);
	mark('fases por voz');
	run(32);
	for (let t = 1; t <= 8; t++) {
		c.setrangetemplate(t);
		mark('rango=' + t);
		run(20);
	}
	c.setrangetemplate(1);
	// Octave patterns: base, range and step count interact, and the collision between the fixed
	// list and the generator lives here.
	c.setvoiceoctavesimple(1, 2, 2, 2, 0);
	c.setvoiceoctavesimple(2, 3, -1, 1, 1);
	c.setvoiceoctavesimple(3, 1, 4, 2, -1);
	mark('patrones de octava');
	run(40);
	for (let v = 1; v <= 4; v++) c.setvoiceoctavesimple(v, 4, 0, 1, 0);

	// --- the catalogue: traversal orders and the filter ---------------------------------------
	c.setlock(0);
	for (let om = 0; om <= 3; om++) {
		c.setorder(om);
		mark('orden=' + om);
		run(30);
	}
	c.setorder(0);
	c.setfilter(1);
	c.setcardmin(3); c.setcardmax(5);
	mark('filtro cardinalidad');
	run(40);
	// C major as an absolute mask, with the fit that lets a set move to where it satisfies it.
	c.setmask(1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1);
	for (let mm = 0; mm <= 2; mm++) {
		c.setmaskmode(mm);
		mark('mask modo=' + mm);
		run(24);
	}
	c.setmaskmode(0);
	c.setmaskfit(0);
	mark('mask sin ajuste');
	run(24);
	c.setmaskfit(1);
	// Vector conditions: no semitones, then must contain a tritone.
	c.setvecmax(1, 0);
	mark('vector ic1 max 0');
	run(30);
	c.setvecmax(1, 12);
	c.setvecmin(6, 1);
	mark('vector ic6 min 1');
	run(30);
	c.setvecmin(6, 0);
	c.setfilter(0);
	c.setcardmin(1); c.setcardmax(12);
	c.setmask(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1);

	// --- musicalidad: harmonic clock, root sequences, drum mode -------------------------------
	for (const r of [1, 4, 8]) {
		c.setharmrate(r);
		mark('harmrate=' + r);
		run(36);
	}
	c.setharmrate(0);
	for (let rs = 1; rs <= 9; rs++) {
		c.setrootseq(rs);
		mark('rootseq=' + rs);
		run(24);
	}
	c.setrootseq(0);
	for (const r of [0, 3, 7, -5]) {
		c.setroot(r);
		mark('root=' + r);
		run(20);
	}
	c.setroot(0);
	for (const o of [0, 1, -2]) {
		c.setmasteroctave(o);
		mark('masteroct=' + o);
		run(16);
	}
	c.setmasteroctave(0);
	c.setdrum(1);
	for (const b of [36, 48]) {
		c.setdrumbase(b);
		mark('drum base=' + b);
		run(24);
	}
	c.setdrum(0);

	// --- rotation, and the stack/unison action buttons -----------------------------------------
	c.setshape(1);
	mark('rot por set');
	run(30);
	c.setshape(0);
	c.stackvoices(1);
	mark('apilar');
	run(30);
	c.stackvoices(0);
	mark('unisono');
	run(20);

	// --- external triggering: the far end of the Hub's Enviar mode ------------------------------
	// Voices 3 and 4 go exclusive, so the shared clock must skip them entirely and only the
	// trigger must move their cursors.
	c.setvoiceexternal(3, 1);
	c.setvoiceexternal(4, 1);
	mark('externas');
	for (let i = 0; i < 48; i++) {
		c.bang();
		if (i % 2 === 0) c.trig(1, 3);
		if (i % 3 === 0) c.trig(1, 4);
		if (i % 5 === 0) c.trig(2, 3);   // wrong bus: must be dropped in silence
	}
	c.setvoiceexternal(3, 0);
	c.setvoiceexternal(4, 0);

	// --- voice count as a runtime value ---------------------------------------------------------
	for (const n of [1, 2, 3, 4]) {
		c.setnumvoices(n);
		for (let v = 1; v <= n; v++) c.setvoicemute(v, 0);
		mark('voces=' + n);
		run(20);
	}

	// --- Fase 5: the sub-clock ------------------------------------------------------------------
	// Sub 1 first, to pin the claim that the scheduler changes nothing when it has nothing to do.
	c.setsub(1);
	mark('sub=1 (identico al reloj cuadrado)');
	run(24);
	for (const sd of [2, 3, 4, 6, 8]) {
		c.setsub(sd);
		mark('sub=' + sd);
		run(24);
	}
	c.setsub(4);
	for (const sw of [50, 58, 66, 75]) {
		c.setswing(sw);
		mark('swing=' + sw);
		run(24);
	}
	c.setswing(50);
	for (const h of [25, 100]) {
		c.sethumanize(h);
		mark('humanize=' + h);
		run(24);
	}
	c.sethumanize(0);
	// Strum only bites on chords, so this block goes through Acordes.
	c.setmode(0);
	for (const sd of [0, 1, 2, 3]) {
		c.setstrumdir(sd);
		c.setstrum(1);
		mark('rasgueo dir=' + sd);
		run(20);
	}
	c.setstrum(0);
	c.setstrumdir(0);
	c.setmode(1);
	for (const rn of [2, 3, 4]) {
		c.setratchet(0, rn);
		c.setratchet(1, rn);
		for (const dec of [0, 60]) {
			c.setratchetdecay(dec);
			mark('ratchet=' + rn + ' caida=' + dec);
			run(20);
		}
	}
	c.setratchetprob(50);
	mark('ratchet prob=50');
	run(24);
	c.setratchetprob(100);
	c.setratchet(0, 1); c.setratchet(1, 1);
	c.setratchetdecay(0);
	// A fixed shove per voice, which is the one offset that is not random and not per step.
	for (let v = 1; v <= 4; v++) c.setvoicetimeoffset(v, v - 1);
	mark('desfase por voz');
	run(32);
	for (let v = 1; v <= 4; v++) c.setvoicetimeoffset(v, 0);
	// Everything back to square, so the block below is not read through a shifted grid.
	c.setsub(1);
	mark('vuelta a sub=1');
	run(16);

	// --- ritmo por voz ------------------------------------------------------------------
	// Coprime lengths, which is the case the feature exists for: 3 against 5 against 7 against
	// 8 only realigns after 840 steps, so every step in this block is a different combination
	// of which voices speak. Run long enough that a rebuild bug shows up as a stuck voice.
	c.setvoiceeuclen(1, 3); c.setvoiceeuck(1, 2);
	c.setvoiceeuclen(2, 5); c.setvoiceeuck(2, 3);
	c.setvoiceeuclen(3, 7); c.setvoiceeuck(3, 3);
	c.setvoiceeuclen(4, 8); c.setvoiceeuck(4, 5);
	mark('ritmo por voz, largos coprimos 3/5/7/8');
	run(64);
	// Rotation is what puts two voices with the same pattern out of phase with each other.
	for (let v = 1; v <= 4; v++) c.setvoiceeucrot(v, v);
	mark('ritmo por voz, girado');
	run(32);
	// Same block on the independent path, where the pattern is read against the steps the
	// divider actually hands the voice rather than against the clock.
	c.setvoiceindep(1);
	c.setvoicediv(2, 2); c.setvoicediv(3, 3);
	mark('ritmo por voz + indep + divisores');
	run(48);
	c.setvoicediv(2, 1); c.setvoicediv(3, 1);
	c.setvoiceindep(0);
	// k >= n is every cell, k = 0 is none: the two edges that must not throw.
	c.setvoiceeuclen(1, 4); c.setvoiceeuck(1, 9);
	c.setvoiceeuclen(2, 4); c.setvoiceeuck(2, 0);
	mark('ritmo por voz, bordes k>=n y k=0');
	run(16);
	for (let v = 1; v <= 4; v++) { c.setvoiceeuclen(v, 0); c.setvoiceeuck(v, 1); c.setvoiceeucrot(v, 0); }
	mark('ritmo por voz apagado');
	run(16);
}

// ---------------------------------------------------------------------------------------------

function generate(seed) {
	const e = makeEngine(seed);
	runScenario(e);
	return e.log;
}

function isNote(line) { return line.charCodeAt(0) === 48 /* '0' */ && line[1] === ' '; }

function report(golden, current) {
	const gN = golden.filter(isNote);
	const cN = current.filter(isNote);
	const gR = golden.filter((l) => !isNote(l) && l[0] !== '#');
	const cR = current.filter((l) => !isNote(l) && l[0] !== '#');

	const firstDiff = (a, b) => {
		const n = Math.min(a.length, b.length);
		for (let i = 0; i < n; i++) if (a[i] !== b[i]) return i;
		return a.length === b.length ? -1 : n;
	};

	const noteDiff = firstDiff(gN, cN);
	const readDiff = firstDiff(gR, cR);

	console.log('frames        ' + current.length + ' (golden ' + golden.length + ')');
	console.log('notas (out 0) ' + cN.length + ' (golden ' + gN.length + ')');
	console.log('readouts      ' + cR.length + ' (golden ' + gR.length + ')');
	console.log('');

	if (noteDiff === -1) {
		console.log('OK   las notas son identicas. Nada de lo que suena cambio.');
	} else {
		console.log('FALLA  la primera nota distinta es la ' + noteDiff + ':');
		console.log('  golden : ' + (gN[noteDiff] === undefined ? '(no hay mas)' : gN[noteDiff]));
		console.log('  ahora  : ' + (cN[noteDiff] === undefined ? '(no hay mas)' : cN[noteDiff]));
	}

	if (readDiff === -1) {
		console.log('OK   los readouts tambien son identicos.');
	} else {
		const delta = cR.length - gR.length;
		console.log('AVISO  los readouts difieren desde el ' + readDiff +
			' (' + (delta >= 0 ? '+' : '') + delta + ' mensajes).');
		console.log('       Es lo esperado al optimizar el camino caliente: menos mensajes es la mejora.');
		console.log('  golden : ' + (gR[readDiff] === undefined ? '(no hay mas)' : gR[readDiff]));
		console.log('  ahora  : ' + (cR[readDiff] === undefined ? '(no hay mas)' : cR[readDiff]));
	}

	return { noteDiff, readDiff };
}

function main() {
	const args = process.argv.slice(2);
	const seed = 20260819;

	if (args.indexOf('--write') >= 0) {
		const log = generate(seed);
		fs.writeFileSync(GOLDEN, log.join('\n') + '\n', 'utf8');
		const notes = log.filter(isNote).length;
		console.log('escrito ' + path.relative(process.cwd(), GOLDEN) +
			': ' + log.length + ' frames, ' + notes + ' notas');
		return;
	}

	if (args.indexOf('--check') >= 0) {
		if (!fs.existsSync(GOLDEN)) {
			console.error('no existe ' + GOLDEN + ' -- corre --write primero');
			process.exit(2);
		}
		// Split on either line ending. Git hands Windows checkouts CRLF, and a stray carriage
		// return on every line would report all 36748 frames as changed at once.
		const golden = fs.readFileSync(GOLDEN, 'utf8').replace(/\s+$/, '').split(/\r?\n/);
		const current = generate(seed);
		const r = report(golden, current);
		const strict = args.indexOf('--strict') >= 0;
		process.exit(r.noteDiff === -1 && (!strict || r.readDiff === -1) ? 0 : 1);
	}

	if (args.indexOf('--time') >= 0) {
		// Three runs, best of. The scenario is the same work the device does in Live, so the ratio
		// between two builds is the honest number; the absolute time is not, because Node's JIT is
		// nothing like the interpreter inside Max's js object.
		let best = Infinity;
		for (let i = 0; i < 3; i++) {
			const t = process.hrtime.bigint();
			generate(seed);
			const ms = Number(process.hrtime.bigint() - t) / 1e6;
			if (ms < best) best = ms;
		}
		console.log(path.basename(path.dirname(ENGINE)) + '/' + path.basename(ENGINE) +
			'  ' + best.toFixed(1) + ' ms');
		return;
	}

	console.log('uso: node forteseq/test/harness.js --write | --check [--strict] | --time [--engine <ruta>]');
	process.exit(2);
}

main();
