#!/usr/bin/env python3
"""Build catalog.html: every concept, module, stack and nested pair with renders and print numbers.

    python3 ../design/concepts.py --stats > stats.json
    python3 make_catalog.py stats.json        # writes catalog.html next to renders/
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape

MODULE_PRICE = {"m-glatt": 49, "m-rippe": 69, "m-twist-r": 69, "m-twist-l": 69, "m-balg": 59, "m-polster": 49,
                "m-spalt": 69, "m-kuehl": 79, "m-gewinde": 59, "m-kuppel": 39}
BASE_KIT = 119   # printed base, socket on threaded tube, cord set, LED

LINES = {
    "WERK": ("Werk", "Industrial. Heat sinks, threads, gears, extrusion profiles and bellows, translated into light. For lofts, studios, offices and anyone who likes machines."),
    "GRENZE": ("Grenze", "Experiments at the edge of vase mode: deep folds, morphs, leaning axes, hundreds of bumps, glitches. Small editions, gallery pieces, press."),
    "TOTEM": ("Totem", "A modular system. Every module has the same Ø140 plug: a collar below and a spigot above. Print modules separately and stack them in any order, in any colour."),
    "DUO": ("Duo", "Two shades nested inside each other. Switched off they look calm; lit, the patterns interfere and move as you walk past."),
}


def metrics(s, price):
    tilt = s["tilt_p99"]
    pct = min(100, tilt / 60 * 100)
    cls = "ok" if s["printable"] else "warn"
    return f"""<dl class="m">
<div><dt>Overhang p99</dt><dd><span class="bar {cls}"><i style="width:{pct:.0f}%"></i><b></b></span>{tilt:.0f}°</dd></div>
<div><dt>H × Ø</dt><dd>{s['height']:.0f} × {s['width_mm']:.0f}</dd></div>
<div><dt>Filament</dt><dd>{s['grams']:.0f} g</dd></div>
<div><dt>Print</dt><dd>{s['hours']:.1f} h</dd></div>
{f'<div><dt>Price</dt><dd>CHF {price}</dd></div>' if price else ''}
</dl>"""


def card(key, title, line, idea, limit, metric_html, extra=""):
    return f"""<article class="card" data-line="{line}" tabindex="0" aria-label="{E(title)}">
<div class="img"><img src="renders/{key}-0-s.jpg" alt="{E(title)}, switched off" loading="lazy" width="400" height="500">
<img class="on" src="renders/{key}-1-s.jpg" alt="" aria-hidden="true" loading="lazy" width="400" height="500"></div>
<div class="txt"><p class="ey">{E(LINES[line][0])} · <code>{E(key)}</code></p><h3>{E(title)}</h3><p>{E(idea)}</p>
{f'<p class="lim">{E(limit)}</p>' if limit else ''}{extra}{metric_html}</div></article>"""


def main():
    data = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stats.json")))
    C, STACKS, NESTS = data["concepts"], data["stacks"], data["nests"]
    sections = []
    for line in ("WERK", "GRENZE"):
        cards = "".join(card(k, s["title"], line, s["idea"], s["limit"], metrics(s, s.get("price"))) for k, s in C.items() if s["line"] == line)
        sections.append((line, cards, len([1 for s in C.values() if s["line"] == line])))
    # TOTEM: modules, then stacks
    mods = "".join(card(k, s["title"], "TOTEM", s["idea"], s["limit"], metrics(s, MODULE_PRICE.get(k))) for k, s in C.items() if s["line"] == "TOTEM")
    stacks = ""
    for k, st in STACKS.items():
        parts = st["parts"]
        h = sum(C[p]["height"] for p in parts) - 8 * (len(parts) - 1)
        grams = sum(C[p]["grams"] for p in parts)
        hours = sum(C[p]["hours"] for p in parts)
        price = round((sum(MODULE_PRICE[p] for p in parts) * 0.9 + BASE_KIT) / 10) * 10 - 1
        chips = "".join(f'<li class="t-{t}">{E(C[p]["title"])}</li>' for p, t in zip(parts, st["tones"]))
        m = f"""<dl class="m"><div><dt>Height</dt><dd>{h:.0f} mm</dd></div><div><dt>Modules</dt><dd>{len(parts)}</dd></div>
<div><dt>Filament</dt><dd>{grams:.0f} g</dd></div><div><dt>Print</dt><dd>{hours:.1f} h</dd></div><div><dt>Price</dt><dd>CHF {price}</dd></div></dl>"""
        stacks += card(k, st["title"], "TOTEM", "Stack of " + str(len(parts)) + " modules.", "", m, f'<ol class="chips">{chips}</ol>')
    duos = ""
    for k, n in NESTS.items():
        o, i = C[n["outer"]], C[n["inner"]]
        m = f"""<dl class="m"><div><dt>Outer / inner</dt><dd>Ø {o['width_mm']:.0f} / {i['width_mm']:.0f}</dd></div>
