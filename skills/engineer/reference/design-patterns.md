# Redstone design patterns

The logic primitives to compose a contraption from when no catalog entry fits.
All are Bedrock-correct — they avoid quasi-connectivity and account for the
fixed 2-tick piston delay and observer drift.

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
  button to flip the door" element. A piston-and-observer T flip-flop is the
  reliable Bedrock build.
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
  standard *long*-period clock (seconds to minutes), the most reliable on
  Bedrock.
- **Observer clock** — two observers facing each other; fast but subject to
  MCPE-15793 drift — avoid where timing matters.

Pick the clock by the period needed; do not run a fast observer clock for a
slow job.

## Randomness — no `/random` on Bedrock

- **Scoreboard random** — a scoreboard random objective produces a number;
  gate outputs on its value.
- **Dropper randomness** — a dropper with several items ejects one at random;
  a hopper/comparator reads which slot emptied. The vanilla-redstone RNG.

## Signal transmission

- **Vertical up** — a torch ladder (torch, block, torch, block …) or an
  observer ladder carries a signal up.
- **Vertical down** — a line of solid blocks with dust, or droppers.
- **Diagonal** — a staircase of blocks with dust and a repeater every 15
  blocks to refresh the signal (dust fades after 15).
- Repeaters both **extend range** (every ≤15 blocks) and **add delay** — use
  them deliberately for retiming, especially to absorb observer drift.

## Composing

When you compose a contraption from these: write the **timing budget** — every
piston is 2 ticks to start plus 2 to move; every observer may drift 2–3 ticks;
sum the worst-case path. Pad with repeaters so the slowest path still
completes inside the cycle. State the budget in the design so the inspection
recipe can wait the right number of ticks.
