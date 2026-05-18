# City catalog

How to recreate a real or fictional city. The catalog is **not** shipped
pre-baked — the `researcher` skill fetches verified data per city. This file
is the **method**, the **entry schema**, and worked examples across eras.

## The replica method

1. **Research first** for any real-world or named-fictional city — invoke
   `researcher`, cite reputable sources, and persist the dossier to the
   project folder (do not carry it in context across iterations).
2. **Fill the entry schema** (below).
3. **Pick a scale** (see the SKILL.md — district / whole-city / silhouette).
4. **Zone, then street, then fill** — see `zoning.md`, `streets.md`,
   `vernacular.md`.
5. **List the landmark handoffs** for `building-architect`.

## Entry schema

For every city, resolve:

- **Era & type** — drives zoning, street grid, palette, density.
- **Signature silhouette** — the 3–5 buildings that make the skyline read.
  Each becomes a `building-architect` handoff.
- **Urban pattern** — grid type, relationship to water, relationship to
  hills, walled or open.
- **Characteristic infrastructure** — the details without which it is
  generic (NYC: fire escapes, rooftop water tanks; Paris: Métro entrances,
  uniform cream façades; Venice: canals instead of streets).
- **Palette** — the dominant Minecraft blocks.
- **Scale notes** — what to keep or cut at 1:1 vs 1:10 vs 1:100.

## Worked examples

Representative entries — confirm specifics with `researcher`.

### Modern

- **New York (Manhattan)** — strict grid, avenues ~30 blocks wide, cross
  streets ~18, blocks ~61 N–S. Silhouette: Empire State, Chrysler, One WTC,
  Flatiron. Infrastructure: fire escapes, rooftop water tanks, yellow cabs,
  steam vents. Palette: smooth stone, sandstone, iron, glass. Supertalls
  exceed the Y range at 1:1 — use the silhouette scale or scale them down.
- **Paris** — Haussmann radial boulevards (~24–30 blocks) off star
  intersections, uniform 5–6 storey cream limestone with aligned cornices and
  45° mansard roofs. Silhouette: Eiffel Tower, Notre-Dame, Sacré-Cœur.
  Infrastructure: Art-Nouveau Métro entrances, planted medians, zinc roofs.
- **London** — organic medieval core overlaid with Georgian/Victorian
  terraces, the Thames through the middle. Silhouette: St Paul's, the Tower,
  the Palace of Westminster, the Shard. Infrastructure: red phone boxes,
  gas-lamp-style posts, brick terraces.
- **Tokyo** — dense, low-to-mid-rise fabric with a radial structure and a
  ring rail line, pockets of supertall. Infrastructure: elevated rail, neon
  signage, narrow side streets.
- **Venice** — canals *instead of* streets; buildings rise straight from the
  water. Grand Canal ~40 blocks wide; secondary canals 6–10. Silhouette: St
  Mark's Basilica and Campanile, the Doge's Palace, the Rialto Bridge.

### Historical

- **Pompeii (79 CE)** — a small walled Roman city; orthogonal `cardo` /
  `decumanus` grid, a forum quarter, insulae and domus, baths, an
  amphitheatre. Small enough to build at 1:1.
- **Constantinople (medieval)** — the great Theodosian land walls (a moat,
  outer and inner walls, towers), Hagia Sophia, the Hippodrome, dense quarters.
- **Edo / old Tokyo** — the castle at the centre, machiya row houses on deep
  narrow lots, a moat-and-canal network, wood-and-plaster palette.
- **A generic medieval European city** — a castle on the high point, a
  cathedral square, a market square, guild and merchant quarters, tanneries
  downstream, a curtain wall with gate towers, organic streets.

### Fictional

- **King's Landing** — a medieval city on three hills, seven gates, the Red
  Keep on the high hill (landmark handoff), the Great Sept, a dense poor
  "sprawl" outside the walls. A city-feel begins around the ~1,000-building
  mark for medieval density.
- **Minas Tirith** — a seven-tier walled city climbing a spur, each tier a
  ring of white buildings, the Citadel and White Tower on top (handoff).
  Tiered cities need explicit Y-budget reservation.
- **A cyberpunk metropolis** — stacked verticality, neon, megablocks,
  elevated transit, deep shadowed canyons between towers; districts by
  corporate/residential/slum.

The same schema applies to any city the user names — research it, fill the
schema, zone, street, fill, and hand off the landmarks.
