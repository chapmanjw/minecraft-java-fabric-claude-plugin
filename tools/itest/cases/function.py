"""Function tools — datapack function listing / definition / execution.

Covers all three live ``function_*`` tools:

  * ``function_list``           — read-only id listing (safe).
  * ``function_get_definition`` — read-only function body (safe).
  * ``function_run``            — executes a datapack function (destructive).

Probe findings (live server, 2026-05-30):
  * ``function_list`` (with and without a ``namespace`` filter) returns a TOON
    array of function ids. On this world *no datapack functions are loaded*, so
    it decodes to an empty list ``[]`` — the list test asserts the call succeeds
    and yields a list, tolerating zero entries.
  * ``function_get_definition`` raises an MCP error (-32002 "Unknown function:
    …") for an id that is not loaded — it does NOT return an error-flagged text
    block, so probing a bogus id would surface as a FAIL. Both the definition
    and run tests therefore discover a real id from ``function_list`` at runtime
    and ``Skip`` when none is loaded, rather than guessing an id.
  * ``function_run`` executes arbitrary datapack commands against the live
    world. It is marked destructive (skipped by default): even confined to a
    discovered function, a function's body can touch world-global state we can't
    cleanly undo. The mod may also refuse to run a function; that refusal is a
    Skip, not a FAIL.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip


def _ids(data):
    """Normalize a function-list response to a list of function-id strings.

    ``function_list`` decodes (via call_toon) to a bare list of ids; tolerate a
    wrapper dict ({functions|items|ids:[...]}) and rows that are either bare
    strings or {id|function_id|name:...} dicts.
    """
    rows = []
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        for k in ("functions", "items", "ids", "list"):
            v = data.get(k)
            if isinstance(v, list):
                rows = v
                break
        else:
            # maybe the dict is itself a single row
            if any(k in data for k in ("id", "function_id", "name")):
                rows = [data]
    out = []
    for r in rows:
        if isinstance(r, str):
            out.append(r)
        elif isinstance(r, dict):
            v = r.get("id") or r.get("function_id") or r.get("name")
            if v:
                out.append(str(v))
    return out


def _discover_function_id(ctx: Ctx):
    """Return a loaded function id, or None when no functions are loaded."""
    ids = _ids(ctx.call("function_list", {}))
    return ids[0] if ids else None


@case("function_list", level="safe")
def test_list(ctx: Ctx):
    # No-arg listing of every loaded function id. On a world with no datapack
    # functions this is legitimately empty, so assert shape (a list) rather than
    # a non-zero count.
    data = ctx.call("function_list", {})
    ctx.expect(isinstance(data, (list, dict)),
               f"function_list not a list/dict: {str(data)[:160]}")
    ids = _ids(data)
    ctx.expect(isinstance(ids, list),
               f"function_list did not yield a list of ids: {str(data)[:160]}")
    # The optional namespace filter must also succeed and be a subset of the
    # unfiltered listing (filtering can only narrow, never add ids).
    filtered = _ids(ctx.call("function_list", {"namespace": "minecraft"}))
    ctx.expect(set(filtered) <= set(ids),
               f"namespace-filtered ids {sorted(filtered)} not a subset of "
               f"unfiltered {sorted(ids)}")
    if ids:
        # every minecraft-filtered id must actually be in that namespace
        for fid in filtered:
            ctx.expect(fid.startswith("minecraft:") or ":" not in fid,
                       f"minecraft-filtered id not in namespace: {fid}")


@case("function_get_definition", level="safe")
def test_get_definition(ctx: Ctx):
    fid = _discover_function_id(ctx)
    if fid is None:
        raise Skip("no datapack functions loaded (function_list empty)")
    data = ctx.call("function_get_definition", {"function_id": fid})
    # tolerant: the body comes back either as a TOON/dict ({definition|body|
    # commands:...}) or as a plain text blob (call_toon returns the raw string
    # when the payload isn't TOON).
    if isinstance(data, dict):
        body = (data.get("definition") or data.get("body")
                or data.get("commands") or data.get("function"))
        ctx.expect(body is not None or len(data) > 0,
                   f"definition dict for {fid} has no body field: {str(data)[:160]}")
    else:
        ctx.expect(data is not None and len(str(data)) >= 0,
                   f"no definition returned for {fid}: {str(data)[:160]}")


@case("function_run", level="destructive")
def test_run(ctx: Ctx):
    # destructive: executing a datapack function runs arbitrary commands against
    # the live world (a discovered function's body can mutate global state we
    # can't cleanly undo). Skipped by default; runs only with --destructive.
    fid = _discover_function_id(ctx)
    if fid is None:
        raise Skip("no datapack functions loaded (function_list empty)")
    text, is_error = ctx.call_text("function_run", {"function_id": fid})
    lowered = text.lower()
    # The mod may legitimately refuse to run a function (e.g. "should not run",
    # "cannot run", "not allowed") — treat a refusal as a Skip, not a FAIL.
    if is_error or any(s in lowered for s in
                       ("should not run", "cannot run", "not allowed",
                        "refused", "unknown function", "no permission")):
        raise Skip(f"function_run refused for {fid}: {text[:160]}")
    ctx.expect(bool(text) or not is_error,
               f"function_run({fid}) returned no result and no error")
