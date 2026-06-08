# The Build Workflow Spine

The canonical phase order every build runs — **no exceptions, no trivial path**. Depth scales with
the build; the gates never drop. The `minecraft-builder` agent always routes to one Tier-2
orchestrator (`build-*`), which executes this spine, invoking Tier-3 leaf skills and threading the
shared coherence context (see `coherence.md`) between them.

```
classify -> SELECT ORCHESTRATOR (always)
  1  SURVEY        survey-site        read terrain/biomes/structures/datum
  2  RESEARCH      survey-research    real/named refs (skip for pure-imaginary)
  3  PLAN          exec-plan          requirements -> plan.toon (absolute, phased)
  4  DESIGN/SHAPE  domain leaves      design-*/system-* author build; terrain-* author ONE
                                      continuous recipe -> verify.py gate -> emit phases
  5  ECOLOGY       terrain-ecology    plant communities/density over heightfield+biome (natural surface)
  6  BLUEPRINT     exec-blueprint     reusable mcb:* structure templates
  7  BUILD+VERIFY  exec-worker        execute plan.toon via harness (columns/strata/fillbiome/scatter)
  -- GATE B --
  8  INTEGRATE     terrain-integrate  ground the footprint into the world (apron erosion, biome blend)
  -- GATE C --
  9  INSPECT       exec-inspect       plan fidelity + quality_contract + build<->world SEAM check
 10  REGISTER      minecraft-builder  record build + recipe.json + apron job in mcbuilder:registry
 11  REFLECT       exec-reflect       record process lessons to memory
```

## Depth scaling (never gate skipping)

A one-block change still runs the spine — it is just *shallow*: survey the spot, plan the single
step, build it, integrate only if it now meets untouched world, inspect, register. Phases with
nothing to do return immediately, but they are **entered** — nothing slips past unverified. Assuming
something is "too simple to bother" is exactly the failure that produced the ziggurat builds.

## The three gates (automatic, run under autonomy)

- **GATE A - offline verify** (before BUILD): `tools/terrain/verify.py` HALTs on ziggurat /
  flatness / monoculture / degenerate terrain. Terrain that fails is never placed.
- **GATE B - Integrate** (before INSPECT): `terrain-integrate` runs the apron-erosion grounding pass
  so the build does not meet the world at a hard edge. Required for any footprint-bearing build.
- **GATE C - inspect + harness lint** (at INSPECT): `exec-inspect` runs the build<->world seam check
  and the `quality_contract` rows; the harness refuses (exit 1) a terrain phase lacking a
  `recipe.json`, the terrain quality rows, or a passing verify token, and a footprint phase lacking
  the seam row.

A fourth gate is **conditional**, not run on every build:

- **Sign-off gate - offline preview** (before an expensive or hard-to-undo pass): when a phase will
  re-materialize terrain, do a large recolor, or rebuild a feature that has already failed once,
  render the *next* proposal offline from the field/model (no world writes) and get user sign-off
  before placing. It is cheaper than place-render-revert: a Zion endcap took three in-world rejections
  before this loop turned the thrash into one clean placement (preview -> "more eroded" -> adjust ->
  preview -> place once). Under autonomy this folds into the offline render-verify you already owe
  (see `reference/execution/large-builds.md`) — if you cannot get a user glance, still render the
  proposal offline and gate the placement on your own `exec-inspect` pass rather than writing a costly
  pass blind.

## Routing table (primary intent -> orchestrator)

| Primary intent | Orchestrator |
|---|---|
| terrain, landform, biome, water, natural scenery, named natural wonder | `build-natural-world` |
| caves, caverns, ravines, underground space | `build-natural-world` (delegates to `terrain-cave`) |
| village, city, district, town, a building **with grounds/context** | `build-settlement` |
| one named/standalone building, replica, statue/monument, player house, bridge-as-object | `build-structure` |
| redstone, farm, contraption, transit line, nether hub, mechanism | `build-systems` |

Cross-domain builds route by **primary** intent; that orchestrator calls sibling leaves (one inline
orchestrator at a time — no nested forking). Ambiguous requests: the orchestrator interviews first.

## Force-load discipline across phases

A build with a permanently force-loaded mechanism (a self-running rail loop, an automatic farm —
chunks that must stay loaded so it ticks at 0 players) carries a hazard the spine has to thread.
Any later phase that brackets its work with `forceload add` / `forceload remove` over a *range* can
remove the mechanism's chunks too, because `remove` takes a box, not a set. The mechanism then
unloads: entities freeze and read as despawned to `entity_query`, redstone reverts. In the Zion
build the ecology pass removed bands that overlapped the rail chunks and silently unloaded the cart
twice.

The orchestrator owns the fix: it tracks a **permanent force-load set** (the mechanism's chunks) and
**re-asserts that set as the last op of any phase that force-toggles** — so even when a phase's
teardown removes its own band, the protected chunks come back loaded before the phase returns. It
records the set as the top-level `protect:` block in `plan.toon`; the harness reads it and does the
re-assert on `run`/`build`/`freshness`. The mechanism and the matching "no later phase may
`forceload remove` a range near mechanism chunks" rule are documented once — see
`reference/execution/build-harness.md` and `reference/orchestration/coherence.md`; the force-load cap
and behaviour live in `reference/execution/engine-limits.md`.
