# Importing a real or user-provided 3D model

When the subject **already exists as a 3D file** — the user hands you a `.3mf`
print, or there's a faithful `.obj`/`.stl` of the thing — voxelizing that mesh
beats hand-authoring an organic figure. In a long figurative session, a
hand-built character took ~6 in-world rebuilds and still wasn't its true shape;
voxelizing the user's print **nailed the silhouette on the first try.** Prefer a
provided model whenever one exists for the *named* subject.

This is the complement to `render-verify.md`: importing replaces the *authoring*
step, then you rejoin the same render → decompose → place → scan-render loop. It
does **not** replace the render check — see the guardrail at the bottom.

## When to use this vs. hand-authoring

- **Import a mesh** when a faithful model of the *specific* subject exists (the
  user's own print file, an accurate scan). The mesh carries proportions you'd
  otherwise guess.
- **Hand-author** (`render-verify.md`) for a *named* subject when the only
  meshes available are generic look-alikes — a random "crossover SUV" mesh is
  not an R1S. A wrong base silhouette can't be detailed away.

## Dependencies

The mesh path needs extras beyond the core toolkit (`numpy` + `pillow`):
`trimesh`, `scipy`, `networkx`, `lxml`. They live in a **separate** file so the
core stays light:

```sh
python -m pip install -r ${CLAUDE_PLUGIN_ROOT}/tools/requirements-mesh.txt
```

If a run reports `ModuleNotFoundError: trimesh` (or `scipy`/`networkx`/`lxml`),
tell the user to run that command — don't fail opaquely.

## Canonical pipeline

Worked reference: `build_perfect_gary.py` from the figurative session (mesh →
pose → label → color → render → `.npy`).

```python
import zipfile, xml.etree.ElementTree as ET
import numpy as np, trimesh
import os, sys
sys.path.insert(0, os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "tools"))
from voxel import Palette, VoxelModel, render_views, write_fills_json

TARGET_H = 78                                    # desired height in blocks

# 1) Parse the mesh to a clean Trimesh.  Do NOT trust trimesh scene assembly
#    for .3mf (see gotchas) — parse the object model XML directly.
z = zipfile.ZipFile("model.3mf")
strip = lambda t: t.split('}')[-1]               # drop XML namespace
root = ET.fromstring(z.read('3D/Objects/object_1.model'))
obj  = [o for o in root.iter() if strip(o.tag) == 'object' and o.get('id') == '1'][0]
mesh_el = [c for c in obj if strip(c.tag) == 'mesh'][0]
V = np.array([[float(v.get('x')), float(v.get('y')), float(v.get('z'))]
              for v in [c for c in mesh_el if strip(c.tag) == 'vertices'][0]])
F = np.array([[int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))]
              for t in [c for c in mesh_el if strip(c.tag) == 'triangles'][0]])

# 2) z-up (print/CAD convention) -> y-up (the voxel toolkit's height axis)
y_extent = V[:, 2].max() - V[:, 2].min()         # measure BEFORE the swap
V2 = V[:, [0, 2, 1]]

# 3) Voxelize to the target height.  Pitch by the mesh's real extent so
#    "78 blocks tall" is exact, not approximate.
mesh = trimesh.Trimesh(vertices=V2, faces=F, process=False)
vox  = mesh.voxelized(pitch=y_extent / TARGET_H).fill()
mat  = np.asarray(vox.matrix).astype(bool)       # (x=width, y=height, z=depth)

# 4) Flip z so FRONT = max z, matching the toolkit's `side`/`front` renders.
mat = mat[:, :, ::-1]

# 5) Wrap in a VoxelModel for rendering + decomposition.
W, H, D = mat.shape
pal = Palette()
SKIN = pal.add("minecraft:yellow_terracotta", (190, 138, 40))
m = VoxelModel(W, H, D, pal)
m.g[mat] = SKIN                                  # color by region/height next
render_views(m, "/abs/scratch/import_check")     # READ these before detailing
```

Then color by region/height band (see `figures.md` for body/limb labeling) and
place via `mcp_place.py` exactly as in `render-verify.md`.

## .3mf gotchas (all hit in the session — Bambu/Orca slicer files)

- **Don't use `trimesh.load(force='scene')` on a `.3mf`.** It mis-assembled the
  components and produced degenerate scales (19 m / 14 mm). **Parse
  `3D/Objects/object_*.model` XML directly** (vertices + triangles) and build a
  clean `Trimesh(V, F, process=False)`, as above.
- **Pick the largest object.** Secondary objects are often decals — in the
  session, object 2 was a flat ~400-unit logo plane, not part of the figure.
  Inspect each object's extent and take the big one.
- **Don't try to decode `paint_color`.** Bambu/Orca per-face paint is a
  recursive sub-triangle bitstream — not reliably decodable and not worth it.
  For the palette, read `filament_colour` from
  `Metadata/project_settings.config` and **color by region/height** instead.
- **Pitch by the real extent.** `pitch = y_extent / TARGET_H` makes the height
  exact. The slicer's build transform (uniform scale + translate, in
  `3D/3dmodel.model`'s `<build><item transform=…>`) is unnecessary if you pitch
  off the raw extent.

## Guardrail: imported meshes are not authoritative

A downloaded mesh voxelizes into *a* shape, not necessarily the **named**
subject's shape. **Render the voxelized silhouette and check it against the
references before you build or detail anything on it** (this is the same
guardrail as in `render-verify.md`). Render-checking on day one is cheap;
detailing a wrong body for days is not.
