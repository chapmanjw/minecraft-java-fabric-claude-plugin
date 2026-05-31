"""Terrain analysis masks — Pillar 2 of the redesign.

Per-cell scalar/boolean fields derived from a heightfield, combined with plain
numpy ``& | ~``. These replace hardcoded materialisation rules: "rock on steep
faces, snow above the snowline, moss in hollows, beach near water" becomes one
declarative pass. The same masks drive the scatter pass (where trees may grow).

All functions take a 2-D height array ``h`` (world Y per cell) and return arrays
of the same shape. ``cell`` is the horizontal block size per cell (1 in our use).
"""
from __future__ import annotations

import numpy as np


def slope_deg(h: np.ndarray, cell: float = 1.0) -> np.ndarray:
    """Slope magnitude in degrees (0 flat … 90 vertical)."""
    gx, gz = np.gradient(h, cell)
    return np.degrees(np.arctan(np.hypot(gx, gz)))


def aspect_deg(h: np.ndarray) -> np.ndarray:
    """Compass-style facing direction of the slope, degrees in [0, 360).
    0 = faces +X; increases toward +Z. Use for sun/shade rules (moss on the
    cool side, snow lingering on poleward faces)."""
    gx, gz = np.gradient(h)
    a = np.degrees(np.arctan2(gz, gx))
    return (a + 360.0) % 360.0


def curvature(h: np.ndarray) -> np.ndarray:
    """Discrete Laplacian: negative = concave (valley/hollow, water collects),
    positive = convex (ridge/spur, wind-scoured)."""
    return (np.roll(h, -1, 0) + np.roll(h, 1, 0)
            + np.roll(h, -1, 1) + np.roll(h, 1, 1) - 4.0 * h)


def dist_to_water(h: np.ndarray, sea_level: float, cell: float = 1.0) -> np.ndarray:
    """Euclidean distance (in blocks) from each land cell to the nearest cell at
    or below ``sea_level``. Drives riparian planting and beach bands. Returns 0
    inside water, large values far inland."""
    from scipy.ndimage import distance_transform_edt
    water = h <= sea_level
    if not water.any():
        return np.full(h.shape, np.inf)
    return distance_transform_edt(~water) * cell


# -- boolean masks --------------------------------------------------------
def mask_slope(h: np.ndarray, lo: float = 0.0, hi: float = 90.0,
               cell: float = 1.0) -> np.ndarray:
    s = slope_deg(h, cell)
    return (s >= lo) & (s <= hi)


def mask_y(h: np.ndarray, op: str, y: float) -> np.ndarray:
    if op in (">", "gt", "above"):
        return h > y
    if op in ("<", "lt", "below"):
        return h < y
    if op in (">=", "ge"):
        return h >= y
    if op in ("<=", "le"):
        return h <= y
    raise ValueError(f"mask_y op {op!r}")


def mask_band(h: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return (h >= lo) & (h <= hi)


def mask_curv(h: np.ndarray, lo: float = -np.inf, hi: float = np.inf) -> np.ndarray:
    c = curvature(h)
    return (c >= lo) & (c <= hi)


def mask_near_water(h: np.ndarray, sea_level: float, within: float,
                    cell: float = 1.0) -> np.ndarray:
    return dist_to_water(h, sea_level, cell) <= within


def mask_noise(sampler, ctx, thr: float = 0.0) -> np.ndarray:
    """Boolean mask from a sampler-graph node: ``True`` where the node's field
    is ``>= thr`` (Design Pillar 2). Lets a noise field break up an otherwise
    geometric layer boundary — patchy moss, scattered boulders, a dithered
    snowline — without leaving the declarative mask algebra (combine with the
    slope/height/water masks via plain ``& | ~``).

    ``sampler`` is a ``terrain.samplers.Sampler`` (or a dict/JSON spec, or a bare
    scalar — passed through ``from_spec``); ``ctx`` is the ``EvalContext`` it is
    evaluated over (same grid as the heightfield's masks)."""
    from .samplers import from_spec
    node = from_spec(sampler)
    field = np.asarray(node.eval(ctx), dtype=float)
    return field >= thr
