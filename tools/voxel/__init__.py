"""Voxel authoring + render-verify toolkit for the minecraft-builder workflow.

Author a form as a parametric numpy model, render it to PNGs you can actually
look at, iterate against references, then decompose it into world fills placed
in one batch. See ``tools/README.md``.

    from voxel import Palette, VoxelModel, render_views, write_fills_json
"""

from .palette import Palette, Entry, AIR
from .model import VoxelModel
from .render import render_views, render_iso, render_ortho
from .decompose import decompose, to_fills, write_fills_json, split, DEFAULT_CAP

__all__ = [
    "Palette", "Entry", "AIR",
    "VoxelModel",
    "render_views", "render_iso", "render_ortho",
    "decompose", "to_fills", "write_fills_json", "split", "DEFAULT_CAP",
]
