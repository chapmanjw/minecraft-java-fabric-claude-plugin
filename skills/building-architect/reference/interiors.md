# Interiors and interior depth

The user chooses how deep the interior goes. This is the **single biggest cost
driver** — surface it early and quote a fill-volume estimate.

## The three interior-depth modes

- **Aesthetic-only** — the exterior is fully detailed; interiors are empty
  shells (floors, walls, ceilings, glazing, lighting) but unfurnished. Lowest
  cost. Good for distant landmarks and pure showpieces.
- **Hybrid** — the user names a few **hero rooms** (the Great Hall, the throne
  room, the library); those are fully furnished, the rest are shells. The
  usual choice for large buildings.
- **Fully furnished** — every room furnished and decorated. An order of
  magnitude more block placement than aesthetic-only. Right for buildings the
  user will actually live in or tour.

Estimate fill volume roughly as
`Σ(module footprint × height) × density`, with density ≈ 0.4 aesthetic /
0.7 hybrid / 0.95 fully furnished. Give the user the number before designing.

## Rules for any furnished interior

- **Every hero room visible from outside** — a furnished room with no window
  or doorway is wasted; add an opening or move the room.
- **Light coverage** — no spawnable dark cell; prefer hidden light (a glowstone
  under a carpet, a sea lantern behind a slab).
- **Match the era** — no Victorian furniture in a medieval hall; furnishing
  follows the building's period.

## Furnishing by era

Use vanilla block tricks (stairs, slabs, trapdoors, fences, item frames,
banners — see the `player-house` skill's `interiors.md` for the catalogue of
furniture forms) with period-appropriate materials:

- **Medieval / Gothic** — long timber tables and benches, banners, iron
  chandeliers (lanterns on chains), rushes (carpet), stone hearths, chests and
  barrels. Cathedrals: pews, an altar, candles, a great rose window lit from
  behind.
- **Classical / Renaissance** — symmetric furniture, columns, statuary
  (armor stands), marble floors, urns (flower pots and finials).
- **Baroque / palace** — gilding (gold blocks), grand staircases, chandeliers,
  long galleries, framed art (paintings, item-frame mosaics).
- **Victorian** — cluttered, patterned (carpets, glazed terracotta), heavy
  drapery (banners, wool), fireplaces.
- **Modern** — minimal, large glazing, hidden lighting, open plan, quartz and
  concrete surfaces.
- **Fantasy** — match the style from `fictional.md`: glowing crystals and soul
  fire for arcane, lava and anvils for dwarven, leaf-and-vine detail for
  elven.

## Signature interiors

Some buildings are defined by an interior as much as a façade — the Hagia
Sophia's dome from within, a Gothic nave, a great hall. When a building has a
signature interior space, treat it as a hero room even in hybrid mode.

---

## Java-exclusive: NBT detailing & loot

These techniques let Java builds achieve the signage, named items, and
believably-stocked rooms that Bedrock's API could not produce. Apply them in
hero rooms; skip them in aesthetic-only shells.

### Signs with text (capability A)

Place a `*_sign` or `*_hanging_sign` block, then set its text with
`block_entity_set_nbt`:

```
block_entity_set_nbt(pos, nbt='{front_text:{messages:[
  "{\"text\":\"GRAND ARCHIVE\",\"color\":\"gold\",\"bold\":true}",
  "{\"text\":\"Restricted Collection\"}", "\"\"", "\"\""],
  has_glowing_text:1b}, is_waxed:1b}')
```

`messages` always has exactly four entries (empty lines are `"\"\""`).
`back_text` is the same shape. `is_waxed:1b` prevents players editing.
Verify with `block_entity_get_nbt` after the merge.

### Banners with patterns (capability A)

Place a `*_banner` block, then:

```
block_entity_set_nbt(pos, nbt='{patterns:[
  {pattern:"minecraft:stripe_bottom",color:"white"},
  {pattern:"minecraft:cross",color:"gold"},
  {pattern:"minecraft:border",color:"black"}]}')
```

Up to 6–8 pattern layers read cleanly. Combine with standing banners flanking
doorways or hanging from balconies for a palace or guild-hall feel.

### Lecterns with books (capability A)

