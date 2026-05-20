# Setblock-placed redstone — what self-starts, what needs a kick

The agent places blocks via MCP tools (`mc_block_set`, `mc_block_fill`,
`mc_structure_place`) that all reduce to `setblock`-equivalent operations.
In Bedrock, **`setblock` does not generate the block-update events that a
player-placed block does.** That has concrete consequences for redstone.

This file documents which redstone patterns will self-start when built blind
and which require a one-time manual kick. The list is grounded in the Cape
Aurelia Phase 10–12 retrospective: every self-starting pattern attempted
there failed; every kicked pattern worked.

## Patterns that self-start when placed via setblock

These work blindly — the inspection recipe samples directly.

- **Direct power: lever on a block adjacent to receiver.** A lever placed
  on a stone block adjacent to a piston, lamp, dispenser, or other receiver
  activates normally. The lever's "on" state set via setblock does propagate
  power.
- **Static power: `redstone_block` adjacent to receiver.** A `redstone_block`
  placed next to a piston/lamp/dispenser sets the receiver active
  immediately. Reliable.
- **Button on a wall.** Pressing a button is the player's job; pre-placed
  buttons sit unpressed and work the moment the player clicks them.
- **Pressure plate on a stand-on-able block.** Players or mobs trigger
  it; pre-placed plates work as soon as something walks on them.
- **Lit redstone torch + adjacent dust.** A `redstone_torch` (lit) next to
  dust powers the dust. Static state; no clock involved.
- **Doors, trapdoors, fence gates with a power source.** Open/closed states
  follow the power source's state at the moment of placement.
- **Note blocks under a button or lever.** Plays on signal. The signal
  doesn't need to be cycling; one-shot triggers are fine.

## Patterns that DO NOT self-start — kick required

Anything that needs an internal cycle to begin. Without a player block-update
event, the cycle stays dormant.

- **2-observer clock** (two observers facing each other). Bedrock's classic
  signal-loop primitive. Built blind, both observers sit idle. Right-click
  either observer to kick.
- **Hopper clock** (two hoppers passing one item, comparators reading
  count). The hoppers don't run their transfer cooldown until an inventory
  change pokes them; comparators don't update until the hopper does. Right-
  click the comparator (or break/replace an item in either hopper) to kick.
- **Repeater loop** (a closed line of repeaters powering itself). Each
  repeater sits `unpowered_repeater` after setblock. Right-click any
  repeater to switch its delay and trigger a block update — the loop
  starts.
- **Observer ring** (4-, 5-, or N-observer cyclic loop). Same as the
  2-observer clock, scaled up. The Cape Aurelia rotating beam tried 4-, 9-,
  and 16-observer rings with repeaters; all settled into 2-of-N
  oscillation or never started. Kick any observer or repeater.
- **Comparator-fed dust loop**. The comparator output drives the input.
  Comparator output state is stale until something updates it. Right-click
  the comparator's front block to kick.
- **Levers whose state is set via setblock as part of a powered chain.**
  The lever's `open_bit` value is correct but the propagation hop doesn't
  happen. Break and replace, or right-click, to kick.
- **Pistons in a sequenced piston door or piston elevator**. The first
  piston of the sequence may extend; downstream stages won't fire because
  the observer/repeater that should detect the first piston's update fires
  on the player's update event, not on the setblock event.

## The kick — what it looks like to the user

A "kick" is the player walking to a named coordinate and clicking once. It
must be:

- **Documented in the inspection recipe** as a `manual_kick` block —
  coordinate + action.
- **Surfaced in the orchestrator's final report** as an outstanding manual
  step ("right-click observer at (-39, 143, -42) to start the rotating
  beam").
- **Done before the functional test samples** the result. If the user
  hasn't kicked yet, the test will fail.

A kicked clock runs **forever** afterward — there is no decay. The kick is a
one-time chore per mechanism per world session.

## What about `mc_structure_place` of a running mechanism?

Theoretical workaround: build the mechanism in a survival session by hand,
capture it with `mc_structure_create_from_world`, then `mc_structure_place`
the captured running state. The Cape Aurelia project did not test this end
to end, but the prevailing evidence is that **placement still de-energises
the loop** because the structure-place itself is a setblock-equivalent
operation that doesn't fire block updates on the blocks it places.

Until tested and confirmed otherwise, **assume structure-placed clocks need
the same kick as setblock-placed clocks.** Document the kick step regardless
of how the mechanism was built.

## Decision tree

When the user asks for a mechanism:

1. **Can it be triggered by a player-operated input** (lever, button, plate,
   walked-into trigger)? → Build it; no kick needed.
2. **Does it need to cycle on its own** (a clock, a self-running animation,
   a self-starting timer)? → Build it AND declare a `manual_kick` step
   AND tell the user upfront — before they pick the feature — that they
   will need to click once to start it.
3. **Is the user willing to live with the one-click kick?** → Build it.
4. **Is the user not willing to click?** → Redesign as a lever-triggered
   one-shot instead of a self-cycling animation. Be honest about the
   tradeoff.

The honesty step is non-negotiable. Cape Aurelia shipped windmills and
rotating beams without flagging the kick; the user had to discover the
limitation after the build was "done". That cost trust. Flag it first.
