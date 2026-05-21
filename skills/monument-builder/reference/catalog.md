# Monument catalog

How to recreate a named monument or creature. The catalog is **not** shipped
pre-baked — the `researcher` skill fetches verified dimensions and reference
images per piece. This file is the **method**, the **entry schema**, and
worked examples across the categories.

## The method

1. **Research first** for any named monument or creature — invoke
   `researcher`, get cited dimensions and reference imagery, persist them to
   the project folder. Real-world figures vary by source (the Statue of
   Liberty is quoted at several "heights" depending on what is included) —
   record the figure *and* its source.
2. **Fill the entry schema** (below).
3. **Resolve scale** against the Java envelope (SKILL.md — Y -64 to 320).
4. **Pick the technique** — pixel-art, organic-curve, voxelization — and the
   palette.
5. **Name the sibling seams** — cliff, pedestal, plinth.

## Entry schema

For every piece, resolve:

- **Subject & category** — real-world monument, pop-culture creature, abstract
  / land art, or original.
- **Dimensions** — height, length, width / wingspan — each with its source.
- **Silhouette signatures** — the few features that make it recognizable (the
  crown and torch, the outstretched arms, the coiled body).
- **Palette** — the Minecraft blocks and any gradient (see `palettes.md`).
- **Pose / composition** — standing, seated, coiled, in motion.
- **Sibling seams** — what is a cliff, a pedestal, a plinth.
- **Tile plan** — the split into ≤64×384×64 structures along anatomy seams.

## Real-world monuments

Representative entries — confirm dimensions with `researcher`.

- **Statue of Liberty** — a ~46 m copper figure (≈49 blocks with the crown
  spikes) on a ~47 m pedestal. The **figure is yours**; the habitable pedestal
  is a `building-architect` handoff. Palette: a copper-oxidation gradient (see
  `palettes.md`) — the statue's real verdigris patina. Split at the waist.
- **Christ the Redeemer** — a ~30 m figure with a ~28 m arm-span on an ~8 m
  pedestal. The arms-outstretched anatomy is the signature. Palette: smooth
  quartz and calcite.
- **Great Sphinx** — ~73 m long × ~20 m high, a recumbent lion with a human
  head. Sandstone palette. The figure is yours; the plateau is `terraforming`.
- **Easter Island moai** — stylized stone heads/torsos, ~4–10 m. Smooth stone,
  andesite, polished diorite. Good for showing stone-tone gradients at small
  scale; build several, varied.
- **Mt. Rushmore** — four ~18 m faces. The **cliff is `natural-landmarks`**;
  the **faces are yours**, carved into it. Granite-blend palette.
- **Memorials** — the Vietnam Veterans Memorial wall (a low angled
  black-stone wall), the Berlin Holocaust Memorial (a field of stelae) — these
  are abstract/minimal; precision of geometry and repetition is the point.

## Pop-culture creatures

- **Dragons** (Smaug, Game-of-Thrones dragons) — large coiled or winged
  organic forms. Heavy organic-curve work: an S-curve spine, voxel-sphere
  muscle bulges, stair-stepped wing membranes. Tile across several structures.
  Several creatures have no canonical size — pick a scale and say so.
- **Giant monsters** (Godzilla, Kong, kaiju) — tall figures; 1:1 height often
  fits near the top of the Y range, the tail/length needs horizontal tiling.
- **Franchise creatures** (Pokémon, mythological beasts — hydra, phoenix,
  griffin) — use franchise-wiki references for proportion; flag where a
  "dimension" is fan-estimated rather than canonical.

## Abstract and land art

- **Cloud Gate ("the Bean")** — a smooth reflective ellipsoid (~10 × 20 × 13 m).
  Minecraft has no true mirror — substitute polished/metallic blocks and
  accept it as a stylization. Pure voxel-curve work.
- **Land art** (Spiral Jetty, Sun Tunnels, Lightning Field) — large, flat or
  low, geometric earthworks; mostly footprint, tiled heavily, simple palettes.
- **Logos and text** — block-lettered or pixel-mapped: see `pixel-art.md`. For
  crisp **3D floating text and logos** at any size, use a `text_display`
  display entity instead (`reference/display-entities.md`) — true smooth
  glyphs, color, and a backing panel, which block letters cannot match.

## Display-entity-suited builds (Java-exclusive)

These piece types are best served (or only possible) with display entities —
see `reference/display-entities.md`. They are a late decoration phase.

- **Giant 3D text and logos** — dedication plaques, monument titles, brand
  marks, crests. A `text_display` gives smooth scalable glyphs with color and a
  backing panel; a `block_display` logo lets you tilt/lay a mark on a wall at
  any angle. Far cleaner than block-lettered text.
- **Glowing sculpture accents** — energy lines, runes, neon-style edges, halos,
  glowing crystal facets: any display with `Glowing:1b` + `glow_color_override`
  for a tinted outline that reads at night and through fog.
- **Scaled-block detail and impossible angles** — sub-block detail (rivets,
  inlay, gem facets, fine facial features) via blocks scaled below `1f`, and
  diagonal banding or tilted facets via blocks rotated to angles no placed
  block can sit at. Use to finish a voxel sculpture past the grid resolution.
- **Giant single-block forms** — a monolith, a giant gem, a floating cube: one
  `block_display` scaled `[8f,8f,8f]` or larger reads as a seamless massive
  form, useful as the core of an abstract piece.
- **Museum / pedestal item displays** — a sword or crown floating over a
  pedestal, a case of artifacts, a scaled-up item as a sculpture, via
  `item_display`.

## Sourcing

Prefer official authorities (a national park service, a museum, a
manufacturer) and reputable references for real-world dimensions; use
franchise wikis for fictional creatures and mark the confidence. Community
builders are inspiration for *technique*, not authoritative for dimensions.
