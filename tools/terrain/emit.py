"""Turn a verified terrain recipe into executable in-world steps — the bridge
from the offline toolkit to the MCP placement path.

``emit_world`` runs the whole pipeline for a recipe and returns a dict of ready
payloads:
  columns   → a block_fill_columns(_strata) plan (the bulk mass)
  biomes    → a list of level_fill_biome rectangles
  scatter   → a list of (x,y,z,kind,id) placements for the batch feature tool
  verify    → the offline verify Report (the gate; emit_world raises if it fails
              unless allow_unverified=True)

``emit_plan_toon`` is the *single terrain path*: it runs the same gate, then
writes a ``<prefix>.plan.toon`` whose terrain phase carries the terrain step-ops
(columns/strata → fillbiome → scatter, pre-tiled to <=65,536 columns), a
top-level recipe reference, an offline verify token, and a quality_contract with
the terrain + (for blended fields) seam rows. The stdlib ``builder.harness`` is
the only executor — it runs those ops with count assertions and its lint refuses
ungated terrain. So terrain no longer bypasses the autonomy gate.
"""
from __future__ import annotations

import hashlib
import json
import os

from .recipe import build_field, save as _recipe_save
from .materialize import MaterialSpec, to_columns_plan
from .climate import BiomeField
from .scatter import scatter_for_biomes
from . import materialize as _materialize
from . import verify as _verify


class VerifyError(RuntimeError):
    pass


def _tile_columns_plan(plan: dict, cap: int = 65536) -> list:
    """Prefer ``materialize.tile_columns_plan`` (contract 2) once it ships; until
    then fall back to a local splitter with the same contract: split a columns
    plan along its LONGER axis into sub-plans each with ``width*length <= cap``,
    slicing the row-major (index = xi*length + zi) arrays and adjusting the per-
    tile origin. Each sub-plan stays a valid ``block_fill_columns`` plan."""
    fn = getattr(_materialize, "tile_columns_plan", None)
    if callable(fn):
        return fn(plan, cap)
    return _fallback_tile(plan, cap)


