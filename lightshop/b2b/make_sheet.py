#!/usr/bin/env python3
"""Build the B2B sales sheet and price list (A4, 3 pages) as HTML and PDF.

    python3 make_sheet.py        # writes sales-sheet.html and sales-sheet.pdf

Prices come from ../site/content.py, so the sheet never disagrees with the shop.
Trade price = 50% of retail (stores). Hospitality: 15% off from 10, 20% from 25.
"""
import html
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "site"))
import content as C  # noqa: E402

E = html.escape
R = "../site/assets/renders/"


def chf(x):
    return f"{x:,.0f}".replace(",", "'")


def rows():
    out = []
    for p in C.PRODUCTS:
        r = p["price"]
        ed = (p.get("edition") or {}).get("de", "")
        out.append(f"""<tr><td><img src="{R}{p['slug']}-{p['colours'][0]}-600.jpg" alt=""></td>
<td><b>{E(p['name'])}</b><br><span>{E(p['type']['de'].split(',')[0])}{' · ' + E(ed) if ed else ''}</span></td>
<td class="n">{p['height'] / 10:g} × {p['diameter'] / 10:g}</td>
<td class="n">{chf(r)}</td><td class="n">{chf(r * 0.85)}</td><td class="n">{chf(r * 0.80)}</td><td class="n">{chf(r * 0.5)}</td></tr>""")
    return "\n".join(out)


