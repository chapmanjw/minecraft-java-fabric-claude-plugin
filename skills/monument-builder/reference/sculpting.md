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

## Voxelization and the render-verify loop

Author the form as a **parametric voxel model you can render and check before
placing it** — see `reference/render-verify.md` for the full loop and the
bundled `voxel` toolkit (`${CLAUDE_PLUGIN_ROOT}/tools/voxel`). The toolkit gives
you the primitives above (ellipsoid, cylinder/cone, `line3d`, `box`, `mirror_x`,
fractional anchors) on a numpy grid, renders three orthogonal views to PNG, and
decomposes the verified model into world fills for one `block_fill_batch`. This
is the primary path for spheres, creatures, vehicles, characters, abstract
curves — anything computed.

For a form best derived from an **existing 3D model** (`.obj`, `.glb`), voxelize
it into a grid (e.g. with the optional `trimesh` dependency, or an external tool
like MagicaVoxel) — but a downloaded mesh is **not authoritative** for a *named*
subject: render its silhouette against the references and confirm it *before*
building anything on it. Hand-authoring a parametric model usually wins for a
specific named subject because you control the silhouette directly. Either way,
the rule is the same: **render-verify before you place.**

## Java-exclusive: display entities for detail and angles voxels can't reach

Voxel blocks are locked to the 1-block grid and to axis-aligned placement.
Where a form needs finer detail or an off-grid angle, **display entities**
(`block_display`, see `reference/display-entities.md`) render a block at
arbitrary scale, rotation, and translation — with no collision, as a late
decoration phase over the blockwork. Reach for them where blockwork stalls:

- **Below grid resolution** — a `block_display` scaled to `[0.25f,0.25f,0.25f]`
  is a quarter-block cube. Tile a few to carve detail finer than any voxel:
  rivets and inlay, gem facets, small facial features (eye, nostril, lip),
  fingertips, claw tips — the things that always look chunky at 1-block size.
- **Off-grid angles** — a placed block can only sit axis-aligned and stair-
  stepped. A `block_display` rotated by a quaternion sits at a true 45° (or any
  angle) — diagonal banding, tilted crystal/scale facets, slanted fins, angled
  spar lines on a wing, a chamfer that reads smoother than a staircase. Quaternion
  rotation is fiddly; verify one before stamping a row (see the reference).
- **Giant seamless forms** — a single block scaled `[8f,8f,8f]`+ is one smooth
  massive cube/face with no block seams — a monolith, a giant gem, an abstract
  core.
- **Glowing accents** — `Glowing:1b` + `glow_color_override` gives tinted edges
  (energy lines, runes, eye-glow) that read at night and through fog.

The main mass stays **real blocks** — displays have no collision and are accent
and finishing detail only, never load-bearing or walkable.

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
