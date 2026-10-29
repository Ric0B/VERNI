#!/usr/bin/env python3
"""Turn a korb.py / weave.py toolpath into files Bambu Studio and the printer accept.

    python3 make_3mf.py out/korb/korb-test.gcode
    # -> out/korb/korb-test.bambu.gcode   tagged G-code (opens in Bambu Studio's preview)
    # -> out/korb/korb-test.gcode.3mf     sliced-plate package (USB stick on the printer, or Bambu Studio)

Why: Bambu Studio's preview starts a new layer at every Z change unless the file carries
its own layer tags. A woven, non-planar path changes Z on almost every move, which gives
tens of thousands of "layers" and crashes the preview. This script adds what a file sliced
by Bambu Studio carries:
  - HEADER_BLOCK (time, layers, filament) and a CONFIG_BLOCK from the official H2S + Bambu PLA
    Basic profiles (templates/h2s_pla_profiles.json) with spiral_mode = 1, so the preview takes
    layers from tags instead of Z changes;
  - per lap: ; CHANGE_LAYER, ; Z_HEIGHT, ; LAYER_HEIGHT, ; FEATURE, M73 progress and layer number;
  - the .gcode.3mf structure of "Export plate sliced file" (bbs_3mf.cpp): plate_1.gcode + MD5,
    slice_info.config, model_settings.config, project_settings.config, thumbnails, an empty model.
The moves themselves are not changed. Python 3 standard library + Pillow (thumbnails only).
"""
import argparse
import hashlib
import io
import json
import math
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO_VERSION = "02.08.04.57"  # the Bambu Studio release the profiles were taken from
PROFILES = os.path.join(HERE, "templates", "h2s_pla_profiles.json")
PREPARE_S = 420  # H2S start sequence (heat, level, wipe, purge), about 7 minutes
DENSITY = 1.26   # Bambu PLA Basic, g/cm3
FIL_D = 1.75
SKIP = {"name", "inherits", "from", "setting_id", "instantiation", "type", "include", "filament_id",
        "compatible_printers", "compatible_printers_condition", "compatible_prints", "compatible_prints_condition",
        "renamed_from", "description", "version", "filament_settings_id", "print_settings_id", "printer_settings_id"}

MOVE = re.compile(r"^G[01]\s")
AX = re.compile(r"([XYZEF])(-?\d*\.?\d+)")


def split(text):
    a, b = text.find("; brim"), text.find("; ---- end")
    if a < 0 or b < 0:
        raise SystemExit("Not a korb.py / weave.py file: no '; brim' / '; ---- end' markers.")
    start, body, end = text[:a], text[a:b], text[b:]
    info = [l for l in start.splitlines()[:6] if l.startswith("; ") and not l.startswith("; ----")]
    return info, start, body, end


def simulate(lines, pos, f):
    """Time (s), filament (mm) and max Z of a block of moves; G90/M83 as korb.py writes them."""
    t = e = 0.0
    zmax = pos[2]
    rel = False
    for l in lines:
        if l.startswith("G91"):
            rel = True
        elif l.startswith("G90"):
            rel = False
        if not MOVE.match(l):
            continue
        v = dict(AX.findall(l.split(";")[0]))
        if "F" in v:
            f = float(v["F"])
        new = list(pos)
        for i, k in enumerate("XYZ"):
            if k in v:
                new[i] = pos[i] + float(v[k]) if rel else float(v[k])
        d = math.dist(pos, new)
        if "E" in v and float(v["E"]) > 0:
            e += float(v["E"])
            zmax = max(zmax, new[2])
        t += (d if d > 0 else abs(float(v.get("E", 0)))) / max(f / 60.0, 0.1)
        pos = new
    return t, e, zmax, pos, f


