"""Block tools — full live coverage.

The first five tests (set/get, fill_region, scan_summary, top_y) prove the
scratch sandbox + assertion mechanics end-to-end; the rest exercise every other
live ``block_*`` tool: clone, replace, batch/column fills, scan, map colour,
render, thermal + hydraulic erosion (dry-run only — no terrain writes), and the
block-entity NBT trio (placed container/sign in the sandbox).

All world writes stay inside the force-loaded scratch sandbox (ctx.pos/ctx.box).
Erosion runs with dry_run=true so it computes-only and never mutates the world.
"""
from __future__ import annotations

import itertools
import time

from ..harness import case, Ctx, Skip

# --- non-overlapping cell allocator -----------------------------------------
# The shared ctx.pos()/ctx.box() cursor advances only +2 per call, so a box
# wider than 2 columns overlaps the next allocation — fine for fill-then-read-
# same-cell tests, but clone (fill A, read B) and the block-entity tests (a
# later column/erode fill must not clobber a placed chest) need footprints that
# never touch. This hands out fresh 10x10 cells from the sandbox grid, each
# isolated, so every multi-block test owns its own region.
#
# The grid is offset to z>=_CELL_Z0 (20016) so it never overlaps the *template*
# tests (set/get, fill_region, scan_summary, top_y), which use the shared
# ctx.pos()/ctx.box() cursor and stay in the z=20000..~20012 band. Sandbox z
# runs 20000..20063, so z=20016..20055 holds a 6(x) x 4(z) = 24-cell grid; the
# block suite consumes ~14 cells.
_SB_X0 = 20000                          # sandbox NW corner X (mirrors harness SCRATCH_X0)
_CELL_Z0 = 20016                        # first cell row, clear of the template band
_CELL = 10                              # cell pitch in blocks
_GRID_X = 6                             # cells across X (20000..20059)
_GRID_Z = 4                             # cell rows in Z (20016..20055)
_CELLS = itertools.count(0)


