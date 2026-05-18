# Catalog — doors, transport, music, and machines

Mechanisms and experiential builds. Each entry: what it is, the
Bedrock-specific points, a footprint hint.

## Piston and hidden doors

All Java door designs that use quasi-connectivity fail on Bedrock — pick a
Bedrock-vetted variant or compose one from observers (`design-patterns.md`).

- **1×2 piston door** — the simplest; a button or pressure plate drives two
  pistons. Reliable on Bedrock.
- **2×2 "jeb" door** — the Bedrock variant is observer-driven, not QC; budget
  ~2 extra blocks of footprint per axis vs the Java version, and put a 2-tick
  repeater between observer pairs to absorb MCPE-15793 drift.
- **3×3 piston door** — use a Bedrock-compatible observer-driven design; never
  port a Java QC design.
- **Hidden doors** — a sliding bookshelf or fireplace, a staircase that pistons
  away, a painting-covered entry — for a player base, coordinate the façade
  with `player-house`.
- **Vault / combination door** — multiple levers or a keypad gating the open
  signal via an AND of the inputs.

## Transport

- **Water elevator (up)** — a soul-sand bubble column in a kelp-or-waterlogged
  shaft lifts entities at ~8 m/s on Bedrock.
- **Drop elevator (down)** — a magma-block column pulls down at ~4.9 m/s.
- **Minecart networks** — powered rails at ~1 per 38 blocks on the flat to
  hold an occupied cart at the 8 m/s top speed; 3 powered rails in a row
  launch a cart from rest. Add junction switches, boost stations, and
  auto-loaders/unloaders at stops.
- **Roller coasters** — scenic minecart routes; top speed 8 m/s straight,
  11.314 m/s diagonal. Plan grades, curves, and an auto-return so the cart
  comes back to the station.
- **Ice roads** — packed/blue-ice lanes for fast boat travel.

## Note-block music

- A note block has **25 pitches (F♯3–F♯5)** and **16 instruments**, the
  instrument set by the block placed *underneath* it. Plan the block palette
  under the note blocks for the instrumentation.
- **Playable keyboard** — note blocks on buttons or pressure plates, one per
  pitch.
- **Sequencer** — a repeater or piston-tape line steps a redstone pulse past
  note blocks in time; a minecart on powered rail past a row of note blocks is
  a simple, reliable Bedrock player.
- Tempo is quantized to redstone ticks — write the timing in ticks.

## Decorative redstone

Analog and digital clocks, a 7-segment digital display, traffic lights, a
redstone fountain (pistons pushing water), a note-block-synced light show.
Decorative machines still get a functional test — the lights must actually
cycle.

## Defensive

- **Basic TNT cannon** — a single-shot or short-burst launcher only; Java
  long-range precision cannons rely on QC propellant timing and do not port.
- **Arrow turret** — a dispenser fired by a tripwire or observer trigger.
- **Traps** — a pitfall (pistons or trapdoors drop the floor), a lava blade,
  a drowning or fall chamber, a mob arena.

Defensive builds near a settlement must not seal it — see the
`village-planner` raid rules.

## Always

Whatever the mechanism, it ships with a functional test recipe
(`verification.md`) — a door is not done until a trigger opens it and a wait
confirms it self-closes.
