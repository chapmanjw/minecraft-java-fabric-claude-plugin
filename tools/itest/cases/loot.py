"""Loot-table tools — list / generate / get_definition.

All three are read-only (generate merely *rolls* a table without dropping the
items into the world), so every case is "safe" — nothing here touches the
sandbox or any world-global state.

Probing notes (confirmed against the live 26.1.2 server):
  * loot_table_list returns {items:[...], total:N, next_offset:N} and honours
    offset/limit.
  * loot_table_generate on a *chest* table (e.g. chests/spawn_bonus_chest)
    rolls with no extra loot context and yields a top-level TOON array of
    {id,count,...} item objects. Block / entity / fishing tables instead
    require minecraft:tool / minecraft:block_state context params and error out,
    so we deliberately only roll chest tables.
  * loot_table_get_definition returns the raw JSON for some tables
    (chests/spawn_bonus_chest) but "Definition not available" for many built-ins
    (entities/sheep, chests/simple_dungeon) — the fabric-loot-api-v3 surface does
    not expose every table's source. The test is tolerant: it walks the list to
    find a table whose definition IS available and Skips if none is.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

# A vanilla chest table that always rolls a non-empty result (guaranteed axe +
# pickaxe pools) and needs no killer/tool/block loot context.
CHEST_TABLE = "minecraft:chests/spawn_bonus_chest"


@case("loot_table_list")
def test_list(ctx: Ctx):
    data = ctx.call("loot_table_list", {"limit": 5, "offset": 0})
    items = ctx.expect_field(data, "items")
    total = ctx.expect_field(data, "total")
    ctx.expect_field(data, "next_offset")
    ctx.expect(isinstance(items, list) and len(items) >= 1,
               f"expected a non-empty items list, got {items!r}")
    ctx.expect(isinstance(total, int) and total >= len(items),
               f"total ({total!r}) should be >= page size {len(items)}")
    ctx.expect(all(isinstance(x, str) and ":" in x for x in items),
               f"every id should be a namespaced string: {items!r}")

    # Pagination actually advances: a fresh page at offset=5 differs from page 0.
    page2 = ctx.call("loot_table_list", {"limit": 5, "offset": 5})
    items2 = ctx.expect_field(page2, "items")
    ctx.expect(items2 and items2 != items,
               f"offset=5 page should differ from offset=0 page: {items} vs {items2}")


@case("loot_table_generate")
def test_generate(ctx: Ctx):
    # Roll a chest table — needs no loot context and is never empty.
    drops, is_error = ctx.call_text("loot_table_generate", {"id": CHEST_TABLE})
    ctx.expect(not is_error, f"generate on {CHEST_TABLE} errored: {drops}")
    parsed = ctx.call("loot_table_generate", {"id": CHEST_TABLE})
    ctx.expect(isinstance(parsed, list),
               f"generate should yield a TOON array of items, got {type(parsed).__name__}: {parsed!r}")
    ctx.expect(len(parsed) >= 1, f"{CHEST_TABLE} should roll at least one stack, got {parsed!r}")
    first = parsed[0]
    ctx.expect(isinstance(first, dict) and ("id" in first),
               f"each drop should carry an item id: {first!r}")
    ctx.expect(any("count" in d for d in parsed if isinstance(d, dict)),
               f"drops should carry stack counts: {parsed!r}")

    # The optional position arg (biome-aware tables) must be accepted on a chest
    # table too — roll inside the scratch sandbox to keep coords harmless.
    px, py, pz = ctx.pos()
    drops2, is_error2 = ctx.call_text(
        "loot_table_generate",
        {"id": CHEST_TABLE, "position": {"x": px, "y": py, "z": pz}})
    ctx.expect(not is_error2, f"generate with position errored: {drops2}")

    # An unknown table id resolves to vanilla's empty table: it rolls nothing
    # (no error), confirming the tool degrades gracefully rather than crashing.
    empty = ctx.call("loot_table_generate", {"id": "minecraft:itest/does_not_exist"})
    ctx.expect(isinstance(empty, list) and len(empty) == 0,
               f"unknown table should roll the empty table ([]), got {empty!r}")


@case("loot_table_get_definition")
def test_get_definition(ctx: Ctx):
    # Prefer the known-good chest table; many vanilla tables legitimately have no
    # exposed source ("Definition not available"), so fall back to scanning.
    candidates = [CHEST_TABLE]
    listing = ctx.call("loot_table_list", {"limit": 200, "offset": 0})
    if isinstance(listing, dict) and isinstance(listing.get("items"), list):
        candidates += [t for t in listing["items"] if t.startswith("minecraft:chests/")]

    last = ""
    for table in candidates:
        text, is_error = ctx.call_text("loot_table_get_definition", {"id": table})
        last = text
        if is_error:
            continue  # "Definition not available" for this one — try the next.
        ctx.expect("pools" in text or "type" in text,
                   f"definition for {table} should look like a loot table JSON: {text[:200]}")
        return

    raise Skip(f"no loot table exposed a raw definition (last response: {last[:160]})")
