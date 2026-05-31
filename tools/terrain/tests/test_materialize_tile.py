"""tile_columns_plan: cap-respecting split with exact, non-overlapping coverage.

The harness drives terrain through one ``block_fill_columns(_strata)`` call per
tile, so emit must pre-tile any plan over the server's column limit. These tests
pin the split invariant the contract relies on: every tile is within ``cap`` and
the tiles partition the original grid (no lost or doubled columns), with
``strata[]`` carried through unchanged.
"""
import numpy as np

from terrain.materialize import tile_columns_plan


def _make_plan(width, length, *, strata=False, ox=100, oz=-200):
    n = width * length
    plan = {
        "dimension": "minecraft:overworld",
        "origin": {"x": ox, "z": oz},
        "width": width, "length": length,
        "floor_y": -10,
        "palette": ["minecraft:stone", "minecraft:water", "minecraft:grass_block"],
        "stone_index": 0, "water_index": 1,
        "subsurface_depth": 3, "sea_level": 62,
        # distinct value per column so coverage mistakes are detectable
        "height": list(range(n)),
        "surface": [(i % 3) for i in range(n)],
        "subsurface": [0] * n,
    }
    if strata:
        plan["strata"] = [{"block": "minecraft:deepslate", "thickness": 5}]
    return plan


def _coverage(plan, tiles):
    """Map every (worldx, worldz) the tiles touch to its height; assert no
    overlap; return the dict so the caller can compare to the original."""
    seen = {}
    for t in tiles:
        ox, oz = t["origin"]["x"], t["origin"]["z"]
        tw, tl = t["width"], t["length"]
        assert len(t["height"]) == tw * tl
        assert len(t["surface"]) == tw * tl
        assert len(t["subsurface"]) == tw * tl
        for xi in range(tw):
            for zi in range(tl):
                key = (ox + xi, oz + zi)
                assert key not in seen, f"tiles overlap at {key}"
                seen[key] = t["height"][xi * tl + zi]
    return seen


def _original(plan):
    ox, oz = plan["origin"]["x"], plan["origin"]["z"]
    w, l = plan["width"], plan["length"]
    return {(ox + xi, oz + zi): plan["height"][xi * l + zi]
            for xi in range(w) for zi in range(l)}


def test_over_cap_splits_each_within_cap():
    plan = _make_plan(300, 300)              # 90,000 cols > 65,536
    tiles = tile_columns_plan(plan)
    assert len(tiles) > 1
    assert all(t["width"] * t["length"] <= 65536 for t in tiles)


def test_split_coverage_is_exact_and_disjoint():
    plan = _make_plan(300, 300)
    tiles = tile_columns_plan(plan)
    assert _coverage(plan, tiles) == _original(plan)


def test_splits_along_longer_axis_x():
    plan = _make_plan(1000, 80)              # long axis = X
    tiles = tile_columns_plan(plan)
    assert all(t["width"] * t["length"] <= 65536 for t in tiles)
    # X (width) was the axis subdivided; length stays whole
    assert all(t["length"] == 80 for t in tiles)
    assert _coverage(plan, tiles) == _original(plan)


def test_splits_along_longer_axis_z():
    plan = _make_plan(80, 1000)              # long axis = Z
    tiles = tile_columns_plan(plan)
    assert all(t["width"] * t["length"] <= 65536 for t in tiles)
    assert all(t["width"] == 80 for t in tiles)
    assert _coverage(plan, tiles) == _original(plan)


def test_under_cap_is_single_tile():
    plan = _make_plan(40, 40)
    tiles = tile_columns_plan(plan)
    assert len(tiles) == 1
    assert tiles[0]["width"] == 40 and tiles[0]["length"] == 40
    assert _coverage(plan, tiles) == _original(plan)


def test_small_cap_tiles_both_axes():
    plan = _make_plan(300, 300)
    tiles = tile_columns_plan(plan, cap=10000)
    assert all(t["width"] * t["length"] <= 10000 for t in tiles)
    assert _coverage(plan, tiles) == _original(plan)


def test_strata_carried_through_each_tile():
    plan = _make_plan(300, 300, strata=True)
    tiles = tile_columns_plan(plan)
    assert len(tiles) > 1
    for t in tiles:
        assert t["strata"] == plan["strata"]
        # the static plan keys survive too
        assert t["dimension"] == "minecraft:overworld"
        assert t["palette"] == plan["palette"]
        assert t["stone_index"] == 0 and t["water_index"] == 1


def test_surface_subsurface_follow_the_same_slicing():
    # surface index cycles 0,1,2 row-major; assert a tile's surface matches the
    # original cells it claims (slicing the right array region, not the wrong one)
    plan = _make_plan(200, 400)
    l = plan["length"]
    tiles = tile_columns_plan(plan)
    for t in tiles:
        ox, oz = t["origin"]["x"], t["origin"]["z"]
        bx, bz = ox - plan["origin"]["x"], oz - plan["origin"]["z"]
        tw, tl = t["width"], t["length"]
        for xi in range(tw):
            for zi in range(tl):
                orig_idx = (bx + xi) * l + (bz + zi)
                assert t["surface"][xi * tl + zi] == plan["surface"][orig_idx]
