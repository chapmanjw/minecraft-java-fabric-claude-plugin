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
from .field import HeightField, smoothstep
from .erosion import hydraulic, thermal
from .render import render_hillshade, render_relief, render_profile, render_views
from .materialize import TerrainLayers, to_voxel_model, write_terrain_fills

__all__ = [
    "ValueNoise2D", "fbm",
    "HeightField", "smoothstep",
    "hydraulic", "thermal",
    "render_hillshade", "render_relief", "render_profile", "render_views",
    "TerrainLayers", "to_voxel_model", "write_terrain_fills",
]
