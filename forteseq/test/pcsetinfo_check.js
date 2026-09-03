// Checks for the analysis helpers in forteseq/pcsetinfo.js -- the chord namer (Feature 1),
// the Krumhansl-Schmuckler key finder (Feature 2) and the circle-of-fifths spread
// (Feature 3). pcsetinfo.js is a Max `js` script with no exports; like harness.js it is
// loaded UNMODIFIED into a `vm` context whose globals are the stubs Max provides, and driven
// through `note` / `list` while `outlet` calls are captured.
//
//   node forteseq/test/pcsetinfo_check.js
//
// Exit code is non-zero on any failure. The McKay dissonance numbers already have assertions
// in the forteseq2 harness -- this file only covers what pcsetinfo grew for the max4.live
// complement features.

'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SRC = path.join(__dirname, '..', 'pcsetinfo.js');

let OUT = [];
const sandbox = {
	autowatch: 0, inlets: 0, outlets: 0,
	arrayfromargs: function (a) { return Array.prototype.slice.call(a); },
	outlet: function () { OUT.push(Array.prototype.slice.call(arguments)); },
	Math: Math, Date: Date, parseInt: parseInt, parseFloat: parseFloat,
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(SRC, 'utf8'), sandbox, { filename: 'pcsetinfo.js' });

let fails = 0;
function eq(label, got, want) {
	const ok = JSON.stringify(got) === JSON.stringify(want);
	console.log((ok ? 'ok   ' : 'FAIL ') + label + '  => ' + JSON.stringify(got) +
		(ok ? '' : '   want ' + JSON.stringify(want)));
	if (!ok) fails++;
}

// last `outlet(0, tag, ...)` message with this tag, as its argument list (tag dropped)
function msg0(tag) {
	for (let i = OUT.length - 1; i >= 0; i--)
		if (OUT[i][0] === 0 && OUT[i][1] === tag) return OUT[i].slice(2);
	return null;
}
// last `outlet(1, [tag, ...])` tagged list
function msg1(tag) {
	for (let i = OUT.length - 1; i >= 0; i--)
		if (OUT[i][0] === 1 && Array.isArray(OUT[i][1]) && OUT[i][1][0] === tag) return OUT[i][1].slice(1);
	return null;
}
// strike a chord as stacked MIDI notes from a C-octave base; leaves it held
function play(rootPc, semis, base) {
	sandbox.clear(); OUT = [];
	semis.forEach(s => sandbox.note((base == null ? 48 : base) + rootPc + s, 100));
}
// play a progression as struck-and-released chords, `reps` times, from a C base
function progression(chords, reps, base) {
	sandbox.clear();
	for (let r = 0; r < (reps || 3); r++)
		for (const [rt, semis] of chords) {
			OUT = [];
			semis.forEach(s => sandbox.note((base == null ? 48 : base) + rt + s, 100));
			semis.forEach(s => sandbox.note((base == null ? 48 : base) + rt + s, 0));
		}
}
const chord = () => (msg0('chord') || [])[0];

// ---- Feature 1: root-relative chord names --------------------------------------------------
play(0, [0, 4, 7]);          eq('C major triad', chord(), 'C');
sandbox.clear(); OUT = []; [52, 60, 67].forEach(n => sandbox.note(n, 100));  // E3 C4 G4
eq('C major, bass E -> slash', chord(), 'C/E');
play(2, [0, 3, 7]);          eq('D minor', chord(), 'Dm');
play(0, [0, 4, 7, 10]);      eq('dominant seventh', chord(), 'C7');
play(0, [0, 4, 7, 11]);      eq('major seventh', chord(), 'Cmaj7');
play(9, [0, 3, 7, 10]);      eq('Am7 wins over C6', chord(), 'Am7');
play(11, [0, 3, 6, 10]);     eq('Bm7b5 wins over Dm6', chord(), 'Bm7b5');
play(0, [0, 3, 6, 9]);       eq('diminished seventh (symmetric)', chord().slice(1), 'dim7');
play(0, [0, 5, 7]);          eq('sus4', chord(), 'Csus4');
play(0, [0, 2, 7]);          eq('sus2', chord(), 'Csus2');
play(0, [0, 4, 8]);          eq('augmented', chord().slice(1), 'aug');
sandbox.clear(); OUT = []; [53, 55, 59, 62].forEach(n => sandbox.note(n, 100));  // F G B D
eq('G7 over F (3rd inversion)', chord(), 'G7/F');
play(9, [0]);                eq('single note', chord(), 'A');
play(0, [0, 2, 4, 7]);       eq('add9', chord(), 'Cadd9');
play(0, [0, 4, 7, 9]);       eq('sixth (no seventh reading)', chord(), 'C6');

// alternates land on outlet 1
play(9, [0, 3, 7, 10]);
eq('Am7 alternates list C6', (msg1('chords') || []).indexOf('C6') >= 0, true);

// ---- Feature 2: Krumhansl-Schmuckler key finding -----------------------------------------
function keyOf() { const m = msg0('keyguess'); return m ? [m[0], m[1]] : null; }
progression([[0, [0, 4, 7]], [5, [0, 4, 7]], [7, [0, 4, 7, 10]], [0, [0, 4, 7]]]);
eq('I-IV-V-I in C -> C major', keyOf(), [0, 0]);
eq('  confidence > 0.6', msg0('keyguess')[2] > 0.6, true);
progression([[7, [0, 3, 7, 10]], [0, [0, 4, 7, 10]], [5, [0, 4, 7]]]);
eq('ii-V-I in F -> F major', keyOf(), [5, 0]);
progression([[9, [0, 3, 7]], [2, [0, 3, 7]], [4, [0, 4, 7, 10]], [9, [0, 3, 7]]]);
eq('Am Dm E7 Am -> A minor', keyOf(), [9, 1]);

// study mode must NOT emit a key guess (frozen MIDI, static shape)
sandbox.clear(); OUT = [];
sandbox.studyset(4, 1, 0, 0, 0);
eq('study set emits no keyguess', msg0('keyguess'), null);

// ---- Feature 3: circle-of-fifths spread (0 tight .. 11 scattered) -----------------------
function q5() { return (msg1('q5span') || [])[0]; }
play(0, [0, 7, 2]);          eq('C-G-D packs tight in fifths', q5(), 2);
play(0, [0, 4, 7]);          eq('C major triad spans a M3 = 4 fifths', q5(), 4);
play(0, [0, 1, 2]);          eq('chromatic cluster is scattered', q5(), 7);

// ---- AnWin: windowed analysis set -----------------------------------------------------
sandbox.anwin(0);
sandbox.clear(); OUT = [];
[48, 52, 55].forEach(n => sandbox.note(n, 100));
[48, 52, 55].forEach(n => sandbox.note(n, 0));
eq('AnWin 0: released set clears', chord(), '');

sandbox.anwin(5);
sandbox.clear(); OUT = [];
[48, 52, 55].forEach(n => { sandbox.note(n, 100); sandbox.note(n, 0); });  // C E G, one at a time
eq('AnWin 5: arpeggio reads as one chord', chord(), 'C');
eq('AnWin 5: forte of the windowed set', (msg1('forte') || [])[0], '3-11B');
sandbox.bang();
eq('AnWin 5: metro bang keeps the windowed set', chord(), 'C');
eq('AnWin 5: info line marks the window', /\ban 5s\b/.test((msg0('info') || [''])[0]), true);

sandbox.anreset();
eq('anreset clears the window', chord(), '');
sandbox.anwin(0);

console.log(fails ? ('\n' + fails + ' FAILED') : '\nall green');
process.exit(fails ? 1 : 0);
