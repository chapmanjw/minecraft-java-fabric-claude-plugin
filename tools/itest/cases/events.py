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
