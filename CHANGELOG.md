# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.5.0] - 2026-05-22

### Added

- **`terrain` toolkit (`tools/terrain/`).** The 2.5-D counterpart of the `voxel`
  toolkit: author a `HeightField` (multi-octave noise, radial falloff, blob
  lakes, carved rivers, build pads), erode it (hydraulic + thermal), and
  **render-verify offline** (hillshade / relief / cross-section profile) before
  placing — then materialise to fills (double-layer substrate, no-monoculture
  surface mix, cliffs, beaches, water columns) and place via the shared
  `mcp_place.py`. numpy + Pillow only. See `tools/README.md`.

### Changed

- **Terraforming skills now reference the mod's v0.3.0+ terrain tools, gated
  with fallbacks.** `reference/engine-limits.md` documents them once (new
  "Terrain helpers" section); terraforming (`landforms`, `command-budget`,
  `weathering`, `palettes`, `SKILL`) and `surveyor` cite them where they help —
  `block_fill_columns` for heightmap placement, `level_place_feature` to grow
  trees/vegetation/ore, `level_fill_biome` for the biome pass,
  `block_get_top_y heightmap=OCEAN_FLOOR` for seabed reads, and the
  `block_render_region hillshade` view for placed-terrain verification. Each is
  written "prefer if available, else current approach" so it stays safe on older
  mods.

## [0.4.0] - 2026-05-21

Give the builder **eyes**, and drive bulk builds natively. Folds in the Rivian
R1S / "Gear Guard Gary" retrospective: a representational build iterated blind
fails on silhouette, and hundreds of one-at-a-time fills are infeasible. Pairs
with [`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server)
**v0.2.0**, which adds the native tools this release leans on (`block_fill_batch`,
`block_render_region`, `block_scan_summary`, `block_get_map_color`, auto-tiling
fills). Verified end-to-end against a live 26.1.2 world.

### Added

- **Voxel toolkit** (`tools/voxel/`, Python — stdlib + numpy + Pillow). Author a
  form as a parametric numpy model (`ellipsoid`/`cylinder`/`line3d`/`box`,
  fractional anchors, `mirror_x`), render three orthogonal views to PNG
  (`render_views`), and decompose it to a world-space fills list (`write_fills_json`,
  greedy maximal boxes split to ≤32k). A `building` palette maps voxel codes to
  block ids + RGB. Worked example + smoke test in `tools/examples/example_bean.py`.
  Deps documented in `tools/requirements.txt`; usage in `tools/README.md`.
- **Render-verify workflow** woven into `monument-builder` (+ new
  `reference/render-verify.md`), `inspector`, and `surveyor`: author → render →
  iterate vs. references → place via `block_fill_batch` → confirm with a
  scan-render (`block_render_region`). The "imported meshes are not authoritative"
  guardrail is spelled out.
- **`reference/engine-limits.md`** — one canonical, cross-skill list of hard tool
  limits and verified behaviour, cited by the orchestrator and block-placing skills.
- **Bean showcase image** in the README (`docs/images/bean.png`).

### Changed

- **Scale-pinning** added to the `planner` interview: fix the size ratio between
  co-located subjects before any blocks (a 70-tall vehicle beside an 18-tall
  figure forces rebuilds).
- **Engine-limits guidance corrected from live testing (26.1.2):** fills now
  auto-tile past 32,768 server-side (confirmed); datapack functions are **inert**
  (`function_run`/`/reload` do nothing — keep using direct block ops);
  `structure_file_write` writes a file but isn't loadable in-session (use
  `structure_save_from_world`/`structure_load_to_world`, which work).
- **`CLAUDE.md`** documents the new `tools/` Python layer (deps + smoke test) and
  the `reference/engine-limits.md` convention.

## [0.3.0] - 2026-05-21

Fold in lessons from a large multi-agent autonomous build (the "Aurelia
Exposition" overnight run), whose final QA revealed several skill-level gaps.
Skill-level changes only; still pairs with
[`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server)
v0.1.0.

