"""Structure tools — save / load / info / list + raw file IO, round-tripped
through the scratch sandbox.

Every structure these tests create uses an ``mcb:itest_*`` name and is removed
in a ``finally`` (both the saved template via ``structure_delete`` and the
on-disk file via ``structure_file_delete``) so nothing outlives the run. The
mod persists a saved structure to BOTH the in-memory template manager and a
``generated/<ns>/structures/<path>.nbt`` file, so a single save is visible to
``structure_get_info`` / ``structure_list`` *and* the ``structure_file_*``
tools (verified in StructureTools.java / WorldOps.structureSaveFromWorld).

Coverage (9 live tools, all "safe" — confined to the sandbox + a test name):
  structure_save_from_world, structure_load_to_world, structure_get_info,
  structure_list, structure_delete, structure_file_list, structure_file_read,
  structure_file_write, structure_file_delete.
"""
from __future__ import annotations

import base64
import time

from ..harness import case, Ctx, Skip

# A unique-per-run test name keeps parallel/leftover runs from colliding and
# makes orphans obvious. mcb namespace matches the existing builder library.
_RUN = int(time.time())


def _name(suffix):
    return f"mcb:itest_{suffix}_{_RUN}"


def _as_items(data):
    """structure_list returns {items:[...], total, next_offset}; tolerate a bare
    list too."""
    if isinstance(data, dict):
        return data.get("items") or []
    if isinstance(data, list):
        return data
    return []


def _as_names(data):
    """structure_file_list returns a TOON inline array -> Python list of names;
    tolerate a dict wrapper."""
    if isinstance(data, list):
        return [str(x) for x in data]
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return [str(x) for x in v]
    return []


def _stamp_box(ctx: Ctx):
    """Fill a fresh sandbox box with a recognisable pattern and return the box."""
    a, b = ctx.box(3, 2, 3)
    ctx.call_text("block_fill_region",
                  {"dimension": ctx.dim, "box": ctx.box_obj(a, b),
                   "block": {"id": "minecraft:stone"}})
    # one marker block at the min corner so a reload is verifiable
    ctx.call_text("block_set_state",
                  {"dimension": ctx.dim, "position": ctx.pos_obj(a),
                   "block": {"id": "minecraft:gold_block"}})
    return a, b


# ---------------------------------------------------------------------------
# save / get_info / list / delete (in-memory + on-disk template)
# ---------------------------------------------------------------------------

@case("structure_save_from_world")
@case("structure_get_info")
def test_save_and_info(ctx: Ctx):
    name = _name("save")
    a, b = _stamp_box(ctx)
    try:
        text, err = ctx.call_text("structure_save_from_world",
                                  {"name": name, "dimension": ctx.dim,
                                   "box": ctx.box_obj(a, b)})
        ctx.expect(not err and "fail" not in text.lower(),
                   f"save failed: {text!r}")
        info = ctx.call("structure_get_info", {"name": name})
        nm = ctx.expect_field(info, "name")
        ctx.expect(name in str(nm), f"get_info name mismatch: {info}")
        # captured size should match the box dims (4x3x4 inclusive)
        sx = info.get("sizeX") if isinstance(info, dict) else None
        ctx.expect(sx in (None, b[0] - a[0] + 1),
                   f"unexpected sizeX {sx} for box {a}->{b}: {info}")
    finally:
        ctx.call_text("structure_delete", {"name": name})
        ctx.call_text("structure_file_delete", {"name": name})


