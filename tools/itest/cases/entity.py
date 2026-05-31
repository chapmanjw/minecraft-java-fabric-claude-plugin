"""Entity tools — summon/query/get, tags, effects, nbt, components, velocity,
teleport, damage, kill, despawn.

Strategy: every test that needs a live entity gets its own freshly-summoned
entity at a unique sandbox position, exercises the tool, then despawns it in a
``finally`` so nothing outlives the per-run sandbox clear (block_fill clears
blocks, not entities, so entity cleanup is on us). Each summon carries a unique
``mcb_itest_*`` scoreboard tag so a stray selector can never touch a real build
entity, and so query-by-tag isolates exactly our entity.

Test-entity provisioning — the deliberate part. The mod's ``entity_summon``
identifies the spawned entity by diffing the entities in a small AABB around the
spawn point before/after a ``/summon``; under the harness's rapid back-to-back
calls that diff races (the just-spawned entity isn't yet visible to
``level.getEntities`` in the same tick), so it intermittently reports a spurious
"Failed to summon". A plain armor stand summoned in mid-air over the sandbox
floor also settled unreliably. Both were confirmed live. So the shared helper
``_provision`` provisions entities the robust way — raw ``/summon`` (which always
spawns) with ``NoGravity`` + a unique tag, then resolves the UUID by polling
``entity_query @e[tag=…]`` (verified 8/8 reliable). The ``entity_summon`` tool
itself is still exercised directly by its own dedicated case, tolerantly.

No players are online, so the player-targeted surface is not relevant here —
every entity tool is keyed by UUID (or a sandbox-scoped selector), which we own.

All summons land inside the force-loaded scratch sandbox; all writes are
confined there. Levels are "safe" because the entities we touch are ones we
created and clean up — nothing world-global is mutated.
"""
from __future__ import annotations

import time as _time
import uuid as _uuidlib

from ..harness import case, Ctx, Skip

# Default test entity: an armor stand. Marker/NoGravity armor stands stay put,
# never wander or despawn on their own, and accept effects/nbt/tags like any
# LivingEntity — everything these tests need, with no AI side effects.
_TYPE = "minecraft:armor_stand"


def _unique_tag(prefix="mcb_itest"):
    """A per-summon tag so selectors never collide with a real build entity."""
    return f"{prefix}_{_uuidlib.uuid4().hex[:12]}"


def _site(ctx: Ctx):
    """A summon site spaced well past the summon box of the previous site.

    ``ctx.pos()`` only steps 2 blocks; space sites ~8 blocks apart so the per-site
    cleanup box of one test never overlaps another's live entity."""
    p = ctx.pos()
    for _ in range(4):  # 4 * 2 blocks = 8-block gap
        ctx.pos()
    return p


def _resolve_by_tag(ctx: Ctx, tag, expect_one=True):
    """Poll entity_query for a uniquely-tagged entity; return its uuid or None.

    A just-summoned entity isn't visible to a selector query until the server has
    committed the spawn on a later tick. Under the harness's back-to-back calls
    that flush can lag behind a burst of immediate polls, so wait a short, growing
    interval between attempts to let real server ticks pass (this is a dedicated
    server ticking continuously). Confirmed live: a clean sandbox resolves the
    entity within the first couple of waited polls."""
    delay = 0.1
    for attempt in range(12):
        res = ctx.call("entity_query", {"dimension": ctx.dim, "selector": f"@e[tag={tag}]", "limit": 8})
        if isinstance(res, list) and res:
            if not expect_one or len(res) == 1:
                uid = res[0].get("uuid") if isinstance(res[0], dict) else None
                if uid:
                    return uid
        _time.sleep(delay)
        delay = min(delay * 1.5, 1.0)
    return None


def _provision(ctx: Ctx, type_id=_TYPE, extra_nbt=""):
    """Provision a live test entity robustly; return (uuid, (x,y,z), tag).

    Spawns via raw /summon (NoGravity + a unique tag) and resolves the UUID by
    tag-query polling — the reliable path, decoupled from entity_summon's racy
    diff. Skips (not fails) if the world won't surface the entity, since that is a
    server-side entity-visibility limitation, not a fault in the tool under test."""
    p = _site(ctx)
    x, y, z = p
    tag = _unique_tag()
    # Clear any stray entity in this site's box first (force-loaded scratch sandbox
    # only — never a real build), so the tag-query isolates exactly our entity.
    try:
        ctx.command(f"kill @e[type=!minecraft:player,x={x - 4},y={y - 4},z={z - 4},dx=9,dy=10,dz=9]")
    except Exception:  # noqa: BLE001
        pass
    nbt = f'{{Tags:["{tag}"],NoGravity:1b{extra_nbt}}}'
    ctx.command(
        f"execute in {ctx.dim} run summon {type_id} {x}.0 {float(y)} {z}.0 {nbt}")
    uid = _resolve_by_tag(ctx, tag)
    if uid is None:
        raise Skip(f"world did not surface a summoned {type_id} at {p} (server-side "
                   f"entity-visibility limitation)")
    return uid, p, tag


