# Functional systems & Java mechanics

The working systems a base may include — and the **Java-Edition rules** that
govern them. Mechanics here are current as of Java 1.21.x; re-check after a
game update.

## Java redstone — key behaviours

- **Quasi-connectivity (QC) exists.** Pistons, dispensers, and droppers can be
  powered by a signal directed at the block *above* them. This is intentional
  Java behaviour; use it if helpful, but be explicit about it in plans so the
  `engineer` knows.
- **Observers output a 1-redstone-tick (2-game-tick) pulse.** Java observer
  timing is stable and matches standard tutorials.
- **0-tick pulses were patched out** (long before 1.21). Do not rely on them.
- **`block_set_state` placement notifies neighbours** (update flags default to
  3: notify + sync), so placed redstone dust, comparators, and repeaters
  receive neighbour updates and most simple clocks self-start. Verify the
  contraption is actually ticking — some loops still need an initial trigger.
- **AFK fishing works on Java** — the standard tripwire-and-trapdoor AFK
  fishing farm is valid. Note it depends on the world not pausing (a player
  must be in range).
- **Hopper transfer order is deterministic on Java** (first filled slot). Item
  sorters work reliably; the common "stacked" design uses **22** filler items
  in the filter chest (not 20 or 21).
- If a redstone design is complex, defer the contraption to `engineer` and
  provide the footprint and input/output points.

## Storage & item handling

- **Auto-smelter** — a bank of hopper-fed furnaces/smokers/blast furnaces with
  a separate fuel feed. Works on Java.
- **Item sorter** — works; needs the overflow buffer above. Filter chests over
  a hopper line keyed to each item.
- **Crafter (1.21)** — the `crafter` block enables automated crafting; pair
  with a redstone pulse and a hopper feed.

## Power & food farms

- **Iron farm** — Java golem spawning requires a valid village: **≥3 villagers
  with beds and workstations, all having slept and worked.** The standard
  Java design uses 3–10 villagers in a detection cell; golems spawn within
  ~8 blocks of the village centre. The Java threshold is lower than in other
  editions — 3 villagers with beds and workstations is enough to start.
- **Mob farm** — hostile mobs spawn in a spherical shell ~24–128 blocks from
  the player (simulation distance 10 default). A dark spawning chamber with
  water-funnel collection works well. Use `/gamerule` to tune `mobSpawning`
  if needed.
- **Crop farms** — kelp, bamboo, sugarcane, cactus, and tree farms all work;
  observer- or piston-based harvest is standard. On Java, QC-based designs
  are also valid.

## Enchanting

The **15-bookshelf** setup gives the level-30 ceiling. Bookshelves must sit
exactly **2 blocks laterally** from the enchanting table, on the same level or
one block higher, and the **2-high gap between shelf and table must be empty**
— a torch, carpet, or snow layer in that gap zeros that shelf's contribution.
The standard form is a 5×5 ring of shelves around the table with the gap kept
clear.

## Beacon

A full **4-tier pyramid is 164 mineral blocks** (81 + 49 + 25 + 9 — 9×9, 7×7,
5×5, 3×3). Iron blocks are the cheapest valid material. The beacon needs a
clear vertical line of sight to the sky — leave an open shaft or a glass
column above it. Only a tier-4 pyramid unlocks the secondary effect.

## Conduit

A **16-block minimum** prismarine / sea-lantern frame activates a conduit; the
full **42-block** frame maximizes its range. Valid frame blocks: prismarine,
dark prismarine, prismarine bricks, sea lanterns — **slabs, stairs, and walls
of those do not count.**

## Other systems

Auto-brewing (dispenser-fed brewing-stand chain), XP storage (a bottling or
furnace-XP store), an ender-chest network across rooms, a lodestone array for
compasses, daylight-sensor auto-lighting, and sculk-sensor or
pressure-plate-triggered doors. For each, give the planner a footprint and a
material list. Note that sculk sensors are available in 1.19+ and calibrated
sculk sensors in 1.20+; they work reliably on Java Edition.

## For the plan

Every utility a base includes becomes rooms and steps in `plan.toon`. Give the
`planner`/`worker` a concrete block list and footprint — never "add a farm
here" without the dimensions. A redstone clock or always-loaded contraption
should carry a brief lag warning for the user.

---

## Java-exclusive: labeled storage and seeded starter chests

### Labeling barrels and chests with signs (capability A)

Place a `*_sign` adjacent to each container, then write its label with
`block_entity_set_nbt`:

```
block_entity_set_nbt(pos, nbt='{front_text:{messages:[
  "{\"text\":\"ORES\",\"color\":\"yellow\",\"bold\":true}",
  "{\"text\":\"coal / iron / gold / diamond\"}", "\"\"", "\"\""],
  has_glowing_text:0b}, is_waxed:1b}')
```

This is faster and more reliable than placing item-frame labels, and the text
is readable from further away. `is_waxed:1b` prevents accidental edits.

### Seeding starter chests with loot tables (capability E)

Use `loot_table_generate` to fill a starting chest with believable contents,
then place the items with `inventory_set_slot`:

```
# 1. Generate a realistic starter loot list
items = loot_table_generate("minecraft:chests/village/village_weaponsmith")

# 2. Write each item into the chest at pos
for slot, item in enumerate(items):
    inventory_set_slot(pos, slot=slot, item=item)
```

Useful table IDs for a player home (enumerate all with `loot_table_list`):
- `minecraft:chests/village/village_weaponsmith` — starter weapons and ingots.
- `minecraft:chests/village/village_toolsmith` — pickaxes, axes, shovels.
- `minecraft:chests/village/village_fletcher` — bows, arrows, flint.
- `minecraft:chests/simple_dungeon` — saddles, records, enchanted gear.

Combine loot seeding with component-named hero items (see `interiors.md`
§ "Java-exclusive") to add one named tool or weapon among otherwise random
loot — the named item stands out immediately.

### Named and enchanted tools in the storage room (capability B)

For a storage room's dedicated tool wall or tool chest, use `inventory_set_slot`
with `components` to pre-place a named, enchanted kit:

```
inventory_set_slot(container_pos, slot=0, item={
  id:"minecraft:netherite_axe", count:1,
  components:'{"minecraft:custom_name":"{\"text\":\"Woodsman\",
    \"italic\":false}",
    "minecraft:enchantments":{"minecraft:efficiency":5,
      "minecraft:unbreaking":3,"minecraft:mending":1}}'})
```

**Version note:** the `minecraft:enchantments` component shape changed between
1.20.5 and 1.21. Verify with a round-trip read on the running server version
(`server_get_status`) before finalising the SNBT in `plan.toon`.
