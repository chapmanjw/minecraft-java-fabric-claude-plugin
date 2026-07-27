# Terrain palettes

Block palettes with Java IDs and mix ratios, covering two traditions:

- **Biome palettes** — surface palettes for terrain shaping (forest, desert,
  taiga, …).
- **Landmark palette presets** — named rock/mineral palettes for specific
  natural wonders (Grand Canyon, Halong, Salar de Uyuni, …).

Ratios are **starting defaults** — let the user override. Never use one block
at 100%; mix 4–8 variants. Blend neighbouring biomes over a 10–30 block
transition zone.

How to apply a ratio: over the surface region, place the dominant block with
`block_fill_region`, then convert sub-percentages to other variants — either
with `replace`-mode fills over sub-regions, or by stamping a single-block
structure module at the matching `integrity` (see
`${CLAUDE_PLUGIN_ROOT}/skills/terrain-shape/reference/command-budget.md`).

---

# Biome palettes

Surface palettes for naturalistic terrain.

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

---

# Landmark palette presets

Named palettes for natural wonders. These are landmark-specific rock/mineral
palettes; for biome surface palettes (forest, desert, taiga) use the **Biome
palettes** section above. Apply a ratio the same way: place the dominant block
with `block_fill_region`, then convert sub-percentages with `replace`-mode
fills or single-block structure modules placed at the matching `integrity`.

## colorado-plateau

Banded canyon strata, top to bottom (Grand Canyon, Capitol Reef):
`red_sandstone` 15% → `orange_terracotta` 15% → `red_terracotta` 10% →
`smooth_sandstone` 15% → `light_gray_terracotta` 10% → `cobbled_deepslate` 15%
→ `deepslate` 20%. Band order matters — red/orange on top, grey/dark at the
bottom. Reversing it reads as alien.

## navajo-sandstone

Sheer red sandstone cliffs and slickrock (Zion, Antelope, The Wave):
`smooth_red_sandstone` 50%, `red_sandstone` 20%, `cut_red_sandstone` 10%,
`red_terracotta` 10%, `orange_terracotta` 10%.

## bryce-terracotta

Hoodoo bands (Bryce): `orange_terracotta` 25%, `red_terracotta` 20%,
`white_terracotta` 20%, `pink_terracotta` 15%, `yellow_terracotta` 10%,
`red_sand` 10%.

## uluru-red

Inselberg body (Uluru, Kata Tjuta): `red_sandstone` 60%, `red_terracotta` 20%,
`orange_terracotta` 10%, `cut_red_sandstone` 10% for vertical ribbing.

## monument-valley

Buttes on red desert: `red_sandstone` caprock (5-block cap), `orange_terracotta`
60% body, `red_terracotta` 30% mid-band, `red_sand` floor.

## basalt-volcanic

Columns, volcanoes, basalt curtains (Giant's Causeway, Devils Tower, Victoria,
Fuji body): `basalt` 80%, `smooth_basalt` 10%, `polished_basalt` 5%,
`blackstone` 5%. Lava fields add `magma_block`, `obsidian`, `gravel`.

## karst-limestone

Limestone towers (Halong, Guilin, Phang Nga): `stone` 30%, `andesite` 20%,
`diorite` 15%, `mossy_cobblestone` 15%, `calcite` 10%, `dripstone_block` 5%;
`moss_block` + jungle saplings + vines on top.

## chalk-cliff

White sea cliffs and stacks (Dover, Étretat, Twelve Apostles): `calcite` 70%,
`diorite` 20%, `bone_block` 10%. Calcite is the block that makes it read as
chalk.

## travertine-white

Mineral terraces (Pamukkale, Huanglong): `calcite` 50%, `dripstone_block` 30%,
`bone_block` 10%, `smooth_quartz` 10%; pool floors `light_blue_concrete`
(turquoise) or `prismarine` (Havasu blue-green) or `honey_block` (Mammoth tan).

## glacier

Ice tongues and bergs (Perito Moreno, icebergs): `packed_ice` 50–60%,
`blue_ice` 30% (more toward the bottom), `ice` 10%, `snow_block` 10% cap;
moraines `gravel` + `cobblestone` + `stone`.

## salt-flat

Salt plains (Salar de Uyuni, Bonneville): `white_concrete` 95% (stable —
**never `white_concrete_powder`**, which falls), `light_gray_concrete` 5% for
the hexagonal crack pattern.

## prismatic-spring

