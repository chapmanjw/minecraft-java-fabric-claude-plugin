"""Coherent value noise on a 2-D lattice — the base layer for terrain
heightfields.

Pure numpy, no native noise dependency. Permutation-hashed value noise that
samples arbitrary float coordinates, so it composes with domain warping and
erosion. ``fbm`` matches the multi-octave value-noise recipe the terraforming
skill prescribes.

For production-grade terrain you can later swap in the optional ``opensimplex``
or ``pyfastnoiselite`` packages to remove value-noise's faint lattice grain —
``fbm`` here is plenty for silhouette + render-verify work, and needs nothing
beyond numpy.
"""
from __future__ import annotations

import numpy as np


class ValueNoise2D:
    """Seeded value noise. ``sample(px, pz)`` takes float arrays and returns a
    coherent field in ``[0, 1]``; arbitrary coordinates are supported so the
    field can be domain-warped or sampled along droplet paths."""

    def __init__(self, seed: int = 0) -> None:
        rng = np.random.default_rng(seed)
        p = rng.permutation(256)
        self._perm = np.concatenate([p, p]).astype(np.int64)   # length 512
        self._val = rng.random(512)                            # lattice values

    def _corner(self, xi, zi):
        h = self._perm[(self._perm[xi & 255] + (zi & 255)) & 511]
        return self._val[h]

    def sample(self, px, pz):
        px = np.asarray(px, dtype=float)
        pz = np.asarray(pz, dtype=float)
        x0 = np.floor(px).astype(np.int64)
        z0 = np.floor(pz).astype(np.int64)
        fx, fz = px - x0, pz - z0
        sx = fx * fx * (3 - 2 * fx)              # smoothstep
        sz = fz * fz * (3 - 2 * fz)
        v00 = self._corner(x0, z0)
        v10 = self._corner(x0 + 1, z0)
        v01 = self._corner(x0, z0 + 1)
        v11 = self._corner(x0 + 1, z0 + 1)
        a = v00 * (1 - sx) + v10 * sx
        b = v01 * (1 - sx) + v11 * sx
        return a * (1 - sz) + b * sz


def fbm(nx: int, nz: int, *, octaves: int = 4, base_freq: float = 0.06,
        lacunarity: float = 2.0, gain: float = 0.5, seed: int = 0,
        ridge: bool = False, warp: float = 0.0) -> np.ndarray:
    """Fractal Brownian motion heightfield on an ``nx × nz`` grid, normalised
    to ``[0, 1]``.

    - ``octaves`` / ``base_freq`` / ``lacunarity`` / ``gain`` — standard fbm
      controls. The defaults follow the terraforming skill's prescription
      (3–4 octaves, summed and normalised).
    - ``ridge=True`` folds each octave to ``1 − |2v − 1|`` for sharp mountain
      ridgelines (combine a low-amplitude ridge field with a smooth base).
    - ``warp`` > 0 applies domain warping (in grid cells) so outlines read
      organic instead of griddy — the cheapest fix for "value-noise look".
    """
    xs = np.arange(nx, dtype=float)[:, None]
    zs = np.arange(nz, dtype=float)[None, :]
    X = np.broadcast_to(xs, (nx, nz)).astype(float)
    Z = np.broadcast_to(zs, (nx, nz)).astype(float)
    if warp > 0:
        wx = ValueNoise2D(seed + 101).sample(X * base_freq, Z * base_freq)
        wz = ValueNoise2D(seed + 202).sample(X * base_freq, Z * base_freq)
        X = X + (wx - 0.5) * 2.0 * warp
        Z = Z + (wz - 0.5) * 2.0 * warp

    total = np.zeros((nx, nz))
    amp, freq, norm = 1.0, base_freq, 0.0
    for o in range(octaves):
        n = ValueNoise2D(seed + o).sample(X * freq, Z * freq)
        if ridge:
            n = 1.0 - np.abs(2.0 * n - 1.0)
        total += amp * n
        norm += amp
        amp *= gain
        freq *= lacunarity

    out = total / max(norm, 1e-9)
    out -= out.min()
    mx = out.max()
    return out / mx if mx > 1e-9 else out
