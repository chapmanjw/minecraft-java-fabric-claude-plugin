# Command budget & execution limits

How to move large volumes of terrain without overrunning the Java MCP server's
limits. Read this before executing any terrain job above ~30 blocks.

## MCP tools vs. raw commands

This plugin shapes the world through **MCP tools** (`block_fill_region`,
`structure_save_from_world`, `block_clone_region`, …), which run inside the
Fabric mod embedded in the server — not via chat. That matters:

- MCP tool calls are **not** subject to the ~256-character chat-command limit.
- They **are** subject to `command_timeout_ms` (default **15 000 ms** per call)
  and the per-client `rate_limit_rpm` (default **60** calls/min).
- The vanilla **`/fill` and `/clone` cap of 32,768 blocks** applies to
  `block_fill_region` and `block_clone_region`. Treat 32,768 as the safe
  ceiling for any single volume operation regardless of tool.

**Rule:** prefer the typed MCP tools; reserve `command_execute` for things
with no dedicated tool (e.g. `/forceload`, `/gamerule`, `/place feature`).

## Tile every large volume

Keep any single fill at or below a safe volume. Good tile sizes:

- **30 × 30 × 30 = 27,000** blocks — comfortable headroom.
- **32 × 16 × 64 = 32,768** blocks — the absolute ceiling.

A 200 × 1 × 200 surface (40,000 blocks) already exceeds the cap — the planner
must split it into multiple `fill` steps. Always emit **pre-tiled** fills in
`plan.toon`; the Haiku `worker` does no arithmetic.

## Structure template sizing — plan it up front

Java structure templates (`.nbt` under `<world>/generated/<namespace>/structures/`)
have no published hard size limit but become unwieldy past **64 × 384 × 64**.
Use that as your practical ceiling. State this cap *at the planning stage* and
tile to it before generating any heightmap tiles — discovering the cap mid-build
wastes a generation cycle.

For the scratch-and-capture workflow (see below), each tile must fit in the
scratch area you have allocated.

## Structure naming — always namespace with `mcb:`

The canonical form everywhere — `plan.toon`, the `mcbuilder:registry` storage,
`structure_load_to_world` calls — is:

```
mcb:<project>_<element>
```

Use the `mcb:` namespace, not a bare name. A name with no namespace gets
dropped into the `minecraft:` namespace, where it sits alongside (and can clash
with) the hundreds of vanilla templates — and makes the builder's own templates
hard to find in `structure_list`. The colon namespace keeps them isolated and
listable. Treat it as required.

## Turning a computed grid into a placeable structure (scratch-and-capture)

Java has **no `mc_structure_create_from_blocks`** equivalent. To turn a
noise-driven or computed heightmap tile into a reusable structure template:

1. **Build the tile into a scratch area.** Choose a reserved flat region away
   from the active build (e.g. Y=0 in the Nether, or a cleared pad in the
   Overworld). Use `block_fill_region` / `block_set_state` to write the
   computed column heights there.
2. **Save the scratch area.** Call `structure_save_from_world` over the exact
   bounding box of the tile. Name it `mcb:<project>_terrain_<tile>`.
3. **Place wherever needed.** Call `structure_load_to_world` at each target
   coordinate. Vary **rotation** (0/90/180/270°) and **mirror** to get up to 8
   orientations from one saved tile.
4. **Clear the scratch area.** Fill it with air when done so it is ready for
   the next tile.

This is the standard path for heightmap-based terrain — fast, repeatable, and
allows re-tuning the noise and re-capturing without rebuilding in-world.

Alternatively, for scripted pipelines that already produce NBT: generate the
structure `.nbt` file externally and write it with `structure_file_write`
(content is base64). Use this only when a generator already produces NBT.

## Fill modes

`block_fill_region` supports modes — choose deliberately:

| Mode | Use |
| ---- | --- |
| `replace` | Default. Swap blocks in the region; can target one old block. |
| `hollow` | Fill the outline only; interior becomes air. Cave/room shells. |
| `outline` | Like `hollow` but leaves the interior untouched. |
| `keep` | Fill **only air** positions. Essential for non-destructive overlay — e.g. dropping `snow` onto terrain without overwriting leaves. |
| `destroy` | Drops existing blocks as items. Rarely useful for terrain. |

## Clone modes

`block_clone_region` supports three modes:

- `normal` — default; copy every block including air.
- `masked` — copy only non-air blocks. Transplant a hill **onto** existing
  terrain without punching air holes. The most useful mode for terrain.
- `move` — relocate a region; the source becomes air.