def tag_body(body, layer_h, width):
    """Insert Bambu layer tags each time the extruded height rises by one layer."""
    lines = body.splitlines()
    layers = []  # (line index, z)
    pos, top, last = [0.0, 0.0, 0.0], 0.0, -1.0
    rel = False
    for i, l in enumerate(lines):
        if l.startswith("G91"):
            rel = True
        elif l.startswith("G90"):
            rel = False
        if not MOVE.match(l):
            continue
        v = dict(AX.findall(l.split(";")[0]))
        for j, k in enumerate("XYZ"):
            if k in v:
                pos[j] = pos[j] + float(v[k]) if rel else float(v[k])
        if "E" in v and float(v["E"]) > 0 and pos[2] > top:
            top = pos[2]
            if top >= last + 0.9 * layer_h:
                layers.append((i, top))
                last = top
    feature = {}
    for i, l in enumerate(lines):
        if l.startswith("; woven"):
            feature[i] = "Outer wall"
        elif l.startswith("; brim"):
            feature[i] = "Brim"
    return lines, layers, feature


def build_gcode(path, layer_h, width, colour):
    info, start, body, end = split(open(path, encoding="utf-8").read())
    lines, layers, feature = tag_body(body, layer_h, width)
    n = len(layers)
    t_start, _, _, pos, f = simulate(start.splitlines(), [0.0, 0.0, 0.0], 3000.0)
    t_body, e_body, zmax, _, _ = simulate(lines, pos, f)
    total = PREPARE_S + t_body
    mass = e_body * math.pi * (FIL_D / 2) ** 2 / 1000 * DENSITY

    # body with tags; progress per layer from the time spent so far
    at = {i: k for k, (i, _) in enumerate(layers)}
    out, chunk, done, cur_feature = [], [], 0.0, "Brim"
    for i, l in enumerate(lines):
        if i in feature:
            cur_feature = feature[i]
        if i in at:
            dt, _, _, pos, f = simulate(chunk, pos, f)
            done += dt
            chunk = []
            k = at[i]
            z = layers[k][1]
            prev = layers[k - 1][1] if k else 0.0
            pct = int(100 * (PREPARE_S + done) / total)
            out += ["; CHANGE_LAYER", f"; Z_HEIGHT: {z:.3f}", f"; LAYER_HEIGHT: {max(z - prev, 0.05):.3f}",
                    f"; layer num/total_layer_count: {k + 1}/{n}", "; update layer progress",
                    f"M73 L{k + 1}", f"M991 S0 P{k} ;notify layer change",
                    f"M73 P{min(pct, 99)} R{max(int((total - PREPARE_S - done) / 60), 0)}",
                    f"; FEATURE: {cur_feature}", f"; LINE_WIDTH: {width:.2f}"]
        out.append(l)
        chunk.append(l)
    tagged_body = "\n".join(out) + "\n"

    def hms(s):
        s = int(s)
        return (f"{s // 3600}h " if s >= 3600 else "") + f"{s % 3600 // 60}m {s % 60}s"

    header = ["; HEADER_BLOCK_START",
              f"; BambuStudio-compatible file written by Schichtlicht make_3mf.py (moves from {os.path.basename(path)}, not sliced)",
              f"; model printing time: {hms(t_body)}; total estimated time: {hms(total)}",
              f"; total layer number: {n}",
              f"; total filament length [mm] : {e_body:.2f}",
              f"; total filament volume [cm^3] : {e_body * math.pi * (FIL_D / 2) ** 2 / 1000:.2f}",
              f"; total filament weight [g] : {mass:.2f}",
              f"; filament_density: {DENSITY}", f"; filament_diameter: {FIL_D}",
              f"; max_z_height: {zmax:.2f}", "; filament: 1", "; support_material_on_wipe_tower: 0",
              "; HEADER_BLOCK_END", ""]
    cfg = config_block(layer_h, width, colour, zmax)
    start_lines = start.rstrip("\n").splitlines()
    # our own description lines stay at the very top, after the header
    text = ("\n".join(header) + "\n" + "\n".join(cfg) + "\n\n" + "\n".join(info) + "\n"
            + "\n".join(start_lines[len(info):]) + "\n; MACHINE_START_GCODE_END\n" + f"M73 P{int(100 * PREPARE_S / total)} R{int(t_body / 60)}\n"
            + tagged_body + "; MACHINE_END_GCODE_START\n" + end.rstrip("\n").replace("M73 P100 R0", "") + "\nM73 P100 R0\n")
    stats = dict(time=total, model_time=t_body, layers=n, length=e_body, weight=mass, zmax=zmax)
    return text, stats


