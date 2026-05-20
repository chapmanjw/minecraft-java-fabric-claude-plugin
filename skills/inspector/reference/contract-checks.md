# Contract checks — sampling algorithms

The `quality_contract` block in `plan.toon` declares the properties a build
must satisfy. This file is the precise, executable form of each row type —
the sampling algorithm, the threshold, and the action on failure.

A failing row is a real failure: emit it as a correction and route back to
the skill that owns the build (terraforming, player-house, etc.), not to the
worker as a paint-over.

## walkability[]{from,to,note}

Sample a straight-line ray from `from` to `to`, step 1 block at a time. At
each step, sample two cells with `mc_block_get`:

- **Floor cell** at `(x, y, z)` — must be a stand-on-able block (any solid;
  not air, water, lava, or fence-top).
- **Head cell** at `(x, y+1, z)` — must be air, a door, or a trapdoor in
  open state.

**Fail** if any step has no stand-on-able floor **or** the head cell is
blocked.

**Correction:** emit the failing coords; if there is no walkable route
between named rooms, route to the planner-class skill — the layout is wrong,
not the blocks.

## doors[]{at,facing,clearance_blocks}

For the door at `at` with `facing` (north / south / east / west) and a
clearance of `clearance_blocks` in front and behind:

- Compute the forward offset for `facing` (e.g. south = `(0, 0, +1)`).
- For each step `i` from 1 to `clearance_blocks` in front and behind:
  - **Floor** at `at + i*forward` (and `at + i*back`) must be stand-on-able.
  - **Head** at `at + i*forward + (0,1,0)` (and back) must be air.

**Fail** if either side is blocked — door faces a cliff, a wall, or has no
floor underneath. This is the Cape Aurelia "doors facing cliffs" failure.

**Correction:** the layout is wrong. Route to the planner-class skill;
re-orient the door or re-site the building.

## headroom[]{over_region_a,over_region_b,min_clear}

For every `(x, z)` column in the region between `over_region_a` and
`over_region_b`:

- Find the highest solid block in the column (call it `y_top`).
- Sample blocks at `y_top + 1` through `y_top + min_clear`.

**Fail** if any sampled block is not air — i.e. the headroom over the
floor/stair/corridor is less than `min_clear`.

**Correction:** raise the ceiling or re-pitch the stair. Route to the
planner-class skill if the failure is systemic; emit `fill ... air` steps
for the worker only if it is a one-off obstruction.

## block_mix_ratios[]{region_a,region_b,palette,max_single_ratio}

`palette` is a comma-separated list of expected block IDs. Sample every cell
in the region between `region_a` and `region_b` with `mc_block_get_volume`:

- Count the occurrences of each palette member.
- Compute the ratio for each: `count(block) / total_cells`.

**Fail** if any single block exceeds `max_single_ratio`, **or** if any
palette member is missing entirely. A 100%-white_concrete wall, or a wall
that's "60–80% white_concrete" but is actually 95%, fails here.

**Correction:** retune the palette weights in the source generator. For
small regions, emit `replace` steps that swap in the missing palette members
at the right ratio. Do not paint over with a single block.

## silhouette[]{region_a,region_b,sample_count,min_y_variance}

Sample `sample_count` random `(x, z)` points in the region's footprint,
spaced at least 5 blocks apart. For each, call `mc_block_get_top` to find
the surface Y.

**Fail** if `max(y) - min(y) < min_y_variance` — the silhouette is too flat
(a plateau, terrace, or ziggurat top).

**Correction:** the heightmap is too flat in this region. Route back to
terraforming to regenerate the noise with higher amplitude or an added
peak; re-place the affected tile.

## edge_irregularity[]{edge_name,from,to,max_collinear_run}

Walk the edge from `from` to `to` in 1-block steps, sampling the surface
block at each step. Track runs of consecutive blocks where X **or** Z stays
the same (i.e. a straight horizontal segment).

**Fail** if any run of identical X or identical Z exceeds
`max_collinear_run`. This is the 7-block rule in checkable form.

**Correction:** the edge was carved as a rectangle. Route back to
terraforming to add lateral jitter every 4–7 blocks, or widen the radial
falloff so the edge curves.

## foundation_naturalised[]{name,perimeter_a,perimeter_b,y_lo,y_hi,min_unique_blocks}

Walk the perimeter of the named foundation between `perimeter_a` and
`perimeter_b` at two depths (`y_lo` and `y_hi`), sampling every 4 blocks. For
each sample collect the block ID.

**Fail** if fewer than `min_unique_blocks` distinct IDs appear along the
sample at either depth — the underwater face is a sheer rectangle of one
block (the Cape Aurelia corestone failure).

**Correction:** apply the talus-skirt rescue from
`terraforming/reference/landforms.md`. Do not paint over with one block.

## water_continuity[]{coast_name,from,to,sample_count}

Sample `sample_count` random points along the coastline between `from` and
`to`, just outside the visible coast. For each, walk the column downward
from `y = sea_level` to the seabed.

**Fail** if any column has an air block above water — i.e. a dry void shelf
where water should be. This was the Cape Aurelia v1 waterline rock-shelf
failure.

**Correction:** extend the affected terrain tile downward to the seabed and
re-place. Do not patch with surface water sources; the column must be
continuous.

## connectivity[]{site_a,site_b,via}

Two named sites must be reachable along the named path. Apply the
`walkability` algorithm between the registered anchor of `site_a` and the
registered anchor of `site_b`, optionally following the path named in `via`
(rail, road, footbridge).

**Fail** if no walkable route connects them. This was the Cape Aurelia
"disconnected paths between districts" failure.

**Correction:** route back to the `transit-architect` skill to connect the
sites; do not insert ad-hoc fills.

## How to run the full contract

For each phase in the plan, the inspector reads the phase's slice of the
`quality_contract` (rows scoped to that phase's region) and runs the
sampling algorithms above. Aggregate the verdicts:

- All rows pass → **PASS**.
- One or more rows fail with a localised fix → **CORRECTIONS NEEDED** with
  the failing samples and the correction steps.
- One or more rows fail fundamentally (silhouette flat, foundation a
  rectangle, no route between sites) → **FAIL**, recommend re-planning the
  phase with the owning specialist.

Re-sample after corrections land. Always.
