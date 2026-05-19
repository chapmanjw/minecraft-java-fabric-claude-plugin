# Pixel art, murals, text, and logos

Turning a 2D image — a sprite, a painting, a logo, a glyph — into a block
grid. The technique is **quantize, grid, lay**.

## Pixel-grid image mapping

1. **Get the source image** — the `researcher` can fetch a reference (a game
   sprite, a logo, a flag). Note its pixel dimensions.
2. **Choose the output size** — one image pixel maps to one block. Upscale a
   small sprite by an integer factor (a 16×16 sprite × 3 = 48×48) so edges
   stay crisp. Add a 1-block border if it wants framing.
3. **Quantize to a block palette.** Map each pixel's colour to the nearest
   block in a chosen palette. **Solid-colour blocks** are what make pixel art
   read — `concrete` (the most saturated), `wool`, `terracotta`, and `glazed
   terracotta` for patterned accents. Build the palette deliberately: pick the
   ~8–24 blocks that cover the image's colours, not every block.
4. **Dither or not.** A clean sprite or logo with flat colours quantizes
   crisply — **no dithering**. A photograph or painting with gradients reads
   better with dithering (alternating two near blocks to suggest an
   in-between tone). Say which you used.
5. **Lay it as a grid.** A quantized image *is* a block grid — the most direct
   way to build it is to have the `blueprinter` generate a run-length-encoded
   block grid and build it with `mc_structure_create_from_blocks` (see the
   blueprinter's `reference/generated-structures.md`): one palette, one index
   per pixel. The plan then places it with a single `place-structure` step.
   Fall back to `fill` / `set` rows in `plan.toon` only for a small or simple
   grid. A flat mural is one block deep.

## Flat vs. relief

- **Flat** (1 block deep) — the default; reads cleanly head-on.
- **Low relief** (raise some regions 1 block) — gives parallax shadow at an
  angle; good for a logo or an emblem. Raise the foreground elements.
- **Orientation** — a wall mural stands vertical; a floor mosaic lies flat and
  reads from above. Quantize the same way; choose the plane.

## Scale and tiling

A mural wider or taller than 64 blocks exceeds one structure file — split it
into tiles on a clean grid line and record the offsets. Keep `fill`/`set`
runs pre-tiled within the 32,768-block cap (a flat mural rarely approaches it).

## Text and logos

- **Block alphabets** — design (or reuse) a glyph grid: 5×7 is the compact
  minimum; 7×9 and larger give serifs and weight. Keep glyph height and
  spacing consistent across a word.
- **3D extruded text** — give letters depth (3–6 blocks) for a freestanding
  sign; pitch or bevel the faces for a logo.
- **Hillside letters** (a Hollywood-sign style) — tall freestanding letters on
  a slope, each its own structure, spaced along the contour.
- **Logos** — treat as pixel art with a tight palette; a simple flat logo is
  often cleaner than a relief one.
- **Banners** — for small heraldic devices, layered banner patterns can carry
  a logo at a fraction of the block count; for large logos, use the block
  grid.

## Common mistakes

- Too small — fine detail in a sprite is lost below a certain block size;
  upscale until the features read.
- Palette too wide — using a near-match block for every pixel makes mud; a
  tight, deliberate palette reads sharper.
- Dithering a flat sprite — adds noise to something that was already clean.
