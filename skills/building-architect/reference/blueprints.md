# Blueprint rendering, scale, and validation

## Scale and recognition

A replica below its **minimum-recognition** size reads as generic — too small
to carry its signatures. Recognition depends on **signature features at
credible proportions**, not raw size:

- A cathedral needs enough length for a real bay rhythm, towers tall relative
  to the nave, and room for a legible rose window.
- A skyscraper needs its setback or silhouette profile to read.
- A castle needs its towers, curtain wall, and keep in true proportion.

If the user asks for a size below recognition, scale up to the threshold or
flag it. If 1:1 exceeds the Y range (-64 to 320), scale down and state the
ratio.

## Rendering modes

Produce these in `.minecraft-builder/<project>/` and show the user before
resolving a plan:

- **ASCII floor plan** (`floorplan.txt`) — one top-down grid per floor.
- **Building table** (`building.md`) — per room/section: name, dimensions,
  floor/wall/ceiling blocks, hero items.
- **Mermaid adjacency** (`adjacency.mmd`) — room flow for multi-room buildings.
- **3-D ASCII cutaway** — a side elevation for towers and cathedrals, showing
  tiers and signature heights.

### ASCII floor plan — example

```
Floor 1 — Nave & aisles   (# wall  . floor  O column  * rose window  D door)
##########################
D....O....O....O....O....##
#........................#
#....O....O....O....O....##
##########################
```

### 3-D cutaway — example

```
       /\        spire
      ####        tower (×2, twin west towers)
      ####  ####
      *##*  *##*  rose window
      #-buttress-#
```

State the chosen scale and a fill-volume estimate on every rendering.

## Iteration

Render, show, take feedback, revise, re-render — loop until the user
explicitly approves. Only then resolve to `plan.toon`.

## Validation checklist

Before handing off, and again for the `philosopher` afterwards, check the
build against these failure modes:

- **Missing a signature feature** — reject; the build is not the building.
- **Wrong material or colour** — the palette in `replicas.md` / `styles.md` is
  authoritative (a white building must not come out grey).
- **Wrong silhouette or proportion** — a too-short tower, a dome where it
  should be a gable.
- **Wrong symmetry** — honour each building's rule (Taj Mahal symmetric,
  Hogwarts asymmetric, Sydney Opera House not).
- **Period mismatch** — no glass curtain wall on a medieval castle, no
  anachronistic interior.
- **Stained glass with no backing light** — dull and dead; add a light block
  behind it.
- **No interior light coverage** — spawnable dark cells.
- **Floating structure** — buttresses with no abutment, unsupported mass.
- **Exceeds the Y range, or a fill over 32,768, or a structure over
  64×384×64** — scale down, pre-tile, or split.
- **A furnished hero room invisible from outside** — add an opening or move it.

A failed signature or symmetry check is a correction to make, not a cosmetic
note — send the build back for a fix.
