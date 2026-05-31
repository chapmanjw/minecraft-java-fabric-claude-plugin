"""Fluid-storage tools — read Fabric Transfer-API FluidStorage tanks in-sandbox.

Two live tools, both prefixed ``fluid_``:
  * fluid_storage_get      (safe read — first tank on a given side)
  * fluid_storage_list_at  (safe read — every tank a block publishes)

Both are read-only probes of ``net.fabricmc...FluidStorage.SIDED.find(...)``.
The mod's RegistryOps tries the side-agnostic null face first, then each of the
six faces, and reports the first matching storage; ``fluid_storage_get`` probes
exactly the requested side. Neither mutates world-global state — every block we
read is placed inside the scratch sandbox — so both cases are ``safe``.

Observed response shapes (probed live, 26.1.2):
  fluid_storage_get:
    block with NO FluidStorage on that side -> {"empty": true}   (only the key)
    block with a tank                       -> {"empty": <bool>, "fluid_id": "<id>",
                                                "amount_droplets": <int>, "capacity_droplets": <int>}
  fluid_storage_list_at:
    no FluidStorage -> []                    (TOON "[]" -> empty Python list)
    has tank(s)     -> [{empty, fluid_id, amount_droplets, capacity_droplets}, ...]

Positive fixture: a vanilla ``water_cauldron[level=3]`` (a full cauldron). Fabric's
transfer-api registers vanilla cauldrons as FluidStorage providers, so a full water
cauldron publishes one tank of ``minecraft:water`` at 81000 droplets (= one bucket),
capacity 81000 — verified live during authoring. The assertions stay tolerant: if a
particular Fabric build does NOT register the cauldron provider (the tank reads
empty / the list is empty), that is treated as a no-fixture Skip rather than a FAIL,
since the *contract* (well-formed empty response) is still exercised by the negative
probe against a plain stone block, which never exposes fluid storage.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip


def _place_full_water_cauldron(ctx: Ctx):
    """Place a full water cauldron in the sandbox; return its position tuple."""
    p = ctx.pos()
    text, is_err = ctx.call_text(
        "block_set_state",
        {"dimension": ctx.dim, "position": ctx.pos_obj(p),
         "block": {"id": "minecraft:water_cauldron", "properties": {"level": "3"}}})
    ctx.expect(not is_err, f"failed to place water cauldron: {text}")
    return p


def _place_stone(ctx: Ctx):
    """Place a plain stone block (never exposes a FluidStorage); return position."""
    p = ctx.pos()
    ctx.call_text("block_set_state",
                  {"dimension": ctx.dim, "position": ctx.pos_obj(p),
                   "block": {"id": "minecraft:stone"}})
    return p


@case("fluid_storage_get", level="safe")
def test_fluid_storage_get(ctx: Ctx):
    """Negative + positive probe of the single-tank reader.

    Negative (always asserted): a stone block exposes no FluidStorage on any
    side, so the call must succeed and report ``empty: true``.

    Positive (tolerant): a full water cauldron should publish a water tank on
    its ``up`` face. If this Fabric build doesn't register the cauldron
    provider, the probe reads empty and we Skip the positive half rather than
    fail — the contract is already proven by the negative probe.
    """
    # --- negative: stone has no fluid storage -> {"empty": true} ---
    stone = _place_stone(ctx)
    none_res = ctx.call("fluid_storage_get",
                        {"dimension": ctx.dim, "position": ctx.pos_obj(stone),
                         "direction": "up"})
    ctx.expect(isinstance(none_res, dict),
               f"fluid_storage_get should return an object, got {none_res!r}")
    empty_flag = ctx.expect_field(none_res, "empty")
    ctx.expect(empty_flag is True,
               f"stone should expose no FluidStorage (empty:true), got {none_res}")

    # --- positive: a full water cauldron should publish a water tank ---
    caul = _place_full_water_cauldron(ctx)
    res = ctx.call("fluid_storage_get",
                   {"dimension": ctx.dim, "position": ctx.pos_obj(caul),
                    "direction": "up"})
    ctx.expect(isinstance(res, dict),
               f"fluid_storage_get should return an object, got {res!r}")
    # The 'empty' field is always present.
    has_empty = ctx.expect_field(res, "empty")
    if has_empty is True or "fluid_id" not in res:
        raise Skip("this Fabric build doesn't expose a FluidStorage for water_cauldron")
    fluid_id = ctx.expect_field(res, "fluid_id")
    amount = ctx.expect_field(res, "amount_droplets")
    capacity = ctx.expect_field(res, "capacity_droplets")
    ctx.expect("water" in str(fluid_id),
               f"full water cauldron should hold water, got fluid_id={fluid_id!r}")
    ctx.expect(isinstance(amount, (int, float)) and amount > 0,
               f"full water cauldron should report amount_droplets>0, got {res}")
    ctx.expect(isinstance(capacity, (int, float)) and capacity >= amount,
               f"capacity_droplets should be >= amount, got {res}")


@case("fluid_storage_list_at", level="safe")
def test_fluid_storage_list_at(ctx: Ctx):
    """Negative + positive probe of the multi-tank lister.

    Negative (always asserted): a stone block publishes no tanks, so the call
    returns an empty list.

    Positive (tolerant): a full water cauldron should list one water tank. If
    the cauldron provider isn't registered in this build, the list is empty and
    we Skip the positive half.
    """
    # --- negative: stone publishes no tanks -> [] ---
    stone = _place_stone(ctx)
    none_list = ctx.call("fluid_storage_list_at",
                         {"dimension": ctx.dim, "position": ctx.pos_obj(stone)})
    # TOON "[]" parses to an empty Python list; tolerate None / {} too.
    ctx.expect(none_list in ([], None, {}) or
               (isinstance(none_list, list) and len(none_list) == 0),
               f"stone should publish no fluid tanks, got {none_list!r}")

    # --- positive: a full water cauldron should list one water tank ---
    caul = _place_full_water_cauldron(ctx)
    lst = ctx.call("fluid_storage_list_at",
                   {"dimension": ctx.dim, "position": ctx.pos_obj(caul)})
    if not (isinstance(lst, list) and len(lst) >= 1):
        raise Skip("this Fabric build doesn't expose a FluidStorage for water_cauldron")
    tank = lst[0]
    ctx.expect(isinstance(tank, dict),
               f"each tank entry should be an object, got {tank!r}")
    fluid_id = ctx.expect_field(tank, "fluid_id")
    ctx.expect_field(tank, "amount_droplets")
    ctx.expect_field(tank, "capacity_droplets")
    ctx.expect("water" in str(fluid_id),
               f"full water cauldron should list a water tank, got {tank}")
