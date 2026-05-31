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
              min_slope: float = 0.01, max_steps: int = 48,
              pad_cells: int = 0, height_falloff: float = 0.0,
              sea_level: float = None) -> np.ndarray:
    """Droplet-based hydraulic erosion (Mei/Lague style). Returns a new eroded
    height array. Each droplet flows downhill carrying sediment up to a
    velocity/water-dependent ``capacity``; it erodes where it has spare capacity
    and deposits where it slows or climbs, building river valleys and alluvial
    fans. ``radius`` spreads erosion over a small brush so channels aren't
    single-cell deep.

    ``pad_cells`` (TerraForged's key detail): reflect-pad the field by this many
    cells, erode, then crop — droplets that would die at the edge keep flowing,
    so there is no erosion seam at the tile boundary. Use ~32 for a hero tile.

    ``height_falloff`` + ``sea_level``: weaken erosion for low terrain so the sim
    doesn't cut below sea level. When set, erosion strength scales by the column's
    normalised elevation once it drops under ``height_falloff`` (0..1 of the land
    range) — protects beaches/seabed."""
    h = h.astype(float)
    if pad_cells and pad_cells > 0:
        p = int(pad_cells)
        padded = np.pad(h, p, mode="reflect")
        eroded = hydraulic(padded, droplets=int(droplets * (padded.size / h.size)),
                           seed=seed, inertia=inertia, capacity=capacity,
                           deposition=deposition, erosion=erosion,
                           evaporation=evaporation, gravity=gravity, radius=radius,
                           min_slope=min_slope, max_steps=max_steps,
                           pad_cells=0, height_falloff=height_falloff,
                           sea_level=sea_level)
        return eroded[p:-p, p:-p].copy()
    h = h.copy()
    nx, nz = h.shape
    rng = np.random.default_rng(seed)
    # optional elevation-based erosion damping (protect low ground)
    erode_scale = None
    if height_falloff and sea_level is not None:
        land_hi = float(h.max())
        land_rng = max(land_hi - sea_level, 1e-6)
        norm = np.clip((h - sea_level) / land_rng, 0.0, 1.0)
        erode_scale = np.clip(norm / max(height_falloff, 1e-6), 0.0, 1.0)

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
                    if erode_scale is not None:
                        take *= float(erode_scale[bx, bz])
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


def flow_accumulation(h: np.ndarray) -> np.ndarray:
    """Per-cell flow accumulation: how many cells drain through each cell, by
    routing every cell to its steepest-downhill 8-neighbour in descending-height
    order (a fast D8 approximation). High-accumulation cells are natural river
    courses. Returns a float array (≥1 everywhere; itself counts)."""
    nx, nz = h.shape
    accum = np.ones((nx, nz), dtype=float)
    order = np.argsort(h.ravel())[::-1]          # highest first
    neigh = [(-1, 0), (1, 0), (0, -1), (0, 1),
             (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for idx in order:
        x, z = divmod(int(idx), nz)
        hz = h[x, z]
        best, bd = None, 0.0
        for dx, dz in neigh:
            nxp, nzp = x + dx, z + dz
            if 0 <= nxp < nx and 0 <= nzp < nz:
                drop = hz - h[nxp, nzp]
                if drop > bd:
                    bd, best = drop, (nxp, nzp)
        if best is not None:
            accum[best] += accum[x, z]
    return accum


def fluvial_rivers(h, *, threshold: float = 800.0, depth: float = 0.3,
                   sea_level: float = None) -> np.ndarray:
    """Carve an emergent dendritic river network from flow accumulation. Cells
    whose drainage exceeds ``threshold`` are deepened proportionally to
    ``log(flow/threshold)`` — main stems cut deeper than tributaries — producing
    a connected network without hand-placed polylines. Clamped so it never digs
    below ``sea_level`` (if given). Returns a new array."""
    h = h.astype(float).copy()
    flow = flow_accumulation(h)
    mask = flow > threshold
    if mask.any():
        cut = depth * np.log(flow[mask] / threshold + 1.0)
        new = h[mask] - cut
        if sea_level is not None:
            new = np.maximum(new, sea_level - 1.0)
        h[mask] = new
    return h
