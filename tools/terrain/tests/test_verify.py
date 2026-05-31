"""verify.py: the extended offline gate.

Covers the contract additions on top of the original five structural checks:
  - edge_irregularity (the field-level 7-block rule on the coastline),
  - palette_monoculture (needs a MaterialSpec) — a single-block surface FAILs,
  - underwater_face (needs a spec) — a single-block submerged wall FAILs,
  - the seam check folded in when a recipe marks the field blended,
  - offline_token: deterministic, well-formed, and flips when a check flips.

Backward compatibility (``verify(hf)`` with no spec/recipe) is exercised by the
existing test_materialize_columns.py suite.
"""
import re

import numpy as np

from terrain import HeightField
from terrain.materialize import MaterialSpec
from terrain import verify


# ---------------------------------------------------------------------------
# fields
# ---------------------------------------------------------------------------
def _good_coast(seed=3):
    """An organic island whose coast is shaped by noise that straddles sea level
    — it wiggles within the 7-block rule, so edge_irregularity passes."""
    hf = HeightField(70, 70, sea_level=62)
    hf.h[:] = 56.0                       # base below sea level
    hf.add_fbm(14, octaves=4, base_freq=0.18, warp=6, seed=seed)
    return hf


def _good_hill():
    hf = HeightField(40, 40, sea_level=62)
    hf.add_fbm(30, octaves=4, base_freq=0.04, seed=3)
    hf.add_fbm(8, octaves=3, base_freq=0.09, ridge=True, seed=5)
    return hf


def _ruler_coast():
    """A manufactured ruler-straight N-S coastline (a wall, not a coast)."""
    hf = HeightField(40, 40, sea_level=62)
    hf.h[:] = 70.0
    hf.h[:20, :] = 55.0                  # land on x>=20, water on x<20, dead straight
    return hf


def _submerged_ramp():
    """Gentle high land that dives into a steep submerged face on the right —
    the geometry for the bathtub-foundation-wall test. Surface stays gentle so
    the *above*-water mix is healthy; only the submerged part is a steep face."""
    hf = HeightField(50, 50, sea_level=62)
    h = np.full((50, 50), 72.0)
    for x in range(30, 50):
        h[x, :] = 72 - (x - 29) * 5.0     # steep dive well below sea level
    hf.h = h
    return hf


# ---------------------------------------------------------------------------
# edge_irregularity (the 7-block rule on the field)
# ---------------------------------------------------------------------------
def test_edge_irregularity_passes_organic_coast():
    rep = verify.verify(_good_coast())
    edge = [c for c in rep.checks if c[0] == "edge_irregularity"][0]
    assert edge[1], f"organic coast wrongly flagged: {edge}"


def test_edge_irregularity_fails_ruler_straight_coast():
    rep = verify.verify(_ruler_coast())
    edge = [c for c in rep.checks if c[0] == "edge_irregularity"][0]
    assert not edge[1], f"ruler-straight coast not flagged: {edge}"
    assert not rep.ok


def test_edge_irregularity_vacuous_without_coastline():
    # an all-land hill has no land/water edge; the rule passes vacuously
    rep = verify.verify(_good_hill())
    edge = [c for c in rep.checks if c[0] == "edge_irregularity"][0]
    assert edge[1]
    assert "no-coastline" in edge[2]


# ---------------------------------------------------------------------------
# palette monoculture (needs a spec)
# ---------------------------------------------------------------------------
def test_monoculture_spec_fails():
    hf = _good_coast()
    # a spec that paints exactly one block everywhere — the literal monoculture
    mono = MaterialSpec(layers=[], base={"minecraft:grass_block": 1.0},
                        subsurface="minecraft:dirt")
    mono.strata = None
    rep = verify.verify(hf, spec=mono)
    assert not rep.ok
    mc = [c for c in rep.checks if c[0] == "palette_monoculture"][0]
    assert not mc[1], mc
    assert "grass_block" in mc[2]


def test_natural_mixed_spec_passes_monoculture():
    # the default natural spec is a real dither (grass-dominant base, sand beach,
    # rock slant) — a legitimate ratio band, not a monoculture
    hf = _good_coast()
    spec = MaterialSpec.natural(hf)
    rep = verify.verify(hf, spec=spec)
    mc = [c for c in rep.checks if c[0] == "palette_monoculture"][0]
    assert mc[1], f"natural dither wrongly flagged as monoculture: {mc}"


def test_monoculture_check_absent_without_spec():
    rep = verify.verify(_good_coast())          # no spec
    names = {c[0] for c in rep.checks}
    assert "palette_monoculture" not in names
    assert "underwater_face" not in names


# ---------------------------------------------------------------------------
# underwater / foundation face (needs a spec)
# ---------------------------------------------------------------------------
def test_underwater_wall_single_block_fails():
    hf = _submerged_ramp()
    # the submerged steep face resolves to a single block (a bathtub wall)
    wall = MaterialSpec(layers=[],
                        base={"minecraft:grass_block": 0.6,
                              "minecraft:coarse_dirt": 0.25,
                              "minecraft:moss_block": 0.15},
                        subsurface="minecraft:dirt")
    wall.slant = [(50.0, {"minecraft:stone": 1.0})]
    wall.strata = None
    rep = verify.verify(hf, spec=wall)
    face = [c for c in rep.checks if c[0] == "underwater_face"][0]
    assert not face[1], f"single-block submerged wall not flagged: {face}"
    assert not rep.ok


