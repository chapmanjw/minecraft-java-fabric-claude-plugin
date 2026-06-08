"""minecraft-builder build + verify harness.

Executes a plan.toon phase and mechanically verifies it against a live
minecraft-java MCP server — entirely outside the LLM context. The model hands
off a phase, this runs every block op and every quality_contract assertion by
POSTing directly to the server, and returns one compact digest.

Think of it as a test harness for builds:
  plan.toon  = source + assertions   (steps = code; acceptance + quality_contract = tests)
  run        = the build step
  verify     = the test runner
  digest     = the results

CLI:
  python -m builder.harness mode                         # detect dedicated vs single-player
  python -m builder.harness selftest [--dim D]           # write-readiness self-test (forceload→set→read→restore)
  python -m builder.harness run    <plan.toon> <phase>   # execute a phase (forceload-bracketed)
  python -m builder.harness verify <plan.toon> <phase>   # run that phase's checks
  python -m builder.harness build  <plan.toon> <phase>   # run, then verify  (the common case)
  python -m builder.harness freshness <plan.toon> <phase>  # stale-plan pre-check (terrain columns vs live top-Y)

Exit code: 0 if everything the command attempted passed; 1 on any failure
(execution error, force-load miss, or a failed check). Designed so the calling
skill can branch on the exit code and read the printed digest.

Force-loading (dedicated/unattended servers): every `run`/`build` brackets the
phase with `forceload add`/`remove`, banded to stay under the 256-chunk/dimension
cap. Writes silently no-op in unloaded chunks, so this is mandatory when no
player is online; harmless when one is. A plan may also declare a top-level
`protect` block (rows of `{corner_a, corner_b}` as "x z") naming the chunks of a
permanently force-loaded, self-running mechanism (a rail loop, a farm). Those
bands are re-asserted with `forceload add` as the LAST op of every force-toggling
phase (run/build/freshness), so a transient `forceload remove` never unloads the
mechanism (its entities would freeze and its redstone revert). See
docs: tools/README.md and reference/engine-limits.md.

Stdlib only. No dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from builder import toon
    from builder.mcpclient import McpClient, McpError
else:
    from . import toon
    from .mcpclient import McpClient, McpError

CHUNK = 16
FORCELOAD_CHUNK_CAP = 256          # vanilla per-dimension forceload cap
DEFAULT_DIM = "minecraft:overworld"
AIR_IDS = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
FLUID_IDS = {"minecraft:water", "minecraft:lava"}

# Fix 5: words that mark a phase as organic terrain (the ziggurat-risk class).
TERRAIN_KEYWORDS = (
    "terrain", "landform", "landscape", "mountain", "canyon", "hill", "mesa",
    "cliff", "ridge", "ridgeline", "coast", "coastline", "shore", "dune",
    "valley", "plateau", "butte", "slope", "cape", "headland", "ravine",
    "gorge", "escarpment", "massif", "bluff", "knoll", "scree", "talus",
    "island", "peninsula", "crater", "volcano", "glacier", "fjord", "reef",
)
# A terrain phase must carry at least one of these quality_contract rows.
TERRAIN_QC_ROWS = (
    "silhouette", "edge_irregularity", "block_mix_ratios", "asymmetry",
    "foundation_naturalised", "water_continuity",
)
RENDER_DISTANCE_BLOCKS = 200       # ~12 chunks; perceivability threshold from spawn
# Words that mark a build as connective transit (softens a far-from-spawn flag).
TRANSIT_KEYWORDS = ("rail", "road", "highway", "path", "bridge", "tunnel",
                    "station", "transit", "dock", "nether-hub", "elevator")


# ===========================================================================
# helpers: ids, coords, block specs
# ===========================================================================

def norm_id(s):
    """Normalise a block/item/entity id to include the minecraft: namespace."""
    s = (s or "").strip()
    if not s:
        return s
    return s if ":" in s else "minecraft:" + s


def parse_block_spec(s):
    """'minecraft:oak_log[axis=y]' or 'stone_bricks' -> {'id':..., 'properties':{...}}."""
    s = (s or "").strip()
    props = {}
    m = re.match(r"^([^\[]+)(?:\[(.*)\])?$", s)
    base = m.group(1).strip()
    if m.group(2):
        for pair in m.group(2).split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                props[k.strip()] = v.strip()
    spec = {"id": norm_id(base)}
    if props:
        spec["properties"] = props
    return spec


def parse_coord(s):
    """'120 63 -340' -> (120, 63, -340). Accepts commas too."""
    parts = re.split(r"[ ,]+", str(s).strip())
    nums = [int(round(float(p))) for p in parts if p != ""]
    if len(nums) != 3:
        raise ValueError(f"expected 'x y z', got {s!r}")
    return tuple(nums)


def parse_xz(s):
    """'118 -342' -> (118, -342)."""
    parts = re.split(r"[ ,]+", str(s).strip())
    nums = [int(round(float(p))) for p in parts if p != ""]
    if len(nums) != 2:
        raise ValueError(f"expected 'x z', got {s!r}")
    return tuple(nums)


def pos_obj(xyz):
    return {"x": xyz[0], "y": xyz[1], "z": xyz[2]}


def box_obj(a, b):
    return {"from": {"x": min(a[0], b[0]), "y": min(a[1], b[1]), "z": min(a[2], b[2])},
            "to": {"x": max(a[0], b[0]), "y": max(a[1], b[1]), "z": max(a[2], b[2])}}


def _tile_box(a, b, max_blocks=32000):
    """Yield ``(lo, hi)`` sub-boxes covering the box ``a``–``b``, each ≤
    ``max_blocks`` blocks. ``block_replace_in_region`` silently truncates at
    ~32,768 blocks per call (unlike ``block_fill_region``, which the mod now
    auto-tiles server-side) — it edits the first ~32k and reports success for
    the rest. Tile under that ceiling so a large replace fully lands. See
    reference/engine-limits.md § Block placement."""
    lo = [min(a[i], b[i]) for i in range(3)]
    hi = [max(a[i], b[i]) for i in range(3)]
    step = [hi[i] - lo[i] + 1 for i in range(3)]
    while step[0] * step[1] * step[2] > max_blocks:
        ax = step.index(max(step))
        step[ax] = max(1, step[ax] // 2)
    for x0 in range(lo[0], hi[0] + 1, step[0]):
        for y0 in range(lo[1], hi[1] + 1, step[1]):
            for z0 in range(lo[2], hi[2] + 1, step[2]):
                yield ((x0, y0, z0),
                       (min(x0 + step[0] - 1, hi[0]),
                        min(y0 + step[1] - 1, hi[1]),
                        min(z0 + step[2] - 1, hi[2])))


def is_air(bid):
    return bid in AIR_IDS or bid.endswith(":air") or bid.endswith("_air")


def is_floor_solid(bid):
    """Stand-on-able: not air, not fluid, not a fence/wall top (per contract-checks)."""
    if is_air(bid) or bid in FLUID_IDS:
        return False
    if bid.endswith("_fence") or bid.endswith("_wall") or bid.endswith("_fence_gate"):
        return False
    return True


def is_head_clear(bid):
    """Air, or a door/trapdoor (passable head space)."""
    return is_air(bid) or "door" in bid


# ===========================================================================
# plan model
# ===========================================================================

class Plan:
    def __init__(self, data, path):
        self.path = path
        self.raw = data
        meta = data.get("plan", data)
        self.project = meta.get("project") or os.path.basename(os.path.dirname(path))
        self.element = meta.get("element")
        self.dimension = norm_id(meta.get("dimension") or DEFAULT_DIM)
        self.steps = data.get("steps") or []
        self.acceptance = data.get("acceptance") or []
        self.quality_contract = data.get("quality_contract") or {}
        # Top-level recipe reference (emit writes "<prefix>.recipe.json" and names
        # it here) + a phase-level verify_token, both consumed by the terrain lint.
        self.recipe = meta.get("recipe") or data.get("recipe")
        self.verify_token = meta.get("verify_token") or data.get("verify_token")
        self.envelopes = {}
        for row in (data.get("envelopes") or []):
            try:
                self.envelopes[int(row["phase"])] = (parse_xz(row["corner_a"]), parse_xz(row["corner_b"]))
            except (KeyError, ValueError):
                continue
        # Permanently force-loaded mechanism chunks (a self-running rail loop, a
        # farm) that must keep ticking at 0 players. Any phase that force-toggles
        # re-asserts these as its last op, so a transient `forceload remove` never
        # unloads them. Rows are {corner_a, corner_b} as "x z" (Zion P2).
        self.protect = []
        for row in (data.get("protect") or []):
            try:
                self.protect.append((parse_xz(row["corner_a"]), parse_xz(row["corner_b"])))
            except (KeyError, ValueError):
                continue

    def phase_steps(self, phase):
        out = [s for s in self.steps if str(s.get("phase")) == str(phase)]
        out.sort(key=lambda s: int(s.get("seq", 0)))
        return out

    def phase_ids(self):
        seen = []
        for s in self.steps:
            p = s.get("phase")
            if p not in seen:
                seen.append(p)
        return seen


def load_plan(path):
    with open(path, encoding="utf-8") as fh:
        return Plan(toon.parse(fh.read()), path)


# ===========================================================================
# force-load envelope (with banding)
# ===========================================================================

def derive_envelope(plan, phase, margin=2):
    """Bounding (x,z) of a phase's step coordinates, expanded by `margin` blocks."""
    xs, zs = [], []
    for s in plan.phase_steps(phase):
        for key in ("a", "b"):
            v = s.get(key)
            if v in (None, "", "null"):
                continue
            try:
                x, _, z = parse_coord(v)
                xs.append(x)
                zs.append(z)
            except ValueError:
                continue
    if not xs:
        return None
    return ((min(xs) - margin, min(zs) - margin), (max(xs) + margin, max(zs) + margin))


