# Catalog — sorters, collectors, and farms

The production machines. Each entry: what it is, the Java-specific points, and a
footprint hint. Confirm rates and version-sensitive figures against current Java
sources (`community-sources.md`) for anything not standard.

## Item sorters

- **Basic 1-row hopper sorter** — one item type, one output. A filter hopper
  holds **18 filler items** spread one per slot (5 slots filled with stacks +
  the remaining configuration that leaves room for exactly one extra of the
  target item); a comparator reads the filter hopper and a redstone-torch
  inverter locks the output hopper. The standard Java sorter uses the
  comparator-overflow trick — confirm the filler count against the specific
  sorter design you cite, since variants differ. Footprint ~1×5×4, tileable.
- **Multi-row universal sorter** — one row per item type, side by side. Space
  filter rows so a neighbouring row's comparator cannot misread; add a 1-block
  isolation gap if rows interfere.
- **Overflow protection** — route unfiltered items to a labelled overflow chest
  (or a lava trash can) so a backed-up sorter does not jam the input.
- **Compactor** — auto-crafts 9 ingots → a block (or reverses it). On 1.21+ the
  vanilla **`minecraft:crafter`** (auto-crafting block, observer- or
  comparator-triggered) is the clean way; a hopper-into-a-crafter feed is the
  modern Java compactor. Verify the Crafter is available on the running version.

## Mob-spawner collectors

- **Drop-tube collector** — for a dungeon spawner: a dark water-flow platform
  funnels mobs into a 1-wide drop column; fall damage or a chute brings them to
  a hopper floor under the collection chest. Light only *outside* the spawn box.
  Footprint compact, vertical.
- **XP / drops split** — a switchable floor lets the player either collect drops
  via hoppers or take XP and the kill themselves.

## Mob farms

- **General mob farm** — a dark spawning platform within the spherical spawn
  shell (~24–128 blocks from an AFK spot, outside 24 and inside the simulation
  distance); water streams funnel mobs to a kill chute and a hopper collector.
  Rate scales with simulation distance — design to the world's setting. Modern
  Java spawns hostiles at block-light level 0, so the platform must be fully
  dark.
- **Specific spawners** — zombie / skeleton / cave-spider / blaze XP farms off a
  natural spawner; drowned, guardian (ocean monument), witch hut; enderman
  platform in the End; slime-chunk farm.
- **Iron / villager farms** — you build the spawn platform, water funnel, kill
  chute, and hopper collector; **`village-planner` builds the village** (beds,
  villagers, the spawn rules that produce iron golems). Hand off the village
  half.

## Crop farms

- **Observer-piston harvester** — an observer watches a crop block; when it
  matures the observer fires a piston that breaks it; water carries the drop to
  a hopper line. The pattern covers sugar cane, bamboo, kelp, cactus,
  pumpkin/melon, sweet berries, nether wart, cocoa. (Use this for sugar cane —
  do **not** rely on patched-out 0-tick harvesting.)
- **Tilled-crop farms** (wheat, carrot, potato, beetroot) — usually a villager
  farmer harvests and a hopper minecart collects; coordinate the villager with
  `village-planner`.
- **Tree farms** — observer-piston harvested per species; on Java a dispenser of
  bone meal plus a saw/piston line is a common automatic design.
- **Animal farms** — breeders and cookers (a hopper-fed egg thrower, a lava or
  campfire cooker) for chicken, cow, pig, sheep.

## Auto-processing

- **Auto-smelter** — a furnace bank fed by an input hopper, a separate fuel
  hopper, and an output hopper to a chest. Three furnaces in parallel ≈ 18
  items/min. Furnaces keep smelting XP until the player collects the output — a
  useful XP source. Add overflow protection if input can outpace smelting.
- **Auto-brewer** — dispenser-fed brewing stands in a chain.

## Java-exclusive: ship a farm pre-configured (block-entity NBT)

Bedrock's MCP couldn't set block-entity contents; Java can, so a farm can
**arrive configured and loaded** rather than requiring the user to set it up:

- **Mob-spawner farms** — configure a placed `minecraft:spawner` directly so the
  build ships a working, tuned spawner instead of relying on a found one:
  ```
  block_entity_set_nbt(pos, nbt='{SpawnData:{entity:{id:"minecraft:zombie"}},
    SpawnCount:4,MaxNearbyEntities:6,RequiredPlayerRange:16,SpawnRange:4,
    MinSpawnDelay:200,MaxSpawnDelay:800}')
  ```
  Set `SpawnData`, `SpawnCount`, `MaxNearbyEntities`, `RequiredPlayerRange`,
  `SpawnRange`, and the delay bounds to match the collector's throughput.
- **Auto-smelter / auto-brewer** — pre-load the **fuel hopper** (coal/blast
  fuel) and seed input/output hoppers via `inventory_set_slot` or an `Items`
  list, so the bank starts smelting/brewing immediately.
- **Tree / animal farms** — pre-fill the bone-meal dispenser or the breeder's
  feed dropper so the farm runs on first tick.

Use `inventory_set_slot` (cleaner, slot-by-slot) or `block_entity_set_nbt` with
an `Items:[{slot:0,id:"minecraft:coal",count:64}]` list. Read it back with
`block_entity_get_nbt` to confirm the merge. The container/spawner SNBT shape is
version-sensitive (1.20.5+ uses the item-components system) — round-trip it on
the running version (`server_get_status`) rather than trusting a literal blindly.

## Throughput budgeting

A hopper moves 2.5 items/s. If several harvested streams converge on one sorter
row faster than that, the row backs up — run rows in parallel or widen the pipe.
State the expected throughput and check it against the hopper rate in the
design.
