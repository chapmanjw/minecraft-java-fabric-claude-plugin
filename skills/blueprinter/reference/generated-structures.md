# Generating a structure from a block grid

`mc_structure_create_from_blocks` turns a **block grid you compute** into a
saved structure — without building it in the world block by block first. Use
it for any element easier to describe with a formula or a script than to lay
by hand: pixel-art murals, voxelized models, anything image-mapped or
parametric.

It is the third blueprint method, alongside capture-from-world and the
`mc_structure_set_block` loop.

## How it works

You hand the tool a structure definition — a block palette plus a
run-length-encoded grid of palette indices. The behavior pack builds it in the
world as a **world-saved** structure: it exists immediately, is placeable with
`mc_structure_place`, shows up in `mc_structure_get` / `mc_structure_list`, and
persists across reloads. No files, no world reload.

## The definition

`mc_structure_create_from_blocks` takes:

- **`id`** — the structure identifier, e.g. `mcb:lakeside-village_mural`. Use
  the same `mcb_<project>_<element>` / `mcb:` naming as any other blueprint.
- **`size`** — `{ x, y, z }` extents in blocks.
- **`palette`** — the distinct block states, indexed from 0. Each entry is a
  block `name` and optional `states` (e.g. `{ "pillar_axis": "y" }`).
- **`blocks`** — the grid, run-length encoded (see below).
- **`save_mode`** — `"world"` (default) or `"memory"`. Leave it at `world` for
  a reusable blueprint.

### The block grid — ZYX order, run-length encoded

Conceptually the grid is one palette index per cell, in **ZYX order**: the cell
`(x, y, z)` sits at flat index

```
z + size.z * (y + size.y * x)
```

An index of **`-1`** is a structure void — the existing world block is left
untouched when the structure is placed. Use it for empty space and the
transparent parts of a mural.

`blocks` is that flat sequence **run-length encoded** as `[count, index]`
pairs. A 16×16 mural with a solid background is a handful of runs, not 256
integers. The run counts must sum to `size.x * size.y * size.z`.

```
blocks: [[60, 0], [3, 1], [12, 0], ...]   // 60 cells of palette[0], then 3 of palette[1], ...
```

A region with no repetition degrades to `[1, index]` runs — still valid.

## Generating it

Do not hand-write the runs. Generate them with a short script:

1. Build the per-cell index array in ZYX order (a nested x → y → z loop).
2. Collapse equal neighbours into `[count, index]` runs.
3. Call `mc_structure_create_from_blocks` with the palette and the runs.

Example — a 16×1×16 checkerboard floor:

```python
sx, sy, sz = 16, 1, 16
cells = []
for x in range(sx):
    for y in range(sy):
        for z in range(sz):
            cells.append((x + z) % 2)            # palette index 0 or 1
runs, i = [], 0
while i < len(cells):
    j = i
    while j < len(cells) and cells[j] == cells[i]:
        j += 1
    runs.append([j - i, cells[i]])
    i = j
# mc_structure_create_from_blocks(
#   id="mcb:demo_floor",
#   size={"x": 16, "y": 1, "z": 16},
#   palette=[{"name": "minecraft:white_concrete"}, {"name": "minecraft:black_concrete"}],
#   blocks=runs)
```

The whole definition travels in the tool call, so keep it reasonable: a single
call comfortably handles a few thousand blocks. For anything larger, tile it
into multiple structures — the same tiling the blueprinter already applies for
the 64×384×64 structure-size limit.

## Register and verify

- Record the structure in `mcbuilder:registry` like any other blueprint.
- It is a world structure, so `mc_structure_get` / `mc_structure_list` confirm
  it saved at the expected size, and `mc_structure_place` stamps it.