def chunk_bands(corner_a, corner_b):
    """Split an (x,z) envelope into forceload bands under the 256-chunk/dim cap.

    Returns a list of (x1, z1, x2, z2) block-coord rectangles, each <=256 chunks.
    """
    x1, z1 = min(corner_a[0], corner_b[0]), min(corner_a[1], corner_b[1])
    x2, z2 = max(corner_a[0], corner_b[0]), max(corner_a[1], corner_b[1])
    cx1, cx2 = x1 // CHUNK, x2 // CHUNK
    cz1, cz2 = z1 // CHUNK, z2 // CHUNK
    x_chunks = cx2 - cx1 + 1
    # Max Z-chunks per band so x_chunks * z_band <= cap.
    z_band = max(1, FORCELOAD_CHUNK_CAP // max(1, x_chunks))
    bands = []
    cz = cz1
    while cz <= cz2:
        cz_end = min(cz2, cz + z_band - 1)
        bands.append((cx1 * CHUNK, cz * CHUNK, cx2 * CHUNK + (CHUNK - 1), cz_end * CHUNK + (CHUNK - 1)))
        cz = cz_end + 1
    return bands


# ===========================================================================
# runner — execute a phase's steps
# ===========================================================================

_INT_RE = re.compile(r"(-?\d+)")


def _changed_count(text):
    """Pull the integer out of 'filled 42 block(s)' / 'replaced 0 block(s)' etc."""
    m = _INT_RE.search(text or "")
    return int(m.group(1)) if m else None


# Terrain ops whose payload is a sidecar JSON file relative to the plan dir.
TERRAIN_OPS = ("columns", "strata", "fillbiome", "scatter", "erode")
SCATTER_BATCH = 4096       # level_place_features_batch per-call entry cap


def _load_payload(step, base_dir):
    """Load a terrain step's sidecar ``payload`` JSON, resolved against the plan dir."""
    payload = step.get("payload")
    if not payload:
        raise ValueError(f"{step.get('op')} step requires a 'payload' file")
    path = payload if os.path.isabs(payload) else os.path.join(base_dir or "", payload)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _coerce_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return int(round(float(v)))
        except (TypeError, ValueError):
            return None


_BLOCKS_SET_RE = re.compile(r"blocks?_set\s*[:=]\s*(-?\d+)", re.I)


def _columns_count(result):
    """blocks_set from a block_fill_columns(_strata) reply ('columns: N\\nblocks_set: M').

    ``call_toon`` normally TOON-parses the text into a dict; fall back to a
    targeted ``blocks_set`` regex on a raw text reply so we never mistake the
    leading ``columns:`` integer for the block count."""
    if isinstance(result, dict):
        for key in ("blocks_set", "blocksSet", "blocks_changed", "blocksChanged"):
            if key in result:
                return _coerce_int(result[key])
        return None
    m = _BLOCKS_SET_RE.search(result or "")
    return int(m.group(1)) if m else _changed_count(result)


def _exec_columns(client, dim, step, base_dir, tool):
    """columns -> block_fill_columns; strata -> block_fill_columns_strata.

    The payload is ONE plan dict (already <=65,536 columns; emit pre-tiles).
    Asserts blocks_set > 0 (0 is a force-load miss or an empty tile)."""
    plan = _load_payload(step, base_dir)
    args = dict(plan)
    args["dimension"] = args.get("dimension") or dim
    if tool == "block_fill_columns":
        args.pop("strata", None)              # single-stone tool ignores strata bands
        args.pop("base_stone", None)
        args.pop("jitter_amplitude", None)
        args.pop("jitter_freq", None)
    else:
        if not args.get("strata"):
            return False, "strata step payload carries no strata[] bands", None, True
        args.setdefault("base_stone", args.get("stone") or "minecraft:stone")
    result = client.call_toon(tool, args)
    n = _columns_count(result)
    detail = f"{tool}: {result if isinstance(result, str) else json.dumps(result)}"
    warn = (n == 0 or n is None)
    return True, detail, n, warn


def _exec_fillbiome(client, dim, step, base_dir):
    """fillbiome -> a JSON list of level_fill_biome arg dicts (climate.to_biome_fill_plan).

    Each rect may carry from/to as {x,y,z} dicts or as [x,y,z] lists. Asserts at
    least one rect was painted; a fillbiome that touches 0 rectangles is a miss."""
    rects = _load_payload(step, base_dir)
    if not isinstance(rects, list):
        return False, "fillbiome payload must be a JSON list of rectangles", None, True
    painted, last = 0, ""
    for rect in rects:
        frm, to = rect.get("from"), rect.get("to")
        args = {"dimension": rect.get("dimension") or dim,
                "from": _corner(frm), "to": _corner(to),
                "biome": rect.get("biome")}
        if rect.get("replace_filter"):
            args["replace_filter"] = rect["replace_filter"]
        text, is_err = client.call_text("level_fill_biome", args)
        last = text
        if not is_err:
            painted += 1
    warn = (painted == 0)
    return True, f"level_fill_biome x{painted}/{len(rects)} (last: {last})", painted, warn


def _corner(c):
    """Coerce a from/to corner ({x,y,z} or [x,y,z]) into the tool's {x,y,z} shape."""
    if isinstance(c, dict):
        return {"x": c.get("x"), "y": c.get("y"), "z": c.get("z")}
    if isinstance(c, (list, tuple)) and len(c) == 3:
        return {"x": c[0], "y": c[1], "z": c[2]}
    raise ValueError(f"bad biome corner {c!r}")


def _scatter_feature(p):
    """One placement -> {feature, x, y, z}. Accepts a dict or a (x,y,z,kind,id) tuple."""
    if isinstance(p, dict):
        return {"feature": p.get("feature") or p.get("id"),
                "x": _coerce_int(p.get("x")), "y": _coerce_int(p.get("y")),
                "z": _coerce_int(p.get("z"))}
    if isinstance(p, (list, tuple)) and len(p) >= 5:
        # scatter.py tuple order: (x, y, z, kind, id)
        return {"feature": p[4], "x": _coerce_int(p[0]),
                "y": _coerce_int(p[1]), "z": _coerce_int(p[2])}
    raise ValueError(f"bad scatter placement {p!r}")


def _exec_scatter(client, dim, step, base_dir):
    """scatter -> JSON list of placements; batched into level_place_features_batch
    calls of <=4096 entries. Asserts at least one feature placed."""
    placements = _load_payload(step, base_dir)
    if not isinstance(placements, list):
        return False, "scatter payload must be a JSON list of placements", None, True
    feats = [_scatter_feature(p) for p in placements]
    placed, batches, last = 0, 0, ""
    for i in range(0, len(feats), SCATTER_BATCH):
        chunk = feats[i:i + SCATTER_BATCH]
        result = client.call_toon("level_place_features_batch",
                                  {"dimension": dim, "features": chunk,
                                   "stop_on_error": False})
        batches += 1
        if isinstance(result, dict):
            n = None
            for key in ("placed", "features_placed", "featuresPlaced", "count", "succeeded"):
                if key in result:
                    n = _coerce_int(result[key])
                    break
            placed += (n if n is not None else len(chunk))
            last = json.dumps(result)
        else:
            placed += len(chunk)            # text reply: assume the batch landed
            last = result
    warn = (placed == 0 or not feats)
    return True, f"level_place_features_batch: {placed} feature(s) in {batches} batch(es) (last: {last})", placed, warn


def _exec_erode(client, dim, step, base_dir):
    """erode -> {tool: block_erode_region|block_erode_hydraulic, args:{...}}.

    block_erode_region is synchronous (read blocks_changed). block_erode_hydraulic
    is async: start, poll status until DONE/FAILED, then read the result. Asserts
    blocks_changed > 0 (unless the args request a dry_run)."""
    spec = _load_payload(step, base_dir)
    tool = (spec.get("tool") or "").strip()
    args = dict(spec.get("args") or {})
    args.setdefault("dimension", dim)
    dry = bool(args.get("dry_run"))

    if tool == "block_erode_region":
        result = client.call_toon("block_erode_region", args)
        n = _erode_changed(result)
        warn = (not dry) and (n == 0 or n is None)
        return True, f"block_erode_region: {_short(result)}", n, warn

    if tool in ("block_erode_hydraulic", "block_erode_hydraulic_start"):
        start = client.call_toon("block_erode_hydraulic_start", args)
        job_id = start.get("job_id") if isinstance(start, dict) else None
        if not job_id:
            return False, f"block_erode_hydraulic_start returned no job_id: {_short(start)}", None, True
        state = _poll_hydraulic(client, job_id)
        if state == "FAILED":
            return False, f"hydraulic erosion job {job_id} FAILED", None, True
        if state == "TIMEOUT":
            return False, (f"hydraulic erosion job {job_id} did not reach DONE within "
                           f"{_HYDRAULIC_POLL_MAX} polls — job still running or stalled; "
                           "re-poll block_erode_hydraulic_status before reading the result"), None, True
        result = client.call_toon("block_erode_hydraulic_result", {"job_id": job_id})
        n = _erode_changed(result)
        warn = (not dry) and (n == 0 or n is None)
        return True, f"block_erode_hydraulic[{job_id}] {state}: {_short(result)}", n, warn

    return False, f"erode step: unknown tool {tool!r}", None, True


_HYDRAULIC_TERMINAL = {"DONE", "FAILED", "COMPLETE"}
_HYDRAULIC_POLL_MAX = 600           # ~ up to 5 min at the 0.5s floor below


def _poll_hydraulic(client, job_id):
    """Poll block_erode_hydraulic_status until a terminal state. Returns the state."""
    import time
    for _ in range(_HYDRAULIC_POLL_MAX):
        status = client.call_toon("block_erode_hydraulic_status", {"job_id": job_id})
        state = str(status.get("state", "")).upper() if isinstance(status, dict) else ""
        if state in _HYDRAULIC_TERMINAL:
            return "DONE" if state == "COMPLETE" else state
        time.sleep(0.5)
    return "TIMEOUT"


def _erode_changed(result):
    if isinstance(result, dict):
        for key in ("blocks_changed", "blocksChanged", "moved"):
            if key in result:
                return _coerce_int(result[key])
        return None
    return _changed_count(result)


def _short(v):
    s = v if isinstance(v, str) else json.dumps(v)
    return s if len(s) <= 240 else s[:237] + "..."


def execute_step(client, dim, step, base_dir=None):
    """Map one plan step to its MCP tool call. Returns (ok, detail, changed, warn).

    ``base_dir`` resolves a terrain op's ``payload`` sidecar JSON (the plan dir)."""
    op = (step.get("op") or "").strip()
    a = step.get("a")
    b = step.get("b")
    block = step.get("block")
    note = step.get("note")

    # --- terrain ops: bulk landform placement via the column/biome/scatter tools.
    if op == "columns":
        return _exec_columns(client, dim, step, base_dir, "block_fill_columns")
    if op == "strata":
        return _exec_columns(client, dim, step, base_dir, "block_fill_columns_strata")
    if op == "fillbiome":
        return _exec_fillbiome(client, dim, step, base_dir)
    if op == "scatter":
        return _exec_scatter(client, dim, step, base_dir)
    if op == "erode":
        return _exec_erode(client, dim, step, base_dir)

    if op == "fill":
        text, _ = client.call_text("block_fill_region",
                                   {"dimension": dim, "box": box_obj(parse_coord(a), parse_coord(b)),
                                    "block": parse_block_spec(block)})
        n = _changed_count(text)
        return True, text, n, (n == 0)
    if op == "set":
        text, _ = client.call_text("block_set_state",
                                   {"dimension": dim, "position": pos_obj(parse_coord(a)),
                                    "block": parse_block_spec(block)})
        warn = "no change" in (text or "").lower()
        return True, text, (0 if warn else 1), warn
    if op == "replace":
        # `block` is the replacement; `note` carries the target block id to replace.
        if not note:
            return False, "replace op requires the target block id in 'note'", None, True
        target = norm_id(str(note).split()[0])
        repl = parse_block_spec(block)
        # block_replace_in_region truncates at ~32,768 blocks/call (it does NOT
        # auto-tile like block_fill_region) — tile so a large replace fully lands.
        total, last, tiles = 0, "", 0
        for lo, hi in _tile_box(parse_coord(a), parse_coord(b)):
            text, _ = client.call_text("block_replace_in_region",
                                       {"dimension": dim, "box": box_obj(lo, hi),
                                        "target": target, "replacement": repl})
            n = _changed_count(text)
            total += (n or 0)
            last, tiles = text, tiles + 1
        detail = last if tiles == 1 else (
            f"{last} (replace tiled into {tiles} sub-boxes ≤32k; {total} replaced total)")
        return True, detail, total, (total == 0)
    if op == "clone":
        ca, cb = parse_coord(a), parse_coord(b)
        dest = parse_coord(note)
        text, _ = client.call_text("block_clone_region",
                                   {"source_dimension": dim,
                                    "source_box": {"from": pos_obj(ca), "to": pos_obj(cb)},
                                    "dest_dimension": dim, "destination": pos_obj(dest)})
        n = _changed_count(text)
        return True, text, n, (n == 0)
    if op == "place-structure":
        text, _ = client.call_text("structure_load_to_world",
                                   {"name": block, "dimension": dim, "origin": pos_obj(parse_coord(a))})
        return True, text, None, ("error" in (text or "").lower())
    if op == "spawn":
        args = {"dimension": dim, "entity_type": norm_id(block), "position": pos_obj(parse_coord(a))}
        if note:
            args["nbt"] = note
        text, _ = client.call_text("entity_summon", args)
        return True, text, None, False
    if op == "block-nbt":
        text, _ = client.call_text("block_entity_set_nbt",
                                   {"dimension": dim, "position": pos_obj(parse_coord(a)), "nbt": note or ""})
        return True, text, None, False
    if op == "set-slot":
        text, _ = client.call_text("inventory_set_slot",
                                   {"target": a, "slot": int(b),
                                    "item": ({"id": norm_id(block), "components": note} if note
                                             else {"id": norm_id(block)})})
        return True, text, None, False
    if op == "run":
        text, _ = client.call_text("command_execute", {"command": note or block or ""})
        warn = "should not run" in (text or "").lower() or "successcount: 0" in (text or "").lower()
        return True, text, None, warn
    return False, f"unknown op {op!r}", None, True


def phase_envelope_bands(plan, phase):
    env = plan.envelopes.get(_as_int(phase)) or derive_envelope(plan, phase)
    return env, (chunk_bands(*env) if env else [])


def _forceload(client, bands, action):
    for (x1, z1, x2, z2) in bands:
        client.command(f"forceload {action} {x1} {z1} {x2} {z2}")


def protected_bands(plan, extra=None):
    """Chunk-aligned force-load bands for the plan's PERMANENT mechanism set (its
    top-level ``protect`` rows) plus any ``extra`` ``(corner_a, corner_b)`` pairs.

    A self-running mechanism (rail loop, farm) must keep its chunks force-loaded
    to tick at 0 players. A per-phase ``forceload remove`` that brackets its own
    range will unload the mechanism's chunks too — entities freeze, redstone
    reverts (Zion P2). The runner re-asserts these bands with ``forceload add`` as
    the LAST op of any force-toggling phase, so a transient remove never strands a
    mechanism."""
    pairs = list(getattr(plan, "protect", None) or []) if plan else []
    if extra:
        pairs += list(extra)
    bands = []
    for a, b in pairs:
        bands += chunk_bands(a, b)
    return bands


def run_phase(client, plan, phase, forceload=True, protect=None):
    """Execute every step of a phase, force-load-bracketed. Returns a digest dict.

    When ``forceload`` is on, the phase's own bands are removed on teardown, then
    the plan's permanent ``protect`` set (plus any ``protect`` ``extra`` pairs) is
    re-asserted so a self-running mechanism keeps ticking (Zion P2)."""
    steps = plan.phase_steps(phase)
    digest = {"phase": phase, "steps_total": len(steps), "ok": 0, "failures": [],
              "warnings": [], "blocks_changed": 0, "bands": []}
    if not steps:
        digest["error"] = f"no steps for phase {phase}"
        return digest

    env, bands = phase_envelope_bands(plan, phase)
    digest["bands"] = bands
    digest["envelope"] = env
    protect_bands = protected_bands(plan, protect)
    digest["protected_bands"] = protect_bands
    base_dir = os.path.dirname(plan.path) if plan.path else None

    if forceload:
        _forceload(client, bands, "add")
    try:
        for s in steps:
            seq = s.get("seq")
            try:
                ok, detail, changed, warn = execute_step(client, plan.dimension, s, base_dir=base_dir)
            except (McpError, ValueError) as e:
                digest["failures"].append({"seq": seq, "op": s.get("op"), "error": str(e)})
                return digest  # stop on first hard failure, like the worker
            if not ok:
                digest["failures"].append({"seq": seq, "op": s.get("op"), "error": detail})
                return digest
            digest["ok"] += 1
            if changed:
                digest["blocks_changed"] += changed
            if warn:
                digest["warnings"].append({"seq": seq, "op": s.get("op"), "detail": detail,
                                           "hint": "possible force-load miss (write affected 0 blocks)"
                                           if changed == 0 else "inert/refused"})
    finally:
        if forceload:
            _forceload(client, bands, "remove")
            if protect_bands:
                # P2: re-assert the permanent mechanism set so this phase's
                # remove never unloads a self-running rail loop / farm.
                _forceload(client, protect_bands, "add")
    return digest


# ===========================================================================
# verifier — mechanical contract checks
# ===========================================================================

def _get_id(client, dim, xyz):
    data = client.call_toon("block_get_state", {"dimension": dim, "position": pos_obj(xyz)})
    return data.get("id") if isinstance(data, dict) else None


def _top_solid_y(client, dim, x, z):
    """Highest solid Y at (x,z). block_get_top_y returns first-air-above, so -1."""
    v = client.call_toon("block_get_top_y", {"dimension": dim, "x": x, "z": z})
    try:
        return int(v) - 1
    except (TypeError, ValueError):
        return None


def _line_cells(a, b):
    """Integer points along the straight segment a->b (inclusive), 1-block steps."""
    ax, ay, az = a
    bx, by, bz = b
    steps = max(abs(bx - ax), abs(by - ay), abs(bz - az))
    if steps == 0:
        return [a]
    out = []
    for i in range(steps + 1):
        t = i / steps
        out.append((round(ax + (bx - ax) * t), round(ay + (by - ay) * t), round(az + (bz - az) * t)))
    return out


def check_acceptance(client, dim, rows, phase):
    results = []
    for r in rows:
        if phase is not None and "phase" in r and str(r.get("phase")) != str(phase):
            continue
        try:
            at = parse_coord(r["at"])
        except (KeyError, ValueError) as e:
            results.append(("acceptance", "FAIL", f"bad row {r}: {e}"))
            continue
        want = norm_id(r.get("expect") or r.get("block") or "")
        got = _get_id(client, dim, at)
        ok = (got == want)
        results.append(("acceptance", "PASS" if ok else "FAIL",
                        f"{at} expect {want} got {got}" if not ok else f"{at}={want}"))
    return results


def check_walkability(client, dim, rows):
    results = []
    for r in rows:
        try:
            frm, to = parse_coord(r["from"]), parse_coord(r["to"])
        except (KeyError, ValueError):
            continue
        bad = None
        for (x, y, z) in _line_cells(frm, to):
            floor = _get_id(client, dim, (x, y, z))
            head = _get_id(client, dim, (x, y + 1, z))
            if floor is None or not is_floor_solid(floor) or not is_head_clear(head):
                bad = (x, y, z, floor, head)
                break
        note = r.get("note", "")
        results.append(("walkability", "PASS" if bad is None else "FAIL",
                        f"{note}: ok" if bad is None else f"{note}: blocked at {bad[:3]} floor={bad[3]} head={bad[4]} -> route to planner-class"))
    return results


def check_doors(client, dim, rows):
    facing = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0)}
    results = []
    for r in rows:
        try:
            at = parse_coord(r["at"])
        except (KeyError, ValueError):
            continue
        fwd = facing.get((r.get("facing") or "").lower())
        clear = int(r.get("clearance_blocks", 2))
        bad = None
        if fwd:
            for sign in (1, -1):
                for i in range(1, clear + 1):
                    cx, cy, cz = at[0] + fwd[0] * i * sign, at[1], at[2] + fwd[2] * i * sign
                    floor = _get_id(client, dim, (cx, cy, cz))
                    head = _get_id(client, dim, (cx, cy + 1, cz))
                    if floor is None or not is_floor_solid(floor) or not is_head_clear(head):
                        bad = (cx, cy, cz)
                        break
                if bad:
                    break
        results.append(("doors", "PASS" if bad is None else "FAIL",
                        f"{at} clear" if bad is None else f"{at} blocked at {bad} -> re-orient/re-site (planner-class)"))
    return results


