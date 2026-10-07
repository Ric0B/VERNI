#!/usr/bin/env python3
"""Builds the crawlable pages from data/shows.json: one page per show, venue, city and region, plus sitemap.xml,
robots.txt and 404.html, and a static summary inside index.html for search engines.

    python3 tools/build_site.py [--base https://example.ch/path]

Run it after every change to data/shows.json (the refresh task does). Generated folders (shows/, venues/, city/, region/)
are deleted and recreated each time, so a show that ended simply disappears. Only the Python standard library is used."""
import argparse, datetime as dt, html, json, re, shutil, sys, urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "https://ric0b.github.io/VERNI"

REGIONS = {"basel": "Basel Region", "zurich": "Zurich Region", "lake-geneva": "Lake Geneva", "bern": "Bern", "central": "Central Switzerland", "ticino": "Ticino"}
CITIES = {  # id: (name, region, country code)
    "basel": ("Basel", "basel", "CH"), "riehen": ("Riehen", "basel", "CH"), "muenchenstein": ("Münchenstein", "basel", "CH"), "liestal": ("Liestal", "basel", "CH"),
    "weil": ("Weil am Rhein", "basel", "DE"), "stlouis": ("Saint-Louis", "basel", "FR"), "loerrach": ("Lörrach", "basel", "DE"),
    "zurich": ("Zurich", "zurich", "CH"), "winterthur": ("Winterthur", "zurich", "CH"),
    "geneva": ("Geneva", "lake-geneva", "CH"), "lausanne": ("Lausanne", "lake-geneva", "CH"), "vevey": ("Vevey", "lake-geneva", "CH"),
    "bern": ("Bern", "bern", "CH"), "lucerne": ("Lucerne", "central", "CH"), "lugano": ("Lugano", "ticino", "CH"),
    "nyon": ("Nyon", "lake-geneva", "CH"), "baden": ("Baden", "zurich", "CH"), "solothurn": ("Solothurn", "bern", "CH"),
    "locarno": ("Locarno", "ticino", "CH"), "neuchatel": ("Neuchâtel", "bern", "CH"),
}
KIND_LABEL = {"film": "Film festival", "media-art": "Media art & technology festival", "photography": "Photography festival", "performance": "Performance festival", "art-week": "Art week", "other": "Festival"}
TYPE_SINGULAR = {"gallery": "Gallery", "institution": "Institution", "foundation": "Foundation / private collection", "offspace": "Off-space"}
TYPE_PLURAL = {"gallery": "Galleries", "institution": "Institutions", "foundation": "Foundations & private collections", "offspace": "Off-spaces"}
EVENT_LABEL = {"opening": "Opening", "finissage": "Finissage", "talk": "Talk", "tour": "Tour", "performance": "Performance"}
DAYS = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ZURICH = ZoneInfo("Europe/Zurich")

esc = lambda s: html.escape(str(s), quote=True)


def host(url):
    return re.sub(r"^www[.]", "", urllib.parse.urlparse(url).netloc)


def directions(v):
    return "https://www.google.com/maps/dir/?api=1&travelmode=walking&destination=" + urllib.parse.quote(f"{v['name']}, {v['address']}")


def fmt_date(iso, year=True):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')}" + (f" {d.year}" if year else "")


def date_range(show):
    if not show.get("start"):
        return "until " + fmt_date(show["end"])
    same_year = show["start"][:4] == show["end"][:4]
    return f"{fmt_date(show['start'], not same_year)} – {fmt_date(show['end'])}"


# ---------- calendar files (.ics) ----------
def ics_text(t):
    return str(t).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics_fold(line):
    out, b = [], line.encode("utf-8")
    while len(b) > 74:
        cut = 74
        while cut > 0 and (b[cut] & 0xC0) == 0x80:  # never split a multi-byte character
            cut -= 1
        out.append(b[:cut].decode("utf-8")); b = b[cut:]
        b = b" " + b
    out.append(b.decode("utf-8"))
    return "\r\n".join(out)


def ics_calendar(name, events):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Weekly VERNI//Listings//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{ics_text(name)}", "X-WR-TIMEZONE:Europe/Zurich"]
    for ev in events:
        lines += ev
    lines.append("END:VCALENDAR")
    return "\r\n".join(ics_fold(l) for l in lines) + "\r\n"


def compact(d):
    return d.replace("-", "")


