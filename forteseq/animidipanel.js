// ANIMIDI -- per-view control row: which of the row-3 groups is shown.
//
// Lives in the an_window subpatcher as [js animidipanel.js]. The header is three rows:
// row 1 selectors, row 2 globals (range + colour + AnWin + Clear + the Panel toggle),
// row 3 the per-view controls -- and row 3 is the only thing this script touches.
//
// Inlet messages:
//   panel <0/1>      -- the "Panel" live.toggle (aw_settings): show/hide the whole row 3
//   viewmode <0..3>  -- tapped off aw_pp_viewmode (Barras/Espiral/Dodecaedro/Practica)
//   timemode <0/1>   -- tapped off aw_pp_timemode (Tiempo real / Lookahead)
//   bang             -- re-apply (loadbang safety)
// Outlets:
//   0 -> thispatcher : "script show <name>" / "script hide <name>" per row-3 box
//   1 -> jsui        : "striph <canvasTop>"  (58 row-3 hidden, 84 shown) so animidi.js's
//                       fitToWindow() gives the row's height back to the canvas.
//
// The union of GROUPS must equal the row-3 box set that the reorg script keeps hidden:1.
// A group shows only when the Panel toggle is on AND it applies to the current state:
//   barras -> viewMode 0                 scale  -> viewMode 0 or 3 (Barras + Practica)
//   curvas -> viewMode 1 or 2            clip   -> timeMode 1 (Lookahead)

autowatch = 1;
outlets = 2;

var panelOn = 1;
var viewMode = 0;
var timeMode = 0;

var GROUPS = {
	barras: ["aw_lb436_10", "aw_grid", "aw_lb740_72", "aw_piano", "aw_lb800_72",
	         "aw_vellane", "aw_lb846_72", "aw_notetags", "aw_lb906_72", "aw_harmlane"],
	scale:  ["aw_lb8_42", "aw_scale"],
	curvas: ["aw_lb440_72", "aw_spin", "aw_lb590_72", "aw_spinmode",
	         "aw_lb510_72", "aw_ringgap", "aw_lb366_72", "aw_tracelen"],
	clip:   ["aw_readclip"]
};

var STRIP_LO = 60;   // canvas top when the Panel toggle hides row 3
var STRIP_HI = 92;   // canvas top when row 3 is shown  (must match animidi.js STRIP_H default)

function wantVisible() {
	return {
		barras: panelOn && viewMode === 0,
		scale:  panelOn && (viewMode === 0 || viewMode === 3),
		curvas: panelOn && (viewMode === 1 || viewMode === 2),
		clip:   panelOn && timeMode === 1
	};
}

function apply() {
	var vis = wantVisible();
	for (var g in GROUPS) {
		var cmd = vis[g] ? "show" : "hide";
		var names = GROUPS[g];
		for (var i = 0; i < names.length; i++) {
			outlet(0, "script", cmd, names[i]);
		}
	}
	outlet(1, "striph", panelOn ? STRIP_HI : STRIP_LO);
}

function panel(v)    { panelOn  = v ? 1 : 0;           apply(); }
function viewmode(v) { viewMode = Math.max(0, v | 0);  apply(); }
function timemode(v) { timeMode = v ? 1 : 0;           apply(); }
function bang()      { apply(); }
function loadbang()  { apply(); }