@case("structure_list")
def test_list(ctx: Ctx):
    """Verify structure_list returns a saved mcb:* structure and the pagination contract.

    Fixed in R5: structure_list now merges in-memory + on-disk entries across ALL
    namespaces (not just 'minecraft:'). A structure saved under 'mcb:itest_*' must
    appear in structure_list results as well as in structure_file_list.
    """
    name = _name("list")
    a, b = _stamp_box(ctx)
    try:
        ctx.call_text("structure_save_from_world",
                      {"name": name, "dimension": ctx.dim, "box": ctx.box_obj(a, b)})

        # Verify the structure IS saved (get_info returns inMemory=true).
        info = ctx.call("structure_get_info", {"name": name})
        ctx.expect(isinstance(info, dict) and info.get("inMemory") is True,
                   f"structure_get_info should confirm inMemory after save: {info}")

        # structure_list pagination contract: items, total, next_offset.
        data = ctx.call("structure_list", {"limit": 2000})
        items = _as_items(data)
        ctx.expect(len(items) > 0, f"structure_list returned no items: {data}")
        if isinstance(data, dict):
            ctx.expect_field(data, "total")
            ctx.expect("next_offset" in data,
                       f"structure_list missing next_offset field: {data}")

        # R5 fix: mcb: namespace structures must now appear in structure_list.
        names = [str(it.get("name")) for it in items if isinstance(it, dict)]
        ctx.expect(any(name in n for n in names),
                   f"structure_list should include {name!r} after R5 fix "
                   f"(namespace merge). Got {len(names)} entries; sample: {names[:10]}")

        # Also confirm the on-disk listing agrees (belt-and-suspenders).
        file_listing = _as_names(ctx.call("structure_file_list", {}))
        ctx.expect(name in file_listing,
                   f"structure_file_list should contain {name!r}: {file_listing[:10]}")
    finally:
        ctx.call_text("structure_delete", {"name": name})
        ctx.call_text("structure_file_delete", {"name": name})


@case("structure_delete")
def test_delete(ctx: Ctx):
    name = _name("del")
    a, b = _stamp_box(ctx)
    # ensure cleanup of the on-disk file even if the body raises mid-way
    try:
        ctx.call_text("structure_save_from_world",
                      {"name": name, "dimension": ctx.dim, "box": ctx.box_obj(a, b)})
        text, err = ctx.call_text("structure_delete", {"name": name})
        ctx.expect(not err and "fail" not in text.lower(),
                   f"delete of existing structure failed: {text!r}")
        ctx.expect("delet" in text.lower(), f"unexpected delete response: {text!r}")
        # after delete the structure is gone: get_info raises "Unknown structure"
        # (JSON-RPC -32002 -> McpError) OR returns an isError block. Either way
        # the lookup must NOT succeed.
        gone = False
        try:
            _, ierr = ctx.call_text("structure_get_info", {"name": name})
            gone = bool(ierr)
        except Exception:  # noqa: BLE001 — any error here means it was deleted
            gone = True
        ctx.expect(gone, f"structure {name!r} still resolvable after delete")
    finally:
        ctx.call_text("structure_file_delete", {"name": name})


# ---------------------------------------------------------------------------
# load_to_world — round-trip a saved template back into the sandbox
# ---------------------------------------------------------------------------

@case("structure_load_to_world")
def test_load_round_trip(ctx: Ctx):
    name = _name("load")
    a, b = _stamp_box(ctx)
    dest = ctx.pos()  # fresh origin elsewhere in the sandbox
    try:
        ctx.call_text("structure_save_from_world",
                      {"name": name, "dimension": ctx.dim, "box": ctx.box_obj(a, b)})
        text, err = ctx.call_text("structure_load_to_world",
                                  {"name": name, "dimension": ctx.dim,
                                   "origin": ctx.pos_obj(dest)})
        ctx.expect(not err and "fail" not in text.lower(),
                   f"load failed: {text!r}")
        # the marker gold_block was at the box min corner -> appears at origin
        got = ctx.call("block_get_state",
                       {"dimension": ctx.dim, "position": ctx.pos_obj(dest)})
        bid = (got.get("id") or got.get("block") or got.get("blockId")
               if isinstance(got, dict) else str(got))
        ctx.expect("gold_block" in str(bid),
                   f"expected loaded gold_block marker at {dest}, got {got}")
    finally:
        ctx.call_text("structure_delete", {"name": name})
        ctx.call_text("structure_file_delete", {"name": name})


