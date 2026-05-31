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
    (fill count, per-block counts, bounding box).

    NOTE: this is the legacy *voxel-grid* path, kept for compatibility. New
    terrain should use ``to_columns_plan`` (Pillar 2) which emits a
    ``block_fill_columns`` plan — one server call, no 3-D grid, no box decompose.
    """
    from voxel import write_fills_json
    model, y_min = to_voxel_model(hf, layers, base_below=base_below)
    ox, oz = origin
    return write_fills_json(model, path, origin=(ox, y_min, oz), cap=cap)


# ======================================================================
# Pillar 2 — mask-driven materialisation → block_fill_columns plan
# ======================================================================

@dataclass
class Layer:
    """One surface layer: where it applies (a boolean ``(nx, nz)`` mask) and the
    weighted block mix to dither there. First matching layer wins per column."""
    mask: "np.ndarray"
    palette: dict                       # block_id -> weight
    subsurface: str = "minecraft:dirt"


@dataclass
class MaterialSpec:
    """Declarative materialisation: a stack of mask→palette ``Layer``s plus a
    slope-keyed ``slant`` override, the substrate, and (optionally) strata bands.

    The layer stack replaces the hardcoded rules: snow above the snowline, rock
    on steep faces, beach near water, grass elsewhere become ``Layer`` masks
    (computed from ``terrain.masks``). ``slant`` is ``[(min_slope_deg, palette)]``
    applied last where the slope exceeds the threshold (the Terra "slant palette"
    — guarantees cliff faces are materialised intentionally, not left as default
    stone). ``strata`` ``[(block, thickness)]`` bands the deep fill top→bottom
    (materialised by the server-side ``block_fill_columns_strata`` tool; ignored
    by the single-stone column plan)."""
    layers: list                        # list[Layer], first match wins
    base: dict = None                   # fallback surface mix if no layer matches
    subsurface: str = "minecraft:dirt"
    subsurface_depth: int = 3
    stone: str = "minecraft:stone"
    water: str = "minecraft:water"
    strata: list = None                 # [(block_id, thickness)] top→bottom
    seed: int = 0

    @classmethod
    def natural(cls, hf, *, surface=None, snow_y=None, cliff_slope=50.0,
                beach=True) -> "MaterialSpec":
        """A sensible default spec built from the field's masks — the
        declarative twin of the old ``TerrainLayers`` behaviour, plus snowline
        and aspect-free defaults. ``surface`` overrides the temperate grass mix."""
        import numpy as np
        from . import masks as M
        surface = surface or {"minecraft:grass_block": 0.78,
                              "minecraft:coarse_dirt": 0.14,
                              "minecraft:moss_block": 0.05,
                              "minecraft:stone": 0.03}
        layers = []
        if beach:
            near = M.mask_near_water(hf.h, hf.sea_level, within=3) & \
                M.mask_band(hf.h, hf.sea_level, hf.sea_level + 2) & \
                ~M.mask_slope(hf.h, lo=cliff_slope)
            layers.append(Layer(mask=near,
                                palette={"minecraft:sand": 0.8, "minecraft:gravel": 0.2},
                                subsurface="minecraft:sand"))
        if snow_y is not None:
            layers.append(Layer(mask=M.mask_y(hf.h, ">", snow_y) &
                                ~M.mask_slope(hf.h, lo=cliff_slope),
                                palette={"minecraft:snow_block": 0.85,
                                         "minecraft:powder_snow": 0.15},
                                subsurface="minecraft:dirt"))
        slant = [(cliff_slope, {"minecraft:stone": 0.6, "minecraft:cobblestone": 0.25,
                                "minecraft:andesite": 0.15})]
        spec = cls(layers=layers, base=surface, subsurface="minecraft:dirt")
        spec.slant = slant
        return spec


def _weighted_pick(weights: dict, shape, seed) -> "np.ndarray":
    """Object array of block-id strings sampled from a weighted mix."""
    rng = np.random.default_rng(seed)
    r = rng.random(shape)
    items = list(weights.items())
    w = np.array([v for _, v in items], dtype=float)
    cum = np.cumsum(w / w.sum())
    out = np.empty(shape, dtype=object)
    assigned = np.zeros(shape, dtype=bool)
    for (bid, _), c in zip(items, cum):
        sel = (~assigned) & (r <= c)
        out[sel] = bid
        assigned |= sel
    out[~assigned] = items[-1][0]
    return out


def resolve_surface(hf, spec: "MaterialSpec"):
    """Return ``(surface_ids, subsurface_ids)`` object arrays, applying the layer
    stack (first match wins), the base fallback, then the slant override."""
    nx, nz = hf.nx, hf.nz
    surface = np.empty((nx, nz), dtype=object)
    subsurf = np.empty((nx, nz), dtype=object)
    base_mix = spec.base or {"minecraft:grass_block": 1.0}
    surface[:] = None
    base_field = _weighted_pick(base_mix, (nx, nz), spec.seed)
    surface = np.where(surface == None, base_field, surface)  # noqa: E711
    subsurf[:] = spec.subsurface
    claimed = np.zeros((nx, nz), dtype=bool)
    for i, layer in enumerate(spec.layers):
        m = np.asarray(layer.mask, dtype=bool) & ~claimed
        if not m.any():
            continue
        pick = _weighted_pick(layer.palette, (nx, nz), spec.seed + 11 + i)
        surface = np.where(m, pick, surface)
        subsurf = np.where(m, layer.subsurface, subsurf)
        claimed |= m
    # slant override (applied regardless of prior layers)
    slant = getattr(spec, "slant", None)
    if slant:
        from . import masks as M
        for min_slope, pal in slant:
            steep = M.mask_slope(hf.h, lo=min_slope)
            if steep.any():
                pick = _weighted_pick(pal, (nx, nz), spec.seed + 101)
                surface = np.where(steep, pick, surface)
                # subsurface under a cliff is the dominant slant block
                dom = max(pal, key=pal.get)
                subsurf = np.where(steep, dom, subsurf)
    return surface, subsurf


def to_columns_plan(hf, spec: "MaterialSpec", *, origin=(0, 0), floor_below: int = 6,
                    dimension: str = "minecraft:overworld") -> dict:
    """Emit a ``block_fill_columns`` plan dict (Pillar 2): a compact height grid
    + small palette + per-column surface/subsurface indices, materialised by the
    server in one call (no 3-D voxel grid, no box decompose — the throughput win).

    Row-major arrays, length ``width*length``, index ``xi*length + zi`` — the
    exact convention the ``block_fill_columns`` MCP tool expects. ``origin`` is
    the world ``(x, z)`` of cell (0,0); ``floor_y`` is set ``floor_below`` blocks
    under the lowest surface. If ``spec.strata`` is set, a ``strata`` key is
    included for the ``block_fill_columns_strata`` tool (the single-stone tool
    ignores it)."""
    nx, nz = hf.nx, hf.nz
    surf_y = np.rint(np.clip(hf.h, -63, 319)).astype(int)
    surface_ids, subsurf_ids = resolve_surface(hf, spec)

    # build the palette: stone first (index 0 reserved-ish), then water, then uniques
    palette: list = []
    index: dict = {}

    def idx(bid: str) -> int:
        if bid not in index:
            index[bid] = len(palette)
            palette.append(bid)
        return index[bid]

    stone_index = idx(spec.stone)
    water_index = idx(spec.water)
    surf_idx = np.empty((nx, nz), dtype=int)
    sub_idx = np.empty((nx, nz), dtype=int)
    for x in range(nx):
        for z in range(nz):
            surf_idx[x, z] = idx(str(surface_ids[x, z]))
            sub_idx[x, z] = idx(str(subsurf_ids[x, z]))

    # row-major flatten (xi*length + zi)
    height = surf_y.reshape(-1).tolist()
    surface = surf_idx.reshape(-1).tolist()
    subsurface = sub_idx.reshape(-1).tolist()
    ox, oz = origin
    floor_y = int(surf_y.min()) - int(floor_below)

    plan = {
        "dimension": dimension,
        "origin": {"x": int(ox), "z": int(oz)},
        "width": nx, "length": nz,
        "floor_y": floor_y,
        "palette": palette,
        "stone_index": stone_index,
        "height": height,
        "surface": surface,
        "subsurface": subsurface,
        "subsurface_depth": int(spec.subsurface_depth),
        "sea_level": int(round(hf.sea_level)),
        "water_index": water_index,
    }
    if spec.strata:
        plan["strata"] = [{"block": b, "thickness": int(t)} for b, t in spec.strata]
    return plan


def tile_columns_plan(plan: dict, cap: int = 65536) -> list:
    """Split a ``to_columns_plan`` output into sub-plans each with
    ``width*length <= cap`` so a single ``block_fill_columns(_strata)`` call
    never exceeds the server's column limit.

    The grid is sliced along its **longer** axis first (fewer, larger tiles);
    if a full strip of the longer axis still exceeds ``cap``, the shorter axis
    is sub-divided too. The row-major ``height``/``surface``/``subsurface``
    arrays (index ``xi*length + zi``) are reshaped to ``(width, length)``, the
    tile rectangle is sliced, then re-flattened row-major — so each sub-plan is
    itself a valid ``block_fill_columns`` plan with the same keys (``strata[]``
    carried through unchanged) and its ``origin`` adjusted by the tile offset.

    Coverage is exact: the tiles partition the grid with no lost or overlapping
    columns (their concatenated column sets equal the original)."""
    if cap < 1:
        raise ValueError("cap must be >= 1")
    width = int(plan["width"])
    length = int(plan["length"])
    n = width * length
    if n <= cap:
        return [dict(plan)]

    # reshape the row-major arrays to (width, length) for rectangular slicing
    h2 = np.asarray(plan["height"]).reshape(width, length)
    s2 = np.asarray(plan["surface"]).reshape(width, length)
    sub2 = np.asarray(plan["subsurface"]).reshape(width, length)
    ox = int(plan["origin"]["x"])
    oz = int(plan["origin"]["z"])

    # choose tile dimensions: split the longer axis as finely as needed; if a
    # full strip of the long axis (long_step=1) still busts cap, split the short
    # axis too so short_dim * 1 <= cap.
    if width >= length:
        # long axis = X (width). keep length whole if it fits, else tile it.
        z_step = length if length <= cap else max(1, cap)
        x_step = max(1, cap // z_step)
    else:
        # long axis = Z (length). keep width whole if it fits, else tile it.
        x_step = width if width <= cap else max(1, cap)
        z_step = max(1, cap // x_step)

    tiles = []
    for xi in range(0, width, x_step):
        x1 = min(xi + x_step, width)
        for zi in range(0, length, z_step):
            z1 = min(zi + z_step, length)
            tw = x1 - xi
            tl = z1 - zi
            tile = dict(plan)
            tile["origin"] = {"x": ox + xi, "z": oz + zi}
            tile["width"] = tw
            tile["length"] = tl
            tile["height"] = h2[xi:x1, zi:z1].reshape(-1).tolist()
            tile["surface"] = s2[xi:x1, zi:z1].reshape(-1).tolist()
            tile["subsurface"] = sub2[xi:x1, zi:z1].reshape(-1).tolist()
            tiles.append(tile)
    return tiles


def write_columns_plan(hf, path: str, spec: "MaterialSpec", *, origin=(0, 0),
                       floor_below: int = 6, dimension: str = "minecraft:overworld") -> dict:
    """Write a ``to_columns_plan`` dict to JSON; return a small summary."""
    import json
    plan = to_columns_plan(hf, spec, origin=origin, floor_below=floor_below,
                           dimension=dimension)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh)
    return {
        "columns": plan["width"] * plan["length"],
        "palette_size": len(plan["palette"]),
        "floor_y": plan["floor_y"],
        "sea_level": plan["sea_level"],
        "has_strata": "strata" in plan,
        "bbox": {"from": [plan["origin"]["x"], plan["floor_y"], plan["origin"]["z"]],
                 "to": [plan["origin"]["x"] + plan["width"] - 1,
                        int(max(plan["height"])), plan["origin"]["z"] + plan["length"] - 1]},
    }
