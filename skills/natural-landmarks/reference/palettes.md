# Landmark palette presets

Named palettes for natural wonders, with Java block IDs and mix ratios.
These are landmark-specific rock/mineral palettes — for biome surface palettes
(forest, desert, taiga) see the `terraforming` skill's `reference/palettes.md`.

Apply a ratio the same way as in terraforming: place the dominant block with
`block_fill_region`, then convert sub-percentages with `replace`-mode fills
or single-block structure modules placed at the matching `integrity`.

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

## Palette notes

- **Water colour comes from what is under the water**, not the water itself —
  Crater Lake deep blue, Ijen turquoise, Havasu blue-green are all the floor
  block. Never expect to tint water directly.
- **Concrete vs concrete powder:** powder obeys gravity (use for White Sands
  dunes); solid concrete does not (use for Salar). Mixing them up collapses the
  build on chunk reload.
- **Version note:** cherry blocks need Java **1.20+**; copper oxidation and
  amethyst need **1.17+**. Check the host version with `server_get_status`.
