# Named-garden catalog

How to recreate a famous garden. The catalog is **not** shipped pre-baked —
the `researcher` skill fetches verified dimensions and reference imagery per
garden. This file is the **method**, the **entry schema**, and worked examples.

## The method

1. **Research first** for a named garden — invoke `researcher`, get cited
   dimensions and plans, persist them. Sources disagree (Ryōan-ji's dry
   garden is quoted at slightly different sizes) — record the figure and its
   source.
2. **Fill the entry schema** (below).
3. **Resolve scale** — a small zen garden builds at 1:1; a Versailles-class
   garden does not. Default Tier 2+ gardens to ~1:4, and surface the
   trade-off to the user.
4. **Compose, then lay elements** — `composition.md`, `elements.md`,
   `water.md`.

## Entry schema

For every garden, resolve:

- **Tradition & era** — drives the geometry and palette (`styles.md`).
- **Dimensions** — overall extent, the main axis length, key feature sizes —
  each with its source.
- **Organizing geometry** — the axis, the symmetry, the quadrant or terrace
  structure.
- **Signature features** — the few elements that make it recognizable.
- **Palette** — the Minecraft blocks.
- **Scale** — 1:1, 1:4, or 1:8, and the resulting block footprint.
- **Sibling handoffs** — roofed structures, statuary, terracing.

## Worked examples

Representative entries — confirm dimensions with `researcher`.

- **Versailles parterre** — French formal. A long central axis with
  symmetrical parterres de broderie near the palace, a parterre d'eau, a
  fountain basin, `tapis vert` (green carpet) allées, a grand canal. Build the
  axis at ~1:4. Handoffs: `monument-builder` for the fountain figures.
- **Ryōan-ji** — a zen dry garden, roughly 25–30 m × 10 m: a rectangle of
  raked gravel with 15 stones in five groups, a low wall on three sides.
  Small — build at 1:1 in one structure. Gravel = light-coloured blocks;
  stones = mossy stone groups.
- **Taj Mahal char bagh** — a ~300 × 300 m square quartered by two water
  channels crossing at a central raised platform, each quarter subdivided into
  flowerbeds, cypress allées along the channels. Strict fourfold symmetry.
- **Hampton Court maze** — a trapezoidal hedge maze, ~0.3 acre, hand-designed
  dead-end topology with a goal at the center. Hedge = persistent leaves on a
  log core. Build at 1:1.
- **An English landscape park** (a Stourhead-type circuit) — a
  designed-irregular lake with classical temples placed around a walking
  circuit, naturalistic tree clumps composed for the view. Needs
  `terraforming` for the lake basin and a belvedere hill; `building-architect`
  for the temples.
- **A civic plaza** (a Place-des-Vosges type) — a paved square framed by
  uniform façades, a central statue or fountain, formal rows of trees.

## Scale note

Real great gardens are vast — a 3 km axis cannot be built at 1:1. Run Tier 2+
gardens at 1:4 (or 1:8 for the very largest), keep the *proportions* exact,
and tell the user the ratio. A small zen or courtyard garden is the rare case
that fits 1:1.
