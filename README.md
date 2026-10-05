# Weekly VERNI

Exhibitions, openings and events in contemporary art across Switzerland. Listings are gathered from the venues' own websites.

- `index.html`, `assets/`: the website (static, no build step). It reads `data/shows.json`.
- `data/shows.json`: the listings. Updated twice a week.
- `data/REFRESH.md`: instructions for the agent that updates the listings.
- `tools/validate_data.py`: must pass before a refresh is published.
- `docs/DESIGN.md`: how it fits together.

Run locally: `python3 -m http.server 8000`, then open http://localhost:8000.

Publish: in the repository settings, Pages > Build and deployment > Source "Deploy from a branch", branch `main`, folder `/ (root)`.
