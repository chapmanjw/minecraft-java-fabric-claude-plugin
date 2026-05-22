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
