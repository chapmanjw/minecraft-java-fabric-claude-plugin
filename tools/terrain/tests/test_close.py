"""Offline geometry tests for close_belt_end (Zion P8).

Run with regen=None so the test needs no erosion deps: it checks the closing
SURFACE geometry (corridor pinch + centre ramp + converging walls) and the
np.maximum merge semantics (tall existing terrain is preserved, the surround is
left untouched).
"""
import numpy as np
import pytest

from terrain import HeightField, Centerline, close_belt_end


def test_close_belt_end_raises_gap_and_preserves_existing():
    nx, nz = 40, 60
    field = HeightField(nx, nz, sea_level=62, base=60.0)
    cl = Centerline([(20, 10), (20, 49)])           # straight belt along +z, ends high at z=49
    keypoints = [(1.0, dict(base=60.0, peak=30.0, rise=8.0))]

    field.h[5, 55] = 200.0                           # a tall spike beyond the end, off-axis
    before = field.h.copy()

    close_belt_end(field, cl, keypoints, "high", close_dist=8.0,
                   corridor_half=4.0, fall=10.0, interior_level=60.0, floor=60.0)

    # max semantics: the pre-existing spike survives
    assert field.h[5, 55] == 200.0
    # cells NOT beyond the end are untouched
    assert field.h[20, 10] == before[20, 10] == 60.0
    # the corridor centre rises going outward (pinch + ramp close the canyon)
    assert field.h[20, 51] > 60.0
    assert field.h[20, 54] > field.h[20, 51]
    # a lateral wall cell inside the cap is raised to the wall profile
    assert field.h[28, 52] > 60.0
    # the merge never lowers anything
    assert np.all(field.h >= before)


def test_close_belt_end_low_end():
    nx, nz = 40, 60
    field = HeightField(nx, nz, sea_level=62, base=60.0)
    cl = Centerline([(20, 10), (20, 49)])
    keypoints = [(0.0, dict(base=60.0, peak=24.0, rise=8.0))]
    close_belt_end(field, cl, keypoints, "low", close_dist=8.0,
                   corridor_half=4.0, fall=10.0, floor=60.0)
    # the LOW end (z<10) closes; the HIGH end stays open
    assert field.h[20, 8] > 60.0          # just past the low end (outward)
    assert field.h[20, 55] == 60.0        # the far (high) end is untouched


def test_close_belt_end_invokes_regen_once_before_merge():
    field = HeightField(30, 40, sea_level=62, base=60.0)
    cl = Centerline([(15, 5), (15, 35)])
    kp = [(1.0, dict(base=60.0, peak=20.0, rise=6.0))]
    seen = []

    def regen(hf):
        seen.append(hf)
        assert hf.h.shape == (30, 40)     # the closing field, pre-merge

    close_belt_end(field, cl, kp, "high", close_dist=6.0, corridor_half=3.0, regen=regen)
    assert len(seen) == 1


def test_close_belt_end_rejects_closed_ring():
    field = HeightField(20, 20, base=60.0)
    ring = Centerline([(2, 2), (16, 2), (16, 16), (2, 16)], closed=True)
    with pytest.raises(ValueError):
        close_belt_end(field, ring, [(0.0, dict(base=60, peak=20, rise=6))], "high")
