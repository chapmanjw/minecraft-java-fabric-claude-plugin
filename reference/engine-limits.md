# Engine limits & verified tool behaviour

The canonical list of hard limits and quirks for the `minecraft-java` MCP tool
surface. Every skill that places, scans, or generates blocks should follow it.
Cite as `${CLAUDE_PLUGIN_ROOT}/reference/engine-limits.md`.

Some entries are marked **VERIFY** — the mod's *source* and an earlier *build
session* disagree about them, so the honest state is "unconfirmed." Smoke-test
those against the running world (a one-shot marker round-trip) before depending
on or warning against them; do not assert either way from memory.

## Block placement

- **`block_fill_region` auto-tiles past the 32,768 ceiling** *(mod ≥ the
  retrospective build)*. Vanilla `/fill` silently no-ops above 32,768 blocks,
  but the mod now splits any fill into ≤32,768 sub-boxes server-side and reports
  the true total. **Confirmed live on 26.1.2: a single 40,000-block fill placed
  all 40,000.** So an arbitrarily large fill is safe on this build. The `voxel`
  toolkit still caps boxes at 32,000 in `decompose` as belt-and-suspenders for
  older servers — harmless either way.
- **`block_fill_batch` (batch placement).** Where available, place many fills
  in one call instead of hundreds of separate requests — it collapses the
  per-call rate-limit and main-thread-tick overhead that throttle large builds
  to ~1 op/sec. The `voxel` toolkit emits a fills list in exactly this shape.
  If the connected server lacks it, drive the same list through a sequence of
  `block_fill_region` calls (the boxes are already capped).
- **Prefer few large ops** (`block_fill_region`, `block_clone_region`,
  `structure_load_to_world`) over many `block_set_state` calls.
- **`blocks_changed: 0` = unloaded chunk.** A fill in an unloaded chunk returns
  success with zero blocks changed. Keep the work zone loaded (near a player,
  or `/forceload`) and watch the changed count.

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
  pulling block data into context at all.
- **`block_get_map_color`** returns a block's base RGB — the authoritative
  block↔colour mapping for pixel-art quantization and matching a render's palette.
- **`block_get_top_y` semantics vary** — it has been seen to return the
  *stand-on* Y (first air above the surface), so the solid top is `result − 1`.
  Verify once per survey and record the convention.
- **Don't archaeology-sweep with a fine `block_get_top_y` grid** — too slow.
  Scan a high Y-layer in a few tiles with histogram mode and cluster by
  region + material instead (see `surveyor`).

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

## Throughput

- The embedded server marshals every world touch onto the main server tick and
  rate-limits per client, so naive one-call-per-op building is slow (~1 op/sec
  at a 60 rpm limit). The fixes, in order of leverage: **batch** (one
  `block_fill_batch`), **few large fills** (decompose to maximal boxes), and a
  higher configured `rate_limit_rpm` for building sessions.
