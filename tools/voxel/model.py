"""Parametric voxel authoring.

A ``VoxelModel`` wraps a ``numpy`` grid ``g[x, y, z]`` of ``uint8`` block codes
(0 = air; codes resolve through a :class:`~voxel.palette.Palette`). The axes are:

    x — length   (the subject's long/front-back axis)   (index 0)
    y — height   (up is +y)                              (index 1)
    z — width    (left-right)                            (index 2)

With this convention the three orthographic renders line up with the names you
expect: ``side`` (flatten z) is the length×height profile — where silhouette
errors show up most — ``front`` (flatten x) is the width×height end view, and
``top`` (flatten y) is the length×width plan. Orient your model so its defining
silhouette lands in the ``side`` view.

The point of authoring parametrically — rather than voxelizing a downloaded
mesh — is total control over the silhouette plus trivial render-verification.
Define the form from anchors (fractions of the bounding extent) and primitives,
render it, compare to references, tune one parameter, re-render. Only place
blocks once the renders genuinely match.

Anchors: ``fx``/``fy``/``fz`` turn a fraction (0..1) into an index, so you can
say "beltline at 45% of height" once and not chase absolute numbers.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .palette import Palette


def _sphere_offsets(radius: float) -> np.ndarray:
    """Integer offsets within a solid sphere of the given radius (for thick lines)."""
    r = int(np.ceil(radius))
    rng = range(-r, r + 1)
    pts = [
        (dx, dy, dz)
        for dx in rng for dy in rng for dz in rng
        if dx * dx + dy * dy + dz * dz <= radius * radius
    ]
    return np.array(pts, dtype=int) if pts else np.zeros((1, 3), int)


class VoxelModel:
    def __init__(self, nx: int, ny: int, nz: int, palette: Palette) -> None:
        self.g = np.zeros((int(nx), int(ny), int(nz)), dtype=np.uint8)
        self.pal = palette

    # -- shape -------------------------------------------------------------
    @property
    def shape(self) -> tuple[int, int, int]:
        return self.g.shape  # type: ignore[return-value]

    # -- anchors (fraction of extent → index) ------------------------------
    def fx(self, frac: float) -> int:
        return int(round(frac * (self.g.shape[0] - 1)))

    def fy(self, frac: float) -> int:
        return int(round(frac * (self.g.shape[1] - 1)))

    def fz(self, frac: float) -> int:
        return int(round(frac * (self.g.shape[2] - 1)))

    # -- coordinate mesh (cached) ------------------------------------------
    def _mesh(self):
        nx, ny, nz = self.g.shape
        xs = np.arange(nx)[:, None, None]
        ys = np.arange(ny)[None, :, None]
        zs = np.arange(nz)[None, None, :]
        return xs, ys, zs

    # -- primitives --------------------------------------------------------
    def box(self, a: tuple, b: tuple, code: int) -> "VoxelModel":
        """Solid axis-aligned box from corner ``a`` to corner ``b`` (inclusive)."""
        (x0, y0, z0), (x1, y1, z1) = a, b
        x0, x1 = sorted((int(x0), int(x1)))
        y0, y1 = sorted((int(y0), int(y1)))
        z0, z1 = sorted((int(z0), int(z1)))
        self.g[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = code
        return self

    def ellipsoid(self, center: tuple, radii: tuple, code: int,
                  shell: Optional[float] = None) -> "VoxelModel":
        """Solid (or hollow) ellipsoid. ``shell`` (in blocks) keeps only the
        outer rind that thick — for heads, muscle masses, domes, the Bean."""
        cx, cy, cz = center
        rx, ry, rz = (max(1e-6, r) for r in radii)
        xs, ys, zs = self._mesh()
        d = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 + ((zs - cz) / rz) ** 2
        mask = d <= 1.0
        if shell is not None and shell > 0:
            inner = (((xs - cx) / max(1e-6, rx - shell)) ** 2
                     + ((ys - cy) / max(1e-6, ry - shell)) ** 2
                     + ((zs - cz) / max(1e-6, rz - shell)) ** 2)
            mask &= inner > 1.0
        self.g[mask] = code
        return self

    def cylinder(self, axis: str, span: tuple, center2d: tuple, radius: float,
                 code: int, radius_end: Optional[float] = None) -> "VoxelModel":
        """Axis-aligned cylinder / tapered cone along ``axis`` in {'x','y','z'}.

        ``span`` is the (start, end) index along the axis; ``center2d`` is the
        centre on the other two axes (in their natural order). Supply
        ``radius_end`` for a taper (cone, horn, tail, spike)."""
        axis = axis.lower()
        s, e = sorted((int(span[0]), int(span[1])))
        r0 = float(radius)
        r1 = float(radius if radius_end is None else radius_end)
        ai = {"x": 0, "y": 1, "z": 2}[axis]
        oth = [i for i in (0, 1, 2) if i != ai]
        nA, nB = self.g.shape[oth[0]], self.g.shape[oth[1]]
        ca, cb = center2d
        ag = np.arange(nA)[:, None]
        bg = np.arange(nB)[None, :]
        length = max(1, e - s)
        for idx in range(s, e + 1):
            t = (idx - s) / length
            r = r0 + (r1 - r0) * t
            disc = (ag - ca) ** 2 + (bg - cb) ** 2 <= r * r
            sl: list = [slice(None), slice(None), slice(None)]
            sl[ai] = idx
            sub = self.g[tuple(sl)]
            # sub is indexed in (oth[0], oth[1]) order already
            sub[disc] = code
        return self

    def line3d(self, p0: tuple, p1: tuple, code: int, radius: float = 0.0) -> "VoxelModel":
        """3D stepped line (Bresenham), optionally thickened by a sphere of
        ``radius`` at each step — the spine of a limb, a coil, a strut."""
        x0, y0, z0 = (int(v) for v in p0)
        x1, y1, z1 = (int(v) for v in p1)
        dx, dy, dz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
        sx = 1 if x1 >= x0 else -1
        sy = 1 if y1 >= y0 else -1
        sz = 1 if z1 >= z0 else -1
        offs = _sphere_offsets(radius) if radius > 0 else None
        nx, ny, nz = self.g.shape

        def stamp(x, y, z):
            if offs is None:
                if 0 <= x < nx and 0 <= y < ny and 0 <= z < nz:
                    self.g[x, y, z] = code
            else:
                for ox, oy, oz in offs:
                    xx, yy, zz = x + ox, y + oy, z + oz
                    if 0 <= xx < nx and 0 <= yy < ny and 0 <= zz < nz:
                        self.g[xx, yy, zz] = code

        x, y, z = x0, y0, z0
        if dx >= dy and dx >= dz:
            ey, ez = 2 * dy - dx, 2 * dz - dx
            for _ in range(dx + 1):
                stamp(x, y, z)
                if ey >= 0:
                    y += sy; ey -= 2 * dx
                if ez >= 0:
                    z += sz; ez -= 2 * dx
                x += sx; ey += 2 * dy; ez += 2 * dz
        elif dy >= dx and dy >= dz:
            ex, ez = 2 * dx - dy, 2 * dz - dy
            for _ in range(dy + 1):
                stamp(x, y, z)
                if ex >= 0:
                    x += sx; ex -= 2 * dy
                if ez >= 0:
                    z += sz; ez -= 2 * dy
                y += sy; ex += 2 * dx; ez += 2 * dz
        else:
            ex, ey = 2 * dx - dz, 2 * dy - dz
            for _ in range(dz + 1):
                stamp(x, y, z)
                if ex >= 0:
                    x += sx; ex -= 2 * dz
                if ey >= 0:
                    y += sy; ey -= 2 * dz
                z += sz; ex += 2 * dx; ey += 2 * dy
        return self

    # -- editing -----------------------------------------------------------
    def fill_where(self, mask: np.ndarray, code: int) -> "VoxelModel":
        self.g[mask] = code
        return self

    def replace(self, old_code: int, new_code: int) -> "VoxelModel":
        self.g[self.g == old_code] = new_code
        return self

    def clear(self, code: int) -> "VoxelModel":
        """Turn every voxel of ``code`` back into air."""
        self.g[self.g == code] = 0
        return self

    def mirror_x(self) -> "VoxelModel":
        """Mirror the right half onto the left (build one side, mirror it)."""
        nx = self.g.shape[0]
        half = nx // 2
        self.g[:half] = self.g[nx - 1:nx - 1 - half:-1]
        return self

    # -- stats / io --------------------------------------------------------
    def counts(self) -> dict:
        """code → number of solid voxels (air excluded)."""
        vals, cnts = np.unique(self.g, return_counts=True)
        return {int(v): int(c) for v, c in zip(vals, cnts) if v != 0}

    def codes_present(self) -> list[int]:
        """Distinct non-air codes actually used in the grid."""
        return [int(v) for v in np.unique(self.g) if v != 0]

    def solid_count(self) -> int:
        return int(np.count_nonzero(self.g))

    def save_npy(self, path: str) -> None:
        np.save(path, self.g)

    @classmethod
    def load_npy(cls, path: str, palette: Palette) -> "VoxelModel":
        g = np.load(path)
        m = cls(*g.shape, palette=palette)
        m.g = g.astype(np.uint8)
        return m
