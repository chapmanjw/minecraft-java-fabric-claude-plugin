# Engine limits & verified tool behaviour

The canonical list of hard limits and quirks for the `minecraft-java` MCP tool
surface. Every skill that places, scans, or generates blocks should follow it.
Cite as `${CLAUDE_PLUGIN_ROOT}/reference/execution/engine-limits.md`.

Some entries are marked **VERIFY** — the mod's *source* and an earlier *build
session* disagree about them, so the honest state is "unconfirmed." Smoke-test
those against the running world (a one-shot marker round-trip) before depending
on or warning against them; do not assert either way from memory.

## Default tool surface (what's registered)

The mod defines 183 tools but **registers a lean ~102-tool surface by default**.
The default-on set is the seven domains the builder needs — `blocks`,
`structures`, `world`, `entities`, `items`, `scripting`, `server` — capped at
`write` access. The opt-in domains `players`, `gameplay`, and `registries`, plus
all `admin`-tagged ops (world border, `level_set_difficulty`,
`level_set_game_rule`, `level_create_explosion`, `command_register`,
`server_reload_resources`, `datapack_enable` / `_disable`, `player_kick`), are
**off** until an operator adds them via `config.json` (`included_categories` /
`max_access` — see the `setup-server` skill).

For building, the default surface is enough — block/fill/clone/scan, structures,
biome/feature/erosion world tools, entity ops, items, `command_execute`, and
structure save/load all sit in the default-on, write-or-below set. A build only
needs an opt-in when it reads from `gameplay` (scoreboards, boss bars) or
`registries` (recipes, loot tables, tags) — both read-only and harmless to
enable. If a tool the build expects answers "method not found," check it isn't a
gated category before assuming an older mod.

## Client inspection endpoint (`minecraft-java-client`)

