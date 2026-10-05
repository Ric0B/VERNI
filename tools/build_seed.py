#!/usr/bin/env python3
"""Builds data/shows.json from the venue master list plus what was gathered from venue websites on 2026-10-05.
The weekly refresh agent (see data/REFRESH.md) overwrites data/shows.json directly; this script only seeds it."""
import json, re, os, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = open(os.path.join(ROOT, "tools", "legacy_sample_rows.swift.txt")).read()
venues = {}
for m in re.finditer(r'VenueSeed\(id: "(.*?)", name: "(.*?)", type: \.(\w+), cityID: "(.*?)", address: "(.*?)", web: (nil|"(.*?)"), lat: ([\d.]+), lon: ([\d.]+)\)', rows):
    id_, name, t, city, addr, _, web, lat, lon = m.groups()
    venues[id_] = dict(id=id_, name=name, type=t, city=city, address=addr, website=("https://" + web if web else None),
                       lat=float(lat), lon=float(lon), hours=None, sourceURL=None)
assert len(venues) == 56, len(venues)

def H(*slots): return [dict(days=d, open=o, close=c) for d, o, c in slots]
def set_v(id_, **kw): venues[id_].update(kw)

# ---- corrections and hours found on the venues' own pages (2026-10-05) ----
set_v("kaskaden", id="kasko", name="Kasko", website="https://www.kasko.ch")
venues["kasko"] = venues.pop("kaskaden")
set_v("krupp", address="Riehentorstrasse 33, 4058 Basel", lat=47.5640, lon=7.5940, geoApprox=True, hours=H(([4, 5], 14, 18)), sourceURL="https://www.nicolaskrupp.com/exhibitions", website="https://www.nicolaskrupp.com")
set_v("vonbartha", hours=H(([2, 3, 4, 5], 14, 18), ([6], 11, 16)), sourceURL="https://vonbartha.com/exhibitions/")
set_v("stampa", website="https://www.stampa-galerie.ch", sourceURL="https://www.stampa-galerie.ch/")
set_v("beyeler", hours=H(([3], 10, 20), ([4, 5, 6, 7], 10, 18)), sourceURL="https://www.fondationbeyeler.ch/en/visit")
set_v("tinguely", hours=H(([2, 3, 5, 6, 7], 11, 18), ([4], 11, 21)), sourceURL="https://www.tinguely.ch/en/exhibitions.html")
set_v("khbl", hours=H(([2, 3, 5], 11, 18), ([4], 11, 20), ([6, 7], 11, 17)), sourceURL="https://kunsthausbaselland.ch/")
set_v("hek", sourceURL="https://hek.ch/")
set_v("vitra", hours=H(([1, 2, 3, 4, 5, 6, 7], 10, 18)), sourceURL="https://www.design-museum.de/en/exhibitions.html")
set_v("kunstraumriehen", website="https://www.kunstraumriehen.ch", hours=H(([3, 4, 5], 13, 18), ([6, 7], 11, 18)), sourceURL="https://www.kunstraumriehen.ch/")
set_v("dreilaender", website="https://www.dreilaendermuseum.eu", hours=H(([2, 3, 4, 5, 6, 7], 11, 18)), sourceURL="https://www.dreilaendermuseum.eu/")
set_v("fernet", website="https://www.fondationfernet-branca.org", hours=H(([3, 4, 5, 6, 7], 13, 18)), sourceURL="https://www.fondationfernet-branca.org/en/")
set_v("kmbasel", hours=H(([2, 3, 4, 5, 6, 7], 11, 18)), sourceURL="https://kunstmuseumbasel.ch/en/exhibitions")
venues["kmbasel_main"] = dict(id="kmbasel_main", name="Kunstmuseum Basel | Hauptbau & Neubau", type="institution", city="basel",
    address="St. Alban-Graben 16, 4051 Basel", website="https://kunstmuseumbasel.ch", lat=47.5547, lon=7.5963, geoApprox=True,
    hours=H(([2, 5, 6, 7], 10, 18), ([4], 10, 18), ([3], 10, 20)), sourceURL="https://kunstmuseumbasel.ch/en/exhibitions")
