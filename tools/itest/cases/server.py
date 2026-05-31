"""Server tools — status / motd / save / reload.

Covers the five live ``server_*`` tools:
  server_get_status        safe         (read-only introspection)
  server_get_motd          safe         (read-only)
  server_save_all_worlds   safe         (flush worlds to disk; non-destructive)
  server_set_motd          global       (save current MOTD, set, assert, restore)
  server_reload_resources  destructive  (equivalent to /reload — session-affecting)

server_get_status returns a TOON object (-> dict). server_get_motd returns a
bare MOTD string, so it is probed with call_text and handled tolerantly.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip


def _motd_text(ctx: Ctx) -> str:
    """Read the current MOTD as a plain string (response is a bare string)."""
    text, is_error = ctx.call_text("server_get_motd", {})
    ctx.expect(not is_error, f"server_get_motd returned error: {text}")
    return (text or "").strip()


@case("server_get_status", level="safe")
def test_get_status(ctx: Ctx):
    data = ctx.call("server_get_status", {})
    ctx.expect(isinstance(data, dict), f"status should parse to a dict, got: {str(data)[:160]}")
    # Tolerant: assert a couple of stable, likely-present fields rather than the
    # whole schema. minecraftVersion + onlinePlayerCount are core to the tool.
    ver = ctx.expect_field(data, "minecraftVersion")
    ctx.expect(bool(str(ver)), f"empty minecraftVersion: {data}")
    ctx.expect_field(data, "onlinePlayerCount")


@case("server_get_motd", level="safe")
def test_get_motd(ctx: Ctx):
    motd = _motd_text(ctx)
    # The MOTD can legitimately be empty, but the call must succeed and return a
    # string-shaped, non-error payload (asserted in _motd_text).
    ctx.expect(isinstance(motd, str), f"motd should be a string, got: {motd!r}")


@case("server_save_all_worlds", level="safe")
def test_save_all_worlds(ctx: Ctx):
    # Flush every loaded world to disk — safe, idempotent, non-destructive.
    text, is_error = ctx.call_text("server_save_all_worlds", {"flush": True})
    ctx.expect(not is_error, f"save_all_worlds returned error: {text}")
    ctx.expect("error" not in text.lower() or "saved" in text.lower(),
               f"save_all_worlds unexpected output: {text}")


@case("server_set_motd", level="global")
def test_set_motd(ctx: Ctx):
    # GLOBAL: read current value, set a test value, assert it took, then RESTORE.
    original = _motd_text(ctx)
    test_motd = "mcb itest motd probe"
    try:
        text, is_error = ctx.call_text("server_set_motd", {"motd": test_motd})
        ctx.expect(not is_error, f"set_motd returned error: {text}")
        # Verify the side effect: read it back.
        now = _motd_text(ctx)
        ctx.expect(now == test_motd, f"motd not applied: expected {test_motd!r}, got {now!r}")
    finally:
        # Restore the original MOTD regardless of assertion outcome.
        ctx.call_text("server_set_motd", {"motd": original})


@case("server_reload_resources", level="destructive")
def test_reload_resources(ctx: Ctx):
    # DESTRUCTIVE: equivalent to /reload — re-reads datapacks/resources, which is
    # session-affecting and cannot be cleanly undone. Skipped by default; a real
    # body runs only under --destructive.
    text, is_error = ctx.call_text("server_reload_resources", {})
    # /reload can legitimately report "should not run" / a refusal in some mod
    # configurations — treat that as a Skip rather than a failure.
    low = (text or "").lower()
    if "should not run" in low or "cannot" in low or "not allowed" in low:
        raise Skip(f"reload refused by mod: {text}")
    ctx.expect(not is_error, f"reload_resources returned error: {text}")
    ctx.expect(text is not None, "reload_resources returned no response")
