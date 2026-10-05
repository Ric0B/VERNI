# Weekly VERNI (iPhone app)

SwiftUI app, iOS 17+, iPhone only. Real listings gathered from venue websites on 2026-10-05; refreshed weekly once the data URL is set.

## Run it

1. Open `WeeklyVerni.xcodeproj` in Xcode 16.
2. Xcode > Settings > Components: install an iOS simulator runtime (none is installed on this Mac yet).
3. Pick an iPhone simulator and press Run. For a real iPhone, choose your team under Signing & Capabilities.

## Layout

- `WeeklyVerni/Models.swift`: venues, shows, events, scopes, opening hours.
- `data/shows.json`: the listings (venues, shows, events), gathered from the venues' own websites. A copy is bundled in `WeeklyVerni/Resources/`.
- `data/REFRESH.md`: instructions for the weekly agent that updates that file. `tools/validate_data.py` must pass before anything is published.
- `WeeklyVerni/Sample.swift`: loads the listings (downloaded copy, else the bundled one) and downloads newer ones. `DataConfig.remoteURLString` points at the published file in github.com/Ric0B/VERNI.
- `WeeklyVerni/AppStore.swift`: state, filters, Tourplan, favourites (saved in UserDefaults).
- Screens: `ShowsScreen`, `EventsScreen`, `MapScreen` (MapKit), `PlanScreen`, `ShowDetailView`, `BrowseScreens`, `Sheets`.
- `tools/make_project.py` regenerates the Xcode project, accent colour and app icon.

New `.swift` files dropped into `WeeklyVerni/` are picked up automatically.