```
block_entity_set_nbt(pos, nbt='{Book:{id:"minecraft:written_book",count:1,
  components:{"minecraft:written_book_content":{title:"Field Notes",
  author:"Archivist",pages:["\"The first record of this place..\"",
  "\"...continues on the second leaf.\""]}},Page:0}')
```

Use in libraries, scriptoria, and museum display cases. The lectern must be
placed first; the NBT merge writes the book into it.

### Decorated pots (capability A)

```
block_entity_set_nbt(pos, nbt='{sherds:["minecraft:brick",
  "minecraft:angler_pottery_sherd","minecraft:brick",
  "minecraft:archer_pottery_sherd"]}')
```

Four faces — cycle sherd IDs to match the room's theme (explorer, warrior,
scholar, etc.). Good for corridor niches and altar pieces.

### Player-head skulls as signage / decor (capability A)

Place `minecraft:player_head`, then:

```
block_entity_set_nbt(pos, nbt='{profile:"Notch"}')
```

Or supply a custom base64 texture for a fully unique head. Use as
architectural ornament (gargoyles, corbels, trophy mounts) or nameplates on
display cases.

### Item frames and paintings (capability C — entity NBT)

Item frames and glow item frames are entities, not block entities; set their
content via `entity_summon` with NBT or `entity_set_nbt` after the fact:

```
entity_summon("minecraft:glow_item_frame", pos, nbt='{Facing:1,
  Item:{id:"minecraft:diamond_sword",count:1},ItemRotation:0,Invisible:0b}')
```

`Facing`: 0=down, 1=up, 2=north, 3=south, 4=west, 5=east. Invisible frames
with displayed items give flush wall-art. See §C of the enhancement spec for
painting `variant` and armor-stand pose NBT.

### Named and enchanted display items via components (capability B)

`inventory_set_slot` and `player_give_item` accept a `components` SNBT string
that names, enchants, or adds lore to any item — ideal for museum pieces,
trophy rooms, and prestigious libraries:

```
inventory_set_slot(container_pos, slot=13, item={
  id:"minecraft:diamond_sword", count:1,
  components:'{"minecraft:custom_name":"{\"text\":\"Blade of the Keeper\",
    \"italic\":false,\"color\":\"aqua\"}",
    "minecraft:lore":["\"Recovered from the deep vault\""],
    "minecraft:enchantments":{"minecraft:sharpness":5,
      "minecraft:unbreaking":3}}'})
```

**Version note:** the `minecraft:enchantments` component shape changed between
1.20.5 and 1.21. Verify the exact SNBT with a round-trip read
(`itemstack_describe` or give-then-read) against the running server version
(`server_get_status`).

Useful components for interiors:
- `minecraft:custom_name` — named artefact on a pedestal.
- `minecraft:lore` — flavour text for a museum card.
- `minecraft:dyed_color` (`{rgb:…}`) — custom-colour leather armour on a
  display stand.
- `minecraft:written_book_content` — a completed book placed directly into a
  chest or lectern slot.

### Seeding library and treasure chests with loot tables (capability E)

Use `loot_table_generate` to get a realistic item list, then place the results
with `inventory_set_slot`:

```
# 1. Generate loot (returns an item list)
items = loot_table_generate("minecraft:chests/stronghold_library")

# 2. Place each item into the chest (chest placed at pos)
for slot, item in enumerate(items):
    inventory_set_slot(pos, slot=slot, item=item)
```

Useful vanilla table IDs (enumerate all with `loot_table_list`):
- `minecraft:chests/stronghold_library` — books, enchanted books, paper.
- `minecraft:chests/village/village_weaponsmith` — weapons, ingots, obsidian.
- `minecraft:chests/simple_dungeon` — saddles, enchanted gear, records.
- `minecraft:chests/shipwreck_treasure` — emeralds, diamonds, iron.
- `minecraft:chests/abandoned_mineshaft` — rails, torches, tools.

Loot-seeded chests feel immediately lived-in and read as authentic exploration
spaces — a library with books already on its shelves, a treasury with real
treasure. Combine with named items (capability B) to add one or two hero
artefacts to an otherwise loot-seeded chest.
