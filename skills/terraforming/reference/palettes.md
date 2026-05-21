# Biome palettes

Block palettes with Java IDs and mix ratios. Ratios are **starting
defaults** — let the user override. Never use one block at 100%; mix 4–8
variants. Blend neighbouring biomes over a 10–30 block transition zone.

How to apply a ratio: over the surface region, place the dominant block with
`block_fill_region`, then convert sub-percentages to other variants — either
with `replace`-mode fills over sub-regions, or by stamping a single-block
structure module at the matching `integrity` (see `command-budget.md`).

## Alpine / mountainous

- Rock: `stone` 50%, `andesite` 15%, `diorite` 10%, `granite` 10%,
  `cobblestone` 8%, `gravel` 5%, `coal_ore` 2%.
- Snowline overlay: `snow_layer` (1–6 layers), `snow`, `packed_ice` on shaded
  north faces, `ice` on tarns.
- Vegetation: `spruce_log` / `spruce_leaves` below snowline; `fern`,
  `large_fern`, `tall_grass`; rare `lily_of_the_valley`.

## Desert

- `sand` 70%, `sandstone` 15% (exposed), `smooth_sandstone` for hard strata,
  `cut_sandstone` rare, `red_sand` 5% toward mesa transitions.
- Detail: `dead_bush`, `cactus` (sparse — never clumped).

## Temperate forest

- Surface: `grass_block` 60%, `dirt` 15%, `podzol` 8%, `coarse_dirt` 7%,
  `moss_block` 5%, `rooted_dirt` 3%, `mud` 2% in damp hollows.
- Vegetation: mixed `oak` / `birch` / `dark_oak`; `azalea`,
  `flowering_azalea`, mushrooms, `tall_grass`.

## Taiga / tundra

- `snow` 50%, `grass_block` or `podzol` 25%, `coarse_dirt` 10%, `stone` 10%,
  `packed_ice` 5% in lakes.
- Vegetation: `spruce_log` / `spruce_leaves`, `sweet_berry_bush`, `fern`.

## Jungle / tropical

- Surface: `grass_block` 70%, `podzol` 15%, `coarse_dirt` 10%, `moss_block` 5%.
- Vegetation: `jungle_log`, `jungle_leaves`, heavy `vine`, `cocoa` on jungle
  logs, `fern`, `large_fern`, rare `melon`.

## Badlands / mesa

- Banded terracotta — red / orange / yellow / white / light-gray / brown /
  plain — in horizontal bands 2–4 tall with ±7 vertical noise per column.
- Surface: `red_sand` 60%, `orange_terracotta` 20%, `terracotta` 15%,
  `coarse_dirt` 5%.
- Vegetation: heavy `dead_bush`, rare `cactus`; wooded badlands add
  `coarse_dirt` + `oak` / `acacia`.

## Coastal

- `sand` 70%, `gravel` 15%, `dirt` 10% (with grass tufts), `cobblestone` 5%
  for rocky promontories.

## Swamp / mangrove

- `mud` 45%, `grass_block` 20%, `dirt` 15%, `coarse_dirt` 10%, `clay` 5%,
  `mangrove_roots` 3%, `muddy_mangrove_roots` 2%.
- Decor: `lily_pad`, `vine`, `mangrove_propagule`, `frogspawn`.

## Cherry blossom

- `grass_block` 70%, `dirt` 15%, `coarse_dirt` 10%, `stone` 5% exposed.
- Decor: `cherry_log`, `cherry_leaves`, `pink_petals` (stages 1–4).

## Mushroom fields

- `mycelium` 90%, `dirt` 10% (rare patches).
- Decor: giant mushrooms from `red_mushroom_block` / `brown_mushroom_block` /
  `mushroom_stem`; small `red_mushroom` / `brown_mushroom`.

## Cave biomes

- **Dripstone caves:** `stone` 60%, `dripstone_block` 30%, `pointed_dripstone`
  clusters 10%.
- **Lush caves:** `moss_block`, `moss_carpet`, `azalea`, `flowering_azalea`,
  `glow_lichen`, `clay`, `rooted_dirt`, `hanging_roots`, `cave_vines` with
  `glow_berries`.
- **Deep dark:** `deepslate` 60%, `cobbled_deepslate` 15%, `sculk` 15%,
  `sculk_vein` 5%, rare `sculk_catalyst` / `sculk_shrieker` / `sculk_sensor`.
- General natural stone: blend `deepslate` + `tuff` + `calcite` for a craggy
  marble look.

## Volcanic (synthetic — no native vanilla biome)

- `basalt` 35%, `blackstone` 20%, `smooth_basalt` 15%, `polished_blackstone`
  10%, `magma_block` 5%, `obsidian` 5%, `gravel` 5%, `cobblestone` 5%.
- Lava channels; rare `crying_obsidian` for cooled-vent accents.

## Nether-inspired Overworld

- `netherrack` 50%, `nether_wart_block` 15%, `crimson_nylium` /
  `warped_nylium` 10%, `basalt` 10%, `magma_block` 5%, `soul_sand` 5%,
  `glowstone` 5% as ceiling lights.

## Biome-matched palette step (Java-exclusive)

Before committing to any palette above, read the actual biome at the build
site with `level_get_biome_at` and bias your selection to match:

```
level_get_biome_at("minecraft:overworld", {x:120,y:64,z:-340})
→ {id:"minecraft:taiga", temperature:0.25, downfall:0.8, hasPrecipitation:true}
```

- `id` maps directly to the palette sections above — use it to pick the
  starting defaults rather than guessing from nearby surface blocks.
- `temperature < 0.15` → expect snow; add `snow_layer` / `snow_block` and
  increase `packed_ice` in water palette.
- `temperature > 1.0` → hot/arid; bias toward sand, coarse dirt, and
  dead vegetation.
- `downfall` and `hasPrecipitation` determine moss, mud, and water-feature
  plausibility — high downfall favours `moss_block`, `mud`, and heavy vine.
- At biome boundaries, call `level_get_biome_at` at multiple points and
  blend the two palettes across a 10–30 block transition zone.

## Version note

Cherry blossom, mangrove, deep dark, and pink petals need Java **1.20+**;
basalt and blackstone need **1.16+**. Check the host version with
`server_get_status` before relying on newer blocks.
