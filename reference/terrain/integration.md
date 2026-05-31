# Grounding a Build into the World (integration / apron)

The reason a build reads as "dropped on" the world instead of "belonging to" it is a hard seam at its
footprint edge — a vertical wall where the build meets untouched terrain, a trench, or a clashing
palette. `terrain-integrate` removes that seam programmatically: it erodes an **apron** around the
build while **protecting the build itself**, then re-materializes the apron to match the surrounding
surveyed palette. This is the automatable form of the manual talus-skirt rescue.

## The method

1. **Footprint + survey.** Take the build's axis-aligned bounding box (the `protect_box`) and survey
   a ring of terrain just outside it for the surrounding palette (dominant surface/subsurface blocks).
2. **Apron band.** Define a band of `apron_width` columns (8-24) outside the protect box. Erosion
   strength tapers `smoothstep(0, apron_width, dist)` from full at the build edge to zero at the
   band's outer edge.
3. **Erode the apron, protect the build.** Run thermal (and optionally light hydraulic) erosion over
   the apron only; the protect-box columns never change. This slumps the hard edge into a natural
   talus/grade.
4. **Re-materialize to the surrounding palette.** Grass tracks the new surface; rock exposes on
   newly-steepened faces; sediment/beach where it filled; water re-floods to sea level. Blend the
   build palette -> surrounding palette across the taper so the seam disappears in colour too.
5. **Dry-run -> check -> apply.** Always run the erosion with `dry_run: true` first; it returns
   height-delta stats (`max_delta`, `mean_abs_delta`, `moved`) — confirm the magnitude is sane before
   re-running with `dry_run: false`. For a high-stakes seam, take the offline route (read -> erode ->
   `render_views` -> apply) for a true visual pre-check. Under autonomy the dry-run check is the gate —
   no blind in-world erosion.

## Erosion tools (mod >= 0.4.0)

- **Thermal, synchronous — `block_erode_region`** (the default for aprons/foundations: deterministic
  talus collapse, sub-second). Region is `origin{x,z}` + `width`/`length` + `floor_y` (a column grid
  like `block_fill_columns`, <= 65,536 cols). Pass `protect_box{x0,z0,x1,z1}` = the build footprint,
  `apron` = taper width, `surface` + `subsurface` = the dominant surveyed blocks, `dry_run: true`
  first. See `reference/execution/engine-limits.md`.
- **Hydraulic, async — `block_erode_hydraulic_start` -> `_status` -> `_result`** (for naturalising
  larger/coarser terrain with carved drainage). `start` returns a `job_id`; poll
  `block_erode_hydraulic_status` until state `DONE`, then read `block_erode_hydraulic_result`. Same
  `protect_box`/`apron`/`dry_run`; region default 256x256, hard cap 512x512 (tile larger client-side).
- **Offline route (any mod, or a true visual pre-check):** read apron heights via
  `block_get_top_y`/`block_scan_region`, build a HeightField, run `erode_thermal` +
  `blend.weld`/`pad_crop_smooth` over the apron in `tools/terrain`, `render_views` to verify, then
  materialize via `block_fill_columns` and re-paint biomes with `level_fill_biome`.

**Current tool limits.** The server erosion tools re-cap with a single `surface`/`subsurface` block
and clear-above on lowered columns; they do not yet infer a multi-block palette, expose rock on
newly-steepened faces, or re-flood water. For a seam needing colour-blend, rock exposure, or water,
use the offline route (until the 0.4.x erosion-depth upgrade).

## When it runs

Every footprint-bearing build runs integration as GATE B of the spine (before inspect). The
`exec-inspect` seam check then confirms no hard build<->world edge remains; the harness lint requires
a `seam` row in the phase's `quality_contract`.

## Naturalizing existing terrain (purpose 2)

The same tool, with no `protect_box`, naturalizes vanilla worldgen or a coarse placement we didn't
author: read the region, erode, re-materialize from the *inferred* palette (sampled from the existing
blocks). Use to soften artificial-looking terrain before building on it.
