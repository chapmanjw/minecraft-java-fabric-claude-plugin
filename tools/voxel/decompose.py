"""Turn a voxel model into a small set of world-space box fills.

A 600k-voxel model placed one block at a time is hopeless; placed as a few
hundred greedy boxes it is one quick batch. ``decompose`` greedily grows
maximal axis-aligned boxes per block code, then ``split`` divides any box that
exceeds the per-fill cap along its longest axis.

Output (``to_fills``) is a list of fill dicts ready for the ``block_fill_batch``
MCP tool::

    {"from": [x, y, z], "to": [x, y, z], "block": "minecraft:cyan_concrete"}

Coordinates are absolute world coordinates: the model's local (x, y, z) plus an
``origin``. The default ``cap`` of 32000 keeps each box under the vanilla /fill
ceiling so the build is safe even against a server that has not yet adopted
auto-tiling.
"""

from __future__ import annotations

import json

import numpy as np

from .model import VoxelModel

DEFAULT_CAP = 32000


def _greedy_boxes(mask: np.ndarray) -> list[tuple]:
    """Greedy maximal-box cover of a boolean mask. Returns inclusive
    (x0,y0,z0,x1,y1,z1) tuples in local grid coordinates."""
    mask = mask.copy()
    nx, ny, nz = mask.shape
    flat = mask.reshape(-1)
    boxes: list[tuple] = []
    while True:
        i = int(np.argmax(flat))
        if not flat[i]:
            break
        x0, y0, z0 = np.unravel_index(i, mask.shape)
        # grow along z, then x, then y, keeping the box fully set
        z1 = z0
        while z1 + 1 < nz and mask[x0, y0, z1 + 1]:
            z1 += 1
        x1 = x0
        while x1 + 1 < nx and mask[x1 + 1, y0, z0:z1 + 1].all():
            x1 += 1
        y1 = y0
        while y1 + 1 < ny and mask[x0:x1 + 1, y1 + 1, z0:z1 + 1].all():
            y1 += 1
        boxes.append((int(x0), int(y0), int(z0), int(x1), int(y1), int(z1)))
        mask[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = False
    return boxes


def split(box: tuple, cap: int = DEFAULT_CAP) -> list[tuple]:
    """Recursively halve a box along its longest axis until volume ≤ cap."""
    x0, y0, z0, x1, y1, z1 = box
    vol = (x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1)
    if vol <= cap:
        return [box]
    dx, dy, dz = x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1
    if dx >= dy and dx >= dz:
        mid = (x0 + x1) // 2
        return split((x0, y0, z0, mid, y1, z1), cap) + split((mid + 1, y0, z0, x1, y1, z1), cap)
    if dy >= dz:
        mid = (y0 + y1) // 2
        return split((x0, y0, z0, x1, mid, z1), cap) + split((x0, mid + 1, z0, x1, y1, z1), cap)
    mid = (z0 + z1) // 2
    return split((x0, y0, z0, x1, y1, mid), cap) + split((x0, y0, mid + 1, x1, y1, z1), cap)


def decompose(model: VoxelModel, cap: int = DEFAULT_CAP) -> dict:
    """Return ``{code: [boxes...]}`` of capped local-coordinate boxes per code."""
    out: dict[int, list[tuple]] = {}
    for code in model.codes_present():
        mask = model.g == code
        boxes: list[tuple] = []
        for b in _greedy_boxes(mask):
            boxes.extend(split(b, cap))
        out[code] = boxes
    return out


def to_fills(model: VoxelModel, origin=(0, 0, 0), cap: int = DEFAULT_CAP) -> list[dict]:
    """World-space fill dicts for the whole model."""
    ox, oy, oz = origin
    fills: list[dict] = []
    for code, boxes in decompose(model, cap).items():
        block_id = model.pal.block_id(code)
        for (x0, y0, z0, x1, y1, z1) in boxes:
            fills.append({
                "from": [ox + x0, oy + y0, oz + z0],
                "to":   [ox + x1, oy + y1, oz + z1],
                "block": block_id,
            })
    return fills


def write_fills_json(model: VoxelModel, path: str, origin=(0, 0, 0),
                     cap: int = DEFAULT_CAP) -> dict:
    """Write the fills list and return a summary (counts per block, totals)."""
    fills = to_fills(model, origin, cap)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fills, fh)
    per: dict[str, int] = {}
    for f in fills:
        per[f["block"]] = per.get(f["block"], 0) + 1
    nx, ny, nz = model.shape
    return {
        "fills": len(fills),
        "solid_voxels": model.solid_count(),
        "per_block": dict(sorted(per.items(), key=lambda kv: -kv[1])),
        "bbox": {"from": list(origin),
                 "to": [origin[0] + nx - 1, origin[1] + ny - 1, origin[2] + nz - 1]},
    }
