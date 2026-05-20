# Vernacular modules — the reuse library

The **load-bearing technique** of this skill. A city is mostly not landmarks —
it is hundreds of ordinary buildings of a few recurring types. Define each type
once and reuse it. This is the `village-planner` reuse model, scaled up to a
city and its street blocks.

## The build-once-stamp-many model

1. **Identify the vernacular types** for the city — usually 3–6 (e.g. for
   Haussmann Paris: the apartment block, the corner block, the ground-floor
   shopfront). Most of the city is these.
2. The `blueprinter` builds each type **once** and saves it as a named
   structure, `mcb:<project>_vern_<type>` (with its variants).
3. The `worker` **stamps** the type along every block edge the layout calls
   for, using rotation and mirror for corners and opposite sides.
4. **Vary every copy** — see "Parametric variation" — so a row reads as
   individual buildings.
5. Record the types and instances in `mcbuilder:registry`.

## Vernacular module types

Footprints are W×D at 1:1; pick the types that match the city's era.

| Module | Footprint | Storeys | Era / city |
| ------ | --------- | ------- | ---------- |
| Roman insula | 10–15 × 20–25 | 3–5 | Roman apartment block |
| Roman domus | 10–15 × 20–30 | 1–2 | Roman courtyard house |
| Haussmann block | full block face × 15–20 deep | 5–6 + mansard | 19C Paris |
| Manhattan brownstone | 6–8 × 12–17 | 4–5 | 19C New York rowhouse |
| Tenement | 8 × 25 | 5–6 | dense 19–20C apartment |
| Edo machiya | 6 × 20 | 1–2 | Japanese row house, deep narrow lot |
| Beijing siheyuan | 15 × 42 | 1 | courtyard house on a hutong |
| Amsterdam canal house | 5–7 × 20–30 | 3–4 + attic | tall narrow gabled house |
| Shophouse | 5–6 × 20–60 | 2–3 | arcaded SE-Asian commercial row |
| Georgian terrace | 5–6 × 10–15 | 3–4 + basement | British terraced housing |
| Half-timber house | 6–8 × 8–10 | 2–3 | medieval European |
| Modern mid-rise | varies | 4–10 | 20–21C mixed-use |
| Tower shell | varies | many | modern skyscraper (a façade shell) |

For an era or city not listed, derive a type the same way: a footprint, a
storey count, a palette, and the 2–3 features that identify it.

## Parametric variation

A row of identical stamped modules is the caricature this skill exists to
avoid. Each module ships with **variants** so a row reads as individual
buildings while still sharing the city's discipline:

- **Shared discipline** — what *must* line up across the row: the cornice line,
  the floor levels, the lot width, the stoop rhythm. This is what makes Paris
  read as Paris.
- **Per-copy variation** — what *changes* between copies: window pattern,
  paint/palette accent, door and awning, balcony presence, roof-tile variant,
  signage, shopfront vs. plain ground floor.
- **Corner variants** — a different module for the corner of a block.
- **Terminator variants** — the end-of-row condition.
- Carry 8–12 variant schedules per module; cycle through them along a row,
  never repeating two adjacent.

## Regulated uniformity

Some cities get their identity from *regulated* uniformity — lean into it:

- **Haussmann Paris** — every block to a locked cornice height, balconies on
  set floors, 45° mansard, one cream-limestone palette.
- **Manhattan** — a standard lot width and a brownstone stoop-and-cornice
  rhythm.
- **Amsterdam** — narrow standard plot widths, but a *varied* gable type
  (stepped, neck, bell, spout) from house to house.

Uniformity is a design tool, not a failure — but it is *disciplined* sameness
(aligned lines) with *detail* variation, never identical copies.
