"""Offline tests for the harness terrain gate (lint_phase) and the seam check.

No live server: every Plan is constructed from an in-memory dict, and the lint
is pure (it only touches the plan + the recipe.json on disk). These prove the
harness is the single gated terrain path — ungated terrain is refused.
"""
import json
import os

from builder import toon
from builder.harness import (
    Plan, lint_phase, classify_terrain, classify_footprint, phase_has_terrain_op,
    recipe_on_disk, phase_verify_token, execute_step, check_seam, CHECK_FUNCS,
    FUNDAMENTAL_CHECKS, load_plan,
)


# --------------------------------------------------------------------------- helpers

def _write_recipe(tmp_path, name="canyon.recipe.json"):
    """Drop a minimal recipe.json next to where the plan will live."""
    p = tmp_path / name
    p.write_text(json.dumps({"version": 1, "nx": 8, "nz": 8, "graph": {"type": "FBM"}}),
                 encoding="utf-8")
    return p


def _plan(tmp_path, data, recipe="canyon.recipe.json"):
    """Build a Plan whose .path is inside tmp_path so recipe_on_disk resolves."""
    plan_path = os.path.join(str(tmp_path), "plan.toon")
    if recipe is not None and "recipe" not in data:
        data = {**data, "recipe": recipe}
    return Plan(data, plan_path)


# A terrain qc block with the rows a well-formed terrain + footprint phase needs.
_GOOD_QC = {
    "silhouette": [{"region_a": "0 60 0", "region_b": "32 90 32",
                    "sample_count": 8, "min_y_variance": 3}],
    "edge_irregularity": [{"edge_name": "coast", "from": "0 64 0",
                           "to": "0 64 32", "max_collinear_run": 7}],
    "seam": [{"a": "0 0", "b": "32 0", "max_step": 12}],
}

# One columns step => the phase carries a terrain op (classify_terrain True).
_COLUMNS_STEP = {"op": "columns", "phase": 1, "seq": 1,
                 "payload": "p1_columns.json", "note": "canyon mass"}


def _terrain_plan(tmp_path, *, recipe=True, token=True, qc=True, footprint=False):
    """Assemble a terrain plan with each gate ingredient toggled on/off."""
    if recipe:
        _write_recipe(tmp_path)
    steps = [dict(_COLUMNS_STEP)]
    qc_block = {}
    if qc:
        qc_block = {"silhouette": _GOOD_QC["silhouette"],
                    "edge_irregularity": _GOOD_QC["edge_irregularity"]}
    if footprint:
        steps.append({"op": "place-structure", "phase": 1, "seq": 2,
                      "block": "keep", "a": "0 64 0", "note": "drop the keep"})
        if qc:
            qc_block["seam"] = _GOOD_QC["seam"]
    data = {"plan": {"project": "isle", "element": "headland"},
            "steps": steps, "quality_contract": qc_block}
    if token:
        data["verify_token"] = "ovt_0123456789ab"
    return _plan(tmp_path, data, recipe="canyon.recipe.json" if recipe else "missing.recipe.json")


# --------------------------------------------------------------------------- classification

def test_terrain_op_classifies_phase_as_terrain(tmp_path):
    plan = _terrain_plan(tmp_path)
    assert phase_has_terrain_op(plan, 1)
    assert classify_terrain(plan, 1)


def test_non_terrain_phase_is_not_classified(tmp_path):
    data = {"plan": {"project": "house", "element": "wall"},
            "steps": [{"op": "fill", "phase": 1, "seq": 1, "a": "0 64 0",
                       "b": "4 68 4", "block": "stone", "note": "a plain wall"}]}
    plan = _plan(tmp_path, data, recipe=None)
    assert not classify_terrain(plan, 1)
    is_terrain, issues = lint_phase(plan, 1)
    assert not is_terrain
    assert issues == []           # non-terrain phases pass the lint untouched


# --------------------------------------------------------------------------- the gate

def test_well_formed_terrain_phase_passes(tmp_path):
    plan = _terrain_plan(tmp_path)
    assert recipe_on_disk(plan)
    assert phase_verify_token(plan, 1) == "ovt_0123456789ab"
    is_terrain, issues = lint_phase(plan, 1)
    assert is_terrain
    assert issues == [], issues


