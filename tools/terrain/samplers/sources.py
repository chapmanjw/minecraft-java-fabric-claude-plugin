"""Source nodes — leaves of the graph that generate a raw coherent field."""
from __future__ import annotations

import numpy as np

from .base import Sampler, EvalContext, register
from ._backend import noise2, noise2_basis


class _BasisSource(Sampler):
    """Common base for single-octave coherent-noise sources that name a basis.

    Accepts ``freq`` (the Design recipe spelling) or ``frequency`` (the legacy
    spelling) interchangeably, plus ``seed``. ``BASIS`` selects the backend
    function so a recipe can pin ``OpenSimplex2S`` / ``Perlin`` / ``Value``
    explicitly regardless of the process-wide default backend. Output ~[-1, 1].
    """

    BASIS = None  # None → current process backend

    def __init__(self, freq: float = None, seed: int = 0, frequency: float = None):
        if freq is None:
            freq = 0.01 if frequency is None else frequency
        self.freq = float(freq)
        self.seed = int(seed)

    @property
    def frequency(self) -> float:           # legacy alias
        return self.freq

    def eval(self, ctx: EvalContext) -> np.ndarray:
        f = self.freq
        return noise2_basis(self.BASIS, ctx.seed + self.seed, ctx.X * f, ctx.Z * f)

    def to_spec(self) -> dict:
        return {"type": self.TYPE, "freq": self.freq, "seed": self.seed}


@register
class Constant(Sampler):
    TYPE = "Constant"

    def __init__(self, value: float = 0.0):
        self.value = float(value)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        return np.full(ctx.shape, self.value, dtype=float)


@register
class Noise(_BasisSource):
    """Single-octave coherent noise at ``frequency`` (cycles per cell). Output
    ~[-1, 1]. The basis is the backend's (Perlin by default)."""

    TYPE = "Noise"
    BASIS = None

    def to_spec(self) -> dict:
        return {"type": self.TYPE, "frequency": self.freq, "seed": self.seed}


@register
class Perlin(_BasisSource):
    """Perlin gradient noise basis, single octave (``freq``, ``seed``)."""

    TYPE = "Perlin"
    BASIS = "perlin"


@register
class Value(_BasisSource):
    """Value noise basis, single octave (``freq``, ``seed``)."""

    TYPE = "Value"
    BASIS = "value"


@register
class OpenSimplex2S(_BasisSource):
    """OpenSimplex2S basis (Design Pillar 4). Uses the ``opensimplex`` package
    when installed and selected; otherwise falls back to the vectorised Perlin
    backend so a recipe naming ``OpenSimplex2S`` still loads and evaluates with
    nothing beyond numpy."""

    TYPE = "OpenSimplex2S"
    BASIS = "opensimplex"


@register
class WhiteNoise(Sampler):
    """Per-cell uniform white noise in ~[-1, 1] (no spatial coherence). A dither
    / jitter source — seed-deterministic per grid cell via an integer hash of
    the cell coordinate, so it is stable under translation of the eval window."""

    TYPE = "WhiteNoise"

    def __init__(self, seed: int = 0):
        self.seed = int(seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        xi = np.floor(ctx.X).astype(np.int64)
        zi = np.floor(ctx.Z).astype(np.int64)
        s = (ctx.seed + self.seed) & 0xFFFFFFFF
        h = (xi * 374761393 + zi * 668265263 + s * 2147483647) & 0xFFFFFFFF
        h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
        return (h.astype(np.float64) / 0xFFFFFFFF) * 2.0 - 1.0


@register
class Cellular(Sampler):
    """Worley / cellular noise. ``ret`` selects the feature:
      ``F1`` smooth basins · ``F2`` wider cells · ``F2F1`` ridge walls ·
      ``inv_F1`` (1-F1) spires (hoodoos, karst towers).
    ``frequency`` sets cell size; ``jitter`` 0..1 randomises feature points."""

    TYPE = "Cellular"

    def __init__(self, frequency: float = 0.02, ret: str = "F1",
                 jitter: float = 1.0, seed: int = 0):
        self.frequency = float(frequency)
        self.ret = str(ret)
        self.jitter = float(jitter)
        self.seed = int(seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        f = self.frequency
        x = ctx.X * f
        z = ctx.Z * f
        xi = np.floor(x).astype(np.int64)
        zi = np.floor(z).astype(np.int64)
        rng = np.random.default_rng((ctx.seed + self.seed) & 0x7FFFFFFF)
        # hash-based per-cell feature offsets, computed for the 3x3 neighbourhood
        f1 = np.full(x.shape, np.inf)
        f2 = np.full(x.shape, np.inf)
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cx = xi + dx
                cz = zi + dz
                ox, oz = _cell_offset(cx, cz, self.seed)
                fx = cx + ox * self.jitter
                fz = cz + oz * self.jitter
                d = np.hypot(x - fx, z - fz)
                closer = d < f1
                f2 = np.where(closer, f1, np.minimum(f2, d))
                f1 = np.where(closer, d, f1)
        if self.ret == "F1":
            out = f1
        elif self.ret == "F2":
            out = f2
        elif self.ret == "F2F1":
            out = f2 - f1
        elif self.ret == "inv_F1":
            return np.clip(1.0 - f1, -1.0, 1.0)
        else:
            raise ValueError(f"Cellular ret {self.ret!r}")
        # normalise roughly to [-1, 1]
        return np.clip(out * 2.0 - 1.0, -1.0, 1.0)


def _cell_offset(cx: np.ndarray, cz: np.ndarray, seed: int):
    """Deterministic per-integer-cell offset in [0,1) via integer hashing."""
    h = (cx * 374761393 + cz * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    ox = ((h & 0xFFFF) / 65535.0)
    oz = (((h >> 16) & 0xFFFF) / 65535.0)
    return ox, oz
