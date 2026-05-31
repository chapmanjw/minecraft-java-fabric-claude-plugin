"""Datapack tools — list available/enabled (safe) and enable/disable (global).

The list_* tools take no args and return a TOON array of
{id, displayName, enabled, builtin} rows (decoded by call_toon as a list of
dicts). enable/disable mutate the world-global enabled set, so that test reads
the current enabled ids first, toggles a currently-disabled pack, asserts the
toggle took, and restores the original enabled set in a finally block.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip
from builder.mcpclient import McpError


def _rows(data):
    """Normalize a datapack-list response to a list of row dicts."""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        # tolerate a wrapper like {"datapacks": [...]} or a single row
        for k in ("datapacks", "packs", "available", "enabled", "items"):
            v = data.get(k)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
        if "id" in data:
            return [data]
    return []


def _ids(data):
    return {r.get("id") for r in _rows(data) if r.get("id")}


@case("datapack_list_available")
def test_list_available(ctx: Ctx):
    data = ctx.call("datapack_list_available", {})
    rows = _rows(data)
    ctx.expect(len(rows) > 0, f"no datapacks listed: {data}")
    # every world has the built-in vanilla pack
    ids = _ids(data)
    ctx.expect("vanilla" in ids, f"expected 'vanilla' among available packs, got {sorted(ids)}")
    # rows carry the documented fields
    sample = rows[0]
    ctx.expect_field(sample, "id")
    ctx.expect("enabled" in sample, f"row missing 'enabled' field: {sample}")


@case("datapack_list_enabled")
def test_list_enabled(ctx: Ctx):
    data = ctx.call("datapack_list_enabled", {})
    rows = _rows(data)
    ctx.expect(len(rows) > 0, f"no enabled datapacks listed: {data}")
    ids = _ids(data)
    # vanilla is always enabled
    ctx.expect("vanilla" in ids, f"expected 'vanilla' among enabled packs, got {sorted(ids)}")
    # enabled list must be a subset of available, and every row flagged enabled
    avail_ids = _ids(ctx.call("datapack_list_available", {}))
    ctx.expect(ids <= avail_ids, f"enabled ids {sorted(ids)} not a subset of available {sorted(avail_ids)}")
    for r in rows:
        ctx.expect(r.get("enabled") in (True, None),
                   f"pack {r.get('id')} appears in enabled list but enabled={r.get('enabled')!r}")


_FEATURE_FLAG_PACKS = frozenset({
    "minecart_improvements", "trade_rebalance", "redstone_experiments",
})


@case("datapack_enable", level="global")
@case("datapack_disable", level="global")
def test_enable_disable(ctx: Ctx):
    """Toggle a currently-disabled pack on then off, restoring the enabled set.

    Fixed in R5: datapack_enable/disable now drives PackRepository.setSelected +
    reloadResources. Two cases are handled:

    1. Ordinary (non-feature-flag) disabled pack: enable it, assert it joins
       the enabled list, disable it, assert it leaves. Restore in finally.

    2. Feature-flag pack (minecart_improvements, trade_rebalance,
       redstone_experiments): enabling requires a feature flag that isn't present;
       the mod now returns a clear error whose message names the missing feature or
       flag — NOT a bare "failed". Assert that the error message contains at least
       one of: "feature", "flag", the pack id, or a named experimental keyword.

    If no disabled packs exist at all, the test is skipped.
    """
    avail = _rows(ctx.call("datapack_list_available", {}))
    before_enabled = _ids(ctx.call("datapack_list_enabled", {}))

    # Partition disabled (non-vanilla, non-builtin) packs into ordinary and
    # feature-flag buckets so we can pick the right assertion path.
    ordinary_candidates = []
    feature_flag_candidates = []
    for r in avail:
        pid = r.get("id")
        if not pid or pid == "vanilla":
            continue
        if r.get("builtin") is True:
            continue
        if pid in before_enabled or r.get("enabled") is True:
            continue
        if pid in _FEATURE_FLAG_PACKS:
            feature_flag_candidates.append(pid)
        else:
            ordinary_candidates.append(pid)

    if not ordinary_candidates and not feature_flag_candidates:
        raise Skip("no toggleable (disabled, non-builtin) datapack available to test enable/disable")

    if ordinary_candidates:
        # --- ordinary pack: full round-trip enable → disable ---
        candidate = ordinary_candidates[0]
        text, is_err = ctx.call_text("datapack_enable", {"id": candidate})
        ctx.expect(not is_err and "fail" not in text.lower(),
                   f"datapack_enable({candidate!r}) should succeed for an ordinary pack: {text!r}")
        try:
            after_enable = _ids(ctx.call("datapack_list_enabled", {}))
            ctx.expect(candidate in after_enable,
                       f"{candidate} not in enabled set after enable: {sorted(after_enable)}")

            text, is_err = ctx.call_text("datapack_disable", {"id": candidate})
            ctx.expect(not is_err, f"datapack_disable({candidate}) errored: {text}")
            after_disable = _ids(ctx.call("datapack_list_enabled", {}))
            ctx.expect(candidate not in after_disable,
                       f"{candidate} still in enabled set after disable: {sorted(after_disable)}")
        finally:
            # Restore: candidate was disabled before; ensure it ends disabled.
            now_enabled = _ids(ctx.call("datapack_list_enabled", {}))
            if candidate in now_enabled:
                ctx.call_text("datapack_disable", {"id": candidate})
            final_enabled = _ids(ctx.call("datapack_list_enabled", {}))
            for pid in before_enabled - final_enabled:
                ctx.call_text("datapack_enable", {"id": pid})
    else:
        # --- only feature-flag packs available: assert the error is descriptive ---
        # R5 fix: the mod raises a descriptive McpError (-32002) naming the missing
        # feature flag, rather than returning a bare "failed" text response.
        # call_text raises McpError for JSON-RPC errors, so we catch it here.
        candidate = feature_flag_candidates[0]
        error_msg = None
        try:
            text, is_err = ctx.call_text("datapack_enable", {"id": candidate})
            # If it somehow returned text rather than raising, treat as a failure response.
            if is_err or "fail" in text.lower():
                error_msg = text
            else:
                ctx.expect(False,
                           f"expected datapack_enable({candidate!r}) to fail (feature-flag pack), "
                           f"but it reported success: {text!r}")
        except McpError as exc:
            error_msg = str(exc)

        ctx.expect(error_msg is not None,
                   f"datapack_enable({candidate!r}) should have failed for a feature-flag pack")
        lower = error_msg.lower()
        descriptive = any(kw in lower for kw in (
            "feature", "flag", candidate.lower(), "experimental", "missing", "require",
        ))
        ctx.expect(descriptive,
                   f"datapack_enable({candidate!r}) error lacks feature/flag detail "
                   f"(R5 fix should name the missing flag): {error_msg!r}")