def profiles():
    with open(PROFILES, encoding="utf-8") as f:
        return json.load(f)


def overrides(layer_h, width, colour):
    return {"spiral_mode": "1", "layer_height": f"{layer_h}", "initial_layer_print_height": "0.3",
            "wall_loops": "1", "sparse_infill_density": "0%", "top_shell_layers": "0", "bottom_shell_layers": "0",
            "outer_wall_line_width": f"{width}", "enable_support": "0", "curr_bed_type": "Textured PEI Plate",
            "nozzle_temperature": ["215"], "nozzle_temperature_initial_layer": ["215"],
            "filament_colour": [colour], "default_filament_colour": [""], "filament_map": ["1"]}


def config_block(layer_h, width, colour, zmax):
    """Scalars from the official profiles plus the few vectors the preview reads, as Bambu Studio writes them."""
    p = profiles()
    merged = {}
    for part in ("machine", "process", "filament"):
        merged.update(p[part])
    merged.update(overrides(layer_h, width, colour))
    keep = {"nozzle_diameter", "filament_diameter", "filament_density", "filament_colour", "filament_type",
            "filament_map", "nozzle_temperature", "nozzle_temperature_initial_layer", "hot_plate_temp",
            "textured_plate_temp", "filament_vendor", "filament_max_volumetric_speed"}
    rows = ["; CONFIG_BLOCK_START"]
    for k in sorted(merged):
        v = merged[k]
        if k in SKIP or "gcode" in k:
            continue
        if isinstance(v, list):
            if k not in keep or not v:
                continue
            v = ";".join(v) if k in ("filament_colour", "filament_type", "filament_vendor") else ",".join(v[:1])
        v = str(v)
        if "\n" in v or len(v) > 200:
            continue
        rows.append(f"; {k} = {v}")
    rows += ["; printer_model = Bambu Lab H2S", "; printer_settings_id = Bambu Lab H2S 0.4 nozzle",
             "; print_settings_id = 0.20mm Standard @BBL H2S", "; filament_settings_id = \"Bambu PLA Basic @BBL H2S\"",
             "; CONFIG_BLOCK_END"]
    return rows


def project_settings(layer_h, width, colour):
    p = profiles()
    merged = {}
    for part in ("machine", "process", "filament"):
        merged.update({k: v for k, v in p[part].items() if k not in SKIP})
    merged.update(overrides(layer_h, width, colour))
    merged.update({"name": "project_settings", "from": "project", "version": STUDIO_VERSION,
                   "printer_model": "Bambu Lab H2S", "printer_settings_id": "Bambu Lab H2S 0.4 nozzle",
                   "print_settings_id": "0.20mm Standard @BBL H2S", "filament_settings_id": ["Bambu PLA Basic @BBL H2S"],
                   "inherits_group": ["0.20mm Standard @BBL H2S", "Bambu PLA Basic @BBL H2S", "Bambu Lab H2S 0.4 nozzle"],
                   "filament_ids": ["GFA00"]})
    return json.dumps(merged, indent=4)


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
 <Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>
 <Relationship Target="/Metadata/plate_1.png" Id="rel-4" Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-middle"/>
 <Relationship Target="/Metadata/plate_1_small.png" Id="rel-5" Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-small"/>
</Relationships>
"""

MODEL = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">
 <metadata name="Application">BambuStudio-{ver}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{title}</metadata>
 <metadata name="Designer">Schichtlicht</metadata>
 <resources>
 </resources>
 <build/>
</model>
"""

