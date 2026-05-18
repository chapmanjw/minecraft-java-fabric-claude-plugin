# Real-world replicas

How to recreate a real building faithfully. The catalog is **not** shipped
pre-baked — the `researcher` skill fetches verified data per build. This file
is the **method**, the **entry schema**, and a set of worked examples that show
the schema in use.

## The replica method

1. **Research first.** Invoke `researcher`. Get verified figures and cite at
   least two reputable sources — official building authority or UNESCO first,
   then encyclopedias, then reputable references. Sources disagree (Notre-Dame
   is quoted at 128–130 m long depending on the source) — record the figure
   *and* its source.
2. **Fill the entry schema** (below) from the research.
3. **Pick the scale** — see "Scale and the Y range".
4. **Decompose into modules** (`modules.md`) — repeating bays, tiers, towers.
5. **Honour the signatures** — the 3–5 features without which the building is
   not recognizable.

## Entry schema

For every real-world target, resolve:

- **Era & style** — drives technique and palette (see `styles.md`).
- **Dimensions** — footprint (W×L), height to roof, height to spire/tip,
  storey count — each with its source.
- **Signature features** — the 3–5 defining elements (twin towers, a specific
  dome, a setback profile, a colonnade).
- **Material → block** — translate the real material to a Minecraft palette
  with rough ratios (e.g. limestone → 60% smooth stone / 25% calcite / …).
- **Symmetry rule** — required (Taj Mahal), forbidden, or mixed.
- **Minimum-recognition scale** — the smallest size that still reads as the
  building.

## Scale and the Y range

The world spans Y -64 to 320 — about 384 blocks. Many real buildings do not
fit at 1:1:

- **Fits at 1:1** — most cathedrals, palaces, and low-rise landmarks.
- **Strains or exceeds** — skyscrapers. The Empire State (~443 m to tip) and
  Burj Khalifa (~828 m) exceed the range. Recommend a reduced ratio (e.g.
  ~1:2 for the Empire State, ~1:3.3 for the Burj Khalifa) and tell the user.

Whatever the scale, keep the building's **proportions** true — a too-short
tower or too-wide nave reads wrong even when every block is correct.

## Worked examples

Representative entries — confirm dimensions with `researcher` before building.

- **Notre-Dame de Paris** — 12–14C Gothic. ~130 m long, ~35 m to the roof,
  ~68 m towers, a central spire. Signatures: asymmetric twin west towers,
  three rose windows, ~36 flying buttresses, the Latin-cross plan. Palette:
  ~60% smooth stone / polished diorite, 25% calcite, 10% deepslate-tile
  accents, 5% stained glass. Fits at 1:1.
- **Colosseum** — Roman, 1C. An ellipse ~188×156 m, ~48 m tall, three arched
  tiers plus an attic. Signatures: the elliptical arcade, ~80 arches per tier,
  the tiered profile. Palette: smooth stone, sandstone, cracked/mossy stone
  brick. Build the arch bay as one module, stamp the ellipse.
- **Pantheon, Rome** — 2C. A coffered concrete dome ~43 m across with a 9 m
  oculus, a Corinthian portico. Signatures: the dome, the oculus, the portico.
- **Taj Mahal** — Mughal, 17C. A ~73 m mausoleum, central onion dome, four
  minarets, on a raised plinth. **Symmetry required.** Palette: calcite +
  smooth quartz, red-sandstone gateway, gold trim.
- **Forbidden City** — a vast walled complex (~960×750 m). A *complex*, not
  one building — decompose into the wall, gates, and the major halls; reuse
  hall modules. Palette: spruce, red terracotta, yellow-glazed roofs.
- **Empire State Building** — Art Deco, 1931. ~381 m to the 102nd floor, a
  setback profile, a crown and mast. Signatures: the setbacks, the Deco crown.
  Build at ~1:2 — 1:1 exceeds the Y range. Palette: smooth sandstone, smooth
  stone mullions, iron accents.
- **Eiffel Tower** — wrought-iron lattice, ~330 m, a 125 m square base, three
  platforms. Fits at 1:1 with headroom. Palette: iron bars / iron trapdoors /
  iron-block lattice — the lattice *is* the building.
- **Sydney Opera House** — 20C. Sail-shell roofs, each a section of a sphere.
  **Not symmetric** — the shell groups face different ways. Palette: white
  concrete / smooth quartz / calcite shells on a deepslate podium.

These span eras and types deliberately — apply the same schema to any target
the user names.