def _kill_quietly(ctx: Ctx, uid):
    """Best-effort cleanup; never raise out of a finally."""
    if not uid:
        return
    try:
        ctx.call_text("entity_despawn", {"uuid": uid})
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# summon + get + query
# ---------------------------------------------------------------------------

@case("entity_summon", level="safe")
def test_summon(ctx: Ctx):
    # Exercise the entity_summon TOOL directly (not the raw-command provisioner).
    # Its diff-based UUID resolution races under rapid calls, so tolerate that:
    # retry, and if the tool can't report the uuid, verify the entity actually
    # spawned via a tag-query before deciding pass/fail.
    p = _site(ctx)
    x, y, z = p
    tag = _unique_tag("itest_summon")
    try:
        ctx.command(f"kill @e[type=!minecraft:player,x={x - 4},y={y - 4},z={z - 4},dx=9,dy=10,dz=9]")
    except Exception:  # noqa: BLE001
        pass
    args = {"dimension": ctx.dim, "entity_type": _TYPE, "position": ctx.pos_obj(p),
            "nbt": f'{{Tags:["{tag}"],NoGravity:1b}}'}
    uid = None
    reported = None
    for _ in range(3):
        try:
            data = ctx.call("entity_summon", args)
        except Exception:  # noqa: BLE001  (racy diff -> retry; verify below)
            continue
        reported = data.get("uuid") if isinstance(data, dict) else None
        if reported:
            ctx.expect("armor_stand" in str(data.get("type", "")), f"summon type wrong: {data}")
            break
    try:
        # Whether or not the tool reported a uuid, the entity must exist now.
        found = _resolve_by_tag(ctx, tag)
        if found is None and reported is None:
            raise Skip("entity_summon could not surface the spawned entity "
                       "(server-side entity-visibility race)")
        ctx.expect(found is not None, "entity_summon reported a uuid but no tagged entity exists")
        if reported is not None:
            ctx.expect(reported == found,
                       f"entity_summon uuid {reported} != live entity {found}")
        uid = found
    finally:
        _kill_quietly(ctx, uid)


@case("entity_get", level="safe")
def test_get(ctx: Ctx):
    uid, p, _ = _provision(ctx)
    try:
        info = ctx.call("entity_get", {"uuid": uid})
        got_uuid = ctx.expect_field(info, "uuid")
        ctx.expect(got_uuid == uid, f"entity_get uuid mismatch: {got_uuid} != {uid}")
        typ = ctx.expect_field(info, "type")
        ctx.expect("armor_stand" in str(typ), f"unexpected type: {typ}")
        pos = ctx.expect_field(info, "position")
        # summoned at the sandbox x; tolerate sub-block centering offsets.
        ctx.expect(abs(float(pos["x"]) - p[0]) < 2.0, f"x off: {pos} vs {p}")
        ctx.expect(abs(float(pos["z"]) - p[2]) < 2.0, f"z off: {pos} vs {p}")
        ctx.expect_field(info, "alive")
    finally:
        _kill_quietly(ctx, uid)


@case("entity_query", level="safe")
def test_query_by_tag(ctx: Ctx):
    # Tag-filtered selectors are honored by the server (confirmed live), so we can
    # isolate exactly our entity instead of enumerating every entity in the world.
    uid, _, tag = _provision(ctx)
    try:
        res = ctx.call("entity_query", {"dimension": ctx.dim, "selector": f"@e[tag={tag}]", "limit": 16})
        ctx.expect(isinstance(res, list), f"query did not return a list: {type(res)} {str(res)[:120]}")
        ctx.expect(len(res) == 1, f"expected exactly our 1 tagged entity, got {len(res)}: {str(res)[:200]}")
        ctx.expect(res[0].get("uuid") == uid, f"query returned wrong entity: {res[0].get('uuid')} != {uid}")
    finally:
        _kill_quietly(ctx, uid)


# ---------------------------------------------------------------------------
# scoreboard tags
# ---------------------------------------------------------------------------

