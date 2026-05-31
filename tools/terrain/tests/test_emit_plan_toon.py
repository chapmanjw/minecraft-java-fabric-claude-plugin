"""emit.emit_plan_toon — the single terrain path (contract 4).

A blended recipe must produce: tiled columns/strata steps (each <=65,536 cols),
a recipe.json on disk, a verify_token, terrain quality_contract rows, and a seam
row; the plan.toon must parse back through builder.toon.parse into the shape the
harness Plan/lint consumes; a degenerate (flat) field must raise VerifyError.
"""
import json
import os

import pytest

from terrain import emit
from terrain.emit import VerifyError


# --- recipes ---------------------------------------------------------------

def _blended_recipe(nx=64, nz=64, base=78, origin=(0, 0, 0)):
    """A blended/multi-region rolling-ridge recipe that passes the verify gate:
    high base (all land), domain-warped FBM (irregular edges), thermal erosion.
    Marked ``blended`` so emit stamps a seam row."""
    return {
        "version": 1, "nx": nx, "nz": nz, "sea_level": 62, "seed": 7,
        "origin": list(origin), "blended": True,
        "graph": {"type": "Add",
                  "a": {"type": "Constant", "value": base},
                  "b": {"type": "Scale",
                        "src": {"type": "DomainWarp", "amplitude": 20,
                                "frequency": 0.03,
                                "src": {"type": "FBM", "frequency": 0.04,
                                        "octaves": 5, "seed": 7}},
                        "factor": 26}},
        "erosion": {"thermal": {"iterations": 4, "talus": 2.0}},
    }


# --- tests -----------------------------------------------------------------

def test_emit_plan_toon_blended(tmp_path):
    prefix = str(tmp_path / "scratch")
    plan = emit.emit_plan_toon(_blended_recipe(), prefix)

    # terrain steps: columns/strata, then fillbiome, then scatter, sequential seq
    ops = [s["op"] for s in plan["steps"]]
    assert "columns" in ops or "strata" in ops
    seqs = [s["seq"] for s in plan["steps"]]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    # columns precede fillbiome precede scatter
    order = {op: i for i, op in enumerate(("columns", "strata", "fillbiome", "scatter"))}
    ranks = [order[op] for op in ops]
    assert ranks == sorted(ranks), ops

    # recipe.json written and referenced relative to the plan dir
    assert plan["recipe"] == "scratch.recipe.json"
    assert (tmp_path / "scratch.recipe.json").exists()

    # verify token stamped (ovt_ + 12 hex)
    tok = plan["verify_token"]
    assert tok.startswith("ovt_") and len(tok) == 16

    # quality_contract: terrain rows + a seam row (blended field)
    qc = plan["quality_contract"]
    assert "silhouette" in qc and "edge_irregularity" in qc
    assert "seam" in qc, "blended field must carry a seam quality_contract row"
    seam = qc["seam"][0]
    assert {"a", "b", "max_step"} <= set(seam.keys())

    # the plan.toon file exists; each step payload is on disk
    assert (tmp_path / "scratch.plan.toon").exists()
    for s in plan["steps"]:
        assert (tmp_path / s["payload"]).exists(), s["payload"]


def test_emit_plan_toon_parses_back_through_harness(tmp_path):
    """The written plan.toon must round-trip through builder.toon.parse into the
    exact shape the harness Plan/lint reads: top-level steps list + recipe field
    + verify_token + quality_contract dict."""
    from builder import toon
    from builder.harness import Plan, lint_phase

    prefix = str(tmp_path / "scratch")
    plan = emit.emit_plan_toon(_blended_recipe(), prefix)

    toon_path = prefix + ".plan.toon"
    with open(toon_path, encoding="utf-8") as fh:
        data = toon.parse(fh.read())

    assert isinstance(data.get("steps"), list) and data["steps"]
    assert data.get("recipe") == "scratch.recipe.json"
    assert str(data.get("verify_token", "")).startswith("ovt_")
    assert isinstance(data.get("quality_contract"), dict)
    assert "seam" in data["quality_contract"]

    p = Plan(data, toon_path)
    assert len(p.steps) == len(plan["steps"])
    assert "silhouette" in p.quality_contract
    # the referenced recipe exists relative to the plan dir
    assert os.path.exists(os.path.join(os.path.dirname(toon_path), data["recipe"]))
    # the current harness lint already classifies this as terrain (step notes)
    # and finds the terrain qc rows -> no ziggurat / no missing-qc issue
    is_terrain, issues = lint_phase(p, 1)
    assert is_terrain
    assert issues == [], issues


def test_emit_plan_toon_pretiles_columns(tmp_path):
    """A >65,536-column field is pre-tiled: multiple columns steps, each tile
    <= cap, and concatenated coverage equals the original (no lost columns)."""
    prefix = str(tmp_path / "big")
    nx = nz = 280  # 78,400 columns > 65,536
    # raise the base so there is no coastline (keeps the edge_irregularity gate happy)
    plan = emit.emit_plan_toon(_blended_recipe(nx=nx, nz=nz, base=95,
                                               origin=(1000, 0, -500)), prefix)
    col_steps = [s for s in plan["steps"] if s["op"] in ("columns", "strata")]
    assert len(col_steps) >= 2, "large field should split into >1 columns tile"

    total = 0
    for s in col_steps:
        with open(tmp_path / s["payload"], encoding="utf-8") as fh:
            sub = json.load(fh)
        cols = sub["width"] * sub["length"]
        assert cols <= 65536, f"tile exceeds cap: {cols}"
        # each tile is itself a valid block_fill_columns plan
        assert len(sub["height"]) == cols
        assert len(sub["surface"]) == cols
        assert len(sub["subsurface"]) == cols
        for k in ("dimension", "origin", "palette", "stone_index",
                  "water_index", "floor_y", "sea_level"):
            assert k in sub, f"tile missing {k}"
        total += cols
    assert total == nx * nz, f"coverage drift: {total} != {nx * nz}"


def test_emit_plan_toon_strata_op(tmp_path):
    """A recipe with strata bands emits 'strata' column steps (not 'columns')."""
    rec = _blended_recipe()
    rec["material"] = {"surface": {"minecraft:grass_block": 0.7,
                                   "minecraft:coarse_dirt": 0.3},
                       "strata": [{"block": "minecraft:red_sandstone", "thickness": 4},
                                  {"block": "minecraft:terracotta", "thickness": 6}]}
    plan = emit.emit_plan_toon(rec, str(tmp_path / "strata"))
    ops = {s["op"] for s in plan["steps"]}
    assert "strata" in ops and "columns" not in ops


def test_emit_plan_toon_raises_on_degenerate(tmp_path):
    """A dead-flat field fails the verify gate -> emit_plan_toon raises."""
    flat = {"version": 1, "nx": 16, "nz": 16, "sea_level": 62, "seed": 1,
            "origin": [0, 0, 0], "graph": {"type": "Constant", "value": 64}}
    with pytest.raises(VerifyError):
        emit.emit_plan_toon(flat, str(tmp_path / "flat"))


def test_emit_plan_toon_unblended_has_no_seam(tmp_path):
    """A non-blended single-region field carries terrain rows but no seam row."""
    rec = _blended_recipe()
    rec.pop("blended")  # single region, no blend markers
    plan = emit.emit_plan_toon(rec, str(tmp_path / "single"))
    qc = plan["quality_contract"]
    assert "silhouette" in qc and "edge_irregularity" in qc
    assert "seam" not in qc
    assert plan["blended"] is False
