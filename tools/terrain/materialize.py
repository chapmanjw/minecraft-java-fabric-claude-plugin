"""Turn a verified ``HeightField`` into world block fills — the terrain
equivalent of ``voxel.write_fills_json``.

Materialisation bakes the non-negotiable rules into the columns by construction:

- **double-layer substrate** — every surface sits on ``subsurface_depth`` blocks
  of dirt/sand over stone, never paint-on-stone;
- **no monoculture** — the surface is a weighted *mix* of blocks, dithered with a
  seeded field, not one flat block;
- **rock on steep faces** — columns steeper than ``cliff_slope_deg`` show the
  ``cliff`` stone instead of grass, so cliffs read as rock;
- **beaches** — a sand/gravel band hugs the waterline;
- **water columns to the floor** — any column below sea level is filled with
  water from the surface up to ``sea_level`` (no void-over-rock shelf).

The result is decomposed by the ``voxel`` toolkit's greedy box cover, so the
output is the same fills JSON ``mcp_place.py`` already places — terrain and
objects share one placement path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# Approximate RGBs so the optional voxel iso render of materialised terrain
# reads correctly; placement only uses the block ids.
_RGB = {
    "minecraft:grass_block": (110, 160, 70),
    "minecraft:dirt": (134, 96, 67),
    "minecraft:coarse_dirt": (120, 90, 60),
    "minecraft:podzol": (90, 64, 30),
    "minecraft:rooted_dirt": (140, 105, 80),
    "minecraft:stone": (125, 125, 125),
    "minecraft:cobblestone": (127, 127, 127),
    "minecraft:andesite": (132, 134, 133),
    "minecraft:gravel": (130, 128, 122),
    "minecraft:granite": (150, 103, 86),
    "minecraft:deepslate": (77, 77, 80),
    "minecraft:sand": (219, 207, 163),
    "minecraft:sandstone": (219, 207, 163),
    "minecraft:red_sand": (190, 102, 33),
    "minecraft:snow_block": (240, 240, 245),
    "minecraft:powder_snow": (236, 240, 248),
    "minecraft:water": (50, 90, 160),
    "minecraft:moss_block": (90, 110, 50),
}


@dataclass
class TerrainLayers:
    surface: dict                              # block_id -> weight (the mix)
    subsurface: str = "minecraft:dirt"
    subsurface_depth: int = 3
    stone: str = "minecraft:stone"
    water: str = "minecraft:water"
    cliff: Optional[str] = "minecraft:stone"   # shown on steep faces
    cliff_slope_deg: float = 55.0
    beach: Optional[dict] = None               # surface mix at/near the waterline
    beach_band: float = 2.0
    seed: int = 0


def _choice_field(weights: dict, shape, seed, pal):
    """Per-cell block-code field sampled from a weighted mix (no monoculture)."""
    rng = np.random.default_rng(seed)
    r = rng.random(shape)
    items = list(weights.items())
    w = np.array([v for _, v in items], dtype=float)
    w = w / w.sum()
    cum = np.cumsum(w)
    out = np.zeros(shape, dtype=np.uint8)
    assigned = np.zeros(shape, dtype=bool)
    for (bid, _), c in zip(items, cum):
        code = pal.add(bid, _RGB.get(bid))
        sel = (~assigned) & (r <= c)
        out[sel] = code
        assigned |= sel
    if not assigned.all():                     # rounding remainder → last block
        last = pal.add(items[-1][0], _RGB.get(items[-1][0]))
        out[~assigned] = last
    return out


def to_voxel_model(hf, layers: TerrainLayers, *, base_below: int = 4):
    """Build a ``voxel.VoxelModel`` of the terrain and return ``(model, y_min)``
    where ``y_min`` is the world Y of grid row 0. ``base_below`` is how many
    extra stone blocks to carry beneath the deepest column."""
    from voxel import Palette, VoxelModel

    pal = Palette()
    stone_code = pal.add(layers.stone, _RGB.get(layers.stone, (125, 125, 125)))
    sub_code = pal.add(layers.subsurface, _RGB.get(layers.subsurface, (134, 96, 67)))
    water_code = pal.add(layers.water, _RGB.get(layers.water, (50, 90, 160)))
    cliff_code = pal.add(layers.cliff, _RGB.get(layers.cliff, (120, 120, 120))) \
        if layers.cliff else stone_code

    surf = np.rint(np.clip(hf.h, -63, 319)).astype(int)
    sea = int(round(hf.sea_level))
    sub_depth = int(layers.subsurface_depth)
    y_min = int(surf.min()) - sub_depth - int(base_below)
    y_max = int(max(surf.max(), sea))
    ny = y_max - y_min + 1
    nx, nz = hf.nx, hf.nz

    # surface + subsurface code fields
    surf_code = _choice_field(layers.surface, (nx, nz), layers.seed, pal)
    subsurf = np.full((nx, nz), sub_code, dtype=np.uint8)

    slope = hf.slope_deg()
    steep = slope > layers.cliff_slope_deg
    surf_code[steep] = cliff_code
    subsurf[steep] = cliff_code

    if layers.beach:
        beach_code = _choice_field(layers.beach, (nx, nz), layers.seed + 9, pal)
        nearshore = (surf >= sea) & (surf <= sea + layers.beach_band) & (~steep)
        surf_code[nearshore] = beach_code[nearshore]
        subsurf[nearshore] = pal.add("minecraft:sand", _RGB["minecraft:sand"])

    g = np.zeros((nx, ny, nz), dtype=np.uint8)
    for x in range(nx):
        for z in range(nz):
            top = int(surf[x, z])
            g_top = top - y_min
            g_stone_top = (top - sub_depth) - y_min      # exclusive
            g[x, 0:g_stone_top, z] = stone_code
            g[x, g_stone_top:g_top, z] = subsurf[x, z]
            g[x, g_top, z] = surf_code[x, z]
            if top < sea:
                g[x, g_top + 1: (sea - y_min) + 1, z] = water_code

    m = VoxelModel(nx, ny, nz, pal)
    m.g = g
    return m, y_min


def write_terrain_fills(hf, path: str, layers: TerrainLayers, *,
                        origin=(0, 0), cap: int = 32000, base_below: int = 4) -> dict:
    """Materialise ``hf`` and write a ``block_fill_batch``-ready fills JSON.

    ``origin`` is the world ``(x, z)`` of grid cell (0, 0); world Y comes from
    the field's heights directly. Place the result with
    ``mcp_place.py place <path>``. Returns the ``write_fills_json`` summary
    (fill count, per-block counts, bounding box)."""
    from voxel import write_fills_json
    model, y_min = to_voxel_model(hf, layers, base_below=base_below)
    ox, oz = origin
    return write_fills_json(model, path, origin=(ox, y_min, oz), cap=cap)