def test_refuses_terrain_phase_missing_recipe(tmp_path):
    # recipe field names a file that does not exist on disk.
    plan = _terrain_plan(tmp_path, recipe=False)
    assert recipe_on_disk(plan) is None
    is_terrain, issues = lint_phase(plan, 1)
    assert is_terrain
    assert any("recipe.json" in i for i in issues), issues


def test_refuses_terrain_phase_missing_verify_token(tmp_path):
    plan = _terrain_plan(tmp_path, token=False)
    assert phase_verify_token(plan, 1) is None
    is_terrain, issues = lint_phase(plan, 1)
    assert any("verify_token" in i for i in issues), issues


def test_refuses_terrain_phase_missing_qc_row(tmp_path):
    plan = _terrain_plan(tmp_path, qc=False)
    is_terrain, issues = lint_phase(plan, 1)
    assert any("quality_contract terrain rows" in i for i in issues), issues


def test_step_level_verify_token_satisfies_gate(tmp_path):
    """A token stamped on a step (not just plan-level) clears the token gate."""
    _write_recipe(tmp_path)
    step = dict(_COLUMNS_STEP, verify_token="ovt_feedfacecafe")
    data = {"plan": {"project": "isle", "element": "headland"},
            "steps": [step],
            "quality_contract": {"silhouette": _GOOD_QC["silhouette"]},
            "recipe": "canyon.recipe.json"}
    plan = _plan(tmp_path, data, recipe="canyon.recipe.json")
    assert phase_verify_token(plan, 1) == "ovt_feedfacecafe"
    _, issues = lint_phase(plan, 1)
    assert not any("verify_token" in i for i in issues), issues


# --------------------------------------------------------------------------- footprint / seam

def test_footprint_phase_requires_seam_row(tmp_path):
    # A footprint phase (place-structure step) WITHOUT a seam row is refused.
    plan = _terrain_plan(tmp_path, footprint=True, qc=True)
    # remove the seam row the helper added so only the seam issue remains
    plan.quality_contract.pop("seam", None)
    assert classify_footprint(plan, 1)
    _, issues = lint_phase(plan, 1)
    assert any("seam" in i for i in issues), issues


def test_footprint_phase_with_seam_row_passes(tmp_path):
    plan = _terrain_plan(tmp_path, footprint=True, qc=True)
    assert classify_footprint(plan, 1)
    _, issues = lint_phase(plan, 1)
    assert issues == [], issues


def test_erode_protect_box_marks_footprint(tmp_path, monkeypatch):
    """An erode op with a protect_box naturalises into a built mass => footprint."""
    _write_recipe(tmp_path)
    # write the erode payload sidecar so classify_footprint can read it
    erode_payload = {"tool": "block_erode_region",
                     "args": {"origin": {"x": 0, "z": 0}, "width": 32, "length": 32,
                              "floor_y": 40, "protect_box": {"x0": 4, "z0": 4,
                                                             "x1": 12, "z1": 12}}}
    (tmp_path / "erode.json").write_text(json.dumps(erode_payload), encoding="utf-8")
    data = {"plan": {"project": "isle", "element": "headland"},
            "steps": [dict(_COLUMNS_STEP),
                      {"op": "erode", "phase": 1, "seq": 2, "payload": "erode.json",
                       "note": "naturalise into the keep"}],
            "quality_contract": {"silhouette": _GOOD_QC["silhouette"]},
            "verify_token": "ovt_0123456789ab",
            "recipe": "canyon.recipe.json"}
    plan = _plan(tmp_path, data, recipe="canyon.recipe.json")
    assert classify_footprint(plan, 1)
    _, issues = lint_phase(plan, 1)
    assert any("seam" in i for i in issues), issues


# --------------------------------------------------------------------------- ziggurat

