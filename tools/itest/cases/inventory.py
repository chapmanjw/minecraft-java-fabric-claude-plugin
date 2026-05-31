"""Inventory / container tools — set/get/count/swap/clear on a block container.

Every test stamps a fresh chest into the scratch sandbox (via block_set_state),
addresses it with a ``block:<dim>:<x>:<y>:<z>`` target string, exercises the
tool, and asserts the side effect by reading the container back. The chest's
slots are cleared in ``finally`` (the sandbox is also aired-out at run end, but
the task contract asks for explicit cleanup).

All five inventory_* tools are sandbox-confined => level "safe".

Response shapes (from InventoryTools.java / PlayerOps.java):
  inventory_get          -> TOON {size:int, slots:[itemStack...]} (one per slot,
                            empty slots included as air/empty stacks)
  inventory_set_slot     -> text "set" | "failed"
  inventory_clear_slot   -> text "cleared" | "failed"
  inventory_swap_slots   -> text "swapped" | "failed"
  inventory_count_items  -> text integer (TOTAL item count across the container)

A non-container target raises a JSON-RPC error (-32002 Container not found),
surfaced by the client as McpError.
"""
from __future__ import annotations

from ..harness import case, Ctx


# --- helpers ---------------------------------------------------------------

def _chest_target(ctx: Ctx, p):
    """Place a chest at sandbox pos p and return its inventory target string."""
    ctx.call_text("block_set_state",
                  {"dimension": ctx.dim, "position": ctx.pos_obj(p),
                   "block": {"id": "minecraft:chest"}})
    return f"block:{ctx.dim}:{p[0]}:{p[1]}:{p[2]}"


def _clear_chest(ctx: Ctx, p):
    """Tear the chest back down to air — cleanup that outlives a slot clear."""
    try:
        ctx.call_text("block_set_state",
                      {"dimension": ctx.dim, "position": ctx.pos_obj(p),
                       "block": {"id": "minecraft:air"}})
    except Exception:  # noqa: BLE001 — best-effort cleanup
        pass


def _slots(data):
    """Pull the slot list out of an inventory_get response, tolerant of shape."""
    if isinstance(data, dict):
        s = data.get("slots")
        if isinstance(s, list):
            return s
    return []


def _slot_ids(data):
    out = []
    for s in _slots(data):
        if isinstance(s, dict):
            out.append(str(s.get("id") or s.get("item") or s.get("blockId") or ""))
        else:
            out.append(str(s))
    return out


# --- inventory_get ---------------------------------------------------------

@case("inventory_get", level="safe")
def test_get(ctx: Ctx):
    p = ctx.pos()
    target = _chest_target(ctx, p)
    try:
        data = ctx.call("inventory_get", {"target": target})
        ctx.expect(isinstance(data, dict), f"inventory_get not a dict: {str(data)[:160]}")
        size = ctx.expect_field(data, "size")
        ctx.expect_field(data, "slots")
        # a single chest is 27 slots; be tolerant but sanity-check it's a real container
        ctx.expect(isinstance(size, int) and size >= 1,
                   f"unexpected container size {size!r} (expected chest ~27)")
    finally:
        _clear_chest(ctx, p)


# --- inventory_set_slot ----------------------------------------------------

@case("inventory_set_slot", level="safe")
def test_set_slot(ctx: Ctx):
    p = ctx.pos()
    target = _chest_target(ctx, p)
    try:
        text, is_err = ctx.call_text("inventory_set_slot",
                                     {"target": target, "slot": 0,
                                      "item": {"id": "minecraft:diamond", "count": 5}})
        ctx.expect(not is_err, f"set_slot reported error: {text}")
        ctx.expect("set" in text.lower() and "failed" not in text.lower(),
                   f"expected 'set', got {text!r}")
        # confirm the side effect by reading the container back
        data = ctx.call("inventory_get", {"target": target})
        ids = _slot_ids(data)
        ctx.expect(any("diamond" in i for i in ids),
                   f"diamond not present after set_slot; slot ids: {ids[:8]}")
    finally:
        _clear_chest(ctx, p)


