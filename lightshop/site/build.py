#!/usr/bin/env python3
"""Build the Schichtlicht draft shop into ./public.

    python3 build.py              # production build: pretty URLs, linked CSS
    python3 build.py --artifact   # preview build: explicit index.html links, inlined CSS

Also writes public/sitemap.xml, public/robots.txt and shopify/products.csv
(Shopify product import format).
"""
import csv
import html
import json
import math
import os
import shutil
import sys

from content import (ARTICLES, BRAND, CARE, COLOURS, FAQ, IN_BOX, PAGES, PRODUCTS, SLUGS, UI)

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("OUT_DIR") or os.path.join(ROOT, "public")
ARTIFACT = "--artifact" in sys.argv
LANGS = ("de", "en")
HTML_LANG = {"de": "de-CH", "en": "en"}
FONTS = ("https://fonts.googleapis.com/css2?family=Gloock&family=Hanken+Grotesk:wght@400;500;600"
         "&family=IBM+Plex+Mono:wght@400;500&display=swap")
CSS = open(os.path.join(ROOT, "assets", "site.css"), encoding="utf-8").read()
E = html.escape
VIEWPORT_META = '\n<meta name="claude:viewport-fit-sides" content="cover">' if ARTIFACT else ""


# ---------------------------------------------------------------- paths

def path_for(page, lang, *rest):
    """Site path without leading slash, ending in '/' (or '' for the root)."""
    parts = [] if lang == "de" else ["en"]
    slug = SLUGS[page][lang] if page in SLUGS else page
    if slug:
        parts.append(slug)
    parts.extend(rest)
    return "/".join(parts) + "/" if parts else ""


def product_path(p, lang):
    return path_for("shop", lang, p["slug"])


def article_path(a, lang):
    return path_for("journal", lang, a["slug"][lang])


def rel(src, dst):
    """Relative link from page at src to page at dst (both site paths)."""
    depth = src.count("/")
    target = "../" * depth + dst
    if ARTIFACT:
        target += "index.html"
    return target or "./"


def asset(src, name):
    return "../" * src.count("/") + "assets/" + name


def absolute(path):
    return BRAND["domain"] + "/" + path


# ---------------------------------------------------------------- lamp art

def profile(shape):
    """Return (segments, extras). Each segment: (list of (y, r), material)."""
    if shape == "aare":
        pts = [(y, 82 + 10 * math.sin((y - 70) / 360 * math.pi) + 4 * math.sin(y / 9)) for y in range(70, 431, 3)]
        return [(pts, "shade")], {"base": (430, 70), "ribs": True}
    if shape == "foehn":
        cap = [(y, 150 * math.sqrt(max(0, 1 - ((230 - y) / 110) ** 2))) for y in range(120, 231, 3)]
        stem = [(y, 34 + (y - 232) * .07) for y in range(232, 441, 4)]
        return [(cap, "shade"), (stem, "shade")], {"base": (440, 60)}
    if shape == "firn":
        dome = [(y, 18 + 152 * math.sin(min(1, (y - 150) / 175) * math.pi / 2) ** 1.4) for y in range(150, 331, 3)]
        return [(dome, "shade")], {"cable": (0, 150), "bulb": 300}
    if shape == "grat":
        crown_r = [70, 112, 88, 124, 96, 116, 84]
        crown = []
        for i in range(len(crown_r) - 1):
            for t in range(0, 10):
                y = 70 + (i + t / 10) * 38
                crown.append((y, crown_r[i] + (crown_r[i + 1] - crown_r[i]) * t / 10))
        base = [(298, 90), (330, 112), (370, 84), (410, 104), (450, 92)]
        return [(crown, "shade"), (base, "solid")], {"base": (450, 92)}
    if shape == "nebel":
        segs = []
        for i in range(4):
            top, bot = 24 + i * 102, 24 + i * 102 + 98
            segs.append(([(y, 46 + 5 * math.sin((y - top) / 98 * math.pi)) for y in range(top, bot + 1, 3)], "shade"))
        return segs, {"base": (446, 78), "stand": True}
    if shape == "glut":
        egg = [(y, 92 * math.sqrt(max(0, 1 - ((y - 300) / 140) ** 2)) * (1 - .12 * (300 - y) / 140)) for y in range(162, 441, 3)]
        return [(egg, "shade")], {"base": (440, 64)}
    raise ValueError(shape)


TONES = {  # (lit centre, edge, layer line opacity, glow strength)
    "frost": ("#fff6e2", "#e9d6b4", .20, .85),
    "sand": ("#f6dcae", "#cfa66b", .22, .7),
    "stein": ("#dedbd2", "#9c9b94", .22, .45),
    "nacht": ("#52627c", "#1f2a3b", .30, .5),
}


