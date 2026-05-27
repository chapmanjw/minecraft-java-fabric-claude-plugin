# Landforms

Shaping rock and land. Every technique here assumes the non-negotiable rules
from `SKILL.md` (7-block rule, asymmetry, no 45°, double-layer).

## The heightmap method — default for anything over ~30 blocks

For any landform whose footprint is larger than ~30 blocks in either
horizontal axis, **build it from a per-column heightmap**, not from stacked
rectangular fills. This is the technique that took Cape Aurelia from a flat
ziggurat to "1000× better" in one rebuild.

**Use the `terrain` toolkit, and render-verify it offline before placing
anything** — `${CLAUDE_PLUGIN_ROOT}/tools/terrain` (numpy + Pillow; the 2.5-D
counterpart of the `voxel` toolkit). You cannot see the world, and a stack of
fills *looks* fine in a plan but builds a ziggurat. Authoring the heightfield in
the toolkit lets you **render it and catch that in seconds**, not after a
demolition. Read `tools/README.md` for the full API. The loop:

1. **Author the heightfield.** Compose the surface from primitives that encode
   the rules by construction:

   ```python
   import os, sys
   sys.path.insert(0, os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "tools"))
   from terrain import HeightField, TerrainLayers, render_views, write_terrain_fills

   hf = (HeightField(nx, nz, sea_level=62)
         .add_fbm(46, octaves=5, base_freq=0.02, warp=20, seed=7)      # rolling base
         .add_fbm(14, octaves=3, base_freq=0.05, ridge=True, seed=11)  # ridgelines
         .radial_falloff(max_radius=70, inner=0.12, sz=1.18)           # taper to sea/plain
         .carve_lake(center=(58, 84), radii=(20, 14), depth=7, seed=3) # organic blob cove
         .carve_river([(120,10),(104,40),(96,70),(78,96),(60,120)], width=3, depth=5)
         .build_pad(center=(90, 60), half=(8, 6), level=70, shoulder=9))  # buildable pad
   ```

   - `add_fbm` is the **multi-octave value noise** (3–5 octaves); add a low-
     amplitude `ridge=True` layer for mountain ridgelines, and `warp` to break
     the griddy look.
   - `radial_falloff` is the **smoothstep taper** so the landmass eases into the
     surrounding sea/plain (`sx`/`sz` make it an irregular ellipse, not a disc).
   - `carve_lake` is the **organic blob** cove/inlet (`hypot(dx/rx, dz/rz) +
     noise < 1`), never a circle.
   - `build_pad` is the **blended build pad** with a shouldered skirt.