def hours_text(v):
    hours = v.get("hours")
    if not hours:
        return "See the venue's website"
    short = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    def clock(h):
        w, m = int(h), round((h - int(h)) * 60)
        return f"{w}:{m:02d}" if m else str(w)
    def rng(days):
        days, out, s, p = sorted(days), [], None, None
        for x in days + [99]:
            if s is None: s = p = x; continue
            if x == p + 1: p = x; continue
            out.append(short[s] if s == p else f"{short[s]}–{short[p]}"); s = p = x
        return ", ".join(out)
    return " · ".join(f"{rng(h['days'])} {clock(h['open'])}–{clock(h['close'])}" for h in hours)


def slug_path(kind, id_):
    return f"{kind}/{id_}/"


def split_address(addr):
    m = re.match(r"^(.*?),\s*(\d{4,5})\s+(.+)$", addr)
    return m.groups() if m else (addr, None, None)


def iso_local(date_iso, time_str):
    """2026-10-10 + 18:00 -> 2026-10-10T18:00:00+02:00 (Swiss time, with the right daylight-saving offset)."""
    y, mo, d = map(int, date_iso.split("-"))
    hh, mm = map(int, time_str.split(":"))
    return dt.datetime(y, mo, d, hh, mm, tzinfo=ZURICH).isoformat()


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"


