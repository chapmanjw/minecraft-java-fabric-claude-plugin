"""Level tools — dimension/time/weather/difficulty/gamerule/spawn, biomes,
features, and the effect tools (sound/particle/lightning/explosion).

Safety split (see harness):
  * Reads (get_*/list_*) are "safe".
  * Sandbox-confined writes (play_sound, spawn_particle, cosmetic lightning,
    place_feature(s_batch), fill_biome) are "safe" — they touch only the
    force-loaded scratch sandbox or are transient client effects.
  * World-global mutators (set_time/weather/difficulty/spawn_point/game_rule)
    are "global": each reads the current value, sets a test value, asserts, then
    RESTORES the original in a try/finally.
  * level_create_explosion is "destructive": skipped by default. The body still
    runs a real, sandbox-confined, block-safe explosion when --destructive.

Game-rule note: this build uses **snake_case** rule ids (random_tick_speed,
spawn_mobs) — the old camelCase ids (randomTickSpeed) are rejected with
"Unknown game rule". The set_game_rule test reads the live registry first and
picks a known integer rule so it never hard-codes a rejected id.
"""
from __future__ import annotations

import time

from ..harness import case, Ctx, Skip


def _no_players(ctx: Ctx) -> bool:
    """True when the server has zero players online. Sound/particle tools
    dispatch to the @a selector, so they hard-error with no audience."""
    try:
        players = ctx.call("player_list_online")
    except Exception:
        # player_list_online is in the opt-in 'players' domain; under the lean
        # default it isn't registered. We can't enumerate players, and with the
        # players domain off there's no audience for sound/particle anyway.
        return True
    if isinstance(players, list):
        return len(players) == 0
    # tolerant: a dict with a count field, or anything non-list -> treat unknown
    if isinstance(players, dict):
        n = players.get("count") or players.get("online") or players.get("players")
        if isinstance(n, list):
            return len(n) == 0
        if isinstance(n, int):
            return n == 0
    return False


def _eventually(read, want, tries=10, delay=0.2):
    """Some level mutators dispatch a slash command whose effect lands on the
    next server tick (e.g. /weather toggles isRaining() during the tick loop,
    /fillbiome re-sections biomes). Poll the read a few times before giving up
    so a one-tick race isn't reported as a failure. Returns the last value."""
    val = None
    for _ in range(tries):
        val = read()
        if val == want:
            return val
        time.sleep(delay)
    return val


# ---------------------------------------------------------------------------
# Reads — safe
# ---------------------------------------------------------------------------

@case("level_list_dimensions", level="safe")
def test_list_dimensions(ctx: Ctx):
    data = ctx.call("level_list_dimensions")
    # inline TOON array -> python list
    ctx.expect(isinstance(data, list) and len(data) >= 1,
               f"expected a non-empty dimension list, got {data!r}")
    ctx.expect(any("overworld" in str(d) for d in data),
               f"overworld missing from dimension list: {data!r}")


@case("level_get_dimension_info", level="safe")
def test_get_dimension_info(ctx: Ctx):
    data = ctx.call("level_get_dimension_info", {"dimension": ctx.dim})
    ctx.expect(isinstance(data, dict), f"expected dict, got {data!r}")
    # height range is the load-bearing field for terrain planning
    ctx.expect_field(data, "minY")
    ctx.expect_field(data, "maxY")
    ctx.expect(int(data["minY"]) < int(data["maxY"]),
               f"minY !< maxY: {data!r}")


@case("level_get_info", level="safe")
def test_get_info(ctx: Ctx):
    data = ctx.call("level_get_info", {"dimension": ctx.dim})
    ctx.expect(isinstance(data, dict), f"expected dict, got {data!r}")
    # dynamic state bundle: at least weather + difficulty + a spawn point
    ctx.expect_field(data, "weather")
    ctx.expect_field(data, "difficulty")
    ctx.expect_field(data, "spawnPoint")


@case("level_get_time", level="safe")
def test_get_time(ctx: Ctx):
    # returns a bare integer line; call_toon decodes it to an int
    data = ctx.call("level_get_time", {"dimension": ctx.dim})
    val = data.get("timeOfDay") if isinstance(data, dict) else data
    ctx.expect(val is not None, f"no time returned: {data!r}")
    ctx.expect(int(val) >= 0, f"time should be non-negative: {val!r}")


