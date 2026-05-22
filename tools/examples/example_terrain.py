"""Smoke-test + worked example for the terrain toolkit.

Builds an eroded island with a cove and a river, renders the three verify views,
and writes a placeable fills JSON. Run it after installing the toolkit deps:

    python tools/examples/example_terrain.py

It writes terrain_hillshade.png / terrain_relief.png / terrain_profile.png and
terrain_fills.json next to this file. Read the PNGs to see the terrain before
placing; place with:

    python tools/voxel/mcp_place.py place tools/examples/terrain_fills.json
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))      # tools/ on the path

from terrain import HeightField, TerrainLayers, render_views, write_terrain_fills  # noqa: E402

SEA = 62

# 1) Author: smooth base + ridge layer, tapered to an irregular island, with a
#    flooded cove and a river carved down to the sea. Tune these vs the renders.
hf = HeightField(160, 128, sea_level=SEA, base=SEA)
hf.add_fbm(46, octaves=5, base_freq=0.020, warp=20, seed=7)      # rolling base
hf.add_fbm(14, octaves=3, base_freq=0.05, ridge=True, seed=11)  # ridgelines
hf.radial_falloff(max_radius=70, inner=0.12, sx=1.0, sz=1.18)   # island
hf.carve_lake(center=(58, 84), radii=(20, 14), depth=7, seed=3)  # cove
hf.carve_river([(120, 10), (104, 40), (96, 70), (78, 96), (60, 120)],
               width=3, depth=5, seed=5)                         # meandering river

# 2) Erosion — the realism multiplier. Run once the massing is right.
hf.erode_thermal(iterations=40, talus=1.4)
hf.erode_hydraulic(droplets=12000, seed=1)
hf.smooth(1)

print("field summary:", hf.summary())

# 3) Render-verify: Read these three PNGs and judge them before placing.
paths = render_views(hf, os.path.join(HERE, "terrain"))
print("rendered:", [os.path.basename(p) for p in paths])

# 4) Materialise to fills (double-layer substrate, mixed surface, beach, cliffs).
layers = TerrainLayers(
    surface={"minecraft:grass_block": 0.74, "minecraft:coarse_dirt": 0.16,
             "minecraft:stone": 0.06, "minecraft:moss_block": 0.04},
    subsurface="minecraft:dirt", subsurface_depth=3,
    cliff="minecraft:stone", cliff_slope_deg=52,
    beach={"minecraft:sand": 0.8, "minecraft:gravel": 0.2}, beach_band=2,
    seed=7,
)
summary = write_terrain_fills(hf, os.path.join(HERE, "terrain_fills.json"),
                              layers, origin=(0, 0))
print("fills summary:", summary["fills"], "fills;",
      "blocks:", summary["per_block"])
