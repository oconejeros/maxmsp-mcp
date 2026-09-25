"""Generate the English hover-help tables inside forteseq/fs2horizon.js and forteseq/fs2setpick.js.

    python tools/gen_fs2_help.py           dry run + drift report, writes nothing
    python tools/gen_fs2_help.py --apply   write the HELP blocks into both jsui files
    python tools/gen_fs2_help.py --bless   record the current Spanish as reviewed (see below)

## Why this exists

Live shows a parameter's `annotation` in its info view, but only for real `live.*` widgets. Every
control in the two popup panels is drawn by jsui: Live does not know those chips exist, so there is
nowhere for help to appear, and those are the densest controls in the whole device. The jsui files
draw their own balloon on hover instead (see drawTooltip there); this script fills it.

## How it stays in sync with the device

tools/fs2help_map.py resolves each drawn chip to the Live parameter it actually drives, by matching
the `outlet(0, ['set...'])` in the chip's spec against the `prepend set...` the widget is wired to.
That gives every chip the Spanish annotation it corresponds to. This script hashes that Spanish and
stores it in tools/fs2help_hashes.json. On the next run it re-hashes and REPORTS every chip whose
Spanish has changed since its English was written -- the English is never silently regenerated, it
is flagged for review, because a translation is a judgement and a hash is not.

Workflow after editing an annotation in the device:
    python tools/gen_fs2_help.py          -> lists what went stale
    (edit EN below for those keys)
    python tools/gen_fs2_help.py --bless --apply

The texts here are deliberately SHORT -- a hover balloon, not the info view. Several device
annotations run past 2000 characters; those are summarised rather than translated line by line.
"""
import hashlib
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fs2help_map import resolve, FORTESEQ

HORIZON = os.path.join(FORTESEQ, 'fs2horizon.js')
SETPICK = os.path.join(FORTESEQ, 'fs2setpick.js')
HASHES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fs2help_hashes.json')

BEGIN = '// ---- FS2_HELP BEGIN (generado por tools/gen_fs2_help.py -- no editar a mano) ----'
END = '// ---- FS2_HELP END ----'