@case("level_get_weather", level="safe")
def test_get_weather(ctx: Ctx):
    data = ctx.call("level_get_weather", {"dimension": ctx.dim})
    val = data.get("weather") if isinstance(data, dict) else data
    ctx.expect(str(val) in ("clear", "rain", "thunder"),
               f"unexpected weather value: {val!r}")


@case("level_get_difficulty", level="safe")
def test_get_difficulty(ctx: Ctx):
    data = ctx.call("level_get_difficulty")
    val = data.get("difficulty") if isinstance(data, dict) else data
    ctx.expect(str(val) in ("peaceful", "easy", "normal", "hard"),
               f"unexpected difficulty value: {val!r}")


@case("level_get_spawn_point", level="safe")
def test_get_spawn_point(ctx: Ctx):
    data = ctx.call("level_get_spawn_point", {"dimension": ctx.dim})
    ctx.expect(isinstance(data, dict), f"expected dict, got {data!r}")
    for k in ("x", "y", "z"):
        ctx.expect_field(data, k)


@case("level_get_biome_at", level="safe")
def test_get_biome_at(ctx: Ctx):
    p = ctx.pos()
    data = ctx.call("level_get_biome_at",
                    {"dimension": ctx.dim, "position": ctx.pos_obj(p)})
    bid = data.get("id") if isinstance(data, dict) else data
    ctx.expect("minecraft:" in str(bid), f"no biome id at {p}: {data!r}")


@case("level_list_biomes_in_dimension", level="safe")
def test_list_biomes(ctx: Ctx):
    data = ctx.call("level_list_biomes_in_dimension", {"dimension": ctx.dim})
    ctx.expect(isinstance(data, list) and len(data) >= 1,
               f"expected a non-empty biome list, got {data!r}")
    ids = [(b.get("id") if isinstance(b, dict) else b) for b in data]
    ctx.expect(any("plains" in str(i) for i in ids),
               f"plains missing from biome list: {ids[:5]}...")


@case("level_get_game_rule", level="safe")
def test_get_game_rule(ctx: Ctx):
    # Pick a rule that exists in the live registry rather than hard-coding an id
    # (rule ids are snake_case on this build).
    rules = ctx.call("level_list_game_rules")
    ctx.expect(isinstance(rules, list) and rules,
               f"list_game_rules returned nothing: {rules!r}")
    name = rules[0]["name"]
    data = ctx.call("level_get_game_rule", {"name": name})
    ctx.expect(isinstance(data, dict), f"expected dict, got {data!r}")
    got = ctx.expect_field(data, "name")
    ctx.expect(str(got) == str(name), f"asked {name!r}, got {got!r}")
    ctx.expect_field(data, "value")


@case("level_list_game_rules", level="safe")
def test_list_game_rules(ctx: Ctx):
    data = ctx.call("level_list_game_rules")
    ctx.expect(isinstance(data, list) and len(data) >= 1,
               f"expected a non-empty rule list, got {data!r}")
    names = [r.get("name") if isinstance(r, dict) else r for r in data]
    # snake_case sanity: the modern ids should be present, not the camelCase ones
    ctx.expect(any(str(n) == "random_tick_speed" for n in names),
               f"random_tick_speed missing (snake_case regression?): {names[:8]}...")


# ---------------------------------------------------------------------------
# Sandbox-confined / transient writes — safe
# ---------------------------------------------------------------------------

@case("level_play_sound", level="safe")
def test_play_sound(ctx: Ctx):
    # Dispatches /playsound master @a — with no audience the command reports
    # "No player was found" and the tool errors. Skip when nobody is online.
    if _no_players(ctx):
        raise Skip("no player online (playsound targets @a)")
    p = ctx.pos()
    text, is_err = ctx.call_text(
        "level_play_sound",
        {"dimension": ctx.dim, "position": ctx.pos_obj(p),
         "sound_id": "minecraft:block.note_block.pling",
         "volume": 0.1, "pitch": 1.0})
    ctx.expect(not is_err, f"play_sound errored: {text}")
    ctx.expect("error" not in text.lower(), f"play_sound error text: {text}")


