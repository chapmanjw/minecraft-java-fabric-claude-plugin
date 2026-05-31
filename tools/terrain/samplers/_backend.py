"""Noise backend for the sampler graph.

The default basis is a **fully-vectorised Perlin gradient noise** implemented in
numpy here — it removes the faint blobby lattice character of plain value noise
(a real quality improvement) while staying fast on large grids and needing
nothing beyond numpy. Domain warping on top (see ``warp.py``) gives the organic,
non-griddy look the research calls for.

``opensimplex`` is supported as an *optional* higher-isotropy backend but is not
the default: its Python binding evaluates one cell at a time, which is too slow
for interactive 256²–1024² authoring. Select it explicitly with
``set_backend("opensimplex")`` if you want it and have installed the package.
"""
from __future__ import annotations

import numpy as np

_BACKEND = "perlin"

try:  # optional
    from opensimplex import OpenSimplex  # type: ignore
    HAVE_OPENSIMPLEX = True
except Exception:  # pragma: no cover
    HAVE_OPENSIMPLEX = False


def set_backend(name: str) -> None:
    global _BACKEND
    if name not in ("perlin", "value", "opensimplex"):
        raise ValueError(f"unknown backend {name!r}")
    if name == "opensimplex" and not HAVE_OPENSIMPLEX:
        raise RuntimeError("opensimplex not installed; pip install opensimplex")
    _BACKEND = name


def get_backend() -> str:
    return _BACKEND


# -- vectorised Perlin gradient noise -------------------------------------
# Classic Ken Perlin gradient noise, evaluated over arbitrary float coordinate
# arrays (so domain warping and droplet sampling compose). Output ~[-1, 1].

_GRAD3 = np.array(
    [[1, 1], [-1, 1], [1, -1], [-1, -1], [1, 0], [-1, 0], [0, 1], [0, -1]],
    dtype=float,
)


def _perm(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    p = rng.permutation(256).astype(np.int64)
    return np.concatenate([p, p])


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _perlin(seed: int, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    perm = _perm(seed)
    xi = np.floor(X).astype(np.int64)
    yi = np.floor(Y).astype(np.int64)
    xf = X - xi
    yf = Y - yi
    xi0 = xi & 255
    yi0 = yi & 255
    xi1 = (xi + 1) & 255
    yi1 = (yi + 1) & 255

    def grad(ix, iy, dx, dy):
        g = perm[(perm[ix] + iy) & 511] & 7
        gx = _GRAD3[g, 0]
        gy = _GRAD3[g, 1]
        return gx * dx + gy * dy

    n00 = grad(xi0, yi0, xf, yf)
    n10 = grad(xi1, yi0, xf - 1, yf)
    n01 = grad(xi0, yi1, xf, yf - 1)
    n11 = grad(xi1, yi1, xf - 1, yf - 1)
    u = _fade(xf)
    v = _fade(yf)
    nx0 = n00 * (1 - u) + n10 * u
    nx1 = n01 * (1 - u) + n11 * u
    out = nx0 * (1 - v) + nx1 * v
    # Perlin 2D range is ~[-0.707, 0.707]; normalise toward [-1, 1].
    return out * 1.4142135623730951


def _value(seed: int, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    from ..noise import ValueNoise2D
    return ValueNoise2D(seed).sample(X, Y) * 2.0 - 1.0


_OS_CACHE: dict = {}


def _opensimplex(seed: int, X: np.ndarray, Y: np.ndarray) -> np.ndarray:  # pragma: no cover
    gen = OpenSimplex(seed=int(seed) & 0x7FFFFFFF)
    fn = _OS_CACHE.get(seed)
    if fn is None:
        fn = np.frompyfunc(gen.noise2, 2, 1)
        _OS_CACHE[seed] = fn
    flat = fn(np.ravel(X), np.ravel(Y)).astype(np.float64)
    return flat.reshape(X.shape)


def noise2(seed: int, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Coherent noise in ~``[-1, 1]`` over coordinate arrays, current backend."""
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    if _BACKEND == "perlin":
        return _perlin(seed, X, Y)
    if _BACKEND == "value":
        return _value(seed, X, Y)
    return _opensimplex(seed, X, Y)


def noise2_basis(basis, seed: int, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Coherent noise over a *named* basis, independent of the process default.

    ``basis`` of ``None`` uses the current process backend (``noise2``).
    ``"opensimplex"`` degrades to the vectorised Perlin basis when the optional
    ``opensimplex`` package is not installed, so a recipe naming
    ``OpenSimplex2S`` always loads and evaluates with numpy alone (a clear,
    documented fallback rather than an opaque import error)."""
    if basis is None:
        return noise2(seed, X, Y)
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    if basis == "perlin":
        return _perlin(seed, X, Y)
    if basis == "value":
        return _value(seed, X, Y)
    if basis == "opensimplex":
        if HAVE_OPENSIMPLEX:
            return _opensimplex(seed, X, Y)
        return _perlin(seed, X, Y)        # numpy-only fallback
    raise ValueError(f"unknown noise basis {basis!r}")
