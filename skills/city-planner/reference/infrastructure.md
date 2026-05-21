# Infrastructure and street-level detail

The fabric between the buildings. This is where a city stops being a model and
starts being a place you can walk around — plan it in, do not leave it bare.

## Walls and gates

For walled cities:

- **Medieval European wall** — ~3 blocks thick, ~12 tall, crenellated, with
  projecting towers every ~30–50 blocks and fortified gatehouses.
- **Great city wall** (Constantinople archetype) — layered defence: a moat, an
  outer wall with a patrol walk, a tall inner wall with high towers.
- **East-Asian city wall** — far thicker (10–20 blocks at the base), battered,
  with monumental gate towers, a wide moat.
- **Gates** terminate streets and frame the entry — make them an event.

## Plazas and squares

The civic "rooms" of the city. Pave them with a deliberate pattern (a border,
a centre motif), give them a focal point (a fountain, a monument, a column),
and frame them with the grandest façades. Reserve them — a city of solid
fabric reads as oppressive.

## Parks and green space

Reserve 15–30% of a district as open space across the city, and hand the
design of each significant green space to a specialist:

- **Formal gardens, plazas, and designed parks** — geometric parterres,
  squares, civic plazas → the `landscape-architect` skill; give it the
  envelope, datum, and axis.
- **Naturalistic parks** — hand the shaping to `terraforming`.

Lay out where the green space goes and how big; let the specialist design it.

## Fountains and water features

Trevi-style display fountains, tiered basins, parterre fountains, simple
public wells and drinking fountains. A focal point for plazas and squares.

## Lighting — by era

Light the whole city; no spawnable dark street. Match the fixture to the era:

- **Ancient / medieval** — torches and lanterns on iron posts, braziers.
- **Industrial / Victorian** — gas-lamp-style lanterns on ornate posts.
- **Modern** — lamp posts, glowing signage, lit interiors behind glass.
- **Cyberpunk** — neon (coloured glow blocks, end rods), deep contrast.

## Street furniture — the lived-in detail

The small things that sell "a real place": benches, planters and street
trees, signage (item frames and banners as shop signs), market stalls and
awnings, kiosks, mailboxes and hydrants and phone boxes (era-appropriate),
fire escapes and rooftop water tanks (NYC), washing lines, carts, crates,
scaffolding. Scatter them with the same anti-uniformity discipline as the
buildings — clustered and irregular, not evenly spaced.

Street trees must be grown from saplings, never placed or duplicated. On Java
Edition: place the sapling with `block_set_state`, then force growth with
`command_execute` running `/place feature minecraft:<tree_type>`, or bone-meal
via `player_give_item` / `itemstack_drop_at`.

## Sewers and the underside

For depth, a city can have an underside — Roman cloaca with street grates,
modern manholes and service tunnels, a canal's working quays. Optional, but it
adds realism for a city the player will explore.

## Site and water prep

A city rarely sits on ready ground. Where the site needs work — leveling a
district, carving a river or canal, raising a hill for an acropolis, digging a
moat, creating an island — emit a `pre-build terraform` step so the
`terraforming` skill prepares the site before the `worker` places any block.
If the city sits on a *named* natural feature (a famous hill or bay), the
`natural-landmarks` skill shapes that.
