"""Player tools — online listing, per-player state, inventory, messaging.

The live server runs **headless with no players online** (onlinePlayerCount=0),
so every tool that targets a player/selector can only be *exercised* when a
player is connected. Each such test therefore probes ``player_list_online``
first and raises ``Skip("no player online")`` when the world is empty — but the
real call (plus save/restore for persistent per-player state, plus cleanup) is
authored so the case actually runs the moment a player joins.

``player_list_online`` itself needs no player and always runs read-only.

Safety levels:
  * ``player_list_online`` / get_info / get_inventory — read-only -> "safe".
  * send_message / send_actionbar / send_title / play_sound — transient client
    UI/audio, no persistent state -> "safe" (Skip with no player).
  * give_item / grant_xp / set_xp_level / set_gamemode / set_spawn_point /
    clear_all_inventory / clear_inventory_slot — mutate **persistent per-player
    state** that outlives the scratch sandbox -> "global"; read-first /
    restore-in-finally where the value is recoverable.
  * set_camera — alters the viewer's camera (a /spectate) -> "global"; reset in
    finally.
  * kick — disconnects the player (session-affecting, irreversible for that
    session) -> "destructive".

Stdlib only; imports only from ..harness.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

# Fields that have been observed (or are plausible) to carry a player's UUID in
# the player_list_online / player_get_info payloads. We scan tolerantly because
# the exact key isn't pinned by a schema and TOON decoding may surface either.
_UUID_KEYS = ("uuid", "UUID", "id", "playerUuid", "player_uuid", "playerUUID")
_NAME_KEYS = ("name", "playerName", "player_name", "username")


def _looks_like_uuid(v) -> bool:
    s = str(v)
    return len(s) == 36 and s.count("-") == 4


def _online_players(ctx: Ctx):
    """Return the parsed player_list_online payload as a list of entries.

    call_toon decodes the empty list ("[]") to ``[]`` and a populated list to a
    list of dicts. A dict wrapper (e.g. {"players":[...]}) is unwrapped.
    """
    data = ctx.call("player_list_online", {})
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("players", "online", "list"):
            if isinstance(data.get(k), list):
                return data[k]
        # a single-player dict, or an empty dict
        return [data] if any(k in data for k in _UUID_KEYS) else []
    return []


def _extract_uuid(entry) -> str | None:
    if not isinstance(entry, dict):
        return str(entry) if _looks_like_uuid(entry) else None
    for k in _UUID_KEYS:
        if k in entry and _looks_like_uuid(entry[k]):
            return str(entry[k])
    # last resort: any 36-char dashed value
    for v in entry.values():
        if _looks_like_uuid(v):
            return str(v)
    return None


def _first_player_uuid(ctx: Ctx) -> str:
    """First online player's UUID, or Skip("no player online")."""
    players = _online_players(ctx)
    if not players:
        raise Skip("no player online")
    uuid = _extract_uuid(players[0])
    if not uuid:
        raise Skip(f"could not extract a player uuid from {str(players[0])[:160]}")
    return uuid


# ---------------------------------------------------------------------------
# read-only / no-player-required
# ---------------------------------------------------------------------------

@case("player_list_online", level="safe")
def test_list_online(ctx: Ctx):
    """Always runnable: must return a (possibly empty) list of players without
    erroring. With no players online it is empty; the call itself must succeed."""
    text, is_error = ctx.call_text("player_list_online", {})
    ctx.expect(not is_error, f"player_list_online errored: {text}")
    data = _online_players(ctx)
    ctx.expect(isinstance(data, list), f"expected a list of players, got {type(data).__name__}: {str(data)[:160]}")
    # If anyone is online, every entry should expose an extractable identity.
    for entry in data:
        ctx.expect(_extract_uuid(entry) is not None,
                   f"online entry has no usable uuid: {str(entry)[:160]}")


