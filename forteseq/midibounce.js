// midibounce.js -- one-button MIDI Bounce for Max for Live.
//
// Reproduces sidebrain.net/midi-bounce: on a press it
//   1. creates a MIDI track directly to the right of this one,
//   2. routes that track's MIDI input from THIS track's Post-FX tap
//      (the MIDI *after* the arpeggiator / Scaler / scale / random / ... on this track),
//   3. optionally slams the Live tempo to 999 BPM (the "999 BPM" toggle, default on),
//   4. fires the selected Session clip on this track and records it onto the new track
//      for exactly its own length (Live's trigger_session_record auto-stops),
//   5. restores tempo, launch quantization and every track's arm state.
// With the "Disable FX after" toggle on it then also switches Device On to 0 on each
// MIDI effect of the source track (reversible -- it never deletes anything).
//
// House rules copied from forteseq2.js's Live-API code:
//   * guard on `typeof LiveAPI` so the file still loads under node / outside Live;
//   * ONE reusable LiveAPI object, re-pointed by .id, rather than dozens;
//   * wrap every API sequence in try/catch -- an uncaught throw halts the whole js
//     object in Live and the device goes dead with only a console line to show for it.

autowatch = 1;
inlets = 2;
outlets = 1;

var FAST_BPM = 999;

// Mirrors the parameter defaults in midibounce.amxd. Kept in an object so the message
// handlers below (which MUST be named `fast` / `disablefx` / `lenbars` for Max to route to
// them) don't collide with the state they write.
//   lenbars: 0 = use the selected clip's own length; >0 = record that many bars instead.
var opt = { fast: 1, disablefx: 0, lenbars: 0 };

var busy = 0;      // a bounce is in flight; a second press is refused until it finishes

// ---- inlet 0: the button ---------------------------------------------------------------
function bang() { bounce(); }
function msg_int(v) { if (v) bounce(); }   // live.text button sends 1 on press, 0 on release

// ---- inlet 1: the toggles ------------------------------------------------------------
function fast(v) { opt.fast = v ? 1 : 0; }
function disablefx(v) { opt.disablefx = v ? 1 : 0; }
function lenbars(v) { v = Math.round(Number(v)); opt.lenbars = (isFinite(v) && v > 0) ? v : 0; }

// ---- small helpers ------------------------------------------------------------------
function first(v) { return (v && typeof v.join === "function") ? v[0] : v; }
function jname(raw) { return (raw && typeof raw.join === "function") ? raw.join(" ") : ("" + raw); }