Separate from the world surface above, the mod's **client** entrypoint serves a
second MCP endpoint, `minecraft-java-client` (default port 8766), with read-only
inspection tools under `mcp__minecraft-java-client__*`: `view_capture` (the
player's real first-person frame as a PNG — true lighting/sky/textures/entities),
`sense_crosshair`, `sense_raycast`, `sense_entities`, `sense_screen`, and
`client_status`. It runs only inside a real, rendered client and is **optional**.

For builds this is a **verification** aid, not a placement tool: it is the
real-pixel "what does this look like in-game" eye that `exec-inspect` uses (aim the
player from the `minecraft-java` world server with `entity_teleport` / `tp … yaw
pitch`, then `view_capture`). When the endpoint is absent, verification falls back
to `block_render_region` (the synthetic server-side render) plus a user screenshot.
Never assume it is connected — feature-detect the `mcp__minecraft-java-client__*`
tools and degrade gracefully.

`view_capture` notes: it defaults to `close_screen: true`, which dismisses the
pause/Esc menu that opens on window focus loss (so an alt-tabbed client still yields
a clean world frame); to stop that menu opening at all, toggle Pause on Lost Focus
off in-game with **F3 + P**. The client window must not be minimized (minimized = no
rendering = capture stalls). A large game window makes a large PNG — raise
`downscale` (e.g. 3–4) for the inline-image path (~1 MB content cap in some clients).

## Caps at a glance

Every hard cap on the tool surface, in one place. The behaviour-past-cap column
is the dangerous part — the silent ones (truncation, dropped entries) produce a
"successful" call that placed less than you asked for. The detail and the
mitigation for each live in the section noted; this table is the index.

| Operation | Cap | Behaviour past cap |
|---|---|---|
| `block_fill_region` / `/fill` (per box) | 32,768 blocks | auto-tiled server-side (places the true total — see Block placement) |
| `block_replace_in_region` | 32,768 blocks (W×H×L) | **silent truncation** — NOT auto-tiled; edits ~the first 32,768 cells and reports success |
| `block_fill_batch` | 8,192 entries | rejected above the cap; **and may silently drop a few entries even under it** (see Block placement) |
| `block_fill_columns` / `_strata` | 65,536 columns | rejected |
| `block_scan_region` | 65,536 blocks | error |
| `block_scan_summary` | 1,048,576 blocks | error |
| `block_render_region` | 4,194,304 sampled cells (after `step`) | error — raise `step` |
| `forceload` | 256 chunks / dimension | new adds rejected |

## Block placement

- **`block_fill_region` auto-tiles past the 32,768 ceiling** *(mod ≥ the
  retrospective build)*. Vanilla `/fill` silently no-ops above 32,768 blocks,
  but the mod now splits any fill into ≤32,768 sub-boxes server-side and reports
  the true total. **Confirmed live on 26.1.2: a single 40,000-block fill placed
  all 40,000.** So an arbitrarily large fill is safe on this build. The `voxel`
  toolkit still caps boxes at 32,000 in `decompose` as belt-and-suspenders for
  older servers — harmless either way.
- **`block_replace_in_region` silently truncates at ~32,768 blocks per call**
  *(W×H×L)* — and, **unlike `block_fill_region` above, it is NOT auto-tiled
  server-side.** It edits ~the first 32,768 matching cells, leaves the rest
  unchanged, and reports success with **no error** (a higher ~1,048,576 cap also
  exists, but the 32,768 one bites first). This was the root cause of repeated
  "the replace didn't do anything" reworks on the parks-grand-loop build — a
  20×20×113 = 45,200-block despeckle left speckle behind; the same op at
  14×14×113 = 22,148 cleared it. *Mitigation:* **tile every replace under 32,768
  blocks** (shrink the XZ tile or split Y for tall features) and **scan-verify
  after.** The build harness's `replace` op now tiles automatically
  (`tools/builder/harness.py`, `_tile_box`); an `exec-plan` step emitting `replace`
  by hand must still tile them — the `exec-worker` "fills are pre-tiled" guidance
  does **not** extend to `replace`.
- **`block_fill_batch` (batch placement).** Where available, place many fills
  in one call instead of hundreds of separate requests — it collapses the
  per-call rate-limit and main-thread-tick overhead that throttle large builds
  to ~1 op/sec. The `voxel` toolkit emits a fills list in exactly this shape.
  **Capped at 8192 entries (fill boxes) per call** (`MAX_ENTRIES`); it errors
  above that, so page a longer list into successive calls. (This is distinct
  from the ≤32,000-*blocks* limit on a single fill above — one is the number of
  boxes in the batch, the other is the volume of one box.) The bundled
  `tools/voxel/mcp_place.py` client pages automatically. If the connected server
  lacks the tool, drive the same list through a sequence of `block_fill_region`
  calls (the boxes are already capped).
- **`block_fill_batch` may silently drop a small number of entries** from a
  large batch — under the 8192 cap, no error. For wide terrain a few missed
  cells are invisible; for a feature where every cell matters (rails, redstone
  lines, thin walls) one gap is fatal, and the batch return won't tell you. A
  Zion rail batch of 1,928 one-block fills left 4 cells unplaced this way; a
  cart stalled dead at each gap. **Don't trust the batch return for 1-wide
  critical features — re-scan and patch after placing.** The continuity verifier
  `${CLAUDE_PLUGIN_ROOT}/tools/voxel/continuity.py` does exactly this:
  `verify_and_patch(intended_cells, dimension, y, shape_of=…, block="minecraft:rail")`
  scans the feature's Y-layer, diffs the intended cell list with `find_gaps`,
  and `set_state`s the missing cells (`set_state` is reliable per-block). It logs
  what it patched — never a silent fix.
- **Prefer few large ops** (`block_fill_region`, `block_clone_region`,
  `structure_load_to_world`) over many `block_set_state` calls.
- **`blocks_changed: 0` = unloaded chunk.** A fill in an unloaded chunk returns
  success with zero blocks changed. Keep the work zone loaded (near a player,
  or `/forceload`) and watch the changed count. **`block_replace_in_region` and
  `level_place_feature` (`/place feature`) likewise silently no-op on unloaded
  chunks**, and **`block_get_top_y` returns void (−64) there** rather than
  erroring — so a `−64` top-Y, like a `0`-change write, is a force-load miss,
  not real data. Additive `forceload add` + a touch-read + a brief settle before
  any of these, and retry on a `−64`.

## Force-loading & headless writes (the #1 unattended-mode footgun)

On a **dedicated / unattended** server (no player online), almost nothing is
write-loaded. The trap: **reads load chunks on demand and succeed almost
anywhere, but writes only affect already-loaded chunks and silently no-op**
otherwise — so a successful `block_get_state` is *not* proof a write will land
(verified live: a write at spawn no-op'd, then succeeded after `forceload add`).

- **Force-load the work envelope before any write, release it after:**
  `forceload add <x1> <z1> <x2> <z2>` (block coords) → do all block work →
  `forceload remove <x1> <z1> <x2> <z2>`.
- **Never use `forceload remove all`.** It unloads **every** force-loaded chunk,
  including spawn chunk (0,0). On the parks build this repeatedly killed an
  always-day **repeating command block** (the world fell back to its day/night
  cycle) because the block's chunk was unloaded. Always
  `forceload remove <the specific box>` you added, and re-assert
  `forceload add 0 0 0 0` (or wherever a persistent command block lives) at the
  end of any script that touched force-loads.
- **A force-REMOVE over a range can unload permanently force-loaded mechanism
  chunks.** `forceload remove` takes a box, not a set, so a later phase's remove
  band that overlaps a self-running mechanism's chunks (a rail loop, a farm, a
  repeating command block) unloads them too — entities freeze, redstone reverts.
  On Zion the ecology pass force-loaded then `forceload remove`d each work band;
  the bands overlapped the rail chunks, so afterwards the cart's spawn chunk was
  no longer force-loaded and summoned carts "despawned" (really: frozen in an
  unloaded chunk — see the diagnostics note below). **Near a mechanism, prefer
  `forceload add` only**, and re-assert the permanent mechanism set as the *last*
  op of every force-toggling phase rather than bracketing with a remove. Reclaim
  the 256-chunk cap with targeted single-chunk removes of *known* non-mechanism
  chunks if you must. The build harness does this for you: it reads a top-level
  `protect:` block in `plan.toon` (rows of `{corner_a, corner_b}` as "x z") and
  re-asserts those chunk bands with `forceload add` as the last op of every
  force-toggling phase — see
  `${CLAUDE_PLUGIN_ROOT}/reference/execution/build-harness.md`.
- **Cap: 256 chunks per dimension.** Regions wider than that must be built in
  **Z-bands** (≤256 chunks each), one force-load at a time. Force-load is
  **per-dimension** — re-do it in the Nether/End.
- **The build harness does all of this for you.** `harness.py run`/`build`
  brackets each phase, auto-bands under the cap, and flags any `blocks_changed: 0`
  as a probable force-load miss. See
  `${CLAUDE_PLUGIN_ROOT}/reference/execution/build-harness.md`.
- **Detect the mode first** (`harness.py mode`): a dedicated server ticks 24/7 and
  needs force-loading; a single-player integrated server needs a focused client
  and freezes ticks when unfocused. See
  `${CLAUDE_PLUGIN_ROOT}/reference/execution/startup-and-recovery.md`.
- **Diagnostics: `entity_query` / `@e` selectors only enumerate entities in
  LOADED chunks.** A `summon` that reports `successCount: 1` followed by an empty
  query usually means the target chunk is not loaded (check
  `forceload query <x> <z>`), not that the entity despawned. Minecarts and items
  in unloaded chunks are frozen, not removed — they reappear when the chunk loads.
  On Zion this misread cost the most time: carts summoned onto unloaded rail
  chunks (see the force-load notes above) returned empty from `entity_query`, which looked like
  "instant despawn" and sent the diagnosis chasing booster theories instead of
  the force-load. Force-load the chunk, re-query, before concluding an entity is
  gone.

## Scanning / reading

- **`block_scan_region` is capped at 65,536 blocks per call** and needs a `box`
  and a `dimension`. Its raw per-block output is large (~10 lines/block) —
  **never dump a raw full-volume scan into the agent context**; a single slab
  has blown the token limit. For recon, prefer **`block_scan_summary`** (a
  server-side material histogram + non-air bounding box over a box up to
  1,048,576; no per-block rows reach you). Reach for raw `block_scan_region`
  only when you need exact per-block states, and page it.
- **To *see* a region, use `block_render_region`** — it returns a PNG (iso /
  side / front / top), rendered server-side from block map colours, with a
  `step` downsample for large areas. This is the verify-time "eyes" and avoids
  pulling block data into context at all. On **mod v0.3.0+** it also accepts
  `view: hillshade` — a relief-shaded plan view for terrain (terraces and flat
  tops read as flat bands; eroded slopes read as branching relief). See
  "Terrain helpers" below; fall back to `top` on older mods.
- **`block_get_map_color`** returns a block's base RGB — the authoritative
  block↔colour mapping for pixel-art quantization and matching a render's palette.
- **`block_get_top_y` semantics vary** — it has been seen to return the
  *stand-on* Y (first air above the surface), so the solid top is `result − 1`.
  Verify once per survey and record the convention. On **mod v0.3.0+** it takes
  a `heightmap` arg (`WORLD_SURFACE` default, plus `OCEAN_FLOOR` for the seabed,
  `MOTION_BLOCKING`, `WORLD_SURFACE_WG`, …); omit it on older mods (only
  `WORLD_SURFACE`).
- **Don't archaeology-sweep with a fine `block_get_top_y` grid** — too slow.
  Scan a high Y-layer in a few tiles with histogram mode and cluster by
  region + material instead (see `survey-site`).

## Structures

- **Structure template envelope ≈ 64×384×64.** A form larger than this in a
  horizontal axis cannot be one template — split along natural seams, or (for
  large parametric art) keep the **authoring script + model `.npy`** as the
  reusable artifact and place via `block_fill_batch`.
- **`forceload` caps at 256 chunks per command** — tile large force-load areas.
- **Many tools require an explicit `dimension`** argument.
- **`structure_save_from_world` + `structure_load_to_world` work** — confirmed
  live on 26.1.2 (saved a region, reloaded it elsewhere, blocks reappeared
  intact). This is the reliable path for reusable blueprints.
- **`structure_file_write` writes the file but the result is NOT loadable
  in-session** — confirmed live: `file_write` returns `written`, but
  `structure_load_to_world` on that name then *fails* (it drops NBT on disk
  without registering the template with the running `StructureManager`). Don't
  rely on `file_write` for round-trips; use `structure_save_from_world`, which
  registers the template.

## Functions / datapacks

- **Datapack functions are INERT — confirmed live on 26.1.2.** A datapack was
  loaded (`function_list` showed `livetest:marker`), yet `function_run` returned
  `failed` and the function's `setblock` never executed (the marker block stayed
  air); `/reload` returns `successCount 0`. **Do not depend on `/function`,
  `function_run`, or `/reload`-driven packs.** Never generate `.mcfunction` files
  expecting them to run — emit direct block ops (`block_fill_region`,
  `block_fill_batch`, `block_set_state`, `block_clone_region`, `structure_*`) or
  live redstone instead.

