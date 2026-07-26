"""Live MCP integration-test harness for the minecraft-java mod.

Exercises every registered MCP tool against the *running* world and asserts it
behaves, so iterating on the mod (or the plugin) can't silently break a tool and
a change is confirmed to actually work. Built on the same ``builder.mcpclient``
transport the build harness uses.

Tests the LIVE tool surface only. After the 26.x tool-categorization redesign an
unconfigured mod registers a lean default of ~104 of the mod's 194 tools (188 of
which are world tools this suite can reach; the other 7 are client-only): the
default-ON domains (blocks, structures, world, entities, items, scripting,
server) up to write access. The rest — the opt-in domains (players,
gameplay, registries) plus the admin-access tools in any domain — are NOT live
by default, so their cases report SKIP "not live (…)", which is expected, not a
regression. To exercise the full 183, configure the mod with every category
included and ``maxAccess=admin`` (see tools/itest/README.md), restart, and re-run.

Design / safety:
  * All world writes happen inside a small **force-loaded scratch sandbox** far
    from any build (``SCRATCH_*`` below). The sandbox is cleared to air at the
    start and end of a run; cleanup runs even on failure.
  * Each test declares a safety ``level``:
      - "safe"        read-only, or confined to the scratch sandbox.
      - "global"      mutates world-global state (time/weather/border/…) — the
                      test MUST save the old value and restore it.
      - "destructive" irreversible or session-affecting (kick a player, reload,
                      explosions near spawn, …) — SKIPPED unless --destructive.
  * Coverage: after running, every *live* tool with no registered case is
    reported as UNCOVERED, so the suite tracks the full surface (no silent gaps).

Usage:
  cd tools && python -m itest.run                 # run the whole suite
  cd tools && python -m itest.run --destructive   # also run destructive cases
  cd tools && python -m itest.run --only block    # one category (name prefix)
  cd tools && python -m itest.run --baseline out.toon   # write a baseline report

Stdlib only (uses builder.mcpclient / builder.toon).
"""
from __future__ import annotations

import re

import os
import sys
import time
import traceback
from dataclasses import dataclass, field

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from builder.mcpclient import McpClient, McpError
else:
    from builder.mcpclient import McpClient, McpError

# --- scratch sandbox: a remote, unused region; force-loaded + cleared per run ---
SCRATCH_DIM = "minecraft:overworld"
SCRATCH_X0, SCRATCH_Z0 = 20000, 20000        # NW corner (far from any build)
SCRATCH_W, SCRATCH_L = 64, 64                 # 64x64 columns = 16 chunks (< 256 cap)
SCRATCH_Y0, SCRATCH_Y1 = 90, 124              # working Y band
SCRATCH_FILL_FLOOR_Y = 89                     # a stone floor under the sandbox


class Skip(Exception):
    """Raise inside a test to SKIP it with a reason (e.g. precondition absent)."""


@dataclass
class Result:
    tool: str
    category: str
    level: str
    status: str          # PASS | FAIL | SKIP | ERROR
    detail: str = ""


# tool name -> {"fn", "level", "category"}
CASES: dict = {}


# --- 26.x tool-categorization spec (used only to explain why a tool is not live) ---
# Domain wireName <- the tool-name prefixes that belong to it. Longest prefixes
# first so "block_entity" wins over "block" and "player_screen" over "player".
_DOMAIN_BY_PREFIX = [
    ("block_entity", "blocks"),
    ("block", "blocks"),
    ("structure", "structures"),
    ("level", "world"),
    ("worldborder", "world"),
    ("entity", "entities"),
    ("player_screen", "players"),
    ("player", "players"),
    ("inventory", "items"),
    ("itemstack", "items"),
    ("item_modify", "items"),
    ("scoreboard", "gameplay"),
    ("bossbar", "gameplay"),
    ("advancement", "gameplay"),
    ("command", "scripting"),
    ("function", "scripting"),
    ("schedule", "scripting"),
    ("events", "scripting"),
    ("data_storage", "scripting"),
    ("data_attachment", "scripting"),
    ("recipe", "registries"),
    ("loot_table", "registries"),
    ("tag", "registries"),
    ("content_registry", "registries"),
    ("resource_loader", "registries"),
    ("resource_condition", "registries"),
    ("fluid_storage", "registries"),
    ("server", "server"),
    ("datapack", "server"),
]

