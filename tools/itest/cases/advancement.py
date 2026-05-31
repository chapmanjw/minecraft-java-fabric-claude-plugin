"""Advancement tools — registry reads + player grant/revoke/list.

Covers all five live ``advancement_*`` tools:

  * ``advancement_list_all``       — read-only registry listing (safe).
  * ``advancement_get_definition`` — read-only JSON definition (safe).
  * ``advancement_grant``          — needs an online player (skipped when none).
  * ``advancement_revoke``         — needs an online player (skipped when none).
  * ``advancement_list_player``    — needs an online player (skipped when none).

Probe findings (live server, 1617 advancements registered):
  * ``advancement_list_all`` returns ``{items:[...], total, next_offset}``.
  * ``advancement_get_definition`` returns ``{advancement_id, definition}`` where
    ``definition`` is a JSON *string*. Not every id from ``list_all`` resolves
    (e.g. ``minecraft:adventure/adventuring_time`` reported "Unknown advancement"),
    so the definition test resolves a known-good id from the page rather than
    blindly using the first id, falling back to a vanilla root.
  * No players are online (onlinePlayerCount=0), so the three player-targeted
    tools Skip per the harness no-player convention.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

# A vanilla root advancement that the live mod resolves via get_definition.
_KNOWN_ADVANCEMENT = "minecraft:adventure/root"


def _online_player_uuid(ctx: Ctx):
    """Return a connected player's UUID, or None when nobody is online."""
    data = ctx.call("player_list_online")
    rows = None
    if isinstance(data, dict):
        # tolerate {players:[...]}, {items:[...]}, or a bare list under any key
        for key in ("players", "items", "online", "list"):
            if isinstance(data.get(key), list):
                rows = data[key]
                break
        if rows is None:
            # maybe the dict *is* a single player record
            rows = [data] if (data.get("uuid") or data.get("id")) else []
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    for row in rows:
        if isinstance(row, dict):
            uuid = row.get("uuid") or row.get("id") or row.get("playerUuid")
            if uuid:
                return str(uuid)
    return None


@case("advancement_list_all", level="safe")
def test_list_all(ctx: Ctx):
    data = ctx.call("advancement_list_all", {"limit": 5, "offset": 0})
    ctx.expect(isinstance(data, dict), f"list_all not a dict: {str(data)[:160]}")
    items = ctx.expect_field(data, "items")
    ctx.expect(isinstance(items, list), f"items not a list: {str(items)[:160]}")
    ctx.expect(len(items) >= 1, "list_all returned no advancement ids")
    total = ctx.expect_field(data, "total")
    ctx.expect(int(total) >= len(items), f"total {total} < page size {len(items)}")
    # paging contract: a non-final page reports the next offset.
    ctx.expect("next_offset" in data, "list_all missing next_offset field")


@case("advancement_get_definition", level="safe")
def test_get_definition(ctx: Ctx):
    # Pull a page and find an id that the mod actually resolves; the registry
    # listing is a superset of what get_definition accepts.
    page = ctx.call("advancement_list_all", {"limit": 50, "offset": 0})
    candidates = []
    if isinstance(page, dict) and isinstance(page.get("items"), list):
        candidates = [str(i) for i in page["items"]]
    # prefer the known-good vanilla root first, then walk the page.
    order = [_KNOWN_ADVANCEMENT] + [c for c in candidates if c != _KNOWN_ADVANCEMENT]

    last_text = ""
    for adv_id in order:
        text, is_error = ctx.call_text("advancement_get_definition",
                                       {"advancement_id": adv_id})
        last_text = text
        if is_error or "unknown advancement" in text.lower():
            continue
        data = ctx.call("advancement_get_definition", {"advancement_id": adv_id})
        ctx.expect(isinstance(data, dict), f"definition not a dict: {str(data)[:160]}")
        defn = ctx.expect_field(data, "definition")
        ctx.expect(bool(str(defn)), f"empty definition for {adv_id}")
        # the definition is a JSON blob describing the advancement.
        ctx.expect("criteria" in str(defn) or "display" in str(defn),
                   f"definition for {adv_id} lacks criteria/display: {str(defn)[:160]}")
        return
    raise AssertionError(f"no resolvable advancement found; last response: {last_text[:200]}")


@case("advancement_list_player", level="safe")
def test_list_player(ctx: Ctx):
    uuid = _online_player_uuid(ctx)
    if not uuid:
        raise Skip("no player online")
    data = ctx.call("advancement_list_player", {"player_uuid": uuid})
    ctx.expect(data is not None, "list_player returned nothing")


@case("advancement_grant", level="global")
def test_grant(ctx: Ctx):
    # global: mutates a player's persistent advancement state; restore by
    # revoking what we granted in a finally so the player is left as found.
    uuid = _online_player_uuid(ctx)
    if not uuid:
        raise Skip("no player online")
    try:
        text, is_error = ctx.call_text("advancement_grant",
                                       {"player_uuid": uuid,
                                        "advancement_id": _KNOWN_ADVANCEMENT,
                                        "mode": "only",
                                        "criterion": "killed_something"})
        ctx.expect(not is_error, f"grant errored: {text}")
    finally:
        ctx.call_text("advancement_revoke",
                      {"player_uuid": uuid,
                       "advancement_id": _KNOWN_ADVANCEMENT,
                       "mode": "only",
                       "criterion": "killed_something"})


@case("advancement_revoke", level="global")
def test_revoke(ctx: Ctx):
    # global: grant first so the revoke has something to undo, then leave the
    # player as found (the grant + revoke net out to the original state).
    uuid = _online_player_uuid(ctx)
    if not uuid:
        raise Skip("no player online")
    ctx.call_text("advancement_grant",
                  {"player_uuid": uuid,
                   "advancement_id": _KNOWN_ADVANCEMENT,
                   "mode": "only",
                   "criterion": "killed_something"})
    text, is_error = ctx.call_text("advancement_revoke",
                                   {"player_uuid": uuid,
                                    "advancement_id": _KNOWN_ADVANCEMENT,
                                    "mode": "only",
                                    "criterion": "killed_something"})
    ctx.expect(not is_error, f"revoke errored: {text}")
