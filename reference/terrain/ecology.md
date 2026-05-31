# Ecology & Planting

What grows where is a design decision, not an afterthought sprinkle. `terrain-ecology` owns it: given
a finished heightfield and its biome assignment, it chooses plant communities, species mixes,
densities, and ecotone transitions, and emits the scatter recipe. Driven by `tools/terrain/scatter.py`
and `tools/terrain/climate.py` (`BIOME_CONTENT`).

## Principles

1. **Communities, not single species.** A stand is a weighted mix (canopy + understory + ground),
   never one tree id repeated. `scatter.assign_species` picks from the biome's feature list per point.
2. **Blue-noise spacing.** Use `scatter.poisson` (variable-density Bridson) — plants compete for
   space, so they spread out, never clump or grid. Density varies with the mask.
3. **Mask-gated placement.** `scatter.density_map` zeroes density on steep faces (no trees on cliffs)
   and below water, and boosts it near water for riparian species. Forest edges thin naturally because
   density falls off with slope and the biome mask.
4. **Grow, never place.** Emit `level_place_feature` ids (e.g. `minecraft:fancy_oak`,
   `minecraft:spruce`, `minecraft:mega_jungle_tree`) so each tree is grown by vanilla with natural
   shape variation — or batch them via `level_place_features_batch` for throughput.
5. **Match the biome.** Species come from `BIOME_CONTENT[biome]["features"]`; density from
   `["density"]`. Co-planned with the surface palette so plant, tint, and ground agree.

## The pass

```python
from terrain import BiomeField, scatter
bf = BiomeField(hf, seed=S)
placements = scatter.scatter_for_biomes(hf, bf, origin=(ox, oz), seed=S)
# placements: [(x, y, z, "feature", feature_id), ...]  -> level_place_features_batch
```

For layered realism, run canopy first (large `r_min`), then a second understory pass at smaller
spacing over the gaps, then ground cover (`moss_patch`, flower/grass features) densely.

## Throughput

Per-feature `level_place_feature` is one call each (~60/min) — a dense forest is hours. The mod's
`level_place_features_batch` (>= 0.4.0) places up to 4096 per call. Prefer it; fall back to per-feature
with a budget (canopy first, inspect, then decide on understory) on mod 0.3.0.

## Rocks, deadfall, detail

Boulders and log clusters that vanilla features can't express are stamped via
`structure_load_to_world` with `integrity` 0.8-0.95 (random decay -> unique each time), placed by a
Poisson pass keyed to steep+concave (scree) masks.
