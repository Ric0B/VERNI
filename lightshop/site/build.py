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


# ---------------------------------------------------------------- images
# Renders come from ../design (lampgen.py + the three.js renderer): one image
# per colour switched off, plus one switched on in the first colour.

def render_name(p, colour=None, on=False):
    colour = colour or p["colours"][0]
    return f'{p["slug"]}-{colour}{"-on" if on else ""}'


def img(src_path, p, lang, colour=None, on=False, eager=False, small=True, extra=""):
    colour = colour or p["colours"][0]
    name = render_name(p, colour, on)
    alt = f'{p["name"]} {p["type"][lang]}, {COLOURS[colour][lang]}' + ((", eingeschaltet" if lang == "de" else ", switched on") if on else "")
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    big = asset(src_path, f"renders/{name}.jpg")
    sm = asset(src_path, f"renders/{name}-600.jpg")
    srcset = f'srcset="{sm} 600w, {big} 1200w" sizes="(max-width: 40rem) 100vw, {"33vw" if small else "50vw"}"'
    return f'<img src="{sm if small else big}" {srcset} width="1200" height="1500" alt="{E(alt)}" {loading} {extra}>'


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
    nav = [("shop", t["nav_shop"]), ("atelier_series", t["nav_atelier"]), ("unikate", t["nav_unikate"]),
           ("b2b", t["nav_b2b"]), ("journal", t["nav_journal"])]
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
    shop = "".join(f'<li><a href="{rel(src, path_for(k, lang))}">{E(v)}</a></li>' for k, v in
                   (("shop", t["all_lamps"]), ("atelier_series", t["nav_atelier"]), ("unikate", t["nav_unikate"]), ("cordless", t["nav_cordless"])))
    return f'''<footer class="site-foot"><div class="wrap">
<div class="foot-news"><p class="logo">Schicht<span>licht</span></p><p>{t["footer_tag"]}</p>
<h2>{t["newsletter_h"]}</h2>
<form class="inline-form" data-form novalidate><label class="skip" for="nl-email">{t["email"]}</label>
<input id="nl-email" type="email" name="email" placeholder="{t["email"]}" required autocomplete="email"><button class="btn" type="submit">{t["subscribe"]}</button></form>
<p class="form-msg" data-msg aria-live="polite"></p></div>
<div><h2>{t["shop"]}</h2><ul>{shop}</ul></div>
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
  document.querySelectorAll('[data-lamp]').forEach(function(fig){
    var im=fig.querySelector('img'), base=fig.getAttribute('data-base'), colour=fig.getAttribute('data-colour'), onc=fig.getAttribute('data-oncolour');
    var btn=document.querySelector('[data-light]'), root=document.documentElement;
    var on=root.getAttribute('data-theme')==='dark' || (root.getAttribute('data-theme')!=='light' && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
    function set(){ var n=on?onc+'-on':colour; im.src=base+n+'.jpg'; im.srcset=base+n+'-600.jpg 600w, '+base+n+'.jpg 1200w';
      if(btn){ btn.setAttribute('aria-pressed',on?'true':'false'); btn.textContent=btn.getAttribute(on?'data-off':'data-on'); } }
    document.querySelectorAll('[data-swatch]').forEach(function(r){ r.addEventListener('change',function(){ colour=r.value; on=false; set(); }); });
    if(btn) btn.addEventListener('click',function(){ on=!on; set(); });
    if(on) set();
  });
})();
</script>"""


def page(src, lang, title, desc, body, alt_path, current=None, lds=(), og_image=None, bare=False):
    t = UI[lang]
    alt_de = src if lang == "de" else alt_path
    alt_en = src if lang == "en" else alt_path
    style = f"<style>{CSS}</style>" if ARTIFACT else f'<link rel="stylesheet" href="{asset(src, "site.css")}">'
    og_image = og_image or absolute("assets/renders/gletscher-frost-on.jpg")
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
    ed = p.get("edition")
    badge = f'<span class="badge">{E(ed[lang])}</span>' if ed else ""
    return f'''<a class="card" href="{rel(src, product_path(p, lang))}">
<div class="card-art">{img(src, p, lang)}{img(src, p, lang, on=True, extra='class="lit" aria-hidden="true"')}{badge}</div>
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
    return p.get("layers") or round(p["height"] / BRAND["layer_mm"])


def fmt_int(n, lang):
    return f"{n:,}".replace(",", "'" if lang == "de" else ",")


# ---------------------------------------------------------------- pages

def seed_fig(src, code, lang, eager=False):
    t = UI[lang]
    name = f"gletscher-s{code}-on"
    alt = f'Gletscher {t["code"]} {code}'
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<figure class="seed"><img src="{asset(src, "renders/" + name + "-600.jpg")}" '
            f'srcset="{asset(src, "renders/" + name + "-600.jpg")} 600w, {asset(src, "renders/" + name + ".jpg")} 1200w" '
            f'sizes="(max-width: 40rem) 100vw, 33vw" width="1200" height="1500" alt="{E(alt)}" {loading}>'
            f'<figcaption><span>{t["code"]}</span> {code:04d}</figcaption></figure>')


