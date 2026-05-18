# Populating the village

A village is only functional once it has villagers who claim beds and jobs.
This is the **population phase** — it runs *after* the buildings are placed,
and the plan must sequence it that way: structures → villagers → animals →
iron golem.

## The plan's population steps

Population is expressed in `plan.toon` as `spawn` steps (the `worker` runs them
with `mc_entity_spawn`), interleaved with the `set` steps that place
workstations. A spawn step carries the entity id, the position, and any tags.

## Spawning villagers — the claim pattern

**Profession is not reliably set when a villager spawns in Bedrock.** Do not
rely on spawning a "librarian" directly. Use the spawn-then-claim pattern:

1. The workstation block is already placed (a `set` step) inside the building,
   within 16 blocks horizontal / 4 vertical of where the villager will be, and
   ≥2 blocks from any other workstation.
2. Spawn `minecraft:villager_v2` inside the building (a `spawn` step).
3. The villager pathfinds to the unclaimed workstation and claims it — shown
   by green particles. It claims a reachable bed the same way.
4. Allow time — claiming is not instant. The `philosopher` verifies claims
   afterward (see "Verification" below).

Choose the villager's biome skin to match the village biome. Leave spare
unclaimed villagers (and beds) if the user wants breeding.

## Iron golems

A golem spawns naturally only when the full set of conditions in
`mechanics.md` is met (≥10 villagers, ≥20 beds, …). That takes in-game time.
For **day-one defense**, spawn one golem directly: a `spawn` step for
`minecraft:iron_golem` near the bell, on a clear surface inside the 17×13×17
volume. Tell the user a *naturally respawning* golem still needs the full
conditions.

## Cats and animals

- **Cats** arrive on their own once the village has claimed beds (≈1 per 4
  beds, cap 5). To seed them immediately, spawn `minecraft:cat` near the
  meeting area.
- **Farm animals** — spawn cows, pigs, sheep, and chickens inside their
  fenced, lit pens (`spawn` steps): a small breeding stock per pen.

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
