# Live MCP integration suite

Exercises the minecraft-java mod's MCP tools against a *running* world and
asserts each one behaves. Run it from the `tools/` directory:

```sh
cd tools && python -m itest.run                # run the live surface
cd tools && python -m itest.run --destructive  # also run destructive cases
cd tools && python -m itest.run --only block   # one category (name prefix)
cd tools && python -m itest.run --baseline out.toon
```

## It tests the LIVE surface, not the whole tool set

After the 26.x tool-categorization redesign the mod registers a subset of its
tools depending on config. The mod defines 194 in total, but 6 of those are
client-only and served by the separate `minecraft-java-client` endpoint, so the
world server this suite targets can register at most **188**. With no config (or
an empty one) an operator gets the lean default: roughly **104 tools live, ~84
not live**. The suite only runs
cases whose tool is actually registered; a case for a tool that isn't live is
reported as `SKIP` with the reason it's off, e.g.
`not live (opt-in domain 'gameplay') — enable via mod config to test`. A
not-live opt-in or admin tool is **expected** under the lean default — it is not
a regression.

The lean default exposes the seven enabled-by-default domains up to `write`
access:

| live by default | not live by default |
| --- | --- |
| blocks, structures, world, entities, items, scripting, server | players, gameplay, registries (opt-in domains) + every admin-access tool |

The ~81 not-live tools break down as: players 16 + gameplay 30 + registries 21
(those three whole domains are opt-in) + the 14 admin-access tools that live in
otherwise-on domains (the worldborder setters, `level_set_difficulty`,
`level_set_game_rule`, `level_create_explosion`, `command_register`,
`server_reload_resources`, `datapack_enable`/`datapack_disable`).
`command_execute` stays `write` (it is the workhorse) even though it can run
arbitrary commands.

## Testing the full world surface

To exercise every tool, configure the mod to include all ten categories and
raise the access cap to `admin`, then restart the server and re-run the suite.
In the mod config, include all categories as the allowlist and set
`maxAccess=admin` (equivalently, the legacy `excludeWriteTools=false` plus an
admin opt-in). Config precedence: a non-empty `includedCategories` is the
allowlist, otherwise the `enabledByDefault` domains are used; then
`excludedCategories` is subtracted; then any tool whose access rank exceeds
`maxAccess` is dropped. With all categories included and `maxAccess=admin`, all
188 world tools register and the suite runs the full surface. The 6 client tools
(`view_capture`, `sense_*`, `client_status`) are never reachable here — they need
a running client on the `minecraft-java-client` endpoint.

## Why a tool is not live

Three independent things can keep a tool out of `tools/list`, and they are
indistinguishable from the client: an opt-in domain, an admin access tag, or an
unmet `requiredFabricModules` / Minecraft-version constraint. The harness can only
infer the first two from its own tables.

Pass `--server-log <path>` and it reads the server's own `Skipping tool '<name>':
<reason>` lines instead, which is the only way to see the third. That third case is
not hypothetical: five tools were dead on every Minecraft version because they
required `fabric-screen-handler-api-v1` and `fabric-resource-loader-v0`, neither of
which Fabric API ships, and nothing here could say so.

```sh
python -m itest.run --server-log /path/to/server/logs/latest.log
```

## Cases

Test logic lives in `cases/*.py`, one module per tool family, registered with
the `@case(tool, level=…)` decorator in `harness.py`. The `level` is a safety
tier: `safe` (read-only or sandbox-confined), `global` (mutates world-global
state and restores it), and `destructive` (irreversible/session-affecting,
skipped unless `--destructive`). All world writes happen in a force-loaded
scratch sandbox far from any build, cleared at the start and end of every run.
The suite is stdlib-only (uses `builder.mcpclient` / `builder.toon`).
