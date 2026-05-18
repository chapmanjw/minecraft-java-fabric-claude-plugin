# Armor-stand detailing

Armor stands add **fine detail** a block grid cannot — held items, posed
accent figures, floating decorative elements. They are placed as a **late
decoration phase**, after the monument's blockwork is built.

## Bedrock armor-stand facts

- Bedrock armor stands **have arms** by default and can hold items.
- They cycle through **13 built-in poses** (not free NBT rotation as on Java):
  Default, Solemn, Athletic, Brandish, Honor, Entertain, Salute, Riposte,
  Cancan A, Cancan B, Hero, Riding, Walking.
- A pose is set by cycling (interaction) or driven by a redstone signal —
  e.g. a powered armor stand holds the Honor pose. Rotations beyond the 13
  presets need behaviour-pack scripting and are out of scope here.
- An armor stand can wear armour in all four slots and hold an item; a mob
  head in the helmet slot is a common detailing trick.

## In the plan

- Spawn armor stands with the **`spawn` plan op** (`mc_entity_spawn`,
  `minecraft:armor_stand`) at the decoration phase.
- Equip and pose them with `run`-op commands.
- Tag them so they can be found and adjusted later.

## Detailing patterns

- **Held detail** — an armor stand holding a banner, a tool, a weapon, or an
  item frame supplies a crisp small element (a flagpole banner, a statue's
  staff or sword) at a scale the block grid cannot.
- **Accent figures** — a ring of posed stands around a monument: an honor
  guard (Salute / Honor), warriors (Brandish), figures in motion (Walking) —
  small human-scale figures that give a giant monument scale and context.
- **Equestrian accents** — the Riding pose for a mounted figure.
- **Floating elements** — an invisible, baseplate-less stand holds an item in
  mid-air (jewels on a treasure pile, a held orb, hovering runes).
- **Mob heads** — player or mob heads on stands or as standalone blocks add
  faces and character.

## Choosing the pose

Match the pose to the role: **Honor / Solemn** for memorial guards, **Salute**
for an honor guard, **Brandish / Hero** for warriors, **Riding** for cavalry,
**Walking / Athletic** for figures in motion, **Entertain / Cancan** for
lively or festival scenes.

## Rules

- Armor-stand decoration is the **last phase** — after all blockwork, so the
  stands are not disturbed by fills.
- Keep counts reasonable — armor stands are entities and a large crowd has a
  cost; use them for *accent*, not bulk.
- A monument's main form is always **blocks**; armor stands only finish it.
