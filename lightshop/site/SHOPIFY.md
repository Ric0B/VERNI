# From draft to Shopify

The static site in `public/` is the design and content blueprint. Shopify runs the real shop. Moving it over takes about one weekend.

## 1. Set up (about 2 h)

1. Register the domain (see `research/04-brand-names.md`).
2. Create a Shopify account in Switzerland. Start with **Basic**, about CHF 21–28 a month (check the official CH price).
3. Under Settings → Payments, turn on **Shopify Payments**, with cards, Apple Pay, Google Pay and **TWINT** if it's listed. If TWINT isn't listed, use an official TWINT app from the Shopify App Store.
4. Settings → Markets: primary market **Switzerland** (CHF). Add Liechtenstein. Leave Germany and Austria off until the legal checklist is done.
5. Settings → Languages: German (default) + English. Install **Translate & Adapt** (free, by Shopify) to enter the English texts from `content.py`.
6. Settings → Shipping: Swiss Post, CHF 8, free above CHF 120.
7. Settings → Taxes: no VAT until you register.

## 2. Theme (about 4 h)

- Start from **Dawn** (free, fast, accessible), or a premium theme made for few products (e.g. "Sense", "Craft").
- Copy the look from `assets/site.css`:
  - Colours: background `#eceeea`, text `#1b2124`, accent `#c97a12`
  - Fonts: Gloock for headings, Hanken Grotesk for body text (both on Google Fonts; in Shopify's font picker, or upload them)
- Rebuild the home page sections in the theme editor: hero, featured collection (3 lamps), "Wie eine Lampe entsteht" as a multicolumn section, the B2B banner, blog posts.

## 3. Products (30 min)

1. Run `python3 build.py`. This writes `shopify/products.csv` (Shopify's import format, one row per colour, all products as drafts).
2. Products → Import → `shopify/products.csv`.
3. **Replace the images.** The CSV points at placeholder drawings on your future domain. Upload real photos per colour instead.
4. Add product metafields for "layers", "print time" and "light source" so the theme can show the spec table.

## 4. Pages and blog

| Draft page | Shopify |
|---|---|
| /kabellose-tischlampen/ | Collection "Kabellose Tischlampen" (tag `kabellos`) with the intro text in the description |
| /gastronomie-hotels/ | Page with a contact form (theme "Contact form" section) |
| /atelier/, /faq/, /versand-rueckgabe/ | Pages |
| /impressum/, /datenschutz/, /agb/ | Settings → Policies (Shopify has templates). **Have them checked** |
| Journal articles | Blog "Journal": paste the text from `content.py` |

Shopify's own URLs are `/products/aare` and `/collections/...`, so they'll differ from the draft. The draft was never live, so no redirects are needed.

## 5. Apps (keep few, and only these)

| App | Why | Cost |
|---|---|---|
| Translate & Adapt | German and English | Free |
| Shopify Email or Klaviyo (free up to 250 contacts) | Newsletter, abandoned-cart email | Free to start |
| Judge.me | Reviews **with correct star-rating data for Google** | Free plan |
| Google & YouTube | Merchant Center, free product listings | Free |
| Facebook & Instagram | Shop on Instagram, Meta pixel and Conversions API | Free |
| Pinterest | Product pins, catalogue | Free |
| Shopify Inbox | Chat | Free |

**Avoid:** apps that inject a lot of JavaScript (popups, countdown timers, "X people are viewing"). They slow the site down and cheapen the brand.

## 6. Before going live

- [ ] Real photos (at least 3 per lamp: lit, unlit, in a room) and one short video per lamp
- [ ] Imprint, privacy policy and terms filled in
- [ ] Lamp label and declaration of conformity ready (see the legal checklist)
- [ ] Place 2 test orders (card + TWINT) and refund them
- [ ] Google Search Console + sitemap
- [ ] Check page speed in PageSpeed Insights: aim for 90+ on mobile

## Connector to add

The official **Shopify** connector (in the claude.ai connector directory, by Shopify) lets Claude create and update products, read orders and analyse sales directly. Add it once the shop exists. Only add connectors from the official directory published by the vendor itself.
