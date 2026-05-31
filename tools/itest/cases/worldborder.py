"""Worldborder tools — read + mutate-then-restore the dimension world border.

The world border is **global** dimension state, so every mutating test follows the
same contract: snapshot the full border via ``worldborder_get``, push a distinct
test value, assert it took effect, then restore *every* field in a ``finally`` so
the run leaves the border exactly as it found it. No player is online, so a
transient border change harms nobody; transitions use ``time_seconds=0`` (or are
omitted) so the new value is readable immediately.

Live ``worldborder_get`` shape (overworld, observed):
    center_x, center_z, size, warning_blocks, warning_seconds,
    damage_per_block, safe_zone
"""
from __future__ import annotations

from ..harness import case, Ctx


# --- helpers ---------------------------------------------------------------

def _snapshot(ctx: Ctx) -> dict:
    """Read the full border and return it as a plain dict (asserts success)."""
    data = ctx.call("worldborder_get", {"dimension": ctx.dim})
    ctx.expect(isinstance(data, dict), f"worldborder_get returned non-dict: {data!r}")
    ctx.expect_field(data, "size")
    return data


def _restore(ctx: Ctx, snap: dict) -> None:
    """Best-effort restore of every border field from a snapshot."""
    if "size" in snap:
        ctx.call_text("worldborder_set_size",
                      {"dimension": ctx.dim, "size": snap["size"], "time_seconds": 0})
    if "center_x" in snap and "center_z" in snap:
        ctx.call_text("worldborder_set_center",
                      {"dimension": ctx.dim, "x": snap["center_x"], "z": snap["center_z"]})
    if "warning_blocks" in snap:
        ctx.call_text("worldborder_set_warning_blocks",
                      {"dimension": ctx.dim, "blocks": int(snap["warning_blocks"])})
    if "warning_seconds" in snap:
        ctx.call_text("worldborder_set_warning_time",
                      {"dimension": ctx.dim, "seconds": int(snap["warning_seconds"])})
    if "damage_per_block" in snap:
        ctx.call_text("worldborder_set_damage_amount",
                      {"dimension": ctx.dim, "amount": snap["damage_per_block"]})
    if "safe_zone" in snap:
        ctx.call_text("worldborder_set_damage_buffer",
                      {"dimension": ctx.dim, "buffer": snap["safe_zone"]})


def _num(v):
    """Coerce a TOON/text scalar to float for tolerant numeric comparison."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# --- read ------------------------------------------------------------------

@case("worldborder_get", level="safe")
def test_get(ctx: Ctx):
    data = _snapshot(ctx)
    # The live server reports these fields; assert the core ones are present.
    for key in ("center_x", "center_z", "size"):
        ctx.expect_field(data, key)
    ctx.expect(_num(data["size"]) is not None and _num(data["size"]) > 0,
               f"border size should be a positive number: {data['size']!r}")


# --- mutate-then-restore ---------------------------------------------------

@case("worldborder_set_size", level="global")
def test_set_size(ctx: Ctx):
    snap = _snapshot(ctx)
    try:
        target = 5000.0
        text, is_err = ctx.call_text("worldborder_set_size",
                                     {"dimension": ctx.dim, "size": target, "time_seconds": 0})
        ctx.expect(not is_err, f"set_size errored: {text}")
        after = _snapshot(ctx)
        ctx.expect(_num(after.get("size")) == target,
                   f"expected size {target}, got {after.get('size')!r}")
    finally:
        _restore(ctx, snap)


@case("worldborder_add_size", level="global")
def test_add_size(ctx: Ctx):
    snap = _snapshot(ctx)
    try:
        # Pin a known base so the delta is deterministic, then add.
        base = 4000.0
        ctx.call_text("worldborder_set_size",
                      {"dimension": ctx.dim, "size": base, "time_seconds": 0})
        delta = 1000.0
        text, is_err = ctx.call_text("worldborder_add_size",
                                     {"dimension": ctx.dim, "delta": delta, "time_seconds": 0})
        ctx.expect(not is_err, f"add_size errored: {text}")
        after = _snapshot(ctx)
        ctx.expect(_num(after.get("size")) == base + delta,
                   f"expected size {base + delta}, got {after.get('size')!r}")
    finally:
        _restore(ctx, snap)


@case("worldborder_set_center", level="global")
def test_set_center(ctx: Ctx):
    snap = _snapshot(ctx)
    try:
        cx, cz = 128.0, -256.0
        text, is_err = ctx.call_text("worldborder_set_center",
                                     {"dimension": ctx.dim, "x": cx, "z": cz})
        ctx.expect(not is_err, f"set_center errored: {text}")
        after = _snapshot(ctx)
        ctx.expect(_num(after.get("center_x")) == cx and _num(after.get("center_z")) == cz,
                   f"expected center ({cx},{cz}), got "
                   f"({after.get('center_x')!r},{after.get('center_z')!r})")
    finally:
        _restore(ctx, snap)


@case("worldborder_set_damage_amount", level="global")
def test_set_damage_amount(ctx: Ctx):
    snap = _snapshot(ctx)
    try:
        amount = 0.75
        text, is_err = ctx.call_text("worldborder_set_damage_amount",
                                     {"dimension": ctx.dim, "amount": amount})
        ctx.expect(not is_err, f"set_damage_amount errored: {text}")
        after = _snapshot(ctx)
        val = _num(after.get("damage_per_block"))
        ctx.expect(val is not None and abs(val - amount) < 1e-6,
                   f"expected damage_per_block {amount}, got {after.get('damage_per_block')!r}")
    finally:
        _restore(ctx, snap)


@case("worldborder_set_damage_buffer", level="global")
def test_set_damage_buffer(ctx: Ctx):
    snap = _snapshot(ctx)
    try:
        buffer = 12.0
        text, is_err = ctx.call_text("worldborder_set_damage_buffer",
                                     {"dimension": ctx.dim, "buffer": buffer})
        ctx.expect(not is_err, f"set_damage_buffer errored: {text}")
        after = _snapshot(ctx)
        val = _num(after.get("safe_zone"))
        ctx.expect(val is not None and abs(val - buffer) < 1e-6,
                   f"expected safe_zone {buffer}, got {after.get('safe_zone')!r}")
    finally:
        _restore(ctx, snap)


@case("worldborder_set_warning_blocks", level="global")
def test_set_warning_blocks(ctx: Ctx):
    snap = _snapshot(ctx)
    try:
        blocks = 17
        text, is_err = ctx.call_text("worldborder_set_warning_blocks",
                                     {"dimension": ctx.dim, "blocks": blocks})
        ctx.expect(not is_err, f"set_warning_blocks errored: {text}")
        after = _snapshot(ctx)
        ctx.expect(_num(after.get("warning_blocks")) == blocks,
                   f"expected warning_blocks {blocks}, got {after.get('warning_blocks')!r}")
    finally:
        _restore(ctx, snap)


@case("worldborder_set_warning_time", level="global")
def test_set_warning_time(ctx: Ctx):
    snap = _snapshot(ctx)
    try:
        seconds = 42
        text, is_err = ctx.call_text("worldborder_set_warning_time",
                                     {"dimension": ctx.dim, "seconds": seconds})
        ctx.expect(not is_err, f"set_warning_time errored: {text}")
        after = _snapshot(ctx)
        ctx.expect(_num(after.get("warning_seconds")) == seconds,
                   f"expected warning_seconds {seconds}, got {after.get('warning_seconds')!r}")
    finally:
        _restore(ctx, snap)