class Site:
    def __init__(self, data, base):
        self.base = base.rstrip("/")
        self.data = data
        self.venues = {v["id"]: v for v in data["venues"]}
        self.shows = data["shows"]
        self.events = data["events"]
        self.festivals = data.get("festivals", [])
        self.generated = data["generatedAt"]
        self.updated = dt.datetime.fromisoformat(self.generated.replace("Z", "+00:00")).astimezone(ZURICH)
        self.pages = []  # (relative url, lastmod)
        self.out = ROOT

    # ---------- helpers ----------
    def city_label(self, cid):
        name, _, cc = CITIES[cid]
        return name + (f" ({cc})" if cc != "CH" else "")

    def show_title(self, s):
        names = ", ".join(s["artists"]) or s["title"]
        sub = "" if not s["artists"] or s["title"] in ("", names) else s["title"]
        return names, sub

    def shows_at(self, vid):
        return sorted((s for s in self.shows if s["venue"] == vid), key=lambda s: (s.get("start") or "0000", s["end"]))

    def events_for_venue(self, vid):
        return sorted((e for e in self.events if e["venue"] == vid), key=lambda e: (e["date"], e.get("time", "")))

    def url(self, rel):
        return f"{self.base}/{rel}"

    # ---------- calendar ----------
    def stamp(self):
        return dt.datetime.fromisoformat(self.generated.replace("Z", "+00:00")).astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def ev_allday(self, uid, summary, start_iso, end_iso, v, url, description, alarm=None):
        """An all-day event from start to end (both inclusive). alarm: ISO-8601 duration after midnight of the start day."""
        end_excl = (dt.date.fromisoformat(end_iso) + dt.timedelta(days=1)).isoformat()
        lines = ["BEGIN:VEVENT", f"UID:{uid}@verni", f"DTSTAMP:{self.stamp()}", f"DTSTART;VALUE=DATE:{compact(start_iso)}", f"DTEND;VALUE=DATE:{compact(end_excl)}",
                 f"SUMMARY:{ics_text(summary)}", f"LOCATION:{ics_text(v['name'] + ', ' + v['address'])}", f"GEO:{v['lat']};{v['lon']}", "TRANSP:TRANSPARENT"]
        if url:
            lines.append(f"URL:{url}")
        lines.append(f"DESCRIPTION:{ics_text(description)}")
        if alarm:
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{ics_text(summary)}", f"TRIGGER;RELATED=START:{alarm}", "END:VALARM"]
        return lines + ["END:VEVENT"]

    def ev_timed(self, e):
        v = self.venues[e["venue"]]
        start = dt.datetime.fromisoformat(iso_local(e["date"], e["time"]))
        end = start + dt.timedelta(hours=1)
        utc = lambda d: d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        label = EVENT_LABEL.get(e["type"], "Talk")
        summary = f"{label}: {e['title']}" if e["type"] not in ("opening", "finissage") else f"{label}: {self.event_subject(e)}"
        lines = ["BEGIN:VEVENT", f"UID:event-{e['id']}@verni", f"DTSTAMP:{self.stamp()}", f"DTSTART:{utc(start)}", f"DTEND:{utc(end)}", f"SUMMARY:{ics_text(summary)} · {ics_text(v['name'])}",
                 f"LOCATION:{ics_text(v['name'] + ', ' + v['address'])}", f"GEO:{v['lat']};{v['lon']}"]
        if e.get("url"):
            lines.append(f"URL:{e['url']}")
        lines += [f"DESCRIPTION:{ics_text('Listed by Weekly VERNI. The end time is not published, so one hour is assumed. Confirm with the venue.')}",
                  "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{ics_text(summary)} starts in 1 hour", "TRIGGER:-PT1H", "END:VALARM", "END:VEVENT"]
        return lines

    def event_subject(self, e):
        s = next((x for x in self.shows if x["id"] == e.get("show")), None)
        return self.show_title(s)[0] if s else e["title"]

    def closing_day(self, s):
        """The day to remind about a closing show: three days before the last day, or the last day itself if that is closer."""
        today = dt.date.fromisoformat(self.generated[:10])
        end = dt.date.fromisoformat(s["end"])
        if end < today:
            return None
        return max(today, end - dt.timedelta(days=3)).isoformat()

    def write_ics(self, rel, name, events):
        path = self.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(ics_calendar(name, events).encode("utf-8"))

    def show_calendars(self, s):
        v = self.venues[s["venue"]]
        names, sub = self.show_title(s)
        label = names + (f": {sub}" if sub else "")
        desc = f"{label} at {v['name']}. {date_range(s)}. Listed by Weekly VERNI; confirm dates and hours with the venue." + (f" Details: {s['url']}" if s.get("url") else "")
        base = slug_path("shows", s["id"])
        out = {}
        if s.get("start"):
            self.write_ics(base + "run.ics", label, [self.ev_allday(f"show-{s['id']}-run", f"{label} · {v['name']}", s["start"], s["end"], v, s.get("url"), desc)])
            out["run"] = base + "run.ics"
        day = self.closing_day(s)
        if day:
            self.write_ics(base + "closing.ics", "Closing reminder", [self.ev_allday(
                f"show-{s['id']}-closing", f"Last days: {label} closes {fmt_date(s['end'], False)}", day, day, v, s.get("url"),
                f"{label} at {v['name']} is on until {fmt_date(s['end'])}. Opening hours: {hours_text(v)}.", alarm="PT9H")])
            out["closing"] = base + "closing.ics"
        return out

    def google_link(self, s):
        v = self.venues[s["venue"]]
        names, sub = self.show_title(s)
        end_excl = (dt.date.fromisoformat(s["end"]) + dt.timedelta(days=1)).isoformat()
        q = urllib.parse.urlencode({"action": "TEMPLATE", "text": f"{names}{': ' + sub if sub else ''} · {v['name']}", "dates": f"{compact(s['start'])}/{compact(end_excl)}",
                                    "details": (s.get("url") or ""), "location": f"{v['name']}, {v['address']}"})
        return "https://calendar.google.com/calendar/render?" + q

    def calendar_files(self):
        for e in self.events:
            if e.get("time"):
                self.write_ics(f"events/{e['id']}.ics", e["title"], [self.ev_timed(e)])
        self.write_ics("calendar/events.ics", "Weekly VERNI: openings and events", [self.ev_timed(e) for e in self.events if e.get("time")])

    # ---------- festivals ----------
    def fest_place(self, f):
        return {"name": f.get("place") or CITIES[f["city"]][0], "address": CITIES[f["city"]][0] + ", Switzerland", "lat": f["lat"], "lon": f["lon"]}

    def festival_calendars(self, f):
        base = slug_path("festivals", f["id"])
        place = self.fest_place(f)
        desc = f"{f['name']}, {date_range(f)}, {place['name']}. Listed by Weekly VERNI; check the festival's website for the programme. {f['url']}"
        self.write_ics(base + "run.ics", f["name"], [self.ev_allday(f"festival-{f['id']}-run", f["name"], f["start"], f["end"], place, f["url"], desc)])
        today = dt.date.fromisoformat(self.generated[:10])
        out = {"run": base + "run.ics"}
        if dt.date.fromisoformat(f["start"]) >= today:
            day = max(today, dt.date.fromisoformat(f["start"]) - dt.timedelta(days=7)).isoformat()
            self.write_ics(base + "reminder.ics", "Festival reminder", [self.ev_allday(
                f"festival-{f['id']}-reminder", f"Starts {fmt_date(f['start'], False)}: {f['name']}", day, day, place, f["url"],
                f"{f['name']} runs {date_range(f)}. Programme and tickets: {f['url']}", alarm="PT9H")])
            out["reminder"] = base + "reminder.ics"
        return out

    def festival_page(self, f):
        rel = slug_path("festivals", f["id"])
        place = self.fest_place(f)
        cal = self.festival_calendars(f)
        kind = KIND_LABEL.get(f["kind"], "Festival")
        dr = date_range(f)
        title = f"{f['name']}, {dr}, {CITIES[f['city']][0]}"
        desc = f"{f['name']} in {CITIES[f['city']][0]}, {dr}. Dates, place and link to the official programme."
        end_excl = (dt.date.fromisoformat(f["end"]) + dt.timedelta(days=1)).isoformat()
        gcal = "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode({"action": "TEMPLATE", "text": f["name"], "dates": f"{compact(f['start'])}/{compact(end_excl)}", "details": f["url"], "location": place["name"]})
        btns = f'<a class="btn" href="{esc(f["url"])}" rel="noopener">Official site: {esc(host(f["url"]))}</a><a class="btn ghost" href="run.ics" download>Add to calendar</a><a class="btn ghost" href="{esc(gcal)}" rel="noopener">Google Calendar</a>'
        if cal.get("reminder"):
            btns += '<a class="btn ghost" href="reminder.ics" download>Remind me a week before</a>'
        body = f"""<nav class="crumbs" aria-label="Breadcrumb"><a href="../../">Home</a> › <a href="../">Festivals</a></nav>
<article class="detail"><div class="page-h"><div class="kicker">{esc(kind)} · {esc(CITIES[f['city']][0])}</div><h1>{esc(f['name'])}</h1></div>
<dl class="kv"><dt>Dates</dt><dd>{esc(dr)}</dd><dt>Place</dt><dd>{esc(place['name'])}</dd><dt>Website</dt><dd><a href="{esc(f['url'])}" rel="noopener">{esc(host(f['url']))}</a></dd></dl>
<p class="mute sm">Dates as published by the festival. Check its website for the programme, venues and tickets.</p>
<div class="btnrow">{btns}</div>
<div class="btnrow"><a class="btn ghost" href="../../#switzerland.festival.{esc(f['id'])}">Open in the app</a></div></article>"""
        jsonld = [{"@context": "https://schema.org", "@type": "Festival", "name": f["name"], "startDate": f["start"], "endDate": f["end"], "url": self.url(rel), "sameAs": f["url"],
                   "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                   "location": {"@type": "Place", "name": place["name"], "address": {"@type": "PostalAddress", "addressLocality": CITIES[f["city"]][0], "addressCountry": CITIES[f["city"]][2]},
                               "geo": {"@type": "GeoCoordinates", "latitude": f["lat"], "longitude": f["lon"]}}}]
        self.write(rel, self.shell(rel, 2, title + " | Weekly VERNI", desc, body, jsonld))

    def festivals_index(self):
        rel = "festivals/"
        fs = sorted(self.festivals, key=lambda f: (f["start"], f["name"]))
        rows = "".join(f'<a class="vrow" href="{f["id"]}/"><span class="nm">{esc(f["name"])}</span><span class="ct">{esc(date_range(f))}</span><span class="ad">{esc(KIND_LABEL.get(f["kind"], "Festival"))} · {esc(CITIES[f["city"]][0])}</span><span></span></a>' for f in fs)
        body = f"""<nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a></nav><div class="detail wide"><div class="page-h"><div class="kicker">Swiss festivals</div><h1>Festivals</h1></div>
<p class="mute">Film festivals and festivals for art, media and performance across Switzerland.</p>{rows or '<p class="empty">No festivals listed yet.</p>'}</div>"""
        items = [{"@type": "ListItem", "position": i + 1, "url": self.url(slug_path("festivals", f["id"])), "name": f["name"]} for i, f in enumerate(fs)]
        self.write(rel, self.shell(rel, 1, "Festivals in Switzerland: film, media art and performance | Weekly VERNI", f"{len(fs)} film festivals and art festivals in Switzerland with dates and links.", body,
                                   [{"@context": "https://schema.org", "@type": "ItemList", "name": "Festivals in Switzerland", "itemListElement": items}]))

    # ---------- page shell ----------
    def shell(self, rel, depth, title, desc, body, jsonld=(), kicker_noindex=False):
        up = "../" * depth
        og = f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website">' \
             f'<meta property="og:url" content="{esc(self.url(rel))}"><meta property="og:image" content="{esc(self.base)}/assets/icons/icon-512.png"><meta name="twitter:card" content="summary">'
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(self.url(rel))}">
{og}
<meta name="theme-color" content="#f1f0f4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0e0d13" media="(prefers-color-scheme: dark)">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'">
<link rel="manifest" href="{up}manifest.webmanifest">
<link rel="icon" type="image/png" href="{up}assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="{up}assets/icons/apple-touch-icon.png">
<link rel="stylesheet" href="{up}assets/fonts.css">
<link rel="stylesheet" href="{up}assets/style.css">
{''.join(ld(j) for j in jsonld)}
</head>
<body class="static">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="brand" href="{up}" aria-label="Weekly VERNI, home">VERNI</a>
  <nav class="slinks" aria-label="Main"><a href="{up}#switzerland">Shows</a><a href="{up}#switzerland.events">Events</a><a href="{up}#switzerland.map">Map</a><a href="{up}#switzerland.venues">Venues</a></nav>
