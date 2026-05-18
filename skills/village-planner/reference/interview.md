# The adaptive interview

Capture what the user wants without over-asking. A **hamlet** needs ~6
questions; a **standard village** the full set. Ask in small grouped batches
(use `AskUserQuestion` for the multiple-choice ones), skip anything already
settled by the request or the surveyor, and record answers in
`requirements.md`.

## Question bank

1. **Scale** — hamlet (2–4 buildings) or standard village (5–15)? Ask first;
   lock it.
2. **Site** — anchor coordinates or "near me"; biome and terrain from the
   surveyor.
3. **Player-house composition** — how does the village relate to the player's
   own base?
   - **A** — built around an existing player house (recommended; if they have
     no house yet, suggest `player-house` first). Ask the buffer distance
     (default 30–50 blocks).
   - **C** — a pure NPC village, separate from the player.
   - **B** — a village building *is* the player's home (advanced).
4. **Style** — vanilla for the biome, vanilla restyled, or a fully custom
   theme (medieval, cottagecore, Tudor, Mediterranean, frontier)?
5. **Layout** (standard only; hamlets default to organic cluster) — linear,
   crossroads, radial plaza, organic cluster, coastal, walled, farm-focused,
   or mountainside.
6. **Profession mix** — a balanced trade hub (one of each), specialized (pick
   2–3), or essentials only (farmer, librarian, smith)? A hamlet gets at most
   2 professions.
7. **Functional priorities** (multi-select):
   - iron-golem-ready (forces ≥10 villagers and ≥20 beds — confirm and resize);
   - trade-focused (extra workstations);
   - raid-defensible (walls, perimeter lighting);
   - breeding-ready (spare beds, a farmer with a composter);
   - cats (needs enough claimed beds).
8. **Defense** (standard only) — walls (none / low / palisade / fortified),
   watchtower count, gate type. Remind the user a wall must not fully seal the
   village.
9. **Agriculture** (standard only) — none, one small farm, or a field complex
   with animal pens.
10. **Village name** — used on signs and as the registry project id.

## Conditional follow-ups

- Iron-golem-ready chosen but the roster is short → propose spare-bed houses
  to reach ≥10 villagers / ≥20 beds, and confirm the larger size.
- Site near a **pillager outpost** → warn the user that Bedrock outposts can
  sit inside village range and cause frequent raids; offer to relocate.
- Mountainside or uneven site → note a `terraforming` pre-build step.
- Coastal → ask about a dock and a fisherman.
- A specific style or real reference named → hand off to `researcher` for
  imagery before composing.

## Conduct

- Lead with scale and the player-house composition mode — they shape
  everything else.
- Group questions; never interrogate one line at a time.
- Proactively warn at standard scale if the roster is near but under the
  iron-golem threshold ("you are at 8 villagers — 2 more unlocks golems").
- Restate the design before rendering layouts, so a misread is cheap to fix.
