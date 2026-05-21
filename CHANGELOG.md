# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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
