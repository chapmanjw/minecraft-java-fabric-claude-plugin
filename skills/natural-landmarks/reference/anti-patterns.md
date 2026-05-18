# Anti-patterns — the signature checklist

A landmark fails when a signature feature is missing or a proportion is wrong —
not when it is "not pretty enough". This is the checklist the `philosopher`
reviews a finished landmark against. Each item is a yes/no gate.

## Strata and colour

- **Too few strata bands.** Real badlands and canyons show 5–10 distinguishable
  layers. A 2-band Grand Canyon reads as a generic cliff. → ≥5 bands, each 5–7
  blocks.
- **Wrong colour sequence.** The Grand Canyon runs red/orange on top to grey/
  dark at the bottom. Reversing the order reads as alien. → Match the palette
  preset's stated top-to-bottom order.

## Silhouette and proportion

- **Symmetric where it should be asymmetric (and vice versa).** Every volcano
  is asymmetric — bias one slope 15–25% wider — **except Mt. Fuji**, which must
  be symmetric. → Check the wonder's entry.
- **Wrong aspect ratio.** Uluru is ~3:1 wider than tall; built taller than wide
  it reads as a mesa. Devils Tower is tall and narrow. → Honour the ratio in
  `wonders.md`.
- **Wrong silhouette.** Devils Tower without vertical column striations is a
  generic plug. A tepui or mesa with tapered (not vertical) cliffs is just a
  hill.

## Signature features

- **Missing the key feature.** Niagara without the horseshoe is just a curtain.
  Iguazu without the Devil's Throat is a stepped weir. A karst tower without
  the waterline notch is just a pillar. → Every signature identified in the
  composer's step 1 must be present and legible.

## Scale

- **Below the recognition floor.** Devils Tower at 20 tall is a plinth; a Grand
  Canyon at 30 long is a ditch. → Enforce the minimum footprint from
  `wonders.md`.

## Surface and material

- **Uniform block faces.** A flat 30-block cliff with no Y-variation reads as a
  wall. → Apply at least a light surface-chipping integrity pass (≥95).
- **Wrong water colour.** Crater Lake is deep blue, Ijen turquoise, Havasu
  blue-green — the colour is the block *under* the water, never the water
  itself. → Set the floor block, not the water.
- **Concrete-powder where stability matters.** White Sands dunes need powder
  (gravity); Salar de Uyuni needs solid concrete. Mixing them collapses the
  build on chunk reload.
- **Vegetation grown over bare rock.** Grass creeping over a rock landmark
  breaks it. → `coarse_dirt` / `rooted_dirt` substrate near rock; suppress
  spread during construction.
- **Wrong vegetation context.** Match plants to the real biome — cactus only in
  desert, spruce for alpine/pine, jungle growth on karst tops.

## How the philosopher uses this

For any landmark build, walk this list against the finished result and the 2–4
signature features the composer recorded. Report each as pass/fail with
coordinates. A failed signature gate sends the build back to `natural-landmarks`
for a corrective primitive — it is not a cosmetic note.