# Domains the operator must opt into (enabledByDefault=false). Their cases SKIP
# under the lean default until enabled via mod config.
_OPT_IN_DOMAINS = {"players", "gameplay", "registries"}

# Tools tagged admin (admin access is opt-in; default maxAccess=write). These
# stay not-live by default even in an enabled-by-default domain.
_ADMIN_TOOLS = {
    "worldborder_set_size", "worldborder_add_size", "worldborder_set_center",
    "worldborder_set_warning_blocks", "worldborder_set_warning_time",
    "worldborder_set_damage_amount", "worldborder_set_damage_buffer",
    "level_set_difficulty", "level_set_game_rule", "level_create_explosion",
    "command_register", "server_reload_resources",
    "datapack_enable", "datapack_disable", "player_kick",
}


def _domain_for(tool: str) -> str:
    """The wireName domain a tool belongs to, by longest-prefix match (or '?')."""
    for prefix, domain in _DOMAIN_BY_PREFIX:
        if tool == prefix or tool.startswith(prefix + "_"):
            return domain
    return "?"


# Populated from the server log when one is supplied — see load_server_skip_log().
# Maps tool name -> the server's own reason for skipping it.
_SERVER_SKIP_REASONS: dict[str, str] = {}

# "Skipping tool 'x': required module 'y' is not installed" and its version-range sibling.
_SKIP_LINE = re.compile(r"Skipping tool '([^']+)': (.+?)\s*$")


def load_server_skip_log(path) -> int:
    """Read the server log and record why IT says each tool was skipped.

    The categorization tables below can only guess. They cannot see the third
    reason a tool goes missing — a `requiredFabricModules` entry that is not
    loaded — so a module-filtered tool used to be reported as merely "absent
    from this server build". That is exactly how five tools stayed dead across
    every Minecraft version without anyone noticing: they required
    fabric-screen-handler-api-v1 and fabric-resource-loader-v0, neither of which
    Fabric API ships, and nothing in the harness could say so.

    The server already logs the authoritative reason per skipped tool. Reading it
    turns a guess into a fact. Returns how many reasons were loaded; 0 is fine and
    simply means the harness falls back to its static inference.
    """
    _SERVER_SKIP_REASONS.clear()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = _SKIP_LINE.search(line)
                if m:
                    _SERVER_SKIP_REASONS[m.group(1)] = m.group(2).strip()
    except OSError:
        return 0
    return len(_SERVER_SKIP_REASONS)


def not_live_reason(tool: str) -> str:
    """Explain why a registered tool is not in the live surface.

    Three independent causes look identical from the client: an opt-in domain,
    an admin access tag, or an unmet `requiredFabricModules` / version
    constraint. Only the server knows which applies, so prefer its log when one
    was supplied and fall back to inference otherwise.
    """
    # The server's own words win — it is the only source that can distinguish a
    # module or version filter from a category opt-out.
    server_said = _SERVER_SKIP_REASONS.get(tool)
    if server_said:
        return f"not live (server: {server_said})"

    domain = _domain_for(tool)
    is_admin = tool in _ADMIN_TOOLS
    is_opt_in = domain in _OPT_IN_DOMAINS
    causes = []
    if is_opt_in:
        causes.append(f"opt-in domain {domain!r}")
    if is_admin:
        causes.append("admin access")
    if causes:
        why = " + ".join(causes)
        return f"not live ({why}) — enable via mod config to test"
    # An ON-domain, non-admin tool that is still missing. Without a server log we
    # cannot tell an unmet module/version constraint from a genuinely older build,
    # so say so rather than asserting the wrong one.
    return (f"not live (domain {domain!r} is on by default and access<=write) — "
            "cause undetermined: could be an unmet requiredFabricModules or "
            "version constraint, or a build predating the tool. Pass "
            "--server-log to read the server's own reason")


