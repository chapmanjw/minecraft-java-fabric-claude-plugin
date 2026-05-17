# Command budget & execution limits

How to move large volumes of terrain without overrunning Bedrock's limits or
the MCP bridge. Read this before executing any terrain job above ~30 blocks.

## MCP tools vs. raw commands

This plugin shapes the world through **MCP tools** (`mc_block_fill`,
`mc_structure_*`, `mc_block_clone`, …), which call the Bedrock Script API —
not chat commands. That matters:

- MCP tool calls are **not** subject to the ~256-character chat-command limit.
- They **are** subject to the bridge's per-command throttle and the BDS script
  watchdog (which kills a script callback that runs too long).
- The vanilla **`/fill` and `/clone` cap of 32,768 blocks** still applies if
  you fall back to `mc_run_command`. Treat 32,768 as the safe ceiling for any
  single volume operation regardless of tool.

**Rule:** prefer the typed `mc_*` tools; reserve `mc_run_command` for things
with no dedicated tool (e.g. `/tickingarea`).

## Tile every large volume

Keep any single fill at or below a safe volume. Good tile sizes:

- **30 × 30 × 30 = 27,000** blocks — comfortable headroom.
- **32 × 16 × 64 = 32,768** blocks — the absolute ceiling.

A 200 × 1 × 200 surface (40,000 blocks) already exceeds the cap — the planner
must split it into multiple `fill` steps. Always emit **pre-tiled** fills in
`plan.toon`; the Haiku `worker` does no arithmetic.

## Fill modes

`mc_block_fill` supports modes — choose deliberately:

| Mode | Use |
| ---- | --- |
| `replace` | Default. Swap blocks in the region; can target one old block. |
| `hollow` | Fill the outline only; interior becomes air. Cave/room shells. |
| `outline` | Like `hollow` but leaves the interior untouched. |
| `keep` | Fill **only air** positions. Essential for non-destructive overlay — e.g. dropping `snow_layer` onto terrain without overwriting leaves. |
| `destroy` | Drops existing blocks as items. Rarely useful for terrain. |

## Clone modes

`mc_block_clone` supports modes:

- `masked` — copy only non-air blocks. Transplant a hill **onto** existing
  terrain without punching air holes. The most useful mode for terrain.
- `move` — relocate a region; the source becomes air.
- `filtered` — copy only blocks matching one ID (e.g. lift just the
  `grass_block` surface).
- `force` — allow overlapping source and destination.

## Structure modules — the force multiplier

`mc_structure_*` is the unit of work for anything reusable or larger than a
fill. Max structure size in Bedrock is **64 × 384 × 64**.

- `mc_structure_create_from_world` — capture a built terrain piece to a named
  structure. Name them `mcb_<project>_terrain_<element>`.
- `mc_structure_place` — stamp it. Vary **rotation** (0/90/180/270) and
  **mirror** to get up to 8 orientations from one module.
- **`integrity`** (0–100) — places only that percentage of the module's
  blocks, chosen pseudo-randomly from an `integritySeed`. This is how you get
  weathered, scattered, and varied placement — load a scree module at
  `integrity 40` for a thinned-out rubble field; reuse it with a different
  seed for a different scatter.

Build one detailed module (e.g. a 32×16×32 hill), then place it 6+ times with
different rotation, mirror, integrity, and seed. This is the only practical way
to fill Tier-3+ terrain.

## Randomness without `/random`

Bedrock has **no `/random` command**. Get randomness from:

- **Structure `integrity` + seed** — the primary method (above).
- **`mc_scoreboard`** — Bedrock supports `scoreboard players random`; pair a
  random score with conditional placement.
- Vary seeds per call so repeated module placements differ.

## Ticking areas — keep chunks loaded

A long terrain job stalls if its chunks unload. Wrap the work zone in a
ticking area via `mc_run_command`:

```
/tickingarea add <x1> <y1> <z1> <x2> <y2> <z2> tf_work
```

- A world allows **max 10 ticking areas**, each up to 100 chunks.
- Reserve 1–2 slots for active terrain work; remove them when done
  (`/tickingarea remove tf_work`).
- For Tier-4+ jobs, rotate ticking areas across cells as construction moves.

## Pacing

- Prefer **few large operations** over many tiny ones — every call pays
  throttle cost.
- For big jobs, let the orchestrator run the `worker` **once per phase** so
  each run stays bounded and within the watchdog's patience.
- World vertical range is **Y=-64 to Y=320** (384 blocks) — plan heights
  inside it; do not modify the Y=-64 bedrock floor.
