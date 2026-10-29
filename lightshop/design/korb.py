#!/usr/bin/env python3
"""KORB: a woven pendant in the spirit of rattan, printed as direct non-planar G-code.

Each lap of a continuous spiral zig-zags up and down at about 60 degrees. The
wave count per lap is a half-integer, so each lap is in anti-phase with the one
below: tips meet tips and the strands read as crossing diagonals, like a rattan
lattice. A few solid hoops (foot, belly rings, top collar) carry the shape the
way the horizontal bands do in a woven shade.

Every point's radius follows its own height on the profile, so tips still meet
where the shape leans in or out; the profile keeps the wall within 52 degrees.

    python3 korb.py                       # full pendant, about Ø280 x 230 mm  -> out/korb/korb.gcode
    python3 korb.py --scale 0.5 --name korb-test     # half size test, about 25 min
    python3 korb.py --cell 9                          # denser lattice (cell width in mm at the belly)

Hang it with `mount-korb` (parts: python3 korb.py --mount), an E27 socket with
outer thread and shade ring, LED only.
"""
import argparse
import math
import os

import weave  # start/end G-code, printer table

TAU = 2 * math.pi
HERE = os.path.dirname(os.path.abspath(__file__))
FIL_AREA = math.pi * (1.75 / 2) ** 2


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Shape:
    """Onion-bulb profile (mm, scaled): foot r0, belly rb at zb, closing to the collar rc at the top."""

    def __init__(self, s):
        self.s = s
        self.H = 230 * s
        self.r0, self.rb, self.rc = 118 * s, 140 * s, 30 * s
        self.zb = 80 * s
        self.zc0 = self.H - 12 * s          # collar starts here

    def r(self, z):
        if z <= self.zb:
            return self.r0 + (self.rb - self.r0) * math.sin(math.pi / 2 * max(0.0, z) / self.zb)
        if z <= self.zc0:
            return self.rb - (self.rb - self.rc) * smooth((z - self.zb) / (self.zc0 - self.zb))
        return self.rc

    def max_tilt(self):
        zs = [i * 0.5 for i in range(int(self.H / 0.5))]
        return max(math.degrees(math.atan(abs(self.r(z + 0.5) - self.r(z)) / 0.5)) for z in zs)


def bands(shape, a):
    """Solid hoops as (z_start, z_end). Foot, two belly rings, collar."""
    s = shape.s
    out = [(0.0, a.foot * s)]
    for z in a.rings:
        out.append((z * s, z * s + a.ring_h * s))
    out.append((shape.zc0, shape.H))
    return sorted(out)


def zigzag(phi, flat):
    """Triangle wave in -1..1 with short flat tips (the fused contacts)."""
    u = (phi / TAU) % 1.0
    tri = 1 - 4 * abs(u - 0.5)               # -1 at u=0, +1 at u=0.5
    return max(-1.0, min(1.0, tri * (1 + flat)))


def toolpath(a):
    sh = Shape(a.scale)
    bl = bands(sh, a)
    step = 0.4
    zc, th, phi = a.first, 0.0, 0.0
    i_band = 0                               # index of the band we are in or heading to
    state, t0 = "band", 0.0
    amp_t = 0.0
    n_waves = 0.5
    pitch_net = 2 * a.amp * a.scale + a.strand_h
    while zc < sh.H:
        b0, b1 = bl[i_band] if i_band < len(bl) else (sh.H, sh.H)
        # state changes
        if state == "band" and zc >= b1:
            i_band += 1
            if i_band >= len(bl):
                break
            nb0 = bl[i_band][0]
            # wave count for this net section: cells of a.cell mm at the section's widest radius
            r_ref = max(sh.r(z) for z in (zc, (zc + nb0) / 2, nb0))
            n_waves = math.floor(TAU * r_ref / (a.cell * a.scale)) + 0.5
            state, t0 = "in", th
        elif state in ("in", "net") and zc + amp_t * a.amp * a.scale + a.strand_h >= bl[i_band][0]:
            state, t0 = "out", th
        k = min(1.0, (th - t0) / TAU)
        if state == "in":
            amp_t, pitch, h = k, a.layer + (pitch_net - a.layer) * k, a.strand_h
            if k >= 1:
                state = "net"
        elif state == "net":
            amp_t, pitch, h = 1.0, pitch_net, a.strand_h
        elif state == "out":
            amp_t, pitch = 1 - k, pitch_net + (a.layer - pitch_net) * k
            h = a.strand_h if k < 1 else a.layer
            if k >= 1:
                state = "band"
        else:
            amp_t, pitch, h = 0.0, a.layer, a.layer
        r_here = sh.r(zc)
        dth = step / max(r_here, 5)
        th += dth
        phi += n_waves * dth
        zc += pitch * dth / TAU
        z = zc + amp_t * a.amp * a.scale * zigzag(phi, a.flat)
        r = sh.r(z)
        yield r * math.cos(th), r * math.sin(th), z, h, state