venues["kmbasel_main"]["hours"] = H(([2, 4, 5, 6, 7], 10, 18), ([3], 10, 20))
set_v("presenhuber", website="https://www.presenhuber.com", hours=H(([2, 3, 4, 5], 11, 18)), sourceURL="https://www.presenhuber.com/")
set_v("migros", hours=H(([2, 3, 5, 6, 7], 11, 18), ([4], 11, 20)), sourceURL="https://www.migrosmuseum.ch/en")
set_v("kunsthaus", hours=H(([2, 3, 5, 6, 7], 10, 18), ([4], 10, 20)), sourceURL="https://www.kunsthaus.ch/en/")
set_v("konstruktiv", address="Limmatstrasse 268, 8005 Zürich", geoApprox=True, sourceURL="https://www.hauskonstruktiv.ch/en")
set_v("kmw", hours=H(([3, 4, 5, 6, 7], 10, 17), ([2], 10, 20)), sourceURL="https://www.kmw.ch/en")
set_v("fotomuseum", hours=H(([2, 4, 5], 11, 17), ([3], 11, 20), ([6, 7], 11, 18)), sourceURL="https://www.fotomuseum.ch/en")
set_v("mai36", website="https://www.mai36.com", sourceURL="https://www.mai36.com/")
set_v("walcheturm", website="https://walcheturm.ch", sourceURL="https://walcheturm.ch/")
set_v("cabaret", website="https://www.cabaretvoltaire.ch", sourceURL="https://www.cabaretvoltaire.ch/")
set_v("coalmine", website="https://www.coalmine.ch", hours=H(([2, 3], 9, 17), ([4, 5], 9, 21), ([6, 7], 10, 16)), sourceURL="https://www.coalmine.ch/")
set_v("skopia", website="https://www.skopia.ch", address="Rue des Vieux-Grenadiers 9, 1205 Genève", hours=H(([2, 3, 4, 5], 11, 18.5), ([6], 11, 17)), sourceURL="https://www.skopia.ch/")
set_v("mamco", address="Rue des Granges 13, 1204 Genève", lat=46.2012, lon=6.1480, geoApprox=True, website="https://www.mamco.ch", sourceURL="https://www.mamco.ch/en")
set_v("cpg", address="Promenade des Bastions 8, 1205 Genève", website="https://www.centrephotogeneve.ch", hours=H(([2, 3, 5], 11, 18), ([4], 11, 20), ([6], 11, 16.75)), sourceURL="https://www.centrephotogeneve.ch/en")
set_v("mcba", website="https://www.mcba.ch", hours=H(([2, 3, 5, 6, 7], 10, 18), ([4], 10, 20)), sourceURL="https://www.mcba.ch/en/")
set_v("artbrut", website="https://www.artbrut.ch", hours=H(([2, 3, 4, 5, 6, 7], 11, 18)), sourceURL="https://www.artbrut.ch/en/")
set_v("jenisch", website="https://museejenisch.ch", hours=H(([2, 3, 5, 6, 7], 11, 18), ([4], 11, 20)), sourceURL="https://museejenisch.ch/")
set_v("khbern", website="https://kunsthallebern.ch", hours=H(([2, 3, 5, 6, 7], 11, 18), ([4], 11, 20)), sourceURL="https://kunsthallebern.ch/en/")
set_v("kmbern", hours=H(([2], 10, 20), ([3, 4, 5, 6, 7], 10, 17)), sourceURL="https://www.kunstmuseumbern.ch/en")
set_v("zpk", hours=H(([2, 3, 4, 5, 6, 7], 10, 17)), sourceURL="https://www.zpk.org/en/")
set_v("kmluzern", address="Europaplatz 1, 6002 Luzern", hours=H(([2, 4, 5, 6, 7], 11, 18), ([3], 11, 19)), sourceURL="https://www.kunstmuseumluzern.ch/en/")