</header>
<main id="main" class="page">
{body}
</main>
<footer class="page">
  <nav aria-label="Footer"><a href="{up}">Home</a><a href="{up}#switzerland.about">About</a></nav>
  <span>Listings gathered from the venues' own websites, updated {self.updated.strftime('%-d %b %Y, %H:%M')}. Confirm dates and hours with the venue.</span>
</footer>
</body>
</html>
"""

    def write(self, rel, content, lastmod=None, index=True):
        path = self.out / rel / "index.html" if rel.endswith("/") else self.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if index:
            self.pages.append((rel, lastmod or self.generated[:10]))

    # ---------- show page ----------
    def show_page(self, s):
        v = self.venues[s["venue"]]
        names, sub = self.show_title(s)
        city = self.city_label(v["city"])
        rel = slug_path("shows", s["id"])
        events = [e for e in self.events if e.get("show") == s["id"]]
        others = [x for x in self.shows_at(v["id"]) if x["id"] != s["id"]]
        dr = date_range(s)
        cal = self.show_calendars(s)
        title = f"{names}{': ' + sub if sub else ''} · {v['name']}, {city}"
        desc = f"{names}{', ' + sub if sub else ''} at {v['name']} in {city}, {dr}. Address, opening hours and directions."
        maps = directions(v)
        detail_btn = f'<a class="btn" href="{esc(s["url"])}" rel="noopener">Details on {esc(host(s["url"]))}</a>' if s.get("url") else ""
        cal_btns = ""
        if cal.get("run"):
            cal_btns += f'<a class="btn ghost" href="run.ics" download>Add to calendar</a><a class="btn ghost" href="{esc(self.google_link(s))}" rel="noopener">Google Calendar</a>'
        if cal.get("closing"):
            cal_btns += '<a class="btn ghost" href="closing.ics" download>Remind me before it closes</a>'
        sub_html = f'<div class="sub">{esc(sub)}</div>' if sub else ""
        others_html = ("<h2 class=\"sec-h\">Also at " + esc(v["name"]) + "</h2>" + "".join(self.show_row(x, "../../") for x in others)) if others else ""
        events_block = self.events_html(events, "../../") if events else ""
        kv = [("Venue", f'<a href="../../{slug_path("venues", v["id"])}"><b>{esc(v["name"])}</b></a><br>{esc(v["address"])}'),
              ("Dates", esc(dr)), ("Hours", esc(hours_text(v)) + '<br><span class="mute sm">As listed on the venue\'s website. Confirm with the venue.</span>')]
        if s["artists"]:
            kv.append(("Artists", esc(", ".join(s["artists"]))))
        kv_html = "".join(f"<dt>{k}</dt><dd>{val}</dd>" for k, val in kv)
        body = f"""<nav class="crumbs" aria-label="Breadcrumb"><a href="../../">Home</a> › <a href="../../{slug_path('city', v['city'])}">{esc(CITIES[v['city']][0])}</a> › <a href="../../{slug_path('venues', v['id'])}">{esc(v['name'])}</a></nav>
