// wf_levelviz.js -- jsui level-ladder for forteseqwf. A row of MAX_LEVELS cells: cells
// 0..levelCount-1 are the levels the hierarchy actually built THIS cycle (can be fewer than the
// Levels control asks for -- see forteseqwf.js's wfHierarchy comment: an earlier level coming out
// isochronous, r=1, stops the hierarchy there on its own), remaining cells are grayed out.
//
// Each built cell shows its r-value and its pulse count (word length). The isochronous (terminal)
// level, if reached, is amber and shows the pulse count large -- "this is where it stopped, and
// this is how many equal pulses the grid has."
//
// The engine also probes the r-recursion FORWARD past the Levels cap (isochronyOutlook), so:
//   * if isochrony would be reached at a level beyond what was built, that future cell is drawn
//     dim-amber with the predicted pulse count;
//   * if r never reaches 1 (the metallic ratios cycle, generic irrationals wander), an infinity
//     glyph is drawn -- "deeply non-isochronous".
//
// Fed by forteseqwf.js's tag-0 diagnostic on its single outlet, with the leading 0 stripped by
// `wf_diag = route 0`, so list() receives:
//   levelCount  r[0..k-1]  pulses[0..k-1]  isoLevel  isoPulses  isoCapped
// The pulses/iso tail is optional -- an older engine sends just (levelCount, r0..r{k-1}) and the
// ladder still draws. MAX_LEVELS mirrors forteseqwf.js's MAX_LEVELS=6.

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var MAX_LEVELS = 6;
var ISO_EPS = 1e-6;

var levelCount = 0;
var rvals = [];
var lens = [];
var isoLevel = -1;      // 0-based hierarchy level where r == 1, or -1
var isoPulses = -1;     // pulse count of that isochronous grid, or -1
var isoCapped = 0;      // 1 = r never reaches 1 within the probe budget
var haveOutlook = false;

function list() {
	var a = arrayfromargs(arguments);
	levelCount = Math.max(0, Math.min(MAX_LEVELS, Math.round(a[0] || 0)));
	rvals = a.slice(1, 1 + levelCount);
	lens = a.slice(1 + levelCount, 1 + 2 * levelCount);
	haveOutlook = a.length >= 1 + 2 * levelCount + 3;
	if (haveOutlook) {
		isoLevel = Math.round(a[1 + 2 * levelCount]);
		isoPulses = Math.round(a[2 + 2 * levelCount]);
		isoCapped = Math.round(a[3 + 2 * levelCount]);
	} else {
		isoLevel = -1; isoPulses = -1; isoCapped = 0;
	}
	mgraphics.redraw();
}

function paint() {
	var width = box.rect[2] - box.rect[0];
	var height = box.rect[3] - box.rect[1];
	var cellW = width / MAX_LEVELS;
	var i, r, x, isIso, predictHere;

	mgraphics.set_source_rgba([0.12, 0.12, 0.12, 1]);
	mgraphics.rectangle(0, 0, width, height);
	mgraphics.fill();
	mgraphics.select_font_face('Arial');

	for (i = 0; i < MAX_LEVELS; i++) {
		x = i * cellW;
		r = (i < levelCount) ? rvals[i] : null;
		isIso = (r !== null) && Math.abs(r - 1) < ISO_EPS;
		// isochrony predicted for THIS cell, which the Levels cap didn't build
		predictHere = haveOutlook && !isoCapped && isoLevel === i && i >= levelCount;

		if (i < levelCount) {
			mgraphics.set_source_rgba(isIso ? [1, 0.73, 0, 1] : [0.25, 0.6, 0.95, 1]);
		} else if (predictHere) {
			mgraphics.set_source_rgba([0.5, 0.4, 0.13, 1]);
		} else {
			mgraphics.set_source_rgba([0.28, 0.28, 0.28, 1]);
		}
		mgraphics.rectangle(x + 2, 2, cellW - 4, height - 4);
		mgraphics.fill();

		if (i < levelCount) {
			mgraphics.set_source_rgba([0, 0, 0, 1]);
			mgraphics.set_font_size(9);
			mgraphics.move_to(x + 4, 12);
			mgraphics.show_text(isIso ? 'iso' : ('r' + r.toFixed(2)));
			if (lens.length > i) {
				mgraphics.set_font_size(isIso ? 13 : 9);
				mgraphics.move_to(x + 4, isIso ? 27 : 24);
				mgraphics.show_text(String(Math.round(lens[i])));
			}
		} else if (predictHere) {
			mgraphics.set_source_rgba([0.92, 0.92, 0.92, 1]);
			mgraphics.set_font_size(9);
			mgraphics.move_to(x + 4, 12);
			mgraphics.show_text('iso');
			mgraphics.set_font_size(13);
			mgraphics.move_to(x + 4, 27);
			mgraphics.show_text(String(isoPulses));
		}
	}

	// r never reaches 1 (metallic ratio cycles / generic irrational wanders), or it would but
	// deeper than the 6-cell strip: a word in the rightmost still-empty cell. The common
	// "isochrony reached within the built ladder" case needs nothing here -- its amber cell says it.
	if (haveOutlook && (isoCapped || isoLevel < 0 || isoLevel >= MAX_LEVELS)
		&& !(isoLevel >= 0 && isoLevel < levelCount) && levelCount < MAX_LEVELS) {
		x = (MAX_LEVELS - 1) * cellW;
		mgraphics.set_source_rgba([0.82, 0.5, 0.5, 1]);
		mgraphics.set_font_size(10);
		mgraphics.move_to(x + 4, 12);
		mgraphics.show_text('no iso');
		if (!isoCapped && isoLevel >= MAX_LEVELS) {
			mgraphics.set_font_size(9);
			mgraphics.move_to(x + 4, 24);
			mgraphics.show_text('L' + (isoLevel + 1));
		}
	}
}
