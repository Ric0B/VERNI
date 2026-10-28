#!/usr/bin/env python3
"""Parametric lamp definitions, in the spirit of a Grasshopper canvas.

Every shade is a radial field r(theta, z): a smooth profile R(z) plus a
pattern term. That keeps each shape a single closed surface that prints in
Bambu Studio's spiral vase mode (one continuous wall, no seams, no supports).

    python3 lampgen.py --list
    python3 lampgen.py aare                 # writes out/aare-shade.stl
    python3 lampgen.py all --res fine       # every design, print resolution
    python3 lampgen.py moraene --set amp=6 twist=0.5

Units are millimetres. Only numpy is needed. Mechanical parts (bases,
socket mounts) are in parts.py and need `pip install manifold3d`.

Print settings for every shade: spiral vase on, bottom shell layers 0 (the
shade becomes an open tube that drops into its base), 0.6 mm nozzle with
1.0 mm line width for a strong 1-line wall, or 0.4 mm nozzle with 0.8 mm.
"""
import argparse
import json
import math
import os
import struct
import sys

import numpy as np

TAU = 2 * math.pi
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
RES = {"preview": (240, 2.0), "render": (720, 1.5), "medium": (480, 1.0), "fine": (960, 0.5)}  # (theta samples, z step mm)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def collar(z, p):
    """0 inside the plain collar that sits in the base, 1 where the pattern is free."""
    c = p.get("collar", 0)
    if c <= 0:
        return np.ones_like(z)
    return smoothstep(c, c + p.get("collar_blend", 12), z)


def bell(z, h, r0, r1, power=1.0):
    t = np.clip(z / h, 0, 1)
    return r0 + (r1 - r0) * np.sin(t * math.pi / 2) ** power


# --------------------------------------------------------------------- definitions
# Each definition: dict of default params + a field function f(T, Z, p) -> R.
# T, Z are 2D grids (theta in radians, z in mm).

def f_aare(T, Z, p):
    """Twisted ribs whose depth swells with the belly of the profile."""
    h = p["height"]
    t = Z / h
    prof = p["r_base"] + (p["r_belly"] - p["r_base"]) * np.sin(math.pi * np.clip(t, 0, 1)) ** p["belly_power"]
    phase = p["ribs"] * (T + TAU * p["twist"] * t)  # twist in full turns
    rib = np.sin(phase)
    rib = np.sign(rib) * np.abs(rib) ** p["rib_sharpness"]
    amp = p["rib_depth"] * (0.35 + 0.65 * np.sin(math.pi * np.clip(t, 0, 1)))
    return prof + amp * rib * collar(Z, p)


def f_firn(T, Z, p):
    """Pendant bell, printed upside down (cable end on the plate). Pleats open towards the rim."""
    h = p["height"]
    t = np.clip(Z / h, 0, 1)
    prof = bell(Z, h, p["r_top"], p["r_rim"], p["bell_power"])
    attract = t ** p["pleat_growth"]
    pleat = np.sin(p["pleats"] * T + p["pleat_wave"] * np.sin(3 * T) * t)
    return prof + p["pleat_depth"] * attract * pleat * collar(Z, p)


def f_grat(T, Z, p):
    """Faceted polygon whose rotation zigzags: crisp ridges like a mountain crest."""
    h = p["height"]
    k = p["sides"]
    t = Z / h
    zig = 2 * np.abs((t * p["folds"]) % 1 - 0.5)  # triangle wave 1..0..1
    rot = p["fold_angle"] * (zig - 0.5) * collar(Z, p)
    seg = TAU / k
    a = np.mod(T + rot, seg) - seg / 2
    poly = math.cos(math.pi / k) / np.cos(a)  # unit polygon radius
    prof = p["r_base"] + (p["r_top"] - p["r_base"]) * t + p["bulge"] * np.sin(math.pi * np.clip(t, 0, 1))
    shape = 1 + (poly - 1) * collar(Z, p)
    return prof * shape


