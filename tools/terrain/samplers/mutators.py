"""Mutator nodes — unary transforms that wrap one child sampler."""
from __future__ import annotations

import numpy as np

from .base import Sampler, EvalContext, register, from_spec


class _Unary(Sampler):
    def __init__(self, src, **kw):
        self.src = from_spec(src)
        for k, v in kw.items():
            setattr(self, k, v)

    def to_spec(self) -> dict:
        spec = {"type": self.TYPE, "src": self.src.to_spec()}
        for k, v in vars(self).items():
            if k != "src" and not k.startswith("_"):
                spec[k] = v
        return spec


@register
class Scale(_Unary):
    TYPE = "Scale"

    def __init__(self, src, factor: float = 1.0):
        super().__init__(src, factor=float(factor))

    def eval(self, ctx):
        return self.src.eval(ctx) * self.factor


@register
class Bias(_Unary):
    TYPE = "Bias"

    def __init__(self, src, offset: float = 0.0):
        super().__init__(src, offset=float(offset))

    def eval(self, ctx):
        return self.src.eval(ctx) + self.offset


@register
class Clamp(_Unary):
    TYPE = "Clamp"

    def __init__(self, src, lo: float = 0.0, hi: float = 1.0):
        super().__init__(src, lo=float(lo), hi=float(hi))

    def eval(self, ctx):
        return np.clip(self.src.eval(ctx), self.lo, self.hi)


@register
class Linear(_Unary):
    """Remap from ``[in_lo, in_hi]`` to ``[out_lo, out_hi]`` (affine)."""

    TYPE = "Linear"

    def __init__(self, src, in_lo: float = -1.0, in_hi: float = 1.0,
                 out_lo: float = 0.0, out_hi: float = 1.0):
        super().__init__(src, in_lo=float(in_lo), in_hi=float(in_hi),
                         out_lo=float(out_lo), out_hi=float(out_hi))

    def eval(self, ctx):
        v = self.src.eval(ctx)
        t = (v - self.in_lo) / max(self.in_hi - self.in_lo, 1e-9)
        return self.out_lo + t * (self.out_hi - self.out_lo)


@register
class CubicSpline(_Unary):
    """Map the child value through a piecewise spline given control points
    ``[[x0,y0], [x1,y1], ...]`` (sorted by x). This is the Minecraft-1.18
    continentalness/erosion remap: control what fraction of the map is
    ocean / lowland / highland by shaping the transfer curve. Monotone-safe
    (uses numpy.interp; extrapolation clamps to the endpoints)."""

    TYPE = "CubicSpline"

    def __init__(self, src, points=None):
        pts = points or [[-1.0, 0.0], [1.0, 1.0]]
        super().__init__(src, points=[[float(a), float(b)] for a, b in pts])

    def eval(self, ctx):
        v = self.src.eval(ctx)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return np.interp(v, xs, ys)


@register
class Posterize(_Unary):
    """Quantise to ``steps`` levels (terraces / strata bands when used on Y)."""

    TYPE = "Posterize"

    def __init__(self, src, steps: int = 6):
        super().__init__(src, steps=int(steps))

    def eval(self, ctx):
        v = self.src.eval(ctx)
        return np.round(v * self.steps) / max(self.steps, 1)


@register
class Terrace(_Unary):
    """Step-quantise with a slope-preserving ramp fraction and optional mask —
    geological ledges that vary in width (not a cookie-cutter staircase).
    ``smoothing`` 0 = hard steps, 1 = original; applied only where ``mask`` (a
    child sampler) is > 0 if given."""

    TYPE = "Terrace"

    def __init__(self, src, steps: int = 5, smoothing: float = 0.3, mask=None):
        super().__init__(src, steps=int(steps), smoothing=float(smoothing))
        self.mask = from_spec(mask) if mask is not None else None

    def eval(self, ctx):
        v = self.src.eval(ctx)
        vmin, vmax = float(v.min()), float(v.max())
        span = max(vmax - vmin, 1e-9)
        norm = (v - vmin) / span
        stepped = np.round(norm * self.steps) / max(self.steps, 1)
        out = stepped * (1 - self.smoothing) + norm * self.smoothing
        result = vmin + out * span
        if self.mask is not None:
            m = self.mask.eval(ctx) > 0
            result = np.where(m, result, v)
        return result

    def to_spec(self) -> dict:
        spec = {"type": self.TYPE, "src": self.src.to_spec(),
                "steps": self.steps, "smoothing": self.smoothing}
        if self.mask is not None:
            spec["mask"] = self.mask.to_spec()
        return spec


@register
class KernelSlope(_Unary):
    """Gradient-magnitude of the child field, evaluated in-graph — the slope of
    the *recipe surface* itself (degrees if ``degrees=True``, else raw rise/run
    per cell). Drives a ``Select``/``Blend`` selector so steep-vs-flat material
    or shape choices live in the recipe (the graph twin of ``masks.slope_deg``).
    ``cell`` is the horizontal block size per grid step."""

    TYPE = "KernelSlope"

    def __init__(self, src, cell: float = 1.0, degrees: bool = True):
        super().__init__(src, cell=float(cell), degrees=bool(degrees))

    def eval(self, ctx):
        v = self.src.eval(ctx)
        gx, gz = np.gradient(v, self.cell)
        mag = np.hypot(gx, gz)
        return np.degrees(np.arctan(mag)) if self.degrees else mag
