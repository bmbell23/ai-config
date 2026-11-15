#!/usr/bin/env python3
"""Color-by-number pages from line art. Pillow + numpy only.

  cbn.py regions ART.png --out DIR [--crop L,T,R,B]
      Label every closed region; write DIR/regions.png (each region tinted, id printed)
      and DIR/regions.json (id, area, deepest point, colour sampled from --color-ref).
  cbn.py render ART.png --palette PALETTE --assign ASSIGN.json --out DIR [--crop ...]
      Write DIR/page.png (Letter, 300 dpi, legend strip + numbered art)
      and DIR/key.png (same page, coloured in).

PALETTE: "Red=#e53935,Yellow=#fdd835,..." or a file with one "Name #hex" per line.
ASSIGN:  {"<region id>": <colour number 1..N>, ...}; regions left out stay blank.
         "auto" instead of a file: adjacent regions get different colours (abstract pages).
--color-ref COLOURED.png (same size as ART): each region gets the nearest palette colour of
         its median pixel; near-white regions stay blank. Writes DIR/assign.json to tweak.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

DPI = 300
PAGE = (int(8.5 * DPI), 11 * DPI)
MARGIN = int(0.4 * DPI)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
NUMBER_INK = (90, 90, 90)


def font(size, bold=True):
    try:
        return ImageFont.truetype(FONT if bold else FONT_REG, size)
    except OSError:
        return ImageFont.load_default(size)


# ---- region analysis -------------------------------------------------------

def load_lines(path, crop, threshold, close):
    img = Image.open(path).convert("L")
    if crop:
        img = img.crop(crop)
    ink = np.asarray(img) < threshold
    for _ in range(close):  # thicken lines to seal hairline gaps
        ink = ink | shift(ink, 1, 0) | shift(ink, -1, 0) | shift(ink, 0, 1) | shift(ink, 0, -1)
    return img, ink


def shift(a, dy, dx, fill=False):
    out = np.full_like(a, fill)
    h, w = a.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = \
        a[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def label(mask):
    """4-connected components, vectorised union-find (hook + pointer jumping). 0 = no region."""
    h, w = mask.shape
    idx = np.arange(h * w).reshape(h, w)
    eh = mask[:, :-1] & mask[:, 1:]
    ev = mask[:-1, :] & mask[1:, :]
    a = np.concatenate([idx[:, :-1][eh], idx[:-1, :][ev]])
    b = np.concatenate([idx[:, 1:][eh], idx[1:, :][ev]])
    parent = idx.ravel().copy()
    while True:
        pa, pb = parent[a], parent[b]
        diff = pa != pb
        if not diff.any():
            break
        np.minimum.at(parent, np.maximum(pa, pb)[diff], np.minimum(pa, pb)[diff])
        while True:
            pp = parent[parent]
            if np.array_equal(pp, parent):
                break
            parent = pp
    roots = parent.reshape(h, w)
    _, inv = np.unique(np.where(mask, roots, -1), return_inverse=True)
    # -1 (non-mask) sorts first and becomes 0; with no non-mask pixels, shift ids to start at 1
    return inv.reshape(h, w) + (0 if (~mask).any() else 1)


def depth(mask):
    """Erosion depth of each pixel (approx. distance to nearest line or edge)."""
    d = np.zeros(mask.shape, np.int32)
    cur = mask.copy()
    k = 0
    while cur.any():
        d += cur
        n = cur & shift(cur, 1, 0) & shift(cur, -1, 0) & shift(cur, 0, 1) & shift(cur, 0, -1)
        if k % 2:  # alternate cross / square: octagonal, close enough to Euclidean
            n &= shift(cur, 1, 1) & shift(cur, 1, -1) & shift(cur, -1, 1) & shift(cur, -1, -1)
        cur, k = n, k + 1
    return d


def analyse(ink, color_ref=None):
    lab = label(~ink)
    d = depth(~ink)
    n = lab.max()
    flat_l, flat_d = lab.ravel(), d.ravel()
    area = np.bincount(flat_l, minlength=n + 1)
    maxd = np.zeros(n + 1, np.int32)
    np.maximum.at(maxd, flat_l, flat_d)
    hit = np.flatnonzero((flat_d == maxd[flat_l]) & (flat_l > 0))
    ids, first = np.unique(flat_l[hit], return_index=True)
    w = lab.shape[1]
    regions = {}
    for rid, pix in zip(ids, hit[first]):
        regions[int(rid)] = {"area": int(area[rid]), "depth": int(maxd[rid]),
                             "x": int(pix % w), "y": int(pix // w)}
    if color_ref is not None:
        ref = np.asarray(color_ref.convert("RGB").resize(lab.shape[::-1]))
        order = np.argsort(flat_l, kind="stable")
        bounds = np.searchsorted(flat_l[order], np.arange(n + 2))
        rgb = ref.reshape(-1, 3)
        for rid in regions:
            px = rgb[order[bounds[rid]:bounds[rid + 1]]]
            regions[rid]["rgb"] = [int(v) for v in np.median(px, axis=0)]
    return lab, regions


def adjacency(lab, reach):
    pairs = set()
    for dy, dx in ((reach, 0), (0, reach), (reach, reach), (reach, -reach)):
        a, b = lab, shift(lab, dy, dx, 0)
        m = (a > 0) & (b > 0) & (a != b)
        for p, q in np.unique(np.stack([a[m], b[m]], 1), axis=0):
            pairs.add((min(p, q), max(p, q)))
    return pairs


# ---- palette & assignment ----------------------------------------------------

def parse_palette(spec):
    if os.path.exists(spec):
        items = [ln.rsplit(None, 1) for ln in open(spec) if ln.strip() and not ln.startswith("#")]
    else:
        items = [s.split("=") for s in spec.split(",")]
    pal = []
    for name, hx in items:
        hx = hx.strip().lstrip("#")
        pal.append((name.strip(), tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))))
    if not 2 <= len(pal) <= 12:
        sys.exit("palette: give 2-12 colours (4-8 prints best)")
    return pal


def assign_from_ref(regions, pal):
    cols = np.array([c for _, c in pal] + [(255, 255, 255)], float)
    out = {}
    for rid, r in regions.items():
        if "rgb" in r:
            k = int(np.argmin(((cols - r["rgb"]) ** 2).sum(1)))
            if k < len(pal):
                out[str(rid)] = k + 1
    return out


def assign_auto(lab, regions, pal, reach):
    adj = {}
    for a, b in adjacency(lab, reach):
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    out = {}
    for rid in sorted(regions, key=lambda r: -regions[r]["area"]):
        used = {out.get(str(o)) for o in adj.get(rid, ())}
        free = [k for k in range(1, len(pal) + 1) if k not in used] or [1]
        count = {k: sum(1 for v in out.values() if v == k) for k in free}
        out[str(rid)] = min(free, key=lambda k: count[k])
    return out


# ---- output ------------------------------------------------------------------

def legend(pal, width):
    sw = min(170, int(width / len(pal) * 0.62))
    h = sw + 90
    strip = Image.new("RGB", (width, h), "white")
    d = ImageDraw.Draw(strip)
    step = width / len(pal)
    for i, (name, rgb) in enumerate(pal):
        cx = int(step * (i + 0.5))
        d.ellipse([cx - sw // 2, 0, cx + sw // 2, sw], fill=rgb, outline="black", width=6)
        lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        d.text((cx, sw // 2), str(i + 1), font=font(int(sw * 0.55)), anchor="mm",
               fill="black" if lum > 110 else "white")
        d.text((cx, sw + 50), name, font=font(46, bold=False), anchor="mm", fill="black")
    return strip


def render(art, lab, regions, assign, pal, out_dir, min_font, border):
    W, H = PAGE
    strip = legend(pal, W - 2 * MARGIN)
    top = MARGIN + strip.height + 60
    box_w, box_h = W - 2 * MARGIN, H - top - MARGIN
    s = min(box_w / art.width, box_h / art.height)
    size = (round(art.width * s), round(art.height * s))
    ox, oy = MARGIN + (box_w - size[0]) // 2, top

    # numbers first: the key colours only regions that got one, so page and key agree
    numbers = []
    for rid, k in assign.items():
        r = regions.get(int(rid))
        if not r:
            continue
        fs = int(min(110, r["depth"] * s * (1.25 if k < 10 else 0.95)))
        if fs >= min_font:
            numbers.append((int(rid), k, fs, ox + (r["x"] + 0.5) * s, oy + (r["y"] + 0.5) * s))
    skipped = len(assign) - len(numbers)

    # crisp black lines at print size; fills drawn under them, grown into the lines so no halo
    line = np.asarray(art.resize(size, Image.LANCZOS)) < 140
    fill_idx = np.zeros(lab.max() + 1, np.int32)
    for rid, k, *_ in numbers:
        fill_idx[rid] = k
    lab = grow(lab, 6)
    lut = np.array([(255, 255, 255)] + [c for _, c in pal], np.uint8)
    lab_big = np.asarray(Image.fromarray(lab.astype(np.int32)).resize(size, Image.NEAREST))
    colored = lut[fill_idx[lab_big]]
    plain = np.full_like(colored, 255)
    for arr in (colored, plain):
        arr[line] = 0

    pages = {}
    for kind, arr in (("page", plain), ("key", colored)):
        pg = Image.new("RGB", PAGE, "white")
        pg.paste(strip, (MARGIN, MARGIN))
        pg.paste(Image.fromarray(arr), (ox, oy))
        if border:
            ImageDraw.Draw(pg).rectangle([ox - 4, oy - 4, ox + size[0] + 3, oy + size[1] + 3],
                                         outline="black", width=8)
        pages[kind] = pg

    d = ImageDraw.Draw(pages["page"])
    for _, k, fs, x, y in numbers:
        d.text((x, y), str(k), font=font(fs), anchor="mm", fill=NUMBER_INK)
    placed = len(numbers)
    for kind, pg in pages.items():
        pg.save(os.path.join(out_dir, f"{kind}.png"), dpi=(DPI, DPI))
    print(f"{placed} numbers placed, {skipped} regions too small to number; "
          f"wrote {out_dir}/page.png and {out_dir}/key.png ({W}x{H} @ {DPI} dpi)")


def grow(lab, steps):
    """Spread region ids into the line pixels next to them (for fills under the ink)."""
    lab = lab.copy()
    for _ in range(steps):
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = shift(lab, dy, dx, 0)
            m = (lab == 0) & (nb > 0)
            lab[m] = nb[m]
    return lab


def debug_map(art, lab, regions, path):
    rng = np.random.default_rng(7)
    lut = np.vstack([[255, 255, 255], rng.integers(120, 256, (lab.max(), 3))]).astype(np.uint8)
    img = lut[lab]
    img[lab == 0] = 0
    im = Image.fromarray(img)
    if im.width < 1600:  # room for legible ids
        f = 1600 / im.width
        im = im.resize((1600, round(im.height * f)), Image.NEAREST)
    else:
        f = 1.0
    d = ImageDraw.Draw(im)
    for rid, r in regions.items():
        d.text((r["x"] * f, r["y"] * f), str(rid), font=font(22), anchor="mm",
               fill="black", stroke_width=3, stroke_fill="white")
    im.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["regions", "render"])
    ap.add_argument("art", help="line-art PNG (black lines on white)")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--crop", help="L,T,R,B pixels to keep (cut off titles, frames)")
    ap.add_argument("--palette")
    ap.add_argument("--assign", help='region->colour JSON, or "auto"')
    ap.add_argument("--color-ref", help="flat-coloured version of the art, same framing")
    ap.add_argument("--threshold", type=int, default=150, help="grey below this is line (default 150)")
    ap.add_argument("--close", type=int, default=1, help="px to thicken lines, seals gaps (default 1)")
    ap.add_argument("--min-area", type=float, default=0.0004,
                    help="regions under this fraction of the art are ignored (default 0.0004)")
    ap.add_argument("--min-font", type=int, default=34,
                    help="smallest number in px at 300 dpi; tighter regions stay unnumbered (default 34 = 8pt)")
    ap.add_argument("--keep-outside", action="store_true",
                    help="auto: colour regions touching the art's edge too (default: leave them blank)")
    ap.add_argument("--border", action="store_true", help="frame the art")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    art, ink = load_lines(a.art, crop, a.threshold, a.close)
    ref = None
    if a.color_ref:
        ref = Image.open(a.color_ref)
        ref = ref.crop(crop) if crop else ref
    lab, regions = analyse(ink, ref)
    total = lab.size
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    for rid in list(regions):
        if regions[rid]["area"] < a.min_area * total:
            del regions[rid]
        elif rid in edge:
            regions[rid]["edge"] = True

    if a.cmd == "regions":
        with open(os.path.join(a.out, "regions.json"), "w") as f:
            json.dump(regions, f, indent=1)
        debug_map(art, lab, regions, os.path.join(a.out, "regions.png"))
        print(f"{len(regions)} regions; wrote {a.out}/regions.png and {a.out}/regions.json")
        return

    if not a.palette:
        sys.exit("render needs --palette")
    pal = parse_palette(a.palette)
    if ref is not None:
        assign = assign_from_ref(regions, pal)
        with open(os.path.join(a.out, "assign.json"), "w") as f:
            json.dump(assign, f, indent=1)
    elif a.assign == "auto":
        inner = {k: v for k, v in regions.items() if a.keep_outside or not v.get("edge")}
        assign = assign_auto(lab, inner, pal, reach=2 * a.close + 6)
    elif a.assign:
        assign = {k: v for k, v in json.load(open(a.assign)).items() if not k.startswith("_")}
        bad = [k for k, v in assign.items() if not 1 <= v <= len(pal)]
        if bad:
            sys.exit(f"assign: colour out of range for regions {bad}")
    else:
        sys.exit("render needs --assign FILE|auto or --color-ref")
    render(art, lab, regions, assign, pal, a.out, a.min_font, a.border)


if __name__ == "__main__":
    main()
