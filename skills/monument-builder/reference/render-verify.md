# Render-verify: give yourself eyes before you place blocks

The single most valuable habit for any representational or parametric build.
You **cannot see the world** — `block_get_state` confirms a block id at a
coordinate, nothing more. It cannot tell you that a vehicle's body is the wrong
shape, that a silhouette doesn't read, that proportions are off. A wrong **base
silhouette** cannot be rescued by any amount of front-end detailing, and built
blind you will not notice until the user does. So build a model you *can* see
first. A renderer is cheaper than one wrong in-world rebuild.

This applies to: vehicles, creatures, statues, characters, logos, any
voxelized form, any large figurative mass. It does **not** apply to a flat
pixel-art grid you already laid out on paper — that you can reason about
directly.

## The loop (offline, seconds per iteration)

1. **Author** the form as a parametric `VoxelModel` (numpy grid + primitives).
2. **Render** three orthogonal views to PNG and **Read them**.
3. **Compare** to the reference images. Adjust **one parameter at a time**.
4. **Re-render.** Repeat until the renders genuinely match the references.
5. **Decompose** to a fills list and **place it** (one batch call).
6. **Verify** with a scan-render (below) and compare to the references again.

Different errors surface in different views — always render multiple, never
just one:

- **side** (length × height) — the make-or-break **silhouette**. Stance,
  proportion, roofline, the overall read. Most identity errors show here.
- **front** (width × height) — the face: light bars, headlights, symmetry,
  shoulders.
- **iso** (3/4) — how the masses sit together in three dimensions.

## The toolkit

Bundled at `${CLAUDE_PLUGIN_ROOT}/tools/voxel` (numpy + Pillow; if a run
reports a missing module, tell the user to
`python -m pip install -r tools/requirements.txt`). Read `tools/README.md` for
the full API. The shape of an authoring script:

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "tools"))
from voxel import Palette, VoxelModel, render_views, write_fills_json

pal = Palette.building()                  # concretes, stone, wood, glass, copper…
BODY = pal.code("cyan_concrete")
GLASS = pal.code("light_blue_stained_glass")

m = VoxelModel(nx=184, ny=70, nz=78, palette=pal)   # x=length, y=height, z=width
# anchors are fractions of the extent — define the form by ratios, tune vs render
roof, belt = m.fy(0.78), m.fy(0.45)
m.ellipsoid(center=(m.fx(0.5), belt, m.fz(0.5)), radii=(80, 22, 34), code=BODY)
m.box((m.fx(0.2), belt, m.fz(0.15)), (m.fx(0.8), roof, m.fz(0.85)), GLASS)

render_views(m, "/abs/scratch/r1s")       # r1s_iso.png / r1s_side.png / r1s_front.png
```

Then `Read` the three PNGs, judge them against the references, edit the model,
and re-run. Author the shape from **anchors and primitives** (`ellipsoid`,
`cylinder`/cone, `line3d` spine, `mirror_x` for symmetry), not absolute
coordinates — so you can tune a ratio and see the effect, not chase numbers.

## Placing the verified model

Once the renders match, decompose and place:

```python
summary = write_fills_json(m, "/abs/scratch/r1s_fills.json", origin=(206, 64, 70))
```

`write_fills_json` greedily covers the model with maximal boxes, splits each to
≤ 32,000 blocks, and writes a list of
`{"from":[x,y,z], "to":[x,y,z], "block":"…"}` in **world** coordinates. Place
the whole list in one **`block_fill_batch`** call (the batch tool collapses
hundreds of fills into a single request and sidesteps the per-call rate limit).
If `block_fill_batch` isn't available on the connected server, feed the same
list to a sequence of `block_fill_region` calls — the boxes are already capped,
so they place safely either way. The script + the model `.npy` are the
**reusable artifact** for a large parametric form (it can't be one structure
template — templates cap at ~64×384×64); record them in the registry.

## Verify the built result — scan-render

After placing, confirm fidelity *visually*, not by spot-checking coordinates:

- **Native (preferred):** call **`block_render_region`** on the placed bounding
  box — the mod renders the actual blocks (real map colours) to a PNG you Read.
  One call, no raw block data in your context.
- **Fallback** (if that tool is absent): scan the region back with **paged**
  `block_scan_region` (never a raw full-volume dump — it can blow the context
  limit), rebuild a `VoxelModel` from the result, and `render_views` it. Use
  `block_scan_summary` for a quick solid-count / material check.

Compare the scan-render to the references. A matching solid-voxel count between
the model and the scan is strong block-for-block evidence; a matching *picture*
is the real proof the build reads as its subject.

## Imported meshes are not authoritative

A free downloaded mesh (Printables, Thingiverse, Sketchfab) voxelizes into
*a* shape, not necessarily the **named** subject's shape — a generic crossover
is not an R1S. If you import a mesh (e.g. voxelized via the optional `trimesh`
dependency into a grid), **render its silhouette and check it against the
references before building anything on it.** Render-checking on day one is
cheap; detailing a wrong body for days is not. Hand-authoring a parametric
model usually wins for a specific named subject because you control the
silhouette directly.

## Scene scale

When the piece shares a scene with another subject (a figure beside a vehicle),
**pin the scale relationship before authoring** — fix the ratio (e.g. figure
height ≈ vehicle roof height) up front, so you don't discover a 4× mismatch
after both are built. See the planner's scale-pinning rule.
