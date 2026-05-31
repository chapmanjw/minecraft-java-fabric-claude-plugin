"""Domain-warp node — the single biggest 'organic, non-griddy' multiplier.

Samples ``src`` at coordinates displaced by two *independent* warp fields (so
the distortion isn't collapsed onto one axis — the "streaky warp" failure).
``levels=2`` applies the warp recursively for fjord-like folded coastlines.
"""
from __future__ import annotations

import numpy as np

from .base import Sampler, EvalContext, register, from_spec
from ._backend import noise2


@register
class DomainWarp(Sampler):
    TYPE = "DomainWarp"

    def __init__(self, src, amplitude: float = 20.0, frequency: float = 0.01,
                 levels: int = 1, seed: int = 0):
        self.src = from_spec(src)
        self.amplitude = float(amplitude)
        self.frequency = float(frequency)
        self.levels = int(levels)
        self.seed = int(seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        X, Z = ctx.X, ctx.Z
        f = self.frequency
        for lvl in range(self.levels):
            s = ctx.seed + self.seed + lvl * 1000
            wx = noise2(s + 11, X * f, Z * f)
            wz = noise2(s + 53, X * f, Z * f)   # distinct seed → 2-vector warp
            X = X + wx * self.amplitude
            Z = Z + wz * self.amplitude
        warped = EvalContext(X=X, Z=Z, seed=ctx.seed, s=ctx.s, perp=ctx.perp)
        return self.src.eval(warped)

    def to_spec(self) -> dict:
        return {"type": self.TYPE, "src": self.src.to_spec(),
                "amplitude": self.amplitude, "frequency": self.frequency,
                "levels": self.levels, "seed": self.seed}