def core(): return [p for p in PRODUCTS if p.get("series") != "atelier"]
def atelier(): return [p for p in PRODUCTS if p.get("series") == "atelier"]


def build_home(lang):
    src = path_for("home", lang)
    alt = path_for("home", "en" if lang == "de" else "de")
    c = PAGES["home"]
    t = UI[lang]
    hero_p = next(p for p in PRODUCTS if p["slug"] == "moraene")
    steps = "".join(f"<li><h3>{E(h)}</h3><p>{E(x)}</p></li>" for h, x in c["steps"][lang])
    posts = "".join(post_card(src, a, lang) for a in ARTICLES[:3])
    seeds = "".join(seed_fig(src, code, lang) for code in PAGES["unikate"]["seeds"])
    body = f'''<section class="hero night"><div class="wrap">
<div class="hero-copy"><p class="eyebrow">{t["made"]}</p><h1>{E(c["hero_h"][lang])}</h1><p class="lead">{E(c["hero_p"][lang])}</p>
<div class="row"><a class="btn light" href="{rel(src, path_for("shop", lang))}">{E(c["cta"][lang])}</a>
<a class="btn ghost light" href="{rel(src, path_for("unikate", lang))}">{E(t["nav_unikate"])}</a></div>
<p class="specline"><span><b>{fmt_int(layers(hero_p), lang)}</b> {t["layers"]} · {E(hero_p["name"])}</span><span><b>0.24 mm</b> {t["layer_height"]}</span><span><b>2700 K</b></span></p></div>
<a class="hero-art" href="{rel(src, product_path(hero_p, lang))}">{img(src, hero_p, lang, on=True, eager=True, small=False)}</a>
</div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{t["collection"]}</h2><a href="{rel(src, path_for("shop", lang))}">{t["all_lamps"]} →</a></div>
{grid(src, lang, core())}</div></section>
<section class="section"><div class="wrap"><div class="section-head"><div class="prose"><p class="eyebrow">{t["nav_atelier"]}</p><h2>{E(c["atelier_h"][lang])}</h2><p class="lead">{E(c["atelier_p"][lang])}</p></div>
<a href="{rel(src, path_for("atelier_series", lang))}">{t["view"]} →</a></div>{grid(src, lang, atelier())}</div></section>
<section class="section night"><div class="wrap"><div class="section-head"><div class="prose"><p class="eyebrow">{t["nav_unikate"]}</p><h2>{E(c["unikat_h"][lang])}</h2><p class="lead">{E(PAGES["unikate"]["intro"][lang])}</p></div>
<a class="btn light" href="{rel(src, path_for("unikate", lang))}">{t["view"]} →</a></div><div class="seeds">{seeds}</div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{E(c["how_h"][lang])}</h2></div><ol class="steps">{steps}</ol></div></section>
<section class="band"><div class="wrap"><div><h2>{E(c["b2b_h"][lang])}</h2><p>{E(c["b2b_p"][lang])}</p></div>
<a class="btn" href="{rel(src, path_for("b2b", lang))}">{t["view"]} →</a></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{t["nav_journal"]}</h2><a href="{rel(src, path_for("journal", lang))}">{t["view"]} →</a></div><div class="posts">{posts}</div></div></section>'''
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND["name"], "url": absolute(src), "inLanguage": HTML_LANG[lang],
            "publisher": {"@id": BRAND["domain"] + "/#org"}}
    write(src, page(src, lang, c["title"][lang], c["desc"][lang], body, alt, None,
                    [org_ld(), site, itemlist_ld(lang, PRODUCTS)], og_image=absolute("assets/renders/moraene-frost-on.jpg"),
                    bare=ARTIFACT and lang == "de"))


def build_atelier(lang):
    c = PAGES["atelier_series"]
    method = "".join(f"<div><h3>{E(h)}</h3><p>{E(x)}</p></div>" for h, x in c["method"][lang])
    extra = (f'<section class="section"><div class="wrap"><div class="section-head"><h2>{E(c["method_h"][lang])}</h2></div>'
             f'<div class="offers">{method}</div></div></section>')
    build_listing("atelier_series", lang, atelier(), extra)