def test_refuses_ziggurat(tmp_path):
    """Stacked Y-banded rectangular slab-fills across >=3 elevations are refused
    even when every other gate (recipe/token/qc) is satisfied."""
    _write_recipe(tmp_path)
    slabs = []
    for i, y in enumerate((64, 68, 72)):
        # nested rectangles, thin in Y, wide in X/Z — the ziggurat signature
        lo, hi = i * 2, 30 - i * 2
        slabs.append({"op": "fill", "phase": 1, "seq": 10 + i,
                      "a": f"{lo} {y} {lo}", "b": f"{hi} {y} {hi}",
                      "block": "stone", "note": "mountain terrace"})
    data = {"plan": {"project": "alps", "element": "peak"},
            "steps": slabs,
            "quality_contract": {"silhouette": _GOOD_QC["silhouette"]},
            "verify_token": "ovt_0123456789ab",
            "recipe": "canyon.recipe.json"}
    plan = _plan(tmp_path, data, recipe="canyon.recipe.json")
    assert classify_terrain(plan, 1)        # "mountain"/"terrace" keywords
    _, issues = lint_phase(plan, 1)
    assert any("ziggurat" in i for i in issues), issues


# --------------------------------------------------------------------------- seam check (offline, stub client)

class _StubClient:
    """Returns scripted block_get_top_y values along a seam line."""
    def __init__(self, tops):
        self._tops = tops          # dict (x, z) -> top_y (the value /place returns)

    def call_toon(self, name, args):
        if name == "block_get_top_y":
            return self._tops.get((args["x"], args["z"]), 64)
        raise AssertionError(f"unexpected call {name}")


def test_seam_registered_and_fundamental():
    assert CHECK_FUNCS.get("seam") is check_seam
    assert "seam" in FUNDAMENTAL_CHECKS


def test_check_seam_flags_hard_wall():
    # a 30-block jump partway along the seam line is a wall -> FAIL
    tops = {(x, 0): 65 for x in range(0, 33)}
    tops[(16, 0)] = 95          # +30 step vs neighbours
    client = _StubClient(tops)
    rows = [{"a": "0 0", "b": "32 0", "max_step": 12, "name": "keep-seam"}]
    results = check_seam(client, "minecraft:overworld", rows)
    assert results and results[0][0] == "seam"
    assert results[0][1] == "FAIL", results


def test_check_seam_passes_graded_apron():
    # a gentle 1-block-per-step ramp is a graded apron -> PASS
    tops = {(x, 0): 65 + x // 8 for x in range(0, 33)}
    client = _StubClient(tops)
    rows = [{"a": "0 0", "b": "32 0", "max_step": 12}]
    results = check_seam(client, "minecraft:overworld", rows)
    assert results[0][1] == "PASS", results


# --------------------------------------------------------------------------- execute_step terrain ops (offline, stub client)

class _RecordingClient:
    """Records tool calls and returns scripted replies for the terrain ops."""
    def __init__(self, replies):
        self.replies = replies      # tool name -> reply (str or dict)
        self.calls = []

    def call_toon(self, name, args):
        self.calls.append((name, args))
        return self.replies.get(name, {})

    def call_text(self, name, args):
        self.calls.append((name, args))
        rep = self.replies.get(name, "")
        return (rep if isinstance(rep, str) else json.dumps(rep)), False


def test_execute_columns_op_count_assertion(tmp_path):
    payload = {"dimension": "minecraft:overworld", "origin": {"x": 0, "z": 0},
               "width": 4, "length": 4, "floor_y": 50, "palette": ["minecraft:stone"],
               "stone_index": 0, "height": [64] * 16, "surface": [0] * 16,
               "subsurface": [0] * 16}
    (tmp_path / "cols.json").write_text(json.dumps(payload), encoding="utf-8")
    step = {"op": "columns", "payload": "cols.json"}

    # blocks_set > 0 -> ok, no warn
    client = _RecordingClient({"block_fill_columns": "columns: 16\nblocks_set: 4096"})
    ok, detail, changed, warn = execute_step(client, "minecraft:overworld", step,
                                             base_dir=str(tmp_path))
    assert ok and changed == 4096 and not warn
    assert client.calls[0][0] == "block_fill_columns"

    # blocks_set == 0 -> warn (a force-load miss / empty tile)
    client0 = _RecordingClient({"block_fill_columns": "columns: 16\nblocks_set: 0"})
    ok, detail, changed, warn = execute_step(client0, "minecraft:overworld", step,
                                             base_dir=str(tmp_path))
    assert ok and changed == 0 and warn


def test_execute_scatter_batches_under_4096(tmp_path):
    placements = [{"feature": "minecraft:fancy_oak", "x": i, "y": 64, "z": 0}
                  for i in range(5000)]
    (tmp_path / "scatter.json").write_text(json.dumps(placements), encoding="utf-8")
    step = {"op": "scatter", "payload": "scatter.json"}
    client = _RecordingClient({"level_place_features_batch": {"placed": 4096}})
    ok, detail, changed, warn = execute_step(client, "minecraft:overworld", step,
                                             base_dir=str(tmp_path))
    assert ok
    batch_calls = [c for c in client.calls if c[0] == "level_place_features_batch"]
    assert len(batch_calls) == 2          # 5000 -> 4096 + 904
    for _, args in batch_calls:
        assert len(args["features"]) <= 4096


def test_execute_erode_hydraulic_polls(tmp_path, monkeypatch):
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda *_a, **_k: None)
    erode = {"tool": "block_erode_hydraulic",
             "args": {"origin": {"x": 0, "z": 0}, "width": 32, "length": 32, "floor_y": 40}}
    (tmp_path / "ero.json").write_text(json.dumps(erode), encoding="utf-8")
    step = {"op": "erode", "payload": "ero.json"}

    class _HydraulicClient:
        def __init__(self):
            self.poll = 0

        def call_toon(self, name, args):
            if name == "block_erode_hydraulic_start":
                return {"job_id": "job-7", "columns": 1024, "state": "ERODING"}
            if name == "block_erode_hydraulic_status":
                self.poll += 1
                return {"state": "DONE" if self.poll >= 2 else "ERODING", "progress": 1.0}
            if name == "block_erode_hydraulic_result":
                return {"state": "DONE", "blocks_changed": 8123, "max_delta": 9}
            raise AssertionError(name)

    ok, detail, changed, warn = execute_step(_HydraulicClient(), "minecraft:overworld",
                                             step, base_dir=str(tmp_path))
    assert ok and changed == 8123 and not warn


