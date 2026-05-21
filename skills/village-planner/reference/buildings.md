# Building catalog

The standard village building types, by function. Reuse a small set of these
per village — build each as a template once, then stamp it (see the reuse model
in `SKILL.md`). Footprints are interior W×D; add wall thickness. Every building
a villager lives in needs one bed (2 air above the pillow) and, if it has a
profession, one workstation within 16h/4v.

## Residential

- **Small house** — 7×7, 1 bed. The village workhorse; carry 2–3 variants and
  reuse them heavily.
- **Medium house** — 9×9, 1–2 beds. A larger family home; spare beds here help
  reach the 20-bed iron-golem threshold and support breeding.
- **Large house** — 11×11, 2–3 beds, often two storeys.
- **Longhouse / bunkhouse** — a long room of several beds; an efficient way to
  add bed count.

## Profession buildings & workstations

One villager per workstation. Java Edition workstation blocks (use the full
`minecraft:` id when placing with `block_set_state`):

| Profession | Workstation | Java block id | Building note |
| ---------- | ----------- | ------------- | ------------- |
| Farmer | Composter | `minecraft:composter` | Cottage beside a crop plot. |
| Librarian | Lectern | `minecraft:lectern` | Library — bookshelves (decorative). |
| Toolsmith | Smithing Table | `minecraft:smithing_table` | Forge with a furnace and chimney. |
| Weaponsmith | Grindstone | `minecraft:grindstone` | Forge; often shares a building with the toolsmith. |
| Armorer | Blast Furnace | `minecraft:blast_furnace` | Smith's house. |
| Cleric | Brewing Stand | `minecraft:brewing_stand` | Temple / shrine. |
| Cartographer | Cartography Table | `minecraft:cartography_table` | Map house. |
| Fisherman | Barrel | `minecraft:barrel` | Cottage near water; pairs with a dock. |
| Fletcher | Fletching Table | `minecraft:fletching_table` | Bowyer's house. |
| Shepherd | Loom | `minecraft:loom` | House near the animal pens. |
| Leatherworker | Cauldron | `minecraft:cauldron` | Tannery. |
| Mason | Stonecutter | `minecraft:stonecutter` | Mason's house. |
| Butcher | Smoker | `minecraft:smoker` | Butcher shop near the animal pens. |

A villager with no workstation stays unemployed (use spares for breeding).

## Civic

- **Meeting hall / plaza** — the heart of the village; **houses the bell**.
  Hay-bale benches, open and lit.
- **Well** — the classic village centerpiece; decorative, 5×5 with a cobble
  curb.
- **Bell** — on a fence post or in the meeting hall, within 48 blocks of every
  bed pillow.
- **Watchtower** — 10–15 blocks tall with a lookout top; doubles as raid
  defense.

## Agriculture

- **Wheat farm** — the vanilla 9×9 plot with a central water source, four
  rows. Beetroot, carrot, and potato farms use the same layout.
- **Large farm** — 13×13+, mixed crops, worked by a second farmer.
- **Pumpkin / melon patch**, **sugar-cane row** (lakeside), **berry bushes**
  (taiga).
- **Composter loop** — a farmer throws surplus crops into a composter; a
  hopper-fed composter→chest loop yields bone meal. Keep the composter
  claimable as the farmer's job site.
- **Animal pens** — fenced enclosures, 7×7 minimum, lit, with water and feed:
  cows, pigs, sheep, chickens. Place near the shepherd and butcher.

## Defense

- **Walls** — cobblestone, stone, or a wood palisade; 3–5 blocks tall, with a
  walkway on tall walls. **Never fully seal the village** — leave spawnable
  ground outside and 1-block gaps every 10–15 blocks, or raiders spawn inside
  (see `mechanics.md`).
- **Gates** — a wooden double-door by default; an open arch reads fine too.
- **Watchtowers and lookout posts** — at corners and the gate.
- **Iron-golem pad** — keep the 17×13×17 volume around the bell open with a
  solid spawn surface.
- **Lighting** — light the whole village interior and perimeter so hostile
  mobs cannot spawn among the buildings.

## Special (optional)

Inn / tavern, market stalls, guard post, chapel, manor — themed extras for
character. They follow the same rules: a bed and workstation if a villager
uses them, otherwise purely decorative.

## Java-exclusive: seeding building chests with loot tables

Rather than hand-picking chest contents item by item, use `loot_table_generate`
to produce a believable set of items from a vanilla loot table, then slot them
in with `inventory_set_slot`.

```
# 1. Generate loot from the matching village loot table
loot_table_generate("minecraft:chests/village/village_weaponsmith")
→ iron_ingot×5, obsidian×4, apple×3, iron_sword×1   (example — rolls are random)

# 2. Place each result into the chest at the building's position
inventory_set_slot(pos=<chest_pos>, slot=0, item={id:"minecraft:iron_sword",count:1})
inventory_set_slot(pos=<chest_pos>, slot=1, item={id:"minecraft:iron_ingot",count:5})
# … continue for each item returned
```

Vanilla village chest loot-table ids follow the pattern
`minecraft:chests/village/village_<profession>`. Common ones:

| Building | Loot table id |
| -------- | ------------- |
| Weaponsmith | `minecraft:chests/village/village_weaponsmith` |
| Toolsmith | `minecraft:chests/village/village_toolsmith` |
| Armorer | `minecraft:chests/village/village_armorer` |
| Cartographer | `minecraft:chests/village/village_cartographer` |
| Shepherd | `minecraft:chests/village/village_shepherd` |
| Fisher | `minecraft:chests/village/village_fisher` |
| Fletcher | `minecraft:chests/village/village_fletcher` |
| Mason | `minecraft:chests/village/village_mason` |
| Tannery (leatherworker) | `minecraft:chests/village/village_tannery` |
| Temple (cleric) | `minecraft:chests/village/village_temple` |
| Desert house | `minecraft:chests/village/village_desert_house` |
| Plains house | `minecraft:chests/village/village_plains_house` |
| Taiga house | `minecraft:chests/village/village_taiga_house` |
| Savanna house | `minecraft:chests/village/village_savanna_house` |
| Snowy house | `minecraft:chests/village/village_snowy_house` |

Use `loot_table_list` to enumerate all available ids on the running server.
The optional `position` parameter makes the roll biome-aware (affects
biome-sensitive tables). Rolls are random each call — re-roll if the result
feels wrong for the building's flavor.