def _fallback_tile(plan: dict, cap: int) -> list:
    w, length = int(plan["width"]), int(plan["length"])
    if w * length <= cap:
        return [plan]
    height = plan["height"]
    surface = plan["surface"]
    subsurface = plan["subsurface"]
    ox, oz = plan["origin"]["x"], plan["origin"]["z"]

    # split the longer axis; size each tile so width*length <= cap
    if w >= length:
        tw = max(1, cap // max(1, length))
        tiles = []
        for xs in range(0, w, tw):
            xe = min(xs + tw, w)
            sub = _slice_plan(plan, height, surface, subsurface, length,
                              xs, xe, 0, length, ox + xs, oz)
            tiles.append(sub)
        return tiles
    tl = max(1, cap // max(1, w))
    tiles = []
    for zs in range(0, length, tl):
        ze = min(zs + tl, length)
        sub = _slice_plan(plan, height, surface, subsurface, length,
                          0, w, zs, ze, ox, oz + zs)
        tiles.append(sub)
    return tiles


def _slice_plan(plan, height, surface, subsurface, length,
                xs, xe, zs, ze, new_ox, new_oz) -> dict:
    nh, ns, nsub = [], [], []
    for xi in range(xs, xe):
        row = xi * length
        for zi in range(zs, ze):
            j = row + zi
            nh.append(height[j])
            ns.append(surface[j])
            nsub.append(subsurface[j])
    sub = dict(plan)
    sub["origin"] = {"x": int(new_ox), "z": int(new_oz)}
    sub["width"] = xe - xs
    sub["length"] = ze - zs
    sub["height"] = nh
    sub["surface"] = ns
    sub["subsurface"] = nsub
    return sub


def emit_world(recipe: dict, *, allow_unverified: bool = False) -> dict:
    """Evaluate a recipe → field, run the verify gate, then emit columns + biomes
    + scatter payloads. ``recipe`` extends the build recipe (see recipe.py) with
    optional ``material`` (a MaterialSpec spec) and ``scatter``/``biomes`` flags."""
    hf = build_field(recipe)
    origin = recipe.get("origin", [0, 0, 0])
    ox, oz = int(origin[0]), int(origin[-1])
    dim = recipe.get("dimension", "minecraft:overworld")

    # material spec: explicit, or a natural default from masks. Built BEFORE the
    # gate so verify sees it — the spec drives the palette-monoculture and
    # underwater-face checks, and a blended/multi-region recipe folds in the seam
    # check. (Previously emit ran verify(hf) bare, so those checks never ran on
    # the emit path despite the gate advertising them — closed here.)
    mat = recipe.get("material")
    if mat:
        spec = _material_from_spec(mat, hf, recipe=recipe)
    else:
        snow_y = recipe.get("snow_y")
        spec = MaterialSpec.natural(hf, snow_y=snow_y)
        if recipe.get("strata"):
            spec.strata = [(s["block"], int(s["thickness"])) for s in recipe["strata"]]

    report = _verify.verify(hf, spec=spec, recipe=recipe)
    if not report.ok and not allow_unverified:
        raise VerifyError(str(report))

    columns = to_columns_plan(hf, spec, origin=(ox, oz), dimension=dim)

    biomes = None
    scatter = None
    if recipe.get("biomes", True):
        bf = BiomeField(hf, seed=int(recipe.get("seed", 0)))
        biomes = bf.to_biome_fill_plan(origin=(ox, oz))
        if recipe.get("scatter", True):
            scatter = scatter_for_biomes(hf, bf, origin=(ox, oz),
                                         seed=int(recipe.get("seed", 0)))

    return {"field": hf, "verify": report, "columns": columns,
            "biomes": biomes, "scatter": scatter}


def _material_from_spec(mat: dict, hf, recipe: dict | None = None) -> MaterialSpec:
    """Build a MaterialSpec from a recipe's ``material`` block.

    Three forms are supported. A ``belt_regions`` list selects the per-arc form
    (``_belt_region_spec``): each region's palette is keyed to a position along
    the belt centerline, so the colour morphs region→region around a blended
    loop the way the shape does (red rock → granite → alpine → forest). The
    simple declarative form ``{surface, snow_y, cliff_slope, beach, strata}``
    builds the default masks + a global steep-face slant (good for grass/rock
    terrain).

    A *layered* form is selected when any of ``snow_palette`` / ``cliff_palette``
    / ``lake_floor`` is given. It expresses the whole surface as an ordered,
    mask-driven ``Layer`` stack (first match wins per column) and **drops** the
    global slant override, so snow/ice can clad a steep horn above the snowline
    instead of being repainted to rock everywhere it is steep — the realistic
    glacial story. Order: lake floor (submerged) → snow/ice (above ``snow_y``) →
    rock cliffs (steep, below the snowline) → base flank mix. The lake-floor mix
    keeps the submerged face multi-block so the GATE-A underwater_face check
    still passes."""
    from .materialize import Layer
    from . import masks as M

    if "belt_regions" in mat:
        return _belt_region_spec(mat, hf, recipe)

    layered = any(k in mat for k in ("snow_palette", "cliff_palette", "lake_floor"))

    if not layered:
        spec = MaterialSpec.natural(
            hf,
            surface=mat.get("surface"),
            snow_y=mat.get("snow_y"),
            cliff_slope=mat.get("cliff_slope", 50.0),
            beach=mat.get("beach", True),
        )
        if mat.get("strata"):
            spec.strata = [(s["block"], int(s["thickness"])) for s in mat["strata"]]
        return spec

    sea = hf.sea_level
    snow_y = mat.get("snow_y")
    cliff_slope = float(mat.get("cliff_slope", 50.0))
    steep = M.mask_slope(hf.h, lo=cliff_slope)
    submerged = M.mask_y(hf.h, "<", sea)

    layers = []
    # 1) turquoise / custom lake floor — every submerged column.
    lake = mat.get("lake_floor")
    if lake:
        layers.append(Layer(mask=submerged, palette=dict(lake),
                            subsurface="minecraft:gravel"))
    # 2) snow / ice cap — high ground, above any submerged/lake cells. Clads the
    #    horns even where steep (glacial horns are snow- and ice-covered).
    snow_pal = mat.get("snow_palette")
    if snow_pal and snow_y is not None:
        snow_mask = M.mask_y(hf.h, ">", snow_y) & ~submerged
        layers.append(Layer(mask=snow_mask, palette=dict(snow_pal),
                            subsurface="minecraft:dirt"))
    # 3) rock cliffs — steep faces below the snowline (and above water).
    cliff_pal = mat.get("cliff_palette")
    if cliff_pal:
        cliff_mask = steep & ~submerged
        if snow_y is not None:
            cliff_mask = cliff_mask & M.mask_y(hf.h, "<=", snow_y)
        layers.append(Layer(mask=cliff_mask, palette=dict(cliff_pal),
                            subsurface="minecraft:stone"))

    spec = MaterialSpec(layers=layers, base=mat.get("surface"),
                        subsurface=mat.get("subsurface", "minecraft:dirt"))
    spec.slant = []                       # ordered layers do the slant's job
    if mat.get("strata"):
        spec.strata = [(s["block"], int(s["thickness"])) for s in mat["strata"]]
    return spec


def _belt_region_spec(mat: dict, hf, recipe: dict | None) -> MaterialSpec:
    """Per-arc material for a blended belt loop: each region's palette is keyed
    to a position ``s`` along the belt centerline.

    ``mat["belt_regions"]`` is a list of ``{s, surface, subsurface?, cliff?,
    snow_y?, snow?}``. Every grid cell is assigned to the region whose ``s`` is
    nearest in *circular* arc-distance (so a closed loop wraps cleanly), giving
    colour zones that mirror the shape keypoints. Within a region the layer
    order is snow (above ``snow_y``) → cliff (steep, below the snowline) →
    surface, so a red-rock wall reads as red rock and an alpine horn keeps its
    snow cap. The region masks partition the grid, so the global ``slant`` is
    dropped (the per-region cliff layers do its job) — the same reasoning as the
    layered glacial form. The centerline is rebuilt from ``recipe["belt"]``."""
    import numpy as np
    from .materialize import Layer
    from . import masks as M
    from .field import Centerline

    belt = (recipe or {}).get("belt") or {}
    if not belt.get("centerline"):
        raise VerifyError("belt_regions material needs recipe['belt']['centerline']")
    cl = Centerline([tuple(p) for p in belt["centerline"]],
                    closed=bool(belt.get("closed", False)))
    nx, nz = hf.nx, hf.nz
    X, Z = np.meshgrid(np.arange(nx), np.arange(nz), indexing="ij")
    s, _perp = cl.query(X, Z)
    sf = (s / cl.length) if cl.length else np.zeros_like(s)

    regions = mat["belt_regions"]
    centers = np.array([float(r["s"]) for r in regions])
    diff = np.abs(sf[..., None] - centers[None, None, :])        # (nx, nz, R)
    circ = np.minimum(diff, 1.0 - diff)                          # wrap on [0, 1)
    nearest = np.argmin(circ, axis=-1)                           # (nx, nz)

    cliff_slope = float(mat.get("cliff_slope", 50.0))
    steep = M.mask_slope(hf.h, lo=cliff_slope)
    above_water = ~M.mask_y(hf.h, "<", hf.sea_level)

    layers: list = []
    for ri, r in enumerate(regions):
        region = nearest == ri
        snow_y = r.get("snow_y")
        if snow_y is not None and r.get("snow"):
            snow_mask = region & M.mask_y(hf.h, ">", snow_y) & above_water
            layers.append(Layer(mask=snow_mask, palette=dict(r["snow"]),
                                subsurface=r.get("snow_subsurface", "minecraft:dirt")))
        if r.get("cliff"):
            cliff_mask = region & steep & above_water
            if snow_y is not None:
                cliff_mask = cliff_mask & M.mask_y(hf.h, "<=", snow_y)
            layers.append(Layer(mask=cliff_mask, palette=dict(r["cliff"]),
                                subsurface=r.get("cliff_subsurface",
                                                 r.get("subsurface", "minecraft:stone"))))
        layers.append(Layer(mask=region, palette=dict(r["surface"]),
                            subsurface=r.get("subsurface", "minecraft:dirt")))

    spec = MaterialSpec(layers=layers,
                        base=mat.get("surface") or dict(regions[0]["surface"]),
                        subsurface=mat.get("subsurface", "minecraft:dirt"))
    spec.slant = []                       # the per-region cliff layers do its job
    if mat.get("strata"):
        spec.strata = [(s2["block"], int(s2["thickness"])) for s2 in mat["strata"]]
    return spec


def write_payloads(payloads: dict, prefix: str) -> dict:
    """Write columns/biomes/scatter payloads to JSON files next to ``prefix``.
    Returns the file paths. (The field/verify objects are not serialised here.)"""
    paths = {}
    if payloads.get("columns"):
        p = f"{prefix}_columns.json"
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(payloads["columns"], fh)
        paths["columns"] = p
    if payloads.get("biomes"):
        p = f"{prefix}_biomes.json"
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(payloads["biomes"], fh)
        paths["biomes"] = p
    if payloads.get("scatter"):
        p = f"{prefix}_scatter.json"
        with open(p, "w", encoding="utf-8") as fh:
            json.dump([list(t) for t in payloads["scatter"]], fh)
        paths["scatter"] = p
    return paths


# ======================================================================
# emit_plan_toon — the single terrain path (the harness executes it)
# ======================================================================

def _scatter_to_placements(scatter: list) -> list:
    """Normalise the scatter tuples ``(x, y, z, kind, id)`` into the placement
    dicts the harness's ``scatter`` op batches into ``level_place_features_batch``
    (``{feature, x, y, z}``). ``kind`` ("feature"/"structure") is preserved for
    callers that route structures differently."""
    out = []
    for t in scatter:
        x, y, z, kind, fid = t[0], t[1], t[2], t[3], t[4]
        out.append({"feature": fid, "x": int(x), "y": int(y), "z": int(z),
                    "kind": kind})
    return out


def _is_blended(recipe: dict, hf) -> bool:
    """True if this field spans multiple regions blended into one continuous
    surface — the case that needs a seam (footprint/integration) check. A recipe
    declares it via ``blended``/``multi_region``, or it is inferred from the
    presence of a centerline/belt/regions/blend node in the recipe."""
    for key in ("blended", "multi_region", "multiregion"):
        if recipe.get(key):
            return True
    for key in ("centerline", "belt", "regions", "blend"):
        if recipe.get(key):
            return True
    graph = recipe.get("graph") or {}
    return bool(_graph_mentions(graph, ("BeltCoord", "Blend", "Region", "Mask")))


def _graph_mentions(node, types) -> bool:
    """Recursively scan a sampler-graph node tree for any node ``type`` in
    ``types`` (used to infer a blended/multi-region field)."""
    if isinstance(node, dict):
        if str(node.get("type")) in types:
            return True
        return any(_graph_mentions(v, types) for v in node.values())
    if isinstance(node, (list, tuple)):
        return any(_graph_mentions(v, types) for v in node)
    return False


def _offline_token(report) -> str:
    """``verify.offline_token`` shim — deterministic ``ovt_<12hex>`` over the
    report's ``(name, passed)`` check tuples (contract 3). Prefers the real
    ``verify.offline_token`` once the verify module ships it; the local fallback
    matches its specified algorithm so emit stamps the same token either way."""
    fn = getattr(_verify, "offline_token", None)
    if callable(fn):
        return fn(report)
    parts = [f"{name}:{1 if passed else 0}"
             for (name, passed, _detail) in report.checks]
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return "ovt_" + digest[:12]


def _columns_steps(payloads: dict, base_dir: str, prefix_name: str, *,
                   seq_start: int, phase: int, cap: int = 65536) -> list:
    """Pre-tile the columns plan into <=cap-column sub-plans, write each as a
    payload JSON, and return one ``columns``/``strata`` step per tile (paths
    relative to ``base_dir`` — the harness resolves them against the plan dir)."""
    plan = payloads.get("columns")
    if not plan:
        return []
    op = "strata" if plan.get("strata") else "columns"
    tiles = _tile_columns_plan(plan, cap=cap)
    steps = []
    for i, tile in enumerate(tiles):
        fname = f"{prefix_name}_columns_{i:03d}.json"
        with open(os.path.join(base_dir, fname), "w", encoding="utf-8") as fh:
            json.dump(tile, fh)
        cols = tile["width"] * tile["length"]
        ox, oz = tile["origin"]["x"], tile["origin"]["z"]
        steps.append({
            "op": op, "phase": phase, "seq": seq_start + i, "payload": fname,
            "note": f"{op} tile {i + 1}/{len(tiles)} ({cols} cols) at x={ox} z={oz}",
        })
    return steps


def _bbox_xz(plan_dict: dict):
    """World (x1,z1,x2,z2) footprint of a columns plan dict."""
    ox = plan_dict["origin"]["x"]
    oz = plan_dict["origin"]["z"]
    return (ox, oz, ox + plan_dict["width"] - 1, oz + plan_dict["length"] - 1)


def emit_plan_toon(recipe: dict, prefix: str, *, phase: int = 1,
                   dimension: str | None = None) -> dict:
    """Run the verify gate (raises ``VerifyError`` on failure), pre-tile columns,
    write every payload + the recipe JSON, and write a ``<prefix>.plan.toon`` the
    stdlib ``builder.harness`` can execute and lint-gate. Returns the plan dict.

    The terrain phase steps run columns/strata (the bulk mass) → fillbiome →
    scatter in sequential ``seq``. The plan carries:
      - a top-level ``recipe`` field naming the on-disk recipe JSON (the lint
        requires it to exist relative to the plan dir);
      - a ``verify_token`` (``verify.offline_token`` of the passing report) —
        tamper-evidence that the offline gate actually ran;
      - a ``quality_contract`` with a terrain ``silhouette`` row and an
        ``edge_irregularity`` row, plus a ``seam`` row when the field is blended
        / multi-region (footprint/integration).
    """
    payloads = emit_world(recipe)  # runs the gate; raises VerifyError on FAIL
    report = payloads["verify"]
    hf = payloads["field"]

    base_dir = os.path.dirname(os.path.abspath(prefix)) or "."
    prefix_name = os.path.basename(prefix)
    os.makedirs(base_dir, exist_ok=True)

    # 1. payloads (columns are pre-tiled below; biomes + scatter written here)
    bio_path = None
    if payloads.get("biomes"):
        bio_path = f"{prefix_name}_biomes.json"
        with open(os.path.join(base_dir, bio_path), "w", encoding="utf-8") as fh:
            json.dump(payloads["biomes"], fh)
    scat_path = None
    if payloads.get("scatter"):
        scat_path = f"{prefix_name}_scatter.json"
        with open(os.path.join(base_dir, scat_path), "w", encoding="utf-8") as fh:
            json.dump(_scatter_to_placements(payloads["scatter"]), fh)

    # 2. recipe JSON (the lint requires it on disk, relative to the plan dir)
    recipe_name = f"{prefix_name}.recipe.json"
    _recipe_save(recipe, os.path.join(base_dir, recipe_name))

    # 3. terrain steps: columns/strata tiles, then fillbiome, then scatter
    dim = dimension or recipe.get("dimension", "minecraft:overworld")
    steps = _columns_steps(payloads, base_dir, prefix_name,
                           seq_start=1, phase=phase)
    seq = (steps[-1]["seq"] + 1) if steps else 1
    if bio_path:
        steps.append({"op": "fillbiome", "phase": phase, "seq": seq,
                      "payload": bio_path,
                      "note": f"paint {len(payloads['biomes'])} biome rect(s)"})
        seq += 1
    if scat_path:
        steps.append({"op": "scatter", "phase": phase, "seq": seq,
                      "payload": scat_path,
                      "note": f"scatter {len(payloads['scatter'])} feature(s)"})
        seq += 1

    # 4. verify token + quality_contract
    token = _offline_token(report)
    cols = payloads.get("columns") or {}
    if cols:
        x1, z1, x2, z2 = _bbox_xz(cols)
    else:                                   # degenerate guard (gate already ran)
        x1, z1, x2, z2 = 0, 0, 0, 0
    qc = {
        "silhouette": [{
            "region_a": f"{x1} 0 {z1}", "region_b": f"{x2} 0 {z2}",
            "sample_count": 9, "min_y_variance": 3,
        }],
        "edge_irregularity": [{
            "edge_name": "ridgeline", "from": f"{x1} 0 {z1}",
            "to": f"{x2} 0 {z2}", "max_collinear_run": 7,
        }],
    }
    blended = _is_blended(recipe, hf)
    if blended:
        sea = int(round(hf.sea_level))
        qc["seam"] = [{
            "a": f"{x1} {sea} {z1}", "b": f"{x2} {sea} {z2}",
            "max_step": 12,
        }]

    plan = {
        "plan": {
            "project": recipe.get("project") or prefix_name,
            "element": recipe.get("element") or "terrain",
            "dimension": dim,
        },
        "recipe": recipe_name,
        "verify_token": token,
        "blended": bool(blended),
        "steps": steps,
        "quality_contract": qc,
    }

    with open(f"{prefix}.plan.toon", "w", encoding="utf-8") as fh:
        fh.write(_to_toon(plan))
    return plan


# ----------------------------------------------------------------------
# minimal TOON encoder — the subset builder.toon.parse reads back
# ----------------------------------------------------------------------

def _to_toon(plan: dict) -> str:
    """Encode the plan dict as TOON parseable by ``builder.toon.parse``.

    Handles exactly the shapes ``emit_plan_toon`` produces: a root object with
    scalar fields, one nested ``plan`` object, a top-level tabular ``steps``
    array, and a ``quality_contract`` object whose values are tabular arrays."""
    lines: list = []
    # nested + scalar top-level fields first, in a stable order
    if "plan" in plan:
        lines.append("plan:")
        for k, v in plan["plan"].items():
            lines.append(f"  {k}: {_toon_scalar(v)}")
    for k in ("recipe", "verify_token", "blended"):
        if k in plan:
            lines.append(f"{k}: {_toon_scalar(plan[k])}")
    lines.extend(_toon_table("steps", plan.get("steps") or [], indent=0))
    qc = plan.get("quality_contract") or {}
    if qc:
        lines.append("quality_contract:")
        for name, rows in qc.items():
            lines.extend(_toon_table(name, rows, indent=1))
    return "\n".join(lines) + "\n"


def _toon_table(name: str, rows: list, *, indent: int) -> list:
    """A TOON tabular array ``name[N]{cols}:`` + N rows. Columns are the union of
    keys across rows (stable first-seen order). Empty list → ``name[]``."""
    pad = "  " * indent
    if not rows:
        return [f"{pad}{name}[]"]
    cols: list = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    out = [f"{pad}{name}[{len(rows)}]{{{','.join(cols)}}}:"]
    rowpad = "  " * (indent + 1)
    for r in rows:
        cells = [_toon_cell(r.get(c)) for c in cols]
        out.append(rowpad + ",".join(cells))
    return out


def _toon_scalar(v) -> str:
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, (int, float)):
        return repr(v) if isinstance(v, float) else str(v)
    s = str(v)
    if s == "" or _needs_quote(s):
        return _quote(s)
    return s


def _toon_cell(v) -> str:
    """Scalar for a tabular row cell. A cell that contains a comma, a quote, or
    bracket characters MUST be quoted so ``_split_cells`` keeps it intact; bare
    strings (block ids, ``x y z`` coords) are emitted raw."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, (int, float)):
        return repr(v) if isinstance(v, float) else str(v)
    s = str(v)
    if s == "" or _needs_quote(s):
        return _quote(s)
    return s


def _needs_quote(s: str) -> bool:
    return any(c in s for c in (",", '"', "[", "]", "{", "}", ":", "\n", "\t"))


def _quote(s: str) -> str:
    s = (s.replace("\\", "\\\\").replace('"', '\\"')
          .replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r"))
    return f'"{s}"'
