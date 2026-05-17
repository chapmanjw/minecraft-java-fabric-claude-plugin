---
name: setup-bedrock-server
description: >-
  Step 1 of 4 of the Minecraft Bedrock MCP setup. Install and configure a
  Minecraft Bedrock Dedicated Server (BDS) — the foundation the MCP stack runs
  on. Use when the user wants to set up a dedicated Minecraft Bedrock server,
  start setting up Minecraft for AI/MCP control from scratch, or asks how to
  get a Bedrock server running so Claude can build in it.
---

# Set up a Bedrock Dedicated Server (Step 1 of 4)

You are guiding the user through the **first** of four setup phases. Work
interactively: do one thing, confirm it worked, then move on. Do not dump the
whole procedure at once.

## The big picture — explain this first

The user is building a stack that lets Claude read and change a live Minecraft
world. It has four pieces, set up by four skills in order:

| Phase | Skill | What it does |
| ----- | ----- | ------------ |
| 1 | `setup-bedrock-server` (this one) | A Minecraft Bedrock Dedicated Server (BDS). |
| 2 | `setup-minecraft-world` | A world with the Beta APIs experiment, plus the bridge behavior pack. |
| 3 | `setup-mcp-server` | The `minecraft-bedrock-mcp-server`, configured and running. |
| 4 | `connect-claude` | Register the MCP server with Claude so the `mc_*` tools appear. |

Tell the user this is Phase 1, and that each phase ends by handing off to the
next. They need: a host for the server, Node.js 20+ on that host (used in
Phase 3), and a copy of Minecraft: Bedrock Edition on a PC/device (used once in
Phase 2 to create the world). Budget ~20–30 minutes total.

> **Experimental-API warning — say this out loud.** This stack depends on
> Mojang's Bedrock Script API, including the *beta* modules
> `@minecraft/server-net` and `@minecraft/server-admin`. A Bedrock update can
> change or remove these. Pin BDS to a known-good version, disable
> auto-update, and upgrade BDS, the behavior pack, and the MCP server together.

## Gather context

Ask the user, before downloading anything:

1. **What OS will the server run on?** BDS ships for **Linux** (Ubuntu is the
   well-trodden path) and **Windows**. Branch the instructions accordingly.
2. **Where does it run?** Same machine as Claude, another box on the LAN, or a
   cloud VM. This matters in Phase 4 for the URL Claude connects to — note
   their answer.

The MCP server (Phase 3) runs on the **same host** as BDS, so the host must
also have Node.js 20+. If it doesn't yet, that's fine — flag it for Phase 3.

## Step 1 — Download BDS

Send the user to the official download page and have them accept the EULA /
privacy prompts to reveal the link:
<https://www.minecraft.net/en-us/download/server/bedrock>

Have them pick the build matching their server OS. **Record the exact version
number** — it must be pinned and kept in lockstep with the behavior pack and
MCP server. BDS 1.21.0 or newer is required.

## Step 2 — Unzip it

**Linux (Ubuntu):**

```sh
sudo mkdir -p /opt/bedrock-server
sudo unzip bedrock-server-*.zip -d /opt/bedrock-server
sudo chown -R "$USER" /opt/bedrock-server
cd /opt/bedrock-server
```

**Windows:** extract the zip to a stable path with no spaces, e.g.
`C:\bedrock-server`. Avoid `Program Files` (the server writes files alongside
itself) and avoid OneDrive-synced folders.

Use this folder as `<bds>` for the rest of the setup. Record its absolute path.

## Step 3 — First test run

Run BDS once so it generates its default files (`server.properties`,
`worlds/`, `config/`, etc.), then stop it with `Ctrl+C`.

**Linux:**

```sh
LD_LIBRARY_PATH=. ./bedrock_server
```

If it reports a missing library:
`sudo apt-get update && sudo apt-get install -y libcurl4 unzip`.

**Windows:** double-click `bedrock_server.exe`, or run it from a terminal in
the folder.

Confirm with the user that it started, printed a few lines, and that the
`worlds/` and `config/` folders now exist. Then have them stop it — BDS must
not be running while later phases edit its files.

## Step 4 — Edit `server.properties`

Open `<bds>/server.properties` and set:

| Setting | Value | Why |
| ------- | ----- | --- |
| `level-name` | leave as-is for now | Phase 2 sets this to the MCP world's folder. |
| `allow-cheats` | `true` | Required for `mc_run_command` and command-backed tools. |
| `gamemode` | `creative` | Lets agents place, break, and spawn freely. |

Leave everything else at its defaults. Note for the user that `level-name`
gets its final value in Phase 2 once the world folder exists.

## Wrap up

Confirm with the user:

- [ ] BDS is downloaded, version recorded, and auto-update is not relied on.
- [ ] It ran once and generated `worlds/` and `config/`.
- [ ] `allow-cheats=true` and `gamemode=creative` are set.
- [ ] BDS is currently **stopped**.

Then hand off: tell the user Phase 1 is done and the next step is creating a
compatible world and installing the behavior pack. Offer to continue with the
**`setup-minecraft-world`** skill now.
