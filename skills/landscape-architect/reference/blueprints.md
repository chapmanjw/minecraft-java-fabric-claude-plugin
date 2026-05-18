# Garden blueprint rendering and validation

A garden is a plan-driven design — render it top-down, the way it is designed
and the way it is best read. Propose blueprints, iterate, then resolve a plan.

## Rendering modes

Produce these in `.minecraft-builder/<project>/` and show the user before
resolving a plan:

- **Plan view** (`garden.txt`) — the top-down ASCII layout: axes, paths,
  parterres, beds, water, structures, with a legend. The primary drawing.
- **Planting plan** (`planting.md`) — per zone or bed: the blocks for hedging,
  bed fill, trees, ground; the leaf-persistence note.
- **Palette sheet** (`palette.md`) — the materials and where each goes.
- **Section** — for a terraced or tiered garden, a side view showing the
  level changes and water staircases.
- **Tile plan** (`tiles.md`) — for a garden over 64 blocks, the split into
  structures with offsets, every seam on a symmetry axis or path line.

### Plan view — example

```
French parterre   (# hedge  . gravel  ~ water  T topiary  * fountain  = lawn)

   # # # # # # # # # # # # #
   # . . T . . | . . T . . #
   # . #broderie# . #broderie# . #
   # . . . . . | . . . . . #
   = = = = = = * = = = = = =     <- central axis, fountain on it
   # . . . . . | . . . . . #
   # . #broderie# . #broderie# . #
   # . . T . . | . . T . . #
   # # # # # # # # # # # # #
```

## Iteration

1. Render the plan view, planting plan, and palette sheet.
2. Show the user; take feedback on layout, axes, features, palette.
3. Revise and re-render.
4. Loop until the user explicitly approves.
5. Only then resolve to `plan.toon`.

## Validation checklist

Check the design — and have the `inspector` and `philosopher` re-check the
build — against these failure modes:

- **Leaves decay** — a hedge or topiary built from non-persistent leaves with
  no log core. The single most common garden failure. Every leaf is persistent
  or cored.
- **Broken symmetry** — a symmetric tradition where the two sides do not
  mirror, or a tile seam that bisects a parterre instead of falling on the
  axis.
- **An axis ending on nothing** — a long vista that terminates on blank
  ground; place a feature or shorten the axis.
- **A maze that does not work** — unintended loops, or no path to the goal;
  hand-design and verify the topology.
- **Flowing water where it should be still** — a reflecting pool or canal with
  flowing tiles; use source blocks throughout.
- **Freehand "organic" curves** — wobble with no geometric or traditional
  justification; that is `terraforming`, not this skill.
- **A hard edge against the wild** — the geometric garden ending in a straight
  line against naturalistic terrain with no transition apron.
- **Scale or cap violations** — a fill over 32,768, a structure over
  64×384×64, an element above Y 320.
- **An accidental roofed building** — a gazebo or temple built here instead of
  handed to `building-architect`.

A decayed hedge or a broken axis is a correction to make, not a cosmetic note
— the geometry is the whole point of the garden.
