// wf_levelviz.js -- jsui level-ladder for forteseqwf. Draws MAX_LEVELS cells in a row: cells
// 0..levelCount-1 are the levels the hierarchy actually built THIS cycle (can be fewer than the
// Levels control asks for -- see forteseqwf.js's wfHierarchy comment: an earlier level coming out
// isochronous, r=1, stops the hierarchy there on its own), remaining cells are grayed out. The
// isochronous (terminal) level, if reached, is colored differently from the others so it reads at
// a glance as "this is where it stopped, not just where you happened to look."
//
// Fed by forteseqwf.js's diagnostic message on its single outlet (tag 0, reserved -- see fireNote's
// comment there): a bare list (0, levelCount, r0, r1, ...) with the leading 0 already stripped by
// the `wf_diag = route 0` object between wf_engine and this jsui, so `list()` below receives just
// (levelCount, r0, r1, ...). MAX_LEVELS mirrors forteseqwf.js's own MAX_LEVELS=6 -- both encode the
// same fact (how many levels the engine can ever build) and must be kept in sync if either changes.

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var MAX_LEVELS = 6;
var ISO_EPS = 1e-6;

var levelCount = 0;
var rvals = [];

function list() {
	var a = arrayfromargs(arguments);
	levelCount = Math.max(0, Math.min(MAX_LEVELS, Math.round(a[0] || 0)));
	rvals = a.slice(1, 1 + levelCount);
	mgraphics.redraw();
}

function paint() {
	var width = box.rect[2] - box.rect[0];
	var height = box.rect[3] - box.rect[1];
	var cellW = width / MAX_LEVELS;
	var i, r, isIso, x;

	mgraphics.set_source_rgba([0.12, 0.12, 0.12, 1]);
	mgraphics.rectangle(0, 0, width, height);
	mgraphics.fill();

	for (i = 0; i < MAX_LEVELS; i++) {
		x = i * cellW;
		if (i < levelCount) {
			r = rvals[i];
			isIso = Math.abs(r - 1) < ISO_EPS;
			if (isIso) {
				mgraphics.set_source_rgba([1, 0.73, 0, 1]);   // terminal level: hierarchy stopped here
			} else {
				mgraphics.set_source_rgba([0.25, 0.6, 0.95, 1]); // ordinary built level
			}
		} else {
			mgraphics.set_source_rgba([0.28, 0.28, 0.28, 1]); // not reached this cycle
		}
		mgraphics.rectangle(x + 2, 2, cellW - 4, height - 4);
		mgraphics.fill();

		if (i < levelCount) {
			mgraphics.set_source_rgba([0, 0, 0, 1]);
			mgraphics.select_font_face('Arial');
			mgraphics.set_font_size(9);
			mgraphics.text_measure(String(i + 1));
			mgraphics.move_to(x + 4, height - 4);
			mgraphics.show_text(String(i + 1));
			mgraphics.move_to(x + 4, height / 2 + 3);
			mgraphics.show_text(r.toFixed(2));
		}
	}
}
