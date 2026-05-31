# Researching Terrain, Geology & Ecology (consumed by survey-research)

When a terrain build references a real or named place — a specific canyon, a coastline, a mountain
range, a biome — `survey-research` loads this to ground the recipe in fact, the way it loads building
references for architecture. Generic research is tuned for buildings; terrain needs different facts.

## What to pull for a terrain subject

- **Landform morphology.** The shape that makes it recognizable: aspect ratio (Uluru ~3:1 wider than
  tall; Devils Tower tall/narrow), the 2-4 signature features (Grand Canyon = 7 strata bands +
  meandering river + perpendicular side canyons; Niagara = horseshoe brink + plunge pool), typical
  slope angles, scale.
- **Geology / strata.** The rock sequence and colours, top->bottom — for canyons/mesas/badlands the
  banding *is* the signature. Map to a Minecraft palette (red/orange/white terracotta, sandstones,
  deepslate). Real strata are roughly horizontal with low-frequency undulation, never per-column random.
- **Hydrology.** River courses (dendritic, meandering — never straight), lakes, waterfalls, the
  drainage pattern. Drives `fluvial_rivers` thresholds and `carve_river` paths.
- **Climate -> biome.** Temperature/precipitation of the real place -> the closest vanilla biome(s) and
  the plant community. Drives `BiomeField` parameters and `BIOME_CONTENT` choices.
- **Ecology.** Dominant species and their distribution (riparian vs. upland, north vs. south slope,
  tree line). Maps to the scatter species mix and density.

## Sources

DEMs (SRTM / Copernicus via QGIS, Tangram Heightmapper, World Machine) for real elevation -> import
with `HeightField.from_image` / the `ImageDEM` sampler node (16-bit PNG to avoid terracing).
Geological survey maps and cross-sections for strata. Biome/climate references (Whittaker diagram) for
the climate->biome mapping. Cite sources in the research note so the recipe is auditable.

## Output

A short research note (in `.minecraft-builder/<project>/`) the terrain-* skill turns into recipe
parameters: signature features list, strata palette top->bottom, scale/aspect ratio, river pattern,
biome + species mix. For named natural wonders, `terrain-landmark` maps these onto its primitive
library (`${CLAUDE_PLUGIN_ROOT}/reference/terrain/primitives.md`).
