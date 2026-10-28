#!/usr/bin/env python3
"""One-offs and numbered editions.

Gletscher (one-off): every order gets a new code. The code is the random seed
of the Voronoi pattern, so the geometry exists once. Codes are recorded in
editions/registry.json and refused if used before.

Moräne (edition of 50): numbers 1-50, each with its own attractor seed, so
pieces in the edition are siblings, not copies.

    python3 edition.py gletscher --code 14062019 --name "Anna & Luca"
    python3 edition.py gletscher --random
    python3 edition.py moraene --number 7
    python3 edition.py --registry

Writes out/<design>-<code>-shade.stl, a pattern image (the unrolled surface)
and a certificate as HTML. Turn the certificate into a PDF in any browser, or
with `python3 edition.py ... --pdf` if Playwright is installed.
"""
import argparse
import datetime as dt
import html
import json
import os
import secrets
import zlib

import numpy as np

import lampgen

HERE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(HERE, "editions", "registry.json")
LIMITS = {"moraene": 50}


def load_registry():
    try:
        with open(REG, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"gletscher": {}, "moraene": {}}


def save_registry(reg):
    os.makedirs(os.path.dirname(REG), exist_ok=True)
    with open(REG, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2, sort_keys=True)


def seed_for(design, code):
    # Mix the design name in, so code 7 for Moräne and Gletscher are unrelated.
    return zlib.crc32(f"{design}:{code}".encode()) % 2_000_000_000


def pattern_png(R, path):
    """Unrolled surface as a greyscale relief map: the lamp's fingerprint."""
    from PIL import Image  # pip install pillow
    rel = R - R.mean(axis=1, keepdims=True)
    lo, hi = np.percentile(rel, 1), np.percentile(rel, 99)
    g = np.clip((rel - lo) / (hi - lo), 0, 1)
    img = (40 + 200 * g[::-1]).astype(np.uint8)  # top of the lamp at the top
    Image.fromarray(img, "L").resize((900, int(900 * img.shape[0] / img.shape[1]))).save(path)


def html_to_pdf(src, dst, fmt="A5"):
    """Python Playwright if installed, else Node's (npm i playwright)."""
    url = "file://" + os.path.abspath(src)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page()
            pg.goto(url)
            pg.pdf(path=dst, format=fmt, print_background=True)
            b.close()
    except ImportError:
        import subprocess
        js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
              f"await p.goto({json.dumps(url)});await p.pdf({{path:{json.dumps(os.path.abspath(dst))},format:'{fmt}',printBackground:true}});await b.close();}})();")
        subprocess.run(["node", "-e", js], check=True)


CERT = """<!doctype html><html lang="de"><head><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gloock&family=Hanken+Grotesk:wght@400;600&family=IBM+Plex+Mono&display=swap"><title>Zertifikat {title} {code}</title>
<style>
@page {{ size: A5; margin: 14mm; }}
body {{ font: 10.5pt/1.5 "Hanken Grotesk", Helvetica, Arial, sans-serif; color: #1b2124; margin: 0; }}
h1 {{ font: 400 26pt/1 Gloock, Georgia, serif; margin: 0 0 4mm; }}
.eyebrow {{ font: 8pt/1 "IBM Plex Mono", monospace; letter-spacing: .14em; text-transform: uppercase; color: #59625e; }}
table {{ border-collapse: collapse; width: 100%; margin: 5mm 0; font-size: 9.5pt; }}
th, td {{ text-align: left; padding: 1.2mm 0; border-bottom: .3mm solid #cdd3ce; }}
th {{ font: 7.5pt "IBM Plex Mono", monospace; text-transform: uppercase; letter-spacing: .08em; color: #59625e; width: 38%; }}
img {{ width: 100%; height: 58mm; object-fit: cover; display: block; margin: 4mm 0; border: .3mm solid #cdd3ce; }}
.sig {{ margin-top: 8mm; display: flex; justify-content: space-between; font-size: 8.5pt; color: #59625e; }}
.sig span {{ border-top: .3mm solid #1b2124; padding-top: 1.5mm; min-width: 45mm; }}
</style></head><body>
<p class="eyebrow">Schichtlicht · {kind}</p>
<h1>{title} {label}</h1>
<p>{text}</p>
<img src="{img}" alt="Abwicklung des Musters">
<table>
<tr><th>Code</th><td>{code}</td></tr>
{dedication}
<tr><th>Gedruckt am</th><td>{date}</td></tr>
<tr><th>Schichten</th><td>{layers} × 0.24 mm</td></tr>
<tr><th>Höhe × Ø</th><td>{height} × {diameter} mm</td></tr>
<tr><th>Parameter</th><td style="font: 8pt 'IBM Plex Mono', monospace">{params}</td></tr>
</table>
<div class="sig"><span>Signatur</span><span>Ort, Datum</span></div>
</body></html>"""


