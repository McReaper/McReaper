"""Generate the Rainy Doom profile header: rain, the hell-round switch, hell, back to rain,
with a shooter holding the street against a horde.

Usage: python tools/header/header.py [out.svg]   (default: assets/header.svg)
Needs Pillow with WebP support (blots.py draws the smoke clump textures).

Loop is 20 s. The switch mirrors zm_hellround_environment: 0.75 s blend into the
transition fog, held until 1 s, then 0.75 s into the bloody fog.
  0-5 s      rain
  5.0 s      black smoke + quake, rain -> transition fog (25% -> 28.75%)
  6.0 s      transition fog -> hell, the sky burns (30% -> 33.75%)
  9.0-9.7 s  meteor, impact quake at 9.7 s
  14.0 s     black smoke + quake, hell -> transition fog (70% -> 73.75%)
  15.0 s     transition fog -> rain (75% -> 78.75%)
The horde: zombies walk in from the right at one speed, so the leading one is always
the next to die; each takes two shots and falls backward, a little closer each time.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blots  # noqa: E402  (smoke clump textures, next to this script)

random.seed(1999)

W, H = 1000, 320
L = 20.0            # loop, seconds
BAND = 268          # top of the ticker band; the scene lives above it
BASE = 266          # street line, where feet stand
FALL = (-66, 300)   # one rain tile: the rain moves along this vector each loop

SHOOTER_X = 70
CH = 1.15           # character scale
MUZZLE = (SHOOTER_X + 38.1 * CH, BASE - 38.4 * CH)   # front of the muzzle brake
LIGHT = (SHOOTER_X + 27 * CH, BASE - 35.7 * CH)      # weapon light lens, where the beam starts
EJECT = (SHOOTER_X + 12 * CH, BASE - 41 * CH)        # ejection port
SPAWN_X = 1040
ZOMBIE_SPEED = 52   # px/s
BULLET_SPEED = 5000
FIRST_SHOT = 0.55   # first hit lands this long before the killing one
# (kill time s, kill x): the leading zombie dies each time, a bit closer to the shooter
KILLS = [(1.4, 820), (3.9, 740), (6.6, 640), (9.9, 520), (12.5, 430), (15.2, 330), (17.9, 250)]

RAIN_TEXT = ("SOFTWARE ENGINEER  ·  GO  ·  C#  ·  PYTHON  ·  K3S HOMELAB  ·  ARGO CD  ·  "
             "OPENTOFU  ·  DOCKER  ·  BUILDS WITH CLAUDE CODE  ·  GRENOBLE, FRANCE  ·  ")
HELL_TEXT = ("ZOMBIES MAPPER  ·  RAINY DOOM: 5,100 SUBSCRIBERS  ·  T7 COMPANION, AN AI "
             "MODDING TOOLKIT FOR BO3  ·  RADIANT  ·  GSC  ·  SPT MODS IN C#  ·  ")
TICK_FONT = 20
TICK_ADV = 12.4     # forced advance per char (textLength), so the loop is seamless in any font
TICK_SPEED = 58     # px per second


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- timelines

def cyclic_keyframes(name, events, fmt):
    """Periodic piecewise-linear track. events: (time s, values tuple), any order, times may
    fall outside [0, L); the whole track must span less than L. Use with linear timing."""
    ev = sorted(((t % L, v) for t, v in events), key=lambda e: e[0])
    (t_first, v_first), (t_last, v_last) = ev[0], ev[-1]
    gap = t_first + (L - t_last)
    u = (L - t_last) / gap if gap else 0.0
    v0 = tuple(a + (b - a) * u for a, b in zip(v_last, v_first))
    pts = [(0.0, v0)] + ev + [(L, v0)]
    body = "".join(f"{t / L * 100:.3f}%{{{fmt(*v)}}}" for t, v in pts)
    return f"@keyframes {name}{{{body}}}"


def zombie_x(td, xd, t):
    return xd + (td - t) * ZOMBIE_SPEED


def check_horde():
    """The leading zombie must be the one shot, and walkers must not overlap."""
    spawns = [td - (SPAWN_X - xd) / ZOMBIE_SPEED for td, xd in KILLS]
    for i in range(len(KILLS)):
        nxt = (i + 1) % len(KILLS)
        gap = (spawns[nxt] + (L if nxt == 0 else 0)) - spawns[i]
        assert gap * ZOMBIE_SPEED >= 38, f"zombies {i} and {nxt} too close: {gap * ZOMBIE_SPEED:.0f}px"
    for (td, xd), ts in zip(KILLS, spawns):
        assert td - ts + 1.6 < L, "a walker would still be up when it respawns"
    return spawns


# ---------------------------------------------------------------- drawing helpers

def rain_path(n, lmin, lmax):
    slant = FALL[0] / FALL[1]
    d = []
    for _ in range(n):
        x, y = random.uniform(-40, 1100), random.uniform(0, FALL[1])
        length = random.uniform(lmin, lmax)
        for ox, oy in ((0, 0), (-FALL[0], -FALL[1])):
            d.append(f"M{f(x + ox)} {f(y + oy)}l{f(slant * length)} {f(length)}")
    return "".join(d)


def bolt_path(x0, x1, y1, seed):
    rnd = random.Random(seed)
    pts = [(x0, -5)]
    steps = 9
    for i in range(1, steps + 1):
        pts.append((x0 + (x1 - x0) * i / steps + rnd.uniform(-18, 18), -5 + (y1 + 5) * i / steps))
    bx, by = pts[4]
    return ("M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts) +
            f" M{f(bx)} {f(by)} L{f(bx + 26)} {f(by + 24)} L{f(bx + 22)} {f(by + 46)} L{f(bx + 44)} {f(by + 70)}")


def flame_path(h, w, tip=0.0):
    t = tip * w
    return (f"M{f(-w / 2)} 0C{f(-w / 2)} {f(-h * .4)} {f(t - w * .2)} {f(-h * .5)} {f(t)} {f(-h)}"
            f"C{f(t + w * .05)} {f(-h * .6)} {f(w / 2)} {f(-h * .4)} {f(w / 2)} 0Z")


def flame(x, base, h, grad, wmin=.38, wmax=.5):
    w = h * random.uniform(wmin, wmax)
    k, dur = random.randint(1, 3), random.uniform(.55, 1.1)
    tip = random.uniform(-.35, .35)
    return (f'<g transform="translate({f(x)} {base})"><path class="fk{k}" d="{flame_path(h, w, tip)}" fill="url(#{grad})" '
            f'style="animation-duration:{dur:.2f}s;animation-delay:-{random.uniform(0, dur):.2f}s"/></g>')


def fire_wall():
    out = []
    rows = ((40, 46, 86, 50, "flameBack", .6, .85),    # tall, deep red, wide and overlapping
            (34, 22, 50, 22, "flameMid", .55, .8))     # shorter, brighter tongues in front
    for row, (n, hmin, hmax, side, grad, wmin, wmax) in enumerate(rows):
        for i in range(n):
            x = -30 + 1060 * (i + random.uniform(-.35, .35) + row * .5) / (n - 1)
            h = random.uniform(hmin, hmax)
            if x < 290 or x > 710:
                h += random.uniform(.4, 1) * side
            out.append(flame(x, 258, h, grad, wmin, wmax))
    return "\n      ".join(out)


def street_fires():
    out = []
    for cx in (238, 468, 612, 906):
        for _ in range(random.randint(3, 4)):
            out.append(flame(cx + random.uniform(-14, 14), BASE - 1, random.uniform(14, 34), "flameFront"))
    return "\n      ".join(out)


def smoke():
    out = []
    for _ in range(8):
        out.append(f'<ellipse cx="{f(random.uniform(-40, 1140))}" cy="{f(random.uniform(0, 70))}" '
                   f'rx="{f(random.uniform(150, 260))}" ry="{f(random.uniform(35, 70))}" fill="url(#smoke)"/>')
    return "".join(out)


def skyline():
    """Small-town silhouette: houses, a gas-station canopy, a church, a water tower, poles."""
    base = BASE
    shapes, windows = [], []

    def house(x, w, h, roof):
        shapes.append(f'<path d="M{x} {base}V{base - h}L{f(x + w / 2)} {base - h - roof}L{x + w} {base - h}V{base}Z"/>')
        for wx in (x + w * 0.22, x + w * 0.62):
            windows.append((wx, base - h * 0.62, w * 0.14, h * 0.28))

    def trees(x0, x1, top):
        d, x = [f"M{x0} {base}"], x0
        while x < x1:
            r = random.uniform(12, 20)
            d.append(f"Q{f(x + r)} {f(top - random.uniform(0, 10))} {f(x + 2 * r)} {base - 14}")
            x += 2 * r
        d.append(f"L{f(x)} {base}Z")
        shapes.append(f'<path d="{"".join(d)}"/>')

    trees(-20, 52, 226)
    house(48, 72, 28, 20)
    shapes.append(f'<path d="M154 {base}L162 204H166L160 {base}ZM190 {base}L184 204H188L194 {base}Z"/>')
    shapes.append('<rect x="150" y="176" width="48" height="30" rx="5"/><path d="M148 177L174 160L200 177Z"/>')
    house(206, 92, 34, 22)
    trees(296, 352, 230)
    house(352, 62, 24, 16)
    shapes.append(f'<rect x="424" y="226" width="150" height="9"/><rect x="436" y="235" width="5" height="{base - 235}"/>'
                  f'<rect x="557" y="235" width="5" height="{base - 235}"/><rect x="476" y="246" width="44" height="{base - 246}"/>')
    windows.append((482, 250, 32, 9))
    house(584, 82, 30, 20)
    trees(664, 726, 228)
    house(728, 92, 40, 26)
    shapes.append(f'<rect x="816" y="{base - 74}" width="32" height="74"/><path d="M812 {base - 74}L832 {base - 132}L852 {base - 74}Z"/>')
    windows.append((826, base - 60, 12, 16))
    house(862, 76, 30, 18)
    trees(932, 1030, 226)
    poles = [104, 330, 672, 958]
    for p in poles:
        shapes.append(f'<rect x="{p - 2}" y="214" width="4" height="{base - 214}"/><rect x="{p - 11}" y="218" width="22" height="3"/>')
    wires = " ".join(f"M{a} {dy}Q{(a + b) / 2} {dy + 16} {b} {dy}" for a, b in zip(poles, poles[1:]) for dy in (219, 224))
    return "\n    ".join(shapes), windows, wires


ZOMBIE_KINDS = ["shambler", "limper", "onearm", "brute", "shambler", "limper", "onearm"]


def zombie(i, td, xd, ts):
    """A zombie facing left, feet at the origin. Returns (markup, keyframes).

    Human build, not spindly: trousered legs with a knee that bends a little on a short
    shuffling stride, shoes, a slumped torso with broad shoulders and a ragged shirt, a short
    neck, a head with a tuft of hair, thick arms held out with drooping hands and torn
    sleeves. Kinds: shambler (both arms out), limper (drags a leg, one arm hanging),
    onearm (a stump), brute (bigger, broader). Gait loops carry the class "gait".
    """
    rnd = random.Random(100 + i)
    kind = ZOMBIE_KINDS[i % len(ZOMBIE_KINDS)]
    s = (1.12 if kind == "brute" else rnd.uniform(.95, 1.03)) * CH
    gait = 1.6 if kind == "limper" else rnd.uniform(1.15, 1.35)
    lean = rnd.uniform(-5, -3.5)            # shoulders a little ahead of the hips: slumped, not folded
    phase = rnd.uniform(0, gait)
    hip = -24

    def anim(name, dur, delay=0.0):
        return f'class="gait {name}" style="animation-duration:{dur:.2f}s;animation-delay:-{(phase + delay) % dur:.2f}s"'

    def leg(thigh, shin, delay):
        return (f'<g transform="translate(0 {hip})"><g {anim(thigh, gait, delay)}><path d="M0 0L0 12" stroke-width="6.2"/>'
                f'<g transform="translate(0 12)"><g {anim(shin, gait, delay)}><path d="M0 0L0 11.4" stroke-width="5.2"/>'
                f'<path d="M1.6 11.6L-4.6 11.8" stroke-width="3.4"/></g></g></g></g>')

    sx, sy = lean - .5, -40.5               # shoulder

    def arm(motion, delay, upper, fore, width=4.6):
        ux, uy = upper
        fx, fy = fore
        return (f'<g transform="translate({f(sx)} {sy})"><g {anim(motion, gait, delay)}>'
                f'<path d="M0 0L{ux} {uy}" stroke-width="{width}"/>'
                f'<path d="M-1.4 1.8L{f(ux * .55)} {f(uy * .55 + 5.4)}L{f(ux * .8)} {f(uy * .8 + 2)}Z" stroke-width=".8"/>'  # torn sleeve
                f'<g transform="translate({ux} {uy})"><path d="M0 0L{fx} {fy}" stroke-width="{width - .8:.1f}"/>'
                f'<path d="M{fx} {fy}l-2.2 2.2" stroke-width="{width - 1.4:.1f}"/></g></g></g>')                # drooping hand

    reach_far = arm("reach", gait / 2, (-7, 2), (-6.5, .5))
    reach_near = arm("reach", 0, (-7.5, 1.2), (-6.5, 0), width=5.4 if kind == "brute" else 4.6)
    hanging = arm("dangle", 0, (-1.5, 9.5), (-.5, 8.5))
    stump = (f'<g transform="translate({f(sx)} {sy})"><path d="M0 0L-3 3.4" stroke-width="5"/>'
             f'<path d="M-1.4 2L-5.2 6.4L-3.4 2.2Z" stroke-width=".8"/></g>')
    far_arm, near_arm = {"shambler": (reach_far, reach_near), "limper": (reach_far, hanging),
                         "onearm": (reach_far, stump), "brute": (reach_far, reach_near)}[kind]
    far_leg = leg("thA", "shA", gait / 2)
    near_leg = leg("thD", "shD", 0) if kind == "limper" else leg("thA", "shA", 0)

    # slumped torso, broad shoulders, ragged shirt hem; the brute is broader still
    broad = 1.22 if kind == "brute" else 1.0
    torso = (f'<g transform="scale({broad} 1)"><path d="M4.4 -22.5L{f(lean + 6)} -41.4Q{f(lean + 2)} -44 {f(lean - 4.4)} -42'
             f'L-4.8 -31.5L-4.6 -22.5L-4.8 -19.8L-2.8 -21.6L-1 -19.2L.8 -21.4L2.6 -19.4L4.6 -21.2Z" stroke-width="1.4"/></g>')
    hx, hy = lean - 2.2, -47.6
    head = (f'<path d="M{f(lean)} -41.5L{f(hx + .6)} {f(hy + 2)}" stroke-width="4.4"/>'             # short neck
            f'<g transform="translate({f(hx)} {f(hy)})"><g {anim("loll", gait * 1.6)}>'
            f'<circle r="5.2" stroke="none"/><path d="M-4.8 1.4Q-5.2 4.8 -1.8 5.4L.4 3.6Z" stroke="none"/>'  # skull + slack jaw
            f'<path d="M-1.6 -5Q3.4 -7.2 5.6 -2.2L4.4 -.6Q3 -3.6 -.8 -3.8Z" stroke="none"/>'               # tuft of hair
            f'<g transform="scale(.62)" stroke-width=".6"><g class="horns">'
            f'<path d="M-3.6 -3.6C-9 -5 -11 -10 -9 -16.5C-7.4 -11.5 -4 -8.6 -.4 -5.4Z"/><path d="M1.4 -5.3C5 -8 8.4 -10.5 7.4 -16C10.6 -10.4 8.6 -5.6 4.4 -3.2Z"/></g></g>'
            f'<circle class="vR" cx="-3" cy="-.8" r="3.6" fill="url(#eyeRain)" stroke="none"/>'
            f'<circle class="vH" cx="-3" cy="-.8" r="5.2" fill="url(#eyeHell)" stroke="none"/>'
            f'<circle class="eye" cx="-3" cy="-.8" r="1.3" stroke="none"/></g></g>')
    upper = (f'<g transform="translate(0 {hip})"><g {anim("sway", gait / 2)}><g transform="translate(0 {-hip})">'
             f'{far_arm}{torso}{head}{near_arm}</g></g></g>')
    body = f'<g {anim("lurch", gait / 2)}>{far_leg}{upper}{near_leg}</g>'
    markup = (f'<g transform="translate(0 {BASE})"><g class="zw z{i}"><g transform="scale({s:.2f})" fill="#000" stroke="#000" '
              f'stroke-linecap="round" stroke-linejoin="round">{body}</g></g></g>')
    ev = [(ts - .05, (SPAWN_X, 0, 0)), (ts, (SPAWN_X, 0, 1)), (td, (xd, 0, 1)), (td + .12, (xd + 5, 16, 1)),
          (td + .45, (xd + 12, 84, 1)), (td + .9, (xd + 12, 84, 1)), (td + 1.5, (xd + 12, 84, 0)), (td + 1.55, (SPAWN_X, 0, 0))]
    kf = cyclic_keyframes(f"z{i}", ev, lambda x, r, o: f"transform:translate({x:.1f}px,0) rotate({r:.1f}deg);opacity:{o:.2f}")
    return markup, kf


def shots():
    """Tracers, hit puffs, muzzle flash and recoil for every shot."""
    tracers, puffs, casings, kfs = [], [], [], []
    flash_ev, recoil_ev = [], []
    n = 0
    for td, xd in KILLS:
        for arrive in (td - FIRST_SHOT, td):
            tx = zombie_x(td, xd, arrive) - 6
            leave = arrive - (tx - MUZZLE[0]) / BULLET_SPEED
            tracers.append(f'<path class="tr t{n}" d="M0 {MUZZLE[1]}h-26"/>')
            kfs.append(cyclic_keyframes(f"t{n}", [(leave - .01, (MUZZLE[0], 0)), (leave, (MUZZLE[0], 1)),
                                                  (arrive, (tx, 1)), (arrive + .01, (tx, 0))],
                                        lambda x, o: f"transform:translateX({x:.1f}px);opacity:{o:.0f}"))
            puffs.append(f'<g transform="translate({f(tx)} {f(BASE - 33 * CH)})"><circle class="pf p{n}" r="5" fill="#7d0a08"/></g>')
            kfs.append(cyclic_keyframes(f"p{n}", [(arrive - .01, (.2, 0)), (arrive, (.3, 1)), (arrive + .35, (1.7, 0))],
                                        lambda s, o: f"transform:scale({s:.2f});opacity:{o:.2f}"))
            drop = BASE - EJECT[1] - 1
            casings.append(f'<g transform="translate({f(EJECT[0])} {f(EJECT[1])})"><rect class="cs c{n}" x="-1.2" y="-.6" width="2.4" height="1.2" rx=".4" fill="#e0ab48"/></g>')
            kfs.append(cyclic_keyframes(f"c{n}", [(leave - .01, (0, 0, 0, 0)), (leave, (0, 0, 0, 1)), (leave + .12, (-6, -11, 200, 1)),
                                                  (leave + .26, (-11, -7, 420, 1)), (leave + .5, (-16, drop, 700, 1)),
                                                  (leave + .9, (-17, drop, 700, 1)), (leave + 1.1, (-17, drop, 700, 0))],
                                        lambda x, y, r, o: f"transform:translate({x:.1f}px,{y:.1f}px) rotate({r:.0f}deg);opacity:{o:.2f}"))
            flash_ev += [(leave - .005, (0,)), (leave, (1,)), (leave + .05, (1,)), (leave + .06, (0,))]
            recoil_ev += [(leave - .005, (0,)), (leave + .01, (-2.5,)), (leave + .09, (0,))]
            n += 1
    kfs.append(cyclic_keyframes("muzzle", flash_ev, lambda o: f"opacity:{o:.0f}"))
    kfs.append(cyclic_keyframes("recoil", recoil_ev, lambda x: f"transform:translateX({x:.1f}px)"))
    return "".join(tracers), "".join(puffs), "".join(casings), kfs


def shooter():
    """A rifleman facing right, feet at the origin, drawn in local units (scaled by CH)."""
    x, b = SHOOTER_X, BASE
    mx, my = (MUZZLE[0] - x) / CH, (MUZZLE[1] - b) / CH
    lx, ly = (LIGHT[0] - x) / CH, (LIGHT[1] - b) / CH
    rifle = ('<path d="M-5 -40.6L4 -40.2V-35.6L-5 -33.6Z"/>'                     # stock
             '<rect x="3.5" y="-40.8" width="15" height="4.6" rx=".6"/>'           # receiver
             '<path d="M8 -40.8V-42.2H7.2V-44.4H15V-42.2H14.2V-40.8Z"/>'           # optic on its mount
             '<rect x="18" y="-40.3" width="10.5" height="3.6" rx=".5"/>'          # handguard
             '<rect x="28" y="-39.2" width="8" height="1.6"/>'                     # barrel
             '<rect x="35.5" y="-39.9" width="2.6" height="3" rx=".4"/>'           # muzzle brake
             '<path d="M7.6 -36.4H10.4L9.2 -31.6H6.6Z"/>'                          # pistol grip
             '<path d="M12.6 -36.4H16L17.8 -30.4L14.8 -29.8Z"/>'                   # magazine
             '<rect x="21.5" y="-36.9" width="5.5" height="2.4" rx="1"/>'          # weapon light
             '<rect x="20" y="-35" width="2" height="3.2" rx=".6"/>')              # foregrip
    body = ('<path d="M-1 -23L-5 -12L-9 -1M2 -23L8 -13L7 -1" stroke="#000" stroke-width="5.4" fill="none"/>'   # rear leg straight, front knee bent
            '<path d="M-12.6 .2H-5.6V-3.2H-10.4Z"/><path d="M4.8 .2H12.2V-2.9H5.4Z"/>'           # boots
            '<rect x="6.6" y="-16" width="3.8" height="4.2" rx="1"/>'                            # knee pad
            '<rect x="-9.8" y="-41.5" width="6.8" height="15.5" rx="2.2"/>'                      # backpack
            '<path d="M-4 -42.8Q1.2 -44.8 6.8 -42.8L7.4 -24H-3.8Z"/>'                           # torso + plate carrier
            '<rect x="-4.8" y="-26.4" width="12.6" height="3.6" rx="1"/>'                        # belt
            '<rect x="5" y="-33.4" width="3.8" height="4.6" rx=".8"/>'                           # chest pouch
            '<circle cx="3.4" cy="-47.2" r="4.6"/>'                                              # head
            '<path d="M-3 -47.6Q-2.6 -54.8 3.8 -54.8Q10.2 -54.6 10.2 -48.4L11.6 -47.6H-3Z"/>'    # helmet with brim
            '<rect x="9" y="-53.4" width="2.8" height="2.8" rx=".6"/>'                           # night-vision mount
            '<path d="M1 -40.6L-2.8 -33.6L7.8 -35.2" stroke="#000" stroke-width="4" fill="none"/>'             # trigger arm
            '<path d="M4.2 -40.6L13.2 -33.8L21 -34.4" stroke="#000" stroke-width="3.8" fill="none"/>')         # support arm on the foregrip
    return (f'<g transform="translate({x} {b}) scale({CH})"><g class="recoil" fill="#000" stroke="#000" stroke-linecap="round" stroke-linejoin="round">'
            f'<g stroke="none">{body}{rifle}</g>'
            f'<circle class="vR" cx="{f(lx)}" cy="{f(ly)}" r="1.1" fill="#eef6ff" stroke="none"/>'
            f'<g class="muzzle" transform="translate({f(mx)} {f(my)})" stroke="none">'
            f'<circle r="7" fill="url(#flashGlow)"/><path d="M0 -1.2L7 -4.5L10 -1L18 0L10 1L7 4.5L0 1.2Z" fill="#fff3c4"/></g>'
            f'</g></g>')


TRANSITIONS = (5.0, 14.0)   # rain -> hell, hell -> rain


def black_smoke():
    """The map's fx_hellround_transition, as it looks in game: opaque black clumps with torn
    edges burst at the camera (a heavy mass rising from the bottom, medium clumps around,
    small fragments flung outward), golden embers drift as bokeh, and the fog thickens and
    blurs the view for a moment. Clumps are generated textures (blots.py), drawn as particles
    the way the game does it. Everything stays under the ticker band."""
    rnd = random.Random(615)
    parts, kfs, names = [], [], []
    fmt = lambda dx, dy, r, s, o: f"transform:translate({dx:.1f}px,{dy:.1f}px) rotate({r:.1f}deg) scale({s:.3f});opacity:{o:.2f}"

    def particle(x, y, size, motion, life, peak, scale_from, scale_to, delay):
        n = len(names)
        dx, dy = motion
        rot = rnd.uniform(-12, 12)
        ev = []
        for T in TRANSITIONS:
            t0 = T + delay
            ev += [(t0 - .01, (0, 0, 0, scale_from, 0)), (t0, (0, 0, 0, scale_from, 0)),
                   (t0 + .28, (dx * .25, dy * .25, rot * .3, scale_from + (scale_to - scale_from) * .3, peak)),
                   (t0 + life * .6, (dx * .7, dy * .7, rot * .7, scale_from + (scale_to - scale_from) * .75, peak * .92)),
                   (t0 + life, (dx, dy, rot, scale_to, 0))]
        names.append(f"q{n}")
        kfs.append(cyclic_keyframes(f"q{n}", ev, fmt))
        parts.append(f'<g transform="translate({f(x)} {f(y)})"><g class="pk q{n}"><use href="#blot{rnd.randrange(6)}" '
                     f'transform="scale({size / 200:.3f})"/></g></g>')

    for _ in range(6):                       # the heavy mass rising from the bottom
        x, y = rnd.uniform(320, 980), rnd.uniform(215, 290)
        particle(x, y, rnd.uniform(230, 330), (rnd.uniform(-20, 20), rnd.uniform(-60, -30)), 2.3, .97, .8, 1.35, rnd.uniform(0, .15))
    for _ in range(12):                      # medium clumps around the view
        x, y = rnd.uniform(40, 960), rnd.uniform(50, 230)
        particle(x, y, rnd.uniform(120, 200), ((x - 500) * .12, (y - 150) * .15 - 10), 1.9, .95, .65, 1.3, rnd.uniform(0, .3))
    for _ in range(14):                      # small fragments flung outward
        x = rnd.choice((rnd.uniform(0, 300), rnd.uniform(700, 1000), rnd.uniform(0, 1000)))
        y = rnd.uniform(0, 160)
        particle(x, y, rnd.uniform(50, 110), ((x - 500) * .25, (y - 150) * .3 - 20), 1.5, .9, .6, 1.6, rnd.uniform(0, .35))

    embers_markup = []
    for n in range(28):                      # golden embers drifting as bokeh
        x, y = rnd.uniform(10, 990), rnd.uniform(10, 255)
        big = rnd.random() < .3
        r = rnd.uniform(6, 12) if big else rnd.uniform(1.4, 3.6)
        peak = rnd.uniform(.35, .55) if big else rnd.uniform(.7, 1)
        dx, dy = rnd.uniform(-25, 25), rnd.uniform(-45, -15)
        d = rnd.uniform(0, .5)
        ev = []
        for T in TRANSITIONS:
            ev += [(T + .15 + d, (0, 0, peak * 0)), (T + .6 + d, (dx * .2, dy * .2, peak)),
                   (T + 2.4 + d, (dx * .8, dy * .8, peak * .8)), (T + 3.4 + d, (dx, dy, 0))]
        names.append(f"g{n}")
        kfs.append(cyclic_keyframes(f"g{n}", ev, lambda a, b, o: f"transform:translate({a:.1f}px,{b:.1f}px);opacity:{o:.2f}"))
        embers_markup.append(f'<g transform="translate({f(x)} {f(y)})"><circle class="pk g{n}" r="{f(r)}" fill="url(#amberBokeh)"/></g>')

    textures = "".join(f'<image id="blot{i}" x="-100" y="-100" width="200" height="200" href="{blots.data_uri(img)}"/>'
                       for i, img in enumerate(blots.all_blots()))
    markup = (f'<g clip-path="url(#scene)"><rect class="fogT" x="0" y="0" width="{W}" height="{BAND}" fill="#7d6b55"/>'
              f'{"".join(parts)}{"".join(embers_markup)}</g>')
    css = "".join(f".{m}{{animation-name:{m}}}" for m in names)
    return markup, kfs, css, textures


def embers(n):
    out = []
    for _ in range(n):
        x, y = random.uniform(10, 990), random.uniform(196, 266)
        r = random.choice([2.4, 3, 3.6, 4.4, 5.2])
        g = random.choice(["emA", "emB", "emC"])
        k, dur = random.randint(1, 4), random.uniform(2.6, 5.4)
        out.append(f'<circle class="em e{k}" cx="{f(x)}" cy="{f(y)}" r="{r}" fill="url(#{g})" '
                   f'style="animation-duration:{dur:.2f}s;animation-delay:-{random.uniform(0, dur):.2f}s"/>')
    return "\n      ".join(out)


def ticker(cls, text, color, anim):
    width = round(len(text) * TICK_ADV)
    copies = "".join(
        f'<text x="{x}" y="{BAND + 33}" textLength="{width}" lengthAdjust="spacing" xml:space="preserve" '
        f'fill="{color}">{text}</text>' for x in (0, width))
    return (f'<g class="{cls}"><g class="{anim}" style="animation-duration:{width / TICK_SPEED:.2f}s">'
            f'{copies}</g></g>'), width


# ---------------------------------------------------------------- styles

STATIC_CSS = """
      .vR{animation:vR 20s infinite}
      .vH{opacity:0;animation:vH 20s infinite}
      .vHh{opacity:0;animation:vHh 20s infinite}
      .vT{opacity:0;animation:vT 20s infinite}
      .tC{animation:tC 20s infinite}
      .txR{animation:txR 20s infinite}
      .txH{opacity:0;animation:txH 20s infinite}
      .pk{opacity:0;animation-duration:20s;animation-timing-function:linear;animation-iteration-count:infinite}
      .fogT{opacity:0;animation:fogT 20s infinite}
      .dof{animation:dof 20s infinite}
      @keyframes fogT{0%,25%{opacity:0}27.5%,31%{opacity:.42}36%,70%{opacity:0}72.5%,76%{opacity:.42}81%,100%{opacity:0}}
      @keyframes dof{0%,24.9%{filter:none}25%{filter:blur(0px)}27.5%,32%{filter:blur(2.2px)}37%{filter:blur(0px)}37.1%,69.9%{filter:none}70%{filter:blur(0px)}72.5%,77%{filter:blur(2.2px)}82%{filter:blur(0px)}82.1%,100%{filter:none}}
      .fl3{opacity:0;animation:fl3 20s infinite}
      .lt{opacity:0;animation:lt 20s infinite}
      .bo1{opacity:0;animation:bo1 20s infinite}
      .bo2{opacity:0;animation:bo2 20s infinite}
      .quake{animation:quake 20s infinite}
      .meteor{opacity:0;animation:meteor 20s linear infinite}
      .impact{opacity:0;animation:impact 20s infinite}
      .kick{fill:#93a9bb;animation:kick 20s infinite}
      .bline{fill:#3f6f93;animation:bline 20s infinite}
      .lbg{fill:#0b1119;animation:lbg 20s infinite}
      .town{fill:#1b2836;animation:town 20s infinite}
      .wires{stroke:#1b2836;animation:wires 20s infinite}
      .eye{fill:#ffd98a;animation:eye 20s infinite}
      .fallF{animation:fall .9s linear infinite}
      .fallN{animation:fall .5s linear infinite}
      .drift{animation:drift 20s linear infinite}
      .heat{animation:heat 2.3s infinite}
      .pulse{animation:pulse 3.2s ease-in-out infinite}
      .blink{animation:blink 1.2s steps(1) infinite}
      .tkR{animation:tkR linear infinite}
      .tkH{animation:tkH linear infinite}
      .fk1,.fk2,.fk3{animation-timing-function:ease-in-out;animation-iteration-count:infinite}
      .fk1{animation-name:fk1}.fk2{animation-name:fk2}.fk3{animation-name:fk3}
      .em{opacity:0;animation-timing-function:linear;animation-iteration-count:infinite}
      .e1{animation-name:e1}.e2{animation-name:e2}.e3{animation-name:e3}.e4{animation-name:e4}
      .zw,.tr,.pf,.cs,.muzzle,.recoil{animation-duration:20s;animation-timing-function:linear;animation-iteration-count:infinite}
      .zw,.tr,.pf,.cs,.muzzle{opacity:0}
      .horns{transform:scale(0);animation:horns 20s infinite}
      .tr{stroke:#ffe9a0;stroke-width:1.6;stroke-linecap:round}
      .muzzle{animation-name:muzzle}.recoil{animation-name:recoil}
      .gait{animation-timing-function:ease-in-out;animation-iteration-count:infinite}
      .thA{animation-name:thA}.shA{animation-name:shA}.thD{animation-name:thD}.shD{animation-name:shD}
      .sway,.loll,.reach,.dangle,.lurch{animation-direction:alternate}
      .sway{animation-name:sway}.loll{animation-name:loll}.reach{animation-name:reach}.dangle{animation-name:dangle}.lurch{animation-name:lurch}
      .title{font:400 132px Impact,Haettenschweiler,'Arial Narrow Bold','Franklin Gothic Heavy','Arial Black',sans-serif;letter-spacing:8px}
      .mono{font-family:ui-monospace,'Cascadia Mono',Consolas,Menlo,'DejaVu Sans Mono',monospace;font-weight:600}

      @keyframes vR{0%,25%{opacity:1}28.75%,75%{opacity:0}78.75%,100%{opacity:1}}
      @keyframes vH{0%,30%{opacity:0}33.75%,70%{opacity:1}73.75%,100%{opacity:0}}
      @keyframes vHh{0%,29.9%{opacity:0}30%,74.9%{opacity:1}75%,100%{opacity:0}}
      @keyframes tC{0%,30%{opacity:1}33.75%,70%{opacity:0}73.75%,100%{opacity:1}}
      @keyframes vT{0%,25%{opacity:0}28.75%,30%{opacity:1}33.75%,70%{opacity:0}73.75%,75%{opacity:1}78.75%,100%{opacity:0}}
      @keyframes txR{0%,26.5%{opacity:1}27.5%,72.5%{opacity:0}73.5%,100%{opacity:1}}
      @keyframes txH{0%,27.5%{opacity:0}28.5%,71.5%{opacity:1}72.5%,100%{opacity:0}}
      @keyframes fl3{0%,48.5%{opacity:0}48.6%{opacity:.35}51%,100%{opacity:0}}
      @keyframes lt{0%,7.9%{opacity:0}8%{opacity:.5}8.4%{opacity:.06}8.9%{opacity:.38}10.5%,16.9%{opacity:0}17%{opacity:.22}17.6%,85.9%{opacity:0}86%{opacity:.45}86.4%{opacity:.05}86.9%{opacity:.32}88.5%,100%{opacity:0}}
      @keyframes bo1{0%,7.9%{opacity:0}8%{opacity:1}8.4%{opacity:0}8.9%{opacity:.85}9.6%,100%{opacity:0}}
      @keyframes bo2{0%,85.9%{opacity:0}86%{opacity:1}86.4%{opacity:0}86.9%{opacity:.8}87.6%,100%{opacity:0}}
      @keyframes quake{
        0%,24.9%,27.2%,48.4%,50.6%,69.9%,72.2%,100%{transform:translate(0,0)}
        25%{transform:translate(-7px,4px)}25.5%{transform:translate(6px,-3px)}26%{transform:translate(-4px,2px)}26.6%{transform:translate(3px,-2px)}
        48.5%{transform:translate(-9px,5px)}49%{transform:translate(8px,-4px)}49.6%{transform:translate(-5px,3px)}50.1%{transform:translate(3px,-1px)}
        70%{transform:translate(6px,-4px)}70.5%{transform:translate(-6px,3px)}71%{transform:translate(4px,-2px)}71.6%{transform:translate(-2px,1px)}
      }
      @keyframes meteor{0%,44.9%{opacity:0;transform:translate(1080px,-60px)}45%{opacity:1;transform:translate(1080px,-60px)}48.5%{opacity:1;transform:translate(592px,250px)}48.6%,100%{opacity:0;transform:translate(592px,250px)}}
      @keyframes impact{0%,48.4%{opacity:0}48.6%{opacity:1}57%,100%{opacity:0}}
      @keyframes kick{0%,25%{fill:#93a9bb}28.75%,75%{fill:#ff9b6a}78.75%,100%{fill:#93a9bb}}
      @keyframes bline{0%,25%{fill:#3f6f93}28.75%,75%{fill:#ff4d1a}78.75%,100%{fill:#3f6f93}}
      @keyframes lbg{0%,25%{fill:#0b1119}28.75%,75%{fill:#1d0603}78.75%,100%{fill:#0b1119}}
      @keyframes town{0%,25%{fill:#1b2836}28.75%,75%{fill:#3d1008}78.75%,100%{fill:#1b2836}}
      @keyframes wires{0%,25%{stroke:#1b2836}28.75%,75%{stroke:#3d1008}78.75%,100%{stroke:#1b2836}}
      @keyframes eye{0%,25%{fill:#ffd98a}28.75%,75%{fill:#f0d2ff}78.75%,100%{fill:#ffd98a}}
      @keyframes horns{0%,30%{transform:scale(0)}34%,70%{transform:scale(1)}73.75%,100%{transform:scale(0)}}
      @keyframes fall{from{transform:translate(0,0)}to{transform:translate(-66px,300px)}}
      @keyframes drift{to{transform:translateX(-110px)}}
      @keyframes heat{0%,100%{opacity:1}12%{opacity:.8}14%{opacity:1}47%{opacity:.9}49%{opacity:1}73%{opacity:.76}75%{opacity:1}}
      @keyframes pulse{0%,100%{opacity:.7}50%{opacity:1}}
      @keyframes blink{0%{opacity:1}50%{opacity:.25}}
      @keyframes fk1{0%,100%{transform:scale(1,1) skewX(0deg)}30%{transform:scale(.9,1.14) skewX(4deg)}60%{transform:scale(1.06,.9) skewX(-3deg)}}
      @keyframes fk2{0%,100%{transform:scale(1,.94) skewX(-2deg)}40%{transform:scale(.92,1.12) skewX(3deg)}70%{transform:scale(1.04,.96) skewX(-4deg)}}
      @keyframes fk3{0%,100%{transform:scale(.96,1.06) skewX(3deg)}25%{transform:scale(1.05,.9) skewX(-2deg)}65%{transform:scale(.9,1.16) skewX(2deg)}}
      @keyframes e1{0%{opacity:0;transform:translate(0,0)}12%{opacity:1}50%{transform:translate(-22px,-110px)}80%{opacity:.8}100%{opacity:0;transform:translate(-14px,-220px)}}
      @keyframes e2{0%{opacity:0;transform:translate(0,0)}12%{opacity:1}50%{transform:translate(18px,-120px)}80%{opacity:.8}100%{opacity:0;transform:translate(34px,-250px)}}
      @keyframes e3{0%{opacity:0;transform:translate(0,0)}12%{opacity:1}50%{transform:translate(-8px,-90px)}80%{opacity:.8}100%{opacity:0;transform:translate(16px,-170px)}}
      @keyframes e4{0%{opacity:0;transform:translate(0,0)}12%{opacity:1}50%{transform:translate(30px,-115px)}80%{opacity:.8}100%{opacity:0;transform:translate(10px,-235px)}}
      @keyframes thA{0%,100%{transform:rotate(14deg)}50%{transform:rotate(-12deg)}}
      @keyframes shA{0%,100%{transform:rotate(-4deg)}50%{transform:rotate(-2deg)}72%{transform:rotate(-24deg)}90%{transform:rotate(-10deg)}}
      @keyframes thD{0%,100%{transform:rotate(6deg)}50%{transform:rotate(-10deg)}}
      @keyframes shD{0%,100%{transform:rotate(-2deg)}60%{transform:rotate(-6deg)}}
      @keyframes lurch{from{transform:translate(0,0)}to{transform:translate(-1.2px,-1.3px)}}
      @keyframes sway{from{transform:rotate(-1.5deg)}to{transform:rotate(3deg)}}
      @keyframes loll{from{transform:rotate(-6deg)}to{transform:rotate(8deg)}}
      @keyframes reach{from{transform:rotate(-5deg)}to{transform:rotate(5deg)}}
      @keyframes dangle{from{transform:rotate(-12deg)}to{transform:rotate(14deg)}}
"""

REDUCED = """      @media (prefers-reduced-motion:reduce){*{animation:none!important}.zw.z0{opacity:1;transform:translate(780px,0)}.zw.z1{opacity:1;transform:translate(840px,0)}.zw.z2{opacity:1;transform:translate(900px,0)}}
"""


def main(out_path):
    spawns = check_horde()
    town, windows, wires = skyline()
    win = "".join(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"/>' for x, y, w, h in windows)
    rain_far, rain_near = rain_path(120, 8, 14), rain_path(60, 16, 26)
    tick_r, wr = ticker("txR", RAIN_TEXT, "#a9c3d6", "tkR")
    tick_h, wh = ticker("txH", HELL_TEXT, "#ffb08a", "tkH")

    zombies, zkf = [], []
    for i, ((td, xd), ts) in enumerate(zip(KILLS, spawns)):
        m, k = zombie(i, td, xd, ts)
        zombies.append(m)
        zkf.append(k)
    tracers, puffs, casings, skf = shots()
    smoke_markup, smoke_kf, smoke_css, smoke_textures = black_smoke()
    zombie_css = "".join(f".z{i}{{animation-name:z{i}}}" for i in range(len(KILLS)))
    shot_css = "".join(f".t{n}{{animation-name:t{n}}}.p{n}{{animation-name:p{n}}}.c{n}{{animation-name:c{n}}}"
                       for n in range(2 * len(KILLS)))
    css = (STATIC_CSS + f"      @keyframes tkR{{to{{transform:translateX(-{wr}px)}}}}\n"
           f"      @keyframes tkH{{to{{transform:translateX(-{wh}px)}}}}\n"
           "      " + zombie_css + shot_css + smoke_css + "\n      " + "\n      ".join(zkf + skf + smoke_kf) + "\n" + REDUCED)

    full = f'x="-20" y="-20" width="{W + 40}" height="{BAND + 20}"'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title">
  <title id="title">Hey, I'm Victor, aka Reapy. A survivor holds a rainy street against a zombie horde until the sky catches fire, like the hell rounds of my Black Ops III Zombies map Rainy Doom.</title>
  <defs>
    <linearGradient id="skyRain" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#03060b"/><stop offset=".6" stop-color="#0b1520"/><stop offset="1" stop-color="#1c2b39"/>
    </linearGradient>
    <linearGradient id="skyTrans" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#140d0a"/><stop offset=".6" stop-color="#2e2018"/><stop offset="1" stop-color="#4d3626"/>
    </linearGradient>
    <linearGradient id="skyHell" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#140302"/><stop offset=".45" stop-color="#4a0b04"/><stop offset=".8" stop-color="#b3300a"/><stop offset="1" stop-color="#f26b1a"/>
    </linearGradient>
    <linearGradient id="hazeRain" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7d9bb4" stop-opacity="0"/><stop offset="1" stop-color="#7d9bb4" stop-opacity=".22"/>
    </linearGradient>
    <linearGradient id="glowHell" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ff7a24" stop-opacity="0"/><stop offset=".75" stop-color="#ff7a24" stop-opacity=".35"/><stop offset="1" stop-color="#ffb347" stop-opacity=".7"/>
    </linearGradient>
    <linearGradient id="flameBack" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#ffcf6a"/><stop offset=".35" stop-color="#ff7a1e"/><stop offset=".7" stop-color="#d2290a" stop-opacity=".85"/><stop offset="1" stop-color="#7a0e04" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="flameFront" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#fff3c4"/><stop offset=".3" stop-color="#ffc04a"/><stop offset=".65" stop-color="#ff6a1a"/><stop offset="1" stop-color="#c81d0a" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="flameMid" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#ffe7a0"/><stop offset=".35" stop-color="#ffa53a"/><stop offset=".75" stop-color="#ff5a14" stop-opacity=".8"/><stop offset="1" stop-color="#d2290a" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="amberBokeh"><stop offset="0" stop-color="#ffe78a" stop-opacity=".95"/><stop offset=".45" stop-color="#f2b634" stop-opacity=".6"/><stop offset="1" stop-color="#e09020" stop-opacity="0"/></radialGradient>
    {smoke_textures}
    <radialGradient id="eyeRain"><stop offset="0" stop-color="#ffc24d" stop-opacity=".95"/><stop offset=".4" stop-color="#ff8a1a" stop-opacity=".55"/><stop offset="1" stop-color="#ff8a1a" stop-opacity="0"/></radialGradient>
    <radialGradient id="eyeHell"><stop offset="0" stop-color="#d98cff" stop-opacity="1"/><stop offset=".4" stop-color="#9d2bff" stop-opacity=".6"/><stop offset="1" stop-color="#9d2bff" stop-opacity="0"/></radialGradient>
    <radialGradient id="flashGlow"><stop offset="0" stop-color="#fff6d0"/><stop offset=".45" stop-color="#ffb347" stop-opacity=".8"/><stop offset="1" stop-color="#ff7a1e" stop-opacity="0"/></radialGradient>
    <radialGradient id="smoke"><stop offset="0" stop-color="#0b0201" stop-opacity=".9"/><stop offset=".55" stop-color="#160402" stop-opacity=".55"/><stop offset="1" stop-color="#160402" stop-opacity="0"/></radialGradient>
    <linearGradient id="beam" gradientUnits="userSpaceOnUse" x1="{MUZZLE[0]}" y1="0" x2="1000" y2="0">
      <stop offset="0" stop-color="#dbe9ff" stop-opacity=".2"/><stop offset=".55" stop-color="#dbe9ff" stop-opacity=".07"/><stop offset="1" stop-color="#dbe9ff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="titleCold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f3f8fc"/><stop offset="1" stop-color="#9fb6c8"/>
    </linearGradient>
    <linearGradient id="titleHot" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffeaa6"/><stop offset=".5" stop-color="#ff8a2a"/><stop offset="1" stop-color="#cf260b"/>
    </linearGradient>
    <linearGradient id="tail" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffe7b0"/><stop offset=".25" stop-color="#ff8a2a" stop-opacity=".8"/><stop offset="1" stop-color="#ff3a10" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="emA"><stop offset="0" stop-color="#fff2c2"/><stop offset=".35" stop-color="#ffb347"/><stop offset="1" stop-color="#ff6a1f" stop-opacity="0"/></radialGradient>
    <radialGradient id="emB"><stop offset="0" stop-color="#ffd27a"/><stop offset=".35" stop-color="#ff7b22"/><stop offset="1" stop-color="#ff3d12" stop-opacity="0"/></radialGradient>
    <radialGradient id="emC"><stop offset="0" stop-color="#ffb08a"/><stop offset=".35" stop-color="#ff4513"/><stop offset="1" stop-color="#b3150a" stop-opacity="0"/></radialGradient>
    <radialGradient id="impactGlow"><stop offset="0" stop-color="#fff0c0"/><stop offset=".3" stop-color="#ff8a2a" stop-opacity=".9"/><stop offset="1" stop-color="#ff3a10" stop-opacity="0"/></radialGradient>
    <radialGradient id="vignette" cx=".5" cy=".45" r=".75">
      <stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".6"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
    <clipPath id="scene"><rect {full}/></clipPath>
    <clipPath id="tickClip"><rect x="234" y="{BAND}" width="{W - 234}" height="{H - BAND}"/></clipPath>
    <filter id="glowCold" x="-20%" y="-40%" width="140%" height="180%">
      <feGaussianBlur stdDeviation="5" result="b"/>
      <feComponentTransfer in="b" result="s"><feFuncA type="linear" slope=".55"/></feComponentTransfer>
      <feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glowHot" x="-25%" y="-50%" width="150%" height="200%">
      <feGaussianBlur stdDeviation="6" result="b"/>
      <feComponentTransfer in="b" result="s"><feFuncA type="linear" slope=".85"/></feComponentTransfer>
      <feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="16"/></filter>
    <style>{css}    </style>
  </defs>

  <g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="#05070b"/>
  <g class="dof"><g class="quake"><g clip-path="url(#scene)">
    <!-- rain sky, lightning -->
    <rect {full} fill="url(#skyRain)"/>
    <g class="vR" filter="url(#soft)" fill="#16212c">
      <ellipse cx="160" cy="30" rx="220" ry="46"/><ellipse cx="520" cy="10" rx="260" ry="40"/><ellipse cx="860" cy="40" rx="230" ry="50"/>
    </g>
    <rect class="lt" {full} fill="#b9d3ea"/>
    <g class="bo1" fill="none" stroke-linejoin="round"><path d="{bolt_path(842, 884, 214, 3)}" stroke="#bcd6f2" stroke-width="7" opacity=".3"/><path d="{bolt_path(842, 884, 214, 3)}" stroke="#eef6ff" stroke-width="2"/></g>
    <g class="bo2" fill="none" stroke-linejoin="round"><path d="{bolt_path(122, 92, 210, 11)}" stroke="#bcd6f2" stroke-width="7" opacity=".3"/><path d="{bolt_path(122, 92, 210, 11)}" stroke="#eef6ff" stroke-width="2"/></g>
    <rect class="vR" x="-20" y="150" width="{W + 40}" height="{BAND - 150}" fill="url(#hazeRain)"/>

    <!-- hell: the sky burns behind the town, smoke rolls over it -->
    <rect class="vHh" {full} fill="url(#skyHell)"/>
    <g class="vH"><g class="drift">{smoke()}</g></g>
    <g class="vH">
      {fire_wall()}
    </g>
    <g class="vH"><rect class="pulse" x="-20" y="120" width="{W + 40}" height="{BAND - 120}" fill="url(#glowHell)"/></g>
    <rect class="vT" {full} fill="url(#skyTrans)"/>

    <g class="vR"><path class="fallF" d="{rain_far}" stroke="#8fb0c8" stroke-width=".8" stroke-linecap="round" opacity=".38"/></g>

    <!-- meteor and its impact behind the town -->
    <g class="meteor"><path d="M0 0L134 -85" stroke="url(#tail)" stroke-width="5" stroke-linecap="round"/><circle r="9" fill="url(#impactGlow)"/><circle r="3" fill="#fff6dc"/></g>
    <ellipse class="impact" cx="600" cy="238" rx="190" ry="70" fill="url(#impactGlow)"/>

    <!-- town -->
    <g class="town">
    {town}
    </g>
    <path class="wires" d="{wires}" fill="none" stroke-width="1.2"/>
    <g class="vR" fill="#e8b96a" opacity=".55">{win}</g>
    <g class="vH"><g class="heat" fill="#ff5a1f">{win}</g></g>
    <rect x="-20" y="{BASE - 2}" width="{W + 40}" height="{BAND - BASE + 22}" fill="#010203"/>
    <g class="vH">
      {street_fires()}
    </g>
    <polygon class="vR" points="{f(LIGHT[0])},{f(LIGHT[1] - 1.5)} 1020,{f(LIGHT[1] - 40)} 1020,{BASE} {f(LIGHT[0])},{f(LIGHT[1] + 1.5)}" fill="url(#beam)"/>

    <!-- name -->
    <text class="kick mono" x="500" y="72" text-anchor="middle" font-size="20" letter-spacing="6">HEY, I'M VICTOR, AKA</text>
    <g class="tC"><text class="title" x="500" y="192" text-anchor="middle" fill="url(#titleCold)" filter="url(#glowCold)">REAPY</text></g>
    <g class="vH"><g class="heat"><text class="title" x="500" y="192" text-anchor="middle" fill="url(#titleHot)" stroke="#1c0503" stroke-width="6" stroke-linejoin="round" paint-order="stroke" filter="url(#glowHot)">REAPY</text></g></g>

    <!-- the street: a survivor holds it against the horde -->
    {puffs}
    {"".join(zombies)}
    {tracers}
    {shooter()}
    {casings}

    <g class="vR"><path class="fallN" d="{rain_near}" stroke="#cfe2f2" stroke-width="1.3" stroke-linecap="round" opacity=".55"/></g>
    <g class="vH">
      {embers(44)}
    </g>
    <rect {full} fill="url(#vignette)"/>
  </g></g></g>

  <!-- the hell-round transition: black smoke rolls over the town, the world switches behind it -->
  {smoke_markup}

  <!-- ticker band: forecast label + what I do, engineer side in the rain, modder side in hell -->
  <rect x="0" y="{BAND}" width="{W}" height="{H - BAND}" fill="#05070b"/>
  <rect class="lbg" x="0" y="{BAND}" width="232" height="{H - BAND}"/>
  <rect class="bline" x="0" y="{BAND}" width="{W}" height="2"/>
  <rect class="bline" x="232" y="{BAND}" width="2" height="{H - BAND}"/>
  <g class="mono" font-size="{TICK_FONT}">
    <g class="txR"><circle class="blink" cx="22" cy="{BAND + 27}" r="5" fill="#5fa8e0"/><text x="38" y="{BAND + 33}" fill="#cfe2f2">FORECAST: RAIN</text></g>
    <g class="txH"><circle class="blink" cx="22" cy="{BAND + 27}" r="5" fill="#ff4a14"/><text x="38" y="{BAND + 33}" fill="#ffd2b8">FORECAST: HELL</text></g>
    <g clip-path="url(#tickClip)"><g transform="translate(250 0)">
      {tick_r}
      {tick_h}
    </g></g>
  </g>

  <rect class="fl3" width="{W}" height="{BAND}" fill="#ff9a4a"/>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#ffffff" stroke-opacity=".08"/>
</svg>
'''
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    print(f"wrote {out_path}: {len(svg.encode('utf-8'))} bytes; spawns " +
          ", ".join(f"{s % L:.2f}" for s in spawns))


if __name__ == "__main__":
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "header.svg")
    main(os.path.normpath(sys.argv[1] if len(sys.argv) > 1 else default))
