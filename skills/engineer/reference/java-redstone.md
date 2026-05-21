# Java redstone fundamentals

Java redstone is deterministic and well-documented, and most tutorials, videos,
and wiki diagrams are written for Java — so they apply directly here. This file
is the reference layer. Mechanics current as of **Java 1.21.11 / 26.1.x** —
several behaviours are version-sensitive (flagged below); confirm the running
version with `server_get_status` and re-check after a game update.

## Java mechanics you can rely on

- **Quasi-connectivity (QC) exists.** A Java piston, dispenser, or dropper is
  powered not only by direct power but also by a power source in the block
  *diagonally up* / "one block above" — the classic QC behaviour. Most Java
  piston-door, BUD, and many flying-machine designs depend on it and work here.
  Use it deliberately; document where a circuit relies on it so verification can
  account for it.
- **Deterministic redstone timing.** Java redstone runs on redstone ticks of 2
  game ticks (0.1 s). Repeater and comparator delays, pulse lengths, and
  observer pulses are reproducible — circuits that depend on exact timing port
  faithfully from Java sources.
- **Observer pulses are a clean 1 redstone tick.** A Java observer emits a
  reliable 1-redstone-tick (2-game-tick) pulse when the block it watches
  changes. Long observer chains are stable — there is no edition-specific drift
  bug to design around. Still pad with repeaters when summing a long worst-case
  path.
- **Repeater locking and comparator subtract/compare modes** behave to the Java
  standard — repeater locking (a powered repeater into the side of another),
  comparator subtraction mode, and comparator measurement of container fullness
  all work as the wiki documents for Java.
- **BUD behaviour is achievable** — either with an observer (the clean modern
  way) or with a QC-driven block-update detector. Prefer the observer.

## Mechanics to NOT rely on — patched out or exploit-grade

Do not design around these; reject and re-design any contraption that needs
them:

- **0-tick pulses.** 0-tick piston and 0-tick farm tricks were **patched out of
  Java years ago** (the 0-tick piston behaviour was removed around 1.16). They
  are not a reliable modern-Java mechanic. Do not propose 0-tick sugar-cane
  farms or 0-tick mini-piston circuits — use an observer-piston harvester
  instead.
- **TNT duping / sand-and-gravel duping / rail duping.** These are **bugs /
  exploits**, not supported mechanics; they can be patched at any update and may
  be disabled on a server. Do not recommend duping as part of a reliable design.
  If a user explicitly asks, flag it as an exploit that may break, and offer a
  non-duping equivalent (e.g. a real cobblestone/stone generator + auto-miner
  for bulk blocks).
- **Anything that needs a client/server mod beyond the Fabric MCP mod itself**
  (carpet-style tweaks, fabric gameplay mods) — design for vanilla Java
  behaviour.

## Version-sensitive — verify against the running version

These are real Java mechanics, but their exact figures or availability move
between releases. State the assumption in the design and verify in-world:

- **The Crafter** (auto-crafting block) exists from 1.21 onward — fine on
  1.21.11, but confirm before making it load-bearing in a compactor.
- **Bubble-column and elevator speeds**, mob-spawn light thresholds, and
  iron-golem spawn volume are tuned across versions — see the timing table and
  re-check on the running version.
- **Trial spawners / vaults / the Mace** and other recent content shift between
  snapshots; verify availability before designing around them.

## Timing reference (Java)

| Quantity | Java value |
| -------- | ---------- |
| Game tick | 0.05 s (20/s) |
| Redstone tick | 2 game ticks (0.1 s) |
| Repeater delay | 1–4 redstone ticks, selectable (2–8 game ticks) |
| Piston activation | near-instant when directly powered; movement ~1.5 game ticks |
| Observer pulse | a clean 1 redstone tick (2 game ticks) |
| Hopper transfer | 1 item per 8 game ticks (2.5 items/s) |
| Hopper item-collection cooldown | extra 8 game ticks after picking up a dropped item |
| Hopper-sorter filler items | **18** in each filter slot of the standard Java sorter (see sorter note) |
| Minecart top speed | 8 m/s straight; faster diagonal |
| Powered-rail flat spacing | ~1 powered rail per 30–38 blocks for an occupied cart; 1–3 in a row launch from rest |
| Note block | 25 pitches (F♯3–F♯5), 16 instruments set by the block underneath |
| Bubble column (soul sand, up) / (magma, down) | soul sand lifts, magma pulls down — verify exact m/s on the running version |
| Hostile-mob light gate | spawns at block-light level 0 (modern Java) — design for full darkness |
| Animal light gate | spawns on grass at light level 9+ |
| Mob-spawn shell | spherical shell ~24–128 blocks from the player; outside 24, inside the simulation distance |

> Flagged for review: the exact bubble-column m/s figures and the modern
> hostile-spawn light threshold (block-light 0 vs the older 0–7 range) are
> version-sensitive — verify on the running 1.21.11 world rather than quoting a
> figure blind.

## Other Java facts to design around

- **Java has `/data` and rich command/predicate tooling.** Java supports NBT
  command editing (`/data`, available via `block_entity_get_nbt` /
  `block_entity_set_nbt` / `entity_get_nbt` / `entity_set_nbt`) plus loot tables
  and predicates. Use them for setup and verification — but a *contraption
  itself* should still run on vanilla redstone so it works without command
  intervention.
- **Randomness** — the vanilla-redstone RNG is a dropper holding several items;
  it ejects one at random and a hopper/comparator reads which slot emptied. For
  command-driven randomness you may also use `loot_table_generate` or a
  scoreboard, but prefer in-world dropper RNG for a self-contained machine.
- **Hopper filtering** behaves to the Java standard — comparator-read filter
  hoppers are reliable; design item streams so matching items reach the right
  filter slot.
- **Iron golem spawning** depends on the village (beds, villagers, the spawn
  volume) — that is `village-planner`'s job; you build only the farm hardware
  (spawn platform, water funnel, kill chute, hopper collector).
- **Simulation distance** is a server setting that gates which chunks tick and
  how far mob farms spawn; ask for it at interview time for any mob farm. Work
  near a player or a force-loaded / ticking chunk — unloaded chunks don't tick,
  so a clock built in one will sit dormant until the chunk loads.
- **AFK fishing works on Java** (a clock-triggered fishing-rod-use farm). It is
  a valid Java design — but note many servers discourage or patch AFK farms, so
  verify the server permits it before recommending it.
