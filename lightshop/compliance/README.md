# Compliance kit: what to fill in before the first sale

> These are templates written to match the Swiss low-voltage product ordinance (NEV) and the EU rules it mirrors. They are not legal advice. Before selling, have one lamp's file checked once, for example by the ESTI (Swiss electrical inspectorate), an electrical engineer, or a testing lab such as Electrosuisse. That one review covers the whole family if you keep the construction the same.

| File | What it is | When |
|---|---|---|
| `declaration-of-conformity.md` | Declaration of conformity, one per lamp model (DE/EN) | Before the first sale, keep 10 years |
| `technical-file.md` | What goes in each model's folder | Build it while prototyping |
| `temperature-test.csv` | Log for the 4-hour heat test | Every new design, every material change |
| `risk-assessment.md` | Hazards and how the design deals with them | Once per model family |
| `label.svg` | Rating label for the underside of the base, 50 × 30 mm | Print on polyester label stock |
| `safety-sheet.md` | Short safety and use instructions for the box (DE/EN/FR/IT) | Every box |

## The approach that keeps this small

1. **Buy only certified electrical parts.** Socket, cord set with plug and switch, dimmer and USB-C kits must carry CE (plus ENEC or VDE where available). Ask every supplier for their declaration of conformity and keep it in the file.
2. **Your own contribution is mechanical:** the housing, the strain relief, the heat behaviour. So your tests are a strain-relief pull test, a temperature test and a stability (tip-over) test. You never open or change the bought electrical parts.
3. **Class II (double insulated), Europlug, LED only, max. 7 W.** No metal parts that could become live. That avoids earthing completely.
4. **Same construction across the collection.** Every table lamp uses the same socket, tube, nut and cord, so one technical file covers the platform and each model adds only its own temperature log.

## Standards to name in the declaration

| Standard | Topic | Applies to |
|---|---|---|
| EN 60598-1 | Luminaires, general requirements and tests | all |
| EN 60598-2-1 | Fixed general-purpose luminaires | Firn (pendant) |
| EN 60598-2-4 | Portable general-purpose luminaires | table lamps, floor lamp |
| EN IEC 55015 | Radio disturbance (EMC) | covered by the bought LED and dimmer; name it for the product |
| EN 61547 | EMC immunity for lighting | as above |
| EN 62493 | Electromagnetic fields from lighting | as above |
| EN 62471 | Photobiological safety | covered by the bought LED |
| EN 62133-2 / UN 38.3 | Lithium cells (Föhn, Glut) | only through the battery kit supplier's documents |

## Registrations (Switzerland)

- [ ] SENS / Stiftung Licht Recycling Schweiz (SLRS): register as a producer of luminaires and pay the advance recycling fee (vRG) per lamp.
- [ ] Business liability insurance with product liability, CHF 3–5 million cover.
- [ ] The maker's name and address on the product (the label does this).
