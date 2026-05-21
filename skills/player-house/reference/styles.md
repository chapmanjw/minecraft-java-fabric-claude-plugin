# Architectural styles

Each style is a **palette** (block ratios), **forms** (roof, windows, massing),
and **detail signatures**. Apply ratios as in the terrain skills: a dominant
block plus accents. Match the style to the biome where possible; let the user
override. Block IDs are Java Edition `minecraft:` namespace (1.21.x).

## Standard / vernacular

The safe default when the user has no strong preference. `oak_planks` 3 :
`cobblestone` 2 : `oak_log` 2 : `stone_bricks` 1, glass-pane windows, a 1:1
stair-pitched gable roof, lanterns at the door. Clean, readable, hard to get
wrong.

## Medieval

`cobblestone` 3 : `stone_bricks` 2 : `oak_log` 2 : `oak_planks` 1. Steep 1:1
peaked roofs in stairs, exposed timber framing, leaded windows (iron bars over
panes), lanterns on chains. Stone base course, timber upper floors.

## Tudor

White (`white_terracotta` / `diorite`) infill between `dark_oak` beams,
`cobblestone` base, steep gables, tall narrow windows. The black-and-white
half-timber look.

## Japanese

`minecraft:smooth_stone` base, `minecraft:dark_oak_planks` / `minecraft:spruce_planks` framing,
`minecraft:blue_terracotta` or weathered-copper roofs with upturned eaves,
paper screens simulated with `minecraft:white_wool` + glass panes. Lantern-and-chain eaves; an engawa veranda on
slabs wrapping sunward rooms.

## Nordic / Viking

`spruce` everything, `stone` and `cobblestone` base, steep `dark_oak` roofs,
sometimes turf (`grass_block`/`moss`) roofing. Carved-post detailing, small
windows for a cold climate.

## Cottagecore

`stripped_oak_log` + `bricks` + `oak`, flowering azalea and flower boxes, a
campfire chimney trailing smoke, warm and cluttered. Suits plains and meadows.

## Modern

`quartz`, `white_concrete`, large glass, `smooth_stone`. Flat or shed roofs,
full-wall windows, hidden lighting (sea lanterns behind quartz slabs), crisp
right angles. Works in any biome.

## Mediterranean

`smooth_sandstone` / white plaster (`white_terracotta`), `terracotta`-tile
roofs (stairs), arched openings, courtyards. Warm, dry-climate look.

## Desert / adobe

`smooth_sandstone`, `cut_sandstone`, `terracotta` accents, flat roofs, small
windows, thick walls. For deserts and badlands.

## Dwarven

`deepslate`, `blackstone`, `polished` variants, `gold_block` and `lantern`
accents, dripstone columns, carved-from-rock massing. For underground bases.

## Industrial / steampunk

Copper in all oxidation states, `iron_block`, `blackstone`, `deepslate`,
exposed redstone-lamp lighting, dripstone "pipes", copper bulbs and grates.

## Fantasy variants

- **Elven** — pale woods, `quartz`, organic curves, leaf canopies, tall thin
  windows.
- **Wizard / fairy** — crooked towers, mushroom and amethyst accents, glowing
  whimsy.
- **Pirate** — weathered `dark_oak`/`spruce`, sails (wool), nautical detail.

Other styles the user may name — Victorian, brutalist, rustic, tropical,
arctic, Greek, Egyptian, Aztec — follow the same method: pick a 3–5 block
palette with ratios, a roof form, a window treatment, and 2–3 detail
signatures. If the user names a specific builder or a real reference, send
`researcher` for imagery first.

## Universal style rules

- **Mix block faces.** Never a wall of one block — blend stone/andesite/
  diorite/cobble/brick, or oak/stripped/planks/log. Flat single-block walls
  are the clearest amateur tell.
- **Never a flat slab roof.** Pitch it (1:1 or 1:2 stairs), add gables, hips,
  or dormers. A modern flat roof is deliberate; an accidental one is not.
- **Two-thick walls** read as real at estate scale and up; one-thick is fine
  for starter and cottage.
- **Trim courses and accent rows** — a band of a contrasting block at floor
  lines and the roofline ties a façade together.
