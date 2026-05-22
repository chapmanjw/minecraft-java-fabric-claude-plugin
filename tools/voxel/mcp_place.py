"""Minimal MCP (Streamable HTTP, JSON-RPC 2.0) client for the local
minecraft-java server. Reliably places a large file-defined block_fill_batch
that is impractical and error-prone to hand-transcribe into a tool call — the
#1 friction when placing a voxelized model (1,000–7,200 fills).

Usage:
  python mcp_place.py test                           # handshake + server_get_status
  python mcp_place.py place <fills.json> [mode]      # block_fill_batch (mode default: replace)
  python mcp_place.py place <fills.json> --dimension minecraft:the_nether

`<fills.json>` is the list written by `voxel.write_fills_json` —
[{"from":[x,y,z], "to":[x,y,z], "block":"…"}, …] in WORLD coordinates.

Server URL and auth are read from `~/.claude.json` → mcpServers["minecraft-java"]
(falling back to a project `.mcp.json` next to the cwd, then to the localhost
default). On single-player there is no auth; a remote/authenticated server uses
an `Authorization: Bearer …` header, which is honoured here. ${VAR} and
${VAR:-default} references in the config are expanded against the environment.

block_fill_batch is bounded to 8192 entries per call server-side; this client
pages larger fill lists into successive calls automatically.

Stdlib only (urllib) — no extra dependencies.
"""
import json
import os
import re
import sys
import urllib.request

DEFAULT_URL = "http://localhost:8765/mcp"
DEFAULT_DIM = "minecraft:overworld"
SERVER_NAME = "minecraft-java"
MAX_ENTRIES = 8192               # block_fill_batch server-side cap (BlockTools.MAX_ENTRIES)

_session = {"id": None}


# --------------------------------------------------------------------------- config

def _expand(value):
    """Expand ${VAR} and ${VAR:-default} against the environment."""
    if not isinstance(value, str):
        return value

    def repl(m):
        name, default = m.group(1), m.group(2)
        return os.environ.get(name, default if default is not None else "")

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}", repl, value)


def _server_entry(cfg):
    """Find the minecraft-java server block in a parsed claude/mcp config."""
    servers = cfg.get("mcpServers")
    if isinstance(servers, dict) and SERVER_NAME in servers:
        return servers[SERVER_NAME]
    # ~/.claude.json also nests servers per project: projects.<path>.mcpServers
    for proj in (cfg.get("projects") or {}).values():
        ps = (proj or {}).get("mcpServers")
        if isinstance(ps, dict) and SERVER_NAME in ps:
            return ps[SERVER_NAME]
    return None


def load_config():
    """Return (url, headers) for the minecraft-java MCP server.

    Reads ~/.claude.json first, then a project .mcp.json in the cwd; falls back
    to the localhost default with no auth.
    """
    candidates = [
        os.path.join(os.path.expanduser("~"), ".claude.json"),
        os.path.join(os.getcwd(), ".mcp.json"),
    ]
    for path in candidates:
        try:
            with open(path, encoding="utf-8") as fh:
                cfg = json.load(fh)
        except (OSError, ValueError):
            continue
        entry = _server_entry(cfg)
        if not entry:
            continue
        url = _expand(entry.get("url") or DEFAULT_URL)
        headers = {}
        for k, v in (entry.get("headers") or {}).items():
            headers[k] = _expand(v)
        return url, headers
    return DEFAULT_URL, {}


URL, HEADERS = load_config()


# --------------------------------------------------------------------------- transport

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
    if "text/event-stream" in ctype:                 # parse SSE: take last data: line
        out = None
        for line in body.splitlines():
            if line.startswith("data:"):
                out = json.loads(line[5:].strip())
        return out
    return json.loads(body) if body.strip() else None


def handshake():
    for ver in ("2025-06-18", "2024-11-05"):
        r = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": ver, "capabilities": {},
                              "clientInfo": {"name": "voxel-placer", "version": "1.0"}}})
        if r and "result" in r:
            _post({"jsonrpc": "2.0", "method": "notifications/initialized"})
            return ver
    raise SystemExit(f"initialize failed: {r}")


def call(name, arguments):
    return _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                  "params": {"name": name, "arguments": arguments}})


def place(fills, dimension, mode):
    """Place a fills list, paging into ≤MAX_ENTRIES-entry block_fill_batch calls."""
    pages = [fills[i:i + MAX_ENTRIES] for i in range(0, len(fills), MAX_ENTRIES)] or [[]]
    if len(pages) > 1:
        print(f"{len(fills)} fills > {MAX_ENTRIES} cap — paging into {len(pages)} calls")
    last = None
    for idx, page in enumerate(pages, 1):
        if len(pages) > 1:
            print(f"  page {idx}/{len(pages)}: {len(page)} fills (mode={mode})...")
        last = call("block_fill_batch",
                    {"dimension": dimension, "default_mode": mode, "fills": page})
        if last and last.get("error"):
            print(json.dumps(last, indent=2)[:1200])
            raise SystemExit(f"block_fill_batch failed on page {idx}/{len(pages)}")
    return last


# --------------------------------------------------------------------------- cli

def _parse_args(argv):
    """Tiny parser: command, optional positional, and a --dimension flag."""
    dimension, rest = DEFAULT_DIM, []
    it = iter(argv)
    for tok in it:
        if tok == "--dimension":
            dimension = next(it, DEFAULT_DIM)
        else:
            rest.append(tok)
    return rest, dimension


if __name__ == "__main__":
    args, dim = _parse_args(sys.argv[1:])
    cmd = args[0] if args else "test"
    ver = handshake()
    print("handshake ok, protocol", ver, "session", _session["id"], "url", URL)
    if cmd == "test":
        print(json.dumps(call("server_get_status", {}), indent=2)[:800])
    elif cmd == "place":
        if len(args) < 2:
            raise SystemExit("usage: mcp_place.py place <fills.json> [mode] [--dimension DIM]")
        fills = json.load(open(args[1], encoding="utf-8"))
        mode = args[2] if len(args) > 2 else "replace"
        print(f"placing {len(fills)} fills (mode={mode}, dimension={dim})...")
        res = place(fills, dim, mode)
        print(json.dumps(res, indent=2)[:1200])
    else:
        raise SystemExit(f"unknown command: {cmd!r} (use 'test' or 'place')")
