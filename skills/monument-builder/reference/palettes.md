# Monument palettes and gradients

A monument's material is half its identity. Build palettes deliberately, and
use **gradients** — a surface shaded across several blocks — to give a flat
block mass form and depth.

## The three palette families

- **Skin / colour** — saturated `concrete` and `wool` for figurative colour
  (a creature's hide, a painted figure, pixel art). Concrete is the most
  saturated; wool is softer.
- **Stone** — `calcite`, `smooth_quartz`, `diorite`, `andesite`, `granite`,
  `smooth_stone`, `bone_block` — for marble and granite statuary.
- **Metal** — `copper` (and its oxidation chain), `iron_block`, `gold_block`,
  `raw_gold_block` — for bronze, steel, and gilded monuments.

## Copper oxidation — the signature gradient

This is the standout technique for any weathered-bronze monument (a
Liberty-style figure). Copper passes through **four oxidation stages** —
`copper_block` → `exposed_copper` → `weathered_copper` → `oxidized_copper` —
from fresh orange to green verdigris, and each stage has a **waxed** variant
that locks it.

Use the stages as a gradient across the figure:

- **Oxidized (green)** on the broad, weather-exposed surfaces — the bulk of a
  patinated statue.
- **Weathered / exposed** on lit folds and edges where rain washes patina off.
- **Fresh copper** as a warm accent on the most sheltered or recently
  touched parts.

Place the blocks **waxed** so they hold the intended stage (unwaxed copper
keeps oxidizing). For a deliberately *aging* look, leave some unwaxed.

## Marble and stone gradients

- **Marble** — blend `calcite` (white) + `smooth_quartz` + `bone_block` +
  `diorite`, mixed so no repeat is obvious; veining with thin `andesite`
  lines.
- **Granite statuary** (a Rushmore-style face) — blend `smooth_stone` +
  `andesite` + `polished_diorite` + `granite` for a grey weathered look.
- **Sandstone** (a Sphinx) — `sandstone`, `smooth_sandstone`, `cut_sandstone`,
  with `terracotta` accents for warmth.

## Shading a form

A single-block surface reads flat. Shade it across the form:

- **Light and shadow** — a slightly lighter block on surfaces facing up and
  toward the light, a darker one in the recesses and undersides. This gives a
  block figure the modelled look of a sculpture.
- **Gradient transitions** — step between two blocks over a band of mixed
  placement rather than a hard line, so the change reads as shading not a seam.
- Keep the gradient consistent with one light direction across the whole
  monument.

## Decorative tile

`glazed_terracotta` gives 16 colours, each a pattern with 4 rotations — a
large vocabulary for mosaic backgrounds, ornamental bases, and abstract
panels.

## Note

Minecraft has **no true mirror or transparent-metal block** — a reflective
sculpture (Cloud Gate) is approximated with polished/metallic blocks and is an
accepted stylization, not a literal match. Tell the user.
