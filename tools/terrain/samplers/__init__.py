"""Composable noise-sampler graph for terrain authoring.

This is Pillar 1 of the terrain redesign (see ``Design/01-terrain-core.md``):
terrain shape is authored as a **declarative graph of small numpy-vectorised
sampler nodes** rather than a fixed chain of imperative ``HeightField`` calls.
The graph is the saved, diffable *recipe* — re-sculpting re-evaluates one node
instead of rebuilding from scratch (the cure for re-sculpt detail loss).

Every node implements ``Sampler.eval(ctx) -> ndarray`` over the whole grid and
``to_spec() -> dict`` for serialisation. ``from_spec`` rebuilds a node tree from
a dict/JSON recipe. Nodes mirror the Terra / TerraForged vocabulary:

  sources    OpenSimplex2S, Perlin, Value, Cellular, Constant, WhiteNoise
  fractal    FBM, Ridged (full Musgrave), Billow, Hybrid, Hetero
  warp       DomainWarp (2-vector, single + recursive)
  mutators   Scale, Bias, Clamp, Linear, CubicSpline, Posterize, Terrace
  arithmetic Add, Sub, Mul, Div, Min, Max, Blend, Select
  geometry   Distance (radial falloff), Image (DEM), BeltCoord

All evaluation is numpy over the (nx, nz) grid, so this is *cheaper* offline
than a per-voxel generator.
"""
from __future__ import annotations

from .base import Sampler, EvalContext, register, from_spec, NODE_TYPES
from . import sources, fractal, warp, mutators, arithmetic, geometry  # noqa: F401  (register nodes)

__all__ = ["Sampler", "EvalContext", "register", "from_spec", "NODE_TYPES"]
