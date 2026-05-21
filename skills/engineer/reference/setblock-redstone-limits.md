# block_set_state-placed redstone — what self-starts, what needs a trigger

The agent places blocks via MCP tools (`block_set_state`, `block_fill_region`,
`block_clone_region`, `structure_load_to_world`). On Java, **`block_set_state`
defaults to update flags `3` (notify + sync)** — so a placed block sends
neighbour updates just like a player-placed block. That means most redstone the
agent builds receives the block updates it needs and **most clocks self-start**.

This is materially better than a parity-limited edition where setblock-style
placement suppresses block updates and every closed loop needs a manual kick.
On Java you usually do not. But three real conditions can still leave a
contraption dormant — surface them in the inspection report rather than assuming
everything ran:

1. **Unloaded / non-ticking chunks don't tick.** Redstone, hoppers, and
   observers in a chunk that isn't loaded and ticking simply pause. A clock
   built far from any player and outside a force-loaded / ticking area will sit
   idle until the chunk loads. Build near a player or a ticking chunk, or
   force-load it.

   **Loaded ≠ ticking — the idle single-player trap.** Force-loading keeps a
   chunk *loaded*, but on a single-player integrated server the game loop only
   advances while the session is active. An idle or unfocused client (an
   unattended overnight build, a minimised window) **pauses the scheduled
   block-tick queue** — even in a force-loaded chunk. The dividing line,
   observed empirically:
   - **Immediate updates still resolve** when something pokes the world (a tool
     call, a player action): levers, redstone dust/torch power, observer→observer
     pulses, redstone-lamp turn-*on*, door/trapdoor/fence-gate toggles.
   - **Anything on the scheduled-tick queue freezes:** piston extend/retract,
     hopper/dropper item transfer, comparator container re-reads, repeater and
     redstone-lamp turn-*off* delays draining, and random-tick crop growth.

   So a piston door, item sorter, hopper clock, or auto-farm built for an
   unattended single-player session **will not self-cycle** — and waiting longer
   won't help. Verify such a mechanism by watching it **fire once** (an
   immediate update you trigger), not by waiting for a cycle. A live, focused
   client or a **dedicated server** keeps the queue draining; that is the
   environment a tick-driven contraption needs to actually run. Surface this in
   the report whenever the build depends on scheduled ticks.
2. **Some loops still need an initial trigger.** A genuinely closed,
   edge-balanced loop (e.g. certain symmetric observer rings, or a circuit whose
   only state change is the one that would have come from placement order) can
   settle without ever toggling. These are the exception, not the rule — but
   when present, the design should name a one-time initial trigger.
3. **Placement order can matter.** Building a loop block-by-block, the partially
   complete circuit may reach a stable state before the last block lands, so the
   finished loop never starts. Placing the whole mechanism as one structure, or
   ordering placement so the power source goes in last, avoids this.

This file documents which redstone patterns reliably self-start when built by
the agent and which may need a one-time initial trigger or a chunk-load
guarantee, plus how to surface that in the inspection recipe.

## Patterns that self-start when placed via block_set_state

These work without intervention as long as the chunk is loaded and ticking.

- **Direct power: lever on a block adjacent to receiver.** A lever placed with
  its powered state on, on a block adjacent to a piston, lamp, dispenser, or
  other receiver, activates normally — the neighbour update propagates power.
- **Static power: `minecraft:redstone_block` adjacent to receiver.** A redstone
  block placed next to a piston/lamp/dispenser activates the receiver
  immediately. Reliable.
- **Button / pressure plate.** Players or mobs trigger these; pre-placed,
  unpressed, they work the moment something interacts.
- **Lit redstone torch + adjacent dust.** A `minecraft:redstone_torch[lit=true]`
  next to dust powers it. Static state; no clock involved.
- **Doors, trapdoors, fence gates with a power source.** Open/closed states
  follow the power source at placement and update with it.
- **Note blocks under a button or lever.** Plays on signal; one-shot triggers
  are fine.
- **Most clocks — observer clocks, repeater loops, hopper clocks, comparator
  loops.** On Java these generally start on their own when placed with the
  default update flags, because the placement neighbour-updates kick the cycle.
  Verify in the functional test that the clock is actually oscillating; do not
  assume.

## Patterns that may need an initial trigger or a chunk-load guarantee

Treat these as "verify it's ticking, and add an initial trigger if not":

- **A perfectly symmetric, edge-balanced loop** built block-by-block may settle
  before completing. If the test shows it static, add an initial-trigger step
  (set a `minecraft:redstone_block` adjacent for one moment, then remove it) and
  re-test.
