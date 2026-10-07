# Weekly refresh: instructions for the gathering agent

Purpose: keep `data/shows.json` current so the Weekly VERNI app (iPhone, and later web) always shows what is on now.
The app downloads this file from the repository's `main` branch. It only accepts a file whose `generatedAt` is newer than the one it has, so a bad run can never make the app older, but a bad file that looks valid will be shown to everyone. Be careful, not fast.

## Steps

1. Read `data/shows.json`. Every venue has `website` and, where known, `sourceURL` (the page that worked last time).
2. For each venue, open its exhibitions / programme page. If the page returns little or nothing, the site is probably built with JavaScript. Try the program page, the "current" or "upcoming" subpages, a sitemap, or a web search for the venue name plus the month. Spend a few attempts per venue, then move on.
3. Collect only facts: artist(s), exhibition title, start date, end date, opening hours, and events with a date and time (openings, finissages, talks, guided tours, performances). Link each record to the venue's own page for it in `url`.
4. Merge into the existing file:
   - Update records whose dates changed. Keep their `id`.
   - Add new exhibitions and events. New ids: `<venue>-<slug of title or artists>`; events `e` + number.
   - Remove exhibitions that ended before yesterday and events in the past.
   - If a venue's page could not be read this week, **keep its existing records**. Never delete because a fetch failed.
5. Set `generatedAt` to the current UTC time (`2026-10-12T06:00:00Z` format).
6. Run `python3 tools/validate_data.py`. Fix every ERROR. Read the warnings.
7. Run `python3 tools/build_site.py`. It regenerates the pages for search engines, the sitemap and the calendar files from the data file.
8. Commit everything (`git add -A`) with a message like `Refresh 2026-10-12: 71 shows, 34 events` and push to `main`. (The iPhone app keeps its own bundled copy as an offline fallback; that copy only changes when a new app version is released.)
9. Reply with a short report: how many venues were read, which failed, what changed, and anything you were unsure about.

## Rules

- **Check you are on the right venue.** The first thing on the page should be the venue's name and address. If it is a different organisation, or the address differs from the file, flag it instead of copying. Venues move (Nicolas Krupp, MAMCO and Haus Konstruktiv all have since 2024); update `address` when a page says so, and set `geoApprox` to true if you have to estimate `lat`/`lon`.
- **Do not copy descriptions, press texts or images.** Facts and links only.
- **Do not guess.** If a start date is not shown, leave `start` null (the show is then treated as already open). If an end date is not shown, skip the show. If you are unsure of a field, leave the record out and mention it in the report.
- Permanent collection displays and festival side programmes are not exhibitions; leave them out unless the venue presents them as a dated show.
- Hours: store only what the page states. `days` use 1 = Monday to 7 = Sunday; `open`/`close` are decimal hours (18.5 = 18:30). Leave `hours` out when not stated.
- Event `type` is one of `opening`, `finissage`, `talk`, `tour`, `performance`. Use `opening` for a vernissage.
- Be polite to the websites: one visit per page, no loops, no more than a few requests per venue.
- Dates are ISO `yyyy-mm-dd`. Times are 24-hour `HH:MM` local Swiss time.

## Venues that need extra attention (no or weak data on 2026-10-05)

Pages that returned little because of JavaScript or errors: Kunsthalle Basel, Schaulager, Weiss Falk, Galerie Gisèle Linder, Kunsthalle Palazzo, Ausstellungsraum Klingental, Oslo10, Kilchmann, Francesca Pia (only archive shown), Hauser & Wirth Zürich, Helmhaus, LUMA Westbau, Römerholz, Kunsthalle Winterthur (closed for renovation until Dec 2026), Centre d'Art Contemporain Genève, MAH Genève, Andata Ritorno, Galerie Mezzanin, Forde, Circuit, Kunsthalle Luzern (site moved to kunsthalle-luzern.ch), MASI Lugano (blocked automated access), Musée Jenisch (no dates published).

Check these first: Kunsthalle Zürich's dates were not trustworthy (both shows appeared to end on the day of the first run), and Kunsthaus Zürich lists no start dates.

## File format

See `tools/validate_data.py` for the exact rules. Top level: `schemaVersion` (1), `generatedAt`, `note`, `venues`, `shows`, `events`.

- venue: `id, name, type (gallery|institution|foundation|offspace), city, address, website, lat, lon, geoApprox?, hours?, sourceURL?`
- show: `id, venue, artists[], title, start (or null), end, url`
- event: `id, venue, show (id or null), type, title, date, time, url`

Cities are the ids in `WeeklyVerni/Models.swift` (`basel`, `riehen`, `muenchenstein`, `liestal`, `weil`, `stlouis`, `loerrach`, `zurich`, `winterthur`, `geneva`, `lausanne`, `vevey`, `bern`, `lucerne`, `lugano`). Group or collection shows have no artists; the title is then shown as the headline.

## Festivals

`data/shows.json` has a `festivals` list: film festivals and festivals for art, media, photography and performance (for example MESH in Basel). Music-only festivals and trade fairs are out of scope.

- Record: `id, name, kind (film|media-art|photography|performance|art-week|other), city, place, lat, lon, start, end, url`. The `url` is the festival's own site. `city` is one of the ids used for venues, plus `nyon`, `baden`, `solothurn`, `locarno`, `neuchatel`.
- Festivals already in the list: keep them current. Read the festival's own site; if dates changed, update them. When an edition has ended, replace it with the next edition once the festival has published it, otherwise remove it.
- Never guess dates. If an official site does not state them, leave the record as it is and mention it in your report.

## Discovery: things you may not publish yourself

Everything above (venues already in the file, festivals already in the file) is updated directly. Anything **new** that comes from outside that trusted list goes to `data/candidates.json` for the owner to approve or reject with `python3 tools/curate.py`:

- festivals, shows, events or venues you find through web searches, listings sites, newsletters or press that are not in `data/shows.json`
- anything you are unsure about

Search for: film festivals in Switzerland (all language regions), festivals for media art and technology, photography festivals and biennials, performance and theatre festivals with an art focus, art weeks, and openings or exhibitions at galleries and off-spaces that are not yet listed.

Rules for candidates:
1. Skip anything that is already in `data/shows.json`, or whose key appears in `data/rejected.json` (`kind|slug of name or title|start date`). Rejected items must never come back.
2. Read the candidates already in the file first and do not add duplicates. Remove candidates whose date has passed.
3. Add each as `{"id": "c-<short-slug>", "kind": "festival|show|event|venue", "record": {...same fields as the live data...}, "source": "<page where you found it>", "note": "<what is uncertain, one or two sentences>", "foundAt": "<today>"}`. For a show or event the venue id must already exist; if the venue is new, add a `venue` candidate first.
4. A note is required whenever dates, place or the organiser come from a search result and not from the festival's or venue's own page.
5. `data/candidates.json` is local, not committed, and has the form `{"generatedAt": "...", "candidates": [...]}`.
6. In your report, say how many candidates you added.
