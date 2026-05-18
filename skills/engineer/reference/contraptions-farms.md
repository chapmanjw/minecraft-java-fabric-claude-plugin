# Catalog — sorters, collectors, and farms

The production machines. Each entry: what it is, the Bedrock-specific points,
and a footprint hint. Confirm rates against current Bedrock sources
(`community-sources.md`) for anything not standard.

## Item sorters

- **Basic 1-row hopper sorter** — one item type, one output. A filter hopper
  holds **20 filler items** + 1 sample of the target item; a comparator reads
  the filter hopper and a torch inverts to lock the output hopper. **Use 20
  filler items on Bedrock, never 21** — 21 lets the filter run the single-item
  trough and leaks. Footprint ~1×5×4, tileable.
- **Multi-row universal sorter** — one row per item type, side by side. Space
  filter rows so a neighbouring row's comparator cannot misread; add a 1-block
  isolation gap if rows interfere.
- **Overflow protection** — route unfiltered items to a labelled overflow
  chest (or a lava trash can) so a backed-up sorter does not jam the input.
- **Compactor** — auto-crafts 9 ingots → a block (or reverses it) with a
  crafter or a hopper-into-crafting feed.

## Mob-spawner collectors

- **Drop-tube collector** — for a dungeon spawner: a dark water-flow platform
  funnels mobs into a 1-wide drop column; fall damage or a chute brings them
  to a hopper floor under the collection chest. Light only *outside* the
  spawn box. Footprint compact, vertical.
- **XP / drops split** — a switchable floor lets the player either collect
  drops via hoppers or take XP and the kill themselves.

## Mob farms

- **General mob farm** — a dark spawning platform within the spherical
  spawn shell (~24–44 blocks from an AFK spot at simulation distance 4); water
  streams funnel mobs to a kill chute and a hopper collector. Rate scales with
  simulation distance — design to the world's setting.
- **Specific spawners** — zombie / skeleton / cave-spider / blaze XP farms
  off a natural spawner; drowned, guardian (ocean monument), witch hut;
  enderman platform in the End; slime-chunk farm.
- **Iron / villager farms** — you build the spawn platform, water funnel,
  kill chute, and hopper collector; **`village-planner` builds the village**
  (the 17×13×17 spawn volume, beds, villagers). Hand off the village half.

## Crop farms

- **Observer-piston harvester** — an observer watches a crop block; when it
  matures the observer fires a piston that breaks it; water carries the drop
  to a hopper line. The pattern covers sugar cane, bamboo, kelp, cactus,
  pumpkin/melon, sweet berries, nether wart, cocoa.
- **Tilled-crop farms** (wheat, carrot, potato, beetroot) — usually a villager
  farmer harvests and a hopper minecart collects; coordinate the villager with
  `village-planner`.
- **Tree farms** — observer-piston or TNT-cleared, per species.
- **Animal farms** — breeders and cookers (a hopper-fed egg thrower, a lava
  or campfire cooker) for chicken, cow, pig, sheep.

## Auto-processing

- **Auto-smelter** — a furnace bank fed by an input hopper, a separate fuel
  hopper, and an output hopper to a chest. Three furnaces in parallel ≈ 18
  items/min. Furnaces keep smelting XP until the player collects the output —
  a useful XP source. Add overflow protection if input can outpace smelting.
- **Auto-brewer** — dispenser-fed brewing stands in a chain.

## Throughput budgeting

A hopper moves 2.5 items/s. If several harvested streams converge on one
sorter row faster than that, the row backs up — run rows in parallel or widen
the pipe. State the expected throughput and check it against the hopper rate
in the design.
