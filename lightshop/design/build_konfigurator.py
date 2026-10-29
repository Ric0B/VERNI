#!/usr/bin/env python3
"""Build the standalone configurator preview (konfigurator.html) from the Shopify theme files,
so the shop and the preview never drift apart:

    shopify-theme/assets/configurator.js     logic, geometry, default prices
    shopify-theme/assets/configurator.css    layout
    shopify-theme/snippets/configurator-markup.liquid
    shopify-theme/assets/base.css            colour tokens (the :root blocks only)

    python3 build_konfigurator.py   # -> design/konfigurator.html (no cart; prices from the defaults in the JS)
    python3 build_konfigurator.py --artifact OUT.html   # same page without the document skeleton, for a claude.ai artifact
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.join(HERE, "..", "shopify-theme")


def read(*p):
    with open(os.path.join(THEME, *p), encoding="utf-8") as f:
        return f.read()


def tokens(css):
    """The :root token blocks of base.css (light, dark media query, forced dark)."""
    end = css.index("*, *::before")
    return css[css.index(":root"):end].strip()


PAGE = """<!doctype html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lampen-Konfigurator</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gloock&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{tokens}
*, *::before, *::after {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font: 400 1.0625rem/1.6 var(--body); -webkit-font-smoothing: antialiased; }}
.cfg-top {{ display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; max-width: 84rem; margin: 0 auto; padding: 1rem clamp(1rem, 3vw, 2.5rem) 0; }}
.cfg-top b {{ font: 400 1.4rem/1 var(--display); }}
.cfg-top span {{ font: 500 .75rem/1.3 var(--mono); color: var(--muted); }}
@media (max-width: 52rem) {{ .cfg-top {{ display: none; }} }}
{css}
</style>
</head>
<body>
<header class="cfg-top"><b>Schichtlicht</b><span>Konfigurator · Vorschau ohne Warenkorb</span></header>
<main class="cfg" data-configurator>
{markup}
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
{js}
</script>
</body>
</html>
"""


def main():
    markup = re.sub(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}\s*", "", read("snippets", "configurator-markup.liquid"), flags=re.S)
    if "{%" in markup or "{{" in markup:
        raise SystemExit("configurator-markup.liquid must stay free of Liquid")
    html = PAGE.format(tokens=tokens(read("assets", "base.css")), css=read("assets", "configurator.css"),
                       markup=markup.strip(), js=read("assets", "configurator.js"))
    out = os.path.join(HERE, "konfigurator.html")
    if len(sys.argv) == 3 and sys.argv[1] == "--artifact":
        out = sys.argv[2]
        for tag in ("<!doctype html>", '<html lang="de-CH">', "<head>", "</head>", "<body>", "</body>", "</html>",
                    '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">'):
            html = html.replace(tag + "\n", "").replace(tag, "")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", os.path.relpath(out), f"({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