def lamp_svg(shape, colour):
    centre, edge, line_op, glow = TONES[colour]
    cx = 200
    segs, extra = profile(shape)
    uid = f"{shape}-{colour}"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500" role="img" aria-label="{shape}">',
           "<defs>",
           f'<radialGradient id="g-{uid}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffb347" stop-opacity="{glow * .55}"/>'
           f'<stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>',
           f'<linearGradient id="s-{uid}" x1="0" x2="1"><stop offset="0" stop-color="{edge}"/><stop offset=".45" stop-color="{centre}"/>'
           f'<stop offset=".6" stop-color="{centre}"/><stop offset="1" stop-color="{edge}"/></linearGradient>',
           f'<linearGradient id="d-{uid}" x1="0" x2="1"><stop offset="0" stop-color="#20262b"/><stop offset=".5" stop-color="#3a4248"/><stop offset="1" stop-color="#1a1f23"/></linearGradient>',
           f'<pattern id="l-{uid}" width="8" height="4" patternUnits="userSpaceOnUse"><rect width="8" height="1" fill="#000" fill-opacity="{line_op}"/></pattern>',
           f'<pattern id="r-{uid}" width="14" height="8" patternUnits="userSpaceOnUse"><rect width="5" height="8" fill="#000" fill-opacity=".07"/></pattern>',
           "</defs>"]
    ys = [y for pts, _ in segs for y, _ in pts]
    gy = (min(ys) + max(ys)) / 2
    out.append(f'<ellipse cx="{cx}" cy="{gy:.0f}" rx="190" ry="{(max(ys) - min(ys)) / 2 + 60:.0f}" fill="url(#g-{uid})"/>')
    if "base" in extra:
        by, br = extra["base"]
        out.append(f'<ellipse cx="{cx}" cy="{by + 8}" rx="{br + 40}" ry="9" fill="#000" fill-opacity=".12"/>')
    if extra.get("cable"):
        a, b = extra["cable"]
        out.append(f'<rect x="{cx - 1.5}" y="{a}" width="3" height="{b - a}" fill="#2a2f33"/>')
    if extra.get("stand"):
        out.append(f'<rect x="{cx - 4}" y="20" width="8" height="430" fill="#9aa0a4"/>')
        out.append(f'<rect x="{cx - 78}" y="440" width="156" height="12" rx="6" fill="#2a2f33"/>')
    if extra.get("bulb"):
        out.append(f'<circle cx="{cx}" cy="{extra["bulb"]}" r="26" fill="#fff4d6" fill-opacity=".9"/>')
    for pts, mat in segs:
        right = " ".join(f"{cx + r:.1f},{y:.1f}" for y, r in pts)
        left = " ".join(f"{cx - r:.1f},{y:.1f}" for y, r in reversed(pts))
        poly = f"{right} {left}"
        fill = f"url(#d-{uid})" if mat == "solid" else f"url(#s-{uid})"
        out.append(f'<polygon points="{poly}" fill="{fill}"/>')
        if extra.get("ribs") and mat == "shade":
            out.append(f'<polygon points="{poly}" fill="url(#r-{uid})"/>')
        out.append(f'<polygon points="{poly}" fill="url(#l-{uid})"/>')
    out.append("</svg>")
    return "\n".join(out)


def write_art():
    d = os.path.join(OUT, "assets", "img")
    os.makedirs(d, exist_ok=True)
    for p in PRODUCTS:
        for c in p["colours"]:
            with open(os.path.join(d, f'{p["slug"]}-{c}.svg'), "w", encoding="utf-8") as f:
                f.write(lamp_svg(p["shape"], c))


def img(src_path, p, lang, colour=None, eager=False):
    colour = colour or p["colours"][0]
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    alt = f'{p["name"]} {p["type"][lang]}, {COLOURS[colour][lang]}'
    return (f'<img src="{asset(src_path, "img/" + p["slug"] + "-" + colour + ".svg")}" width="400" height="500" '
            f'alt="{E(alt)}" {loading}>')


# ---------------------------------------------------------------- layout

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def org_ld():
    return {"@context": "https://schema.org", "@type": "Organization", "@id": BRAND["domain"] + "/#org",
            "name": BRAND["name"], "url": BRAND["domain"] + "/", "email": BRAND["email"],
            "logo": BRAND["domain"] + "/assets/logo.svg",
            "address": {"@type": "PostalAddress", "addressLocality": BRAND["city"], "addressCountry": BRAND["country"]},
            "sameAs": [BRAND["instagram"], BRAND["pinterest"], BRAND["tiktok"]]}


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": absolute(p)} for i, (n, p) in enumerate(items)]}


