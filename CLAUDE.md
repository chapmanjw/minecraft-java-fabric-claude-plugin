# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
node scripts/validate-plugin.mjs       # validate manifests, frontmatter, and skill/folder name alignment (Node 20+)
python -m pip install -r tools/requirements.txt   # one-time: deps for the voxel + terrain toolkits (numpy, Pillow, scipy; optional opensimplex)
python tools/examples/example_bean.py  # smoke-test the voxel toolkit (renders 3 PNGs + a fills JSON)
```

No build step for the markdown content — skills and agents are plain markdown
and take effect in the next Claude Code session after the plugin is reloaded.
The `tools/` directory adds a small **Python helper layer** (the `voxel` and
`terrain` toolkits) that the builder skills run locally; the `voxel` toolkit is
numpy + Pillow, the `terrain` toolkit adds scipy (+ optional opensimplex), and
the `builder` harness is stdlib-only. They are referenced from skills via
`${CLAUDE_PLUGIN_ROOT}/tools/…`. These helpers
run in **Claude Code** (CLI or desktop app), where the agent has local Bash and
can read the PNGs they produce.

## Architecture

This is the Claude-facing piece of a two-repository system. The MCP server is **embedded in the Fabric mod** and runs inside Minecraft — there is no separate server process and no behavior pack.

```
Claude (Code / Desktop)
  │ MCP over Streamable HTTP (http://127.0.0.1:8765/mcp)
minecraft-java-fabric-mcp-server   ← Fabric mod; embeds the MCP server
  │ Minecraft server API + Fabric API (on the main thread)
the Minecraft world
```

The plugin adds two things:
- **Guided setup** — four ordered skills (`setup-fabric` → `setup-mod` → `setup-server` → `setup-connect`) that walk a user through standing up the full stack on Java Edition.
- **World builder** — a `minecraft-builder` agent that, for **every** request (no
  trivial/inline path), routes to one of four **Tier-2 specialty orchestrator**
  skills (`build-natural-world`, `build-settlement`, `build-structure`,
  `build-systems`), which sequence the **Tier-3 leaf** skills (`survey-*`,
  `terrain-*`, `design-*`, `system-*`, `exec-*`) through one gated pipeline. **28
  skills total** — see `skills/TAXONOMY.md`.

### The three-tier, no-trivial model (0.9.0)

- **Tier 1** — the `minecraft-builder` agent: routes to exactly one orchestrator,
  owns state/registry/gates. Never builds inline.
- **Tier 2** — `build-*` orchestrators (opus, **inline**): domain playbooks that
  sequence leaves and thread the **coherence context** (one datum, one continuous
  terrain recipe, one palette, one biome+scatter plan, one integration pass) so
  builds cohere. Inline so each leaf still forks independently. Contract in
  `reference/orchestration/coherence.md` + `workflow-spine.md`.
- **Tier 3** — leaf skills: forked, single-purpose.
- **No trivial path.** Every request runs the full gated spine
  (survey→research→plan→shape→ecology→blueprint→build→**integrate**→inspect→
  register→reflect); depth scales, the three gates never drop:
  **GATE A** offline `tools/terrain/verify.py` (ziggurat/seam/relief),
  **GATE B** `terrain-integrate` (ground the footprint), **GATE C** `exec-inspect`
  + harness lint (seam + quality_contract).

### Terrain core (`tools/terrain/`)

Terrain is authored as a **recipe** (a composable sampler graph), verified offline,
and materialized via **`block_fill_columns`** (one server call — not a 3-D voxel
grid). Pipeline: recipe → `HeightField.from_graph` → erosion → biome/seam blend →
masks → `MaterialSpec` (layer+slant) → scatter → verify → emit. API in
`reference/terrain/toolkit-api.md`; method in `reference/terrain/method.md`. Deps:
numpy, Pillow, **scipy** (core), **opensimplex**; optional **numba**
(`tools/requirements-perf.txt`). Run tests: `cd tools && python -m pytest terrain/tests`.

### File structure

```
agents/                         ← agent steering files (.md with YAML frontmatter)
skills/<name>/SKILL.md          ← skill playbooks (.md with YAML frontmatter)
skills/<name>/reference/        ← reference libraries loaded on demand (not always present)
reference/execution/engine-limits.md  ← cross-skill tool limits & verified behaviour (cited by all block-placing skills)
tools/builder/                  ← Python build+verify harness: execute a plan.toon phase + run acceptance/quality_contract checks against the live server, outside the LLM (stdlib only: toon reader, MCP client, runner, verifier)
tools/voxel/                    ← Python voxel toolkit: author → render → decompose → place (numpy + Pillow); mcp_place.py is the shared HTTP placer
tools/terrain/                  ← Python terrain toolkit: heightfield → erode → render-verify → materialize to fills (numpy + Pillow)
tools/requirements.txt          ← Python deps for tools/ (core: numpy + Pillow + scipy; optional opensimplex)
tools/requirements-mesh.txt     ← optional deps for the voxel mesh-import path (trimesh, scipy, networkx, lxml)
.claude-plugin/plugin.json      ← plugin manifest
.claude-plugin/marketplace.json ← marketplace manifest
.mcp.json.example               ← reference MCP config template
scripts/validate-plugin.mjs     ← CI validation script
```

### Adding a skill

1. Create `skills/<prefix>-<name>/SKILL.md` with YAML frontmatter (`name` =
   folder; `description`; `model`/`context` per the tier). Use a namespace prefix
   (`setup-/survey-/build-/terrain-/design-/system-/exec-`); the validator enforces it.
2. A terrain leaf must **link** `reference/terrain/` (never copy the method); a
   `build-*` orchestrator must be `model: opus`, inline (no `context: fork`).
3. Add it to `skills/TAXONOMY.md` and the `minecraft-builder` routing if Tier-2.
4. Run `node scripts/validate-plugin.mjs` — it checks names, prefixes, tier rules,
   the taxonomy, and the shared reference cores.

A one-shot renamer for the prefixed scheme lives at `scripts/migrate-skills.mjs`
(old→new map of the 0.9.0 rename).

### Key conventions

- Skill bodies are instructions to Claude, not docs for the user.
- A skill's `description` determines when Claude invokes it — make it concrete and specific.
- The four setup skills must stay runnable in order, each handing off to the next.
- Tool references use the Java MCP surface (`level_*`, `block_*`, `entity_*`, `structure_*`, `data_storage_*`, …) under the server name **`minecraft-java`** — never the Bedrock `mc_*` names.
- The mod groups its 183 tools into ten domain categories (`blocks`, `structures`, `world`, `entities`, `players`, `items`, `gameplay`, `scripting`, `registries`, `server`) and tags each `read`/`write`/`admin`. With no config it registers a lean ~102-tool default: the seven default-on domains (`blocks`, `structures`, `world`, `entities`, `items`, `scripting`, `server`) capped at `write`. **The builder runs entirely within this default-on set** — it never needs an opt-in domain or admin access, except occasional read-only calls into `gameplay` / `registries`. The taxonomy and how to widen the surface live in the `setup-server` skill; the surface note for builds is in `reference/execution/engine-limits.md`.
- Bundled helper scripts live under `tools/` and are referenced from skills via `${CLAUDE_PLUGIN_ROOT}/tools/…`. Dependency posture: the `builder` harness is stdlib-only; the `voxel` toolkit is numpy + Pillow; the `terrain` toolkit adds scipy (+ optional opensimplex). Document any dependency in `tools/requirements.txt` and have a script degrade with a clear "run `pip install …`" message rather than failing opaquely. Hard tool limits are documented once in `reference/execution/engine-limits.md` — cite it rather than restating limits per skill.
- Keep the Minecraft version, Fabric API jar, the MCP mod jar, and the values referenced in these skills in lockstep — the mod is built per Minecraft version.

## Releasing

Bump `version` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` together, add a dated section to `CHANGELOG.md`, and tag the commit (`vX.Y.Z`).
