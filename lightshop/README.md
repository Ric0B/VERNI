# Schichtlicht: lamp business launch pack

Overnight work from 28–29 Oct 2026. Working brand name **Schichtlicht** ("layer light"); see the name options.

| # | What | Where |
|---|---|---|
| 1 | Suppliers with prices: filament, electrics, bulbs, packaging, shipping, sales channels | `research/01-suppliers.md` |
| 2 | Market research: competitors, price gap, trends, range, costs per lamp, revenue scenarios, paid ads verdict | `research/02-market-and-range.md` |
| 2b | Legal checklist (NEV, vRG, GPSR, WEEE) | `research/03-legal-checklist.md` |
| 2c | Brand names | `research/04-brand-names.md` |
| 3 | **Parametric design system**: 10 lamp formulas, STL export, printability check | `design/lampgen.py`, `design/README.md` |
| 3b | Bases, mounts and couplers (PETG), sized from each shade | `design/parts.py` |
| 3c | One-offs and numbered editions with registry and certificate PDF | `design/edition.py`, `samples/certificate-example.pdf` |
| 3d | **Formlabor**: in-browser configurator with live 3D (private page) | `design/formlabor.html` · https://claude.ai/artifact/9G4yVFCJJCnMvVcZBLtnwQ |
| 4 | Draft website, German + English, renders, Atelier series, one-off page, 13 articles, SEO | `site/` · preview https://claude.ai/artifact/9HEDNLgLsuSYMm6TYPxPck |
| 4b | Keyword map, article plan, link building | `site/seo/keywords.md` |
| 4c | **Shopify theme** (Online Store 2.0, 0 Theme Check issues) + product CSV with metafields | `shopify-theme/`, `site/shopify/`, `site/SHOPIFY.md` |
| 5 | Social media plan (90 days) | `social/campaign-plan.md` |
| 5b | First 4 weeks written out + outreach messages (creators, cafés, stores, press) | `social/first-4-weeks.md` |
| 6 | B2B sales sheet and price list (PDF) | `b2b/sales-sheet.pdf` (rebuild: `python3 b2b/make_sheet.py`) |
| 7 | Compliance kit: declaration of conformity, technical file, test log, risk assessment, safety sheet, label | `compliance/` |

## View the site

    cd lightshop/site && python3 build.py && cd public && python3 -m http.server 8000
    # open http://localhost:8000

Edit any text or price in `site/content.py`, then run `python3 build.py` again.

## The decisions that matter most

1. **Price:** "accessible premium" at CHF 129–249, plus an entry lamp at CHF 69 and B2B sets. Under CHF 70 is crowded; CHF 90–200 is thin in Switzerland.
2. **Market:** Switzerland and Liechtenstein first. Germany and Austria in year 2, because selling into the EU from Switzerland needs an EU responsible person (GPSR), WEEE registration and customs handling.
3. **Product:** launch with 3 lamps (Aare, Föhn cordless, Firn pendant) plus the Atelier series as the brand's halo: Bise CHF 390, Moräne edition of 50 at CHF 460, Gletscher one-off at CHF 540, own-code commission at CHF 690.
4. **Safety:** LED only, max. 7 W. PETG at the socket, pre-certified electrics, a temperature test log per design. Europlug works in CH, DE and AT.
5. **Ads:** none before Christmas 2026. Test CHF 300–450 in Feb–Mar 2027 after 20 organic sales. Break-even ROAS is about 1.5.

## Connectors worth adding (official directory, by the vendor itself)

| Connector | Use | When |
|---|---|---|
| **Shopify** (by Shopify) | Create products, read orders, sales analysis | Once the shop exists |
| **Semrush** or **Ubersuggest** | Real keyword volumes for CH, DE, AT | Now: fills the gap in the market research |
| **Canva** (already installed, failed to connect in this session) | Social templates | Fix the connection in claude.ai settings |
| Klaviyo (already installed, failed to connect) | Newsletter flows | At launch |

I'd skip connectors that run ad accounts on their own ("autonomous" ad agents) until you have run ads manually yourself.

## What I could not do in this session

- Open printyourlight.ch or any shop page directly. The network allows search only, so prices come from search results and must be checked.
- Check whether the domains are free.
- Get real search volumes (the SEO connectors failed to connect).
