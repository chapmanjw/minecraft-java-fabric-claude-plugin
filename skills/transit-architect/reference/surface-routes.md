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
- **Curves** — Bedrock rail corners are simple single-block curves; lay them
  explicitly. A 4-way crossing's auto-orientation is unreliable — design
  junctions as explicit curves and stubs, and hand any *switched* junction to
  `engineer`.
- **Stations** — a platform a block above the rail, a waiting area, a 3-rail
  launcher; the station *building* is a `building-architect` handoff, the
  dispenser or button redstone an `engineer` handoff.

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

- Build a channel of **packed ice** — on Bedrock, packed ice and blue ice run
  at the *same* boat speed, so packed ice is the right choice (blue ice costs
  far more for no gain).
- A 2-block-wide channel, with a **slab or block guard** along both sides so a
  boat does not derail on the diagonals.
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
