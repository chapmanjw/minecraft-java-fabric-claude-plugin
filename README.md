<p align="center">
  <img src="docs/images/logo.png" width="200" alt="Minecraft Java Fabric MCP — Claude plugin logo">
</p>

# Minecraft Java — Claude Plugin

A [Claude Code](https://code.claude.com) plugin that gives Claude **agent
skills** and an **agent** for driving a live Minecraft Java Edition world
through the [`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server)
— a Fabric mod that embeds an MCP server inside Minecraft.

![A voxel mascot standing on a superflat world, built by the minecraft-builder agent](docs/images/bean.png)

*Built by the `minecraft-builder` agent: authored as a parametric voxel model,
render-checked against the design before placing, stamped into the world in a
single batch, then verified in-world — block-for-block.*

![Ghasticlawd, a voxel Ghast-and-Claude mascot, built in a live world](docs/images/ghasticlawd.png)

*And **Ghasticlawd** — the project's Ghast × Claude mascot — built the same way:
voxelized, render-verified against the design, then placed and confirmed in-world.*

It does two things:

1. **Guided setup** — skills and an agent that walk you, step by step, through
   standing up the whole stack: Minecraft Java with the Fabric loader, the MCP
   mod and its Fabric API dependency, the mod's configuration, and the
   connection to Claude.
2. **Building in the world** — a `minecraft-builder` agent that surveys,
   researches, plans, blueprints, builds, and reflects, coordinating a set of
   model-tuned skills to design and construct elements in a live world.

## The stack

This plugin is the Claude-facing piece of a two-repository system. The MCP
server is **embedded in the Fabric mod** and runs inside Minecraft itself —
there is no separate server process and no behavior pack.

| Repository | Role |
| ---------- | ---- |
| [`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server) | The Fabric mod. Embeds the MCP HTTP server and executes tool calls against the world on the server main thread. |
| **`minecraft-java-fabric-claude-plugin`** (this repo) | The Claude plugin — skills and agents that use the MCP tools. |

```
Claude (Code / Desktop)
   │  MCP over Streamable HTTP  (http://127.0.0.1:8765/mcp)
minecraft-java-fabric-mcp-server   ← Fabric mod; embeds the MCP server
   │  Minecraft server API + Fabric API  (on the main thread)
the Minecraft world
```

## ⚠️ Pin your versions

The mod ships a separate jar for each supported Minecraft version, built against
that version's Fabric API. A Minecraft or Fabric update can change the modding
surface the mod depends on. Pin your Minecraft version, your Fabric API jar, and
the mod jar to a matched, known-good set and upgrade them together. The mod's
release notes list the supported Minecraft versions (v0.1.0 supports **1.21.11,
26.1.1, and 26.1.2**). Treat the whole stack as experimental.

## Install

Add this repo as a plugin marketplace and install the plugin:

```
/plugin marketplace add chapmanjw/minecraft-java-fabric-claude-plugin
/plugin install minecraft-java@minecraft-java-claude
```

Then restart Claude Code. The skills appear under `/minecraft-java:*` and the
`minecraft-mcp-setup` and `minecraft-builder` agents become available for
delegation.

## Setup skills

The four setup skills are meant to be run **in order**. Each one ends by
handing off to the next. The default path is a **single-player** install on
localhost (no token, no firewall changes); each skill also covers the
**dedicated Fabric server** branch (LAN/remote, bearer-token auth).

| Skill | Phase | What it covers |
| ----- | ----- | -------------- |
| `setup-fabric` | 1 | Install Minecraft Java Edition and the Fabric loader — a single-player client or a headless dedicated server. |
| `install-mcp-mod` | 2 | Download the MCP mod jar and the matching Fabric API jar and install both into the `mods/` folder. |
| `setup-mcp-server` | 3 | Configure the mod's `config.json`, launch, and verify the embedded MCP server is listening (`/healthz`); capture the bearer token for remote setups. |
| `connect-claude` | 4 | Register the MCP server with Claude and verify with a live tool call. |

To start a fresh setup, just ask Claude to set up Minecraft Java for MCP — the
first skill triggers automatically — or invoke it explicitly:

```
/minecraft-java:setup-fabric
```

## Builder skills

Seventeen skills make up the build pipeline. Each runs on the model best suited
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
| `engineer` | Designs and verifies complex redstone and mechanical contraptions — Java-correct, with functional tests. | Opus |
| `monument-builder` | Designs monuments and build-art — statues, creatures, abstract sculpture, pixel art, logos. | Opus |
| `landscape-architect` | Designs intentionally designed outdoor space — formal gardens, parks, plazas, courtyards, hedge mazes. | Opus |
| `transit-architect` | Designs the connective network between builds — rail, roads, nether hubs, bridges, tunnels, docks. | Opus |
| `terraforming` | Designs natural terrain and environments — mountains, water, biomes — using vetted landscaping technique. | Inherit |
| `natural-landmarks` | Composes recognizable real-world natural wonders from a library of formation primitives. | Sonnet |
| `blueprinter` | Turns the plan into named, reusable structure templates in the world. | Sonnet |
| `worker` | Executes the plan step by step — mechanical, no redesign. | Haiku |
| `inspector` | Verifies each build phase in-world and proposes course corrections. | Sonnet |
| `philosopher` | Reviews the finished job and records process lessons in project memory. | Sonnet |

The `terraforming`, `natural-landmarks`, `player-house`, `village-planner`,
`city-planner`, `building-architect`, `engineer`, `monument-builder`,
`landscape-architect`, and `transit-architect` skills each carry a `reference/`
library — landforms, water, palettes, weathering, formation primitives, wonder
recipes, rooms, styles, layouts, village mechanics, urban zoning, vernacular
modules, architectural techniques, redstone contraptions, sculpting and
pixel-art technique, garden traditions, network topology and transit
engineering, interview scripts, blueprint rendering — loaded on demand so the
detail never bloats context until it is needed.

For representational and parametric builds (vehicles, creatures, statues),
`monument-builder` runs a **render-verify loop** backed by a bundled Python
voxel toolkit (`tools/voxel/`, stdlib + numpy + Pillow): author the form as a
parametric model, render three orthogonal views to PNG and check the silhouette
*before* placing a block, stamp the whole thing into the world in one
`block_fill_batch`, then confirm with an in-world `block_render_region`. See
[`tools/README.md`](tools/README.md). The agent can't see the world, and a
wrong silhouette can't be detailed away — so the cheap iteration happens on a
render first. (The bean above was built exactly this way.)

## Agents

**`minecraft-mcp-setup`** — orchestrates the complete setup end to end. It runs
all four phases in one continuous session: checks prerequisites up front, works
each phase interactively, verifies every phase's checklist before advancing,
and carries forward the values later phases depend on (paths, ports, token,
host).

**`minecraft-builder`** — designs and constructs elements in a live world. It
health-checks the MCP connection (and points you at `minecraft-mcp-setup` if
the world isn't reachable), recovers existing project state from the world,
then coordinates the seventeen builder skills: survey → research → plan → shape →
blueprint → build → inspect → reflect. Delegate to it for anything beyond a trivial block change —
e.g. *"Build a lakeside village near the nearest player."*

Use the individual `/minecraft-java:*` skills directly if you'd rather drive
one step yourself.

## State model

The builder keeps **persistent state in the Minecraft world**, not in your
workspace — a project folder is useful only while you're working in it, but the
world travels everywhere:

- **Blueprints** are saved as named structure templates (`mcb:<project>_<element>`)
  via the `structure_*` tools, so build elements can be placed, copied, and
  iterated later.
- A **registry** — vanilla command storage at `mcbuilder:registry`, holding a
  [TOON](https://toonformat.dev/) document (read/written with the
  `data_storage_*` tools) — records every project and build (element, structure,
  coordinates, dimension, status, revision). Any future session reads it back
  and can pick up where the last left off.

Local files under `.minecraft-builder/<project>/` (requirements, survey, plan)
are treated as throwaway scratch — Markdown for prose, TOON for structured
data. The `philosopher` records only *process lessons* in project memory, never
build data.

## MCP connection

This plugin does **not** auto-register an MCP server, because the endpoint and
posture are per-user (your own host, port, and — for remote setups — a bearer
token). The `connect-claude` skill registers it for you.

For a **single-player** install the mod listens on `http://127.0.0.1:8765/mcp`
with no authentication — just the URL is needed. For a **dedicated/remote**
server the mod generates a bearer token on first boot; pass it via an
environment variable so it stays out of version control.
[`.mcp.json.example`](.mcp.json.example) in this repo is a reference template
showing both the no-auth localhost form and the token-via-env pattern.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and how to validate
changes, [CHANGELOG.md](CHANGELOG.md) for release history, and
[SECURITY.md](SECURITY.md) to report a vulnerability.

## License

MIT — see [LICENSE](LICENSE).
