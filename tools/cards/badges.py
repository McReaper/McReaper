"""Generate the profile badges (links and stack) in the cards' style: a dark rounded chip,
the brand's icon and a monospace label.

Usage: python tools/cards/badges.py [out_dir]   (default: assets/badges)
Icons come from tools/cards/src/icons.json, copied from Simple Icons (CC0 1.0).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = json.load(open(os.path.join(HERE, "src", "icons.json"), encoding="utf-8"))

H = 32
ICON = 16                  # Simple Icons are drawn on a 24x24 grid
PAD_L, GAP, PAD_R = 8, 7, 9
CHAR = 7.8                 # forced advance per character (textLength), the same in any monospace font
MONO_FONT = "ui-monospace,'Cascadia Mono',Consolas,Menlo,'DejaVu Sans Mono',monospace"
BG, BORDER, TEXT, MUTED = "#0d1117", "#30363d", "#e6edf3", "#8b949e"

# Brand colours too dark to read on the badge's dark background.
LIGHTER = {"steam": "#c7d5e0", "dotnet": "#a78bfa", "linkedin": "#4a9be8", "kubernetes": "#6a9bf4"}

# A crosshair for SPT, which has no brand icon (drawn on the same 24x24 grid).
CROSSHAIR = '<circle cx="12" cy="12" r="8.5"/><path d="M12 1v7M12 16v7M1 12h7M16 12h7"/>'

# name: (icon, colour or None for the brand's, label, value shown muted after the label)
BADGES = {
    "steam": ("steam", None, "STEAM WORKSHOP", ""),
    "spt": (None, "#c8b98a", "SPT MODS", ""),
    "linkedin": ("linkedin", None, "LINKEDIN", ""),
    "discord": ("discord", None, "DISCORD", "reapy"),
    "csharp": ("dotnet", None, "C#", ""),
    "go": ("go", None, "GO", ""),
    "claude-code": ("claude", None, "CLAUDE CODE", ""),
    "python": ("python", None, "PYTHON", ""),
    "kubernetes": ("kubernetes", None, "K8S", ""),
    "argo-cd": ("argo", None, "ARGO CD", ""),
    "opentofu": ("opentofu", None, "OPENTOFU", ""),
    "docker": ("docker", None, "DOCKER", ""),
    "github-actions": ("githubactions", None, "GH ACTIONS", ""),
}


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def badge(icon, colour, label, value):
    place = f'transform="translate({PAD_L} {(H - ICON) / 2}) scale({f(ICON / 24)})"'
    if icon:
        colour = colour or LIGHTER.get(icon, "#" + ICONS[icon]["hex"])
        glyph = f'<path {place} fill="{colour}" d="{ICONS[icon]["path"]}"><title>{ICONS[icon]["title"]}</title></path>'
    else:
        glyph = f'<g {place} fill="none" stroke="{colour}" stroke-width="2.4">{CROSSHAIR}</g>'
    text = label + (" " + value if value else "")
    tw = len(text) * CHAR
    w = PAD_L + ICON + GAP + tw + PAD_R
    tx = PAD_L + ICON + GAP
    value_span = f'<tspan fill="{MUTED}"> {value}</tspan>' if value else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{f(w)}" height="{H}" viewBox="0 0 {f(w)} {H}" role="img" aria-label="{text}">
  <title>{text}</title>
  <rect x=".75" y=".75" width="{f(w - 1.5)}" height="{H - 1.5}" rx="8" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>
  {glyph}
  <text x="{tx}" y="{H / 2 + 4.6}" textLength="{f(tw)}" lengthAdjust="spacing" fill="{TEXT}" font-family="{MONO_FONT}" font-size="13" font-weight="600">{label}{value_span}</text>
</svg>
'''


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "assets", "badges")
    os.makedirs(out, exist_ok=True)
    for name, spec in BADGES.items():
        with open(os.path.join(out, name + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(badge(*spec))
    print(f"{len(BADGES)} badges in {os.path.normpath(out)}")
