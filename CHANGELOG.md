# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `terraforming` skill — designs natural terrain and environments (mountains,
  valleys, rivers, lakes, coastlines, caves, biomes, weathering) using vetted
  landscaping technique, and writes the terrain phases into the build plan.
- `natural-landmarks` skill — composes recognizable real-world natural wonders
  (Grand Canyon, Niagara, Uluru, Halong Bay, Giant's Causeway, …) from a
  library of reusable formation primitives, enforcing signature features and
  minimum recognition scale.
- `player-house` skill — designs a player's base of operations through an
  adaptive interview, proposes ASCII / Markdown-table / Mermaid blueprints,
  iterates with the user until approved, then writes the build plan. Covers
  rooms, architectural styles, layouts, special-site environments (underwater,
  mountainside, cave, sky, nether, end), functional systems, storage, and
  interiors.
- `village-planner` skill — designs functional villages and settlements
  (hamlets to standard villages), reusing standard Minecraft building types
  adapted to the biome and the request. Proposes layout options, iterates with
  the user, and respects Bedrock village mechanics (iron golems, beds,
  workstations, bells, raids, breeding, cats).
- `building-architect` skill — designs specific named buildings: real-world
  replicas (historical and modern), pop-culture replicas, user-described
  originals, and generative-style fictional buildings. Uses deep research with
  citations for real-world targets, resolves the book/film/game adaptation
  conflict for fictional ones, applies advanced building technique, and leans
  on a reusable structure-module library so detailed builds stay tractable.
- A `spawn` plan operation (`mc_entity_spawn`) so plans can place villagers,
  animals, and other entities; the `worker` executes it.
- `inspector` skill — verifies a build in-world after each phase: checks the
  plan was carried out, that the result fits the world cleanly (no dangling
  edges, blocked paths, or unintended overrides), and proposes course
  corrections. Runs after every major phase as the build's self-correction
  checkpoint; its corrections are logged for the `philosopher`.
- A `reference/` library inside the `terraforming`, `natural-landmarks`, and
  `player-house` skills — command-budget, landforms, water, palettes,
  weathering, formation primitives, wonder recipes, rooms, styles, layouts,
  environments, utilities, interiors, interview scripts, and blueprint
  rendering — loaded on demand so detail does not bloat context until needed.

### Changed

- The `minecraft-builder` agent now coordinates twelve skills: it gained a
  `shape` step routing terrain work to `terraforming` (generic) or
  `natural-landmarks` (named wonders), routes the `plan` step to
  `player-house` for player bases, `village-planner` for settlements, or
  `building-architect` for specific named buildings and replicas, and runs the
  `build` step as a phase-by-phase build-and-inspect loop with the `inspector`
  for self-correction.
- The `planner` defers terrain phases to the terrain specialists and keeps
  `fill` steps within the ~32,768-block volume limit; the `worker` executes
  pre-tiled fills without merging or splitting them.
- The `philosopher` checks natural-wonder builds against the
  `natural-landmarks` signature-feature anti-pattern checklist.

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
