"""Generate the project cards of the profile README: one self-contained animated SVG per
project, in the style of the header (dark panel, Impact title, monospace tagline).

Usage: python tools/cards/cards.py [out_dir]   (default: assets/cards)
Needs Pillow with WebP support. Sources are in tools/cards/src.

Each card is 480x300: a 480x200 animated visual over a 100px caption panel. The README
shows them at width="410", so two sit side by side on desktop and each takes the full
width on a phone. Animations are CSS only (no scripts, no outside requests) and stop
under prefers-reduced-motion.
"""
import base64
import io
import os
import random
import re
import sys

from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
W, H, VH = 480, 300, 200   # card size, height of the visual above the caption

TITLE_FONT = "Impact,Haettenschweiler,'Arial Narrow Bold','Franklin Gothic Heavy','Arial Black',sans-serif"
MONO_FONT = "ui-monospace,'Cascadia Mono',Consolas,Menlo,'DejaVu Sans Mono',monospace"
BG, BORDER, TEXT = "#0d1117", "#30363d", "#e6edf3"

# How each project was built, shown as a chip in the card's corner.
HANDMADE = ("HANDMADE", "#7ee787")
AI_ASSISTED = ("AI-ASSISTED", "#79c0ff")
AI_BUILT = ("AI-BUILT", "#d2a8ff")


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def webp(img, quality=80):
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def crop_to(path, box, size):
    """Crop box (l, t, r, b) out of a source image and resize it to size, as a data URI."""
    img = Image.open(os.path.join(SRC, path)).convert("RGB").crop(box)
    return webp(img.resize(size, Image.LANCZOS))