For the vanilla `/clone` extras — `filtered` (copy only blocks matching one ID,
e.g. lift just the `minecraft:grass_block` surface) or `force` (allow
overlapping source and destination) — fall back to `command_execute` with a
`/clone … filtered`/`force` command.

## Structure modules — the force multiplier

Structure templates are the unit of work for anything reusable or larger than
a fill. Keep tiles under 64 × 384 × 64 — see the sizing rules above.

- `structure_save_from_world` — capture a built terrain piece to a named
  template. Name them `mcb:<project>_terrain_<element>` (colon namespace).
- `structure_load_to_world` — stamp it. Vary **rotation** (0/90/180/270°) and
  **mirror** to get up to 8 orientations from one module.
- **`integrity`** (0.0–1.0) — places only that proportion of the module's
  blocks, chosen pseudo-randomly. This is how you get weathered, scattered,
  and varied placement — load a scree module at `integrity 0.4` for a
  thinned-out rubble field; reuse it with a different seed for a different
  scatter.

Build one detailed module (e.g. a 32×16×32 hill), then place it 6+ times with
different rotation, mirror, integrity, and seed. This is the only practical
way to fill Tier-3+ terrain.

### Offline generation is legitimate

For noise-driven terrain (mountains, headlands, coastlines), **offline
generation in Python → scratch-and-capture → `structure_load_to_world`** is
usually better than live block-by-block sculpting. It is fast, repeatable,
lets you tune the noise and re-place without rebuilding in-world, and is the
only practical way to get organic shapes at scale. Do not feel obliged to
live-sculpt when a heightmap will do the job — see `landforms.md § The
heightmap method`.

## Randomness without `/random`

Get randomness from:

- **Structure `integrity` + seed** — the primary method (above).
- **`command_execute`** with `/scoreboard players random` — pair a random
  score with conditional placement logic.
- Vary seeds per call so repeated module placements differ.

## Scanning large regions — block_scan_region

`block_scan_region` is capped at **65,536 blocks per call**. Page large scans:
split the region into sub-volumes each ≤65,536 and call once per sub-volume.
Use this to verify fills and check monoculture before reporting a phase done.

## Force-loaded chunks — keep the work zone loaded

A long terrain job stalls if its chunks unload. On Java, force-load the work
zone's chunks via `command_execute` with `/forceload` (chunk coordinates — no
Y, no name; divide block coords by 16):

```
/forceload add <chunkX1> <chunkZ1> <chunkX2> <chunkZ2>
```

- A dimension allows **up to 256 force-loaded chunks** by default. Force-load
  only the chunks the active phase touches.
- Remove them when the phase is done: `/forceload remove <…>` (or
  `/forceload remove all`). Leaving chunks force-loaded taxes the server.
- For large jobs, move the force-loaded window across cells as construction
  progresses. Working near an online player also keeps chunks loaded.

## Pacing — good practice, not a bridge limit

There is no hard "N ops then a pause" rule on the Java MCP server — it has no
BDS script watchdog. The real limits are `command_timeout_ms` (15 s per call)
and `rate_limit_rpm` (60/min). That said, some practices prevent wasted work:

- **Prefer few large operations** over many tiny ones — every call pays
  rate-limit cost and round-trip latency. `block_fill_region`, `block_clone_region`,
  and `structure_load_to_world` are the right units of work.
- **Don't chase a placement burst with a read burst.** A burst of
  `structure_load_to_world` calls followed immediately by many
  `block_get_top_y` reads can back up the queue. Interleave reads and
  writes where practical — place, verify one spot, place again.
- **Use ticking areas over the work zone.** `block_fill_region` in unloaded
  chunks silently no-ops (`blocks_changed: 0`); a ticking area guarantees the
  chunks stay loaded. Add one before any large terrain phase, remove it when
  the phase ends.
- For big jobs, let the orchestrator run the `worker` **once per phase** so
  each run stays bounded.
- World vertical range is **Y=-64 to Y=320** (384 blocks) — plan heights
  inside it; do not modify the Y=-64 bedrock floor.

## The chunk-loading trap

`block_fill_region` and related ops in unloaded chunks return
`blocks_changed: 0` with no error. If the player has wandered away from the
work zone — or the zone is far from spawn — your fills and sets silently no-op.

- Add a ticking area over the work zone before any large terrain phase.
- Verify with a `block_get_state` at a coord you just set; if it doesn't match,
  the chunk wasn't loaded.
- Remove the ticking area when the phase ends — the world has 10 slots total.