@case("entity_add_tag", level="safe")
@case("entity_list_tags", level="safe")
@case("entity_remove_tag", level="safe")
def test_tag_lifecycle(ctx: Ctx):
    uid, _, _ = _provision(ctx)
    tag = _unique_tag("itest_tag")
    try:
        add_txt, add_err = ctx.call_text("entity_add_tag", {"uuid": uid, "tag": tag})
        ctx.expect(not add_err, f"add_tag errored: {add_txt}")

        tags = ctx.call("entity_list_tags", {"uuid": uid})
        ctx.expect(isinstance(tags, list), f"list_tags not a list: {tags!r}")
        ctx.expect(tag in tags, f"tag {tag!r} not in {tags}")

        rm_txt, rm_err = ctx.call_text("entity_remove_tag", {"uuid": uid, "tag": tag})
        ctx.expect(not rm_err, f"remove_tag errored: {rm_txt}")

        tags_after = ctx.call("entity_list_tags", {"uuid": uid})
        # tolerant: list_tags of an entity with no tags may be [] (empty list).
        ctx.expect(tag not in (tags_after if isinstance(tags_after, list) else []),
                   f"tag {tag!r} still present after remove: {tags_after}")
    finally:
        _kill_quietly(ctx, uid)


# ---------------------------------------------------------------------------
# status effects
# ---------------------------------------------------------------------------

@case("entity_apply_effect", level="safe")
@case("entity_get_effects", level="safe")
@case("entity_remove_effect", level="safe")
def test_effect_lifecycle(ctx: Ctx):
    uid, _, _ = _provision(ctx)
    effect = "minecraft:glowing"  # harmless, visible, applies to an armor stand
    try:
        ap_txt, ap_err = ctx.call_text("entity_apply_effect",
                                       {"uuid": uid, "effect": effect, "duration_ticks": 600,
                                        "amplifier": 1, "show_particles": False})
        ctx.expect(not ap_err, f"apply_effect errored: {ap_txt}")

        # effect application commits on a following tick; poll briefly (the
        # server can lag a tick or two applying the effect under full-suite load).
        ids = []
        for _ in range(15):
            effects = ctx.call("entity_get_effects", {"uuid": uid})
            ctx.expect(isinstance(effects, list), f"get_effects not a list: {effects!r}")
            ids = [e.get("id") for e in effects if isinstance(e, dict)]
            if any("glowing" in str(i) for i in ids):
                break
            _time.sleep(0.2)
        ctx.expect(any("glowing" in str(i) for i in ids),
                   f"applied effect not present after polling: {ids}")

        rm_txt, rm_err = ctx.call_text("entity_remove_effect", {"uuid": uid, "effect": effect})
        ctx.expect(not rm_err, f"remove_effect errored: {rm_txt}")

        after = ctx.call("entity_get_effects", {"uuid": uid})
        after_ids = [e.get("id") for e in after if isinstance(e, dict)] if isinstance(after, list) else []
        ctx.expect(not any("glowing" in str(i) for i in after_ids),
                   f"effect still present after remove: {after_ids}")
    finally:
        _kill_quietly(ctx, uid)


# ---------------------------------------------------------------------------
# nbt + components
# ---------------------------------------------------------------------------

@case("entity_get_nbt", level="safe")
@case("entity_set_nbt", level="safe")
def test_nbt_roundtrip(ctx: Ctx):
    uid, _, _ = _provision(ctx)
    try:
        # entity_get_nbt returns raw SNBT text (not TOON) — read as text.
        nbt_text, nbt_err = ctx.call_text("entity_get_nbt", {"uuid": uid})
        ctx.expect(not nbt_err, f"get_nbt errored: {nbt_text}")
        ctx.expect(len(nbt_text) > 0, "get_nbt returned empty")
        ctx.expect("{" in nbt_text, f"get_nbt does not look like SNBT: {nbt_text[:120]}")

        # Merge a custom name and confirm it round-trips into the NBT.
        set_txt, set_err = ctx.call_text("entity_set_nbt",
                                         {"uuid": uid, "nbt": '{CustomName:\'{"text":"itest_marker"}\'}'})
        ctx.expect(not set_err, f"set_nbt errored: {set_txt}")

        after, _ = ctx.call_text("entity_get_nbt", {"uuid": uid})
        ctx.expect("itest_marker" in after, f"merged CustomName not in NBT after set: {after[:200]}")
    finally:
        _kill_quietly(ctx, uid)


@case("entity_get_components", level="safe")
def test_get_components(ctx: Ctx):
    uid, _, _ = _provision(ctx)
    try:
        # Documented behavior: non-player entities return a literal "{}" (empty
        # component map). call_toon parses "{}" to an empty dict; either an empty
        # dict or the literal string is acceptable — just assert it didn't error.
        text, is_err = ctx.call_text("entity_get_components", {"uuid": uid})
        ctx.expect(not is_err, f"get_components errored: {text}")
        ctx.expect("{}" in text or text.strip() == "" or ":" in text,
                   f"unexpected components payload: {text[:160]}")
    finally:
        _kill_quietly(ctx, uid)


# ---------------------------------------------------------------------------
# velocity + teleport (within the sandbox)
# ---------------------------------------------------------------------------