function tailIndex(pathStr) {
	var m = ("" + pathStr).match(/(\d+)\s*"?\s*$/);
	return m ? parseInt(m[1], 10) : -1;
}

// create_midi_track / get("canonical_parent") come back as ["id", N] under the js object
// but as the string "id N" in some hosts -- take the first number either way.
function idFromReturn(ret) {
	if (ret && typeof ret.join === "function") {
		for (var i = 0; i < ret.length; i++) if (typeof ret[i] === "number") return ret[i];
	}
	var m = ("" + ret).match(/(\d+)/);
	return m ? parseInt(m[1], 10) : 0;
}

// A routing property takes the whole {display_name, identifier} object. h1data's ioRouting.js
// passes the parsed object straight to set(); if this host rejects that, retry as a JSON string.
function setRouting(track, prop, obj) {
	try { track.set(prop, obj); return true; } catch (e) {}
	try { track.set(prop, JSON.stringify(obj)); return true; } catch (e2) {}
	post("midibounce: could not set " + prop + "\n");
	return false;
}

function routePostFx(newTrack, srcName) {
	var types = JSON.parse(newTrack.get("available_input_routing_types")).available_input_routing_types;
	var chosen = null;
	for (var i = 0; i < types.length; i++) {
		if (("" + types[i].display_name) === srcName) { chosen = types[i]; break; }
	}
	if (!chosen) {
		for (var j = 0; j < types.length; j++) {
			if (("" + types[j].display_name).indexOf(srcName) === 0) { chosen = types[j]; break; }
		}
	}
	if (!chosen) { post('midibounce: no input-routing type named "' + srcName + '"\n'); return false; }
	if (!setRouting(newTrack, "input_routing_type", chosen)) return false;

	// The channel list only becomes the source track's taps AFTER the type is set.
	var chans = JSON.parse(newTrack.get("available_input_routing_channels")).available_input_routing_channels;
	var pf = null;
	for (var k = 0; k < chans.length; k++) {
		if (/post[\s-]?fx/i.test("" + chans[k].display_name)) { pf = chans[k]; break; }
	}
	if (!pf && chans.length > 1) pf = chans[1];   // order is Pre FX / Post FX / Post Mixer / inserts...
	if (!pf) { post("midibounce: no Post-FX channel on that track\n"); return false; }
	return setRouting(newTrack, "input_routing_channel", pf);
}

function restoreArms(arms) {
	var t = new LiveAPI(null);
	for (var a = 0; a < arms.length; a++) {
		if (!arms[a].canArm) continue;
		try { t.id = arms[a].id; t.set("arm", arms[a].arm); } catch (e) {}
	}
}

function isMidiEffect(d) {
	try {
		var ty = first(d.get("type"));                     // Live 11: 1 instrument, 2 audio fx, 4 midi fx
		if (ty === 4 || ty === "midi_effect") return true;
		if (ty === 1 || ty === 2 || ty === "instrument" || ty === "audio_effect") return false;
	} catch (e) {}
	try {
		var cn = "" + first(d.get("class_name"));
		return /Arpeggiator|Chord|Note ?Length|Pitch|Random|Scale|Velocity/i.test(cn);
	} catch (e2) {}
	return false;
}

function disableSourceFx(trackIndex) {
	try {
		var track = new LiveAPI(null, "live_set tracks " + trackIndex);
		var devIds = track.get("devices");
		var d = new LiveAPI(null), p = new LiveAPI(null), n = 0;
		for (var i = 0; i < devIds.length; i++) {
			if (typeof devIds[i] !== "number") continue;
			d.id = devIds[i];
			if (!isMidiEffect(d)) continue;
			var params = d.get("parameters");
			for (var j = 0; j < params.length; j++) {
				if (typeof params[j] !== "number") continue;
				p.id = params[j];                 // parameters[0] is always "Device On"
				p.set("value", 0);
				n++;
				break;
			}
		}
		post("midibounce: disabled " + n + " MIDI effect(s) on the source track\n");
	} catch (e) {
		post("midibounce: disablefx failed -- " + e + "\n");
	}
}

// ---- the bounce -------------------------------------------------------------------
function bounce() {
	if (typeof LiveAPI === "undefined") { post("midibounce: no Live API (running outside Live)\n"); return; }
	if (busy) { post("midibounce: a bounce is already running\n"); return; }

	var song = new LiveAPI(null, "live_set");
	var saved = null, undoOpen = false;

	try {
		// 1. this track + the clip to bounce ------------------------------------------
		var dev = new LiveAPI(null, "this_device");
		var srcTrack = new LiveAPI(null);
		srcTrack.id = idFromReturn(dev.get("canonical_parent"));
		var srcIndex = tailIndex(srcTrack.path);
		if (srcIndex < 0) { post("midibounce: can't locate this track\n"); return; }
		var srcName = jname(srcTrack.get("name"));

		var hi = new LiveAPI(null, "live_set view highlighted_clip_slot");
		var sceneIndex = tailIndex(hi.path);
		if (sceneIndex < 0) { post("midibounce: select a clip slot in Session view first\n"); return; }
		var base = "live_set tracks " + srcIndex + " clip_slots " + sceneIndex;
		var srcSlot = new LiveAPI(null, base);
		if (first(srcSlot.get("has_clip")) != 1) {
			post("midibounce: no clip on this track at the selected scene\n"); return;
		}
		var srcClip = new LiveAPI(null, base + " clip");
		var lenBeats = Number(first(srcClip.get("length")));
		if (!isFinite(lenBeats) || lenBeats <= 0) { post("midibounce: that clip has no length\n"); return; }

		// "Length (bars)" override: 0 = use the clip length above. Clip/beat units are quarter
		// notes, so bars -> beats scales by the set's time signature.
		if (opt.lenbars > 0) {
			var sn = 4, sd = 4;
			try { sn = Number(first(song.get("signature_numerator"))) || 4; } catch (e) {}
			try { sd = Number(first(song.get("signature_denominator"))) || 4; } catch (e) {}
			var beatsPerBar = sn * 4 / sd;
			if (isFinite(beatsPerBar) && beatsPerBar > 0) lenBeats = opt.lenbars * beatsPerBar;
		}

		// 2. snapshot everything we are about to touch --------------------------------
		saved = {
			tempo: Number(first(song.get("tempo"))),
			quant: first(song.get("clip_trigger_quantization")),
			arms: [],
			changedTempo: false
		};
		var trackIds = song.get("tracks");
		var t = new LiveAPI(null);
		for (var i = 0; i < trackIds.length; i++) {
			if (typeof trackIds[i] !== "number") continue;
			t.id = trackIds[i];
			var canArm = first(t.get("can_be_armed")) ? 1 : 0;
			saved.arms.push({ id: trackIds[i], canArm: canArm, arm: canArm ? first(t.get("arm")) : 0 });
		}

		// 3. one undo step for the whole thing ---------------------------------------
		song.call("begin_undo_step");
		undoOpen = true;

		// 4. the bounce track ------------------------------------------------------
		var newId = idFromReturn(song.call("create_midi_track", srcIndex + 1));
		if (!newId) { post("midibounce: track creation failed\n"); song.call("end_undo_step"); return; }
		var newTrack = new LiveAPI(null);
		newTrack.id = newId;
		try { newTrack.set("name", srcName + " BOUNCE"); } catch (e) {}

		// 5. route its input from the source track's Post-FX tap ----------------------
		routePostFx(newTrack, srcName);

		// 6. arm ONLY the bounce track (restored in finish) --------------------------
		for (var a = 0; a < saved.arms.length; a++) {
			if (!saved.arms[a].canArm) continue;
			try { t.id = saved.arms[a].id; t.set("arm", 0); } catch (e) {}
		}
		newTrack.set("arm", 1);
		try { newTrack.set("current_monitoring_state", 0); } catch (e) {}   // 0 = In
		try { new LiveAPI(null, "live_set view").set("selected_track", newId); } catch (e) {}

		// 7. no launch quantize; optionally go fast --------------------------------
		try { song.set("clip_trigger_quantization", 0); } catch (e) {}
		var effTempo = saved.tempo;
		if (opt.fast) {
			song.set("tempo", FAST_BPM);
			saved.changedTempo = true;
			effTempo = FAST_BPM;
		}

		// 8. play the source clip, record the new track for exactly lenBeats ---------
		srcSlot.call("fire");
		song.call("trigger_session_record", lenBeats);

		// 9. schedule the restore. trigger_session_record auto-stops the recording at
		//    lenBeats; this Task only has to clean up afterwards, so a fixed delay off
		//    the known length + a margin is enough -- no observer needed.
		busy = 1;
		var ctx = { song: song, saved: saved, srcIndex: srcIndex, newId: newId, done: 0 };
		var task = new Task(function () { finish(ctx); }, this);
		task.schedule(lenBeats * (60000 / effTempo) + 600);

		post("midibounce: bouncing " + lenBeats + " beats"
			+ (opt.lenbars > 0 ? " (" + opt.lenbars + " bars)" : "") + " at "
			+ (opt.fast ? FAST_BPM : Math.round(effTempo)) + ' BPM -> "' + srcName + ' BOUNCE"\n');

	} catch (err) {
		post("midibounce: aborted -- " + err + "\n");
		if (saved) {
			try { if (saved.changedTempo) song.set("tempo", saved.tempo); } catch (e) {}
			try { song.set("clip_trigger_quantization", saved.quant); } catch (e) {}
			restoreArms(saved.arms);
		}
		if (undoOpen) { try { song.call("end_undo_step"); } catch (e) {} }
		busy = 0;
	}
}

function finish(ctx) {
	if (ctx.done) return;
	ctx.done = 1;
	var song = ctx.song, saved = ctx.saved;

	try { song.call("stop_playing"); } catch (e) {}
	try { song.set("clip_trigger_quantization", saved.quant); } catch (e) {}
	try { if (saved.changedTempo) song.set("tempo", saved.tempo); } catch (e) {}

	try {
		var nt = new LiveAPI(null);
		nt.id = ctx.newId;
		nt.set("arm", 0);
		nt.set("current_monitoring_state", 1);   // 1 = Auto, so it stops eating input
	} catch (e) {}

	restoreArms(saved.arms);
	if (opt.disablefx) disableSourceFx(ctx.srcIndex);

	try { song.call("end_undo_step"); } catch (e) {}
	post("midibounce: done\n");
	busy = 0;
}
