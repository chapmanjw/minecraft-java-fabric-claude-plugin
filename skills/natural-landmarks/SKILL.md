---
name: natural-landmarks
description: >-
  Composes recognizable real-world natural wonders and landmarks — canyons,
  mesas, monoliths, volcanoes, waterfalls, karst towers, glaciers, sea stacks,
  salt flats — in a live Minecraft Java Edition world from a library of reusable
  formation primitives. Use when a build recreates a named natural wonder
  (Grand Canyon, Niagara, Uluru, Halong Bay, Giant's Causeway, …) or a
  recognizable landmark type. Part of the minecraft-builder workflow.
model: sonnet
effort: high
---

# Natural Landmarks

You recreate **recognizable natural wonders** — the Grand Canyon, Niagara,
Uluru, Halong Bay — in a live Minecraft Java Edition world. You are a *composer*:
you assemble wonders from a library of reusable **formation primitives**, you
do not invent each one from scratch.

This skill is the specialist for *named or recognizable* landmarks. For generic
terrain and scenery, use `terraforming` instead — and lean on its technique
either way (`terraforming` is the underlying landscaping craft; this skill is
the composition layer on top of it).

## Connection

If a tool call fails because the MCP server is unreachable, stop and tell
the user to run the `minecraft-mcp-setup` agent.

## The core principle

**Recognizability comes from 2–4 signature features at credible relative
proportions — not from size.** A 60-block-deep canyon with seven named strata
bands, a meandering river, and side canyons reads as the Grand Canyon. A
200-block hole in one terracotta colour does not.

Two rules follow:

- **Componentize, don't recipe-code.** Every wonder decomposes into 2–5
  reusable primitives plus a palette and a scale ratio. The same `hoodoo-spire`
  serves Bryce, Cappadocia, and Goblin Valley; the same `karst-tower` serves
  Halong, Guilin, and Phang Nga. Wonder recipes are *data*, not bespoke code.
- **Nail the signatures.** Identify the 2–4 features that make the wonder
  itself, and get those right above all else. Missing one — Niagara without the
  horseshoe, Devils Tower without vertical column striations — and the build
  reads as generic terrain.

## The composer workflow

1. **Identify the wonder.** Named (use the researcher's findings and
   `reference/wonders.md`) or described freeform. Pin down its **2–4 signature
   features** explicitly — write them down; the `philosopher` checks against
   them later.
2. **Decompose into primitives.** Look the wonder up in `reference/wonders.md`
   for its primitive composition, or for a freeform request pick primitives
   from `reference/primitives.md` by family.
3. **Choose a palette.** Select a named preset from `reference/palettes.md`
   (e.g. `colorado-plateau`, `karst-limestone`, `basalt-volcanic`); let the
   user override.
4. **Set scale.** Enforce the **minimum recognition floor** from
   `reference/wonders.md` — a "Niagara" requested at 10 blocks tall must be
   scaled up to its threshold (or flagged). Keep each wonder's signature
   *aspect ratio* (Uluru is ~3:1 wider than tall; Devils Tower is tall and
   narrow).
5. **Order the build.** Each primitive is **carve-first** or **build-up-first**
   — never chosen ad hoc. See `reference/sequencing.md`.
6. **Emit the composition.** Write a composition manifest to
   `.minecraft-builder/<project>/landmark.toon`, and expand it into terrain
   phases in `plan.toon` for the `worker`.

## Reference library

Read the file for the step you are on — do not load them all up front:

| File | Covers |
| ---- | ------ |
| `reference/primitives.md` | The formation-primitive library — dimensions, build method, and approach for each. |
| `reference/wonders.md` | Named real-wonder recipes: signature features, minimum recognition footprint, palette, and primitive composition. |
| `reference/palettes.md` | Named palette presets with Java block IDs and mix ratios. |
| `reference/sequencing.md` | Carve-first vs build-up-first rules, water-last, integrity weathering passes, lighting tricks. |
| `reference/anti-patterns.md` | The signature-and-proportion failure checklist the `philosopher` reviews against. |

For volume limits, tiled fills, structure modules, ticking areas, and
randomness without `/random`, follow the **`terraforming` skill's
`reference/command-budget.md`** — the same rules apply here.

## The composition manifest

`landmark.toon` records the composition so a build can be rebuilt or iterated:

```toon
landmark:
  wonder: grand-canyon
  project: red-rock-park
  origin: {x: 0, y: 64, z: 0}
  scale: "1:7000"
  palette: colorado-plateau
signatures[4]{feature}:
  seven-band-strata
  meandering-river
  perpendicular-side-canyons
  vermillion-caprock
primitives[4]{seq,primitive,x,y,z,method,params}:
  1,canyon-strata-stack,0 4 0,,,build-up,"bands=7 length=250 depth=60"
  2,slot-canyon-segment,40 64 0,,,carve,"depth=55 width=8 meander=true"
  3,side-canyon,90 64 12,,,carve,"count=5 spacing=80"
  4,plunge-pool,120 9 100,,,carve,"river=true"
```

## How it feeds the pipeline

- **Plan** — expand each primitive into phases and pre-tiled steps in
  `plan.toon`, using the standard `steps` table. Resolve all coordinates to
  absolutes; the Haiku `worker` does no arithmetic. For any primitive
  whose footprint exceeds ~30 blocks, follow terraforming's heightmap method
  (`terraforming/reference/landforms.md § The heightmap method`) — stacked
  rectangular fills produce the ziggurat artifact, every time.
- **Modules** — save reusable primitive instances as named structure templates
  **`mcb:<project>_<primitive>_<index>`** (colon namespace — required; an
  underscore-only ID is rejected) via `structure_save_from_world` /
  `structure_load_to_world`, like the `blueprinter`. Reuse them with rotation,
  mirror, and `integrity` for weathered variation. A landmark at minimum
  recognition size can span several structure templates (max 64×384×64 each) —
  tile them.
- **Quality contract** — emit a `quality_contract` block per
  `planner/SKILL.md`, with terrain rows from
  `terraforming/reference/non-negotiable-enforcement.md`:
  - **silhouette** for the landmark's overall mass (no flat plateaus).
  - **edge_irregularity** for every recognisable rim, ridge, or coastline.
  - **block_mix_ratios** for every banded or weathered surface.
  - **asymmetry** to confirm the build isn't a mirror-perfect cone.
  - **foundation_naturalised** if the wonder rises from a sea or basin.
- **Registry** — record the landmark and its modules in `mcbuilder:registry`
  command storage (namespace `mcbuilder`, path `registry`, via `data_storage_set`
  / `data_storage_get`).

## Quality gate

Before handing off, check the build against the **signature features** you
identified in step 1 and against `reference/anti-patterns.md` — insufficient
strata bands, wrong colour sequence, symmetric-where-asymmetric, missing
signature, scale below the recognition floor. If a signature is weak or
missing, fix it before reporting done. The `quality_contract` rows above are
the inspector's automated form of this gate; both run.

## Hand off

State the wonder, its signature features, the chosen scale, and the primitive
composition back to the user, and confirm before building. The terrain phases
are now in `plan.toon`; the manifest and modules are recorded for later
iteration.