def check_headroom(client, dim, rows):
    results = []
    for r in rows:
        try:
            a = parse_coord(r["over_region_a"])
            b = parse_coord(r["over_region_b"])
        except (KeyError, ValueError):
            continue
        clear = int(r.get("min_clear", 2))
        bad = None
        for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
            for z in range(min(a[2], b[2]), max(a[2], b[2]) + 1):
                ytop = _top_solid_y(client, dim, x, z)
                if ytop is None:
                    continue
                for dy in range(1, clear + 1):
                    if not is_air(_get_id(client, dim, (x, ytop + dy, z)) or "minecraft:air"):
                        bad = (x, ytop, z)
                        break
                if bad:
                    break
            if bad:
                break
        results.append(("headroom", "PASS" if bad is None else "FAIL",
                        "ok" if bad is None else f"obstruction over {bad} -> raise ceiling/re-pitch stair"))
    return results


def check_block_mix_ratios(client, dim, rows):
    """Uses block_scan_summary (histogram + volume) — no raw per-block dump."""
    results = []
    for r in rows:
        try:
            a = parse_coord(r["region_a"])
            b = parse_coord(r["region_b"])
        except (KeyError, ValueError):
            continue
        palette = [norm_id(p) for p in re.split(r"[ ,]+", str(r.get("palette", "")).strip()) if p]
        max_ratio = float(r.get("max_single_ratio", 1.0))
        summary = client.call_toon("block_scan_summary", {"dimension": dim, "box": box_obj(a, b), "top": 512})
        hist = {h["id"]: h["count"] for h in (summary.get("histogram") or [])} if isinstance(summary, dict) else {}
        total = sum(hist.values()) or 1
        worst = max(((bid, cnt / total) for bid, cnt in hist.items()), key=lambda kv: kv[1], default=(None, 0))
        missing = [p for p in palette if p not in hist]
        fail = worst[1] > max_ratio or missing
        msg = f"max {worst[0]}={worst[1]:.2f} (cap {max_ratio})"
        if missing:
            msg += f"; missing palette {missing}"
        results.append(("block_mix_ratios", "FAIL" if fail else "PASS",
                        msg + (" -> retune palette weights" if fail else "")))
    return results


