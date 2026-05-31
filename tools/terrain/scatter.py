"""Mask-weighted vegetation/feature scatter — Pillar 7.

Replaces uniform-random placement (which clumps and voids) with variable-density
Poisson-disk (blue noise) sampling whose local spacing is driven by a density
map = product of terrain masks (slope, curvature, height band, distance-to-water)
and the biome's own density. Each point is then assigned a species from a
weighted vector, so a stand is a natural mix, not a monoculture.

Output is a placement list — ``[(x, y, z, kind, id), ...]`` — consumed by
``emit.py`` and ultimately by ``level_place_feature`` / the batch tool /
``structure_load_to_world``. ``kind`` is "feature" (grow a vanilla configured
feature) or "structure" (stamp a saved template, e.g. a boulder).
"""
from __future__ import annotations

import numpy as np

from . import masks as M


def density_map(hf, *, prefer_flat: bool = True, near_water: float = 0.0,
                height_band: tuple = None, base: float = 1.0,
                avoid_steep_deg: float = 32.0) -> np.ndarray:
    """A 0..1 density field from terrain masks. ``prefer_flat`` drops density on
    steep ground (trees don't grow on cliffs); ``near_water`` (>0) boosts density
    within that many blocks of water (riparian); ``height_band`` (lo, hi) limits
    to an elevation range (e.g. tree line)."""
    nx, nz = hf.nx, hf.nz
    d = np.full((nx, nz), float(base))
    s = M.slope_deg(hf.h)
    if prefer_flat:
        d *= np.clip(1.0 - s / max(avoid_steep_deg, 1e-6), 0.0, 1.0)
    # never on land below water
    d *= (hf.h > hf.sea_level)
    if near_water > 0:
        dw = M.dist_to_water(hf.h, hf.sea_level)
        d *= np.exp(-dw / max(near_water, 1e-6))
    if height_band is not None:
        lo, hi = height_band
        d *= ((hf.h >= lo) & (hf.h <= hi))
    return np.clip(d, 0.0, 1.0)


def poisson(density: np.ndarray, *, r_min: float = 3.0, r_max: float = 14.0,
            seed: int = 0, k: int = 20) -> list:
    """Variable-density Poisson-disk sampling (Bridson) over a density field.
    Local minimum spacing scales from ``r_min`` (dense, density≈1) to ``r_max``
    (sparse, density≈0). Returns a list of (x, z) grid points. Cells with
    density ≤ 0 are never seeded."""
    nx, nz = density.shape
    rng = np.random.default_rng(seed)
    cell = r_min / np.sqrt(2)
    gw = int(np.ceil(nx / cell)) + 1
    gh = int(np.ceil(nz / cell)) + 1
    grid = -np.ones((gw, gh), dtype=int)
    pts: list = []
    active: list = []

    def r_at(x, z):
        d = density[min(int(x), nx - 1), min(int(z), nz - 1)]
        return r_min + (r_max - r_min) * (1.0 - float(d))

    def fits(x, z, r):
        gx, gz = int(x / cell), int(z / cell)
        for ix in range(max(gx - 2, 0), min(gx + 3, gw)):
            for iz in range(max(gz - 2, 0), min(gz + 3, gh)):
                pi = grid[ix, iz]
                if pi >= 0:
                    px, pz = pts[pi]
                    if (px - x) ** 2 + (pz - z) ** 2 < r * r:
                        return False
        return True

    # seed from a few random in-density starting points
    cand = np.argwhere(density > 0.05)
    if len(cand) == 0:
        return []
    for _ in range(min(8, len(cand))):
        sx, sz = cand[rng.integers(len(cand))]
        if fits(sx, sz, r_at(sx, sz)):
            pts.append((float(sx), float(sz)))
            active.append(len(pts) - 1)
            grid[int(sx / cell), int(sz / cell)] = len(pts) - 1

    while active:
        ai = rng.integers(len(active))
        pi = active[ai]
        px, pz = pts[pi]
        placed = False
        rr = r_at(px, pz)
        for _ in range(k):
            ang = rng.uniform(0, 2 * np.pi)
            rad = rng.uniform(rr, 2 * rr)
            x = px + rad * np.cos(ang)
            z = pz + rad * np.sin(ang)
            if 0 <= x < nx and 0 <= z < nz:
                d = density[int(x), int(z)]
                if d > 0.05 and fits(x, z, r_at(x, z)):
                    pts.append((x, z))
                    active.append(len(pts) - 1)
                    grid[int(x / cell), int(z / cell)] = len(pts) - 1
                    placed = True
                    break
        if not placed:
            active.pop(ai)
    return [(int(round(x)), int(round(z))) for x, z in pts]


def assign_species(points: list, weights: dict, seed: int = 0) -> list:
    """Assign each point a feature id from a ``{id: weight}`` mix."""
    rng = np.random.default_rng(seed)
    ids = list(weights.keys())
    w = np.array([weights[i] for i in ids], dtype=float)
    w = w / w.sum()
    pick = rng.choice(len(ids), size=len(points), p=w)
    return [ids[i] for i in pick]


def scatter_for_biomes(hf, biome_field, *, origin=(0, 0), seed: int = 0) -> list:
    """Build a full placement list for a heightfield + BiomeField. For each
    biome present, compute a density map (scaled by the biome's density), run
    variable-density Poisson, and assign species from the biome's feature list.
    Returns ``[(wx, wy, wz, "feature", feature_id), ...]`` in world coordinates
    (wy is surface+1). Forest edges thin naturally because density falls off with
    slope and the biome mask."""
    from .climate import BIOME_CONTENT
    labels = biome_field.assign()
    ox, oz = origin
    out: list = []
    placed_grid = np.zeros((hf.nx, hf.nz), dtype=bool)
    # process densest biomes first so canopy claims space before understory
    biomes = sorted(set(labels.reshape(-1).tolist()),
                    key=lambda b: -BIOME_CONTENT.get(b, {}).get("density", 0.0))
    for bi, biome in enumerate(biomes):
        content = BIOME_CONTENT.get(biome)
        if not content or content["density"] <= 0 or not content["features"]:
            continue
        mask = (labels == biome)
        riparian = content["density"] if "jungle" in biome or "swamp" in biome else 0.0
        d = density_map(hf, near_water=18.0 if riparian else 0.0, base=1.0)
        d = d * mask * content["density"]
        # spacing: dense canopy ~3, sparse plains ~12
        dens = content["density"]
        rmin = 2.5 + (1 - dens) * 3
        rmax = 8 + (1 - dens) * 18
        pts = poisson(d, r_min=rmin, r_max=rmax, seed=seed + bi)
        # keep in-bounds points (poisson can emit a sample at index == n on the
        # far edge), and don't double-place where a denser biome already seeded
        pts = [(x, z) for (x, z) in pts
               if 0 <= x < hf.nx and 0 <= z < hf.nz and not placed_grid[x, z]]
        species = assign_species(pts, {f: 1.0 for f in content["features"]},
                                 seed=seed + 100 + bi)
        for (x, z), fid in zip(pts, species):
            wy = int(round(hf.h[x, z])) + 1
            out.append((ox + x, wy, oz + z, "feature", fid))
            placed_grid[max(x - 1, 0):x + 2, max(z - 1, 0):z + 2] = True
    return out
