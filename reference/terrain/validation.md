# Terrain Validation (consumed by exec-inspect; mirrored by verify.py)

The terrain-specific checks `exec-inspect` runs in-world, mirroring the offline `tools/terrain/verify.py`
gate so offline and in-world agree. The six failure modes each map to a check.

## The checks

1. **No ziggurat (failure #1).** Render the placed region's profile / eye-level. Slopes must be
   compound — not flat tops with vertical walls. Offline: `verify.py` `no_ziggurat` score < 0.6. The
   harness lint refuses a terrain phase that is stacked Y-band rectangular fills.
2. **No seam (failure #2).** Render iso **and** eye-level across every region boundary and the
   build<->world edge. No boundary wall — height must ramp. Offline: `verify.verify_seam(h, max_step=12)`.
3. **No bare walls (failure #3).** Render the **slope map**. Every steep (red) face must be
   materialized as rock/strata by the slant palette — never default surface/stone. Sample steep
   columns in-world and confirm rock, not grass.
4. **Detail preserved on re-sculpt (failure #4).** A re-sculpt must edit the recipe and re-emit, not
   rebuild — confirm the recipe.json is the source and unaffected regions are unchanged.
5. **No silent op failure (failure #5).** Assert the columns/scatter/erode response counts match
   expected; tile non-auto-tile ops; force-load + verify `block_get_top_y != -64` before passes.
6. **Gates ran (failure #6).** Confirm the offline verify token is present and the Integrate pass ran
   (apron exists, no hard footprint edge).

## Verify at eye-level, NEVER top-down alone

The parks-grand-loop lesson: top-down renders showed "done" while the vertical faces a player sees
were bare gray walls. For any ride-through / walk-through terrain, the acceptance renders are
**iso + eye-level + slope**. Top-down is valid only for flat-pattern checks (mosaics, road networks).
A user visual checkpoint is required under autonomy for hero terrain.

iso is not enough on its own either. iso hides vertical faces, far-side openings, and texture seams
because the camera only sees one set of faces. The Zion build repeatedly "verified done" by iso while
the user's in-game screenshots caught what it missed: a floating overhang above a wall rail, a
west-facing alcove on the far side from the iso camera (it read as solid wall), and a smooth-vs-rough
endcap seam. For anything a player views from *inside* — ledges, alcoves, overhangs, wall texture —
add an **eye-level / thin-slab cross-section** render: `view: side` or `view: front` over a 1-3 block
slab, which shows the recess or overhang in profile that iso flattens away. Worked example: to check a
wall-base rail bench for the floating-overhang problem, render a z-slab one to three blocks deep
at the rail and read the wall-and-bench profile side-on. Treat the user's in-game look as the
acceptance gate.

## Underwater faces

Sample **below** sea level too — pad walls, foundation faces, the seabed profile. Cape Aurelia's
rectangular corestone passed inspection because only above-water was sampled; underwater it was a
sheer 80-block rectangle. Coastal/underwater terrain must include below-sea samples in its
`quality_contract`.

## quality_contract rows (terrain)

`silhouette` (Y variance >= 3, no flat plateaus), `edge_irregularity` (7-block rule on rims/coasts),
`block_mix_ratios` (no single block > 70%), `asymmetry`, `foundation_naturalised` (underwater face >= 3
block ids), `water_continuity` (water to seabed, no dry shelf), `seam` (no hard build<->world edge).