def check_silhouette(client, dim, rows):
    results = []
    for r in rows:
        try:
            a = parse_coord(r["region_a"])
            b = parse_coord(r["region_b"])
        except (KeyError, ValueError):
            continue
        n = int(r.get("sample_count", 8))
        min_var = float(r.get("min_y_variance", 3))
        x1, x2 = min(a[0], b[0]), max(a[0], b[0])
        z1, z2 = min(a[2], b[2]), max(a[2], b[2])
        side = max(1, int(n ** 0.5))
        ys = []
        for i in range(side):
            for j in range(side):
                x = x1 + (x2 - x1) * i // max(1, side - 1)
                z = z1 + (z2 - z1) * j // max(1, side - 1)
                y = _top_solid_y(client, dim, x, z)
                if y is not None:
                    ys.append(y)
        var = (max(ys) - min(ys)) if ys else 0
        ok = var >= min_var
        results.append(("silhouette", "PASS" if ok else "FAIL",
                        f"y_variance={var} (min {min_var})" + ("" if ok else " -> too flat; regenerate noise (terrain-shape)")))
    return results


def check_edge_irregularity(client, dim, rows):
    results = []
    for r in rows:
        try:
            frm, to = parse_coord(r["from"]), parse_coord(r["to"])
        except (KeyError, ValueError):
            continue
        max_run = int(r.get("max_collinear_run", 7))
        cells = _line_cells((frm[0], 0, frm[2]), (to[0], 0, to[2]))
        run_x = run_z = 1
        worst = 1
        for k in range(1, len(cells)):
            run_x = run_x + 1 if cells[k][0] == cells[k - 1][0] else 1
            run_z = run_z + 1 if cells[k][2] == cells[k - 1][2] else 1
            worst = max(worst, run_x, run_z)
        ok = worst <= max_run
        results.append(("edge_irregularity", "PASS" if ok else "FAIL",
                        f"{r.get('edge_name','edge')} longest_run={worst} (max {max_run})"
                        + ("" if ok else " -> add lateral jitter (terrain-shape)")))
    return results


def check_connectivity(client, dim, rows):
    # Same algorithm as walkability between named anchors.
    mapped = [{"from": r.get("site_a"), "to": r.get("site_b"), "note": r.get("via", "connectivity")}
              for r in rows if r.get("site_a") and r.get("site_b")]
    return [("connectivity", st, msg) for (_, st, msg) in check_walkability(client, dim, mapped)]


def _xz(s):
    """(x, z) from 'x z' or 'x y z'."""
    parts = [int(round(float(p))) for p in re.split(r"[ ,]+", str(s).strip()) if p != ""]
    if len(parts) == 2:
        return parts[0], parts[1]
    if len(parts) == 3:
        return parts[0], parts[2]
    raise ValueError(f"expected 'x z' or 'x y z', got {s!r}")


