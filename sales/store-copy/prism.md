# Prism — store copy

Source for the maxforlive.com listing (Prism is **free**, distributed there like ANIMIDI)
and seed for `release/Prism/README.txt`. **English only.** (ex-invertedprism.)

---

## Title

**Prism — Turn colour into chords for Ableton Live**

## Hook

Drop points of colour on a canvas. Where they land decides the chord: left-to-right is the
circle of fifths, top-to-bottom is register. Drag them and the chord follows, live.

## What it does

- **Colour → chord**: each point's horizontal position picks a root (circle-of-fifths
  wheel), vertical position sets its register. The blended colour of all active points
  becomes one chord — its hue picks the root, saturation picks how dense/dissonant it is,
  lightness picks the octave.
- **Three mixing models**: subtractive (pigment — opposite colours muddy toward black),
  additive (light — opposite colours brighten toward white), OKLab (perceptual average,
  the clearest default).
- **Polychords**: group points (shift-click cycles a point's group, up to 4) and each
  group blends into its own chord — all groups sound together, stacked.
- **Reharmoniser**: play into it and a swatch shows the colour of the chord you're
  actually playing, live — the colour↔harmony map runs both directions.
- **Split**: the inverse operation — hands you back a set of colour points whose blend
  matches a target chord or colour.

## Requirements

- Ableton Live 12 or later with **Max for Live**.
- MIDI-effect device on a track feeding an instrument.

## Price

**Free.** No watermark, no time limit.

Prism pairs with **Color Theory**, the deeper harmony visualizer in the
**Conejeros MIDI Creative Pack** — same colour-by-pitch-class idea, eight linked views and
a 351-set-class study mode.

## FAQ

- **Do I need to know music theory?** No — drop colours, hear chords.
- **Can I use it to reharmonise what I'm already playing?** Yes, that's the swatch in the
  corner — it shows the colour of your incoming MIDI in real time.
- **Does it expire?** No.