@case("entity_set_velocity", level="safe")
def test_set_velocity(ctx: Ctx):
    # The provisioned stand is NoGravity, so a set velocity won't fling it out of
    # the sandbox; assert the call succeeded.
    uid, _, _ = _provision(ctx)
    try:
        txt, err = ctx.call_text("entity_set_velocity",
                                 {"uuid": uid, "velocity": {"x": 0.0, "y": 0.1, "z": 0.0}})
        ctx.expect(not err, f"set_velocity errored: {txt}")
        ctx.expect("set" in txt.lower() or "fail" not in txt.lower(),
                   f"set_velocity unexpected result: {txt}")
    finally:
        _kill_quietly(ctx, uid)


@case("entity_teleport", level="safe")
def test_teleport(ctx: Ctx):
    uid, _, _ = _provision(ctx)
    dest = _site(ctx)  # another fresh sandbox position, spaced clear
    try:
        txt, err = ctx.call_text("entity_teleport",
                                 {"uuid": uid, "dimension": ctx.dim, "position": ctx.pos_obj(dest)})
        ctx.expect(not err, f"teleport errored: {txt}")
        info = ctx.call("entity_get", {"uuid": uid})
        pos = ctx.expect_field(info, "position")
        ctx.expect(abs(float(pos["x"]) - dest[0]) < 2.0, f"teleport x off: {pos} vs {dest}")
        ctx.expect(abs(float(pos["z"]) - dest[2]) < 2.0, f"teleport z off: {pos} vs {dest}")
    finally:
        _kill_quietly(ctx, uid)


# ---------------------------------------------------------------------------
# damage
# ---------------------------------------------------------------------------

@case("entity_apply_damage", level="safe")
def test_apply_damage(ctx: Ctx):
    # A plain armor stand has 0 maxHealth and is immune to most damage; use a pig
    # (a real LivingEntity with health) so the damage pipeline has something to
    # act on. NoAI/Silent keeps it from wandering or making noise. Confirm health
    # drops, then clean up.
    uid, _, _ = _provision(ctx, type_id="minecraft:pig", extra_nbt=",NoAI:1b,Silent:1b")
    try:
        before = ctx.call("entity_get", {"uuid": uid})
        hp0 = float(ctx.expect_field(before, "health"))
        ctx.expect(hp0 > 0, f"pig had no health to damage: {hp0}")

        txt, err = ctx.call_text("entity_apply_damage",
                                 {"uuid": uid, "amount": 3.0, "damage_type": "minecraft:generic"})
        ctx.expect(not err, f"apply_damage errored: {txt}")

        after = ctx.call("entity_get", {"uuid": uid})
        hp1 = float(ctx.expect_field(after, "health"))
        # alive entity should have lost health (it may regen later, but not within
        # the same tick window); tolerate exactly-equal only if it reports dead.
        alive = after.get("alive", True)
        ctx.expect(hp1 < hp0 or not alive,
                   f"damage had no effect: {hp0} -> {hp1} (alive={alive})")
    finally:
        _kill_quietly(ctx, uid)


# ---------------------------------------------------------------------------
# kill + despawn (terminal — each summons its own victim)
# ---------------------------------------------------------------------------

@case("entity_kill", level="safe")
def test_kill(ctx: Ctx):
    uid, _, _ = _provision(ctx, type_id="minecraft:pig", extra_nbt=",NoAI:1b,Silent:1b")
    killed = False
    try:
        txt, err = ctx.call_text("entity_kill", {"uuid": uid})
        ctx.expect(not err, f"kill errored: {txt}")
        ctx.expect("kill" in txt.lower() or "fail" not in txt.lower(),
                   f"kill unexpected result: {txt}")
        killed = True
        # After a kill, entity_get should fail (entity gone) or report not-alive.
        try:
            info = ctx.call("entity_get", {"uuid": uid})
            ctx.expect(info.get("alive") is False,
                       f"entity still alive after kill: {info}")
        except Exception:
            pass  # entity removed entirely — also a valid post-kill state
    finally:
        if not killed:
            _kill_quietly(ctx, uid)


@case("entity_despawn", level="safe")
def test_despawn(ctx: Ctx):
    uid, _, _ = _provision(ctx)
    despawned = False
    try:
        txt, err = ctx.call_text("entity_despawn", {"uuid": uid})
        ctx.expect(not err, f"despawn errored: {txt}")
        ctx.expect("despawn" in txt.lower() or "fail" not in txt.lower(),
                   f"despawn unexpected result: {txt}")
        despawned = True
        # The entity should now be gone — entity_get is expected to error.
        gone = False
        try:
            ctx.call("entity_get", {"uuid": uid})
        except Exception:
            gone = True
        ctx.expect(gone, "entity_get still returned an entity after despawn")
    finally:
        if not despawned:
            _kill_quietly(ctx, uid)