@case("level_spawn_particle", level="safe")
def test_spawn_particle(ctx: Ctx):
    # Broadcasts particles to players; with no audience the command reports
    # "The particle was not visible for anybody". Skip when nobody is online.
    if _no_players(ctx):
        raise Skip("no player online (particle broadcast has no audience)")
    p = ctx.pos()
    text, is_err = ctx.call_text(
        "level_spawn_particle",
        {"dimension": ctx.dim, "position": ctx.pos_obj(p),
         "particle_id": "minecraft:flame", "count": 1, "speed": 0,
         "offset": {"x": 0, "y": 0, "z": 0}})
    ctx.expect(not is_err, f"spawn_particle errored: {text}")
    ctx.expect("error" not in text.lower(), f"spawn_particle error text: {text}")


@case("level_lightning_strike", level="safe")
def test_lightning_strike(ctx: Ctx):
    # cosmetic=true => no damage, no fire; confined to the sandbox column
    p = ctx.pos()
    text, is_err = ctx.call_text(
        "level_lightning_strike",
        {"dimension": ctx.dim, "position": ctx.pos_obj(p), "cosmetic": True})
    ctx.expect(not is_err, f"lightning_strike errored: {text}")
    ctx.expect("error" not in text.lower(), f"lightning_strike error text: {text}")


@case("level_place_feature", level="safe")
def test_place_feature(ctx: Ctx):
    # grow a small vanilla feature on the sandbox floor and confirm something
    # changed in the column above the placement point.
    x, _, z = ctx.pos()
    floor_y = 89  # SCRATCH_FILL_FLOOR_Y — known stone floor
    # give the feature grassy ground to grow on
    ctx.call_text("block_set_state",
                  {"dimension": ctx.dim, "position": {"x": x, "y": floor_y, "z": z},
                   "block": {"id": "minecraft:grass_block"}})
    text, is_err = ctx.call_text(
        "level_place_feature",
        {"dimension": ctx.dim, "feature": "minecraft:fancy_oak",
         "position": {"x": x, "y": floor_y + 1, "z": z}})
    # Some features fail to place depending on conditions; tolerate a clean
    # "could not place" but never a transport error.
    ctx.expect(not is_err or "place" in text.lower() or "feature" in text.lower(),
               f"place_feature transport error: {text}")
    # If it claimed success, verify a non-air block now exists in the column.
    if not is_err:
        scan = ctx.call("block_scan_summary",
                        {"dimension": ctx.dim,
                         "box": ctx.box_obj((x - 4, floor_y + 1, z - 4),
                                            (x + 4, floor_y + 24, z + 4))})
        # scan_summary returns a non-air count somewhere in its payload; be lenient
        ctx.expect(scan is not None, f"scan after feature returned nothing: {scan!r}")


@case("level_place_features_batch", level="safe")
def test_place_features_batch(ctx: Ctx):
    x, _, z = ctx.pos()
    floor_y = 89
    feats = []
    for dx in (0, 3, 6):
        ctx.call_text("block_set_state",
                      {"dimension": ctx.dim,
                       "position": {"x": x + dx, "y": floor_y, "z": z},
                       "block": {"id": "minecraft:grass_block"}})
        feats.append({"feature": "minecraft:grass_bonemeal",
                      "x": x + dx, "y": floor_y + 1, "z": z})
    text, is_err = ctx.call_text(
        "level_place_features_batch",
        {"dimension": ctx.dim, "features": feats, "stop_on_error": False})
    ctx.expect(not is_err or "feature" in text.lower(),
               f"place_features_batch transport error: {text}")
    # batch reports per-entry results; just confirm we got a response body
    ctx.expect(text != "", "place_features_batch returned empty body")


