# Formation primitive library

Reusable building blocks for natural wonders. Each primitive has a typical
size range, a **build method** (`carve` = build solid then cut; `build-up` =
additive — see `sequencing.md`), and an approach. Every primitive lives within
the limits in `terraforming/reference/command-budget.md`.

Naming: save primitive instances as structure templates `mcb:<project>_<primitive>_<index>` (colon namespace — the underscore-only form is rejected by the structure tools).

## V1 primitives — implement these first

These 18 cover the top ~30 most-requested wonders.

### canyon-strata-stack — *build-up*
Vertical sequence of horizontal sedimentary bands; the substrate everything
else is carved from. 16–60 tall × any horizontal extent. Loop bands top to
bottom, one tiled `block_fill_region` per band. **≥5 distinct bands of 5–7
blocks each** — fewer reads as a solid cliff. Substrate for canyons, mesas,
hoodoos.

### slot-canyon-segment — *carve*
Narrow sinuous slot cut into a sandstone mass. 30–60 deep × 2–6 wide × any
length. Carve a serpentine path — offset the cut 1 block horizontally per Y
layer so walls curve. Add 2–3 vertical skylight shafts.

### hoodoo-spire — *build-up*
Banded vertical spire with a resistant cap. 8–25 tall × 2–4 base tapering to
1–2 top, 3×3 cap. Banded terracotta shaft, sandstone cap. Cluster 20–60 in a
bowl amphitheatre; do **not** integrity-weather — hoodoos read as ordered.

### mesa-butte — *carve*
Flat-topped tabular landform with a talus skirt. 12–35 tall × 20–60 wide.
Build a strata stack, carve the outer shell for steep cliffs (~1 block setback
per 4–6 Y), add an integrity-weathered talus pile at the base.

### sea-stack — *build-up*
Isolated rock column standing in water. 8–35 tall × 2–8 wide. Tapered cylinder
rising from the seafloor through the surface; integrity-weather the outer
shell. Palettes: sandstone, calcite chalk, or basalt.

### sea-arch — *carve*
Rock arch with ocean passing through. Span 8–20 × clearance 6–15. A sea-stack
mass with an arch carved at sea level.

### karst-tower — *build-up*
Steep limestone tower, vertical to overhanging sides. 25–60 tall × 8–20 wide,
height:width up to 6:1. **Signature: a 1–2 block waterline notch carved fully
around the base** (the Halong mushroom-foot look). Slightly wider near the top
than the middle to suggest overhang; moss, grass, and 2–4 jungle saplings on
top; vines from the rim.

### columnar-basalt-field — *build-up*
Tiled hexagonal basalt columns. Hexagonal lattice on a 2-block pitch (every
other row offset 1 in x); each column an `1×N×1` fill, heights varied **1–12**
so the field reads as a sloped ramp into the sea. Flat for Giant's Causeway,
vertical for Devils Tower, radial fan for Devils Postpile.

### inselberg — *build-up*
Isolated rounded rock rising from a flat plain (Uluru, Sugarloaf). Stacked
ellipsoidal fills into a rounded mound; carve vertical ribbing every 3–5 blocks
of circumference; small base alcoves. Honour the wonder's aspect ratio.

### cinder-cone / stratovolcano — *build-up*
Conical volcano. Base ≥40 × height ≥25. Radial cone with a parametric profile;
bias one slope 15–25% wider for asymmetry — **except Mt. Fuji, which must be
symmetric**. Small caldera 3–5 wide × 2 deep at the summit.

### caldera — *carve*
Collapsed circular basin holding a lake. 40–80 wide × 15–30 deep. Circular
air-fill excavation, then water (deep blue), `light_blue_concrete` floor
(turquoise crater lake), or lava (active).

### travertine-terrace — *build-up*
Stepped cascading mineral pools. 4–8 steps × pool radius 4–12 × step height
1–2. Concentric stepped rings of decreasing radius, each 1–2 Y above the last;
pour-points at low edges; pointed dripstone under the lower lips. Pool floors
coloured by the block beneath the water.

### iceberg — *build-up*
Asymmetric ice mass, **~7:1 below-water to above-water** (allow 5:1–9:1).
6–25 above × 42–175 below. Prolate asymmetric shape, more blue ice toward the
bottom; ~30% chance of a snow cap.