def _perimeter_points(a_xz, b_xz, step=4):
    x1, z1 = a_xz
    x2, z2 = b_xz
    x1, x2 = min(x1, x2), max(x1, x2)
    z1, z2 = min(z1, z2), max(z1, z2)
    pts = []
    x = x1
    while x <= x2:
        pts.append((x, z1))
        pts.append((x, z2))
        x += step
    z = z1
    while z <= z2:
        pts.append((x1, z))
        pts.append((x2, z))
        z += step
    return list(dict.fromkeys(pts))


def check_foundation_naturalised(client, dim, rows):
    """Perimeter at two depths must show >= min_unique_blocks distinct ids (not a sheer rectangle)."""
    results = []
    for r in rows:
        try:
            a, b = _xz(r["perimeter_a"]), _xz(r["perimeter_b"])
            y_lo, y_hi = int(r["y_lo"]), int(r["y_hi"])
        except (KeyError, ValueError):
            continue
        min_unique = int(r.get("min_unique_blocks", 3))
        pts = _perimeter_points(a, b, step=4)
        worst_n, worst_y = None, None
        for y in (y_lo, y_hi):
            ids = {_get_id(client, dim, (x, y, z)) for (x, z) in pts}
            ids.discard(None)
            if worst_n is None or len(ids) < worst_n:
                worst_n, worst_y = len(ids), y
        ok = worst_n is not None and worst_n >= min_unique
        results.append(("foundation_naturalised", "PASS" if ok else "FAIL",
                        f"{r.get('name','foundation')}: {worst_n} unique at y={worst_y} (min {min_unique})"
                        + ("" if ok else " -> sheer face; apply talus-skirt (terrain-shape)")))
    return results


