# The adaptive interview

Capture the city design without over-asking. Ask in small grouped batches (use
`AskUserQuestion` for the multiple-choice ones), skip what the request or the
surveyor already settled, and record answers in `requirements.md`.

## Question bank

1. **Target type** — a real-world city (modern or historical), a city from
   fiction, or an original? This routes the research and the catalog entry.
2. **Which city / era** — the specific city and, for historical, the era
   anchor (Pompeii 79 CE, London 1880). For an original, the era and culture.
3. **Scale** — a single district at 1:1, a whole small city at ~1:10, or a
   metropolitan silhouette at ~1:100? Lock this early; it bounds everything.
4. **Scope** — the whole city, or named districts? For a large city, which
   districts, and in what build order?
5. **Site** — anchor coordinates or "near me"; biome, terrain, and water from
   the surveyor. Flag a site that cannot hold the requested footprint.
6. **Landmarks** — which named buildings to include (each becomes a
   `building-architect` handoff)? Which are must-have vs optional?
7. **Functional districts** — should any residential quarter be a working
   villager village (delegated to `village-planner`), or is the whole city
   aesthetic-only?
8. **Detail level** — façades and streetscape only, or interiors too (and for
   which districts)?
9. **Palette overrides** — keep the city's real palette, or restyle it?
10. **Project name** — the registry slug.

## Conditional follow-ups

- Real-world or named-fictional city → invoke `researcher` before composing.
- A supertall skyline (modern metropolis) → warn that 1:1 exceeds the world's
  height and confirm the silhouette scale or a reduced ratio.
- Site needs major shaping (a river, a hill, an island, reclaimed land) → note
  a `terraforming` pre-build step.
- A walled city → ask the wall type and whether the sprawl outside the wall is
  included.
- A canal city → ask whether canals replace streets entirely (Venice) or
  supplement them (Amsterdam).
- A tiered city (Minas Tirith) → reserve the Y-budget for the tiers up front.

## Conduct

- Lock the **target type** and **scale** first — they shape every later
  answer.
- Group questions; never interrogate line by line.
- For a large city, agree the **district build order** — cities are built and
  inspected district by district, not all at once.
- Restate the plan — scale, districts, landmark list, detail level — before
  rendering layouts, so a misread is cheap to fix.
