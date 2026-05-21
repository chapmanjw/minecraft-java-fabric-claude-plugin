# Display entities — block_display / item_display / text_display

**This is the single biggest Java-exclusive build-art technique. Bedrock has
nothing like it.** A display entity is summoned with `entity_summon` (entity
type `minecraft:block_display`, `minecraft:item_display`, or
`minecraft:text_display`) carrying NBT that controls how it is rendered. They
have **no hitbox, no collision, and do not tick** — they are purely visual. Use
them for things voxel blocks and armor stands cannot do:

- **3D floating text and logos** — `text_display`, at any size, any color, with
  a backing panel.
- **Blocks at arbitrary scale, rotation, and translation** — `block_display`,
  for sub-block detail, impossible angles, and giant single-block forms.
- **Glowing tinted accent geometry** — any display with `Glowing:1b` +
  `glow_color_override`.
- **Museum / pedestal item displays** — `item_display`, an item shown floating,
  on the ground, or mounted on a wall.

Place display entities in a **late decoration phase**, like armor stands, after
the blockwork is built so fills do not disturb them. Tag every one
(`Tags:["mcb_deco"]`) so it can be found again with `entity_query` and adjusted
with `entity_set_nbt`.

> **Version note (verify before relying on edge cases).** All examples below
> are verified live on **26.1.2**; this mod also supports **1.21.11**. The
> display-entity NBT (`transformation`, `billboard`, `brightness`,
> `glow_color_override`, the `text_display` text/background fields) has been
> stable since 1.19.4 and is reliable on both. Item-`components` SNBT inside an
> `item_display`'s shown item is the format that *does* drift across versions —
> if you embed a custom item, round-trip it with `itemstack_describe` on the
> running version (`server_get_status` reports the version). Do not assert a
> component shape blindly.

## The transformation block — common to all three

Every display entity carries a `transformation` compound that is applied to its
rendered geometry. It has four fields, applied in order
**translation → left_rotation → scale → right_rotation**:

```
transformation:{
  scale:[1f,1f,1f],              // per-axis scale, floats (note the f suffix)
  left_rotation:[0f,0f,0f,1f],   // quaternion [x,y,z,w]
  right_rotation:[0f,0f,0f,1f],  // quaternion [x,y,z,w]
  translation:[0f,0f,0f]         // per-axis offset in blocks, floats
}
```

- **`scale`** — `[x,y,z]` floats. `[2f,2f,2f]` doubles the form; `[0.5f,3f,0.5f]`
  is a thin tall pillar; `[8f,8f,8f]` is a giant single block. There is no hard
  cap, but very large scales clip oddly near other geometry.
- **`translation`** — `[x,y,z]` floats, an offset (in blocks) from the entity's
  summon position. Scaling grows a block from its corner, so a scaled block
  usually needs a negative translation to re-center it (a block scaled `[2f,2f,2f]`
  grows +1 in each axis; translate `[-0.5f,0f,-0.5f]` to keep it centered on the
  original footprint).
- **`left_rotation` / `right_rotation`** — **quaternions** `[x,y,z,w]`, not Euler
  angles. The **identity (no rotation) quaternion is `[0f,0f,0f,1f]`** — use it
  whenever you don't want rotation. See the quaternion section below.

### The identity quaternion and the safe default

When you only need scale and/or translation (no rotation), set **both**
rotations to the identity:

```
left_rotation:[0f,0f,0f,1f], right_rotation:[0f,0f,0f,1f]
```

This is the safe default and what most block_display / text_display uses want.

### Quaternions are fiddly — how to get a rotation right

A quaternion `[x,y,z,w]` for a rotation of angle θ about a unit axis `(ax,ay,az)`
is `[ax·sin(θ/2), ay·sin(θ/2), az·sin(θ/2), cos(θ/2)]`. Common single-axis
rotations (set as `left_rotation`, leave `right_rotation` identity):

| Rotation | Quaternion `[x,y,z,w]` |
|----------|------------------------|
| none (identity) | `[0f,0f,0f,1f]` |
| 90° about Y (yaw) | `[0f,0.7071f,0f,0.7071f]` |
| 180° about Y | `[0f,1f,0f,0f]` |
| −90° / 270° about Y | `[0f,-0.7071f,0f,0.7071f]` |
| 45° about Y | `[0f,0.3827f,0f,0.9239f]` |
| 90° about X (pitch) | `[0.7071f,0f,0f,0.7071f]` |
| 45° about X | `[0.3827f,0f,0f,0.9239f]` |
| 90° about Z (roll) | `[0f,0f,0.7071f,0.7071f]` |
| 45° about Z (a tilt) | `[0f,0f,0.3827f,0.9239f]` |

