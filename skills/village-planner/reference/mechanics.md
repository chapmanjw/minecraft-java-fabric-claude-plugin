# Bedrock village mechanics

The functional contract. A village that ignores these looks fine and does not
work. All values are **Bedrock Edition** (they differ from Java) and current as
of 1.21.x — re-check after a game update. The Minecraft Wiki pages for Village
mechanics, Iron Golem, Bell, Villager, Raid, and Cat are the source of truth.

## What makes a village

A **village center** is any subchunk holding a claimed bed, a bell, or a job
site; the village is the 3×3×3 cube of subchunks around it. So a few beds plus
workstations near a bell already register as a village.

## Villagers, beds, and workstations

- **Workstation claim** — a villager claims an unclaimed job-site block within
  **16 blocks horizontally and 4 blocks vertically**, by pathfinding (not line
  of sight). One villager per workstation.
- **Bed claim** — a villager claims a bed it can pathfind to. The **pillow
  needs 2 air blocks above it**; slabs or trapdoors over the bed block the
  claim. A villager that cannot claim a bed sleeps outside and shows anger.
- **Profession is not reliably set at spawn in Bedrock.** The dependable
  pattern is: spawn the villager → place its workstation in range → wait for
  the green-particle claim. See `population.md`.
- Space workstations **≥2 blocks apart**, ideally one per room — Bedrock can
  race-claim a shared job-site list, leaving a villager jobless.

## Iron golems

A golem spawns naturally only when **all** of these hold:

- **≥10 villagers** and **≥20 beds** in the village;
- ≥75% of villagers worked their workstation the previous day;
- every villager is linked to a bed;
- there is a valid spawn surface in the **17×13×17** volume (±8 horizontal,
  ±6 vertical) around the village center — the bell or any claimed-bed pillow.

Keep that volume clear of obstruction (carpets, half-slabs, low ceilings). A
player house sitting on the bell blocks golem spawns — keep it ≥16 blocks away.
For day-one defense, spawn one golem manually (see `population.md`).

## The bell

- **Auto-claim** — a bell placed within **48 blocks** of a claimed-bed pillow,
  with a valid path, is claimed automatically (between day-time ticks
  9000–12000). Place it at the meeting plaza.
- **Ring gather** — ringing the bell sends every villager within **32 blocks**
  to the nearest bed (the raid/danger response).

## Raids

- Triggered when a player with Bad Omen enters the village; waves are
  **3 / 5 / 7** on Easy / Normal / Hard.
- Raiders spawn on valid surfaces within a **64×23×64** zone around the village
  center. **A fully sealed wall makes them spawn inside** — always leave
  spawnable ground outside the wall. Walls slow ravagers; they do not stop a
  raid.

## Breeding

Villagers breed when willing — fed enough food (bread, carrots, potatoes,
beetroot) — and there is an **unclaimed bed with 2 air above the pillow** for
the baby. A breeding-ready village wants spare beds and a farmer with a
composter feeding the food loop.

## Cats and wandering traders

- **Cats** spawn at roughly **1 per 4 claimed beds**, capped at **5 per
  village**; the spawn check uses a 97×17×97 box around the village center.
- A **wandering trader** spawns periodically anchored near the bell — leave a
  few air blocks of clearance there so its llamas do not get stuck.

## Bedrock quirks to plan around

- **Pillager outposts can spawn next to or inside a village** in Bedrock
  (unlike Java). Warn the user during site selection and offer to relocate.
- Vanilla Bedrock villages do not always generate every building type, and a
  notable share generate as "abandoned" — design to the user's intent, not to
  Java expectations.
- Bedrock paths regenerate at terrain level over slopes; grades steeper than
  ~2 blocks need `terraforming` to level them or villagers cannot traverse.