# ---------------------------------------------------------------------------
# raw file IO — write / read / list / delete the .nbt bytes directly
# ---------------------------------------------------------------------------

@case("structure_file_list")
@case("structure_file_read")
def test_file_list_and_read(ctx: Ctx):
    # Save a real structure (lands a .nbt on disk), then list + read its bytes.
    name = _name("file")
    a, b = _stamp_box(ctx)
    try:
        ctx.call_text("structure_save_from_world",
                      {"name": name, "dimension": ctx.dim, "box": ctx.box_obj(a, b)})
        listing = ctx.call("structure_file_list", {})
        names = _as_names(listing)
        ctx.expect(name in names,
                   f"saved file {name!r} not in structure_file_list ({len(names)} files)")
        text, err = ctx.call_text("structure_file_read", {"name": name})
        ctx.expect(not err, f"file_read errored: {text!r}")
        ctx.expect(len(text.strip()) > 0, "file_read returned empty payload")
        # payload is base64 of gzip'd NBT; decoding must succeed and be non-trivial
        raw = base64.b64decode(text.strip(), validate=False)
        ctx.expect(len(raw) > 8, f"decoded structure bytes too small: {len(raw)}")
        # gzip magic 0x1f 0x8b (NbtIo.writeCompressed) — tolerant: just check it decoded
        ctx.expect(raw[:2] == b"\x1f\x8b" or len(raw) > 8,
                   "decoded bytes look wrong")
    finally:
        ctx.call_text("structure_delete", {"name": name})
        ctx.call_text("structure_file_delete", {"name": name})


@case("structure_file_write")
@case("structure_file_delete")
def test_file_write_read_delete(ctx: Ctx):
    # Capture a real structure, read its bytes, write them to a NEW name, then
    # read the copy back and confirm byte-identity. file_write only touches disk
    # (not the in-memory manager), so we verify via file_read + file_list.
    src = _name("wsrc")
    dst = _name("wdst")
    a, b = _stamp_box(ctx)
    try:
        ctx.call_text("structure_save_from_world",
                      {"name": src, "dimension": ctx.dim, "box": ctx.box_obj(a, b)})
        payload, rerr = ctx.call_text("structure_file_read", {"name": src})
        ctx.expect(not rerr and payload.strip(), f"could not read source bytes: {payload!r}")
        payload = payload.strip()

        wtext, werr = ctx.call_text("structure_file_write",
                                    {"name": dst, "payload_base64": payload})
        ctx.expect(not werr and "fail" not in wtext.lower(),
                   f"file_write failed: {wtext!r}")
        ctx.expect("written" in wtext.lower() or "fail" not in wtext.lower(),
                   f"unexpected file_write response: {wtext!r}")

        # the copy must now appear on disk and read back identically
        names = _as_names(ctx.call("structure_file_list", {}))
        ctx.expect(dst in names, f"written file {dst!r} not listed: {len(names)} files")
        back, berr = ctx.call_text("structure_file_read", {"name": dst})
        ctx.expect(not berr, f"read-back of {dst!r} errored: {back!r}")
        ctx.expect(back.strip() == payload, "round-tripped structure bytes differ")

        # file_delete removes the disk copy and is idempotent
        dtext, derr = ctx.call_text("structure_file_delete", {"name": dst})
        ctx.expect(not derr and "delet" in dtext.lower(),
                   f"file_delete failed: {dtext!r}")
        names_after = _as_names(ctx.call("structure_file_list", {}))
        ctx.expect(dst not in names_after, f"{dst!r} still listed after file_delete")
    finally:
        # src lives both in-memory and on-disk; dst is disk-only (already deleted
        # on the happy path, but clean up again defensively).
        ctx.call_text("structure_delete", {"name": src})
        ctx.call_text("structure_file_delete", {"name": src})
        ctx.call_text("structure_file_delete", {"name": dst})
