# Generating a structure from a block grid

Use this path for any element easier to describe with a formula or a script
than to lay by hand: pixel-art murals, voxelized models, anything
image-mapped or parametric. There is **no `mc_structure_create_from_blocks`
equivalent on Java Edition** — instead, use one of the two methods below.

Both produce a named structure template that `structure_load_to_world` can
stamp anywhere, `structure_get_info` / `structure_list` can inspect, and
`structure_delete` can clean up.

---

## Method 1 — Scratch-and-capture (default)

Build the computed grid in-world in a scratch area, then save it as a
structure. Straightforward; works for any grid size within the tool limits.

### Steps

1. **Compute the per-cell block list** in your chosen order (XYZ or ZYX,
   it doesn't matter as long as you iterate consistently).
2. **Place the grid** in the scratch area using `block_fill_region` for
   solid runs and `block_set_state` for individual cells or cells with
   blockstate properties. Keep each `block_fill_region` within the 32,768-block
   volume limit; tile larger grids.
3. **Capture** the bounding box with `structure_save_from_world`:
   - `name`: `mcb:<project>_<element>` (colon namespace required).
   - `dimension`: the dimension you built the scratch in.
   - `box`: `{from, to}` — the exact corners of the placed grid.
4. **Clear the scratch area** with a `block_fill_region` of `minecraft:air`.
5. **Verify** with `structure_get_info` that the saved size matches the
   expected dimensions.

### Example — 16×1×16 checkerboard floor

```python
# Compute cell list
sx, sy, sz = 16, 1, 16
cells = []
for x in range(sx):
    for z in range(sz):
        # alternate minecraft:white_concrete / minecraft:black_concrete
        cells.append("minecraft:white_concrete" if (x + z) % 2 == 0
                      else "minecraft:black_concrete")

# Group into runs for fill calls
# (each run of the same block → one block_fill_region along z)
# Place at scratch origin e.g. 0, 200, 0
origin_x, origin_y, origin_z = 0, 200, 0
for x in range(sx):
    for z in range(sz):
        block = "minecraft:white_concrete" if (x + z) % 2 == 0 \
                else "minecraft:black_concrete"
        # block_set_state(id=block, x=origin_x+x, y=origin_y, z=origin_z+z)
```

After placing all cells, call:
```
structure_save_from_world(
  name="mcb:demo_floor",
  dimension="minecraft:overworld",
  box={from: {x: 0, y: 200, z: 0}, to: {x: 15, y: 200, z: 15}})
```

Then clear: `block_fill_region(dimension=..., box={from:..., to:...}, block={id: "minecraft:air"})`.

For large grids, use `block_fill_region` for homogeneous runs (same block
along a row) to stay within the `block_set_state` per-step budget. A 64×64
checkerboard can be placed as 64 alternating fill calls (one per row),
not 4,096 individual `block_set_state` calls.

---

## Method 2 — Direct NBT write

Generate a structure `.nbt` file programmatically and write it with
`structure_file_write` (content is base64-encoded NBT). Use this path only
when a script already produces NBT output — it is heavier than
scratch-and-capture and requires correct NBT encoding.

Java structure `.nbt` files follow the vanilla structure template format:
- Top-level compound with keys `size` (list of 3 ints), `entities` (list),
  `blocks` (list of `{pos:[x,y,z], state:int}` compounds), `palette` (list
  of `{Name:string, Properties:{…}}` compounds), and `DataVersion` (int).
- `DataVersion` must match the running server's data version.

After writing, call `structure_list` to confirm the template is visible and
`structure_get_info` to verify its dimensions.

---

## Register and verify (both methods)

- Record the structure in `mcbuilder:registry` via `data_storage_set`
  (namespace `mcbuilder`, path `registry`) like any other blueprint.
- Confirm with `structure_get_info` / `structure_list` that it saved at the
  expected size.
- Place it with `structure_load_to_world` to verify it renders correctly
  before committing it to the plan.
