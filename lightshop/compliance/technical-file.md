# Technical file: one folder per model

Keep it as a folder (cloud or printed binder). The ESTI can ask for it at any time for 10 years.

```
technical-file/
  00-platform/                     shared by all table lamps
    parts-list.xlsx                part, supplier, type, certificate number
    supplier-declarations/         PDF declarations of conformity from each supplier
    wiring-diagram.pdf             socket → cord → switch → plug (class II, no earth)
    strain-relief-test.md          pull test result
    stability-test.md              tip-over test result
  aare/
    declaration-of-conformity.pdf  signed
    drawings/                      lampgen parameters + base STL version (git commit hash)
    photos/                        outside, inside, label, packaging
    temperature-test.csv           4-hour test
    label.svg                      final label
    instructions.pdf               the box insert
    changes.md                     every change after release, with date and reason
```

## Tests you run yourself (no lab needed)

| Test | How | Pass |
|---|---|---|
| **Temperature** | Ambient about 25 °C, lamp assembled, strongest allowed LED, 4 h on. Measure the shade wall (hottest point, usually just above the bulb), the socket mount and the base top every 30 min with an IR thermometer or a K-type probe | Shade below **45 °C** for PLA (softens from 55 °C), PETG mount below **60 °C**. Log with `temperature-test.csv` |
| **Strain relief** | Pull the cord 25 times with 60 N (about 6 kg on a luggage scale) for 1 s each, in the least favourable direction | Cord moves less than 2 mm and the socket terminals carry no strain |
| **Stability** | Tilt the lamp 6° on a slope (table lamps) and 10° (floor lamp) in the least stable direction | It does not tip over |
| **Drop** | Packaged lamp dropped from 80 cm onto each face | No damage to shade or electrics |
| **Bulb clearance** | Measure distance bulb to shade wall | At least 30 mm (table) and 40 mm (pendant) |
| **Visual** | No sharp edges, no access to live parts with the test finger (a pencil is a good proxy) | Pass |

## When something changes

A new material, a new bought part, a smaller shade or a stronger bulb means: repeat the temperature test, update the parts list, and issue a new revision of the declaration.
