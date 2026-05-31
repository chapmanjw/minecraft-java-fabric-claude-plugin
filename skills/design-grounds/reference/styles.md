# Garden traditions

Each tradition is a set of organizing principles, signature features, and a
palette. Match the user's request to one (or a deliberate fusion), and let it
govern the geometry.

## French formal (jardin à la française)

Strict bilateral symmetry about a long central axis; the garden is an
extension of the building's axis. **Parterres de broderie** (low scrollwork
hedging) near the house, `allées` and `bosquets` (geometric tree blocks)
beyond, a `parterre d'eau` (reflecting rectangles), grand perspective tricks.
Palette: clipped boxwood-green leaf hedging, gravel paths, lawn, stone basins.
Exemplars: Versailles, Vaux-le-Vicomte.

## Italian Renaissance / Baroque

Terraced hillsides linked by stairs and water; geometric beds, grottoes,
cypress alleys, water staircases cascading down the slope. Palette: stone
terracing, dark conifer verticals, statuary niches. Exemplars: Villa d'Este,
Villa Lante.

## English landscape

The "designed to look natural" tradition — sweeping lawns, a serpentine
*designed-irregular* lake, clumps of trees placed for composition, a ha-ha
(hidden ditch) instead of a wall, classical temples and follies as eye-catchers
on a circuit walk. It looks naturalistic but every clump and curve is
deliberate. Exemplars: Stourhead, Stowe. (English Arts-and-Crafts — Hidcote,
Sissinghurst — adds intimate hedged "garden rooms".)

## Mughal / Persian / Islamic

The **char bagh** — a four-quadrant paradise garden split by water channels
crossing at the center, often with a tomb or pavilion on the axis. Sunken
planting beds, narrow `acequia` channels, fountains, strict geometry. Terraced
variants descend a slope. Palette: stone channels, dark hedging, cypress,
flowering beds. Exemplars: the Taj Mahal garden, Shalimar Bagh, the Generalife.

## Japanese

Three sub-traditions:

- **Stroll garden** (chisen-kaiyū) — a pond circuit with sequenced, framed
  views; *no* axial geometry — composed viewpoints instead. `shakkei`
  (borrowed scenery), `miegakure` (hide-and-reveal).
- **Zen / dry landscape** (karesansui) — raked gravel and carefully placed
  stones representing water and mountains; small, contemplative, precise.
- **Tea garden** (roji) — a naturalistic path of stepping stones to a tea
  house, a stone water basin (`tsukubai`), lanterns.

Palette: moss, gravel, stone, maples and cherries, spruce framing, stone
lanterns. Exemplars: Kenroku-en, Ryōan-ji, Saihō-ji.

## Chinese scholar garden

Asymmetric, composed of four elements — rock (rugged rockeries), water,
plants, architecture (pavilions, covered corridors). Moon gates, lattice
windows, framed views, a winding route. Exemplars: the Suzhou classical
gardens.

## Modernist

Clean geometry, large planes — concrete, gravel, sheet water — minimal
planting, single specimen trees, bold simple form. Civic and contemporary.

## Contemporary perennial ("New Perennial")

Dense, naturalistic-looking matrix planting — many flowering plants packed
tightly through a grass matrix — but laid out deliberately. In Minecraft:
dense beds mixing flower and bush blocks through a grass base.

## Civic plaza

A hard-paved public square — geometric paving pattern, framed by uniform
façades, a central feature (a fountain, a monument, a column), trees in a
formal grid or rows. Exemplars: Place des Vosges, Piazza San Marco.

## Monastic cloister garth

A small, enclosed, four-square garden inside a covered walk — a central well
or fountain, quartered planting beds, quiet and simple.

## Fusion

The user may want a deliberate fusion (a French parterre in a Mughal palette,
a Japanese stroll garden in a cherry biome). Keep one tradition's *geometry* as
the governing structure and borrow the other's palette or features — do not
blend the structural logic of two, or the garden loses its order.

## Biome-aware plant and material selection (Java-exclusive)

Before choosing plant species and materials, read the site's actual biome with
`level_get_biome_at`:

```
level_get_biome_at("minecraft:overworld", {x:80,y:64,z:200})
→ {id:"minecraft:flower_forest", temperature:0.7, downfall:0.8, hasPrecipitation:true}
```

Map the biome id to appropriate plant species and path/wall materials:
- `minecraft:cherry_grove` → `cherry_log` pergolas, `cherry_leaves` canopy,
  `pink_petals` ground cover, stone lanterns. (Requires Java 1.20+.)
- `minecraft:jungle` / `minecraft:sparse_jungle` → `jungle_log` frames,
  heavy `vine`, `fern`, `cocoa` on logs, mossy stone.
- `minecraft:taiga` / `minecraft:snowy_taiga` → `spruce_log` pergolas,
  `spruce_leaves`, `fern`, `sweet_berry_bush`; paths in `cobblestone` /
  `stone` (no bare soil — it snows).
- `minecraft:plains` / `minecraft:sunflower_plains` → `oak_log` trellises,
  mixed wildflower beds, `grass_block` lawns, gravel paths.
- `minecraft:desert` → `sandstone` / `cut_sandstone` paths, `dead_bush`
  accents, `cactus` (sparse), palm-silhouette `jungle_log` columns.
- `temperature < 0.15` → use `snow_block` / `snow_layer` ground cover on
  terraces; avoid moisture-dependent plants.
- High `downfall` (≥ 0.8) → favour moss, `mud` edging, water channels, and
  lush vegetation; low downfall (≤ 0.2) → favour gravel, sand, dry stone.

Pick the tradition's geometry; let the biome govern the species and materials.
