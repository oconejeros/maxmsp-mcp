// animidifeed.js -- the engine of ANIMIDIFeed.amxd, a tiny MIDI-effect device dropped on
// every track whose notes you want to see grouped as a separate voice in ANIMIDI.
//
// It forwards this track's note on/offs onto the cross-device bus `ANIMIDI_NOTE` (a Max
// `send`, global across the whole Live set's embedded Max process -- the same mechanism as
// FORTESEQ v2's `FORTESEQ_TRIG`, see the forteseq-v2-architecture memory), tagged with this
// device's own Live track index so ANIMIDI can tell the voices apart.
//
// House rules from forteseq2.js / midibounce.js: guard on `typeof LiveAPI`, ONE reusable
// LiveAPI object, wrap every API call in try/catch (an uncaught throw kills the js object).
//
// Patch wiring (see tools/build_animidifeed.py):
//   midiin -> midiout                       (pass-through: the track still plays its instrument)
//   notein -> pack 0 0 -> prepend n -> here
//   live.thisdevice -> bang -> here         (re-resolve the track index on load)
//   live.numbox "Voz" -> prepend voz -> here   (-1 = auto index, >=0 = force)
// Outlet 0: `feed <pitch> <vel> <trackIdx>` -> route feed -> pack 0 0 0 -> send ANIMIDI_NOTE

autowatch = 1;
inlets = 1;
outlets = 1;

var myIdx = -1;      // resolved Live track index
var override = -1;   // Voz control: -1 = auto, >=0 = forced

function idOf(ret) {
	if (!ret) return 0;
	for (var i = 0; i < ret.length; i++) if (ret[i] === "id") return ret[i + 1];
	return 0;
}
function trackIndexFromPath(p) {
	var m = String(p).match(/tracks (\d+)/);
	return m ? parseInt(m[1], 10) : -1;
}
function resolve() {
	myIdx = -1;
	if (typeof LiveAPI === "undefined") return;
	try {
		var dev = new LiveAPI(null, "this_device");
		var trk = new LiveAPI(null);
		trk.id = idOf(dev.get("canonical_parent"));
		myIdx = trackIndexFromPath(trk.path);
	} catch (e) { myIdx = -1; }
}
resolve();

function bang() { resolve(); }
function refresh() { resolve(); }
function voz(v) { override = Math.round(v); }

// a note from the patch: `n <pitch> <vel>` (vel 0 = note-off)
function n(pitch, vel) {
	var idx = (override >= 0) ? override : myIdx;
	if (idx < 0) idx = 0;
	outlet(0, "feed", Math.round(pitch), Math.round(vel), idx);
}
function msg_int(v) { n(v, 127); }

post("animidifeed.js cargado — pista " + myIdx + "\n");
