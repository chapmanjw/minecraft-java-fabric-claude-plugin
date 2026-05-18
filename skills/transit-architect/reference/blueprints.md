# Network blueprint rendering and validation

A transit network is rendered at two levels — the **whole network** and the
**individual element** — then iterated with the user.

## Rendering modes

Produce these in `.minecraft-builder/<project>/` and show the user before
resolving a plan:

- **Network map** (`network.txt`) — a schematic of the whole network: every
  site, every link, the topology, the mode of each link, labelled. The
  decision-level drawing.
- **Network graph** (`network.mmd`) — a Mermaid graph of sites and links, with
  each edge labelled by mode and approximate length.
- **Route profiles** (`route-<link>.txt`) — for a link with significant
  crossings, an elevation profile showing where it bridges, tunnels, and
  climbs.
- **Element blueprints** — top-down and section views for each major element:
  the hub chamber, a station, a bridge, a tunnel portal, a dock.
- **Link table** (`links.md`) — every link: endpoints, topology role, mode,
  length, major crossings, handoff flags.

### Network map — example

```
Five-base network — topology: nether hub   (* hub  o site  = tunnel)

         o N
         |
   o W = * = o E
        / \
      o S   o F
```

## Iteration

1. Render the network map, the graph, and a couple of route profiles.
2. Show the user; take feedback on topology, routes, modes, where to bridge vs
   tunnel.
3. Revise and re-render.
4. Loop until the user explicitly approves.
5. Resolve to `plan.toon` — link by link, in an agreed build order.

## Validation checklist

Check the design — and have the `inspector` and `philosopher` re-check the
build — against these failure modes:

- **Wrong topology** — a mesh of many sites where a hub belongs; a long
  overworld haul where a nether hub would have been a fraction of the work.
- **Portal mispair** — a nether portal pair not built at the exact ÷8
  coordinates, or another portal inside the search radius, so travel
  mis-links. Build and light both ends manually.
- **A route through a protected build or landmark** — it should have been
  routed around.
- **Unlit corridor** — a rail, road, or tunnel that becomes a mob spawner;
  light it and cap dark surfaces.
- **A "suspended" deck with no support** — chains and hangers are decorative;
  the deck needs hidden piers.
- **Disconnected modes** — a dock with no road to it, an elevator that does
  not meet the rail, a station the network does not actually reach.
- **Scale or cap violations** — a bridge or tunnel not split into ≤64-block
  sleeves, a fill over 32,768, a route outside Y -64 to 320.
- **Inline grading** — terrain carved into the plan instead of flagged for
  `terraforming`.
- **Redstone in the plan** — a boost station or switch designed here instead
  of handed to `engineer`.

A mis-paired portal or a disconnected mode breaks the journey — those are
corrections to make, not cosmetic notes.
