# Layouts and scale tiers

## Scale tiers

Lock the tier before anything else — the interview length, room count, and
layout all scale from it. Footprints are W×D×H; counts are approximate.

| Tier | Footprint | Rooms | ~Blocks | Game stage |
| ---- | --------- | ----- | ------- | ---------- |
| Starter shack | 5×5×4 | 1 (bed + crafting + chest combined) | ~150 | first night |
| Cozy cottage | 8×10×6 | 2–3 | ~500 | early |
| Standard home | 12×14×8 | 4–6 | ~1,800 | mid |
| Estate | 20×30×12 | 8–12 | ~6,000 | mid–late |
| Mansion | 40+ wide | 15–25 | ~25,000 | late |
| Castle / keep | 60+ wide | 20–35 | ~80,000 | late |
| Megabase | 100+ wide | 30+ | 250,000+ | end-game |

A tier sets expectations: do not offer a beacon room or a quad-wing layout at
starter scale, and do not propose a single-room cabin when the user asked for
a megabase.

## Layout topologies

Pick a topology that fits the tier, the site, and the style.

- **Single-room cabin** — everything in one space. Starter and cottage only.
- **Linear hallway** — rooms strung along a corridor. Simple, scales to
  standard/estate; can feel like a motel if overlong.
- **Open loft** — one large volume, zones defined by furniture and half-walls,
  not doors. Good for modern and cottage.
- **Two-story** — public ground floor (kitchen, dining, living), private upper
  floor (bedrooms, enchanting). The reliable standard-home default.
- **Tower** — stacked floors, small footprint, vertical circulation. Good for
  tight or sloped sites.
- **Compound** — separate small buildings linked by paths or covered walkways.
  Suits cottagecore, Japanese, estate scale.
- **Quad-wing radial** — a central hall with wings. Mansion and up only.
- **Courtyard** — rooms wrapped around an open central court. Mediterranean,
  castle.
- **Castle / fortress** — curtain walls, a keep, towers, a gatehouse, a
  courtyard, a dungeon level. Castle tier.

## Circulation rules

- Every room reachable without passing through a private room — route public
  traffic through halls, not bedrooms.
- Corridors ≥2 wide at estate scale and up; 1-wide reads as cramped.
- Stairs, ladders, or scaffolding between every floor — and a second vertical
  route at mansion scale and up (it doubles as an escape route).
- Place the storage and crafting cluster central — most trips end there.
- Keep a tool/food station within 2 blocks of every external door.

## Matching layout to site

The `surveyor` site and `environments.md` constrain the topology:

- **Flat plains** — any topology; two-story or compound are easy wins.
- **Mountainside** — terraced compound or tower; carve back into the slope.
- **Underground / cave** — linear or radial chambers off a central hub.
- **Underwater** — compact, sealed; domes and tubes, not sprawl.
- **Sky** — compact tower or platform cluster with a fall-protected rim.
- **Small lot / server claim** — tower upward rather than out.

When the site needs reshaping first (levelling, terracing, hollowing), note a
`pre-build terraform` step so the `terraforming` skill runs before the build.
