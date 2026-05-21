# Populating the village

A village is only functional once it has villagers who claim beds and jobs.
This is the **population phase** — it runs *after* the buildings are placed,
and the plan must sequence it that way: structures → villagers → animals →
iron golem.

## The plan's population steps

Population is expressed in `plan.toon` as `spawn` steps (the `worker` runs them
with `entity_summon`), interleaved with the `set` steps that place
workstations. A spawn step carries the entity id, the position, and any SNBT
tags.

## Spawning villagers — the claim pattern

**In Java Edition, profession is assigned when a villager claims its
workstation — not at spawn time.** Do not try to force a profession via SNBT
at spawn. Use the spawn-then-claim pattern:

1. The workstation block is already placed (a `set` step) inside the building,
   within the villager's pathfinding range, and ≥2 blocks from any other
   workstation.
2. Summon `minecraft:villager` inside the building with `entity_summon`. Pass
   a `VillagerData` SNBT tag to set the biome skin type:
   `{VillagerData:{type:"minecraft:plains",profession:"minecraft:none",level:1}}`
   (swap `plains` for `desert`, `savanna`, `snow`, `swamp`, or `taiga`).
3. The villager pathfinds to the unclaimed workstation during the next daytime
   "seek work" tick and claims it — shown by green sparkle particles. It
   claims a reachable bed the same way.
4. Allow time — claiming is not instant. The `philosopher` verifies claims
   afterward (see "Verification" below).

Leave spare unclaimed villagers (and beds) if the user wants breeding.

## Iron golems

A golem spawns naturally only when the full set of conditions in
`mechanics.md` is met (≥10 villagers, ≥20 beds, …). That takes in-game time.
For **day-one defense**, spawn one golem directly: a `spawn` step
(`entity_summon`) for `minecraft:iron_golem` near the bell, on a clear surface
inside the 16×13×16 spawn volume centred on the village's average bed position.
Tell the user a *naturally respawning* golem still needs the full Java
conditions (see `mechanics.md`).

## Cats and animals

- **Cats** arrive on their own once the village has claimed beds (1 per dawn
  check while bed count exceeds cat count, cap 5 within 48 blocks). To seed
  them immediately, summon `minecraft:cat` near the meeting area with
  `entity_summon`.
- **Farm animals** — summon cows, pigs, sheep, and chickens inside their
  fenced, lit pens (`entity_summon` steps): a small breeding stock per pen.

## Verification

The population phase is not done when the entities exist — it is done when
they *function*. Hand the `philosopher` a check:

- Every profession villager claimed its workstation (green particles, robed).
- Every villager claimed a bed (sleeps indoors, no anger particles).
- If iron-golem-ready: the conditions in `mechanics.md` actually hold.

If a claim failed, the usual fixes: the workstation is out of the 16h/4v
range or unreachable; the bed pillow lacks 2 air blocks; two villagers raced
for one job site (space workstations apart); or the path is blocked. Re-place
the workstation or clear the path and let the villager re-claim.
