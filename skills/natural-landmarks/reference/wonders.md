# Named wonder recipes

Data, not code — each entry is signatures + minimum recognition footprint +
palette + primitive composition. Adding a wonder means adding a row here, not
writing new logic. Real-world dimensions vary by source; treat them as ±10%.

## Minimum recognition footprints

A wonder requested below its floor must be scaled up to the floor (or the user
explicitly overrides). Below the floor it reads as generic terrain.

| Wonder | Minimum Minecraft size | Key signature |
| ------ | ---------------------- | ------------- |
| Grand Canyon | 50–60 deep × 250+ long × 60 wide | ≥5 strata bands |
| Niagara | 25 tall × 80 horseshoe + 25×50 straight | horseshoe shape |
| Victoria Falls | 35 tall × 120 wide | curtain straightness + zigzag gorge below |
| Iguazu Devil's Throat | 30 × 30 × 60 U-chasm | U-shape, tier islands, jungle |
| Uluru | 30 tall × 80 long × 35 wide | wider-than-tall, ~3:1 |
| Devils Tower | 60 tall × 30 base | vertical column striations |
| Giant's Causeway | ≥200 columns in a 30×30 grid | hex tessellation visible |
| Mt. Fuji | 50 tall × 100 base | radial symmetry, snow cap |
| Halong Bay | 12–25 karst towers, 25–60 tall | height:width up to 6:1 + waterline notch |
| Bryce Canyon | 50 hoodoos, 12–25 tall, in a 100×100 bowl | dense cluster + bands |
| Pamukkale | 4–6 steps, radius 8–12 | concentric pool tiers |
| Twelve Apostles | 4–8 stacks, ~25 tall | a line of separate stacks |
| Salar de Uyuni | ≥80 × 80 white plain | perfect flatness |

## Composition recipes

**Grand Canyon** — *Signatures:* 5–7 banded strata; meandering river;
perpendicular side canyons; vermillion caprock. *Palette:* `colorado-plateau`.
`canyon-strata-stack` (7 bands) + meandering river-canyon carve + `side-canyon`
×4–8 + vermillion-cliff rim + 2 isolated `mesa-butte` inside + sparse dead-bush
and dark oak on north rims.

**Zion** — *Signatures:* sheer Navajo cliffs ≥80; narrow river slot; hanging
gardens at seep lines; knife-edge ridge. *Palette:* `navajo-sandstone`.
`canyon-strata-stack` + `slot-canyon-segment` (the Narrows) + knife-edge ridge
+ `hanging-garden` ×several.

**Bryce Canyon** — *Signatures:* dense amphitheatre of hoodoo spires; orange/
pink/white bands; resistant caps. *Palette:* `bryce-terracotta`. Bowl
amphitheatre carved as substrate + `hoodoo-spire` ×50–80 + flat lookout rim.
Do **not** integrity-weather.

**Antelope Canyon** — *Signatures:* extremely narrow (2–4 wide) sinuous slot;
smooth wave-curved walls; vertical light shafts. *Palette:* `navajo-sandstone`.
`slot-canyon-segment` (3–4 wide, 40 tall, 80 long) + 2–3 skylight shafts.

**Niagara** — *Signatures:* horseshoe curtain; straight curtain; plunge pool;
downstream gorge. *Palette:* limestone (`polished_diorite` / `smooth_stone`).
escarpment edge + `horseshoe-falls-edge` + `curtain-waterfall` separated by
Goat Island + `plunge-pool` + carved downstream gorge.

**Victoria Falls** — *Signatures:* long straight basalt curtain; narrow zigzag
Batoka Gorge. *Palette:* `basalt-volcanic`. `curtain-waterfall` (120 wide × 35
tall) + zigzag gorge turning 90° + mist particles + jungle rim.

