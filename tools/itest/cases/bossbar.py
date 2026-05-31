"""Bossbar tools — the full /bossbar surface (11 tools).

Boss bars are a server-global named registry (MinecraftServer#getCustomBossEvents),
not world state, so these tests don't touch the scratch sandbox. Each test creates
a uniquely-named ``mcb:itest_*`` bar, mutates/reads it, and removes it in a
``finally`` so nothing leaks. The id is unique per test (no collisions) and the
suite never depends on a pre-existing bar.

Response shapes (from the mod's BossbarTools / BossbarInfo):
  * bossbar_add / remove / set_*  -> plain text "added" / "removed" / "set" / "failed"
  * bossbar_get                   -> object {id,name,value,max,color,style,visible,players[]}
  * bossbar_list                  -> array of those objects

The setters (value/max/name/color/style/visible) use the direct CustomBossEvent
API, so they're idempotent-safe and we can assert the side effect back via
bossbar_get.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

# A distinct mcb:itest_* id per test keeps concurrent registry entries from
# colliding and makes leaked bars obvious if a cleanup is ever skipped.
ID_LIFECYCLE = "mcb:itest_lifecycle"
ID_VALUE = "mcb:itest_value"
ID_MAX = "mcb:itest_max"
ID_NAME = "mcb:itest_name"
ID_COLOR = "mcb:itest_color"
ID_STYLE = "mcb:itest_style"
ID_VISIBLE = "mcb:itest_visible"
ID_PLAYERS = "mcb:itest_players"


def _add(ctx: Ctx, bid: str, name: str = "itest"):
    """Create a bar; assert the mod reported success (text 'added')."""
    text, is_err = ctx.call_text("bossbar_add", {"id": bid, "name": name})
    ctx.expect(not is_err, f"bossbar_add({bid}) errored: {text}")
    ctx.expect("fail" not in text.lower(), f"bossbar_add({bid}) failed: {text}")


def _remove(ctx: Ctx, bid: str):
    """Best-effort removal for finally blocks — never raise out of cleanup."""
    try:
        ctx.call_text("bossbar_remove", {"id": bid})
    except Exception:
        pass


@case("bossbar_add", level="safe")
@case("bossbar_get", level="safe")
@case("bossbar_remove", level="safe")
def test_add_get_remove(ctx: Ctx):
    """Lifecycle: add -> get (confirm it exists with sane defaults) -> remove
    (confirm get then fails)."""
    bid = ID_LIFECYCLE
    _remove(ctx, bid)  # clear any leak from a prior aborted run
    try:
        _add(ctx, bid, "itest bar")
        got = ctx.call("bossbar_get", {"id": bid})
        ctx.expect(isinstance(got, dict), f"bossbar_get returned non-object: {got!r}")
        rid = ctx.expect_field(got, "id")
        ctx.expect(bid in str(rid), f"id mismatch: wanted {bid}, got {rid!r}")
        # default vanilla bar: value 0, max 100, visible false, empty players
        ctx.expect_field(got, "max")
        ctx.expect_field(got, "value")
        ctx.expect_field(got, "color")
        ctx.expect_field(got, "style")
        ctx.expect_field(got, "players")
        ctx.expect("visible" in got, f"bossbar_get missing 'visible': {got}")
    finally:
        text, is_err = ctx.call_text("bossbar_remove", {"id": bid})
        ctx.expect(not is_err, f"bossbar_remove errored: {text}")
        ctx.expect("fail" not in text.lower(), f"bossbar_remove failed: {text}")
    # after removal, get must fail — the mod throws a JSON-RPC error (McpError),
    # NOT an isError=True response, so call_text raises rather than returning (text, True).
    # Tolerate both: a raised McpError OR a returned is_err=True.
    try:
        _, got_err = ctx.call_text("bossbar_get", {"id": bid})
        ctx.expect(got_err, "bossbar_get should error after the bar was removed")
    except Exception:  # noqa: BLE001 — McpError / McpException both map here
        pass  # raised = errored as expected


@case("bossbar_list", level="safe")
def test_list(ctx: Ctx):
    """list returns an array; after adding our bar it must appear in it."""
    bid = "mcb:itest_list"
    _remove(ctx, bid)
    try:
        before = ctx.call("bossbar_list", {})
        ctx.expect(isinstance(before, list), f"bossbar_list is not a list: {before!r}")
        _add(ctx, bid, "itest list")
        after = ctx.call("bossbar_list", {})
        ctx.expect(isinstance(after, list), f"bossbar_list is not a list: {after!r}")
        ids = [str(b.get("id")) for b in after if isinstance(b, dict)]
        ctx.expect(any(bid in i for i in ids),
                   f"added bar {bid} not present in list: {ids}")
    finally:
        _remove(ctx, bid)


@case("bossbar_set_value", level="safe")
def test_set_value(ctx: Ctx):
    bid = ID_VALUE
    _remove(ctx, bid)
    try:
        _add(ctx, bid, "itest value")
        # raise max so the value is in range, then set value and read it back
        ctx.call_text("bossbar_set_max", {"id": bid, "max": 50})
        text, is_err = ctx.call_text("bossbar_set_value", {"id": bid, "value": 37})
        ctx.expect(not is_err and "fail" not in text.lower(),
                   f"bossbar_set_value failed: {text}")
        got = ctx.call("bossbar_get", {"id": bid})
        ctx.expect(int(ctx.expect_field(got, "value")) == 37,
                   f"value not applied: {got}")
    finally:
        _remove(ctx, bid)


@case("bossbar_set_max", level="safe")
def test_set_max(ctx: Ctx):
    bid = ID_MAX
    _remove(ctx, bid)
    try:
        _add(ctx, bid, "itest max")
        text, is_err = ctx.call_text("bossbar_set_max", {"id": bid, "max": 250})
        ctx.expect(not is_err and "fail" not in text.lower(),
                   f"bossbar_set_max failed: {text}")
        got = ctx.call("bossbar_get", {"id": bid})
        ctx.expect(int(ctx.expect_field(got, "max")) == 250,
                   f"max not applied: {got}")
    finally:
        _remove(ctx, bid)


@case("bossbar_set_name", level="safe")
def test_set_name(ctx: Ctx):
    bid = ID_NAME
    _remove(ctx, bid)
    try:
        _add(ctx, bid, "before")
        text, is_err = ctx.call_text("bossbar_set_name", {"id": bid, "name": "after_name"})
        ctx.expect(not is_err and "fail" not in text.lower(),
                   f"bossbar_set_name failed: {text}")
        got = ctx.call("bossbar_get", {"id": bid})
        # name is set via Component.literal -> read back as that literal string
        ctx.expect("after_name" in str(ctx.expect_field(got, "name")),
                   f"name not applied: {got}")
    finally:
        _remove(ctx, bid)


@case("bossbar_set_color", level="safe")
def test_set_color(ctx: Ctx):
    bid = ID_COLOR
    _remove(ctx, bid)
    try:
        _add(ctx, bid, "itest color")
        text, is_err = ctx.call_text("bossbar_set_color", {"id": bid, "color": "purple"})
        ctx.expect(not is_err and "fail" not in text.lower(),
                   f"bossbar_set_color failed: {text}")
        got = ctx.call("bossbar_get", {"id": bid})
        ctx.expect("purple" in str(ctx.expect_field(got, "color")).lower(),
                   f"color not applied: {got}")
    finally:
        _remove(ctx, bid)


@case("bossbar_set_style", level="safe")
def test_set_style(ctx: Ctx):
    bid = ID_STYLE
    _remove(ctx, bid)
    try:
        _add(ctx, bid, "itest style")
        text, is_err = ctx.call_text("bossbar_set_style", {"id": bid, "style": "notched_10"})
        ctx.expect(not is_err and "fail" not in text.lower(),
                   f"bossbar_set_style failed: {text}")
        got = ctx.call("bossbar_get", {"id": bid})
        # mod may report the vanilla style key ("notched_10") or its enum form ("10")
        style = str(ctx.expect_field(got, "style")).lower()
        ctx.expect("10" in style or "notched" in style,
                   f"style not applied: {got}")
    finally:
        _remove(ctx, bid)


@case("bossbar_set_visible", level="safe")
def test_set_visible(ctx: Ctx):
    bid = ID_VISIBLE
    _remove(ctx, bid)
    try:
        _add(ctx, bid, "itest visible")
        text, is_err = ctx.call_text("bossbar_set_visible", {"id": bid, "visible": True})
        ctx.expect(not is_err and "fail" not in text.lower(),
                   f"bossbar_set_visible failed: {text}")
        got = ctx.call("bossbar_get", {"id": bid})
        ctx.expect(bool(ctx.expect_field(got, "visible")) is True,
                   f"visible not applied (True): {got}")
        # flip it back off and confirm
        ctx.call_text("bossbar_set_visible", {"id": bid, "visible": False})
        got2 = ctx.call("bossbar_get", {"id": bid})
        ctx.expect(bool(ctx.expect_field(got2, "visible")) is False,
                   f"visible not applied (False): {got2}")
    finally:
        _remove(ctx, bid)


@case("bossbar_set_players", level="safe")
def test_set_players(ctx: Ctx):
    """Exercises bossbar_set_players with the empty-list clear path (no players
    online required). The fix (R5) uses CustomBossEvent.removeAllPlayers() for
    the empty-list case instead of issuing a broken vanilla command, so an empty
    player_uuids list must now succeed. If a player IS online, also exercise the
    populate path and confirm the count, then clear via empty list."""
    bid = ID_PLAYERS
    _remove(ctx, bid)
    try:
        _add(ctx, bid, "itest players")

        # Check if any player is online so we can exercise the populate path too.
        online = ctx.call("player_list_online", {})
        rows = online if isinstance(online, list) else []
        uuid = None
        for p in rows:
            if isinstance(p, dict):
                uuid = p.get("uuid") or p.get("id") or p.get("playerUuid")
                if uuid:
                    break

        if uuid is not None:
            # A player is online — set them, verify, then clear via empty list.
            t2, e2 = ctx.call_text("bossbar_set_players",
                                    {"id": bid, "player_uuids": [str(uuid)]})
            ctx.expect(not e2 and "fail" not in t2.lower(),
                       f"bossbar_set_players([{uuid}]) failed: {t2}")
            got2 = ctx.call("bossbar_get", {"id": bid})
            ctx.expect(len(ctx.expect_field(got2, "players")) == 1,
                       f"player not added: {got2}")

        # Empty-list clear: fixed in R5 via CustomBossEvent.removeAllPlayers().
        # Must succeed (not "failed") regardless of whether any player was online.
        t_clear, e_clear = ctx.call_text("bossbar_set_players",
                                          {"id": bid, "player_uuids": []})
        ctx.expect(not e_clear and "fail" not in t_clear.lower(),
                   f"bossbar_set_players([]) failed (empty-clear should succeed after R5 fix): {t_clear}")
        got_after = ctx.call("bossbar_get", {"id": bid})
        players_after = ctx.expect_field(got_after, "players")
        ctx.expect(isinstance(players_after, list) and len(players_after) == 0,
                   f"players should be empty after clear with []: {got_after}")
    finally:
        _remove(ctx, bid)