`0.7071` ≈ sin/cos of 45° (= √½); `0.3827`/`0.9239` ≈ sin/cos of 22.5° (the
half-angle of a 45° rotation). **Because the agent cannot see the world**, do
not trust a hand-computed quaternion blindly: **summon one test display, ask the
user to glance at it (or read it back with `entity_get_nbt`), and confirm the
orientation before stamping a row of them.** For a compound tilt, prefer
composing two single-axis rotations (one in `left_rotation`, one in
`right_rotation`) over hand-multiplying quaternions.

### Animation (optional) — interpolation fields

A transformation can be animated smoothly instead of snapping. Set the new
`transformation` with `entity_set_nbt`, and on the same entity set:

- `start_interpolation:0` — tick offset at which the interpolation begins
  (`0` = next tick).
- `interpolation_duration:20` — number of ticks (20 = 1 second) to ease into the
  new transformation.
- `teleport_duration:N` — ticks to interpolate position changes from teleports.

This is the non-redstone way to make displays drift, spin, pulse, or grow. To
loop an animation, drive the `entity_set_nbt` updates from a `schedule_function`
that re-schedules itself (see the datapack-functions note in the planner /
engineer references) — that requires the build to ship a small datapack, so
treat looping animation as an advanced option and note the datapack requirement
in `plan.toon`.

## text_display — 3D floating text and logos

Floating text/logos at any size and color, optionally with a backing panel.
Verified example:

```
entity_summon("minecraft:text_display", pos, nbt='{
  text:"{\"text\":\"GRAND HALL\",\"color\":\"gold\",\"bold\":true}",
  billboard:"center", line_width:200, background:1073741824,
  transformation:{scale:[2f,2f,2f],left_rotation:[0f,0f,0f,1f],
    right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f]},
  Tags:["mcb_deco"]}')
```

Fields specific to `text_display`:

- **`text`** — a stringified JSON text component (same shape as a sign line):
  `"{\"text\":\"…\",\"color\":\"gold\",\"bold\":true}"`. For multiple lines, use
  a `\n` inside the text, or a list of components.
- **`billboard`** — how the text faces the viewer:
  - `fixed` — locked to the transformation's orientation (use this for text laid
    flat on a wall or floor, or a sign that must keep a fixed angle).
  - `vertical` — yaws to face the player but stays upright.
  - `horizontal` — pitches to face the player but keeps its yaw.
  - `center` — always faces the player head-on (a classic floating title).
- **`line_width`** — max pixel width before wrapping (default 200); raise it for
  long single-line titles, lower it to force wrapping.
- **`background`** — ARGB packed int for the panel behind the text. `1073741824`
  (`0x40000000`) is the default semi-transparent black; `0` removes the panel
  entirely (text only); a fully-opaque tint is `0xFF......` (e.g. `0xFF202020` =
  `-14671840`). For a clean glowing logo, set `background:0` and use a bold color.
- **`text_opacity`** — `0`–`255` (or `-1` for default).
- **`alignment`** — `center` / `left` / `right`.
- **`see_through:1b`** — render the text through walls.
- **`default_background:1b`** — use the vanilla chat background instead of a
  custom `background` value.

Use cases: monument titles and dedication plaques, giant 3D logos and crests
laid on a wall (`billboard:"fixed"` + a `transformation` rotation), floating
labels over museum exhibits, large readable text Bedrock could only fake with
block letters.

## block_display — blocks at arbitrary scale, rotation, translation

A single block rendered with full control over scale, rotation, and offset —
the workhorse for **detail below 1-block resolution, impossible angles, and
giant single-block forms**. Verified example (a glowing, gold, thin-tall pillar):

```
entity_summon("minecraft:block_display", pos, nbt='{
  block_state:{Name:"minecraft:gold_block"},
  brightness:{block:15,sky:15}, glow_color_override:16766720, Glowing:1b,
  transformation:{scale:[0.5f,3f,0.5f],left_rotation:[0f,0f,0f,1f],
    right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f]},
  Tags:["mcb_deco"]}')
```

Fields specific to `block_display`:

- **`block_state`** — `{Name:"minecraft:gold_block"}`, plus an optional
  `Properties:{…}` for stateful blocks
  (`{Name:"minecraft:oak_stairs",Properties:{facing:"east",half:"top"}}`). This is
  the rendered block; it is **not** a real block in the world (no collision, no
  light unless `brightness` is set, no block updates).
