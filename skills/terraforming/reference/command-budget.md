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

## Structure tile sizing — plan it up front

The `mc_structure_*` cap is **64 × 384 × 64**. State this cap *at the planning
stage* and tile to it before generating any RLE arrays — discovering the cap
mid-build wastes a generation cycle (Cape Aurelia terrain v2 generated tiles
112 deep and had to re-tile 3×2).

For hand-transcribed RLE arrays into `mc_structure_create_from_blocks`:

- Cap each tile at **~1500 RLE runs** (≈ 28-deep × 30×30 footprint, depending
  on entropy). Many small tiles beat few large ones — the
  `create_from_blocks` cell-count validator catches transcription drift, but
  a 3000-run array is near the limit where a 56-cell drop slips through.
- If the generator emits tiles that exceed either cap, **regenerate at half
  tile-depth** before retrying — don't try to "squeeze" a too-large tile.

## Structure naming — colon, not underscore

`mc_structure_create_from_blocks` (and the other create tools) **rejects**
underscore-only structure IDs with `invalid or missing namespace`. The
canonical form everywhere — `plan.toon`, `mcbuilder:registry`,
`mc_structure_place` calls — is:

```
mcb:<project>_<element>
```

An underscore-only `mcb_<project>_<element>` form will fail at create time
and force a plan-wide find/replace later. Treat this as the canonical name
form; the colon is required, not optional.

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
fill. Max structure size in Bedrock is **64 × 384 × 64** — see the sizing
rules above.

- `mc_structure_create_from_world` — capture a built terrain piece to a named
  structure. Name them `mcb:<project>_terrain_<element>` (colon namespace).
- `mc_structure_create_from_blocks` — synthesise a tile from an offline-baked
  RLE array. **This is the default for heightmap-based terrain** — generate
  the per-column heights offline, encode to RLE, and place directly without
  ever building it block-by-block in-world.
- `mc_structure_place` — stamp it. Vary **rotation** (0/90/180/270) and
  **mirror** to get up to 8 orientations from one module.
- **`integrity`** (0–100) — places only that percentage of the module's
  blocks, chosen pseudo-randomly from an `integritySeed`. This is how you get
  weathered, scattered, and varied placement — load a scree module at
  `integrity 40` for a thinned-out rubble field; reuse it with a different
  seed for a different scatter.

Build one detailed module (e.g. a 32×16×32 hill), then place it 6+ times with
different rotation, mirror, integrity, and seed. This is the only practical
way to fill Tier-3+ terrain.

### Offline generation is legitimate

For noise-driven terrain (mountains, headlands, coastlines), **offline
generation in Python → RLE → `mc_structure_create_from_blocks`** is usually
better than live block-by-block sculpting. It is fast, repeatable, lets you
tune the noise and re-place without rebuilding in-world, and is the only
practical way to get organic shapes at scale. Do not feel obliged to live-sculpt
when a heightmap will do the job — see `landforms.md § The heightmap method`.

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

## Pacing — keep the bridge alive

The BDS script watchdog will silently drop the bridge
(`BRIDGE_DISCONNECTED`) if a script callback runs too long or a burst of
calls saturates it. The Cape Aurelia v2 terrain build hit this repeatedly
until the rhythm below was adopted.

- **Cap at ≤6–8 heavy ops in a row** — structure placements, large fills,
  large clones. After the burst, drop in **one light verify read** (e.g. a
  single `mc_block_get`) before the next burst.
- **Never chase a placement burst with a read burst.** A burst of
  `mc_structure_place` followed immediately by a burst of `mc_block_get_top`
  is the most reliable way to crash the bridge. Alternate: place, place,
  read, place, place, read.
- **Prefer few large operations** over many tiny ones — every call pays
  throttle cost.
- **Use ticking areas over the work zone away from the player.** `mc_block_*`
  ops in unloaded chunks silently no-op (`blocks_changed: 0`); a ticking area
  guarantees the chunks stay loaded. Add one for the work zone, remove it
  when the phase ends.
- For big jobs, let the orchestrator run the `worker` **once per phase** so
  each run stays bounded and within the watchdog's patience.
- World vertical range is **Y=-64 to Y=320** (384 blocks) — plan heights
  inside it; do not modify the Y=-64 bedrock floor.

## The chunk-loading trap

`mc_block_*` ops in unloaded chunks return `blocks_changed: 0` with no error.
If the player has wandered away from the work zone — or the zone is far from
spawn — your fills and sets silently no-op.

- Add a ticking area over the work zone before any large terrain phase.
- Verify with a `mc_block_get` at a coord you just set; if it doesn't match,
  the chunk wasn't loaded.
- Remove the ticking area when the phase ends — the world has 10 slots total.
