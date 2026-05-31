"""The Design's named sampler nodes load via from_spec and evaluate.

Pillar 1 says terrain shape is a saved sampler-graph recipe. The Design's
example recipe pins specific node *names* (``OpenSimplex2S``, ``Perlin``,
``Value``, ``WhiteNoise``, ``Hetero``, ``Select``, ``KernelSlope``) and a
basis-source nesting (``FBM`` wrapping an ``OpenSimplex2S`` ``src``). These tests
assert ``from_spec`` no longer KeyErrors on those names and that the documented
example recipe loads, evaluates over the grid, and round-trips through
``to_spec``.
"""
import numpy as np
import pytest

from terrain.samplers import EvalContext, from_spec, NODE_TYPES
from terrain import masks as M


def _ctx(n=48, seed=7):
    return EvalContext.grid(n, n, seed=seed)


# the example recipe straight out of Design/01-terrain-core.md
EXAMPLE = {
    "type": "Max",
    "left": {
        "type": "CubicSpline",
        "points": [[-1, -60], [-0.1, 50], [0, 64], [0.6, 100], [1, 160]],
        "src": {"type": "FBM", "octaves": 4,
                "src": {"type": "OpenSimplex2S", "freq": 0.0004, "seed": 7}},
    },
    "right": {
        "type": "DomainWarp", "amplitude": 18,
        "src": {"type": "Ridged", "octaves": 8, "gain": 2.0,
                "src": {"type": "OpenSimplex2S", "freq": 0.004, "seed": 11}},
    },
}


def test_named_nodes_registered():
    for t in ("OpenSimplex2S", "Perlin", "Value", "WhiteNoise", "Hetero",
              "Select", "KernelSlope"):
        assert t in NODE_TYPES, f"{t} not registered"


def test_example_recipe_loads_and_evaluates():
    node = from_spec(EXAMPLE)            # must not KeyError
    out = node.eval(_ctx(32, seed=3))
    assert out.shape == (32, 32)
    assert np.isfinite(out).all()


def test_example_recipe_roundtrips():
    node = from_spec(EXAMPLE)
    out1 = node.eval(_ctx(32, seed=3))
    out2 = from_spec(node.to_spec()).eval(_ctx(32, seed=3))
    assert np.array_equal(out1, out2)


def test_fbm_with_opensimplex_src_matches_freq_seed():
    # nesting an OpenSimplex2S src should pull its freq/seed into the octave loop
    nested = from_spec({"type": "FBM", "octaves": 4,
                        "src": {"type": "OpenSimplex2S", "freq": 0.05, "seed": 9}})
    flat = from_spec({"type": "FBM", "octaves": 4, "frequency": 0.05, "seed": 9})
    # OpenSimplex2S falls back to the perlin basis when the package is absent,
    # which is also the default backend → identical fields here.
    from terrain.samplers._backend import HAVE_OPENSIMPLEX, get_backend
    if not HAVE_OPENSIMPLEX and get_backend() == "perlin":
        assert np.allclose(nested.eval(_ctx()), flat.eval(_ctx()))
    else:
        assert nested.eval(_ctx()).shape == (48, 48)


def test_perlin_and_value_sources_evaluate():
    for t in ("Perlin", "Value"):
        out = from_spec({"type": t, "freq": 0.04, "seed": 2}).eval(_ctx())
        assert out.shape == (48, 48)
        assert -1.5 < out.min() and out.max() < 1.5


def test_white_noise_is_high_variance_and_seed_stable():
    a = from_spec({"type": "WhiteNoise", "seed": 5}).eval(_ctx())
    b = from_spec({"type": "WhiteNoise", "seed": 5}).eval(_ctx())
    c = from_spec({"type": "WhiteNoise", "seed": 6}).eval(_ctx())
    assert np.array_equal(a, b)              # deterministic per seed
    assert not np.array_equal(a, c)          # seed matters
    # white noise has near-zero spatial correlation: neighbour diffs are large
    assert np.var(np.diff(a, axis=0)) > np.var(a) * 0.5


def test_select_hard_threshold_picks_a_or_b():
    spec = {"type": "Select", "thr": 0.0,
            "selector": {"type": "Constant", "value": 0.5},
            "a": {"type": "Constant", "value": 100.0},
            "b": {"type": "Constant", "value": 7.0}}
    out = from_spec(spec).eval(_ctx())
    assert np.allclose(out, 100.0)           # selector 0.5 >= 0 → a
    spec["selector"] = {"type": "Constant", "value": -0.5}
    out = from_spec(spec).eval(_ctx())
    assert np.allclose(out, 7.0)             # selector -0.5 < 0 → b


def test_kernel_slope_flat_is_zero_ramp_is_positive():
    # KernelSlope of a constant field is ~0; of a linear ramp is constant > 0
    flat = from_spec({"type": "KernelSlope",
                      "src": {"type": "Constant", "value": 64.0}}).eval(_ctx())
    assert np.allclose(flat, 0.0)
    # build a ramp via a Linear remap of X is awkward in-graph; use a Distance
    ramp_src = {"type": "Distance", "radius": 1000.0}
    ramp = from_spec({"type": "KernelSlope", "src": ramp_src}).eval(_ctx())
    assert ramp.max() > 0.0


def test_hetero_one_sided_and_finite():
    out = from_spec({"type": "Hetero", "frequency": 0.04, "octaves": 5}).eval(_ctx())
    assert np.isfinite(out).all()
    assert out.min() >= -0.05                # one-sided multifractal


def test_mask_noise_thresholds_a_sampler_field():
    ctx = _ctx(40)
    # Constant 0.5 >= 0.0 → all True ; >= 1.0 → all False
    assert M.mask_noise({"type": "Constant", "value": 0.5}, ctx, 0.0).all()
    assert not M.mask_noise({"type": "Constant", "value": 0.5}, ctx, 1.0).any()
    # a real noise field gives a non-trivial, same-shape mask
    m = M.mask_noise({"type": "FBM", "frequency": 0.05, "octaves": 4}, ctx, 0.0)
    assert m.shape == (40, 40)
    assert 0 < m.sum() < m.size