def crumbs_html(src, items):
    lis = []
    for i, (name, p) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f'<li aria-current="page">{E(name)}</li>')
        else:
            lis.append(f'<li><a href="{rel(src, p)}">{E(name)}</a></li>')
    return f'<nav class="crumbs wrap" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'


def header(src, lang, alt_path, current):
    t = UI[lang]
    nav = [("shop", t["nav_shop"]), ("cordless", t["nav_cordless"]), ("b2b", t["nav_b2b"]),
           ("about", t["nav_about"]), ("journal", t["nav_journal"])]
    links = "".join(
        f'<a href="{rel(src, path_for(k, lang))}"{" aria-current=page" if k == current else ""}>{E(label)}</a>'
        for k, label in nav)
    other = "en" if lang == "de" else "de"
    return f'''<a class="skip" href="#main">{t["skip"]}</a>
<header class="site-head"><div class="wrap">
<a class="logo" href="{rel(src, path_for("home", lang))}">Schicht<span>licht</span></a>
<nav class="nav" aria-label="Main">{links}</nav>
<div class="head-tools"><a href="{rel(src, alt_path)}" hreflang="{HTML_LANG[other]}" lang="{HTML_LANG[other]}">{other.upper()}</a>
<a href="#" data-cart>{t["cart"]}<span class="cart-count" data-count>0</span></a></div>
</div></header>'''


def footer(src, lang):
    t = UI[lang]
    short = {"faq": t["faq_h"], "b2b": t["nav_b2b"], "about": t["nav_about"]}
    col = lambda keys: "".join(f'<li><a href="{rel(src, path_for(k, lang))}">{E(short.get(k) or PAGES[k]["h1"][lang])}</a></li>' for k in keys)
    shop = "".join(f'<li><a href="{rel(src, product_path(p, lang))}">{E(p["name"])}</a></li>' for p in PRODUCTS[:4])
    return f'''<footer class="site-foot"><div class="wrap">
<div class="foot-news"><p class="logo">Schicht<span>licht</span></p><p>{t["footer_tag"]}</p>
<h2>{t["newsletter_h"]}</h2>
<form class="inline-form" data-form novalidate><label class="skip" for="nl-email">{t["email"]}</label>
<input id="nl-email" type="email" name="email" placeholder="{t["email"]}" required autocomplete="email"><button class="btn" type="submit">{t["subscribe"]}</button></form>
<p class="form-msg" data-msg aria-live="polite"></p></div>
<div><h2>{t["shop"]}</h2><ul>{shop}<li><a href="{rel(src, path_for("shop", lang))}">{t["all_lamps"]}</a></li></ul></div>
<div><h2>{t["help"]}</h2><ul>{col(["faq", "shipping", "b2b", "about"])}</ul></div>
<div><h2>{t["legal"]}</h2><ul>{col(["imprint", "privacy", "terms"])}</ul>
<h2 style="margin-top:1.5rem">{t["follow"]}</h2><ul><li><a href="{BRAND["instagram"]}" rel="noopener">Instagram</a></li><li><a href="{BRAND["pinterest"]}" rel="noopener">Pinterest</a></li><li><a href="{BRAND["tiktok"]}" rel="noopener">TikTok</a></li></ul></div>
<div class="fineprint"><span>© 2026 {BRAND["name"]} · {t["vat_note"]}</span><span>{t["made"]}</span></div>
</div></footer>'''


JS = """<script>
(function(){
  var count=0, toast;
  function say(msg){ if(!toast){toast=document.createElement('div');toast.className='toast';toast.setAttribute('role','status');document.body.appendChild(toast);}
    toast.textContent=msg; toast.hidden=false; clearTimeout(say.t); say.t=setTimeout(function(){toast.hidden=true;},4000); }
  document.querySelectorAll('[data-add]').forEach(function(b){ b.addEventListener('click',function(){ count++;
    document.querySelectorAll('[data-count]').forEach(function(c){c.textContent=count;}); say(b.getAttribute('data-note')); }); });
  document.querySelectorAll('[data-cart]').forEach(function(a){ a.addEventListener('click',function(e){ e.preventDefault(); say(document.documentElement.lang.indexOf('de')===0?'Vorschau: Der Warenkorb folgt mit Shopify.':'Preview: the cart arrives with Shopify.'); }); });
  document.querySelectorAll('[data-form]').forEach(function(f){ f.addEventListener('submit',function(e){ e.preventDefault();
    var m=f.parentNode.querySelector('[data-msg]'); var email=f.querySelector('input[type=email]');
    if(email && !email.checkValidity()){ if(m) m.textContent=email.validationMessage; email.focus(); return; }
    if(m) m.textContent=f.getAttribute('data-ok')||document.body.getAttribute('data-ok'); f.reset(); }); });
  document.querySelectorAll('[data-swatch]').forEach(function(r){ r.addEventListener('change',function(){
    var im=document.querySelector('[data-hero-img]'); if(im){ im.src=im.src.replace(/-[a-z]+\\.svg$/, '-'+r.value+'.svg'); } }); });
})();
</script>"""


