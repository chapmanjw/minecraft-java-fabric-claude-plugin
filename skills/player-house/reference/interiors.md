# Interiors — storage, furniture, lighting, decor

A base is only finished when its interiors work. This is where a build stops
reading as an empty shell.

## Storage

- **Categorize by use, not by material.** Combat / farming / building /
  redstone / food / misc — a use-based scheme survives new items entering the
  game; a material-based one breaks the moment you mine something new.
- **Forms:** a wall of barrels (compact, top-access), stacked double chests
  (classic), or shulker-box stations (mobile loadouts). Label every container
  with an item frame holding a sample.
- **Shulker colour coding** — the 16 dye colours map cleanly to 16 categories.
- **Universal ender-chest loadout** — keep a portable kit in the 27-slot
  ender chest: a tool set, food, a totem, ender pearls, building blocks, a
  water bucket, a golden apple, beds, a crafting table, torches. Mirrors
  across every room with an ender chest.
- **Hidden storage** — piston doors, painting reveals, pressure-plate floor
  caches — for valuables.
- Put a quick-access tool/food chest within 2 blocks of every external door.

## Furniture (vanilla block tricks)

- **Chairs** — stairs with a sign, trapdoor, or item frame as the back. Item
  frames pair tightly; signs force a gap.
- **Tables** — a fence post under a carpet, pressure plate, or trapdoor; or a
  slab on stair bases for a longer table.
- **Sofas** — a run of stairs with corner stairs as armrests.
- **Beds** — single; doubled for co-op; a four-poster with fence posts and a
  banner canopy for a master bedroom.
- **Counters / desks** — slabs, trapdoors, and stairs; a lectern as a desk.
- Decorate with paintings, item frames, banners, flower pots, candles (1–4
  per block for variable light), lanterns, chains, and bells.

## Lighting

- **No spawnable dark cell** in any finished room — this is a hard rule, not a
  preference.
- **Hidden light** keeps a clean look: glowstone or a sea lantern under a
  carpet or a top slab, a lantern sunk into a wall behind iron bars.
- Light *behind* translucent blocks for effect — glowstone behind stained
  glass, a sea lantern beneath blue ice.
- Outdoors: lanterns on a fence-and-chain post; soul lanterns for a cold blue
  tone; keep paths and the perimeter lit so mobs do not spawn against the base.

## Decor & finish

- **Roofs** — never a flat slab. Pitch with stairs (1:1 or 1:2), add gables,
  hips, dormers; double-stair the roof for visible thickness.
- **Wall variation** — mix block faces (stone / andesite / diorite / cobble /
  brick; oak / stripped / planks / log). A flat one-block wall is the loudest
  amateur tell.
- **Trim courses** — a contrasting band at floor lines and the roofline.
- **Windows** — vary them: single panes, full-wall glass, leaded (iron bars
  over panes), stained-glass accents.
- **Door surrounds** — a stair-and-slab frame, a carpet mat, a porch overhang.
- **Chimneys** — a campfire (on a hay bale for taller smoke) vented up a flue.
- **Texture, don't tile** — small irregular variation everywhere reads as
  craftsmanship; perfect repetition reads as a template.
- **Grounds and gardens** — for any trees and bushes around the base, **grow
  them from saplings; never place or duplicate a tree.** Plant
  biome-appropriate saplings with spacing and light, then force growth with
  bone meal (`player_give_item` / `itemstack_drop_at` + use), or via
  `command_execute` with `/place feature minecraft:<tree_type>`, or place a
  sapling with `block_set_state` and apply bone meal via a command. Prefer the
  sapling + bone-meal path for organic, varied results. Mix flower types and
  planters; keep paths and bushes irregular (see also the `terraforming`
  skill's `reference/weathering.md`).

---

## Java-exclusive: NBT detailing for a home interior

### Labeled storage with signs (capability A)

Place a `*_sign` beside or above each chest or barrel, then write a label
with `block_entity_set_nbt`:

```
block_entity_set_nbt(pos, nbt='{front_text:{messages:[
  "{\"text\":\"FOOD\",\"color\":\"green\",\"bold\":true}",
  "{\"text\":\"seeds / crops / cooked\"}", "\"\"", "\"\""],
  has_glowing_text:0b}, is_waxed:1b}')
```

`is_waxed:1b` prevents accidental edits. Four lines per face; `back_text`
follows the same shape for double-sided standing signs. Verify with
`block_entity_get_nbt` after merging.

### Lecterns as readable displays (capability A)

A lectern in a study or library can hold a written book pre-loaded via NBT:

```
block_entity_set_nbt(pos, nbt='{Book:{id:"minecraft:written_book",count:1,
  components:{"minecraft:written_book_content":{title:"House Rules",
  author:"Owner",pages:["\"Welcome home.\""]}},Page:0}')
```

### Decorated pots as ornaments (capability A)

```
block_entity_set_nbt(pos, nbt='{sherds:["minecraft:brick",
  "minecraft:angler_pottery_sherd","minecraft:brick",
  "minecraft:arms_up_pottery_sherd"]}')
```

Place in entrance alcoves, on fireplaces, or as garden ornaments. Rotate the
sherd IDs to match the home's style.

### Player-head decor (capability A)

`minecraft:player_head` blocks can be given a named profile for a
recognizable skin, or a custom base64 texture for fully bespoke ornament
(a carved knob, a trophy head, a unique nameplate on a door):

```
block_entity_set_nbt(pos, nbt='{profile:"Notch"}')
```

### Named and enchanted gear in storage (capability B)

`inventory_set_slot` accepts `components` SNBT to name, enchant, or add lore
to any item placed into a chest, barrel, or display case:

```
inventory_set_slot(container_pos, slot=0, item={
  id:"minecraft:diamond_pickaxe", count:1,
  components:'{"minecraft:custom_name":"{\"text\":\"Vein Seeker\",
    \"italic\":false,\"color\":\"gold\"}",
    "minecraft:enchantments":{"minecraft:fortune":3,
      "minecraft:efficiency":5,"minecraft:unbreaking":3}}'})
```

**Version note:** the `minecraft:enchantments` component shape changed between
1.20.5 and 1.21. Verify the exact SNBT with a round-trip (`itemstack_describe`
or give-then-read) on the running version (`server_get_status`).

Use this for a "hero kit" chest near the front door, a trophy sword above the
fireplace, or a named heirloom in a display case.
