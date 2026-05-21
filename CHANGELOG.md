# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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
