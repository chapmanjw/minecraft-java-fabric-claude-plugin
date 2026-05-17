---
name: setup-mcp-server
description: >-
  Step 3 of 4 of the Minecraft Bedrock MCP setup. Install the
  minecraft-bedrock-mcp-server, generate its bearer tokens, write its .env,
  configure the behavior pack's permissions/variables/secrets files, start BDS
  and the MCP server, and verify the bridge handshake. Use when the user has a
  Bedrock server and a world with the behavior pack installed and needs the MCP
  server running.
---

# Install and run the MCP server (Step 3 of 4)

This is **Phase 3** of the four-phase Minecraft Bedrock MCP setup. It assumes
Phase 2 (`setup-minecraft-world`) is done. You should have, written down:

- the **world path**, e.g. `/opt/bedrock-server/worlds/mcp-world`
- the **behavior-pack path**, e.g. `<world>/behavior_packs/bedrock-bridge`

If either is missing, get it before continuing. The MCP server runs on the
**same host as BDS** and needs **Node.js 20+** there — verify with `node -v`.

## How the pieces talk

The MCP server exposes two authenticated surfaces:

- `/mcp` — what Claude connects to (Phase 4), guarded by `BRIDGE_CLIENT_TOKEN`.
- `/bridge` — what the behavior pack long-polls, guarded by `BRIDGE_AGENT_TOKEN`.

So there are **two separate tokens**. Keep them straight: the client token is
for Claude, the agent token is for the behavior pack inside the world.

## Step 1 — Install the MCP server

On the BDS host:

```sh
npm install -g minecraft-bedrock-mcp-server
```

Alternatives, if the user prefers: `npx minecraft-bedrock-mcp-server` (no
install), or the Docker image
`ghcr.io/chapmanjw/minecraft-bedrock-mcp-server:latest` (`docker run --env-file
.env -p 8765:8765 ...`). Pin to a version tag for reproducibility, and keep it
aligned with the BDS and behavior-pack versions.

## Step 2 — Generate the two tokens

Generate two long random secrets:

```sh
openssl rand -hex 32   # -> BRIDGE_CLIENT_TOKEN
openssl rand -hex 32   # -> BRIDGE_AGENT_TOKEN
```

On Windows without `openssl`:

```powershell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
```

Have the user keep both values somewhere safe. They are needed again in this
phase and in Phase 4.

## Step 3 — Write the MCP server `.env`

Create a `.env` file for the MCP server (this plugin ships `.mcp.json.example`
in its repo root as a reference, but the server's own `.env` is what matters
here):

```sh
BRIDGE_CLIENT_TOKEN=<first secret>
BRIDGE_AGENT_TOKEN=<second secret>
BRIDGE_WORLD_PATH=<the world path from Phase 2>
BRIDGE_BEHAVIOR_PACK_PATH=<the behavior-pack path from Phase 2>
BRIDGE_HOST=0.0.0.0
BRIDGE_PORT=8765
```

Other variables (`BRIDGE_TLS_CERT`/`BRIDGE_TLS_KEY`, `BRIDGE_TRUST_PROXY`,
rate limits, etc.) have defaults; leave them unless the user has a reason. The
full reference is in the
[MCP server README](https://github.com/chapmanjw/minecraft-bedrock-mcp-server#configuration-reference).

> **TLS:** the bridge carries bearer tokens and world data. On anything beyond
> a fully trusted LAN, set `BRIDGE_TLS_CERT`/`BRIDGE_TLS_KEY` or terminate TLS
> at a reverse proxy. For a first local setup, plain HTTP is acceptable — note
> the server logs a warning when running without TLS.

## Step 4 — Configure the behavior pack

The pack reads config from the BDS scripting config directory:
`<bds>/config/default/`. Create that folder and add **three files**. The
behavior pack repo ships copy-ready versions under its `config/default/`.

**`permissions.json`** — lets the pack load its Script API modules:

```json
{
  "allowed_modules": ["@minecraft/server", "@minecraft/server-net", "@minecraft/server-admin"]
}
```

**`variables.json`** — where the bridge listens. This is the MCP server's
`/bridge` surface. If the pack and server are on the same host, `localhost` is
right:

```json
{ "bridge_url": "http://localhost:8765" }
```

**`secrets.json`** — the bridge token. The value is the **full `Authorization`
header**: the literal word `Bearer`, a space, then the `BRIDGE_AGENT_TOKEN`
(the *second* secret):

```json
{ "bridge_agent_token": "Bearer <the BRIDGE_AGENT_TOKEN second secret>" }
```

> The `Bearer ` prefix **must** be inside the stored secret. The pack receives
> an opaque secret handle it cannot read or concatenate, so the scheme prefix
> has to travel as part of the secret value itself. This is the single most
> common setup mistake — double-check it.

Never commit `secrets.json` anywhere.

## Step 5 — Start everything

Start the **MCP server first**, so the bridge is listening when the world
loads, then BDS.

### Option A — foreground (quick test)

```sh
# Terminal 1 — MCP server (reads .env from the working directory)
minecraft-bedrock-mcp-server

# Terminal 2 — Bedrock Dedicated Server
cd /opt/bedrock-server && LD_LIBRARY_PATH=. ./bedrock_server
```

On Windows: run `minecraft-bedrock-mcp-server` in one terminal (with `.env` in
the working directory) and `bedrock_server.exe` in another.

### Option B — long-lived service (recommended)

For a deployment that survives logout and restarts, install both as services.
On **Linux**, use `systemd` — the
[MCP server README, Step 7](https://github.com/chapmanjw/minecraft-bedrock-mcp-server#step-7--start-everything)
has ready-to-paste `bedrock-server.service` and `mc-mcp-server.service` units,
a dedicated `minecraft` user, and a locked-down `EnvironmentFile`. On
**Windows**, wrap each executable as a service with NSSM or a Task Scheduler
"at startup" task. In all cases, start the MCP server before BDS.

Walk the user through whichever they choose; don't paste the full systemd
units unless they pick Option B on Linux — then reproduce them from the README.

## Step 6 — Verify the handshake

When the world loads, the behavior pack handshakes with the bridge. Check:

1. **Liveness:** `curl http://localhost:8765/healthz` returns OK.
2. **MCP server log:** shows a successful bridge handshake.
3. **BDS log:** shows the `bedrock-bridge` pack's script starting.

If the handshake fails, the usual causes, in order of likelihood:

- **Token mismatch** — `bridge_agent_token` in `secrets.json` ≠ `Bearer ` +
  `BRIDGE_AGENT_TOKEN` in `.env`. Check the `Bearer ` prefix and for stray
  whitespace.
- **Wrong `bridge_url`** in `variables.json`, or the MCP server isn't running
  / isn't reachable on that host:port.
- **Behavior pack not active** — `world_behavior_packs.json` missing or wrong
  UUID, or the world wasn't created with **Beta APIs**.
- **`config/default/` in the wrong place** — it must be under the BDS root,
  not the world folder.

## Wrap up

Confirm with the user:

- [ ] MCP server installed and its `.env` written with both tokens and both
      paths.
- [ ] `permissions.json`, `variables.json`, `secrets.json` in
      `<bds>/config/default/`.
- [ ] MCP server and BDS both running (foreground or as services).
- [ ] `/healthz` is OK and the handshake succeeded in the logs.

Hand off: Phase 3 is done — the world is now reachable over MCP. The last step
is connecting Claude to it. Offer to continue with the **`connect-claude`**
skill now. The user will need the **`BRIDGE_CLIENT_TOKEN`** (the *first*
secret) and the server's host:port for that step.