def page(src, lang, title, desc, body, alt_path, current=None, lds=(), og_image=None, bare=False):
    t = UI[lang]
    alt_de = src if lang == "de" else alt_path
    alt_en = src if lang == "en" else alt_path
    style = f"<style>{CSS}</style>" if ARTIFACT else f'<link rel="stylesheet" href="{asset(src, "site.css")}">'
    og_image = og_image or absolute("assets/img/aare-frost.svg")
    head = f'''<title>{E(title)}</title>{VIEWPORT_META}
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{absolute(src)}">
<link rel="alternate" hreflang="de-CH" href="{absolute(alt_de)}">
<link rel="alternate" hreflang="en" href="{absolute(alt_en)}">
<link rel="alternate" hreflang="x-default" href="{absolute(alt_de)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND["name"]}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{absolute(src)}"><meta property="og:image" content="{og_image}">
<meta property="og:locale" content="{"de_CH" if lang == "de" else "en_GB"}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#eceeea" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#111416" media="(prefers-color-scheme: dark)">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
{style}
{"".join(ld(x) for x in lds)}'''
    content = f'''{header(src, lang, alt_path, current)}
<main id="main">{body}</main>
{footer(src, lang)}
{JS}'''
    if bare:
        return f'{head}\n<div data-ok="{E(t["subscribed"])}" lang="{HTML_LANG[lang]}">{content}</div>'.replace(
            "document.body.getAttribute('data-ok')", "document.querySelector('[data-ok]').getAttribute('data-ok')")
    return f'''<!doctype html>
<html lang="{HTML_LANG[lang]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head}
</head>
<body data-ok="{E(t["subscribed"])}">
{content}
</body>
</html>
'''


def write(path, text):
    full = os.path.join(OUT, path, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------- pieces

def chf(n):
    return f"CHF {n:,}".replace(",", "'")


def card(src, p, lang):
    return f'''<a class="card" href="{rel(src, product_path(p, lang))}">
<div class="card-art">{img(src, p, lang)}</div>
<div class="card-meta"><h3>{E(p["name"])}</h3><span class="price">{chf(p["price"])}</span></div>
<p class="type">{E(p["type"][lang])} · {E(p["tagline"][lang])}</p></a>'''


def grid(src, lang, items):
    return '<div class="grid">' + "".join(card(src, p, lang) for p in items) + "</div>"


def itemlist_ld(lang, items):
    return {"@context": "https://schema.org", "@type": "ItemList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": absolute(product_path(p, lang)), "name": p["name"]}
                                for i, p in enumerate(items)]}


def faq_ld(pairs):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}


def details(pairs):
    return '<div class="qa">' + "".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in pairs) + "</div>"


def blocks(items):
    out = []
    for kind, val in items:
        if kind == "ul":
            out.append("<ul>" + "".join(f"<li>{E(x)}</li>" for x in val) + "</ul>")
        else:
            out.append(f"<{kind}>{E(val)}</{kind}>")
    return "".join(out)


def layers(p):
    return round(p["height"] / BRAND["layer_mm"])


def fmt_int(n, lang):
    return f"{n:,}".replace(",", "'" if lang == "de" else ",")


# ---------------------------------------------------------------- pages