def fit_with_blur(path, size):
    """The whole source image, fitted to the height of size, over a blurred and darkened copy
    that fills the rest of the width: nothing is cropped away."""
    img = Image.open(os.path.join(SRC, path)).convert("RGB")
    w, h = size
    scale = max(w / img.width, h / img.height)
    back = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (back.width - w) // 2, (back.height - h) // 2
    back = back.crop((left, top, left + w, top + h)).filter(ImageFilter.GaussianBlur(h / 20))
    back = ImageEnhance.Brightness(back).enhance(0.45)
    fw = round(img.width * h / img.height)
    back.paste(img.resize((fw, h), Image.LANCZOS), ((w - fw) // 2, 0))
    return webp(back)


def card(alt, title, tagline, chip, accent, visual, css="", defs="", caption=""):
    label, chip_color = chip
    chip_w = len(label) * 8 + 20
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
  <title id="t">{alt}</title>
  <defs>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
    <clipPath id="vis"><rect width="{W}" height="{VH}"/></clipPath>
    {defs}
  </defs>
  <style>
    .ti{{font:400 36px {TITLE_FONT};letter-spacing:2px}}
    .tg{{font:600 19px {MONO_FONT}}}
    .ch{{font:700 12px {MONO_FONT};letter-spacing:1px}}
    {css}
    @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
  </style>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <g clip-path="url(#vis)">{visual}</g>
    {caption}
    <rect y="{VH}" width="{W}" height="2" fill="{accent}"/>
    <text x="24" y="{VH + 48}" class="ti" fill="{TEXT}">{title}</text>
    <text x="24" y="{VH + 80}" class="tg" fill="{accent}">{tagline}</text>
    <g transform="translate({W - 16 - chip_w} 16)">
      <rect width="{chip_w}" height="24" rx="12" fill="{BG}" fill-opacity=".8" stroke="{chip_color}" stroke-width="1.5"/>
      <text x="{chip_w / 2}" y="16.5" text-anchor="middle" class="ch" fill="{chip_color}">{label}</text>
    </g>
  </g>
  <rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="13.5" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
</svg>
'''


# ---------------------------------------------------------------- Rainy Doom: rain above, hell below

def flames(rnd):
    """Flame tongues licking up behind the caption, and embers rising from them."""
    def tongues(n, cls, w, h):
        out = []
        for i in range(n):
            x = (i + rnd.uniform(0.15, 0.85)) * W / n
            tw, th = rnd.uniform(*w), rnd.uniform(*h)
            out.append(f'<g transform="translate({f(x)} {H})"><path class="{cls}" '
                       f'd="M{f(-tw)} 0C{f(-tw)} {f(-th * .45)} {f(-tw * .2)} {f(-th * .6)} 0 {f(-th)}'
                       f'C{f(tw * .2)} {f(-th * .6)} {f(tw)} {f(-th * .45)} {f(tw)} 0Z" '
                       f'style="animation-duration:{f(rnd.uniform(.8, 1.5))}s;animation-delay:-{f(rnd.uniform(0, 1.5))}s"/></g>')
        return "".join(out)

    embers = "".join(
        f'<circle class="em" cx="{f(rnd.uniform(10, W - 10))}" cy="{f(H - rnd.uniform(4, 30))}" r="{f(rnd.uniform(1, 1.9))}" '
        f'style="animation-duration:{f(rnd.uniform(2.4, 4))}s;animation-delay:-{f(rnd.uniform(0, 4))}s"/>'
        for _ in range(14))
    return (f'<rect y="{VH}" width="{W}" height="{H - VH}" fill="url(#heat)"/>'
            + tongues(9, "fb", (26, 38), (52, 84)) + tongues(14, "ff", (14, 22), (30, 56)) + embers)


def rainy_doom():
    rnd = random.Random(1999)
    pic = fit_with_blur("rainy-doom.jpg", (960, 400))
    drop = (-40, VH)          # one rain tile moves along this vector each cycle
    streaks = []
    for _ in range(70):
        x, y, n = rnd.uniform(0, W + 40), rnd.uniform(0, VH), rnd.uniform(10, 22)
        streaks.append(f'M{f(x)} {f(y)}l{f(-n * 0.2)} {f(n)}')
    tile = f'<path d="{"".join(streaks)}"/>'
    visual = f'''<image href="{pic}" width="{W}" height="{VH}" preserveAspectRatio="xMidYMid slice"/>
    <rect width="{W}" height="{VH}" fill="#0b1119" opacity=".25"/>
    <g class="rain"><g>{tile}</g><g transform="translate({-drop[0]} {-drop[1]})">{tile}</g></g>
    <rect class="flash" width="{W}" height="{VH}" fill="#dbe9ff"/>'''
    defs = '''<linearGradient id="heat" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff5a1a" stop-opacity="0"/><stop offset="1" stop-color="#ff5a1a" stop-opacity=".28"/></linearGradient>
    <linearGradient id="fireBack" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ff7a1e" stop-opacity=".9"/><stop offset=".55" stop-color="#b3300a" stop-opacity=".75"/><stop offset="1" stop-color="#4a0b04" stop-opacity="0"/></linearGradient>
    <linearGradient id="fireFront" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ffd98a"/><stop offset=".4" stop-color="#ff8a24"/><stop offset="1" stop-color="#d2290a" stop-opacity="0"/></linearGradient>'''
    css = f'''.rain{{stroke:#cfe3f5;stroke-opacity:.45;stroke-width:1.1;stroke-linecap:round;animation:fall .8s linear infinite}}
    @keyframes fall{{to{{transform:translate({drop[0]}px,{drop[1]}px)}}}}
    .flash{{opacity:0;animation:flash 9s infinite}}
    @keyframes flash{{0%,71%{{opacity:0}}72%{{opacity:.38}}73%{{opacity:.05}}74.5%{{opacity:.24}}77%,100%{{opacity:0}}}}
    .fb,.ff{{transform-box:fill-box;transform-origin:50% 100%;animation:lick 1.2s ease-in-out infinite}}
    .fb{{fill:url(#fireBack)}}.ff{{fill:url(#fireFront);opacity:.85}}
    @keyframes lick{{0%,100%{{transform:scale(1,1)}}25%{{transform:scale(.9,1.2)}}50%{{transform:scale(1.06,.88)}}75%{{transform:scale(.94,1.12)}}}}
    .em{{fill:#ffd27a;opacity:0;animation:rise 3s linear infinite}}
    @keyframes rise{{0%{{opacity:0;transform:translate(0,0)}}15%{{opacity:1}}100%{{opacity:0;transform:translate(-14px,-96px)}}}}
    .ti,.tg{{stroke:#120604;stroke-opacity:.85;stroke-width:6px;stroke-linejoin:round;paint-order:stroke}}'''
    return card("Rainy Doom, my Black Ops III Zombies map, with 5,100 subscribers on the Steam Workshop. Made by hand.",
                "RAINY DOOM", "BO3 Zombies map · 5,100 subs", HANDMADE, "#ff8a4a", visual, css, defs, flames(rnd))


# ---------------------------------------------------------------- T7 Companion: current runs through the logo

def t7_companion():
    rnd = random.Random(7)
    src = open(os.path.join(SRC, "t7-logo.svg"), encoding="utf-8").read()
    body = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    body = re.sub(r"<title>.*?</title>", "", body, flags=re.S)
    for old in ("grid", "c0", "c1", "c2"):          # keep the logo's ids apart from the card's
        body = body.replace(f'id="{old}"', f'id="t7{old}"').replace(f"url(#{old})", f"url(#t7{old})")

    def pulses(group):
        lines = re.findall(r'<polyline points="([^"]+)"', group)
        out = []
        for i, pts in enumerate(lines):
            if i % 3:
                continue
            out.append(f'<polyline class="pl" points="{pts}" pathLength="100" '
                       f'style="animation-delay:-{f(rnd.uniform(0, 3.4))}s;animation-duration:{f(rnd.uniform(2.6, 4.2))}s"/>')
        return group + "".join(out)

    body = re.sub(r'(<g clip-path="url\(#t7c\d\)">)(.*?)(</g>)',
                  lambda m: m.group(1) + pulses(m.group(2)) + m.group(3), body, flags=re.S)

    def blink(m):
        if rnd.random() > 0.14:
            return m.group(0)
        return m.group(0).replace("<circle ", f'<circle class="bl" style="animation-delay:-{f(rnd.uniform(0, 5))}s" ', 1)

    body = re.sub(r"<circle [^>]*/>", blink, body)
    s = 0.86
    visual = f'''<rect width="{W}" height="{VH}" fill="url(#bggrid)"/>
    <ellipse cx="{W / 2}" cy="{VH / 2}" rx="150" ry="90" fill="url(#halo)"/>
    <g transform="translate({f(W / 2 - 128 * s)} {f(VH / 2 - 128 * s)}) scale({s})">{body}</g>'''
    defs = '''<pattern id="bggrid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0H0V16" fill="none" stroke="#9fd8ff" stroke-opacity=".06"/></pattern>
    <radialGradient id="halo"><stop offset="0" stop-color="#1f6feb" stop-opacity=".35"/><stop offset="1" stop-color="#1f6feb" stop-opacity="0"/></radialGradient>'''
    css = '''.pl{fill:none;stroke:#f0faff;stroke-width:2.6;stroke-linecap:round;stroke-dasharray:5 95;stroke-dashoffset:100;animation:run 3.4s linear infinite}
    @keyframes run{to{stroke-dashoffset:0}}
    .bl{animation:bl 5s infinite}
    @keyframes bl{0%,86%,100%{fill:#0b2a4a}90%{fill:#bfe6ff}}'''
    return card("T7 Companion: an AI modding toolkit for Black Ops III, its circuit logo pulsing. Written with an AI agent, reviewed by me.",
                "T7 COMPANION", "AI modding toolkit for BO3", AI_ASSISTED, "#79c0ff", visual, css, defs)


# ---------------------------------------------------------------- Radio Norvinsk: on air

def radio_norvinsk():
    # The source is 1248x832; keep the radio and the city, below the painted title.
    box = (248, 400, 1248, 817)
    pic = crop_to("radio-norvinsk.jpg", box, (960, 400))
    sx = W / (box[2] - box[0])
    speaker = ((720 - box[0]) * sx, (645 - box[1]) * sx)    # centre of the speaker grille
    lamp = ((860.6 - box[0]) * sx, (613.1 - box[1]) * sx)  # the orange light on the front panel
    waves = "".join(
        f'<path class="wv" d="M{f(speaker[0] - 46)} {f(speaker[1] - 30)}a56 56 0 0 0 0 60" style="animation-delay:-{f(i * 0.8)}s"/>'
        for i in range(3))
    visual = f'''<image href="{pic}" width="{W}" height="{VH}" preserveAspectRatio="xMidYMid slice"/>
    <g transform-origin="{f(speaker[0])} {f(speaker[1])}">{waves}</g>
    <circle class="lamp" cx="{f(lamp[0])}" cy="{f(lamp[1])}" r="3.6"/>
    <g transform="translate(18 18)"><rect width="78" height="24" rx="4" fill="#0d1117" fill-opacity=".75"/>
      <circle class="lamp" cx="14" cy="12" r="4.5"/><text x="26" y="16.5" class="ch" fill="#ffb3a8">ON AIR</text></g>'''
    css = f'''.wv{{fill:none;stroke:#e3b341;stroke-width:3;stroke-linecap:round;transform-box:view-box;transform-origin:{f(speaker[0])}px {f(speaker[1])}px;animation:wave 2.4s ease-out infinite}}
    @keyframes wave{{0%{{opacity:0;transform:translate(0,0) scale(.6)}}15%{{opacity:.9}}100%{{opacity:0;transform:translate(-26px,0) scale(1.6)}}}}
    .lamp{{fill:#ff5a4a;animation:lamp 1.6s steps(1) infinite}}
    @keyframes lamp{{50%{{fill:#5a1712}}}}'''
    return card("Radio Norvinsk: a radio host that tells your friends' Tarkov raids in Discord, on air. Written by an AI agent.",
                "RADIO NORVINSK", "SPT raids, told in Discord", AI_BUILT, "#e3b341", visual, css)


# ---------------------------------------------------------------- Homelab: Git flows into the cluster

def homelab():
    def box(x, y, w, h, title, sub, cls="bx"):
        return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="7"/>'
                f'<text x="{x + w / 2}" y="{y + h / 2 - 2}" text-anchor="middle" class="bt">{title}</text>'
                f'<text x="{x + w / 2}" y="{y + h / 2 + 15}" text-anchor="middle" class="bs">{sub}</text>')

    # Everything sits below y=44: the chip takes the card's top-right corner.
    chips = "".join(
        f'<rect class="cp" x="330" y="{y}" width="118" height="26" rx="6" style="animation-delay:{f(i * 0.6)}s"/>'
        f'<text x="389" y="{y + 18}" text-anchor="middle" class="cpt">{name}</text>'
        for i, (y, name) in enumerate([(96, "Traefik"), (128, "cert-manager"), (160, "Authelia")]))
    visual = f'''<rect width="{W}" height="{VH}" fill="url(#bggrid)"/>
    {box(24, 46, 120, 56, "GitHub", "repo + SOPS")}
    {box(174, 46, 120, 56, "Argo CD", "app of apps")}
    {box(24, 130, 120, 56, "OpenTofu", "VPS + DNS")}
    <rect class="k3s" x="318" y="50" width="142" height="144" rx="10"/>
    <text x="389" y="72" text-anchor="middle" class="bt">k3s</text>
    <text x="389" y="88" text-anchor="middle" class="bs">OVH VPS</text>
    {chips}
    <path class="fl" d="M144 74H168"/><path class="fl" d="M294 74H312"/><path class="fl" d="M144 158H312"/>
    <path class="ah" d="M168 69l7 5-7 5z"/><path class="ah" d="M312 69l7 5-7 5z"/><path class="ah" d="M312 153l7 5-7 5z"/>
    <text x="228" y="150" text-anchor="middle" class="bs">provisions</text>'''
    defs = '<pattern id="bggrid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0H0V16" fill="none" stroke="#9fd8ff" stroke-opacity=".06"/></pattern>'
    css = f'''.bx{{fill:#161b22;stroke:{BORDER};stroke-width:1.5}}
    .k3s{{fill:#0d1d33;stroke:#58a6ff;stroke-width:1.5;animation:k3s 3s ease-in-out infinite}}
    @keyframes k3s{{50%{{stroke:#a5d6ff}}}}
    .bt{{font:700 17px 'Segoe UI',-apple-system,Helvetica,Arial,sans-serif;fill:{TEXT}}}
    .bs{{font:12.5px 'Segoe UI',-apple-system,Helvetica,Arial,sans-serif;fill:#8b949e}}
    .cp{{fill:#161b22;stroke:{BORDER};stroke-width:1.5;animation:cp 1.8s ease-in-out infinite}}
    @keyframes cp{{0%,60%,100%{{stroke:{BORDER}}}30%{{stroke:#58a6ff}}}}
    .cpt{{font:13.5px 'Segoe UI',-apple-system,Helvetica,Arial,sans-serif;fill:{TEXT}}}
    .fl{{fill:none;stroke:#58a6ff;stroke-width:2.5;stroke-dasharray:6 5;animation:flow .9s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-11}}}}
    .ah{{fill:#58a6ff}}'''
    return card("Homelab: GitHub and Argo CD deploy to k3s on an OVH VPS, provisioned by OpenTofu, rebuilt from Git. Written with an AI agent, reviewed by me.",
                "HOMELAB", "k3s on OVH, rebuilt from Git", AI_ASSISTED, "#f0883e", visual, css, defs)


CARDS = {"rainy-doom": rainy_doom, "t7-companion": t7_companion,
         "radio-norvinsk": radio_norvinsk, "homelab": homelab}

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "assets", "cards")
    os.makedirs(out, exist_ok=True)
    for name, make in CARDS.items():
        path = os.path.join(out, name + ".svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(make())
        print(f"{path}  {os.path.getsize(path) // 1024} KB")
