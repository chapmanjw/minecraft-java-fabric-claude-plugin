"""Give yourself eyes on the *terrain* before you place a block — the single
habit that turns a 3-iteration ziggurat into a 1-iteration headland.

Three views, each catching a different class of error:

- **hillshade** — relief shading from the surface normals. The make-or-break
  view: terraces, flat tops, and the ziggurat artifact show up instantly as
  flat bands; organic erosion reads as branching drainage. Look here first.
- **relief** — hypsometric colour (sea → beach → green → brown → snow) with the
  hillshade multiplied over it and water filled to sea level. Reads as a map;
  good for massing, coastline shape, lake/island outlines.
- **profile** — cross-section line(s). The proof a slope is compound and not a
  pure 45° wall or a flat-topped step. Plots a few slices with the sea line.

All numpy + Pillow. Images are oriented +x → right, +z → down (a plan view, like
the ``top`` voxel render). Render, ``Read`` the PNGs, judge them against the
references and the non-negotiable rules, tune one parameter, re-render.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .field import HeightField

_SEA = (40, 90, 150)


def _hillshade(h, azimuth=315.0, altitude=45.0, z_factor=2.0):
    gx, gz = np.gradient(h * z_factor)
    slope = np.pi / 2.0 - np.arctan(np.hypot(gx, gz))
    aspect = np.arctan2(-gz, gx)
    az = np.radians(360.0 - azimuth + 90.0)
    alt = np.radians(altitude)
    shade = (np.sin(alt) * np.sin(slope)
             + np.cos(alt) * np.cos(slope) * np.cos(az - aspect))
    return np.clip(shade, 0.0, 1.0)


def _to_image(arr_xz):
    """arr indexed [x, z] → PIL image with +x right, +z down."""
    return Image.fromarray(np.ascontiguousarray(arr_xz.transpose(1, 0, 2)
                                                if arr_xz.ndim == 3
                                                else arr_xz.T))


def _upscale(im, px):
    if px > 1:
        im = im.resize((im.width * px, im.height * px), Image.NEAREST)
    return im


def render_hillshade(hf: HeightField, out: str, *, azimuth: float = 315.0,
                     altitude: float = 45.0, z_factor: float = 2.0,
                     px: int = 3) -> str:
    shade = _hillshade(hf.h, azimuth, altitude, z_factor)
    g = (shade * 255).astype(np.uint8)
    rgb = np.stack([g, g, g], axis=-1)
    rgb[hf.h < hf.sea_level] = _SEA                    # mark water
    _upscale(_to_image(rgb), px).save(out)
    return out


def _hypsometric(t):
    """Map normalised land height t∈[0,1] → RGB (beach→green→brown→snow)."""
    stops = [
        (0.00, (198, 186, 130)),   # sand / beach
        (0.12, (96, 150, 70)),     # lowland green
        (0.45, (120, 142, 78)),    # upland
        (0.70, (140, 120, 92)),    # rock brown
        (0.88, (150, 146, 140)),   # bare grey rock
        (1.00, (240, 240, 245)),   # snow
    ]
    for (t0, c0), (t1, c1) in zip(stops[:-1], stops[1:]):
        if t <= t1:
            f = (t - t0) / max(t1 - t0, 1e-9)
            return tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(3))
    return stops[-1][1]


def render_relief(hf: HeightField, out: str, *, px: int = 3,
                  z_factor: float = 2.0) -> str:
    h = hf.h
    land = h >= hf.sea_level
    hi = max(float(h[land].max()) if land.any() else hf.sea_level + 1,
             hf.sea_level + 1)
    norm = np.clip((h - hf.sea_level) / (hi - hf.sea_level), 0.0, 1.0)

    # build a small lookup for speed
    ramp = np.array([_hypsometric(i / 255.0) for i in range(256)], dtype=float)
    idx = (norm * 255).astype(int)
    rgb = ramp[idx]

    shade = _hillshade(h, z_factor=z_factor)[..., None]
    rgb = rgb * (0.45 + 0.55 * shade)                  # multiply hillshade over colour

    # water: depth-tinted blue
    depth = np.clip((hf.sea_level - h) / 12.0, 0.0, 1.0)[..., None]
    water = np.array(_SEA, float) * (1.0 - 0.4 * depth)
    rgb = np.where((h < hf.sea_level)[..., None], water, rgb)

    _upscale(_to_image(np.clip(rgb, 0, 255).astype(np.uint8)), px).save(out)
    return out


def render_profile(hf: HeightField, out: str, *, axis: str = "x",
                   slices: int = 3, scale: int = 3, pad: int = 8) -> str:
    """Cross-section line plot. ``axis='x'`` profiles run along x at evenly
    spaced z (and vice-versa). Flat tops and pure-45° walls are obvious here;
    compound convex/concave slopes are the goal."""
    h = hf.h
    if axis == "x":
        length = hf.nx
        lines = [h[:, int(z)] for z in np.linspace(hf.nz * 0.2, hf.nz * 0.8, slices)]
    else:
        length = hf.nz
        lines = [h[int(x), :] for x in np.linspace(hf.nx * 0.2, hf.nx * 0.8, slices)]

    y_lo = float(min(l.min() for l in lines))
    y_hi = float(max(l.max() for l in lines))
    y_lo = min(y_lo, hf.sea_level)
    span = max(y_hi - y_lo, 1.0)
    W = length * scale + 2 * pad
    H = int(span * scale) + 2 * pad
    img = Image.new("RGB", (W, H), (245, 245, 245))
    d = ImageDraw.Draw(img)

    def to_xy(i, y):
        return pad + i * scale, H - pad - (y - y_lo) * scale

    # sea line
    sy = H - pad - (hf.sea_level - y_lo) * scale
    d.line([(pad, sy), (W - pad, sy)], fill=_SEA, width=1)

    palette = [(20, 20, 20), (180, 60, 60), (60, 110, 200)]
    for k, line in enumerate(lines):
        col = palette[k % len(palette)]
        pts = [to_xy(i, float(line[i])) for i in range(len(line))]
        d.line(pts, fill=col, width=2)
    img.save(out)
    return out


def render_views(hf: HeightField, prefix: str, *, px: int = 3) -> list:
    """Write the three standard terrain views and return their paths."""
    return [
        render_hillshade(hf, f"{prefix}_hillshade.png", px=px),
        render_relief(hf, f"{prefix}_relief.png", px=px),
        render_profile(hf, f"{prefix}_profile.png"),
    ]
