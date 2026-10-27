"""Event tools — the subscribe / list / poll / unsubscribe lifecycle.

The events surface is a small, self-contained pub/sub: a subscription is created
for one or more event types, events accumulate in a server-side ring buffer, and
a client drains them with poll. Everything here is "safe": a subscription is a
read-only observer (it never mutates the world), and the test always removes the
subscription it created in a finally so no observer leaks past the run.

We subscribe to ``server.tick`` — it fires every tick on the dedicated server
regardless of players, so poll has events to drain without us having to provoke
anything (no player is online). The four tools share one lifecycle test so each
is exercised against a real, freshly-created subscription on every run.
"""
from __future__ import annotations

import time

from ..harness import case, Ctx


def _extract_subscription_id(data):
    """Pull the subscription_id out of an events_subscribe response.

    subscribe returns a TOON object ``{subscription_id: <uuid>}``; be tolerant of
    a couple of plausible field spellings, and of a bare string fallback."""
    if isinstance(data, dict):
        for k in ("subscription_id", "subscriptionId", "id"):
            if data.get(k):
                return str(data[k])
        return None
    if isinstance(data, str):
        return data.strip() or None
    return None


def _subscription_ids(listing):
    """Collect subscription_id values from an events_list_subscriptions result.

    list_subscriptions emits a *root* TOON array, which the reader decodes to a
    Python list of dicts (``[]`` when there are none). Tolerate a dict wrapper
    just in case the encoder ever nests it under a key."""
    rows = []
    if isinstance(listing, list):
        rows = listing
    elif isinstance(listing, dict):
        for v in listing.values():
            if isinstance(v, list):
                rows = v
                break
    ids = []
    for row in rows:
        if isinstance(row, dict):
            sid = row.get("subscription_id") or row.get("subscriptionId") or row.get("id")
            if sid:
                ids.append(str(sid))
    return ids


@case("events_subscribe", level="safe")
@case("events_list_subscriptions", level="safe")
@case("events_poll", level="safe")
@case("events_unsubscribe", level="safe")
def test_event_lifecycle(ctx: Ctx):
    """subscribe -> list (sees it) -> poll (drains ticks) -> unsubscribe (gone)."""
    sub = ctx.call("events_subscribe", {"event_types": ["server.tick"]})
    sid = _extract_subscription_id(sub)
    ctx.expect(sid is not None, f"events_subscribe gave no subscription_id: {sub}")

    try:
        # list_subscriptions must now include the subscription we just created.
        listing = ctx.call("events_list_subscriptions", {})
        ids = _subscription_ids(listing)
        ctx.expect(sid in ids,
                   f"list_subscriptions missing our id {sid}: {listing}")

        # poll: server.tick fires continuously on the dedicated server, so after
        # a brief wait there should be events to drain. Be tolerant of timing —
        # require a well-formed response with an events list, and (best effort)
        # confirm at least one server.tick came through.
        events = []
        for _ in range(5):
            res = ctx.call("events_poll", {"subscription_id": sid, "max": 16})
            drained = ctx.expect_field(res, "events")
            ctx.expect(isinstance(drained, list),
                       f"events_poll 'events' not a list: {res}")
            events.extend(drained)
            if events:
                break
            time.sleep(1.0)
        ctx.expect(events,
                   "events_poll drained no server.tick events after ~5s — "
                   "is the server ticking?")
        first = events[0]
        ctx.expect(isinstance(first, dict) and "type" in first,
                   f"polled event missing 'type': {first}")
        ctx.expect(any(str(e.get("type")) == "server.tick" for e in events),
                   f"no server.tick in drained events: {events[:3]}")
    finally:
        text, is_error = ctx.call_text("events_unsubscribe", {"subscription_id": sid})
        ctx.expect(not is_error, f"events_unsubscribe errored: {text}")

    # after unsubscribe the id must be gone from the active list.
    after = _subscription_ids(ctx.call("events_list_subscriptions", {}))
    ctx.expect(sid not in after,
               f"events_unsubscribe left {sid} active: {after}")

    if ctx.mc_at_least(26, 2) and ctx.mod_at_least(1, 2):
        _check_fluid_flow(ctx)


def _check_fluid_flow(ctx: Ctx):
    """fluid.flow (mod 1.2.0, Minecraft 26.2+): needs a region, delivers flow inside it, and
    reports its gate and rate-limit counter. One water source in the sandbox is enough; it
    fires hundreds of events a second, so the rate limit is exercised too."""
    try:
        ctx.call_text("events_subscribe", {"event_types": ["fluid.flow"]})
        refused = False
    except Exception:  # noqa: BLE001 - the JSON-RPC refusal is the expected outcome
        refused = True
    ctx.expect(refused, "fluid.flow without filters.region should be refused")

    x, y, z = ctx.pos()
    region = {"dimension": ctx.dim,
              "from": {"x": x - 3, "y": y - 1, "z": z - 3},
              "to": {"x": x + 3, "y": y + 1, "z": z + 3}}
    sub = ctx.call("events_subscribe", {"event_types": ["fluid.flow"],
                                        "filters": {"region": region, "max_per_second": 10}})
    sid = _extract_subscription_id(sub)
    ctx.expect(sid is not None, f"fluid.flow subscribe gave no id: {sub}")
    water = {"dimension": ctx.dim, "position": {"x": x, "y": y, "z": z}}
    try:
        ctx.call_text("block_set_state", dict(water, block={"id": "minecraft:water"}))
        events = []
        for _ in range(20):
            time.sleep(0.25)
            res = ctx.call("events_poll", {"subscription_id": sid, "max": 50})
            batch = res.get("events") if isinstance(res, dict) else None
            if batch:
                events = batch
                break
        ctx.expect(events, "no fluid.flow events from a water source inside the region")
        payload = events[0].get("payload") if isinstance(events[0], dict) else None
        ctx.expect(isinstance(payload, dict) and payload.get("fluid", "").endswith("water"),
                   f"fluid.flow payload should name the water, got {events[0]!r}")
        listing = ctx.call("events_list_subscriptions", {})
        rows = listing if isinstance(listing, list) else []
        mine = [r for r in rows if isinstance(r, dict) and r.get("subscription_id") == sid]
        ctx.expect(mine and "region" in mine[0] and "rate_limited_count" in mine[0],
                   f"listing should show the region gate and rate_limited_count: {mine!r}")
    finally:
        ctx.call_text("block_set_state", dict(water, block={"id": "minecraft:air"}))
        ctx.call_text("block_fill_region", {"dimension": ctx.dim, "box": ctx.box_obj(
            (x - 8, y, z - 8), (x + 8, y, z + 8)), "block": {"id": "minecraft:air"}})
        ctx.call_text("events_unsubscribe", {"subscription_id": sid})
