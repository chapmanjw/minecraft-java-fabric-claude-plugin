# minecraft-builder tools

Helper scripts the builder skills run on the local machine. They are bundled
with the plugin and referenced from skills via
`${CLAUDE_PLUGIN_ROOT}/tools/…`. Everything here runs in **Claude Code** (CLI or
desktop app), where the agent has local Bash and can read the PNGs it produces.

## Dependencies

Stdlib + **numpy** + **Pillow** only. Install once:

```sh
python -m pip install -r tools/requirements.txt
```

If a script reports a missing module, that pip line is the fix — say so to the
user rather than failing silently.

## The `builder` harness — execute and verify a plan outside the model

`builder/` is the **build + verify harness**: it executes a `plan.toon` phase and
mechanically verifies it against the live server, **entirely outside the LLM
context**. Instead of the `worker` emitting hundreds of in-context MCP calls and
the `inspector` issuing dozens of scan calls, the harness POSTs everything
directly and returns one compact digest. It is the token-efficient path for
static, contract-checked work.

It is **stdlib-only** — no numpy/Pillow needed (unlike voxel/terrain) — and reads
the server URL/auth from `~/.claude.json` like `voxel/mcp_place.py`.

```sh
P=${CLAUDE_PLUGIN_ROOT}/tools/builder/harness.py
python $P mode                          # dedicated vs single-player (gameTime test)
python $P selftest                      # write-readiness (forceload→set→read→restore)
python $P run    <plan.toon> <phase>    # execute a phase (force-load-bracketed, banded)
python $P verify <plan.toon> <phase>    # run acceptance + quality_contract checks
python $P build  <plan.toon> <phase>    # run, then verify  (the common case)
```

Exit `0` = everything passed; `1` = any execution failure, force-load miss, or
failed check. Think of it as a test harness: `plan.toon` `steps` are the
code, `acceptance` + `quality_contract` are the assertions, `verify` is the test
runner. The model keeps design, freshness judgement, failure diagnosis, and the
perceptual "does it look right" call (renders + user checkpoints). Full detail:
`${CLAUDE_PLUGIN_ROOT}/reference/build-harness.md`.

### Modules

| Module | What it gives you |
| ------ | ----------------- |
| `builder.toon` | Minimal TOON reader — parses `plan.toon` and the server's TOON tool responses. |
| `builder.mcpclient` | Generic MCP HTTP client (handshake, `call_toon`), config from `~/.claude.json`. |
| `builder.harness` | Plan model, runner (op→tool, force-load bracketing/banding), verifier (contract checks), CLI. |

## The `voxel` toolkit — give yourself eyes before you place blocks

The agent cannot see the world. For any representational or parametric build (a
vehicle, a creature, a statue, a logo) that blindness is fatal: no amount of
front-end detailing fixes a body whose **silhouette** is simply wrong, and
nothing in-world will tell you it's wrong. So you build a model you *can* see
first. A renderer is cheaper than one wrong in-world rebuild.

The loop (seconds per iteration, all offline):

1. **Author** the form as a parametric `VoxelModel` (numpy grid + primitives).
2. **Render** it to PNGs from three orthogonal views and **Read them**.
3. **Compare** to the reference images; adjust one parameter at a time.
4. **Re-render.** Repeat until the renders genuinely match the references.
5. **Only then** decompose to fills and place them in the world.
6. **Verify**: scan the placed blocks back into a grid and render *those*
   ("scan-render"); compare to the references. A visual pass beats spot-checking
   a few `block_get_state` coordinates.

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "tools"))
from voxel import Palette, VoxelModel, render_views, write_fills_json

pal = Palette.building()                 # 16 concretes, stone, wood, glass, copper…
BODY = pal.code("cyan_concrete")
GLASS = pal.code("light_blue_stained_glass")

m = VoxelModel(nx=184, ny=70, nz=78, palette=pal)   # x=length, y=height, z=width
m.ellipsoid(center=(m.fx(0.5), m.fy(0.4), m.fz(0.5)), radii=(80, 22, 34), code=BODY)
m.box((m.fx(0.2), m.fy(0.45), m.fz(0.15)), (m.fx(0.8), m.fy(0.7), m.fz(0.85)), GLASS)