def check_water_continuity(client, dim, rows):
    """No air block above water in a sampled coastal column (the dry-shelf failure)."""
    results = []
    for r in rows:
        try:
            frm, to = _xz(r["from"]), _xz(r["to"])
        except (KeyError, ValueError):
            continue
        n = max(2, int(r.get("sample_count", 8)))
        sea = int(r.get("sea_level", 63))
        seabed = int(r.get("seabed", sea - 30))
        cells = _line_cells((frm[0], 0, frm[1]), (to[0], 0, to[1]))
        picks = cells if len(cells) <= n else [cells[i * (len(cells) - 1) // (n - 1)] for i in range(n)]
        bad = None
        for (x, _, z) in picks:
            seen_water = False
            for y in range(sea, seabed - 1, -1):
                bid = _get_id(client, dim, (x, y, z)) or "minecraft:air"
                if "water" in bid:
                    seen_water = True
                elif is_air(bid) and seen_water:
                    bad = (x, y, z)
                    break
            if bad:
                break
        results.append(("water_continuity", "PASS" if bad is None else "FAIL",
                        f"{r.get('coast_name','coast')}: continuous" if bad is None
                        else f"{r.get('coast_name','coast')}: dry void below water at {bad} -> extend terrain to seabed"))
    return results


def check_seam(client, dim, rows):
    """Build<->world boundary must meet as a graded apron, not a hard wall.

    A seam row ``{a, b, max_step}`` names the boundary line (``a``/``b`` are
    ``x z`` or ``x y z`` endpoints). Sample ``block_get_top_y`` at every 1-block
    step along the line and FAIL if any adjacent pair differs by more than
    ``max_step`` blocks — a sheer wall where build meets terrain (failure mode
    #2). This is the in-world twin of the offline ``verify.verify_seam`` check."""
    results = []
    for r in rows:
        try:
            a_xz, b_xz = _xz(r["a"]), _xz(r["b"])
        except (KeyError, ValueError):
            results.append(("seam", "FAIL", f"bad seam row {r}: needs 'a' and 'b' as 'x z'"))
            continue
        max_step = float(r.get("max_step", 12))
        cells = _line_cells((a_xz[0], 0, a_xz[1]), (b_xz[0], 0, b_xz[1]))
        ys, worst, worst_at = [], 0.0, None
        for (x, _y, z) in cells:
            ys.append(_top_solid_y(client, dim, x, z))
        prev = None
        for i, y in enumerate(ys):
            if y is None:
                continue
            if prev is not None:
                step = abs(y - prev)
                if step > worst:
                    worst, worst_at = step, cells[i][:1] + cells[i][2:]
            prev = y
        ok = worst <= max_step
        name = r.get("name", "seam")
        results.append(("seam", "PASS" if ok else "FAIL",
                        f"{name}: max adjacent step={worst:.0f} (max {max_step})"
                        + ("" if ok else f" at {worst_at} -> hard wall; grade an apron "
                           "(terrain-integrate) — terrain-shape hard-rule 1")))
    return results


def check_block_entity_nbt(client, dim, rows):
    """Content precision — expected_value must appear in the block entity's SNBT."""
    results = []
    for r in rows:
        try:
            at = parse_coord(r["at"])
        except (KeyError, ValueError):
            continue
        want = str(r.get("expected_value", ""))
        field = r.get("field_path", "")
        text, is_err = client.call_text("block_entity_get_nbt", {"dimension": dim, "position": pos_obj(at)})
        ok = (not is_err) and (want in (text or ""))
        results.append(("block_entity_nbt", "PASS" if ok else "FAIL",
                        f"{at} {field}~={want}" if ok
                        else f"{at} {field}: {want!r} not in block-entity NBT -> emit block-nbt correction"))
    return results


def check_event_trigger(client, dim, rows):
    """Functional check: subscribe, fire the trigger command, poll for the expected event type."""
    import time
    results = []
    for r in rows:
        types = [t for t in re.split(r"[ ,]+", str(r.get("event_types", "")).strip()) if t]
        expect = r.get("expect_type") or (types[0] if types else "")
        trigger = r.get("trigger_note")
        if not types or not trigger:
            results.append(("event_trigger", "FAIL", f"row missing event_types/trigger_note: {r}"))
            continue
        sub = client.call_toon("events_subscribe", {"event_types": types})
        sub_id = sub.get("subscription_id") if isinstance(sub, dict) else None
        if not sub_id:
            results.append(("event_trigger", "FAIL", f"could not subscribe to {types}"))
            continue
        client.command(str(trigger))
        time.sleep(0.8)
        poll_text, _ = client.call_text("events_poll", {"subscription_id": sub_id, "max": 64})
        client.call_text("events_unsubscribe", {"subscription_id": sub_id})
        if expect in (poll_text or ""):
            results.append(("event_trigger", "PASS", f"{expect} fired after '{trigger}'"))
            continue
        # No event captured. On a headless server (0 players) entity/block events
        # don't fire for MCP-driven actions, so this is inconclusive, not a failure
        # — defer functional verification to a player-present session.
        players = _status_field(client, "onlinePlayerCount")
        if not players:
            results.append(("event_trigger", "SKIP",
                            f"{expect} not captured headless (events need a player tracking the chunk); "
                            "verify functionally with a player present (inspector/engineer)"))
        else:
            results.append(("event_trigger", "FAIL",
                            f"no {expect} after '{trigger}' -> mechanism not functioning (engineer)"))
    return results


CHECK_FUNCS = {
    "walkability": check_walkability,
    "doors": check_doors,
    "headroom": check_headroom,
    "block_mix_ratios": check_block_mix_ratios,
    "silhouette": check_silhouette,
    "edge_irregularity": check_edge_irregularity,
    "connectivity": check_connectivity,
    "foundation_naturalised": check_foundation_naturalised,
    "water_continuity": check_water_continuity,
    "seam": check_seam,
    "block_entity_nbt": check_block_entity_nbt,
    "event_trigger": check_event_trigger,
}

# Failing these means the terrain/layout generation is wrong → re-plan (FAIL).
# Anything else failing is correctable with a few steps → CORRECTIONS NEEDED.
# `seam` is fundamental: a hard build<->world wall is a re-shape, not a patch.
FUNDAMENTAL_CHECKS = {"silhouette", "connectivity", "foundation_naturalised",
                      "water_continuity", "seam"}


def verify_token(plan, rep):
    """A content-bound token proving *this* verify run passed (Fix 4).

    Deterministic from the plan identity + phase + every check result, so the
    same passing verification always yields the same token and a later audit can
    tell a real PASS from a hand-typed string. It is a tamper-*evidence* tool,
    not tamper-proof: its value is that a build which never ran verify simply has
    no token to write, making a self-approved `status:built` row detectable.
    """
    parts = [str(plan.project or ""), str(plan.element or ""), str(rep["phase"]),
             rep["verdict"], str(rep["passed"]), str(rep["failed"])]
    for (kind, status, _msg) in sorted((r[0], r[1], r[2]) for r in rep["results"]):
        parts.append(f"{kind}:{status}")
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return "vt_" + digest[:12]


def verify_phase(client, plan, phase):
    """Run acceptance + every applicable quality_contract check. Returns a report dict."""
    results = []
    results += check_acceptance(client, plan.dimension, plan.acceptance, phase)
    qc = plan.quality_contract or {}
    for name, fn in CHECK_FUNCS.items():
        rows = qc.get(name)
        if rows:
            results += fn(client, plan.dimension, rows)
    passed = [r for r in results if r[1] == "PASS"]
    failed = [r for r in results if r[1] == "FAIL"]
    skipped = [r for r in results if r[1] == "SKIP"]
    if not failed:
        verdict = "PASS"
    elif any(c[0] in FUNDAMENTAL_CHECKS for c in failed):
        verdict = "FAIL"
    else:
        verdict = "CORRECTIONS NEEDED"
    rep = {"phase": phase, "verdict": verdict, "passed": len(passed),
           "failed": len(failed), "skipped": len(skipped), "results": results}
    # Only a passing verification that actually *checked something* mints a
    # token. A phase with no acceptance and no quality_contract verified nothing
    # — it must not earn `status:built`, so it gets a note instead of a token.
    if verdict == "PASS":
        if passed:
            rep["token"] = verify_token(plan, rep)
        else:
            rep["note"] = ("no acceptance or quality_contract checks defined — "
                           "nothing was verified, so NO token is minted; do not "
                           "mark this element built")
    return rep


# ===========================================================================
# server-mode detection + write-readiness self-test
# ===========================================================================

def detect_mode(client, dim=DEFAULT_DIM):
    """Sample overworld gameTime twice; if it advances at 0 players the server is
    ticking headlessly (dedicated / unpaused) and players are optional."""
    import time
    t0 = _game_time(client, dim)
    players = _status_field(client, "onlinePlayerCount")
    time.sleep(1.2)
    t1 = _game_time(client, dim)
    ticking = (t0 is not None and t1 is not None and t1 > t0)
    mode = "dedicated-or-unpaused" if ticking else "single-player-or-paused"
    return {"mode": mode, "ticking_at_zero_players": ticking,
            "gameTime_delta": (t1 - t0) if (t0 is not None and t1 is not None) else None,
            "onlinePlayerCount": players,
            "guidance": ("Players optional; force-load every work envelope before writing." if ticking
                         else "Have a player join AND keep the client focused (ticks freeze unfocused).")}


def _game_time(client, dim=DEFAULT_DIM):
    data = client.call_toon("level_get_info", {"dimension": dim})
    return data.get("gameTime") if isinstance(data, dict) else None


def _status_field(client, field):
    data = client.call_toon("server_get_status", {})
    if isinstance(data, dict):
        return data.get(field)
    return None


def self_test(client, dim=DEFAULT_DIM, at=(5000, 100, 5000)):
    """Force-load → place marker → read back → restore → release. Proves headless writes."""
    x, z = at[0], at[2]
    client.command(f"forceload add {x} {z} {x} {z}")
    try:
        before = _get_id(client, dim, at)
        client.call_text("block_set_state", {"dimension": dim, "position": pos_obj(at),
                                              "block": {"id": "minecraft:glowstone"}})
        after = _get_id(client, dim, at)
        ok = (after == "minecraft:glowstone")
        client.call_text("block_set_state", {"dimension": dim, "position": pos_obj(at),
                                             "block": {"id": before or "minecraft:air"}})
    finally:
        client.command(f"forceload remove {x} {z} {x} {z}")
    return {"write_readiness": "OK" if ok else "FAILED",
            "detail": f"marker round-trip at {at}: wrote glowstone, read back {after}",
            "hint": "" if ok else "writes are not landing — chunk not loaded or server paused"}


# ===========================================================================
# pre-flight lint — refuse the ziggurat anti-pattern (Fix 5)
# ===========================================================================

def _phase_terrain_blob(plan, phase):
    """Lower-cased text from the plan identity + this phase's step notes."""
    bits = [plan.project or "", plan.element or ""]
    for s in plan.phase_steps(phase):
        bits.append(str(s.get("note") or ""))
    return " ".join(bits).lower()


def phase_has_terrain_op(plan, phase):
    """True if any step in the phase is a terrain op (columns/strata/fillbiome/
    scatter/erode). These ops only exist to place generated landform, so their
    presence makes the phase a terrain phase regardless of its note text."""
    return any((s.get("op") or "").strip() in TERRAIN_OPS for s in plan.phase_steps(phase))


def classify_terrain(plan, phase):
    """True if this phase is organic terrain — either it carries a terrain op
    (the harness-executed path) or its note/identity text reads as terrain (the
    ziggurat-risk class)."""
    if phase_has_terrain_op(plan, phase):
        return True
    blob = _phase_terrain_blob(plan, phase)
    return any(kw in blob for kw in TERRAIN_KEYWORDS)


def _phase_steps_ops(plan, phase):
    return [(s.get("op") or "").strip() for s in plan.phase_steps(phase)]


def recipe_on_disk(plan):
    """Resolve the plan's top-level ``recipe`` field to an existing file (relative
    to the plan dir). Returns the absolute path if it exists, else None."""
    ref = plan.recipe
    if not ref or not isinstance(ref, str):
        return None
    base = os.path.dirname(plan.path) if plan.path else ""
    path = ref if os.path.isabs(ref) else os.path.join(base, ref)
    return path if os.path.isfile(path) else None


def phase_verify_token(plan, phase):
    """The verify token gating this terrain phase: a phase-level token on a step,
    or the plan-level token. Returns the token string, or None."""
    for s in plan.phase_steps(phase):
        tok = s.get("verify_token")
        if tok and str(tok).strip():
            return str(tok).strip()
    if plan.verify_token and str(plan.verify_token).strip():
        return str(plan.verify_token).strip()
    return None


def classify_footprint(plan, phase):
    """True if this phase lands a structure/foundation onto the world — it has a
    place-structure step, OR a ``foundation_naturalised`` qc row, OR an ``erode``
    op carrying a ``protect_box`` (terrain naturalising into a built mass). A
    footprint phase must prove its build<->world boundary is graded (a seam row)."""
    if "place-structure" in _phase_steps_ops(plan, phase):
        return True
    if (plan.quality_contract or {}).get("foundation_naturalised"):
        return True
    base = os.path.dirname(plan.path) if plan.path else None
    for s in plan.phase_steps(phase):
        if (s.get("op") or "").strip() != "erode":
            continue
        try:
            spec = _load_payload(s, base)
        except (OSError, ValueError):
            continue
        if isinstance(spec, dict) and (spec.get("args") or {}).get("protect_box"):
            return True
    return False


def _fill_slabs(plan, phase):
    """Horizontal rectangular slab-fills in a phase: (x1,x2,z1,z2,y) tuples.

    A slab is a fill/replace box wide in both X and Z (>=8) and thin in Y (<=4)
    — the building block of a Y-banded ziggurat.
    """
    slabs = []
    for s in plan.phase_steps(phase):
        if s.get("op") not in ("fill", "replace"):
            continue
        try:
            a = parse_coord(s.get("a"))
            b = parse_coord(s.get("b"))
        except (ValueError, TypeError):
            continue
        dx, dy, dz = abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2])
        if dx >= 8 and dz >= 8 and dy <= 4:
            slabs.append((min(a[0], b[0]), max(a[0], b[0]),
                          min(a[2], b[2]), max(a[2], b[2]), min(a[1], b[1])))
    return slabs


def detect_ziggurat(slabs):
    """Stacked rectangular slabs across >=3 Y-levels that share edges / nest."""
    if len(slabs) < 3:
        return False
    ylevels = sorted({sl[4] for sl in slabs})
    if len(ylevels) < 3:
        return False
    shared = 0
    for i in range(len(slabs)):
        for j in range(i + 1, len(slabs)):
            A, B = slabs[i], slabs[j]
            edge = (A[0] == B[0] or A[1] == B[1] or A[2] == B[2] or A[3] == B[3])
            nested = ((A[0] >= B[0] and A[1] <= B[1] and A[2] >= B[2] and A[3] <= B[3]) or
                      (B[0] >= A[0] and B[1] <= A[1] and B[2] >= A[2] and B[3] <= A[3]))
            if edge or nested:
                shared += 1
    return shared >= 2


NONNEG_REF = "${CLAUDE_PLUGIN_ROOT}/reference/terrain/non-negotiables.md"


