"""Command tools — run slash commands as the console or as an entity.

Covers the three live ``command_*`` tools:
  * command_execute     run a benign read command as the console (safe).
  * command_execute_as  run a benign command as a summoned sandbox entity (safe).
  * command_register    reserved/no-op in this build (destructive — can't unregister).

The harness itself calls ``command_execute`` for forceload/cleanup, so an outright
break there would fail the whole run; these cases assert the documented response
shape on top of that.

Notes on this 26.1.x target:
  * ``time query daytime`` is rejected (the ``daytime`` timeline element doesn't
    exist); ``time query day`` is the valid read form, so that's the probe.
  * command_execute / command_execute_as return a dict with a ``successCount``
    int and an ``output`` list (TOON-decoded).
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip


def _success_count(data):
    """Pull successCount out of a command_execute(_as) response, tolerantly."""
    if isinstance(data, dict):
        return data.get("successCount")
    return None


@case("command_execute", level="safe")
def test_execute(ctx: Ctx):
    # Benign read: a query command that mutates nothing. `time query day`
    # returns the world day count; `daytime` is invalid on this target.
    text, is_error = ctx.call_text("command_execute", {"command": "time query day"})
    ctx.expect(not is_error, f"command_execute reported error: {text}")
    data = ctx.call("command_execute", {"command": "time query day"})
    ctx.expect(isinstance(data, dict), f"expected a dict response, got {data!r}")
    # The console source ran successfully -> at least one success, no command error.
    sc = _success_count(data)
    ctx.expect(sc is not None, f"response missing successCount: {data}")
    ctx.expect("output" in data, f"response missing output list: {data}")
    ctx.expect("error" not in data, f"command_execute surfaced an error: {data}")
    ctx.expect(isinstance(sc, int) and sc >= 1,
               f"expected successCount>=1 for 'time query day', got {sc}: {data}")


@case("command_execute_as", level="safe")
def test_execute_as(ctx: Ctx):
    # /execute as needs an actor. No players are online, so summon a harmless,
    # stationary marker armor stand inside the (force-loaded) sandbox and run a
    # benign `data get` as it. Tear the entity down in finally.
    p = ctx.pos()
    summon = ctx.call("entity_summon", {
        "dimension": ctx.dim,
        "entity_type": "minecraft:armor_stand",
        "position": ctx.pos_obj(p),
        "nbt": '{Marker:1b,NoGravity:1b,Invisible:1b,Tags:["mcb_itest_cmd"]}',
    })
    uuid = ctx.expect_field(summon, "uuid", f"entity_summon gave no uuid: {summon}")
    try:
        # `data get entity @s Pos` reads the actor's own position — no mutation.
        text, is_error = ctx.call_text(
            "command_execute_as", {"actor": uuid, "command": "data get entity @s Pos"})
        ctx.expect(not is_error, f"command_execute_as reported error: {text}")
        data = ctx.call(
            "command_execute_as", {"actor": uuid, "command": "data get entity @s Pos"})
        ctx.expect(isinstance(data, dict), f"expected a dict response, got {data!r}")
        sc = _success_count(data)
        ctx.expect(sc is not None, f"response missing successCount: {data}")
        # Running as a valid actor -> exactly the one success.
        ctx.expect(isinstance(sc, int) and sc >= 1,
                   f"expected successCount>=1 running as actor, got {sc}: {data}")
    finally:
        try:
            ctx.call_text("entity_kill", {"uuid": uuid})
        except Exception:  # noqa: BLE001 — best-effort cleanup; sandbox clear is the backstop
            pass


@case("command_register", level="destructive")
def test_register(ctx: Ctx):
    # Reserved capability: in this build command_register accepts the call but
    # does NOT actually register a runtime command (no webhook channel yet), or
    # returns an actionable error saying so. Either is acceptable — we can't
    # cleanly unregister a real command, hence destructive. Assert the call is
    # handled (returns a response) and, if it claims success, that nothing was
    # actually wired up. Use call_text so an isError result doesn't raise.
    try:
        text, is_error = ctx.call_text(
            "command_register",
            {"name": "mcb_itest_noop", "handler_url": "http://127.0.0.1:9/itest"})
    except Exception as e:  # noqa: BLE001 — a JSON-RPC McpError is the documented refusal
        raise Skip(f"command_register refused (reserved capability): {e}")
    low = (text or "").lower()
    # If the mod surfaced a "reserved / not registered / should not run" style
    # message, that's the documented behavior — accept it as a pass.
    refused_markers = ("reserved", "not register", "future", "v0.2", "unsupported",
                       "should not run", "not supported", "not implemented")
    if is_error or any(m in low for m in refused_markers):
        return
    # Otherwise it reported success. Per the build it's a no-op, so the command
    # must NOT be live: running it as the console should fail (unknown command).
    out, _ = ctx.call_text("command_execute", {"command": "mcb_itest_noop"})
    ctx.expect("mcb_itest_noop" not in out or "error" in out.lower()
               or "unknown" in out.lower() or "find element" in out.lower(),
               f"command_register appears to have registered a live command: {out}")