render_views(m, "/path/scratch/r1s")    # → r1s_iso.png, r1s_side.png, r1s_front.png
# …Read those, iterate vs references, then:
summary = write_fills_json(m, "/path/scratch/r1s_fills.json", origin=(206, 64, 70))
```

### Modules

| Module | What it gives you |
| ------ | ----------------- |
| `voxel.palette` | `Palette` — voxel code ↔ block id ↔ approximate RGB. `Palette.building()` is a broad starter set; `add()` more as needed. |
| `voxel.model` | `VoxelModel` — numpy grid + primitives: `box`, `ellipsoid` (solid/shell), `cylinder` (taper → cone), `line3d` (thickenable), `mirror_x`, anchors `fx/fy/fz` (fraction → index). |
| `voxel.render` | `render_views` (iso + side + front), `render_iso`, `render_ortho` (side/front/top). Surface voxels only; per-block colour. |
| `voxel.decompose` | `write_fills_json` / `to_fills` — greedy maximal-box cover, split to ≤ cap, → world-space fills. |

### Placing the result

`write_fills_json` emits a list ready for the **`block_fill_batch`** MCP tool —
the whole model placed in one call instead of hundreds:

```json
[{"from": [206,64,70], "to": [212,66,78], "block": "minecraft:cyan_concrete"}, …]
```

Each box is pre-split to ≤ 32,000 (the `cap`), so the build is safe even on a
server that has not yet adopted server-side auto-tiling. If `block_fill_batch`
is unavailable, the same list drives a sequence of `block_fill_region` calls.

**Place it with `voxel/mcp_place.py`** rather than hand-transcribing a long
fills list into a tool call (the #1 friction on a big build):

```sh
python tools/voxel/mcp_place.py place /path/scratch/r1s_fills.json replace
```

It reads the server URL/auth from `~/.claude.json`, does the MCP handshake, and
POSTs the fills as `block_fill_batch` calls — paging automatically past the
**8192-entry** cap. Stdlib only. The **`terrain` toolkit below shares this exact
placement path.**

### Authoring guidance

- Define **anchors** as fractions of the extent (rocker / beltline / roof;
  bumper / hood / windshield) and tune against the render — not absolute
  numbers you have to chase.
- Build **mass from primitives** along a spine: ellipsoid bulges, tapered
  cylinders for limbs, `line3d` spines, `mirror_x` for symmetric subjects.
- A downloaded mesh is **not authoritative** for a *named* subject — render its
  silhouette and check it against references *before* building on it. A free
  R1S mesh that voxelized into a generic sleek crossover cost days. If you must
  import a mesh, voxelize it (e.g. with `trimesh`, optional) into a grid and
  render-check it like any other model first.

See `examples/example_bean.py` for a complete worked model (and the toolkit's
smoke test): `python tools/examples/example_bean.py`.

## The `terrain` toolkit — give yourself eyes before you shape land

The 2.5-D counterpart of `voxel`, for **natural terrain** — mountains, islands,
valleys, coastlines. The same blindness applies: a stack of rectangular fills
produces a flat-topped ziggurat and nothing in-world tells you until the user
sees it (the Cape Aurelia rebuild). So author a heightfield you can *render and
check offline first*, then materialise it to blocks. Stdlib + numpy + Pillow
only — no extra deps.

The loop (seconds per iteration, all offline):

1. **Author** a `HeightField` — multi-octave noise, radial falloff, blob
   lakes/coves, carved rivers, blended build pads.
2. **Erode** — hydraulic (droplet) + thermal erosion, the realism multiplier
   that turns *lumpy noise* into *eroded terrain* with real drainage.
3. **Render** three verify views and **Read them**: `hillshade` (terraces and
   ziggurats jump out as flat bands; erosion reads as branching valleys),
   `relief` (hypsometric colour map — massing, coastline, lakes), and `profile`
   (cross-sections — proof slopes are compound, not flat-topped or pure 45°).
4. **Tune** one parameter, re-render.
5. **Materialise** to fills and place via `voxel/mcp_place.py` (shared path).

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "tools"))
from terrain import HeightField, TerrainLayers, render_views, write_terrain_fills

hf = (HeightField(160, 128, sea_level=62)
      .add_fbm(46, octaves=5, base_freq=0.02, warp=20, seed=7)   # rolling base
      .add_fbm(14, octaves=3, base_freq=0.05, ridge=True, seed=11)  # ridgelines
      .radial_falloff(max_radius=70, inner=0.12, sz=1.18)        # irregular island
      .carve_lake(center=(58, 84), radii=(20, 14), depth=7, seed=3)
      .erode_hydraulic(droplets=12000, seed=1))

render_views(hf, "/path/scratch/island")          # Read the 3 PNGs, tune, repeat
layers = TerrainLayers(                            # bakes in the non-negotiables
    surface={"minecraft:grass_block": 0.74, "minecraft:coarse_dirt": 0.16,
             "minecraft:stone": 0.06, "minecraft:moss_block": 0.04},
    subsurface="minecraft:dirt", subsurface_depth=3,   # double-layer substrate
    cliff="minecraft:stone", cliff_slope_deg=52,       # rock on steep faces
    beach={"minecraft:sand": 0.8, "minecraft:gravel": 0.2})
write_terrain_fills(hf, "/path/scratch/island_fills.json", layers, origin=(0, 0))
```

### Modules

| Module | What it gives you |
| ------ | ----------------- |
| `terrain.noise` | `ValueNoise2D`, `fbm` (octaves, ridge, domain-warp) — coherent value noise, pure numpy. |
| `terrain.field` | `HeightField` — `add_fbm`, `radial_falloff`, `carve_lake`, `carve_river`, `build_pad`, `smooth`, `erode_*`, `slope_deg`, `summary`, `from_image`. |
| `terrain.erosion` | `hydraulic` (droplet) + `thermal` (talus) erosion. |
| `terrain.render` | `render_views` (hillshade + relief + profile) — the terrain verify eyes. |
| `terrain.materialize` | `TerrainLayers` + `write_terrain_fills` — heightfield → world fills (double-layer, mixed surface, cliffs, beaches, water columns), reusing `voxel`'s decompose. |

`HeightField.from_image()` loads a greyscale heightmap PNG (a DEM exported from
QGIS / Tangram Heightmapper / World Machine) — the zero-dep "import real
elevation" path. Native GeoTIFF/DEM import (via `rasterio`/`richdem`) is a
future optional add-on.

See `examples/example_terrain.py` for a worked island (and the smoke test):
`python tools/examples/example_terrain.py`.