def f_foehn_cap(T, Z, p):
    """Mushroom cap, printed upside down as a bowl. Fine radial gills on the outside."""
    h = p["height"]
    t = np.clip(Z / h, 0, 1)
    ease = 0.6 * t + 0.4 * (3 * t ** 2 - 2 * t ** 3)  # keeps the wall under about 50 degrees
    prof = p["r_stem_fit"] + (p["r_cap"] - p["r_stem_fit"]) * ease
    gills = np.sin(p["gills"] * T) * t ** 2
    return prof + p["gill_depth"] * gills * collar(Z, p)


def f_foehn_stem(T, Z, p):
    h = p["height"]
    t = np.clip(Z / h, 0, 1)
    prof = p["r_foot"] + (p["r_neck"] - p["r_foot"]) * t ** 0.8
    flutes = np.sin(p["flutes"] * (T + TAU * p["twist"] * t))
    return prof + p["flute_depth"] * flutes * collar(Z, p)


def f_nebel(T, Z, p):
    """Two counter-rotating waves interfere into a diamond moire, like fog moving."""
    h = p["height"]
    t = Z / h
    prof = p["radius"] + p["waist"] * np.cos(TAU * t)
    w1 = np.sin(p["n1"] * T + TAU * p["t1"] * t)
    w2 = np.sin(p["n2"] * T - TAU * p["t2"] * t)
    return prof + p["amp"] * (w1 + w2) / 2 * collar(Z, p)


def f_glut(T, Z, p):
    """Small egg that closes in towards the top, with a quilted cushion pattern."""
    h = p["height"]
    t = np.clip(Z / h, 0, 1)
    s = p["s0"] + (p["s1"] - p["s0"]) * t
    prof = p["r_max"] * np.sin(math.pi * s) ** 0.8
    quilt = np.abs(np.sin(p["cells"] * T / 2)) * np.abs(np.sin(math.pi * p["rows"] * t))
    return prof + p["quilt"] * (quilt - 0.5) * collar(Z, p) * np.sin(math.pi * t)


def _attractors(p):
    rng = np.random.default_rng(p["seed"])
    n = p["attractors"]
    return np.stack([rng.uniform(0, TAU, n), rng.uniform(0.25, 0.85, n) * p["height"]], axis=1)


def f_moraene(T, Z, p):
    """Grasshopper classic: rib depth driven by distance to attractor points."""
    h = p["height"]
    t = Z / h
    prof = p["r_base"] + (p["r_belly"] - p["r_base"]) * np.sin(math.pi * np.clip(t, 0, 1)) ** 0.9
    infl = np.zeros_like(T)
    for at, az in _attractors(p):
        dth = np.angle(np.exp(1j * (T - at)))  # wrapped angle difference
        d = np.hypot(dth * prof, Z - az)
        infl = np.maximum(infl, np.exp(-(d / p["reach"]) ** 2))
    phase = p["ribs"] * (T + TAU * p["twist"] * t) + p["warp"] * infl
    return prof + (p["rib_min"] + (p["rib_max"] - p["rib_min"]) * infl) * np.sin(phase) * collar(Z, p)


def f_gletscher(T, Z, p):
    """Voronoi crevasses: grooves along the cell borders of random seeds on the surface."""
    h = p["height"]
    t = Z / h
    prof = p["r_base"] + (p["r_top"] - p["r_base"]) * t + p["bulge"] * np.sin(math.pi * np.clip(t, 0, 1))
    rng = np.random.default_rng(p["seed"])
    n = p["cells"]
    st = rng.uniform(0, TAU, n)
    sz = rng.uniform(-0.05, 1.05, n) * h
    circ = p["r_base"]  # scale theta to arc length so cells stay round
    d1 = np.full(T.shape, np.inf)
    d2 = np.full(T.shape, np.inf)
    for a, b in zip(st, sz):
        dth = np.angle(np.exp(1j * (T - a)))
        d = np.hypot(dth * circ, (Z - b) * p["stretch"])
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        d1 = np.where(closer, d, d1)
    edge = d2 - d1
    groove = np.exp(-(edge / p["groove_width"]) ** 2)
    cushion = np.clip(d1 / p["cushion_scale"], 0, 1)
    return prof - (p["groove_depth"] * groove + p["dome"] * cushion) * collar(Z, p)


