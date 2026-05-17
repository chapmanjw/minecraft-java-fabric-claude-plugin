---
name: connect-claude
description: >-
  Step 4 of 4 of the Minecraft Bedrock MCP setup. Register the running
  minecraft-bedrock-mcp-server with Claude (Claude Code or Claude Desktop) so
  the mc_* tools become available, then verify the connection with a live test
  call. Use when the user has the MCP server running and needs to connect
  Claude to their Minecraft world.
---

# Connect Claude to the Minecraft world (Step 4 of 4)

This is the **final** phase of the Minecraft Bedrock MCP setup. It assumes
Phase 3 (`setup-mcp-server`) is done: the MCP server is running and its bridge
handshake with the world succeeded.

Before starting, get two things from the user:

- **The `/mcp` URL** — `http://<host>:<port>/mcp`, e.g.
  `http://localhost:8765/mcp`. Use `localhost` only if Claude runs on the same
  machine as the MCP server; otherwise use the host's LAN IP or hostname. If
  the MCP server uses TLS, the scheme is `https`.
- **The `BRIDGE_CLIENT_TOKEN`** — the *first* secret from Phase 3 (the client
  token, **not** the agent token).

> **Name the server `minecraft-bedrock`.** The builder agent and skills in this
> plugin expect MCP tools under that name (`mcp__minecraft-bedrock__mc_*`).
> Use exactly `minecraft-bedrock` as the server name below.

Ask the user which Claude they're connecting: **Claude Code** (CLI / IDE
extension) or **Claude Desktop**. Follow the matching section.

## Connecting Claude Code

The MCP server speaks the **Streamable HTTP** transport, which Claude Code
supports natively. The simplest path is the `claude mcp add` command:

```sh
claude mcp add --transport http minecraft-bedrock "http://<host>:8765/mcp" \
  --header "Authorization: Bearer <BRIDGE_CLIENT_TOKEN>"
```

Pick a scope with `-s`: `local` (default, this project only), `project`
(shared via a committed `.mcp.json`), or `user` (all projects on this
machine). For a personal setup, `user` is usually what the user wants:
`-s user`.

**Do not commit the token.** If the user wants project scope, write the
`.mcp.json` with the token pulled from an environment variable instead of
inlining it. This plugin ships `.mcp.json.example` in its repo root showing
that pattern:

```json
{
  "mcpServers": {
    "minecraft-bedrock": {
      "type": "http",
      "url": "${MINECRAFT_MCP_URL:-http://localhost:8765/mcp}",
      "headers": { "Authorization": "Bearer ${MINECRAFT_MCP_TOKEN}" }
    }
  }
}
```

With that, the user sets `MINECRAFT_MCP_URL` and `MINECRAFT_MCP_TOKEN` in their
environment and the committed file stays secret-free.

After adding it, the user restarts Claude Code (or reloads the window in the
IDE extension). Confirm the server shows up with `claude mcp list` or
`/mcp` — it should report `minecraft-bedrock` as connected.

## Connecting Claude Desktop

Two options:

**A — Native custom connector (preferred, if the user's Claude Desktop has
it).** In **Settings → Connectors**, add a custom connector with the URL
`http://<host>:8765/mcp` and a header `Authorization: Bearer <BRIDGE_CLIENT_TOKEN>`.

**B — Via the `mcp-remote` adapter.** Edit Claude Desktop's config file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add under `mcpServers`:

```json
{
  "mcpServers": {
    "minecraft-bedrock": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://<host>:8765/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ],
      "env": {
        "AUTH_HEADER": "Bearer <BRIDGE_CLIENT_TOKEN>"
      }
    }
  }
}
```

The token goes through the `AUTH_HEADER` env var so its space isn't mangled by
argument parsing. Then **fully restart** Claude Desktop — the `mc_*` tools
appear under the tools (🔌) menu once it reconnects.

## Verify the connection

A registered server isn't a working one — confirm with a **live call**:

1. Make sure at least one player is in the world (many tools act relative to
   players or the world origin).
2. Call **`mc_world_get_info`** (or `mc_server_get_status`). A successful
   response — time, weather, dimensions — means the full chain is up: Claude →
   MCP server → bridge → behavior pack → world.
3. As a visible smoke test, call `mc_world_send_message` with a short greeting
   and confirm the user sees it in the in-game chat.

If a call fails:

- **Auth / 401** — wrong token, or the agent token was used instead of the
  client token. The client token is the *first* secret from Phase 3.
- **Connection refused / timeout** — MCP server not running, wrong host:port,
  or a firewall between Claude and the host.
- **Tools connect but calls hang or error about the bridge** — the world side
  is down: re-check the Phase 3 handshake (BDS running, behavior pack active,
  `secrets.json` token).

## Wrap up

Once `mc_world_get_info` returns cleanly, the setup is complete:

- [ ] `minecraft-bedrock` MCP server registered with Claude.
- [ ] `mc_*` tools visible.
- [ ] A live test call succeeded against the world.

Tell the user they're done — all four phases are complete. Suggest next steps:

- Try a simple prompt: *"What's the time and weather? Set it to clear midday."*
- Try building: *"Build a small stone-brick house near the nearest player."*
  Claude works through the `mc_*` tools to plan and place blocks in the world.
