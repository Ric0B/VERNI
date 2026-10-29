#!/usr/bin/env python3
"""Conceptual lamps that push spiral vase mode, in three lines plus a stack system.

  WERK     industrial: fins, threads, gears, extrusion profiles, bellows, flanges
  GRENZE   experiments: deep folds, morphs, leaning axes, phyllotaxis, glitches
  TOTEM    modules on a common plug (Ø140): any module stacks on any other
  DUO      two shades nested inside each other for moiré when lit

Every shape is a stack of closed rings (one per height step). Rings can be any
simple outline, not only "radius around a centre", so T-slot profiles and
I-beams work, and the centre can drift (leaning lamps). The printability check
uses the real surface normal: tilt from vertical, which is what makes or
breaks a single-wall vase print.

    python3 concepts.py --list
    python3 concepts.py all                      # every concept + module as STL in out/concepts/
    python3 concepts.py werk-gewinde --res fine
    python3 concepts.py --stats > concepts.json   # numbers for the catalogue

Print settings are the same as lampgen.py (vase mode, 0 bottom layers, 0.6 mm
nozzle, 1.0 mm line). Modules: print each one separately; they plug together.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

import lampgen as L

TAU = 2 * math.pi
OUT = os.path.join(L.OUT, "concepts")
RES = {"preview": (360, 2.0), "render": (720, 1.5), "medium": (720, 1.0), "fine": (1080, 0.5)}
PLUG_R = 70.0        # TOTEM interface radius (wall centre), Ø140
PLUG_H = 8.0         # collar / spigot height
SPIGOT_R = PLUG_R - 1.4


def ss(a, b, x):
    return L.smoothstep(a, b, x)


def tri(x):
    """Triangle wave 0..1..0 with period 1."""
    return 1 - np.abs(2 * np.mod(x, 1.0) - 1)


def sqwave(x, sharp=4.0):
    """Smoothed square wave in 0..1, period 2*pi in x."""
    return 0.5 * (1 + np.tanh(sharp * np.sin(x)) / math.tanh(sharp))


def superellipse(th, n, a=1.0, b=1.0):
    return (np.abs(np.cos(th) / a) ** n + np.abs(np.sin(th) / b) ** n) ** (-1.0 / n)


def polygon(th, k):
    seg = TAU / k
    u = np.mod(th, seg) - seg / 2
    return math.cos(math.pi / k) / np.cos(u)


def env(z, h, margin=12.0):
    """1 in the middle, easing to 0 at both ends: keeps a plain rim for base and top."""
    return ss(0, margin, z) * ss(0, margin, h - z)


# --------------------------------------------------------------------- polar concepts
# f(T, Z, h) -> R, optionally (R, CX, CY) for a drifting centre.

def werk_kuehlkoerper(T, Z, h):
    """Heat sink: 24 deep square fins. Light leaks bright through the thin fin roots."""
    return 62 + 24 * sqwave(24 * T, 3.5) * env(Z, h, 34)


def werk_turbine(T, Z, h):
    """Turbine: 18 sawtooth blades twisting a quarter turn."""
    t = Z / h
    u = np.mod(18 * (T + TAU * 0.25 * t) / TAU, 1.0)
    blade = np.where(u < 0.8, u / 0.8, (1 - u) / 0.2)
    return 70 + 16 * blade ** 1.5 * env(Z, h, 14)


def werk_wellblech(T, Z, h):
    """Corrugated sheet folded into a square tube."""
    sq = superellipse(T, 8)
    return sq * (78 + 3.2 * np.sin(64 * T) * env(Z, h, 10))


def werk_kuehlturm(T, Z, h):
    """Cooling tower: hyperboloid waist with 72 vertical slats."""
    z0, c = 0.62 * h, 120.0
    prof = 60 * np.sqrt(1 + ((Z - z0) / c) ** 2) + 8
    return prof + 1.4 * np.sin(72 * T) * env(Z, h, 10)


def werk_balg(T, Z, h):
    """Bellows: square accordion like a machine boot. Folds stay under 40°."""
    fold = tri(Z / 26.0)
    return superellipse(T, 6) * (72 + 8 * fold * env(Z, h, 14))


def werk_flansch(T, Z, h):
    """Pipe with three 45° chamfered flanges and bolt heads."""
    r = np.full_like(Z, 60.0)
    bolts = np.zeros_like(Z)
    for zc in (0.22 * h, 0.55 * h, 0.85 * h):
        d = np.abs(Z - zc)
        r = r + np.clip(16 - np.maximum(d - 3, 0), 0, 14)            # 45° up, flat, 45° down
        bolts = bolts + np.exp(-(d / 2.6) ** 2)
    bolt = np.clip(np.cos(8 * T), 0, 1) ** 12 * 3.5
    return r + bolt * bolts


def werk_gewinde(T, Z, h):
    """Four-start thread, 60°-ish flanks: bold helices that read as machined."""
    starts, pitch, depth = 4, 20.0, 8.0
    phase = Z / pitch + starts * T / TAU
    return 70 + depth * tri(phase) * env(Z, h, 12)


def werk_zahnrad(T, Z, h):
    """Helical gear: 36 teeth, an eighth of a turn of helix."""
    u = np.mod(36 * (T + TAU / 8 * Z / h) / TAU, 1.0)
    d = np.abs(u - 0.5)
    tooth = np.clip((0.32 - d) / 0.12, 0, 1)
    return 76 + 9 * tooth * env(Z, h, 18)


def werk_lochblech(T, Z, h):
    """Perforated sheet illusion: a hex grid of dimples on a square tube. Lit, the dimples glow like holes."""
    sq = superellipse(T, 10)
    s = T * 78                       # arc length along the outline (approx.)
    pitch = 13.0
    row = np.floor(Z / (pitch * 0.866))
    u = (s / pitch + 0.5 * np.mod(row, 2)) % 1 - 0.5
    v = (Z / (pitch * 0.866)) % 1 - 0.5
    d2 = (u * pitch) ** 2 + (v * pitch * 0.866) ** 2
    dimple = np.exp(-d2 / 9.0)
    return sq * (78 - 3.0 * dimple * env(Z, h, 14))


def werk_seil(T, Z, h):
    """Rope / cable: three strands laid 1.5 turns."""
    rot = TAU * 1.5 * Z / h
    lobes = np.zeros_like(T)
    for k in range(3):
        a = np.angle(np.exp(1j * (T - rot - k * TAU / 3)))
        lobes = np.maximum(lobes, np.clip(np.cos(a * 1.5), 0, 1))
    return 58 + 16 * lobes ** 0.7 * env(Z, h, 24)


def grenze_stern(T, Z, h):
    """Deep star: 7 folds 42 mm deep, the wall almost doubles back on itself."""
    k = 7
    u = np.mod(k * (T + 0.08 * TAU * Z / h) / TAU, 1.0)
    v = np.abs(2 * u - 1)
    return 52 + 42 * v ** 0.65 * env(Z, h, 60)


def grenze_morph(T, Z, h):
    """Square at the foot, triangle at the top, a quarter turn in between."""
    t = np.clip(Z / h, 0, 1)
    b = ss(0.1, 0.9, t)
    rot = TAU * 0.25 * b
    shape = (1 - b) * polygon(T, 4) / math.cos(math.pi / 4) + b * polygon(T - rot, 3) / math.cos(math.pi / 3)
    return 62 * (0.55 + 0.45 * shape) * (1 + 0.12 * np.sin(math.pi * t))


def grenze_knoten(T, Z, h):
    """Trefoil section turning three quarters of a turn, breathing in and out."""
    t = Z / h
    rot = TAU * 0.6 * t
    breathe = 1 + 0.08 * np.sin(TAU * t)
    return 78 * breathe * (1 + 0.20 * np.cos(3 * (T - rot)) * env(Z, h, 26))


def grenze_schieflage(T, Z, h):
    """Leaning: the axis drifts 35 mm in an S, the elliptical section turns half a turn."""
    t = Z / h
    rot = TAU * 0.5 * t
    a, b = 1.15, 0.87
    r = 70 * superellipse(T - rot, 2, a, b)
    blend = env(Z, h, 20)
    cx = 35 * np.sin(TAU * t) * blend
    cy = 12 * np.sin(math.pi * t) * blend
    r = 70 + (r - 70) * blend
    return r, cx, cy


def grenze_phyllotaxis(T, Z, h):
    """Pine cone: 170 bumps on the golden angle."""
    prof = 74 + 10 * np.sin(math.pi * np.clip(Z / h, 0, 1))
    n = 170
    golden = math.pi * (3 - math.sqrt(5))
    bump = np.zeros_like(T)
    for k in range(n):
        th = (k * golden) % TAU
        zc = 14 + (h - 28) * (k + 0.5) / n
        dth = np.angle(np.exp(1j * (T - th)))
        d2 = (dth * 80) ** 2 + ((Z - zc) * 1.1) ** 2
        bump = np.maximum(bump, np.exp(-d2 / (2 * 8.5 ** 2)))
    return prof + 6.0 * bump * env(Z, h, 10)


def grenze_fraktal(T, Z, h):
    """Folds within folds within folds: 6, 36 and 144 pleats."""
    e = env(Z, h, 26)
    t = Z / h
    f1 = np.abs(np.sin(3 * (T + 0.05 * TAU * t)))
    f2 = np.abs(np.sin(18 * T))
    f3 = np.abs(np.sin(72 * T))
    return 64 + e * (14 * f1 + 3.2 * f2 * f1 + 0.9 * f3)


def grenze_glitch(T, Z, h):
    """Digital glitch: 24 mm bands of a pentagon, each band rotated and scaled at random."""
    band = 30.0
    rnd = L.mulberry32(5)
    nb = int(h // band) + 2
    rots = [(rnd() - 0.5) * math.radians(18) for _ in range(nb)]
    scales = [0.94 + 0.12 * rnd() for _ in range(nb)]
    idx = np.floor(Z / band).astype(int)
    frac = (Z / band) - idx
    w = ss(0.3, 1.0, frac)             # 9 mm flat, 21 mm transition
    rot = np.take(rots, idx) * (1 - w) + np.take(rots, np.minimum(idx + 1, nb - 1)) * w
    sc = np.take(scales, idx) * (1 - w) + np.take(scales, np.minimum(idx + 1, nb - 1)) * w
    e = env(Z, h, 14)
    shape = 1 + (polygon(T - rot * e, 5) / math.cos(math.pi / 5) - 1) * e
    return 74 * shape * (1 + (sc - 1) * e)


def grenze_kaskade(T, Z, h):
    """Pagoda: hexagonal terraces stepping out 9 mm each, every step a 45° chamfer."""
    step, rise = 40.0, 9.0
    k = np.floor(Z / step)
    within = Z - k * step
    r = 54 + rise * k + np.clip(within, 0, rise)
    return r * (0.9 + 0.1 * polygon(T, 6) / math.cos(math.pi / 6))


def grenze_topo(T, Z, h):
    """Terrain: a periodic noise field, so every layer line becomes a contour line."""
    rnd = L.mulberry32(21)
    r = np.full_like(T, 76.0)
    amp = 7.0
    for octave in range(5):
        m = 2 ** (octave + 1)
        for _ in range(2):
            ph, kz = rnd() * TAU, (rnd() - 0.5) * 0.06 * (octave + 1)
            r = r + amp * np.sin(m * T + kz * Z + ph) * (0.5 + 0.5 * np.sin(Z / (30 + 20 * rnd()) + ph))
        amp *= 0.5
    return 76 + (r - 76) * env(Z, h, 14)


def duo_aussen(T, Z, h):
    """Outer shell of the moiré pair: 64 fine straight ribs."""
    return 92 + 1.6 * np.sin(64 * T) * env(Z, h, 10)


def duo_innen(T, Z, h):
    """Inner shell: 68 ribs with a slight twist. Through the outer shell they beat into moiré bands."""
    return 76 + 1.6 * np.sin(68 * (T + 0.03 * TAU * Z / h)) * env(Z, h, 10)


def duo_kern(T, Z, h):
    """Smooth frosted core that sits inside the heat sink (WERK Kühlkörper) as a glowing lining."""
    return 52 + 0 * T


# --------------------------------------------------------------------- polygon concepts (non star-shaped)

def resample(poly, n):
    """Closed polyline -> n points at equal arc length, starting nearest angle 0, counter-clockwise."""
    p = np.asarray(poly, float)
    if _area(p) < 0:
        p = p[::-1]
    start = np.argmin(np.abs(np.arctan2(p[:, 1], p[:, 0])) + (p[:, 0] < 0) * 10)
    p = np.roll(p, -start, axis=0)
    closed = np.vstack([p, p[:1]])
    seg = np.hypot(*np.diff(closed, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n, endpoint=False)
    x = np.interp(t, s, closed[:, 0])
    y = np.interp(t, s, closed[:, 1])
    return np.stack([x, y], 1)


def _area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def tslot_outline(size=150.0, slot=30.0, depth=36.0, under=56.0, lip=9.0, corner=10.0):
    """Outline of a 40-series aluminium T-slot profile, scaled up. One slot on each side."""
    s = size / 2
    pts = []
    for k in range(4):
        rot = k * math.pi / 2
        c, si = math.cos(rot), math.sin(rot)
        side = [  # walk along the +x side from bottom corner to top corner (local coords)
            (s, -s + corner), (s, -slot / 2), (s - lip, -slot / 2), (s - lip, -under / 2),
            (s - depth, -under / 2 + 8), (s - depth, under / 2 - 8), (s - lip, under / 2),
            (s - lip, slot / 2), (s, slot / 2), (s, s - corner), (s - corner * 0.3, s - corner * 0.3)]
        pts += [(x * c - y * si, x * si + y * c) for x, y in side]
    return pts


def ibeam_outline(w=150.0, hgt=150.0, web=26.0, flange=20.0, fillet=6.0):
    a, b, t, f = w / 2, hgt / 2, web / 2, flange
    return [(a, -b), (a, -b + f), (t + fillet, -b + f), (t, -b + f + fillet), (t, b - f - fillet), (t + fillet, b - f),
            (a, b - f), (a, b), (-a, b), (-a, b - f), (-t - fillet, b - f), (-t, b - f - fillet),
            (-t, -b + f + fillet), (-t - fillet, -b + f), (-a, -b + f), (-a, -b)]


def contour_concept(outline, twist=0.0, taper=0.0, flare=0.0):
    def make(nt, Zs, h):
        base = resample(outline(), nt)
        X = np.empty((len(Zs), nt))
        Y = np.empty((len(Zs), nt))
        for j, z in enumerate(Zs):
            t = z / h
            a = TAU * twist * t
            sc = 1 - taper * t + flare * math.sin(math.pi * t)
            c, s = math.cos(a), math.sin(a)
            X[j] = sc * (base[:, 0] * c - base[:, 1] * s)
            Y[j] = sc * (base[:, 0] * s + base[:, 1] * c)
        return X, Y
    return make


# --------------------------------------------------------------------- TOTEM modules (Ø140 plug)

def module(pattern):
    """Wrap a pattern so the foot is the Ø140 collar and the top is the spigot that slides into the next module."""
    def f(T, Z, h):
        body = pattern(T, Z, h)
        foot = ss(PLUG_H, PLUG_H + 22, Z)
        top = ss(h - PLUG_H - 22, h - PLUG_H, Z)
        r = PLUG_R + (body - PLUG_R) * foot
        return r * (1 - top) + SPIGOT_R * top
    return f


def mod_glatt(T, Z, h):
    return 72 + 0 * T


def mod_rippe(T, Z, h):
    return 72 + 4 * np.sin(60 * T)


def mod_twist(sign):
    def f(T, Z, h):
        return 72 + 4.5 * np.sin(48 * (T + sign * TAU * 0.12 * Z / h))
    return f


def mod_balg(T, Z, h):
    return 72 + 8 * tri((Z - PLUG_H) / 24.0)


def mod_polster(T, Z, h):
    q = np.sin(8 * T) ** 2 * np.sin(math.pi * (Z - PLUG_H) / 24.0) ** 2
    return 72 + 6 * q


def mod_spalt(T, Z, h):
    p = {"r_base": 74, "r_top": 74, "bulge": 0, "cells": 26, "stretch": 1.2, "groove_width": 4.0,
         "groove_depth": 2.6, "dome": 1.6, "cushion_scale": 26, "seed": 3, "height": h, "collar": 0, "collar_blend": 1}
    return L.f_gletscher(T, Z, p)


def mod_kuehl(T, Z, h):
    return 66 + 18 * sqwave(20 * T, 3.0)


def mod_gewinde(T, Z, h):
    return 70 + 7 * tri(Z / 18.0 + 3 * T / TAU)


def mod_kuppel(T, Z, h):
    """Closing dome, the top of every stack. Printed upright; the 40 mm opening at the top lets heat out."""
    t = np.clip((Z - PLUG_H) / (h - PLUG_H), 0, 1)
    r = PLUG_R * np.cos(t * math.radians(72)) ** 0.9
    return np.where(Z < PLUG_H, PLUG_R, np.maximum(r, 20))


# --------------------------------------------------------------------- registry

C = {}


def add(name, line, title, idea, limit, h, fn, kind="polar", price=None):
    C[name] = dict(name=name, line=line, title=title, idea=idea, limit=limit, height=h, fn=fn, kind=kind, price=price)


add("werk-kuehlkoerper", "WERK", "Kühlkörper", "24 deep square fins like an aluminium heat sink.", "Fin depth 24 mm on a 1 mm wall; light leaks bright at the fin roots.", 300, werk_kuehlkoerper, price=249)
add("werk-turbine", "WERK", "Turbine", "18 sawtooth blades twisting a quarter turn.", "Asymmetric blade flanks: one face catches light, the other shades.", 300, werk_turbine, price=269)
add("werk-wellblech", "WERK", "Wellblech", "Corrugated sheet folded into a square tube.", "64 corrugations on a square section; corners stretch the wave.", 320, werk_wellblech, price=229)
add("werk-kuehlturm", "WERK", "Kühlturm", "Hyperboloid cooling tower with 72 slats.", "Waist narrower than foot and top; light pools at the waist.", 320, werk_kuehlturm, price=239)
add("werk-balg", "WERK", "Balg", "Square bellows like a machine boot.", "Horizontal folds at 40°: close to the vase-mode limit.", 300, werk_balg, price=249)
add("werk-flansch", "WERK", "Flansch", "Pipe with three chamfered flanges and bolt heads.", "Flanges stick out 14 mm, built only from 45° chamfers.", 320, werk_flansch, price=259)
add("werk-gewinde", "WERK", "Gewinde", "Four-start thread, cut deep.", "Thread flanks at 39°, helices read as machined.", 300, werk_gewinde, price=249)
add("werk-zahnrad", "WERK", "Zahnrad", "Helical gear with 36 teeth.", "Sharp tooth flanks in a single wall.", 280, werk_zahnrad, price=239)
add("werk-lochblech", "WERK", "Lochblech", "Perforated sheet without holes: a hex grid of dimples.", "Vase mode cannot make holes; thin dimples glow like them.", 320, werk_lochblech, price=259)
add("werk-seil", "WERK", "Seil", "Three strands laid like steel cable.", "Strand lobes 16 mm deep, 1.5 turns.", 320, werk_seil, price=249)
add("werk-profil", "WERK", "Profil", "A T-slot aluminium extrusion profile, scaled to 150 mm.", "Not star-shaped: the outline folds back into undercut T-slots.", 330, contour_concept(tslot_outline), kind="contour", price=289)
add("werk-profil-twist", "WERK", "Profil Twist", "The T-slot profile twisted 45°.", "Undercut slots that also spiral.", 330, contour_concept(tslot_outline, twist=0.125), kind="contour", price=319)
add("werk-traeger", "WERK", "Träger", "An I-beam, standing up, light coming out of its web.", "Two flanges and a web from one wall; the web gap is 26 mm.", 330, contour_concept(ibeam_outline), kind="contour", price=279)
add("grenze-stern", "GRENZE", "Stern", "Seven folds 42 mm deep.", "Fold depth close to the radius: the wall nearly doubles back.", 300, grenze_stern, price=289)
add("grenze-morph", "GRENZE", "Morph", "Square foot, triangular top, a quarter turn between.", "Section changes topology class while twisting.", 320, grenze_morph, price=279)
add("grenze-knoten", "GRENZE", "Knoten", "Trefoil section turning three quarters, breathing.", "Twist plus lobes: tilt near the limit on the lobe flanks.", 320, grenze_knoten, price=279)
add("grenze-schieflage", "GRENZE", "Schieflage", "Leaning: the axis drifts 35 mm in an S.", "The whole lamp leans; tilt comes from the drift, not the pattern.", 330, grenze_schieflage, price=299)
add("grenze-phyllotaxis", "GRENZE", "Zapfen", "170 bumps on the golden angle, like a pine cone.", "Hundreds of local overhangs, each kept under 40°.", 320, grenze_phyllotaxis, price=319)
add("grenze-fraktal", "GRENZE", "Fraktal", "Folds within folds: 6, 36 and 144 pleats.", "Three scales of detail, the finest at 2.5 mm pitch.", 320, grenze_fraktal, price=299)
add("grenze-glitch", "GRENZE", "Glitch", "Pentagon bands rotated and scaled at random.", "Hard digital steps made printable with 21 mm ramps.", 312, grenze_glitch, price=279)
add("grenze-kaskade", "GRENZE", "Kaskade", "Hexagonal terraces stepping outward like a pagoda.", "Every step is a pure 45° chamfer.", 320, grenze_kaskade, price=269)
add("grenze-topo", "GRENZE", "Topo", "A noise landscape: every layer line becomes a contour line.", "Layer lines become the drawing.", 320, grenze_topo, price=289)
add("duo-aussen", "DUO", "Interferenz (aussen)", "Outer shell, 64 straight ribs.", "Two nested prints, 16 mm apart.", 320, duo_aussen)
add("duo-innen", "DUO", "Interferenz (innen)", "Inner shell, 68 twisted ribs.", "Moiré appears only when lit.", 320, duo_innen)
add("duo-kern", "DUO", "Kern", "Smooth frosted core for inside the heat sink.", "A glowing lining behind deep fins.", 300, duo_kern)

MODULES = {
    "m-glatt": ("Glatt", 80, mod_glatt), "m-rippe": ("Rippe", 120, mod_rippe), "m-twist-r": ("Twist rechts", 120, mod_twist(1)),
    "m-twist-l": ("Twist links", 120, mod_twist(-1)), "m-balg": ("Balg", 120, mod_balg), "m-polster": ("Polster", 80, mod_polster),
    "m-spalt": ("Spalt", 120, mod_spalt), "m-kuehl": ("Kühlrippe", 120, mod_kuehl), "m-gewinde": ("Gewinde", 120, mod_gewinde),
}
for k, (title, h, fn) in MODULES.items():
    add(k, "TOTEM", title, "TOTEM module, Ø140 plug.", "Collar below, spigot above: stacks on any other module.", h, module(fn))
add("m-kuppel", "TOTEM", "Kuppel", "Closing dome, the top of every stack.", "Closes to a 40 mm vent.", 90, mod_kuppel)

STACKS = {
    "totem-industrie": dict(title="Totem Industrie", parts=["m-gewinde", "m-kuehl", "m-balg", "m-kuppel"], tones=["stein", "nacht", "stein", "nacht"]),
    "totem-licht": dict(title="Totem Licht", parts=["m-glatt", "m-rippe", "m-glatt", "m-rippe", "m-glatt", "m-kuppel"], tones=["frost"] * 6),
    "schichtwechsel": dict(title="Schichtwechsel", parts=["m-twist-r", "m-twist-l", "m-twist-r", "m-twist-l", "m-kuppel"], tones=["frost", "sand", "frost", "sand", "frost"]),
    "kontrast": dict(title="Kontrast", parts=["m-polster", "m-glatt", "m-polster", "m-glatt", "m-polster", "m-kuppel"], tones=["nacht", "frost", "nacht", "frost", "nacht", "nacht"]),
    "eisberg": dict(title="Eisberg", parts=["m-spalt", "m-spalt", "m-glatt", "m-kuppel"], tones=["frost", "frost", "frost", "frost"]),
    "maschine": dict(title="Maschine", parts=["m-kuehl", "m-gewinde", "m-kuehl", "m-gewinde", "m-kuehl", "m-kuppel"], tones=["stein"] * 6),
}
NESTS = {
    "duo-interferenz": dict(title="Interferenz", outer="duo-aussen", inner="duo-innen", line="DUO",
                            idea="Two ribbed shells nested 16 mm apart. Switched off they look plain; lit, moiré bands appear and move as you walk past.", price=390),
    "duo-kuehlkern": dict(title="Kühlkern", outer="werk-kuehlkoerper", inner="duo-kern", line="DUO",
                          idea="The heat sink with a frosted core inside: the fins become dark blades against a glowing column.", price=329),
}


# --------------------------------------------------------------------- build, mesh, check

def build(name, res="medium"):
    c = C[name]
    nt, dz = RES[res]
    h = c["height"]
    nz = int(math.ceil(h / dz)) + 1
    Zs = np.linspace(0, h, nz)
    if c["kind"] == "contour":
        X, Y = c["fn"](nt, Zs, h)
    else:
        th = np.linspace(0, TAU, nt, endpoint=False)
        T, Z = np.meshgrid(th, Zs)
        out = c["fn"](T, Z, h)
        if isinstance(out, tuple):
            R, CX, CY = out
        else:
            R, CX, CY = out, 0, 0
        X = CX + R * np.cos(T)
        Y = CY + R * np.sin(T)
    Z = np.repeat(Zs[:, None], X.shape[1], axis=1)
    return X, Y, Z


def check(X, Y, Z):
    """Tilt of the wall from vertical, from real surface normals. Vase mode wants < 50° for 99% of the wall."""
    P = np.stack([X, Y, Z], -1)
    dth = np.roll(P, -1, axis=1) - P
    dz = np.diff(P, axis=0)
    n = np.cross(dth[:-1], dz)
    nh = np.hypot(n[..., 0], n[..., 1])
    tilt = np.degrees(np.arctan2(np.abs(n[..., 2]), nh))
    # closest approach of the wall to itself across the outline (narrow folds fuse below ~2 mm)
    ring = P[len(P) // 2, :, :2]
    k = max(1, len(ring) // 90)
    sample = ring[::k]
    d = np.hypot(sample[:, None, 0] - sample[None, :, 0], sample[:, None, 1] - sample[None, :, 1])
    idx = np.arange(len(sample))
    near = np.abs(idx[:, None] - idx[None, :])
    near = np.minimum(near, len(sample) - near)
    d[near < 6] = np.inf
    seg = np.hypot(*np.diff(np.vstack([ring, ring[:1]]), axis=0).T)
    ring_len = seg.sum()
    r_eq = np.hypot(X, Y).max()
    return {"tilt_p99": float(np.percentile(tilt, 99)), "tilt_max": float(tilt.max()),
            "min_gap_mm": float(d.min()), "outline_mm": float(ring_len),
            "width_mm": float(2 * max(np.abs(X).max(), np.abs(Y).max())), "r_max": float(r_eq)}


def mesh(X, Y, Z, caps=True):
    nz, nt = X.shape
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(nz * nt).reshape(nz, nt)
    nxt = np.r_[1:nt, 0]
    a, b, c, d = idx[:-1, :], idx[:-1, nxt], idx[1:, :], idx[1:, nxt]
    F = np.concatenate([np.stack([a, b, d], -1).reshape(-1, 3), np.stack([a, d, c], -1).reshape(-1, 3)])
    if caps:
        cb, ct = len(V), len(V) + 1
        V = np.vstack([V, [X[0].mean(), Y[0].mean(), Z[0, 0]], [X[-1].mean(), Y[-1].mean(), Z[-1, 0]]])
        F = np.concatenate([F, np.stack([np.full(nt, cb), idx[0, nxt], idx[0]], -1), np.stack([np.full(nt, ct), idx[-1], idx[-1, nxt]], -1)])
    return V.astype(np.float32), F.astype(np.int64)


def export(name, res="medium", out=OUT, caps=True):
    os.makedirs(out, exist_ok=True)
    X, Y, Z = build(name, res)
    s = check(X, Y, Z)
    V, F = mesh(X, Y, Z, caps)
    path = os.path.join(out, f"{name}-shade.stl")
    L.write_stl(path, V, F)
    h = C[name]["height"]
    s.update({"file": path, "height": h,
              "grams": s["outline_mm"] * h / 1000 * 1.24,                 # 1.0 mm wall, PLA
              "hours": s["outline_mm"] * (h / 0.24) / 40 / 3600})
    return s


def stats_all(res="medium"):
    out = {}
    for n, c in C.items():
        X, Y, Z = build(n, res)
        s = check(X, Y, Z)
        h = c["height"]
        out[n] = {k: c[k] for k in ("line", "title", "idea", "limit", "height", "price")}
        out[n].update({k: round(v, 1) for k, v in s.items()})
        out[n]["grams"] = round(s["outline_mm"] * h / 1000 * 1.24)
        out[n]["hours"] = round(s["outline_mm"] * (h / 0.24) / 40 / 3600, 1)
        out[n]["printable"] = s["tilt_p99"] <= 50 and s["min_gap_mm"] >= 2.0
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", default="all")
    ap.add_argument("--res", choices=RES, default="medium")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.list:
        for n, c in C.items():
            print(f'{n:22} {c["line"]:7} {c["title"]:22} {c["idea"]}')
        print("\nstacks:", ", ".join(STACKS), "\nnested:", ", ".join(NESTS))
        return
    if a.stats:
        json.dump({"concepts": stats_all(), "stacks": STACKS, "nests": NESTS}, sys.stdout, ensure_ascii=False, indent=1)
        return
    for n in (C if a.name == "all" else [a.name]):
        s = export(n, a.res)
        ok = "OK" if s["tilt_p99"] <= 50 and s["min_gap_mm"] >= 2 else "CHECK"
        print(f'{n:22} tilt p99 {s["tilt_p99"]:4.0f}°  gap {s["min_gap_mm"]:5.1f} mm  Ø {s["width_mm"]:4.0f}  '
              f'{s["grams"]:4.0f} g  {s["hours"]:4.1f} h  {ok}')


if __name__ == "__main__":
    main()
