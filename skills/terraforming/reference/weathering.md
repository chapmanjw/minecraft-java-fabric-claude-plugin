# Weathering, detail & composition

The final pass — and the largest visual-quality multiplier per block of
effort. Shaped, palettized terrain still looks flat until it is weathered.

## Surface speckling / noise

Break up any uniform surface with 5–15% variant noise:

- **Structure-integrity method (best).** Save a single-block module (one
  `minecraft:coarse_dirt` block, say) with `structure_save_from_world`. Load
  it across the target region with `structure_load_to_world` at `integrity 0.3`
  with a unique seed — only ~30% of positions place. Repeat with other blocks
  and other seeds to layer noise. (See `command-budget.md` for the
  integrity mechanic.)
- **Replace-fill method.** Chain `replace`-mode fills at descending coverage
  to convert subsets of a base block to variants.

## Detail-block library — use sparsely, never uniformly

Scatter these in **clusters**, not evenly:

- `rooted_dirt` — rare, in grass.
- `moss_block`, `moss_carpet` — shaded and damp areas.
- `azalea`, `flowering_azalea` — near water.
- `tall_grass`, `fern`, `large_fern` — understory.
- `grass` (short) tufts — on coarse dirt and edges.
- `dead_bush` — dry zones.
- Lone saplings — "first growth".
- Fallen logs — `oak` / `spruce` logs laid on their side, 3–6 long, near
  forest edges.
- `glow_lichen` — on vertical stone.
- `vine`, `cave_vines`, `hanging_roots` — on overhangs and under rooted_dirt.
- `pointed_dripstone` — cliff edges and cave ceilings.
- `sculk` patches — ancient, ruined areas.

## Vegetation distribution rules

- **Cluster, never sprinkle.** Plants "get lonely" — group them in 3–7 with
  2–8 blocks between clusters. Single plants are rare in dense biomes.
- **Density gradients.** High near water (>40% ground cover) → low on exposed
  slopes (<5%).
- **Edge bleed.** Forest edges scatter grass tufts 4–12 blocks outward into
  open ground.
- **Bare patches.** 5–15% of any "grass" region should be coarse dirt, podzol,
  or exposed stone — pristine uniform grass reads as paint.
- **Double-layer.** Always ≥2 substrate blocks under the surface.

## Trees — grow them, never place them

**Never build a tree block by block, and never stamp the same tree structure
twice.** A hand-placed canopy and duplicated trees are the loudest tell in any
landscape — real groves are all different. Every tree is **grown from a
sapling** so vanilla generation makes each one unique.

To plant trees:

1. **Pick the species** for the biome and the look — `oak_sapling`,
   `spruce_sapling`, `birch_sapling`, `jungle_sapling`, `acacia_sapling`,
   `dark_oak_sapling`, `cherry_sapling`, `mangrove_propagule`, or `azalea` /
   `flowering_azalea` (which grow into azalea trees).
2. **Place the sapling** with `block_set_state` on valid soil (dirt, grass,
   podzol, mud for mangrove), with the light and headroom the species needs.
   For 2×2 species — jungle, dark oak, large spruce — place the full
   four-sapling square.
3. **Space them naturally** — clusters of 3–7 with irregular gaps, never a
   grid. The 7-block rule applies to tree lines too.
4. **Grow them.** Two methods:
   - **Tick speed (scriptable).** Temporarily raise `randomTickSpeed` with
     `command_execute` (`/gamerule randomTickSpeed 300`), let the saplings grow,
     then **restore it to the default** (`/gamerule randomTickSpeed 3`). Raised
     tick speed also speeds crops, fire spread, and leaf decay in loaded chunks
     — raise it briefly and restore it promptly.
   - **Bone meal.** Apply bone meal to each sapling via `player_give_item` /
     `itemstack_drop_at` + use, or a dispenser.
   - **Place feature (most direct).** On a **v0.3.0+ mod**, call
     **`level_place_feature`** (dimension, feature id, position) to grow a
     configured feature at a spot — e.g. `minecraft:fancy_oak`,
     `minecraft:spruce`, `minecraft:flower_default` — no sapling/tick wait, and
     every placement varies. **Fall back** to `command_execute` with
     `/place feature minecraft:<feature> <x> <y> <z>` on older mods (same effect,
     untyped). This also grows **vegetation patches and ore veins** as features —
     the way to add natural detail (rule 7) without stamping identical copies.
5. **Vary** species, age, and spacing across a stand so no two trees match —
   that variation is the whole point of growing rather than placing.

A single oversized **hero tree** — a giant landmark baobab or sequoia beyond
vanilla sapling scale — may be custom-built as a deliberate one-off, but it is
never duplicated. Ordinary trees and every grove are grown.

Keep trees short and away from mountain feet — oversized trees dwarf the
topography and kill the sense of scale.

## Composition principles

Terrain is seen, not just built — compose it for the viewer.

- **Foreground / midground / background.** Detail-dense features 20–80 blocks
  from viewing positions; simplified features 80–200; silhouette-only beyond
  200 — far terrain needs a dramatic outline, not block detail.
- **One hero feature** per scene (the tallest mountain, the biggest fall).
  Subordinate features at roughly 1:0.6:0.4 scale. Let ridgelines and rivers
  guide the eye toward it.
- **Rule of thirds.** Place focal points about 1/3 across the visual field —
  for a 200×200 scene, the hero peak near (66,66) or (134,134), not center.
- **Negative space.** Reserve 20–40% of a scene as open space — sky, water,
  plain, valley floor. Quiet zones make the dense areas read as impressive.
- **Decay level.** When the user wants ruins or age, raise weathering density:
  more moss, cracked variants, `sculk` patches, fallen logs, vine drape, and
  partial structure `integrity` on placed modules.
