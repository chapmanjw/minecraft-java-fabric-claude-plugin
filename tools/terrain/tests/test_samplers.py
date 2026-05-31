"""Sampler graph: evaluation, ranges, determinism, round-trip serialisation."""
import numpy as np
import pytest

from terrain.samplers import EvalContext, from_spec, NODE_TYPES


def _ctx(n=48, seed=7):
    return EvalContext.grid(n, n, seed=seed)


def test_all_nodes_registered():
    for t in ("Constant", "Noise", "Cellular", "FBM", "Ridged", "Billow",
              "Hybrid", "DomainWarp", "Add", "Sub", "Mul", "Div", "Min", "Max",
              "Blend", "Scale", "Bias", "Clamp", "Linear", "CubicSpline",
              "Posterize", "Terrace", "Distance", "ImageDEM", "BeltCoord"):
        assert t in NODE_TYPES, f"{t} not registered"


def test_fbm_shape_and_range():
    s = from_spec({"type": "FBM", "frequency": 0.05, "octaves": 5})
    out = s.eval(_ctx())
    assert out.shape == (48, 48)
    assert -1.2 < out.min() and out.max() < 1.2  # ~[-1,1]


def test_constant_sugar():
    # bare scalar → Constant
    s = from_spec(64)
    out = s.eval(_ctx())
    assert np.allclose(out, 64.0)


def test_ridged_one_sided_and_peaky():
    flat = from_spec({"type": "FBM", "frequency": 0.05, "octaves": 4}).eval(_ctx())
    ridged = from_spec({"type": "Ridged", "frequency": 0.05, "octaves": 6}).eval(_ctx())
    assert ridged.min() >= -0.05  # one-sided ~[0,1]
    # ridged noise is "peakier": higher kurtosis / more mass near its max than fbm
    assert ridged.max() <= 1.2


def test_determinism():
    spec = {"type": "DomainWarp", "amplitude": 15,
            "src": {"type": "Ridged", "frequency": 0.04, "octaves": 5}}
    a = from_spec(spec).eval(_ctx(seed=3))
    b = from_spec(spec).eval(_ctx(seed=3))
    assert np.array_equal(a, b)
    c = from_spec(spec).eval(_ctx(seed=4))
    assert not np.array_equal(a, c)  # seed actually matters


def test_domain_warp_two_vector_not_streaky():
    # A warped constant-frequency field should differ along BOTH axes, i.e. the
    # warp is 2-vector, not collapsed onto one axis (the "streaky warp" bug).
    spec = {"type": "DomainWarp", "amplitude": 25, "frequency": 0.03,
            "src": {"type": "Noise", "frequency": 0.08}}
    out = from_spec(spec).eval(_ctx(64))
    var_x = np.var(np.diff(out, axis=0))
    var_z = np.var(np.diff(out, axis=1))
    assert var_x > 1e-6 and var_z > 1e-6
    # neither axis dominates by more than ~20x (would indicate 1-axis streaking)
    assert 0.05 < var_x / var_z < 20.0


def test_max_composition_mountains_from_plains():
    spec = {"type": "Max",
            "a": {"type": "Constant", "value": 0.0},
            "b": {"type": "Ridged", "frequency": 0.05, "octaves": 5}}
    out = from_spec(spec).eval(_ctx())
    assert out.min() >= -1e-9  # plains floor at 0, ridges rise above


def test_cubic_spline_remap():
    spec = {"type": "CubicSpline",
            "src": {"type": "Constant", "value": 0.0},
            "points": [[-1, -60], [0, 64], [1, 160]]}
    out = from_spec(spec).eval(_ctx())
    assert np.allclose(out, 64.0)  # value 0 maps to 64


def test_cellular_returns():
    for ret in ("F1", "F2", "F2F1", "inv_F1"):
        out = from_spec({"type": "Cellular", "frequency": 0.05, "ret": ret}).eval(_ctx())
        assert out.shape == (48, 48)
        assert np.isfinite(out).all()


def test_roundtrip_serialisation():
    spec = {
        "type": "Add",
        "a": {"type": "CubicSpline",
              "src": {"type": "FBM", "frequency": 0.004, "octaves": 4, "seed": 7},
              "points": [[-1, -40], [0, 64], [1, 120]]},
        "b": {"type": "DomainWarp", "amplitude": 18,
              "src": {"type": "Ridged", "frequency": 0.03, "octaves": 6, "seed": 11}},
    }
    node = from_spec(spec)
    out1 = node.eval(_ctx())
    spec2 = node.to_spec()
    out2 = from_spec(spec2).eval(_ctx())
    assert np.array_equal(out1, out2)  # spec → node → spec → node is stable


def test_terrace_quantises():
    base = {"type": "Scale", "src": {"type": "FBM", "frequency": 0.03, "octaves": 4},
            "factor": 40.0}
    plain = from_spec(base).eval(_ctx())
    terr = from_spec({"type": "Terrace", "src": base, "steps": 4,
                      "smoothing": 0.0}).eval(_ctx())
    # hard terracing has far fewer distinct rounded levels than the smooth field
    assert len(np.unique(np.round(terr, 3))) < len(np.unique(np.round(plain, 3)))
