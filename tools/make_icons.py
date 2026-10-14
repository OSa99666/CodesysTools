#!/usr/bin/env python3
"""
Draws the icons of the three plugins (development tool - needs Pillow, the deliverables don't).

    python tools/make_icons.py

Writes   notepadpp/*.ico   codesys/*.ico   twincat/*.ico   and a preview sheet  tools/icons_preview.png
Per plugin: a main icon (ST_<Plugin>.ico) and the function icons ST_Format, ST_CheckNames, ST_SpellCheck.
Accent colours: Notepad++ green, CODESYS blue, TwinCAT red.
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 1024                                           # master size, scaled down per icon size
SIZES = [16, 24, 32, 48, 64, 128, 256]

PLUGINS = {
    # folder, main icon name, light, dark accent
    "notepadpp": ("ST_NotepadPP", (92, 205, 92), (24, 110, 44)),
    "codesys": ("ST_Codesys", (86, 168, 255), (16, 70, 160)),
    "twincat": ("ST_TwinCAT", (255, 110, 96), (150, 24, 36)),
}
WHITE = (255, 255, 255, 255)


def font(size, bold=True):
    for name in (("consolab.ttf", "arialbd.ttf") if bold else ("consola.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", name), size)
        except OSError:
            pass
    return ImageFont.load_default()


def rounded_mask(box, radius):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius, fill=255)
    return m


def badge(light, dark):
    """Rounded square with a vertical gradient, soft gloss, inner rim and drop shadow."""
    pad = int(S * 0.06)
    box = (pad, pad, S - pad, S - pad - int(S * 0.02))
    mask = rounded_mask(box, int(S * 0.2))
    grad = Image.new("RGBA", (S, S))
    px = grad.load()
    for y in range(S):
        t = min(1.0, max(0.0, (y - box[1]) / float(box[3] - box[1])))
        t = t * t * (3 - 2 * t)
        c = tuple(int(light[i] + (dark[i] - light[i]) * t) for i in range(3)) + (255,)
        for x in range(S):
            px[x, y] = c
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 120), (0, int(S * 0.025)), mask)
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(S * 0.02)))
    img.paste(grad, (0, 0), mask)
    # gloss: a lighter lens over the upper half
    gloss = Image.new("L", (S, S), 0)
    ImageDraw.Draw(gloss).ellipse((-S * 0.25, -S * 0.75, S * 1.25, S * 0.52), fill=70)
    gloss = ImageChops.multiply(gloss, mask)
    img = Image.alpha_composite(img, Image.merge("RGBA", (Image.new("L", (S, S), 255),) * 3 + (gloss,)))
    # inner rim
    rim = rounded_mask(box, int(S * 0.2)).filter(ImageFilter.MinFilter(9))
    edge = ImageChops.subtract(mask, rim)
    edge = Image.merge("RGBA", (Image.new("L", (S, S), 255),) * 3 + (edge.point(lambda v: v // 3),))
    return Image.alpha_composite(img, edge)


def glyph_shadow(layer):
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    a = layer.split()[3].point(lambda v: v // 2)
    sh.paste((0, 0, 0, 255), (0, int(S * 0.012)), a)
    return sh.filter(ImageFilter.GaussianBlur(S * 0.012))


def put(base, layer):
    return Image.alpha_composite(Image.alpha_composite(base, glyph_shadow(layer)), layer)


# ---- glyphs ----------------------------------------------------------------
def g_main(light, dark):
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(int(S * 0.5))
    w = d.textlength("ST", font=f)
    d.text(((S - w) / 2, S * 0.2), "ST", font=f, fill=WHITE)
    # a small cursor/underline bar: "structured" line under the monogram
    d.rounded_rectangle((S * 0.24, S * 0.74, S * 0.76, S * 0.80), S * 0.03, fill=(255, 255, 255, 190))
    d.rounded_rectangle((S * 0.24, S * 0.84, S * 0.56, S * 0.88), S * 0.02, fill=(255, 255, 255, 120))
    return layer


def g_format(light, dark):
    """Aligned declarations:  name  :  type  with a bright alignment column."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rows = [(0.20, 0.14), (0.34, 0.18), (0.26, 0.12), (0.30, 0.16)]
    x0, colon = S * 0.18, S * 0.58
    h = S * 0.075
    for i, (wl, wr) in enumerate(rows):
        y = S * (0.2 + 0.17 * i)
        d.rounded_rectangle((x0, y, x0 + S * wl, y + h), h / 2, fill=WHITE)
        d.ellipse((colon - h * 0.45, y + h * 0.05, colon + h * 0.45, y + h * 0.95), fill=(255, 235, 120, 255))
        d.rounded_rectangle((colon + h * 1.1, y, colon + h * 1.1 + S * wr, y + h), h / 2,
                            fill=(255, 255, 255, 190))
    # alignment guide
    for k in range(7):
        y = S * (0.17 + 0.095 * k)
        d.rounded_rectangle((colon - h * 0.12, y, colon + h * 0.12, y + S * 0.05), h * 0.1, fill=(255, 235, 120, 150))
    return layer


