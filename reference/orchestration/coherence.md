# The Coherence Contract

The reason builds used to come out *disjointed* — each specialist did its piece but the pieces didn't
come together — is that leaf skills never saw each other's work. The fix is this contract: a Tier-2
orchestrator (`build-*`) holds a **shared context** and threads it into every leaf it invokes, then
reconciles their returns. Coherence lives in one place per domain, on the main thread that can see
every leaf's result.

## What the orchestrator owns and passes to every leaf

1. **One datum / sea level.** A single `sea_level` and ground datum for the whole build. Every leaf
   (terrain, buildings, grading) works to it. No leaf invents its own.
2. **One continuous terrain recipe.** Terrain is authored as ONE `recipe.json` (a sampler graph),
   never as independent per-region fields butted together. Regions blend by construction (belt /
   `sparse_convolution_blend`). The orchestrator forbids hand-authored fills.
3. **One palette / material vocabulary.** A shared block-and-material palette family so buildings,
   ground, and detail read as one place — not a patchwork. Passed to design-* and terrain-* alike.
4. **One biome + scatter plan.** Biome assignment and vegetation density are decided once (for the
   whole footprint) so tints, plants, and surfaces agree across regions.
5. **One seam / integration plan.** The orchestrator records the build's footprint so the final
   `terrain-integrate` pass grounds the WHOLE thing into the world in one coherent apron, not
   per-element patches.
6. **One permanent force-load set.** If the build includes a permanently force-loaded mechanism
   (a self-running rail loop, an automatic farm, a persistent command block) the orchestrator
   tracks its chunks as a permanent set and threads it to every phase that force-toggles. The
   chunks must stay loaded for 0-player ticking; a later phase that force-removes a *range*
   overlapping them unloads the mechanism (entities freeze, redstone reverts). See the force-load
   rule under Reconciliation below.

## How it threads through the spine

- The orchestrator runs `survey-site` first and derives the datum/palette/biome context from the
  *actual* site — not assumptions.
- It passes that context into each leaf's brief (in the plan.toon header + the leaf invocation).
- After each leaf returns, it **reconciles**: ecology is checked against the heightfield the shape
  actually produced; building materials are checked against the shared palette; grading is checked
  against the datum. Mismatches are corrected before advancing.
- It assembles ONE `plan.toon` with all phases, so exec-worker builds them in a coherent order and
  exec-inspect checks them as a whole.

## Reconciliation rules (catch the disjointedness)

- **Terrain <-> ecology:** species/density must match the biome AND the slope the heightfield produced
  (no forests on cliffs, no desert plants on a grassed slope).
- **Buildings <-> terrain:** a structure's pad/datum must match the graded terrain; its foundation is
  grounded by `terrain-integrate`, not left floating or trenched.
- **Region <-> region:** adjacent terrain regions share one continuous field; adjacent buildings share
  the material vocabulary; the street/transit network connects them.
- **Whole <-> world:** the assembled footprint is grounded into the surrounding world by a single
  integration pass that re-materializes the apron to the surveyed surrounding palette.
- **Mechanism <-> force-loads:** if a phase force-toggles near the permanent force-load set, the
  mechanism's chunks must still be loaded when the phase ends. Prefer `forceload add` only; never
  force-REMOVE a *range*, since the remove takes a box, not a set, and will catch the mechanism's
  chunks. Reclaim the 256-chunk-per-dimension cap with targeted single-chunk removes of KNOWN
  non-mechanism chunks. The orchestrator re-asserts the permanent set with `forceload add` as the
  LAST op of any force-toggling phase (run / build / freshness), which the harness does for you when
  the set is declared as a top-level `protect:` block in `plan.toon` (rows of `corner_a corner_b` as
  `x z`) — see `${CLAUDE_PLUGIN_ROOT}/reference/execution/build-harness.md`. The mechanics of the
  force-load cap, banding, and the `forceload remove all` footgun live once in
  `${CLAUDE_PLUGIN_ROOT}/reference/execution/engine-limits.md`.

If any reconciliation fails, fix the owning leaf and re-run it — do not paper over a shape/seam
problem with a colour pass (the parks-grand-loop lesson: a seam is a shape problem).

## Adversarial integration defenses

When a phase replaces or re-materializes a structure that was already built, clear its ENTIRE prior
footprint, not just the footprint of the replacement. Recompute the old extent from the generator
that made it; it often reaches past where you think (a canyon endcap's headwall extended ~22 blocks
past the new clear box, leaving a vertical-drip tower poking up behind the replacement). The old
extent can also reach BEYOND the world border — blocks placed in a force-loaded chunk outside the
border still exist and survive a too-small clear box. Compute the full old extent, clear all of it,
THEN place the replacement.
