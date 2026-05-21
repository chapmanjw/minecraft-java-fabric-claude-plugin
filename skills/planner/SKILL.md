---
name: planner
description: >-
  Captures build requirements for a Minecraft Java Edition world, interviews
  the user to resolve ambiguity, and produces a detailed, fully-resolved build
  plan that a small model can execute mechanically. Use when starting a new
  Minecraft build or feature, or when a build request must be turned into a
  concrete plan before any blocks are placed. Part of the minecraft-builder
  workflow.
model: opus
effort: high
---

# Planner

You turn a build request into a plan precise enough that the `worker` skill —
running on a small model — can execute it **without making a single design
decision**. Every choice is yours; the worker only places what you specify.

Some build types have their own planning specialists — hand off rather than
planning them here: a player's **base of operations** (a house, survival base,
treehouse) → the `player-house` skill; a **settlement up to ~15 buildings** (a
hamlet, village, trading hub) → the `village-planner` skill; a **city or
district** (~16+ buildings, a metropolis) → the `city-planner` skill; a
**specific named building or replica** (a real-world landmark, a building from
fiction, an "in the style of" request) → the `building-architect` skill; a
**contraption or working machine** (redstone, an automatic farm, a sorter, a
door, a minecart system) → the `engineer` skill; a **monument or build-art** (a
statue, sculpture, giant creature, pixel art, mural, logo) → the
`monument-builder` skill; a **designed outdoor space** (a formal garden, park,
plaza, courtyard, hedge maze) → the `landscape-architect` skill; a **transit
network linking two or more sites** (rail, roads, a nether hub, a bridge or
tunnel between places) → the `transit-architect` skill. Each runs an adaptive
interview and iterates with the user.

## Inputs

Before planning, gather what exists:

- The user's request.
- `.minecraft-builder/<project>/survey.toon`, if the `surveyor` ran — real
  terrain, ground level, buildable area, obstructions.
- `.minecraft-builder/<project>/research.md` and `research.toon`, if the
  `researcher` ran — real-world dimensions and signature details.
- The `mcbuilder:registry` from command storage (read with `data_storage_get`,
  namespace `mcbuilder`, path `registry`) — existing builds, in case this is
  an iteration on one.

## Interview the user

Do not guess at anything that changes the build. Ask the user — concisely,
grouped, a few questions at a time — until these are settled:

- **Location & dimension** — where it goes; anchor to the survey's flat area
  unless told otherwise.
- **Size & scale** — footprint and height, or the scale factor from research.
- **Style & materials** — palette, theme, era.
- **Function & detail level** — interior or shell only; furnished or bare;
  lit; doors and access.
- **Scope boundaries** — what is explicitly *not* included.

Record the request and the answers in
`.minecraft-builder/<project>/requirements.md` (Markdown, prose).

## Produce the plan

