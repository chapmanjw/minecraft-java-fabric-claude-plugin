"""Climate-driven biome assignment with blended heights — Pillar 6.

We can't inject worldgen biomes, but we can assign vanilla biome IDs offline
from climate proxies and paint them with ``level_fill_biome``. The model is the
industry-standard low-dimensional climate space (Whittaker temperature×moisture,
extended with continentalness and an erosion/slope proxy), decoupled from height.

The seam fix lives here too: where a build spans several biomes with different
base heights, blend the per-biome height fields (see ``terrain.blend``) so the
boundary is a ramp, and jitter the label boundary so it is wavy, not straight.

Outputs:
  assign()            → object array of vanilla biome ids per cell
  to_biome_fill_plan()→ list of {from,to,biome} rectangles for level_fill_biome
  palette_for()       → a MaterialSpec surface mix matching a biome (co-planned
                        so the painted tint and the placed ground block agree)
"""
from __future__ import annotations

import numpy as np

from . import masks as M


# A compact Whittaker-style table over (temperature, moisture), each in [-1, 1].
# Picked for vanilla biome ids that read distinctly at distance.
def _classify(t: float, m: float, cont: float, ero: float, height: float,
              sea: float) -> str:
    if height < sea - 6:
        return "minecraft:ocean" if cont < 0.2 else "minecraft:deep_ocean"
    if height < sea + 2:
        return "minecraft:beach"
    if t < -0.45:
        if m > 0.2:
            return "minecraft:snowy_taiga"
        return "minecraft:snowy_plains"
    if t < -0.1:
        if m > 0.3:
            return "minecraft:taiga"
        if m > 0.0:
            return "minecraft:old_growth_spruce_taiga"
        return "minecraft:plains"
    if t > 0.55:
        if m > 0.3:
            return "minecraft:jungle"
        if m > -0.1:
            return "minecraft:savanna"
        return "minecraft:desert"
    # temperate
    if m > 0.4:
        return "minecraft:dark_forest"
    if m > 0.1:
        return "minecraft:forest"
    if m > -0.2:
        return "minecraft:birch_forest"
    return "minecraft:plains"


# Per-biome surface palette + a couple of feature ids, co-planned so tint matches
# ground. Used by palette_for() and the scatter pass.
BIOME_CONTENT = {
    "minecraft:plains": dict(surface={"minecraft:grass_block": 0.92, "minecraft:coarse_dirt": 0.08},
                             features=["minecraft:oak", "minecraft:flower_plains"], density=0.10),
    "minecraft:forest": dict(surface={"minecraft:grass_block": 0.85, "minecraft:podzol": 0.1, "minecraft:moss_block": 0.05},
                             features=["minecraft:oak", "minecraft:birch", "minecraft:fancy_oak"], density=0.55),
    "minecraft:birch_forest": dict(surface={"minecraft:grass_block": 0.9, "minecraft:coarse_dirt": 0.1},
                                   features=["minecraft:birch", "minecraft:birch_tall"], density=0.5),
    "minecraft:dark_forest": dict(surface={"minecraft:grass_block": 0.8, "minecraft:podzol": 0.2},
                                  features=["minecraft:dark_oak", "minecraft:huge_brown_mushroom"], density=0.7),
    "minecraft:taiga": dict(surface={"minecraft:grass_block": 0.8, "minecraft:podzol": 0.2},
                            features=["minecraft:spruce", "minecraft:pine"], density=0.55),
    "minecraft:old_growth_spruce_taiga": dict(surface={"minecraft:podzol": 0.7, "minecraft:grass_block": 0.3},
                                              features=["minecraft:mega_spruce", "minecraft:spruce"], density=0.5),
    "minecraft:snowy_taiga": dict(surface={"minecraft:snow_block": 0.5, "minecraft:grass_block": 0.5},
                                  features=["minecraft:spruce"], density=0.4),
    "minecraft:snowy_plains": dict(surface={"minecraft:snow_block": 0.85, "minecraft:powder_snow": 0.15},
                                   features=["minecraft:spruce"], density=0.05),
    "minecraft:savanna": dict(surface={"minecraft:grass_block": 0.9, "minecraft:coarse_dirt": 0.1},
                              features=["minecraft:acacia"], density=0.12),
    "minecraft:desert": dict(surface={"minecraft:sand": 0.97, "minecraft:sandstone": 0.03},
                             features=["minecraft:desert_well"], density=0.01),
    "minecraft:jungle": dict(surface={"minecraft:grass_block": 0.8, "minecraft:podzol": 0.15, "minecraft:moss_block": 0.05},
                             features=["minecraft:jungle_tree", "minecraft:mega_jungle_tree", "minecraft:fancy_oak"], density=0.8),
    "minecraft:beach": dict(surface={"minecraft:sand": 0.85, "minecraft:gravel": 0.15},
                            features=[], density=0.0),
    "minecraft:ocean": dict(surface={"minecraft:gravel": 0.6, "minecraft:sand": 0.4},
                            features=["minecraft:seagrass_mid", "minecraft:kelp"], density=0.2),
    "minecraft:deep_ocean": dict(surface={"minecraft:gravel": 0.7, "minecraft:clay": 0.3},
                                 features=["minecraft:kelp"], density=0.1),
}


