"""Seam blending — Pillar 3 of the redesign (the fix for failure mode #2).

A seam between two terrain regions is a *shape* discontinuity, not a colour one;
colour-dithering the boundary cannot fix it (the parks-grand-loop lesson). The
only fix is to blend the height *field* across the boundary. Three mechanisms,
all here:

  box_blur_blend         hard region labels + a separable box blur of each
                         region's own height function → a ramp at every border
                         (TerraformGenerator's SectionBlurCache, in numpy).
  sparse_convolution_blend   jittered seed points, quartic-falloff weights to the
                         K nearest, normalised to sum 1 → smooth 2-D blend that
                         handles three-way junctions a two-neighbour lerp cannot.
  weld / pad_crop_smooth   additive / mass-preserving Gaussian across a boundary
                         band — the fallback when two independent fields must meet
                         (Axiom's Weld; WorldEdit's pad-and-crop //smooth).

The Centerline belt method (in field.py) remains the strongest fix for
corridor-shaped spans; these handle 2-D patchworks the belt can't.
"""
from __future__ import annotations

import numpy as np


def box_blur_blend(label_grid: np.ndarray, height_fns, radius: int = 8) -> np.ndarray:
    """Blend per-region heights into one seamless field.

    ``label_grid`` is an int ``(nx, nz)`` array naming each cell's region;
    ``height_fns`` maps a label to either a 2-D height array (already evaluated)
    or a callable ``() -> array``. Each cell first takes its own region's height,
    then a separable box blur (radius ``radius``) averages across borders so a
    column near a boundary becomes a weighted blend of both regions — a ramp,
    never a wall.
    """
    from scipy.ndimage import uniform_filter
    shape = label_grid.shape
    raw = np.zeros(shape, dtype=float)
    for label, fn in height_fns.items():
        hv = fn() if callable(fn) else np.asarray(fn, dtype=float)
        raw = np.where(label_grid == label, hv, raw)
    size = max(1, int(radius) * 2 + 1)
    return uniform_filter(raw, size=size, mode="nearest")


def sparse_convolution_blend(shape, seeds, height_fns, k: int = 4) -> np.ndarray:
    """Normalised sparse-convolution blend over an ``(nx, nz)`` grid.

    ``seeds`` is a list of ``(x, z, label)``; ``height_fns`` maps a label to a
    2-D height array (or callable). For every cell, the K nearest seeds vote with
    a quartic-falloff weight ``(r**2 - d**2)**2`` (r = distance to the K-th seed),
    normalised to sum 1, and the cell's height is that weighted blend of the
    seeds' regional height functions. Generalises the belt to unbounded 2-D and
    blends three-way junctions cleanly.
    """
    nx, nz = shape
    X, Z = np.meshgrid(np.arange(nx, dtype=float), np.arange(nz, dtype=float),
                       indexing="ij")
    # evaluate each label's height field once
    fields = {lab: (fn() if callable(fn) else np.asarray(fn, dtype=float))
              for lab, fn in height_fns.items()}
    seeds = list(seeds)
    sx = np.array([s[0] for s in seeds], dtype=float)
    sz = np.array([s[1] for s in seeds], dtype=float)
    slab = [s[2] for s in seeds]
    k = min(k, len(seeds))
    # distance from every cell to every seed: (nseeds, nx, nz)
    d = np.sqrt((X[None] - sx[:, None, None]) ** 2
                + (Z[None] - sz[:, None, None]) ** 2)
    # K nearest seeds per cell
    order = np.argsort(d, axis=0)[:k]                       # (k, nx, nz)
    dk = np.take_along_axis(d, order, axis=0)              # (k, nx, nz)
    r = dk[-1] + 1e-6                                       # K-th distance (support)
    w = np.clip(r[None] ** 2 - dk ** 2, 0.0, None) ** 2    # quartic falloff
    wsum = w.sum(axis=0) + 1e-12
    out = np.zeros(shape, dtype=float)
    for i in range(k):
        # gather the regional height for each cell's i-th nearest seed
        lab_idx = order[i]                                  # (nx, nz) seed index
        # build the height contribution: for each distinct label, mask in
        contrib = np.zeros(shape, dtype=float)
        for si, lab in enumerate(slab):
            sel = lab_idx == si
            if sel.any():
                contrib[sel] = fields[lab][sel]
        out += w[i] * contrib
    return out / wsum


def weld(h: np.ndarray, band_mask: np.ndarray, strength: float = 2.0) -> np.ndarray:
    """Additive Gaussian across a boundary band — raise/lower toward a blurred
    target only where ``band_mask`` is true, joining two authored fields. The
    in-toolkit equivalent of Axiom's Weld."""
    from scipy.ndimage import gaussian_filter
    target = gaussian_filter(h, sigma=max(strength, 1e-3))
    out = h.copy()
    out[band_mask] = target[band_mask]
    return out


def pad_crop_smooth(h: np.ndarray, sigma: float = 2.0, pad: int = None,
                    edge_heights: np.ndarray = None) -> np.ndarray:
    """Gaussian smooth without a selection-boundary cliff. The field is padded by
    ``pad`` (default ``ceil(3*sigma)``) — reflecting its own edge, or using
    ``edge_heights`` (real neighbour heights from the world) when given — then
    smoothed and cropped. Fixes WorldEdit's //smooth seam."""
    from scipy.ndimage import gaussian_filter
    if pad is None:
        pad = int(np.ceil(3 * sigma))
    if edge_heights is not None:
        padded = np.asarray(edge_heights, dtype=float)
        assert padded.shape == (h.shape[0] + 2 * pad, h.shape[1] + 2 * pad)
        padded[pad:-pad, pad:-pad] = h
    else:
        padded = np.pad(h, pad, mode="reflect")
    sm = gaussian_filter(padded, sigma=sigma)
    return sm[pad:pad + h.shape[0], pad:pad + h.shape[1]]
