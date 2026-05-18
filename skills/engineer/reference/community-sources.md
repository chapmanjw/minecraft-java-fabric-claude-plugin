# Community sources

Redstone content overwhelmingly targets **Java Edition**. When you ask
`researcher` to pull a design that is not in the catalog, this is who to trust
for **Bedrock** and who to treat with caution.

## Trust for Bedrock

- **The Minecraft Wiki** (minecraft.wiki) — Mojang-endorsed; the
  Bedrock-specific notes embedded on each block and tutorial page are the
  highest-trust source for parity facts. Prefer it over the Fandom mirror,
  which carries outdated figures.
- **Bedrock-focused creators** — creators who build and test exclusively or
  primarily on Bedrock are the right source for "what actually works now."
  Their item-sorter, farm, and door tutorials are catalog-eligible.
- **Microsoft Learn — Spawn Rules** — authoritative for spawn mechanics
  (`brightness_filter`, `distance_filter`, `density_limit`).
- **Mojang Feedback** (feedback.minecraft.net) — the official statement that
  the two editions' redstone is functionally different and will stay so.

## Treat with caution — Java-first

- **Most popular redstone YouTubers are Java-first.** Their designs almost
  always assume quasi-connectivity and Java piston timing, and do **not** port
  to Bedrock. Use them only to understand *why* a circuit works — never copy
  the build. If a creator has explicit Bedrock-port videos, only those are
  catalog-eligible.
- Any tutorial that does not state its edition — assume Java and verify before
  trusting it.

## Sourcing rules

- **Cite a Bedrock-edition source for every catalog entry.** A Minecraft Wiki
  page with a Bedrock note, or a named Bedrock creator's current video.
- **Reject** a design whose only source is a Java tutorial with no Bedrock
  confirmation — re-derive it from `design-patterns.md` instead.
- **Prefer recent sources.** Bedrock redstone parity changes between releases
  (piston and observer behaviour, iron-golem spawn volume, raid mechanics have
  all shifted). Ask `researcher` for post-1.21 material and note the version a
  design was verified on.
- When the `philosopher` records a contraption pattern as proven on a given
  Bedrock version, prefer that logged pattern next time over re-deriving — but
  re-verify it if the world's version has since changed.

## Bug references

The timing bugs the skill designs around — **MCPE-15793** and **MCPE-73342**
(observer pulse delay) — are documented via the Minecraft Wiki's references to
them. The Mojang bug tracker has restricted public access to many MCPE issues;
cite the wiki's references rather than the tracker directly.