EN = {
    # --- per-voice chips -------------------------------------------------------------------
    'v:on': 'Voice on/off. A voice that is off is muted in the engine: neither the shared clock '
            'nor an external trigger will sound it.',
    'v:ext': 'External: the shared clock skips this voice, and it only sounds when a Hub in Send '
             'mode triggers it.',
    'v:trig': 'Fires this voice once, right now -- the same momentary trigger as the panel\'s Trig '
              'button. Nothing is stored; it is for auditioning a voice without the transport.',
    'v:art': 'Own articulation: this voice stops reading the Normal/Accent bands and uses its own '
             'velocity, note length and rest chance -- the four chips beside it. Off by default.',
    'v:artvmin': 'Lowest velocity for this voice, used only when its own articulation is on. Each '
                 'note is drawn at random between Min and Max.',
    'v:artvmax': 'Highest velocity for this voice, used only when its own articulation is on.',
    'v:artdur': 'Note length for this voice as a note-value denominator: 4 = quarter, 8 = eighth, '
                '16 = sixteenth. Used only when its own articulation is on.',
    'v:artsil': 'Chance, in percent, that this voice rests instead of playing -- used only when '
                'its own articulation is on.',
    'v:lec': 'Own reading: this voice stops following the global Pattern and Direction and uses '
             'its own. Only does anything under Independent Voices or an external trigger, which '
             'is where a voice already has a cursor of its own. Off by default.',
    'v:patron': 'Reading order for this voice, used only when its own reading is on.',
    'v:dir': 'Reading direction for this voice, used only when its own reading is on.',
    'v:copsalto': 'Coprime step for this voice (1-11, snapped to the nearest coprime of the set '
                  'size), when its own reading is on and its Pattern is Coprime. Otherwise the '
                  'global step is used.',
    'v:ornt': 'Ornament type for this voice, when its own reading is on and its Pattern is '
              'Ornament. Ignored the rest of the time.',
    'v:ornnotas': 'How many ornament notes (1-4) this voice adds, when its own reading is on and '
                  'its Pattern is Ornament. Ignored the rest of the time.',
    'v:ornbase': 'Base interval in semitones (1-14) for this voice\'s ornament, when its own '
                 'reading is on and its Pattern is Ornament. Ignored the rest of the time.',
    'v:ton': 'Own key: this voice stops following the global Set and Root and plays in its OWN key '
             '(bitonal/polytonal). Only does anything under Independent Voices or an external '
             'trigger, same as own reading. Off by default.',
    'v:setbox': 'This voice\'s own set (1-351), read only when its own key is on. The rest of the '
                'time the voice follows the shared harmony.',
    'v:rootoff': 'This voice\'s own transpose in semitones, read only when its own key is on. The '
                 'rest of the time the voice follows the shared harmony.',
    'v:fijar': 'Freezes this voice\'s own set: it stops advancing on each harmony change and keeps '
               'sounding where it is, while other own-key voices carry on. It does NOT turn own '
               'key off -- to rejoin the shared harmony, turn that off instead.',
    'v:grado': 'How many DEGREES of the set this voice sits above its own reading. 0,1,2,3 across '
               'four voices gives a four-part chord; negative puts it below. Always active in '
               'Arpeggio, and in Chords only under Independent Voices.',
    'v:div': 'Clock divider: this voice sounds once every N steps, and its cursor only advances '
             'when it sounds. Different dividers drift the voices apart and bring them back '
             'together at their common multiple. Needs Independent Voices.',
    'v:fase': 'Shifts where this voice reads the accent grid, so the voices do not all accent on '
              'the same step.',
    'v:desf': 'Fixed delay for this voice, in sub-ticks: how late it plays relative to the step. '
              'This is what turns four voices on one rhythm into an ensemble that is not quite '
              'together. Different from Phase, which moves which cell it reads. Needs Sub above 1.',
    'v:euclen': 'Length of this voice\'s own euclidean rhythm -- how many cells the pattern spans. '
                'At 0 there is no pattern and the voice plays on every step it is given.',
    'v:euck': 'How many pulses this voice\'s euclidean rhythm spreads over its length. A cell that '
              'is not a pulse is a rest, and the cursor still advances through it.',
    'v:eucrot': 'Rotates this voice\'s euclidean rhythm: which cell the pattern starts on. The '
                'same pattern rotated is a different rhythm.',
    'v:octbase': 'Base octave for this voice, on top of the root and the master octave. The octave '
                 'pattern (Ev / Rg / Ps) starts from here.',
    'v:octevery': 'How many notes pass before this voice\'s octave pattern moves up one step.',
    'v:octrange': 'How far the octave pattern travels, in octaves. Negative goes down instead of '
                  'up. At 0 the voice stays at its fixed octave.',
    'v:octsteps': 'How many stops there are between 0 and the range. Fewer steps means bigger, '
                  'less gradual jumps.',
    'v:rgmin': 'Lowest MIDI note this voice may sound. Notes outside the register are folded by '
               'whole octaves and never remapped, so the pitch class survives. Amber means this '
               'voice no longer matches the Range template the menu is showing.',
    'v:rgspan': 'How wide this voice\'s register is, in semitones counted up from Min. Amber means '
                'this voice no longer matches the Range template the menu is showing.',
    'v:rrate': 'This voice\'s own Root Rhythm: one notch of its root walk every N steps. At 0 it '
               'stays on the shared walk. The route stays the global Root Seq -- only the clock is '
               'the voice\'s -- so two voices at different rates travel the same road out of phase.',

    # --- global sidebar --------------------------------------------------------------------
    'g:run': 'Starts and stops the engine. In Sync mode Live also has to be playing.',
    'g:ind': 'Independent Voices: every voice walks its own cursor instead of all of them being '
             'handed the same note. This is what makes the voice count buy texture, and what most '
             'per-voice controls need before they do anything at all.',
    'g:flt': 'Master switch for the filter: cardinality, interval vector, favourites and the '
             'chromatic mask. Off puts the full 351-class catalogue back in play.',
    'g:lck': 'Freezes the shared set, so the harmony stops moving. The root walk keeps going '
             'underneath, so a locked set is still carried around.',
    'g:set': 'Picks the pitch-class set from Forte\'s catalogue (1-351). Moving it jumps there at '
             'once, even with Lock off.',
    'g:modo': 'Chords: every note of the set sounds together. Arpeggio: one note per step.',
    'g:orden': 'The route through the catalogue. Card: generation order. Forte: catalogue order. '
               'Cons: most consonant to most tense, by interval vector. Vec: chained by common '
               'tones. McKay / Natural / Modal: the Harmonic Processions orderings. Vector: by '
               'distance between interval vectors rather than shared notes.',
    'g:ordrev': 'Walks the chosen Order backwards: the next set is the previous neighbour instead '
                'of the next one. What sounds now does not change, only which way it moves from '
                'here. Applies to own-key voices too.',
    'g:dir': 'Reading direction, over whichever order is chosen. Forward; backward, the same pass '
             'reversed; or alternating, there and back without repeating either end. The set does '
             'not change until the pass finishes, so alternating doubles how long a harmony lasts.',
    'g:patron': 'Reading order: how the engine walks the notes of the current set -- straight, '
                'super-permutation, modes, coprime, zigzag, urn, or ornament.',
    'g:harm': 'How many steps between set changes. At 0 the reading decides, as always: the set '
              'changes when the pass ends. Any other value puts the harmony on its own clock, so a '
              '720-step super-permutation can run over chords changing every 4. Lock still wins.',
    'g:raizrate': 'How many steps between notches of the root walk. At 0 the walk stays tied to '
                  'the harmony and moves when the set moves. Any other value gives Root Seq its '
                  'OWN clock, whether or not the set ever changes.',
    'g:rootseq': 'The route the root walks: fourths, fifths, thirds, chromatic, whole tones, '
                 'tritones, I-IV-V, or a fresh root drawn at random. Off leaves the root where the '
                 'dial puts it.',
    'g:root': 'The root everything is transposed to, in semitones. It is the origin of the root '
              'walk, so moving it carries the whole sequence with it.',
    'g:octm': 'Master octave: shifts every voice at once, on top of each voice\'s own octave. '
              'Ignored in Drum mode, where there are no registers to shift.',
    'g:rango': 'Writes the register of all four voices at once, V1 the highest. Free releases them '
               'entirely; the rest are working ranges, not the extremes of an instrument. Nothing '
               'is locked afterwards, so a voice you nudge shows an amber Mn/Sp.',
    'g:voicing': 'How a chord is spread in Chords mode. Extended is the classic: notes spread '
                 'evenly over four octaves. Closed stacks them inside one. Drop 2, Drop 3 and Drop '
                 '2+4 lower inner voices an octave for the wind-section sound. Open alternates. A '
                 'drop that does not fit the chord falls back to closed rather than sinking the bass.',
    'g:cond': 'Voice leading in Chords mode. On each set change it tries every inversion in every '
              'octave within reach and keeps the one that moves least from the chord that just '
              'sounded. It changes no note of the set, only inversion and octave. Tight per-voice '
              'registers can undo part of the work.',
    'g:rotacion': 'Rotates the current set: which note starts it. In Chords it picks the inversion '
                  '(C-E-G, E-G-C, G-C-E); in Arpeggio it adds to the automatic rotation rather '
                  'than fighting it. It wraps at the set size, so in a triad 3 equals 0. Voice '
                  'leading still wins when it is on.',
    'g:rotarx': 'How often the set\'s shape rotates. Off: once per complete pass of the catalogue. '
                'On: on every set change.',
    'g:salto': 'How many degrees the Coprime reading steps by. The engine snaps it to the nearest '
               'coprime of the set size, which is the only thing that guarantees hitting every '
               'degree before repeating. On a 7-note set, 2 is a chain of thirds.',
    'g:sub': 'Sub-ticks per step: the fine grid that swing, strum and per-voice delay are measured '
             'in. The higher the Sub, the finer they can be placed; at Sub 1 there is nothing '
             'between the steps for them to use.',
    'g:swing': '50 is straight. 66 is triplet feel, the off-beat landing two thirds of the way. 75 '
               'is a dotted lilt. It only moves in whole sub-ticks, so the higher the Sub, the '
               'finer the swing.',
    'g:human': 'Random timing jitter, in percent: how far each note may wander from its exact '
               'position. It loosens a mechanical grid without changing the written rhythm.',
    'g:rasg': 'Strum: sub-ticks between one note of a chord and the next. At 0 the chord is struck '
              'together. It is measured in sub-ticks, so at Sub 1 a strum of 2 spreads the chord '
              'over two whole steps.',
    'g:dirrasg': 'Which note the chord opens from. Alternate flips the direction on every step.',
    'g:drum': 'Every pitch class becomes a Drum Rack pad instead of a note: the set chooses WHICH '
              'drums play and the reading chooses when. While it is on, nothing that moves a note '
              'vertically applies -- a rack\'s rows are different instruments, not registers, so '
              'folding would land on another drum. The root still counts: it shifts the whole set '
              'across the rack.',
    'g:pad': 'Which MIDI note is the first pad. 36 is C1, the bottom-left pad of a Live Drum Rack, '
             'and the twelve pitch classes run upward from there.',
    'g:emit': 'Broadcasts which class this device is on, over its bus. Only WHICH set travels: '
              'root, octave, voicing and register stay each engine\'s own, because two engines in '
              'different registers or keys over one harmony is the point of having two.',
    'g:seguir': 'Takes the harmony from the bus instead of choosing it. With this on, this '
                'device\'s clock no longer moves the catalogue -- the broadcaster decides. A '
                'follower never broadcasts, so no loop is possible.',
    'g:escuchar': 'Off: the device does not listen. Follow: while you hold notes the harmony is '
                  'the class you are playing, in the key you played it, and the sequence waits; '
                  'releasing returns it exactly where it was. Latch: it keeps that chord and '
                  'carries on from there. Any chord works -- the catalogue holds all 351 classes, '
                  'so identifying one is a lookup that cannot fail.',
    'g:panic': 'All notes off. Releases anything left hanging, including a chord the listener '
               'latched.',
    'g:fav': 'Marks or unmarks the set sounding right now, which is what makes the button usable '
             'while browsing: hear something, mark it, carry on. It repaints on every harmony '
             'change, so it always tells the truth about the current set. The list travels with '
             'the Live set, not with the device presets.',
    'g:favonly': 'Only marked sets are visited. It is one more filter, not a separate mode: it '
                 'combines with cardinality, vector and mask instead of replacing them. With an '
                 'empty list nothing would pass, so the device falls back to the whole catalogue '
                 'and says so in the console.',
    'g:progfav': 'Plays the favourites in the order you marked them rather than catalogue order, '
                 'which turns a short list into a chord progression. It overrides Link and Tension '
                 'and ignores the filter -- you picked these by hand. To move one to the end, '
                 'unmark it and mark it again.',
    'g:clearfavs': 'Empties the favourites list. It lives with the Live set rather than with the '
                   'device presets, so this is the only thing that clears it.',
    'g:nmin': 'Smallest set allowed through the filter: its minimum number of notes.',
    'g:nmax': 'Largest set allowed through the filter: its maximum number of notes.',
    'g:maskmode': 'How a set is compared with the mask. Sub: the set fits inside the mask (mask = '
                  'scale). Con: the set contains the whole mask (mask = required interval). Int: '
                  'it shares at least k notes with the mask.',
    'g:maskk': 'How many notes in common the Int mask mode requires.',
    'g:maskfit': 'Fit: when a set does not satisfy the mask where it is stored, it is transposed to '
                 'where it does and sounds there. Without fit almost nothing passes -- not even the '
                 'diatonic scale passes its own scale\'s filter. With fit, the mask outranks the Root.',
    'g:randmask': 'Fills the chromatic mask at random. How much of it gets filled is the '
                  'percentage beside it.',
    'g:randmaskpct': 'What share of the 12 mask cells the random fill turns on -- at least one, so '
                     'the mask filter is never emptied by accident.',
    'g:enlace': 'Minimum common tones between one set and the next: the harmony may only move to a '
                'set sharing at least this many notes with the current one. At 0 the constraint is '
                'off, and the walk is free to jump anywhere the order allows.',
    'g:tension': 'Length of the tension cycle, counted in set changes. The harmony is asked to '
                 'follow a consonance curve across that many changes instead of simply walking the '
                 'order. At 0 it is off.',
    'g:curva': 'The shape of the tension cycle: how consonance rises and falls across it.',
    'g:tensmodel': 'Which measure of consonance the tension curve judges a set by.',
    'g:ciclo': 'How many cells of the accent grid are in play, from 1 to 16.',
    'g:tie': 'On: the accent cycle takes the length of the current set, so accents always land on '
             'the same notes of the chord. Off: it uses the fixed Cycle length.',
    'g:euc': 'On: the accent grid generates itself as E(k,n) -- k accents spread as evenly as the '
             'cycle allows -- and the toggles become a drawing of the result. Off: the grid is the '
             'one you drew by hand.',
    'g:eupuls': 'How many accents the generator spreads over the cycle. 3 over 8 gives the triplet '
                'feel, 5 over 8 the cinquillo, 5 over 16 the clave. More pulses than cells accents '
                'everything.',
    'g:eugir': 'Which cell the pattern starts on. The same E(k,n) rotated is a different rhythm -- '
               'it is the difference between the clave and its reverse.',
    'g:randacc': 'Fills the accent grid at random, within the current cycle length. How much gets '
                 'filled is the percentage beside it.',
    'g:randaccpct': 'What share of the cells inside the current accent cycle the random fill turns '
                    'on. Cells outside the cycle are cleared.',
    'g:velminn': 'Lowest velocity for unaccented notes. Each note is drawn at random between Min '
                 'and Max.',
    'g:velmaxn': 'Highest velocity for unaccented notes.',
    'g:velmina': 'Lowest velocity for accented notes.',
    'g:velmaxa': 'Highest velocity for accented notes.',
    'g:fign': 'Length of unaccented notes as a denominator: 4 = quarter, 8 = eighth, 16 = sixteenth.',
    'g:figa': 'Length of accented notes as a denominator: 4 = quarter, 8 = eighth, 16 = sixteenth.',
    'g:silnorm': 'Chance, in percent, that an unaccented step rests instead of playing.',
    'g:silacc': 'Chance, in percent, that an accented step rests instead of playing.',
    'g:silpre': 'Loads a ready-made pair of rest chances for the Normal and Accent groups -- a '
                'quick way to open up a dense part without dialling both by hand.',
    'g:ratn': 'How many times an unaccented note repeats (ratchet). 1 is a single note.',
    'g:rata': 'How many times an accented note repeats (ratchet). 1 is a single note.',
    'g:ratprob': 'How often the ratchet actually fires. At 100 always; at 30 one in three.',
    'g:ratcaida': 'How much velocity the roll loses between its first repeat and its last.',
    'g:ornt': 'Ornament type: how the extra notes sit around each principal tone -- infra-, inter- '
              'or ultrapolation, in Slonimsky\'s terms.',
    'g:ornnotas': 'How many ornament notes (1-4) are added around each principal tone.',
    'g:ornbase': 'Base interval in semitones (1-14) of the interval cycle the ornament is built '
                 'on. This is the Slonimsky ladder the principal tones climb.',
    'g:ornbasemode': 'Where the ornament\'s principal tones come from: Degrees (the current set), '
                     'Quadritone (a fixed four-note scheme), or Series (a generated progression).',
    'g:ornstep': 'The step the interval cycle climbs by, when the ornament\'s base is not taken '
                 'from the set.',
    'g:ornquad': 'Which quadritone scheme the principal tones follow, when the base mode is '
                 'Quadritone.',
    'g:serstart': 'First interval of the generated series the principal tones follow, when the '
                  'base mode is Series.',
    'g:serstep': 'How much the series grows at each step, when the base mode is Series.',
    'g:serpeak': 'Where the series turns around, when the base mode is Series.',
    'g:reparto': 'How this engine\'s notes are shared out over the bus -- which of them travel for '
                 'other devices to pick up.',
    'g:tirar': 'Throw: re-rolls everything the three switches beside it allow -- the set, the '
               'rests, the accents -- in one go.',
    'g:rndset': 'Include the set in what Throw re-rolls.',
    'g:rndsil': 'Include the rest chances in what Throw re-rolls.',
    'g:rndacc': 'Include the accent grid in what Throw re-rolls.',
    'g:slot': 'Which of the twenty preset slots Save, Load and Clear work on. The slot itself is '
              'in no preset: if it were, loading one would move the slot and the next click would '
              'land somewhere else.',
    'g:pguardar': 'Saves the current state into the selected slot.',
    'g:pcargar': 'Loads the selected slot.',
    'g:pborrar': 'Clears the selected slot.',

    # --- fs2setpick.js regions -------------------------------------------------------------
    'sp:bar': 'The shared voice bar: choose which voice this panel\'s picks are sent to, or Shared '
              'to aim at the global harmony. The colours are the same ones the Horizon view uses.',
    'sp:soltar': 'Releases the selected voice back to the shared harmony: turns its own key off so '
                 'it follows the global set and root again.',
    'sp:piano': 'The chromatic mask, as a keyboard. Click a key to let that pitch class through or '
                'block it. The keys are absolute pitches -- key C is C whatever the Root is.',
    'sp:maskgrid': 'Every set that currently passes the filter, coloured by its pitch content. '
                   'Click one to send it to the selected voice; the name above is the Forte label '
                   'of whichever one you are pointing at.',
    'sp:maskpage': 'Pages through the sets that pass the filter, when more of them pass than fit '
                   'on screen.',
    'sp:card': 'Narrows this list to sets of one cardinality -- one size of chord. Todos shows '
               'every size again.',
    'sp:zgrid': 'Z-pairs: two sets with the same interval vector that are not transpositions or '
                'inversions of each other. They measure identically and sound different, which is '
                'what makes them worth hearing side by side. Click one to assign it.',
    'sp:zpar': 'Splits the live voices between a set and its Z-mate: the first half take the set, '
               'the rest its partner. The same interval content in two different shapes, at once.',
    'sp:zpage': 'Pages through the Z-pairs list.',
    'sp:redpadres': 'Parents: every class you reach by REMOVING one pitch class from the current '
                    'set. Click one to give it to the selected voice, at the root that makes it '
                    'sound like the swatch you clicked.',
    'sp:redhijos': 'Children: every class you reach by ADDING one pitch class to the current set. '
                   'Click one to give it to the selected voice, at the root that makes it sound '
                   'like the swatch you clicked.',
    'sp:redback': 'Steps back to the previous set in the network, so you can wander the '
                  'parent/child graph and find your way home.',
}