def case(tool: str, level: str = "safe"):
    """Register a test for a tool. The function receives a Ctx and asserts."""
    def deco(fn):
        CASES[tool] = {"fn": fn, "level": level, "category": tool.split("_")[0]}
        return fn
    return deco


class Ctx:
    """The per-test context: a connected client + scratch-sandbox allocators."""

    def __init__(self, client: McpClient):
        self.client = client
        self.dim = SCRATCH_DIM
        self._cx = SCRATCH_X0          # cursor for pos()/box() allocation
        self._cz = SCRATCH_Z0
        self._cy = SCRATCH_Y0

    # -- tool calls --------------------------------------------------------
    def call(self, tool, args=None):
        return self.client.call_toon(tool, args or {})

    def call_text(self, tool, args=None):
        return self.client.call_text(tool, args or {})

    def command(self, cmd):
        return self.client.command(cmd)

    # -- assertions --------------------------------------------------------
    @staticmethod
    def expect(cond, msg):
        if not cond:
            raise AssertionError(msg)

    @staticmethod
    def expect_field(data, key, msg=None):
        if not (isinstance(data, dict) and key in data):
            raise AssertionError(msg or f"response missing field {key!r}: {str(data)[:160]}")
        return data[key]

    # -- scratch allocation ------------------------------------------------
    def pos(self):
        """A fresh, unique (x,y,z) in the sandbox."""
        x, y, z = self._cx, self._cy, self._cz
        self._cx += 2
        if self._cx >= SCRATCH_X0 + SCRATCH_W:
            self._cx = SCRATCH_X0
            self._cz += 2
            if self._cz >= SCRATCH_Z0 + SCRATCH_L:
                self._cz = SCRATCH_Z0
                self._cy += 2
        return (x, y, z)

    def box(self, dx=3, dy=3, dz=3):
        """A fresh small box ((x,y,z),(x2,y2,z2)) in the sandbox."""
        x, y, z = self.pos()
        return (x, y, z), (x + dx, y + dy, z + dz)

    @staticmethod
    def pos_obj(p):
        return {"x": p[0], "y": p[1], "z": p[2]}

    @staticmethod
    def box_obj(a, b):
        return {"from": {"x": a[0], "y": a[1], "z": a[2]},
                "to": {"x": b[0], "y": b[1], "z": b[2]}}


# ---------------------------------------------------------------------------
# sandbox lifecycle
# ---------------------------------------------------------------------------

def _forceload(client, action):
    x1, z1 = SCRATCH_X0 - 1, SCRATCH_Z0 - 1
    x2, z2 = SCRATCH_X0 + SCRATCH_W, SCRATCH_Z0 + SCRATCH_L
    client.command(f"forceload {action} {x1} {z1} {x2} {z2}")


def _clear_sandbox(client):
    """Air out the working band and lay a stone floor — a clean, known slate."""
    a = {"x": SCRATCH_X0, "y": SCRATCH_Y0 - 1, "z": SCRATCH_Z0}
    b = {"x": SCRATCH_X0 + SCRATCH_W - 1, "y": SCRATCH_Y1, "z": SCRATCH_Z0 + SCRATCH_L - 1}
    client.call_text("block_fill_region",
                     {"dimension": SCRATCH_DIM, "box": {"from": a, "to": b}, "block": {"id": "minecraft:air"}})
    floor_a = {"x": SCRATCH_X0, "y": SCRATCH_FILL_FLOOR_Y, "z": SCRATCH_Z0}
    floor_b = {"x": SCRATCH_X0 + SCRATCH_W - 1, "y": SCRATCH_FILL_FLOOR_Y, "z": SCRATCH_Z0 + SCRATCH_L - 1}
    client.call_text("block_fill_region",
                     {"dimension": SCRATCH_DIM, "box": {"from": floor_a, "to": floor_b}, "block": {"id": "minecraft:stone"}})


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------