def write(a):
    pr = weave.PRINTERS[a.printer]
    cx, cy = pr["cx"], pr["cy"]
    out_dir = os.path.join(HERE, "out", "korb")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{a.name}.gcode")
    sh = Shape(a.scale)
    custom = os.path.join(HERE, f"start_{a.printer}.gcode")
    L = [f"; Schichtlicht KORB woven pendant '{a.name}' (korb.py)",
         f"; scale {a.scale}, H {sh.H:.0f} mm, foot Ø{2 * sh.r0:.0f}, belly Ø{2 * sh.rb:.0f}, collar Ø{2 * sh.rc:.0f}",
         f"; cell {a.cell} mm, amp {a.amp * a.scale:.2f} mm, strand {a.width} x {a.strand_h} mm, layer {a.layer}, {a.temp} C, PLA 1.75"]
    r_foot = sh.r(0) + a.brim * a.width + 2
    if a.printer == "h2s" and not a.generic_start:
        import bambu_gcode
        bambu_start, bambu_end = bambu_gcode.h2s(bed_min=(cx - r_foot, cy - r_foot), bed_size=(2 * r_foot, 2 * r_foot), max_z=sh.H)
        L.append("; ---- Bambu Lab H2S machine start G-code (official template, filled by bambu_gcode.py)")
        L.append(bambu_start)
        L.append("G90\nM83\nG92 E0\nG91\nG1 Z2 F600\nG90")
    else:
        bambu_end = None
        L.append(open(custom, encoding="utf-8").read() if os.path.exists(custom) else
                 weave.START.format(bed=a.bed, nozzle=a.temp, px0=cx - 60, px1=cx + 60, py=12.0, py2=12.6, z=a.first))
    e_rate = a.width / FIL_AREA
    length = fil = 0.0
    # brim around the foot
    L.append("; brim")
    for k in range(a.brim, 0, -1):
        rr = sh.r(0) + k * a.width * 0.9
        pts = [(rr * math.cos(TAU * j / 720), rr * math.sin(TAU * j / 720)) for j in range(721)]
        L.append(f"G1 X{cx + pts[0][0]:.3f} Y{cy + pts[0][1]:.3f} F6000")
        L.append(f"G1 Z{a.first:.3f} F600")
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            d = math.hypot(x2 - x1, y2 - y1)
            e = d * a.first * e_rate * 1.05
            fil += e
            length += d
            L.append(f"G1 X{cx + x2:.3f} Y{cy + y2:.3f} E{e:.5f} F{a.speed_first * 60:.0f}")
    L.append("; woven body")
    prev = None
    fan = False
    rmax = zmax = 0.0
    for x, y, z, h, state in toolpath(a):
        rmax = max(rmax, math.hypot(x, y))
        if prev is None:
            L.append(f"G1 X{cx + x:.3f} Y{cy + y:.3f} F6000")
            L.append(f"G1 Z{z:.3f} F600")
            prev = (x, y, z)
            continue
        d = math.dist(prev, (x, y, z))
        first = z < a.first + 2 * a.layer
        hh = a.first if first else h
        e = d * hh * e_rate * a.flow
        fil += e
        length += d
        if not fan and z > 1.2:
            L.append(f"M106 P1 S{int(2.55 * a.fan)}")
            fan = True
        v = a.speed_first if first else (a.speed if state in ("in", "net", "out") else a.speed_band)
        L.append(f"G1 X{cx + x:.3f} Y{cy + y:.3f} Z{z:.3f} E{e:.5f} F{v * 60:.0f}")
        prev = (x, y, z)
        zmax = max(zmax, z)
    if bambu_end:
        L.append("; ---- end\n; ---- Bambu Lab H2S machine end G-code (official template)")
        L.append(bambu_end)
    else:
        L.append(weave.END.format(zup=zmax + 15, cx=cx, yaway=pr["size"][1] - 10))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    fits = 2 * rmax + 2 * a.brim * a.width + 10 < min(pr["size"][:2]) and zmax + 15 < pr["size"][2]
    return path, dict(height=zmax, diameter=2 * rmax, path_m=length / 1000, grams=fil * FIL_AREA / 1000 * 1.24,
                      hours=length / a.speed / 3600 * 1.1, fits=fits, tilt=sh.max_tilt())


