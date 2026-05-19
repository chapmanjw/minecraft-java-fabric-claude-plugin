# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.5.0] - 2026-05-18

Replaces the 0.4.0 structure-upload path, which did not work on a dedicated
server. Needs
[`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server)
and
[`minecraft-bedrock-mcp-behavior-pack`](https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack)
v0.3.0.

### Changed

- The `blueprinter`'s third blueprint method now builds a structure with
  `mc_structure_create_from_blocks` — it sends a run-length-encoded block grid
  to the behavior pack, which builds a world-saved structure directly,
  immediately placeable. This replaces the 0.4.0 `mc_structure_upload` path,
  which wrote a `.mcstructure` file and relied on a world reload that does not
  re-index structure files on a dedicated server, and on a host-side file path
  unreachable from a remote client. The `reference/structure-upload.md` guide
  is rewritten as `reference/generated-structures.md`.
- `monument-builder` routes pixel-art grids and voxelized forms through
  `mc_structure_create_from_blocks`.

## [0.4.0] - 2026-05-18

Structure uploads. Build elements that are easier to compute than to lay by
hand — pixel-art murals, voxelized forms — can now be generated and uploaded
as `.mcstructure` files instead of placed block by block. Needs
[`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server)
and
[`minecraft-bedrock-mcp-behavior-pack`](https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack)
v0.2.0 for the `mc_structure_upload` and `mc_server_reload_world` tools.

### Added

- `blueprinter` gains a third blueprint method — generating a block-grid
  structure definition and uploading it with `mc_structure_upload`, alongside
  capture-from-world and the block-by-block loop. A new
  `reference/structure-upload.md` covers the definition format, ZYX index
  ordering, generating the grid with a script, and the world-reload
  requirement (`/reload all` needs an online player).

### Changed

- `monument-builder` routes a quantized pixel-art grid or a voxelized form
  through the `blueprinter`'s upload path rather than emitting it as thousands
  of `fill` / `set` rows in the plan.

## [0.3.0] - 2026-05-18

The build pipeline. Adds the `minecraft-builder` agent and a suite of
model-tuned builder skills that survey, research, plan, shape, blueprint,
build, inspect, and reflect — turning a request into a verified build in a
live world.

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
- `city-planner` skill — designs whole cities and city districts: real-world
  replicas (modern and historical), pop-culture replicas, and originals. Plans
  the urban fabric — district zoning, street hierarchy, transit, walls,
  reused vernacular building modules — defers every named landmark to
  `building-architect` via a handoff contract, can delegate functional
  quarters to `village-planner`, and works at district / whole-city /
  silhouette scales within Bedrock's limits.
- `engineer` skill — designs and verifies complex redstone and mechanical
  contraptions: item sorters, piston and hidden doors, automatic farms,
  mob-spawner collectors, minecart networks and roller coasters, elevators,
  note-block music, traps. Bedrock-correct — it refuses Java-only mechanics
  (quasi-connectivity, 0-tick pulses, BUD switches, TNT duping) — and ships
  every design with a functional in-world test recipe and a symptom →
  diagnosis → fix correction catalog.
- The `inspector` now runs the `engineer`'s functional test recipes
  (`inspection-recipe.toon`) in addition to its plan-fidelity and world-fit
  checks — a contraption that does not work fails inspection.
- `monument-builder` skill — designs monuments and build-art: giant statues,
  organic creatures, abstract sculpture, pixel art and murals, large 3D text
  and logos. Produces solid or shell-only figurative forms (no habitable
  interiors) using pixel-grid image mapping, organic-curve construction,
  voxelization, palette-gradient mapping (including the copper-oxidation
  chain), and armor-stand detailing. Coordinates with `natural-landmarks`
  (cliffs), `building-architect` (pedestals), and `terraforming` (plinths).
- `landscape-architect` skill — designs intentionally designed outdoor space:
  formal gardens, parks, plazas, courtyards, hedge mazes, fountains, parterres,
  topiary. Covers French formal, Italian, English landscape, Mughal, Japanese,
  Chinese, modernist, and other traditions. It is the geometric, intentional
  counterpart to the naturalistic `terraforming`, and coordinates heavily with
  `terraforming` (grading), `building-architect` (roofed structures),
  `monument-builder` (statuary), `engineer` (animated water), and
  `city-planner` (delegated plaza and park envelopes).
- `transit-architect` skill — designs the world-spanning connective network
  between builds: rail lines, roads and highways, nether-hub transit, bridges,
  tunnels, elevators, docks, and airports. Chooses the network topology
  (hub-and-spoke, mesh, ring, trunk-and-branch, nether hub) and routes the
  links, applying the nether 8:1 ratio and Bedrock rail and ice-boat
  mechanics. Owns static infrastructure only — redstone goes to `engineer`,
  station buildings to `building-architect`, grading to `terraforming`;
  `city-planner` covers streets within a city, `transit-architect` connects
  cities.
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

- The `minecraft-builder` agent now coordinates seventeen skills: it gained a
  `shape` step routing terrain work to `terraforming` (generic) or
  `natural-landmarks` (named wonders), routes the `plan` step to
  `player-house` for player bases, `village-planner` for settlements,
  `city-planner` for cities and districts, `building-architect` for specific
  named buildings and replicas, `engineer` for redstone and mechanical
  contraptions, `monument-builder` for statues and build-art,
  `landscape-architect` for designed outdoor space, or `transit-architect` for
  networks connecting sites, and runs the `build` step as a phase-by-phase
  build-and-inspect loop with the `inspector` for self-correction.
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