# ---- shows: (venue, artists, title, start|None, end, url) ----
S = []
def show(v, artists, title, start, end, path):
    base = (venues[v].get("website") or "").rstrip("/")
    url = path if path.startswith("http") else base + path
    S.append(dict(venue=v, artists=artists, title=title, start=start, end=end, url=url))
show("vonbartha", ["Francisco Sierra"], "Bijna een vlinder", "2026-08-27", "2026-10-23", "/exhibitions/francisco-sierra-bijna-een-vlinder/")
show("vonbartha", ["Christian Andersson"], "Mother Tongue", "2026-08-27", "2026-10-23", "/exhibitions/christian-andersson-mother-tongue/")
show("vonbartha", [], "Headroom", "2026-11-05", "2027-01-08", "/exhibitions/headroom/")
show("vonbartha", ["Landon Metz"], "2026", "2026-11-05", "2027-01-08", "/exhibitions/landon-metz-2026/")
show("krupp", ["Kaspar Müller"], "Maintenance 3", "2026-08-28", "2026-10-31", "/exhibitions/2026-08-kaspar-müller")
show("stampa", ["Jonas Burkhalter"], "Space Bee Freedom", "2026-09-10", "2026-11-07", "https://www.stampa-galerie.ch/")
show("beyeler", [], "Constellations", "2026-09-26", "2027-09-05", "https://www.fondationbeyeler.ch/en/exhibitions")
show("beyeler", ["Ruth Asawa"], "Ruth Asawa", "2026-10-18", "2027-01-10", "https://www.fondationbeyeler.ch/en/exhibitions")
show("tinguely", ["Nicolas Darrot"], "Fuzzy Logic", "2026-03-05", "2027-03-07", "https://www.tinguely.ch/en/exhibitions.html")
show("tinguely", [], "Labouring Bodies", "2026-06-10", "2026-11-08", "https://www.tinguely.ch/en/exhibitions.html")
show("tinguely", ["Zilla Leutenegger"], "SPACES BETWEEN", "2026-09-23", "2027-03-07", "https://www.tinguely.ch/en/exhibitions.html")
show("tinguely", [], "Les témoins oculistes. The sense of sight in art", "2026-12-02", "2027-05-09", "https://www.tinguely.ch/en/exhibitions.html")
KM = "https://kunstmuseumbasel.ch/en/exhibitions/"
show("kmbasel", ["Cao Fei"], "Testimonies to the Near Future", "2026-05-30", "2026-10-11", KM + "2026/cao-fei")
show("kmbasel_main", ["Renée Levi"], "Mira", "2025-08-30", "2029-01-01", KM + "2025/renee-levi")
show("kmbasel_main", ["Marc Bauer"], "Fear Rage Desire, Still Standing", "2026-03-07", "2027-05-02", KM + "2026/marc-bauer")
show("kmbasel_main", ["Roy Lichtenstein"], "Sweet Dreams, Baby!", "2026-08-22", "2027-03-14", KM + "2026/roy-lichtenstein-sweet-dreams-baby")
show("kmbasel_main", [], "Van Gogh, Hodler, and a Cabriolet. The Collector and Pioneer Gertrud Dübi-Müller", "2026-09-19", "2027-02-07", KM + "2026/van-gogh-hodler-und-ein-cabriolet")
show("kmbasel_main", [], "Friendship, Collecting, Connoisseurship. Karl and Marianne Im Obersteg-Buess", "2026-09-01", "2027-02-07", KM + "2026/friendship-collecting-connoisseurship-karl-and-marianne-im-obersteg")
show("kmbasel_main", [], "Boundless Printmaking. The Schweizerische Graphische Gesellschaft", "2026-08-04", "2026-11-29", KM + "2026/boundless-printmaking-the-schweizerische-graphische-gesellschaft")
show("khbl", ["Monira Al Qadiri"], "Benzene Float", "2026-02-06", "2027-01-24", "/ausstellungen/monira-al-qadiri")
show("khbl", ["Yanik Soland"], "Walking on Rubber Eggshells", "2026-09-25", "2026-11-15", "/ausstellungen/yanik-soland")
show("khbl", [], "Sinnesumschmeichelungen", "2026-09-25", "2027-04-04", "/ausstellungen/sinnesumschmeichelungen")
show("hek", ["Studio Lemercier"], "", "2026-08-22", "2026-11-15", "https://hek.ch/programm/ausstellungen/studio-lemercier")
show("vitra", ["Geoffrey Bawa"], "Architecture for the Senses", "2026-09-26", "2027-02-28", "https://www.design-museum.de/en/exhibitions/detailpages/geoffrey-bawa.html")
show("vitra", ["Verner Panton"], "Form, Colour, Space", "2026-05-23", "2027-05-09", "https://www.design-museum.de/en/exhibitions/detailpages/verner-panton-form-colour-space.html")
show("kunstraumriehen", ["Jahic/Roethlisberger"], "La Maison des Heures Perdues", "2026-09-12", "2026-11-08", "/de/page/jahicroethlisberger-la-maison-des-heures-perdues")
show("kunstraumriehen", [], "Regionale 27. Geteilte Sicht", "2026-11-28", "2027-01-31", "/de/page/regionale-27-geteilte-sicht")
show("dreilaender", [], "Zuhause – unterwegs", "2026-09-19", "2027-04-18", "/anschauen/sonderausstellungen/")
show("dreilaender", [], "100 Jahr Motettenchor", "2026-06-20", "2026-11-08", "/anschauen/sonderausstellungen/")
show("fernet", ["Aurora Király"], "Parcours de regards", "2026-10-10", "2027-03-07", "https://www.fondationfernet-branca.org/en/exhibitions/aurora-kiraly-practices-looking")
show("presenhuber", ["Angela Bulloch"], "Entropy, 2026", "2026-09-12", "2026-10-23", "/exhibitions/angela-bulloch4")
show("presenhuber", ["Liam Gillick"], "The Case is Altered or Die Sache ist anders", "2026-09-18", "2026-10-31", "/exhibitions/liam-gillick5")
show("presenhuber", ["Josh Smith"], "Mind Child", "2026-09-25", "2026-12-11", "/exhibitions/josh-smith7")
show("presenhuber", ["Dieter Roth"], "Curated by Josh Smith", "2026-09-25", "2026-12-11", "/exhibitions/dieter-roth2")
show("migros", ["Nicole L'Huillier"], "Canción de Amor", "2026-09-26", "2027-01-17", "https://migrosmuseum.ch/en/exhibitions/nicole-lhuillier-2")
show("migros", ["Sylvie Fleury", "Shamiran Istifan"], "She-Devils on Wheels, Angels on Heels", "2026-09-26", "2027-01-17", "https://migrosmuseum.ch/en/exhibitions/she-devils-on-wheels-angels-on-heels")
show("kunsthaus", ["Maria Lassnig", "Edvard Munch"], "Maria Lassnig and Edvard Munch", None, "2027-02-21", "https://www.kunsthaus.ch/en/besuch-planen/ausstellungen/maria-lassnig-und-edvard-munch/")
show("kunsthaus", ["Vilhelm Hammershøi"], "The Eye That Listens", None, "2026-10-25", "https://www.kunsthaus.ch/en/besuch-planen/ausstellungen/vilhelm-hammershoi/")
show("kunsthaus", [], "Evergreens. Selected Works from the Collection", None, "2027-01-10", "https://www.kunsthaus.ch/en/besuch-planen/ausstellungen/ikonen/")
show("konstruktiv", [], "The Body Within Abstraction", "2026-09-26", "2027-01-10", "/en/exhibitions/the-body-within-abstraction")
show("kmw", ["Mona Hatoum"], "Routes of Dissonance", "2026-10-03", "2027-01-31", "https://www.kmw.ch/en/exhibition/mona-hatoum/")
show("kmw", [], "Monet to Mondrian – Bailly to Baer", "2026-09-19", "2026-12-31", "https://www.kmw.ch/en/exhibition/moderne-reloaded/")
show("kmw", ["Jutta Koether"], "Jutta Koether", "2026-09-12", "2027-01-17", "https://www.kmw.ch/en/exhibition/jutta-koether/")
show("kmw", [], "Paths of Plein-Air Painting Around 1800", "2026-07-04", "2026-10-25", "https://www.kmw.ch/en/exhibition/zur-sonne-zur-freiheit/")
show("kmw", ["Heidi Bucher", "Liesl Raff"], "Closer", "2026-06-13", "2026-11-08", "https://www.kmw.ch/en/exhibition/heidi-bucher-liesl-raff/")
show("fotomuseum", [], "Shadow Creatures – From Spirit Photography to the Ghosts of the Algorithm", "2026-06-27", "2026-10-11", "https://www.fotomuseum.ch/en/exhibitions-post/schattenwesen-von-der-geisterfotografie-zu-den-phantomen-des-algorithmus/")
show("fotomuseum", ["Nhu Xuan Hua"], "One Another – Nhu Xuan Hua and the Collection of Fotomuseum Winterthur", "2026-06-27", "2026-10-11", "https://www.fotomuseum.ch/en/exhibitions-post/miteinander-nhu-xuan-hua-und-die-sammlung-des-fotomuseum-winterthur/")
show("mai36", ["Markus Saile"], "False Horizon", "2026-09-10", "2026-11-07", "/exhibitions/markus-saile")
show("mai36", ["Hiroki Tsukuda"], "Inferno", "2026-09-10", "2026-11-07", "/exhibitions/hiroki-tsukuda")
show("mai36", [], "flowers", "2026-09-11", "2026-11-07", "/exhibitions/flowers")
show("cabaret", [], "DadaZwischenSprachen", "2026-06-06", "2027-01-10", "/programme/dadazwischensprachen")
show("cabaret", ["Katalin Ladik", "Babi Badalov"], "Artists' Bar (Künstler*innenkneipe)", "2026-06-06", "2027-01-10", "/programme/dadazwischensprachen-2")
show("coalmine", [], "ALLES ECHT!", "2026-10-30", "2027-01-24", "/event/alles-echt/")
show("skopia", ["Pierre André Ferrand"], "Pierre André Ferrand", "2026-09-18", "2026-10-31", "/exhibitions-all/pierre-andre-ferrand-2026")
show("mamco", ["Joana Hadjithomas", "Khalil Joreige"], "MAMCO x SaSA", "2026-09-05", "2026-11-15", "/en/2329/MAMCO-x-SaSA")
show("mamco", ["Sylvia Sleigh"], "Sylvia Sleigh and Re-Collection: An Exhibition in Two Parts", "2026-06-05", "2026-10-25", "/en/2330/MAMCO-x-MAH")
show("cpg", ["Sarah Jade Sullivan"], "Minor Tides", "2026-07-02", "2026-10-10", "/exhibitions/marees-mineures")
show("cpg", ["Louise Desnos"], "Acedia", "2026-10-12", "2027-01-08", "/exhibitions/louise-desnos-acedia")
show("cpg", ["Edmund Clark", "Crofton Black"], "Cosmopolemos", "2026-10-29", "2027-02-20", "/exhibitions/edmund-clark-et-crofton-black-cosmopolemos")
show("mcba", ["Lucas Erin"], "La ronde (Manor Art Prize 2026 Vaud)", "2026-08-28", "2027-02-14", "https://www.mcba.ch/en/exhibitions/lucas-erin/")
show("mcba", ["Charles Blanc-Gatti"], "The Colours of Sound", "2026-09-25", "2027-01-17", "https://www.mcba.ch/en/exhibitions/blanc-gatti/")
show("artbrut", ["Armand Schulthess"], "The World of Armand Schulthess", "2026-11-27", "2027-04-25", "/en/events/the-world-of-armand-schulthess")
show("khbern", ["Saodat Ismailova"], "Amanat – As We Sleep", "2026-09-11", "2026-11-22", "/en/exhibitions/2026-saodat-ismailova-amanat-as-we-sleep")
show("kmbern", ["Franz Gertsch"], "Blow-Up (Part I)", "2026-08-14", "2027-01-17", "/en/node/9770")
show("kmbern", [], "Journey into Freedom. Capri – Skagen – Monte Verità", "2026-10-30", "2027-01-31", "/en/node/11397")
show("zpk", ["Florence Henri"], "Fokus. Florence Henri (1893–1982)", "2026-08-29", "2027-01-10", "/en/node/11353")
show("zpk", ["Roberto Burle Marx"], "Modernismo tropical", "2026-10-17", "2027-02-07", "/en/node/11349")
show("kmluzern", ["Shirana Shahbazi"], "All at Once. An Interplay with Li Tavor", "2026-07-04", "2026-10-18", "/en/exhibitions/shirana-shahbazi/")
show("kmluzern", ["Andreas Brunner"], "spot on Andreas Brunner", "2026-07-04", "2026-10-11", "/en/exhibitions/andreas-brunner/")
show("kmluzern", ["Dominik Zietlow"], "Nur die Berge begegnen sich nie", "2026-10-24", "2027-01-31", "/en/exhibitions/dominik-zietlow-manor/")
show("kmluzern", ["Noemi Pfister"], "hier & jetzt", "2026-11-14", "2027-01-31", "/en/exhibitions/hier-jetzt-vdg/")

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48]
seen = set()
for s in S:
    base = s["venue"] + "-" + slug(s["title"] or " ".join(s["artists"]) or "show")
    i, sid = 2, base
    while sid in seen: sid = f"{base}-{i}"; i += 1
    seen.add(sid); s["id"] = sid
    assert s["venue"] in venues, s["venue"]
    assert s["start"] is None or s["start"] <= s["end"], s

