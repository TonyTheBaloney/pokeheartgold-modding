#!/usr/bin/env python3
# [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-22
"""Prototype: shiny palettes for Pokémon icons, rendered next to the real shiny battle sprite.

NOT PART OF THE BUILD: a prototype run by hand. See docs/ideas/shiny-icons.md.

    python3 docs/ideas/shiny-icons/preview.py OUT.png [SPECIES,...]   (needs Pillow; run from the repo root)

Columns: the normal icon; "swap A"/"swap B" (drawn with the other two shared palettes);
"nearest" and "family" (generated from the battle sprite's normal -> shiny colors);
"best" (whichever of the two is closer to the real shiny sprite); the real shiny sprite.
"""

import collections
import colorsys
import math
import os
import re
import sys

from PIL import Image, ImageDraw

ICONS = "files/poketool/icongra/poke_icon"
POKEGRA = "files/poketool/pokegra/pokegra"
KEEP = (0, 14, 15)          # transparent and the two outline grays: never recolored
DEFAULT = [25, 6, 130, 157, 181, 197, 248, 249, 94, 1, 212, 245]


# --- the game's data -----------------------------------------------------------------------

def icon_palette_numbers():
    """sPokemonPalNoBySpeciesAndForm: which of the 3 shared palettes each icon uses."""
    src = open("src/pokemon_icon_idx.c", encoding="utf-8").read()
    t = src[src.index("sPokemonPalNoBySpeciesAndForm"):]
    t = t[t.index("{") + 1:t.index("};")]
    return [int(x) for x in re.findall(r"\b(\d+)\b", re.sub(r"//.*", "", t))]


def shared_palettes():
    lines = [x for x in open(ICONS + "/poke_icon_00000000.pal").read().split("\n")[3:] if x.strip()]
    cols = [tuple(map(int, x.split())) for x in lines]
    return [cols[p * 16:p * 16 + 16] for p in range(3)]


def plte(path):
    p = Image.open(path).getpalette()[:48]
    return [tuple(p[i:i + 3]) for i in range(0, 48, 3)]


def battle_sprite(species):
    """(normal palette, shiny palette, front image): make_pokegra.py takes the normal palette
    from front.png and the shiny one from back.png."""
    d = "%s/%04d/male/" % (POKEGRA, species)
    if not os.path.exists(d + "front.png") or os.path.getsize(d + "front.png") == 0:
        d = d.replace("male", "female")
    return plte(d + "front.png"), plte(d + "back.png"), Image.open(d + "front.png")


def counts(img, mask=255):
    data = img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
    return collections.Counter(v & mask for v in data)


# --- color helpers -------------------------------------------------------------------------

def hls(c):
    return colorsys.rgb_to_hls(*[v / 255 for v in c])


def chroma(c):
    h, l, s = hls(c)
    return s * (1 - abs(2 * l - 1))


def hue_dist(a, b):
    d = abs(a - b) % 1.0
    return min(d, 1 - d) * 360


def rgb_dist(a, b):
    r = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return (2 + r / 256) * dr * dr + 4 * dg * dg + (2 + (255 - r) / 256) * db * db