def make(design, code, number=None, name=None, pdf=False, force=False):
    reg = load_registry()
    book = reg.setdefault(design, {})
    key = str(number if design in LIMITS else code)
    if key in book and not force:
        raise SystemExit(f"{design} {key} was already issued on {book[key]['date']}. Codes are never reused.")
    if design in LIMITS and not 1 <= number <= LIMITS[design]:
        raise SystemExit(f"{design} is an edition of {LIMITS[design]}.")
    seed = seed_for(design, code)
    tag = f"-{key}"
    out = os.path.join(lampgen.OUT, "editions")
    info = lampgen.export(design, {"seed": seed}, res="medium", out=out, tag=tag)
    T, Z, R, p = lampgen.build(design, {"seed": seed}, res="medium")
    png = os.path.join(out, f"{design}{tag}-pattern.png")
    pattern_png(R, png)
    today = dt.date.today().isoformat()
    title = lampgen.DESIGNS[design]["title"]
    if design in LIMITS:
        kind, label = f"Edition von {LIMITS[design]}", f"{number:02d}/{LIMITS[design]}"
        text = "Teil einer nummerierten Edition. Jedes Exemplar hat eigene Attraktorpunkte und unterscheidet sich von seinen Geschwistern."
    else:
        kind, label = "Unikat", f"№ {code}"
        text = "Dieses Muster wurde aus dem untenstehenden Code berechnet und genau einmal gedruckt. Der Code ist gesperrt und wird nie wieder vergeben."
    shown = {k: v for k, v in p.items() if k not in ("collar", "collar_blend")}
    cert = CERT.format(title=html.escape(title), label=html.escape(label), kind=kind, text=text, code=html.escape(str(code)),
                       img=os.path.basename(png), date=today, layers=round(p["height"] / 0.24), height=p["height"],
                       diameter=round(2 * info["r_max"]),
                       dedication=f"<tr><th>Für</th><td>{html.escape(name)}</td></tr>" if name else "",
                       params=html.escape(", ".join(f"{k}={v}" for k, v in shown.items())))
    cert_path = os.path.join(out, f"{design}{tag}-certificate.html")
    with open(cert_path, "w", encoding="utf-8") as f:
        f.write(cert)
    if pdf:
        html_to_pdf(cert_path, cert_path.replace(".html", ".pdf"))
    book[key] = {"code": code, "seed": seed, "date": today, "name": name, "stl": os.path.relpath(info["file"], HERE),
                 "overhang_p99": round(info["p99_overhang_deg"], 1)}
    save_registry(reg)
    return info, cert_path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("design", nargs="?", choices=["gletscher", "moraene"])
    ap.add_argument("--code", help="any number or word, e.g. a date 14062019")
    ap.add_argument("--random", action="store_true")
    ap.add_argument("--number", type=int, help="edition number (Moräne)")
    ap.add_argument("--name", help="dedication on the certificate")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--force", action="store_true", help="re-issue (only to replace a failed print)")
    ap.add_argument("--registry", action="store_true")
    a = ap.parse_args()
    if a.registry:
        print(json.dumps(load_registry(), ensure_ascii=False, indent=2))
        return
    if not a.design:
        ap.error("choose a design")
    if a.design == "moraene":
        if not a.number:
            ap.error("Moräne needs --number 1..50")
        code = f"M{a.number:02d}"
    else:
        code = secrets.randbelow(10**8) if a.random or not a.code else a.code
    info, cert = make(a.design, code, a.number, a.name, a.pdf, a.force)
    flag = "OK" if info["p99_overhang_deg"] <= 50 else "CHECK THE PREVIEW BEFORE PRINTING"
    print(f"{a.design} {code}: {info['file']}  overhang p99 {info['p99_overhang_deg']:.0f}°  {flag}\ncertificate: {os.path.relpath(cert)}")


if __name__ == "__main__":
    main()