def build_home(lang):
    src = path_for("home", lang)
    alt = path_for("home", "en" if lang == "de" else "de")
    c = PAGES["home"]
    t = UI[lang]
    hero_p = PRODUCTS[0]
    steps = "".join(f"<li><h3>{E(h)}</h3><p>{E(x)}</p></li>" for h, x in c["steps"][lang])
    posts = "".join(post_card(src, a, lang) for a in ARTICLES)
    body = f'''<section class="hero"><div class="wrap">
<div class="hero-copy"><p class="eyebrow">{t["made"]}</p><h1>{E(c["hero_h"][lang])}</h1><p class="lead">{E(c["hero_p"][lang])}</p>
<div class="row"><a class="btn" href="{rel(src, path_for("shop", lang))}">{E(c["cta"][lang])}</a>
<a class="btn ghost" href="{rel(src, path_for("b2b", lang))}">{E(t["nav_b2b"])}</a></div>
<p class="specline"><span><b>{fmt_int(layers(hero_p), lang)}</b> {t["layers"]} · {E(hero_p["name"])}</span><span><b>0.24 mm</b> {t["layer_height"]}</span><span><b>2700 K</b></span><span><b>{chf(PRODUCTS[-1]["price"])}–{chf(PRODUCTS[4]["price"])}</b></span></p></div>
<div class="hero-art"><a href="{rel(src, product_path(hero_p, lang))}">{img(src, hero_p, lang, eager=True)}</a></div>
</div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{t["all_lamps"]}</h2><a href="{rel(src, path_for("shop", lang))}">{t["view"]} →</a></div>
{grid(src, lang, PRODUCTS[:3])}</div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{E(c["how_h"][lang])}</h2></div><ol class="steps">{steps}</ol></div></section>
<section class="band"><div class="wrap"><div><h2>{E(c["b2b_h"][lang])}</h2><p>{E(c["b2b_p"][lang])}</p></div>
<a class="btn" href="{rel(src, path_for("b2b", lang))}">{t["view"]} →</a></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{t["nav_journal"]}</h2></div><div class="posts">{posts}</div></div></section>'''
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND["name"], "url": absolute(src), "inLanguage": HTML_LANG[lang],
            "publisher": {"@id": BRAND["domain"] + "/#org"}}
    write(src, page(src, lang, c["title"][lang], c["desc"][lang], body, alt, None,
                    [org_ld(), site, itemlist_ld(lang, PRODUCTS)], bare=ARTIFACT and lang == "de"))


def build_listing(key, lang, items, extra=""):
    src = path_for(key, lang)
    alt = path_for(key, "en" if lang == "de" else "de")
    c = PAGES[key]
    t = UI[lang]
    trail = [(t["breadcrumb_home"], path_for("home", lang)), (c["h1"][lang], src)]
    body = f'''{crumbs_html(src, trail)}
<section class="section"><div class="wrap"><div class="section-head"><div class="prose"><h1>{E(c["h1"][lang])}</h1><p class="lead">{E(c["intro"][lang])}</p></div></div>
{grid(src, lang, items)}</div></section>{extra}'''
    lds = [crumbs_ld(trail), itemlist_ld(lang, items)]
    if key == "cordless":
        lds.append(faq_ld(c["points"][lang]))
    write(src, page(src, lang, c["title"][lang] + " | " + BRAND["name"], c["desc"][lang], body, alt, key, lds))


