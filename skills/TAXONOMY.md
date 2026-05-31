# Skill Taxonomy

The 28 skills of the minecraft-builder plugin, grouped by prefix namespace and
tier. Plugin skills are discovered flat (`skills/<name>/SKILL.md`); the prefix is
the namespace convention (they group in the `/` menu). The three-tier
orchestration model and the no-trivial routing rule are in
`../reference/orchestration/workflow-spine.md` and the `minecraft-builder` agent.

## Tiers

- **Tier 1** — the `minecraft-builder` *agent* (not a skill): routes every request
  to exactly one Tier-2 orchestrator; owns state, registry, gates.
- **Tier 2** — specialty **orchestrator** skills (`build-*`): inline (main-thread)
  domain playbooks that sequence Tier-3 leaves and thread the shared coherence
  context. Full coverage — every request maps to exactly one.
- **Tier 3** — **leaf** specialists: forked, single-purpose, return a result.

## The skills

| Skill | Group | Tier | model / context | Role |
|---|---|---|---|---|
| build-natural-world | build | 2 | opus / inline | Orchestrates terrain/landscape/wonder/cave regions |
| build-settlement | build | 2 | opus / inline | Orchestrates villages/cities/districts/building+grounds |
| build-structure | build | 2 | opus / inline | Orchestrates one sited building/replica/statue/house |
| build-systems | build | 2 | opus / inline | Orchestrates redstone/farms/transit + housing |
| survey-site | survey | 3 | sonnet / fork | Investigates the live world (terrain, biomes, builds) |
| survey-research | survey | 3 | sonnet / fork | Researches real refs incl. geology/ecology (terrain/research.md) |
| terrain-shape | terrain | 3 | sonnet / fork | Naturalistic terrain as a recipe (was terraforming) |
| terrain-landmark | terrain | 3 | sonnet / fork | Recognizable natural wonders (was natural-landmarks) |
| terrain-ecology | terrain | 3 | sonnet / fork | Planting/biome ecology + scatter recipe |
| terrain-integrate | terrain | 3 | sonnet / fork | Grounds a build into the world (GATE B; apron erosion) |
| terrain-cave | terrain | 3 | sonnet / fork | Designed subterranean space (caves/caverns/ravines) |
| design-house | design | 3 | opus / inline | Player base of operations |
| design-village | design | 3 | opus / inline | Settlements ≤ ~15 buildings (layout leaf) |
| design-city | design | 3 | opus / inline | Cities/districts ~16+ (layout leaf) |
| design-building | design | 3 | opus / inline | Specific named buildings/replicas |
| design-monument | design | 3 | opus / inline | Statues, sculpture, pixel art, logos |
| design-grounds | design | 3 | opus / inline | Designed outdoor space (gardens/plazas/mazes) |
| system-redstone | system | 3 | opus / inline | Redstone & mechanical contraptions (was engineer) |
| system-transit | system | 3 | opus / inline | Rail/road/nether-hub/bridge networks |
| exec-plan | exec | 3 | opus / inline | Requirements → plan.toon (was planner) |
| exec-blueprint | exec | 3 | sonnet / fork | Reusable mcb:* structure templates (was blueprinter) |
| exec-worker | exec | 3 | haiku / fork | Executes plan.toon via the harness (was worker) |
| exec-inspect | exec | 3 | sonnet / fork | Verifies each phase + seam check (GATE C; was inspector) |
| exec-reflect | exec | 3 | sonnet / fork | Drafts process lessons (was philosopher) |
| setup-fabric | setup | — | inherit / inline | Install Minecraft + Fabric (setup stack) |
| setup-mod | setup | — | inherit / inline | Install the MCP mod + Fabric API (was install-mcp-mod) |
| setup-server | setup | — | inherit / inline | Configure & launch the MCP server (was setup-mcp-server) |
| setup-connect | setup | — | inherit / inline | Register the server with Claude (was connect-claude) |

## Routing table (primary intent → Tier-2 orchestrator)

| Primary intent | Orchestrator |
|---|---|
| terrain, landform, biome, water, natural scenery, named natural wonder, caves | build-natural-world |
| village, city, district, town, a building **with grounds/context** | build-settlement |
| one named/standalone building, replica, statue/monument, player house, bridge-as-object | build-structure |
| redstone, farm, contraption, transit line, nether hub, mechanism | build-systems |

Cross-domain → route by primary intent (one inline orchestrator at a time; no
nested forking). There is **no trivial/inline path** — every request runs the full
gated pipeline, depth-scaled.

## Setup stack

The four `setup-*` skills are run in order by the separate `minecraft-mcp-setup`
agent (setup-fabric → setup-mod → setup-server → setup-connect), not by the
`minecraft-builder` build pipeline.

## Future skills (flagged, not built)

None outstanding for the build pipeline — `terrain-cave` (designed subterranean)
and `terrain-ecology` (planting) are now real skills. A `build-scene` orchestrator
was considered and folded into `build-structure`; split it out only if
build-structure grows too heavy.
