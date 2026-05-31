"""Scoreboard tools — objectives, scores, display slots, teams, membership.

Scoreboard state is *world-global*, not sandbox-confined: an objective or team
created here persists until removed. So every test that creates state is marked
``global`` and removes what it created in a ``finally`` (the harness clears the
block sandbox between runs, but never touches the scoreboard). list/get tools
are read-only and ``safe``.

No player is online, so score/team participants use *fake-player* names
(arbitrary strings Minecraft accepts as scoreboard participants). All test
objectives/teams use an ``itest_`` prefix so a stray leftover is recognisable.

Response shapes (from ScoreboardTools.java):
  * list_objectives -> TOON array of {name, displayName, criterion, displaySlot}
  * get_objective   -> TOON object {name, displayName, criterion}; errors if unknown
  * get_score       -> bare int (String.valueOf(int)); 0 when unset
  * list_teams      -> TOON array of {name, displayName, color, friendlyFire,
                       seeInvisibles, members[]}
  * add/remove/set/reset/membership -> plain text verb ("added"/"removed"/...)
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

OBJ = "itest_obj"
OBJ2 = "itest_obj2"
TEAM = "itest_team"
PART = "itest_p"          # fake-player participant (no online player needed)


def _names(rows):
    """Pull the 'name' field out of a list-of-dicts TOON array, tolerantly."""
    out = []
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict) and "name" in r:
                out.append(r["name"])
            else:
                out.append(str(r))
    return out


def _remove_objective(ctx, name):
    try:
        ctx.call_text("scoreboard_remove_objective", {"name": name})
    except Exception:
        pass


def _remove_team(ctx, name):
    try:
        ctx.call_text("scoreboard_remove_team", {"name": name})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# objectives: add / get / list / remove
# ---------------------------------------------------------------------------

@case("scoreboard_add_objective", level="global")
@case("scoreboard_get_objective", level="global")
@case("scoreboard_remove_objective", level="global")
def test_objective_lifecycle(ctx: Ctx):
    _remove_objective(ctx, OBJ)  # ensure clean slate (idempotent)
    try:
        text, err = ctx.call_text("scoreboard_add_objective",
                                  {"name": OBJ, "criterion": "dummy",
                                   "display_name": "ITest Objective"})
        ctx.expect(not err, f"add_objective errored: {text}")
        ctx.expect("added" in text.lower(),
                   f"add_objective did not confirm 'added': {text!r}")

        got = ctx.call("scoreboard_get_objective", {"name": OBJ})
        name = ctx.expect_field(got, "name")
        ctx.expect(name == OBJ, f"get_objective wrong name: {got}")
        ctx.expect_field(got, "criterion")

        rtext, rerr = ctx.call_text("scoreboard_remove_objective", {"name": OBJ})
        ctx.expect(not rerr, f"remove_objective errored: {rtext}")
        ctx.expect("removed" in rtext.lower(),
                   f"remove_objective did not confirm 'removed': {rtext!r}")

        # confirm side effect: getting it now must error (mod throws JSON-RPC
        # error for unknown objective, so call_text raises McpError rather than
        # returning is_err=True — tolerate both forms of "errored").
        try:
            _, gerr = ctx.call_text("scoreboard_get_objective", {"name": OBJ})
            ctx.expect(gerr, "get_objective should error after removal but did not")
        except Exception:  # noqa: BLE001 — McpError raised = errored as expected
            pass
    finally:
        _remove_objective(ctx, OBJ)


@case("scoreboard_list_objectives", level="global")
def test_list_objectives(ctx: Ctx):
    # safe-ish: read once, create, read again to assert the new one appears,
    # then remove. Marked global because it briefly creates an objective.
    _remove_objective(ctx, OBJ)
    try:
        before = ctx.call("scoreboard_list_objectives")
        ctx.expect(isinstance(before, list),
                   f"list_objectives should be a list, got {type(before).__name__}: {before}")
        ctx.call_text("scoreboard_add_objective", {"name": OBJ, "criterion": "dummy"})
        after = ctx.call("scoreboard_list_objectives")
        ctx.expect(OBJ in _names(after),
                   f"new objective {OBJ!r} not listed: {after}")
    finally:
        _remove_objective(ctx, OBJ)


# ---------------------------------------------------------------------------
# scores: set / add / get / reset
# ---------------------------------------------------------------------------

def _score_int(val):
    """get_score returns a bare int via call_toon; tolerate dict/str too."""
    if isinstance(val, bool):
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, dict):
        for k in ("score", "value"):
            if k in val:
                return val[k]
        return None
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


@case("scoreboard_set_score", level="global")
@case("scoreboard_get_score", level="global")
@case("scoreboard_add_score", level="global")
@case("scoreboard_reset_participant", level="global")
def test_score_lifecycle(ctx: Ctx):
    _remove_objective(ctx, OBJ)
    try:
        ctx.call_text("scoreboard_add_objective", {"name": OBJ, "criterion": "dummy"})

        # set to 7
        stext, serr = ctx.call_text("scoreboard_set_score",
                                    {"participant": PART, "objective": OBJ, "score": 7})
        ctx.expect(not serr, f"set_score errored: {stext}")
        ctx.expect("set" in stext.lower(), f"set_score not confirmed: {stext!r}")
        got = _score_int(ctx.call("scoreboard_get_score",
                                  {"participant": PART, "objective": OBJ}))
        ctx.expect(got == 7, f"score should be 7 after set, got {got!r}")

        # add +5 -> 12
        atext, aerr = ctx.call_text("scoreboard_add_score",
                                    {"participant": PART, "objective": OBJ, "delta": 5})
        ctx.expect(not aerr, f"add_score errored: {atext}")
        got = _score_int(ctx.call("scoreboard_get_score",
                                  {"participant": PART, "objective": OBJ}))
        ctx.expect(got == 12, f"score should be 12 after +5, got {got!r}")

        # reset participant
        rtext, rerr = ctx.call_text("scoreboard_reset_participant",
                                    {"participant": PART, "objective": OBJ})
        ctx.expect(not rerr, f"reset_participant errored: {rtext}")
        ctx.expect("reset" in rtext.lower(),
                   f"reset_participant not confirmed: {rtext!r}")
        # after reset the score is unset; the read returns 0 (or errors -> tolerate)
        _, gerr = ctx.call_text("scoreboard_get_score",
                                {"participant": PART, "objective": OBJ})
        if not gerr:
            got = _score_int(ctx.call("scoreboard_get_score",
                                      {"participant": PART, "objective": OBJ}))
            ctx.expect(got in (0, None),
                       f"score should be 0/unset after reset, got {got!r}")
    finally:
        # removing the objective drops all its participant scores too
        _remove_objective(ctx, OBJ)


# ---------------------------------------------------------------------------
# display slot (global display state — set then clear)
# ---------------------------------------------------------------------------

@case("scoreboard_set_display_slot", level="global")
def test_set_display_slot(ctx: Ctx):
    _remove_objective(ctx, OBJ)
    try:
        ctx.call_text("scoreboard_add_objective", {"name": OBJ, "criterion": "dummy"})
        text, err = ctx.call_text("scoreboard_set_display_slot",
                                  {"slot": "sidebar", "objective": OBJ})
        ctx.expect(not err, f"set_display_slot errored: {text}")
        ctx.expect("set" in text.lower(),
                   f"set_display_slot not confirmed: {text!r}")
    finally:
        # clear the slot (empty objective clears) then drop the objective
        try:
            ctx.call_text("scoreboard_set_display_slot",
                          {"slot": "sidebar", "objective": ""})
        except Exception:
            pass
        _remove_objective(ctx, OBJ)


# ---------------------------------------------------------------------------
# teams: add / list / remove + membership
# ---------------------------------------------------------------------------

@case("scoreboard_add_team", level="global")
@case("scoreboard_list_teams", level="global")
@case("scoreboard_remove_team", level="global")
def test_team_lifecycle(ctx: Ctx):
    _remove_team(ctx, TEAM)
    try:
        text, err = ctx.call_text("scoreboard_add_team",
                                  {"name": TEAM, "display_name": "ITest Team"})
        ctx.expect(not err, f"add_team errored: {text}")
        ctx.expect("added" in text.lower(), f"add_team not confirmed: {text!r}")

        teams = ctx.call("scoreboard_list_teams")
        ctx.expect(isinstance(teams, list),
                   f"list_teams should be a list, got {type(teams).__name__}: {teams}")
        ctx.expect(TEAM in _names(teams), f"new team {TEAM!r} not listed: {teams}")

        rtext, rerr = ctx.call_text("scoreboard_remove_team", {"name": TEAM})
        ctx.expect(not rerr, f"remove_team errored: {rtext}")
        ctx.expect("removed" in rtext.lower(),
                   f"remove_team not confirmed: {rtext!r}")

        after = ctx.call("scoreboard_list_teams")
        ctx.expect(TEAM not in _names(after),
                   f"team {TEAM!r} still listed after removal: {after}")
    finally:
        _remove_team(ctx, TEAM)


@case("scoreboard_team_add_member", level="global")
@case("scoreboard_team_remove_member", level="global")
def test_team_membership(ctx: Ctx):
    _remove_team(ctx, TEAM)
    try:
        ctx.call_text("scoreboard_add_team", {"name": TEAM})

        atext, aerr = ctx.call_text("scoreboard_team_add_member",
                                    {"team": TEAM, "participant": PART})
        ctx.expect(not aerr, f"team_add_member errored: {atext}")
        ctx.expect("added" in atext.lower(),
                   f"team_add_member not confirmed: {atext!r}")

        # confirm side effect: PART now appears in the team's members
        teams = ctx.call("scoreboard_list_teams")
        members = []
        if isinstance(teams, list):
            for t in teams:
                if isinstance(t, dict) and t.get("name") == TEAM:
                    m = t.get("members")
                    members = m if isinstance(m, list) else ([m] if m else [])
        ctx.expect(PART in [str(x) for x in members],
                   f"{PART!r} not in team members after add: {teams}")

        rtext, rerr = ctx.call_text("scoreboard_team_remove_member",
                                    {"team": TEAM, "participant": PART})
        ctx.expect(not rerr, f"team_remove_member errored: {rtext}")
        ctx.expect("removed" in rtext.lower(),
                   f"team_remove_member not confirmed: {rtext!r}")
    finally:
        _remove_team(ctx, TEAM)
