"""Geometry nodes — coordinate-driven fields: radial falloff, DEM image, belt."""
from __future__ import annotations

from typing import Optional

import numpy as np

from .base import Sampler, EvalContext, register


@register
class Distance(Sampler):
    """Radial falloff in ``[0, 1]``: 1 at ``center``, smoothstepping to 0 past
    ``radius``. ``sx``/``sz`` make it elliptical (irregular islands). Folds the
    old ``radial_falloff`` into the graph; multiply terrain by it for islands,
    or use as a ``Blend`` selector."""

    TYPE = "Distance"

    def __init__(self, center=None, radius: float = 64.0, inner: float = 0.0,
                 sx: float = 1.0, sz: float = 1.0):
        self.center = list(center) if center is not None else None
        self.radius = float(radius)
        self.inner = float(inner)
        self.sx = float(sx)
        self.sz = float(sz)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        nx, nz = ctx.shape
        cx, cz = self.center if self.center else (nx / 2.0, nz / 2.0)
        d = np.hypot((ctx.X - cx) * self.sx, (ctx.Z - cz) * self.sz)
        lo = self.inner * self.radius
        t = np.clip((d - lo) / max(self.radius - lo, 1e-9), 0.0, 1.0)
        t = t * t * (3 - 2 * t)
        return 1.0 - t


@register
class ImageDEM(Sampler):
    """Sample a greyscale heightmap PNG as a field in ``[0, 1]``. 16-bit images
    (mode ``I;16``) are honoured to avoid terracing real-world DEMs; alpha is
    stripped; ``zoom`` resamples to the grid. The DEM import path as a graph
    node (compose with ``Add(Ridged)`` to add procedural detail on a real DEM)."""

    TYPE = "ImageDEM"

    def __init__(self, path: str, zoom: float = 1.0):
        self.path = str(path)
        self.zoom = float(zoom)
        self._cache: Optional[np.ndarray] = None

    def _load(self, shape) -> np.ndarray:
        from PIL import Image
        im = Image.open(self.path)
        if im.mode == "I;16":
            a = np.asarray(im, dtype=np.float64) / 65535.0
        else:
            a = np.asarray(im.convert("L"), dtype=np.float64) / 255.0
        a = a.T  # (rows=z, cols=x) → (x, z)
        nx, nz = shape
        if a.shape != (nx, nz):
            from scipy.ndimage import zoom as ndzoom
            a = ndzoom(a, (nx / a.shape[0], nz / a.shape[1]), order=1)
        return a

    def eval(self, ctx: EvalContext) -> np.ndarray:
        if self._cache is None or self._cache.shape != ctx.shape:
            self._cache = self._load(ctx.shape)
        return self._cache

    def to_spec(self) -> dict:
        return {"type": self.TYPE, "path": self.path, "zoom": self.zoom}


@register
class BeltCoord(Sampler):
    """Expose the belt ``s`` (arc-length) or ``perp`` (signed perpendicular)
    field set on the EvalContext, so a recipe authored along a Centerline can
    drive nodes by position along/across the corridor. Returns zeros if the
    context has no belt coords."""

    TYPE = "BeltCoord"

    def __init__(self, which: str = "perp"):
        self.which = str(which)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        v = ctx.s if self.which == "s" else ctx.perp
        if v is None:
            return np.zeros(ctx.shape)
        return np.asarray(v, dtype=float)
