"""Erosion — the realism multiplier the noise-only heightfield is missing.

Noise alone reads as *lumpy*; erosion makes terrain read as *eroded* — carving
coherent drainage networks, depositing sediment in valleys, and collapsing
over-steep faces to a believable angle of repose. Both functions are pure numpy
and operate on a 2-D height array (in block units).

Run erosion **after** the silhouette/massing is right and **before**
materialising — it is the slowest step (hydraulic is droplet-looped), so don't
re-run it on every parameter tweak. For a 128–256-wide tile, 10–30k droplets is
a few seconds; scale droplets with area.
"""
from __future__ import annotations

import numpy as np


def _bilinear(h, px, pz):
    """Height + downslope gradient (gx, gz) at a float coordinate."""
    nx, nz = h.shape
    x0 = min(max(int(px), 0), nx - 2)
    z0 = min(max(int(pz), 0), nz - 2)
    u, v = px - x0, pz - z0
    h00, h10 = h[x0, z0], h[x0 + 1, z0]
    h01, h11 = h[x0, z0 + 1], h[x0 + 1, z0 + 1]
    gx = (h10 - h00) * (1 - v) + (h11 - h01) * v
    gz = (h01 - h00) * (1 - u) + (h11 - h10) * u
    height = (h00 * (1 - u) + h10 * u) * (1 - v) + (h01 * (1 - u) + h11 * u) * v
    return height, gx, gz


def _deposit(h, px, pz, amount):
    nx, nz = h.shape
    x0 = min(max(int(px), 0), nx - 2)
    z0 = min(max(int(pz), 0), nz - 2)
    u, v = px - x0, pz - z0
    h[x0, z0] += amount * (1 - u) * (1 - v)
    h[x0 + 1, z0] += amount * u * (1 - v)
    h[x0, z0 + 1] += amount * (1 - u) * v
    h[x0 + 1, z0 + 1] += amount * u * v


def hydraulic(h, *, droplets: int = 20000, seed: int = 0, inertia: float = 0.05,
              capacity: float = 4.0, deposition: float = 0.3, erosion: float = 0.3,
              evaporation: float = 0.02, gravity: float = 4.0, radius: int = 2,
              min_slope: float = 0.01, max_steps: int = 48) -> np.ndarray:
    """Droplet-based hydraulic erosion (Mei/Lague style). Returns a new eroded
    height array. Each droplet flows downhill carrying sediment up to a
    velocity/water-dependent ``capacity``; it erodes where it has spare capacity
    and deposits where it slows or climbs, building river valleys and alluvial
    fans. ``radius`` spreads erosion over a small brush so channels aren't
    single-cell deep."""
    h = h.astype(float).copy()
    nx, nz = h.shape
    rng = np.random.default_rng(seed)

    # precompute a normalised erosion brush (offsets + weights)
    brush = []
    wsum = 0.0
    for dx in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            d = np.hypot(dx, dz)
            if d <= radius:
                w = 1.0 - d / (radius + 1e-9)
                brush.append((dx, dz, w))
                wsum += w
    brush = [(dx, dz, w / wsum) for dx, dz, w in brush] if wsum else [(0, 0, 1.0)]

    for _ in range(int(droplets)):
        px = rng.uniform(1, nx - 2)
        pz = rng.uniform(1, nz - 2)
        dirx = dirz = 0.0
        speed, water, sediment = 1.0, 1.0, 0.0
        for _ in range(max_steps):
            height, gx, gz = _bilinear(h, px, pz)
            dirx = dirx * inertia - gx * (1 - inertia)
            dirz = dirz * inertia - gz * (1 - inertia)
            mag = np.hypot(dirx, dirz)
            if mag < 1e-9:
                break
            dirx /= mag
            dirz /= mag
            npx, npz = px + dirx, pz + dirz
            if not (0 <= npx < nx - 1 and 0 <= npz < nz - 1):
                break
            new_h, _, _ = _bilinear(h, npx, npz)
            dh = new_h - height
            if dh >= 0:
                # uphill / flat: drop sediment (cannot climb with a load)
                drop = min(sediment, dh + 1e-3) if dh > 0 else sediment * deposition
                _deposit(h, px, pz, drop)
                sediment -= drop
            else:
                cap = max(-dh, min_slope) * speed * water * capacity
                if sediment > cap:
                    drop = (sediment - cap) * deposition
                    _deposit(h, px, pz, drop)
                    sediment -= drop
                else:
                    take = min((cap - sediment) * erosion, -dh)
                    bx, bz = int(px), int(pz)
                    for ox, oz, w in brush:
                        xx, zz = bx + ox, bz + oz
                        if 0 <= xx < nx and 0 <= zz < nz:
                            h[xx, zz] -= take * w
                    sediment += take
            speed = np.sqrt(max(speed * speed + abs(dh) * gravity, 0.0))
            water *= (1 - evaporation)
            px, pz = npx, npz
    return h


def thermal(h, *, iterations: int = 50, talus: float = 1.0,
            factor: float = 0.5) -> np.ndarray:
    """Thermal (talus) erosion: material on slopes steeper than ``talus`` blocks
    per cell slides to lower neighbours, settling toward a stable angle of
    repose. Vectorised over the 4-neighbourhood; conserves material. Use to tame
    pure-45° noise faces and scree slopes."""
    h = h.astype(float).copy()
    nx, nz = h.shape
    dirs = [(0, 1), (0, -1), (1, 1), (1, -1)]
    for _ in range(int(iterations)):
        delta = np.zeros_like(h)
        for ax, off in dirs:
            cell = [slice(None), slice(None)]
            nb = [slice(None), slice(None)]
            if off == 1:
                cell[ax] = slice(0, h.shape[ax] - 1)
                nb[ax] = slice(1, h.shape[ax])
            else:
                cell[ax] = slice(1, h.shape[ax])
                nb[ax] = slice(0, h.shape[ax] - 1)
            c, n = tuple(cell), tuple(nb)
            diff = h[c] - h[n]
            move = np.where(diff > talus, (diff - talus) * factor * 0.25, 0.0)
            delta[c] -= move
            delta[n] += move
        h += delta
    return h
