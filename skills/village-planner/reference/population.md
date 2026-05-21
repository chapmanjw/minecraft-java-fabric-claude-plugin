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

## Java-exclusive: scripted villagers (exact traders and trade lists)

The spawn-then-claim pattern above produces organic behavior — the game assigns
profession and trades. Use it when you want a living, self-managing village.

**When the user wants a specific trader with predetermined trades**, use
`entity_summon` with a full NBT payload instead. The `VillagerData` tag sets
profession, biome type, and level at spawn; `Offers.Recipes` hardwires the
trade list. This villager still needs a bed and workstation in range (for the
golem conditions), but its trades are fixed from the moment it spawns:

```
entity_summon("minecraft:villager", pos, nbt='{
  VillagerData:{profession:"minecraft:librarian",type:"minecraft:plains",level:3},
  CustomName:"{\"text\":\"Archivist\"}",
  Offers:{Recipes:[{buy:{id:"minecraft:emerald",count:8},
    sell:{id:"minecraft:enchanted_book",count:1},maxUses:5}]}}')
```

- **`VillagerData.profession`** — one of `minecraft:armorer`, `minecraft:butcher`,
  `minecraft:cartographer`, `minecraft:cleric`, `minecraft:farmer`,
  `minecraft:fisherman`, `minecraft:fletcher`, `minecraft:leatherworker`,
  `minecraft:librarian`, `minecraft:mason`, `minecraft:shepherd`,
  `minecraft:toolsmith`, `minecraft:weaponsmith`, or `minecraft:none`.
- **`VillagerData.type`** — biome skin: `plains`, `desert`, `savanna`, `snow`,
  `swamp`, or `taiga`.
- **`VillagerData.level`** — 1 (Novice) through 5 (Master).
- **`Offers.Recipes`** — each recipe has `buy` (first item), optionally `buyB`
  (second item), `sell`, and `maxUses`. Set `rewardExp:0b` to suppress XP.
- Add `PersistenceRequired:1b` so the villager does not despawn.

The SNBT shape of `Offers` (and item id format) is version-sensitive across
1.20.x → 1.21.x. Verify the exact format against the running server version
with `server_get_status`, then do a round-trip: summon the villager, read it
back with `entity_get_nbt`, and confirm the trades loaded correctly.

To patch trades on an already-spawned villager, use `entity_set_nbt` with the
same `Offers` block (merges into the existing entity).

**When to use which approach:**

| Goal | Use |
| ---- | --- |
| Organic village that feels lived-in | Spawn-then-claim (profession set by workstation) |
| Specific quest merchant, unique trader | Scripted summon with full NBT |
| Fixed-price shop that won't be reset by players | Scripted summon + `PersistenceRequired:1b` |

## Java-exclusive: mob loadout NBT (named/equipped/static mobs)

`entity_summon` (or `entity_set_nbt` on an existing mob) accepts equipment and
behavior flags, which the Bedrock MCP could not set:

```
entity_summon("minecraft:zombie", pos, nbt='{
  CustomName:"{\"text\":\"Guard\"}",
  CustomNameVisible:1b,
  HandItems:[{id:"minecraft:iron_sword",count:1},{}],
  ArmorItems:[{id:"minecraft:iron_boots",count:1},{id:"minecraft:iron_leggings",count:1},
              {id:"minecraft:iron_chestplate",count:1},{id:"minecraft:iron_helmet",count:1}],
  HandDropChances:[0.0f,0.0f],
  ArmorDropChances:[0.0f,0.0f,0.0f,0.0f],
  NoAI:1b,
  PersistenceRequired:1b}')
```

- `NoAI:1b` — freezes the mob in place; useful for static display guards,
  scarecrows, or decorative creatures.
- `HandDropChances`/`ArmorDropChances` all `0.0f` — mob drops nothing when
  killed (keeps the display clean).
- `PersistenceRequired:1b` — prevents despawn. Always include for any mob that
  is a named landmark in the village.
- `Glowing:1b` — adds a permanent glowing outline; useful for ceremonial guards.
- Omit `NoAI` (or set `NoAI:0b`) to get a patrolling guard that still wears the
  equipment.

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
