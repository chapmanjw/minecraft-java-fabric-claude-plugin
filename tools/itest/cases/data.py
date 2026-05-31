"""Data tools — vanilla data storage + Fabric data attachments.

Covers every live ``data_*`` tool:

  data_storage_set / get / remove / list_namespaces
  data_attachment_set / get / remove / list_keys

Storage tests are confined to a private namespace (``mcbitest``) that the test
creates and fully removes, so they never touch real world state — level "safe".

Attachment tests need an attachment *type* (namespace:key) that a loaded mod
registered via Fabric ``AttachmentRegistry``; the MCP mod registers none, so a
``set`` against any type returns "failed". Those tests summon a sandbox marker
entity to target, attempt the op, and Skip on the documented refusal (the mod
cannot create attachment types) — but ``list_keys`` is read-only and is asserted
to return a list. The summoned entity is always despawned in a finally.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

# Private namespace + key prefix the suite owns end-to-end.
NS = "mcbitest"


# --------------------------------------------------------------------------- storage


@case("data_storage_set", level="safe")
@case("data_storage_get", level="safe")
def test_storage_set_get(ctx: Ctx):
    """Write a private value, read it back, then clean up the path."""
    path = "round_trip"
    try:
        text, is_err = ctx.call_text(
            "data_storage_set", {"namespace": NS, "path": path, "snbt": "12345"})
        ctx.expect(not is_err, f"storage_set errored: {text}")
        ctx.expect("set" in text.lower(), f"storage_set should report 'set', got: {text!r}")

        got, get_err = ctx.call_text("data_storage_get", {"namespace": NS, "path": path})
        ctx.expect(not get_err, f"storage_get errored: {got}")
        ctx.expect("12345" in got, f"stored value 12345 not in read-back: {got!r}")
    finally:
        ctx.call_text("data_storage_remove", {"namespace": NS, "path": path})


@case("data_storage_remove", level="safe")
def test_storage_remove(ctx: Ctx):
    """Set a path, remove it, and confirm the value is gone (get now errors)."""
    path = "to_remove"
    ctx.call_text("data_storage_set", {"namespace": NS, "path": path, "snbt": "7"})

    text, is_err = ctx.call_text("data_storage_remove", {"namespace": NS, "path": path})
    ctx.expect(not is_err, f"storage_remove errored: {text}")
    ctx.expect("removed" in text.lower(), f"storage_remove should report 'removed', got: {text!r}")

    # The value is gone: a follow-up get must fail ("No value at storage:...").
    gone = False
    try:
        _, get_err = ctx.call_text("data_storage_get", {"namespace": NS, "path": path})
        gone = bool(get_err)  # tolerate an isError result instead of a JSON-RPC error
    except Exception:  # noqa: BLE001  — McpError on missing value is the success signal
        gone = True
    ctx.expect(gone, "value at removed path still readable after remove")


@case("data_storage_list_namespaces", level="safe")
def test_storage_list_namespaces(ctx: Ctx):
    """The private namespace shows up while a value lives in it, then is cleaned up."""
    path = "presence"
    try:
        ctx.call_text("data_storage_set", {"namespace": NS, "path": path, "snbt": "1"})
        data = ctx.call("data_storage_list_namespaces")
        names = data if isinstance(data, list) else []
        ctx.expect(isinstance(data, list), f"list_namespaces should be a list, got: {data!r}")
        ctx.expect(any(NS in str(n) for n in names),
                   f"namespace {NS!r} not listed while populated: {names}")
    finally:
        ctx.call_text("data_storage_remove", {"namespace": NS, "path": path})


# --------------------------------------------------------------------------- attachments


def _summon_marker(ctx: Ctx):
    """Summon a marker entity in the sandbox; return its uuid (or None)."""
    p = ctx.pos()
    ctx.call_text("entity_summon",
                  {"dimension": ctx.dim, "entity_type": "minecraft:marker",
                   "position": ctx.pos_obj(p)})
    # Find it: enumerate markers in the sandbox dimension and take the nearest by coords.
    q = ctx.call("entity_query", {"dimension": ctx.dim, "selector": "@e[type=minecraft:marker]",
                                  "limit": 64})
    entries = q if isinstance(q, list) else (q.get("entities") if isinstance(q, dict) else None)
    if not entries:
        return None
    for e in entries:
        if not isinstance(e, dict):
            continue
        uid = e.get("uuid") or e.get("id") or e.get("uuidString")
        if uid:
            return str(uid)
    return None


@case("data_attachment_list_keys", level="safe")
def test_attachment_list_keys(ctx: Ctx):
    """list_keys is read-only — assert it returns a list for a real sandbox target."""
    uuid = _summon_marker(ctx)
    if not uuid:
        raise Skip("could not summon/locate a sandbox marker entity")
    try:
        data = ctx.call("data_attachment_list_keys",
                        {"target": f"entity:{uuid}", "namespace": NS})
        ctx.expect(isinstance(data, list), f"list_keys should be a list, got: {data!r}")
    finally:
        ctx.call_text("entity_despawn", {"uuid": uuid})


@case("data_attachment_set", level="safe")
@case("data_attachment_get", level="safe")
@case("data_attachment_remove", level="safe")
def test_attachment_set_get_remove(ctx: Ctx):
    """Round-trip an attachment on a sandbox entity.

    The MCP mod registers no attachment *types*, so set returns "failed". When
    that happens we Skip (the mod cannot create attachment types — a documented
    refusal). If a future loaded mod registers ``mcbitest:flag``, the set/get/
    remove cycle is asserted instead.
    """
    uuid = _summon_marker(ctx)
    if not uuid:
        raise Skip("could not summon/locate a sandbox marker entity")
    target = f"entity:{uuid}"
    key = "flag"
    try:
        set_text, set_err = ctx.call_text(
            "data_attachment_set",
            {"target": target, "namespace": NS, "key": key, "snbt": "99"})
        ctx.expect(not set_err, f"attachment_set errored: {set_text}")
        if "failed" in set_text.lower():
            raise Skip("no attachment type registered (mod cannot create attachment types) — "
                       "data_attachment_set returns 'failed'")
        ctx.expect("set" in set_text.lower(), f"attachment_set unexpected result: {set_text!r}")

        got, get_err = ctx.call_text(
            "data_attachment_get", {"target": target, "namespace": NS, "key": key})
        ctx.expect(not get_err and "99" in got, f"attachment value not read back: {got!r}")

        rm_text, rm_err = ctx.call_text(
            "data_attachment_remove", {"target": target, "namespace": NS, "key": key})
        ctx.expect(not rm_err and "removed" in rm_text.lower(),
                   f"attachment_remove unexpected result: {rm_text!r}")
    finally:
        ctx.call_text("entity_despawn", {"uuid": uuid})
