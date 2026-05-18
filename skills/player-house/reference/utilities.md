# Functional systems & Bedrock mechanics

The working systems a base may include — and the **Bedrock-Edition rules** that
make Java tutorials wrong. Mechanics here are current as of Bedrock 1.21.x;
re-check them after a game update.

## Bedrock is not Java — refuse Java-only designs

- **No quasi-connectivity.** Piston doors and contraptions that rely on QC do
  not work. Use observer-driven or direct-powered designs instead.
- **Observers detect block updates**, not only block-state changes, and the
  Bedrock observer pulse is delayed an extra 2 — sometimes 4 or 6 — game ticks
  (MCPE-15793). Redstone timing from Java tutorials will be off.
- **AFK fishing does not work in Bedrock** — tripwire/door mechanics differ and
  Mojang does not intend to allow it. If the user wants emerald-generating
  fish, route them to a villager fisherman trading hall instead.
- **Hopper transfer order is non-deterministic.** Item sorters work, but need
  an overflow buffer; on the common "Dark Altair" sorter, use **20** filler
  items in part B, not 21, or the filter leaks.
- If the user asks for any of the above, **substitute the Bedrock-safe
  equivalent and tell them why** — do not silently build a broken farm.

## Storage & item handling

- **Auto-smelter** — a bank of hopper-fed furnaces/smokers/blast furnaces with
  a separate fuel feed. Works in Bedrock.
- **Item sorter** — works; needs the overflow buffer above. Filter chests over
  a hopper line keyed to each item.
- **Crafter (1.21)** — the `crafter` block enables automated crafting; pair
  with a redstone pulse and a hopper feed.

## Power & food farms

- **Iron farm** — Bedrock golem spawning needs a real village: **≥20 beds,
  ≥10 villagers, ≥75% of them having worked their workstation the previous
  day, every villager bed-linked.** Do not copy a 5-villager Java design — it
  will not produce golems.
- **Mob farm** — hostile mobs spawn in a spherical shell ~24–44 blocks from
  the player at simulation distance 4, and ~24–128 at sim-distance 6+. A dark
  central spawning platform with a water-funnel collection works well.
- **Crop farms** — kelp, bamboo, sugarcane, cactus, and tree farms all work;
  prefer observer- or piston-based harvest (no QC).

## Enchanting

The **15-bookshelf** setup gives the level-30 ceiling. Bookshelves must sit
exactly **2 blocks laterally** from the enchanting table, on the same level or
one block higher, and the **2-high gap between shelf and table must be empty**
— a torch, carpet, or snow layer in that gap zeros that shelf's contribution.
The standard form is a 5×5 ring of shelves around the table with the gap kept
clear.

## Beacon

A full **4-tier pyramid is 164 mineral blocks** (81 + 49 + 25 + 9 — 9×9, 7×7,
5×5, 3×3). Iron blocks are the cheapest valid material. The beacon needs a
clear vertical line of sight to the sky — leave an open shaft or a glass
column above it. Only a tier-4 pyramid unlocks the secondary effect.

## Conduit

A **16-block minimum** prismarine / sea-lantern frame activates a conduit; the
full **42-block** frame maximizes its range. Valid frame blocks: prismarine,
dark prismarine, prismarine bricks, sea lanterns — **slabs, stairs, and walls
of those do not count.**

## Other systems

Auto-brewing (dispenser-fed brewing-stand chain), XP storage (a bottling or
furnace-XP store), an ender-chest network across rooms, a lodestone array for
compasses, daylight-sensor auto-lighting, and sculk-sensor or
pressure-plate-triggered doors. For each, give the planner a footprint and a
material list, and flag any Bedrock parity caveat.

## For the plan

Every utility a base includes becomes rooms and steps in `plan.toon`. Give the
`planner`/`worker` a concrete block list and footprint — never "add a farm
here" without the dimensions. A redstone clock or always-loaded contraption
should carry a brief lag warning for the user.