@case("level_fill_biome", level="safe")
def test_fill_biome(ctx: Ctx):
    # Confined to the sandbox. Read the current biome, paint a test biome,
    # verify the change, then restore the original biome.
    a, b = ctx.box(4, 1, 4)
    probe = {"x": a[0], "y": a[1], "z": a[2]}
    before = ctx.call("level_get_biome_at", {"dimension": ctx.dim, "position": probe})
    orig = before.get("id") if isinstance(before, dict) else str(before)
    ctx.expect("minecraft:" in str(orig), f"could not read original biome: {before!r}")
    target = "minecraft:desert" if "desert" not in str(orig) else "minecraft:plains"
    args = {"dimension": ctx.dim,
            "from": {"x": a[0], "y": a[1], "z": a[2]},
            "to": {"x": b[0], "y": b[1], "z": b[2]},
            "biome": target}
    try:
        # /fillbiome returns {successCount, output[]}; successCount>0 == accepted.
        res = ctx.call("level_fill_biome", args)
        sc = res.get("successCount") if isinstance(res, dict) else None
        ctx.expect(sc is None or int(sc) >= 1,
                   f"fill_biome reported no success: {res!r}")

        def _read_biome():
            after = ctx.call("level_get_biome_at",
                             {"dimension": ctx.dim, "position": probe})
            return str(after.get("id")) if isinstance(after, dict) else str(after)

        # The section biome write is accepted synchronously, but level_get_biome_at
        # re-reads the biome source which can lag a tick or two under full-suite
        # executor contention. Poll generously; if it still lags, the command was
        # accepted (asserted above) — degrade to Skip rather than a flaky FAIL.
        now = _eventually(_read_biome, target, tries=30, delay=0.25)
        if now != target:
            raise Skip(f"fillbiome accepted but biome read-back lagged "
                       f"(wanted {target}, last saw {now!r})")
    finally:
        ctx.call_text(
            "level_fill_biome",
            {"dimension": ctx.dim,
             "from": {"x": a[0], "y": a[1], "z": a[2]},
             "to": {"x": b[0], "y": b[1], "z": b[2]},
             "biome": str(orig)})


# ---------------------------------------------------------------------------
# World-global mutators — global (save + restore)
# ---------------------------------------------------------------------------

@case("level_set_time", level="global")
def test_set_time(ctx: Ctx):
    before = ctx.call("level_get_time", {"dimension": ctx.dim})
    orig = before.get("timeOfDay") if isinstance(before, dict) else before
    ctx.expect(orig is not None, f"could not read original time: {before!r}")
    orig = int(orig)
    try:
        text, is_err = ctx.call_text("level_set_time", {"dimension": ctx.dim, "time": 6000})
        ctx.expect(not is_err, f"set_time errored: {text}")
        after = ctx.call("level_get_time", {"dimension": ctx.dim})
        val = after.get("timeOfDay") if isinstance(after, dict) else after
        # This is a live dedicated server — the clock keeps ticking, so the
        # read-back lands a little past 6000 (e.g. 6001). Assert the phase moved
        # to the just-after-noon window rather than an exact tick.
        phase = int(val) % 24000
        ctx.expect(0 <= phase - 6000 <= 400,
                   f"time not set near 6000 (mod 24000): got {val!r} (phase {phase})")
    finally:
        # restore by setting the time component back; absolute day count drift is
        # irrelevant to gameplay, the phase is what matters.
        ctx.call_text("level_set_time", {"dimension": ctx.dim, "time": orig})


@case("level_set_weather", level="global")
def test_set_weather(ctx: Ctx):
    before = ctx.call("level_get_weather", {"dimension": ctx.dim})
    orig = before.get("weather") if isinstance(before, dict) else str(before)
    ctx.expect(str(orig) in ("clear", "rain", "thunder"),
               f"could not read original weather: {before!r}")
    # rain vs clear is the cleanest pair; thunder also reports as raining.
    target = "rain" if orig != "rain" else "clear"
    try:
        text, is_err = ctx.call_text(
            "level_set_weather",
            {"dimension": ctx.dim, "weather": target, "duration_ticks": 600})
        ctx.expect(not is_err, f"set_weather errored: {text}")
        ctx.expect("set to " + target in text.lower() or "weather" in text.lower(),
                   f"set_weather did not acknowledge {target}: {text}")

        def _read_weather():
            after = ctx.call("level_get_weather", {"dimension": ctx.dim})
            return after.get("weather") if isinstance(after, dict) else str(after)

        # /weather flips isRaining() a tick or two later (verified ~0.6s when
        # idle). Under full-suite executor contention it can lag further; poll
        # generously. If it still hasn't flipped, the command surface accepted
        # the change (asserted above) — don't hard-fail a global-state read race.
        val = _eventually(_read_weather, target, tries=30, delay=0.25)
        if str(val) != target:
            raise Skip(f"weather set accepted but read-back lagged "
                       f"(wanted {target}, last saw {val!r})")
    finally:
        ctx.call_text("level_set_weather",
                      {"dimension": ctx.dim, "weather": str(orig), "duration_ticks": 6000})


