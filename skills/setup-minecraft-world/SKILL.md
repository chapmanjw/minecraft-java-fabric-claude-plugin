---
name: setup-minecraft-world
description: >-
  Step 2 of 4 of the Minecraft Bedrock MCP setup. Create a Minecraft world with
  the Beta APIs experiment enabled, export it, transfer it onto the dedicated
  server, and install + activate the bedrock-bridge behavior pack. Use when the
  user has a Bedrock Dedicated Server ready and needs a compatible world and
  the behavior pack installed.
---

# Create the world and install the behavior pack (Step 2 of 4)

This is **Phase 2** of the four-phase Minecraft Bedrock MCP setup. It assumes
Phase 1 (`setup-bedrock-server`) is done: BDS is unzipped, has run once, and is
currently stopped.

Work interactively — confirm each step before the next. BDS must stay
**stopped** throughout; you are editing files inside its world folder.

## Why the world must be created in the Minecraft client

The behavior pack needs the **Beta APIs** experiment. That toggle can *only* be
set when a world is created in the **Minecraft client** — the dedicated server
cannot enable it, and it travels with the world afterward. So the user creates
the world on a PC/device, then moves it to the server.

Confirm the user has Minecraft: Bedrock Edition on a PC or device.

## Step 1 — Create the world in the Minecraft client

In Minecraft: Bedrock Edition, choose **Create New World** and set:

| Setting | Value | Why |
| ------- | ----- | --- |
| **Game Mode** | Creative | Agents place/break blocks and spawn entities freely. |
| **Cheats** (Activate Cheats) | On | Enables commands; pairs with `allow-cheats` on the server. |
| **Experiments → Beta APIs** | **On** | **Required.** `@minecraft/server-net` / `-admin` are beta modules. |

Have the user give the world a clear name. Then **play the world once** for a
few seconds so it is fully written to disk, and exit.

## Step 2 — Export the world

In Minecraft, on the worlds list, open the world's settings (the pencil icon)
and choose **Export World**. This produces a `.mcworld` file — which is just a
ZIP archive under a different extension.

Have the user copy that `.mcworld` file to the BDS host (`scp`, a USB drive, a
file share — whatever fits their setup from Phase 1).

## Step 3 — Transfer the world into BDS

Pick a folder name for the world under `<bds>/worlds/` — `mcp-world` is a good
default. Unzip the `.mcworld` into it.

**Linux:**

```sh
cd /opt/bedrock-server/worlds
mkdir "mcp-world"
unzip ~/exported-world.mcworld -d "mcp-world"
```

**Windows (PowerShell):** rename the file to `.zip` (or use Expand-Archive
directly), then:

```powershell
$dest = "C:\bedrock-server\worlds\mcp-world"
New-Item -ItemType Directory -Force $dest
Expand-Archive -Path "$HOME\Downloads\exported-world.mcworld" -DestinationPath $dest
```

Verify the world folder directly contains `level.dat` and a `db/` folder (not a
nested subfolder). If it's nested one level deep, move the contents up.

Now set `level-name` in `<bds>/server.properties` to the folder name:

```
level-name=mcp-world
```

**Record the world's absolute path** — e.g.
`/opt/bedrock-server/worlds/mcp-world` or `C:\bedrock-server\worlds\mcp-world`.
Phase 3 needs it.

## Step 4 — Get the behavior pack

The behavior pack is the **bedrock-bridge** pack from a separate repository:
<https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack>

Two ways to get it:

- **Download** `bedrock-bridge.mcpack` from that repo's
  [Releases](https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack/releases).
  An `.mcpack` is just a ZIP — unzip it to get the pack folder.
- **Build it** — clone the repo and run `npm install && npm run build`.

Either way, the pack is the folder containing `manifest.json`,
`scripts/main.js`, and `pack_icon.png`. If the local clone is on this machine
(it may be a sibling folder of this plugin repo), you can use it directly.

> Keep the pack version aligned with the BDS version and the MCP server version
> — the experimental Script API requires the three to move together.

## Step 5 — Install the pack into the world

Place the pack folder at `<world>/behavior_packs/bedrock-bridge/`.

**Linux:**

```sh
mkdir -p "/opt/bedrock-server/worlds/mcp-world/behavior_packs"
cp -r bedrock-bridge "/opt/bedrock-server/worlds/mcp-world/behavior_packs/"
```

**Windows (PowerShell):**

```powershell
$bp = "C:\bedrock-server\worlds\mcp-world\behavior_packs"
New-Item -ItemType Directory -Force $bp
Copy-Item -Recurse .\bedrock-bridge $bp
```

## Step 6 — Activate the pack on the world

Create (or edit) `<world>/world_behavior_packs.json` so BDS loads the pack:

```json
[{ "pack_id": "fa013817-66f2-4a5f-a724-1347f912bd40", "version": [0, 2, 0] }]
```

`pack_id` is the pack's header UUID — use exactly the value above. If the pack
you downloaded reports a different version in its `manifest.json`, match the
`version` array to it.

**Record the pack's absolute path** — e.g.
`<world>/behavior_packs/bedrock-bridge`. Phase 3 needs it too.

## Wrap up

Confirm with the user:

- [ ] World created in the Minecraft client with **Beta APIs**, Creative, and
      Cheats on; played once.
- [ ] World exported and unzipped under `<bds>/worlds/`, with `level.dat` at
      its top level.
- [ ] `level-name` in `server.properties` points at the world folder.
- [ ] `bedrock-bridge` pack folder is at `<world>/behavior_packs/bedrock-bridge`.
- [ ] `world_behavior_packs.json` exists with the pack UUID.
- [ ] World path and behavior-pack path are written down.

Hand off: Phase 2 is done. The next step installs and configures the MCP
server and starts everything. Offer to continue with the **`setup-mcp-server`**
skill now.