<article class="detail">
<div class="page-h"><div class="kicker">{esc(TYPE_SINGULAR[v['type']])} · {esc(city)}</div><h1>{esc(names)}</h1>{sub_html}</div>
<dl class="kv">{kv_html}</dl>
<div class="btnrow">{detail_btn}
<a class="btn ghost" href="{esc(maps)}" rel="noopener">Walking directions</a>
<a class="btn ghost" href="../../#switzerland.show.{esc(s['id'])}">Plan this in the app</a></div>
<div class="btnrow">{cal_btns}</div>
{events_block}
{others_html}
</article>"""
        crumbs = {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": self.url("")},
            {"@type": "ListItem", "position": 2, "name": CITIES[v["city"]][0], "item": self.url(slug_path("city", v["city"]))},
            {"@type": "ListItem", "position": 3, "name": v["name"], "item": self.url(slug_path("venues", v["id"]))},
            {"@type": "ListItem", "position": 4, "name": names}]}
        jsonld = [crumbs]
        if s.get("start"):  # an Event needs a start date; without one we only publish the page
            event = {"@context": "https://schema.org", "@type": "ExhibitionEvent", "name": f"{names}{': ' + sub if sub else ''}",
                     "startDate": s["start"], "endDate": s["end"], "eventStatus": "https://schema.org/EventScheduled",
                     "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "url": self.url(rel),
                     "location": self.place_ld(v), "description": f"{names}{', ' + sub if sub else ''} at {v['name']}, {dr}."}
            if s["artists"]:
                event["performer"] = [{"@type": "Person", "name": a} for a in s["artists"]]
            if s.get("url"):
                event["sameAs"] = s["url"]
            jsonld.append(event)
        self.write(rel, self.shell(rel, 2, title + " | Weekly VERNI", desc, body, jsonld))

    def place_ld(self, v):
        street, postal, locality = split_address(v["address"])
        place = {"@type": "Museum" if v["type"] in ("institution", "foundation") else "ArtGallery", "name": v["name"],
                 "address": {"@type": "PostalAddress", "streetAddress": street, "addressCountry": CITIES[v["city"]][2],
                             **({"postalCode": postal, "addressLocality": locality} if postal else {"addressLocality": CITIES[v["city"]][0]})},
                 "geo": {"@type": "GeoCoordinates", "latitude": v["lat"], "longitude": v["lon"]}}
        if v.get("website"):
            place["url"] = v["website"]
        return place

    def events_html(self, events, up):
        rows = []
        for e in sorted(events, key=lambda e: (e["date"], e.get("time", ""))):
            when = fmt_date(e["date"]) + (", " + e["time"] if e.get("time") else "")
            add = f'<br><a class="sm" href="{up}events/{esc(e["id"])}.ics" download>Add to calendar with reminder</a>' if e.get("time") else ""
            rows.append(f'<div class="vrow"><span><b>{esc(when)}</b><br><span class="mute sm">{esc(e["title"])}</span>{add}</span><span><span class="tag t-{esc(EVENT_LABEL.get(e["type"], "Talk"))}">{esc(EVENT_LABEL.get(e["type"], "Talk"))}</span></span></div>')
        return '<h2 class="sec-h">Events</h2>' + "".join(rows)

    def show_row(self, s, up):
        names, sub = self.show_title(s)
        v = self.venues[s["venue"]]
        return (f'<a class="vrow" href="{up}{slug_path("shows", s["id"])}"><span class="nm">{esc(names)}{"<br><i>" + esc(sub) + "</i>" if sub else ""}</span>'
                f'<span class="ct">{esc(date_range(s))}</span><span class="ad">{esc(v["name"])} · {esc(CITIES[v["city"]][0])}</span><span></span></a>')

    # ---------- venue page ----------
    def venue_page(self, v):
        rel = slug_path("venues", v["id"])
        city = self.city_label(v["city"])
        shows = self.shows_at(v["id"])
        events = self.events_for_venue(v["id"])
        title = f"{v['name']} · {TYPE_SINGULAR[v['type']]} in {city}"
        desc = f"{v['name']}, {v['address']}. Current and upcoming exhibitions and events, opening hours and directions."
        osm = f"https://www.openstreetmap.org/?mlat={v['lat']}&mlon={v['lon']}#map=17/{v['lat']}/{v['lon']}"
        maps = directions(v)
        site = f'<a href="{esc(v["website"])}" rel="noopener">{esc(host(v["website"]))}</a>' if v.get("website") else "Not listed"
        shows_html = "".join(self.show_row(x, "../../") for x in shows) if shows else '<p class="empty">No shows listed right now. Check the venue\'s website.</p>'
        events_block = self.events_html(events, "../../") if events else ""
        approx = '<br><span class="mute sm">Map position is approximate.</span>' if v.get("geoApprox") else ""
        body = f"""<nav class="crumbs" aria-label="Breadcrumb"><a href="../../">Home</a> › <a href="../../{slug_path('city', v['city'])}">{esc(CITIES[v['city']][0])}</a></nav>
