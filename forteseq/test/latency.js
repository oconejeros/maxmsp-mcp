// When a note leaves, and what a tick costs.
//
// harness.js answers a different question -- WHAT the device plays -- and it answers it well, but
// it is blind to this one by construction: its log has no clock in it, so a note that came out a
// tick late still lands on the same line. That is not hypothetical. The sub-clock added in the
// Fase 5 work routed every note through a ring buffer drained only by bang(), which meant a note
// triggered from a MIDI clip waited for the next metro tick -- up to a whole step late, quantised
// to the grid, and with the transport stopped it never came out at all. The golden file reported
// no change, because there was none to report in the only dimension it measures.
//
//   node forteseq/test/latency.js
//
// Exit 0 if the timing tests pass. The cost table always prints: it is a reference, not a test,
// because there is no threshold worth asserting on a machine whose JIT is nothing like the
// interpreter inside Max's js object. What it is good for is the RATIO between two builds, and
// the count of Max crossings per tick, which is the number that actually governs this device
// (the engine has never been limited by JavaScript; it is limited by how often it talks to Max).

'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const engineArg = process.argv.indexOf('--engine');
const ENGINE = engineArg >= 0
	? path.resolve(process.argv[engineArg + 1])
	: path.join(__dirname, '..', 'forteseq2.js');

