#!/usr/bin/env python3
"""Mechanical parts that hold the shades and the electrics.

Print these in PETG (heat) with 4 walls and 30% infill, normal mode (not vase).
Every part reads the collar radius from lampgen.py, so a changed shade still fits.

    pip install manifold3d
    python3 parts.py              # all parts into out/
    python3 parts.py --list

Bought parts the dimensions assume (measure yours and change the constants):
  - E27 thermoplastic socket on an M10x1 threaded tube (table and floor lamps)
  - E27 socket with outer thread and shade ring, ring hole 40.5 mm (pendant, Föhn)
  - M10 hex nut, 17 mm across flats
  - Steel washer or disc as ballast inside the hollow base (table lamps about 400 g)
  - 12 mm aluminium tube (Nebel floor lamp)
"""
import argparse
import math
import os

import manifold3d as mf
import numpy as np

import lampgen

M = mf.Manifold
SEG = 192
OUT = lampgen.OUT

WALL_GAP = 1.4        # groove width for a 1.0 mm vase wall plus clearance
GROOVE_DEPTH = 8.0
M10_HOLE = 10.3
NUT_AF = 17.2
SOCKET_RING_HOLE = 40.5
TUBE_HOLE = 12.3
USB_C = (9.5, 4.0)    # port opening, width x height


def cyl(h, r, r2=None, z=0.0):
    return M.cylinder(h, r, r if r2 is None else r2, SEG).translate([0, 0, z])


def ring(h, r_in, r_out, z=0.0):
    return cyl(h, r_out, z=z) - cyl(h + 0.02, r_in, z=z - 0.01)


def box(x, y, z, at=(0, 0, 0)):
    return M.cube([x, y, z], True).translate(list(at))


def hexagon(af, h, z=0.0):
    r = af / math.sqrt(3)
    return M.cylinder(h, r, r, 6).translate([0, 0, z])


def collar_radius(name, z=0.0):
    T, Z, R, p = lampgen.build(name, res="preview")
    return float(R[0].mean()) if z == 0 else float(R[-1].mean())


def groove(r_wall, z_top, depth=GROOVE_DEPTH):
    return ring(depth + 0.01, r_wall - WALL_GAP / 2, r_wall + WALL_GAP / 2, z_top - depth)


def vents(n, r_pitch, d, h, z=0.0):
    out = None
    for i in range(n):
        a = 2 * math.pi * i / n
        c = cyl(h, d / 2, z=z).translate([r_pitch * math.cos(a), r_pitch * math.sin(a), 0])
        out = c if out is None else out + c
    return out


# --------------------------------------------------------------------- parts

def table_base(name):
    """Base for table lamps: shade groove, M10 socket tube, nut pocket, ballast pocket, cable channel, vents."""
    rc = collar_radius(name)
    h = 22.0
    r_out = rc + 9
    body = cyl(h, r_out - 1.5, r_out, 0)
    body -= groove(rc, h)
    body -= cyl(h + 1, M10_HOLE / 2, z=-0.5)                       # threaded tube goes through
    body -= hexagon(NUT_AF, 9, z=-0.01)                             # nut sits in the bottom
    body -= ring(15, 14, rc - 5, z=-0.01)                           # hollow underside; a steel ring or disc goes in as ballast
    body -= box(r_out + 2, 7.5, 7.0, at=((r_out + 2) / 2, 0, 3.5))  # cable channel to the rim
    body -= vents(12, rc - 14, 6, h + 1, z=-0.5)                    # air in at the bottom, out at the top of the shade
    return body


def pendant_mount():
    """Firn: disc that sits inside the narrow collar, clamped by the E27 socket's shade ring."""
    rc = collar_radius("firn")
    plate = cyl(3.0, rc + 6, z=0) + cyl(6.0, rc - WALL_GAP, z=3.0)  # flange outside, plug inside the collar
    plate -= cyl(12, SOCKET_RING_HOLE / 2, z=-1)
    plate -= vents(10, (rc + SOCKET_RING_HOLE / 2) / 2 + 2, 7, 12, z=-1)
    return plate