<div><dt>Filament</dt><dd>{o['grams'] + i['grams']:.0f} g</dd></div><div><dt>Print</dt><dd>{o['hours'] + i['hours']:.1f} h</dd></div><div><dt>Price</dt><dd>CHF {n['price']}</dd></div></dl>"""
        duos += card(k, n["title"], "DUO", n["idea"], "", m)
    n_total = len(C) + len(STACKS) + len(NESTS)

    body = []
    for line, cards, n in sections:
        body.append(f'<section class="line" data-section="{line}"><header class="lh"><h2>{LINES[line][0]}</h2><p>{E(LINES[line][1])}</p><span>{n}</span></header><div class="grid">{cards}</div></section>')
    body.append(f'<section class="line" data-section="TOTEM"><header class="lh"><h2>{LINES["TOTEM"][0]}</h2><p>{E(LINES["TOTEM"][1])}</p><span>{len(STACKS)} stacks</span></header><div class="grid stacks">{stacks}</div>'
                f'<h3 class="sub">The modules</h3><div class="grid mods">{mods}</div></section>')
    body.append(f'<section class="line" data-section="DUO"><header class="lh"><h2>{LINES["DUO"][0]}</h2><p>{E(LINES["DUO"][1])}</p><span>{len(NESTS)}</span></header><div class="grid">{duos}</div></section>')

    page = f"""<meta charset="utf-8">
<title>Schichtlicht Konzepte</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gloock&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a night gallery, the same dark studio the renders were shot in; one deliberate dark look. */
:root {{ --bg:#0c0e10; --panel:#13161a; --ink:#ecebe6; --muted:#8f9894; --line:#252a2e; --glow:#f0a640; --ok:#6cc18f; --warn:#f08a4b;
  --display:"Gloock",Georgia,serif; --body:"Hanken Grotesk","Helvetica Neue",Arial,sans-serif; --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace; color-scheme:dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:400 15px/1.5 var(--body); }}