## Game rules & world settings

- **Use snake_case gamerule ids on MC 26.x — camelCase is rejected.** On 26.1.2
  the rule ids are snake_case (`spawn_mobs`, `random_tick_speed`, `advance_time`
  for the old `doDaylightCycle`, `advance_weather`, `keep_inventory`, …); the
  historical camelCase names fail with a confusing parser error pointing at the
  name position, through both `/gamerule` and the typed `level_set_game_rule`
  tool. **Get the live id from `level_list_game_rules` before setting one**
  rather than typing a name from memory. The parks-loop retrospective reported
  "`gamerule` / `level_set_game_rule` rejected on 26.1.x" — that was almost
  certainly a camelCase id (e.g. `doDaylightCycle`) hitting this rejection, not
  the surface being inert. **VERIFY** with a one-shot snake_case
  `level_set_game_rule` round-trip if you depend on it.
- *Robust regardless:* for permanent world state, a **repeating command block**
  in a force-loaded chunk is the bulletproof path — a `repeating,
  always-active` block running `time set day` holds permanent daytime even where
  a gamerule is awkward. Keep that chunk force-loaded, and never
  `forceload remove all` (it unloads the block — see Force-loading above).

## Throughput

- The embedded server marshals every world touch onto the main server tick and
  rate-limits per client, so naive one-call-per-op building is slow (~1 op/sec
  at a 60 rpm limit). The fixes, in order of leverage: **batch** (one
  `block_fill_batch`), **few large fills** (decompose to maximal boxes), and a
  higher configured `rate_limit_rpm` for building sessions.
