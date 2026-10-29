#!/usr/bin/env python3
"""Fill Bambu Lab's official machine start/end G-code templates without Bambu Studio.

The templates come from the Bambu Studio repository (resources/profiles/BBL/machine,
"Bambu Lab H2S 0.4 nozzle template machine_start_gcode.json" etc.). They use Bambu's
placeholder language: [var], {expression}, {if ...}{elsif ...}{else}{endif}. This file
implements the small part of it those templates use, with the values Bambu Studio
itself would set for Bambu PLA Basic on a 0.4 mm nozzle (read from the same repository).

    import bambu_gcode
    start, end = bambu_gcode.h2s(bed_min=(108, 98), bed_size=(124, 124), max_z=115)

Copies of the two templates are stored next to this file (templates/), so this works
offline. Refresh them from a newer Bambu Studio checkout with --refresh PATH.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "templates")


class Vec(list):
    """A one-filament vector that also behaves like its first value (Bambu's templates use both forms)."""

    def _v(self):
        return self[0]

    def __eq__(self, o):
        return self._v() == o if not isinstance(o, list) else list.__eq__(self, o)

    def __ne__(self, o):
        return not self.__eq__(o)

    def __lt__(self, o): return self._v() < o
    def __le__(self, o): return self._v() <= o
    def __gt__(self, o): return self._v() > o
    def __ge__(self, o): return self._v() >= o
    def __float__(self): return float(self._v())
    def __str__(self): return fmt(self._v())
    __hash__ = None


def fmt(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return ("%.6f" % v).rstrip("0").rstrip(".")
    return str(v)


PLA_H2S = {
    "filament_type": Vec(["PLA"]),
    "nozzle_temperature": Vec([220]),
    "nozzle_temperature_initial_layer": Vec([220]),
    "bed_temperature_initial_layer_single": 55,
    "filament_max_volumetric_speed": Vec([25.0]),
    "flush_volumetric_speeds": Vec([25.0]),          # filament_flush_volumetric_speed 0 -> falls back to max volumetric speed
    "flush_temperatures": Vec([240]),                # filament_flush_temp 0 -> nozzle_temperature_range_high
    "min_vitrification_temperature": 45,
    "overall_chamber_temperature": 0,
    "is_all_bbl_filament": True,
    "cooling_filter_enabled": False,
    "has_tpu_in_first_layer": False,
    "initial_no_support_extruder": 0,
    "nozzle_diameter": Vec([0.4]),
    "curr_bed_type": "Textured PEI Plate",
}


def _expr(src, env):
    py = " ".join(src.split()).replace("&&", " and ").replace("||", " or ")
    py = re.sub(r"!(?!=)", " not ", py)
    py = py.replace("true", "True").replace("false", "False")
    return eval(py, {"__builtins__": {}, "min": min, "max": max, "int": int, "abs": abs, "math": math}, env)


def fill(tpl, env):
    """Expand {if}/{elsif}/{else}/{endif}, {expr} and [var] like Bambu Studio's placeholder parser."""
    tokens = re.split(r"(\{[^{}]*\})", tpl)
    out, stack = [], []  # stack of [active, taken]

    def active():
        return all(s[0] for s in stack)

    for t in tokens:
        if t.startswith("{") and t.endswith("}"):
            body = t[1:-1].strip()
            m = re.match(r"(if|elsif)\b(.*)", body, re.S)
            if m and m.group(1) == "if":
                cond = bool(_expr(m.group(2), env)) if active() else False
                stack.append([cond, cond])
                continue
            if m and m.group(1) == "elsif":
                top = stack[-1]
                cond = (not top[1]) and bool(_expr(m.group(2), env))
                top[0], top[1] = cond, top[1] or cond
                continue
            if body == "else":
                top = stack[-1]
                top[0], top[1] = not top[1], True
                continue
            if body == "endif":
                stack.pop()
                continue
            if active():
                out.append(fmt(_expr(body, env)))
            continue
        if active():
            out.append(re.sub(r"\[([a-z_][a-z0-9_]*)\]", lambda m: str(env[m.group(1)]) if m.group(1) in env else m.group(0), t))
    if stack:
        raise ValueError("unbalanced {if} in template")
    text = "".join(out)
    left = re.findall(r"\[[a-z_][a-z0-9_]*\]|\{[^{}]*\}", text)
    if left:
        raise ValueError(f"unfilled placeholders: {sorted(set(left))[:10]}")
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", text)


def load(name):
    with open(os.path.join(TPL, name), encoding="utf-8") as f:
        d = json.load(f)
    return d[[k for k in d if k.endswith("gcode")][0]]


def h2s(bed_min, bed_size, max_z, filament=PLA_H2S, bed_type="Textured PEI Plate", allow_nozzle_cam=False):
    env = dict(filament)
    env.update(curr_bed_type=bed_type, max_print_z=round(max_z, 2), max_layer_z=round(max_z, 2),
               first_layer_print_min=[round(bed_min[0], 2), round(bed_min[1], 2)],
               first_layer_print_size=[round(bed_size[0], 2), round(bed_size[1], 2)])
    start = fill(load("Bambu Lab H2S 0.4 nozzle template machine_start_gcode.json"), env)
    end = fill(load("Bambu Lab H2S 0.4 nozzle template machine_end_gcode.json"), env)
    if not allow_nozzle_cam:
        # The nozzle camera's clump detection is tuned for sliced prints; a woven, non-planar path can look
        # like a failure to it. Keep it off for these prints.
        start = start.replace("M993 A1 B1 C1 ; nozzle cam detection allowed.", "M993 A0 B0 C0 ; nozzle cam detection kept off for woven toolpath")
        # Air-printing detection can mistake long bridged strands for a clog and pause the print.
        start = start.replace("M1015.4 S1 K1 H0.4 ;enable E air printing detect", "M1015.4 S0 K0 H0.4 ;air printing detect kept off for woven toolpath")
    return start, end


def refresh(repo):
    os.makedirs(TPL, exist_ok=True)
    src = os.path.join(repo, "resources", "profiles", "BBL", "machine")
    for n in ("Bambu Lab H2S 0.4 nozzle template machine_start_gcode.json", "Bambu Lab H2S 0.4 nozzle template machine_end_gcode.json"):
        with open(os.path.join(src, n), encoding="utf-8") as f, open(os.path.join(TPL, n), "w", encoding="utf-8") as g:
            g.write(f.read())
        print("copied", n)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--refresh":
        refresh(sys.argv[2])
    else:
        s, e = h2s((108, 98), (124, 124), 115)
        print(s[-1200:], "\n...\n", e[:600])
