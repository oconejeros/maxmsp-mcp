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
function makeEngine(seed, extraGlobals) {
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
		// `File` is deliberately absent by default. savefavs()/loadfavs()/savepresets()/
		// loadpresets() all begin with `if (typeof File === "undefined") return;` precisely so
		// the engine runs off Max, and leaving it undefined keeps the main scenario from writing
		// to any real file. checkPresetNames() passes its own in-memory stub via extraGlobals to
		// exercise the actual save/load round trip without touching disk.
	};
	if (extraGlobals) for (const k in extraGlobals) sandbox[k] = extraGlobals[k];
	sandbox.global = sandbox;

	const ctx = vm.createContext(sandbox);
	vm.runInContext(fs.readFileSync(ENGINE, 'utf8'), ctx, { filename: 'forteseq2.js' });

	return { ctx, log };
}

// In-memory stand-in for Max's `File` object, just enough of it for savepresets()/loadpresets():
// write mode buffers writeline() calls and flushes to `store` on close(); read mode replays
// whatever is in `store` line by line. `position`/`eof` are line counts, not bytes -- the engine
// only ever compares them (`position < eof`), never reads them as an offset, so the unit doesn't
// have to match Max's as long as the ordering is right.
function makeFakeFile(store) {
	function FakeFile(pathArg, mode) {
		this._path = pathArg;
		this._mode = mode;
		if (mode === 'read') {
			const lines = store[pathArg];
			this.isopen = lines ? 1 : 0;
			this._lines = lines || [];
			this._idx = 0;
			this.position = 0;
			this.eof = this._lines.length;
		} else {
			this.isopen = 1;
			this._buf = [];
			this.position = 0;
			this.eof = 0;
		}
	}
	FakeFile.prototype.writeline = function (s) { this._buf.push(s); };
	FakeFile.prototype.readline = function () {
		if (this._idx >= this._lines.length) { this.position = this.eof; return ''; }
		this.position++;
		return this._lines[this._idx++];
	};
	FakeFile.prototype.close = function () { if (this._mode !== 'read') store[this._path] = this._buf; };
	return FakeFile;
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

	// --- camino armonico ----------------------------------------------------------------
	// The harmony on its own clock, so a set change happens every four steps and a block of 64
	// is sixteen of them -- enough for a curve to come round twice.
	c.setharmrate(4);
	c.setlink(3);
	mark('enlace: 3 tonos comunes');
	run(64);
	// Six common tones is unsatisfiable for most of the catalogue. What is being tested is the
	// fallback: the sequence must keep moving rather than freeze on one set.
	c.setlink(6);
	mark('enlace: 6, que casi nadie cumple');
	run(48);
	c.setlink(0);
	for (const shape of [0, 1, 2]) {
		c.settension(8);
		c.settenshape(shape);
		mark('tension: ciclo 8, forma ' + shape);
		run(48);
	}
	// The two rules together: the curve asks for a consonance, the link vetoes the sets that do
	// not hold enough in common, and the closest survivor wins.
	c.setlink(2);
	mark('tension + enlace');
	run(48);
	c.setlink(0);
	c.settension(0);
	// A curated progression. The sets are marked in a deliberate order and the sequence has to
	// play them in it, not in catalogue order -- which is the whole difference between a
	// progression and a filter.
	c.clearfavs();
	for (const s of [200, 40, 137, 88, 3]) { c.setlockindex(s); c.setfav(1); }
	c.setfavseq(1);
	mark('favoritos como progresion');
	run(48);
	// Unmarking one has to drop it out of the progression without disturbing the rest.
	c.setlockindex(137);
	c.setfav(0);
	mark('progresion con uno menos');
	run(32);
	c.setfavseq(0);
	c.clearfavs();
	c.setharmrate(0);
	mark('camino armonico apagado');
	run(16);

	// --- escuchar y responder -------------------------------------------------------------
	// A hand on the keys IS the harmony, so these blocks are about what the sequence does while
	// it is being told what to play and what it does when it is let go.
	c.setharmrate(4);
	const chord = (pitches, vel) => pitches.forEach((p) => c.noteheard(p, vel));
	c.setlisten(1);
	chord([60, 64, 67], 100);           // do mayor
	mark('escuchar Sigue: sosteniendo una triada mayor');
	run(32);
	chord([60, 64, 67], 0);
	mark('escuchar Sigue: soltada, la secuencia vuelve');
	run(24);
	c.setlisten(2);
	chord([62, 65, 69, 72], 100);       // re menor con septima
	chord([62, 65, 69, 72], 0);
	mark('escuchar Latch: agarrada y soltada');
	run(32);
	// A chord let go note by note must not be re-read on the way out, and a doubled octave must
	// not clear a pitch class that is still down. Both are silent failures if they regress.
	chord([60, 64, 67, 72], 100);
	c.noteheard(72, 0);
	c.noteheard(64, 0);
	mark('escuchar Latch: soltando de a una');
	run(16);
	c.listenpanic();
	c.setlisten(0);
	mark('escuchar apagado despues del panic');
	run(16);
	// Following: the clock stops choosing the harmony and the bus provides it.
	c.setfollow(1);
	mark('siguiendo el bus, sin que llegue nada');
	run(24);
	for (const s of [300, 12, 175]) {
		c.followset(c.busId, s);
		mark('el bus manda el set ' + s);
		run(16);
	}
	c.followset(c.busId + 1, 40);       // otro bus: no tiene que moverse
	mark('un set de otro bus, que se ignora');
	run(16);
	c.setfollow(0);
	c.setharmrate(0);
	mark('escuchar y responder apagados');
	run(16);

	// --- modulacion -------------------------------------------------------------------------
	// Depth 0 is what the whole file above already covers, so these blocks pin down the other
	// direction: that every destination actually moves, that two modulators aimed at one
	// destination add up, and -- the one that would fail silently -- that switching them all
	// off leaves nothing of the last sweep behind.
	c.setmode(1);
	c.setlock(1);
	c.setlockindex(120);
	c.setsub(1);
	for (let s = 0; s <= 5; s++) {
		c.setmodshape(1, s);
		c.setmodcycle(1, 8);
		c.setmodphase(1, 0);
		c.setmoddest(1, 1);            // Raiz, where a wrong number is audible as a wrong key
		c.setmoddepth(1, 100);
		mark('mod forma=' + s + ' sobre Raiz');
		run(24);
	}
	// The rest of the destinations, through the shape that sweeps rather than jumps.
	c.setmodshape(1, 0);
	c.setgroupsilence(0, 50);
	for (const d of [2, 3, 4, 5, 9]) {
		c.setmoddest(1, d);
		mark('mod destino=' + d);
		run(24);
	}
	c.setgroupsilence(0, 0);
	// The three that need a sub-clock before they have anywhere to put themselves.
	c.setsub(4);
	c.setswing(60);
	c.setmoddest(1, 6);
	mark('mod sobre Swing');
	run(24);
	c.setswing(50);
	c.setmode(0);
	c.setstrum(2);
	c.setmoddest(1, 7);
	mark('mod sobre Rasgueo');
	run(20);
	c.setstrum(0);
	c.setmode(1);
	c.setratchet(0, 3);
	c.setratchet(1, 3);
	c.setratchetprob(50);
	c.setmoddest(1, 8);
	mark('mod sobre Ratchet');
	run(24);
	c.setratchet(0, 1);
	c.setratchet(1, 1);
	c.setratchetprob(100);
	c.setsub(1);
	// A negative depth turns the shape over rather than doing nothing.
	c.setmoddest(1, 1);
	c.setmoddepth(1, -100);
	mark('mod prof negativa');
	run(24);
	// Two on one destination, on cycles that do not divide each other, so the sum never repeats
	// inside the block -- which is what a last-writer-wins bug would show up as.
	c.setmoddepth(1, 60);
	c.setmodshape(2, 1);
	c.setmodcycle(2, 5);
	c.setmodphase(2, 25);
	c.setmoddest(2, 1);
	c.setmoddepth(2, 40);
	mark('dos moduladores sobre Raiz, ciclos 8 y 5');
	run(40);
	// All four, each somewhere else, including both random shapes.
	c.setmodshape(3, 4);
	c.setmodcycle(3, 3);
	c.setmoddest(3, 3);
	c.setmoddepth(3, 70);
	c.setmodshape(4, 5);
	c.setmodcycle(4, 16);
	c.setmoddest(4, 9);
	c.setmoddepth(4, 100);
	mark('los cuatro a la vez');
	run(48);
	for (let k = 1; k <= 4; k++) {
		c.setmoddepth(k, 0);
		c.setmoddest(k, 0);
	}
	mark('modulacion apagada');
	run(24);

	// --- presets ---------------------------------------------------------------------------
	// Off Max there is no Live API and no File, and both halves of the preset system are meant
	// to notice that and do nothing rather than throw. That is worth pinning down here because
	// an exception inside a js object stops the script dead in Live -- the sequencer would go
	// silent, and the only clue would be one line in the console.
	c.setpresetslot(3);
	c.storepreset();
	c.recallpreset();
	c.recallpreset(2);
	c.clearpreset(3);
	c.setpresetslot(99);          // se recorta al ultimo slot, no explota
	c.storepreset(0);             // fuera de rango: se rechaza
	c.loadpresets();
	c.savepresets();
	c.presetrescan();
	mark('presets sin Live: inertes');
	run(16);

	// --- McKay: el quinto Orden y el Modelo de la curva de tension ---------------------------
	// checkMcKay() (mas abajo) ya fija los tres valores exactos del libro contra un motor limpio;
	// esto en cambio deja el modo funcionando dentro de una corrida real, para que un cambio que
	// rompa harmonyValueOf() o dissonanceOf() sin lanzar excepcion igual se note en el golden.
	c.setorder(4);
	mark('orden McKay: del mas consonante al cromatico completo');
	run(24);
	c.setfilter(1);
	c.setcardmin(3);
	c.setcardmax(7);
	c.settensmodel(1);
	c.settension(8);
	c.settenshape(2);
	mark('curva de tension con el modelo McKay, forma arco');
	run(32);
	c.settension(0);
	c.settensmodel(0);
	c.setfilter(0);
	c.setorder(0);
	mark('McKay apagado, vuelta al orden por defecto');
	run(16);

	// --- Natural Harmonic Procession: el sexto Orden ------------------------------------------
	// checkNHP() fija los tres valores exactos del libro y los pares Z contra un motor limpio;
	// esto deja Orden=Natural andando dentro de una corrida real por la misma razon que el bloque
	// de McKay de arriba.
	c.setorder(5);
	mark('orden Natural (procesion quintal): del mas compacto al cromatico completo');
	run(24);
	c.setorder(0);
	mark('Natural apagado, vuelta al orden por defecto');
	run(16);

	// --- Modalidades: el septimo Orden ---------------------------------------------------------
	// checkModality() (mas abajo) fija las cinco clasificaciones exactas del libro y los dos pares
	// espejo contra un motor limpio; esto deja Orden=Modal andando dentro de una corrida real por
	// la misma razon que los bloques de McKay y Natural de arriba.
	c.setorder(6);
	mark('orden Modal (agrupado por modalidad, cap. 26): de Suspended Triad a 12-Tone');
	run(24);
	c.setorder(0);
	mark('Modal apagado, vuelta al orden por defecto');
	run(16);

	// --- Rotacion manual: setrotation(), en Acordes y en Arpegio ------------------------------
	// checkRotation() (mas abajo) ya fija los tres valores exactos del ejemplo del usuario (C-E-G /
	// E-G-C / G-C-E) contra un motor limpio; esto deja el control funcionando dentro de una corrida
	// real, con Conduccion de por medio, por la misma razon que los bloques anteriores.
	c.setmode(0);
	c.setlock(1);
	c.setlockindex(c.setForte.indexOf('3-11B') + 1);
	c.setvoicing(1);
	for (const r of [0, 1, 2]) {
		c.setrotation(r);
		mark('rotacion manual=' + r + ' (acordes)');
		run(20);
	}
	c.setvoicelead(1);
	mark('rotacion manual + conduccion: la conduccion tiene que ganar');
	run(30);
	c.setvoicelead(0);
	c.setmode(1);
	c.setrotation(0);
	mark('rotacion manual sobre arpegio, apagada primero (referencia)');
	run(24);
	c.setrotation(2);
	mark('rotacion manual=2 sobre arpegio, sumada a la rotacion automatica');
	run(24);
	c.setrotation(0);
	c.setvoicing(0);
	mark('rotacion manual apagada, vuelta al reposo');
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

// Dosia McKay's "Harmonic Processions" (forteseq/Harmonic-Processions-Dosia-McKay.pdf, chapters
// 29-34) gives three worked examples for its dissonance-gradient model: the major triad, the
// diatonic set, and the twelve-tone chromatic set. These are algebraic facts, independent of any
// audible scenario, so they are checked once here rather than folded into the note-log golden --
// a wrong weight would not necessarily change which notes play, only how the sets are ordered.
function checkMcKay() {
	const e = makeEngine(1);
	const c = e.ctx;
	let ok = true;
	const want = [['3-11B', 0.75, 3.21], ['7-35', 6, 25.64], ['12-1', 23.4, 100]];
	for (const [forte, raw, pct] of want) {
		const i = c.setForte.indexOf(forte);
		if (i < 0) { console.error('McKay: no encontre ' + forte + ' en el catalogo'); ok = false; continue; }
		const gotRaw = c.dissonanceOf(i), gotPct = c.dissonancePercent(i);
		if (Math.abs(gotRaw - raw) > 1e-6 || Math.abs(gotPct - pct) > 0.01) {
			console.error('McKay: ' + forte + ' dio raw=' + gotRaw + ' pct=' + gotPct.toFixed(2) +
				', el libro dice raw=' + raw + ' pct=' + pct);
			ok = false;
		}
	}
	// Orden = McKay: el primer set del recorrido tiene que ser el mas consonante posible -- un
	// vector interValico vacio, que solo puede ser una nota sola o el silencio del catalogo.
	c.setorder(4);
	const first = c.order[0];
	if (c.setVec[first].some((x) => x !== 0)) {
		console.error('McKay: Orden=McKay no arranca en el set mas consonante, vector=' + c.setVec[first]);
		ok = false;
	}
	// Modelo = McKay en la curva de tension: no debe tirar excepcion.
	try {
		c.settensmodel(1);
		c.settension(8);
		for (let i = 0; i < 16; i++) c.bang();
		c.settensmodel(0);
	} catch (err) {
		console.error('McKay: Modelo=McKay + curva de tension tiro ' + err);
		ok = false;
	}
	if (ok) console.log('OK   McKay: los tres valores del libro y el modo Orden/Modelo McKay andan.');
	return ok;
}

// McKay's Natural Harmonic Procession (chapters 18-23, 22-23 specifically) gives three worked
// entry numbers: F-C-A (major triad, sharp-projecting) = 10011, the Ionian pentachord C-G-D-A-B
// (sharp) = 101111, the Phrygian pentachord E-F-G-A-B (flat-projecting) = 1010111. Checked here by
// Forte label rather than literal pcs, because sets[] stores one canonical rotation per shape and
// setNP() is rotation-invariant by construction (it searches all twelve rotations itself, the same
// way zeroedNormalOrder() already does for Forte prime forms) -- any transposition of the same
// shape must give the same entry number, which is exactly what makes this check meaningful.
//
// Z-relation (chapter 36, locked to the printed edition in this PDF -- not McKay-specific, it is
// Allen Forte's own 1973 term) is checked against the one Z-pair the project already names
// elsewhere, 4-Z15/4-Z29, plus a plain tetrachord that must have no mate.
function checkNHP() {
	const e = makeEngine(1);
	const c = e.ctx;
	let ok = true;
	const want = [['3-11B', 10011], ['5-23B', 101111], ['5-24A', 1010111]];
	for (const [forte, np] of want) {
		const i = c.setForte.indexOf(forte);
		if (i < 0) { console.error('NHP: no encontre ' + forte); ok = false; continue; }
		if (c.setNP[i] !== np) {
			console.error('NHP: ' + forte + ' dio ' + c.setNP[i] + ', el libro dice ' + np);
			ok = false;
		}
	}
	const z15 = c.setForte.indexOf('4-Z15A') >= 0 ? c.setForte.indexOf('4-Z15A') : c.setForte.indexOf('4-Z15');
	if (z15 >= 0 && c.zMateOf(z15) !== '4-Z29') {
		console.error('NHP: 4-Z15 deberia emparejar con 4-Z29, dio ' + JSON.stringify(c.zMateOf(z15)));
		ok = false;
	}
	const i20 = c.setForte.indexOf('4-20A') >= 0 ? c.setForte.indexOf('4-20A') : c.setForte.indexOf('4-20');
	if (i20 >= 0 && c.zMateOf(i20) !== '') {
		console.error('NHP: 4-20 no deberia tener Z-mate, dio ' + JSON.stringify(c.zMateOf(i20)));
		ok = false;
	}
	// Orden = Natural: el primer set tiene que ser el mas compacto posible (span 0, una nota sola).
	c.setorder(5);
	if (c.setNP[c.order[0]] !== 1) {
		console.error('NHP: Orden=Natural no arranca en el set mas compacto, NP=' + c.setNP[c.order[0]]);
		ok = false;
	}
	if (ok) console.log('OK   NHP: los tres valores del libro, los pares Z y Orden=Natural andan.');
	return ok;
}

// McKay's modalities (chapter 26) group sets by span on the circle of fifths rather than by
// cardinality. Checked against five of the book's own classifications: the major triad and the
// tritone dyad both come from Figure 21's mirror-set examples, the Ionian pentachord and the full
// diatonic set from Figure 26-1/26-2's fractal tables, and the whole-tone hexachord from chapter
// 28's own worked span-11 example. Mirror sets are checked against the same chapter's two named
// pairs: major triad / minor triad, and the Lydian / Phrygian pentachord.
function checkModality() {
	const e = makeEngine(1);
	const c = e.ctx;
	let ok = true;
	const want = [
		['3-11B', 'Pentatonic'], ['7-35', 'Diatonic'], ['5-23B', 'Ionian Hexachord'],
		['2-6', 'Diatonic'], ['6-35', 'Whole-Tone'],
	];
	for (const [forte, name] of want) {
		const i = c.setForte.indexOf(forte);
		if (i < 0) { console.error('Modalidad: no encontre ' + forte); ok = false; continue; }
		const got = c.modalityNameOf(i);
		if (got !== name) {
			console.error('Modalidad: ' + forte + ' dio "' + got + '", el libro dice "' + name + '"');
			ok = false;
		}
	}
	const mirrors = [['3-11B', '3-11A'], ['5-24B', '5-24A']];
	for (const [forte, mate] of mirrors) {
		const i = c.setForte.indexOf(forte);
		if (i < 0) { console.error('Modalidad: no encontre ' + forte); ok = false; continue; }
		const got = c.mirrorForteOf(i);
		if (got !== mate) {
			console.error('Modalidad: espejo de ' + forte + ' dio "' + got + '", el libro dice "' + mate + '"');
			ok = false;
		}
	}
	// Orden = Modal: el primer set tiene que ser el de la modalidad mas chica (Suspended Triad).
	c.setorder(6);
	const first = c.order[0];
	const fm = c.modalityOf(first);
	if (!fm || fm.rank !== 0) {
		console.error('Modalidad: Orden=Modal no arranca en la primera modalidad, rank=' +
			(fm ? fm.rank : 'ninguna'));
		ok = false;
	}
	if (ok) console.log('OK   Modalidad: las cinco clasificaciones del libro y los dos pares espejo andan.');
	return ok;
}

// Azar Mask/Acentos: randomSubset()/maskRandomPattern()/accentRandomPattern() are checked as pure
// functions -- the COUNT of active cells a given percentage produces is deterministic regardless
// of which cells the seeded PRNG happens to pick, so these assertions hold on every run without
// depending on the harness's fixed seed. randomizemask()/randomizeaccents() themselves need the
// Live API (undefined outside Live, like the rest of the preset system) and are only checked here
// for not throwing -- the same smoke-test shape checkMcKay() already uses for Modelo=McKay.
function checkRandomize() {
	const e = makeEngine(1);
	const c = e.ctx;
	let ok = true;

	const countOnes = (arr) => arr.reduce((n, b) => n + b, 0);

	const maskCases = [[0, 1], [50, 6], [100, 12]];
	for (const [pct, want] of maskCases) {
		const pat = c.maskRandomPattern(pct);
		if (pat.length !== 12 || countOnes(pat) !== want) {
			console.error('Azar: maskRandomPattern(' + pct + ') dio ' + JSON.stringify(pat) +
				', esperaba ' + want + ' de 12');
			ok = false;
		}
	}

	const accentPat = c.accentRandomPattern(50, 8);
	if (accentPat.length !== 16 || countOnes(accentPat) !== 4 ||
			countOnes(accentPat.slice(8)) !== 0) {
		console.error('Azar: accentRandomPattern(50, 8) dio ' + JSON.stringify(accentPat) +
			', esperaba 4 encendidas entre las primeras 8 y el resto apagado');
		ok = false;
	}

	// randomSubset() nunca repite una celda: el conteo de unos tiene que ser exacto, no aproximado.
	for (let trial = 0; trial < 20; trial++) {
		const sub = c.randomSubset(12, 5);
		if (sub.length !== 12 || countOnes(sub) !== 5) {
			console.error('Azar: randomSubset(12, 5) dio ' + JSON.stringify(sub));
			ok = false;
			break;
		}
	}

	try {
		c.setrandmaskpct(70);
		c.randomizemask();
		c.setrandaccentpct(30);
		c.randomizeaccents();
	} catch (err) {
		console.error('Azar: randomizemask/randomizeaccents sin Live API tiro ' + err);
		ok = false;
	}

	if (ok) console.log('OK   Azar: los conteos de Mask/Acentos y el boton de accion sin Live API andan.');
	return ok;
}

// Presets: 8 -> 20 slots, y un nombre por slot. seedfactorypresets() escribe presetBank
// directamente (no necesita la Live API, a diferencia de storepreset/recallpreset), asi que
// SI es testeable a fondo aca -- incluida la ida y vuelta real por disco, con un File en memoria
// que no toca nada fuera del test. El resto (storepreset/recallpreset/clearpreset/setpresetname)
// se prueba como humo sin Live API, mismo criterio que randomizemask/randomizeaccents en Azar.
function checkPresetNames() {
	const store = {};
	const e = makeEngine(1, { File: makeFakeFile(store) });
	const c = e.ctx;
	let ok = true;

	if (c.PRESET_SLOTS !== 20) {
		console.error('Presets: PRESET_SLOTS deberia ser 20, es ' + c.PRESET_SLOTS);
		ok = false;
	}

	const notesBefore = e.log.filter(isNote).length;
	c.seedfactorypresets();
	if (e.log.filter(isNote).length !== notesBefore) {
		console.error('Presets: seedfactorypresets() disparo una nota, y no deberia sonar nada');
		ok = false;
	}
	if (!c.presetBank[1] || c.presetBank[1].__name !== 'Denso 4v' || c.presetBank[1]['Voces'] !== 4) {
		console.error('Presets: el slot 1 de fabrica no salio como se esperaba: ' +
			JSON.stringify(c.presetBank[1]));
		ok = false;
	}
	if (!store['forteseq2_presets.txt']) {
		console.error('Presets: seedfactorypresets() no escribio el archivo (simulado)');
		ok = false;
	}

	// Ida y vuelta real: vaciar la memoria y releer desde el File simulado.
	c.presetBank = [];
	c.loadpresets();
	if (!c.presetBank[1] || c.presetBank[1].__name !== 'Denso 4v' || c.presetBank[3]['Voces'] !== 3) {
		console.error('Presets: loadpresets() no recupero lo que seedfactorypresets() escribio');
		ok = false;
	}

	// Compatibilidad con un archivo formato-1, escrito a mano, sin __name en ningun lado.
	store['forteseq2_presets.txt'] = ['forteseq2 presets 1', '7\tVoces=2\tCiclo Acentos=5'];
	c.presetBank = [];
	c.loadpresets();
	const slot7 = c.presetBank[7];
	if (!slot7 || slot7['Voces'] !== 2 || slot7['Ciclo Acentos'] !== 5 || slot7.__name) {
		console.error('Presets: un archivo formato-1 (sin nombres) no cargo bien: ' +
			JSON.stringify(slot7));
		ok = false;
	}

	// El readout de nombre sigue al numbox de slot.
	c.presetBank = []; c.seedfactorypresets();
	c.setpresetslot(1);
	if (e.log[e.log.length - 1] !== '4 | presetname Denso 4v') {
		console.error('Presets: setpresetslot(1) no mando el nombre por la salida 4, mando "' +
			e.log[e.log.length - 1] + '"');
		ok = false;
	}
	c.setpresetslot(99);   // se recorta a PRESET_SLOTS = 20, no explota
	if (c.presetSlot !== 20) {
		console.error('Presets: setpresetslot(99) deberia recortar a 20, dio ' + c.presetSlot);
		ok = false;
	}

	try {
		c.storepreset(5);
		c.recallpreset(5);
		c.clearpreset(5);
		c.setpresetname(1, 'Otro nombre');
		c.presetrescan();
	} catch (err) {
		console.error('Presets: store/recall/clear/setpresetname sin Live API tiro ' + err);
		ok = false;
	}

	if (ok) console.log('OK   Presets: 20 slots, el nombre por slot y la compatibilidad con formato-1 andan.');
	return ok;
}

// Selector de articulacion por voz: apagado (voiceArtOwn = 0) tiene que ser exactamente el
// camino de grupo de siempre -- lo que ya prueba el resto del golden, byte a byte, contra un
// motor que nunca toco este bloque. Lo que hace falta probar aca es la otra mitad: prendido en
// UNA voz, esa voz y solo esa voz deja de mirar groupVelMin/Max.
function checkVoiceArt() {
	const e = makeEngine(1);
	const c = e.ctx;
	let ok = true;

	c.setnumvoices(2);
	c.setvoicemute(2, 0);   // solo la voz 1 no esta muda por defecto
	c.setvoiceindep(1);
	c.setvoicediv(1, 1);
	c.setvoicediv(2, 1);
	c.setlockindex(c.setForte.indexOf('5-35') + 1);   // setlockindex takes the 1-based Set number
	c.setlock(1);

	// Banda imposible de confundir con la del grupo (55-80/95-115): min=max=100 saca SIEMPRE 100.
	c.setvoiceartown(1, 1);
	c.setvoicearticulation(1, 100, 100, 16, 0);
	for (let i = 0; i < 12; i++) c.bang();

	// Log line shape is "0 | <bus> <voice> <vel> <dur> <pitch>", so split(' ') puts the '|' at
	// index 1 and the five atoms at 2-6.
	const velOf = (line) => Number(line.split(' ')[4]);
	const v1 = e.log.filter((l) => l[0] === '0' && l.split(' ')[3] === '1').map(velOf);
	const v2 = e.log.filter((l) => l[0] === '0' && l.split(' ')[3] === '2').map(velOf);

	if (v1.length === 0 || v1.some((v) => v !== 100)) {
		console.error('Articulacion: voz 1 con Propia debia sonar siempre a vel 100, dio ' +
			JSON.stringify(v1));
		ok = false;
	}
	// Voz 2 no tiene Propia, asi que sigue el grupo -- Normal o Acento segun su propia grilla de
	// acentos, cualquiera de las dos bandas menos la de la voz 1 (100 fijo no es parte de ninguna).
	if (v2.length === 0 || v2.every((v) => v === 100)) {
		console.error('Articulacion: voz 2 sin Propia no deberia sonar fija a 100 como la voz 1, dio ' +
			JSON.stringify(v2));
		ok = false;
	}

	if (ok) console.log('OK   Articulacion por voz: Propia aisla una voz sin tocar la otra.');
	return ok;
}

// Patron/Direccion de lectura por voz: mismo criterio que arriba. Zigzag es determinista (no
// tira de Math.random como Urna), asi que la comparacion no depende de la semilla -- alcanza con
// que la secuencia sea DISTINTA de una lectura Recta para probar que el selector realmente pega.
function checkVoiceReadOrder() {
	const e = makeEngine(1);
	const c = e.ctx;
	let ok = true;

	c.setnumvoices(2);
	c.setvoicemute(2, 0);   // solo la voz 1 no esta muda por defecto
	c.setvoiceindep(1);
	c.setvoicediv(1, 1);
	c.setvoicediv(2, 1);
	c.setlockindex(c.setForte.indexOf('5-35') + 1);   // setlockindex takes the 1-based Set number
	c.setlock(1);
	c.setmode(1);        // Arpegio: el cursor de cada voz avanza (en Acordes queda fijo en grado 0)
	c.setreadmode(0);   // global en Recto, para que la voz 2 (sin Propia) sea la referencia

	c.setvoicereadown(1, 1);
	c.setvoicereadmode(1, 5);   // READ_ZIGZAG
	for (let i = 0; i < 10; i++) c.bang();

	const pitchOf = (line) => Number(line.split(' ')[6]);
	const v1 = e.log.filter((l) => l[0] === '0' && l.split(' ')[3] === '1').map(pitchOf);
	const v2 = e.log.filter((l) => l[0] === '0' && l.split(' ')[3] === '2').map(pitchOf);

	if (v1.length < 4 || JSON.stringify(v1) === JSON.stringify(v2)) {
		console.error('Lectura por voz: voz 1 en Zigzag propio debia diferir de la voz 2 en Recto, ' +
			'ambas dieron ' + JSON.stringify(v1));
		ok = false;
	}

	if (ok) console.log('OK   Lectura por voz: Patron/Dir propios aislan una voz bajo Voces Indep.');
	return ok;
}

// Manual rotation (setrotation(), the "Rotacion" dial): the user's own example, C-E-G rotated to
// E-G-C to G-C-E, i.e. chordFor() on the major triad (3-11B, pcs [0,4,7]) picking each of
// closedStack()'s three rotations in turn. Voicing pinned to Cerrado (VOICING_CLOSED=1, whose
// applyVoicing() branch is a no-op) so the expected pitches are closedStack()'s own output with
// nothing else in the way -- an algebraic fact, independent of any scenario/seed, same reason
// checkMcKay()/checkNHP() live here instead of in the note-log golden.
function checkRotation() {
	const e = makeEngine(1);
	const c = e.ctx;
	let ok = true;
	const triad = c.setForte.indexOf('3-11B');
	if (triad < 0) { console.error('Rotacion: no encontre 3-11B en el catalogo'); return false; }
	c.setlockindex(triad + 1);   // setlockindex takes the 1-based Set number
	c.setlock(1);
	c.setmode(0);        // Acordes
	c.setvoicelead(0);   // Conduccion apagada: el candidato manual no se pisa
	c.setvoicing(1);     // Cerrado
	const pcs = c.sets[triad];
	const want = [[0, [48, 52, 55]], [1, [52, 55, 60]], [2, [55, 60, 64]]];
	for (const [r, expect] of want) {
		c.setrotation(r);
		const got = c.chordFor(pcs);
		if (JSON.stringify(got) !== JSON.stringify(expect)) {
			console.error('Rotacion: setrotation(' + r + ') dio ' + JSON.stringify(got) +
				', esperaba ' + JSON.stringify(expect));
			ok = false;
		}
	}
	// Wraps by the ACTIVE set's cardinality (3 here), not a fixed 12: setrotation(3) on a triad
	// must land back on rotation 0, not stay at a dangling index 3 that cands[] does not have.
	c.setrotation(3);
	const wrapped = c.chordFor(pcs);
	if (JSON.stringify(wrapped) !== JSON.stringify(want[0][1])) {
		console.error('Rotacion: setrotation(3) en una triada deberia envolver a 0, dio ' +
			JSON.stringify(wrapped));
		ok = false;
	}
	// setrotation(0) is the default, so it must not disturb chord mode at all: a manual rotation
	// left at its resting value has to be indistinguishable from the feature never existing.
	c.setrotation(0);
	const rest = c.chordFor(pcs);
	if (JSON.stringify(rest) !== JSON.stringify(want[0][1])) {
		console.error('Rotacion: setrotation(0) deberia ser identico a no tocar el control, dio ' +
			JSON.stringify(rest));
		ok = false;
	}
	if (ok) console.log('OK   Rotacion: setrotation() elige la inversion correcta y envuelve por cardinalidad.');
	return ok;
}

function main() {
	const args = process.argv.slice(2);
	const seed = 20260819;

	if (!checkMcKay()) process.exit(1);
	if (!checkNHP()) process.exit(1);
	if (!checkModality()) process.exit(1);
	if (!checkRandomize()) process.exit(1);
	if (!checkPresetNames()) process.exit(1);
	if (!checkVoiceArt()) process.exit(1);
	if (!checkVoiceReadOrder()) process.exit(1);
	if (!checkRotation()) process.exit(1);

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