# ---- events (only ones stated on venue pages) ----
E = []
def ev(v, type_, title, date, time, url, show=None):
    base = (venues[v].get("website") or "").rstrip("/")
    E.append(dict(venue=v, type=type_, title=title, date=date, time=time, url=url if url.startswith("http") else base + url, show=show))
def sid(v, key): return next(s["id"] for s in S if s["venue"] == v and key.lower() in (s["title"] + " " + " ".join(s["artists"])).lower())
ev("khbl", "tour", "Kunst über Mittag mit Lunch", "2026-10-06", "12:15", "/")
ev("khbl", "tour", "Abendführung", "2026-10-08", "18:30", "/")
ev("khbl", "talk", "Performance und Künstlergespräch: Yanik Soland", "2026-11-07", "16:00", "/", sid("khbl", "Soland"))
ev("hek", "performance", "Open Decks", "2026-10-15", "17:00", "https://hek.ch/programm/veranstaltungen/open-decks")
ev("fernet", "opening", "Opening of Aurora Király exhibition", "2026-10-10", "16:00", "/en/exhibitions/aurora-kiraly-practices-looking", sid("fernet", "Király"))
ev("migros", "tour", "Guided tour: Collection Insights with Kamilla Ødegård", "2026-10-18", "15:00", "/en")
ev("konstruktiv", "tour", "Public guided tour", "2026-10-11", "11:45", "/en/events/534149", sid("konstruktiv", "Body Within"))
ev("konstruktiv", "tour", "Public guided tour", "2026-10-14", "18:15", "/en/events/536189", sid("konstruktiv", "Body Within"))
ev("konstruktiv", "tour", "Public guided tour", "2026-10-18", "11:45", "/en/events/534152", sid("konstruktiv", "Body Within"))
ev("fotomuseum", "talk", "Shadow Creatures in Photography, Psychology and AI (lecture)", "2026-10-10", "13:00", "/en")
ev("fotomuseum", "opening", "Opening: Helen Levitt – City at Play", "2026-10-23", "18:00", "/en")
ev("fotomuseum", "talk", "Curator's talk with Joshua Chuang and Alessandra Nappo", "2026-10-24", "15:00", "/en")
ev("fotomuseum", "tour", "Guided tour: Helen Levitt – City at Play", "2026-10-25", "11:30", "/en")
for d, t, ttl in [("2026-10-08", "20:30", "IGNM Konzert: Galina Ustwolskaja «Grand Duet»"), ("2026-10-19", "20:00", "Zhao Ziyi & Manfred Werder"), ("2026-10-20", "20:00", "Stepmother: Album Presentation"),
                  ("2026-10-21", "20:00", "Glenn Jones, Liam Grant, Son of Buzzi"), ("2026-10-22", "21:00", "FRANCE"), ("2026-10-24", "20:00", "Ensemble Tzara #1: Jannik Giger"), ("2026-10-25", "19:00", "hiddenbell Percussion Night")]:
    ev("walcheturm", "performance", ttl, d, t, "/agenda")