<article class="detail">
<div class="page-h"><div class="kicker">{esc(TYPE_SINGULAR[v['type']])} · {esc(city)}</div><h1>{esc(v['name'])}</h1></div>
<dl class="kv"><dt>Address</dt><dd>{esc(v['address'])}<br><a href="{esc(maps)}" rel="noopener">Walking directions</a> · <a href="{esc(osm)}" rel="noopener">Map</a>{approx}</dd>
<dt>Hours</dt><dd>{esc(hours_text(v))}<br><span class="mute sm">As listed on the venue's website. Confirm with the venue.</span></dd>
<dt>Website</dt><dd>{site}</dd></dl>
<h2 class="sec-h">Current &amp; upcoming</h2>
{shows_html}
{events_block}
<div class="btnrow"><a class="btn ghost" href="../../#switzerland.venue.{esc(v['id'])}">Open in the app</a></div>
</article>"""
        jsonld = [self.place_ld(v) | {"@context": "https://schema.org"} | ({"openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": [DAYS[d] for d in h["days"]], "opens": f"{int(h['open']):02d}:{round((h['open'] % 1) * 60):02d}",
             "closes": f"{int(h['close']):02d}:{round((h['close'] % 1) * 60):02d}"} for h in v["hours"]]} if v.get("hours") else {}),
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": self.url("")},
                {"@type": "ListItem", "position": 2, "name": CITIES[v["city"]][0], "item": self.url(slug_path("city", v["city"]))},
                {"@type": "ListItem", "position": 3, "name": v["name"]}]}]
        self.write(rel, self.shell(rel, 2, title + " | Weekly VERNI", desc, body, jsonld))

    # ---------- city and region pages ----------
    def place_page(self, kind, pid, name, venue_ids, intro):
        rel = slug_path(kind, pid)
        shows = sorted((s for s in self.shows if s["venue"] in venue_ids), key=lambda s: (s["end"], s.get("start") or ""))
        venues = sorted((self.venues[i] for i in venue_ids), key=lambda v: v["name"].lower())
        title = f"Art exhibitions in {name}: what is on now"
        desc = f"{len(shows)} current and upcoming exhibitions at {len(venues)} galleries, museums and art spaces in {name}. {intro}"
        body = f"""<nav class="crumbs" aria-label="Breadcrumb"><a href="../../">Home</a></nav>
