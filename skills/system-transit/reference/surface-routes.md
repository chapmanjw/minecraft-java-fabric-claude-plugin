# Surface routes — rail, road, ice, trails

The linear travel-ways that run across the Overworld surface.

## Rail

Minecart rail is the workhorse of medium-distance overworld transit.

- **Speed** — a minecart tops out at 8 m/s on a straight track, ≈11.3 m/s on
  a diagonal.
- **Powered rails** — on flat track, roughly **one powered rail every 38
  blocks** holds an *occupied* cart at top speed (an empty utility cart needs
  them closer, ~1 per 27). Three powered rails in a row launch a cart from
  rest — use that at every station.
- **Track** — a single track for one direction; a **double track** (two lines
  a few blocks apart) for two-way traffic without a head-on.
- **Climbing** — a cart loses speed uphill; on a sustained climb, increase the
  powered-rail density. Prefer to keep grades gentle.
- **Curves** — Java rail corners auto-orient when placed; lay them explicitly
  to be certain. A 4-way crossing's auto-orientation is unreliable — design
  junctions as explicit curves and stubs, and hand any *switched* junction to
  `system-redstone`.
- **Stations** — a platform a block above the rail, a waiting area, a 3-rail
  launcher; the station *building* is a `design-building` handoff, the
  dispenser or button redstone an `system-redstone` handoff.

### Powered rails need a real redstone source

