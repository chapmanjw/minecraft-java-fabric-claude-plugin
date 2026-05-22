# Figurative builds: posing, labeling, and garments

Techniques for a **posed character** — clothing that wraps a leaning body, arms
raised in a wave, a draping cape, a hat that sticks out past the head. These
solve problems that bit a long figurative session (a base character + a themed
trio) repeatedly. Worked references: `build_perfect_gary.py` (base pipeline) and
`build_dracula_gary.py` / `build_scarecrow_gary.py` / `build_docbrown_gary.py`
(re-costumed variants).

Pairs with `mesh-import.md` (getting the body) and `render-verify.md` (the
render-before-place loop). Needs `scipy` from `requirements-mesh.txt` for the
labeling step.

## a. Label voxels BODY vs LIMB by nearest mesh vertex — the key technique

Putting clothing on a posed figure is the hardest recurring problem. Two naive
masks **both failed**:

- **Fixed center-band** (`|x − center| ≤ k`): goes off-center the instant the
  figure leans or poses, leaving one side of the torso bare ("looks naked").
- **Depth-threshold mask** (color only thick columns): leaves the thin curved
  torso *sides* unpainted — vertical seams; the clothing doesn't wrap around.

The robust fix: you already select limb vertices to pose them (b) — reuse that
selection to label **every voxel** by its nearest mesh vertex.

```python
import numpy as np
from scipy.spatial import cKDTree

arm_vert = rmask | lmask                 # bool over mesh vertices V2 (from posing, below)

# after voxelizing, map each filled voxel to a world point, find its nearest vertex
idx = np.argwhere(mat)                   # filled voxel indices, shape (N,3)
pts = vox.indices_to_points(idx.astype(float))
_, nn = cKDTree(V2).query(pts, k=1)      # nearest mesh vertex per voxel

arm_grid = np.zeros(mat.shape, bool)
arm_grid[idx[:, 0], idx[:, 1], idx[:, 2]] = arm_vert[nn]
body = mat & ~arm_grid                   # torso/head/legs
arm  = mat & arm_grid                    # limbs
```

Then color clothing on **`body`** voxels by height band — it wraps the full
torso at every depth with zero arm bleed — and keep **`arm`** voxels as
skin/sleeve. Bonus: `body` gives a correct **head centroid** for face placement
(`HCX = mean x of body voxels in the head height band`).

## b. Pose by rotating limb VERTICES about the joint, then re-voxelize

Pose in the mesh, not the grid. Select the limb's vertices, rotate them about
the joint pivot in the relevant plane, then voxelize the whole posed mesh. The
same selection feeds the (a) labels.

```python
def rot_xz(P, piv, deg):                 # rotate in the x-z plane about a pivot
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    dx, dz = P[:, 0] - piv[0], P[:, 2] - piv[2]
    P[:, 0] = piv[0] + dx * c - dz * s
    P[:, 2] = piv[2] + dx * s + dz * c
    return P

rmask = (V[:, 0] > ARM_X) & (V[:, 2] < SH_Z + 0.35)    # right-arm verts
lmask = (V[:, 0] < -ARM_X) & (V[:, 2] < SH_Z + 0.35)   # left-arm verts
V[rmask] = rot_xz(V[rmask].copy(), (ARM_X, 0, SH_Z), 118)   # +118° up = wave
V[lmask] = rot_xz(V[lmask].copy(), (-ARM_X, 0, SH_Z), 20)   # +20° down
```

Re-renderable and clean: change the angle, re-voxelize, re-render.

## c. Garments are arcs, not planes

A flat vertical slab reads as a billboard, not a cape ("it's just a flat
vertical thing"). Build a draping garment as a curved **arc shell** that wraps
the body's x-z cross-section per height:

- For each height row, take the body's x-z footprint and lay blocks along an arc
  that follows it; **inner radius = lining color, +1–2 radius = outer color.**
- **Flare toward the hem** (wider arc at lower rows) so it drapes.
- A tall flaring arc *behind the head* = a **collar**.

## d. Pad the grid for accessories, build relative to the body-derived center

Accessories extend past the figure, so the voxel grid must have room:

- cape → pad the back (`+z`); hat → pad the top (`+y`); wild hair → pad all
  sides. Allocate the `VoxelModel` larger than the body and place the body
  inside it.
- Compute the **head center from `body` voxels** (a) and build the accessory
  relative to it, so it stays put when the figure is posed.

## Re-costume one base for a themed series

`build_perfect_gary.py` (mesh → pose → label) is the **base**; each variant is
that base **plus a recolor-by-region step plus accessory geometry**. The
Halloween trio (Dracula, Scarecrow, Doc Brown) was one base + per-costume
recolor + arc capes/hats/hair — each new character cost ~1 script and a couple
of render iterations. Build the base once, branch per costume.