### salt-flat — *build-up*
Perfectly flat reflective white plain. `white_concrete` 95% / `light_gray_concrete`
5% for cracks, as a 1-block layer. Optional 1-deep water sheet for a mirror.
Flatness *is* the signature — no jitter.

### sand-dune — *build-up*
Wind-shaped dune with a proper slipface: gentle windward (~1:8), steep leeward
(~1:1.5). 4–20 tall × 8–40 wide. Loose sand over sandstone for stability.
Variants: transverse (long perpendicular ridge), barchan (crescent horns
downwind), star, longitudinal.

### chalk-cliff — *build-up*
White near-vertical sea cliff (Dover, Étretat). `calcite` 70% / `diorite` 20% /
`bone_block` 10%, flat grass top. Calcite is the block that sells it.

### horseshoe-falls-edge — *carve*
Semicircular waterfall curtain. Carve a U-shaped edge, line the lip with water
sources at 1-block spacing, and dig the plunge pool **≥3× the fall height** so
spray does not spread.

### curtain-waterfall — *carve*
Single wide, thin falls from a straight edge (Victoria, American Falls). A long
line of source blocks along the top edge; deep plunge pool below.

## V2 primitives — add after V1 is validated

Brief — same parameter discipline applies.

- **tepui** — *build-up*. High flat plateau, sheer cliffs ≥50, waterfalls off
  the lip. Near-zero taper.
- **slickrock-undulation** — *build-up*. Smooth wavy banded sandstone (The
  Wave); swirled, non-horizontal bands from layered sine heightmaps.
- **hot-spring-prismatic** — *build-up*. Concentric colour rings (blue → cyan →
  green → yellow → orange → red concrete) under shallow water.
- **geyser-cone** — *build-up*. Raised silica cone with a vent; optional
  particle burst loop.
- **mud-pot-field** — *build-up*. Bubbling clay cluster — `mud`, `packed_mud`,
  `brown_concrete`, `clay`.
- **cenote** — *carve*. Vertical limestone shaft, clear water at the bottom,
  vine drape at the rim.
- **glacier-tongue** — *build-up*. Descending blue ice with transverse
  crevasses and lateral moraines.
- **fjord-segment** — *carve*. Deep narrow water inlet, vertical walls ≥40,
  ribbon waterfalls.
- **lava-tube** — *carve*. Long curving cave with 2–3 ceiling skylights.
- **granite-dome** — *build-up*. Rounded smooth dome with sparse exfoliation
  cracks.
- **mushroom-rock / pedestal-rock** — *build-up*. Wide cap on a narrow base.
- **goblin-balanced-rock** — *build-up*. Precarious wide cap on a thin neck.
- **arch / natural-bridge** — *carve*. Single rock span, semicircular underside.
- **plunge-pool** — *carve*. Deep round pool at a fall base, ≥6 radius × ≥6 deep.
- **multi-tier-waterfall-ledge** — *carve*. Chained plunge pools with falls
  between, 6–12 Y apart.
- **devils-throat** — *carve*. Multiple falls converging into one U-chasm.
- **hanging-garden** — *build-up*. Vegetation drape along a cliff seep line.
- **painted-desert-banding / rainbow-mountain-striations** — bands following
  contour lines across a slope, not horizontal.
- **petrified-forest-patch** — fossil-log scatter (`bone_block` horizontal
  cylinders) on banded terracotta ground.
- **speleothem-column / cave-drapery** — pointed dripstone stalactites and
  stalagmites.
- **sequoia-tree / baobab-tree** — oversized *hero* tree primitives, built as
  deliberate one-offs and **never duplicated**. **cypress-knee-patch /
  mangrove-root-cluster** — specialty ground vegetation. For ordinary trees and
  any grove, **grow saplings — never place or repeat a tree** — see the
  `terraforming` skill's `reference/weathering.md`.

## Common mistakes

- Strata stacks with fewer than 4 bands, or bands under 2 blocks tall.
- Tapering a tepui or mesa cliff — they are near-vertical.
- Integrity-weathering a hoodoo field — Bryce reads as ordered, not eroded.
- Forgetting the karst-tower waterline notch.
- A symmetric volcano that is not Mt. Fuji.