def f_bise(T, Z, p):
    """Woven lattice: two helical waves multiplied, like knitted wool in a cold wind."""
    h = p["height"]
    t = Z / h
    prof = p["r_mid"] + p["r_swing"] * np.cos(math.pi * (2 * t - 1)) * -1
    weave = np.sin(p["n"] * T + TAU * p["turns"] * t) * np.cos(p["n"] * T - TAU * p["turns"] * t)
    return prof + p["amp"] * weave * collar(Z, p)


COMMON = {"collar": 10, "collar_blend": 14}

DESIGNS = {
    "aare": {"title": "Aare", "kind": "table", "fn": f_aare, "params": {
        "height": 320, "r_base": 88, "r_belly": 104, "belly_power": 1.2, "ribs": 48, "twist": 0.12,
        "rib_depth": 4.5, "rib_sharpness": 0.7, **COMMON}},
    "firn": {"title": "Firn", "kind": "pendant", "fn": f_firn, "params": {
        "height": 200, "r_top": 34, "r_rim": 170, "bell_power": 1.6, "pleats": 96, "pleat_depth": 3.2,
        "pleat_growth": 1.4, "pleat_wave": 2.5, "collar": 12, "collar_blend": 18}},
    "grat": {"title": "Grat", "kind": "table", "fn": f_grat, "params": {
        "height": 300, "r_base": 98, "r_top": 84, "bulge": 14, "sides": 14, "folds": 3, "fold_angle": 0.38, **COMMON}},
    "foehn-cap": {"title": "Föhn cap", "kind": "cordless", "fn": f_foehn_cap, "params": {
        "height": 112, "r_stem_fit": 34, "r_cap": 138, "gills": 120, "gill_depth": 1.2, "collar": 8, "collar_blend": 10}},
    "foehn-stem": {"title": "Föhn stem", "kind": "cordless", "fn": f_foehn_stem, "params": {
        "height": 150, "r_foot": 58, "r_neck": 32, "flutes": 24, "flute_depth": 1.6, "twist": 0.0, **COMMON}},
    "nebel": {"title": "Nebel segment", "kind": "floor", "fn": f_nebel, "params": {
        "height": 300, "radius": 92, "waist": 7, "n1": 18, "n2": 18, "t1": 1.0, "t2": 1.0, "amp": 4.0, **COMMON}},
    "glut": {"title": "Glut", "kind": "cordless", "fn": f_glut, "params": {
        "height": 140, "r_max": 60, "s0": 0.2, "s1": 0.88, "cells": 16, "rows": 5, "quilt": 3.0,
        "collar": 8, "collar_blend": 10}},
    "moraene": {"title": "Moräne", "kind": "table", "fn": f_moraene, "params": {
        "height": 330, "r_base": 92, "r_belly": 112, "ribs": 56, "twist": 0.06, "rib_min": 0.6, "rib_max": 8.0,
        "reach": 85, "warp": 4.0, "attractors": 4, "seed": 7, **COMMON}},
    "gletscher": {"title": "Gletscher", "kind": "table", "fn": f_gletscher, "params": {
        "height": 300, "r_base": 96, "r_top": 82, "bulge": 18, "cells": 70, "stretch": 1.35, "groove_width": 3.6,
        "groove_depth": 2.8, "dome": 2.2, "cushion_scale": 34, "seed": 11, **COMMON}},
    "bise": {"title": "Bise", "kind": "table", "fn": f_bise, "params": {
        "height": 320, "r_mid": 92, "r_swing": 10, "n": 20, "turns": 2.0, "amp": 5.0, **COMMON}},
}


# --------------------------------------------------------------------- mesh

def build(name, overrides=None, res="medium"):
    d = DESIGNS[name]
    p = dict(d["params"], **(overrides or {}))
    nt, dz = RES[res]
    nz = int(math.ceil(p["height"] / dz)) + 1
    th = np.linspace(0, TAU, nt, endpoint=False)
    zz = np.linspace(0, p["height"], nz)
    T, Z = np.meshgrid(th, zz)
    R = d["fn"](T, Z, p)
    return T, Z, R, p