def build_product(p, lang):
    src = product_path(p, lang)
    alt = product_path(p, "en" if lang == "de" else "de")
    t = UI[lang]
    trail = [(t["breadcrumb_home"], path_for("home", lang)), (PAGES["shop"]["h1"][lang], path_for("shop", lang)), (p["name"], src)]
    swatches = "".join(
        f'<span class="swatch"><input type="radio" name="colour" id="c-{c}" value="{c}" data-swatch{" checked" if i == 0 else ""}>'
        f'<label for="c-{c}"><i style="background:{COLOURS[c]["hex"]}"></i>{E(COLOURS[c][lang])}</label></span>'
        for i, c in enumerate(p["colours"]))
    size_row = (f'<tr><th>{t["height"]}</th><td>{p["height"] / 10:g} cm</td></tr>'
                f'<tr><th>{t["diameter"]}</th><td>{p["diameter"] / 10:g} cm</td></tr>')
    specs = f'''<table class="specs"><tbody>{size_row}
<tr><th>{t["weight"]}</th><td>{p["weight"]:g} kg</td></tr>
<tr><th>{t["layers"]}</th><td>{fmt_int(layers(p), lang)} × {BRAND["layer_mm"]} mm</td></tr>
<tr><th>{t["print_time"]}</th><td>{p["print_h"]} h</td></tr>
<tr><th>{t["material"]}</th><td>{E(p["material"][lang])}</td></tr>
<tr><th>{t["light"]}</th><td>{E(p["light"][lang])}</td></tr>
<tr><th>{t["power"]}</th><td>{E(p["power"][lang])}</td></tr>
<tr><th>{t["cable"]}</th><td>{E(p["cable"][lang])}</td></tr></tbody></table>'''
    in_box = "<ul>" + "".join(f"<li>{E(x)}</li>" for x in IN_BOX[lang]) + "</ul>"
    related = [x for x in PRODUCTS if x is not p][:3]
    body = f'''{crumbs_html(src, trail)}
<div class="wrap pdp">
<div class="pdp-art">{img(src, p, lang, eager=True).replace("<img ", "<img data-hero-img ")}</div>
<div class="pdp-info">
<div><p class="eyebrow">{E(p["type"][lang])}</p><h1>{E(p["name"])}</h1></div>
<p class="lead">{E(p["tagline"][lang])}</p>
<p class="pdp-price">{chf(p["price"])}</p>
<fieldset class="swatches"><legend>{t["colour"]}</legend>{swatches}</fieldset>
<div class="row"><button class="btn" type="button" data-add data-note="{E(t["preview_note"])}">{t["add"]}</button></div>
<ul class="promises"><li>{t["made"]}</li><li>{t["ship"]}</li><li>{t["return"]}</li><li>{t["warranty"]}</li></ul>
<div class="prose">{"".join(f"<p>{E(x)}</p>" for x in p["body"][lang])}</div>
<details open><summary>{t["specs"]}</summary>{specs}</details>
<details><summary>{t["in_box"]}</summary>{in_box}</details>
<details><summary>{t["care"]}</summary><p>{E(CARE[lang])}</p></details>
</div></div>
<section class="section"><div class="wrap"><div class="section-head"><h2>{t["related"]}</h2></div>{grid(src, lang, related)}</div></section>'''
    image_urls = [absolute(f'assets/img/{p["slug"]}-{c}.svg') for c in p["colours"]]
    product = {
        "@context": "https://schema.org", "@type": "Product", "name": f'{p["name"]} {p["type"][lang]}',
        "description": p["seo_desc"][lang], "sku": f'SL-{p["slug"].upper()}', "image": image_urls,
        "brand": {"@type": "Brand", "name": BRAND["name"]}, "material": p["material"][lang],
        "color": [COLOURS[c][lang] for c in p["colours"]],
        "height": {"@type": "QuantitativeValue", "value": p["height"] / 10, "unitCode": "CMT"},
        "width": {"@type": "QuantitativeValue", "value": p["diameter"] / 10, "unitCode": "CMT"},
        "weight": {"@type": "QuantitativeValue", "value": p["weight"], "unitCode": "KGM"},
        "countryOfOrigin": "CH",
        "additionalProperty": [{"@type": "PropertyValue", "name": t["layers"], "value": layers(p)}],
        "offers": {
            "@type": "Offer", "url": absolute(src), "priceCurrency": "CHF", "price": f'{p["price"]}.00',
            "availability": "https://schema.org/InStock", "itemCondition": "https://schema.org/NewCondition",
            "seller": {"@id": BRAND["domain"] + "/#org"},
            "shippingDetails": {"@type": "OfferShippingDetails",
                                "shippingRate": {"@type": "MonetaryAmount", "value": 0 if p["price"] >= 120 else 8, "currency": "CHF"},
                                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": ["CH", "LI"]},
                                "deliveryTime": {"@type": "ShippingDeliveryTime",
                                                 "handlingTime": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 2, "unitCode": "DAY"},
                                                 "transitTime": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 3, "unitCode": "DAY"}}},
            "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": ["CH", "LI"],
                                        "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                                        "merchantReturnDays": 30, "returnMethod": "https://schema.org/ReturnByMail",
                                        "returnFees": "https://schema.org/FreeReturn"},
        },
    }
    write(src, page(src, lang, p["seo_title"][lang] + " | " + BRAND["name"], p["seo_desc"][lang], body, alt, "shop",
                    [crumbs_ld(trail), product], og_image=image_urls[0]))


def post_card(src, a, lang):
    t = UI[lang]
    return f'''<a class="post" href="{rel(src, article_path(a, lang))}"><p class="eyebrow">{a["minutes"]} {t["min"]}</p>
<h3>{E(a["title"][lang])}</h3><p>{E(a["desc"][lang])}</p></a>'''


