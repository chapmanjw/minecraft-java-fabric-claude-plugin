# Landforms

Shaping rock and land. Every technique here assumes the non-negotiable rules
from `SKILL.md` (7-block rule, asymmetry, no 45°, double-layer).

## The heightmap method — default for anything over ~30 blocks

For any landform whose footprint is larger than ~30 blocks in either
horizontal axis, **build it from a per-column heightmap**, not from stacked
rectangular fills. This is the technique that took Cape Aurelia from a flat
ziggurat to "1000× better" in one rebuild.

The recipe:

1. **Per-column heightmap.** For each `(x, z)` in the footprint compute a
   target surface height `h(x, z)` as:

   ```
   h(x, z) = sea_level
           + base_amplitude * radial_falloff(x, z, center, max_radius)
           * sum_octaves(value_noise(x*f, z*f) * a for (f, a) in octaves)
   ```

   - **Multi-octave value noise.** 3–4 octaves at frequencies (0.06, 0.13,
     0.27, 0.55) and amplitudes (1.0, 0.5, 0.25, 0.12), summed and normalised.
     A coherent surface with detail at every scale.
   - **Radial falloff.** Smoothstep that goes 1 at the centre and 0 at
     `max_radius`. Multiplied with the noise so the landmass tapers naturally
     into the surrounding sea or plain.
   - **Organic blob lakes / coves / inlets.** A cove is a point where
     `hypot(dx*sx, dz*sz) + valueNoise(x,z) < 1` — an irregular elliptical
     blob, never a circle or rectangle. Carve from `h` so the column floods.
   - **Blended build pads.** Where a flat pad is needed for a building, set
     `h = pad_height` inside the pad and blend a 9-block shoulder where it
     meets natural terrain. The pad is buildable; the shoulder hides the
     transition.

2. **Bake to RLE tiles.** Walk `(x, z)` in tile-sized chunks (≤30×30 with a
   tile depth fitting under 64×384×64 and ~1500 RLE runs — see
   `command-budget.md`). For each column write a vertical run: stone /
   substrate / surface block / air (or water above sea level). Encode as
   compact RLE for `mc_structure_create_from_blocks`.

3. **Place tiles.** One `mc_structure_create_from_blocks` per tile, one
   `mc_structure_place` per spot. Pace the placements (≤6–8 in a row, then a
   light verify read) to avoid bridge drops.

4. **Tiles reach the seabed.** For coastal tiles, extend the column down to
   the seabed (or at least 10 blocks below the lowest expected water column)
   so water sits on real ground, not in a void-over-rock shelf.

This is fast, repeatable, and produces organic terrain by construction. Once
the heightmap is right, re-placing it is one tool call per tile. Stacked
rectangular fills produced the v1 ziggurat — do not return to that method.

## Naturalising an existing rectangular mass — the talus-skirt rescue

If you discover a rectangular foundation, base mass, or "corestone megablock"
underwater or above ground that violates the foundations-are-terrain rule,
**do not demolish it** — naturalise it. The pattern that worked at
Cape Aurelia:

1. **Banded talus skirt.** Place 4–6 concentric bands around the rectangle,
   each ~2–4 blocks wider than the band above it (or narrower as height
   rises). Mix the band's blocks with the surrounding terrain palette
   (basalt + smooth_basalt + tuff for a basaltic headland; granite + gravel
   + cobblestone for a generic mountain). Edge each band with the 7-block
   rule — never a clean ring.
2. **Corner knolls.** At each corner of the rectangle, place a small
   asymmetric mound that extends the rock outward and breaks the corner
   silhouette. Knolls should be different sizes; do not paste the same one
   four times.
3. **Side mounds.** Along the longer faces, drop 2–3 irregular mounds that
   bulge the wall outward by 4–8 blocks. Heights and footprints vary.
4. **Cap with naturalistic surface.** Top the skirt with the appropriate
   biome surface (grass/dirt + scree, sand + gravel, etc.) blended into the
   existing terrain above.

The result reads as an organic massif with the original rectangle hidden
inside it. Underwater, concentrate effort in the **lit band** (seabed → seabed
+ ~20); below that, fog black hides detail and the blocks are wasted.

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
