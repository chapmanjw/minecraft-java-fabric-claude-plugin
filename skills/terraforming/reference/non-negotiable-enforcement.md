# Non-negotiable enforcement — the machine-checkable form

The `SKILL.md` non-negotiables (7-block rule, asymmetry, no 45°, no
monoculture, double-layer, exaggerated scale, grown trees) were treated as
human guidance until the Cape Aurelia ziggurat. The fix is to express them as
**machine-checkable contract rows** that go into the plan's `quality_contract`
block and are sampled by the `inspector` automatically.

A violation that survives this gate is a build failure, not a stylistic note —
the build does not advance to the next phase until it passes.

## Required `quality_contract` rows for any terrain phase

Emit these as part of `plan.toon`'s `quality_contract` block (see the
`planner` skill for the full schema). For every terrain phase of every build:

### 1. Silhouette variance — no flat plateaus

For any landform with horizontal extent ≥ 20 blocks, sample 8 surface
points spaced ≥ 5 blocks apart and require Y values to vary by **≥ 3 blocks**
across the sample set. A landform that comes back with all 8 points at the
same Y is a flat plateau or terrace — refuse.

```toon
silhouette[1]{region_a,region_b,sample_count,min_y_variance}:
  -55 105 -47,55 130 63,8,3
```

### 2. Edge irregularity — the 7-block rule

For every named coastline, ridgeline, or terrain edge, sample 20 consecutive
surface points along the edge and require **no run of more than 7 collinear
blocks** (same X or same Z). This is the 7-block rule in checkable form.

```toon
edge_irregularity[1]{edge_name,from,to,max_collinear_run}:
  headland-west-coast,-55 105 -47,-55 105 63,7
```

### 3. Block-mix ratio — no monoculture

For every "natural" surface fill, count blocks in a representative 10×10×1
area and require **no single block to exceed 70%** of the cells (or the
ratio band the palette specifies — `palettes.md` § biome).

```toon
block_mix_ratios[1]{surface_name,region_a,region_b,palette,max_single_ratio}:
  headland-grass-cap,-30 128 -20,-10 128 0,"grass_block,coarse_dirt,podzol",0.7
```

### 4. Symmetry test — no mirrored mountains

For any "natural" landform, the bounding-box flipped left-right (or top-down
for footprints) must **not** be a pixel-perfect match. Sample 20 random
`(x, z)` points; flip them about the landform's centre line; require Y
values to differ at ≥ 30% of the points.

```toon
asymmetry[1]{landform_name,center_x,center_z,sample_count,min_differ_ratio}:
  headland,0,8,20,0.3
```

### 5. Foundation visibility — naturalised below-water faces

If the build includes a foundation/core mass with **any** vertical face
between Y_seabed and Y_seabed + 20, sample the perimeter every 4 blocks at
two depths (seabed + 5, seabed + 15) and require the face to have **at least
3 unique block IDs** along the sample (i.e. it's not a sheer rectangular
wall of one stone block).

```toon
foundation_naturalised[1]{name,perimeter_a,perimeter_b,y_lo,y_hi,min_unique_blocks}:
  headland-core,-55 -49,55 62,20,40,3
```

### 6. Water column continuity — no dry shelves

Along any coastline of a built landform, sample 12 surface points just
outside the visible coast and require **water all the way down to the
seabed** — no air or void column above water level.

```toon
water_continuity[1]{coast_name,from,to,sample_count}:
  headland-perimeter,-55 105 -47,55 105 63,12
```

## How the inspector uses these

The `inspector` reads the phase's `quality_contract` block from `plan.toon`,
runs every row's sampling algorithm against the world with `mc_block_get` /
`mc_block_get_top`, and produces:

- **PASS** — every row passes its threshold.
- **CORRECTIONS NEEDED** — one or more rows fail; the inspector emits the
  failing samples and routes back to this skill for live correction.
- **FAIL** — the violation is fundamental (e.g. the silhouette is a
  perfectly flat plateau); recommend regenerating the heightmap from scratch.

See `inspector/reference/contract-checks.md` for the precise sampling
algorithms and tolerances.

## What to do when a contract row fails

The Cape Aurelia retrospective: half-measures cost more iterations than they
save. On `CORRECTIONS NEEDED`, **fix the root cause**, not the symptom:

- Silhouette variance fails → the heightmap is too flat in that region; raise
  noise amplitude or add a peak, regenerate the tile, re-place.
- Edge irregularity fails → the coastline was carved as a rectangle; widen
  the radial falloff or add an organic-blob inlet, regenerate, re-place.
- Block-mix ratio fails → the palette generator is picking one block too
  often; retune the weights and re-place.
- Foundation visibility fails → apply the talus-skirt rescue from
  `landforms.md`; do not paint over with a single block type.

Then **re-sample after acting** to confirm the fix landed and did not break
a neighbouring contract row. Verify is not optional.
