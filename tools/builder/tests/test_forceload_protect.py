"""Offline tests for the P2 force-load re-assert (the permanent ``protect`` set).

A self-running mechanism (rail loop, farm) keeps ticking at 0 players only while
its chunks stay force-loaded. A per-phase ``forceload remove`` that brackets its
own range would unload those chunks too — entities freeze, redstone reverts. The
runner must re-assert the plan's ``protect`` bands with ``forceload add`` as the
LAST force-load op of any force-toggling phase. These tests drive ``run_phase``
with a fake client that records every command, asserting the order is
remove-then-readd and that the mechanism chunks are force-loaded at the end.
"""
import json

from builder.harness import Plan, run_phase, protected_bands, chunk_bands, CHUNK


class _FakeClient:
    """Records forceload commands and serves scripted tool replies (no server)."""

    def __init__(self, replies=None):
        self.replies = replies or {}
        self.commands = []
        self.calls = []

    def command(self, cmd):
        self.commands.append(cmd)

    def call_text(self, name, args):
        self.calls.append((name, args))
        rep = self.replies.get(name, "filled 1 block(s)")
        return (rep if isinstance(rep, str) else json.dumps(rep)), False

    def call_toon(self, name, args):
        self.calls.append((name, args))
        return self.replies.get(name, {})


def _forceloads(commands):
    """(action, x1, z1, x2, z2) tuples for every forceload command, in order."""
    out = []
    for c in commands:
        parts = c.split()
        if parts and parts[0] == "forceload":
            out.append((parts[1],) + tuple(int(p) for p in parts[2:6]))
    return out


# A plan with one trivial fill step in phase 1 and a protected mechanism band.
def _plan_with_protect(protect_rows, *, step_a="200 64 200", step_b="204 66 204"):
    data = {
        "plan": {"project": "rideway", "element": "loop", "dimension": "minecraft:overworld"},
        "steps": [{"op": "fill", "phase": 1, "seq": 1, "a": step_a, "b": step_b,
                   "block": "stone", "note": "a plain platform"}],
        "protect": protect_rows,
    }
    return Plan(data, "/tmp/plan.toon")


def test_plan_parses_protect_rows():
    plan = _plan_with_protect([{"corner_a": "0 0", "corner_b": "32 32"}])
    assert plan.protect == [((0, 0), (32, 32))]


def test_plan_ignores_malformed_protect_rows():
    plan = _plan_with_protect([{"corner_a": "0 0"},                 # missing corner_b
                               {"corner_a": "x y", "corner_b": "1 1"},  # unparseable
                               {"corner_a": "0 0", "corner_b": "16 16"}])
    assert plan.protect == [((0, 0), (16, 16))]


def test_protected_bands_are_chunk_aligned():
    plan = _plan_with_protect([{"corner_a": "-3 27", "corner_b": "-3 27"}])
    bands = protected_bands(plan)
    assert bands == chunk_bands((-3, 27), (-3, 27))
    # a single block resolves to its one containing 16x16 chunk
    assert len(bands) == 1
    x1, z1, x2, z2 = bands[0]
    assert (x2 - x1 + 1) == CHUNK and (z2 - z1 + 1) == CHUNK


def test_protected_bands_extra_pairs():
    plan = _plan_with_protect([])
    bands = protected_bands(plan, extra=[((0, 0), (0, 0))])
    assert bands == chunk_bands((0, 0), (0, 0))


def test_run_phase_reasserts_protect_after_remove():
    """The mechanism band is force-added at the end, AFTER the phase's own remove."""
    plan = _plan_with_protect([{"corner_a": "-3 27", "corner_b": "-3 27"}])
    client = _FakeClient()
    digest = run_phase(client, plan, 1, forceload=True)

    seq = _forceloads(client.commands)
    actions = [s[0] for s in seq]
    # phase bracket: add (work bands) ... remove (work bands) ... add (protect)
    assert actions[0] == "add"
    assert actions[-1] == "add", seq
    assert "remove" in actions
    # the LAST add must be the protected mechanism band, and it must come after
    # the phase's remove (so the remove can't strand the mechanism).
    last_remove = max(i for i, a in enumerate(actions) if a == "remove")
    last_add = len(actions) - 1
    assert last_add > last_remove, seq

    prot = protected_bands(plan)[0]
    assert seq[-1] == ("add",) + prot, seq
    assert digest["protected_bands"] == [prot]


def test_run_phase_without_protect_has_no_trailing_readd():
    """A plan with no protect set keeps the plain add/remove bracket (no regression)."""
    plan = _plan_with_protect([])
    client = _FakeClient()
    run_phase(client, plan, 1, forceload=True)
    actions = [s[0] for s in _forceloads(client.commands)]
    assert actions, "expected a force-load bracket"
    assert actions[0] == "add" and actions[-1] == "remove", actions
    assert "add" not in actions[1:][-1:] or actions[-1] == "remove"


def test_run_phase_forceload_off_does_not_toggle():
    """forceload=False (the build path drives its own bracket) => run_phase emits
    no forceload commands of its own, so it never strands a mechanism either."""
    plan = _plan_with_protect([{"corner_a": "0 0", "corner_b": "16 16"}])
    client = _FakeClient()
    run_phase(client, plan, 1, forceload=False)
    assert _forceloads(client.commands) == []
