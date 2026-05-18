# Water, air, and vertical transit

The network's nodes that are not simple linear routes — where boats berth,
where aircraft sit, and where a route changes height.

## Docks, marinas, and harbors

Where a water route meets the land:

- **Pier** — a walkway a block above the water on posts; the simplest landing.
- **Slip / berth** — a boat space, ~4–6 blocks wide; berths can be end-on (bow
  in), parallel (alongside), or in finger piers off a main walkway.
- **Approach** — keep the water in front of a berth clear and deep enough; a
  shallow shelf strands boats.
- **Quay** — a solid stone edge for a larger or industrial waterfront.
- **Scale up** — a marina is many slips off shared walkways; an industrial
  port adds warehouses (`building-architect`) and cranes (`monument-builder`);
  a naval harbor has large ship berths and a drydock.
- **Mooring** — Bedrock has no real boat mooring; add fence-post rings as a
  visual cue and accept that boats drift.
- A **lighthouse** marking a harbor entrance is a `building-architect` handoff.

## Airports and airship terminals

Minecraft has no real powered flight (only elytra), so aircraft are
**decorative** — design these as showpieces and elytra-launch points:

- **Runway** — a long, flat, smooth strip; an apron and taxiways beside it.
- **Helipad** — a small marked square.
- **Hangars, terminals, and control towers** → `building-architect`; you place
  the footprints and the airside connections.
- **Airship / zeppelin** — a tall mooring mast and a docking platform; a
  steampunk or fantasy showpiece.
- An elytra launch point (a high platform, a drop, a bubble lift to altitude)
  turns a decorative airport into a functional one.

## Elevators

Where a route changes height sharply:

- **Bubble elevator (up)** — a water column over **soul sand**; carries an
  entity up at ~8 m/s. The water column (kelp-set source blocks) and the soul
  sand are yours to design; any **activator** redstone is an `engineer`
  handoff.
- **Drop column (down)** — a water column over **magma blocks**, pulling down
  at ~4.9 m/s.
- **Stairs and ladders** — a stairwell (about one block up per two across) or
  a ladder shaft, for a simple, no-mechanism climb.
- **Ice drop / ramp** — a steep packed-ice ramp for a fast boat descent.
- **Piston or slime-block lifts** are redstone contraptions — an `engineer`
  handoff entirely; you only specify where the elevator goes.

## Connecting nodes into the network

A dock, an airport, or an elevator is a **node** on the transit network —
route a rail, road, or path right up to it so the modes connect, and label it
on the network map. A dock with no road to it, or an elevator that does not
meet the rail, breaks the journey.
