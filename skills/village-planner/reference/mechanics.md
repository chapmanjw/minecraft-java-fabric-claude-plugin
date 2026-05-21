# Java Edition village mechanics

The functional contract. A village that ignores these looks fine and does not
work. All values are **Java Edition** (1.21.x / Fabric) — re-check after a
game update. The Minecraft Wiki pages for Village mechanics, Iron Golem, Bell,
Villager, Raid, and Cat are the source of truth.

## What makes a village

In Java Edition a **village** is defined by the presence of at least one
villager linked to at least one valid **bed**. There is no explicit "village
center" subchunk concept as in Bedrock. The iron golem spawn point and raid
anchor are derived from the positions of claimed beds, not from a fixed center
block. The **bell** is not required to form a village but is required for iron
golem spawning and raid-gather behavior — always include one.

## Villagers, beds, and workstations

### Bed claiming

- A villager claims an **unclaimed bed** it can pathfind to. The **pillow block
  needs 2 air blocks above it**; a slab, trapdoor, or any solid block over
  the pillow prevents the claim.
- A villager that cannot claim a bed will not sleep indoors and will show anger
  particles. It also cannot contribute to iron golem spawning.
- One villager per bed. Beds in a fully sealed room the villager cannot enter
  will not be claimed.

### Workstation (job-site block) claiming

- A villager claims an **unclaimed job-site block** within roughly **48 blocks**
  (pathfinding distance, not straight-line) during daytime "seek work" ticks.
  In practice, keep workstations within the same building or immediately
  adjacent to where the villager sleeps.
- **One villager per workstation.** Space workstations at least **2 blocks
  apart** — villagers race-claim the nearest unclaimed site; a cluster of
  workstations in one room may leave some villagers jobless if the distances
  are equal.
- **Profession is set when the villager successfully claims its workstation**
  (green sparkle particles). Do not rely on the spawn-time profession; use the
  spawn-then-claim pattern (see `population.md`).
- A villager loses its profession if its workstation is broken or moved out of
  range while it has not yet traded with the player. After a trade has
  occurred the link is permanent.

### Trading and gossip

- **Trading** unlocks higher-tier trades (1 trade per level: Novice → Master).
- **Gossip** is the Java-specific reputation system: villagers share gossip
  about the player (positive for trading/curing, negative for attacking) and
  this affects prices. Curing a zombie villager grants a major positive gossip,
  dramatically reducing that villager's trade prices.
- Gossip affects iron golem spawning indirectly: villagers that have recently
  panicked or been harmed broadcast negative gossip, which can lower the
  player's standing.

## Iron golems

Java Edition iron golem spawning is **gossip-and-sleep-based**, not a simple
villager-count threshold.

A golem spawns naturally when **all** of the following hold:

1. At least **3 villagers** can path to each other (they perceive each other
   as a "village").
2. At least one villager has attempted to sleep (day→night transition) in
   the last 24 000 game ticks (one in-game day) and was unable to (because of
   a threat — a hostile mob near a bed) — **OR** the village-wide "no golem
   recently seen" timer has elapsed (roughly 700 game ticks after the last
   golem died or was absent).
3. A valid **spawn surface** exists within a **16×13×16** box centred on the
   average position of the beds in the village (the "village center"). The
   surface must be solid, non-air, and have 2 clear blocks above it. Carpets,
   half-slabs, and low ceilings block spawns.

Practical design rules:
- **≥3 claimed beds** is the minimum; more beds = more villagers = more robust
  golem spawning.
- The **16×13×16** spawn area must be kept clear of solid obstacles, low
  ceilings, and water. Keep the bell in or near this area and do not build
  over it.
- A player house sitting on top of the village center blocks golem spawns —
  keep it **≥16 blocks** away from the average-bed center.
- For **day-one defense**, spawn one golem manually with `entity_summon` near
  the bell on a clear surface. Tell the user a *naturally respawning* golem
  still needs the full conditions above.

## The bell