# --------------------------------------------------------------------------- contract seam: a real plan.toon on disk

def test_load_plan_toon_terrain_phase_passes_gate(tmp_path):
    """End-to-end: a plan.toon as emit would write it (recipe + verify_token +
    terrain step + qc), read back through toon.parse + load_plan, clears the
    lint. Locks the emit<->harness contract seam."""
    _write_recipe(tmp_path, "isle.recipe.json")
    (tmp_path / "p1_columns.json").write_text("{}", encoding="utf-8")
    doc = (
        "plan:\n"
        "  project: isle\n"
        "  element: headland\n"
        "  dimension: minecraft:overworld\n"
        "recipe: isle.recipe.json\n"
        "verify_token: ovt_abc123def456\n"
        "steps[1]{op,phase,seq,payload,note}:\n"
        "  columns,1,1,p1_columns.json,canyon mass\n"
        "quality_contract:\n"
        "  silhouette[1]{region_a,region_b,sample_count,min_y_variance}:\n"
        "    0 60 0,32 90 32,8,3\n"
    )
    plan_path = tmp_path / "plan.toon"
    plan_path.write_text(doc, encoding="utf-8")
    plan = load_plan(str(plan_path))
    assert plan.recipe == "isle.recipe.json"
    assert plan.verify_token == "ovt_abc123def456"
    assert recipe_on_disk(plan)
    assert phase_has_terrain_op(plan, 1)
    is_terrain, issues = lint_phase(plan, 1)
    assert is_terrain
    assert issues == [], issues


def test_load_plan_toon_terrain_phase_missing_token_refused(tmp_path):
    """Same plan.toon but with no verify_token -> the gate refuses it."""
    _write_recipe(tmp_path, "isle.recipe.json")
    (tmp_path / "p1_columns.json").write_text("{}", encoding="utf-8")
    doc = (
        "plan:\n"
        "  project: isle\n"
        "  element: headland\n"
        "recipe: isle.recipe.json\n"
        "steps[1]{op,phase,seq,payload,note}:\n"
        "  columns,1,1,p1_columns.json,canyon mass\n"
        "quality_contract:\n"
        "  silhouette[1]{region_a,region_b,sample_count,min_y_variance}:\n"
        "    0 60 0,32 90 32,8,3\n"
    )
    plan_path = tmp_path / "plan.toon"
    plan_path.write_text(doc, encoding="utf-8")
    plan = load_plan(str(plan_path))
    _, issues = lint_phase(plan, 1)
    assert any("verify_token" in i for i in issues), issues
