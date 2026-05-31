# The Terrain Method (recipe pipeline)

The single method all terrain-* skills follow. Terrain is authored as one **recipe** (a sampler
graph), verified offline, then emitted as executable phases — never hand-placed fills, never stacked
rectangles. This file is the canonical method; `toolkit-api.md` is the exact API.

## The pipeline

```
recipe (sampler graph, JSON)
  -> HeightField.from_graph        evaluate the graph into a heightfield
  -> shape ops                     erosion (thermal->hydraulic, pad_cells), fluvial rivers, terrace
  -> climate/biome                 BiomeField: assign vanilla biomes, blend per-biome heights
  -> seam blend                    one continuous field; belt or sparse_convolution_blend at borders
  -> masks                         slope / aspect / curvature / height / dist-to-water
  -> materialize                   MaterialSpec layer+slant stack -> block_fill_columns(+strata) plan
  -> scatter                       mask-weighted Poisson -> species mix -> feature placements
  -> verify (GATE A)               verify.py: HALT on ziggurat / flatness / monoculture / seam
  -> emit                          plan.toon terrain phases (columns / strata / fillbiome / scatter)
```

All of this runs in `${CLAUDE_PLUGIN_ROOT}/tools/terrain` (numpy + scipy + Pillow). The agent writes
a recipe, calls `emit.emit_world(recipe)`, render-verifies the PNGs, and hands the payloads to
`exec-worker` / MCP tools.

## Non-negotiables (enforced by `verify.py` and the harness lint)

1. **One continuous field — never butt independent regions.** Multi-region terrain is one recipe; at
   borders use the belt (`Centerline` + `belt_from_path`) or `blend.sparse_convolution_blend`. A
   seam is a *shape* problem; a colour pass cannot fix it.
2. **No ziggurats.** Author a heightfield and materialize via `block_fill_columns` — never stack
   Y-banded rectangular fills. The verify gate detects and rejects the terraced anti-pattern.
3. **Mask-driven surface.** Rock on steep faces (slant palette), snow above the snowline, beach near
   water, mix everywhere — declared as `MaterialSpec` layers, not hardcoded. No monoculture.
4. **Verify at eye-level, never top-down alone.** `render_views` emits hillshade, relief, profile,
   **slope**, and **eye-level** PNGs. Judge the slope + eye-level views — they expose the bare-wall
   failure that top-down hides.
5. **Erosion is the realism multiplier.** Run thermal then hydraulic (with `pad_cells` to kill edge
   seams) before materializing. Fluvial rivers for emergent drainage.
6. **Recipes are saved.** Persist `recipe.json` (Pillar 1). A re-sculpt edits one node and
   re-evaluates — it never discards accreted detail.

## Authoring loop

1. Write a recipe graph: a base (`FBM`/`Hybrid` through a `CubicSpline` to set the Y histogram) plus
   structure (`Max` with a `DomainWarp`-ed `Ridged` for mountains; `Cellular` for spires/basins).
2. `emit.emit_world(recipe)` -> runs erosion, biomes, masks, materialize, scatter, and the verify gate.
3. `render_views(field, "scratch/site")` -> Read the 5 PNGs. Fix the recipe, not the blocks.
4. Hand `columns` to `block_fill_columns`, `biomes` to `level_fill_biome`, `scatter` to
   `level_place_features_batch` (or per-feature `level_place_feature`).
5. After placement, `terrain-integrate` grounds the footprint; `exec-inspect` checks the seam.

## What each terrain-* skill owns

- **terrain-shape** — naturalistic terrain (mountains, valleys, rivers, coasts) as a recipe.
- **terrain-landmark** — recognizable wonders, composing 2-4 signature primitives (`${CLAUDE_PLUGIN_ROOT}/reference/terrain/primitives.md`).
- **terrain-ecology** — the planting/biome decision over a finished heightfield (`ecology.md`).
- **terrain-integrate** — grounding a build into the world (`integration.md`).
- **terrain-cave** — designed subterranean space (`caves.md`).
