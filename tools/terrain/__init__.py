"""The terrain toolkit — author a heightfield, *render-verify it offline*, then
materialise it to world fills. The 2.5-D counterpart of the ``voxel`` toolkit.

    from terrain import HeightField, TerrainLayers, render_views, write_terrain_fills

    hf = (HeightField(160, 128, sea_level=62)
          .add_fbm(44, octaves=5, base_freq=0.02, warp=18, seed=7)
          .radial_falloff(max_radius=72, inner=0.15, sz=1.15)
          .erode_hydraulic(droplets=12000, seed=1))
    render_views(hf, "/abs/scratch/island")          # Read the 3 PNGs, then tune
    layers = TerrainLayers(surface={"minecraft:grass_block": 0.8,
                                    "minecraft:coarse_dirt": 0.2})
    write_terrain_fills(hf, "/abs/scratch/island_fills.json", layers, origin=(100, -200))
    # place:  python tools/voxel/mcp_place.py place /abs/scratch/island_fills.json
"""
from .noise import ValueNoise2D, fbm
from .field import HeightField, Centerline, smoothstep
from .erosion import hydraulic, thermal
from .render import render_hillshade, render_relief, render_profile, render_views
from .materialize import TerrainLayers, to_voxel_model, write_terrain_fills

# Blended multi-region terrain — one continuous field, never butted segments:
#     loop = Centerline([(20,20),(140,20),(140,108),(20,108)], closed=True)
#     hf.belt_from_path(loop, [(0.0, dict(base=64, peak=40, rise=28)),   # red rock
#                              (0.25,dict(base=66, peak=70, rise=20)),   # alpine
#                              (0.5, dict(base=64, peak=34, rise=30)),   # forest
#                              (0.75,dict(base=66, peak=70, rise=20))],  # alpine
#                       corridor_half=4, interior_level=66)             # protect the rail

__all__ = [
    "ValueNoise2D", "fbm",
    "HeightField", "Centerline", "smoothstep",
    "hydraulic", "thermal",
    "render_hillshade", "render_relief", "render_profile", "render_views",
    "TerrainLayers", "to_voxel_model", "write_terrain_fills",
]
