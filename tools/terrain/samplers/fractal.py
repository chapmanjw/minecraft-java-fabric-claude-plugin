"""Fractal nodes — layer octaves of a coherent basis into terrain-grade noise.

These evaluate the backend basis directly across octaves (rather than wrapping a
child Noise node) so the octave loop stays a tight vectorised numpy sum. Output
is normalised to ~[-1, 1] (FBM/Billow) or ~[0, 1] (Ridged/Hybrid/Hetero, which
are one-sided by construction).
"""
from __future__ import annotations

import numpy as np

from .base import Sampler, EvalContext, register, from_spec
from ._backend import noise2, noise2_basis


def _octave_coords(ctx: EvalContext, freq: float):
    return ctx.X * freq, ctx.Z * freq


def _resolve_basis(src, frequency, seed):
    """A fractal node may be authored two ways:

      - the *legacy* flat form ``{"type":"FBM","frequency":0.05,"octaves":5}``;
      - the *Design recipe* form that nests a basis source,
        ``{"type":"FBM","octaves":4,"src":{"type":"OpenSimplex2S","freq":..,"seed":..}}``.

    Both resolve to ``(basis, base_freq, base_seed)`` here so the octave loop is
    one tight vectorised numpy sum either way. When ``src`` is given, its
    ``freq``/``frequency``, ``seed`` and (for named bases) backend are read off
    the child; otherwise the node's own ``frequency``/``seed`` are used over the
    process default backend (``basis=None``)."""
    if src is None:
        return None, float(frequency), int(seed)
    node = from_spec(src)
    basis = getattr(node, "BASIS", None)
    base_freq = float(getattr(node, "freq", getattr(node, "frequency", frequency)))
    base_seed = int(getattr(node, "seed", seed))
    return basis, base_freq, base_seed


