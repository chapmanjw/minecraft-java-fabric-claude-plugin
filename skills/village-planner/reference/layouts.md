# Layouts, paths, and scale

## Scale tiers

Lock the tier before anything else.

| Tier | Buildings | Villagers | Iron golem? | Paths |
| ---- | --------- | --------- | ----------- | ----- |
| Hamlet | 2–4 | 1–4 | No (below threshold) | a single path |
| Standard village | 5–15 | 5–20 | Yes when ≥10 villagers + ≥20 beds | a path network |

A **hamlet** is intimate: a couple of homes, maybe one or two professions, a
well or a bell, an organic cluster. A **standard village** has a profession
roster, a meeting plaza, and a real path network. "Iron-golem-ready" means
≥10 villagers and ≥20 beds — call this out to the user, and if they want
golems but the roster is short, propose adding spare-bed houses.

## Layout patterns

Pick one that fits the site, the scale, and the style:

- **Linear (along a road)** — buildings line one street. Simple, scales from
  hamlet to village, fits valleys and roadsides. Can feel like a strip if
  overlong — curve the road.
- **Crossroads** — two streets meeting at the bell plaza; quadrants of
  buildings. The reliable standard-village default.
- **Radial plaza** — buildings ring a central plaza with the well and bell;
  paths spoke outward. Compact and communal.
- **Organic cluster** — buildings scattered at natural angles around a loose
  center, paths meandering between. The best look for hamlets and cottagecore.
- **Linear river / coast** — buildings along a waterline; a fisherman's dock,
  plank paths over water.
- **Walled hamlet** — a compact cluster inside a wall (with the no-full-seal
  rule from `mechanics.md`).
- **Farm-focused** — fields dominate; a few homes and a barn at the edge.
- **Mountainside terraced** — buildings on cut shelves linked by stairs; needs
  a `terraforming` pre-build step.

## Building spacing

- Leave **3–8 blocks** between buildings — enough to walk and light between
  them, not so much the village feels sparse.
- Doors face the path; give each building a 1-block stoop.
- Keep the bell central, with every bed pillow within 48 blocks of it.
- Cluster related buildings — the farm by the farmer's cottage, the pens by
  the shepherd and butcher, the forges together.

## Path network

- **Width** — 1 block for a side alley, 2–3 for a main road.
- **Material** — `dirt_path` on grass (plains, savanna, taiga, snowy),
  `smooth_sandstone` in desert, planks over water. Gravel reads well in taiga.
- **Curves** — organic 1-block jogs, not hard 90° elbows; the 7-block rule
  from the terrain skills applies to roads too.
- **Intersections** — T-junctions, crossroads, or a circle around the well.
- **Lighting** — a lantern on a fence post every 6–10 blocks; no spawnable
  dark block within 1 block of a path.
- **Bridges** — plank decks with fence rails over water or ravines.
- Paths over slopes steeper than ~2 blocks need `terraforming` to grade them,
  or villagers cannot traverse.
