# Startup, server-mode detection & recovery

The orchestrator's Step 0 cites this file. It covers (1) detecting whether the
world is a **dedicated/headless** server or a **single-player integrated** one,
(2) the connection recovery tree, and (3) the write-readiness self-test. Read it
when `server_get_status` fails, or when you need to know whether a player is
required.

## Detect the operating mode (do this once per session)

A **dedicated server** ticks 24/7 with nobody online and keeps almost nothing
write-loaded without a `forceload`. A **single-player integrated** server needs a
player in-world *and* the client focused (ticks freeze when unfocused). The build
rules differ, so classify first.

The mechanical test (the harness does this for you):

```sh
python ${CLAUDE_PLUGIN_ROOT}/tools/builder/harness.py mode
```

It samples overworld `gameTime` twice ~1s apart at 0 players:

- **gameTime advances → DEDICATED / unpaused.** Players are optional. Do **not**
  ask the user to join. The only loaded area is what you `forceload` (plus
  spawn), so plan to force-load every work envelope. Mechanisms tick headlessly.
- **gameTime frozen at 0 players → SINGLE-PLAYER integrated.** Ask the user to
  join *and keep the Minecraft window focused* — the scheduled block-tick queue
  freezes when the client is idle/unfocused, freezing pistons, hoppers,
  comparator container-reads, redstone-lamp turn-*off*, and crop growth.

If the install dir is known (e.g. `C:\fabric-mcp`), also read `server.properties`
and report `pause-when-empty-seconds` (must be `0` or `-1` for unattended),
`player-idle-timeout` (`0` recommended), and `spawn-protection` (note the radius
if non-zero). When the dir is unknown, infer pause behaviour from the gameTime
test.

## Write-readiness self-test (dedicated mode)

A successful **read** does not prove a **write** will land — `block_get_state`
loads chunks on demand, but `block_set_state`/fills only affect already-loaded
chunks and **silently no-op** otherwise. Confirm writes up front:

```sh
python ${CLAUDE_PLUGIN_ROOT}/tools/builder/harness.py selftest
```

It force-loads a scratch column, places a marker, reads it back, restores it, and
releases the force-load. `write_readiness: OK` means headless writes work.

## Connection recovery tree

`server_get_status` (or `level_get_info` for `minecraft:overworld`) is the
liveness check. If it fails:

```
CHECK 1: Is the MCP server reachable?
  curl -sf http://localhost:8765/healthz   (use the configured host/port)
  FAIL → The mod isn't serving. Minecraft isn't running, no world is loaded
         (single-player), or the dedicated server is down. Ask the user to
         launch Minecraft and load a world (or start the server), then retry.
  PASS → continue

CHECK 2: Does an MCP tool call succeed?
  call server_get_status
  FAIL (but /healthz is OK) → Claude isn't registered/connected, or the URL or
         bearer token is wrong. Run `claude mcp list`; point the user at the
         connect-claude skill to re-register `minecraft-java`.
  PASS → continue

CHECK 3 (mode-aware): Determine operating mode — do NOT assume a player.
  Run `harness.py mode` (above).
  DEDICATED / unpaused (gameTime advances at 0 players) → players optional;
         proceed. Force-load every work envelope.
  SINGLE-PLAYER (gameTime frozen at 0 players) → ask the user to join AND keep
         the window focused, then proceed.

CHECK 4: Retry server_get_status / level_get_info once.
  PASS → continue.  FAIL → Stop. Report each check result, the error, and the
         /healthz output. Point the user at minecraft-mcp-setup. Do not build.
```

After 3 failed recovery attempts across a session, stop and report the full
diagnostic — do not loop indefinitely.

**Chunks must be loaded.** Tools operate on the loaded part of the world. Work
near a player, or force-load the work zone — block and entity operations against
unloaded chunks fail or silently no-op.
