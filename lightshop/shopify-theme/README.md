# Schichtlicht Shopify theme (Online Store 2.0)

The draft website's design as a real Shopify theme: night hero, product cards that switch the light on when you hover, a light toggle on product pages, Atelier badges, a one-off page, a hospitality contact form and a waitlist (password) page. It has no apps and no frameworks: one CSS file and 2 KB of JavaScript. Fonts are self-hosted, so no visitor data goes to Google. That matters for customers in Germany and Austria.

**Validated with Shopify Theme Check 3.31: 0 errors, 0 warnings.**

## Upload

1. Zip the *contents* of this folder (not the folder itself). `make_zip.sh` does this and writes `schichtlicht-theme.zip`.
2. Shopify admin → Online Store → Themes → Add theme → Upload zip file.
3. Customize → check each template, then Publish.

## Set up once

| What | Where | Value |
|---|---|---|
| Metafields | Settings → Custom data → Products | See `../site/shopify/metafields.md` (layers, sizes, material, edition, tagline…) |
| Products | Products → Import | `../site/shopify/products.csv` (all drafts). **Images:** the CSV points at `https://www.schichtlicht.ch/assets/renders/…`. Until that domain serves the files, upload the JPGs from `../site/assets/renders/` by hand. Keep the alt text ending in `#on` on the lit image |
| Collections | Products → Collections | `kollektion` (tag = kollektion), `atelier-serie` (tag = atelier-serie), `kabellos` (tag = kabellos) |
| Menus | Online Store → Navigation | `main-menu`: Lampen, Atelier-Serie, Unikate, Gastronomie, Journal. `footer`, `help`, `legal` for the three footer columns |
| Pages | Online Store → Pages | "Unikate" with template `page.unikate`; "Gastronomie und Hotels" with template `page.contact`; Atelier, FAQ, Versand und Rückgabe |
| Blog | Online Store → Blog posts | Blog "Journal"; paste the 13 articles from `../site/content.py` and `../site/articles_more.py` |
| Languages | Settings → Languages | German default, English added; translate with *Translate & Adapt* |
| Hero and one-off images | Customize → Home | `moraene-frost-on.jpg` and `gletscher-s23/42/108-on.jpg` from `../site/assets/renders/` |

## Light toggle

On product pages the theme shows the variant's image (switched off). If the product has an image whose alt text contains `#on`, a "Licht einschalten" ("Switch the light on") button appears. Visitors whose system is in dark mode see the lit image first.

## Konfigurator (page template `page.konfigurator`)

Customers choose shape, size (S / M / L), colour or two colours, base or ceiling canopy and cable, dimmer and engraving. The page shows a live 3D lamp and the price. Preview without a shop: `design/konfigurator.html` (built by `design/build_konfigurator.py` from the same files).

Set up once:
1. **One product per shape** (Aare, Grat, Bise, Firn, Korb), each with an option "Grösse" and variants **S, M, L**. The variant prices are the prices shown. Suggested: Aare 139/169/199, Grat 179/219/259, Bise 189/229/269, Firn 149/189/229, Korb 169/219/269.
2. **One product per extra**, each with a single variant: Sockel Eiche (59), Kabel 3 m (12), Schnurdimmer (29), Gravur (19), Zweifarbig (25). Hide them from the shop's collections; they're only added with a lamp.
3. Pages → Add page "Konfigurator" → Template `page.konfigurator`.
4. Customize → Konfigurator page → each "Form" block: pick its product. Section settings: pick the five extras.

Colours, base, cable and engraving travel as line-item properties and show in the order. Hidden properties for the workshop: `_Druck` (the exact `lampgen.py` / `korb.py` command for that size), `_Konfiguration` (link that reopens the configuration) and `_Ref` (ties the extras to their lamp).

Sizes are uniform scales of the same shape, so every size prints like the original. `python3 lampgen.py aare --scale 0.85 --res fine` exports the M size. Firn uses a 150 mm rim radius (`--set r_rim=150`) so that L (Ø about 31 cm) fits the H2S plate.

The 3D view uses three.js r128 (MIT licence), shipped in `assets/three.min.js` so no outside server is contacted (as with the self-hosted fonts).