def build_journal(lang):
    src = path_for("journal", lang)
    alt = path_for("journal", "en" if lang == "de" else "de")
    c = PAGES["journal"]
    t = UI[lang]
    trail = [(t["breadcrumb_home"], path_for("home", lang)), (c["h1"][lang], src)]
    body = f'''{crumbs_html(src, trail)}<section class="section"><div class="wrap"><div class="section-head"><h1>{c["h1"][lang]}</h1></div>
<div class="posts">{"".join(post_card(src, a, lang) for a in ARTICLES)}</div></div></section>'''
    write(src, page(src, lang, c["title"][lang] + " | " + BRAND["name"], c["desc"][lang], body, alt, "journal", [crumbs_ld(trail)]))
    for a in ARTICLES:
        asrc = article_path(a, lang)
        aalt = article_path(a, "en" if lang == "de" else "de")
        atrail = trail + [(a["title"][lang], asrc)]
        abody = f'''{crumbs_html(asrc, atrail)}<article class="wrap article"><header class="prose"><p class="eyebrow"><time datetime="{a["date"]}">{a["date"]}</time> · {a["minutes"]} {t["min"]}</p>
<h1>{E(a["title"][lang])}</h1><p class="lead">{E(a["desc"][lang])}</p></header>
<div class="prose">{blocks(a["body"][lang])}</div>
<p class="row"><a class="btn" href="{rel(asrc, path_for("shop", lang))}">{t["all_lamps"]} →</a></p></article>'''
        art = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"][lang], "description": a["desc"][lang],
               "datePublished": a["date"], "dateModified": a["date"], "inLanguage": HTML_LANG[lang],
               "author": {"@id": BRAND["domain"] + "/#org"}, "publisher": {"@id": BRAND["domain"] + "/#org"},
               "mainEntityOfPage": absolute(asrc), "image": absolute("assets/img/aare-frost.svg")}
        write(asrc, page(asrc, lang, a["title"][lang], a["desc"][lang], abody, aalt, "journal", [crumbs_ld(atrail), art]))


def build_text(key, lang, inner, lds_extra=()):
    src = path_for(key, lang)
    alt = path_for(key, "en" if lang == "de" else "de")
    c = PAGES[key]
    t = UI[lang]
    trail = [(t["breadcrumb_home"], path_for("home", lang)), (c["h1"][lang], src)]
    body = f'''{crumbs_html(src, trail)}<section class="section"><div class="wrap" style="display:grid;gap:2.5rem">{inner}</div></section>'''
    write(src, page(src, lang, c["title"][lang] + " | " + BRAND["name"], c["desc"][lang], body, alt, key, [crumbs_ld(trail), *lds_extra]))


def build_b2b(lang):
    c = PAGES["b2b"]
    t = UI[lang]
    offers = "".join(f"<div><h3>{E(h)}</h3><p>{E(x)}</p></div>" for h, x in c["offers"][lang])
    L = {"de": ("Name", "Betrieb", "E-Mail", "Anzahl Lampen", "Worum geht es?", "Anfrage senden", "Danke. In dieser Vorschau wird noch nichts gesendet."),
         "en": ("Name", "Business", "Email", "Number of lamps", "What is the project?", "Send request", "Thank you. This preview does not send anything yet.")}[lang]
    form = f'''<form class="form" data-form data-ok="{E(L[6])}" novalidate>
<label for="b-name">{L[0]}<input id="b-name" name="name" autocomplete="name"></label>
<label for="b-biz">{L[1]}<input id="b-biz" name="business" autocomplete="organization"></label>
<label for="b-email">{L[2]}<input id="b-email" type="email" name="email" required autocomplete="email"></label>
<label for="b-qty">{L[3]}<select id="b-qty" name="qty"><option>10–24</option><option>25–49</option><option>50+</option></select></label>
<label for="b-msg">{L[4]}<textarea id="b-msg" name="message" rows="4"></textarea></label>
<button class="btn" type="submit">{L[5]}</button></form><p class="form-msg" data-msg aria-live="polite"></p>'''
    inner = f'''<div class="prose"><h1>{E(c["h1"][lang])}</h1><p class="lead">{E(c["intro"][lang])}</p></div>
<div class="offers">{offers}</div>
{grid(path_for("b2b", lang), lang, [PRODUCTS[2], PRODUCTS[1], PRODUCTS[0]])}
<div><h2>{E(c["form_h"][lang])}</h2></div><div>{form}</div>'''
    build_text("b2b", lang, inner)


def build_simple(key, lang):
    c = PAGES[key]
    inner = f'<div class="prose"><h1>{E(c["h1"][lang])}</h1>'
    if key == "about":
        inner += "".join(f"<p>{E(x)}</p>" for x in c["body"][lang])
    else:
        inner += blocks(c["body"][lang])
    inner += "</div>"
    build_text(key, lang, inner)


def build_faq(lang):
    c = PAGES["faq"]
    inner = f'<div class="prose"><h1>{E(c["h1"][lang])}</h1></div>{details(FAQ[lang])}'
    build_text("faq", lang, inner, [faq_ld(FAQ[lang])])