<div class="detail wide"><div class="page-h"><div class="kicker">Contemporary art</div><h1>{esc(name)}</h1></div>
<p class="mute">{esc(intro)}</p>
<h2 class="sec-h">Exhibitions ({len(shows)})</h2>
{''.join(self.show_row(s, '../../') for s in shows) if shows else '<p class="empty">No shows listed right now.</p>'}
<h2 class="sec-h">Venues ({len(venues)})</h2>
{''.join(f'<a class="vrow" href="../../{slug_path("venues", v["id"])}"><span class="nm">{esc(v["name"])}</span><span class="ct">{esc(TYPE_SINGULAR[v["type"]])}</span><span class="ad">{esc(v["address"])}</span><span></span></a>' for v in venues)}
<div class="btnrow"><a class="btn ghost" href="../../#{'region-' + pid if kind == 'region' else pid}">Open in the app</a></div></div>"""
        items = [{"@type": "ListItem", "position": i + 1, "url": self.url(slug_path("shows", s["id"])), "name": ", ".join(s["artists"]) or s["title"]} for i, s in enumerate(shows)]
        self.write(rel, self.shell(rel, 2, title + " | Weekly VERNI", desc, body, [{"@context": "https://schema.org", "@type": "ItemList", "name": f"Exhibitions in {name}", "itemListElement": items}]))

    # ---------- home summary, 404, sitemap, robots ----------
    def home_summary(self):
        by_city = {}
        for s in self.shows:
            by_city.setdefault(self.venues[s["venue"]]["city"], []).append(s)
        festivals = "".join(f'<li><a href="{slug_path("festivals", f["id"])}">{esc(f["name"])}</a>, {esc(CITIES[f["city"]][0])}, {esc(date_range(f))}</li>' for f in sorted(self.festivals, key=lambda f: f["start"]))
        regions = "".join(f'<li><a href="{slug_path("region", r)}">{esc(n)}</a></li>' for r, n in REGIONS.items())
        cities = "".join(f'<li><a href="{slug_path("city", c)}">{esc(CITIES[c][0])}</a> <span class="mute">{len(by_city.get(c, []))}</span></li>' for c in CITIES if by_city.get(c))
        shows = "".join(f'<li><a href="{slug_path("shows", s["id"])}">{esc(self.show_title(s)[0])}</a>, {esc(self.venues[s["venue"]]["name"])}, {esc(date_range(s))}</li>'
                        for s in sorted(self.shows, key=lambda s: s["end"]))
        return f"""<!--SSR:START-->
