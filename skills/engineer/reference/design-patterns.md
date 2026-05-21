# Redstone design patterns

The logic primitives to compose a contraption from when no catalog entry fits.
All are Java-correct — they use deterministic redstone-tick timing and clean
1-redstone-tick observer pulses, and may use quasi-connectivity where it
simplifies the circuit (document where they do).

## Logic gates

The eight gates built from redstone dust, torches, and blocks:

- **NOT** — a redstone torch on a powered block (the inverter).
- **AND** — two inputs both required; e.g. two torches in series, or
  comparator logic.
- **OR** — two inputs merged onto one dust line.
- **NAND / NOR / XOR / XNOR / buffer** — composed from the above.

XOR is the workhorse for "toggle" behaviour (two switches controlling one
lamp); build it deliberately, not by guesswork.

## Memory

- **RS-latch** — two cross-coupled NOR gates (torches); set and reset inputs,
  holds a bit. The basic memory cell.
- **T flip-flop** — toggles state on each input pulse; the standard "press the
  button to flip the door" element. A piston-and-observer T flip-flop is a
  compact, reliable Java build.
- **D-latch** — captures an input on a clock edge.
- **Counters** — chained T flip-flops count pulses in binary.

## Edge detection and pulse shaping

- **Rising-edge detector** — an observer facing a redstone line emits a short
  pulse when the line turns on.
- **Falling-edge detector** — an observer fires on the line turning off too;
  use one observer for both edges, or invert.
- **Pulse extender** — a chain of repeaters holds a short pulse longer.
- **Pulse limiter / shortener** — a repeater feeding a torch that cuts the
  line shortens a long input to a fixed pulse.
- **Monostable** — any trigger produces one fixed-length output pulse.

## Clocks

- **Repeater clock** — a loop of repeaters; the slowest reliable clock, period
  set by the repeater delays.
- **Comparator (subtraction) clock** — a comparator loop for longer, tunable
  periods.
- **Hopper clock** — items cycling between two hoppers via comparators; the
  standard *long*-period clock (seconds to minutes), tunable by item count.
- **Observer clock** — two observers facing each other; fast and stable on Java
  (clean 1-redstone-tick pulses, no drift bug). Good where a short, precise
  period is wanted.

Pick the clock by the period needed; do not run a fast observer clock for a
slow job. Java timing is deterministic, so a clock's period is reproducible —
state it in redstone ticks.

## Randomness

- **Dropper randomness** — a dropper with several items ejects one at random; a
  hopper/comparator reads which slot emptied. The vanilla-redstone RNG, and the
  right choice for a self-contained in-world machine.
- **Scoreboard / loot-table random** — for command-driven setup or verification,
  a scoreboard random objective or `loot_table_generate` produces a number; gate
  outputs on its value. Keep this out of the contraption's running logic — the
  machine itself should run on the dropper RNG so it works without commands.

## Signal transmission

- **Vertical up** — a torch ladder (torch, block, torch, block …) or an
  observer ladder carries a signal up.
- **Vertical down** — a line of solid blocks with dust, or droppers.
- **Diagonal** — a staircase of blocks with dust and a repeater every 15
  blocks to refresh the signal (dust fades after 15).
- Repeaters both **extend range** (every ≤15 blocks) and **add delay** — use
  them deliberately for retiming, especially to absorb observer drift.

## Java-exclusive: command-driven path (datapack functions)

A **non-redstone** way to sequence, time, and animate — something Bedrock's MCP
could not do. Two tools:

- **`function_run(function_id, as_entity?)`** — runs a datapack function *now*.
- **`schedule_function(function_id, ticks, mode)`** — runs one after N game
  ticks. `mode` is `append` (queue alongside any existing schedule for that
  function) or `replace` (overwrite the pending schedule — the right choice for
  a self-rescheduling loop so it can't double up).

What it unlocks:

- **Timed sequences** — staged light/door reveals: `function_run` step one, then
  `schedule_function("build:reveal_2", 40, "replace")`, etc.
- **Recurring animations** — a function whose last line re-schedules itself
  (`schedule_function(<self>, 5, "replace")`) is a clean software clock with
  *exact* tick timing, no redstone-clock drift or footprint. Pairs naturally
  with display-entity `transformation` tweens (`entity_set_nbt` per frame).
- **Staged reveals / firework shows** — choreograph events to the exact tick
  without a physical clock.

**Caveat — the datapack must be loaded.** The function only exists if its
datapack is enabled: check `datapack_list_enabled`, enable with
`datapack_enable`, and verify the function resolves with `function_list` /
`function_get_definition` before relying on it. So this is an **advanced option
for a build that already ships a small datapack.**

**Trade-off — prefer self-contained redstone for portability.** A redstone
machine works in any world the moment it's placed, with nothing else installed.
A function path needs the datapack to travel with the build. Use functions when
the build *ships a datapack* and wants exact, frame-accurate timing (animations,
choreographed reveals); use in-world redstone for a self-contained machine the
user can copy anywhere. State the datapack requirement up front, the same way
you'd surface an `initial_trigger` or chunk-load requirement.

## Composing

When you compose a contraption from these: write the **timing budget** — sum the
deterministic delays along the worst-case path (each repeater 1–4 redstone
ticks, each observer a clean 1-redstone-tick pulse, piston movement ~1.5 game
ticks). Java timing is reproducible, so the sum is exact — pad with repeaters
only to align paths, not to absorb a drift bug. State the budget in the design
so the inspection recipe can wait the right number of ticks.
