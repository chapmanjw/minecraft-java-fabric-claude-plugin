# Bridges and tunnels — crossings

How to get a route across a gap or through an obstacle.

## Bridges by span

Pick the bridge type by the span it must cross — each type has a credible
range:

- **Beam** — up to ~16 blocks. A simple deck on piers every ~8 blocks. The
  default short crossing.
- **Arch** — ~16–40 blocks. A semicircular or segmental arch carrying the
  deck; the Roman aqueduct and the classic stone bridge. Build the arch with
  the voxel-circle method, soften with stairs.
- **Truss** — ~30–120 blocks. A criss-cross of iron (or wood) members above or
  below the deck; the industrial railway bridge.
- **Cantilever** — long spans built out from piers to meet in the middle; a
  distinctive deep-structured profile.
- **Suspension** — ~100–2000 blocks. Tall towers, a main cable in a catenary
  curve (chains or fences) between them, vertical hangers down to the deck.
  The iconic long crossing.
- **Cable-stayed** — long spans with cables fanning straight from tall pylons
  to the deck (a fan or harp pattern). The modern long bridge.
- **Aqueduct** — a multi-tier arcade carrying a water channel (or a path)
  across a valley.
- **Drawbridge / bascule** — a lifting span; the static structure is yours,
  the **lift mechanism is an `engineer` handoff**.

### Block-stability note

A real suspension or cable-stayed bridge hangs its deck from cables. Minecraft
blocks do not hang — a "suspended" deck must actually rest on supports. Build
**hidden piers or columns** under the deck (every ~16 blocks is plenty) and
let the cables and hangers be *decorative*. The bridge reads as suspended; the
deck is structurally held up.

### Scale

Real famous bridges are enormous — a 2 km span at 1:1 is thousands of blocks.
Confirm real dimensions with `researcher`, then scale down (0.25× or 0.5× is
common) while keeping the proportions and the signature profile. Split a long
bridge into ≤64-block structure "sleeves".

## Tunnels

For routing through a mountain, under water, or below a build:

- **Cross-section** — 3×3 for a footpath, ~4×4 per road lane, ~6×4 for double
  rail, larger for a highway. Add headroom above a rail or road.
- **Lining** — stone brick, deepslate when very deep, nether brick in the
  Nether; line it so it reads as engineered.
- **Lighting** — frequent enough that no stretch is dark; a light every ~8
  blocks for a path, closer for a fast route. A capped or slabbed floor stops
  spawns.
- **Cut-and-cover vs bored** — cut an open trench and lid it (fast, but
  disrupts the surface — flag `terraforming`), or bore from inside (slower,
  preserves the landscape above).
- **Underwater tunnels** — double-wall: an outer water-stop layer with a
  1-block air gap before the inner walking tunnel, so one broken block does
  not flood the whole tunnel.
- A long tunnel splits into ≤64-block sleeves like a bridge.

## Choosing between them

A bridge is seen and celebrated — use it where the crossing should be part of
the view. A tunnel is invisible and preserves the landscape — use it where the
terrain above matters or a bridge would be impractically tall. Either way,
flag any approach grading for `terraforming`.
