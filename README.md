# Minecraft Bedrock — Claude Plugin

A [Claude Code](https://code.claude.com) plugin that gives Claude **agent
skills** and an **agent** for driving a live Minecraft Bedrock world through
the [`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server).

It does two things:

1. **Guided setup** — four skills that walk you, step by step, through standing
   up the whole stack: a Bedrock Dedicated Server, a compatible world, the
   bridge behavior pack, the MCP server, and the connection to Claude.
2. **End-to-end orchestration** — a `minecraft-mcp-setup` agent that runs all
   four setup phases from start to finish in one continuous session.

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
the `minecraft-mcp-setup` agent becomes available for delegation.

## Skills

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

## Agent

**`minecraft-mcp-setup`** — orchestrates the complete setup end to end. It runs
all four phases in one continuous session: checks prerequisites up front, works
each phase interactively, verifies every phase's checklist before advancing,
and carries forward the values later phases depend on (paths, tokens, host).
The four setup skills are preloaded into the agent as its per-phase procedures.

Delegate to it when you want the whole stack stood up without driving the
phases yourself — e.g. *"Set up the Minecraft Bedrock MCP stack for me."* Use
the individual `/minecraft-bedrock:*` skills instead if you'd rather do (or
re-do) a single phase on its own.

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