- **Long runs need 429 backoff.** At the ~60 rpm limit a sustained placement
  script — a big parametric heightfield placed page-by-page via
  `block_fill_batch` — *will* hit HTTP 429. Pace requests and back off
  (exponential, honour any `Retry-After`) rather than hammering. The bundled
  `tools/voxel/mcp_place.py` paces and retries; a hand-rolled placer must too.
  Driving such a generated placement script is a first-class execution mode for
  forms too large to be one structure template — see
  `${CLAUDE_PLUGIN_ROOT}/reference/execution/build-harness.md`.

## Terrain helpers (mod v0.3.0+)

These tools exist only on the **v0.3.0+** MCP mod. **Probe before relying on
them** — a `tools/list` that lacks the name, or a call that errors
method-not-found, means an older mod — and use the listed fallback so builds
still work everywhere. (Where the fallback is "the same `/command` via
`command_execute`", that works on any version; the typed tool just adds schema
and validation.)

- **`block_fill_columns`** — materialise a per-column heightmap into terrain in
  one server-side pass: send a compact height grid + a small palette (surface /
  subsurface / stone / water indices) instead of thousands of box fills, with
  **no 8192-entry cap**. Fills each column stone → subsurface → surface and
  floods to `sea_level`. Capped at **65,536 columns per call** — tile larger
  terrain. The efficient placement path for the `terrain` toolkit's heightfields.
  **It does not clear blocks *above* the new surface** — re-sculpting terrain
  *lower* than it was leaves the old taller columns floating. Clear first: run
  `block_fill_columns` (or `fill_batch`) with an **air** palette from floor to
  ceiling over the footprint, then fill the real field.
  **Fallback:** decompose the heightfield to box fills and place via
  `block_fill_batch` (paging the 8192 cap) / `block_fill_region` — the existing
  `tools/voxel/mcp_place.py` path.
