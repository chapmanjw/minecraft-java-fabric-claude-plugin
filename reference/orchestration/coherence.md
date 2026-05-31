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

If any reconciliation fails, fix the owning leaf and re-run it — do not paper over a shape/seam
problem with a colour pass (the parks-grand-loop lesson: a seam is a shape problem).