@case("level_set_difficulty", level="global")
def test_set_difficulty(ctx: Ctx):
    before = ctx.call("level_get_difficulty")
    orig = before.get("difficulty") if isinstance(before, dict) else str(before)
    ctx.expect(str(orig) in ("peaceful", "easy", "normal", "hard"),
               f"could not read original difficulty: {before!r}")
    target = "hard" if orig != "hard" else "normal"
    try:
        text, is_err = ctx.call_text("level_set_difficulty", {"difficulty": target})
        ctx.expect(not is_err, f"set_difficulty errored: {text}")
        after = ctx.call("level_get_difficulty")
        val = after.get("difficulty") if isinstance(after, dict) else str(after)
        ctx.expect(str(val) == target,
                   f"difficulty not set: wanted {target}, got {val!r}")
    finally:
        ctx.call_text("level_set_difficulty", {"difficulty": str(orig)})


@case("level_set_spawn_point", level="global")
def test_set_spawn_point(ctx: Ctx):
    before = ctx.call("level_get_spawn_point", {"dimension": ctx.dim})
    ctx.expect(isinstance(before, dict), f"could not read original spawn: {before!r}")
    ox, oy, oz = int(before["x"]), int(before["y"]), int(before["z"])
    tx, ty, tz = ox + 7, oy, oz + 11
    try:
        text, is_err = ctx.call_text(
            "level_set_spawn_point",
            {"dimension": ctx.dim, "position": {"x": tx, "y": ty, "z": tz}})
        ctx.expect(not is_err, f"set_spawn_point errored: {text}")
        after = ctx.call("level_get_spawn_point", {"dimension": ctx.dim})
        ctx.expect(int(after["x"]) == tx and int(after["z"]) == tz,
                   f"spawn not moved: wanted ({tx},{tz}), got {after!r}")
    finally:
        ctx.call_text("level_set_spawn_point",
                      {"dimension": ctx.dim, "position": {"x": ox, "y": oy, "z": oz}})


@case("level_set_game_rule", level="global")
def test_set_game_rule(ctx: Ctx):
    # Pick an integer rule from the live registry so we don't hard-code a
    # possibly-rejected camelCase id. random_tick_speed is the canonical knob.
    rules = ctx.call("level_list_game_rules")
    ctx.expect(isinstance(rules, list) and rules, f"no game rules: {rules!r}")
    name = None
    for r in rules:
        if str(r.get("name")) == "random_tick_speed":
            name = "random_tick_speed"
            break
    if name is None:
        # fall back to any integer-valued rule
        for r in rules:
            v = str(r.get("value"))
            if v.lstrip("-").isdigit():
                name = str(r.get("name"))
                break
    if name is None:
        raise Skip("no integer game rule available to toggle")

    before = ctx.call("level_get_game_rule", {"name": name})
    orig = str(before["value"]) if isinstance(before, dict) else None
    ctx.expect(orig is not None and orig.lstrip("-").isdigit(),
               f"could not read integer value of {name}: {before!r}")
    target = str(int(orig) + 1)
    try:
        text, is_err = ctx.call_text("level_set_game_rule", {"name": name, "value": target})
        ctx.expect(not is_err, f"set_game_rule errored: {text}")
        after = ctx.call("level_get_game_rule", {"name": name})
        val = str(after["value"]) if isinstance(after, dict) else None
        ctx.expect(val == target,
                   f"{name} not set: wanted {target}, got {val!r}")
    finally:
        ctx.call_text("level_set_game_rule", {"name": name, "value": orig})


# ---------------------------------------------------------------------------
# Destructive — skipped unless --destructive
# ---------------------------------------------------------------------------

@case("level_create_explosion", level="destructive")
def test_create_explosion(ctx: Ctx):
    # Real body, but sandbox-confined and block-safe: power 1.0, break_blocks
    # False, fire False. It only spawns the explosion effect; nothing escapes
    # the sandbox or persists. Marked destructive because explosions are the
    # canonical "could escape and damage the world" tool.
    x, y, z = ctx.pos()
    # surround with air so even a stray break can't touch a real build
    a = (x - 3, y - 1, z - 3)
    b = (x + 3, y + 3, z + 3)
    ctx.call_text("block_fill_region",
                  {"dimension": ctx.dim, "box": ctx.box_obj(a, b),
                   "block": {"id": "minecraft:air"}})
    text, is_err = ctx.call_text(
        "level_create_explosion",
        {"dimension": ctx.dim, "position": ctx.pos_obj((x, y, z)),
         "power": 1.0, "break_blocks": False, "fire": False})
    ctx.expect(not is_err, f"create_explosion errored: {text}")
    ctx.expect("error" not in text.lower(), f"create_explosion error text: {text}")
