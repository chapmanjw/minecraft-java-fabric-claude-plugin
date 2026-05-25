# Large and autonomous multi-site builds

The orchestrator cites this when a build spans many zones (an exposition, a city,
a whole landscape) — especially one run **unattended** while the user is away.
These fail in a specific way: they report steady progress while quietly shipping
far less than planned. A real overnight build of eleven zones finished with
**four zones flat-absent**, the village and cathedral half-built, and the
blueprinter's templates **never persisted** — yet nothing flagged it until the
final sweep. Guard against that:

- **Keep a completion ledger.** Track every planned element/zone in the
  `mcbuilder:registry` with an explicit status. An element is `built` **only
  after its verification passed** (harness `verify`, or the `inspector`) — not
  when a sub-agent says it finished. Never report the job done until every planned
  element has a passing verification; list any `absent`/`partial` zone honestly in
  the final report.
- **Verify every phase, not just at the end.** The per-phase verify loop is what
  catches a zone that silently didn't build. One final QA sweep at dawn is too
  late — by then the gaps are baked in. Do not batch verification.
- **Verify the blueprinter actually persisted.** After the blueprint phase,
  confirm with `structure_list` that each `mcb:<project>_*` template exists before
  any consumer references it. A consumer that can't find its template must
  **alert you, not substitute ad-hoc geometry** — silent substitution breaks
  visual cohesion. Save shared modules early, before settlement/detailing agents
  run.
- **Parallelism ceiling ≈ 3.** Running about three background sub-agents on
  **non-overlapping coordinate zones** is the practical throughput ceiling; beyond
  that the shared MCP rate limit throttles all of them and net throughput doesn't
  rise. Assign one agent per zone envelope, keep envelopes disjoint, and stagger
  starts so they don't all hit the rate limit at once.
- **Force-load per zone, and mind the 256-chunk cap.** On a dedicated/unattended
  server each zone's write envelope must be force-loaded before writing and
  released after (the build harness does this; see `reference/build-harness.md`).
  The cap is **256 chunks per dimension** — disjoint parallel zones share that
  budget, so keep each zone's envelope modest and release it when the zone is done
  rather than holding every zone loaded at once.
- **Unattended ≠ ticking — but only on single-player.** On a **single-player**
  client left idle/unfocused, the scheduled block-tick queue freezes, so don't
  schedule any step that relies on pistons, hoppers, comparator container-reads,
  or crop growth self-completing overnight. On a **dedicated** server with
  `pause-when-empty-seconds=0` the tick queue runs 24/7 and these *do* advance —
  as long as the chunk stays force-loaded. Detect which you're on with
  `harness.py mode` (see `reference/startup-and-recovery.md`) and report it.
  Either way, verify mechanisms by an immediate fire while active rather than
  waiting for a cycle to self-complete across a context gap, and force-load the
  work zone so block ops don't no-op.
