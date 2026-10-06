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
7. Copy the file to `WeeklyVerni/Resources/shows.json` (the copy shipped inside the app) and commit both with a message like `Weekly refresh 2026-10-12: 71 shows, 34 events`. Push to `main`.
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