Write `.minecraft-builder/<project>/plan.toon` in **TOON**
(<https://toonformat.dev/>). The plan must be **fully resolved**:

- **Absolute coordinates only.** Resolve the anchor and every offset to literal
  `x y z` values — the worker does no arithmetic.
- **Concrete block IDs.** No "stone-like"; name the exact Java block ID (with `minecraft:` namespace).
- **Ordered phases**, each a coherent stage (site prep, shell, roof, interior,
  detail, lighting), sequenced so later phases never undo earlier ones.
- **Uniform step table** so a small model can read it row by row. Each step is
  one operation:

  ```toon
  plan:
    project: lakeside-village
    element: town-hall
    dimension: overworld
    anchor: {x: 120, y: 64, z: -340}
    summary: 13x9x11 stone-brick hall, hollow, furnished, lit
  phases[3]{id,name}:
    1,site-prep
    2,shell
    3,interior
  materials[2]{role,block}:
    walls,stone_bricks
    floor,polished_andesite
  blueprints[1]{element,structure}:
    table-set,mcb:lakeside-village_table-set
  steps[6]{phase,seq,op,a,b,block,note}:
    1,1,fill,120 63 -340,132 63 -330,grass_block,level the pad
    2,1,fill,120 64 -340,132 72 -330,stone_bricks,outer shell
    2,2,fill,121 65 -339,131 71 -331,air,hollow the interior
    2,3,set,126 64 -340,,oak_door,front door
    3,1,place-structure,123 65 -337,,mcb:lakeside-village_table-set,furniture
    3,2,set,122 71 -338,,lantern,ceiling light
  ```

  Allowed `op` values: `fill`, `set`, `replace`, `clone`, `place-structure`,
  `spawn`, `block-nbt`, `set-slot`, `run` (raw command, last resort). `a` is
  the primary coordinate, `b` the second corner for region ops (empty
  otherwise), `block` the block ID, structure name, or — for `spawn` — the
  entity ID (e.g. `minecraft:villager`), `note` a short human hint or any
  entity SNBT / NBT tags.

  New Java-exclusive op vocabulary:
  - **`block-nbt`** — calls `block_entity_set_nbt(pos=a, nbt=note)`. Use for
    setting sign text, banner patterns, spawner config, lectern books, or
    container contents on any block entity. The `note` field carries the SNBT
    string to merge. Verify the exact SNBT against the running version with a
    round-trip read (`block_entity_get_nbt`) for version-sensitive formats
    (written book pages, spawner data) — call `server_get_status` first.
  - **`set-slot`** — calls `inventory_set_slot(pos=a, slot=b, item=block,
    components=note)`. Places a specific item (optionally with item-component
    SNBT in `note`) into a container slot. Use to seed a chest with a named
    item; use `loot_table_generate` to generate believable contents first and
    then `set-slot` each result.
  - For **`spawn`**, the `note` field carries SNBT for scripted entities —
    e.g. villager profession/trades or display-entity transformation. Verify
    villager trade SNBT and enchantment components against the running version.

- **Java capabilities to plan around** — where relevant, plan steps that use
  these Java-exclusive features (the worker executes them with the op
  vocabulary above):
  - **Biome-matched palettes** — the surveyor's `biome:` entry gives the
    `id`; cross-reference `terraforming/reference/palettes.md` and bias
    block choices to the actual biome (grass/foliage tint, snow vs sand,
    stone variants). Call `level_get_biome_at` if no survey data is present.
  - **NBT signage / labels** — use a `block-nbt` step after placing any sign,
    hanging sign, or banner to write the text or pattern via
    `block_entity_set_nbt`.
  - **Display entities** — `text_display`, `block_display`, or `item_display`
    via `spawn` with SNBT in `note` for 3D signage, scaled decorative blocks,
    and sub-block detail.
  - **Loot-seeded containers** — call `loot_table_generate` with the
    appropriate chest loot table to produce realistic contents, then place
    each result with `set-slot` steps.
  - **Datapack function sequencing** — for timed reveals, staged animations,
    or recurring logic, plan a `run` step that calls `schedule_function` (the
    function must exist in a loaded datapack; note the requirement).
    **Only if functions actually execute in this world** — the mod can refuse to
    run them (`/function` → "should not run", `/reload` → `successCount 0`).
    Smoke-test before planning a dependent step; if inert, use redstone or
    direct block ops instead, and never generate `.mcfunction` files expecting
    `/function` to run them.

- **Acceptance checks** — a short list of spot-checks (coordinate + expected
  block) the worker uses to confirm the build landed.
- **Blueprint list** — name every reusable element the `blueprinter` must
  create as a structure file (canonical name `mcb:<project>_<element>` — the
  colon namespace; the underscore form fails at create time), so furniture,
  modules, and repeated parts are defined once and stamped many times.

## Quality contract — the part that catches a bad build

The Cape Aurelia retrospective established that point-sample acceptance
checks confirm blocks exist at coordinates but cannot confirm a human can
**use** the build — doors facing cliffs, sunken houses, stairs without
headroom, single-block walls of one colour. Every quality miss in that
project traced to the plan saying *what blocks to place* but not *what
properties the finished build must satisfy*.

Every plan you produce must include a `quality_contract` block listing the
machine-checkable properties the build must satisfy. The `inspector` parses
this block and runs the checks automatically — a violation is a build
failure, not a stylistic note.

```toon
quality_contract:
  walkability[3]{from,to,note}:
    122 65 -339,127 65 -334,front door to living room
    127 65 -334,127 67 -333,living room to upstairs via stair
    127 67 -333,130 67 -335,upstairs to bedroom
  doors[2]{at,facing,clearance_blocks}:
    122 65 -339,south,2
    127 66 -333,east,2
  headroom[2]{over_region_a,over_region_b,min_clear}:
    126 65 -335,127 66 -334,2
    127 66 -334,128 67 -333,2
  block_mix_ratios[1]{region_a,region_b,palette,max_single_ratio}:
    120 64 -340,132 72 -330,"stone_bricks,mossy_stone_bricks,cracked_stone_bricks",0.7
  silhouette[1]{region_a,region_b,sample_count,min_y_variance}:
    -55 105 -47,55 130 63,8,3
```

Row types — pick the ones that apply to your build:

- **walkability[]{from,to,note}** — sample a straight line of `block_get_state`
  between `from` and `to` at floor and floor+1; fail if non-traversable
  blocks block the route or there is no stand-on-able floor.
- **doors[]{at,facing,clearance_blocks}** — sample the cells in front of
  (and behind) the door for `clearance_blocks` blocks; fail if both sides
  aren't air with a stand-on-able floor.
- **headroom[]{over_region_a,over_region_b,min_clear}** — for every column
  in the region, require at least `min_clear` air blocks above the highest
  solid block (over stairs, corridors, doorways).
- **block_mix_ratios[]{region_a,region_b,palette,max_single_ratio}** —
  count blocks in the region (using `block_scan_region`, paged at 65,536
  blocks per call); fail if any single block exceeds `max_single_ratio` of
  the total, or if listed palette members are missing entirely.
- **silhouette[]{region_a,region_b,sample_count,min_y_variance}** — sample
  N surface points; fail if Y variance < spec (for naturalistic terrain,
  no flat plateaus).
- **edge_irregularity[]{edge_name,from,to,max_collinear_run}** — sample
  along an edge; fail if any run of identical X or Z exceeds the limit
  (the 7-block rule for terrain).
- **connectivity[]{site_a,site_b,via}** — two named sites must be reachable
  along the named path (rail, road, footbridge).

Terrain phases get a richer set of contract rows specific to the
non-negotiables — see `terraforming/reference/non-negotiable-enforcement.md`.

Every `walkability`, `doors`, and `headroom` row in the contract is one
the inspector samples and one the worker is forbidden to silently work
around. If you can't write a row because you don't know the answer (e.g.
"is this door reachable?"), the plan is not detailed enough — interview the
user further or check the survey.

## Terrain and environment

If the build involves terrain, water, or natural scenery, **do not plan it
freehand** — a specialist skill owns it and writes the terrain phases into
`plan.toon` for you:

- A **named or recognizable natural wonder** (the Grand Canyon, a volcano, a
  karst bay) → the `natural-landmarks` skill.
- **Generic terrain or scenery** (a mountain, a river, a biome, a landscaped
  setting around a structure) → the `terraforming` skill.

Plan the structures and capture the requirements; leave the terrain phases to
the specialist, and note in `requirements.md` which one is needed.

Also keep `fill` steps within Minecraft's volume limit: any single `fill` must
cover at most ~32,768 blocks (a ~30×30×30 tile is a safe size). Split larger
volumes into multiple pre-tiled `fill` steps — the worker does no arithmetic.

## Hand off

State the plan back to the user in plain language and confirm it before
building. Then tell the orchestrator the plan is ready: the `blueprinter`
creates any listed structures, then the `worker` executes `plan.toon`.

The plan files are scratch — the durable record is the registry and structure
files written into the world during the build.
