# Concepts: 43 designs to choose from

Catalogue (private page, filter by line, lights on/off): **https://claude.ai/artifact/M2QpZT4NgEakgd8wVrW1G2**. Locally: open `catalog.html` in a browser. Rebuild it with `python3 ../design/concepts.py --stats > stats.json && python3 make_catalog.py stats.json`.

Source: `../design/concepts.py`. Every design is a formula with a printability check: 99% of the wall within 50° of vertical, and no two walls closer than 2 mm. **All 35 printable parts pass at print resolution.**

```bash
cd ../design
python3 concepts.py --list                 # everything, with one-line ideas
python3 concepts.py werk-profil --res fine # one STL into out/concepts/
python3 concepts.py all                    # all of them
```

## The lines

| Line | What | Who buys it | Price band | Count |
|---|---|---|---|---|
| **Kollektion** (existing) | Soft, organic, Swiss landscape names | Homes, gifts | CHF 69–349 | 6 |
| **Atelier** (existing) | Parametric, editions and one-offs | Design collectors | CHF 390–690 | 3 |
| **WERK** | Industrial: heat sink, turbine, corrugated sheet, cooling tower, bellows, flange, thread, gear, perforated sheet, rope, T-slot profile, I-beam | Lofts, studios, offices, co-working, bars, men's gifts | CHF 229–319 | 13 |
| **GRENZE** | Experiments: 42 mm deep star folds, square-to-triangle morph, trefoil knot, leaning axis, pine cone (170 bumps), fractal pleats, glitch, pagoda, terrain | Galleries, press, Instagram reach, limited drops | CHF 269–319 | 9 |
| **TOTEM** | 10 modules on one Ø140 plug, stacked into table and floor lamps | Customers who want to configure; B2B (custom heights and colours per venue) | CHF 39–79 per module, stacks CHF 319–469 | 10 modules, 6 stacks |
| **DUO** | Two nested shades: moiré when lit | Statement pieces | CHF 329–390 | 2 |

**Running several lines at once works** because they share everything behind the shade: the same bases, sockets, cords, LED, packaging, label, technical file and shop. A new line costs design time, not stock. In Shopify each line is a collection with its own look in the hero section. Keep **one brand** with line names (Schichtlicht WERK, Schichtlicht GRENZE). A second brand only makes sense if a line targets B2B buyers who would be put off by the home décor side.

## How stacking works (TOTEM)

- Every module starts with an 8 mm **collar** (radius 70.0 mm, wall centre) and ends with an 8 mm **spigot** (radius 68.6 mm). A spigot slides into the next collar with about 0.4 mm clearance per side: a snug push fit, no glue.
- The pattern ramps in over 22 mm above the collar and out over 22 mm below the spigot, so every pattern meets every other pattern cleanly.
- Print modules in different colours and mix them: night blue between frost, sand between frost (see "Kontrast", "Schichtwechsel").
- Stacks taller than about 40 cm need a 10–12 mm aluminium tube through the middle with an LED filament strip or two sockets. Use the Nebel floor-lamp hardware (`foot-nebel`, couplers) from `parts.py`.
- Sell modules singly (refills, new patterns every month) and as ready stacks. It is the cheapest way to have a large catalogue: one 1–4 h print per module.

## Limits these designs push (and what to watch on the first print)

| Design | Limit | First-print check |
|---|---|---|
| Kühlkörper, Stern, Fraktal | Very deep folds on a 1 mm wall | Fins can wobble at the top: print at 30 mm/s, maximum cooling |
| Balg, Gewinde, Kaskade, Flansch | Overhangs near 45° | Use a 0.6 mm nozzle; if edges curl, reduce layer height to 0.2 mm |
| Profil, Profil Twist, Träger | Outline folds back into itself (undercut slots) | Check the slicer preview: vase mode must keep the full outline |
| Schieflage | The whole lamp leans 35 mm | Brim on; the base needs 300 g ballast |
| Zapfen (phyllotaxis), Lochblech | Hundreds of small local overhangs | Fine at 0.2 mm layers; frost PLA hides the steps best |
| Duo | Two shades must fit inside each other | Print the inner one first and test the fit before the outer |
| Totem modules | Fit between collar and spigot | Print two modules first; tune `SPIGOT_R` in `concepts.py` by ±0.2 mm |

## Choosing what to make

1. Mark 10 favourites in the catalogue.
2. Instagram poll in Stories with renders, 2 at a time, over a week. The winners are your launch shapes for that line.
3. Print the top 6, photograph them lit and unlit, and run the 4-hour temperature test.
4. Launch one line at a time, a drop every 4–6 weeks (fits the social plan).

My picks to start: **WERK Profil** (nobody else has it, strong B2B appeal), **WERK Kühlkörper** and **Gewinde** (read instantly as industrial, easy to explain), **GRENZE Schieflage** (stops the scroll), **TOTEM Maschine** as the floor lamp, and **DUO Interferenz** for press.