# The six interval classes of the vector filter, and the four modulation slots: same sentence each
# time, so they are generated rather than copy-pasted twelve and twenty times over.
_IC = {1: 'semitones (ic1)', 2: 'whole tones (ic2)', 3: 'minor thirds (ic3)',
       4: 'major thirds (ic4)', 5: 'fourths (ic5)', 6: 'tritones (ic6)'}
for _k, _name in _IC.items():
    EN['g:vmin%d' % _k] = ('Fewest %s a set may contain and still pass the filter. The interval '
                           'vector counts how many of each interval class a set holds.' % _name)
    EN['g:vmax%d' % _k] = ('Most %s a set may contain and still pass the filter. The interval '
                           'vector counts how many of each interval class a set holds.' % _name)
for _k in range(1, 5):
    EN['g:mod%dshape' % _k] = 'Waveform of modulator %d: the shape of the value it sends.' % _k
    EN['g:mod%ddest' % _k] = ('What modulator %d moves. With the destination on "-" the modulator '
                              'runs but changes nothing.' % _k)
    EN['g:mod%dcycle' % _k] = 'How many steps one full cycle of modulator %d takes.' % _k
    EN['g:mod%ddepth' % _k] = 'How far modulator %d moves its destination. At 0 it leaves it alone.' % _k
    EN['g:mod%dphase' % _k] = ('Where in its cycle modulator %d starts, so several modulators can '
                               'run out of phase with each other.' % _k)