- **A loop whose last placed block leaves the circuit in a stable, non-cycling
  state.** Re-order placement (power source last) or place it as one structure.
- **Any contraption built in a chunk that may not stay loaded.** Not a redstone
  fault — a ticking fault. Guarantee the chunk loads (near a player / ticking
  area / force-load) before sampling.

When in doubt, the cheap, reliable nudge on Java is: place a
`minecraft:redstone_block` (or flip a `minecraft:lever[powered=true]`) adjacent
to the loop for one game tick, then set it back to `minecraft:air`. That single
block update reliably starts any stalled loop.

## The initial trigger / chunk-load requirement — what it looks like

When a contraption is one of the exceptions above, the design surfaces it as an
optional **initial trigger** (or chunk-load note), not a mandatory manual chore:

- **Recorded in the inspection recipe** as an `initial_trigger` block —
  coordinate + action (the agent can perform it itself via `command_execute` /
  `block_set_state`, since these are not player-only interactions on Java).
- **Surfaced in the orchestrator's final report** only if it remains an
  outstanding requirement (e.g. "this loop must be force-loaded to keep
  ticking", or "if the clock is static, trigger once at (x,y,z)").
- **Applied before the functional test samples** the result.

Unlike a manual right-click on a parity-limited edition, on Java the agent can
usually apply the initial trigger itself with a tool call — so this is rarely a
user chore. Reserve a *player* action for cases that genuinely need one (a
button the user wants to press).

## Java-exclusive: `update_flags` — place dormant, then trigger deliberately

`block_set_state` takes an `update_flags` argument (the vanilla `/setblock`
update bitfield) that Bedrock's interface lacked. This is **precise placement
control** — choose whether a placed block fires neighbour/redstone updates:

- **`3` (default) — notify neighbours + sync to clients.** A placed block
  behaves like a player-placed one: power propagates, redstone self-starts,
  water flows, observers and pistons react. This is why most clocks self-start
  (above) and is what you want for nearly every placement.
- **`2` — sync to clients *without* notifying neighbours.** The block appears
  and is real, but fires **no** neighbour/redstone update. Use it to stage a
  component **dormant**: place a redstone block, lever, or torch with
  `update_flags:2` and the circuit around it does **not** react yet. Then
  trigger the circuit deliberately — e.g. set one adjacent block with the
  default flag `3`, or do a one-tick `redstone_block` nudge — so it starts on
  *your* signal rather than on placement order.

When this helps the engineer:

- **Stage a circuit cold, arm it on cue.** Build a sequence with `update_flags:2`
  so nothing self-starts mid-build, then fire a single default-flag update to
  launch the whole thing at once — sidesteps placement-order races on a
  symmetric loop.
- **Avoid mid-build misfires.** Lay a long redstone line or a powered component
  without it kicking pistons before the rest of the machine exists.
- **Performance on big static fills** — flag `2` skips the neighbour-update
  cascade on large decorative placements that have no redstone purpose.

Trade-off: a `update_flags:2` redstone component is intentionally inert until
something updates it, so it *will* read static in a functional test until you
arm it. Treat "armed it with a deliberate trigger" as a recipe step, not a
fault. (Default `3` placement plus the one-tick nudge remains the simplest path
for an ordinary self-starting machine — reach for `2` only when you specifically
want dormant staging.)

## What about structure-placing a running mechanism?

`structure_load_to_world` places blocks with neighbour updates by default too,
so a captured mechanism generally resumes ticking on placement (chunk loaded).
A closed, edge-balanced loop captured mid-cycle is the one case to verify — if
it lands static, apply the one-tick redstone-block nudge described above. Build
the mechanism, place it, then run the functional test to confirm it's actually
oscillating; don't assume the captured state survived the round trip.

## Decision tree

When the user asks for a mechanism:

1. **Player-operated input** (lever, button, plate, walked-into trigger)? →
   Build it; nothing extra needed.
2. **Self-cycling** (a clock, a self-running animation, a self-starting timer)?
   → Build it; it will usually self-start. Add an `initial_trigger` step to the
   recipe as a safety net, and verify in the functional test that it is
   oscillating. Note any chunk-load / force-load requirement.
3. **Built far from a player / in a chunk that may unload?** → Guarantee ticking
   (near a player, a ticking area, or force-load) and say so in the report.
4. **The functional test shows it static?** → Apply the one-tick redstone-block
   nudge, re-test, and only escalate to a player action if a tool nudge can't
   start it.

Be honest in the report: if a contraption needs the chunk force-loaded to keep
running, or needs a one-time trigger, say so up front — don't ship a "working"
clock that the user later finds standing still.
