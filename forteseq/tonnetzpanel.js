// tonnetz -- adaptive per-view control strip (mirror of animidipanel.js).
//
// Lives in the tz_window subpatcher as [js tonnetzpanel.js].  The header is two rows that
// never move: row 1 (y 8) the panel + mode toggles, row 2 (y 38) the globals.  Everything
// else is a group that shows only while its visual panel is on.  Visible groups pack
// upward into dynamic slots at y 68 / 98 / 128, and the jsui canvas top (tonnetz.js
// BOX_TOP) follows via striph() so the freed vertical space goes back to the drawing.
//
// Inlet messages -- tapped off each toggle's existing [prepend <sel>] helper, plus loadbang:
//   vton vchr vfif vvoc vpno vgtr vdia vtet vcol xfprev harmmode <0/1>
//   studymode <0/1>   -- tapped off obj-318 [prepend studymode]
//   bang / loadbang   -- re-apply (safety)
// Outlets:
//   0 -> thispatcher : "script show|hide <name>" per member, then "script move <name> <x> <y>"
//   1 -> jsui        : "striph <canvasTop>"   canvasTop = 68 + 30 * (packed dynamic rows)
//
// The union of every GROUPS member name must equal the set of hidden:1 group boxes in the
// patch -- relayout_tonnetz_panels.py asserts it.  x / yoff must match the authored rects
// in that script (yoff 0 for toggle/menu/tab/text, 2 for numbox/comment).

autowatch = 1;
outlets = 2;

var HEADER_H = 68;   // two 30 px header rows starting at y 8
var ROW_H = 30;

var f = { vton: 0, vchr: 0, vfif: 0, vvoc: 0, vpno: 0, vgtr: 0, vdia: 0, vtet: 0,
          vcol: 0, xfprev: 0, harmmode: 0, study: 0 };

var GROUPS = {
	tonnetz: { row: 0, m: [
		["tzw_preset", 8, 0], ["tzw_lb154_40", 152, 2], ["tzw_tona", 182, 2],
		["tzw_tonb", 210, 2], ["tzw_tonc", 238, 2], ["tzw_harmonize", 276, 0],
		["tzw_lb96_68", 294, 2], ["tzw_faces", 350, 0], ["tzw_lb166_68", 368, 2],
		["tzw_plr", 424, 0], ["tzw_lb26_128", 442, 2], ["tzw_regtrace", 488, 0],
		["tzw_lb374_128", 506, 2], ["tzw_autofit", 566, 0], ["tzw_lb452_128", 584, 2] ] },
	circles: { row: 0, m: [
		["tzw_lb_conex", 636, 2], ["tzw_conex", 672, 0], ["tzw_tracepath", 752, 0],
		["tzw_lb306_68", 770, 2] ] },
	tet: { row: 0, m: [
		["tzw_lb420_40", 830, 2], ["tzw_tetpreset", 848, 0] ] },
	pnogtr: { row: 1, m: [
		["tzw_pianomode", 8, 0], ["tzw_guitarmode", 100, 0], ["tzw_tuning", 202, 0],
		["tzw_lb296_100", 290, 2], ["tzw_frets", 322, 2], ["tzw_lb360_100", 352, 2],
		["tzw_zoom", 384, 2], ["tzw_lb424_100", 414, 2], ["tzw_pan", 440, 2] ] },
	diat: { row: 1, m: [
		["tzw_key", 486, 0], ["tzw_keymode", 544, 0], ["tzw_keyauto", 632, 0],
		["tzw_lb497_8", 648, 2] ] },
	colorharm: { row: 1, m: [
		["tzw_lb726_70", 694, 2], ["tzw_anwin", 732, 2], ["tzw_reset", 772, 0] ] },
	xform: { row: 1, m: [
		["tzw_xfmode", 836, 0], ["tzw_lb236_128", 952, 2], ["tzw_xpose", 984, 2],
		["tzw_lb298_128", 1014, 2], ["tzw_invc", 1036, 2] ] },
	study: { row: 2, m: [
		["tzw_lb72_158", 8, 2], ["tzw_studycard", 38, 2], ["tzw_lb128_158", 64, 2],
		["tzw_studyidx", 74, 2], ["tzw_lb174_158", 108, 2], ["tzw_studyrot", 128, 2],
		["tzw_lb222_158", 156, 2], ["tzw_studytonic", 178, 0], ["tzw_studyinv", 232, 0],
		["tzw_lb316_158", 250, 2], ["tzw_disssort", 276, 0], ["tzw_lb360_158", 294, 2],
		["tzw_studytrav", 318, 0], ["tzw_lb508_158", 442, 2], ["tzw_studymove", 468, 0] ] }
};

function wantVisible() {
	return {
		tonnetz:   f.vton,
		circles:   f.vchr || f.vfif,
		tet:       f.vtet,
		pnogtr:    f.vpno || f.vgtr,
		diat:      f.vdia,
		colorharm: f.vcol || f.harmmode,
		xform:     f.xfprev,
		study:     f.study
	};
}

function apply() {
	var vis = wantVisible();
	var g, i, mm;

	// 1. show / hide every member
	for (g in GROUPS) {
		var cmd = vis[g] ? "show" : "hide";
		mm = GROUPS[g].m;
		for (i = 0; i < mm.length; i++) outlet(0, "script", cmd, mm[i][0]);
	}

	// 2. which physical rows carry a visible group
	var rowOn = [0, 0, 0];
	for (g in GROUPS) if (vis[g]) rowOn[GROUPS[g].row] = 1;

	// 3. pack visible rows upward; move their members into the packed slot
	var slot = 0, r, y;
	for (r = 0; r < 3; r++) {
		if (!rowOn[r]) continue;
		y = HEADER_H + slot * ROW_H;
		for (g in GROUPS) {
			if (!vis[g] || GROUPS[g].row !== r) continue;
			mm = GROUPS[g].m;
			for (i = 0; i < mm.length; i++)
				outlet(0, "script", "move", mm[i][0], mm[i][1], y + mm[i][2]);
		}
		slot++;
	}

	// 4. canvas top follows the packed-row count
	outlet(1, "striph", HEADER_H + slot * ROW_H);
}

function setflag(k, v) { f[k] = v ? 1 : 0; apply(); }

function vton(v)      { setflag("vton", v); }
function vchr(v)      { setflag("vchr", v); }
function vfif(v)      { setflag("vfif", v); }
function vvoc(v)      { setflag("vvoc", v); }
function vpno(v)      { setflag("vpno", v); }
function vgtr(v)      { setflag("vgtr", v); }
function vdia(v)      { setflag("vdia", v); }
function vtet(v)      { setflag("vtet", v); }
function vcol(v)      { setflag("vcol", v); }
function xfprev(v)    { setflag("xfprev", v); }
function harmmode(v)  { setflag("harmmode", v); }
function studymode(v) { setflag("study", v); }
function bang()       { apply(); }
function loadbang()   { apply(); }
