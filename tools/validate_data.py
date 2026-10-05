#!/usr/bin/env python3
"""Checks data/shows.json before it is published. Exit code 1 means do not publish.
Usage: python3 tools/validate_data.py [path]   (default data/shows.json)"""
import json, sys, os, re, datetime as dt

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "shows.json")
d = json.load(open(path))
errors, warnings = [], []
today = dt.date.today()

def day(s, where):
    try: return dt.date.fromisoformat(s)
    except Exception: errors.append(f"{where}: bad date {s!r}")

if d.get("schemaVersion") != 1: errors.append("schemaVersion must be 1")
try: gen = dt.datetime.fromisoformat(d["generatedAt"].replace("Z", "+00:00"))
except Exception: errors.append("generatedAt must be an ISO-8601 UTC time like 2026-10-05T12:00:00Z"); gen = None

CITIES = {"basel","riehen","muenchenstein","liestal","weil","stlouis","loerrach","zurich","winterthur","geneva","lausanne","vevey","bern","lucerne","lugano"}
TYPES = {"gallery","institution","foundation","offspace"}
EVENTS = {"opening","finissage","talk","tour","performance"}

vids = set()
for v in d["venues"]:
    if v["id"] in vids: errors.append(f"duplicate venue {v['id']}")
    vids.add(v["id"])
    if v["type"] not in TYPES: errors.append(f"{v['id']}: bad type")
    if v["city"] not in CITIES: errors.append(f"{v['id']}: unknown city {v['city']}")
    if not (45.7 < v["lat"] < 48.0 and 5.9 < v["lon"] < 10.6) and v["city"] not in {"weil","stlouis","loerrach"}: errors.append(f"{v['id']}: coordinates outside Switzerland")
    for h in v.get("hours") or []:
        if not (0 <= h["open"] < h["close"] <= 24) or not h["days"] or any(x < 1 or x > 7 for x in h["days"]): errors.append(f"{v['id']}: bad hours {h}")

sids = set()
for s in d["shows"]:
    w = f"show {s['id']}"
    if s["id"] in sids: errors.append(f"duplicate show id {s['id']}")
    sids.add(s["id"])
    if s["venue"] not in vids: errors.append(f"{w}: unknown venue {s['venue']}")
    e = day(s["end"], w)
    st = day(s["start"], w) if s.get("start") else None
    if e and st and e < st: errors.append(f"{w}: ends before it starts")
    if e and (e < today - dt.timedelta(days=1)): warnings.append(f"{w}: already ended on {e}, drop it")
    if e and e > today + dt.timedelta(days=900): warnings.append(f"{w}: ends more than 2 years out, check")
    if st and (st - today).days > 400: warnings.append(f"{w}: starts more than a year out")
    if not s.get("artists") and not s.get("title"): errors.append(f"{w}: needs an artist or a title")
    if not s.get("url"): warnings.append(f"{w}: missing source url")
    elif not re.match(r"https?://", s["url"]): errors.append(f"{w}: url must be absolute")

for e in d["events"]:
    w = f"event {e['id']}"
    if e["venue"] not in vids: errors.append(f"{w}: unknown venue")
    if e["type"] not in EVENTS: errors.append(f"{w}: bad type {e['type']}")
    if e.get("show") and e["show"] not in sids: errors.append(f"{w}: unknown show {e['show']}")
    x = day(e["date"], w)
    if x and x < today - dt.timedelta(days=1): warnings.append(f"{w}: in the past, drop it")
    if e.get("time") and not re.fullmatch(r"\d\d:\d\d", e["time"]): errors.append(f"{w}: time must be HH:MM")
    if e.get("url") and not re.match(r"https?://", e["url"]): errors.append(f"{w}: url must be absolute")

if len(d["shows"]) < 20: errors.append("fewer than 20 shows: a failed gather must never replace good data")
for w in warnings: print("warning:", w)
for e in errors: print("ERROR:", e)
print(f"{len(d['venues'])} venues, {len(d['shows'])} shows, {len(d['events'])} events, {len(errors)} errors, {len(warnings)} warnings")
sys.exit(1 if errors else 0)
