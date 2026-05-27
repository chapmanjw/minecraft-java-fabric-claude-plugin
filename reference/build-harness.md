# The build + verify harness

A local Python harness that executes a `plan.toon` phase and mechanically
verifies it against the live server — **entirely outside the LLM context**. It is
the token-efficient path for static work: instead of the `worker` emitting
hundreds of in-context tool calls and the `inspector` issuing dozens of scan
calls, the harness POSTs everything to the server directly and returns one
compact digest.

The analogy is a test harness for builds:

| Build artifact | Harness role |
| --- | --- |
| `plan.toon` `steps` | the code |
| `plan.toon` `acceptance` + `quality_contract` | the assertions |
| `harness.py run` | the build step |
| `harness.py verify` | the test runner |
| the printed digest | the results |

It runs in **Claude Code** (where there's local Bash + Python), is **stdlib-only**
(no deps), and talks to the same MCP server over HTTP — reading the URL/auth from
`~/.claude.json` like `voxel/mcp_place.py` does.

## CLI

```sh
P=${CLAUDE_PLUGIN_ROOT}/tools/builder/harness.py
python $P mode                              # dedicated vs single-player (gameTime test)
python $P selftest                          # write-readiness (forceload→set→read→restore)
python $P run    <plan.toon> <phase>        # execute a phase (force-load-bracketed)
python $P verify <plan.toon> <phase>        # run that phase's acceptance + contract checks
python $P build  <plan.toon> <phase>        # run, then verify  (the common case)
python $P perceivable                       # can a player at spawn see/reach the built elements?
python $P audit                             # flag registry `built` rows with no verify_token
```

Exit code `0` = everything attempted passed; `1` = any execution failure,
force-load miss, failed check, lint refusal, or perceivability/audit flag. The
calling skill branches on the exit code and reads the printed digest/report.

`run`/`build` take `--force` to override the terrain anti-pattern lint (below).
`perceivable` takes `--threshold N` (default 200 blocks) and `--spawn 'x y z'`.

## Pre-flight lint — the terrain anti-pattern gate

Before executing, `run`/`build` lint the phase. If the phase reads as **organic
terrain** (its project/element/step-notes mention terrain, canyon, mountain,
coastline, mesa, …) the harness **refuses** (exit 1) when either:

- it carries **no** `quality_contract` terrain row (`silhouette`,
  `edge_irregularity`, `block_mix_ratios`, `asymmetry`, `foundation_naturalised`,
  `water_continuity`) — a terraforming-class phase with no contract; or
- it is **stacked Y-banded rectangular slab-fills** across ≥3 elevations that
  share edges or nest — the banned "ziggurat" construction.

This is the machine backstop for terraforming hard-rule 1: organic terrain must
come from the heightmap method or live sculpt, never a static stack of
rectangles. A deliberately rectilinear build (a plaza, a floor stack) is not
classified as terrain and is not affected; pass `--force` only if you are
certain a flagged phase is not organic terrain.

## Verify tokens — the `status:built` gate

On a **PASS** with at least one real check, `verify`/`build` print a
`VERIFY-TOKEN: vt_…` line. It is a content hash of the plan identity, phase, and
every check result — deterministic, so a real passing run always reproduces it.
Record it in the registry build row's `verify_token` cell: **`status:built` is
only legitimate with a token.** A phase that verified *nothing* (no acceptance
and no `quality_contract`) prints a "no token" note instead and must not be
marked built. `harness.py audit` reads the registry and flags every `built` row
whose `verify_token` is blank or malformed — a self-approved build that never
passed an independent verification.

## What it does

- **run** — executes every step of the phase in `seq` order, mapping each `op`
  to its MCP tool (`fill`→`block_fill_region`, `set`→`block_set_state`,
  `replace`, `clone`, `place-structure`→`structure_load_to_world`,
  `spawn`→`entity_summon`, `block-nbt`, `set-slot`→`inventory_set_slot`,
  `run`→`command_execute`). It **force-load-brackets** the phase (see below) and
  flags any write that changed 0 blocks as a probable force-load miss.
- **verify** — runs `acceptance` (coordinate→expected-block) and every applicable
  `quality_contract` row (`walkability`, `doors`, `headroom`, `block_mix_ratios`,
  `silhouette`, `edge_irregularity`, `connectivity`) using the sampling algorithms
  in `inspector/reference/contract-checks.md`, computing PASS / CORRECTIONS NEEDED
  / FAIL with the exact failing samples and the routing hint.

## Force-load envelope (dedicated/unattended servers)

`run`/`build` bracket the phase with `forceload add` … `forceload remove`,
because writes silently no-op in unloaded chunks when no player is online. The
envelope comes from the plan's `envelopes` metadata for that phase, else it is
derived from the phase's step coordinates. It is auto-**banded** to stay under the
vanilla **256-chunk per-dimension** cap (regions wider than that build in Z-bands,
one force-load at a time). Force-load is per-dimension; Nether/End work re-loads
in that dimension. The envelope is held through `verify`'s read-backs, then
released.

Declare envelopes in `plan.toon` so both the harness and the fallback worker know
them:

```toon
envelopes[2]{phase,corner_a,corner_b}:
  1,118 -342,134 -328
  2,118 -342,134 -328
```

`corner_a`/`corner_b` are `x z` block coords (Y is irrelevant to force-loading).

## Graceful fallback

The harness is **opt-in**. If Python isn't available, the package is missing, or
a phase is unusually dynamic, the `worker` falls back to executing the steps as
in-context MCP tool calls (and force-loads the declared envelope manually). The
mechanical verification still applies — the `inspector` can run the same checks
in-context when the harness can't.

## What stays in the model

The harness does the deterministic, high-volume work. The model still owns:
**design** (planner-class skills), **freshness judgement** (is the plan stale
against current terrain?), **failure diagnosis and routing** when a check fails in
a way the fixed routing table doesn't cover, and **perceptual judgement** — "does
it *look* right" — which no assertion captures and which stays with
`block_render_region` + user visual checkpoints. For a **ride-through /
walk-through** build that means an **iso + eye-level** render from the viewer's
height — never a top-down plan view, which hides the vertical faces a viewer
actually sees (the parks-loop "snow re-skin" and "blending done" both passed a
top-down look and were walls from the cart). And a render judged by the same
agent that placed the blocks is self-assessment, not verification — the gate is
an independent `inspector` pass and a user visual checkpoint.

## Generated placement scripts — a third execution mode

The harness executes a `plan.toon` of discrete steps; the `worker` can also fall
back to in-context ops. There is a **third mode** for a form too large or too
parametric to be a single structure template or a tractable step list — a whole
continuous heightfield, a voxelized monument, a ring-spanning belt: **drive a
generated placement script.** Author the form as a parametric model (the
`terrain` / `voxel` toolkits), render-verify it offline, then place it with the
bundled paced placer:

```sh
python ${CLAUDE_PLUGIN_ROOT}/tools/voxel/mcp_place.py place /abs/scratch/field_fills.json
```

`mcp_place.py` pages `block_fill_batch` under the 8192-entry cap, paces under the
~60 rpm limit, and backs off on HTTP 429. The authoring **script + model `.npy`
are the reusable, registry-worthy artifact** — record their location in the
registry exactly as for a structure template, since the form can be regenerated
and re-placed from them. A hand-rolled placer must replicate the pacing + 429
backoff (see `${CLAUDE_PLUGIN_ROOT}/reference/engine-limits.md` § Throughput).
