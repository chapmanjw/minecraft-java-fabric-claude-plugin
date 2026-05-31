"""Content-registry tools — fuel / compostable / flammable introspection + mutation.

Six live tools, all prefixed ``content_``:
  * content_registry_get_fuel              (safe read)
  * content_registry_is_compostable        (safe read)
  * content_registry_is_flammable_block    (safe read)
  * content_registry_set_fuel              (GLOBAL — runtime no-op in Fabric, but
                                            still treated as global: read/restore)
  * content_registry_set_compostable       (GLOBAL — mutates the composter table)
  * content_registry_set_flammable_block   (GLOBAL — mutates the fire registry)

Observed response shapes (probed live, 26.1.2):
  get_fuel             -> {"burn_time_ticks": <int>}                 (0 = not a fuel)
  is_compostable       -> {"compostable": true, "chance": <number>}  (chance 0 = not compostable)
  is_flammable_block   -> {"flammable": true, "spread_chance": <int>, "burn_chance": <int>}

NOTE on the booleans: ``is_compostable``/``is_flammable_block`` appear to always
report the flag ``true`` and key the real answer off the numeric field (chance /
burn_chance+spread_chance == 0 means "not registered"). Assertions therefore key
on the numeric fields, not the boolean.

The three ``set_*`` tools mutate process-global registries, so each reads the
current value first, sets a distinct test value, asserts, then RESTORES the
original in a try/finally.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip


# ---------------------------------------------------------------------------
# safe reads
# ---------------------------------------------------------------------------

@case("content_registry_get_fuel", level="safe")
def test_get_fuel(ctx: Ctx):
    # coal is a vanilla fuel (1600 ticks); diamond is not a fuel (0).
    fuel = ctx.call("content_registry_get_fuel", {"item_id": "minecraft:coal"})
    bt = ctx.expect_field(fuel, "burn_time_ticks")
    ctx.expect(isinstance(bt, (int, float)) and bt > 0,
               f"coal should be a fuel with positive burn time, got {fuel}")

    nonfuel = ctx.call("content_registry_get_fuel", {"item_id": "minecraft:diamond"})
    bt0 = ctx.expect_field(nonfuel, "burn_time_ticks")
    ctx.expect(bt0 == 0, f"diamond should not be a fuel (burn_time_ticks 0), got {nonfuel}")


@case("content_registry_is_compostable", level="safe")
def test_is_compostable(ctx: Ctx):
    # apple is compostable in vanilla (0.65 chance).
    res = ctx.call("content_registry_is_compostable", {"item_id": "minecraft:apple"})
    chance = ctx.expect_field(res, "chance")
    ctx.expect(isinstance(chance, (int, float)) and chance > 0,
               f"apple should be compostable with chance>0, got {res}")

    # diamond is not compostable (chance 0).
    res0 = ctx.call("content_registry_is_compostable", {"item_id": "minecraft:diamond"})
    chance0 = ctx.expect_field(res0, "chance")
    ctx.expect(chance0 == 0, f"diamond should not be compostable (chance 0), got {res0}")


@case("content_registry_is_flammable_block", level="safe")
def test_is_flammable_block(ctx: Ctx):
    # oak_planks burn in vanilla (spread 5 / burn 20).
    res = ctx.call("content_registry_is_flammable_block", {"block_id": "minecraft:oak_planks"})
    burn = ctx.expect_field(res, "burn_chance")
    spread = ctx.expect_field(res, "spread_chance")
    ctx.expect(isinstance(burn, (int, float)) and burn > 0,
               f"oak_planks should have burn_chance>0, got {res}")
    ctx.expect(isinstance(spread, (int, float)) and spread > 0,
               f"oak_planks should have spread_chance>0, got {res}")

    # stone does not burn.
    res0 = ctx.call("content_registry_is_flammable_block", {"block_id": "minecraft:stone"})
    burn0 = ctx.expect_field(res0, "burn_chance")
    ctx.expect(burn0 == 0, f"stone should not be flammable (burn_chance 0), got {res0}")


# ---------------------------------------------------------------------------
# global mutations — read original, set test value, assert, RESTORE
# ---------------------------------------------------------------------------

@case("content_registry_set_fuel", level="global")
def test_set_fuel(ctx: Ctx):
    """set_fuel is documented as a recorded no-op under current Fabric (runtime
    fuel mutation unsupported). We still treat it as global: read the original,
    issue the set, assert the call is accepted (non-error), and confirm the
    registry value is unchanged afterward (no-op) so nothing leaks across runs.
    Use a non-fuel item so even if a future build *does* honor it, the original
    (0) is trivially restored."""
    item = "minecraft:diamond"
    before = ctx.call("content_registry_get_fuel", {"item_id": item})
    orig = ctx.expect_field(before, "burn_time_ticks")
    try:
        text, is_err = ctx.call_text("content_registry_set_fuel",
                                     {"item_id": item, "burn_time_ticks": 1234})
        ctx.expect(not is_err, f"set_fuel returned error: {text}")
        # Tolerant: either it was a no-op (still orig) or it took effect (1234).
        after = ctx.call("content_registry_get_fuel", {"item_id": item})
        bt = ctx.expect_field(after, "burn_time_ticks")
        ctx.expect(bt in (orig, 1234), f"set_fuel: unexpected burn time {bt} (orig {orig})")
    finally:
        # Restore original regardless (harmless no-op if unsupported).
        ctx.call_text("content_registry_set_fuel",
                      {"item_id": item, "burn_time_ticks": orig})


@case("content_registry_set_compostable", level="global")
def test_set_compostable(ctx: Ctx):
    """Mutates the composter level-up table for an item. Read original chance,
    set a distinct test value, verify via is_compostable, then restore."""
    item = "minecraft:diamond"   # vanilla non-compostable (chance 0) — clean baseline
    before = ctx.call("content_registry_is_compostable", {"item_id": item})
    orig = ctx.expect_field(before, "chance")
    test_chance = 0.5
    try:
        text, is_err = ctx.call_text("content_registry_set_compostable",
                                     {"item_id": item, "chance": test_chance})
        ctx.expect(not is_err, f"set_compostable returned error: {text}")
        after = ctx.call("content_registry_is_compostable", {"item_id": item})
        chance = ctx.expect_field(after, "chance")
        ctx.expect(abs(float(chance) - test_chance) < 1e-6,
                   f"set_compostable did not take effect: chance={chance} (wanted {test_chance})")
    finally:
        ctx.call_text("content_registry_set_compostable",
                      {"item_id": item, "chance": orig})


@case("content_registry_set_flammable_block", level="global")
def test_set_flammable_block(ctx: Ctx):
    """Mutates the fire-spread/burn registry for a block. Read original
    burn/spread, set distinct test values, verify, then restore both.

    Fixed in R5: burn_chance and spread_chance are no longer swapped between the
    setter and the getter. set(burn_chance=15, spread_chance=30) now reads back
    burn_chance=15 and spread_chance=30 (not the previously inverted 30/15).
    """
    block = "minecraft:stone"   # vanilla non-flammable (0/0) — clean baseline
    before = ctx.call("content_registry_is_flammable_block", {"block_id": block})
    orig_burn = ctx.expect_field(before, "burn_chance")
    orig_spread = ctx.expect_field(before, "spread_chance")
    test_burn, test_spread = 15, 30
    try:
        text, is_err = ctx.call_text(
            "content_registry_set_flammable_block",
            {"block_id": block, "burn_chance": test_burn, "spread_chance": test_spread})
        ctx.expect(not is_err, f"set_flammable_block returned error: {text}")
        after = ctx.call("content_registry_is_flammable_block", {"block_id": block})
        burn = ctx.expect_field(after, "burn_chance")
        spread = ctx.expect_field(after, "spread_chance")
        # R5 fix: getter and setter are now aligned — values must match exactly.
        ctx.expect(burn == test_burn and spread == test_spread,
                   f"set_flammable_block readback mismatch: burn={burn} spread={spread} "
                   f"(expected burn={test_burn}, spread={test_spread})")
    finally:
        ctx.call_text(
            "content_registry_set_flammable_block",
            {"block_id": block, "burn_chance": orig_burn, "spread_chance": orig_spread})
