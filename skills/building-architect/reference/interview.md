# The adaptive interview

Pin down the design without over-asking. Every branch ends with the **three
core questions** plus a name. Ask in small grouped batches (use
`AskUserQuestion` for the multiple-choice ones), skip what is already settled,
and record answers in `requirements.md`.

## Step 1 — classify the target

What is the user asking for?

- **Real-world** building → real branch.
- **Canonical-fictional** — a building from a named work → fictional branch.
- **User-original** — their own described design → original branch.
- **Generative-style** — "in the style of X" with no specific building →
  generative branch.

## Branch questions

**Real branch**
- Which building?
- As built, or a variant ("Notre-Dame, but cherry-blossom themed")?
- → Then always invoke `researcher` and cite ≥2 sources.

**Fictional branch**
- Which work, and **which adaptation** — book, film, game, or theme-park?
  (They differ — see `fictional.md`.)
- Any deliberate deviations from canon?
- → Cite the adaptation source.

**User-original branch** — gather enough to design:
- Building kind (cathedral, castle, tower, palace, hall, temple, manor,
  academy, fortress, monument, mausoleum, library, observatory)?
- Era or style (see `styles.md`)?
- Dominant materials?
- The one hero feature?
- Room mix?
- Symmetry — required, forbidden, or mixed?
- Approximate footprint and height?

**Generative branch**
- Which style (from `fictional.md`)?
- Mood — pristine, lived-in, ruined, or under-construction?
- The signature feature?
- Symmetry?

## The three core questions — every branch

1. **Scale** — minimum-recognition, medium, 1:1 (only if it fits the Y range),
   or custom. If 1:1 would exceed the world height, say so and propose a
   ratio.
2. **Interior depth** — aesthetic-only, hybrid (name the hero rooms), or fully
   furnished. Explain the cost difference and give a fill-volume estimate.
3. **Composition** — standalone, anchoring a village (the `village-planner`
   coordinates), or doubling as the player's base (the `player-house` skill
   coordinates).

Then: **project name** (the registry slug).

## After the answers

- Invoke `surveyor` for site context; note a `pre-build terraform` step if the
  site needs shaping.
- Compute and state the fill-volume estimate.
- Render preview blueprints (`blueprints.md`), show the user, iterate, and
  confirm before resolving the plan.

## Conduct

- Ask the three core questions before generating any blueprint — they change
  the build by orders of magnitude.
- Group questions; do not interrogate line by line.
- Restate the design — target, adaptation, scale, interior depth, signature
  features — before rendering, so a misread is cheap to fix.
