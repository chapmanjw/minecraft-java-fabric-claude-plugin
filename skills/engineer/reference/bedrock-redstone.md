# Bedrock redstone fundamentals

Bedrock redstone is **materially different from Java**, and most tutorials,
videos, and wiki diagrams are written for Java. This file is the translation
layer. Mechanics current as of Bedrock 1.21.x — re-check after a game update.

## The differences that break Java designs

- **No quasi-connectivity (QC).** A Bedrock piston is powered only when
  *directly* powered — never from "one block above" the way Java allows. Most
  Java piston doors, BUD switches, and many flying machines and TNT cannons
  silently fail on Bedrock. This is Mojang's standing policy: the two editions'
  redstone systems are functionally different and will stay that way.
- **Fixed 2-game-tick piston start delay.** A Bedrock piston starts to extend
  or retract 2 game ticks (0.1 s) after it is activated — always. Java pistons
  can have a 0- or 1-tick delay depending on the power source; Java circuits
  that rely on that timing do not port.
- **Buggy observer pulses.** A Bedrock observer pulse is nominally 1 redstone
  tick but is **sometimes delayed by 4 or 6 game ticks** (MCPE-15793, and
  timing can also be off via MCPE-73342). Long observer chains drift — design
  in explicit repeater retiming to absorb it.
- **No 0-tick pulses, no TNT duping.** Both are Java-only and structurally
  impossible on vanilla Bedrock. Any design that needs them is out.

## The Java-only ban list — refuse these at verification

Reject and re-design any contraption that depends on:

- **Quasi-connectivity** — piston powered from a non-adjacent block.
- **0-tick pulses** — Java sugar-cane 0-tick farms, Java mini-piston circuits.
- **BUD switches** (block-update detector via QC) — use an observer instead.
- **TNT duping** — coral/flying-machine duplication.
- **Instant-retracting pistons** / Java sticky-piston "block dropping".
- **Java 3×3 piston doors that depend on QC repeaters** — use a Bedrock-vetted
  observer-driven variant.

When you reject one, tell the user *why* and give the Bedrock-correct
substitute.

## Timing reference

| Quantity | Bedrock value |
| -------- | ------------- |
| Game tick | 0.05 s |
| Redstone tick | 2 game ticks (0.1 s) |
| Piston start delay | 2 game ticks, fixed |
| Piston extend / retract | 2 game ticks each |
| Observer pulse | 1 rs tick nominal — 2–3 rs ticks under MCPE-15793 / 73342 |
| Hopper transfer | 1 item per 8 game ticks (2.5 items/s) |
| Hopper item-collection cooldown | extra 8 game ticks after picking up a dropped item |
| Hopper-sorter filler items | **20** (Bedrock), not 21 |
| Minecart top speed | 8 m/s straight, 11.314 m/s diagonal |
| Powered-rail flat spacing | 1 powered rail per ~38 blocks (occupied cart); 3 in a row launch from rest |
| Note block | 25 pitches (F♯3–F♯5), 16 instruments set by the block underneath |
| Bubble column (soul sand, up) | ~8 m/s on Bedrock (Java is ~11) |
| Bubble column (magma, down) | ~4.9 m/s |
| Hostile-mob light gate | spawns at light level 0–7 |
| Animal light gate | spawns at light level 7+ (Java needs 9+) |
| Mob-spawn shell | a *spherical* shell ~24–44 blocks from the player at simulation distance 4 |

## Other Bedrock facts to design around

- **No `/random`, no `/data`.** Randomness comes from a scoreboard random
  objective or dropper randomness; there is no NBT command editing.
- **Hopper filter quirk** — at full load a hopper pipe can skip a small
  fraction of items past filters, and any non-matching item in a filter
  hopper's collection range can block it from collecting a matching item.
  Design item streams so matching items arrive alone.
- **Iron golem spawn volume** is 17×13×17 around the village center — but the
  *village* (20 beds, 10 villagers, the work rules) is `village-planner`'s job;
  you build only the farm hardware.
- **AFK fishing is broken on Bedrock by design** — do not design it.
- **Simulation distance** is a per-world setting (often 4 on consoles, up to 12
  on PC). Mob-farm spawn rates depend on it — ask for it at interview time.
