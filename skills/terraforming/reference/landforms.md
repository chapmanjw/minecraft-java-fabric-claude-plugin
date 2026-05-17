# Landforms

Shaping rock and land. Every technique here assumes the non-negotiable rules
from `SKILL.md` (7-block rule, asymmetry, no 45°, double-layer).

## Mountains

1. **Irregular base outline.** The footprint is never a circle or oval — it is
   uneven and lumpy. Walk the perimeter with 1–3 block lateral jitter every
   4–7 blocks.
2. **Regular rise, irregular plan.** Each contour level steps up one block in
   height, but its *shape* changes at every level.
3. **Height beats width.** Until near the peak, each level should be taller
   than it is wide. Target a height-to-base-radius ratio of 1:1.2 to 1:2.
4. **Round large mountains.** Jagged peaks read fine at small scale; at large
   scale, round the corners or it looks like rubble.
5. **Ridgelines connect peaks — never straight.** Pick the highest peak as the
   anchor; place 2–4 secondary peaks lower and laterally offset. Connect them
   with a curved ridgeline polyline.

**Build order (silhouette pass):** plot peak coordinates → walk a coarse
curved ridgeline between them → emit contours outward from each ridge node
with a diminishing random walk → fill the interior solid with tiled fills →
sweep the surface to notch overhangs and break regularity.

**Foothills & scree.** Radiate a gravel + cobblestone + andesite scatter from
the base, fading from ~60% rock at the foot to ~5% at the grass margin. A
saved scree module placed at `integrity 40` does this well.

**Exposed rock faces.** Mix at least three stone variants. 6–8 horizontal
bands is the sweet spot for a cliff face.

## Slopes

- **Avoid pure 45°** — it reads as manmade.
- **Convex** slopes (gentler near the top) suit old, eroded hills.
- **Concave** slopes (steeper near the top) suit young, aggressive peaks and
  glacial U-valley walls.
- Real mountainsides are **compound**: convex along the ridge, concave toward
  the valley.

## Valleys

- **V-shaped (river-cut):** narrow floor 1–4 blocks wide, rough walls at
  ~60–70°. Build by carving `fill ... air` down from a raised landmass.
- **U-shaped (glacier-cut):** wide floor 10–40+ blocks, steep walls, often
  with **hanging valleys** — tributary valleys that end in a cliff above the
  main floor.

## Plateaus, mesas, badlands, canyons

- **Horizontal terracotta banding** at regular Y intervals: bands 2–4 blocks
  tall of red / orange / yellow / white / light-gray / brown / plain
  terracotta, repeating.
- **±7 jitter:** shift each band up or down by up to 7 blocks per column
  (noise) so band edges are never perfectly level — this is how Minecraft's
  own badlands generation looks natural.
- **Hoodoos:** spires 1–3 blocks wide, 8–25 tall, banded, with a regular
  terracotta cap.

## Caves, overhangs, arches, sea stacks

- **Arches:** lay a horizontal plank of stone 1–3 blocks thick, then carve a
  parabolic profile out of the underside.
- **Overhangs:** `clone` the top 2 strata of a cliff and translate them
  outward 3–8 blocks (use `masked` mode).
- **Sea stacks:** isolated stratified columns standing in water, 5–15 across,
  12–40 tall, capped with grass and a sparse tree.
- **Cave shells:** `fill ... hollow` to carve a chamber, then break the
  regularity with notches and dripstone.

## Coastlines

- **Never straight** — the 7-block rule is strict here.
- **Beach gradient:** water → sand (3–8 wide) → mixed sand + coarse_dirt
  (2–4) → grass. For rocky coasts, swap sand for gravel + cobblestone.
- **Tide pools:** 2×2 to 4×4 indentations in coastal rock, 1–2 deep, filled
  with water, optionally seagrass and a sea pickle.

## Underwater terrain

- The sea floor needs the same anti-flatness treatment as land: mix sand
  (~60%), gravel (~20%), dirt (~10%), clay (~10%).
- **Continental shelf** around Y=50–55; drop to deep ocean Y=30–40 over a
  30–80 block transition.
- **Trenches:** vertical drops of Y=20–40 with deepslate + tuff walls.
- Kelp in clusters of 8–25 stalks; coral reefs in patches 5–20 across with
  mixed coral and coral fans on dead coral blocks.
