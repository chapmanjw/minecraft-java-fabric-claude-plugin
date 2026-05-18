# City blueprint rendering and validation

Propose the city as blueprints the user can react to, then iterate. A city is
too large for one grid — render it at the **district** level and zoom in.

## Rendering modes

Produce these in `.minecraft-builder/<project>/` and show the user before
resolving a plan:

- **District map** (`city.txt`) — a top-down map of the whole city, one
  character per district or per N blocks, districts labelled and zone-coded.
- **Per-district plan** (`district-<name>.txt`) — a finer ASCII top-down of
  one district: streets, block subdivision, landmark footprints, vernacular
  fill.
- **District table** (`city.md`) — every district: zone type, scale, palette,
  `functional` flag, landmark list, build order.
- **Mermaid graph** (`city.mmd`) — district adjacency and the transit network.
- **Skyline silhouette** — for a metropolis, an ASCII side elevation so the
  user can check the profile reads as the real city.
- **Street-level walkthrough** — a short written narrative of walking a main
  street: what you pass, the rhythm, the detail. Often the most efficient way
  to convey whether the city will *feel* right.

### District map — example

```
City: kings-landing   (1 char ≈ one district)

  . . W W W W W .
  . R R M K K . .     R residential   M market
  . R R M K K . .     K keep/civic    H harbour
  . S S . H H H .     S sprawl        W wall
  . S S . H H H .
```

## Iteration

1. Render the district map + a couple of per-district plans + the walkthrough.
2. Show the user; take feedback on zoning, density, landmarks, street feel.
3. Revise and re-render.
4. Loop until the user explicitly approves.
5. Resolve to `plan.toon` — district by district, in the agreed build order.

## Validation checklist

Check the design — and have the `inspector` and `philosopher` re-check it —
against these city-specific failure modes:

- **Too few buildings** — under ~16 it is a village; defer to `village-planner`.
- **Wrong era or density** — skyscrapers in a Roman city, a medieval alley grid
  in a modern downtown.
- **Skyline does not read** — the silhouette is not recognizable as the real
  city; the signature landmarks are missing or mis-proportioned.
- **No street hierarchy** — every street the same width reads as a grid of
  boxes, not a city.
- **No vista termination** — long streets ending on nothing.
- **Monotonous fill** — vernacular rows that are obvious copies (variation
  failure — see `vernacular.md`).
- **Bare streets** — no lighting, no furniture, no trees; the caricature.
- **Disconnected transit** — a canal, rail line, or bridge that does not
  actually connect.
- **Missing characteristic detail** — Paris without Métro entrances, NYC
  without fire escapes, Venice without canals.
- **Functional villagers in the wrong zone** — golem/pathfinding failures in a
  dense tower district; keep villagers to medieval/low-rise quarters.
- **Y-budget or fill-cap violation** — a 1:1 supertall over the Y range, a
  district fill over 32,768, a structure over 64×384×64.

A missing signature or a monotonous fill is a correction to make, not a
cosmetic note.
