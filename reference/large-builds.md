# Large and autonomous multi-site builds

The orchestrator cites this when a build spans many zones (an exposition, a city,
a whole landscape) — especially one run **unattended** while the user is away.
These fail in a specific way: they report steady progress while quietly shipping
far less than planned. A real overnight build of eleven zones finished with
**four zones flat-absent**, the village and cathedral half-built, and the
blueprinter's templates **never persisted** — yet nothing flagged it until the
final sweep. Guard against that:

- **Autonomy relaxes only *waiting on the user* — never the gates.** This is the
  single most important rule for unattended runs, and the one a real overnight
  parks build got exactly backwards. "Run autonomously / don't wait on me" means
  *do not block on my approval between phases* — it does **not** mean skip the
  `inspector`, the prototype render, the offline render-verify, or the
  `quality_contract`. Those automated checks are the **only** feedback when no
  one is watching, so unattended makes them more essential, not optional. If you
  cannot get a user glance, still build the prototype, render-verify it offline,
  store the render, and gate scale-up on your own `inspector` pass. Reading
  "why'd you stop?" as "build faster" and churning out more unverified volume is
  the documented failure, not the fix.
- **Keep a completion ledger.** Track every planned element/zone in the
  `mcbuilder:registry` with an explicit status. An element is `built` **only
  after its verification passed** — recorded as a `verify_token` in the registry
  row (the `vt_…` token `harness.py verify`/`build` prints on PASS; see the State
  model). Not when a sub-agent says it finished. A `built` row with **no token**
  is self-approval, not verification — `harness.py audit` scans the registry and
  flags exactly these. Never report the job done until every planned element has
  a passing verification; list any `absent`/`partial` zone honestly in the final
  report.
- **The iteration boundary is a gate (loops especially).** Under `/loop` or any
  iterated build, do not start the next element/zone until the previous one is
  `built` with a token. Starting the next iteration before the last verified is
  how a loop silently ships a row of unverified builds while reporting progress.
- **Before reporting done, confirm a human can perceive the result.** Run
  `python ${CLAUDE_PLUGIN_ROOT}/tools/builder/harness.py perceivable`: it checks
  every `built`/`partial` element against world spawn and flags any whose nearest
  point is beyond render distance (~200 blocks) with no registered connecting
  transit. A build that nobody standing in-world can see or reach is not done —
  this is the gate that catches the "spawn in an empty interior, everything
  beyond render distance" outcome before the user does.
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
