"""Black smoke clump textures for the hell-round transition, generated (no game assets).

Each clump is fractal noise shaped by a soft elliptical falloff, then thresholded with a
soft edge: an opaque black core, torn edges, holes, and loose fragments around it, like the
ink-blot clumps of fx_hellround_transition. Returned as small WebP data URIs (black + alpha).
"""
import base64
import io
import random

from PIL import Image, ImageChops, ImageFilter, ImageOps

SIZE = 200


def _smooth_noise(rnd, size, cell):
    n = size // cell + 3
    small = Image.frombytes("L", (n, n), rnd.randbytes(n * n))
    big = small.resize((n * cell, n * cell), Image.BICUBIC)
    ox, oy = rnd.randrange(cell), rnd.randrange(cell)
    return big.crop((ox, oy, ox + size, oy + size))


def _fractal(rnd, size):
    out = None
    for cell, weight in ((56, .5), (26, .28), (12, .15), (6, .07)):
        layer = _smooth_noise(rnd, size, cell).point(lambda v, w=weight: v * w)
        out = layer if out is None else ImageChops.add(out, layer)
    return out.point(lambda v: min(255, int(v * 1.0)))


def _falloff(rnd, size, stretch):
    g = Image.radial_gradient("L")                      # 0 at the centre, 255 at the rim
    g = ImageChops.invert(g).resize((size, size), Image.BICUBIC)
    sx, sy = stretch
    w, h = int(size * sx), int(size * sy)
    g = g.resize((w, h), Image.BICUBIC)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(g, ((size - w) // 2 + rnd.randint(-4, 4), (size - h) // 2 + rnd.randint(-4, 4)))
    return canvas


def blot(seed, stretch=(1.0, 1.0), density=1.0):
    rnd = random.Random(seed)
    noise = ImageOps.autocontrast(_fractal(rnd, SIZE), cutoff=1)
    fall = _falloff(rnd, SIZE, (stretch[0] * .72, stretch[1] * .72)).filter(ImageFilter.GaussianBlur(9))
    # noise and shape weigh about the same: a solid core, holes and torn lobes further out,
    # loose fragments where the noise peaks near the rim; noise alone never crosses the
    # threshold, so nothing gets cut by the texture's square edge
    mix = ImageChops.add(noise.point(lambda v: v * .57), fall.point(lambda v: v * .7 * density))
    lo = 150
    alpha = mix.point(lambda v: max(0, min(255, int((v - lo) * 7))))
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.3))  # a little softness, like the out-of-focus clumps
    rgba = Image.new("RGBA", (SIZE, SIZE), (5, 3, 4, 0))
    rgba.putalpha(alpha)
    return rgba


def data_uri(img):
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=72, alpha_quality=70, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


VARIANTS = [(11, (1.0, 1.0), 1.0), (23, (1.0, .8), 1.05), (37, (.85, 1.0), .95),
            (41, (1.0, .9), 1.1), (58, (.9, .9), .9), (63, (1.0, .75), 1.0)]


def all_blots():
    return [blot(s, st, d) for s, st, d in VARIANTS]


if __name__ == "__main__":
    import sys
    imgs = all_blots()
    sheet = Image.new("RGB", (SIZE * 3 + 40, SIZE * 2 + 30), (150, 132, 108))
    for i, im in enumerate(imgs):
        sheet.paste(im, (10 + (i % 3) * (SIZE + 10), 10 + (i // 3) * (SIZE + 10)), im)
    sheet.save(sys.argv[1])
    print("bytes per blot:", [len(data_uri(im)) for im in imgs])
