# The module library

The central technique of this skill: **define modules, do not build brick by
brick.** A detailed building is overwhelming as one mass and impossible to keep
within Bedrock's limits as a single fill. As a kit of repeated modules it
becomes tractable, consistent, and fast.

## What a module is

A module is **one repeating architectural component**, defined once as a named
structure and reused. A Gothic cathedral is not a million blocks placed by
hand — it is:

- 1 flying-buttress module, stamped ~30 times along the nave;
- 1 window-bay module, stamped ~20 times;
- 1 nave-vault bay, stamped along the length;
- 2 tower modules; 1 spire; 1 rose-window module; 1 portal module.

That is a handful of designed pieces, then placement.

## The build-once-stamp-many model

1. **Identify the modules** — scan the building for what repeats: bays, tiers,
   towers, buttresses, window units, roof segments.
2. The `blueprinter` builds each module **once** and saves it as a named
   structure, `mcb_<project>_<element>` (e.g. `mcb_notredame_buttress`).
3. The `worker` **stamps** each module wherever the manifest places it, using
   rotation and mirror for corners and opposite faces.
4. **Vary** to avoid a copy-paste look — alternate two window variants, age
   copper differently per batch, tweak a palette accent. Variation lives in a
   small set of *variant* modules, not in unique hand-building.
5. Record every module and its instances in `mcbuilder:registry`.

A module must fit **64×384×64** (one structure file). Anything larger is split
into several modules joined by an overlap.

## Module catalog by category

Compose a building's manifest from these kinds:

**Structural**
- Curtain-wall section — a run of wall with its courses and crenelation.
- Tower — round (octagon-via-stairs) or square; carry 2–3 height variants.
- Buttress / flying buttress — the pier and its arched reach.
- Arch bay — one arcade unit (Colosseum, aqueduct, cloister).
- Column / pilaster — with base and capital.

**Roof**
- Pagoda / hip / gable roof segment.
- Dome segment — one wedge of an octagonal or ribbed dome.
- Spire / finial.

**Façade**
- Window bay — the window and its surrounding wall and trim.
- Setback step — one tier of an Art Deco or ziggurat profile.
- Portal / door surround — the main entrance unit.
- Balcony / oriel.

**Ornament**
- Rose window.
- Frieze / cornice run.
- Crenelation run.
- Statue / finial sculpture.

**Interior** (when furnishing — see `interiors.md`)
- A furnished room template, reused for repeating rooms (cells, dorms,
  offices).

## Tiling rules

- Keep each module within the 64×384×64 structure cap and each constituent
  fill within 32,768 blocks (the `worker` runs pre-tiled).
- Design modules to **align on a grid** so stamped copies meet cleanly — a
  buttress every 8 blocks, a window bay every 6.
- Where a module meets terrain or another module, design a deliberate seam
  (a course, a pilaster) so the join reads as intentional.
