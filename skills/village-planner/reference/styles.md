# Village styles and biome palettes

A village request falls into one of four buckets — match the user's to the
right amount of customization:

1. **Vanilla [biome]** — pure reuse of the standard look for that biome.
2. **Vanilla [biome], restyled** — the same layout and building forms, a
   swapped palette (a block-substitution map).
3. **Fully custom theme** — custom palette and building variants, but the
   vanilla building *roles* (farmer, librarian, smith, …) are preserved so the
   village stays functional.
4. **Specialty** — coastal, walled, farm-focused; a fixed template with knobs.

Whatever the style, professions and the functional rules in `mechanics.md` do
not change — only the look.

## Vanilla biome palettes

- **Plains** — `oak_planks`, `oak_log`, `cobblestone`, `oak_stairs`,
  `oak_fence`, hay bales, glass panes. Peaked roofs, the default village look.
- **Desert** — `sandstone`, `smooth_sandstone`, `cut_sandstone`,
  `terracotta` accents; flat or low roofs, small windows. Keep wooden doors.
  Paths are `smooth_sandstone`.
- **Savanna** — `acacia_planks` / `acacia_log`, `terracotta`, low-pitched
  roofs; an open, warm look.
- **Taiga** — `spruce_planks` / `spruce_log`, `stone`, `cobblestone`; steeper
  roofs, sturdy.
- **Snowy (plains / taiga)** — the spruce/stone taiga palette plus `snow`
  layers and the occasional `packed_ice`; snow settles on any open-sky block.

## Custom styles

Each is a palette + roof form + a few signature details, applied over the
vanilla building roles:

- **Medieval** — `stone_bricks` + `dark_oak` timber + `cobblestone`, leaded
  windows, steep roofs, a walled core, banners.
- **Cottagecore hamlet** — `stripped_birch_log` + `bricks` + `oak`, flower
  boxes and flowering azalea, lanterns everywhere, thatched-look roofs (oak
  stairs), small and charming, 3–5 buildings.
- **Tudor** — white infill between dark beams, steep gables.
- **Mediterranean / coastal** — white plaster (`white_terracotta`),
  `terracotta`-tile roofs, a fishing pier and boats.
- **Frontier / rustic** — rough `spruce` and `cobblestone`, a palisade, a
  watchtower.
- **Nordic** — heavy `spruce`, carved posts, turf roofs.

## Cross-biome notes

- In a sandstone biome, some vanilla buildings still use `cobblestone` (the
  well, the smiths) — a deliberate contrast; keep it.
- Match path material and lighting tone to the palette — soul lanterns suit
  snowy and spooky themes, ordinary lanterns suit the rest.
- Grow trees and bushes from saplings in any style — never place or duplicate
  a tree (see the `terraforming` skill). On Java Edition: place the sapling
  with `block_set_state`, then force growth with `command_execute` running
  `/place feature minecraft:<tree_type>`, or bone-meal via
  `player_give_item` / `itemstack_drop_at`. Buildings reuse; trees do not.