# Which file each key's table belongs in.
SETPICK_PREFIX = 'sp:'


def sha(s):
    return hashlib.sha1((s or '').encode('utf-8')).hexdigest()[:12]


def js_string(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def render(keys, texts):
    lines = [BEGIN, 'var HELP = {']
    for i, k in enumerate(sorted(keys)):
        comma = ',' if i < len(keys) - 1 else ''
        lines.append('\t%s: %s%s' % (js_string(k), js_string(texts[k]), comma))
    lines.append('};')
    lines.append(END)
    return '\n'.join(lines)


def write_block(path, block, apply_it):
    src = open(path, encoding='utf-8').read()
    i, j = src.index(BEGIN), src.index(END) + len(END)
    new = src[:i] + block + src[j:]
    if new == src:
        print('  %s: sin cambios' % path)
        return
    if apply_it:
        shutil.copyfile(path, path + '.before-help')
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(new)
    print('  %s: bloque HELP reescrito (%d entradas)' % (path, block.count('\n\t')))


def main():
    apply_it = '--apply' in sys.argv
    bless = '--bless' in sys.argv

    rows = resolve()
    chip_keys = [r[0] for r in rows]
    spanish = dict((r[0], r[3]) for r in rows)

    old = {}
    if os.path.exists(HASHES):
        old = json.load(open(HASHES, encoding='utf-8'))

    missing = [k for k in chip_keys if k not in EN]
    orphan = [k for k in EN if not k.startswith(SETPICK_PREFIX) and k not in chip_keys]
    stale = [k for k in chip_keys
             if spanish.get(k) and k in old and old[k] != sha(spanish[k])]
    unblessed = [k for k in chip_keys if spanish.get(k) and k not in old]

    print('chips dibujados: %d   textos en ingles: %d' % (len(chip_keys), len(EN)))
    print('chips SIN ayuda: %d%s' % (len(missing), ('  -> ' + ', '.join(missing)) if missing else ''))
    print('claves EN que ya no corresponden a ningun chip: %d%s'
          % (len(orphan), ('  -> ' + ', '.join(sorted(orphan))) if orphan else ''))
    print('ingles DESACTUALIZADO (su anotacion en espanol cambio): %d%s'
          % (len(stale), ('  -> ' + ', '.join(sorted(stale))) if stale else ''))
    if unblessed and old:
        print('sin registrar todavia (corre --bless): %d' % len(unblessed))

    if missing or orphan:
        print('\nARREGLA lo de arriba antes de escribir: cada chip dibujado necesita su entrada.')
        return 1

    hz_keys = [k for k in chip_keys]
    sp_keys = [k for k in EN if k.startswith(SETPICK_PREFIX)]

    print('\nbloques a escribir:')
    write_block(HORIZON, render(hz_keys, EN), apply_it)
    write_block(SETPICK, render(sp_keys, EN), apply_it)

    if bless and apply_it:
        fresh = dict((k, sha(spanish[k])) for k in chip_keys if spanish.get(k))
        with open(HASHES, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(fresh, f, indent=1, sort_keys=True)
        print('  %s: %d hashes registrados' % (HASHES, len(fresh)))
    elif bless:
        print('  (--bless sin --apply: no se registro nada)')

    if not apply_it:
        print('\n(dry run: no se escribio nada -- corre con --apply)')
    return 0


sys.exit(main())