def g_names(light, dark):
    """Checklist of identifiers: ok, wrong, ok."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = S * 0.085
    for i, ok in enumerate((True, False, True)):
        cy = S * (0.28 + 0.22 * i)
        cx = S * 0.27
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(120, 235, 140, 255) if ok else (255, 190, 80, 255))
        lw = int(S * 0.028)
        if ok:
            d.line([(cx - r * 0.5, cy), (cx - r * 0.1, cy + r * 0.45), (cx + r * 0.55, cy - r * 0.4)],
                   fill=(10, 70, 20, 255), width=lw, joint="curve")
        else:
            d.line([(cx - r * 0.4, cy - r * 0.4), (cx + r * 0.4, cy + r * 0.4)], fill=(120, 40, 0, 255), width=lw)
            d.line([(cx + r * 0.4, cy - r * 0.4), (cx - r * 0.4, cy + r * 0.4)], fill=(120, 40, 0, 255), width=lw)
        h = S * 0.075
        d.rounded_rectangle((S * 0.42, cy - h / 2, S * (0.82 if i != 1 else 0.66), cy + h / 2), h / 2, fill=WHITE)
    return layer


def g_spell(light, dark):
    """'Ab' with a red wavy underline."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(int(S * 0.52), bold=True)
    w = d.textlength("Ab", font=f)
    x = (S - w) / 2
    d.text((x, S * 0.1), "Ab", font=f, fill=WHITE)
    y0 = S * 0.74
    pts = []
    n = 120
    for i in range(n + 1):
        t = i / float(n)
        pts.append((S * 0.2 + t * S * 0.6, y0 + math.sin(t * math.pi * 6) * S * 0.035))
    d.line(pts, fill=(255, 214, 64, 255), width=int(S * 0.05), joint="curve")
    # a tick bottom-right
    cx, cy, r = S * 0.76, S * 0.80, S * 0.1
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(120, 235, 140, 255))
    d.line([(cx - r * 0.5, cy), (cx - r * 0.1, cy + r * 0.45), (cx + r * 0.55, cy - r * 0.4)],
           fill=(10, 70, 20, 255), width=int(S * 0.028), joint="curve")
    return layer


GLYPHS = {"": g_main, "_Format": g_format, "_CheckNames": g_names, "_SpellCheck": g_spell}


def render(folder, suffix):
    main, light, dark = PLUGINS[folder]
    img = badge(light, dark)
    return put(img, GLYPHS[suffix](light, dark))


def save_ico(img, path):
    frames = [img.resize((s, s), Image.LANCZOS) for s in SIZES]
    frames[-1].save(path, format="ICO", sizes=[(s, s) for s in SIZES], append_images=frames[:-1])


def main():
    sheet = Image.new("RGBA", (4 * 270, 3 * 270 + 60), (245, 245, 247, 255))
    for r, folder in enumerate(PLUGINS):
        name = PLUGINS[folder][0]
        for c, suffix in enumerate(GLYPHS):
            img = render(folder, suffix)
            fname = name if suffix == "" else "ST" + suffix
            save_ico(img, os.path.join(ROOT, folder, fname + ".ico"))
            big = img.resize((256, 256), Image.LANCZOS)
            sheet.alpha_composite(big, (c * 270 + 7, r * 270 + 7))
            small = img.resize((32, 32), Image.LANCZOS)
            sheet.alpha_composite(small, (c * 270 + 7, 3 * 270 + 12))
            sheet.alpha_composite(img.resize((16, 16), Image.LANCZOS), (c * 270 + 47, 3 * 270 + 20))
        print("wrote %s/*.ico" % folder)
    sheet.convert("RGB").save(os.path.join(ROOT, "tools", "icons_preview.png"))


if __name__ == "__main__":
    main()
