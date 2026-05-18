# Organic-curve construction and voxelization

Building rounded, organic, three-dimensional forms — bodies, limbs, creatures,
smooth abstract shapes — out of cubic blocks.

## Voxel primitives

Compose organic forms from computed primitives:

- **Sphere / ellipsoid** — a block at `(x,y,z)` is solid when
  `x²/a² + y²/b² + z²/c² ≤ 1` (a sphere when `a=b=c=r`). The base primitive
  for heads, muscle masses, the Bean.
- **Cylinder** — a circle (`x²+z²≤r²`) extruded along an axis; limbs, columns,
  necks.
- **Tapered cylinder / cone** — radius shrinking along the axis; tails, horns,
  spikes.
- **3D line** — a Bresenham-style stepped line between two points; the spine
  of a limb or a coil to build mass around.

Resolve each primitive to a set of `fill`/`set` steps in `plan.toon`.

## Curves and articulation

- **Stair-stepped curves** — approximate a smooth curve with a staircase of
  blocks; use stairs and slabs on the steps to soften the silhouette.
- **Stair-rounded edges** — face a hard edge with stairs to read as a chamfer
  or a fillet; this is the single biggest "less blocky" technique.
- **Slab cascades** — overlapping slabs stepping down read as drapery, cloth,
  flowing hair, or scales.
- **Articulated joints** — build a limb as cylinders meeting at a joint;
  rotate each segment's axis and bridge the joint with a voxel sphere so it
  reads as a shoulder, elbow, or knee.

## Anatomy of a creature

- Lay the **spine first** as a 3D line or spline — for a dragon, an S-curve;
  for a coiled serpent, a loose helix. Everything hangs off it.
- Add **mass** as voxel-sphere bulges along the spine — ribcage, haunches,
  skull — sized by the creature's proportions.
- **Limbs** as tapered cylinders; **wings** as stair-stepped membranes between
  spar lines; **tail** as a long tapered cone.
- Keep **proportion** true to the reference — a too-short neck or too-small
  head breaks the read more than any blockiness.
- Detail last: scales (slab cascade), claws and teeth (small tapered cones),
  eyes (a contrasting palette inset).

## Voxelization from a 3D model

For a form that is best derived from an actual 3D model rather than computed:

- The conversion of a real 3D model (`.obj`, `.glb`) to a voxel grid is an
  **external step** — a voxelizer or a tool like MagicaVoxel produces the
  grid, which is then imported as structure files. This skill does not run
  external tools; if the user has a model, treat the voxel grid as a given
  input and plan its placement and tiling.
- For everything else — spheres, creatures, abstract curves — compute the
  voxels here, with the primitives above.

## Solid vs. shell

- A small monument can be **solid**.
- A large one should be a **hollow shell** — fill the outer surface, leave the
  interior air. This is also required when the solid volume is impractically
  large. Keep the shell thick enough (2+ blocks) that it reads as massive and
  no light leaks through.

## Tiling

Split a form over 64 blocks in any axis into structure tiles along **natural
anatomy seams** — a waist, a neck, a wing root, a limb joint. A seam at a joint
hides; a seam through a smooth surface shows.
