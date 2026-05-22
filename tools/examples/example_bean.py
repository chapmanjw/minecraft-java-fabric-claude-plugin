"""Worked example: a small mascot "bean" figure — body, head, two feet, eyes.

This is the pattern the monument-builder skill follows for any voxel/parametric
art: build a VoxelModel from primitives, render three views to compare against
references, then decompose to a fills list for placement. Run it directly:

    python tools/examples/example_bean.py

It writes renders + a fills JSON next to itself and prints a summary. It also
serves as the toolkit's smoke test.
"""

import os
import sys

# Make the bundled `voxel` package importable regardless of cwd. In a skill,
# inject ${CLAUDE_PLUGIN_ROOT}/tools here instead of walking up from __file__.
TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

from voxel import Palette, VoxelModel, render_views, write_fills_json  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))


def build() -> VoxelModel:
    pal = Palette.building()
    GREEN = pal.code("lime_concrete")
    DARK = pal.code("green_concrete")
    WHITE = pal.code("white_concrete")
    BLACK = pal.code("black_concrete")

    m = VoxelModel(nx=28, ny=44, nz=24, palette=pal)

    # body: a tall rounded bean (ellipsoid), widest at ~35% height
    m.ellipsoid(center=(m.fx(0.5), m.fy(0.40), m.fz(0.5)),
                radii=(11, 17, 9), code=GREEN)
    # belly highlight (a lighter front patch) — a shallow ellipsoid pushed forward
    m.ellipsoid(center=(m.fx(0.5), m.fy(0.38), m.fz(0.78)),
                radii=(6, 9, 4), code=WHITE)
    # head: smaller sphere sitting on top
    m.ellipsoid(center=(m.fx(0.5), m.fy(0.82), m.fz(0.5)),
                radii=(8, 8, 8), code=GREEN)
    # feet: two stubby cylinders at the base
    m.cylinder(axis="y", span=(m.fy(0.0), m.fy(0.08)),
               center2d=(m.fx(0.36), m.fz(0.5)), radius=3.5, code=DARK)
    m.cylinder(axis="y", span=(m.fy(0.0), m.fy(0.08)),
               center2d=(m.fx(0.64), m.fz(0.5)), radius=3.5, code=DARK)
    # eyes: two dark insets on the front of the head
    for ex in (0.40, 0.60):
        m.ellipsoid(center=(m.fx(ex), m.fy(0.84), m.fz(0.92)),
                    radii=(1.6, 2.4, 1.6), code=BLACK)
    return m


def main() -> int:
    m = build()
    views = render_views(m, os.path.join(OUT, "bean"))
    summary = write_fills_json(m, os.path.join(OUT, "bean_fills.json"),
                               origin=(0, 64, 0))
    print("rendered:", *(os.path.basename(v) for v in views))
    print("solid voxels:", summary["solid_voxels"])
    print("fills:", summary["fills"])
    for block, n in summary["per_block"].items():
        print(f"  {n:4d}  {block}")
    print("bbox:", summary["bbox"])
    # sanity: the model must have mass and decompose to a sane number of boxes
    assert summary["solid_voxels"] > 1000, "model is suspiciously empty"
    assert 0 < summary["fills"] < summary["solid_voxels"], "decomposition looks wrong"
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