2. **Erode** — `.erode_thermal(...)` then `.erode_hydraulic(...)`. This is the
   single biggest realism multiplier: it carves coherent drainage and deposits
   sediment so the land reads as *eroded*, not *noisy*. Run it once the massing
   is right (it's the slow step).

3. **Render-verify offline — mandatory.** `render_views(hf, "/abs/scratch/site")`
   writes three PNGs; **Read them and judge against the references and the
   non-negotiables before placing a block:**
   - **hillshade** — terraces, flat tops, and the ziggurat artifact show as flat
     bands; good erosion reads as branching valleys. Look here first.
   - **relief** — hypsometric colour map: massing, coastline shape, lake/island
     outlines, beaches.
   - **profile** — cross-sections: proof the slopes are compound, not flat-
     topped or pure 45°.

   Tune one parameter, re-render. This replaces guessing — and is far cheaper
   than the in-world prototype patch (do that too, but *after* the render reads
   right).

4. **Materialise and place.** `write_terrain_fills(hf, path, layers, origin=(x,z))`
   bakes in the rules — double-layer substrate, a no-monoculture surface mix,
   rock on steep faces, beaches, and **water columns continuous to the seabed**
   — and emits the same fills JSON the `voxel` placer uses. Place it with one
   call:

   ```sh
   python ${CLAUDE_PLUGIN_ROOT}/tools/voxel/mcp_place.py place /abs/scratch/site_fills.json
   ```

   The heights are absolute world Y, so `sea_level=62` and real coordinates work
   directly, and coastal columns reach the floor by construction.

   **On a v0.3.0+ mod, prefer `block_fill_columns`** — send the height grid +
   palette and the server materialises the columns in one pass, with **no
   8192-entry cap** and no client-side box decomposition (tile to ≤65,536
   columns). Probe `tools/list` first; **fall back** to the `mcp_place.py` /
   `block_fill_batch` path above on older mods. See `reference/engine-limits.md`
   § Terrain helpers.

   **"Generated offline" means the *heightmap math* runs offline, not via a
   datapack.** Place with `mcp_place.py` / `block_fill_batch` / `block_fill_region`.
   **Never generate `.mcfunction` files and `/function` them in:** the mod can
   refuse to execute datapack functions (`/function` → "should not run",
   `/reload` → `successCount 0`), leaving terrain patchy and half-built.

5. **For reusable tiles, scratch-and-capture.** When a tile will be stamped many
   times, place it once, `structure_save_from_world` it as
   `mcb:<project>_terrain_<tile_id>`, then `structure_load_to_world` with varied
   rotation / mirror / `integrity` (see `command-budget.md`). Keep tiles under
   64×384×64. The heightfield script + its `.npy` are the reusable artifact for
   a one-off landform too large to be a single template — record them in the
   registry, exactly as for a large voxel model.

This is fast, repeatable, and produces organic terrain by construction. Stacked
rectangular fills produced the v1 ziggurat — do not return to that method.

**Import real elevation.** For a *named* real-world feature, `HeightField.from_image()`
loads a greyscale DEM heightmap PNG (exported from QGIS / Tangram Heightmapper /
World Machine / SRTM) and scales it to a Y range — the terrain analogue of
voxelizing a provided mesh, and the highest-fidelity path for a real mountain or
coastline. Render-check it before building, like any imported data.

## The continuous-field (belt) method — for blended multi-region terrain

The heightmap method above shapes one landform. When **several named regions
must abut seamlessly** — a ring of biomes, a valley grading into mountains, four
parks around a loop — do **not** author each as its own heightfield and stitch
them: every boundary and corner becomes a wall, and dithering the palette across
the seam blends *colour* while the *shape* discontinuity stays (terraforming
hard rule 4). Author the whole span as **one field parameterised by `(s, perp)`.**

`s` is arc-length along a centerline (or closed loop) through the span; `perp` is
signed perpendicular distance from it. Every cross-section parameter — base
level, crest height, rise distance, roughness, palette family, snowline — is a
**continuous function of `s`**, interpolated between region keypoints. With no
segments, regions morph gradually and corners blend by construction.

The `terrain` toolkit ships the primitive:

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "tools"))
from terrain import HeightField, Centerline, render_views

loop = Centerline([(20,20),(140,20),(140,108),(20,108)], closed=True)   # the rail ring
hf = HeightField(160, 128, sea_level=62)
hf.belt_from_path(loop, [                         # keypoints: (s_frac, cross-section)
        (0.00, dict(base=64, peak=40, rise=28)),  # red-rock straight
        (0.25, dict(base=66, peak=70, rise=20)),  # alpine straight (taller, steeper)
        (0.50, dict(base=64, peak=34, rise=30)),  # forest straight
        (0.75, dict(base=66, peak=70, rise=20))], # alpine straight
    corridor_half=4, interior_level=66, roughness=3)  # keep the rail corridor flat
render_views(hf, "/abs/scratch/loop")             # Read the PNGs; tune; only then place
```

- **`Centerline(points, closed=…)`** — the path/loop; `query(X, Z)` returns
  `(s, perp)` for any cells. Reusable for any corridor, road, river, or coast.
- **`belt_from_path(centerline, keypoints, …)`** — each region is a **belt**:
  the corridor (`|perp| ≤ corridor_half`) stays flat at `base` (protect a rail
  here); height rises to `base + peak` at the crest, then falls to
  `interior_level`, a uniform rolling interior. Rising-then-falling makes it a
  belt, which also removes the **medial-axis crease** a filled-footprint
  rectangle leaves down its spine.
- **`protect=<bool mask>`** — leave a working viaduct, village, or rail footprint
  untouched, so a re-sculpt fixes the blend without rebuilding hard-won work.

Layer the per-region richness (strata, hoodoos, couloirs) on top **driven by the
same `(s, perp)`** so it stays seam-free — continuity is a base-layer property,
richness a detail-layer one (see `SKILL.md` § Continuity belongs in the base
layer). Render-verify offline, then place via `mcp_place.py` /
`block_fill_columns` exactly as for the heightmap method.

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
- **Overhangs:** `block_clone_region` the top 2 strata of a cliff and
  translate them outward 3–8 blocks (use `masked` mode).
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