<div class="page ssr"><div class="page-h"><div class="kicker">Weekly VERNI</div><h1>Contemporary art in Switzerland</h1></div>
<p>Exhibitions, openings and events at galleries, museums and art spaces from Basel to Lugano, gathered from the venues' own websites and updated twice a week.</p>
<p><a href="calendar/events.ics" download>Calendar file with every opening and event</a>, each with a reminder one hour before. Add it once to your calendar app.</p>
<h2 class="sec-h"><a href="festivals/">Festivals</a></h2><ul>{festivals}</ul>
<h2 class="sec-h">Regions</h2><ul>{regions}</ul><h2 class="sec-h">Cities</h2><ul>{cities}</ul>
<h2 class="sec-h">On view and coming up</h2><ul>{shows}</ul></div>
<!--SSR:END-->"""

    def patch_index(self):
        p = self.out / "index.html"
        s = p.read_text(encoding="utf-8")
        summary = self.home_summary()
        if "<!--SSR:START-->" in s:
            s = re.sub(r"<!--SSR:START-->.*?<!--SSR:END-->", lambda _m: summary, s, flags=re.S)
        else:
            s = s.replace('<p class="page loading" id="loading">Loading listings…</p>', f'<div id="loading">{summary}</div>')
        canonical = f'<link rel="canonical" href="{self.base}/">'
        s = re.sub(r'<link rel="canonical" href="[^"]*">', canonical, s) if 'rel="canonical"' in s else s.replace('<link rel="manifest"', canonical + '\n<link rel="manifest"', 1)
        site_ld = ld({"@context": "https://schema.org", "@type": "WebSite", "name": "Weekly VERNI", "url": self.base + "/",
                      "description": "Exhibitions, openings and events in contemporary art across Switzerland."})
        s = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", s, flags=re.S)
        s = s.replace("</head>", site_ld + "\n</head>", 1)
        p.write_text(s, encoding="utf-8")

    def not_found(self):
        body = '<div class="page-h"><h1>Page not found</h1></div><p class="mute">That page is not here. Shows end, and their pages go with them.</p><div class="btnrow"><a class="btn" href="/VERNI/">See what is on now</a></div>'
        (self.out / "404.html").write_text(self.shell("404.html", 0, "Page not found | Weekly VERNI", "Page not found", body).replace(f'<link rel="canonical" href="{self.url("404.html")}">', ""), encoding="utf-8")

    def sitemap(self):
        urls = [("", self.generated[:10])] + self.pages
        xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        xml += [f"<url><loc>{esc(self.url(rel))}</loc><lastmod>{lm}</lastmod></url>" for rel, lm in urls]
        xml.append("</urlset>")
        (self.out / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
        (self.out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {self.base}/sitemap.xml\n", encoding="utf-8")

    def build(self):
        for d in ("shows", "venues", "city", "region", "events", "calendar", "festivals"):
            shutil.rmtree(self.out / d, ignore_errors=True)
        for f in self.festivals:
            self.festival_page(f)
        self.festivals_index()
        for s in self.shows:
            self.show_page(s)
        for v in self.venues.values():
            self.venue_page(v)
        by_city = {}
        for v in self.venues.values():
            by_city.setdefault(v["city"], []).append(v["id"])
        for cid, ids in by_city.items():
            self.place_page("city", cid, CITIES[cid][0], ids, f"Galleries, museums and art spaces in {CITIES[cid][0]} and what is on at each.")
        for rid, name in REGIONS.items():
            ids = [v["id"] for v in self.venues.values() if CITIES[v["city"]][1] == rid]
            if ids:
                self.place_page("region", rid, name, ids, f"Galleries, museums and art spaces across the {name}.")
        self.calendar_files()
        self.patch_index()
        self.not_found()
        self.sitemap()
        return len(self.pages)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE)
    a = ap.parse_args()
    site = Site(json.loads((ROOT / "data" / "shows.json").read_text(encoding="utf-8")), a.base)
    n = site.build()
    print(f"built {n} pages ({len(site.shows)} shows, {len(site.venues)} venues) for {site.base}")