def foehn_foot():
    """Föhn: foot plate under the stem with a pocket for the battery board and a USB-C opening."""
    rc = collar_radius("foehn-stem")
    h = 16.0
    body = cyl(h, rc + 7, rc + 6) - groove(rc, h)
    body -= cyl(h - 3, rc - 6, z=3.0)                                # cavity for battery kit, open towards the stem
    w, hh = USB_C
    body -= box(rc + 10, w, hh, at=((rc + 10) / 2, 0, 3 + hh / 2 + 1))  # USB-C cable path to the rim
    return body


def foehn_neck():
    """Föhn: disc at the top of the stem that carries the E27 socket ring; the cap rests on it."""
    r_neck = collar_radius("foehn-stem", z=1)
    rc_cap = collar_radius("foehn-cap")
    plate = cyl(3.0, rc_cap + 4) + cyl(6.0, r_neck - WALL_GAP, z=-6.0)
    plate -= cyl(14, SOCKET_RING_HOLE / 2, z=-7)
    return plate


def nebel_coupler(end=False):
    """Nebel: hub that joins two segments on the aluminium tube. end=True makes the top cap ring."""
    rc = collar_radius("nebel")
    t = 4.0
    disc = ring(t, TUBE_HOLE / 2 + 6, rc + 4)
    hub = cyl(t + 16, TUBE_HOLE / 2 + 6, z=-8) - cyl(t + 18, TUBE_HOLE / 2, z=-9)
    spokes = None
    rim = ring(t, rc - WALL_GAP / 2 - 3, rc + 4)
    for i in range(6):
        s = box(rc, 6, t, at=(rc / 2, 0, t / 2)).rotate([0, 0, 60 * i])
        spokes = s if spokes is None else spokes + s
    part = rim + hub + spokes
    lip_up = ring(6, rc - WALL_GAP / 2 - 3, rc - WALL_GAP / 2, z=t)
    lip_dn = ring(6, rc - WALL_GAP / 2 - 3, rc - WALL_GAP / 2, z=-6)
    part = part + lip_dn + (lip_up if not end else cyl(0.01, 0.01))
    return part


def nebel_foot():
    rc = collar_radius("nebel")
    h = 28.0
    body = cyl(h, rc + 50, rc + 45)
    body -= groove(rc, h)
    body -= cyl(h + 2, TUBE_HOLE / 2, z=-1)
    body -= ring(18, 14, rc + 38, z=-0.01)                           # hollow underside for a 150 x 10 mm steel disc
    body -= box(rc + 60, 8, 9, at=((rc + 60) / 2, 0, 4.5))
    return body


def glut_base():
    rc = collar_radius("glut")
    h = 14.0
    body = cyl(h, rc + 5, rc + 4) - groove(rc, h, depth=6)
    body -= cyl(h - 3, rc - 6, z=3)
    w, hh = USB_C
    body -= box(rc + 8, w, hh, at=((rc + 8) / 2, 0, 3 + hh / 2 + 1))
    return body


PARTS = {
    **{f"base-{n}": (lambda n=n: table_base(n)) for n in ("aare", "grat", "bise", "moraene", "gletscher")},
    "mount-firn": pendant_mount,
    "foot-foehn": foehn_foot,
    "neck-foehn": foehn_neck,
    "coupler-nebel": nebel_coupler,
    "cap-nebel": lambda: nebel_coupler(end=True),
    "foot-nebel": nebel_foot,
    "base-glut": glut_base,
}


def write(name, part, out=OUT):
    os.makedirs(out, exist_ok=True)
    mesh = part.to_mesh()
    V = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    F = np.asarray(mesh.tri_verts).astype(np.int64)
    path = os.path.join(out, f"{name}.stl")
    lampgen.write_stl(path, V, F)
    bb = part.bounding_box()
    return path, len(F), part.volume(), bb


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", default="all")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("\n".join(PARTS))
        return
    for n in (PARTS if a.name == "all" else [a.name]):
        part = PARTS[n]()
        path, tris, vol, bb = write(n, part)
        grams = vol / 1000 * 1.27 * 0.55  # PETG density, rough infill factor
        size = f"{bb[3] - bb[0]:.0f} x {bb[4] - bb[1]:.0f} x {bb[5] - bb[2]:.0f} mm"
        print(f"{n:16} {size:22} about {grams:4.0f} g PETG  genus {part.genus():>3}  {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
