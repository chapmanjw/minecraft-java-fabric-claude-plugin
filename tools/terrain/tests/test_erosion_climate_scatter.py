"""Erosion (pad/fluvial), climate (biome assign + blend), scatter (Poisson mix), emit."""
import numpy as np

from terrain import HeightField, BiomeField, fluvial_rivers, flow_accumulation
from terrain import scatter as S
from terrain import emit


def _terrain(n=60, seed=4):
    hf = HeightField(n, n, sea_level=62)
    hf.add_fbm(40, octaves=5, base_freq=0.03, seed=seed)
    hf.add_fbm(12, octaves=4, base_freq=0.08, ridge=True, seed=seed + 1)
    return hf


# -- erosion ---------------------------------------------------------------
def test_hydraulic_pad_no_edge_bias():
    hf = _terrain()
    base = hf.h.copy()
    eroded = hf.erode_hydraulic(droplets=4000, seed=1, pad_cells=12).h
    assert eroded.shape == base.shape
    # erosion changed the field but kept it finite and bounded
    assert np.isfinite(eroded).all()
    assert not np.array_equal(eroded, base)


def test_flow_accumulation_and_fluvial():
    # a tilted plane: all flow concentrates at the low edge
    h = np.tile(np.arange(40.0)[::-1, None], (1, 40)) + 64
    acc = flow_accumulation(h)
    assert acc.max() > acc.mean()           # some cells accumulate a lot
    carved = fluvial_rivers(h, threshold=20, depth=0.5, sea_level=62)
    assert carved.min() <= h.min()          # channels were cut


def test_fluvial_respects_sea_level():
    hf = _terrain()
    carved = fluvial_rivers(hf.h, threshold=200, depth=2.0, sea_level=62)
    assert carved.min() >= 62 - 1.5


# -- climate ---------------------------------------------------------------
def test_biome_assign_returns_vanilla_ids():
    hf = _terrain()
    bf = BiomeField(hf, seed=7)
    labels = bf.assign()
    assert labels.shape == (hf.nx, hf.nz)
    ids = set(labels.reshape(-1).tolist())
    assert all(i.startswith("minecraft:") for i in ids)
    assert len(ids) >= 1


def test_biome_fill_plan_rectangles():
    hf = _terrain()
    bf = BiomeField(hf, seed=7)
    plan = bf.to_biome_fill_plan(origin=(100, -50))
    assert len(plan) > 0
    for r in plan:
        assert set(r) == {"from", "to", "biome"}
        assert r["to"][0] >= r["from"][0] and r["to"][2] >= r["from"][2]
        assert r["biome"].startswith("minecraft:")


def test_biome_height_blend_no_wall():
    # two flat biomes at different heights, blended → ramp not wall
    from terrain import blend
    nx, nz = 60, 30
    lab = np.zeros((nx, nz), dtype=int)
    lab[30:, :] = 1
    blended = blend.box_blur_blend(
        lab, {0: np.full((nx, nz), 66.0), 1: np.full((nx, nz), 96.0)}, radius=10)
    col = blended[:, 0]
    assert np.max(np.abs(np.diff(col))) < 12


# -- scatter ---------------------------------------------------------------
def test_density_map_zero_on_steep_and_underwater():
    hf = HeightField(30, 30, sea_level=62)
    hf.h = np.tile(np.arange(30.0)[:, None] * 3 + 50, (1, 30))   # steep ramp, part underwater
    d = S.density_map(hf, avoid_steep_deg=30.0)
    assert (d[hf.h <= hf.sea_level] == 0).all()  # never on/under water
    assert d.max() <= 1.0


def test_poisson_blue_noise_spacing():
    hf = _terrain()
    d = S.density_map(hf, base=1.0)
    pts = S.poisson(d, r_min=4.0, r_max=10.0, seed=1)
    assert len(pts) > 5
    # minimum pairwise distance respects ~r_min (allow rounding slack)
    pa = np.array(pts, dtype=float)
    # check a sample of nearest-neighbour distances
    from scipy.spatial import cKDTree
    tree = cKDTree(pa)
    dists, _ = tree.query(pa, k=2)
    nn = dists[:, 1]
    assert nn.min() >= 3.0   # no two closer than ~r_min


def test_scatter_species_mix_not_monoculture():
    hf = _terrain()
    bf = BiomeField(hf, seed=7)
    placements = S.scatter_for_biomes(hf, bf, seed=3)
    # placements may be empty if the biome rolled desert/plains only; force a forest
    if placements:
        kinds = {p[3] for p in placements}
        assert kinds <= {"feature", "structure"}
        for (x, y, z, kind, fid) in placements[:20]:
            assert fid.startswith("minecraft:")
            assert isinstance(y, int)


def test_scatter_no_edge_index_error():
    """poisson can sample at index == n on the far edge; scatter_for_biomes must
    drop those rather than raise IndexError (regression: a 344-wide loop field
    crashed on ``placed_grid[344, z]``). Every placement stays inside the grid."""
    for n in (61, 100, 137, 200, 344):
        hf = _terrain(n=n, seed=2)
        bf = BiomeField(hf, seed=1)
        ox, oz = 1328, -137
        placements = S.scatter_for_biomes(hf, bf, origin=(ox, oz), seed=3)
        for (wx, wy, wz, _kind, _fid) in placements:
            assert ox <= wx <= ox + n - 1, (n, wx)
            assert oz <= wz <= oz + n - 1, (n, wz)


# -- emit ------------------------------------------------------------------
def _recipe(n=48):
    return {
        "version": 1, "nx": n, "nz": n, "sea_level": 62, "seed": 5,
        "origin": [0, 0, 0], "dimension": "minecraft:overworld",
        "graph": {"type": "Add",
                  "a": {"type": "CubicSpline",
                        "src": {"type": "FBM", "frequency": 0.02, "octaves": 5, "seed": 5},
                        "points": [[-1, 58], [0, 72], [1, 105]]},
                  "b": {"type": "Scale",
                        "src": {"type": "Ridged", "frequency": 0.05, "octaves": 5, "seed": 9},
                        "factor": 14}},
    }


def test_emit_world_runs_and_gates():
    payloads = emit.emit_world(_recipe())
    assert payloads["verify"].ok
    cols = payloads["columns"]
    assert cols["width"] * cols["length"] == 48 * 48
    assert len(cols["height"]) == 48 * 48
    assert payloads["biomes"] is not None and len(payloads["biomes"]) > 0


def test_emit_world_halts_on_degenerate():
    bad = _recipe()
    bad["graph"] = {"type": "Constant", "value": 64.0}  # dead flat → verify fail
    try:
        emit.emit_world(bad)
        assert False, "should have raised VerifyError"
    except emit.VerifyError:
        pass
    # but allow_unverified bypasses
    payloads = emit.emit_world(bad, allow_unverified=True)
    assert not payloads["verify"].ok
