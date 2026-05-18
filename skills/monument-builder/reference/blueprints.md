# Monument blueprint rendering and validation

Propose the piece as blueprints the user can react to, then iterate. A
monument is a 3D form — render it from more than one angle.

## Rendering modes

Produce these in `.minecraft-builder/<project>/` and show the user before
resolving a plan:

- **Silhouette views** (`silhouette.txt`) — ASCII front and side elevations,
  one character per block, so the user can check the outline reads as the
  subject. The silhouette is the single most important thing to get right.
- **Cross-sections** (`sections.txt`) — a few horizontal slices (per Y band)
  showing the form's footprint at different heights — the practical guide for
  a figure or creature.
- **Pixel grid** (`grid.txt`) — for pixel art and murals, the block grid with
  a palette key.
- **Palette sheet** (`palette.md`) — the blocks used, and the gradient bands
  (which block goes where on the form).
- **Tile plan** (`tiles.md`) — for a tiled monument, the split into
  structures with absolute offsets and the anatomy seam each split follows.

## Iteration

1. Render the silhouette views, cross-sections, and palette sheet.
2. Show the user; take feedback on the silhouette, proportion, pose, palette.
3. Revise and re-render.
4. Loop until the user explicitly approves.
5. Only then resolve to `plan.toon`.

## Validation checklist

Check the design — and have the `inspector` and `philosopher` re-check the
build — against these failure modes:

- **The silhouette does not read** as the subject — the core failure. Thicken
  the outline, sharpen the signature features, raise the palette contrast.
- **Wrong proportion** — a too-short neck, undersized head, wrong arm-span;
  re-anchor to the catalog/researcher dimensions.
- **Wrong palette or colour** — a green-patina statue built fresh-copper, a
  white monument built grey.
- **Flat, unshaded mass** — a single-block surface with no light-and-shadow
  gradient reads as a blob, not a sculpture.
- **Visible tile seams** — a split made through a smooth surface instead of an
  anatomy seam (a joint, a waist, a neck).
- **Scale exceeds the Y range**, a fill over 32,768, or a structure over
  64×384×64 — scale down, pre-tile, or split.
- **Pixel art too small** — fine features lost; upscale until they read.
- **Accidental interior program** — a monument is solid or a hollow shell; a
  habitable space inside belongs to `building-architect`.
- **Armor-stand overuse** — entities used for bulk instead of accent.

A silhouette that does not read is a correction to make, not a cosmetic note —
it is the whole point of the piece.