def lab(c):
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    rgb = [((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c]
    x = (rgb[0] * .4124 + rgb[1] * .3576 + rgb[2] * .1805) / .95047
    y = rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722
    z = (rgb[0] * .0193 + rgb[1] * .1192 + rgb[2] * .9505) / 1.08883
    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


# --- the two generators --------------------------------------------------------------------

def nearest(base, icon_used, norm, shin, sprite_used):
    """Each icon color takes the shiny color of the nearest normal sprite color.
    Good when the icon was drawn in the sprite's colors (Charizard, Scizor, Umbreon)."""
    out, cand = list(base), [j for j in sprite_used if j != 0]
    for i in icon_used:
        if i in KEEP:
            continue
        j = min(cand, key=lambda j: rgb_dist(base[i], norm[j]))
        if norm[j] != shin[j]:
            out[i] = shin[j]
    return out


def families(idx_cols, gap=35, min_chroma=0.12):
    chrom = sorted(((i, c) for i, c in idx_cols if chroma(c) >= min_chroma), key=lambda ic: hls(ic[1])[0])
    fams = []
    for i, c in chrom:
        for f in fams:
            if min(hue_dist(hls(c)[0], hls(fc)[0]) for _, fc in f) <= gap:
                f.append((i, c))
                break
        else:
            fams.append([(i, c)])
    return fams


def family_hue(f):
    x = sum(math.cos(hls(c)[0] * 2 * math.pi) * chroma(c) for _, c in f)
    y = sum(math.sin(hls(c)[0] * 2 * math.pi) * chroma(c) for _, c in f)
    return (math.atan2(y, x) / (2 * math.pi)) % 1.0


def by_lightness(src, dst):
    s = sorted(src, key=lambda ic: hls(ic[1])[1])
    d = sorted(dst, key=lambda ic: hls(ic[1])[1])
    if len(s) == 1:
        return {s[0][0]: min(d, key=lambda jc: abs(hls(jc[1])[1] - hls(s[0][1])[1]))[0]}
    return {i: d[round(k / (len(s) - 1) * (len(d) - 1))][0] for k, (i, c) in enumerate(s)}


def family(base, icon_used, norm, shin, sprite_used, max_hue=90):
    """Groups icon and sprite colors by hue, pairs the groups, maps dark to dark and light to
    light. Good when the icon artist used another hue (Gyarados: lavender icon, cyan sprite)."""
    out = list(base)
    icon = [(i, base[i]) for i in sorted(icon_used) if i not in KEEP]
    spr = [(j, norm[j]) for j in sorted(sprite_used) if j != 0]
    sfam, mapping = families(spr), {}
    for f in families(icon):
        h = family_hue(f)
        best = min(sfam, key=lambda g: hue_dist(h, family_hue(g)), default=None)
        if best is not None and hue_dist(h, family_hue(best)) <= max_hue:
            mapping.update(by_lightness(f, best))
    grays = [(j, c) for j, c in spr if chroma(c) < 0.12]
    for i, c in icon:
        if i not in mapping and chroma(c) < 0.12 and grays:
            mapping[i] = min(grays, key=lambda jc: abs(hls(jc[1])[1] - hls(c)[1]))[0]
    for i, j in mapping.items():
        if norm[j] != shin[j]:
            out[i] = shin[j]
    return out


def score(icon_counts, pal, sprite_counts, shin):
    """How far the icon's colors are from the real shiny sprite's (symmetric chamfer in Lab,
    weighted by pixel share). Lower is closer."""
    def hist(cnt, p, skip):
        tot = sum(n for i, n in cnt.items() if i not in skip)
        return [(lab(p[i]), n / tot) for i, n in cnt.items() if i not in skip and n]

    def d(p, q):
        return sum((x - y) ** 2 for x, y in zip(p, q)) ** 0.5
    a, b = hist(icon_counts, pal, {0, 15}), hist(sprite_counts, shin, {0})
    return sum(w * min(d(c, c2) for c2, _ in b) for c, w in a) + sum(w * min(d(c, c2) for c2, _ in a) for c, w in b)


def best(base, icon_counts, norm, shin, sprite_counts):
    iu, su = set(icon_counts), set(sprite_counts)
    cands = {"nearest": nearest(base, iu, norm, shin, su), "family": family(base, iu, norm, shin, su)}
    s, m = min((score(icon_counts, p, sprite_counts, shin), m) for m, p in cands.items())
    return cands[m], m


# --- the preview sheet ---------------------------------------------------------------------

def main():
    out_path = sys.argv[1]
    species = [int(s) for s in sys.argv[2].split(",")] if len(sys.argv) > 2 else DEFAULT
    pal_of, shared = icon_palette_numbers(), shared_palettes()
    heads = ["", "normal", "swap A", "swap B", "nearest", "family", "best", "real shiny"]
    W = 96
    sheet = Image.new("RGB", (W * len(heads), W * len(species) + 16), (40, 40, 48))
    draw = ImageDraw.Draw(sheet)
    for c, h in enumerate(heads):
        draw.text((W * c + 6, 2), h, fill=(255, 255, 120))

    def render(icon, pal):
        tile = Image.new("RGB", (32, 32), (40, 40, 48))
        tp, px = tile.load(), icon.load()
        for y in range(32):
            for x in range(32):
                if px[x, y] & 15:
                    tile.putpixel((x, y), pal[px[x, y] & 15])
        return tile.resize((W, W), Image.NEAREST)

    for r, sp in enumerate(species):
        y = 16 + r * W
        icon = Image.open("%s/poke_icon_%08d.png" % (ICONS, sp + 7))   # GetMonIconNaixEx: species + 7
        p = pal_of[sp]
        norm, shin, sprite = battle_sprite(sp)
        ic, sc = counts(icon, 15), counts(sprite)
        b, method = best(shared[p], ic, norm, shin, sc)
        pals = [shared[p], shared[(p + 1) % 3], shared[(p + 2) % 3],
                nearest(shared[p], set(ic), norm, shin, set(sc)), family(shared[p], set(ic), norm, shin, set(sc)), b]
        for c, pal in enumerate(pals):
            sheet.paste(render(icon, pal), (W * (c + 1), y))
        real = sprite.copy()
        real.putpalette([v for c in shin for v in c] + [0] * (768 - 48))
        sheet.paste(real.convert("RGB").crop((0, 0, 80, 80)).resize((W, W)), (W * 7, y))
        draw.text((4, y + W // 2 - 6), "#%d" % sp, fill=(230, 230, 230))
        draw.text((4, y + W // 2 + 8), method, fill=(150, 220, 150))
    sheet.save(out_path)


if __name__ == "__main__":
    main()
