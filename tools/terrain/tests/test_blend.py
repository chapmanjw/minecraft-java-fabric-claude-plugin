"""Seam-blend tests: the boundary between two regions must be a ramp, not a wall."""
import numpy as np

from terrain import blend


def _two_region_labels(nx=80, nz=40):
    """Left half = region 0, right half = region 1."""
    lab = np.zeros((nx, nz), dtype=int)
    lab[nx // 2:, :] = 1
    return lab


def test_box_blur_blend_removes_wall():
    nx, nz = 80, 40
    lab = _two_region_labels(nx, nz)
    low = np.full((nx, nz), 64.0)     # region 0: plains at Y64
    high = np.full((nx, nz), 110.0)   # region 1: plateau at Y110
    # Hard-stitched field has a 46-block cliff at the seam.
    raw = np.where(lab == 0, low, high)
    seam_jump_raw = abs(raw[nx // 2, 0] - raw[nx // 2 - 1, 0])
    assert seam_jump_raw > 40

    blended = blend.box_blur_blend(lab, {0: low, 1: high}, radius=8)
    # Across the seam, the max single-cell step must be a gentle ramp, not a wall.
    col = blended[:, 0]
    max_step = np.max(np.abs(np.diff(col)))
    assert max_step < 12, f"seam still a wall: {max_step}"
    # ...but far from the seam each region keeps its own height.
    assert abs(blended[2, 0] - 64.0) < 2
    assert abs(blended[-3, 0] - 110.0) < 2


def test_box_blur_blend_monotone_ramp():
    nx, nz = 60, 20
    lab = _two_region_labels(nx, nz)
    low = np.full((nx, nz), 64.0)
    high = np.full((nx, nz), 100.0)
    blended = blend.box_blur_blend(lab, {0: low, 1: high}, radius=6)
    # the transition zone should rise monotonically from low to high
    band = blended[nx // 2 - 6: nx // 2 + 7, 0]
    assert np.all(np.diff(band) >= -1e-6)


def test_sparse_convolution_blend_three_way():
    nx, nz = 60, 60
    seeds = [(10, 10, "a"), (50, 10, "b"), (30, 50, "c")]
    fields = {
        "a": np.full((nx, nz), 64.0),
        "b": np.full((nx, nz), 90.0),
        "c": np.full((nx, nz), 120.0),
    }
    out = blend.sparse_convolution_blend((nx, nz), seeds, fields, k=3)
    # near each seed, the field approaches that seed's height
    assert abs(out[10, 10] - 64.0) < 8
    assert abs(out[50, 10] - 90.0) < 8
    assert abs(out[30, 50] - 120.0) < 8
    # the centre (triple junction) is a blend, strictly between min and max
    cx, cz = 30, 24
    assert 64.0 < out[cx, cz] < 120.0
    # no NaNs / infinities
    assert np.isfinite(out).all()


def test_pad_crop_smooth_no_edge_cliff():
    nx, nz = 40, 40
    h = np.full((nx, nz), 80.0)
    h[20:, :] = 80.0  # uniform: smoothing must not pull the borders down
    sm = blend.pad_crop_smooth(h, sigma=3.0)
    # a uniform field stays ~uniform incl. at the edges (no boundary darkening)
    assert abs(sm[0, 0] - 80.0) < 0.5
    assert abs(sm[-1, -1] - 80.0) < 0.5


def test_weld_joins_only_band():
    nx, nz = 40, 40
    h = np.full((nx, nz), 64.0)
    h[20:, :] = 100.0
    band = np.zeros((nx, nz), dtype=bool)
    band[18:23, :] = True
    out = blend.weld(h, band, strength=2.5)
    # inside the band the step is softened; outside it is untouched
    assert out[0, 0] == 64.0 and out[-1, -1] == 100.0
    band_step = np.max(np.abs(np.diff(out[18:23, 0])))
    raw_step = np.max(np.abs(np.diff(h[18:23, 0])))
    assert band_step < raw_step
