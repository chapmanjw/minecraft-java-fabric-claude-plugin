# Special-site environments

Building a base into a non-flat site. Each environment has site-prep needs
(usually a `terraforming` pre-build step), structural rules, and hazards.

## Mountainside

- **Terrace the slope** rather than building on a ramp — a series of flat
  cut shelves linked by stairs. Carve *back into* the mountain for rooms
  rather than cantilevering out.
- Note a `pre-build terraform` step for the terracing.
- Add drainage so water from above does not sheet through rooms.
- A compound-of-pavilions or tower topology fits best.

## Underground / bunker

- A central hub with chambers off it; a clear vertical shaft to the surface
  as the escape route, with a ladder.
- **Light aggressively** — sunken sea lanterns, glowstone behind carpet — no
  dark cell anywhere; the surrounding dark stone spawns mobs the moment a
  cell is unlit.
- Keep a water source for bucket refills; iron-bar "vents" sell the look.
- Dwarven and industrial styles suit this.

## Cave conversion

- Work *with* the existing cave shape — irregular chambers, dripstone, natural
  stone — rather than boxing it out.
- **Avoid the deep dark.** Do not build a base inside a deep-dark biome
  without a plan to manage sculk sensors and shriekers — warn the user about
  the Warden.
- Light every reachable surface; cave mobs spawn fast.

## Underwater

- Build the shell, then **drain it with sponges** (or fill-then-remove water).
- A **conduit** grants water-breathing and night-vision: a prismarine /
  sea-lantern frame of **16 blocks minimum** activates it; the full 42-block
  frame gives the maximum range. Slabs, stairs, and walls do **not** count
  toward the frame.
- Domes and tubes, not sprawl — pressure and glass spans want compact forms.
- Before placing the structure, replace nearby sand/gravel seabed with a
  stable block so it does not collapse.
- Sea-lantern or glowstone lighting; the surface is far away.

## Sky base

- A solid pillar or several foundation columns to the ground — not a truly
  floating island unless the user accepts it as such.
- A **fall-protected rim** — a wall or scaffolding edge around every open
  side.
- Access by elevator (bubble column or scaffolding), ladder, or water drop;
  give a safe way down as well as up.

## Nether

- **Blast-resistant shell** — obsidian or crying obsidian against ghast fire.
- Overhanging eaves block ghast line-of-sight into windows.
- `gold_block` accents keep piglins neutral near the base.
- **No beds** — they explode in the Nether. Set spawn with a respawn anchor
  instead, and tell the user.
- A strider pen near lava for transport.

## End

- Wide platforms over the void; a void-safe railing on every edge.
- `end_stone`, `purpur`, and `obsidian` palette; a chorus-plant nook.
- **No beds** — they explode in the End; use the dimension's own spawn rules.

## Other biomes

Volcanic, frozen/glacier, jungle canopy, desert oasis, swamp stilts, bamboo
grove, mushroom island (note: mushroom islands suppress hostile spawns — a
genuine safety advantage worth telling the user). Each mostly drives the
**palette** (see `styles.md`) and minor structural tweaks (stilts over swamp
water, thick walls in the desert, steep roofs to shed snow).

## Always

- Whatever the site, the base still obeys the hard rules: light coverage, two
  exits, beds only where they will not explode, and rooms inside 64×384×64.
