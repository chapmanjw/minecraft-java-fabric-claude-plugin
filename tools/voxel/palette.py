"""Block palette: maps small integer voxel codes to a Minecraft block id and an
approximate RGB so the same model can be (a) rendered to PNG for visual review
and (b) decomposed into world fills.

A model's numpy grid holds ``uint8`` codes; ``0`` is always air. A ``Palette``
resolves each code to its block id (for placement) and its RGB (for rendering).
The RGBs are deliberately approximate — they exist so the *silhouette and the
material regions* read correctly in a render, not to colour-match Minecraft.

Typical use while authoring a model::

    from voxel import Palette
    pal = Palette()
    CYAN  = pal.add("minecraft:cyan_concrete",        (21, 119, 136))
    GLASS = pal.add("minecraft:light_blue_stained_glass", (140, 190, 220))
    # ... write CYAN / GLASS into the grid ...

Or start from the built-in building palette and look codes up by name::

    pal = Palette.building()
    body = pal.code("cyan_concrete")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Entry:
    name: str           # short key, e.g. "cyan_concrete"
    block_id: str       # full id, e.g. "minecraft:cyan_concrete"
    rgb: Optional[tuple] # (r, g, b) 0..255, or None for air / invisible


AIR = Entry("air", "minecraft:air", None)


class Palette:
    """A registry of voxel codes. Code 0 is always air."""

    def __init__(self) -> None:
        self._by_code: dict[int, Entry] = {0: AIR}
        self._by_name: dict[str, int] = {"air": 0}
        self._next = 1

    # -- building the palette ------------------------------------------------

    def add(self, block_id: str, rgb: Optional[tuple], name: Optional[str] = None) -> int:
        """Register a block and return its integer code. If a short ``name`` is
        omitted it is derived from the block id (namespace stripped)."""
        if name is None:
            name = block_id.split(":", 1)[-1]
        if name in self._by_name:                 # idempotent: re-adding a name
            code = self._by_name[name]
            self._by_code[code] = Entry(name, block_id, tuple(rgb) if rgb else None)
            return code
        if self._next > 255:
            raise ValueError("palette is full (max 255 non-air codes)")
        code = self._next
        self._next += 1
        self._by_code[code] = Entry(name, block_id, tuple(rgb) if rgb else None)
        self._by_name[name] = code
        return code

    # -- lookups -------------------------------------------------------------

    def code(self, name: str) -> int:
        return self._by_name[name]

    def entry(self, code: int) -> Entry:
        return self._by_code[code]

    def block_id(self, code: int) -> str:
        return self._by_code[code].block_id

    def rgb(self, code: int) -> Optional[tuple]:
        return self._by_code[code].rgb

    def codes(self) -> list[int]:
        return [c for c in self._by_code if c != 0]

    # -- persistence ---------------------------------------------------------

    def to_json(self, path: str) -> None:
        data = {str(c): [e.name, e.block_id, e.rgb] for c, e in self._by_code.items()}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "Palette":
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        pal = cls()
        pal._by_code, pal._by_name = {}, {}
        maxc = 0
        for c_str, (name, block_id, rgb) in data.items():
            c = int(c_str)
            pal._by_code[c] = Entry(name, block_id, tuple(rgb) if rgb else None)
            pal._by_name[name] = c
            maxc = max(maxc, c)
        pal._next = maxc + 1
        return pal

    # -- a ready-made building palette --------------------------------------

    @classmethod
    def building(cls) -> "Palette":
        """A broad starter palette covering the blocks most builds reach for:
        the 16 concretes, common stone/wood, glass, glow, metals, and the
        copper oxidation series. Add more with ``add`` as a build needs them."""
        p = cls()
        a = p.add
        # 16 concretes (the workhorse for vehicles, monuments, signage)
        a("minecraft:white_concrete",      (207, 213, 214))
        a("minecraft:orange_concrete",     (224,  97,   1))
        a("minecraft:magenta_concrete",    (169,  48, 159))
        a("minecraft:light_blue_concrete", ( 35, 137, 198))
        a("minecraft:yellow_concrete",     (240, 175,  21))
        a("minecraft:lime_concrete",       ( 94, 168,  24))
        a("minecraft:pink_concrete",       (213, 101, 142))
        a("minecraft:gray_concrete",       ( 54,  57,  61))
        a("minecraft:light_gray_concrete", (125, 125, 115))
        a("minecraft:cyan_concrete",       ( 21, 119, 136))
        a("minecraft:purple_concrete",     (100,  32, 156))
        a("minecraft:blue_concrete",       ( 44,  46, 143))
        a("minecraft:brown_concrete",      ( 96,  60,  32))
        a("minecraft:green_concrete",      ( 73,  91,  36))
        a("minecraft:red_concrete",        (142,  33,  33))
        a("minecraft:black_concrete",      (  8,  10,  15))
        # stone family
        a("minecraft:stone",               (125, 125, 125))
        a("minecraft:cobblestone",         (127, 127, 127))
        a("minecraft:deepslate",           ( 77,  77,  80))
        a("minecraft:andesite",            (132, 134, 133))
        a("minecraft:smooth_stone",        (158, 158, 158))
        a("minecraft:blackstone",          ( 42,  37,  43))
        a("minecraft:quartz_block",        (235, 229, 222))
        a("minecraft:sandstone",           (219, 207, 163))
        a("minecraft:terracotta",          (152,  94,  67))
        # wood planks
        a("minecraft:oak_planks",          (162, 131,  79))
        a("minecraft:spruce_planks",       (114,  84,  48))
        a("minecraft:birch_planks",        (196, 179, 123))
        a("minecraft:dark_oak_planks",     ( 66,  43,  20))
        # glass (rendered opaque-ish; for silhouette reading only)
        a("minecraft:glass",                       (200, 225, 235))
        a("minecraft:light_blue_stained_glass",    (140, 190, 220))
        a("minecraft:gray_stained_glass",          ( 90, 100, 110))
        a("minecraft:black_stained_glass",         ( 30,  32,  38))
        # light sources / accents
        a("minecraft:sea_lantern",         (220, 235, 225))
        a("minecraft:glowstone",           (215, 180, 110))
        a("minecraft:gold_block",          (246, 208,  61))
        a("minecraft:iron_block",          (220, 220, 222))
        a("minecraft:redstone_block",      (175,  25,  18))
        # copper oxidation series
        a("minecraft:copper_block",            (192, 107,  79))
        a("minecraft:exposed_copper",          (161, 124, 103))
        a("minecraft:weathered_copper",        (108, 135, 114))
        a("minecraft:oxidized_copper",         ( 82, 138, 114))
        return p