# --- inventory_count_items -------------------------------------------------

@case("inventory_count_items", level="safe")
def test_count_items(ctx: Ctx):
    p = ctx.pos()
    target = _chest_target(ctx, p)
    try:
        # empty chest first => 0
        text0, is_err0 = ctx.call_text("inventory_count_items",
                                       {"target": target, "item_id": "minecraft:cobblestone"})
        ctx.expect(not is_err0, f"count_items errored on empty chest: {text0}")
        ctx.expect(text0.strip() == "0", f"expected 0 in empty chest, got {text0!r}")
        # add a known stack and re-count: PlayerOps sums getCount(), so total == 7
        ctx.call_text("inventory_set_slot",
                      {"target": target, "slot": 3,
                       "item": {"id": "minecraft:cobblestone", "count": 7}})
        text1, is_err1 = ctx.call_text("inventory_count_items",
                                       {"target": target, "item_id": "minecraft:cobblestone"})
        ctx.expect(not is_err1, f"count_items errored: {text1}")
        ctx.expect(text1.strip() == "7",
                   f"expected total count 7 of cobblestone, got {text1!r}")
    finally:
        _clear_chest(ctx, p)


# --- inventory_swap_slots --------------------------------------------------

@case("inventory_swap_slots", level="safe")
def test_swap_slots(ctx: Ctx):
    p = ctx.pos()
    target = _chest_target(ctx, p)
    try:
        # seed slot 0 = gold_ingot, slot 1 = iron_ingot
        ctx.call_text("inventory_set_slot",
                      {"target": target, "slot": 0, "item": {"id": "minecraft:gold_ingot", "count": 1}})
        ctx.call_text("inventory_set_slot",
                      {"target": target, "slot": 1, "item": {"id": "minecraft:iron_ingot", "count": 1}})
        text, is_err = ctx.call_text("inventory_swap_slots",
                                     {"target": target, "slot_a": 0, "slot_b": 1})
        ctx.expect(not is_err, f"swap_slots reported error: {text}")
        ctx.expect("swap" in text.lower() and "failed" not in text.lower(),
                   f"expected 'swapped', got {text!r}")
        # verify the contents actually swapped
        ids = _slot_ids(ctx.call("inventory_get", {"target": target}))
        ctx.expect(len(ids) >= 2, f"too few slots to verify swap: {ids[:4]}")
        ctx.expect("iron" in ids[0] and "gold" in ids[1],
                   f"slots did not swap: slot0={ids[0]!r} slot1={ids[1]!r}")
    finally:
        _clear_chest(ctx, p)


# --- inventory_clear_slot --------------------------------------------------

@case("inventory_clear_slot", level="safe")
def test_clear_slot(ctx: Ctx):
    p = ctx.pos()
    target = _chest_target(ctx, p)
    try:
        ctx.call_text("inventory_set_slot",
                      {"target": target, "slot": 2, "item": {"id": "minecraft:emerald", "count": 2}})
        # sanity: emerald present before clear
        before = _slot_ids(ctx.call("inventory_get", {"target": target}))
        ctx.expect(any("emerald" in i for i in before),
                   f"emerald not present before clear; ids: {before[:8]}")
        text, is_err = ctx.call_text("inventory_clear_slot",
                                     {"target": target, "slot": 2})
        ctx.expect(not is_err, f"clear_slot reported error: {text}")
        ctx.expect("clear" in text.lower() and "failed" not in text.lower(),
                   f"expected 'cleared', got {text!r}")
        # verify the slot no longer holds emerald (count_items is the cleanest check)
        cnt, _ = ctx.call_text("inventory_count_items",
                               {"target": target, "item_id": "minecraft:emerald"})
        ctx.expect(cnt.strip() == "0",
                   f"emerald still present after clear_slot: count={cnt!r}")
    finally:
        _clear_chest(ctx, p)