Every powered rail a player will ever ride past must sit on top of a real
redstone source — a `redstone_block` directly under the rail at `y = RAILY-1`.
Setting `powered=true` with `block_set_state` and no source does **not** hold:
a source-less `powered_rail` re-evaluates to `powered=false` on the next block
update, and a player's presence (chunk load, lighting, neighbour updates)
generates those updates continuously. So a rail that read `powered=true` during
a headless 0-player verify collapses the instant the user logs in to ride it.
A `redstone_block` under the rail recomputes to `powered=true` on every re-eval,
so it is player-proof and reload-proof. (`update_flags=2` to skip neighbour
notify does not help — the rail still self-reverts on the chunk's rail re-eval.)

Place the source first, then the rail, so the rail computes its power from it:

```python
# Booster cell: redstone_block source UNDER the rail, powered_rail ON TOP.
# Order: place the source first, then the rail (so the rail computes powered from it).
set_state(x, RAILY-1, z, {"id": "minecraft:redstone_block"})
set_state(x, RAILY,   z, {"id": "minecraft:powered_rail",
                          "properties": {"shape": shape, "powered": "true"}})
```

A source-less `set_state powered=true` is acceptable only for a headless,
never-visited mechanism, and even then is fragile. With real sources you can go
denser than the ~38-block flat cadence without the mutual-revert problem that
plagues source-less boosters at spacing under ~5 — every ~4 cells on flat keeps
an occupied cart accelerating. The acceptance test is a full-loop ride **with a
player online**, not a headless one: log a player in, then read `powered` on a
sample — it must stay `true`.

### Turns: square single-block-corner U-turns, never sweeping arcs

Powered rails cannot boost on a curve shape, so a cart only coasts across curve
cells. A long arc bleeds nearly all the cart's speed, and the boosters on the
straight beyond it cannot re-accelerate a near-stopped cart. Connect two
parallel straights with a **square U-turn**: a short outward jog, a single-block
corner, a straight boostable cross-run, a single-block corner, back to the other
straight. Never a multi-cell arc. A 169-cell semicircular end-turn left the cart
exiting nearly stopped; replacing it with a cross connector plus two single-block
corners cut the curve count to 2 and the loop ran continuously. Verify by riding
from a *slow* start, not just a max-speed launch — a fast cart can skim a bad
turn that a slow cart stalls on.

### Wall-base rails ride a sloped-back bench

A rail run along a cliff or canyon wall must not be a horizontal tube bored into
the rock — the mass above it overhangs with nothing beneath and reads as
floating. Carve the rail as a **bench whose outward wall recedes ~0.85 blocks
per block of height**, so the wall slopes back above the rail with no overhang
while the canyon side stays open for the view.

Order matters: **run all the carve/clear fills first, then all the rail fills.**
A per-cell `[clear, rail]` order lets cell i+1's wide clear wipe cell i's rail
before it is placed, disconnecting the track along every jog.

```python
carves, rails = [], []
for cell in path:
    carves.extend(bench_clear(cell))   # ledge + sloped-back air
    rails.append(rail_fill(cell))
batch(carves)   # ALL clears first ...
batch(rails)    # ... THEN all rails
```

Grounding the bench into the wall (the talus skirt where the carve meets
surrounding rock) is a `terrain-integrate` concern — flag it.

### Auto-board station (a "step on the plate and ride" template)

"Step on a plate and ride" is a common ask. Command blocks execute on this mod
(datapack functions are inert — see
`${CLAUDE_PLUGIN_ROOT}/reference/execution/engine-limits.md`), so the working
pattern is a pressure plate powering an impulse command block, then a chain of
command blocks that clear the old cart, summon a tagged cart with launch motion,
and `ride @p mount` the player into it. `/ride mount` teleports the player in
regardless of distance, so the plate need not be on the rail. This is the static
footprint plus its command blocks; if the line wants a *switched* or
*scheduled* dispatch instead of step-to-ride, that is a `system-redstone` seam.

```
plate (-,RAILY+0..) stone_pressure_plate            # player steps here
impulse  command_block[facing=down] auto:0b         # kill @e[type=minecraft:minecart,tag=boardcart]
chain1   chain_command_block[facing=down] auto:1b   # summon minecart <x> <y> <z> {Tags:["boardcart"],Motion:[0,0,-4]}
chain2   chain_command_block[facing=down] auto:1b   # ride @p mount @e[type=minecraft:minecart,tag=boardcart,limit=1,sort=nearest]
```

Gotchas, all learned the hard way:

- The chain blocks need `auto:1b` (always active) so they fire on the upstream
  trigger.
- The cart summon must land on a loaded, force-loaded rail cell or it freezes
  invisibly (an `entity_query` then returns `[]` on a cart that exists but is in
  an unloaded chunk — see engine-limits).
- `setworldspawn <x> <y> <z> <angle>` — the trailing **angle** argument silently
  failed on this mod (spawn stayed at the old point). Set spawn **without** the
  angle.
- Clear `armor_stand` between tests (each occupied test cart leaves its passenger
  behind — see ride-test hygiene below).

### Ride-test hygiene

Before AND after every ride test, clear the strays a test leaves on the track —
they read as "broken rail / no cart" when the next cart stalls behind them:

```python
for ent in ("minecart", "pig", "item", "armor_stand"):
    cmd(f"kill @e[type=minecraft:{ent}]")
```

`armor_stand` is the easy one to miss: an `armor_stand` passenger gives a test
cart the low-friction physics of a ridden cart, and killing the cart leaves the
armor_stand on the rail. A self-running loop also means a *previous* test's cart
is still lapping — clear it too, both before and after.

## Roads and highways

- **Lane width** — about **4 blocks per lane**. A simple road is one lane; a
  2-lane road is ~8 wide; a divided highway adds a planted median; a grand
  interstate is 6 lanes plus shoulders.
- **Surface** — match the era: smooth stone or polished blackstone for modern
  asphalt, cobblestone or packed mud for medieval, gravel for rural,
  sandstone in the desert, stone for a Roman road (with a cambered surface and
  side ditches).
- **Markings and furniture** — a stripe down the lane, contrasting kerbs,
  guardrails on drops, a lamp every ~16 blocks (mob-proofing as well as
  lighting).
- **Interchanges** — a diamond for a simple junction, a cloverleaf or stack
  for grade-separated crossings, a roundabout (8–40 blocks across) for a
  multi-way meeting.

## Ice-boat highways

A fast, cheap water-or-ice express:

- **Blue ice** (~73 m/s) is the fastest surface on Java — prefer it for
  high-speed highways. **Packed ice** (~40 m/s) is significantly slower but
  far cheaper; use it for budget or medium-distance corridors.
- Build a 2-block-wide channel, with a **slab or block guard** along both
  sides so a boat does not derail on the diagonals.
- Light it (buttons or other non-spawnable surface, or lamps) so it does not
  spawn mobs.

## Footpaths and trails

For short links and scenery:

- **Cobble or stone path** — 1–2 blocks wide, for a tidy walked route.
- **Dirt trail** — irregular podzol and coarse dirt, for an informal path
  through wild terrain.
- **Boardwalk** — planks on fence posts, a block above water or marsh.
- **Mountain switchback** — a zig-zag climbing a steep slope, a few blocks
  across, gaining a few blocks of height per leg.
- Mark long trails — a cairn or signpost at intervals.

## Mob-proofing every route

Whatever the mode, the corridor must not become a mob farm: light it
adequately end to end, and where the route is a flat dark surface (a tunnel
floor, a wide roadbed at night) cap or light it so nothing spawns on it.
