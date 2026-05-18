# Topology, route-finding, and mode selection

The three planning decisions that come before any blueprint: the *shape* of
the network, the *path* of each link, and the *transport mode* of each link.

## Choosing the topology

The topology is the network's shape. Pick it from the number and arrangement
of sites:

- **Direct line** — 2 sites. One link, mode-selected by distance.
- **Mesh** — 3–4 sites. Link each to each; cheap at this count, and every trip
  is direct.
- **Hub-and-spoke** — 5–8 sites with one dominant center (a capital, the
  player's main base). Every site links to the hub; trips route through it.
- **Ring** — sites arranged in a loop, or a sightseeing circuit. One loop
  line, travel either direction.
- **Trunk-and-branch** — sites strung along an axis (a coast, a river, a
  valley). One trunk line, a short branch into each site.
- **Nether hub** — 5+ scattered sites with no natural center. A single hub in
  the Nether with a spoke tunnel to each site; the 8:1 ratio makes this the
  cheapest option for anything spread out. The default for scattered sites.
- **Hybrid** — more than ~8 sites, or several regional clusters. Regional
  hubs (often nether hubs) joined by trunk links.

A mesh of many sites explodes in link count (n sites → n(n-1)/2 links) — past
~4 sites, route through a hub instead.

## Route-finding

For each link, trace a path from A to B that is cheap to build and good to
travel:

- **Follow the terrain** — a valley, a ridgeline, a riverbank, a coast — far
  cheaper than cutting straight across hills.
- **Cost the terrain** — flat ground is cheap; hills, water, and ravines cost
  more; lava and the interiors of protected builds are impassable.
- **Route around** existing builds and natural landmarks — keep a buffer; do
  not plough a highway through someone's base or a named wonder.
- **Cross, do not carve** — where terrain is in the way, prefer a bridge or a
  tunnel to massive grading. When grading is genuinely needed, **flag a
  `terraforming` step** rather than carving it into the plan yourself.
- Keep the whole route within Y -64 to 320.

## Mode selection

Choose the transport mode per link by distance and purpose:

| Distance / case | Mode |
| --------------- | ---- |
| < ~250 blocks | A footpath or trail; a simple road. |
| ~250 m – 1 km | A cobble or stone road, or a single rail line. |
| ~1–3 km | A highway or a double rail line. |
| 3 km+ | A **nether-hub** spoke first; an overworld rail or road only if the journey itself is meant to be scenic. |
| Across water | A bridge (if the crossing should be seen and walked) or an ice-boat highway (if speed is the point). |
| Steep vertical | An elevator (see `water-and-air.md`). |

Speed-first projects lean on the nether and ice boats; scenery-first projects
keep links on the surface with bridges and viaducts that frame the view.

## Per-link record

For every link, the plan records: the two endpoints, the topology role
(spoke, trunk, branch, ring segment), the chosen mode, the route, the major
crossings (bridges, tunnels), and any `terraforming` grading flags.