def build_404():
    body = f'''<section class="section"><div class="wrap prose"><h1>404</h1><p class="lead">Diese Seite gibt es nicht (mehr). / This page does not exist.</p>
<p class="row"><a class="btn" href="/">Start</a><a class="btn ghost" href="/en/">Home</a></p></div></section>'''
    html_ = page("", "de", "404 | " + BRAND["name"], "Seite nicht gefunden.", body, "en/")
    html_ = html_.replace('<link rel="canonical"', '<meta name="robots" content="noindex"><link rel="x-canonical"')
    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8") as f:
        f.write(html_)


# ---------------------------------------------------------------- sitemap, robots, shopify

def all_pairs():
    pairs = [(path_for(k, "de"), path_for(k, "en")) for k in ("home", "shop", "cordless", "b2b", "about", "journal", "faq", "shipping", "imprint", "privacy", "terms")]
    pairs += [(product_path(p, "de"), product_path(p, "en")) for p in PRODUCTS]
    pairs += [(article_path(a, "de"), article_path(a, "en")) for a in ARTICLES]
    return pairs


def build_sitemap():
    rows = []
    for de, en in all_pairs():
        for loc in (de, en):
            rows.append(f'''<url><loc>{absolute(loc)}</loc><lastmod>2026-10-28</lastmod>
<xhtml:link rel="alternate" hreflang="de-CH" href="{absolute(de)}"/><xhtml:link rel="alternate" hreflang="en" href="{absolute(en)}"/>
<xhtml:link rel="alternate" hreflang="x-default" href="{absolute(de)}"/></url>''')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BRAND['domain']}/sitemap.xml\n")


def build_shopify_csv():
    d = os.path.join(ROOT, "shopify")
    os.makedirs(d, exist_ok=True)
    cols = ["Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags", "Published",
            "Option1 Name", "Option1 Value", "Variant SKU", "Variant Grams", "Variant Inventory Tracker",
            "Variant Inventory Policy", "Variant Fulfillment Service", "Variant Price", "Variant Requires Shipping",
            "Variant Taxable", "Image Src", "Image Position", "Image Alt Text", "SEO Title", "SEO Description", "Status"]
    with open(os.path.join(d, "products.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for p in PRODUCTS:
            body = "".join(f"<p>{E(x)}</p>" for x in p["body"]["de"])
            tags = ", ".join(["3D-Druck", "Made in Switzerland", p["type"]["de"]] + (["kabellos", "Akku"] if p["cordless"] else []))
            for i, c in enumerate(p["colours"]):
                first = i == 0
                w.writerow([
                    p["slug"], p["name"] if first else "", body if first else "", BRAND["name"] if first else "",
                    "Home & Garden > Lighting > Lamps" if first else "", p["type"]["de"] if first else "", tags if first else "",
                    "TRUE" if first else "", "Farbe" if first else "", COLOURS[c]["de"], f'SL-{p["slug"].upper()}-{c.upper()}',
                    int(p["weight"] * 1000), "shopify", "continue", "manual", f'{p["price"]}.00', "TRUE", "TRUE",
                    f'{BRAND["domain"]}/assets/img/{p["slug"]}-{c}.svg', i + 1, f'{p["name"]} {COLOURS[c]["de"]}',
                    p["seo_title"]["de"] if first else "", p["seo_desc"]["de"] if first else "", "draft" if first else ""])


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"))
    shutil.copy(os.path.join(ROOT, "assets", "site.css"), os.path.join(OUT, "assets", "site.css"))
    with open(os.path.join(OUT, "assets", "logo.svg"), "w", encoding="utf-8") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#1b2124"/>'
                + "".join(f'<rect x="16" y="{14 + i * 4}" width="32" height="2" fill="#f0a640" fill-opacity="{.35 + i * .06:.2f}"/>' for i in range(10))
                + "</svg>")
    write_art()
    for lang in LANGS:
        build_home(lang)
        build_listing("shop", lang, PRODUCTS)
        cordless_extra = (f'<section class="section"><div class="wrap"><div class="section-head"><h2>{UI[lang]["faq_h"]}</h2></div>'
                          f'{details(PAGES["cordless"]["points"][lang])}</div></section>')
        build_listing("cordless", lang, [p for p in PRODUCTS if p["cordless"]], cordless_extra)
        for p in PRODUCTS:
            build_product(p, lang)
        build_journal(lang)
        build_b2b(lang)
        build_faq(lang)
        for key in ("about", "shipping", "imprint", "privacy", "terms"):
            build_simple(key, lang)
    build_404()
    build_sitemap()
    build_shopify_csv()
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"Built {n} files into {OUT}{' (artifact mode)' if ARTIFACT else ''}")


if __name__ == "__main__":
    main()
