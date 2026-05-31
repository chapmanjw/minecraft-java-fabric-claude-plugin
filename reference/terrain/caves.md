# Designed Subterranean Space (caves, caverns, ravines)

Designed underground space — show caves, cavern halls, ravines, lava tubes, and the surroundings of a
cave base — as opposed to the random vanilla caves the world already has. Owned by `terrain-cave`.
The toolkit can carve; this is how to carve *deliberately*.

## What "designed" means here

Vanilla caves are noise the player stumbles into. A designed cave system has **intent**: a known
entrance, a route, chambers sized for a purpose (a base, a passage, a dramatic reveal), and a
material story (stone type, ores, dripstone, water features). You author the void, then dress it.

## Carving method (anisotropic 3D noise threshold)

Caves are a 3D void carved out of solid stone, the underground analogue of the surface heightfield.
The portable technique (from TerraformGenerator's cheese/ravine carve):

- **Cheese caverns (wide, rounded):** sample a 3D noise at `(x*0.5, y, z*0.5)` — scaling x,z down
  stretches the blobs horizontally into cavern shapes; carve `air` where `noise < threshold`
  (~ -0.3), damped near the surface so caves don't breach it.
- **Ravines (tall, thin):** sample at `(3x, 0.4y, 3z)` — the opposite anisotropy makes knife-thin
  vertical slots; carve where `noise < ~ -1.3`, with a log depth filter so they fade toward the
  surface.
- **Tubes/passages:** carve a swept circular cross-section along a `Centerline` path (reuse the belt
  machinery for the route), radius varying along arc-length.

Implement the carve offline as a 3D boolean mask over the column stack, then emit `air` fills via
`block_fill_region` (hollow) / `block_fill_batch` (mind the 32,768 cap — tile manually;
`block_replace_in_region` does NOT auto-tile).

## Structural safety & support

- Leave pillars / thick ceilings over wide spans — a 30-block-wide flat ceiling reads wrong and (for
  a base) feels unsafe. Vary ceiling height; add stalactite columns as visual supports.
- Never carve into a fluid body without a plan — check the survey for water/lava above the carve.
- Light the void deliberately (the build will be dark); place light sources as part of the plan, not
  after.

## Dressing the void (the detail pass)

- **Strata on the walls:** band the exposed rock by depth (deepslate below y0, tuff/stone above) —
  the same strata idea as canyons, applied to cave walls.
- **Features:** `level_place_feature` for `dripstone_cluster`, `pointed_dripstone`, `glow_lichen`,
  `cave_vine`, `moss_patch`, `amethyst_geode` — gated by masks (lichen on walls, dripstone on ceiling
  via a downward scan, moss in damp/low areas).
- **Water/lava features:** still pools, drip features, a subterranean river along the route.
- **Cave base surroundings:** if the cave hosts a build, hand the chamber floor + walls as the
  build's site to `build-structure`, and ground the structure with `terrain-integrate` so it sits in
  the cave, not in a box carved out of it.

## Pipeline placement

`terrain-cave` is a Tier-3 leaf invoked by `build-natural-world` (for cave/cavern requests) or by
`build-structure`/`build-settlement` when a build needs designed underground space (a mine, a vault,
an underground hall). It writes its carve + dress phases into `plan.toon` with the standard
`quality_contract` rows (no flat ceilings, support present, lit, no unintended fluid breach), and runs
through GATE A (verify) and `exec-inspect` like any terrain.
