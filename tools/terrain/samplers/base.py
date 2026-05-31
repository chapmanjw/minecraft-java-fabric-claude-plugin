"""Sampler base class, evaluation context, and the node registry / loader."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class EvalContext:
    """Everything a sampler needs to evaluate over the grid.

    ``X``/``Z`` are ``(nx, nz)`` float meshgrids of world-relative cell
    coordinates (index space; the materialiser adds the world origin). ``s`` and
    ``perp`` are the optional belt arc-length / signed-perpendicular fields, set
    when a recipe is evaluated along a ``Centerline`` so ``BeltCoord`` nodes can
    read them.
    """

    X: np.ndarray
    Z: np.ndarray
    seed: int = 0
    s: Optional[np.ndarray] = None
    perp: Optional[np.ndarray] = None

    @classmethod
    def grid(cls, nx: int, nz: int, seed: int = 0) -> "EvalContext":
        X, Z = np.meshgrid(np.arange(nx, dtype=float),
                           np.arange(nz, dtype=float), indexing="ij")
        return cls(X=X, Z=Z, seed=seed)

    @property
    def shape(self) -> tuple:
        return self.X.shape


class Sampler:
    """Base class for all graph nodes. Subclasses set ``TYPE`` and implement
    ``eval``; ``to_spec``/``_from_spec`` handle (de)serialisation."""

    TYPE: str = "sampler"

    def eval(self, ctx: EvalContext) -> np.ndarray:  # pragma: no cover - abstract
        raise NotImplementedError

    # -- serialisation ----------------------------------------------------
    def to_spec(self) -> dict:
        """Default: emit every public attribute that is a scalar/str/list, and
        recurse into child samplers. Subclasses override only when they need
        custom handling."""
        spec: dict = {"type": self.TYPE}
        for k, v in vars(self).items():
            if k.startswith("_"):
                continue
            spec[k] = _spec_value(v)
        return spec

    @classmethod
    def _from_spec(cls, spec: dict) -> "Sampler":
        kwargs = {k: _build_value(v) for k, v in spec.items() if k != "type"}
        return cls(**kwargs)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<{self.TYPE}>"


def _spec_value(v):
    if isinstance(v, Sampler):
        return v.to_spec()
    if isinstance(v, (list, tuple)):
        return [_spec_value(x) for x in v]
    if isinstance(v, np.generic):
        return v.item()
    return v


def _build_value(v):
    if isinstance(v, dict) and "type" in v:
        return from_spec(v)
    if isinstance(v, list):
        return [_build_value(x) for x in v]
    return v


# -- registry -------------------------------------------------------------
NODE_TYPES: dict = {}


def register(klass):
    """Class decorator: register a Sampler subclass by its ``TYPE``."""
    NODE_TYPES[klass.TYPE] = klass
    return klass


def from_spec(spec) -> Sampler:
    """Rebuild a sampler (sub)tree from a dict spec or a bare scalar.

    A bare ``int``/``float`` is sugar for a ``Constant`` node, so recipes can
    write ``{"type": "Add", "a": {...}, "b": 64}``.
    """
    if isinstance(spec, Sampler):
        return spec
    if isinstance(spec, (int, float)):
        return NODE_TYPES["Constant"](value=float(spec))
    if not isinstance(spec, dict) or "type" not in spec:
        raise ValueError(f"not a sampler spec: {spec!r}")
    t = spec["type"]
    if t not in NODE_TYPES:
        raise KeyError(f"unknown sampler type {t!r}; known: {sorted(NODE_TYPES)}")
    return NODE_TYPES[t]._from_spec(spec)
