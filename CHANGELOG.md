# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `terraforming` skill — designs natural terrain and environments (mountains,
  valleys, rivers, lakes, coastlines, caves, biomes, weathering) using vetted
  landscaping technique, and writes the terrain phases into the build plan.
- A `reference/` library inside the terraforming skill — command-budget,
  landforms, water, biome palettes, and weathering — loaded on demand so
  technique detail does not bloat context until needed.

### Changed

- The `minecraft-builder` agent gained a `shape` step and now coordinates
  seven skills (survey → research → plan → shape → blueprint → build →
  reflect).
- The `planner` defers terrain phases to `terraforming` and keeps `fill` steps
  within the ~32,768-block volume limit; the `worker` executes pre-tiled fills
  without merging or splitting them.

## [0.2.0] - 2026-05-16

### Added

- `minecraft-builder` agent — coordinates a build pipeline in a live world:
  health-checks the MCP connection, recovers project state from the world, and
  runs survey → research → plan → blueprint → build → reflect.
- Six builder skills, each tuned to a model suited to its job: `surveyor` and
  `researcher` (Sonnet, forked), `planner` (Opus), `blueprinter` (Sonnet),
  `worker` (Haiku, forked), and `philosopher` (Sonnet).
- World-anchored state model: blueprints saved as named structure files and a
  `mcbuilder:registry` world dynamic property (TOON) recording every build, so
  projects can be iterated later with no external state. Local
  `.minecraft-builder/` files are treated as ephemeral scratch (Markdown +
  TOON).

## [0.1.0] - 2026-05-16

Initial release. Pairs with
[`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server)
v0.1.0 and
[`minecraft-bedrock-mcp-behavior-pack`](https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack)
v0.1.0 — install all three together.

### Added

- Plugin manifest (`.claude-plugin/plugin.json`) and marketplace manifest
  (`.claude-plugin/marketplace.json`) — the repo is installable directly as a
  Claude Code plugin marketplace.
- Four guided setup skills, run in order, that walk a user through standing up
  the whole stack: `setup-bedrock-server`, `setup-minecraft-world`,
  `setup-mcp-server`, and `connect-claude`.
- `minecraft-mcp-setup` agent — orchestrates all four setup phases end to end
  in one continuous session, with the setup skills preloaded as per-phase
  procedures.
- `.mcp.json.example` — a secret-free reference template for registering the
  `minecraft-bedrock` MCP server with Claude.
- CI workflow that validates the plugin, marketplace, skill, and agent files.
