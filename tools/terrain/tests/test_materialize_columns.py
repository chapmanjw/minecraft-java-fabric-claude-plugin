"""block_fill_columns plan: schema correctness, mask-driven surfaces, verify gate."""
import numpy as np

from terrain import HeightField
from terrain.materialize import (MaterialSpec, Layer, TerrainLayers,
                                 to_columns_plan, to_voxel_model, resolve_surface)
from terrain import verify


def _hill(n=40):
    hf = HeightField(n, n, sea_level=62)
    hf.add_fbm(30, octaves=4, base_freq=0.04, seed=3)
    hf.add_fbm(8, octaves=3, base_freq=0.09, ridge=True, seed=5)
    return hf


def test_columns_plan_schema():
    hf = _hill()
    spec = MaterialSpec.natural(hf)
    plan = to_columns_plan(hf, spec, origin=(100, -200))
    n = hf.nx * hf.nz
    # required keys present
    for k in ("dimension", "origin", "width", "length", "floor_y", "palette",
              "stone_index", "height", "surface", "subsurface",
              "subsurface_depth", "sea_level", "water_index"):
        assert k in plan, f"missing {k}"
    # row-major arrays of the right length
    assert len(plan["height"]) == n
    assert len(plan["surface"]) == n
    assert len(plan["subsurface"]) == n
    # indices are valid into the palette
    psize = len(plan["palette"])
    assert 0 <= plan["stone_index"] < psize
    assert 0 <= plan["water_index"] < psize
    assert all(0 <= i < psize for i in plan["surface"])
    assert all(0 <= i < psize for i in plan["subsurface"])
    # floor below the lowest surface
    assert plan["floor_y"] < min(plan["height"])


def test_columns_rowmajor_matches_xi_length_zi():
    hf = HeightField(6, 4, sea_level=62)
    hf.h[:] = 64.0
    hf.h[2, 3] = 80.0
    spec = MaterialSpec.natural(hf)
    plan = to_columns_plan(hf, spec)
    # index xi*length + zi
    assert plan["height"][2 * 4 + 3] == 80
    assert plan["height"][0] == 64


def test_slant_puts_rock_on_steep_faces():
    # a steep ramp: slope well above the slant threshold
    hf = HeightField(30, 30, sea_level=62)
    hf.h = np.tile(np.arange(30.0)[:, None] * 3.0 + 50.0, (1, 30))  # ~72° slope
    spec = MaterialSpec.natural(hf, cliff_slope=50.0)
    surface, subsurf = resolve_surface(hf, spec)
    # the steep interior columns should be stone/rock, not grass
    interior = surface[5:25, 15]
    rock = sum(1 for b in interior if "stone" in b or "andesite" in b or "cobble" in b)
    assert rock >= len(interior) * 0.8, f"slant didn't rock the cliff: {set(interior)}"


def test_no_monoculture_in_surface_mix():
    hf = HeightField(50, 50, sea_level=62)
    hf.h[:] = 70.0  # flat → base mix only, but should still be a *mix*
    spec = MaterialSpec.natural(hf)
    surface, _ = resolve_surface(hf, spec)
    uniq = set(surface.reshape(-1).tolist())
    assert len(uniq) >= 2, f"surface is a monoculture: {uniq}"


def test_strata_passthrough():
    hf = _hill()
    spec = MaterialSpec.natural(hf)
    spec.strata = [("minecraft:red_sandstone", 4), ("minecraft:orange_terracotta", 3)]
    plan = to_columns_plan(hf, spec)
    assert "strata" in plan
    assert plan["strata"][0] == {"block": "minecraft:red_sandstone", "thickness": 4}


def test_verify_passes_good_terrain():
    hf = _hill()
    rep = verify.verify(hf)
    assert rep.ok, str(rep)


def test_verify_flags_flat_degenerate():
    hf = HeightField(40, 40, sea_level=62)
    hf.h[:] = 64.0  # dead flat: no relief
    rep = verify.verify(hf)
    assert not rep.ok
    names = {n for n, ok, _ in rep.failures()}
    assert "relief" in names or "not_degenerate" in names


def test_verify_flags_ziggurat():
    # stacked flat terraces with vertical walls between — the anti-pattern
    hf = HeightField(60, 60, sea_level=62)
    h = np.zeros((60, 60))
    for i, lo in enumerate(range(0, 60, 12)):
        h[lo:lo + 12, :] = 64 + i * 15   # flat tops, 15-block vertical jumps
    hf.h = h
    rep = verify.verify(hf)
    zig = [c for c in rep.checks if c[0] == "no_ziggurat"][0]
    assert not zig[1], f"ziggurat not detected: {zig}"


def test_verify_seam_detects_wall():
    h = np.full((40, 40), 64.0)
    h[20:, :] = 110.0  # 46-block cliff
    rep = verify.verify_seam(h, max_step=12)
    assert not rep.ok
    # and a blended ramp passes once the blend radius is wide enough for the
    # height delta (a 46-block delta needs a wider kernel than radius 8 to come
    # in under 12 blocks/cell — the blend radius must scale with the delta).
    from terrain import blend
    lab = np.zeros((40, 40), dtype=int)
    lab[20:, :] = 1
    blended = blend.box_blur_blend(lab, {0: np.full((40, 40), 64.0),
                                         1: np.full((40, 40), 110.0)}, radius=14)
    assert verify.verify_seam(blended, max_step=12).ok


def test_columns_surface_matches_voxel_top_layer_flat():
    """Design §11 gate: columns-vs-voxel round-trip. On a flat field with a
    single-block surface mix (so the dithered pick is deterministic across both
    code paths), the ``to_columns_plan`` surface index per column must name the
    same block as the *top* voxel layer of ``to_voxel_model`` at that column —
    the two materialisation paths agree on the visible surface."""
    hf = HeightField(8, 6, sea_level=40)        # sea well below the flat top
    hf.h[:] = 70.0
    surface_mix = {"minecraft:grass_block": 1.0}

    # columns path
    spec = MaterialSpec(layers=[], base=surface_mix, subsurface="minecraft:dirt")
    plan = to_columns_plan(hf, spec)
    w, l = plan["width"], plan["length"]
    col_surf = np.empty((w, l), dtype=object)
    for xi in range(w):
        for zi in range(l):
            col_surf[xi, zi] = plan["palette"][plan["surface"][xi * l + zi]]

    # voxel path: top block per column
    layers = TerrainLayers(surface=surface_mix, subsurface="minecraft:dirt",
                           cliff=None, beach=None)
    model, y_min = to_voxel_model(hf, layers)
    surf_y = np.rint(np.clip(hf.h, -63, 319)).astype(int)
    vox_top = np.empty((w, l), dtype=object)
    for xi in range(w):
        for zi in range(l):
            g_top = int(surf_y[xi, zi]) - y_min
            vox_top[xi, zi] = model.pal.block_id(int(model.g[xi, g_top, zi]))

    assert (col_surf == vox_top).all(), \
        f"columns {set(col_surf.reshape(-1))} != voxel top {set(vox_top.reshape(-1))}"