**Iguazu** — *Signatures:* semicircular fall arc; U-shaped Devil's Throat;
stepped tier islands; dense jungle. *Palette:* `basalt-volcanic` + jungle.
`multi-tier-waterfall-ledge` curved into a 60-radius arc + 15–20 micro-island
carve-cuts + `devils-throat` U-chasm at centre (30 × 25 × 60).

**Uluru** — *Signatures:* single isolated inselberg; wider than tall (~3:1);
vertical ribbing; flat red plain. *Palette:* `uluru-red`. `inselberg` (80–120
long × 25–35 tall, ribbed) + flat red-sand plain ≥80 each side + 3–5
Kata-Tjuta domes at distance + sparse dead-bush + a small base alcove.

**Devils Tower** — *Signatures:* fluted vertical column; tapering hexagonal
prism; talus skirt. *Palette:* `basalt-volcanic`. `columnar-basalt-field` used
vertically as a monolith (60 tall × 30 base, top ~60% of base) + talus skirt +
a small river and pine forest around the base.

**Giant's Causeway** — *Signatures:* ~hexagonal interlocking columns; varied
heights ramping into the sea. *Palette:* `basalt-volcanic`. `columnar-basalt-field`
flat, ≥200 columns, heights varied 1–12.

**Mt. Fuji** — *Signatures:* near-perfect radial symmetry (the rare symmetry
exception); fixed-Y snow cap; small caldera; cherry blossom at the wide base.
*Palette:* `basalt-volcanic` body + snow cap. `cinder-cone` built **symmetric**
+ `powder_snow` / `snow_block` top 25% + cherry trees at the base.

**Halong Bay** — *Signatures:* vertical limestone towers in water; waterline
notch at every base; height:width up to 6:1. *Palette:* `karst-limestone`.
`karst-archipelago` of 12–25 `karst-tower` + deep ocean + one larger conjoined
fengcong cluster + occasional sea-cave entrance.

**Pamukkale** — *Signatures:* concentric white travertine pool tiers.
*Palette:* `travertine-white`. `travertine-terrace` (6–8 tiers) + a thermal
spring source at the top + a gentle stone/calcite slope below.

**Yellowstone** — a composition of compositions: `caldera` + `travertine-terrace`
(Mammoth) + `geyser-cone` ×5–10 + `hot-spring-prismatic` (Grand Prismatic) +
`mud-pot-field` + a yellow-rhyolite `canyon-strata-stack` + a lower-falls
curtain.

**Crater Lake** — *Signatures:* near-circular caldera; deep blue lake; Wizard
Island cinder cone in the lake; sheer walls. *Palette:* stone/andesite walls,
`light_blue_concrete` or prismarine floor. `caldera` (40–80 wide) + a small
`cinder-cone` island + spruce rim forest.

**Salar de Uyuni** — *Signatures:* perfect flat reflective white plain.
*Palette:* `salt-flat`. `salt-flat` ≥80×80 + a rocky cactus island + an
optional 1-deep mirror water layer.

**Twelve Apostles** — *Signatures:* a line of isolated limestone sea stacks.
*Palette:* `chalk-cliff`-tinted sandstone. `sea-stack` ×4–8, 20–50 tall, off a
chalk/sandstone coast.

**White Cliffs of Dover** — *Signatures:* near-vertical white chalk into the
sea. *Palette:* `chalk-cliff`. `chalk-cliff` with flat grass top.

**Étretat** — *Signatures:* chalk arch + needle sea stack. *Palette:*
`chalk-cliff`. `chalk-cliff` + `sea-arch` + `sea-stack` (L'Aiguille needle).

**The Wave (Arizona)** — *Signatures:* smooth undulating *swirled* (not
horizontal) sandstone bands. *Palette:* `navajo-sandstone`.
`slickrock-undulation`.

**Perito Moreno glacier** — *Signatures:* blue-ice tongue; transverse crevasse
field; lateral moraines; vertical calving face. *Palette:* `glacier`.
`glacier-tongue` (≥80 long) + moraine strips + a ≥15-tall calving face.
