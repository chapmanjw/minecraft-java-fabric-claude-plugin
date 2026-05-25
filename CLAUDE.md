# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
node scripts/validate-plugin.mjs       # validate manifests, frontmatter, and skill/folder name alignment (Node 20+)
python -m pip install -r tools/requirements.txt   # one-time: deps for the voxel toolkit (numpy, Pillow)
python tools/examples/example_bean.py  # smoke-test the voxel toolkit (renders 3 PNGs + a fills JSON)
```

No build step for the markdown content — skills and agents are plain markdown
and take effect in the next Claude Code session after the plugin is reloaded.
The `tools/` directory adds a small **Python helper layer** (the `voxel`
toolkit) that the builder skills run locally; it is stdlib + numpy + Pillow only
and is referenced from skills via `${CLAUDE_PLUGIN_ROOT}/tools/…`. These helpers
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
- **Guided setup** — four ordered skills (`setup-fabric` → `install-mcp-mod` → `setup-mcp-server` → `connect-claude`) that walk a user through standing up the full stack on Java Edition.
- **World builder** — a `minecraft-builder` agent that coordinates 17 skills (survey → research → plan → blueprint → build → inspect → reflect) to design and construct elements in a live world.

### File structure

```
agents/                         ← agent steering files (.md with YAML frontmatter)
skills/<name>/SKILL.md          ← skill playbooks (.md with YAML frontmatter)
skills/<name>/reference/        ← reference libraries loaded on demand (not always present)
reference/engine-limits.md      ← cross-skill tool limits & verified behaviour (cited by all block-placing skills)
tools/builder/                  ← Python build+verify harness: execute a plan.toon phase + run acceptance/quality_contract checks against the live server, outside the LLM (stdlib only: toon reader, MCP client, runner, verifier)
tools/voxel/                    ← Python voxel toolkit: author → render → decompose → place (numpy + Pillow); mcp_place.py is the shared HTTP placer
tools/terrain/                  ← Python terrain toolkit: heightfield → erode → render-verify → materialize to fills (numpy + Pillow)
tools/requirements.txt          ← Python deps for tools/ (core: numpy + Pillow)
tools/requirements-mesh.txt     ← optional deps for the voxel mesh-import path (trimesh, scipy, networkx, lxml)
.claude-plugin/plugin.json      ← plugin manifest
.claude-plugin/marketplace.json ← marketplace manifest
.mcp.json.example               ← reference MCP config template
scripts/validate-plugin.mjs     ← CI validation script
```

### Adding a skill

1. Create `skills/<kebab-name>/SKILL.md` with the required YAML frontmatter (`name`, `description`; `model` where the skill pins one).
2. The `name` field must exactly match the folder name.
3. Reference it in the relevant agent's `skills:` frontmatter list.
4. Run `node scripts/validate-plugin.mjs` — it catches missing/mismatched names and bad frontmatter.

### Key conventions

- Skill bodies are instructions to Claude, not docs for the user.
- A skill's `description` determines when Claude invokes it — make it concrete and specific.
- The four setup skills must stay runnable in order, each handing off to the next.
- Tool references use the Java MCP surface (`level_*`, `block_*`, `entity_*`, `structure_*`, `data_storage_*`, …) under the server name **`minecraft-java`** — never the Bedrock `mc_*` names.
- Bundled helper scripts live under `tools/` and are referenced from skills via `${CLAUDE_PLUGIN_ROOT}/tools/…`. Keep them **stdlib + numpy + Pillow only** (the agreed dependency posture); document any dependency in `tools/requirements.txt` and have a script degrade with a clear "run `pip install …`" message rather than failing opaquely. Hard tool limits are documented once in `reference/engine-limits.md` — cite it rather than restating limits per skill.
- Keep the Minecraft version, Fabric API jar, the MCP mod jar, and the values referenced in these skills in lockstep — the mod is built per Minecraft version.

## Releasing

Bump `version` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` together, add a dated section to `CHANGELOG.md`, and tag the commit (`vX.Y.Z`).