- **`level_place_feature`** — grow a vanilla configured feature at a position
  (`/place feature <id> <x> <y> <z>`): trees, vegetation, ore veins, geodes,
  dripstone. The way to *grow* detail rather than stamp copies (terrain method
  non-negotiable 5, erosion/grow detail). **Fallback:** `command_execute` with the same `/place feature`
  command, or bone-meal / `random_tick_speed` sapling growth.
- **`level_fill_biome`** — paint the biome of a region (`/fillbiome`): foliage /
  water tint, mob spawns, climate. Biome is read-only otherwise. **Fallback:**
  `command_execute` with `/fillbiome`.
- **`block_get_top_y` `heightmap` arg** and **`block_render_region` `hillshade`
  view** — documented inline above; both degrade to their pre-0.3.0 behaviour
  (`WORLD_SURFACE` only; `top` view) on older mods.

## Terrain helpers (mod v0.4.0+, WS-C)

The v0.4.0 mod adds batch feature scatter, strata banding, and in-world
erosion. Same posture as the 0.3.0 helpers above — **probe before relying on
them** (`tools/list` / a method-not-found error means an older mod) and use the
listed fallback. The v0.4.0 mod defines 183 tools in all; the terrain helpers
here are in the default-on `blocks` / `world` domains, so they register under
the lean default (see "Default tool surface" above — a `tools/list` on a default
config shows ~102, not the full 183).

