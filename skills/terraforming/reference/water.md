# Water systems

Lakes, rivers, falls, wetlands, and frozen water. All the non-negotiable rules
apply — irregular outlines, the 7-block rule on every bank and shore.

## Water mechanics in Bedrock

- Water **flows** when placed. For a large still body, either place source
  blocks along the **top edge** of a sealed basin and let them propagate, or
  fill the whole volume with source blocks.
- The infinite-source rule works: a `+` of four source blocks regenerates a
  source in any adjacent flowing tile.
- To embed water inside a saved module, capture it with the blocks
  **waterlogged** where the structure tools support it.
- Water cannot exist in the Nether dimension — it evaporates instantly.

## Lakes

- Irregular outline, never rectangular or circular. Any lake wider than ~20
  blocks needs **at least 3 lobes**.
- **Depth gradient:** 1 block at the shore → 4–8 at the center, as a soft bowl
  curve, never a flat floor.
- **Bed:** clay + gravel + sand patches (~60/30/10), with occasional dirt and
  a few seagrass blocks.
- **Shoreline:** alternate sand patches (2–6 wide) with grass-and-coarse-dirt
  patches (3–8) and the occasional gravel beach.

## Rivers

- **Meanders:** the centerline turns at least 15° before any straight segment
  reaches 7 blocks. Width 3–8 for a small river, 8–20 for a major one.
- **Bed:** replace plain clay/gravel with brown dirt, granite, and seagrass;
  texture the banks with coarse dirt and grass paths. (BlueNerd technique.)
- **Oxbow lakes:** a former meander cut off by erosion — a disconnected curved
  water body 4–10 blocks from the active channel.
- **Tributaries:** join the main channel at an acute 30–60° angle, narrower
  than the main river.
- **Headwaters:** a spring emerging from a hillside as a 1×1 source, widening
  over 10–30 blocks.
- **Deltas:** at the mouth, split into 3–6 branches across a triangular fan
  30–80 blocks wide.

## Waterfalls, cascades, rapids

- A single source makes a thin fall; a wide fall needs a line of sources along
  the top edge.
- **Cascades:** 2–5 stepped falls with mossy cobblestone ledges and spillways
  1–2 blocks wide.
- **Rapids:** a river bed broken by cobblestone + gravel humps that breach the
  surface; pointed dripstone above adds a spray feel.

## Wetlands, swamps, bogs

- **Mangrove swamp:** mud, mangrove_roots, muddy_mangrove_roots, mangrove
  logs, lily pads; dominant water depth 1–2 blocks; occasional grass/dirt
  disks.
- **Wet meadow:** grass + tall_grass + sweet_berry_bush with 2×2 water
  puddles.
- **Bog:** podzol + coarse_dirt + dead_bush + brown_mushroom with small water
  pockets — a dark, peaty look.

## Frozen features

- **Ice lakes:** a top layer of ice or packed_ice over normal water, with a
  1–2 block snow margin.
- **Glaciers:** a blue_ice core, packed_ice body, snow_block surface, and
  occasional crevasses (3–6 block slits filled with water or air).
- **Icebergs:** asymmetric masses of blue_ice + packed_ice + snow_block. Roughly
  **7/8 of an iceberg sits below the waterline** — model the submerged volume
  as ~7× the visible part. Pick the ratio once per build and stay consistent.
