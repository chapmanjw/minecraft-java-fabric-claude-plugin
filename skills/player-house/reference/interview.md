# The adaptive interview

Capture what the user wants without grilling them. The interview **scales with
the tier**: a starter shack gets ~5 questions, a megabase up to ~25. Ask in
small grouped batches (use `AskUserQuestion` for the multiple-choice ones), not
one at a time. Skip anything the request, the surveyor, or an earlier answer
already settled. Record everything in `requirements.md`.

## Question bank

1. **Tier** — starter shack / cozy cottage / standard home / estate / mansion /
   castle / megabase. Ask this first; lock it before the rest.
2. **Site** — anchor coordinates, or "next to me"; biome and terrain come from
   the surveyor. Surface anything unusual the surveyor flagged (cave, ocean,
   cliff, deep dark).
3. **Solo or co-op** — if co-op, how many beds, and shared or private rooms?
4. **Game stage** — early / mid / late / creative. Gates which blocks and
   rooms are realistic.
5. **Must-have rooms** — present a checklist from `rooms.md` filtered to the
   tier.
6. **Blank-canvas rooms** — any rooms to leave empty for the user to furnish?
7. **Style** — offer 3–5 styles from `styles.md` matched to the biome.
8. **Vibe** — one phrase ("cozy autumn", "cold steel fortress").
9. **Aesthetic vs. functional** — a slider from "purely pretty" to "purely
   working"; drives how much detail vs. how many systems.
10. **Automation depth** — none / convenient (auto-smelter, sorters) / full
    (beacon, conduit, multiple farms).
11. **Site threats** — what is nearby (deep dark, ravine, raids, lava)?
12. **Resource ceiling** — limited survival stock, or creative inventory?
13. **Server rules** — claim sizes, no-grief zones, anything constraining.
14. **Anchor landmark** — a mountain, lake, or tree to build into or beside?
15. **Project name** — a slug for the registry and structure files.

**Starter tier** fires only questions 1, 2, 3, 5, 15 — infer the rest from
sensible defaults and say so.

## Conditional follow-ups

Fire these only when relevant:

- Style is Japanese / Nordic / medieval / fantasy → ask roof-pitch preference.
- Site is underwater → ask conduit-power radius and sponge-drain extent.
- Site is sky / nether / end → ask fall/void protection and the escape route;
  remind the user beds explode in the nether and end.
- Tier is mansion or above → ask the wing layout (radial / linear / compound).
- Tier is megabase → ask farm priorities (XP / iron / mob / crop).
- Automation is "full" → ask which utilities to build first.
- Co-op → ask whether players get private rooms or shared quarters.
- Request mentions "secret" → ask the hidden-door mechanism and trigger.
- Request mentions a portal / dimension → ask which dimensions are linked.
- Request names a specific builder or real reference → hand off to
  `researcher` for imagery before composing.

## Conduct

- Lead with the tier; everything scales from it.
- Group questions; never interrogate one line at a time.
- Offer concrete options, not open prompts — "medieval, Japanese, or modern?"
  beats "what style?".
- Restate your understanding before moving to blueprints, so the user can
  correct a misread cheaply.
