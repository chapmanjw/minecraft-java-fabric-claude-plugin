# Minecraft Bedrock — Claude Plugin

A [Claude Code](https://code.claude.com) plugin that gives Claude **agent
skills** and an **agent** for driving a live Minecraft Bedrock world through
the [`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server).

It does two things:

1. **Guided setup** — skills and an agent that walk you, step by step, through
   standing up the whole stack: a Bedrock Dedicated Server, a compatible world,
   the bridge behavior pack, the MCP server, and the connection to Claude.
2. **Building in the world** — a `minecraft-builder` agent that surveys,
   researches, plans, blueprints, builds, and reflects, coordinating a set of
   model-tuned skills to design and construct elements in a live world.

## The stack

This plugin is the Claude-facing piece of a three-repository system:

| Repository | Role |
| ---------- | ---- |
| [`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server) | The MCP server. Bridges MCP clients to the world. |
| [`minecraft-bedrock-mcp-behavior-pack`](https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack) | The BDS behavior pack. Runs inside the world and executes commands. |
| **`minecraft-bedrock-claude-plugin`** (this repo) | The Claude plugin — skills and agents that use the MCP tools. |

```
Claude (Code / Desktop)
   |  MCP over Streamable HTTP
minecraft-bedrock-mcp-server
   |  HTTP long-poll
bedrock-bridge behavior pack
   |  @minecraft/server Script API
the Minecraft world
```

## ⚠️ Built on an experimental API

The underlying stack depends on Mojang's Bedrock **Script API**, including the
*beta* modules `@minecraft/server-net` and `@minecraft/server-admin`. A Bedrock
update can change or remove these. Pin your Bedrock Dedicated Server to a
known-good version and keep the server, behavior pack, and MCP server upgraded
together. Treat the whole stack as experimental.

## Install

Add this repo as a plugin marketplace and install the plugin:

```
/plugin marketplace add chapmanjw/minecraft-bedrock-claude-plugin
/plugin install minecraft-bedrock@minecraft-bedrock-claude
```

Then restart Claude Code. The skills appear under `/minecraft-bedrock:*` and
the `minecraft-mcp-setup` and `minecraft-builder` agents become available for
delegation.

## Setup skills

The four setup skills are meant to be run **in order**. Each one ends by
handing off to the next.

| Skill | Phase | What it covers |
| ----- | ----- | -------------- |
| `setup-bedrock-server` | 1 | Download, install, and configure a Bedrock Dedicated Server. |
| `setup-minecraft-world` | 2 | Create a Beta-APIs world, transfer it to the server, install the behavior pack. |
| `setup-mcp-server` | 3 | Install and configure the MCP server, configure the behavior pack, start everything, verify the handshake. |
| `connect-claude` | 4 | Register the MCP server with Claude and verify with a live tool call. |

To start a fresh setup, just ask Claude to set up a Minecraft Bedrock server
for MCP — the first skill triggers automatically — or invoke it explicitly:

```
/minecraft-bedrock:setup-bedrock-server
```

## Builder skills

Sixteen skills make up the build pipeline. Each runs on the model best suited
to its work — heavy reasoning where it pays off, a small model for mechanical
execution. The `minecraft-builder` agent invokes them in order; you can also
invoke any one directly.

| Skill | Role | Model |
| ----- | ---- | ----- |
| `surveyor` | Investigates the world — terrain, biomes, existing builds, surroundings. | Sonnet |
| `researcher` | Researches real-world references for faithful recreation. | Sonnet |
| `planner` | Captures requirements, interviews the user, produces a fully-resolved plan. | Opus |
| `player-house` | Designs a player's base of operations — adaptive interview, iterated blueprints, full plan. | Opus |
| `village-planner` | Designs functional villages and settlements, reusing standard building types. | Opus |
| `city-planner` | Designs whole cities and districts — urban fabric, zoning, streets, transit, vernacular reuse. | Opus |
| `building-architect` | Designs specific named buildings — real-world and fictional replicas, originals. | Opus |
| `engineer` | Designs and verifies complex redstone and mechanical contraptions — Bedrock-correct, with functional tests. | Opus |
| `monument-builder` | Designs monuments and build-art — statues, creatures, abstract sculpture, pixel art, logos. | Opus |
| `landscape-architect` | Designs intentionally designed outdoor space — formal gardens, parks, plazas, courtyards, hedge mazes. | Opus |
| `terraforming` | Designs natural terrain and environments — mountains, water, biomes — using vetted landscaping technique. | Inherit |
| `natural-landmarks` | Composes recognizable real-world natural wonders from a library of formation primitives. | Sonnet |
| `blueprinter` | Turns the plan into named, reusable structure files in the world. | Sonnet |
| `worker` | Executes the plan step by step — mechanical, no redesign. | Haiku |
| `inspector` | Verifies each build phase in-world and proposes course corrections. | Sonnet |
| `philosopher` | Reviews the finished job and records process lessons in project memory. | Sonnet |

The `terraforming`, `natural-landmarks`, `player-house`, `village-planner`,
`city-planner`, `building-architect`, `engineer`, `monument-builder`, and
`landscape-architect` skills each carry a `reference/` library — landforms,
water, palettes, weathering, formation primitives, wonder recipes, rooms,
styles, layouts, village mechanics, urban zoning, vernacular modules,
architectural techniques, redstone contraptions, sculpting and pixel-art
technique, garden traditions, interview scripts, blueprint rendering — loaded
on demand so the detail never bloats context until it is needed.

## Agents

**`minecraft-mcp-setup`** — orchestrates the complete setup end to end. It runs
all four phases in one continuous session: checks prerequisites up front, works
each phase interactively, verifies every phase's checklist before advancing,
and carries forward the values later phases depend on (paths, tokens, host).

**`minecraft-builder`** — designs and constructs elements in a live world. It
health-checks the MCP connection (and points you at `minecraft-mcp-setup` if
the world isn't reachable), recovers existing project state from the world,
then coordinates the sixteen builder skills: survey → research → plan → shape →
blueprint → build → inspect → reflect. Delegate to it for anything beyond a trivial block change —
e.g. *"Build a lakeside village near the nearest player."*

Use the individual `/minecraft-bedrock:*` skills directly if you'd rather drive
one step yourself.

## State model

The builder keeps **persistent state in the Minecraft world**, not in your
workspace — a project folder is useful only while you're working in it, but the
world travels everywhere:

- **Blueprints** are saved as named structure files (`mcb_<project>_<element>`),
  so build elements can be placed, copied, and iterated later.
- A **registry** — a world dynamic property `mcbuilder:registry` holding a
  [TOON](https://toonformat.dev/) document — records every project and build
  (element, structure, coordinates, status, revision). Any future session reads
  it back and can pick up where the last left off.

Local files under `.minecraft-builder/<project>/` (requirements, survey, plan)
are treated as throwaway scratch — Markdown for prose, TOON for structured
data. The `philosopher` records only *process lessons* in project memory, never
build data.

## MCP connection

This plugin does **not** auto-register an MCP server, because the server is
remote and per-user (your own host and bearer token). The `connect-claude`
skill registers it for you. [`.mcp.json.example`](.mcp.json.example) in this
repo is a reference template showing the recommended secret-free pattern
(token via an environment variable).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and how to validate
changes, [CHANGELOG.md](CHANGELOG.md) for release history, and
[SECURITY.md](SECURITY.md) to report a vulnerability.

## License

MIT — see [LICENSE](LICENSE).
