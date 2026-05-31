# Terrain Toolkit API

The offline Python toolkit at `${CLAUDE_PLUGIN_ROOT}/tools/terrain` (numpy + scipy + Pillow;
optional `opensimplex`, `numba`). Import as `from terrain import ...` with `tools/` on `sys.path`.
This is the exact surface the terrain-* skills call.

## Sampler graph (`terrain.samplers`)

Author terrain shape as a nestable dict/JSON node tree; `from_spec(spec).eval(ctx)` evaluates it. Or
use `HeightField.from_graph(spec, nx, nz, sea_level=, seed=)`.

| Group | Nodes |
|---|---|
| sources | `Constant(value)`, `Noise(frequency, seed)`, `Cellular(frequency, ret=F1/F2/F2F1/inv_F1, jitter, seed)` |
| fractal | `FBM(frequency, octaves, lacunarity, gain, seed)`, `Ridged(... gain, offset, h)` (real Musgrave), `Billow(...)`, `Hybrid(... h, offset)` |
| warp | `DomainWarp(src, amplitude, frequency, levels, seed)` (2-vector) |
| arithmetic | `Add/Sub/Mul/Div/Min/Max(a, b)`, `Blend(a, b, selector, mid, rng)` |
| mutators | `Scale(src, factor)`, `Bias(src, offset)`, `Clamp(src, lo, hi)`, `Linear(src, in_lo, in_hi, out_lo, out_hi)`, `CubicSpline(src, points=[[x,y]...])`, `Posterize(src, steps)`, `Terrace(src, steps, smoothing, mask)` |
| geometry | `Distance(center, radius, inner, sx, sz)` (radial falloff), `ImageDEM(path, zoom)` (DEM), `BeltCoord(which=s/perp)` |

A bare number is sugar for `Constant`. Recipes round-trip via `node.to_spec()`.

## HeightField (`terrain.HeightField`)

- `HeightField(nx, nz, sea_level=62, base=62)` - `.h` is the `(nx,nz)` world-Y array.
- **author:** `from_graph(spec, nx, nz, sea_level=, seed=, centerline=)`, `add_fbm(...)`,
  `radial_falloff(...)`, `carve_lake/carve_river/build_pad(...)`, `belt_from_path(centerline, keypoints, ...)`, `apply_spline_remap(points)`, `from_image(path, ...)`.
- **shape:** `smooth(iterations)`, `gaussian_smooth(sigma, mask=)`, `melt(mask=, strength=, amount=)`,
  `distort(scale, distance, seed)`, `weld(mask, strength=)`, `erode_thermal(...)`,
  `erode_hydraulic(... pad_cells=, height_falloff=, sea_level=)`, `carve_rivers_from_flow(threshold, depth)`, `clamp(min_y, max_y)`.
- **analysis:** `slope_deg()`, `aspect_deg()`, `curvature()`, `dist_to_water()`, `mask_slope(lo, hi)`, `mask_y(op, y)`, `summary()`.
- **io:** `save_npy/load_npy`.

## Masks (`terrain.masks`)
`slope_deg(h)`, `aspect_deg(h)`, `curvature(h)`, `dist_to_water(h, sea)`, and boolean
`mask_slope/mask_y/mask_band/mask_curv/mask_near_water`. Combine with numpy `& | ~`.

## Blend (`terrain.blend`) - the seam fix
`box_blur_blend(label_grid, height_fns, radius)`, `sparse_convolution_blend(shape, seeds, height_fns, k)`, `weld(h, band_mask, strength)`, `pad_crop_smooth(h, sigma, pad, edge_heights)`. Blend radius must scale with the height delta across the seam (a ~46-block delta needs radius ~14+).

## Erosion (`terrain.erosion`)
`hydraulic(h, droplets, ..., pad_cells, height_falloff, sea_level)`, `thermal(h, iterations, talus, factor)`, `flow_accumulation(h)`, `fluvial_rivers(h, threshold, depth, sea_level)`.

## Climate (`terrain.BiomeField`)
`BiomeField(hf, seed=, latitude=)` -> `.climate()`, `.assign(boundary_jitter=)` (vanilla biome id grid), `.to_biome_fill_plan(origin, quant=4)` (-> `level_fill_biome` rects), `.palette_for(biome_id)`. `terrain.climate.BIOME_CONTENT` maps biome -> surface mix + feature ids + density.

## Scatter (`terrain.scatter`)
`density_map(hf, prefer_flat, near_water, height_band, base, avoid_steep_deg)`, `poisson(density, r_min, r_max, seed, k)` (variable-density blue noise), `assign_species(points, weights, seed)`, `scatter_for_biomes(hf, biome_field, origin, seed)` -> `[(x,y,z,"feature",id), ...]`.

## Materialize (`terrain.materialize`)
- `MaterialSpec(layers, base, subsurface, subsurface_depth, stone, water, strata, seed)` with
  `MaterialSpec.natural(hf, surface=, snow_y=, cliff_slope=, beach=)` for a sensible default.
- `Layer(mask, palette, subsurface)` - first match wins; `.slant = [(min_slope_deg, palette)]` rocks cliffs.
- `to_columns_plan(hf, spec, origin, floor_below, dimension)` -> the **block_fill_columns** payload
  (height/surface/subsurface arrays + palette + optional strata). `write_columns_plan(...)` to JSON.
- Legacy `to_voxel_model` / `write_terrain_fills` (voxel-grid path) kept for compatibility - prefer columns.

## Verify (`terrain.verify`) - GATE A
`verify(hf, ...)` -> `Report(ok, checks)` (bounds/relief/land/no_ziggurat). `verify_seam(h, max_step)`. HALT the build if `not report.ok`.

## Recipe & emit (`terrain.recipe`, `terrain.emit`)
`recipe.save/load`, `recipe.build_field(recipe)`. `emit.emit_world(recipe, allow_unverified=False)` ->
`{field, verify, columns, biomes, scatter}` (raises `VerifyError` on a failed gate). `emit.write_payloads(payloads, prefix)`.

## Render (`terrain.render`) - Pillar 8
`render_views(hf, prefix)` writes 5 PNGs: hillshade, relief, profile, **slope**, **eye-level**.
Individual: `render_hillshade/relief/profile/render_slope/render_eye_level`. Judge slope + eye-level,
never top-down alone.
