# The adaptive interview

Pin down the network without over-asking. Ask in small grouped batches (use
`AskUserQuestion` for the multiple-choice ones), skip what is already settled,
and record answers in `requirements.md`.

## Question bank

1. **The sites** — which destinations to connect? Get every site's name and
   coordinates (the `surveyor` and the `mcbuilder:registry` fill gaps). The
   count drives the topology.
2. **A center?** — is one site a dominant hub (a capital, the main base), or
   are they peers? This decides hub-and-spoke vs mesh vs nether hub.
3. **Distances** — roughly how far apart are the sites? Long distances point
   to a nether hub.
4. **Speed vs scenery** — should the network be as *fast* as possible
   (nether hubs, ice boats), or is the *journey* part of the experience
   (scenic overworld rail and roads, viaducts framing the view)?
5. **Era / aesthetic** — Roman, medieval, industrial, modern, fantasy, or
   sci-fi? This sets the materials and the bridge and station styles.
6. **Terrain-disruption tolerance** — should the network bridge and tunnel
   around the landscape (no grading), allow minor cuts, or may `terraforming`
   reshape terrain freely?
7. **Preserve list** — existing builds, monuments, or natural landmarks the
   routes must route around.
8. **Project name** — the registry slug.

## Conditional follow-ups

- A named real-world bridge, road, or rail style → invoke `researcher` for
  references and dimensions.
- Sites across an ocean → ask whether the crossing should be a bridge (seen,
  walked) or an ice-boat highway (fast).
- A request for a nether hub → confirm the sites' coordinates precisely; the
  portal math depends on them.
- Stations or terminals wanted as real buildings → note the
  `building-architect` handoffs.
- A route that must cross a mountain range or a deep valley → flag the
  `terraforming` grading up front so the user expects it.

## Conduct

- Lead with the **sites and whether one is a center** — they decide the
  topology, which decides everything else.
- Group questions; never interrogate line by line.
- For a large network, agree the **build order** of the links — a network is
  built and inspected link by link, not all at once.
- Restate the network — topology, links and their modes, major crossings —
  before rendering blueprints, so a misread is cheap to fix.