def build_unikate(lang):
    src = path_for("unikate", lang)
    alt = path_for("unikate", "en" if lang == "de" else "de")
    c = PAGES["unikate"]
    t = UI[lang]
    g = next(p for p in PRODUCTS if p["slug"] == "gletscher")
    trail = [(t["breadcrumb_home"], path_for("home", lang)), (c["h1"][lang], src)]
    seeds = "".join(seed_fig(src, code, lang, eager=i == 0) for i, code in enumerate(c["seeds"]))
    steps = "".join(f"<li><h3>{E(h)}</h3><p>{E(x)}</p></li>" for h, x in c["steps"][lang])
    L = {"de": ("Dein Code (eine Zahl, z. B. 14062019)", "E-Mail", "Vorschau anfragen", "Danke. In dieser Vorschau wird noch nichts gesendet."),
         "en": ("Your code (a number, e.g. 14062019)", "Email", "Request a preview", "Thank you. This preview does not send anything yet.")}[lang]
    form = f'''<form class="form" data-form data-ok="{E(L[3])}" novalidate>
<label for="u-code">{L[0]}<input id="u-code" name="code" inputmode="numeric" pattern="[0-9]*" maxlength="12"></label>
<label for="u-email">{L[1]}<input id="u-email" type="email" name="email" required autocomplete="email"></label>
<button class="btn" type="submit">{L[2]}</button></form><p class="form-msg" data-msg aria-live="polite"></p>'''
    body = f'''{crumbs_html(src, trail)}
<section class="section night"><div class="wrap"><div class="section-head"><div class="prose"><h1>{E(c["h1"][lang])}</h1><p class="lead">{E(c["intro"][lang])}</p></div></div>
<div class="seeds">{seeds}</div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{E(c["commission_h"][lang])}</h2><span class="pdp-price">{chf(c["commission_price"])}</span></div>
<div class="split"><div class="prose"><p class="lead">{E(c["commission"][lang])}</p><ol class="steps steps-2">{steps}</ol></div><div>{form}</div></div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{t["related"]}</h2></div>{grid(src, lang, [g, *[p for p in atelier() if p is not g]])}</div></section>'''
    offer = {"@context": "https://schema.org", "@type": "Product", "name": "Gletscher " + c["h1"][lang] + (" mit eigenem Code" if lang == "de" else " with your own code"),
             "description": c["desc"][lang], "brand": {"@type": "Brand", "name": BRAND["name"]}, "sku": "SL-GLETSCHER-CODE",
             "image": [absolute(f"assets/renders/gletscher-s{x}-on.jpg") for x in c["seeds"]],
             "offers": {"@type": "Offer", "priceCurrency": "CHF", "price": f'{c["commission_price"]}.00', "url": absolute(src),
                        "availability": "https://schema.org/MadeToOrder", "seller": {"@id": BRAND["domain"] + "/#org"}}}
    write(src, page(src, lang, c["title"][lang] + " | " + BRAND["name"], c["desc"][lang], body, alt, "unikate",
                    [crumbs_ld(trail), offer], og_image=absolute("assets/renders/gletscher-s42-on.jpg")))


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
<figure class="pdp-art" data-lamp data-base="{asset(src, "renders/" + p["slug"] + "-")}" data-colour="{p["colours"][0]}" data-oncolour="{p["colours"][0]}">
{img(src, p, lang, eager=True, small=False)}
<figcaption><button class="light-toggle" type="button" data-light aria-pressed="false" data-on="{t["light_on"]}" data-off="{t["light_off"]}">{t["light_on"]}</button></figcaption></figure>
<div class="pdp-info">
<div><p class="eyebrow">{E(p["type"][lang])}{" · " + E(p["edition"][lang]) if p.get("edition") else ""}</p><h1>{E(p["name"])}</h1></div>
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
    image_urls = [absolute(f'assets/renders/{p["slug"]}-{c}.jpg') for c in p["colours"]] + [absolute(f'assets/renders/{render_name(p, on=True)}.jpg')]
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
               "mainEntityOfPage": absolute(asrc), "image": absolute("assets/renders/aare-frost-on.jpg")}
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
    pairs = [(path_for(k, "de"), path_for(k, "en")) for k in ("home", "shop", "atelier_series", "unikate", "cordless", "b2b", "about", "journal", "faq", "shipping", "imprint", "privacy", "terms")]
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
                    f'{BRAND["domain"]}/assets/renders/{p["slug"]}-{c}.jpg', i + 1, f'{p["name"]} {COLOURS[c]["de"]}',
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
    shutil.copytree(os.path.join(ROOT, "assets", "renders"), os.path.join(OUT, "assets", "renders"))
    for lang in LANGS:
        build_home(lang)
        build_listing("shop", lang, PRODUCTS)
        cordless_extra = (f'<section class="section"><div class="wrap"><div class="section-head"><h2>{UI[lang]["faq_h"]}</h2></div>'
                          f'{details(PAGES["cordless"]["points"][lang])}</div></section>')
        build_listing("cordless", lang, [p for p in PRODUCTS if p["cordless"]], cordless_extra)
        for p in PRODUCTS:
            build_product(p, lang)
        build_atelier(lang)
        build_unikate(lang)
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