### Changed

- **Registry has a single writer.** The orchestrator now solely owns
  `mcbuilder:registry`; the `worker` and `blueprinter` report their results as
  text instead of calling `data_storage_set` themselves. Parallel sub-agents
  writing the shared document were clobbering each other's entries. Updated in
  `minecraft-builder` (workflow + state model), `worker`, `blueprinter`, and
  `philosopher`.
- **Datapack functions: resolving ≠ executing.** Every place that recommends
  `function_run` / `schedule_function` / `/reload` (`engineer` skill and
  `reference/design-patterns.md`, `planner`, `monument-builder`'s
  `display-entities.md`, and the orchestrator's Conduct) now requires a
  smoke-test that the function actually runs before planning around it — the mod
  has been seen to accept the call but refuse execution (`/function` → "should
  not run", `/reload` → `successCount 0`). Never generate `.mcfunction` files
  expecting `/function` to run them; emit direct block ops instead. The
  `terraforming` heightmap method now spells this out (a heightmap baked into a
  function that never runs leaves terrain patchy).
- **Loaded ≠ ticking.** The `engineer` skill and
  `reference/setblock-redstone-limits.md`, plus the orchestrator's honesty
  contract, now distinguish immediate redstone updates (which resolve) from the
  scheduled block-tick queue (pistons, hoppers, comparator container-reads, lamp
  turn-*off*, crop growth), which **freezes on an idle/unfocused single-player
  client even in a force-loaded chunk**. Verify tick-driven mechanisms by an
  immediate fire, not by waiting; they need a focused client or dedicated server
  to run. `philosopher` surfaces this as an outstanding step for unattended
  builds.
- **`block_get_top_y` semantics.** The `surveyor` now confirms, once per survey,
  whether the tool returns the stand-on (air) Y vs. the solid-block Y (observed:
  solid = `result − 1`) and records the convention in `survey.toon`, so floors
  land flush instead of one block high.

### Added

- **Large / autonomous multi-site build discipline** in the `minecraft-builder`
  agent: a completion ledger gated on per-phase inspection (an element is
  `built` only after the inspector passes it), mandatory verification that the
  blueprinter actually persisted each template before any consumer references it
  (consumers alert rather than substitute), a ~3 background-sub-agent
  parallelism ceiling on non-overlapping zones, and an explicit rule never to
  report "done" until every planned element has a passing inspection.

## [0.2.0] - 2026-05-20

Optimize the builder skills for Java-exclusive techniques the Fabric mod's tool
surface exposes but Bedrock's MCP could not. Skill-level changes only; still
pairs with [`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server)
v0.1.0. Every technique below was verified live against the running server
before being documented; version-sensitive SNBT is flagged with
round-trip-verify guidance rather than asserted.

### Added

- **Display entities** — new `monument-builder/reference/display-entities.md`
  covering `text_display` (3D floating text and logos), `block_display` (blocks
  rendered at arbitrary scale / rotation / translation — sub-block detail,
  impossible angles, giant glowing forms), and `item_display`, with
  transformation/quaternion, billboard, brightness, and glow guidance. Wired
  into the `monument-builder` skill, catalog, and sculpting; signage pointers
  added to `transit-architect` and `city-planner`.
- **Direct block-entity NBT** (`block_entity_set_nbt`) — signs with text,
  banners, configured mob spawners, lecterns with books, decorated pots,
  player-head skulls, and pre-loaded containers — added to `building-architect`
  and `player-house` interiors and to `engineer` (pre-loaded
  dispensers/droppers/spawners).
- **Item components** — named / enchanted / lore / dyed items via `components`
  SNBT on `player_give_item` / `inventory_set_slot`, for museum displays,
  labeled storage, and stocked gear.
- **Scripted villagers** (`entity_summon` / `entity_set_nbt`) — exact
  profession, biome type, level, and full trade lists, documented in
  `village-planner` as complementary to the emergent village mechanics.
- **Loot-table seeding** (`loot_table_generate`) — believable container
  contents for villages, treasure/library rooms, and starter chests.
- **Datapack functions** (`function_run` / `schedule_function`) — a non-redstone
  path for timed sequences and animations in `engineer`, with the
  datapack-required caveat.
- **Biome-aware design** (`level_get_biome_at`) — read the real biome to drive
  palette, vegetation, and roof choices in `surveyor`, `planner`, and the
  terraforming / natural-landmarks / landscape palettes.
- **Event-based functional verification** (`events_subscribe` / `events_poll`)
  in `engineer` and `inspector`, plus two new `quality_contract` row types
  (`event_trigger`, `block_entity_nbt`) in the inspector's contract checks.

### Changed

- `engineer` gains `block_set_state` `update_flags` guidance — place a circuit
  dormant (flag `2`) versus self-starting (flag `3`).
- New `block-nbt` and `set-slot` plan operations, consistent across `planner`
  and `worker`; `place-structure` documents the exact `structure_load_to_world`
  enum strings (`rotation` none/clockwise_90/180/counterclockwise_90, `mirror`
  none/front_back/left_right, `integrity`, `include_entities`).

## [0.1.0] - 2026-05-20

Initial release of the **Minecraft Java** Claude plugin. Pairs with the
[`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server)
Fabric mod (v0.1.0) — the MCP server is embedded in the mod and runs inside Minecraft.

This plugin was forked from the Minecraft Bedrock Claude plugin and rewritten top to bottom
for Java Edition: the Bedrock `mc_*` tool surface is replaced by the Fabric mod's tool surface
(`level_*`, `block_*`, `entity_*`, `structure_*`, …), the four-phase setup is rebuilt around
Fabric and the mod jar (no dedicated server binary, no behavior pack, no Beta-APIs experiment),
and the builder's world-anchored state model now uses structure templates plus a command-storage
registry.

### Added

- Plugin manifest (`.claude-plugin/plugin.json`) and marketplace manifest
  (`.claude-plugin/marketplace.json`) — the repo is installable directly as a Claude Code
  plugin marketplace under the name `minecraft-java`.
- Four guided setup skills, run in order, that walk a user through standing up the stack on
  Java Edition: `setup-fabric` (Minecraft Java + Fabric loader, single-player or dedicated
  server), `install-mcp-mod` (the MCP mod jar + matching Fabric API jar), `setup-mcp-server`
  (the mod's `config.json`, launch, and `/healthz` verification, with bearer-token capture for
  remote setups), and `connect-claude` (register the server with Claude and verify with a live
  call). Single-player localhost is the default path; a dedicated Fabric server with auth is the
  advanced branch.
- `minecraft-mcp-setup` agent — orchestrates all four setup phases end to end in one continuous
  session, with the setup skills preloaded as per-phase procedures.
- `minecraft-builder` agent and seventeen model-tuned builder skills (`surveyor`, `researcher`,
  `planner`, `player-house`, `village-planner`, `city-planner`, `building-architect`, `engineer`,
  `monument-builder`, `landscape-architect`, `transit-architect`, `terraforming`,
  `natural-landmarks`, `blueprinter`, `worker`, `inspector`, `philosopher`) that survey, research,
  plan, shape, blueprint, build, inspect, and reflect — turning a request into a verified build
  in a live world.
- World-anchored state model: blueprints saved as named **structure templates**
  (`mcb:<project>_<element>`) and a registry stored in vanilla **command storage**
  (`mcbuilder:registry`, a TOON document) recording every build, so projects can be iterated
  later with no external state. Local `.minecraft-builder/` files are treated as ephemeral
  scratch (Markdown + TOON).
- `.mcp.json.example` — a secret-free reference template for registering the `minecraft-java`
  MCP server with Claude (no token for localhost single-player; bearer token via environment
  variable for remote/authenticated servers).
- CI workflow that validates the plugin, marketplace, skill, and agent files.
