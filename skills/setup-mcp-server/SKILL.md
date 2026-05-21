---
name: setup-mcp-server
description: >-
  Step 3 of 4 of the Minecraft Java MCP setup. Configure the MCP mod's
  config.json (host, port, auth, tool categories), launch Minecraft or the
  dedicated server, verify the embedded MCP server is listening on /healthz,
  and capture the bearer token for remote setups. Use when the user has the MCP
  mod and Fabric API installed and needs the MCP server configured and running.
---

# Configure and run the MCP server (Step 3 of 4)

This is **Phase 3** of the four-phase Minecraft Java MCP setup. It assumes
Phase 2 (`install-mcp-mod`) is done: the MCP mod jar and Fabric API jar are in
`mods/`. The MCP server is embedded in the mod, so "running the MCP server"
means launching Minecraft (single-player) or the dedicated server.

Work interactively. Branch on the choice from Phase 1: **single-player** is
mostly defaults; **dedicated/remote** needs a config file and a token.

## Where config lives

The mod reads `config/minecraft_fabric_mcp/config.json` under the game
directory:

- **Single-player:** `<.minecraft>/config/minecraft_fabric_mcp/config.json`.
- **Dedicated server:** `<server>/config/minecraft_fabric_mcp/config.json`.

The file is **optional** — it's only needed to override defaults. Any field can
also be overridden by an environment variable named `MCP_<FIELD>` (e.g.
`MCP_PORT`, `MCP_AUTH_REQUIRED`).

The defaults are deliberately safe: bind `127.0.0.1`, port `8765`, **no auth**,
reject all cross-origin browser requests.

---

## Single-player branch — defaults are enough

For Claude running on the **same machine** as Minecraft, you do **not** need a
config file. The mod listens on `http://127.0.0.1:8765/mcp` with no token.

### Step 1 — Launch

Have the user start the Fabric profile in the Minecraft Launcher and load any
world. (At least one loaded world is needed — many tools act on the world or
relative to a player.)

### Step 2 — Verify it's listening

Check the game log for:

```
[minecraft_fabric_mcp] MCP server listening at http://127.0.0.1:8765 (host=127.0.0.1, port=8765, auth=false, tls=false)
```

Then the liveness probe (no auth required for `/healthz`):

```sh
curl http://localhost:8765/healthz
# → {"status":"ok"}
```

If `/healthz` answers, Phase 3 is done — skip to **Wrap up**. There is no token
for this path.

---

## Dedicated / remote branch — config + token

Use this when Claude connects from another machine, or you want LAN/internet
access. (If Claude runs on the *same host* as the dedicated server, you can use
the single-player defaults above and skip the config file.)

### Step 1 — Write `config.json`

Create `<server>/config/minecraft_fabric_mcp/config.json`:

```json
{
  "host": "0.0.0.0",
  "port": 8765,
  "allow_remote": true,
  "auth_required": true,
  "rate_limit_rpm": 120
}
```

Leave `bearer_token` unset — the mod generates a 256-bit token on first boot
and logs it once.

> **The mod refuses unsafe bindings.** Binding to a non-loopback host
> (`0.0.0.0` or a LAN IP) requires **both** `allow_remote: true` **and**
> `auth_required: true`. If either is missing, the mod errors at startup rather
> than exposing an unauthenticated world to the network. This is intentional —
> don't work around it.

Optional fields the user may want:

- `tls_cert_path` / `tls_key_path` — PEM cert + PKCS8 key for TLS at the mod
  (set **both** or neither). For internet-facing servers, use TLS here or
  terminate it at a reverse proxy. See the mod's `docs/security.md`.
- `included_categories` / `excluded_categories` — restrict the tool set by
  domain (`world`, `actors`, `gameplay`, `registries`, `server`).
- `exclude_write_tools: true` — read-only mode (drops every mutating tool).
- `command_timeout_ms` (default 15000) and `rate_limit_rpm` (default 60).

### Step 2 — Launch and capture the token

Start the server:

```sh
java -Xmx4G -jar fabric-server-launch.jar nogui
```

In the log, find the generated token (shown **once**):

```
[minecraft_fabric_mcp] Generated bearer token for MCP server. Save this value — it is shown only once:
[minecraft_fabric_mcp]   Authorization: Bearer 9c1f9a…
```

Have the user copy the token somewhere safe — Phase 4 needs it. To rotate it
later, delete `bearer_token` from `config.json` and restart. **Never commit the
token or the config file that contains it.**

### Step 3 — Run as a service (optional, recommended for 24/7)

For a deployment that survives logout and reboots, wrap the server as a
service: **systemd** on Linux, **NSSM** or Task Scheduler on Windows. The mod's
[`docs/setup-dedicated-server.md`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server/blob/main/docs/setup-dedicated-server.md)
has ready-to-paste `fabric-mcp.service` and NSSM commands plus a locked-down
`minecraft` user. Walk the user through it only if they want it now.

### Step 4 — Verify it's listening

```sh
curl http://<host>:8765/healthz
# → {"status":"ok"}
```

Use `localhost` if testing on the server itself, otherwise the host's LAN
IP/hostname. `/healthz` needs no auth even when `auth_required` is on, so a
plain `curl` confirms reachability independent of the token.

---

## Wrap up

Confirm with the user (the relevant set):

- [ ] **Single-player:** Minecraft launched with a world loaded; `/healthz` is
      OK on `http://localhost:8765`. No token.
- [ ] **Dedicated/remote:** `config.json` written with `allow_remote` +
      `auth_required`; server launched; bearer token captured; `/healthz` is OK
      on the host.

Hand off: Phase 3 is done — the world is reachable over MCP. The last step is
connecting Claude to it. Offer to continue with the **`connect-claude`** skill
now. For that step the user needs the **`/mcp` URL**
(`http://<host>:8765/mcp`) and, for a remote setup, the **bearer token**.
