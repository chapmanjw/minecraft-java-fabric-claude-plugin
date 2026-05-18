# Zoning and districts

A city is a set of **districts** with deliberate **adjacencies**. Zone the city
before laying streets or buildings — the zones drive everything downstream.

## The village / city threshold

- Under ~16 buildings → it is a settlement; use `village-planner`.
- ~16+ buildings, or a request for a city / district / metropolis → this skill.

Within a city, a **functional residential quarter** (villager-capable) can be
delegated back to `village-planner` — mark that district `functional: true`
and hand it off. Aesthetic-only districts skip villagers (and the iron-golem
and pathfinding constraints that come with them).

## Districting

- Break the city into **districts of ≤256×256 blocks** — each a build unit.
- Give each district a **character**: its dominant zone type, era, density,
  and palette.
- Plan **adjacencies** — districts that belong next to each other (market by
  the gate, docks on the water, slums outside the wall) and the transitions
  between them.

## Zone patterns by city type

**Roman** — a central *forum* (basilica, curia, temples), public baths, an
amphitheatre, an orthogonal grid of `insulae` (apartment blocks) and `domus`
(courtyard houses), a wall with gates, a port or river quarter.

**Medieval** — a castle on the high point; a cathedral square; a market
square; guild and merchant quarters; "dirty" trades (tanners, dyers)
downstream of the water; monasteries; a curtain wall; a poor sprawl outside
the gates.

**Renaissance / Baroque** — formal axes and vistas, planned squares (piazze),
palaces, a regularized grid grafted onto the medieval core.

**Haussmann (19C Paris model)** — broad boulevards radiating from star
intersections, uniform apartment blocks, planned parks, grand civic buildings
terminating the vistas.

**Industrial Victorian** — a civic/commercial core, dense terraced
residential rows, factories and warehouses by the rail and water, parks
inserted as relief.

**Modern American grid** — a financial/downtown core of towers, a regular
street grid, mid-rise mixed-use, low-rise residential at the edges, a central
park, an airport or port at the periphery.

**East-Asian axial** — a strong north–south ceremonial axis, a palace or
civic complex on the axis, a grid of low courtyard housing (siheyuan,
machiya) on narrow lanes, a moat and wall.

**Islamic / Middle-Eastern** — a central congregational mosque and a
bazaar/souk, organic lanes, courtyard houses turned inward, a citadel, gardens
and fountains.

## Composing the zones

- Put **civic and religious** zones on prominent ground and terminate street
  vistas on them.
- Put **commerce** (market, bazaar, financial core) where movement
  concentrates — gates, the waterfront, axis crossings.
- Put **residential** in graded rings: denser and grander toward the core,
  looser toward the edge.
- Put **industry / docks** on the water and downwind, with rail or canal
  access.
- Reserve **green space** — a city of solid fabric reads as oppressive; parks
  and squares are the relief.

Every zone is one or more `≤256×256` districts in the plan. Record each
district's type, scale, palette, and `functional` flag in the registry.
