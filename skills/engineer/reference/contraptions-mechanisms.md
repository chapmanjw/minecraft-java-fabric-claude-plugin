# Catalog — doors, transport, music, and machines

Mechanisms and experiential builds. Each entry: what it is, the Java-specific
points, a footprint hint.

## Piston and hidden doors

Java piston doors can use **quasi-connectivity** (a piston powered from the
block one above), so the standard Java tutorial designs apply directly — pick a
catalog variant or compose one from `design-patterns.md`. Document where a door
relies on QC so verification accounts for it.

- **1×2 piston door** — the simplest; a button or pressure plate drives two
  pistons. Reliable.
- **2×2 "jeb" door** — the classic Java diagonal-pulse design; observers or QC
  repeaters drive the four corner pistons. Java timing is deterministic, so the
  pulse lengths port faithfully — budget repeater delays per the source design.
- **3×3 piston door** — use a standard Java QC- or observer-driven design; these
  are well-documented and reliable on Java.
- **Hidden doors** — a sliding bookshelf or fireplace, a staircase that pistons
  away, a painting-covered entry — for a player base, coordinate the façade with
  `player-house`.
- **Vault / combination door** — multiple levers or a keypad gating the open
  signal via an AND of the inputs.

## Transport

- **Water elevator (up)** — a soul-sand bubble column in a kelp-or-waterlogged
  shaft lifts entities upward. (Verify the exact lift speed on the running
  version.)
- **Drop elevator (down)** — a magma-block column pulls entities down. (Verify
  the exact descent speed on the running version.)
- **Minecart networks** — powered rails at ~1 per 30–38 blocks on the flat to
  hold an occupied cart near the 8 m/s top speed; 1–3 powered rails in a row
  launch a cart from rest. Add junction switches, boost stations, and
  auto-loaders/unloaders at stops.
- **Roller coasters** — scenic minecart routes; top speed ~8 m/s straight,
  faster diagonal. Plan grades, curves, and an auto-return so the cart comes
  back to the station.
- **Ice roads** — packed/blue-ice lanes for fast boat travel (blue ice is
  fastest).

## Note-block music

- A note block has **25 pitches (F♯3–F♯5)** and **16 instruments**, the
  instrument set by the block placed *underneath* it. Plan the block palette
  under the note blocks for the instrumentation.
- **Playable keyboard** — note blocks on buttons or pressure plates, one per
  pitch.
- **Sequencer** — a repeater or piston-tape line steps a redstone pulse past
  note blocks in time; a minecart on powered rail past a row of note blocks is a
  simple, reliable player. For tight timing, a redstone-clock-driven sequencer
  is precise on Java's deterministic ticks.
- Tempo is quantized to redstone ticks — write the timing in ticks.

## Decorative redstone

Analog and digital clocks, a 7-segment digital display, traffic lights, a
redstone fountain (pistons pushing water), a note-block-synced light show.
Decorative machines still get a functional test — the lights must actually
cycle.

## Defensive

- **TNT cannon** — single-shot, short-burst, or a Java-style charged cannon.
  Java QC-timed propellant designs work here; build a documented Java cannon and
  budget the propellant timing precisely. Do **not** rely on duping for ammo.
- **Arrow turret** — a dispenser fired by a tripwire or observer trigger.
- **Traps** — a pitfall (pistons or trapdoors drop the floor), a lava blade, a
  drowning or fall chamber, a mob arena.

Defensive builds near a settlement must not seal it — see the `village-planner`
raid rules.

## Java-exclusive: ship the mechanism pre-loaded (block-entity NBT)

Bedrock's MCP couldn't set block-entity contents; Java can, so a contraption can
**arrive loaded and ready** instead of needing the user to hand-fill it.
Pre-load any dispenser, dropper, or hopper with exact contents — either with
`inventory_set_slot` (cleaner, slot-by-slot) or `block_entity_set_nbt` with an
`Items` list:

```
block_entity_set_nbt(pos, nbt='{Items:[
  {slot:0,id:"minecraft:arrow",count:64},
  {slot:1,id:"minecraft:arrow",count:64}]}')
```

Targets that matter for mechanisms:

- **Arrow turret** — pre-fill its dispenser with arrows (or fireworks / fire
  charges) so it fires the moment its trigger fires.
- **TNT cannon** — load the propellant dispensers (and the loading dropper) so
  the cannon is charged on arrival; still budget the propellant *timing* in
  redstone, only the *ammo* is pre-loaded.
- **Auto-brewer / dispenser chains** — seed the dispensers with potions,
  ingredients, or splash items.
- **Note-block / show machines** — pre-load any dropper-fed staging container.

For a **spawner-driven** mechanism, configure the `minecraft:spawner` block
entity directly — entity, count, range, delays — so it ships working:

```
block_entity_set_nbt(pos, nbt='{SpawnData:{entity:{id:"minecraft:zombie"}},
  SpawnCount:4,MaxNearbyEntities:6,RequiredPlayerRange:16,SpawnRange:4,
  MinSpawnDelay:200,MaxSpawnDelay:800}')
```

Verify the merge by reading it back with `block_entity_get_nbt` (or
`block_get_state`, which includes `blockEntityNbt`). The container/spawner SNBT
shape is version-sensitive — on 1.20.5+ item entries use the components system —
so do a round-trip read on the running version (`server_get_status` for the
version) rather than trusting a literal blindly.

## Always

Whatever the mechanism, it ships with a functional test recipe
(`verification.md`) — a door is not done until a trigger opens it and a wait
confirms it self-closes.
