# Uploading a generated structure

`mc_structure_upload` turns a **block grid you compute** into a placeable
structure — without building it in the world block by block first. Use it for
any element that is easier to describe with a formula or a script than to lay
by hand: pixel-art murals, voxelized models, anything image-mapped or
parametric.

It is the third blueprint method. The other two — capture-from-world and the
`mc_structure_set_block` loop — stay the right choice for everything a small
script cannot describe.

## How it works

1. You produce a **structure definition** — a JSON object: a palette of
   distinct block states, plus a flat array of palette indices, one per cell.
2. `mc_structure_upload` encodes it into a `.mcstructure` file in the behavior
   pack's reserved `mcp/` namespace.
3. It reloads the world so Bedrock indexes the new file.
4. The structure is then placeable as **`mcp:<name>`** — by `mc_structure_place`
   or a `place-structure` step in `plan.toon`.

## The definition format

```json
{
  "size": { "x": 16, "y": 1, "z": 16 },
  "palette": [
    { "name": "minecraft:white_concrete" },
    { "name": "minecraft:oak_log", "states": { "pillar_axis": "y" } }
  ],
  "blocks": [0, 1, -1, 0, ...],
  "waterlog": [-1, -1, ...],
  "block_version": 18153472
}
```

- **`size`** — the X/Y/Z extents in blocks. Volume must stay within Bedrock's
  64 × 384 × 64 structure cap; split anything larger into tiles.
- **`palette`** — the distinct block states, indexed from 0. Each entry is a
  block `name` and optional `states` (e.g. `{ "pillar_axis": "y" }`).
- **`blocks`** — one palette index per cell, length `size.x * size.y * size.z`,
  in **ZYX order**: the index for cell `(x, y, z)` is

  ```
  z + size.z * (y + size.y * x)
  ```

  An entry of **`-1`** is a structure void — the block already in the world is
  left untouched when the structure is placed. Use it for empty space and for
  the transparent regions of a mural.
- **`waterlog`** *(optional)* — a second layer of the same length, for
  waterlogged blocks; omit it unless you need water.
- **`block_version`** *(optional)* — leave it unset. The default targets a
  current Minecraft version. Only set it if uploaded blocks render as their
  default state on an older server.

## Generating the definition

Do **not** write a large `blocks` array by hand. Generate it with a short
script and hand the file to the tool:

1. Write a Python or Node script that builds the palette and the `blocks`
   array and dumps the JSON to
   `.minecraft-builder/<project>/structures/<name>.json`.
2. Call `mc_structure_upload` with `definition_path` set to the **absolute**
   path of that file. (The MCP server reads it from disk — keep the data out
   of the conversation.)

For a small structure — a few hundred cells — you may instead pass the
`definition` object inline.

Example: a 16 × 1 × 16 checkerboard floor.

```python
import json, pathlib
sx, sy, sz = 16, 1, 16
palette = [{"name": "minecraft:white_concrete"}, {"name": "minecraft:black_concrete"}]
blocks = [0] * (sx * sy * sz)
for x in range(sx):
    for z in range(sz):
        i = z + sz * (0 + sy * x)          # ZYX index, y = 0
        blocks[i] = (x + z) % 2
path = pathlib.Path(".minecraft-builder/demo/structures/floor.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps({"size": {"x": sx, "y": sy, "z": sz},
                            "palette": palette, "blocks": blocks}))
```

Then: `mc_structure_upload` with `name: "demo_floor"`, `definition_path` set to
the absolute path of `floor.json`.

## The world reload

`mc_structure_upload` reloads the world automatically, but **`/reload all`
requires at least one player online** — it works by making players rejoin.

- The result reports `reload_performed` and `reload_required`. If
  `reload_required` is `true`, the file is written but not yet placeable:
  tell the user to join the world (or rejoin), then run `mc_server_reload_world`
  — or, with nobody able to join, restart the dedicated server.
- The reload briefly disconnects and rejoins every online player. That is
  expected; the bridge reconnects on its own.

## Naming and the registry

- The placed id is always **`mcp:<name>`**. Name uploads
  `<project>_<element>` so they parallel the `mcb_<project>_<element>`
  convention — e.g. `name: "lakeside-village_mural"` → `mcp:lakeside-village_mural`.
- Record the upload in `mcbuilder:registry` exactly like any other blueprint,
  with the `mcp:<name>` id in the `structure` column.

## Verifying

Behavior-pack structures do not appear in `mc_structure_list` (it lists only
world and in-memory structures). To confirm an upload: after a successful
reload, place it with `mc_structure_place` into a staging area and inspect it,
or proceed to the `place-structure` step and let the `inspector` check the
result.
