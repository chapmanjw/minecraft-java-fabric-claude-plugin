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

Check the design — and have the `exec-inspect` and `exec-reflect` re-check the
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
  `terrain-shape`.
- **Redstone in the plan** — a boost station or switch designed here instead
  of handed to `system-redstone`.
- **A gapped 1-wide line** — a missing rail or wire cell. `block_fill_batch`
  can silently drop a few entries from a large batch; for wide terrain that is
  invisible, but for a 1-wide rail it is fatal (the cart stalls dead at each
  gap). See the continuity check below.

A mis-paired portal or a disconnected mode breaks the journey — those are
corrections to make, not cosmetic notes.

## Verifying 1-wide continuity

A single batch of 1,928 one-block rail fills left 4 cells unplaced with no
error; the cart skimmed the gaps at launch speed once (so the ride "passed"),
then stalled at each of them after it slowed. For any 1-wide critical line
(rail, redstone, a thin wall), do not trust the batch return — re-scan the
feature's Y-layer and patch.

Run `${CLAUDE_PLUGIN_ROOT}/tools/voxel/continuity.py` after laying the line:
`verify_and_patch(intended_cells, dimension, y, shape_of=..., block="minecraft:rail")`
scans the layer in cap-sized tiles, diffs the intended cell list against what is
present (`find_gaps(intended, present)` is the pure set diff under it),
`set_state`s the missing cells (per-block placement is reliable where the batch
was not), and returns the patched cells so the gap is logged rather than silent.
The `exec-inspect` pass should assert the scanned layer count equals the
intended count. Hard tool caps (scan volume, batch entries) live in
`${CLAUDE_PLUGIN_ROOT}/reference/execution/engine-limits.md`.