def lint_phase(plan, phase):
    """Return (is_terrain, [issue strings]) for the pre-execution gate.

    A **terrain phase** (any step is a terrain op, or the notes read as terrain)
    must (a) reference an on-disk recipe.json, (b) carry a verify_token, and (c)
    carry at least one terrain quality_contract row. A **footprint phase** (lands
    a structure/foundation) must additionally carry a ``seam`` row. The ziggurat
    construction is refused outright. The harness is the SINGLE terrain path —
    ungated terrain never executes."""
    issues = []
    is_terrain = classify_terrain(plan, phase)
    if not is_terrain:
        return is_terrain, issues
    qc = plan.quality_contract or {}

    # (a) the recipe.json the field was generated from must exist on disk — terrain
    # placed without a re-derivable recipe is unverifiable and unrepeatable.
    if not recipe_on_disk(plan):
        ref = plan.recipe
        issues.append(
            "terrain phase has no on-disk recipe.json: the plan's top-level "
            f"'recipe' field is {ref!r} and no such file exists relative to the "
            "plan. emit.emit_plan_toon writes '<prefix>.recipe.json' and names it "
            f"here. No recipe -> no gate. See {NONNEG_REF}.")

    # (b) a verify_token proves the offline verify gate actually ran and passed.
    if not phase_verify_token(plan, phase):
        issues.append(
            "terrain phase carries NO verify_token (phase-level on a step, or "
            "plan-level). emit stamps verify.offline_token(report) only when the "
            f"offline verify PASSed. A token-less terrain phase never cleared the "
            f"gate — refused. See {NONNEG_REF}.")

    # (c) at least one machine-checkable terrain quality_contract row.
    if not any(qc.get(r) for r in TERRAIN_QC_ROWS):
        issues.append(
            "terrain phase carries NO quality_contract terrain rows "
            f"({', '.join(TERRAIN_QC_ROWS)}). A terrain-class phase without a "
            f"quality_contract is a refusal — see {NONNEG_REF}.")

    # footprint phase: the build<->world boundary must be proven graded.
    if classify_footprint(plan, phase) and not qc.get("seam"):
        issues.append(
            "footprint phase (it lands a structure/foundation) carries NO 'seam' "
            "quality_contract row. The build<->world boundary must be sampled for "
            "a hard wall (block_get_top_y along the seam line); add a seam row "
            f"{{a,b,max_step}} proving a graded apron. See {NONNEG_REF}.")

    if detect_ziggurat(_fill_slabs(plan, phase)):
        issues.append(
            "ziggurat anti-pattern: this phase is stacked Y-banded rectangular "
            "slab-fills across >=3 elevations that share edges or nest. That is "
            "the banned terrain construction (terraces + flat tops by definition). "
            "Use the heightmap recipe (block_fill_columns) or live sculpt — "
            "terrain-shape hard-rule 1.")
    return is_terrain, issues


def print_lint(phase, issues):
    print(f"LINT phase {phase}: REFUSED ({len(issues)} issue(s))")
    for i in issues:
        print(f"  XX {i}")
    print("  This phase looks like organic terrain. Route it through the "
          "terrain-shape / terrain-landmark path (recipe -> offline verify -> "
          "emit -> harness), or pass --force only if you are certain this is NOT "
          "organic terrain (e.g. a deliberately rectilinear plaza).")


# ===========================================================================
# registry-backed gates — perceivability + token audit (Fixes 3, 4)
# ===========================================================================

def fetch_registry(client):
    """Read mcbuilder:registry command storage and parse the inner TOON doc."""
    try:
        data = client.call_toon("data_storage_get",
                                 {"namespace": "mcbuilder", "path": "registry"})
    except McpError as e:
        raise McpError(f"could not read mcbuilder:registry — {e}")
    doc = None
    if isinstance(data, dict):
        if "builds" in data or "projects" in data:
            return data  # already the parsed registry
        doc = data.get("doc") or data.get("value") or data.get("data")
    elif isinstance(data, str):
        doc = data
    if isinstance(doc, str) and doc.strip():
        try:
            return toon.parse(doc)
        except toon.ToonError as e:
            raise McpError(f"registry doc did not parse as TOON — {e}")
    raise McpError("registry is empty or has an unexpected shape")


def _registry_builds(reg):
    builds = reg.get("builds")
    return builds if isinstance(builds, list) else []


def _build_xyz(b):
    try:
        return (int(round(float(b["x"]))), int(round(float(b["y"]))),
                int(round(float(b["z"]))))
    except (KeyError, TypeError, ValueError):
        return None


def _world_spawn(client):
    data = client.call_toon("level_get_spawn_point", {})
    if isinstance(data, dict):
        try:
            return (int(round(float(data.get("x", 0)))),
                    int(round(float(data.get("y", 64)))),
                    int(round(float(data.get("z", 0)))))
        except (TypeError, ValueError):
            return None
    return None


def cmd_perceivable(client, spawn=None, threshold=RENDER_DISTANCE_BLOCKS):
    """Fix 3: a built element a human can't see or reach from spawn isn't done."""
    reg = fetch_registry(client)
    builds = [b for b in _registry_builds(reg)
              if str(b.get("status", "")).strip() in ("built", "partial")]
    if spawn is None:
        spawn = _world_spawn(client)
    if spawn is None:
        print("PERCEIVABLE: could not resolve world spawn — pass --spawn 'x y z'")
        return 1
    if not builds:
        print("PERCEIVABLE: no built/partial elements in the registry — nothing "
              "to perceive. (Is the registry being written?)")
        return 1

    has_transit = any(
        any(kw in (str(b.get("element", "")) + " " + str(b.get("project", ""))).lower()
            for kw in TRANSIT_KEYWORDS)
        for b in builds)

    rows, nearest = [], None
    for b in builds:
        xyz = _build_xyz(b)
        if xyz is None:
            rows.append((b.get("element", "?"), None, None))
            continue
        d = math.hypot(xyz[0] - spawn[0], xyz[2] - spawn[2])
        rows.append((b.get("element", "?"), d, xyz))
        nearest = d if nearest is None else min(nearest, d)

    far = [r for r in rows if r[1] is not None and r[1] > threshold]
    print(f"PERCEIVABLE: spawn={spawn[0]} {spawn[1]} {spawn[2]}  "
          f"threshold={threshold}  elements={len(builds)}")
    for (name, d, xyz) in sorted(rows, key=lambda r: (r[1] is None, r[1] or 0)):
        if d is None:
            print(f"  ?? {name}: no coordinates in registry row")
            continue
        mark = "ok " if d <= threshold else "XX "
        at = f"@ {xyz[0]} {xyz[1]} {xyz[2]}" if xyz else ""
        print(f"  {mark}{name}: {d:.0f} blocks from spawn {at}")

    critical = nearest is None or nearest > threshold
    unreachable = bool(far) and not has_transit
    if critical:
        print(f"  XX CRITICAL: nearest element is "
              f"{'inf' if nearest is None else f'{nearest:.0f}'} blocks from spawn "
              f"(> {threshold}). A player at spawn sees an empty world. Move a "
              f"build near spawn, or build connecting transit, before reporting done.")
    elif unreachable:
        print(f"  XX {len(far)} element(s) beyond render distance from spawn and "
              f"NO registered transit connects them — add a path/rail, or report "
              f"them honestly as not-yet-reachable. Not done.")
    elif far:
        print(f"  !! {len(far)} element(s) beyond render distance from spawn, but "
              f"registered transit exists — confirm it actually connects them.")
    else:
        print("  ok every built element is within render distance of spawn.")
    return 1 if (critical or unreachable) else 0


def cmd_audit(client):
    """Fix 4: flag registry `built` rows with no/blank verify_token (self-approval)."""
    reg = fetch_registry(client)
    builds = _registry_builds(reg)
    if not builds:
        print("AUDIT: no builds recorded in the registry.")
        return 0
    unverified = []
    for b in builds:
        if str(b.get("status", "")).strip() != "built":
            continue
        tok = str(b.get("verify_token", "")).strip()
        if not tok or tok.lower() in ("-", "null", "none", "todo") or not tok.startswith("vt_"):
            unverified.append(b)
    print(f"AUDIT: {len(builds)} build row(s); {len(unverified)} marked 'built' "
          f"without a valid verify_token.")
    for b in unverified:
        print(f"  XX {b.get('project', '?')}/{b.get('element', '?')}: "
              f"status=built but verify_token={b.get('verify_token', '<missing>')!r} "
              f"— self-approved, not verified. Re-run harness verify and record the token.")
    if unverified:
        print("  A 'built' row without a vt_ token never passed an independent "
              "verification. Treat these as unverified until re-checked.")
    return 1 if unverified else 0


# ===========================================================================
# reporting + CLI
# ===========================================================================

def _as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


def print_digest(d):
    print(f"RUN phase {d['phase']}: {d['ok']}/{d['steps_total']} steps ok, "
          f"{d['blocks_changed']} blocks changed, {len(d['bands'])} force-load band(s)")
    if d.get("envelope"):
        print(f"  envelope(x,z): {d['envelope']}")
    if d.get("protected_bands"):
        print(f"  re-asserted {len(d['protected_bands'])} protected force-load "
              f"band(s) (permanent mechanism chunks kept loaded)")
    for w in d.get("warnings", []):
        print(f"  WARN seq {w['seq']} ({w['op']}): {w['hint']} — {w['detail']}")
    for f in d.get("failures", []):
        print(f"  FAIL seq {f['seq']} ({f['op']}): {f['error']}")
    if d.get("error"):
        print(f"  ERROR: {d['error']}")


