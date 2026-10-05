# Weekly VERNI: system design

## Requirements

Functional
- Browse what is on in contemporary art in Switzerland: shows (closing soon, opening, on view, coming up), events, venues, artists, a map and a walking route.
- Filter by place (country, region, city), venue type, open now, free-text search.
- Save favourites and build a Tourplan (shortest or own order). Both stay on the visitor's device.
- Mobile first. On laptops the header carries the navigation and list pages get a map beside them.
- Real content only. Nothing is invented: every show and event comes from a venue's own website and links back to it.

Non-functional
- No server to run or pay for. Fast on a phone connection. Works offline from the last copy.
- Accessible: real buttons and links, 44 px targets, visible focus, light and dark themes, reduced motion.
- Self-hosted fonts and map library. The only third-party request is map tiles (OpenStreetMap).

Constraints
- One person, no backend, no build step. Data is gathered by an agent that reads websites.

## Architecture

    venue websites
         |  (twice a week, Claude agent on the owner's Mac)
         v
    data/shows.json  --validated by tools/validate_data.py-->  git push to main
         |
         +--> GitHub Pages: this site (index.html + assets/) reads ./data/shows.json
         +--> iPhone app downloads raw.githubusercontent.com/Ric0B/VERNI/main/data/shows.json

The site is static files. The browser fetches `data/shows.json` on every visit (`no-cache`), keeps the last good copy in localStorage, and renders everything client side. A refresh of the data therefore updates the site and the app with no deploy step.

## Data model (data/shows.json, schemaVersion 1)

- venue: id, name, type, city, address, website, lat, lon, geoApprox?, hours?, sourceURL?
- show: id, venue, artists[], title, start (null = unknown, treated as already open), end, url
- event: id, venue, show?, type (opening|finissage|talk|tour|performance), title, date, time, url

Hours are stored only when the venue's page states them. Unknown hours show as "See the venue's website", never as "closed".

## Decisions and trade-offs

| Decision | Why | Cost |
|---|---|---|
| Static site on GitHub Pages | Free, no operations, deploys on push | No server-side search, no accounts, no push notifications |
| Vanilla JS modules, no framework or build | Nothing to install or break; easy for an agent to edit | Hand-written rendering; fine at this size |
| One JSON file as the database | Simple, diffable, versioned in git, shared by site and app | Whole file (about 50 KB) is downloaded each visit; revisit above roughly 1,000 shows |
| Hash routing (`#basel.show.id`) | Works on static hosting with no rewrite rules | URLs are not indexed as separate pages |
| Leaflet + OpenStreetMap tiles | Real map, no API key | OSM tiles are for light use. Move to a paid tile provider if traffic grows |
| Gathering by an LLM agent reading pages | Handles 50+ different site layouts | Can misread a page; mitigated by the validator, source links, and never deleting a venue's records after a failed read |

## What to revisit as it grows

- More than about 1,000 shows or heavy traffic: split the data by region, add a CDN-friendly index, change map tiles.
- Wrong or stale data: show per-record "last confirmed" dates and add a way for venues to correct their own listing.
- Discoverability: pre-render one static page per show and venue so search engines can index them.
- Languages: German, French and Italian.
- Offline and install: add a service worker so the site opens with no connection.
