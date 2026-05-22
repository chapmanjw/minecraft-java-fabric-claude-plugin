"""Render a :class:`~voxel.model.VoxelModel` to PNGs so the agent can *see* the
form and judge it against references — the single most valuable habit for any
representational build. The agent cannot see the world; a renderer is cheaper
than one wrong in-world rebuild.

Always render multiple orthogonal views — different errors surface in different
views. A wrong **silhouette** shows in the side/front ortho; the **isometric**
3/4 view shows how masses read in three dimensions.

- ``render_iso`` — isometric 3/4 view, painter's algorithm, top/left/right
  face shading. Surface voxels only.
- ``render_ortho`` — flat orthographic side / front / top; each pixel is the
  outermost visible voxel along the flattened axis, coloured by its block.
- ``render_views`` — writes ``<prefix>_iso.png``, ``_side.png``, ``_front.png``
  in one call. This is what you normally call.

The same functions verify a *built* result: scan the placed blocks back into a
grid and render that ("scan-render"), then compare to the references. A visual
inspector pass is far stronger than spot-checking a handful of coordinates.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

from .model import VoxelModel

_BG = (200, 214, 228)
_MISSING = (160, 160, 160)


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _surface_mask(g: np.ndarray) -> np.ndarray:
    """Solid voxels that have at least one air neighbour (6-neighbourhood)."""
    solid = g != 0
    air = ~solid
    exposed = np.zeros_like(solid)
    nx, ny, nz = g.shape
    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        shifted = np.ones_like(solid)  # treat out-of-bounds as air → border is surface
        xs = slice(max(0, dx), nx + min(0, dx))
        xd = slice(max(0, -dx), nx + min(0, -dx))
        ys = slice(max(0, dy), ny + min(0, dy))
        yd = slice(max(0, -dy), ny + min(0, -dy))
        zs = slice(max(0, dz), nz + min(0, dz))
        zd = slice(max(0, -dz), nz + min(0, -dz))
        shifted[xd, yd, zd] = air[xs, ys, zs]
        exposed |= solid & shifted
    return exposed


def render_iso(model: VoxelModel, out: str, a: int = 3, vh: int = 3,
               flipz: bool = True, flipx: bool = False, label: str = "") -> str:
    """Isometric 3/4 render. ``a`` is half the tile width, ``vh`` the vertical
    rise per y-level. ``flipz``/``flipx`` spin the view to expose a chosen face."""
    g = model.g
    nx, ny, nz = g.shape
    surf = _surface_mask(g)
    pts = np.argwhere(surf)
    if len(pts) == 0:
        Image.new("RGB", (16, 16), _BG).save(out)
        return out
    th = max(1, a // 2)

    def proj(x, y, z):
        zz = (nz - 1 - z) if flipz else z
        xx = (nx - 1 - x) if flipx else x
        return (xx - zz) * a, (xx + zz) * th - y * vh

    SX, SY = [], []
    for x, y, z in pts:
        sx, sy = proj(x, y, z)
        SX += [sx - a, sx + a]
        SY += [sy - vh, sy + th]
    minx, maxx, miny, maxy = min(SX), max(SX), min(SY), max(SY)
    W, H = maxx - minx + 8, maxy - miny + 8
    img = Image.new("RGB", (W, H), _BG)
    d = ImageDraw.Draw(img)
    ox, oy = -minx + 4, -miny + 4

    def depth(p):
        x, y, z = p
        zz = (nz - 1 - z) if flipz else z
        xx = (nx - 1 - x) if flipx else x
        return (xx + zz) * 2 - y

    for i in sorted(range(len(pts)), key=lambda i: depth(pts[i])):
        x, y, z = pts[i]
        c = model.pal.rgb(int(g[x, y, z])) or _MISSING
        sx, sy = proj(x, y, z)
        sx += ox
        sy += oy
        top = [(sx, sy - vh), (sx + a, sy - vh + th), (sx, sy - vh + 2 * th), (sx - a, sy - vh + th)]
        left = [(sx - a, sy - vh + th), (sx, sy - vh + 2 * th), (sx, sy + 2 * th), (sx - a, sy + th)]
        right = [(sx, sy - vh + 2 * th), (sx + a, sy - vh + th), (sx + a, sy + th), (sx, sy + 2 * th)]
        d.polygon(left, fill=_shade(c, 0.66))
        d.polygon(right, fill=_shade(c, 0.50))
        d.polygon(top, fill=_shade(c, 1.0))
    img.save(out)
    return out


def _outermost_codes(g: np.ndarray, flat_axis: int) -> np.ndarray:
    """For each cell of the two non-flattened axes, the code of the outermost
    solid voxel along ``flat_axis`` (viewer on the + side; 0 where none)."""
    solid = g != 0
    n = g.shape[flat_axis]
    shape = [1, 1, 1]
    shape[flat_axis] = n
    idxarr = np.where(solid, np.arange(n).reshape(shape), -1)
    best = idxarr.max(axis=flat_axis)                 # outermost index, -1 if empty
    pick = np.clip(best, 0, None)
    codes = np.take_along_axis(g, np.expand_dims(pick, flat_axis), axis=flat_axis).squeeze(flat_axis)
    return np.where(best < 0, 0, codes)


def render_ortho(model: VoxelModel, out: str, axis: str = "side", px: int = 4) -> str:
    """Flat orthographic projection. ``axis``:

    - ``side``  — flatten Z; image is length (x) × height (y).
    - ``front`` — flatten X; image is width  (z) × height (y).
    - ``top``   — flatten Y; image is length (x) × width  (z).

    Each pixel is the outermost visible voxel along the flattened axis,
    coloured by its block — so wheels read black, glass reads blue, etc.,
    rather than a flat monochrome silhouette."""
    g = model.g
    nx, ny, nz = g.shape
    axis = axis.lower()

    if axis == "side":          # flatten z → codes indexed [x, y]
        codes = _outermost_codes(g, 2)
        cols, rows, flip_v = nx, ny, True
        def code_at(c, r): return codes[c, r]
    elif axis == "front":       # flatten x → codes indexed [y, z]
        codes = _outermost_codes(g, 0)
        cols, rows, flip_v = nz, ny, True
        def code_at(c, r): return codes[r, c]
    elif axis == "top":         # flatten y (topmost) → codes indexed [x, z]
        codes = _outermost_codes(g, 1)
        cols, rows, flip_v = nx, nz, False
        def code_at(c, r): return codes[c, r]
    else:
        raise ValueError(f"unknown axis {axis!r}")

    img = Image.new("RGB", (cols * px, rows * px), _BG)
    draw = ImageDraw.Draw(img)
    for c in range(cols):
        for r in range(rows):
            code = int(code_at(c, r))
            if code == 0:
                continue
            rgb = model.pal.rgb(code) or _MISSING
            rr = (rows - 1 - r) if flip_v else r      # +y reads upward
            draw.rectangle([c * px, rr * px, c * px + px - 1, rr * px + px - 1], fill=rgb)
    img.save(out)
    return out


def render_views(model: VoxelModel, prefix: str, iso_a: int = 3, iso_vh: int = 3,
                 ortho_px: int = 4) -> list[str]:
    """Write the three standard views and return their paths."""
    return [
        render_iso(model, f"{prefix}_iso.png", a=iso_a, vh=iso_vh),
        render_ortho(model, f"{prefix}_side.png", axis="side", px=ortho_px),
        render_ortho(model, f"{prefix}_front.png", axis="front", px=ortho_px),
    ]
