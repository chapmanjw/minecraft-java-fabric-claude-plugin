"""Place terrain payloads from the toolkit directly into the world via MCP.

Standalone (stdlib only) MCP client for the live-sculpt / prototype loop and for
the worker fallback. Reads the server URL + auth the same way the voxel
``mcp_place.py`` does (``~/.claude.json`` then ``.mcp.json``), then calls:

  columns  <plan.json>   -> block_fill_columns (or _strata if the plan has strata
                            and the server advertises the tool; else single-stone)
  biomes   <plan.json>   -> level_fill_biome per rectangle
  scatter  <plan.json>   -> level_place_features_batch if available, else
                            per-feature level_place_feature (paced)

Usage:
  python tools/terrain/place_terrain.py columns scratch_columns.json
  python tools/terrain/place_terrain.py biomes  scratch_biomes.json
  python tools/terrain/place_terrain.py scatter scratch_scatter.json
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8765/mcp"
_session = {"id": None}


def _expand(v: str) -> str:
    if not isinstance(v, str):
        return v
    import re

    def sub(m):
        name = m.group(1)
        default = m.group(2)
        if ":-" in (m.group(0)) and default is not None:
            return os.environ.get(name, default)
        return os.environ.get(name, "")
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}", sub, v)


def _server_entry(cfg: dict):
    # look for an mcpServers/minecraft-java style entry
    servers = cfg.get("mcpServers") or {}
    for key in ("minecraft-java", "minecraft_java", "minecraft"):
        if key in servers:
            return servers[key]
    # nested under projects
    for proj in (cfg.get("projects") or {}).values():
        servers = proj.get("mcpServers") or {}
        for key in ("minecraft-java", "minecraft_java", "minecraft"):
            if key in servers:
                return servers[key]
    return None


def load_config():
    for path in (os.path.join(os.path.expanduser("~"), ".claude.json"),
                 os.path.join(os.getcwd(), ".mcp.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                cfg = json.load(fh)
        except (OSError, ValueError):
            continue
        entry = _server_entry(cfg)
        if not entry:
            continue
        url = _expand(entry.get("url") or DEFAULT_URL)
        headers = {k: _expand(v) for k, v in (entry.get("headers") or {}).items()}
        return url, headers
    return DEFAULT_URL, {}


URL, HEADERS = load_config()


def _post(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    for k, v in HEADERS.items():
        req.add_header(k, v)
    if _session["id"]:
        req.add_header("Mcp-Session-Id", _session["id"])
    with urllib.request.urlopen(req, timeout=120) as resp:
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            _session["id"] = sid
        ctype = resp.headers.get("Content-Type", "")
        body = resp.read().decode()
    if "text/event-stream" in ctype:
        out = None
        for line in body.splitlines():
            if line.startswith("data:"):
                out = json.loads(line[5:].strip())
        return out
    return json.loads(body) if body.strip() else None


def _init():
    _post({"jsonrpc": "2.0", "id": 0, "method": "initialize",
           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "place_terrain", "version": "1"}}})
    # notifications/initialized
    try:
        _post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    except Exception:
        pass


_id = [1]


def call(tool: str, args: dict):
    _id[0] += 1
    resp = _post({"jsonrpc": "2.0", "id": _id[0], "method": "tools/call",
                  "params": {"name": tool, "arguments": args}})
    return resp


def _has_tool(name: str) -> bool:
    resp = _post({"jsonrpc": "2.0", "id": 999, "method": "tools/list", "params": {}})
    try:
        tools = resp["result"]["tools"]
        return any(t["name"] == name for t in tools)
    except Exception:
        return False


def place_columns(plan: dict):
    args = dict(plan)
    strata = args.get("strata")
    tool = "block_fill_columns"
    if strata and _has_tool("block_fill_columns_strata"):
        tool = "block_fill_columns_strata"
    else:
        args.pop("strata", None)
    print(f"placing {args['width']}x{args['length']} columns via {tool} at {args['origin']}")
    r = call(tool, args)
    print(json.dumps(r, indent=2)[:1500])
    return r


def place_biomes(plan: list):
    print(f"painting {len(plan)} biome rectangles")
    last = None
    for i, rect in enumerate(plan):
        last = call("level_fill_biome", {
            "dimension": "minecraft:overworld",
            "from": {"x": rect["from"][0], "y": rect["from"][1], "z": rect["from"][2]},
            "to": {"x": rect["to"][0], "y": rect["to"][1], "z": rect["to"][2]},
            "biome": rect["biome"]})
        if (i + 1) % 20 == 0:
            time.sleep(1.0)
    return last


def place_scatter(plan: list):
    batch = _has_tool("level_place_features_batch")
    print(f"scattering {len(plan)} features (batch={batch})")
    if batch:
        feats = [{"feature": p[4], "x": p[0], "y": p[1], "z": p[2]} for p in plan]
        for i in range(0, len(feats), 4096):
            call("level_place_features_batch",
                 {"dimension": "minecraft:overworld", "features": feats[i:i + 4096]})
        return
    for i, p in enumerate(plan):
        call("level_place_feature", {"dimension": "minecraft:overworld",
                                     "feature": p[4],
                                     "position": {"x": p[0], "y": p[1], "z": p[2]}})
        if (i + 1) % 30 == 0:
            time.sleep(1.0)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    mode, path = sys.argv[1], sys.argv[2]
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    _init()
    if mode == "columns":
        place_columns(data)
    elif mode == "biomes":
        place_biomes(data)
    elif mode == "scatter":
        place_scatter(data)
    else:
        print("unknown mode", mode)
        sys.exit(2)


if __name__ == "__main__":
    main()
