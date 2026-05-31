"""Belt recipes — the continuous blended loop, recipe-expressible and gated.

``recipe.build_field`` must build a ``HeightField`` from a ``belt`` section
(with or without a graph base); ``emit._material_from_spec`` must turn a
``belt_regions`` material into a per-arc Layer stack; and the whole thing must
pass through ``emit.emit_plan_toon`` (the single gated terrain path) producing a
seam-rowed plan whose field clears the offline verify gate. This is the durable,
harness-runnable form of the fix for failure mode #2 (seams): one continuous
field whose cross-section and palette morph region→region, never butted walls.
"""
import numpy as np
import pytest

from terrain import recipe as R
from terrain import emit, verify
from terrain.emit import VerifyError


# A small closed belt loop that passes the gate: high base (all land → no
# coastline), four park-like keypoints morphing peak/rise/base around the ring,
# four colour regions, micro-relief + thermal erosion, marked blended.
def _loop_recipe(nx=80, nz=80, origin=(0, 0, 0)):
    cx, cz = nx / 2.0, nz / 2.0
    corners = [(cx - 26, cz - 26), (cx + 26, cz - 26),
               (cx + 26, cz + 26), (cx - 26, cz + 26)]
    return {
        "version": 1, "nx": nx, "nz": nz, "sea_level": 62, "seed": 5,
        "origin": list(origin), "blended": True,
        "belt": {
            "centerline": [list(p) for p in corners], "closed": True,
            "corridor_half": 4, "fall": 14, "interior_level": 70,
            "roughness": 2, "roughness_freq": 0.04, "smooth": 2,
            "keypoints": [
                {"s": 0.00, "peak": 16, "rise": 22, "base": 70},   # forest
                {"s": 0.25, "peak": 40, "rise": 12, "base": 68},   # red rock
                {"s": 0.50, "peak": 30, "rise": 20, "base": 71},   # hoodoo
                {"s": 0.75, "peak": 52, "rise": 22, "base": 72},   # alpine
            ],
        },
        "micro_relief": {"amplitude": 1.5, "octaves": 3, "base_freq": 0.05},
        "erosion": {"thermal": {"iterations": 4, "talus": 2.0}},
        "material": {
            "cliff_slope": 48,
            "belt_regions": [
                {"s": 0.00, "subsurface": "minecraft:dirt",
                 "surface": {"minecraft:grass_block": 0.7, "minecraft:podzol": 0.2,
                             "minecraft:coarse_dirt": 0.1},
                 "cliff": {"minecraft:stone": 0.6, "minecraft:andesite": 0.4}},
                {"s": 0.25, "subsurface": "minecraft:red_sandstone",
                 "surface": {"minecraft:red_sand": 0.6, "minecraft:orange_terracotta": 0.4},
                 "cliff": {"minecraft:red_sandstone": 0.6, "minecraft:terracotta": 0.4}},
                {"s": 0.50, "subsurface": "minecraft:red_sandstone",
                 "surface": {"minecraft:orange_terracotta": 0.5, "minecraft:white_terracotta": 0.5},
                 "cliff": {"minecraft:orange_terracotta": 0.5, "minecraft:white_terracotta": 0.5}},
                {"s": 0.75, "subsurface": "minecraft:stone",
                 "surface": {"minecraft:stone": 0.6, "minecraft:gravel": 0.4},
                 "cliff": {"minecraft:stone": 0.6, "minecraft:cobblestone": 0.4},
                 "snow_y": 96, "snow": {"minecraft:snow_block": 0.8,
                                        "minecraft:powder_snow": 0.2}},
            ],
        },
    }


def test_build_field_belt_only_no_graph():
    """A belt-only recipe (no graph) builds a sane field: flat corridor at base,
    crests above it, finite + in-bounds."""
    rec = _loop_recipe()
    hf = R.build_field(rec)
    assert hf.h.shape == (rec["nx"], rec["nz"])
    assert np.isfinite(hf.h).all()
    assert hf.h.min() >= -64 and hf.h.max() <= 320
    # the alpine keypoint (peak 52 over base 72) must lift the field well above
    # the corridor floor somewhere
    assert hf.h.max() > 100
    # corridor floor near base (≈70), not the crest
    assert hf.h.min() < 80


def test_build_field_belt_closed_loop_wraps():
    """A closed loop has no seam at s=0/1: the max single-cell step stays a ramp
    (the whole reason the belt exists)."""
    hf = R.build_field(_loop_recipe())
    step = verify._max_single_step(hf.h)
    assert step <= 12.0, f"belt produced a wall (max step {step:.1f})"


def test_belt_regions_material_resolves_mixed():
    """belt_regions resolves to a multi-block surface (no monoculture) and uses
    each region's palette — red rock appears, snow appears, grass appears."""
    rec = _loop_recipe()
    hf = R.build_field(rec)
    spec = emit._material_from_spec(rec["material"], hf, recipe=rec)
    from terrain.materialize import resolve_surface
    surf, _sub = resolve_surface(hf, spec)
    ids = set(np.unique(surf.astype(object)).tolist())
    assert "minecraft:red_sand" in ids or "minecraft:orange_terracotta" in ids
    assert "minecraft:grass_block" in ids
    # not a monoculture
    _, counts = np.unique(surf.astype(object), return_counts=True)
    assert counts.max() / surf.size <= 0.92


def test_emit_plan_toon_belt_loop_gated(tmp_path):
    """The belt loop runs through the single gated path: verify passes (incl. the
    seam check now active on the emit path), and the plan carries a seam row,
    columns steps, a recipe.json, and a verify token."""
    rec = _loop_recipe()
    plan = emit.emit_plan_toon(rec, str(tmp_path / "loop"))
    qc = plan["quality_contract"]
    assert "seam" in qc, "blended belt loop must carry a seam row"
    assert any(s["op"] in ("columns", "strata") for s in plan["steps"])
    assert plan["recipe"] == "loop.recipe.json"
    assert (tmp_path / "loop.recipe.json").exists()
    assert plan["verify_token"].startswith("ovt_")


def test_emit_world_gate_runs_seam_and_monoculture():
    """emit_world now feeds spec+recipe to verify, so the report includes the
    palette_monoculture, underwater_face, and seam_max_step checks (they were
    silently skipped before)."""
    rec = _loop_recipe()
    payloads = emit.emit_world(rec)
    names = {c[0] for c in payloads["verify"].checks}
    assert {"palette_monoculture", "underwater_face", "seam_max_step"} <= names
    assert payloads["verify"].ok
