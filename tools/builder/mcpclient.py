"""Generic MCP (Streamable HTTP, JSON-RPC 2.0) client for the minecraft-java
server — the shared transport the build+verify harness runs on.

Mirrors the proven config-loading + handshake logic of
`tools/voxel/mcp_place.py`, but as a reusable class with a TOON-decoding
`call_toon()` helper so callers get Python data instead of raw text.

Server URL and auth are read from `~/.claude.json` → mcpServers["minecraft-java"]
(then a project `.mcp.json` in the cwd, then the localhost default). ${VAR} and
${VAR:-default} references are expanded against the environment.

Stdlib only (urllib). No dependencies.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

from . import toon

DEFAULT_URL = "http://localhost:8765/mcp"
DEFAULT_DIM = "minecraft:overworld"
SERVER_NAME = "minecraft-java"


class McpError(RuntimeError):
    pass


def _expand(value):
    if not isinstance(value, str):
        return value

    def repl(m):
        name, default = m.group(1), m.group(2)
        return os.environ.get(name, default if default is not None else "")

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}", repl, value)


def _server_entry(cfg):
    servers = cfg.get("mcpServers")
    if isinstance(servers, dict) and SERVER_NAME in servers:
        return servers[SERVER_NAME]
    for proj in (cfg.get("projects") or {}).values():
        ps = (proj or {}).get("mcpServers")
        if isinstance(ps, dict) and SERVER_NAME in ps:
            return ps[SERVER_NAME]
    return None


def load_config():
    """Return (url, headers) for the minecraft-java MCP server."""
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
        headers = {k: _expand(v) for k, v in (entry.get("headers") or {}).items()}
        return url, headers
    return DEFAULT_URL, {}


class McpClient:
    def __init__(self, url=None, headers=None, timeout=120, max_retries=6):
        cfg_url, cfg_headers = load_config()
        self.url = url or cfg_url
        self.headers = headers if headers is not None else cfg_headers
        self.timeout = timeout
        self.max_retries = max_retries
        self.session_id = None
        self.protocol = None

    # -- transport ---------------------------------------------------------

    def _post(self, payload):
        """POST a JSON-RPC payload, backing off on HTTP 429/503 (rate limit /
        busy). The verifier issues many small reads, so the per-client
        `rate_limit_rpm` is easy to hit — back off rather than crash."""
        data = json.dumps(payload).encode()
        attempt = 0
        while True:
            req = urllib.request.Request(self.url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json, text/event-stream")
            for k, v in self.headers.items():
                req.add_header(k, v)
            if self.session_id:
                req.add_header("Mcp-Session-Id", self.session_id)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    sid = resp.headers.get("Mcp-Session-Id")
                    if sid:
                        self.session_id = sid
                    ctype = resp.headers.get("Content-Type", "")
                    body = resp.read().decode()
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 503) and attempt < self.max_retries:
                    retry_after = e.headers.get("Retry-After")
                    delay = float(retry_after) if (retry_after and retry_after.isdigit()) else min(2 ** attempt, 30)
                    time.sleep(max(0.5, delay))
                    attempt += 1
                    continue
                raise
        if "text/event-stream" in ctype:
            out = None
            for line in body.splitlines():
                if line.startswith("data:"):
                    out = json.loads(line[5:].strip())
            return out
        return json.loads(body) if body.strip() else None

    def handshake(self):
        for ver in ("2025-06-18", "2024-11-05"):
            r = self._post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": ver, "capabilities": {},
                                       "clientInfo": {"name": "mc-build-harness", "version": "1.0"}}})
            if r and "result" in r:
                self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
                self.protocol = ver
                return ver
        raise McpError(f"initialize failed: {r}")

    # -- tool calls --------------------------------------------------------

    def call_raw(self, name, arguments):
        return self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": name, "arguments": arguments}})

    def call_text(self, name, arguments):
        """Call a tool; return (text, is_error). Raises McpError on JSON-RPC error."""
        r = self.call_raw(name, arguments)
        if r is None:
            raise McpError(f"{name}: empty response")
        if "error" in r:
            raise McpError(f"{name}: {r['error']}")
        result = r.get("result", {})
        blocks = result.get("content", []) or []
        text = "\n".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return text, bool(result.get("isError"))

    def call_toon(self, name, arguments):
        """Call a tool and decode its TOON text payload into Python data."""
        text, is_error = self.call_text(name, arguments)
        if is_error:
            raise McpError(f"{name} returned error: {text}")
        try:
            return toon.parse(text)
        except toon.ToonError:
            return text  # plain-text result (e.g. block_get_top_y returns an int line)

    # -- convenience -------------------------------------------------------

    def command(self, cmd):
        """Run a raw slash command (no leading slash) via command_execute."""
        return self.call_text("command_execute", {"command": cmd})


def connected_client():
    """Build a client and complete the MCP handshake."""
    c = McpClient()
    c.handshake()
    return c
