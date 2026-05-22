"""The terrain analogue of ``voxel.VoxelModel``: a 2.5-D ``HeightField`` you
author with noise and carving operations, *render to see it* before placing a
single block, then materialise to world fills.

``h[x, z]`` is the surface height in **world Y** (so ``sea_level=62`` and real
Y coordinates work directly). The point, exactly as with the voxel toolkit, is
total control plus trivial render-verification: compose a field, render a
hillshade + cross-section, judge it against the references and the
non-negotiable rules, tune one parameter, re-render — and only then place.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from .noise import ValueNoise2D, fbm


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / max(edge1 - edge0, 1e-9), 0.0, 1.0)
    return t * t * (3 - 2 * t)


class HeightField:
    def __init__(self, nx: int, nz: int, sea_level: float = 62.0,
                 base: float = 62.0) -> None:
        self.nx, self.nz = int(nx), int(nz)
        self.h = np.full((self.nx, self.nz), float(base), dtype=float)
        self.sea_level = float(sea_level)

    # -- builders (chainable) ---------------------------------------------
    def add_fbm(self, amplitude: float, *, octaves: int = 4,
                base_freq: float = 0.06, lacunarity: float = 2.0,
                gain: float = 0.5, seed: int = 0, ridge: bool = False,
                warp: float = 0.0) -> "HeightField":
        """Add ``amplitude`` blocks of multi-octave noise. Stack a smooth base
        layer with a low-amplitude ``ridge=True`` layer for mountains."""
        self.h += amplitude * fbm(self.nx, self.nz, octaves=octaves,
                                  base_freq=base_freq, lacunarity=lacunarity,
                                  gain=gain, seed=seed, ridge=ridge, warp=warp)
        return self

    def radial_falloff(self, *, center: Optional[tuple] = None,
                       max_radius: Optional[float] = None, inner: float = 0.0,
                       sx: float = 1.0, sz: float = 1.0,
                       floor: Optional[float] = None) -> "HeightField":
        """Taper height toward ``floor`` (default sea level) past ``max_radius``
        so a landmass sinks into the surrounding sea/plain instead of ending at
        a wall. ``inner`` (0..1) keeps the centre full; ``sx``/``sz`` make the
        falloff elliptical (irregular islands, not discs)."""
        cx, cz = center if center else (self.nx / 2.0, self.nz / 2.0)
        if max_radius is None:
            max_radius = min(self.nx, self.nz) / 2.0
        if floor is None:
            floor = self.sea_level
        X, Z = np.meshgrid(np.arange(self.nx), np.arange(self.nz), indexing="ij")
        d = np.hypot((X - cx) * sx, (Z - cz) * sz)
        f = 1.0 - smoothstep(inner * max_radius, max_radius, d)
        self.h = floor + (self.h - floor) * f
        return self

    def carve_lake(self, *, center: tuple, radii: tuple, depth: float = 6.0,
                   edge: float = 0.35, seed: int = 0) -> "HeightField":
        """Carve an organic blob depression that floods (height pushed below sea
        level). The rim is an irregular ellipse — ``hypot(dx/rx, dz/rz) + noise
        < 1`` — never a circle. Use for lakes, coves, inlets."""
        cx, cz = center
        rx, rz = (max(1e-6, r) for r in radii)
        X, Z = np.meshgrid(np.arange(self.nx), np.arange(self.nz), indexing="ij")
        n = ValueNoise2D(seed + 71).sample(X * 0.12, Z * 0.12)
        blob = np.hypot((X - cx) / rx, (Z - cz) / rz) + (n - 0.5) * 2.0 * edge
        target = self.sea_level - depth
        inside = blob < 1.0
        # smooth the basin floor in toward the centre
        deepen = (1.0 - smoothstep(0.0, 1.0, np.clip(blob, 0, 1))) * (self.h - target)
        self.h = np.where(inside, np.minimum(self.h, self.h - deepen), self.h)
        return self

    def carve_river(self, points: list, *, width: float = 4.0, depth: float = 4.0,
                    bank: float = 3.0, seed: int = 0) -> "HeightField":
        """Carve a meandering channel along a polyline of ``(x, z)`` points.
        The channel is recessed by ``depth`` within ``width``, blended out over
        ``bank`` blocks. Add intermediate points to meander — never a straight
        line (the 7-block rule applies to rivers too)."""
        X, Z = np.meshgrid(np.arange(self.nx), np.arange(self.nz), indexing="ij")
        dist = np.full((self.nx, self.nz), np.inf)
        pts = [np.array(p, dtype=float) for p in points]
        for p0, p1 in zip(pts[:-1], pts[1:]):
            seg = p1 - p0
            L2 = float(seg @ seg) or 1e-9
            t = ((X - p0[0]) * seg[0] + (Z - p0[1]) * seg[1]) / L2
            t = np.clip(t, 0.0, 1.0)
            projx, projz = p0[0] + t * seg[0], p0[1] + t * seg[1]
            dist = np.minimum(dist, np.hypot(X - projx, Z - projz))
        # jitter the banks so the channel edge is not a clean offset curve
        n = ValueNoise2D(seed + 41).sample(X * 0.15, Z * 0.15)
        dist = dist + (n - 0.5) * 2.0
        cut = depth * (1.0 - smoothstep(width, width + bank, dist))
        self.h -= cut
        return self

    def build_pad(self, *, center: tuple, half: tuple, level: float,
                  shoulder: float = 9.0) -> "HeightField":
        """Flatten a buildable pad at ``level``, blending a ``shoulder``-block
        skirt into the surrounding terrain so the pad doesn't sit on a cliff."""
        cx, cz = center
        hx, hz = half
        X, Z = np.meshgrid(np.arange(self.nx), np.arange(self.nz), indexing="ij")
        # Chebyshev-ish distance outside the pad rectangle
        dx = np.maximum(np.abs(X - cx) - hx, 0.0)
        dz = np.maximum(np.abs(Z - cz) - hz, 0.0)
        d = np.hypot(dx, dz)
        w = 1.0 - smoothstep(0.0, shoulder, d)        # 1 on the pad, →0 past skirt
        self.h = self.h * (1 - w) + level * w
        return self

    # -- shaping ----------------------------------------------------------
    def smooth(self, iterations: int = 1) -> "HeightField":
        """Separable 1-2-1 blur (numpy, no scipy). Softens stairstep artifacts
        and pure-45° faces; run 1–3 passes."""
        for _ in range(int(iterations)):
            h = self.h
            hp = np.pad(h, 1, mode="edge")
            kx = (hp[:-2, 1:-1] + 2 * hp[1:-1, 1:-1] + hp[2:, 1:-1]) / 4.0
            kp = np.pad(kx, 1, mode="edge")
            self.h = (kp[1:-1, :-2] + 2 * kp[1:-1, 1:-1] + kp[1:-1, 2:]) / 4.0
        return self

    def erode_hydraulic(self, **kwargs) -> "HeightField":
        """Hydraulic droplet erosion — carves drainage networks and deposits
        sediment, the single biggest realism multiplier. See
        ``terrain.erosion.hydraulic`` for parameters."""
        from .erosion import hydraulic
        self.h = hydraulic(self.h, **kwargs)
        return self

    def erode_thermal(self, **kwargs) -> "HeightField":
        """Thermal/talus erosion — collapses over-steep slopes to a stable
        angle of repose. See ``terrain.erosion.thermal``."""
        from .erosion import thermal
        self.h = thermal(self.h, **kwargs)
        return self

    def clamp(self, min_y: float = -64.0, max_y: float = 320.0) -> "HeightField":
        np.clip(self.h, min_y, max_y, out=self.h)
        return self

    # -- analysis ---------------------------------------------------------
    def slope_deg(self) -> np.ndarray:
        """Per-cell slope in degrees (gradient magnitude), 1 block per cell."""
        gx, gz = np.gradient(self.h)
        return np.degrees(np.arctan(np.hypot(gx, gz)))

    def summary(self) -> dict:
        h = self.h
        below = float(np.mean(h < self.sea_level))
        return {
            "shape": (self.nx, self.nz),
            "min": round(float(h.min()), 2),
            "max": round(float(h.max()), 2),
            "mean": round(float(h.mean()), 2),
            "sea_level": self.sea_level,
            "underwater_fraction": round(below, 3),
            "max_slope_deg": round(float(self.slope_deg().max()), 1),
        }

    # -- io ---------------------------------------------------------------
    def save_npy(self, path: str) -> None:
        np.save(path, self.h)

    @classmethod
    def load_npy(cls, path: str, sea_level: float = 62.0) -> "HeightField":
        h = np.load(path).astype(float)
        hf = cls(h.shape[0], h.shape[1], sea_level=sea_level)
        hf.h = h
        return hf

    @classmethod
    def from_image(cls, path: str, *, min_y: float = 50.0, max_y: float = 120.0,
                   sea_level: float = 62.0) -> "HeightField":
        """Load a greyscale heightmap PNG and scale it to ``[min_y, max_y]``.

        The zero-dependency "import real elevation" path: export a DEM (SRTM /
        Copernicus, QGIS, Tangram Heightmapper, World Machine) to a greyscale
        PNG and bring it in here. For native GeoTIFF/DEM import, add the
        optional ``rasterio``/``richdem`` deps (a future ``requirements-terrain.txt``)."""
        from PIL import Image
        im = Image.open(path).convert("L")
        a = np.asarray(im, dtype=float)            # (rows=z, cols=x) in image space
        a = a.T                                    # → (x, z)
        a = a / 255.0
        hf = cls(a.shape[0], a.shape[1], sea_level=sea_level)
        hf.h = min_y + a * (max_y - min_y)
        return hf
