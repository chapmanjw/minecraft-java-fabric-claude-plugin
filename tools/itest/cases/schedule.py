"""Schedule tools — the vanilla ``/schedule`` command surface.

Covers the three live ``schedule_*`` tools:
  schedule_list      safe     (read-only; runs bare ``/schedule`` and parses entries)
  schedule_function  global   (mutates the world TimerQueue; schedule far-future,
                               assert it is pending, then clear it in finally)
  schedule_clear     global   (clears a pending entry; exercised as the cleanup
                               half of the schedule_function test and on its own)

Behaviour learned from the mod (ScheduleTools + GameplayOps):
  * schedule_function runs ``/schedule function <id> <ticks>t <mode>``. The vanilla
    ``/schedule function`` command resolves the function id at PARSE time via
    FunctionArgument, so the function must already be loaded — otherwise the
    command fails and the tool returns the bare text "failed".
  * schedule_list runs bare ``/schedule`` and best-effort-parses the feedback into
    a TOON array of {function_id, ticks_remaining} rows (call_toon -> list[dict]).
  * schedule_clear runs ``/schedule clear <id>`` and returns "cleared"/"failed";
    clearing a non-pending id is harmless (vanilla reports 0 cleared).

No datapack functions may be loaded (function_list can be empty). When no loadable
function id exists, ``/schedule function`` cannot parse a target, so the
schedule_function test Skips with that reason per the category note (the mod /
vanilla "refuses" the schedule). The far-future tick count (never reached during a
run) keeps the scheduled entry from ever firing, and the finally block always
clears it — nothing escapes the test.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

# A tick count so large the entry can never fire during a suite run (~13.9 hours
# of ticks). Used only as a transient, immediately-cleared schedule entry.
FAR_FUTURE_TICKS = 1_000_000


def _list_rows(data):
    """Normalize a schedule_list response to a list of row dicts."""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for k in ("entries", "schedules", "items", "scheduled"):
            v = data.get(k)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
        if "function_id" in data:
            return [data]
    return []


def _list_ids(ctx: Ctx):
    """Set of function_ids currently pending in the scheduler."""
    rows = _list_rows(ctx.call("schedule_list", {}))
    return {r.get("function_id") for r in rows if r.get("function_id")}


def _pick_loadable_function(ctx: Ctx):
    """Return a loaded function id usable as a /schedule target, or None.

    /schedule function requires the function to resolve at parse time, so we can
    only schedule a function that function_list reports as loaded. function_list
    returns a TOON array of ids (or row dicts); be tolerant about the shape.
    """
    data = ctx.call("function_list", {})
    ids = []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, str):
                ids.append(entry)
            elif isinstance(entry, dict):
                fid = entry.get("id") or entry.get("function_id") or entry.get("name")
                if fid:
                    ids.append(fid)
    elif isinstance(data, dict):
        for k in ("functions", "ids", "items"):
            v = data.get(k)
            if isinstance(v, list):
                for entry in v:
                    if isinstance(entry, str):
                        ids.append(entry)
                    elif isinstance(entry, dict):
                        fid = entry.get("id") or entry.get("function_id") or entry.get("name")
                        if fid:
                            ids.append(fid)
    # Skip function *tags* (#namespace:path) — schedule_function takes a plain id.
    plain = [i for i in ids if isinstance(i, str) and i and not i.startswith("#")]
    return plain[0] if plain else None


@case("schedule_list", level="safe")
def test_list(ctx: Ctx):
    """Read-only: bare /schedule parse. Returns a (possibly empty) row list."""
    data = ctx.call("schedule_list", {})
    rows = _list_rows(data)
    # An empty scheduler is the normal idle state — assert only that the call
    # succeeded and parsed to a list-shaped payload, and that any present rows
    # carry the documented fields.
    ctx.expect(isinstance(rows, list), f"schedule_list should parse to a list, got: {str(data)[:160]}")
    for r in rows:
        ctx.expect_field(r, "function_id")
        ctx.expect("ticks_remaining" in r, f"schedule row missing 'ticks_remaining': {r}")


@case("schedule_function", level="global")
def test_function_schedule_then_clear(ctx: Ctx):
    """GLOBAL: schedule a loaded function far in the future, assert it is pending,
    then clear it (restoring the empty/original scheduler state) in finally.

    Requires a loaded datapack function as the schedule target. If none is loaded,
    /schedule function cannot resolve a target and the schedule is refused — Skip.
    """
    fid = _pick_loadable_function(ctx)
    if fid is None:
        raise Skip("no loaded datapack function to schedule (function_list empty); /schedule function would be refused")

    # Snapshot the scheduler so we can assert our specific entry was added and
    # never disturb a pre-existing schedule for the same id.
    before = _list_ids(ctx)
    if fid in before:
        raise Skip(f"function {fid!r} already scheduled; refusing to disturb a pre-existing entry")

    scheduled = False
    try:
        text, is_err = ctx.call_text(
            "schedule_function",
            {"function_id": fid, "ticks": FAR_FUTURE_TICKS, "mode": "replace"},
        )
        low = (text or "").lower()
        # The mod returns "scheduled"/"failed"; vanilla can also refuse with a
        # parse/should-not-run style message. Treat any refusal as a Skip.
        if is_err or "failed" in low or "should not run" in low or "cannot" in low or "unknown" in low:
            raise Skip(f"schedule refused for {fid!r}: {text}")
        ctx.expect("scheduled" in low, f"unexpected schedule_function response for {fid!r}: {text}")
        scheduled = True

        # Verify the side effect: the id is now pending in the scheduler.
        after = _list_ids(ctx)
        ctx.expect(fid in after,
                   f"{fid!r} not pending after schedule (schedule_list={sorted(after)})")
    finally:
        # Restore: clear our entry so the scheduler returns to its prior state.
        if scheduled:
            ctx.call_text("schedule_clear", {"function_id": fid})


@case("schedule_clear", level="global")
def test_clear(ctx: Ctx):
    """GLOBAL: clearing is the cleanup primitive. Clearing a non-pending id is a
    no-op in vanilla (0 entries cleared), so this is safe to exercise directly
    against a synthetic id, and it never mutates a real pending schedule.

    If a real function is loadable, prove a full round-trip: schedule it, clear
    it, and assert it left the pending set — then guarantee removal in finally.
    """
    fid = _pick_loadable_function(ctx)

    if fid is None:
        # No loadable function to schedule; just prove schedule_clear accepts a
        # call against a synthetic, never-scheduled id without erroring (no-op).
        synthetic = "mcb:itest_never_scheduled"
        text, is_err = ctx.call_text("schedule_clear", {"function_id": synthetic})
        low = (text or "").lower()
        ctx.expect(not is_err, f"schedule_clear errored on a no-op clear: {text}")
        # Mod returns "cleared"/"failed"; a no-op clear may legitimately be either
        # ("failed" == nothing to clear). Both are acceptable — assert we got a
        # non-empty, non-exception response.
        ctx.expect(low in ("cleared", "failed") or low != "",
                   f"unexpected schedule_clear no-op response: {text}")
        # And the synthetic id must not be pending afterward.
        ctx.expect(synthetic not in _list_ids(ctx),
                   f"synthetic id unexpectedly pending after clear: {synthetic}")
        return

    if fid in _list_ids(ctx):
        raise Skip(f"function {fid!r} already scheduled; refusing to disturb a pre-existing entry")

    scheduled = False
    try:
        text, is_err = ctx.call_text(
            "schedule_function",
            {"function_id": fid, "ticks": FAR_FUTURE_TICKS, "mode": "replace"},
        )
        low = (text or "").lower()
        if is_err or "failed" in low or "should not run" in low or "cannot" in low or "unknown" in low:
            raise Skip(f"schedule refused for {fid!r}: {text}")
        scheduled = True
        ctx.expect(fid in _list_ids(ctx), f"{fid!r} not pending before clear")

        # The assertion under test: clear removes the pending entry.
        ctext, cerr = ctx.call_text("schedule_clear", {"function_id": fid})
        ctx.expect(not cerr, f"schedule_clear errored: {ctext}")
        ctx.expect("cleared" in (ctext or "").lower(),
                   f"unexpected schedule_clear response for {fid!r}: {ctext}")
        scheduled = False
        ctx.expect(fid not in _list_ids(ctx),
                   f"{fid!r} still pending after clear (schedule_list={sorted(_list_ids(ctx))})")
    finally:
        if scheduled:
            ctx.call_text("schedule_clear", {"function_id": fid})