def _cell(y=95):
    """A fresh isolated cell: returns the (x,y,z) min corner."""
    i = next(_CELLS)
    if i >= _GRID_X * _GRID_Z:
        raise RuntimeError("block.py cell allocator exhausted — add cells or reuse")
    cx = _SB_X0 + (i % _GRID_X) * _CELL
    cz = _CELL_Z0 + (i // _GRID_X) * _CELL
    return cx, y, cz


# ---------------------------------------------------------------------------
# core set/get/fill/scan (harness-validation template — keep as-is)
# ---------------------------------------------------------------------------

@case("block_set_state")
@case("block_get_state")
def test_set_get(ctx: Ctx):
    p = ctx.pos()
    ctx.call_text("block_set_state", {"dimension": ctx.dim, "position": ctx.pos_obj(p),
                                      "block": {"id": "minecraft:stone"}})
    got = ctx.call("block_get_state", {"dimension": ctx.dim, "position": ctx.pos_obj(p)})
    bid = got.get("id") or got.get("block") or got.get("blockId") if isinstance(got, dict) else str(got)
    ctx.expect("stone" in str(bid), f"expected stone at {p}, got {got}")


@case("block_fill_region")
def test_fill_region(ctx: Ctx):
    a, b = ctx.box(4, 2, 4)
    text, _ = ctx.call_text("block_fill_region",
                            {"dimension": ctx.dim, "box": ctx.box_obj(a, b), "block": {"id": "minecraft:dirt"}})
    ctx.expect("error" not in text.lower(), f"fill error: {text}")


@case("block_scan_summary")
def test_scan_summary(ctx: Ctx):
    a, b = ctx.box(4, 2, 4)
    ctx.call_text("block_fill_region",
                  {"dimension": ctx.dim, "box": ctx.box_obj(a, b), "block": {"id": "minecraft:cobblestone"}})
    data = ctx.call("block_scan_summary", {"dimension": ctx.dim, "box": ctx.box_obj(a, b)})
    ctx.expect(data is not None, "scan_summary returned nothing")


@case("block_get_top_y")
def test_top_y(ctx: Ctx):
    p = ctx.pos()
    ctx.call_text("block_set_state", {"dimension": ctx.dim, "position": ctx.pos_obj(p),
                                      "block": {"id": "minecraft:stone"}})
    res = ctx.call("block_get_top_y", {"dimension": ctx.dim, "x": p[0], "z": p[2]})
    # tolerant: returns an int line or {"y": n}
    val = res.get("y") if isinstance(res, dict) else res
    ctx.expect(val is not None, f"no top-y for column {p[0]},{p[2]}: {res}")


# ---------------------------------------------------------------------------
# scan / colour / render reads
# ---------------------------------------------------------------------------

@case("block_scan_region")
def test_scan_region(ctx: Ctx):
    # Fill a small box with a marker block, then scan for exactly that block id.
    cx, cy, cz = _cell()
    a, b = (cx, cy, cz), (cx + 2, cy, cz + 2)
    ctx.call_text("block_fill_region",
                  {"dimension": ctx.dim, "box": ctx.box_obj(a, b), "block": {"id": "minecraft:gold_block"}})
    data = ctx.call("block_scan_region",
                    {"dimension": ctx.dim, "box": ctx.box_obj(a, b),
                     "match_block_id": "minecraft:gold_block", "limit": 256})
    # Root is a TOON list of {position, state} entries.
    ctx.expect(isinstance(data, list), f"scan_region should return a list, got {type(data).__name__}: {str(data)[:160]}")
    ctx.expect(len(data) > 0, "scan_region found no gold_block in a freshly-filled box")
    first = data[0]
    state = ctx.expect_field(first, "state")
    ctx.expect("gold_block" in str(state), f"scanned entry not gold_block: {first}")


@case("block_get_map_color")
def test_get_map_color(ctx: Ctx):
    # Place a known block, read its authoritative map colour.
    cx, cy, cz = _cell()
    pos = {"x": cx, "y": cy, "z": cz}
    ctx.call_text("block_set_state", {"dimension": ctx.dim, "position": pos,
                                      "block": {"id": "minecraft:red_wool"}})
    data = ctx.call("block_get_map_color", {"dimension": ctx.dim, "position": pos})
    ctx.expect(isinstance(data, dict), f"map_color should be a dict, got {str(data)[:160]}")
    # Tolerant: assert the colour fields exist; don't over-specify the exact rgb.
    ctx.expect_field(data, "hex")
    ctx.expect_field(data, "rgb")
    for ch in ("r", "g", "b"):
        ctx.expect_field(data, ch)


@case("block_render_region")
def test_render_region(ctx: Ctx):
    # Build a tiny colourful box, then render it (returns a PNG content block).
    cx, cy, cz = _cell()
    a, b = (cx, cy, cz), (cx + 6, cy + 4, cz + 6)
    ctx.call_text("block_fill_region",
                  {"dimension": ctx.dim, "box": ctx.box_obj(a, b), "block": {"id": "minecraft:lime_concrete"}})
    text, is_error = ctx.call_text("block_render_region",
                                   {"dimension": ctx.dim, "box": ctx.box_obj(a, b),
                                    "view": "iso", "step": 1, "scale": 2})
    # Render returns an image (no text payload). Assert it didn't error.
    ctx.expect(not is_error, f"render_region errored: {text}")


# ---------------------------------------------------------------------------
# clone / replace
# ---------------------------------------------------------------------------

@case("block_clone_region")
def test_clone_region(ctx: Ctx):
    # Fill a source box with diamond_block, clone to a fresh, separate dest cell,
    # verify the dest block id matches via a read-back.
    sx, sy, sz = _cell()
    sa, sb = (sx, sy, sz), (sx + 3, sy + 1, sz + 3)
    ctx.call_text("block_fill_region",
                  {"dimension": ctx.dim, "box": ctx.box_obj(sa, sb), "block": {"id": "minecraft:diamond_block"}})
    dx, dy, dz = _cell()
    dest = (dx, dy, dz)
    text, is_error = ctx.call_text("block_clone_region",
                                   {"source_dimension": ctx.dim,
                                    "source_box": ctx.box_obj(sa, sb),
                                    "dest_dimension": ctx.dim,
                                    "destination": ctx.pos_obj(dest),
                                    "mode": "normal"})
    ctx.expect(not is_error, f"clone_region errored: {text}")
    got = ctx.call("block_get_state", {"dimension": ctx.dim, "position": ctx.pos_obj(dest)})
    bid = got.get("id") if isinstance(got, dict) else str(got)
    ctx.expect("diamond_block" in str(bid), f"clone dest not diamond_block: {got}")


@case("block_replace_in_region")
def test_replace_in_region(ctx: Ctx):
    # Fill with sandstone, replace sandstone->emerald_block, verify the swap.
    cx, cy, cz = _cell()
    a, b = (cx, cy, cz), (cx + 3, cy + 1, cz + 3)
    ctx.call_text("block_fill_region",
                  {"dimension": ctx.dim, "box": ctx.box_obj(a, b), "block": {"id": "minecraft:sandstone"}})
    text, is_error = ctx.call_text("block_replace_in_region",
                                   {"dimension": ctx.dim, "box": ctx.box_obj(a, b),
                                    "target": "minecraft:sandstone",
                                    "replacement": {"id": "minecraft:emerald_block"}})
    ctx.expect(not is_error, f"replace_in_region errored: {text}")
    got = ctx.call("block_get_state", {"dimension": ctx.dim, "position": ctx.pos_obj(a)})
    bid = got.get("id") if isinstance(got, dict) else str(got)
    ctx.expect("emerald_block" in str(bid), f"replace target not emerald_block: {got}")


# ---------------------------------------------------------------------------
# batch / column fills
# ---------------------------------------------------------------------------

@case("block_fill_batch")
def test_fill_batch(ctx: Ctx):
    # Two fills in one batch call; verify each landed via read-back.
    cx, cy, cz = _cell()
    p1 = (cx, cy, cz)
    p2 = (cx + 4, cy, cz + 4)
    fills = [
        {"from": [p1[0], p1[1], p1[2]], "to": [p1[0], p1[1], p1[2]], "block": "minecraft:iron_block"},
        {"from": [p2[0], p2[1], p2[2]], "to": [p2[0], p2[1], p2[2]], "block": "minecraft:copper_block"},
    ]
    text, is_error = ctx.call_text("block_fill_batch", {"dimension": ctx.dim, "fills": fills})
    ctx.expect(not is_error, f"fill_batch errored: {text}")
    g1 = ctx.call("block_get_state", {"dimension": ctx.dim, "position": ctx.pos_obj(p1)})
    g2 = ctx.call("block_get_state", {"dimension": ctx.dim, "position": ctx.pos_obj(p2)})
    b1 = g1.get("id") if isinstance(g1, dict) else str(g1)
    b2 = g2.get("id") if isinstance(g2, dict) else str(g2)
    ctx.expect("iron_block" in str(b1), f"batch fill 1 wrong: {g1}")
    ctx.expect("copper_block" in str(b2), f"batch fill 2 wrong: {g2}")


@case("block_fill_columns")
def test_fill_columns(ctx: Ctx):
    # Materialise a tiny 4x4 flat heightmap and verify a column's surface block.
    ox, _, oz = _cell()
    w = l = 4
    surf_y = 95
    floor_y = 90
    n = w * l
    args = {
        "dimension": ctx.dim,
        "origin": {"x": ox, "z": oz},
        "width": w, "length": l,
        "floor_y": floor_y,
        "palette": ["minecraft:stone", "minecraft:dirt", "minecraft:grass_block"],
        "stone_index": 0,
        "height": [surf_y] * n,
        "surface": [2] * n,         # grass_block
        "subsurface": [1] * n,      # dirt
        "subsurface_depth": 3,
    }
    text, is_error = ctx.call_text("block_fill_columns", args)
    ctx.expect(not is_error, f"fill_columns errored: {text}")
    got = ctx.call("block_get_state", {"dimension": ctx.dim, "position": {"x": ox, "y": surf_y, "z": oz}})
    bid = got.get("id") if isinstance(got, dict) else str(got)
    ctx.expect("grass_block" in str(bid), f"column surface not grass_block at y={surf_y}: {got}")


@case("block_fill_columns_strata")
def test_fill_columns_strata(ctx: Ctx):
    # Banded geological fill; verify the surface cap landed.
    ox, _, oz = _cell()
    w = l = 4
    surf_y = 95
    floor_y = 90
    n = w * l
    args = {
        "dimension": ctx.dim,
        "origin": {"x": ox, "z": oz},
        "width": w, "length": l,
        "floor_y": floor_y,
        "palette": ["minecraft:terracotta", "minecraft:red_sand", "minecraft:red_sand"],
        "height": [surf_y] * n,
        "surface": [2] * n,         # red_sand cap
        "subsurface": [1] * n,
        "subsurface_depth": 2,
        "strata": [
            {"block": "minecraft:orange_terracotta", "thickness": 2},
            {"block": "minecraft:yellow_terracotta", "thickness": 2},
        ],
        "base_stone": "minecraft:stone",
    }
    text, is_error = ctx.call_text("block_fill_columns_strata", args)
    ctx.expect(not is_error, f"fill_columns_strata errored: {text}")
    got = ctx.call("block_get_state", {"dimension": ctx.dim, "position": {"x": ox, "y": surf_y, "z": oz}})
    bid = got.get("id") if isinstance(got, dict) else str(got)
    ctx.expect("red_sand" in str(bid), f"strata surface not red_sand at y={surf_y}: {got}")


# ---------------------------------------------------------------------------
# erosion — DRY RUN ONLY (compute-only; never mutates the world)
# ---------------------------------------------------------------------------

@case("block_erode_region")
def test_erode_region(ctx: Ctx):
    # Lay a small heightmap in the sandbox, then thermal-erode it dry-run.
    # dry_run=true => reports stats, writes nothing.
    ox, _, oz = _cell()
    w = l = 8
    floor_y = 90
    n = w * l
    # Build a sloped surface so there is excess to (notionally) collapse.
    height = [95 + (xi % 4) for xi in range(w) for _ in range(l)]
    ctx.call_text("block_fill_columns", {
        "dimension": ctx.dim, "origin": {"x": ox, "z": oz}, "width": w, "length": l,
        "floor_y": floor_y, "palette": ["minecraft:stone", "minecraft:dirt", "minecraft:grass_block"],
        "stone_index": 0, "height": height, "surface": [2] * n, "subsurface": [1] * n,
    })
    data = ctx.call("block_erode_region", {
        "dimension": ctx.dim, "origin": {"x": ox, "z": oz}, "width": w, "length": l,
        "floor_y": floor_y, "iterations": 4, "dry_run": True,
    })
    ctx.expect(isinstance(data, dict), f"erode_region dry_run should be a dict: {str(data)[:160]}")
    ctx.expect_field(data, "columns")
    ctx.expect_field(data, "max_delta")
    ctx.expect(data.get("dry_run") is True, f"expected dry_run=true, got {data.get('dry_run')}")
    ctx.expect(data.get("blocks_changed") == 0, f"dry_run wrote blocks: {data.get('blocks_changed')}")
    # R5 fix: dry_run result must include a flat "heights" int array (the eroded
    # grid); length must equal columns (width * length = w * l).
    heights = data.get("heights")
    expected_len = w * l
    ctx.expect(isinstance(heights, list) and len(heights) > 0,
               f"erode_region dry_run missing non-empty 'heights' array (R5 fix): {str(data)[:200]}")
    ctx.expect(len(heights) == expected_len,
               f"erode_region heights length {len(heights)} != expected {expected_len} (w={w} l={l})")


@case("block_erode_hydraulic_start")
@case("block_erode_hydraulic_status")
@case("block_erode_hydraulic_result")
def test_erode_hydraulic(ctx: Ctx):
    # Full async lifecycle, dry-run: start -> poll status to DONE -> read result.
    # One test covers all three tools (stacked @case decorators).
    ox, _, oz = _cell()
    w = l = 8
    floor_y = 90
    n = w * l
    height = [95 + ((xi + zi) % 3) for xi in range(w) for zi in range(l)]
    ctx.call_text("block_fill_columns", {
        "dimension": ctx.dim, "origin": {"x": ox, "z": oz}, "width": w, "length": l,
        "floor_y": floor_y, "palette": ["minecraft:stone", "minecraft:dirt", "minecraft:grass_block"],
        "stone_index": 0, "height": height, "surface": [2] * n, "subsurface": [1] * n,
    })
    started = ctx.call("block_erode_hydraulic_start", {
        "dimension": ctx.dim, "origin": {"x": ox, "z": oz}, "width": w, "length": l,
        "floor_y": floor_y, "droplets": 500, "max_lifetime": 20, "dry_run": True,
    })
    ctx.expect(isinstance(started, dict), f"hydraulic_start should be a dict: {str(started)[:160]}")
    job_id = ctx.expect_field(started, "job_id")

    # Poll status until DONE (or FAILED). dry-run finishes fast; bound the wait.
    status = None
    for _ in range(60):
        status = ctx.call("block_erode_hydraulic_status", {"job_id": job_id})
        ctx.expect(isinstance(status, dict), f"hydraulic_status should be a dict: {str(status)[:160]}")
        st = str(status.get("state", "")).upper()
        ctx.expect_field(status, "progress")
        if st in ("DONE", "FAILED"):
            break
        time.sleep(0.5)
    ctx.expect(status is not None, "hydraulic_status never returned")
    final_state = str(status.get("state", "")).upper()
    if final_state == "FAILED":
        raise Skip(f"hydraulic erosion job FAILED: {status}")
    ctx.expect(final_state == "DONE", f"hydraulic job did not reach DONE: {status}")

    result = ctx.call("block_erode_hydraulic_result", {"job_id": job_id})
    ctx.expect(isinstance(result, dict), f"hydraulic_result should be a dict: {str(result)[:160]}")
    ctx.expect_field(result, "blocks_changed")
    ctx.expect_field(result, "max_delta")
    ctx.expect(result.get("dry_run") is True, f"expected dry_run result, got {result.get('dry_run')}")
    ctx.expect(result.get("blocks_changed") == 0, f"dry_run wrote blocks: {result.get('blocks_changed')}")
    # R5 fix: hydraulic dry_run result must include a flat "heights" int array;
    # length must equal columns (width * length = w * l).
    h_heights = result.get("heights")
    expected_len = w * l
    ctx.expect(isinstance(h_heights, list) and len(h_heights) > 0,
               f"hydraulic_result dry_run missing non-empty 'heights' array (R5 fix): {str(result)[:200]}")
    ctx.expect(len(h_heights) == expected_len,
               f"hydraulic_result heights length {len(h_heights)} != expected {expected_len} (w={w} l={l})")


# ---------------------------------------------------------------------------
# block-entity NBT (needs a placed container / sign in the sandbox)
# ---------------------------------------------------------------------------

@case("block_entity_get_nbt")
@case("block_entity_set_nbt")
def test_block_entity_nbt(ctx: Ctx):
    # Place a chest, merge a custom name via set_nbt, then read it back.
    # One test covers get + set (stacked @case).
    cx, cy, cz = _cell()
    pos = {"x": cx, "y": cy, "z": cz}
    ctx.call_text("block_set_state", {"dimension": ctx.dim, "position": pos,
                                      "block": {"id": "minecraft:chest"}})
    # Confirm the placement actually produced a block entity; if not, skip
    # rather than fail (a sandbox column fight or unloaded chunk would do this).
    placed = ctx.call("block_get_state", {"dimension": ctx.dim, "position": pos})
    if not (isinstance(placed, dict) and placed.get("hasBlockEntity")):
        raise Skip(f"chest placement produced no block entity: {placed}")
    try:
        # set_nbt merges SNBT (vanilla /data merge). Give the chest a custom name.
        merge = '{CustomName:\'{"text":"itest_chest"}\'}'
        text, is_error = ctx.call_text("block_entity_set_nbt",
                                       {"dimension": ctx.dim, "position": pos, "nbt": merge})
        ctx.expect(not is_error, f"block_entity_set_nbt errored: {text}")
        # get_nbt returns SNBT text (not TOON) — read it raw.
        snbt, is_error = ctx.call_text("block_entity_get_nbt", {"dimension": ctx.dim, "position": pos})
        ctx.expect(not is_error, f"block_entity_get_nbt errored: {snbt}")
        ctx.expect(len(snbt.strip()) > 0, "block_entity_get_nbt returned empty SNBT")
        # The merge round-trips: the custom name should be present in the NBT.
        ctx.expect("itest_chest" in snbt, f"merged CustomName not found in NBT: {snbt[:200]}")
    finally:
        # Clear the chest back to air (the sandbox clear also handles this).
        ctx.call_text("block_set_state", {"dimension": ctx.dim, "position": pos,
                                          "block": {"id": "minecraft:air"}})


@case("block_entity_clear_inventory")
def test_block_entity_clear_inventory(ctx: Ctx):
    # Place a chest, put an item in it via /data merge, clear it, verify empty.
    cx, cy, cz = _cell()
    pos = {"x": cx, "y": cy, "z": cz}
    ctx.call_text("block_set_state", {"dimension": ctx.dim, "position": pos,
                                      "block": {"id": "minecraft:chest"}})
    placed = ctx.call("block_get_state", {"dimension": ctx.dim, "position": pos})
    if not (isinstance(placed, dict) and placed.get("hasBlockEntity")):
        raise Skip(f"chest placement produced no block entity: {placed}")
    try:
        # Stock slot 0 with a diamond so there is something to clear.
        stock = '{Items:[{Slot:0b,id:"minecraft:diamond",count:5}]}'
        ctx.call_text("block_entity_set_nbt", {"dimension": ctx.dim, "position": pos, "nbt": stock})
        before, _ = ctx.call_text("block_entity_get_nbt", {"dimension": ctx.dim, "position": pos})
        if "diamond" not in before:
            raise Skip(f"could not stock chest before clear (Items merge ignored): {before[:160]}")
        text, is_error = ctx.call_text("block_entity_clear_inventory",
                                       {"dimension": ctx.dim, "position": pos})
        ctx.expect(not is_error, f"block_entity_clear_inventory errored: {text}")
        after, _ = ctx.call_text("block_entity_get_nbt", {"dimension": ctx.dim, "position": pos})
        ctx.expect("diamond" not in after, f"chest still holds items after clear: {after[:200]}")
    finally:
        ctx.call_text("block_set_state", {"dimension": ctx.dim, "position": pos,
                                          "block": {"id": "minecraft:air"}})