def tube_stl(a, path):
    """The toolpath as round strands (for renders): 6-sided tubes along the path."""
    import numpy as np
    import lampgen
    P = np.array([(x, y, z) for x, y, z, h, s in toolpath(a)])[::2]
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    up = np.tile([0, 0, 1.0], (len(P), 1))
    N = np.cross(T, up)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    B = np.cross(T, N)
    k = 6
    ang = np.linspace(0, TAU, k, endpoint=False)
    rad = a.width / 2 * 1.15
    V = (P[:, None, :] + rad * (np.cos(ang)[None, :, None] * N[:, None, :] + np.sin(ang)[None, :, None] * B[:, None, :])).reshape(-1, 3)
    idx = np.arange(len(P) * k).reshape(len(P), k)
    nx = np.r_[1:k, 0]
    a0, b0, c0, d0 = idx[:-1], idx[:-1, nx], idx[1:], idx[1:, nx]
    F = np.concatenate([np.stack([a0, b0, d0], -1).reshape(-1, 3), np.stack([a0, d0, c0], -1).reshape(-1, 3)])
    lampgen.write_stl(path, V.astype(np.float32), F)
    return len(F)


def mount(a):
    """PETG disc that pushes up into the top collar from inside and is clamped by the socket's shade ring."""
    import manifold3d as mf
    import lampgen
    import numpy as np
    sh = Shape(a.scale)
    M = mf.Manifold
    rc = sh.rc
    flange = M.cylinder(3.0, rc + 6, rc + 6, 160)
    spigot = M.cylinder(8.0, rc - a.width / 2 - 0.45, rc - a.width / 2 - 0.45, 160).translate([0, 0, 3.0])
    hole = M.cylinder(14, 40.5 / 2, 40.5 / 2, 160).translate([0, 0, -1])
    part = flange + spigot - hole
    mesh = part.to_mesh()
    out = os.path.join(HERE, "out", "korb", f"mount-{a.name}.stl")
    lampgen.write_stl(out, np.asarray(mesh.vert_properties)[:, :3].astype(np.float32), np.asarray(mesh.tri_verts).astype(np.int64))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="korb")
    ap.add_argument("--printer", choices=weave.PRINTERS, default="h2s")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--cell", type=float, default=9.0, help="cell width at the widest radius of each section, mm (before scale)")
    ap.add_argument("--amp", type=float, default=3.9, help="zig-zag amplitude, mm (before scale); ~0.43 x cell gives 60° strands")
    ap.add_argument("--flat", type=float, default=0.12, help="flat tips for longer fused contacts")
    ap.add_argument("--rings", type=float, nargs="*", default=[80.0, 150.0], help="heights of solid hoops, mm (before scale)")
    ap.add_argument("--ring-h", type=float, default=1.6)
    ap.add_argument("--foot", type=float, default=4.0)
    ap.add_argument("--layer", type=float, default=0.25)
    ap.add_argument("--first", type=float, default=0.3)
    ap.add_argument("--strand-h", type=float, default=0.5)
    ap.add_argument("--width", type=float, default=0.65, help="strand width (0.4 nozzle: up to 0.65; 0.6 nozzle: 0.9)")
    ap.add_argument("--flow", type=float, default=1.0)
    ap.add_argument("--temp", type=int, default=215)
    ap.add_argument("--bed", type=int, default=55)
    ap.add_argument("--fan", type=int, default=100)
    ap.add_argument("--speed", type=float, default=12, help="mm/s in the lattice")
    ap.add_argument("--speed-band", type=float, default=30)
    ap.add_argument("--speed-first", type=float, default=18)
    ap.add_argument("--brim", type=int, default=5)
    ap.add_argument("--generic-start", action="store_true", help="use the simple generic start instead of Bambu's H2S sequence")
    ap.add_argument("--mount", action="store_true", help="also write the PETG hanging disc STL")
    ap.add_argument("--tubes", help="also write the toolpath as a tube STL to this path (for renders)")
    a = ap.parse_args()
    path, s = write(a)
    print(f"{path}\n  H {s['height']:.0f} mm, Ø {s['diameter']:.0f} mm, path {s['path_m']:.0f} m, about {s['grams']:.0f} g, "
          f"about {s['hours']:.1f} h, profile tilt max {s['tilt']:.0f}°, fits {a.printer}: {s['fits']}")
    if a.mount:
        print("  mount:", mount(a))
    if a.tubes:
        print("  tubes:", tube_stl(a, a.tubes), "triangles")


if __name__ == "__main__":
    main()
