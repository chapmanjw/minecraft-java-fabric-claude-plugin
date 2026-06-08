"""Close one END of a belt-style canyon/valley so it integrates with the side
walls instead of reading as a pasted-in headwall (Zion P8).

Closing a canyon end with a *different* process than the surrounding walls always
reads as pasted-in. The failure taxonomy from the Zion build, in the order it was
hit: a per-column random-top headwall is a vertical "dripping curtain"; "more
eroded" via per-column gully/notch makes the same vertical pins; remnants of the
old wider structure flank the new one; and a smooth formula bowl between rough
eroded walls looks pasted-in. The fix is to close the end with the SAME machinery
that made the walls.

``close_belt_end`` does exactly that on the toolkit's belt model
(``HeightField.belt_from_path`` + ``Centerline``):

- it reuses the belt's OWN cross-section — the ``keypoints`` you passed to
  ``belt_from_path`` — sampled at the chosen end, with the corridor half-width
  pinching to 0 and a centre ramp rising so the two walls converge and the canyon
  seams shut;
- it asks the caller to re-apply, via ``regen``, the EXACT SAME ``add_fbm``
  (identical seeds, the field's global grid coordinates) and
  ``erode_thermal``/``erode_hydraulic`` used to build the belt, so the noise phase
  and rock texture line up at the seam;
- it merges with ``np.maximum`` — keeping tall existing walls and only raising the
  gap.

    def regen(hf):                       # the SAME calls used to build the belt
        hf.add_fbm(3.0, octaves=4, base_freq=0.018, warp=14, seed=11)
        hf.add_fbm(4.0, octaves=4, base_freq=0.050, warp=20, seed=23)
        hf.erode_thermal(iterations=18, talus=1.6)
        hf.erode_hydraulic(droplets=30000, seed=7)

    close_belt_end(field, centerline, keypoints, "high",
                   close_dist=46, corridor_half=4, regen=regen)
    # then re-run the SAME materializer over the end window.

Numpy only (erosion deps are reached through the caller's ``regen``), so the
geometry is unit-testable offline with ``regen=None``.
"""
from __future__ import annotations

import numpy as np

from .field import smoothstep

_LOW_ALIASES = {"low", "start", "begin", "s0", "0"}
_HIGH_ALIASES = {"high", "end", "finish", "s1", "1"}


def _end_axis(centerline, end):
    """Return ``(p_end, outward_unit)`` for the chosen end: the end point of the
    centerline and the unit vector pointing OUTWARD past it (away from the belt)."""
    pts = centerline.pts
    if len(pts) < 2:
        raise ValueError("centerline needs at least 2 points to have an end")
    if end in _HIGH_ALIASES:
        p_end = pts[-1]
        tangent = pts[-1] - pts[-2]          # belt -> end, i.e. outward
    elif end in _LOW_ALIASES:
        p_end = pts[0]
        tangent = pts[0] - pts[1]            # belt -> start, i.e. outward
    else:
        raise ValueError(f"end must be one of {sorted(_LOW_ALIASES | _HIGH_ALIASES)}, got {end!r}")
    norm = float(np.hypot(tangent[0], tangent[1])) or 1e-9
    return np.asarray(p_end, dtype=float), tangent / norm


def _end_params(keypoints, end):
    """Sample (base, peak, rise) from the belt keypoints at the chosen end."""
    target = 1.0 if end in _HIGH_ALIASES else 0.0
    if not keypoints:
        return 62.0, 0.0, 16.0
    sf, params = min(keypoints, key=lambda k: abs(float(k[0]) - target))
    return (float(params.get("base", 62.0)),
            float(params.get("peak", 0.0)),
            max(float(params.get("rise", 16.0)), 1e-6))


def close_belt_end(field, centerline, keypoints, end, *, close_dist=46.0,
                   corridor_half=0.0, fall=24.0, interior_level=None,
                   floor=None, regen=None):
    """Close one end of a belt so it blends with the side walls. Mutates and
    returns ``field`` (a ``HeightField``).

    ``centerline`` / ``keypoints`` — the SAME ones passed to ``belt_from_path``.
    ``end`` — "low" closes the s=0 end of the centerline, "high" the s=length end.
    ``close_dist`` — blocks of distance over which the canyon pinches shut.
    ``corridor_half`` — the belt's flat-corridor half-width (it pinches to 0 going
    outward). ``fall`` — distance over which the wall falls back to the interior.
    ``interior_level`` — level beyond the walls (default: ``floor``; keeps the
    lateral surround low so ``np.maximum`` never raises it). ``floor`` — the base
    level of the closing field outside the cap (default: the field's current min,
    so the merge only raises the canyon mouth). ``regen(hf)`` — a callback that
    re-applies the SAME noise + erosion used to build the belt; called on the
    closing field before the merge so the seam matches by construction.

    Raises ``ValueError`` for a closed centerline (a ring has no end to close).
    """
    if getattr(centerline, "closed", False):
        raise ValueError("close_belt_end needs an OPEN centerline (a ring has no end)")

    p_end, outward = _end_axis(centerline, end)
    ux, uz = float(outward[0]), float(outward[1])
    base, peak, rise = _end_params(keypoints, end)
    floor_v = float(field.h.min()) if floor is None else float(floor)
    interior = floor_v if interior_level is None else float(interior_level)
    fall = max(float(fall), 1e-9)
    close_dist = max(float(close_dist), 1e-9)

    nx, nz = field.nx, field.nz
    X, Z = np.meshgrid(np.arange(nx), np.arange(nz), indexing="ij")
    vx = X - p_end[0]
    vz = Z - p_end[1]
    t = vx * ux + vz * uz                       # distance OUTWARD past the end
    lat = np.hypot(vx - t * ux, vz - t * uz)    # perpendicular to the axis
    cap = (t > 0) & (t <= close_dist)

    frac = np.clip(t / close_dist, 0.0, 1.0)
    ch_k = corridor_half * (1.0 - frac)         # corridor half-width -> 0 (pinch)
    flank = np.maximum(lat - ch_k, 0.0)
    crest = base + peak
    up = smoothstep(0.0, 1.0, flank / rise)     # 0 at corridor, 1 at crest
    h_up = base + (crest - base) * up
    down = smoothstep(0.0, 1.0, (flank - rise) / fall)   # crest -> interior
    h_cross = h_up * (1.0 - down) + interior * down
    ramp = base + (peak * 0.62) * frac          # centre floor rises to close

    surface = np.maximum(h_cross, ramp)
    closing = np.where(cap, surface, floor_v)

    from .field import HeightField
    hf2 = HeightField(nx, nz, sea_level=field.sea_level, base=floor_v)
    hf2.h = closing
    if regen is not None:
        regen(hf2)
    field.h = np.maximum(field.h, hf2.h)
    return field
