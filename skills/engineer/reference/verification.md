# Verification and correction

A contraption built correctly block-for-block can still not *work*. Every
design ships a **functional test recipe**; the `inspector` runs it; when it
fails, you diagnose and correct. This file is how.

## Authoring an inspection recipe

Write the recipe to `.minecraft-builder/<project>/inspection-recipe.toon`. A
test is a sequence of **trigger → wait → sample**:

- **trigger** — apply an input. The `inspector` does this with `mc_run_command`
  — e.g. place a `redstone_block` at a button position then set it back to
  `air`, or `replaceitem` a stack into an input container.
- **wait** — hold for the design's **timing budget** plus slack (the
  worst-case path from `design-patterns.md`, padded for observer drift).
- **sample** — read the result: `mc_block_get` for a block state (a door
  block now `air`, a piston `extended`, a comparator powered),
  `mc_block_get_volume` for a region, `mc_entity_get` for collected drops.
- **expect** — the value a working contraption produces.

```toon
test: jeb-door-2x2
steps[4]{action,target,detail}:
  trigger,{x:4,y:64,z:0},place stone_button powered then release
  wait,,20 game ticks
  sample,{x:4,y:64,z:2},expect air at all 4 door-block coords
  sample,{x:4,y:64,z:2},after 20 more ticks expect the door self-closed
```

Give every contraption a test — even a "trivial" one. The whole point of the
inspector loop is to catch the long tail of Bedrock quirks.

## Per-type test contracts

| Contraption | Trigger | Sample after wait | Pass criterion |
| ----------- | ------- | ----------------- | -------------- |
| Door | power the button position | door-block coords | all become `air`; self-closes |
| Sorter | put a stack of the target item in the input | output and overflow chests | target item only in its row; others empty |
| Mob farm | spawn the mob in the spawn box, or wait a cycle | collection chest | drops arrive within the expected rate |
| Clock | apply the enable signal | a target coord, sampled repeatedly | oscillation period within ±1 tick of plan |
| Minecart | place a test cart at the start | detector rails along the route | rails fire in order, ETAs within ~2 ticks |
| Elevator | place an entity at the base | a coord at the top | entity arrives within the budgeted time |
| Music | trigger the sequencer | the note-block coords | each pulses in sequence |

## Correction catalog — symptom → diagnosis → fix

When the inspector reports a failure, diagnose with this table and emit
corrected steps:

| Symptom | Diagnosis | Fix |
| ------- | --------- | --- |
| Piston never extends, though redstone next to it is powered | A Java quasi-connectivity design — Bedrock has no QC | Move the power to a face *directly* adjacent to the piston; re-design off any "block above" pattern |
| Sorter leaks the target item, or sorts into the wrong row | 21 filler items, or filter rows interfering | Use exactly **20** filler items; add a 1-block isolation gap between rows |
| Hopper not pulling | The hopper is powered (locked) by a stray signal | Find and insulate the stray redstone — often a torch on an adjacent block |
| Filter hopper skips matching items | A non-matching item is in its collection range | Re-route the item stream so matching items arrive alone |
| Observer chain fires late or intermittently | MCPE-15793 / MCPE-73342 timing drift | Add a 2-tick repeater between the affected observer pairs |
| Mob farm: zero spawns | Spawn surface too bright, or outside the spawn shell | Re-check light level (0–7 for hostiles) and the 24–44-block shell at the world's simulation distance |
| Powered rail does not propel the cart | The rail is not actually powered | Power it from an adjacent block/repeater facing it, and respect the ~1-per-38 spacing |
| Door corner does not move | A stuck piston, or one observer drifted | Free the piston / clear obstruction; add retiming for the drifted observer |
| Iron-golem / villager farm rate low | A village-mechanics problem, not engineering | Hand the village half back to `village-planner` |

After a fix, the `worker` applies the corrected steps and the `inspector`
re-runs the test. Loop until it passes — a contraption is not done until its
functional test passes.