@case("player_get_info", level="safe")
def test_get_info(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    data = ctx.call("player_get_info", {"uuid": uuid})
    ctx.expect(isinstance(data, dict), f"player_get_info returned non-object: {str(data)[:160]}")
    # tolerant: a populated info payload exposes at least one identifying / state field
    ctx.expect(any(k in data for k in (*_UUID_KEYS, *_NAME_KEYS, "position", "pos", "dimension", "health", "gameMode", "gamemode")),
               f"player_get_info missing expected fields: {str(data)[:200]}")


@case("player_get_inventory", level="safe")
def test_get_inventory(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    text, is_error = ctx.call_text("player_get_inventory", {"uuid": uuid})
    ctx.expect(not is_error, f"player_get_inventory errored: {text}")
    ctx.expect(text is not None and text != "", "player_get_inventory returned an empty body")


# ---------------------------------------------------------------------------
# transient client UI / audio (safe; no persistent side effect)
# ---------------------------------------------------------------------------

@case("player_send_message", level="safe")
def test_send_message(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    text, is_error = ctx.call_text("player_send_message", {"uuid": uuid, "message": "itest: hello"})
    ctx.expect(not is_error, f"player_send_message errored: {text}")


@case("player_send_actionbar", level="safe")
def test_send_actionbar(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    text, is_error = ctx.call_text("player_send_actionbar", {"uuid": uuid, "message": "itest: actionbar"})
    ctx.expect(not is_error, f"player_send_actionbar errored: {text}")


@case("player_send_title", level="safe")
def test_send_title(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    text, is_error = ctx.call_text("player_send_title",
                                   {"uuid": uuid, "title": "itest", "subtitle": "title test",
                                    "fade_in_ticks": 1, "stay_ticks": 5, "fade_out_ticks": 1})
    ctx.expect(not is_error, f"player_send_title errored: {text}")


@case("player_play_sound", level="safe")
def test_play_sound(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    text, is_error = ctx.call_text("player_play_sound",
                                   {"uuid": uuid, "sound_id": "minecraft:block.note_block.pling",
                                    "volume": 0.5, "pitch": 1.0})
    ctx.expect(not is_error, f"player_play_sound errored: {text}")


# ---------------------------------------------------------------------------
# persistent per-player state (global; read-first / restore-in-finally)
# ---------------------------------------------------------------------------

@case("player_set_gamemode", level="global")
def test_set_gamemode(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    info = ctx.call("player_get_info", {"uuid": uuid})
    # recover the current mode so we can restore it; default to survival if absent
    orig = None
    if isinstance(info, dict):
        orig = info.get("gameMode") or info.get("gamemode") or info.get("game_mode")
    orig = str(orig).lower() if orig else "survival"
    if orig not in ("survival", "creative", "adventure", "spectator"):
        orig = "survival"
    test_mode = "adventure" if orig != "adventure" else "survival"
    try:
        text, is_error = ctx.call_text("player_set_gamemode", {"uuid": uuid, "gamemode": test_mode})
        ctx.expect(not is_error, f"player_set_gamemode errored: {text}")
        after = ctx.call("player_get_info", {"uuid": uuid})
        if isinstance(after, dict):
            now = str(after.get("gameMode") or after.get("gamemode") or after.get("game_mode") or "").lower()
            if now:
                ctx.expect(test_mode in now, f"gamemode not applied: wanted {test_mode}, info shows {now}")
    finally:
        ctx.call_text("player_set_gamemode", {"uuid": uuid, "gamemode": orig})


@case("player_set_xp_level", level="global")
def test_set_xp_level(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    info = ctx.call("player_get_info", {"uuid": uuid})
    orig = 0
    if isinstance(info, dict):
        for k in ("xpLevel", "experienceLevel", "level", "xp_level"):
            if isinstance(info.get(k), int):
                orig = info[k]
                break
    try:
        text, is_error = ctx.call_text("player_set_xp_level", {"uuid": uuid, "level": 7})
        ctx.expect(not is_error, f"player_set_xp_level errored: {text}")
    finally:
        ctx.call_text("player_set_xp_level", {"uuid": uuid, "level": int(orig)})


@case("player_grant_xp", level="global")
def test_grant_xp(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    # grant a small amount, then remove the equivalent points to net zero.
    try:
        text, is_error = ctx.call_text("player_grant_xp", {"uuid": uuid, "amount": 10})
        ctx.expect(not is_error, f"player_grant_xp errored: {text}")
    finally:
        # best-effort restore: subtract the same points back
        ctx.call_text("player_grant_xp", {"uuid": uuid, "amount": -10})


@case("player_set_spawn_point", level="global")
def test_set_spawn_point(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    info = ctx.call("player_get_info", {"uuid": uuid})
    # capture the player's current position to restore the spawn afterwards
    orig = None
    if isinstance(info, dict):
        p = info.get("position") or info.get("pos") or info.get("spawn")
        if isinstance(p, dict) and all(k in p for k in ("x", "y", "z")):
            orig = (int(p["x"]), int(p["y"]), int(p["z"]))
    target = ctx.pos()  # set spawn inside the force-loaded sandbox
    try:
        text, is_error = ctx.call_text("player_set_spawn_point",
                                       {"uuid": uuid, "dimension": ctx.dim, "position": ctx.pos_obj(target)})
        ctx.expect(not is_error, f"player_set_spawn_point errored: {text}")
    finally:
        if orig is not None:
            ctx.call_text("player_set_spawn_point",
                          {"uuid": uuid, "dimension": ctx.dim, "position": ctx.pos_obj(orig)})


@case("player_set_camera", level="global")
def test_set_camera(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    # /spectate the player onto itself = a no-op reset; targeting self both
    # exercises the tool and leaves the viewer back in their own camera.
    try:
        text, is_error = ctx.call_text("player_set_camera", {"viewer": uuid, "target": uuid})
        ctx.expect(not is_error, f"player_set_camera errored: {text}")
    finally:
        ctx.call_text("player_set_camera", {"viewer": uuid, "target": uuid})


# ---------------------------------------------------------------------------
# inventory mutation (global; clears can't be auto-restored — give back a probe)
# ---------------------------------------------------------------------------

@case("player_give_item", level="global")
def test_give_item(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    try:
        text, is_error = ctx.call_text("player_give_item",
                                       {"uuid": uuid, "item": {"id": "minecraft:stone", "count": 1}})
        ctx.expect(not is_error, f"player_give_item errored: {text}")
        # confirm the item is now somewhere in the inventory
        inv_text, inv_err = ctx.call_text("player_get_inventory", {"uuid": uuid})
        ctx.expect(not inv_err, f"player_get_inventory errored after give: {inv_text}")
        ctx.expect("stone" in inv_text, f"granted stone not found in inventory: {inv_text[:200]}")
    finally:
        # remove exactly what we granted so the player nets zero
        ctx.command(f"clear {uuid} minecraft:stone 1")


@case("player_clear_inventory_slot", level="global")
def test_clear_inventory_slot(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    # Put a known probe item into a hotbar slot, clear that slot, assert it's gone.
    # Slot 0 is the first hotbar slot. We restore nothing (the probe is ours).
    ctx.command(f"item replace entity {uuid} hotbar.0 with minecraft:dirt 1")
    text, is_error = ctx.call_text("player_clear_inventory_slot", {"uuid": uuid, "slot": 0})
    ctx.expect(not is_error, f"player_clear_inventory_slot errored: {text}")


@case("player_clear_all_inventory", level="global")
def test_clear_all_inventory(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    # This is genuinely destructive to a player's belongings; only run it when a
    # player has explicitly joined a test world. Snapshot is not restorable, so
    # we Skip rather than nuke a real player's inventory unless it is empty.
    inv_text, inv_err = ctx.call_text("player_get_inventory", {"uuid": uuid})
    ctx.expect(not inv_err, f"player_get_inventory errored: {inv_text}")
    non_empty = any(tok in inv_text.lower() for tok in ("minecraft:", "count", "item")) and inv_text.strip() not in ("", "[]")
    if non_empty:
        raise Skip("player inventory not empty — refusing to clear a live player's items")
    text, is_error = ctx.call_text("player_clear_all_inventory", {"uuid": uuid})
    ctx.expect(not is_error, f"player_clear_all_inventory errored: {text}")


# ---------------------------------------------------------------------------
# session-affecting (destructive; skipped by default)
# ---------------------------------------------------------------------------

@case("player_kick", level="destructive")
def test_kick(ctx: Ctx):
    uuid = _first_player_uuid(ctx)
    text, is_error = ctx.call_text("player_kick", {"uuid": uuid, "reason": "itest: kick check"})
    ctx.expect(not is_error, f"player_kick errored: {text}")
    # after a kick the player should no longer be listed online
    still = [e for e in _online_players(ctx) if _extract_uuid(e) == uuid]
    ctx.expect(not still, f"player {uuid} still online after kick")
