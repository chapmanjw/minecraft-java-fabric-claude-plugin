# The adaptive interview

Pin down the contraption without over-asking. Ask in small grouped batches
(use `AskUserQuestion` for the multiple-choice ones), skip what is already
clear, and record answers in `requirements.md`.

## Question bank

1. **Contraption class** — door / hidden mechanism, item sorter or storage,
   mob farm or spawner collector, crop or animal farm, transport (minecart,
   elevator, ice road), music, decorative redstone, trap or defence.
2. **What it processes / does** — which items, which mobs, which crops; for a
   door, the opening size; for transport, the route and stops.
3. **Throughput / target** — a casual build, or a rate target ("keep up with
   an AFK session")? Throughput drives parallelism and footprint.
4. **Trigger** — button, lever, pressure plate, automatic (observer / clock),
   or hidden.
5. **Site and space** — anchor coordinates from the surveyor; how much room is
   available; underground, in a base, standalone.
6. **Simulation distance** — for any mob farm, the world's simulation distance
   (often 4 on consoles, up to 12 on PC). The viable spawn shell depends on it.
7. **Aesthetic** — exposed redstone (functional), or hidden behind a façade
   (then coordinate the enclosure with `player-house` / `building-architect`)?
8. **Integration** — standalone, inside a building, or part of a village's
   industrial quarter (coordinate with `village-planner`)?
9. **Project name** — the registry slug.

## Conditional follow-ups

- Mob / iron / villager farm → confirm the simulation distance and, for
  iron/villager farms, hand the village half to `village-planner`.
- The request names a Java tutorial or creator → check
  `community-sources.md`; warn that it likely needs Bedrock translation, and
  ask `researcher` for a Bedrock-edition source.
- The request is AFK fishing → explain it is broken on Bedrock and offer
  villager trading or a pufferfish/sea-pickle farm instead.
- A timing-critical build (music, fast door, clock) → confirm the tempo or
  speed in redstone ticks.
- A large farm → ask whether overflow protection (a trash can / overflow
  chest) is wanted.

## Iterate on ideas

The user may arrive with a vague want ("something cool with redstone") or a
firm spec. When it is vague, **suggest options** — name two or three
contraptions from the catalog that fit their world and ask which appeals.
Engineering is collaborative; propose, do not just interrogate.

## Conduct

- Lead with the contraption class and what it does — they shape everything.
- Group questions; never interrogate line by line.
- Restate the design — what it does, footprint, throughput, trigger — before
  resolving the plan, so a misread is cheap to fix.
