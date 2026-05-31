"""Recipe tools — list / find-by-ingredient / find-by-result / get-definition.

All four recipe tools are pure reads against the server's recipe manager, so
every case is "safe" (no world mutation, nothing to restore or clean up). The
recipe set is vanilla data, so a handful of canonical recipes (chest, the
diamond block compaction) are stable anchors to assert real content against.

Response shapes (confirmed live against the running 26.1.2 server):
  recipe_list            -> {"items":[{id,type,group,ingredients[],result,resultCount}], total, next_offset}
  recipe_find_by_result  -> root list of recipe objects (same row shape) or [] when none
  recipe_find_by_ingredient -> root list of recipe objects or [] when none
  recipe_get_definition  -> a single recipe object {id,type,group,ingredients[],result,resultCount}
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip


def _rows(data):
    """Normalize a recipe response to a list of recipe dicts.

    Tolerant of: a root list (find_by_*), an object wrapping {"items": [...]}
    (recipe_list), or a single recipe object (get_definition)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("items"), list):
            return data["items"]
        return [data]
    return []


@case("recipe_list", level="safe")
def test_recipe_list(ctx: Ctx):
    # Default (all types) list — must come back paginated with a total + items.
    data = ctx.call("recipe_list", {"limit": 5})
    ctx.expect(isinstance(data, dict), f"recipe_list should be an object, got {type(data).__name__}: {str(data)[:160]}")
    total = ctx.expect_field(data, "total")
    items = ctx.expect_field(data, "items")
    ctx.expect(isinstance(items, list) and len(items) >= 1, f"expected at least one recipe item, got {items!r}")
    ctx.expect(isinstance(total, int) and total > 0, f"expected positive total, got {total!r}")
    ctx.expect(len(items) <= 5, f"limit=5 not honored, got {len(items)} items")
    first = items[0]
    ctx.expect_field(first, "id")
    ctx.expect_field(first, "result")

    # Type filter narrows to a single recipe type and reports its own total.
    crafting = ctx.call("recipe_list", {"type": "minecraft:crafting", "limit": 3})
    citems = _rows(crafting)
    ctx.expect(len(citems) >= 1, f"no minecraft:crafting recipes returned: {str(crafting)[:160]}")
    for r in citems:
        t = r.get("type") if isinstance(r, dict) else None
        ctx.expect(t == "minecraft:crafting", f"type filter leaked a non-crafting recipe: {r!r}")

    # Pagination: offset should advance the window (different first id than page 0).
    page0 = _rows(ctx.call("recipe_list", {"type": "minecraft:crafting", "limit": 1, "offset": 0}))
    page1 = _rows(ctx.call("recipe_list", {"type": "minecraft:crafting", "limit": 1, "offset": 1}))
    if page0 and page1:
        ctx.expect(page0[0].get("id") != page1[0].get("id"),
                   f"offset did not advance: both pages start with {page0[0].get('id')!r}")


@case("recipe_find_by_result", level="safe")
def test_find_by_result(ctx: Ctx):
    data = ctx.call("recipe_find_by_result", {"item_id": "minecraft:chest"})
    rows = _rows(data)
    ctx.expect(len(rows) >= 1, f"expected a crafting recipe for minecraft:chest, got {str(data)[:200]}")
    # Every returned recipe must actually produce the requested item.
    for r in rows:
        res = r.get("result") if isinstance(r, dict) else None
        ctx.expect(res == "minecraft:chest", f"find_by_result returned a recipe with wrong result: {r!r}")
    ctx.expect_field(rows[0], "ingredients")

    # An item with no recipe should yield an empty list, not an error.
    empty = ctx.call("recipe_find_by_result", {"item_id": "minecraft:bedrock"})
    erows = _rows(empty)
    ctx.expect(isinstance(erows, list), f"non-craftable result should still parse to a list, got {empty!r}")
    ctx.expect(len(erows) == 0, f"minecraft:bedrock unexpectedly has recipes: {erows!r}")


@case("recipe_find_by_ingredient", level="safe")
def test_find_by_ingredient(ctx: Ctx):
    data = ctx.call("recipe_find_by_ingredient", {"item_id": "minecraft:diamond"})
    rows = _rows(data)
    ctx.expect(len(rows) >= 1, f"expected recipes consuming minecraft:diamond, got {str(data)[:200]}")
    # At least one returned recipe must list diamond among its ingredients.
    found = False
    for r in rows:
        ings = r.get("ingredients") if isinstance(r, dict) else None
        if isinstance(ings, list) and any("diamond" in str(i) for i in ings):
            found = True
            break
    ctx.expect(found, f"no returned recipe actually lists minecraft:diamond as an ingredient: {str(rows)[:200]}")

    # diamond_block (9-diamond compaction) is a stable, known-present hit.
    ids = {r.get("id") for r in rows if isinstance(r, dict)}
    ctx.expect("minecraft:diamond_block" in ids,
               f"expected minecraft:diamond_block among diamond-consuming recipes, got ids {sorted(str(i) for i in ids)[:12]}")


@case("recipe_get_definition", level="safe")
def test_get_definition(ctx: Ctx):
    # Resolve a real recipe id from the live list first, so this doesn't hinge
    # on a hardcoded id surviving version bumps; fall back to a vanilla anchor.
    listed = _rows(ctx.call("recipe_list", {"type": "minecraft:crafting", "limit": 1}))
    rid = listed[0].get("id") if listed and isinstance(listed[0], dict) else "minecraft:chest"
    if not rid:
        raise Skip("could not resolve a recipe id from recipe_list to fetch")

    data = ctx.call("recipe_get_definition", {"id": rid})
    ctx.expect(isinstance(data, dict), f"recipe_get_definition should be an object, got {type(data).__name__}: {str(data)[:160]}")
    got_id = ctx.expect_field(data, "id")
    ctx.expect(got_id == rid, f"asked for {rid!r}, definition reports id {got_id!r}")
    ctx.expect_field(data, "type")
    ctx.expect_field(data, "result")
    ctx.expect_field(data, "ingredients")