def print_report(rep):
    skip = rep.get("skipped", 0)
    tail = f" / {skip} skip" if skip else ""
    print(f"VERIFY phase {rep['phase']}: {rep['verdict']}  "
          f"({rep['passed']} pass / {rep['failed']} fail{tail})")
    marks = {"PASS": "ok ", "FAIL": "XX ", "SKIP": ".. "}
    for (kind, status, msg) in rep["results"]:
        print(f"  {marks.get(status, '?? ')}{kind}: {msg}")
    if rep.get("token"):
        print(f"  VERIFY-TOKEN: {rep['token']}")
        print(f"    -> record this in the registry build row's verify_token cell; "
              f"status:built is only legitimate with it.")
    elif rep.get("note"):
        print(f"  (no token) {rep['note']}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="builder.harness")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "verify", "build", "freshness"):
        p = sub.add_parser(name)
        p.add_argument("plan")
        p.add_argument("phase")
        if name in ("run", "build"):
            p.add_argument("--force", action="store_true",
                           help="override the terrain anti-pattern lint refusal")
    sub.add_parser("mode")
    st = sub.add_parser("selftest")
    st.add_argument("--dim", default=DEFAULT_DIM)
    pv = sub.add_parser("perceivable")
    pv.add_argument("--threshold", type=int, default=RENDER_DISTANCE_BLOCKS)
    pv.add_argument("--spawn", default=None, help="override world spawn as 'x y z'")
    sub.add_parser("audit")
    args = ap.parse_args(argv)

    client = McpClient()
    client.handshake()

    if args.cmd == "mode":
        print(json.dumps(detect_mode(client), indent=2))
        return 0
    if args.cmd == "selftest":
        res = self_test(client, dim=args.dim)
        print(json.dumps(res, indent=2))
        return 0 if res["write_readiness"] == "OK" else 1
    if args.cmd == "perceivable":
        spawn = parse_coord(args.spawn) if args.spawn else None
        return cmd_perceivable(client, spawn=spawn, threshold=args.threshold)
    if args.cmd == "audit":
        return cmd_audit(client)

    plan = load_plan(args.plan)

    if args.cmd == "freshness":
        return _freshness(client, plan, args.phase)
    if args.cmd == "run":
        _is_terrain, issues = lint_phase(plan, args.phase)
        if issues and not args.force:
            print_lint(args.phase, issues)
            return 1
        digest = run_phase(client, plan, args.phase, forceload=True)
        print_digest(digest)
        return 1 if (digest.get("failures") or digest.get("error")) else 0
    if args.cmd == "verify":
        rep = verify_phase(client, plan, args.phase)
        print_report(rep)
        return 0 if rep["verdict"] == "PASS" else 1
    if args.cmd == "build":
        _is_terrain, issues = lint_phase(plan, args.phase)
        if issues and not args.force:
            print_lint(args.phase, issues)
            return 1
        # Hold the force-load across BOTH run and verify (guidance Rule 1).
        _env, bands = phase_envelope_bands(plan, args.phase)
        protect_bands = protected_bands(plan)
        _forceload(client, bands, "add")
        try:
            digest = run_phase(client, plan, args.phase, forceload=False)
            print_digest(digest)
            if digest.get("failures") or digest.get("error"):
                return 1
            rep = verify_phase(client, plan, args.phase)
        finally:
            _forceload(client, bands, "remove")
            if protect_bands:
                _forceload(client, protect_bands, "add")   # P2: keep mechanisms ticking
        print_report(rep)
        return 0 if rep["verdict"] == "PASS" else 1
    return 0


FRESHNESS_DRIFT_TOLERANCE = 24      # blocks; live top-Y this far from planned = drift


def _freshness(client, plan, phase, sample=4):
    """Stale-plan pre-check.

    A terrain ``columns``/``strata`` step's payload carries the planned surface Y
    per column, so we *can* check freshness: sample a few columns, compare the
    planned height against the live ``block_get_top_y``, and WARN if the world has
    drifted far from what the plan assumes (someone re-shaped the area, or the
    coordinates are stale). For any other op the schema carries no before-state —
    we cannot determine freshness, so we say so plainly (proceed with
    forceload + selftest) rather than silently reporting OK.

    Exit 0 = no drift detected OR cannot-determine (an honest non-blocking note);
    exit 1 = a terrain column drifted past the tolerance (a likely stale plan).
    """
    base_dir = os.path.dirname(plan.path) if plan.path else None
    env = plan.envelopes.get(_as_int(phase)) or derive_envelope(plan, phase)
    planned = []          # (x, z, planned_y)
    terrain_steps = 0
    for s in plan.phase_steps(phase):
        if (s.get("op") or "").strip() not in ("columns", "strata"):
            continue
        terrain_steps += 1
        try:
            payload = _load_payload(s, base_dir)
        except (OSError, ValueError) as e:
            print(f"FRESHNESS phase {phase}: cannot read a {s.get('op')} payload "
                  f"({e}); cannot determine drift — proceed with forceload + selftest.")
            return 0
        planned += _column_height_samples(payload, want=sample)
        if len(planned) >= sample:
            break

    # Resolve the live surface at each sampled column. Force-load the bands first
    # so a read isn't a void (−64) force-load miss masquerading as drift.
    samples = []          # (x, z, planned_y, live_y)
    bands = chunk_bands(*env) if env else []
    protect_bands = protected_bands(plan)
    if planned:
        _forceload(client, bands, "add")
        try:
            for (x, z, py) in planned[:sample]:
                samples.append((x, z, py, _top_solid_y(client, plan.dimension, x, z)))
        finally:
            _forceload(client, bands, "remove")
            if protect_bands:
                _forceload(client, protect_bands, "add")   # P2: keep mechanisms ticking

    if not samples:
        if terrain_steps:
            print(f"FRESHNESS phase {phase}: {terrain_steps} terrain column step(s) "
                  "but no sampleable columns (empty/degenerate payload); cannot "
                  "determine drift — proceed with forceload + selftest.")
        else:
            print(f"FRESHNESS phase {phase}: no terrain column steps and the "
                  "fill/set/clone schema carries no before-state, so freshness "
                  "CANNOT be determined here — proceed with forceload + selftest "
                  "(harness.py selftest), which proves writes land before you build.")
        if env:
            print(f"  envelope(x,z): {env}")
        return 0

    drifted, lines = [], []
    for (x, z, planned, live) in samples[:sample]:
        if live is None:
            lines.append(f"  ?? ({x},{z}): planned surface y={planned}, live top-Y "
                         "unreadable (-64/void = force-load miss, not drift)")
            continue
        delta = abs(live - planned)
        mark = "ok " if delta <= FRESHNESS_DRIFT_TOLERANCE else "XX "
        lines.append(f"  {mark}({x},{z}): planned y={planned} live={live} (d={delta})")
        if delta > FRESHNESS_DRIFT_TOLERANCE:
            drifted.append((x, z, planned, live, delta))

    verdict = "DRIFTED" if drifted else "fresh"
    print(f"FRESHNESS phase {phase}: {verdict} — sampled {len(lines)} terrain "
          f"column(s) vs live top-Y (tolerance {FRESHNESS_DRIFT_TOLERANCE} blocks)")
    for ln in lines:
        print(ln)
    if drifted:
        print(f"  XX {len(drifted)} column(s) drifted past tolerance — the plan's "
              "coordinates look STALE against the current world (re-shaped or "
              "moved). Re-survey and re-emit before executing; do not overwrite "
              "live terrain blind.")
        return 1
    print("  ok the live surface still matches the plan's assumed heights.")
    return 0


def _column_height_samples(payload, want=4):
    """Pick up to ``want`` ``(x, z, planned_y)`` triples spread across a columns
    plan payload (row-major index = xi*length + zi). The caller resolves the live
    surface at each (x, z) to compare against ``planned_y``."""
    if not isinstance(payload, dict):
        return []
    try:
        ox = int(payload["origin"]["x"])
        oz = int(payload["origin"]["z"])
        w = int(payload["width"])
        ln = int(payload["length"])
        heights = payload["height"]
    except (KeyError, TypeError, ValueError):
        return []
    n = w * ln
    if n <= 0 or not isinstance(heights, list) or len(heights) < n:
        return []
    # Spread the picks across the grid (row-major index = xi*length + zi).
    picks = []
    for k in range(want):
        idx = (k * (n - 1) // max(1, want - 1)) if want > 1 else 0
        xi, zi = divmod(idx, ln)
        x, z = ox + xi, oz + zi
        planned = _coerce_int(heights[idx])
        picks.append((x, z, planned))
    return picks


if __name__ == "__main__":
    # The Windows console defaults to cp1252; any non-ASCII in a printed digest
    # (e.g. a distance ∞ or a Δ) would otherwise raise UnicodeEncodeError AFTER
    # the verdict+token are printed, turning a PASS into exit 1 and breaking the
    # exit-code contract callers branch on. Force UTF-8 so output never crashes.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