- **`brightness`** — `{block:0-15, sky:0-15}` overrides how the block is lit.
  Set both to `15` so a display reads brightly regardless of ambient light
  (displays are otherwise lit by their position, which can leave them dim).
- **`glow_color_override`** — packed RGB int for the outline color when
  `Glowing:1b` is set (`16766720` = `0xFFD700`, gold). Without this, a glowing
  display uses its team color (white by default).
- **`Glowing:1b`** — draw the glowing outline (visible through walls). Pair with
  `glow_color_override` for tinted accent geometry.

Use cases for build-art:

- **Sub-block detail** — a block scaled to `[0.25f,0.25f,0.25f]` is a quarter-block
  cube; tile several to carve detail finer than the voxel grid allows (rivets,
  inlay, small facial features on a statue, gem facets).
- **Impossible angles** — a block rotated 45° (or any quaternion) sits at an
  angle no placed block can; use for diagonal banding, tilted crystal facets,
  angled signage, slanted roof or fin detail.
- **Giant single-block forms** — a block scaled `[8f,8f,8f]` or larger is one
  enormous cube/sphere-faced form with no seams — a monolith, a giant gem, a
  floating cube of obsidian, the core of an abstract sculpture.
- **Glowing accent geometry** — `Glowing:1b` + `glow_color_override` makes
  tinted edges that read at night and through fog: energy lines on a sculpture,
  glowing runes, neon-style edges, a halo.

## item_display — museum and pedestal item displays

An item rendered floating, on the ground, in a frame-like pose, or in a hand
pose — for **museum exhibits, pedestal trophies, and held props** at a scale and
freedom no item frame allows.

```
entity_summon("minecraft:item_display", pos, nbt='{
  item:{id:"minecraft:diamond",count:1},
  item_display:"fixed",
  transformation:{scale:[1.5f,1.5f,1.5f],left_rotation:[0f,0f,0f,1f],
    right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f]},
  Tags:["mcb_deco"]}')
```

Fields specific to `item_display`:

- **`item`** — the shown itemstack (`{id:"…",count:1}`, optionally with a
  `components` SNBT — verify that component shape against the running version, it
  drifts across releases).
- **`item_display`** — the display context, which controls the item's default
  orientation/scale like a model in that slot:
  - `none`, `fixed` (in a frame / on a wall), `ground` (dropped-item look),
    `gui`, `head`, `thirdperson_lefthand` / `thirdperson_righthand`,
    `firstperson_lefthand` / `firstperson_righthand`.
  - `fixed` and `ground` are the usual choices for build-art (a flat displayed
    item vs. a small grounded prop).

Use cases: a sword or crown floating over a pedestal, a museum case of artifacts
(one `item_display` per exhibit, lit with a nearby `block_display` or real light),
a giant scaled-up item as a sculpture, a held prop too large or oddly-angled for
an armor stand.

## Honest limits

- **No collision, no physics, purely visual.** Players walk through a display
  entity. It is decoration only — never load-bearing or walkable. A real block is
  still required for any surface a player stands on or any wall that must block
  movement.
- **No light unless you set `brightness`.** A `block_display` of glowstone does
  not emit light; set `brightness:{block:15,sky:15}` to make it *look* lit, or
  place a real light block nearby for actual illumination.
- **The agent cannot see the result.** Quaternion orientation, scale, and
  text-panel sizing are easy to get wrong sight-unseen. For any display-heavy
  piece, **summon one representative display first and propose an explicit user
  visual checkpoint** ("I've placed one test logo / one tilted facet — does the
  orientation and size look right?") before stamping the full set. Read state
  back with `entity_get_nbt` to confirm the NBT applied, but a read confirms the
  fields, not how it *looks*.
- **Entity count has a cost.** Displays are cheap (they don't tick) but not free;
  use them for *accent and detail*, not as a replacement for bulk blockwork. A
  monument's main mass is always real blocks.

## In the plan

- Summon every display with `entity_summon` at the **decoration phase**, passing
  all NBT in the `nbt` argument, and tag it `Tags:["mcb_deco"]`.
- For a row or grid of identical displays (e.g. a logo band, a facet array),
  list each summon with its position and per-instance `transformation` in
  `plan.toon` — there is no fill primitive for entities.
- Add a `quality_contract` checkpoint that names the **user visual confirmation**
  for orientation/scale on the first placed display before the rest are stamped.
- Use `entity_set_nbt` to adjust a placed display's `transformation`, `text`, or
  `glow_color_override` after the fact (and to drive interpolated animation).
