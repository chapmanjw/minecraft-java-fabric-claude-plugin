# Building catalog

The standard village building types, by function. Reuse a small set of these
per village — build each as a template once, then stamp it (see the reuse model
in `SKILL.md`). Footprints are interior W×D; add wall thickness. Every building
a villager lives in needs one bed (2 air above the pillow) and, if it has a
profession, one workstation within 16h/4v.

## Residential

- **Small house** — 7×7, 1 bed. The village workhorse; carry 2–3 variants and
  reuse them heavily.
- **Medium house** — 9×9, 1–2 beds. A larger family home; spare beds here help
  reach the 20-bed iron-golem threshold and support breeding.
- **Large house** — 11×11, 2–3 beds, often two storeys.
- **Longhouse / bunkhouse** — a long room of several beds; an efficient way to
  add bed count.

## Profession buildings & workstations

One villager per workstation. Bedrock workstation blocks:

| Profession | Workstation | Building note |
| ---------- | ----------- | ------------- |
| Farmer | `composter` | Cottage beside a crop plot. |
| Librarian | `lectern` | Library — bookshelves (decorative). |
| Toolsmith | `smithing_table` | Forge with a furnace and chimney. |
| Weaponsmith | `grindstone` | Forge; often shares a building with the toolsmith. |
| Armorer | `blast_furnace` | Smith's house. |
| Cleric | `brewing_stand` | Temple / shrine. |
| Cartographer | `cartography_table` | Map house. |
| Fisherman | `barrel` | Cottage near water; pairs with a dock. |
| Fletcher | `fletching_table` | Bowyer's house. |
| Shepherd | `loom` | House near the animal pens. |
| Leatherworker | `cauldron` | Tannery. |
| Mason | `stonecutter` | Mason's house. |
| Butcher | `smoker` | Butcher shop near the animal pens. |

A villager with no workstation stays unemployed (use spares for breeding).

## Civic

- **Meeting hall / plaza** — the heart of the village; **houses the bell**.
  Hay-bale benches, open and lit.
- **Well** — the classic village centerpiece; decorative, 5×5 with a cobble
  curb.
- **Bell** — on a fence post or in the meeting hall, within 48 blocks of every
  bed pillow.
- **Watchtower** — 10–15 blocks tall with a lookout top; doubles as raid
  defense.

## Agriculture

- **Wheat farm** — the vanilla 9×9 plot with a central water source, four
  rows. Beetroot, carrot, and potato farms use the same layout.
- **Large farm** — 13×13+, mixed crops, worked by a second farmer.
- **Pumpkin / melon patch**, **sugar-cane row** (lakeside), **berry bushes**
  (taiga).
- **Composter loop** — a farmer throws surplus crops into a composter; a
  hopper-fed composter→chest loop yields bone meal. Keep the composter
  claimable as the farmer's job site.
- **Animal pens** — fenced enclosures, 7×7 minimum, lit, with water and feed:
  cows, pigs, sheep, chickens. Place near the shepherd and butcher.

## Defense

- **Walls** — cobblestone, stone, or a wood palisade; 3–5 blocks tall, with a
  walkway on tall walls. **Never fully seal the village** — leave spawnable
  ground outside and 1-block gaps every 10–15 blocks, or raiders spawn inside
  (see `mechanics.md`).
- **Gates** — a wooden double-door by default; an open arch reads fine too.
- **Watchtowers and lookout posts** — at corners and the gate.
- **Iron-golem pad** — keep the 17×13×17 volume around the bell open with a
  solid spawn surface.
- **Lighting** — light the whole village interior and perimeter so hostile
  mobs cannot spawn among the buildings.

## Special (optional)

Inn / tavern, market stalls, guard post, chapel, manor — themed extras for
character. They follow the same rules: a bed and workstation if a villager
uses them, otherwise purely decorative.