@register
class FBM(Sampler):
    """Fractional Brownian motion: ``octaves`` of the basis, each at
    ``lacunarity``× frequency and ``gain``× amplitude. The general-purpose
    rolling-terrain layer. Output ~[-1, 1]."""

    TYPE = "FBM"

    def __init__(self, frequency: float = 0.01, octaves: int = 5,
                 lacunarity: float = 2.0, gain: float = 0.5, seed: int = 0,
                 src=None):
        self.frequency = float(frequency)
        self.octaves = int(octaves)
        self.lacunarity = float(lacunarity)
        self.gain = float(gain)
        self.seed = int(seed)
        self._src = src
        self._basis, self._freq0, self._seed0 = _resolve_basis(src, frequency, seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        total = np.zeros(ctx.shape)
        amp, freq, norm = 1.0, self._freq0, 0.0
        for o in range(self.octaves):
            x, z = _octave_coords(ctx, freq)
            total += amp * noise2_basis(self._basis, ctx.seed + self._seed0 + o, x, z)
            norm += amp
            amp *= self.gain
            freq *= self.lacunarity
        return total / max(norm, 1e-9)

    def to_spec(self) -> dict:
        spec = {"type": self.TYPE, "octaves": self.octaves,
                "lacunarity": self.lacunarity, "gain": self.gain}
        if self._src is not None:
            spec["src"] = from_spec(self._src).to_spec()
        else:
            spec["frequency"] = self.frequency
            spec["seed"] = self.seed
        return spec


@register
class Ridged(Sampler):
    """Ridged multifractal (Musgrave) with the spectral-weight gain-feedback
    loop — sharp mountain ridgelines that read as geologically correct. This is
    the real algorithm, not the ``1-|2n-1|`` value-noise stub. Output ~[0, 1]."""

    TYPE = "Ridged"

    def __init__(self, frequency: float = 0.01, octaves: int = 6,
                 lacunarity: float = 2.0, gain: float = 2.0, offset: float = 1.0,
                 h: float = 1.0, seed: int = 0, src=None):
        self.frequency = float(frequency)
        self.octaves = int(octaves)
        self.lacunarity = float(lacunarity)
        self.gain = float(gain)
        self.offset = float(offset)
        self.h = float(h)
        self.seed = int(seed)
        self._src = src
        self._basis, self._freq0, self._seed0 = _resolve_basis(src, frequency, seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        freq = self._freq0
        s0 = self._seed0
        weights = [self.lacunarity ** (-i * self.h) for i in range(self.octaves)]
        x, z = _octave_coords(ctx, freq)
        signal = self.offset - np.abs(noise2_basis(self._basis, ctx.seed + s0, x, z))
        signal *= signal
        result = signal * weights[0]
        weight = signal * self.gain
        for o in range(1, self.octaves):
            freq *= self.lacunarity
            np.clip(weight, 0.0, 1.0, out=weight)
            x, z = _octave_coords(ctx, freq)
            sig = self.offset - np.abs(noise2_basis(self._basis, ctx.seed + s0 + o, x, z))
            sig *= sig
            sig *= weight
            result += sig * weights[o]
            weight = sig * self.gain
        # normalise to ~[0,1] by the summed weights
        return result / max(sum(weights), 1e-9)

    def to_spec(self) -> dict:
        spec = {"type": self.TYPE, "octaves": self.octaves,
                "lacunarity": self.lacunarity, "gain": self.gain,
                "offset": self.offset, "h": self.h}
        if self._src is not None:
            spec["src"] = from_spec(self._src).to_spec()
        else:
            spec["frequency"] = self.frequency
            spec["seed"] = self.seed
        return spec


@register
class Billow(Sampler):
    """Billow noise — rounded lumps (the inverse character of Ridged). Good for
    foothills, dunes, rolling meadows. Output ~[-1, 1]."""

    TYPE = "Billow"

    def __init__(self, frequency: float = 0.01, octaves: int = 5,
                 lacunarity: float = 2.0, gain: float = 0.5, seed: int = 0,
                 src=None):
        self.frequency = float(frequency)
        self.octaves = int(octaves)
        self.lacunarity = float(lacunarity)
        self.gain = float(gain)
        self.seed = int(seed)
        self._src = src
        self._basis, self._freq0, self._seed0 = _resolve_basis(src, frequency, seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        total = np.zeros(ctx.shape)
        amp, freq, norm = 1.0, self._freq0, 0.0
        for o in range(self.octaves):
            x, z = _octave_coords(ctx, freq)
            n = np.abs(noise2_basis(self._basis, ctx.seed + self._seed0 + o, x, z))
            total += amp * (2.0 * n - 1.0)
            norm += amp
            amp *= self.gain
            freq *= self.lacunarity
        return total / max(norm, 1e-9)

    def to_spec(self) -> dict:
        spec = {"type": self.TYPE, "octaves": self.octaves,
                "lacunarity": self.lacunarity, "gain": self.gain}
        if self._src is not None:
            spec["src"] = from_spec(self._src).to_spec()
        else:
            spec["frequency"] = self.frequency
            spec["seed"] = self.seed
        return spec


@register
class Hybrid(Sampler):
    """Hybrid multifractal — altitude-dependent roughness: smooth lowlands,
    progressively rougher highlands, for free (no manual slope mask). Output
    ~[0, 1+]."""

    TYPE = "Hybrid"

    def __init__(self, frequency: float = 0.01, octaves: int = 6,
                 lacunarity: float = 2.0, h: float = 0.25, offset: float = 0.7,
                 seed: int = 0, src=None):
        self.frequency = float(frequency)
        self.octaves = int(octaves)
        self.lacunarity = float(lacunarity)
        self.h = float(h)
        self.offset = float(offset)
        self.seed = int(seed)
        self._src = src
        self._basis, self._freq0, self._seed0 = _resolve_basis(src, frequency, seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        freq = self._freq0
        s0 = self._seed0
        weights = [self.lacunarity ** (-i * self.h) for i in range(self.octaves)]
        x, z = _octave_coords(ctx, freq)
        result = (noise2_basis(self._basis, ctx.seed + s0, x, z) + self.offset) * weights[0]
        weight = result.copy()
        for o in range(1, self.octaves):
            freq *= self.lacunarity
            np.clip(weight, 0.0, 1.0, out=weight)
            x, z = _octave_coords(ctx, freq)
            sig = (noise2_basis(self._basis, ctx.seed + s0 + o, x, z) + self.offset) * weights[o]
            result += weight * sig
            weight = weight * sig
        return result / max(sum(weights), 1e-9)

    def to_spec(self) -> dict:
        spec = {"type": self.TYPE, "octaves": self.octaves,
                "lacunarity": self.lacunarity, "h": self.h, "offset": self.offset}
        if self._src is not None:
            spec["src"] = from_spec(self._src).to_spec()
        else:
            spec["frequency"] = self.frequency
            spec["seed"] = self.seed
        return spec


@register
class Hetero(Sampler):
    """Heterogeneous multifractal (Musgrave) — like Hybrid but the roughness
    feedback multiplies the *running sum* rather than the previous octave, so
    detail accretes faster in already-high areas: smooth plains, increasingly
    rugged highlands. Output ~[0, 1+]. Accepts the same legacy/``src`` forms as
    the other fractals."""

    TYPE = "Hetero"

    def __init__(self, frequency: float = 0.01, octaves: int = 6,
                 lacunarity: float = 2.0, h: float = 0.25, offset: float = 0.7,
                 seed: int = 0, src=None):
        self.frequency = float(frequency)
        self.octaves = int(octaves)
        self.lacunarity = float(lacunarity)
        self.h = float(h)
        self.offset = float(offset)
        self.seed = int(seed)
        self._src = src
        self._basis, self._freq0, self._seed0 = _resolve_basis(src, frequency, seed)

    def eval(self, ctx: EvalContext) -> np.ndarray:
        freq = self._freq0
        s0 = self._seed0
        weights = [self.lacunarity ** (-i * self.h) for i in range(self.octaves)]
        x, z = _octave_coords(ctx, freq)
        result = (noise2_basis(self._basis, ctx.seed + s0, x, z) + self.offset) * weights[0]
        for o in range(1, self.octaves):
            freq *= self.lacunarity
            x, z = _octave_coords(ctx, freq)
            sig = (noise2_basis(self._basis, ctx.seed + s0 + o, x, z) + self.offset) * weights[o]
            # running-sum feedback: rough where already high
            result = result + np.clip(result, 0.0, 1.0) * sig
        return result / max(sum(weights), 1e-9)

    def to_spec(self) -> dict:
        spec = {"type": self.TYPE, "octaves": self.octaves,
                "lacunarity": self.lacunarity, "h": self.h, "offset": self.offset}
        if self._src is not None:
            spec["src"] = from_spec(self._src).to_spec()
        else:
            spec["frequency"] = self.frequency
            spec["seed"] = self.seed
        return spec
