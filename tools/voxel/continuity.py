"""Rail / wire continuity verifier — catch the cells a bulk placement silently
dropped, then patch them one block at a time.

``block_fill_batch`` can silently drop a small number of entries from a large
batch (Zion: 4 of 1,928 one-block rail fills landed nowhere, with no error). For
wide terrain that is invisible; for a **1-wide** feature — a rail, a redstone
line, a thin wall — it is fatal: the cart stalls dead at each gap. So after any
1-wide placement, re-scan the feature's own Y-layer, diff it against the cell
list you intended, and re-place only the missing cells. ``block_set_state`` is
reliable per block, so the patch always lands.

The pure ``find_gaps`` is the testable core (intended set minus placed set).
``verify_and_patch`` wires it to the live server through ``voxel.mcp_place``:
scan the layer (tiled under the 65,536-volume scan cap), find the gaps, and
``block_set_state`` each one.

    from voxel.continuity import find_gaps, verify_and_patch
    report = verify_and_patch(loop_cells, "minecraft:overworld", RAILY,
                              shape_of={(x, z): "north_south", ...})
    print(report["gaps"], "patched")   # never silent — logs what it fixed

Stdlib + ``voxel.mcp_place`` only. The MCP ``call`` is injectable so the logic
is unit-testable without a server.
"""
from __future__ import annotations

import re

# block_scan_region caps at 65,536 cells of *volume*; a single Y-layer tile is
# (x_span * 1 * z_span), so keep x_span*z_span under this with headroom.
SCAN_VOLUME_CAP = 60000
RAIL_BLOCK_IDS = ("minecraft:rail", "minecraft:powered_rail")

_POS_RE = re.compile(r"x:\s*(-?\d+)\D+?y:\s*(-?\d+)\D+?z:\s*(-?\d+)")


# --------------------------------------------------------------------------- pure core

def find_gaps(intended, present):
    """Return the ``intended`` cells missing from ``present``, in intended order
    (de-duplicated). Cells are compared on their full tuple, so pass matching
    shapes — ``(x, z)`` against ``(x, z)``, or ``(x, y, z)`` against ``(x, y, z)``.

    This is the whole correctness idea: a placement is complete only when every
    intended cell is actually present; trust the world read, not the batch reply.
    """
    have = {tuple(c) for c in present}
    seen, gaps = set(), []
    for c in intended:
        t = tuple(c)
        if t in seen:
            continue
        seen.add(t)
        if t not in have:
            gaps.append(t)
    return gaps


def layer_tiles(x0, z0, x1, z1, cap=SCAN_VOLUME_CAP):
    """Yield ``(ax0, az0, ax1, az1)`` sub-rectangles covering ``[x0..x1] x
    [z0..z1]``, each with area <= ``cap`` so a single-Y ``block_scan_region``
    stays under the volume ceiling. Tiles partition the rectangle exactly."""
    x0, x1 = min(x0, x1), max(x0, x1)
    z0, z1 = min(z0, z1), max(z0, z1)
    xspan = x1 - x0 + 1
    if xspan <= cap:
        x_step, z_step = xspan, max(1, cap // xspan)
    else:
        x_step, z_step = cap, 1
    ax = x0
    while ax <= x1:
        bx = min(ax + x_step - 1, x1)
        az = z0
        while az <= z1:
            bz = min(az + z_step - 1, z1)
            yield (ax, az, bx, bz)
            az = bz + 1
        ax = bx + 1


def parse_positions(text):
    """Extract ``(x, z)`` pairs from a ``block_scan_region`` text reply."""
    return {(int(m.group(1)), int(m.group(3))) for m in _POS_RE.finditer(text or "")}


def _reply_text(reply):
    """Pull the text payload out of an MCP tool reply (result.content[0].text),
    tolerant of a bare string or a missing field."""
    if isinstance(reply, str):
        return reply
    if not isinstance(reply, dict):
        return ""
    res = reply.get("result", reply)
    if isinstance(res, dict):
        content = res.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                return first.get("text", "") or ""
            return str(first)
        return str(res.get("text", "") or "")
    return str(res or "")


# --------------------------------------------------------------------------- live wiring

def _default_call():
    from . import mcp_place
    mcp_place.handshake()
    return mcp_place.call


def scan_present(dimension, y, x0, z0, x1, z1, *, block_ids=RAIL_BLOCK_IDS,
                 call=None, cap=SCAN_VOLUME_CAP):
    """Scan the ``y`` layer over ``[x0..x1] x [z0..z1]`` for any of ``block_ids``
    and return the set of ``(x, z)`` present. Tiles under the scan-volume cap."""
    if call is None:
        call = _default_call()
    present = set()
    for (ax0, az0, ax1, az1) in layer_tiles(x0, z0, x1, z1, cap):
        for bid in block_ids:
            reply = call("block_scan_region", {
                "dimension": dimension, "match_block_id": bid, "limit": 65536,
                "box": {"from": {"x": ax0, "y": y, "z": az0},
                        "to": {"x": ax1, "y": y, "z": az1}}})
            present |= parse_positions(_reply_text(reply))
    return present


def verify_and_patch(intended_cells, dimension, y, *, shape_of=None,
                     block="minecraft:rail", scan_block_ids=RAIL_BLOCK_IDS,
                     call=None, margin=1):
    """Verify a 1-wide feature placed at world Y ``y`` and patch any dropped
    cells. ``intended_cells`` is the ``(x, z)`` cell list you meant to place;
    ``shape_of`` (optional) maps ``(x, z) -> rail shape`` for the patch
    blockstate. Returns ``{"intended", "present", "gaps", "patched"}`` — the
    ``gaps`` list is the cells that were missing (logged, never silent)."""
    if call is None:
        call = _default_call()
    cells = [tuple(c) for c in intended_cells]
    xs = [c[0] for c in cells]
    zs = [c[1] for c in cells]
    present = scan_present(dimension, y, min(xs) - margin, min(zs) - margin,
                           max(xs) + margin, max(zs) + margin,
                           block_ids=scan_block_ids, call=call)
    gaps = find_gaps(cells, present)
    patched = 0
    for (x, z) in gaps:
        spec = {"id": block}
        shape = (shape_of or {}).get((x, z))
        if shape:
            spec["properties"] = {"shape": shape}
        call("block_set_state", {"dimension": dimension,
                                 "position": {"x": x, "y": y, "z": z},
                                 "block": spec})
        patched += 1
    return {"intended": len(cells), "present": len(present),
            "gaps": gaps, "patched": patched}
