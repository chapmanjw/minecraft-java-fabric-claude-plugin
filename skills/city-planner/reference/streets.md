# Streets and transit

The street network is the skeleton of the city — lay it after zoning and
before buildings. One block ≈ 1 metre at 1:1.

## Street hierarchy

A real city has a *hierarchy* of street widths, not one width. Use it:

| Street type | Width (blocks, 1:1) | Notes |
| ----------- | ------------------- | ----- |
| Ceremonial axis / grand boulevard | 24–30 | Planted medians; terminates on a landmark. |
| Major avenue | 16–24 | The primary movement streets. |
| Standard street | 8–12 | The everyday grid; a Roman `cardo` sits here. |
| Residential street | 4–6 | Quiet, local. |
| Alley / mews | 2–3 | Medieval lanes, service access. |
| Pedestrian court / plaza spur | 3–4 | No through traffic. |

Reference points: Manhattan avenues ~30 blocks and cross-streets ~18; a
Haussmann boulevard ~24–30; a Manhattan block ~61 blocks N–S. Scale these down
proportionally for the 1:10 and silhouette scales.

## Grid topologies

Pick the topology the city actually has:

- **Orthogonal grid** — Roman (`cardo` N–S × `decumanus` E–W) and modern
  American. Regular, rectangular blocks.
- **Organic medieval** — streets follow terrain and property lines; a market
  square as a hub; no straight runs (the 7-block rule from the terrain skills
  applies to organic streets).
- **Radial / Haussmann** — boulevards radiate from star intersections, cutting
  across an older fabric.
- **Axial** — a dominant ceremonial spine (East-Asian capitals, Baroque
  planning) with a subordinate grid.
- **Canal-organic** — Venice: canals are the streets; foot lanes and bridges
  are secondary.

Keep block sizes consistent within a district; vary them between districts to
mark zone changes.

## Streets as designed space

A street is not just a gap between buildings:

- **Pave** it — the carriageway and the footway in different blocks.
- **Light** it — lamps at a regular rhythm (see `infrastructure.md`); no
  spawnable dark stretch.
- **Furnish** it — trees, benches, signage, the era-appropriate detail that
  makes it walkable.
- **Terminate vistas** — a long straight street should end on something worth
  looking at (a landmark, a gate, a fountain).

## Transit

Route the transit the city is known for:

- **Canals** — Venice Grand Canal ~40 blocks wide × 5 deep; secondary canals
  6–10 wide × 3 deep; Amsterdam ring canals ~25 wide × 3 deep. Quays and steps
  along the edges.
- **Aqueducts** — multi-level Roman arches carrying water in over distance.
- **Rail** — elevated lines (a viaduct of arches or steel), ground-level
  tracks, stations; surface entrances for an underground system.
- **Bridges** — from simple spans to inhabited bridges (shops along the deck,
  like the Ponte Vecchio).
- **Streetcars / cable cars** — tracks and stops for the relevant era.

Make transit actually **connect** — a canal that dead-ends, a rail line to
nowhere, or a bridge that misses the far bank all break the illusion. Verify
connectivity in the plan.

This covers transit *within* the city. A network *between* the city and other
settlements — long-distance rail, highways, a nether hub — is the
`transit-architect` skill's job; hand it the city's transit terminal as the
connection point.
