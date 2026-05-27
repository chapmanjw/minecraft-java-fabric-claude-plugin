# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.8.0] - 2026-05-27

Deeper findings from continuing the parks-grand-loop build, with the v0.7.0 gates
already in place. Where 0.7.0 stopped a rogue orchestrator, 0.8.0 fixes how the
pipeline **sculpts and verifies blended terrain** — and pins down four hard engine
limits the build surfaced (chief among them a silent `block_replace_in_region`
truncation that caused most of the build's "mystery" reworks).

### Added

- **Continuous-field terrain primitive (`terrain.Centerline` +
  `HeightField.belt_from_path`).** Blended multi-region terrain is a *shape*
  problem: authoring each region as its own heightfield and butting them together
  makes a wall at every boundary, and dithering the seam blends colour, not shape.
  `Centerline` (polyline / closed loop with an arc-length + signed-perpendicular
  `(s, perp)` query) and `belt_from_path` (every cross-section parameter a
  continuous function of `s`, with a `protect` mask to spare a working
  rail/village) make the whole span one continuous field. New terraforming **hard
  rule 4** and a `landforms.md` § require it whenever ≥2 named regions must blend.
- **Eye-level verification for ride-through / walk-through builds.** Top-down /
  hillshade renders hide the vertical faces a rider sees — the parks-loop "snow
  re-skin" and "blending done" both passed a top-down look and were walls from the
  cart. The `inspector` now renders iso + an eye-level slice and records a
  `rider_pov` row; terraforming, the orchestrator honesty contract, and
  `build-harness.md` state that top-down is for flat-pattern checks only.
- **Generated-placement-script execution mode.** `build-harness.md` documents
  driving a paced parametric placement script (`mcp_place.py`: 8192-entry paging +
  ~60 rpm pacing + 429 backoff) as a first-class mode for forms too large to be one
  structure template; `engine-limits.md` Throughput names the 429 backoff.

### Changed

- **Harness tiles `block_replace_in_region`.** It silently truncates at ~32,768
  blocks/call (it is *not* auto-tiled server-side like `block_fill_region`) — the
  root cause of most of the build's "the replace did nothing" reworks. `harness.py`
  now tiles every `replace` under the cap (`_tile_box`); `engine-limits.md` and the
  `worker` document that fills auto-tile but replace does not.
- **Structural re-sculpt = base + detail-restoration phases.** Terraforming and the
  orchestrator now treat a rebuild as separable layers — continuity in the base,
  richness in detail: inventory existing detail before regenerating, drive
  detailers from `(s, perp)`, and warn before a rebuild regresses a liked
  dimension.
- **Engineer: powered rails + stray entities.** A `redstone_block` underneath a
  powered rail doesn't compute on this mod and `block_fill_batch` fires no
  neighbour update, so set `powered=true` explicitly via `block_set_state`; and
  clear stray minecarts/mobs (the #1 false "broken rail") before/after every ride
  test. Documented in `verification.md` and `setblock-redstone-limits.md`.
- **More verified engine limits (`engine-limits.md`).** `block_fill_columns` does
  not clear above the new surface (clear to air first); `block_replace_in_region`
  and `level_place_feature` no-op on unloaded chunks while `block_get_top_y`
  returns −64 there; never `forceload remove all` (it unloads spawn chunk 0,0 and
  killed a persistent always-day command block); and gamerule ids must be
  **snake_case** on MC 26.x (camelCase is rejected — get the live id from
  `level_list_game_rules`; a repeating command block remains the bulletproof
  always-day path).

## [0.7.0] - 2026-05-25

Verification-gate hardening from the parks-loop post-mortem — an unattended build
that freelanced past every skill and quality gate, shipped stacked box-fill
"terrain", self-approved its own renders as "verified", and left every build
beyond render distance of spawn. This release turns the pipeline's "shoulds" into
enforced gates, with mechanical backstops at the surfaces a rogue orchestrator
still touches (the registry and the final report).

### Added

- **Perceivability gate (`harness.py perceivable`).** Checks every `built`/`partial`
  registry element against world spawn and **fails (exit 1)** when nothing is within
  render distance (~200 blocks) of spawn, or when a far element has no registered
  connecting transit. Catches the "spawn in an empty world, every build beyond
  render distance" outcome before the user does. `--threshold` and `--spawn`
  override the defaults.
- **Verify tokens + registry audit (`harness.py audit`).** `verify`/`build` mint a
  content-hash `vt_…` token only on a real PASS (a phase that checked nothing mints
  none); the `mcbuilder:registry` build row gains a `verify_token` cell and
  `status:built` is only legitimate with one. `audit` flags every `built` row whose
  token is missing or malformed — a self-approved build that never passed an
  independent verification.
- **Terrain anti-pattern lint.** `run`/`build` refuse (exit 1) a phase that reads as
  organic terrain when it is stacked Y-banded rectangular slab-fills (the banned
  "ziggurat") or carries no `quality_contract` terrain row. `--force` overrides for a
  genuinely rectilinear build. The machine backstop for terraforming hard-rule 1; it
  does not trip on a building's floor stack.

### Changed

- **Autonomy keeps the gates on.** The orchestrator and `large-builds.md` now state
  that autonomous / `/loop` mode relaxes only *waiting on the user* — never the
  inspector, offline render-verify, prototype, or `quality_contract` checks — and that
  the loop iteration boundary is a gate (no next element until the previous is `built`
  with a token).
- **Hard delegation gate + router rules.** New "orchestrator freelancing terrain"
  adversarial defense, and terraforming's two hard rules (heightmap-or-live-sculpt,
  never stacked rectangles; you cannot see the world) lifted into the Step 0c
  complexity router so they are encountered at classification time, not buried in a
  skill that was never opened.
- **Worker** relays the verify token in its report and refuses to `--force` past a
  lint refusal (that override is an orchestrator decision).
- Registry schema documents the `verify_token` column; `reference/build-harness.md`
  and `non-negotiable-enforcement.md` document the lint, the token gate, and the
  audit/perceivable commands.

## [0.6.0] - 2026-05-25

Token-usage optimization + dedicated/headless-server support.

### Added

- **Build + verify harness (`tools/builder/`).** Executes a `plan.toon` phase and
  mechanically verifies it against the live server **outside the LLM context** —
  `plan.toon` `steps` are the code, `acceptance` + `quality_contract` are the
  assertions, the harness is the test runner, and it returns one compact digest
  instead of hundreds of in-context tool calls. Subcommands: `run`, `verify`,
  `build`, plus `mode` (dedicated-vs-single-player detection) and `selftest`
  (write-readiness). Stdlib-only (a minimal TOON reader, an MCP HTTP client, the
  runner, and the verifier). See `tools/README.md` and
  `reference/build-harness.md`.
- **Force-load bracketing.** `run`/`build` wrap each phase in `forceload
  add`/`remove`, auto-banded under the 256-chunk/dimension cap — mandatory on a
  dedicated server where writes silently no-op in unloaded chunks. Plans may
  declare per-phase `envelopes`; the harness derives them from step coordinates
  otherwise. The force-load is held across both `run` and `verify`.
- **Rate-limit resilient.** The MCP client backs off and retries on HTTP 429/503,
  so the verifier's many small reads ride out the per-client `rate_limit_rpm`
  instead of crashing. Functional `event_trigger` checks return **SKIP** (not
  FAIL) on a headless server — entity/block events don't fire for MCP-driven
  actions with no player tracking the chunk — deferring that check to a
  player-present session.
- **Validated end-to-end** against a live dedicated server: all nine plan ops
  (fill/set/replace/clone/place-structure/spawn/block-nbt/set-slot/run) and all
  contract checks (acceptance, walkability, doors, headroom, block_mix_ratios,
  silhouette, edge_irregularity, connectivity, foundation_naturalised,
  water_continuity, block_entity_nbt, event_trigger).
- **New references:** `reference/build-harness.md`, `reference/startup-and-recovery.md`
  (server-mode detection + recovery tree), `reference/large-builds.md` (the
  multi-zone/unattended playbook, extracted from the agent).

### Changed

- **Models routed off Opus where reasoning isn't needed.** `blueprinter`,
  `philosopher`, and `natural-landmarks` now run **forked** (Sonnet, isolated
  context) instead of inline on the orchestrator. `philosopher` returns drafted
  memory lessons for the orchestrator to persist (it has no memory access when
  forked); `natural-landmarks` returns a proposed composition for the orchestrator
  to confirm palette/scale with the user.
- **Orchestrator runs at `effort: high`** (was inheriting the session default) —
  routing/sequencing/bookkeeping doesn't need max effort; design skills still pin
  their own.
- **`worker` drives the harness** (`harness.py build`) as the primary path, with a
  documented in-context fallback that force-loads the declared envelope.
- **`inspector` consumes the harness's mechanical verdict** and focuses on what a
  script can't judge — world fit, functional behaviour, and whether a
  representational build *reads* (renders + the perceptual call).
- **Step 0 detects the operating mode** (samples `gameTime` at 0 players) instead
  of always asking for a player; the "ticking freezes when unfocused" warning is
  now single-player-conditional (a dedicated server ticks 24/7).
- **Registry records each build's force-load envelope** and whether it was
  released, so a later session reloads the exact area to iterate.
- **`researcher` is WebFetch-first** (out-of-context extraction) and pulls exact
  dimensions from Wikipedia/Wikidata REST endpoints — no new MCP dependency.
- **`planner` pins the `acceptance` table schema and an optional `envelopes`
  block** the harness consumes.
- **`reference/engine-limits.md`** gains a consolidated force-load / headless-write
  section (the read-masks-write footgun).
- Trimmed the orchestrator steering file by moving situational sections (recovery
  tree, large-build playbook) to on-demand references.

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
