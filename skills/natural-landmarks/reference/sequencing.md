# Build sequencing

The order operations run in is not arbitrary. Mixing carve-first and
build-up-first is the single most common landmark failure. Each primitive in
`primitives.md` is tagged with its method — follow it.

## Carve-first

Place a **solid substrate mass first**, then cut the form out of it with
air-fills. The cut walls inherit the substrate's stratigraphy — which is the
whole point for anything where you see *into* the rock.

Carve-first primitives: canyons, slot canyons, side canyons, cenotes, fjords,
lava tubes, sea arches, caldera bowls.

For these: build the `canyon-strata-stack` (or stone mass) completely, *then*
carve. Never carve into a hollow or unbanded mass — the walls will be wrong.

## Build-up-first

Add material **outward from the base or centre**. The outer shell is what
receives the weathering pass, so it must be the last solid geometry placed.

Build-up-first primitives: volcanoes, monoliths, inselbergs, hoodoos, mesas,
sea stacks, karst towers, dunes, travertine terraces, icebergs, granite domes,
columnar basalt.

## Water is always last

Place water sources **after** all surrounding geometry is in place.

- For waterfalls, dig the plunge pool **≥3× the fall height** *before* placing
  water, or the falls spread sideways.
- For a large still body, place sources along the top edge of a sealed basin
  and let them propagate, or fill the volume with sources.
- A useful vanilla trick: fill the channel with a placeholder solid first, then
  remove the placeholder from the outer edge inward so flow stays controlled.

## Weathering passes

Integrity-based weathering happens **after main geometry, before decoration**:

1. Build the form clean and smooth.
2. Capture a weathering-pattern region as a structure with
   `mc_structure_create_from_world`.
3. Re-place it with `integrity` 30–70 and a **deterministic seed string** (from
   project + primitive + index) so a rebuild is reproducible.

Bedrock `integrity` is a **0–100 integer**, not a 0–1 float — do not reuse
Java integrity values. `integrity 60` removes ~40% of the structure's blocks.
See `terraforming/reference/command-budget.md` for the full mechanic.

Exception: **do not weather ordered formations** — a Bryce hoodoo field reads
as carved and orderly, not eroded.

## Decoration last

Pointed dripstone, vines, glow lichen, moss carpet, flowering azalea, and
saplings go on **after** everything else. Suppress vegetation spread during
construction (`mobGriefing false`, or remove ticking areas) so grass does not
creep over bare-rock landmarks. Use `coarse_dirt` / `rooted_dirt` as the
substrate next to rock to block grass spread.

## Lighting tricks

Light placed *behind* translucent blocks gives effects vanilla cannot
otherwise: `glowstone` behind orange terracotta for a Bryce sunset glow; a
sea lantern or ochre froglight beneath blue ice for a glacier glow; `magma_block`
as ambient floor light in a lava tube. Plan these into the build, not as an
afterthought.

## Standard landmark build order

1. Substrate / strata stack (carve-first wonders) **or** core mass (build-up).
2. Primary form — carve or build per primitive method.
3. Secondary primitives (side canyons, talus skirts, satellite stacks).
4. Weathering integrity passes on exposed shells.
5. Water.
6. Decoration and lighting.
