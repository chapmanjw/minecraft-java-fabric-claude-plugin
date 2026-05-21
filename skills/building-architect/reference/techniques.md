# Advanced building techniques

What makes a build read as real architecture rather than a block box. Apply
these throughout — they are the difference between "a wall" and "a façade".

## Depth and contrast — the foundation

A flat wall is the loudest amateur tell. Build walls in **three depth layers**:
a recessed back layer, the main wall plane, and protruding elements (pillars,
buttresses, window frames).

- **Negative space.** Do not cover a whole wall in detail. Plain structural
  pieces — pillars, bare courses — should frame detailed areas. Detail
  everywhere reads as noise.
- **Texture mixing.** Never one block for one material. "White stone" = smooth
  quartz + quartz + chiseled quartz + diorite + calcite + bone block, mixed so
  no repeat is obvious. "Old stone" = cobblestone + andesite + diorite + mossy
  cobblestone + cracked stone brick + gravel patches. "Marble" = calcite +
  diorite + smooth quartz + bone block.

## Trim and courses

- Slab and stair **courses** at floor lines and the roofline tie a façade
  together.
- **Quoins** (contrasting blocks at corners), **stringcourses** (a band every
  few storeys), accent stripes.

## Arches

- **Round (Romanesque)** — stairs up each side, a slab or block keystone.
- **Pointed (Gothic)** — stairs from each side meeting at an apex.
- **Ogee** — stair-and-slab S-curve.
- **Horseshoe (Islamic)** — a stair stack that curves back inward at the base.
- **Lancet** — a tall narrow pointed arch.

## Domes

- **Octagonal stepped** — concentric stair rings narrowing each level; the
  most reliable vanilla dome.
- **Ribbed** — fence-post or wall ribs over the dome surface.
- **Onion** — a stepped stack that flares out then tapers to a finial.

## Roofs

Pitch with stairs (1:1 or 1:2). Forms: gable, hip, mansard, gambrel, **pagoda
tiers** (a stair flare with a slab soffit and dark-log eave beams per tier),
dormers and lucarnes for detail. Never a flat slab roof unless the style is
modern.

## Spires and towers

Tapering pyramidal stair stacks; an end rod or fence post as the needle
finial. Round towers as octagons-via-stairs at each level.

## Windows

Single pane; mullioned (iron bars over panes); leaded (an iron-bar grid);
Gothic pointed (a two-stair frame with a slab apex); rose windows (a
stained-glass mosaic in a circular stair frame). **Always put a light block
behind stained glass** — unlit stained glass reads as dull and dead.

## Fortification detail

Crenelations (a stair-slab-stair merlon pattern), machicolations (a slab
overhang), arrow loops (1×2 gaps), battered curtain walls (1 block of inset
per N of height).

## Copper as art direction

Copper oxidizes through four stages (normal → exposed → weathered →
oxidized); **waxing locks a stage**. Decide the look deliberately: wax on
placement for a fixed appearance, or place unwaxed batches aged to different
stages for an intentional gradient (a green-streaked roof, an aged dome).

## Weathering for mood

For a "lived-in" or "ruined" build: cracked and mossy block variants, missing
sections, vines and moss, partial collapse, `sculk` for ancient decay. Apply
weathering after the clean geometry, never instead of it.

## Java Edition notes

Compose with `block_fill_region`, `block_set_state`, `block_clone_region`, and
`structure_save_from_world` / `structure_load_to_world` — there is no WorldEdit
mod in this setup. `/data` commands are available via `command_execute` for NBT
manipulation on block entities and entities. Lean on structure modules
(`modules.md`) for anything repeated. Keep each `block_fill_region` within the
32,768-block vanilla volume limit; split larger fills across calls.