.wrap {{ max-width:84rem; margin:0 auto; padding-left:max(16px,env(safe-area-inset-left,0px)); padding-right:max(16px,env(safe-area-inset-right,0px)); }}
.top {{ padding-block:48px 24px; display:grid; gap:20px; }}
.top h1 {{ font:400 clamp(44px,8vw,96px)/.95 var(--display); margin:0; letter-spacing:-.01em; }}
.top h1 span {{ color:var(--glow); }}
.top p {{ margin:0; max-width:46rem; color:var(--muted); font-size:17px; }}
.bar-top {{ position:sticky; top:env(safe-area-inset-top,0px); z-index:5; background:color-mix(in srgb,var(--bg) 90%,transparent); backdrop-filter:blur(8px); border-bottom:1px solid var(--line); }}
body::before {{ content:""; position:fixed; inset:0 0 auto; height:env(safe-area-inset-top,0px); z-index:10; background:var(--bg); }}
.bar-top .wrap {{ display:flex; gap:10px; align-items:center; padding-block:12px; flex-wrap:wrap; }}
.chip, .switch {{ font:500 13px/1 var(--body); padding:9px 14px; border-radius:999px; border:1px solid var(--line); background:transparent; color:var(--ink); cursor:pointer; }}
.chip[aria-pressed="true"] {{ background:var(--ink); color:var(--bg); border-color:var(--ink); }}
.switch {{ margin-left:auto; display:inline-flex; align-items:center; gap:8px; }}
.switch::before {{ content:""; width:9px; height:9px; border-radius:50%; background:var(--muted); }}
.switch[aria-pressed="true"]::before {{ background:var(--glow); box-shadow:0 0 10px var(--glow); }}
button:focus-visible, .card:focus-visible {{ outline:2px solid var(--glow); outline-offset:3px; }}
.count {{ font:400 12px var(--mono); color:var(--muted); }}
.line {{ padding-block:40px 24px; border-bottom:1px solid var(--line); }}
.lh {{ display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:8px 24px; align-items:baseline; margin-bottom:24px; }}
.lh h2 {{ font:400 clamp(32px,5vw,56px)/1 var(--display); margin:0; }}
.lh p {{ margin:0; color:var(--muted); max-width:44rem; }}
.lh span {{ font:400 12px var(--mono); color:var(--muted); }}
.sub {{ font:500 12px var(--mono); letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin:36px 0 16px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:28px 18px; }}
.grid.stacks {{ grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); }}
.card {{ display:grid; gap:12px; align-content:start; min-width:0; cursor:pointer; }}
.img {{ position:relative; aspect-ratio:4/5; background:#d9dcd6; overflow:hidden; max-width:100%; }}
.img img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; transition:opacity .5s ease; }}
.img img.on {{ opacity:0; }}
body.lit .img img.on {{ opacity:1; }}
.card.flip .img img.on {{ opacity:1; }}
body.lit .card.flip .img img.on {{ opacity:0; }}
.txt {{ display:grid; gap:6px; min-width:0; }}
.ey {{ margin:0; font:400 11px/1.3 var(--mono); color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }}
.ey code {{ text-transform:none; letter-spacing:0; font-size:11px; }}
.txt h3 {{ margin:0; font:400 26px/1.05 var(--display); }}
.txt p {{ margin:0; font-size:14px; color:#c7cbc8; }}
.txt p.lim {{ color:var(--muted); font-size:13px; border-left:2px solid var(--glow); padding-left:8px; }}
.m {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px 12px; margin:6px 0 0; padding-top:8px; border-top:1px solid var(--line); }}
.m div {{ display:grid; gap:1px; min-width:0; }}
.m dt {{ font:400 10px var(--mono); text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }}
.m dd {{ margin:0; font:500 13px var(--mono); font-variant-numeric:tabular-nums; display:flex; align-items:center; gap:6px; }}
.bar {{ position:relative; width:46px; height:5px; background:var(--line); border-radius:3px; flex:none; }}
.bar i {{ position:absolute; inset:0 auto 0 0; border-radius:3px; background:var(--ok); }}
.bar.warn i {{ background:var(--warn); }}
.bar b {{ position:absolute; left:83%; top:-3px; bottom:-3px; width:1px; background:var(--ink); opacity:.6; }}
.chips {{ list-style:none; padding:0; margin:2px 0 0; display:flex; flex-wrap:wrap; gap:4px; }}
.chips li {{ font:400 11px var(--mono); padding:3px 7px; border-radius:3px; border:1px solid var(--line); }}
.chips .t-nacht {{ background:#2c3a4f; }} .chips .t-sand {{ background:#6b5a3e; }} .chips .t-stein {{ background:#3a3d3c; }} .chips .t-frost {{ background:#2a2b29; }}
.foot {{ padding-block:32px 48px; color:var(--muted); font-size:13px; display:grid; gap:6px; }}
.foot code {{ font-family:var(--mono); color:var(--ink); }}
[hidden] {{ display:none !important; }}
@media (max-width:640px) {{ .lh {{ grid-template-columns:1fr; }} .switch {{ margin-left:0; }} .grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px 12px; }} .txt h3 {{ font-size:21px; }} .m {{ grid-template-columns:1fr; }} }}
@media (prefers-reduced-motion:reduce) {{ .img img {{ transition:none; }} }}
</style>

<header class="wrap top">
  <h1>Schicht<span>licht</span><br>Concepts</h1>
  <p>{n_total} designs that push what a single-wall spiral print can do: two lines of lamps, a plug-together module system and two double-wall lamps. Every form is a formula in <code>design/concepts.py</code>, and every one passed the printability check (99% of the wall within 50° of vertical). Tap a lamp to switch it on or off on its own.</p>
</header>
<nav class="bar-top" aria-label="Filter"><div class="wrap">
  <button class="chip" type="button" aria-pressed="true" data-f="all">All</button>
  <button class="chip" type="button" aria-pressed="false" data-f="WERK">Werk</button>
  <button class="chip" type="button" aria-pressed="false" data-f="GRENZE">Grenze</button>
  <button class="chip" type="button" aria-pressed="false" data-f="TOTEM">Totem</button>
  <button class="chip" type="button" aria-pressed="false" data-f="DUO">Duo</button>
  <button class="switch" type="button" aria-pressed="false" id="lights">Switch all lights on</button>
</div></nav>
<main class="wrap">{''.join(body)}</main>
<footer class="wrap foot">
  <p>Renders of the print-ready models, PLA, 2700 K light. Overhang is the wall's tilt from vertical (99th percentile); the tick marks the 50° limit. Filament and print time assume a 1.0 mm wall, 0.24 mm layers and 40 mm/s.</p>
  <p>Export: <code>python3 concepts.py werk-gewinde --res fine</code>. Stacks: print each module separately and plug them together. Prices are suggestions; stack prices include a base with electrics.</p>
</footer>
<script>
(function () {{
  var lit = false, btn = document.getElementById('lights');
  btn.addEventListener('click', function () {{ lit = !lit; document.body.classList.toggle('lit', lit);
    btn.setAttribute('aria-pressed', lit); btn.textContent = lit ? 'Switch all lights off' : 'Switch all lights on';
    document.querySelectorAll('.card.flip').forEach(function (c) {{ c.classList.remove('flip'); }}); }});
  document.querySelectorAll('.card').forEach(function (c) {{
    function t() {{ c.classList.toggle('flip'); }}
    c.addEventListener('click', t);
    c.addEventListener('keydown', function (e) {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); t(); }} }});
  }});
  var chips = document.querySelectorAll('.chip');
  chips.forEach(function (ch) {{ ch.addEventListener('click', function () {{
    var f = ch.getAttribute('data-f');
    chips.forEach(function (x) {{ x.setAttribute('aria-pressed', x === ch); }});
    document.querySelectorAll('[data-section]').forEach(function (s) {{ s.hidden = !(f === 'all' || s.getAttribute('data-section') === f); }});
  }}); }});
}})();
</script>
"""
    with open(os.path.join(HERE, "catalog.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote catalog.html,", n_total, "entries")


if __name__ == "__main__":
    main()
