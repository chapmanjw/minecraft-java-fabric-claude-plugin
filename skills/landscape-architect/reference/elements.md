# Garden elements

The constructed pieces of a designed garden. Each is a reusable unit — define
it once as a `mcb:<project>_<element>` structure and stamp it.

## The leaf-persistence rule

Bedrock leaves **decay** unless near a log. Every hedge, topiary, parterre
hedge, and clipped allée built from leaf blocks must be placed as **persistent
leaves** or built on a **log core** within range. State this explicitly in the
plan — a garden whose hedges decay overnight is a failure. This applies to
every element below that uses leaves.

## Parterres

Low, flat, ornamental beds, viewed from above (from the house or a terrace):

- **Parterre de broderie** — scrollwork "embroidery" in low clipped hedging
  (boxwood-green leaves on a fence/log core) against a gravel ground.
- **Parterre à l'anglaise** — a simple lawn panel framed by a low hedge.
- **Knot garden** — interlacing low hedges of contrasting plants in a tight
  geometric knot.
- **Parterre d'eau** — a still reflecting rectangle (see `water.md`).

Build a parterre as a quartered, symmetric unit; the pattern is pre-baked into
the design, not randomized.

## Hedges and hedge mazes

- **Hedges** — leaf walls on a log core, 1–3 blocks thick, 2–5 tall; clipped
  flat-topped. Tall hedges (5–7) make dramatic maze walls.
- **Hedge maze** — **hand-design the topology**: a single solution path with
  dead-end branches and a goal at the center (a gazebo, a fountain, a raised
  viewing platform). Path width 2–3 blocks (one person) or 3–4 (comfortable).
  Verify every fork resolves — a maze with unintended loops or no solution is
  a failure. Do not generate it randomly (no `/random` on Bedrock anyway);
  bake the layout into the design.

## Topiary

Clipped leaf-and-log shapes — spheres, cones, cubes, pyramids, spirals — on a
log core for both structure and leaf persistence. Compute a sphere with the
voxel formula (`x²+y²+z²≤r²`) and soften it with stairs. Figurative animal
topiary is a `monument-builder` handoff.

## Allées and bosquets

- **Allée** — a formal avenue: paired rows of matched trees lining a path.
  Here, **uniformity is the design** — clipped, matched trees at exact spacing
  (6–10 blocks apart), unlike a naturalistic grove. Place them as a repeated
  tree unit, or as pollarded leaf-and-log forms.
- **Bosquet** — a formal block or grove of trees with a clipped outer face,
  often hiding a hidden room, a fountain, or a clearing within.
- A *naturalistic* clump (in an English-landscape garden) is the exception —
  grow it from saplings per the `terraforming` grow-trees rule.

## Paving

Hard ground in a deliberate pattern:

- **Chessboard** — two contrasting blocks alternating.
- **Herringbone, basketweave, running bond** — brick/stone-laid patterns.
- **Radial** — rings and spokes around a circular plaza.
- Materials: smooth stone, polished diorite, calcite, sandstone, dark
  prismarine, glazed terracotta (16 colours × 4 rotations) for civic plazas;
  gravel or light concrete for garden paths.

## Pergolas, arbors, and trellis

Open overhead structures — a pergola walk, a rose arbor, a vine trellis —
built of posts and beams with climbing planting. Open structures stay with
this skill; a **roofed** garden building (gazebo-as-building, summerhouse,
temple, tea house) is a `building-architect` handoff — you place the
footprint.

## Garden furniture

Benches, sundials, urns and finials, balustrades, low walls, gate piers,
stone lanterns (Japanese). Small, but they finish the garden — place them on
the axes and at the vista points.
