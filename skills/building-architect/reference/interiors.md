# Interiors and interior depth

The user chooses how deep the interior goes. This is the **single biggest cost
driver** — surface it early and quote a fill-volume estimate.

## The three interior-depth modes

- **Aesthetic-only** — the exterior is fully detailed; interiors are empty
  shells (floors, walls, ceilings, glazing, lighting) but unfurnished. Lowest
  cost. Good for distant landmarks and pure showpieces.
- **Hybrid** — the user names a few **hero rooms** (the Great Hall, the throne
  room, the library); those are fully furnished, the rest are shells. The
  usual choice for large buildings.
- **Fully furnished** — every room furnished and decorated. An order of
  magnitude more block placement than aesthetic-only. Right for buildings the
  user will actually live in or tour.

Estimate fill volume roughly as
`Σ(module footprint × height) × density`, with density ≈ 0.4 aesthetic /
0.7 hybrid / 0.95 fully furnished. Give the user the number before designing.

## Rules for any furnished interior

- **Every hero room visible from outside** — a furnished room with no window
  or doorway is wasted; add an opening or move the room.
- **Light coverage** — no spawnable dark cell; prefer hidden light (a glowstone
  under a carpet, a sea lantern behind a slab).
- **Match the era** — no Victorian furniture in a medieval hall; furnishing
  follows the building's period.

## Furnishing by era

Use vanilla block tricks (stairs, slabs, trapdoors, fences, item frames,
banners — see the `player-house` skill's `interiors.md` for the catalogue of
furniture forms) with period-appropriate materials:

- **Medieval / Gothic** — long timber tables and benches, banners, iron
  chandeliers (lanterns on chains), rushes (carpet), stone hearths, chests and
  barrels. Cathedrals: pews, an altar, candles, a great rose window lit from
  behind.
- **Classical / Renaissance** — symmetric furniture, columns, statuary
  (armor stands), marble floors, urns (flower pots and finials).
- **Baroque / palace** — gilding (gold blocks), grand staircases, chandeliers,
  long galleries, framed art (paintings, item-frame mosaics).
- **Victorian** — cluttered, patterned (carpets, glazed terracotta), heavy
  drapery (banners, wool), fireplaces.
- **Modern** — minimal, large glazing, hidden lighting, open plan, quartz and
  concrete surfaces.
- **Fantasy** — match the style from `fictional.md`: glowing crystals and soul
  fire for arcane, lava and anvils for dwarven, leaf-and-vine detail for
  elven.

## Signature interiors

Some buildings are defined by an interior as much as a façade — the Hagia
Sophia's dome from within, a Gothic nave, a great hall. When a building has a
signature interior space, treat it as a hero room even in hybrid mode.
