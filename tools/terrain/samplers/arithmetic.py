"""Arithmetic / selector nodes — combine two (or more) child samplers."""
from __future__ import annotations

import numpy as np

from .base import Sampler, EvalContext, register, from_spec


class _Binary(Sampler):
    def __init__(self, a=None, b=None, left=None, right=None):
        # ``left``/``right`` are the Design-recipe spelling of ``a``/``b``.
        a = a if a is not None else left
        b = b if b is not None else right
        if a is None or b is None:
            raise ValueError(f"{self.TYPE} needs two operands (a/b or left/right)")
        self.a = from_spec(a)
        self.b = from_spec(b)

    def to_spec(self) -> dict:
        return {"type": self.TYPE, "a": self.a.to_spec(), "b": self.b.to_spec()}


@register
class Add(_Binary):
    TYPE = "Add"

    def eval(self, ctx):
        return self.a.eval(ctx) + self.b.eval(ctx)


@register
class Sub(_Binary):
    TYPE = "Sub"

    def eval(self, ctx):
        return self.a.eval(ctx) - self.b.eval(ctx)


@register
class Mul(_Binary):
    TYPE = "Mul"

    def eval(self, ctx):
        return self.a.eval(ctx) * self.b.eval(ctx)


@register
class Div(_Binary):
    TYPE = "Div"

    def eval(self, ctx):
        return self.a.eval(ctx) / (self.b.eval(ctx) + 1e-9)


@register
class Min(_Binary):
    TYPE = "Min"

    def eval(self, ctx):
        return np.minimum(self.a.eval(ctx), self.b.eval(ctx))


@register
class Max(_Binary):
    TYPE = "Max"

    def eval(self, ctx):
        # Max(base, ridged) = mountains rising out of plains
        return np.maximum(self.a.eval(ctx), self.b.eval(ctx))


@register
class Blend(Sampler):
    """Lerp between ``a`` and ``b`` by a ``selector`` field, smoothstepped over
    a window of width ``rng`` centred on ``mid`` — the TerraForged terrain-type
    cross-fade. ``selector`` is read in its native range; pick ``mid``/``rng``
    to suit (e.g. selector in [-1,1], mid 0, rng 0.6)."""

    TYPE = "Blend"

    def __init__(self, a, b, selector, mid: float = 0.0, rng: float = 0.5):
        self.a = from_spec(a)
        self.b = from_spec(b)
        self.selector = from_spec(selector)
        self.mid = float(mid)
        self.rng = float(rng)

    def eval(self, ctx):
        s = self.selector.eval(ctx)
        lo = self.mid - self.rng / 2.0
        t = np.clip((s - lo) / max(self.rng, 1e-9), 0.0, 1.0)
        t = t * t * (3 - 2 * t)
        return self.a.eval(ctx) * (1 - t) + self.b.eval(ctx) * t

    def to_spec(self) -> dict:
        return {"type": self.TYPE, "a": self.a.to_spec(), "b": self.b.to_spec(),
                "selector": self.selector.to_spec(), "mid": self.mid, "rng": self.rng}


@register
class Select(Sampler):
    """Hard threshold gate: pick ``a`` where ``selector >= thr``, else ``b``
    (the libnoise/Terra ``Select`` with a zero-width edge). An optional
    ``falloff`` smoothsteps the boundary over ``±falloff`` of the selector value
    so the switch is not a vertical wall — set ``falloff=0`` for a crisp cut
    (e.g. land/sea by continentalness). ``a``/``b`` accept ``high``/``low``
    aliases too."""

    TYPE = "Select"

    def __init__(self, selector, a=None, b=None, thr: float = 0.0,
                 falloff: float = 0.0, high=None, low=None):
        a = a if a is not None else high
        b = b if b is not None else low
        if a is None or b is None:
            raise ValueError("Select needs a/b (or high/low) operands")
        self.selector = from_spec(selector)
        self.a = from_spec(a)
        self.b = from_spec(b)
        self.thr = float(thr)
        self.falloff = float(falloff)

    def eval(self, ctx):
        s = self.selector.eval(ctx)
        a = self.a.eval(ctx)
        b = self.b.eval(ctx)
        if self.falloff <= 0:
            return np.where(s >= self.thr, a, b)
        t = np.clip((s - (self.thr - self.falloff)) / (2.0 * self.falloff), 0.0, 1.0)
        t = t * t * (3 - 2 * t)
        return b * (1 - t) + a * t

    def to_spec(self) -> dict:
        return {"type": self.TYPE, "selector": self.selector.to_spec(),
                "a": self.a.to_spec(), "b": self.b.to_spec(),
                "thr": self.thr, "falloff": self.falloff}