// The same generator harness.js uses, for the same reason: a seeded run is reproducible, and the
// velocities still look random to the ear.
function mulberry32(seed) {
	let a = seed >>> 0;
	return function () {
		a = (a + 0x6D2B79F5) | 0;
		let t = Math.imul(a ^ (a >>> 15), 1 | a);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

// `when` is a LOGICAL clock: the number of bangs delivered so far. It is the whole point of this
// file. Wall time would measure Node, not the device; the bang count measures the thing the user
// hears, which is how many metro ticks passed between asking for a note and getting it.
function makeEngine(seed) {
	const state = { when: 0, notes: [], crossings: {} };
	const seededMath = Object.create(Math);
	seededMath.random = mulberry32(seed === undefined ? 20260819 : seed);
	const sandbox = {
		Math: seededMath,
		post: function () {},
		outlet: function (n, value) {
			state.crossings[n] = (state.crossings[n] || 0) + 1;
			if (n === 0) {
				const atoms = Array.isArray(value) ? value : [value];
				state.notes.push({ when: state.when, atoms: atoms.slice() });
			}
		}
	};
	sandbox.global = sandbox;
	const ctx = vm.createContext(sandbox);
	vm.runInContext(fs.readFileSync(ENGINE, 'utf8'), ctx, { filename: path.basename(ENGINE) });
	state.ctx = ctx;
	state.bang = function () { ctx.bang(); state.when++; };
	state.run = function (n) { for (let i = 0; i < n; i++) state.bang(); };
	return state;
}

// Four voices audible and in distinct registers. `external` decides whether the shared clock
// drives them or whether they wait to be triggered, which is the difference the whole file is about.
function setup(e, external) {
	const c = e.ctx;
	c.setnumvoices(4);
	c.setbpmtrack(120);
	for (let v = 1; v <= 4; v++) {
		c.setvoicemute(v, 0);
		c.setvoiceexternal(v, external ? 1 : 0);
		c.setvoicerange(v, 36 + v * 8, 24);
		c.setvoiceoctavesimple(v, 4, 0, 1, 0);
		c.setvoicephase(v, 0);
		c.setvoicedegoffset(v, 0);
		c.setvoicediv(v, 1);
	}
	return c;
}

function ringDepth(ctx) {
	let n = 0;
	const pending = ctx.pending;
	for (let i = 0; i < pending.length; i++) if (pending[i]) n += pending[i].length;
	return n;
}

const results = [];

function check(name, ok, detail) {
	results.push({ name, ok, detail });
	console.log((ok ? '  OK   ' : '  FALLA ') + name);
	if (detail) console.log('         ' + detail);
}

// ---------------------------------------------------------------------------------------------
console.log('--- 1. un trigger externo sale en el instante en que llega -------------------------');
// Eight triggers, one just after each tick. Every one must leave on the tick it arrived on. Before
// the fix all eight came out on the FOLLOWING tick, which is the same as saying the device
// quantised a MIDI clip to its own metro.
{
	const e = makeEngine();
	const c = setup(e, true);
	for (let i = 0; i < 8; i++) {
		e.bang();
		c.trig(c.busId, 1);
	}
	const expected = [];
	for (let i = 1; i <= 8; i++) expected.push(i);
	const got = e.notes.map((n) => n.when);
	const ok = e.notes.length === 8 && got.every((w, i) => w === expected[i]);
	check('ocho triggers, ocho notas, cada una en su propio tick',
		ok,
		'esperado ' + expected.join(' ') + '  |  obtenido ' + (got.join(' ') || '(ninguna)'));
	check('nada quedo en el ring', ringDepth(c) === 0, 'ring: ' + ringDepth(c));
}

// ---------------------------------------------------------------------------------------------
console.log('--- 2. con el transporte parado los triggers igual suenan --------------------------');
// The worst face of the same bug: with Run off there are no bangs, so there was no drain, so the
// notes accumulated in one ring slot and all fired together the moment the transport started.
{
	const e = makeEngine();
	const c = setup(e, true);
	for (let i = 0; i < 12; i++) c.trig(c.busId, 1);
	check('doce triggers sin un solo bang producen doce notas',
		e.notes.length === 12, 'notas: ' + e.notes.length);
	check('y no dejan nada encolado esperando a Run',
		ringDepth(c) === 0, 'ring: ' + ringDepth(c));
}

// ---------------------------------------------------------------------------------------------
console.log('--- 3. el reloj sigue usando el ring, que es para lo que existe --------------------');
// The other direction. Making everything immediate would "fix" the tests above and silently
// destroy swing, humanize, strum and the ratchet, all of which work by holding a note back a
// fraction of a step. With Sub 4 and a strum, one chord has to arrive spread over several ticks.
{
	const e = makeEngine();
	const c = setup(e, false);
	c.setmode(0);          // Acordes: strum only has something to spread when there is a chord
	c.setsub(4);
	c.setstrum(1);
	c.setlock(1);
	c.setlockindex(120);   // five notes, so the spread is visible and bounded
	e.run(12);
	const ticks = new Set(e.notes.map((n) => n.when));
	check('un acorde rasgueado con Sub 4 llega repartido en varios ticks',
		e.notes.length > 0 && ticks.size > 1,
		e.notes.length + ' notas repartidas en ' + ticks.size + ' ticks distintos');
}

// ---------------------------------------------------------------------------------------------
console.log('');
console.log('--- costo por tick (referencia, no es una prueba) ----------------------------------');
{
	const N = 20000;
	const rows = [];
	function row(label, external, tweak) {
		const e = makeEngine();
		const c = setup(e, external);
		if (tweak) tweak(c);
		const t0 = process.hrtime.bigint();
		for (let i = 0; i < N; i++) c.bang();
		const us = Number(process.hrtime.bigint() - t0) / 1e3 / N;
		let total = 0;
		for (const k in e.crossings) total += e.crossings[k];
		rows.push([label, us.toFixed(1), (total / N).toFixed(1),
			((e.crossings[0] || 0) / N).toFixed(1)]);
	}
	row('4 voces externas, Acordes', true, null);
	row('4 voces externas, Arpegio', true, (c) => c.setmode(1));
	row('4 voces del reloj, Acordes', false, null);
	row('4 voces del reloj, Acordes + Conduccion', false, (c) => c.setvoicelead(1));
	row('4 voces del reloj, Arpegio', false, (c) => c.setmode(1));
	row('4 voces del reloj, Arpegio, monitor off', false, (c) => { c.setmode(1); c.setmonitor(0); });
	console.log('  escenario                                  us/tick  cruces  notas');
	for (const r of rows) {
		console.log('  ' + r[0].padEnd(42) + r[1].padStart(7) + r[2].padStart(8) + r[3].padStart(7));
	}
	console.log('');
	console.log('  "cruces" son mensajes por outlet, que es lo que le cuesta caro a este device:');
	console.log('  cada nota cruza a Max y llega a TODOS los Hub del set, que filtran por (bus, voz).');
}

// ---------------------------------------------------------------------------------------------
console.log('');
const failed = results.filter((r) => !r.ok);
if (failed.length) {
	console.log('FALLARON ' + failed.length + ' de ' + results.length + ' pruebas de tiempo.');
	process.exit(1);
}
console.log('las ' + results.length + ' pruebas de tiempo pasan.');
