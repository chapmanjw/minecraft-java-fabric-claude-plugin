# Community sources

Redstone content overwhelmingly targets **Java Edition** — which is what this
world runs — so most tutorials, videos, and wiki diagrams apply directly. The
real risk is not edition mismatch but **version drift**: redstone behaviour,
spawn rules, and mechanics shift between releases. This is who to trust and how
to verify against the running version.

## Trust for Java

- **The Minecraft Wiki** (minecraft.wiki) — Mojang-endorsed; the highest-trust
  source for mechanics, timing, and block behaviour. Each block/tutorial page
  documents the Java behaviour and notes the version a change landed in. Prefer
  it over the Fandom mirror, which carries outdated figures.
- **Java-focused redstone creators** — the major redstone YouTubers and the
  technical-Minecraft community build and test on Java, so their item-sorter,
  farm, door, and flying-machine tutorials are catalog-eligible. Note the game
  version each design was demonstrated on.
- **The Open Redstone Engineers (ORE) community** and other technical-Java
  references — strong for logic-circuit and computational redstone primitives.
- **The Minecraft Wiki's tutorial namespace** — the "Tutorials/" pages
  (mechanisms, farming, redstone) are vetted Java designs.
- **Mojang changelogs / official snapshots** — authoritative for what changed
  in a given version (e.g. the removal of 0-tick pulses, Crafter additions).

## Verify against the running version

- **Confirm the world's version first** with `server_get_status`. A design
  proven on an older version may behave differently on 1.21.11 / 26.1.x.
- **Version-sensitive areas** to double-check before relying on them:
  spawn-light thresholds, mob-spawn shell distances, bubble-column speeds,
  iron-golem spawn volume, powered-rail spacing, and any contraption that
  exploits a specific tick quirk.
- **Reject patched-out and exploit mechanics** even when a tutorial shows them:
  0-tick farms (removed years ago) and TNT/item duping (bugs that may be patched
  or server-disabled). Re-derive from `design-patterns.md` with a reliable
  mechanic instead.
- **Prefer recent sources.** Ask `researcher` for material verified on a recent
  Java version and note the version a design was confirmed on.
- When the `philosopher` records a contraption pattern as proven on a given Java
  version, prefer that logged pattern next time over re-deriving — but re-verify
  it if the world's version has since changed.

## Sourcing rules

- **Cite a source and its game version for every catalog entry.** A Minecraft
  Wiki page (with the version note) or a named creator's current video.
- **Reject** a design whose only source relies on a patched-out or exploit
  mechanic — re-derive it from `design-patterns.md` instead.
- **Any tutorial that does not state its version** — note the uncertainty and
  verify the load-bearing timing/mechanic in-world before trusting it.

## When in doubt — test it live

Java's determinism means you can verify a mechanic directly: build a minimal
version in a scratch area, run the functional-test recipe pattern from
`verification.md`, and confirm the behaviour on the actual running version
before committing it to a full design. A two-block observer clock, a single
sorter row, or a one-piston door is cheap to prove and removes any
version-drift doubt.
