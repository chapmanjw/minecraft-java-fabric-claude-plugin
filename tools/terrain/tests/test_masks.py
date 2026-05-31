"""Mask correctness against known heightfields."""
import numpy as np

from terrain import masks


def test_slope_flat_is_zero():
    h = np.full((20, 20), 64.0)
    assert np.allclose(masks.slope_deg(h), 0.0)


def test_slope_45_degree_ramp():
    # height increases 1 block per cell along x → 45° slope
    h = np.tile(np.arange(20.0)[:, None], (1, 20))
    s = masks.slope_deg(h)
    assert abs(s[10, 10] - 45.0) < 1e-6


def test_curvature_sign():
    # a pyramid peak → convex (positive) at the apex region edges, concave bowl negative
    x = np.arange(21) - 10
    X, Z = np.meshgrid(x, x, indexing="ij")
    bowl = (X.astype(float) ** 2 + Z ** 2)          # concave-up paraboloid (valley)
    c = masks.curvature(bowl)
    assert c[10, 10] > 0  # bottom of a valley: Laplacian positive
    hill = -bowl
    assert masks.curvature(hill)[10, 10] < 0  # hilltop: Laplacian negative


def test_mask_slope_selects_steep():
    h = np.tile(np.arange(20.0)[:, None] * 2.0, (1, 20))  # ~63° slope
    steep = masks.mask_slope(h, lo=45.0, hi=90.0)
    assert steep.any()
    flat = masks.mask_slope(np.full((20, 20), 64.0), lo=45.0, hi=90.0)
    assert not flat.any()


def test_mask_y():
    h = np.tile(np.arange(10.0)[:, None], (1, 10))
    assert int(masks.mask_y(h, ">", 5).sum()) == 40   # rows 6,7,8,9
    assert int(masks.mask_y(h, "<", 5).sum()) == 50    # rows 0..4


def test_dist_to_water():
    h = np.full((20, 20), 70.0)
    h[0, :] = 60.0  # a strip of water along x=0
    d = masks.dist_to_water(h, sea_level=62.0)
    assert np.allclose(d[0, :], 0.0)
    assert d[5, 10] > d[1, 10]  # farther rows are farther from water


def test_combinators_are_numpy_bool():
    h = np.tile(np.arange(20.0)[:, None], (1, 20))
    steep = masks.mask_slope(h, lo=30.0)
    high = masks.mask_y(h, ">", 10)
    combined = steep & high & ~masks.mask_y(h, ">", 18)
    assert combined.dtype == bool