PAGE = """<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Schichtlicht Gastronomie und Handel</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gloock&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 10pt/1.5 "Hanken Grotesk", Helvetica, Arial, sans-serif; color: #1b2124; }}
.page {{ width: 210mm; height: 297mm; padding: 16mm 16mm 14mm; position: relative; page-break-after: always; overflow: hidden; }}
.night {{ background: linear-gradient(#15181b, #0b0d0f); color: #ecebe6; }}
h1, h2 {{ font-family: Gloock, Georgia, serif; font-weight: 400; margin: 0; line-height: 1.05; }}
h1 {{ font-size: 40pt; }} h2 {{ font-size: 20pt; margin-bottom: 4mm; }}
.eyebrow {{ font: 500 7.5pt/1 "IBM Plex Mono", monospace; letter-spacing: .14em; text-transform: uppercase; color: #8f9894; }}
.logo {{ font: 400 16pt/1 Gloock, Georgia, serif; }} .logo span {{ color: #f0a640; }}
.hero {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8mm; align-items: end; margin-top: 18mm; }}
.hero img {{ width: 100%; display: block; -webkit-mask-image: radial-gradient(ellipse 50% 50% at 50% 50%, #000 70%, transparent 100%); }}
.lead {{ font-size: 12pt; color: #b9bfbc; margin: 5mm 0 0; }}
.cols {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 6mm 8mm; margin-top: 10mm; }}
.cols h3 {{ font: 600 10.5pt/1.3 "Hanken Grotesk", sans-serif; margin: 0 0 1.5mm; padding-top: 2.5mm; border-top: .4mm solid #ecebe6; }}
.cols p {{ margin: 0; color: #b9bfbc; }}
.trio {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm; margin-top: 6mm; }}
.trio figure {{ margin: 0; }} .trio img {{ width: 100%; display: block; }}
.trio figcaption {{ font: 400 8pt "IBM Plex Mono", monospace; color: #59625e; margin-top: 1.5mm; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
th {{ font: 500 7pt "IBM Plex Mono", monospace; text-transform: uppercase; letter-spacing: .08em; color: #59625e; text-align: left; padding: 2mm 1.5mm; border-bottom: .4mm solid #1b2124; }}
td {{ padding: 1.5mm; border-bottom: .2mm solid #cdd3ce; vertical-align: middle; }}
td img {{ width: 13mm; height: 16mm; object-fit: cover; display: block; }}
td span {{ color: #59625e; font-size: 8pt; }}
.n {{ font-family: "IBM Plex Mono", monospace; text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
th.n {{ text-align: right; }}
.terms {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm 8mm; margin-top: 7mm; font-size: 8.5pt; }}
.terms h3 {{ font: 600 9.5pt "Hanken Grotesk", sans-serif; margin: 0 0 1mm; }}
.terms p {{ margin: 0; color: #3d4542; }}
.foot {{ position: absolute; left: 16mm; right: 16mm; bottom: 10mm; display: flex; justify-content: space-between; font: 400 7.5pt "IBM Plex Mono", monospace; color: #8f9894; }}
</style></head><body>

<section class="page night">
  <p class="logo">Schicht<span>licht</span></p>
  <div class="hero">
    <div><p class="eyebrow">Gastronomie · Hotels · Büros · Handel</p>
      <h1>Licht, das zu Ihrem Konzept passt.</h1>
      <p class="lead">Lampen aus der Schweiz, nach parametrischen Formeln gedruckt und von Hand montiert. Farben nach Ihrem Konzept, Serien ab 10 Stück, Lieferung in 3 bis 4 Wochen.</p></div>
    <img src="{R}moraene-frost-on.jpg" alt="">
  </div>
  <div class="cols">
    <div><h3>Kabellos für jeden Tisch</h3><p>Föhn mit Akku und Touch-Dimmer, rund 12 Stunden Licht. Ladestation für 10 Lampen. Kein Wachs, kein Flackern, keine Kabel über den Boden.</p></div>
    <div><h3>Pendelleuchten über Theke und Tisch</h3><p>Firn, Ø 35 cm, blendfrei, in Ihren Farben. Kabellänge nach Mass.</p></div>
    <div><h3>Farbe nach Konzept</h3><p>Wir drucken Farbmuster in Ihren Tönen, abgestimmt auf Möbel, Wände oder Corporate Design.</p></div>
    <div><h3>Unikate für Lobby und Empfang</h3><p>Gletscher mit eigenem Code, zum Beispiel dem Gründungsdatum Ihres Hauses. Mit Zertifikat.</p></div>
    <div><h3>Ersatz garantiert</h3><p>Bricht etwas im Betrieb, liefern wir den Ersatzschirm innert einer Woche. Jede Lampe ist zerlegbar und reparierbar.</p></div>
    <div><h3>Aus der Schweiz</h3><p>Entwurf, Druck, Prüfung und Montage in einem Atelier. Elektrik nur aus zertifizierten Teilen. Kurze Wege, kleine Serien.</p></div>
  </div>
  <div class="foot"><span>schichtlicht.ch · hallo@schichtlicht.ch</span><span>Stand {date}</span></div>
</section>

<section class="page">
  <p class="eyebrow">Kollektion und Atelier-Serie</p>
  <h2>Formen</h2>
  <div class="trio">
    <figure><img src="{R}foehn-frost-on-600.jpg" alt=""><figcaption>Föhn · kabellos</figcaption></figure>
    <figure><img src="{R}firn-frost-on-600.jpg" alt=""><figcaption>Firn · Pendelleuchte</figcaption></figure>
    <figure><img src="{R}gletscher-s42-on-600.jpg" alt=""><figcaption>Gletscher · Unikat, Code 0042</figcaption></figure>
    <figure><img src="{R}aare-frost-on-600.jpg" alt=""><figcaption>Aare · Tischlampe</figcaption></figure>
    <figure><img src="{R}grat-stein-on-600.jpg" alt=""><figcaption>Grat · Tischlampe</figcaption></figure>
    <figure><img src="{R}bise-frost-on-600.jpg" alt=""><figcaption>Bise · Atelier-Serie</figcaption></figure>
    <figure><img src="{R}moraene-frost-on-600.jpg" alt=""><figcaption>Moräne · Edition von 50</figcaption></figure>
    <figure><img src="{R}nebel-frost-on-600.jpg" alt=""><figcaption>Nebel · Stehlampe 123 cm</figcaption></figure>
    <figure><img src="{R}glut-frost-on-600.jpg" alt=""><figcaption>Glut · Nachtlicht</figcaption></figure>
  </div>
  <div class="foot"><span>Alle Bilder sind Renderings der druckfertigen Modelle.</span><span>2</span></div>
</section>

<section class="page">
  <p class="eyebrow">Preisliste {year} · CHF</p>
  <h2>Preise</h2>
  <table>
    <thead><tr><th></th><th>Modell</th><th class="n">H × Ø cm</th><th class="n">Endkunde</th><th class="n">ab 10</th><th class="n">ab 25</th><th class="n">Handel*</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="terms">
    <div><h3>Gastronomie und Hotels</h3><p>15 % ab 10 Lampen, 20 % ab 25 Lampen, gemischt über alle Modelle. Musterlampe zum halben Preis, wird bei Bestellung angerechnet. Ladestation Föhn (10 Plätze) CHF 180.</p></div>
    <div><h3>* Handel</h3><p>50 % auf den Endkundenpreis ab 6 Stück, Nachbestellung ab 3 Stück. Unverbindliche Preisempfehlung: Endkundenpreis. Atelier-Serie nur für ausgewählte Partner.</p></div>
    <div><h3>Sonderfarben und -grössen</h3><p>Sonderfarbe CHF 20 pro Lampe, ab 10 Stück gratis. Kabellänge nach Mass gratis. Grössenänderungen auf Anfrage.</p></div>
    <div><h3>Lieferung und Zahlung</h3><p>Ab Lager 2 Werktage, Serien 3 bis 4 Wochen. Versand in der Schweiz und nach Liechtenstein gratis ab CHF 500. Zahlung 30 Tage netto.</p></div>
  </div>
  <div class="foot"><span>Preise in CHF. Änderungen vorbehalten.</span><span>3</span></div>
</section>
</body></html>"""


def main():
    import datetime as dt
    today = dt.date.today()
    out = os.path.join(HERE, "sales-sheet.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(PAGE.format(R=R, rows=rows(), date=["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"][today.month - 1] + f" {today.year}", year=today.year))
    pdf = out.replace(".html", ".pdf")
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
          f"await p.goto('file://{out}');await p.waitForTimeout(800);await p.pdf({{path:'{pdf}',format:'A4',printBackground:true}});await b.close();}})();")
    try:
        subprocess.run(["node", "-e", js], check=True)
        print("wrote", os.path.relpath(pdf))
    except (OSError, subprocess.CalledProcessError):
        print("wrote", os.path.relpath(out), "(open it in a browser and print to PDF; Playwright not found)")


if __name__ == "__main__":
    main()
