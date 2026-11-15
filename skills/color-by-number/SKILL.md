---
name: color-by-number
description: Make a printable kids' color-by-number page (Letter, 300 dpi) plus a coloured answer key from a subject like "a bunny in a meadow". Image model draws the line art; cbn.py places every number exactly. Use when asked for a color-by-number, paint-by-number or numbered coloring page.
---

# Color by number

Image models can't put the right number in the right region (they draw a "3" on an ear and a "7"
that matches nothing). So the work is split:

1. **The image model draws line art only**: bold closed outlines, big simple regions, no text.
2. **`cbn.py` does the numbers**: labels every closed region, gives each a palette colour, prints
   the number at the region's deepest interior point (never touching a line), and skips slivers
   too small to colour.
3. **`cbn.py` builds the page**: a legend strip of numbered swatches with colour names (no title
   banner), the numbered art, and a filled-in answer key to sanity-check before printing.

Needs only Python 3, Pillow and numpy. Script: `cbn.py` next to this file (`--help` for all flags).

## 1. Draw the line art

Office agents: `/home/brandon/projects/agent-bus/bin/image --aspect 3:4 --out /tmp/agentbus/<you>/art.png --prompt "…"`
(≈ $0.03, shared pool of 50 a day; don't reroll more than 2–3 times without asking).
Elsewhere, any image model that takes a prompt works.

Prompt recipe (fill in the subject; keep every other line):

```
Children's coloring book page, black and white line art.
Subject: <ONE friendly subject doing one simple thing>, <2-4 simple background props>.
Style: cute kawaii cartoon, centered, fills the frame.
Lines: very thick, uniform, solid black outlines, all the same weight. Every shape is a fully
closed outline with no gaps where lines meet. Shapes overlap cleanly.
Regions: 25-45 large, simple shapes. No tiny details, no fur strokes, no texture, no hatching,
no stippling, no small dots. Faces: simple eyes and a small smile only.
Background: plain white sky and a simple ground line or hill. No frame or border.
Absolutely no colour, no grey, no shading, no gradients, no shadows.
No text, no letters, no numbers, no title, no watermark.
```

Subjects that work: one animal or vehicle, with flowers, clouds, sun, hills, a tree, balloons,
fish/bubbles, stars. Avoid crowds, hands with fingers, patterns (plaid, scales), lettering.

Check the result before going on: lines black on white, outlines closed, nothing hair-thin.
A stray gap that merges two shapes is fixed with `--close 2` (or 3), not a reroll.

**Using an existing page** (a downloaded sheet, a scan): fine. Cut away any title, legend or frame
with `--crop L,T,R,B` (pixel box to keep) so only the art is analysed.

## 2. Choose the palette (4-8 colours)

- Start from what the subject *is*: list its big parts and give each its natural colour
  (bunny → brown body, pink inner ears, orange carrot, green leaves; sky blue, grass green).
- Merge near-duplicates until there are 4-8. Younger kids: 4-6. Every colour should be used at
  least twice; drop one used once and recolour that region.
- Name colours the way a crayon box does: Red, Yellow, Blue, Green, Orange, Purple, Pink, Brown,
  Black, Grey, Light Blue. Hex values close to standard crayons print best:

```
Red #e53935      Yellow #fdd835   Blue #64b5f6     Green #66bb6a
Orange #fb8c00   Purple #ab47bc   Pink #f48fb1     Brown #a1887f
Light Blue #b3e5fc  Dark Green #2e7d32  Grey #9e9e9e  Black #424242
```

Save as `palette.txt`, one `Name #hex` per line, in legend order (number 1 first).
Leave white things (clouds, eye whites, teeth) out of the palette: unassigned regions stay blank.

## 3. Map regions, assign colours

```bash
python3 cbn.py regions art.png --out OUT [--crop L,T,R,B] [--close 2]
```

Writes `OUT/regions.png` (every region tinted, its id printed) and `OUT/regions.json`
(area, depth, deepest point; `"edge": true` for regions touching the art's edge, like sky and
ground). **Look at `regions.png`**, then write `OUT/assign.json`, region id → colour number:

```json
{"1": 3, "8": 8, "2": 8, "4": 7, "38": 5, "67": 4}
```

Regions you leave out stay white and unnumbered. Check `regions.png` for merges (two shapes with
one id: a gap in the outline). Raise `--close` and run `regions` again; ids change, so assign after.

For abstract or pattern pages, `--assign auto` colours regions so neighbours differ
(edge regions stay blank unless `--keep-outside`).

## 4. Render

```bash
python3 cbn.py render art.png --palette palette.txt --assign OUT/assign.json --out OUT \
    [--crop …] [--close 2] [--border]
```

Use the same `--crop`/`--close`/`--threshold` as the `regions` run, or the ids won't match.
Writes `OUT/page.png` (to print) and `OUT/key.png` (answer key), both 2550×3300 = Letter at
300 dpi. Numbers scale with their region (8-26 pt); regions too tight for an 8 pt number
(`--min-font`, px) are left unnumbered *and* uncoloured in the key, so the two always agree.

**Look at both images before handing them over.** Check that every big region has a number,
the key looks like a sensible picture, and no colour appears only once. Fix with assign.json
and re-render (no new generation needed).

## Flags worth knowing

| flag | default | when |
|---|---|---|
| `--crop L,T,R,B` | none | cut titles, legends, frames off an existing page |
| `--close N` | 1 | seal hairline gaps; 2-3 for sketchy art |
| `--threshold N` | 150 | grey below this counts as line; lower it if pale shading becomes lines |
| `--min-area F` | 0.0004 | regions smaller than this fraction of the art are ignored |
| `--min-font PX` | 34 (8 pt) | smallest number printed |
| `--border` | off | draw a frame around the art |

`--color-ref coloured.png` (same framing as the art): each region takes the nearest palette
colour of its median pixel and `assign.json` is written for you. Only useful when you have a
flat-coloured version that lines up exactly with the line art.

## Example

`examples/bunny-page.png` and `examples/bunny-key.png`: Brandon's reference bunny sheet with its
title and legend cropped off, rendered with `examples/bunny-palette.txt` and
`examples/bunny-assign.json`:

```bash
python3 cbn.py render bunny.png --crop 18,158,470,614 --close 2 --border \
    --palette examples/bunny-palette.txt --assign examples/bunny-assign.json --out OUT
```
