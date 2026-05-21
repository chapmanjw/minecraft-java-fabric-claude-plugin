---
name: connect-claude
description: >-
  Step 4 of 4 of the Minecraft Java MCP setup. Register the running
  minecraft-java MCP server (the Fabric mod) with Claude (Claude Code or Claude
  Desktop) so the Java world tools become available, then verify the connection
  with a live test call. Use when the user has the MCP server running and needs
  to connect Claude to their Minecraft world.
---

# Connect Claude to the Minecraft world (Step 4 of 4)

This is the **final** phase of the Minecraft Java MCP setup. It assumes Phase 3
(`setup-mcp-server`) is done: the mod is running and `/healthz` returns OK.

Before starting, get from the user:

- **The `/mcp` URL** — `http://<host>:<port>/mcp`, e.g.
  `http://localhost:8765/mcp`. Use `localhost` only if Claude runs on the same
  machine as Minecraft; otherwise the host's LAN IP or hostname. If the mod
  uses TLS, the scheme is `https`.
- **The bearer token** — only for a dedicated/remote setup (the token captured
  in Phase 3). A single-player localhost setup has **no token**.

> **Name the server `minecraft-java`.** The builder agent and skills in this
> plugin expect MCP tools under that name (`mcp__minecraft-java__*`). Use
> exactly `minecraft-java` as the server name below.

Ask the user which Claude they're connecting: **Claude Code** (CLI / IDE
extension) or **Claude Desktop**. Follow the matching section.

## Connecting Claude Code

The mod speaks the **Streamable HTTP** transport, which Claude Code supports
natively. Use `claude mcp add`.

**Single-player / localhost (no token):**

```sh
claude mcp add --transport http minecraft-java "http://localhost:8765/mcp"
```

**Dedicated / remote (with token):**

```sh
claude mcp add --transport http minecraft-java "http://<host>:8765/mcp" \
  --header "Authorization: Bearer <token>"
```

Pick a scope with `-s`: `local` (default, this project only), `project`
(shared via a committed `.mcp.json`), or `user` (all projects on this machine).
For a personal setup, `user` is usually what the user wants: `-s user`.

**Do not commit the token.** If the user wants project scope on a remote setup,
write `.mcp.json` with the token pulled from an environment variable instead of
inlining it. This plugin ships `.mcp.json.example` showing that pattern:

```json
{
  "mcpServers": {
    "minecraft-java": {
      "type": "http",
      "url": "${MINECRAFT_MCP_URL:-http://localhost:8765/mcp}",
      "headers": { "Authorization": "Bearer ${MINECRAFT_MCP_TOKEN}" }
    }
  }
}
```

For localhost single-player, drop the `headers` block entirely — just the
`type` and `url` are needed.

After adding it, the user restarts Claude Code (or reloads the window in the
IDE extension). Confirm the server shows up with `claude mcp list` or `/mcp` —
it should report `minecraft-java` as connected.

## Connecting Claude Desktop

Two options:

**A — Native custom connector (preferred, if the user's Claude Desktop has
it).** In **Settings → Connectors**, add a custom connector with the URL
`http://<host>:8765/mcp`. For a remote setup, add a header
`Authorization: Bearer <token>`; for localhost, no header.

**B — Via the `mcp-remote` adapter.** Edit Claude Desktop's config file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Localhost (no token):

```json
{
  "mcpServers": {
    "minecraft-java": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8765/mcp"]
    }
  }
}
```

Remote (with token):

```json
{
  "mcpServers": {
    "minecraft-java": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://<host>:8765/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ],
      "env": {
        "AUTH_HEADER": "Bearer <token>"
      }
    }
  }
}
```

The token goes through the `AUTH_HEADER` env var so its space (`Bearer <space>token`)
isn't mangled by argument parsing. Then **fully restart** Claude Desktop — the
tools appear under the tools (🔌) menu once it reconnects.

## Verify the connection

A registered server isn't a working one — confirm with a **live call**:

1. Make sure at least one world is loaded (and, ideally, a player is in it —
   many tools act relative to players or the world).
2. Call **`server_get_status`** — it needs no arguments and no player. A
   successful response (Minecraft version, TPS, online player count, loaded
   dimensions) means the chain is up: Claude → MCP server (the mod) → world.
   Then `level_get_info` with `dimension: "minecraft:overworld"` confirms
   world-level reads work.
3. As a visible smoke test, run `command_execute` with `say MCP connected` and
   confirm the user sees the message in the in-game chat.

If a call fails:

- **Auth / 401** — wrong or missing token on a remote setup, or a stray space
  in the header. (`/healthz` works without auth, so a 401 on tool calls but a
  healthy `/healthz` points squarely at the token.)
- **Connection refused / timeout** — the mod isn't running (no world loaded /
  server down), wrong host:port, or a firewall between Claude and the host.
- **Tools connect but calls error about no world / no player** — load a world
  and have a player join, then retry.

## Wrap up

Once `server_get_status` returns cleanly, the setup is complete:

- [ ] `minecraft-java` MCP server registered with Claude.
- [ ] Java tools (`level_*`, `block_*`, `entity_*`, …) visible.
- [ ] A live test call succeeded against the world.

Tell the user they're done — all four phases are complete. Suggest next steps:

- Try a simple prompt: *"What's the time and weather? Set it to clear midday."*
- Try building: *"Build a small stone-brick house near the nearest player."*
  Claude works through the Java MCP tools to plan and place blocks in the world.