def stats(T, Z, R):
    """Wall slope from vertical: the number that decides if vase mode prints cleanly."""
    dr = np.diff(R, axis=0)
    dz = np.diff(Z, axis=0)
    slope = np.degrees(np.arctan(np.abs(dr) / dz))
    # sideways slope over a single layer matters less, so report the vertical one
    return {"r_min": float(R.min()), "r_max": float(R.max()), "max_overhang_deg": float(slope.max()),
            "p99_overhang_deg": float(np.percentile(slope, 99))}


def to_triangles(T, Z, R, caps=True):
    nz, nt = R.shape
    X = R * np.cos(T)
    Y = R * np.sin(T)
    V = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    idx = np.arange(nz * nt).reshape(nz, nt)
    a = idx[:-1, :]
    b = idx[:-1, np.r_[1:nt, 0]]
    c = idx[1:, :]
    d = idx[1:, np.r_[1:nt, 0]]
    F = np.concatenate([np.stack([a, b, d], -1).reshape(-1, 3), np.stack([a, d, c], -1).reshape(-1, 3)])
    if not caps:  # open tube, for renders
        return V.astype(np.float32), F.astype(np.int64)
    # caps: the slicer needs a closed solid; vase mode with 0 bottom layers removes them again
    cb = len(V)
    ct = cb + 1
    V = np.vstack([V, [0, 0, Z[0, 0]], [0, 0, Z[-1, 0]]])
    ring0, ringN = idx[0], idx[-1]
    nxt = np.r_[1:nt, 0]
    F = np.concatenate([F,
                        np.stack([np.full(nt, cb), ring0[nxt], ring0], -1),
                        np.stack([np.full(nt, ct), ringN, ringN[nxt]], -1)])
    return V.astype(np.float32), F.astype(np.int64)


def check_closed(F):
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    _, counts = np.unique(e, axis=0, return_counts=True)
    return bool((counts == 2).all())


def write_stl(path, V, F):
    tri = V[F]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(F), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"] = n
    rec["v"] = tri
    with open(path, "wb") as f:
        f.write(b"Schichtlicht parametric lamp".ljust(80, b" "))
        f.write(struct.pack("<I", len(F)))
        f.write(rec.tobytes())


def export(name, overrides=None, res="medium", out=OUT, caps=True, tag=""):
    os.makedirs(out, exist_ok=True)
    T, Z, R, p = build(name, overrides, res)
    V, F = to_triangles(T, Z, R, caps)
    path = os.path.join(out, f"{name}{tag}-shade.stl")
    write_stl(path, V, F)
    s = stats(T, Z, R)
    s.update({"file": os.path.relpath(path), "triangles": int(len(F)), "closed": check_closed(F) if res == "preview" else None,
              "params": {k: v for k, v in p.items()}})
    return s


def parse_set(items):
    out = {}
    for it in items or []:
        k, v = it.split("=", 1)
        out[k] = float(v) if "." in v or "e" in v else int(v)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", default="all")
    ap.add_argument("--res", choices=RES, default="medium")
    ap.add_argument("--set", nargs="*", help="override parameters, e.g. ribs=60 twist=0.5")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, d in DESIGNS.items():
            print(f'{k:12} {d["title"]:15} {d["kind"]:9} {json.dumps(d["params"])}')
        return
    names = list(DESIGNS) if a.name == "all" else [a.name]
    for n in names:
        s = export(n, parse_set(a.set), a.res)
        flag = "OK" if s["p99_overhang_deg"] <= 50 else "CHECK"
        print(f'{n:12} {s["triangles"]:>8} tris  r {s["r_min"]:.0f}-{s["r_max"]:.0f} mm  '
              f'overhang p99 {s["p99_overhang_deg"]:.0f}° max {s["max_overhang_deg"]:.0f}°  {flag}  {s["file"]}')


if __name__ == "__main__":
    sys.exit(main())