def test_underwater_face_mixed_rock_passes():
    hf = _submerged_ramp()
    good = MaterialSpec(layers=[],
                        base={"minecraft:grass_block": 0.6,
                              "minecraft:coarse_dirt": 0.4},
                        subsurface="minecraft:dirt")
    good.slant = [(50.0, {"minecraft:stone": 0.5, "minecraft:gravel": 0.3,
                          "minecraft:andesite": 0.2})]
    good.strata = None
    rep = verify.verify(hf, spec=good)
    face = [c for c in rep.checks if c[0] == "underwater_face"][0]
    assert face[1], f"mixed-rock submerged face wrongly flagged: {face}"


# ---------------------------------------------------------------------------
# seam folded in when the recipe marks the field blended
# ---------------------------------------------------------------------------
def test_seam_check_folded_when_recipe_blended():
    hf = _good_hill()
    base = verify.verify(hf)
    assert not any(c[0] == "seam_max_step" for c in base.checks)
    for marker in ({"blended": True}, {"multi_region": True},
                   {"regions": ["a", "b"]}, {"blend": {"radius": 8}},
                   {"seam": True}):
        rep = verify.verify(hf, recipe=marker)
        assert any(c[0] == "seam_max_step" for c in rep.checks), marker


def test_seam_fold_fails_on_a_wall():
    # a blended recipe over a field with a 46-block single-cell wall must FAIL
    hf = HeightField(40, 40, sea_level=62)
    h = np.full((40, 40), 64.0)
    h[20:, :] = 110.0
    hf.h = h
    rep = verify.verify(hf, recipe={"blended": True}, seam_max_step=12)
    seam = [c for c in rep.checks if c[0] == "seam_max_step"][0]
    assert not seam[1]
    assert not rep.ok


# ---------------------------------------------------------------------------
# the good field passes the whole gate
# ---------------------------------------------------------------------------
def test_good_field_with_spec_passes_everything():
    hf = _good_coast()
    spec = MaterialSpec.natural(hf)
    rep = verify.verify(hf, spec=spec, recipe={"blended": True})
    assert rep.ok, str(rep)
    # every contract check is present in the report
    names = {c[0] for c in rep.checks}
    for expected in ("bounds", "not_degenerate", "relief", "land_present",
                     "no_ziggurat", "edge_irregularity", "palette_monoculture",
                     "underwater_face", "seam_max_step"):
        assert expected in names, f"missing check {expected}"


# ---------------------------------------------------------------------------
# offline_token: deterministic, well-formed, flips on a changed check
# ---------------------------------------------------------------------------
def test_offline_token_format_and_determinism():
    hf = _good_hill()
    r1 = verify.verify(hf)
    r2 = verify.verify(hf)
    t1 = verify.offline_token(r1)
    t2 = verify.offline_token(r2)
    assert re.fullmatch(r"ovt_[0-9a-f]{12}", t1), t1
    assert t1 == t2                       # same outcomes → same token


def test_offline_token_ignores_detail_strings():
    # token is over (name, passed) only; a different detail string for the same
    # outcomes must not change the token (no float-formatting churn)
    a = verify.Report(ok=True, checks=[("relief", True, "variance 46.22")])
    b = verify.Report(ok=True, checks=[("relief", True, "variance 99.99")])
    assert verify.offline_token(a) == verify.offline_token(b)


def test_offline_token_flips_when_a_check_flips():
    hf = _good_hill()
    base = verify.verify(hf)
    t_base = verify.offline_token(base)
    flipped = verify.Report(
        ok=False,
        checks=[(n, (not p if n == "relief" else p), d) for n, p, d in base.checks],
    )
    assert verify.offline_token(flipped) != t_base


def test_offline_token_changes_when_seam_added():
    # adding the seam check (blended recipe) changes the check set → token shifts
    hf = _good_hill()
    t_base = verify.offline_token(verify.verify(hf))
    t_blended = verify.offline_token(verify.verify(hf, recipe={"blended": True}))
    assert t_base != t_blended


# ---------------------------------------------------------------------------
# backward compatibility
# ---------------------------------------------------------------------------
def test_verify_no_args_backward_compatible():
    # the original call form still works and still runs the five core checks
    rep = verify.verify(_good_hill())
    names = {c[0] for c in rep.checks}
    assert {"bounds", "not_degenerate", "relief", "land_present",
            "no_ziggurat"} <= names


def test_verify_accepts_legacy_thresholds_as_kwargs():
    hf = _good_hill()
    # legacy keyword thresholds must still be accepted
    rep = verify.verify(hf, min_land_fraction=0.0, silhouette_var_min=1.0,
                        require_relief=False)
    assert rep.ok, str(rep)


def test_verify_seam_helper_still_works():
    flat = np.full((10, 10), 64.0)
    assert verify.verify_seam(flat).ok
    wall = np.full((20, 20), 64.0)
    wall[10:, :] = 100.0
    assert not verify.verify_seam(wall, max_step=12).ok