Hot-spring colour rings (Grand Prismatic), centre outward: `blue_concrete` →
`cyan_concrete` → `light_blue_concrete` → `green_concrete` → `yellow_concrete`
→ `orange_concrete` → `red_concrete`, then a `stone` rim. Place at the floor
under 1–2 blocks of water — the water tints to the block beneath.

## rainbow-mountain

Diagonal contour stripes (Vinicunca): `red_terracotta`, `orange_terracotta`,
`yellow_terracotta`, `lime_terracotta`, `cyan_terracotta`, `purple_terracotta`,
`brown_terracotta` — bands running *along contour lines*, across the slope.

---

# Biome-matched palette step (Java-exclusive)

Before committing to any palette above — biome or landmark — read the actual
biome at the build site with `level_get_biome_at` and bias your selection to
match.

```
level_get_biome_at("minecraft:overworld", {x:120,y:64,z:-340})
→ {id:"minecraft:taiga", temperature:0.25, downfall:0.8, hasPrecipitation:true,
   precipitation:"rain", waterColor:"#3F76E4", grassColorModifier:"none"}
```

For biome palettes:

- `id` maps directly to the biome palette sections above — use it to pick the
  starting defaults rather than guessing from nearby surface blocks.
- `temperature < 0.15` → expect snow; add `snow_layer` / `snow_block` and
  increase `packed_ice` in the water palette.
- `temperature > 1.0` → hot/arid; bias toward sand, coarse dirt, and
  dead vegetation.
- `downfall` and `hasPrecipitation` determine moss, mud, and water-feature
  plausibility — high downfall favours `moss_block`, `mud`, and heavy vine.
  (`downfall` was reported as 0 for every biome by mod versions before 1.0.1;
  if you see a flat 0 everywhere, the server is running an older jar.)
- `precipitation` resolves what actually falls **at that block** — `none`,
  `rain` or `snow`. It accounts for altitude, so the same biome can answer
  `snow` on a peak and `rain` in the valley. Prefer it over inferring from
  `temperature` by hand.
- `waterColor` and any `grassColorOverride` / `foliageColorOverride` /
  `dryFoliageColorOverride` give the biome's actual tint, so water features and
  foliage choices can match. Overrides are absent for biomes that sample the
  colour gradient rather than pinning a value. `grassColorModifier` is `swamp`
  or `dark_forest` where vanilla post-processes the tint.
- At biome boundaries, call `level_get_biome_at` at multiple points and
  blend the two palettes across a 10–30 block transition zone.

For landmark palettes:

```
level_get_biome_at("minecraft:overworld", {x:200,y:80,z:50})
→ {id:"minecraft:badlands", temperature:2.0, downfall:0, hasPrecipitation:false,
   precipitation:"none", waterColor:"#3F76E4",
   grassColorOverride:"#90814D", foliageColorOverride:"#9E814D"}
```

- A high-temperature, zero-downfall biome (badlands, desert) confirms
  `dead_bush`, `cactus`, `red_sand` and excludes moss or heavy vegetation.
- A cold biome (`temperature < 0.15`) confirms snow cap, `packed_ice` on
  shaded ledges, and no liquid-water features at altitude.
- `hasPrecipitation: false` means no rain/snow regardless of temperature —
  adjust vegetation accordingly.

The landmark palette governs the landmark's primary rock/mineral body. The
biome read governs the ground surround, vegetation, and accent materials that
tie the landmark to its setting.

**Paint the biome to match the landform.** Surface blocks alone don't change
foliage/water tint, mob spawns, or climate — the underlying biome does. On a
**v0.3.0+ mod**, set the biome of the built region with **`level_fill_biome`**
(dimension, from/to, biome id, optional `replace_filter`) so a snowy peak spawns
snowy-biome mobs and tints its foliage, rather than borrowing the surrounding
biome. **Fall back** to `command_execute` with `/fillbiome` on older mods. Skip
this when the build already sits in the matching biome.

---

# Palette notes

- **Water colour comes from what is under the water**, not the water itself —
  Crater Lake deep blue, Ijen turquoise, Havasu blue-green are all the floor
  block. Never expect to tint water directly.
- **Concrete vs concrete powder:** powder obeys gravity (use for White Sands
  dunes); solid concrete does not (use for Salar). Mixing them up collapses the
  build on chunk reload.
- **Version note:** cherry blossom, mangrove, deep dark, and pink petals need
  Java **1.20+**; basalt and blackstone need **1.16+**; copper oxidation and
  amethyst need **1.17+**. Check the host version with `server_get_status`
  before relying on newer blocks.