MODEL_SETTINGS = """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="{title}"/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="filament_maps" value="1"/>
    <metadata key="gcode_file" value="Metadata/plate_1.gcode"/>
    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>
  </plate>
</config>
"""

SLICE_INFO = """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
    <header_item key="X-BBL-Client-Version" value="{ver}"/>
  </header>
  <plate>
    <metadata key="index" value="1"/>
    <metadata key="extruder_type" value="0"/>
    <metadata key="nozzle_volume_type" value="0"/>
    <metadata key="printer_model_id" value="O1S"/>
    <metadata key="nozzle_diameters" value="0.4"/>
    <metadata key="timelapse_type" value="0"/>
    <metadata key="prediction" value="{pred}"/>
    <metadata key="weight" value="{weight:.2f}"/>
    <metadata key="pause_count" value="0"/>
    <metadata key="outside" value="false"/>
    <metadata key="support_used" value="false"/>
    <metadata key="label_object_enabled" value="false"/>
    <metadata key="support_material_on_wipe_tower" value="false"/>
    <metadata key="enable_filament_dynamic_map" value="false"/>
    <metadata key="has_filament_switcher" value="false"/>
    <metadata key="filament_maps" value="1"/>
    <filament id="1" tray_info_idx="GFA00" type="PLA" color="{colour}" used_m="{used_m:.2f}" used_g="{weight:.2f}" group_id="0" nozzle_diameter="0.40" volume_type="Standard" used_for_object="true" used_for_support="false"/>
  </plate>
</config>
"""


def thumbnails(render):
    from PIL import Image
    im = Image.open(render).convert("RGB") if render and os.path.exists(render) else Image.new("RGB", (512, 512), (40, 36, 32))
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    out = []
    for size in (512, 128):
        b = io.BytesIO()
        im.resize((size, size), Image.LANCZOS).save(b, "PNG")
        out.append(b.getvalue())
    return out


def write_3mf(out, gcode, stats, title, colour, render, layer_h, width):
    data = gcode.encode("utf-8")
    big, small = thumbnails(render)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", MODEL.format(ver=STUDIO_VERSION, title=title))
        z.writestr("Metadata/plate_1.gcode", data)
        z.writestr("Metadata/plate_1.gcode.md5", hashlib.md5(data).hexdigest().upper())
        z.writestr("Metadata/model_settings.config", MODEL_SETTINGS.format(title=title))
        z.writestr("Metadata/slice_info.config", SLICE_INFO.format(ver=STUDIO_VERSION, pred=int(stats["time"]),
                   weight=stats["weight"], colour=colour, used_m=stats["length"] / 1000))
        z.writestr("Metadata/project_settings.config", project_settings(layer_h, width, colour))
        z.writestr("Metadata/plate_1.png", big)
        z.writestr("Metadata/plate_1_small.png", small)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gcode", help="toolpath from korb.py or weave.py (already contains the H2S start/end)")
    ap.add_argument("--title")
    ap.add_argument("--render", help="image for the printer's thumbnail")
    ap.add_argument("--colour", default="#FFFFFF")
    ap.add_argument("--layer", type=float, default=0.25)
    ap.add_argument("--width", type=float, default=0.65)
    a = ap.parse_args()
    base = a.gcode[:-6] if a.gcode.endswith(".gcode") else a.gcode
    title = a.title or os.path.basename(base)
    text, st = build_gcode(a.gcode, a.layer, a.width, a.colour)
    with open(base + ".bambu.gcode", "w", encoding="utf-8") as f:
        f.write(text)
    write_3mf(base + ".gcode.3mf", text, st, title, a.colour, a.render, a.layer, a.width)
    print(f"{title}: {st['layers']} layers, {st['weight']:.1f} g, {st['length'] / 1000:.1f} m, "
          f"about {st['time'] / 3600:.1f} h with start, top Z {st['zmax']:.1f}\n  {base}.bambu.gcode\n  {base}.gcode.3mf")


if __name__ == "__main__":
    main()