def discover_live_tools(client):
    r = client._post({"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": {}})
    return sorted(t["name"] for t in (r.get("result", {}).get("tools") or []))


def load_cases():
    """Import every itest.cases_* module so their @case decorators register."""
    import importlib
    import pkgutil
    from . import cases  # noqa
    base = os.path.join(os.path.dirname(__file__), "cases")
    for m in pkgutil.iter_modules([base]):
        importlib.import_module(f"itest.cases.{m.name}")


def run(only=None, include_destructive=False):
    client = McpClient()
    client.handshake()
    live = discover_live_tools(client)
    load_cases()

    results: list = []
    _forceload(client, "add")
    try:
        _clear_sandbox(client)
        ctx = Ctx(client)
        for tool in sorted(CASES):
            spec = CASES[tool]
            if only and not tool.startswith(only):
                continue
            if tool not in live:
                results.append(Result(tool, spec["category"], spec["level"], "SKIP",
                                      not_live_reason(tool)))
                continue
            if spec["level"] == "destructive" and not include_destructive:
                results.append(Result(tool, spec["category"], spec["level"], "SKIP",
                                      "destructive — run with --destructive"))
                continue
            try:
                spec["fn"](ctx)
                results.append(Result(tool, spec["category"], spec["level"], "PASS"))
            except Skip as e:
                results.append(Result(tool, spec["category"], spec["level"], "SKIP", str(e)))
            except (AssertionError, McpError, Exception) as e:  # noqa: BLE001
                detail = f"{type(e).__name__}: {e}"
                if not isinstance(e, (AssertionError, McpError)):
                    detail += " | " + traceback.format_exc().splitlines()[-1]
                results.append(Result(tool, spec["category"], spec["level"], "FAIL", detail))
    finally:
        try:
            _clear_sandbox(client)
        finally:
            _forceload(client, "remove")

    uncovered = [t for t in live if t not in CASES and (not only or t.startswith(only))]
    return results, uncovered, live


def report(results, uncovered, live, baseline_path=None):
    by_status = {}
    for r in results:
        by_status.setdefault(r.status, []).append(r)
    npass = len(by_status.get("PASS", []))
    nfail = len(by_status.get("FAIL", []))
    nskip = len(by_status.get("SKIP", []))
    print(f"\n=== MCP integration suite ===")
    print(f"live tools: {len(live)} | cases: {len(CASES)} | "
          f"PASS {npass}  FAIL {nfail}  SKIP {nskip}  UNCOVERED {len(uncovered)}")
    for r in results:
        if r.status in ("FAIL", "ERROR"):
            print(f"  XX [{r.category}] {r.tool}: {r.detail}")
    for r in results:
        if r.status == "SKIP":
            print(f"  -- SKIP {r.tool}: {r.detail}")
    if uncovered:
        print(f"  UNCOVERED ({len(uncovered)}): " + ", ".join(uncovered))
    if baseline_path:
        with open(baseline_path, "w", encoding="utf-8") as fh:
            fh.write(f"live_tools: {len(live)}\ncases: {len(CASES)}\n")
            fh.write(f"pass: {npass}\nfail: {nfail}\nskip: {nskip}\nuncovered: {len(uncovered)}\n")
            for r in sorted(results, key=lambda x: x.tool):
                fh.write(f"{r.tool}\t{r.status}\t{r.detail}\n")
            for t in uncovered:
                fh.write(f"{t}\tUNCOVERED\t\n")
        print(f"  baseline written: {baseline_path}")
    return nfail == 0
