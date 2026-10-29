# Design system: parametric lamps

Every Schichtlicht lamp is a formula, not a drawing. A shade is a radial field `r(θ, z)`: a smooth profile plus a pattern. Each shape is therefore one closed surface that prints in **spiral vase mode**: a single unbroken line from bottom to top, with no seam and no supports. This is how studios using Grasshopper/Rhino work, here written in Python so it runs anywhere.

| File | What it does |
|---|---|
| `lampgen.py` | 10 shade definitions, STL export, printability check (wall angle) |
| `parts.py` | Bases, mounts and couplers in PETG, sized from each shade's collar (needs `pip install manifold3d`) |
| `edition.py` | One-offs (Gletscher) and the numbered edition (Moräne): code → geometry, a registry so no code is ever reused, a certificate PDF |
| `formlabor.html` | The same definitions in the browser: sliders, live 3D (day and night), printability, filament and time estimates. Published as a private page: https://claude.ai/artifact/9G4yVFCJJCnMvVcZBLtnwQ |
| `../samples/certificate-example.pdf` | What a one-off customer receives |

```bash
cd lightshop/design
pip install numpy manifold3d pillow          # once
python3 lampgen.py all --res fine           # every shade as STL in out/
python3 parts.py                            # every base and mount
python3 edition.py gletscher --code 14062019 --name "Anna & Luca" --pdf
python3 edition.py moraene --number 1 --pdf
```

The Formlabor and the Python code use the same maths and the same seeded random generator (checked bit for bit). A shape you find in the browser exports identically from the command line, and its **Export** box shows the exact command.

## The collection

| Lamp | Series | Idea | Key parameters | Shade H × Ø | Filament | Print |
|---|---|---|---|---|---|---|
| **Aare** | Collection | Ribs twisting ⅛ turn, swelling with the belly | ribs 48, twist 0.12, rib_depth 4.5 | 320 × 216 | ≈ 375 g | ≈ 9 h |
| **Föhn** | Collection, cordless | Mushroom: fluted stem + gilled cap | gills 120, cap Ø 276 | stem 150 + cap 112 | ≈ 140 g | ≈ 4 h |
| **Firn** | Collection, pendant | Bell; 96 pleats open towards the rim | pleats 96, pleat_growth 1.4 | 200 × 346 | ≈ 215 g | ≈ 5 h |
| **Grat** | Collection | 14-sided polygon whose rotation zigzags 3× | sides 14, folds 3, fold_angle 0.38 | 300 × 212 | ≈ 230 g | ≈ 6 h |
| **Nebel** | Collection, floor | Two counter-rotating waves → moiré diamonds, 4 segments | n1 = n2 = 18, t1 = t2 = 1 | 4 × 300 × 206 | ≈ 920 g | ≈ 21 h |
| **Glut** | Collection, cordless | Closing egg with a quilted surface | cells 16, rows 5 | 140 × 122 | ≈ 55 g | ≈ 1.5 h |
| **Bise** | Atelier | Two helices multiplied → a knitted lattice | n 20, turns 2 | 320 × 210 | ≈ 285 g | ≈ 7 h |
| **Moräne** | Atelier, edition of 50 | Ribs deflected by 4 attractor points (the classic Grasshopper move) | attractors 4, reach 85, warp 4 | 330 × 236 | ≈ 400 g | ≈ 9 h |
| **Gletscher** | Atelier, one-off | Voronoi crevasses from 70 seeded points | cells 70, groove 4.6 / 2.6 | 300 × 214 | ≈ 235 g | ≈ 6 h |

Times assume a single 1.0 mm wall, 0.24 mm layers and 40 mm/s. Weigh your first print and update the shop.

Every design passes the printability rule: **99% of the wall is within 50° of vertical**. Gletscher was tested across 40 codes (worst 48°) and Moräne across editions 1–10 (worst 32°). `edition.py` warns if a code ever exceeds the limit.

## Bambu Studio settings (H2S / H2D)

| Setting | Shades (vase mode) | Parts (bases, mounts) |
|---|---|---|
| Nozzle | **0.6 mm** (stronger, less transparent) or 0.4 mm | 0.4 mm |
| Mode | *Others → Spiral vase* **on** | off |
| Layer height | 0.24 mm | 0.2 mm |
| Line width | 1.0 mm (0.6 nozzle) / 0.8 mm (0.4 nozzle) | default |
| Bottom shell layers | **0**: the shade becomes an open tube. **Exception, Föhn cap: 3** (closes the top) | default |
| Material | PLA (translucent or matte), dried 55 °C / 6 h | **PETG** (heat near the bulb), 4 walls, 30% infill |
| Speed | outer wall 40–60 mm/s, cooling 100% | default |
| Plate | textured PEI, glue stick for translucent PLA | textured PEI |
| On the H2D | Print shades on one nozzle | Print PETG parts on their own plate, never next to a vase-mode shade |