- **`level_place_features_batch`** — grow many vanilla configured features in
  one call (the batch form of `level_place_feature`): send a `features[]` list of
  `{feature, x, y, z}` and the whole scatter is placed in one main-thread
  submission, one rate-limit slot. The throughput path for the `terrain`
  toolkit's vegetation/detail scatter — one round-trip instead of ~60/min, which
  would take hours. **Capped at 4096 entries per call** (it errors above; page
  longer scatters across calls); reports per-entry `placed`/`failed` so you retry
  only the misses. Like `level_place_feature` it silently no-ops on unloaded
  chunks — force-load the envelope first. **Fallback:** loop
  `level_place_feature` (or `command_execute` `/place feature`), accepting the
  per-call rate cost.
- **`block_fill_columns_strata`** — a strata-banded `block_fill_columns`: same
  per-column heightmap fill, but bands the deep mass below the subsurface into
  geological strata (`strata[]` of `{block, thickness}` top→bottom, `base_stone`
  below the deepest band) instead of one stone block — the canyon / mesa /
  badlands signature. Optional `jitter_amplitude` / `jitter_freq` wobble the band
  boundaries so they are not dead-flat. **Same 65,536-column cap** as
  `block_fill_columns` (tile larger terrain), and the same caveat: it does **not**
  clear blocks *above* the new surface — clear the footprint to air first if
  re-sculpting lower. Row-major arrays index `xi*length+zi`. **Fallback:**
  `block_fill_columns` with a stone deep-fill (no banding), or box fills via
  `block_fill_batch`.
- **`block_erode_region`** — synchronous thermal (talus-collapse) erosion of
  terrain that already exists in the world: reads the live surface, collapses
  unstable slopes, re-materialises surface + subsurface. `protect_box` (with a
  smoothstep `apron`) shields built structures so terrain naturalises into them;
  `dry_run` reports max/mean height delta with no writes — survey before
  committing. **Same 65,536-column cap** (tile larger regions). Synchronous, so
  it must finish inside the command-timeout budget; for big regions prefer the
  async hydraulic trio below. **Fallback:** none typed — pre-0.4.0 erosion was
  client-side only in the `terrain` toolkit.
- **`block_erode_hydraulic_start` / `_status` / `_result`** — async hydraulic
  (rain-droplet) erosion on the mod's job engine, for regions too large for a
  synchronous pass. `_start` surveys the surface and queues a worker-thread
  droplet simulation, returning a `job_id` (the writeback is metered across
  server ticks). **Poll `_status`** for state (`ERODING` → `WRITING` → `DONE` /
  `FAILED`) and `progress`; once `DONE`, read **`_result`** for `blocks_changed`
  / `max_delta` / `mean_abs_delta` / `moved`. `protect_box` + `apron` shield
  built structures; `dry_run` computes without writing. **Region default
  256×256, hard cap 512×512** — it errors above 512×512; tile larger regions. As
  with any write, force-load the envelope first or the writeback no-ops on
  unloaded chunks. **Fallback:** `block_erode_region` (synchronous thermal) for
  small regions; none for hydraulic specifically on older mods.

Per the version-lockstep rule, the mod, Fabric API, and Minecraft move together;
when in doubt about the connected mod's surface, `server_get_status` /
`tools/list` is the source of truth.