- **Ring gather** — ringing the bell sends every nearby villager to seek their
  bed (the raid/threat response) and highlights nearby hostile mobs with a
  glowing outline for the player.
- **Raid anchor** — the bell is the focal point during a raid; villagers scatter
  toward their beds when it rings. Place it centrally so all villagers are
  within its 48-block gather radius.
- A bell does not need to be linked; simply placing it in the village is
  enough. However, for the raid and gather behavior to reach every villager,
  keep all bed pillows within **48 blocks** of the bell.

## Raids

- Triggered when a player with the **Bad Omen** effect enters the village
  boundary (within ~96 blocks of a claimed bed). Bad Omen is obtained by
  killing a **Raid Captain** (a pillager or vindicator carrying an ominous
  banner). In Java 1.21+ the effect is **Ominous Bottle** based — the player
  must drink an Ominous Bottle dropped by a Raid Captain to get Bad Omen.
- Waves: **3 / 5 / 7** on Easy / Normal / Hard; wave count scales with the Bad
  Omen level (I–V from multiple captains).
- **Raiders spawn on valid surfaces within ~128 blocks of the village center**
  (the average-bed position), outside the village or along paths toward it.
  **A fully sealed wall pushes spawn points inside** — always leave spawnable
  ground outside the walls. Walls slow ravagers; they do not stop a raid.
- Defeating all waves grants the **Hero of the Village** effect, giving
  discounted trades from all villagers.

## Breeding and willingness

Villagers breed when **willing** — the willingness condition in Java is:

- The villager has enough food in its inventory: **3 bread, 12 carrots, 12
  potatoes, or 12 beetroots** (any combination meeting the internal hunger
  threshold).
- There is at least one **unclaimed bed** (with 2 air blocks above the pillow)
  that the baby can claim.
- The villager is not in a "cooldown" from a recent breeding event.

A **breeding-ready** village design therefore needs:
- A **farmer villager** with a composter who actively harvests and throws food
  to other villagers (the Java food-sharing loop).
- **Spare unclaimed beds** above the current villager count — at least 1 free
  bed per baby slot desired.
- Enough food available in the village (a working crop farm, or the player can
  throw food to villagers to trigger willingness manually).

## Cats

- **Cats** spawn in villages that have at least **1 claimed bed** and fewer than
  **5 cats** within a **48-block** radius of the village center.
- The spawn check runs at dawn (once per in-game day). One cat attempts to
  spawn per check if the bed-to-cat ratio supports it.
- To seed cats immediately, spawn `minecraft:cat` near the meeting area with
  `entity_summon`.

## Wandering traders

- A **wandering trader** spawns near the player (not at the bell) on a random
  timer (15–60 in-game minutes). It brings two trader llamas.
- Leave a few blocks of clearance near the bell and main paths so its llamas
  do not get stuck on fences or doorways.

## Scripted villagers vs. emergent profession assignment

The spawn-then-claim pattern described in `population.md` is the default: the
game assigns a profession organically when a villager claims its workstation.
For **specific traders with fixed trade lists** (a named quest merchant, a
player-economy shop), use the scripted `entity_summon` NBT approach documented
in `population.md` instead — the two techniques are complementary, not
exclusive. Most villages mix both: organic workers for atmosphere, scripted
merchants for deliberate player-facing shops.

## Java-specific notes to plan around

- **Pillager outposts** in Java do *not* spawn inside villages the way they
  can on Bedrock — the generation rules prevent overlap. No special outpost
  warning is needed during site selection (unlike Bedrock).
- **Abandoned villages** in Java have cobwebs and zombie villagers, but the
  mechanical rules are the same as a normal village once repaired.
- Villagers in Java pathfind up to 3 blocks vertically over a single step, but
  steep slopes (>2 blocks per step) still prevent traversal. Grades steeper
  than ~2 blocks need `terraforming` to level them.
- **Villager sleeping and golem spawning require loaded chunks.** Keep the
  village inside a player's view distance or a force-loaded ticking area;
  operations on unloaded chunks will fail or not tick.