**Tips**
- Print the pendant **Firn** and the **Föhn cap** narrow end down; they sit upside down in use.
- Colour: one spool per shade. A mid-print colour change (Bambu "Add pause / change filament" at a layer) works in vase mode and gives two-tone versions of Grat without a seam.
- First article of each design: weigh it, measure diameter at the collar (fit in the base groove: 1.4 mm gap) and run the 4-hour temperature test (see compliance).

## Parts list per lamp (bought parts)

| Lamp | Electrics | Mechanical |
|---|---|---|
| Aare, Grat, Bise, Moräne, Gletscher | E27 thermoplastic socket with M10×1 thread + strain relief, M10×1 threaded tube 30 mm, M10 nut, 2 m cord set with switch or dimmer and Europlug (certified), 4.9 W 2700 K LED | printed base (`base-<name>`), steel washer about 400 g as ballast, 4 felt pads. **Atelier: oak base** turned to the same drawing (outer Ø = base Ø, groove and holes identical) |
| Firn | E27 socket with outer thread + shade ring, ceiling canopy kit with 1.5 m textile cable (certified), 6 W LED | `mount-firn` |
| Föhn | 5 V USB-C rechargeable kit with E27 socket and 5 V bulb (Creative Cables), 18650 cell from the kit vendor | `foot-foehn`, `neck-foehn` |
| Nebel | 2 × E27 sockets on M10 tube, cord set with foot switch, 2 × LED | 12 mm aluminium tube 1250 mm, `foot-nebel`, 3 × `coupler-nebel`, `cap-nebel`, steel disc 150 × 10 mm |
| Glut | 5 V USB-C kit, small LED board (2200 K) | `base-glut` |

The constants at the top of `parts.py` (hole sizes, groove width, USB-C opening) are the bought parts' measured dimensions. **Measure your real parts once and adjust** before printing batches.

## Atelier finish

- Oak bases: commission a Swiss turner or a CNC shop (search "Drechslerei" in your canton). Give them `base-<name>.stl` as the drawing. Expect about CHF 25–45 each in batches of 10.
- Number editions on the underside of the base (laser or brass plate).
- Dimmer: inline rotary dimmer for LED (certified, e.g. Relco/Kopp).
- Packaging: a box with honeycomb insert, the certificate in an envelope, the layer-count card.

## Ideas for the next definitions

- **Schrattenkalk**: limestone karst, eroded grooves from a flow field (curl noise).
- **Bergwald**: tree-ring Voronoi, cells growing in size towards the top.
- **Raureif**: hoarfrost, fine reaction-diffusion pattern from a seed.
- **Personal skyline**: the profile of a mountain panorama chosen by the customer (from a Swisstopo elevation line) wrapped around the lamp. A strong one-off product.

## Woven nets (direct G-code, no slicer)

`weave.py` writes G-code directly: a continuous spiral where each lap waves up and down (non-planar) in anti-phase to the lap below. Laps fuse only at the wave tips and bridge open cells in between, giving a real see-through net that no slicer can produce. Solid bands at foot and rim hold it together and fit the base groove.

```bash
python3 weave.py                                   # 100 mm test, ~40 min, ~7 g
python3 weave.py --name gewebe-lampe --height 220 --radius 70 --belly 18 --waves 46.5 --band 8 --rim 6
```

Key knobs: `--amp` (cell height = 2 × amp), `--waves` (must end in .5), `--flat` (longer fused contacts), `--strand-h`, `--speed` (keep 12–18 mm/s in the net), `--radial` (adds an in/out wave for texture). Ready files and previews are in `../samples/weave/`.

### KORB: woven rattan-style pendant

`korb.py` writes a woven ceiling pendant (onion bulb, Ø280 × 230 mm) as direct G-code: each lap zig-zags at about 60° in anti-phase to the lap below, so the strands cross like a rattan lattice, with solid hoops at the foot, two belly rings and a top collar. Radii follow each point's own height, so crossings meet even where the shape leans. `python3 korb.py --mount` also writes the PETG hanging disc (`mount-korb.stl`) for an E27 socket with shade ring.

```bash
python3 korb.py --scale 0.5 --name korb-test   # half size test, Ø140 × 115 mm, under 1 h
python3 korb.py --mount                        # full pendant + hanging disc
python3 korb.py --cell 7                       # denser lattice
```

Ready files and a render: `../samples/korb/`.

### Into Bambu Studio and onto the printer

`make_3mf.py` packs a toolpath into what Bambu Studio and the printer expect. A raw woven file crashes Studio's preview: without layer tags it starts a new layer at every Z change (about 30,000 for the test KORB). The script adds the tags (one layer per 0.25 mm of height), a Bambu header and config block, progress (M73), and the `.gcode.3mf` structure. The moves are unchanged (checked line by line).

```bash
python3 make_3mf.py out/korb/korb-test.gcode --render ../samples/korb/korb-render.jpg
# -> korb-test.bambu.gcode  (preview in Studio)   korb-test.gcode.3mf  (print)
```

Print: copy the `.gcode.3mf` to a USB stick, plug it into the H2S, pick it on the touchscreen, PLA in slot 1, textured PEI plate. Or open the `.gcode.3mf` in Bambu Studio and click *Print plate*.