class BiomeField:
    """Climate proxies → biome labels (+ boundary jitter), over a HeightField."""

    def __init__(self, hf, *, seed: int = 0, latitude: float = 0.0,
                 temp_freq: float = 0.004, moist_freq: float = 0.005):
        self.hf = hf
        self.seed = int(seed)
        self.latitude = float(latitude)
        self.temp_freq = float(temp_freq)
        self.moist_freq = float(moist_freq)
        self._labels = None

    def climate(self) -> dict:
        from .samplers import from_spec, EvalContext
        nx, nz = self.hf.nx, self.hf.nz
        ctx = EvalContext.grid(nx, nz, seed=self.seed)
        temp = from_spec({"type": "FBM", "frequency": self.temp_freq,
                          "octaves": 3, "seed": 1}).eval(ctx)
        # latitude + elevation lapse: higher + farther = colder
        land_hi = max(float(self.hf.h.max()), self.hf.sea_level + 1)
        elev = np.clip((self.hf.h - self.hf.sea_level) /
                       (land_hi - self.hf.sea_level), 0, 1)
        temp = temp - 1.1 * elev - self.latitude
        moist = from_spec({"type": "FBM", "frequency": self.moist_freq,
                           "octaves": 3, "seed": 2}).eval(ctx)
        # wetter near water
        dw = M.dist_to_water(self.hf.h, self.hf.sea_level)
        moist = moist + np.exp(-dw / 24.0) * 0.6
        cont = np.tanh((self.hf.h - self.hf.sea_level) / 24.0)
        ero = np.tanh(-M.slope_deg(self.hf.h) / 30.0)
        return dict(temperature=np.clip(temp, -1, 1), moisture=np.clip(moist, -1, 1),
                    continentalness=cont, erosion=ero)

    def assign(self, *, boundary_jitter: float = 4.0) -> np.ndarray:
        if self._labels is not None:
            return self._labels
        c = self.climate()
        nx, nz = self.hf.nx, self.hf.nz
        # jitter the sampling coords so biome borders are wavy, not gridlined
        labels = np.empty((nx, nz), dtype=object)
        h = self.hf.h
        t, m, cont, ero = (c["temperature"], c["moisture"],
                           c["continentalness"], c["erosion"])
        if boundary_jitter > 0:
            from .noise import ValueNoise2D
            X, Z = np.meshgrid(np.arange(nx, dtype=float),
                               np.arange(nz, dtype=float), indexing="ij")
            jx = (ValueNoise2D(self.seed + 31).sample(X * 0.05, Z * 0.05) - 0.5) * 2 * boundary_jitter
            jm = (ValueNoise2D(self.seed + 37).sample(X * 0.05, Z * 0.05) - 0.5) * 0.15
            t = np.clip(t + jx * 0.01, -1, 1)
            m = np.clip(m + jm, -1, 1)
        sea = self.hf.sea_level
        for x in range(nx):
            for z in range(nz):
                labels[x, z] = _classify(float(t[x, z]), float(m[x, z]),
                                         float(cont[x, z]), float(ero[x, z]),
                                         float(h[x, z]), sea)
        self._labels = labels
        return labels

    def to_biome_fill_plan(self, origin=(0, 0), *, quant: int = 4) -> list:
        """Greedy-rectangle cover of the label grid (downsampled to ``quant``-block
        cells — MC's biome resolution) → ``level_fill_biome`` calls. Each entry is
        {from:[x,y,z], to:[x,y,z], biome}. Y spans the column range loosely; the
        tool paints the whole column."""
        labels = self.assign()
        nx, nz = self.hf.nx, self.hf.nz
        ox, oz = origin
        y0 = int(self.hf.h.min()) - 8
        y1 = int(self.hf.h.max()) + 4
        # simple row-run greedy merge at quant resolution
        plan = []
        covered = np.zeros((nx, nz), dtype=bool)
        for x in range(0, nx, quant):
            z = 0
            while z < nz:
                if covered[x, z]:
                    z += 1
                    continue
                bid = labels[x, z]
                z2 = z
                while z2 + quant < nz and labels[x, min(z2 + quant, nz - 1)] == bid:
                    z2 += quant
                plan.append({"from": [ox + x, y0, oz + z],
                             "to": [ox + min(x + quant - 1, nx - 1), y1,
                                    oz + min(z2 + quant - 1, nz - 1)],
                             "biome": bid})
                covered[x:x + quant, z:z2 + quant] = True
                z = z2 + quant
        return plan

    def palette_for(self, biome_id: str):
        """A MaterialSpec surface mix for a biome (co-planned tint↔ground)."""
        return BIOME_CONTENT.get(biome_id, BIOME_CONTENT["minecraft:plains"])["surface"]
