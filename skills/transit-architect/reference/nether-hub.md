# The nether hub

The single cheapest distance technique in Minecraft. Because 1 block in the
Nether equals **8 blocks in the Overworld**, a short nether tunnel replaces a
long overworld journey — a 1 km nether tunnel covers 8 km of overworld
distance.

## Portal-pair math

A nether portal links an Overworld location to a Nether location by
coordinates:

- **Nether coordinate** = Overworld X and Z **÷ 8** (Y stays roughly the
  same). An overworld base at (3600, 70, 0) pairs to a nether portal at
  (450, 70, 0).
- The game pairs portals by **searching near the converted coordinate** — a
  128-block radius in the Overworld, 16 in the Nether — and will link to or
  create *any* portal it finds there. So an unmanaged pair drifts or
  mis-links.
- **Always build and light both ends manually**, at the exact converted
  coordinates, and keep other portals well outside the search radius. Compute
  every pair; never rely on an auto-generated exit portal.

## Designing the hub

1. Pick a **hub center** in the Nether — a clear spot, Y ≈ 70–110 (above the
   lava sea, below the bedrock ceiling).
2. Convert it to its overworld coordinate (× 8) — that is where the hub's
   "home" portal lands on the surface.
3. For each site, compute its nether coordinate (÷ 8); a spoke tunnel runs
   from the hub to that point, where the site's portal stands.
4. The hub chamber is a room — octagonal, hexagonal, or square — with one
   portal per spoke, each clearly **labelled** (a sign with the destination
   name and overworld coordinates, a distinct banner colour).

## Tunnels

- **Cross-section** — 3×3 minimum for a footpath; 5×4 for a comfortable
  highway-class tunnel; wider for rail.
- **Floor** — full blocks or slabs so nothing spawns on the walking surface.
- **Walls** — nether brick or any solid block; line it so it reads as built,
  not bored rubble.
- **Light it brightly** — a light source every ~4 blocks for light level
  14–15; a dark nether tunnel fills with mobs.
- **Mob-proofing** — slab or solid floor (no spawns), a roof that denies
  ghasts (they need open space), and **gold blocks beside each portal** so
  piglins stay neutral to a player arriving without gold armour.
- Split a long tunnel into ≤64-block structure "sleeves" for the blueprinter.

## When a nether hub is right

- 5+ sites scattered with no natural center.
- Any pair of sites more than a few thousand blocks apart.
- Speed-first projects.

A nether hub is *not* right when the journey itself is the point — a scenic
overworld rail or road wins there — or when sites are close enough that an
overworld link is simpler than two portals and a tunnel.
