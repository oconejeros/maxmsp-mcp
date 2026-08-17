autowatch = 1;
inlets = 1;
outlets = 0;

var NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
var CIRCLE = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5];   // pitch classes in circle-of-fifths order, clockwise from top
var activeSet = [];

function list() {
	activeSet = arrayfromargs(arguments);
	mgraphics.redraw();
}

function msg_int(i) {
	activeSet = [i];
	mgraphics.redraw();
}

function paint() {
	var w = box.rect[2] - box.rect[0];
	var h = box.rect[3] - box.rect[1];
	var cx = w / 2, cy = h / 2;
	var r = Math.min(w, h) / 2 - 16;

	mgraphics.set_source_rgba(0.14, 0.14, 0.14, 1);
	mgraphics.rectangle(0, 0, w, h);
	mgraphics.fill();

	for (var i = 0; i < 12; i++) {
		var pc = CIRCLE[i];
		var ang = (Math.PI * 2 * i / 12) - Math.PI / 2;
		var x = cx + r * Math.cos(ang);
		var y = cy + r * Math.sin(ang);
		var active = activeSet.indexOf(pc) >= 0;

		mgraphics.set_line_width(1.5);
		if (active) {
			mgraphics.set_source_rgba(0.594, 0.72, 0.928, 1);
			mgraphics.ellipse(x - 13, y - 13, 26, 26);
			mgraphics.fill();
			mgraphics.set_source_rgba(0.1, 0.1, 0.1, 1);
		} else {
			mgraphics.set_source_rgba(0.45, 0.45, 0.45, 1);
			mgraphics.ellipse(x - 13, y - 13, 26, 26);
			mgraphics.stroke();
			mgraphics.set_source_rgba(0.7, 0.7, 0.7, 1);
		}
		mgraphics.select_font_face("Arial Bold");
		mgraphics.set_font_size(10);
		mgraphics.move_to(x - 8, y + 4);
		mgraphics.show_text(NOTE_NAMES[pc]);
	}
}
