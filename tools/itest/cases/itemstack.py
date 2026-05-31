"""ItemStack tools — describe (pure) and drop_at (spawns a dropped-item entity).

Two live tools, both keyed by an item spec ({id, count?, components?}):

  * itemstack_describe  pure/read-only: validates the item id and reports what the
    stack would look like (max stack size, durability, component keys). No world
    mutation, so "safe" and no cleanup.
  * itemstack_drop_at   spawns a dropped-item entity at a position. We drop inside
    the force-loaded scratch sandbox, assert an item entity actually appeared, and
    kill it in a ``finally`` so nothing outlives the per-run sandbox clear.

Cleanup strategy for the dropped item: ``itemstack_drop_at`` exposes no entity-NBT
hook to tag the spawned item, and ``entity_query`` documents that complex
(volume/type) selectors are limited in this build — so instead of querying for a
uuid we both *detect* and *remove* the item with one tight-area ``kill`` slash
command scoped to the exact sandbox cell we dropped into:

    kill @e[type=item,x=..,y=..,z=..,distance=..2]

The console ``kill`` returns a ``successCount`` equal to the number of matched
entities, which doubles as the assertion that the drop produced an item entity.
Because the selector is pinned to a fresh ``ctx.pos()`` cell deep in the sandbox,
it can never touch a real build entity even if the test crashes mid-way.
"""
from __future__ import annotations

from ..harness import case, Ctx


# ---------------------------------------------------------------------------
# itemstack_describe — pure / read-only
# ---------------------------------------------------------------------------

@case("itemstack_describe", level="safe")
def test_describe(ctx: Ctx):
    # NOTE: CASES is keyed by tool name, so a tool can only have ONE registered
    # function — all itemstack_describe assertions must live in this one body.
    #
    # (1) A tool with durability and a single-stack limit exercises the interesting
    # fields. Live shape (confirmed): id, count, componentKeys[], maxStackSize,
    # maxDurability, damage.
    data = ctx.call("itemstack_describe", {"id": "minecraft:diamond_sword"})
    ctx.expect(isinstance(data, dict), f"describe did not decode to a dict: {data!r}")

    got_id = ctx.expect_field(data, "id")
    ctx.expect("diamond_sword" in str(got_id), f"unexpected id echoed back: {got_id}")

    mss = ctx.expect_field(data, "maxStackSize")
    ctx.expect(int(mss) == 1, f"diamond_sword should be a 1-stack item, got maxStackSize={mss}")

    # A sword has durability; assert the tool surfaced it as a positive number.
    md = ctx.expect_field(data, "maxDurability")
    ctx.expect(int(md) > 0, f"expected positive maxDurability for a sword, got {md}")

    # componentKeys should be a non-empty list of component identifiers.
    keys = ctx.expect_field(data, "componentKeys")
    ctx.expect(isinstance(keys, list) and len(keys) > 0,
               f"componentKeys not a non-empty list: {keys!r}")
    ctx.expect(any("max_stack_size" in str(k) for k in keys),
               f"expected a max_stack_size component key: {keys}")

    # (2) A stackable item with an explicit count: maxStackSize should reflect the
    # item's vanilla cap (64 for stone), independent of the requested count.
    data = ctx.call("itemstack_describe", {"id": "minecraft:stone", "count": 16})
    ctx.expect(isinstance(data, dict), f"describe(stone) did not decode to a dict: {data!r}")
    mss = ctx.expect_field(data, "maxStackSize")
    ctx.expect(int(mss) == 64, f"stone should be a 64-stack item, got maxStackSize={mss}")
    cnt = ctx.expect_field(data, "count")
    ctx.expect(int(cnt) == 16, f"requested count not echoed back: {cnt}")

    # Validation: an unknown item id must be rejected (the tool documents that it
    # validates the id). Tolerate either a JSON-RPC error (McpError -> raised by
    # call_toon) or an isError text response.
    raised = False
    try:
        text, is_err = ctx.call_text("itemstack_describe", {"id": "minecraft:not_a_real_item_xyz"})
    except Exception:  # noqa: BLE001 — an McpError is a valid rejection of a bad id
        raised = True
    else:
        raised = is_err or ("error" in text.lower() or "unknown" in text.lower()
                            or "invalid" in text.lower() or "no such" in text.lower())
    ctx.expect(raised, "itemstack_describe accepted a bogus item id without complaint")


# ---------------------------------------------------------------------------
# itemstack_drop_at — spawns a dropped-item entity (cleaned up in finally)
# ---------------------------------------------------------------------------

@case("itemstack_drop_at", level="safe")
def test_drop_at(ctx: Ctx):
    p = ctx.pos()  # a fresh sandbox cell; everything below is pinned to it
    px, py, pz = p
    # Selector scoped to exactly this cell — kills only item entities we spawn
    # here, never anything in a real build.
    sel = f"@e[type=item,x={px},y={py},z={pz},distance=..2]"
    dropped = False
    try:
        text, is_err = ctx.call_text("itemstack_drop_at", {
            "dimension": ctx.dim,
            "position": ctx.pos_obj(p),
            "item": {"id": "minecraft:diamond", "count": 3},
        })
        ctx.expect(not is_err, f"itemstack_drop_at reported error: {text}")
        ctx.expect("error" not in text.lower() and "fail" not in text.lower(),
                   f"itemstack_drop_at unexpected result: {text}")
        dropped = True

        # Assert the side effect: an item entity now exists at the drop cell.
        # `kill` returns successCount == number of matched (and removed) entities,
        # so this both verifies and cleans up in one shot.
        res = ctx.call("command_execute", {"command": f"kill {sel}"})
        ctx.expect(isinstance(res, dict), f"kill did not return a dict: {res!r}")
        sc = res.get("successCount")
        ctx.expect(isinstance(sc, int) and sc >= 1,
                   f"expected >=1 dropped item entity at {p}, got successCount={sc}: {res}")
        dropped = False  # kill above already removed it; finally has nothing to do
    finally:
        if dropped:
            # Drop succeeded but the verify/kill step never ran (or failed) — sweep
            # the cell so no item entity outlives the sandbox clear. Best-effort.
            try:
                ctx.command(f"kill {sel}")
            except Exception:  # noqa: BLE001
                pass
