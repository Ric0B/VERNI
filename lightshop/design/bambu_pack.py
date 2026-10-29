#!/usr/bin/env python3
"""Pack a generated toolpath (korb.py / weave.py) into a Bambu .gcode.3mf that uses
the printer's own start sequence (bed levelling, nozzle wipe, filament load).

How: slice any tiny object in Bambu Studio for the same printer, nozzle and
filament, export it with File > Export > Export plate sliced file, then:

    python3 bambu_pack.py dummy.gcode.3mf out/korb/korb-test.gcode
    # -> out/korb/korb-test.gcode.3mf   (open in Bambu Studio, Print plate)

The packer keeps Bambu's start G-code from the dummy (everything before its
first layer), drops the dummy's object, inserts our toolpath (from "; brim"
to "; ---- end"), adds a safe end sequence and recomputes the MD5 file the
firmware checks. Python 3 standard library only.
"""
import argparse
import hashlib
import os
import re
import sys
import zipfile

END = """; ---- end (bambu_pack)
G1 Z{zup:.1f} F600
M104 S0
M140 S0
M106 P1 S0
M106 P2 S0
M106 P3 S0
G1 X{x:.1f} Y{y:.1f} F6000
M84
"""


def split_start(gcode):
    """Everything before the dummy's first layer is the printer's start sequence."""
    for marker in ("; CHANGE_LAYER", "; layer num/total_layer_count: 1/", ";LAYER_CHANGE", ";LAYER:0"):
        i = gcode.find(marker)
        if i > 0:
            return gcode[:i], marker
    raise SystemExit("Could not find the first layer in the dummy file. Slice a small cube in Bambu Studio and export "
                     "the plate sliced file again (File > Export > Export plate sliced file).")


def our_body(path):
    text = open(path, encoding="utf-8").read()
    a = text.find("; brim")
    b = text.find("; ---- end")
    if a < 0 or b < 0:
        raise SystemExit(f"{path} does not look like a korb.py / weave.py file (no '; brim' / '; ---- end' markers).")
    header = "\n".join(l for l in text[:a].splitlines() if l.startswith("; Schichtlicht") or l.startswith("; scale") or l.startswith("; cell") or l.startswith("; height") or l.startswith("; layer"))
    zs = [float(m) for m in re.findall(r"Z(\d+\.?\d*)", text[a:b])]
    return header, text[a:b], max(zs) if zs else 100.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dummy", help="a .gcode.3mf exported from Bambu Studio for your printer")
    ap.add_argument("gcode", help="toolpath from korb.py or weave.py")
    ap.add_argument("-o", "--out")
    ap.add_argument("--park", default="170,300", help="X,Y to park at the end")
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.gcode)[0] + ".gcode.3mf"
    with zipfile.ZipFile(a.dummy) as z:
        names = z.namelist()
        plates = [n for n in names if re.fullmatch(r"Metadata/plate_\d+\.gcode", n)]
        if not plates:
            sys.exit("No Metadata/plate_N.gcode inside the dummy. Export with 'Export plate sliced file', not 'Export project'.")
        plate = plates[0]
        start, marker = split_start(z.read(plate).decode("utf-8", "replace"))
        header, body, zmax = our_body(a.gcode)
        x, y = (float(v) for v in a.park.split(","))
        new = (start.rstrip() + "\n; ==== Schichtlicht toolpath (bambu_pack) ====\n" + header + "\n"
               "G90\nM83\nG92 E0\nG1 Z2 F600\n" + body + END.format(zup=min(zmax + 15, 330), x=x, y=y))
        data = new.encode("utf-8")
        md5 = hashlib.md5(data).hexdigest().upper()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as w:
            for n in names:
                if n == plate:
                    w.writestr(n, data)
                elif n == plate + ".md5":
                    w.writestr(n, md5)
                else:
                    w.writestr(z.getinfo(n), z.read(n))
            if plate + ".md5" not in names:
                w.writestr(plate + ".md5", md5)
    print(f"wrote {out}\n  start sequence: {len(start.splitlines())} lines from the dummy (cut at '{marker}')"
          f"\n  toolpath: {len(body.splitlines())} lines, top at Z{zmax:.1f}")


if __name__ == "__main__":
    main()