ev("cabaret", "talk", "Michael Taussig: Postcards for Mia", "2026-10-27", "18:00", "/programme/michael-taussig-postcards-for-mia")
ev("cabaret", "talk", "dears, write", "2026-10-28", "19:00", "/programme/dears-write-21-2")
ev("mamco", "tour", "Family activities (SaSA)", "2026-10-07", "16:00", "/en")
ev("mamco", "tour", "Free tour (Joana Hadjithomas & Khalil Joreige)", "2026-10-13", "15:00", "/en")
ev("mamco", "talk", "Panel: Male gaze / Female gaze", "2026-10-11", "14:00", "/en")
ev("mamco", "finissage", "Closing event: Sylvia Sleigh and Re-Collection", "2026-10-25", "11:00", "/en", sid("mamco", "Sleigh"))
ev("kmbern", "talk", "Erzählcafé: Franz Gertsch. Blow-Up (Part I)", "2026-10-10", "11:00", "/en", sid("kmbern", "Gertsch"))
ev("kmbern", "talk", "Zwischen Realität und Wahrheit: Fotografie und Malerei", "2026-10-20", "18:30", "/en")
ev("kmbern", "opening", "Vernissage: Journey into Freedom", "2026-10-29", "18:30", "/en/node/11397", sid("kmbern", "Journey"))
ev("zpk", "tour", "Guided tour: Kosmos Klee", "2026-10-11", "15:00", "/en/")
ev("khbern", "tour", "Exhibition visit & guided relaxation", "2026-10-10", "17:30", "/en/")
ev("khbern", "talk", "Walk & Talk", "2026-10-29", "17:30", "/en/")
ev("coalmine", "talk", "Yael Inokai: Die Auster", "2026-10-27", "19:30", "/event/yael-inokai-die-auster/")
ev("coalmine", "opening", "Vernissage: ALLES ECHT!", "2026-10-29", "18:30", "/event/vernissage-zur-ausstellung-alles-echt/", sid("coalmine", "ALLES"))
for i, e in enumerate(E): e["id"] = f"e{i+1:03d}"

out = dict(schemaVersion=1, generatedAt="2026-10-05T12:00:00Z",
           note="Facts gathered from each venue's own website. Hours and dates should be confirmed with the venue. Descriptions and images are not copied; every record links to its source.",
           venues=[{k: v for k, v in venue.items() if v is not None} for venue in venues.values()],
           shows=[{k: v for k, v in s.items() if v is not None or k == "start"} for s in S], events=E)
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "data", "shows.json"), "w"), ensure_ascii=False, indent=1)
print(len(venues), "venues,", len(S), "shows,", len(E), "events;", sum(1 for v in venues.values() if v["hours"]), "venues with hours")
