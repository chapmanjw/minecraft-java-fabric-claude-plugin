# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
node scripts/validate-plugin.mjs   # validate manifests, frontmatter, and skill/folder name alignment (Node 20+)
```

No build step — all files are plain markdown. Changes take effect in the next Claude Code session after the plugin is reloaded.

## Architecture

This is the Claude-facing piece of a three-repository system:

```
Claude (Code / Desktop)
  │ MCP over Streamable HTTP
minecraft-bedrock-mcp-server        ← MCP server / bridge
  │ HTTP long-poll
minecraft-bedrock-mcp-behavior-pack ← BDS behavior pack
  │ @minecraft/server Script API
the Minecraft world
```

The plugin adds two things:
- **Guided setup** — four ordered skills (`connect-claude` → `setup-bedrock-server` → `setup-minecraft-world` → `setup-mcp-server`) that walk a user through standing up the full stack.
- **World builder** — a `minecraft-builder` agent that coordinates 17 skills (survey → research → plan → blueprint → build → inspect → reflect) to design and construct elements in a live world.

### File structure

```
agents/                         ← agent steering files (.md with YAML frontmatter)
skills/<name>/SKILL.md          ← skill playbooks (.md with YAML frontmatter)
skills/<name>/references/       ← reference libraries loaded on demand (not always present)
.claude-plugin/plugin.json      ← plugin manifest
.claude-plugin/marketplace.json ← marketplace manifest
.mcp.json.example               ← reference MCP config template
scripts/validate-plugin.mjs     ← CI validation script
```

### Adding a skill

1. Create `skills/<kebab-name>/SKILL.md` with the required YAML frontmatter (`name`, `description`, `model`).
2. The `name` field must exactly match the folder name.
3. Reference it in the relevant agent's `skills:` frontmatter list.
4. Run `node scripts/validate-plugin.mjs` — it catches missing/mismatched names and bad frontmatter.

### Key conventions

- Skill bodies are instructions to Claude, not docs for the user.
- A skill's `description` determines when Claude invokes it — make it concrete and specific.
- The four setup skills must stay runnable in order, each handing off to the next.
- Keep BDS version, behavior pack, MCP server, and skill references (UUIDs, versions) in lockstep.

## Releasing

Bump `version` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` together, add a dated section to `CHANGELOG.md`, and tag the commit (`vX.Y.Z`).
