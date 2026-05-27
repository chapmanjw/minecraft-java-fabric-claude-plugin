# Verification and correction

A contraption built correctly block-for-block can still not *work*. Every
design ships a **functional test recipe**; the `inspector` runs it; when it
fails, you diagnose and correct. This file is how.

## Authoring an inspection recipe

Write the recipe to `.minecraft-builder/<project>/inspection-recipe.toon`. A
test is a sequence of **trigger → wait → sample**:

- **trigger** — apply an input. The `inspector` does this with `command_execute`
  / `block_set_state` — e.g. place a `minecraft:redstone_block` at a button
  position then set it back to `minecraft:air` — or `inventory_set_slot` /
  `player_give_item` to load a stack into an input container.
- **wait** — hold for the design's **timing budget** plus slack (the worst-case
  deterministic path from `design-patterns.md`).
- **sample** — read the result: `block_get_state` for a block state (a door
  block now `minecraft:air`, a piston `[extended=true]`, a comparator powered),
  `block_scan_region` for a region, `inventory_get` / `inventory_count_items`
  for container contents, `entity_get` / `entity_query` for collected drops.
  Use `scoreboard_*` to count events over time (e.g. items processed).
- **expect** — the value a working contraption produces.

```toon
test: jeb-door-2x2
steps[4]{action,target,detail}:
  trigger,{x:4,y:64,z:0},place stone_button powered then release
  wait,,20 game ticks
  sample,{x:4,y:64,z:2},expect air at all 4 door-block coords
  sample,{x:4,y:64,z:2},after 20 more ticks expect the door self-closed
```

Give every contraption a test — even a "trivial" one. The whole point of the
inspector loop is to confirm the machine actually runs: that a clock is
oscillating, a chunk is ticking, and timing landed where the budget said.

## Java-exclusive: event-based functional verification

Sampling block state is a snapshot — it can miss a mechanism that fired and
reset between reads. Java exposes a **real feedback channel** Bedrock's MCP did
not: subscribe to world events, trigger, then drain them.

- **`events_subscribe(event_types, filters?)`** → a `subscription_id`. Useful
  types: `block.use` (a button/lever/door interacted), `block.place` /
  `block.break`, `container.open` / `container.close`, `entity.death`,
  `player.chat`. Narrow with `filters` (e.g. an area or entity type) to avoid
  noise.
- **`events_poll(subscription_id)`** drains the events captured since the last
  poll.
- **`events_unsubscribe`** when done so the subscription doesn't accumulate.

The flow is **subscribe → trigger → wait → poll → expect events**, a complement
to the snapshot `sample` step rather than a replacement. It confirms the
mechanism *fired*, not just that geometry ended up in some state:

```toon
test: mob-farm-is-killing
steps[4]{action,target,detail}:
  subscribe,,events_subscribe(["entity.death"]) over the kill chute → sub_id
  wait,,600 game ticks
  poll,,events_poll(sub_id) expect ≥1 entity.death of the farmed mob
  sample,{x:10,y:62,z:8},and the collection chest holds drops
```

Where it earns its place:

- **Mob farm / collector** — `entity.death` events prove the kill chamber is
  actually killing, even if the chest is briefly empty between hopper pulls.
- **Door / button / trap** — `block.use` confirms a player (or a redstone-driven
  interaction) triggered it; pair with the door-block `sample`.
- **Sorter / storage** — `container.open` / `container.close` and item movement
  confirm the right chest received the stream.
- **Interactive builds** — watch `player.chat` or `block.use` to drive a build
  that responds to the user in real time.

Not a substitute for sampling geometry (it can't read a static block state), but
a genuine signal that a mechanism is firing under load. Event payload shapes are
version-sensitive — confirm against the running version (`server_get_status`)
with one `events_subscribe` / trigger / `events_poll` round trip before relying
on a specific field.

## Per-type test contracts

| Contraption | Trigger | Sample after wait | Pass criterion |
| ----------- | ------- | ----------------- | -------------- |
| Door | power the button position | door-block coords | all become `minecraft:air`; self-closes |
| Sorter | put a stack of the target item in the input | output and overflow chests | target item only in its row; others empty |
| Mob farm | spawn the mob in the spawn box, or wait a cycle | collection chest | drops arrive within the expected rate |
| Clock | apply the enable signal | a target coord, sampled repeatedly | oscillation period within ±1 tick of plan |
| Minecart | **clear stray entities** (`kill @e[type=minecart]` + stray mobs), then place a test cart at the start | detector rails along the route | rails fire in order, ETAs within ~2 ticks; no mid-route stall |
| Elevator | place an entity at the base | a coord at the top | entity arrives within the budgeted time |
| Music | trigger the sequencer | the note-block coords | each pulses in sequence |

## Correction catalog — symptom → diagnosis → fix

When the inspector reports a failure, diagnose with this table and emit
corrected steps:

| Symptom | Diagnosis | Fix |
| ------- | --------- | --- |
| Clock / loop is static at the first sample | Edge-balanced loop never toggled, placement order, or the chunk isn't ticking | Apply the one-tick nudge (place `minecraft:redstone_block` adjacent, then set `minecraft:air`); confirm the chunk is loaded/force-loaded; re-sample |
| Piston never extends, though redstone next to it is powered | The circuit assumed a QC power position the build didn't actually create, or the power face is wrong | Verify the QC/direct-power face matches the design; move power to the intended block and re-test |
| Sorter leaks the target item, or sorts into the wrong row | Wrong filler-item count for the sorter variant, or filter rows interfering | Set the filler count exactly per the cited Java sorter design (typically 18 in the filter slot); add a 1-block isolation gap between rows |
| Hopper not pulling | The hopper is powered (locked) by a stray signal | Find and insulate the stray redstone — often a torch on an adjacent block |
| Filter hopper skips matching items | A non-matching item is in its collection range | Re-route the item stream so matching items arrive alone |
| Timing path lands a tick early/late | Repeater delays not summed to the design budget | Re-check the deterministic timing budget; adjust repeater delays so paths align |
| Mob farm: zero spawns | Spawn surface too bright, or outside the spawn shell | Re-check light level (block-light 0 for hostiles on modern Java) and the ~24–128-block shell at the world's simulation distance |
| Powered rail does not propel the cart | On this mod a `redstone_block` underneath does **not** compute/hold the rail's power, and `block_fill_batch` fires no neighbor update — so the rail lands `powered=false` and acts as a **brake** | Set `powered=true` **explicitly** via `block_set_state` (default update_flags 3) on each powered rail; don't rely on an underneath redstone source or a batch fill. Respect the ~1-per-30–38 spacing |
| Cart dead-stops partway along a working route | A **stray entity** is sitting on the rail — a stalled earlier test cart, or an ejected/spawned mob (a pig, etc.). The #1 false "broken rail" | `kill @e[type=minecart]` AND stray mobs (`@e[type=pig]`, …) along the route **before and after** every ride test, then re-test |
| Door corner does not move | A stuck piston, or a missed power/timing connection | Free the piston / clear obstruction; verify the corner's power and timing against the design |
| Iron-golem / villager farm rate low | A village-mechanics problem, not engineering | Hand the village half back to `village-planner` |

After a fix, the `worker` applies the corrected steps and the `inspector`
re-runs the test. Loop until it passes — a contraption is not done until its
functional test passes.
