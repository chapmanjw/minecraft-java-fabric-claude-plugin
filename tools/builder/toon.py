"""Minimal TOON (Token-Oriented Object Notation) reader — stdlib only.

Parses the subset of TOON v3.2 the minecraft-java MCP server emits (see the
server's `Toon.java` encoder) and the subset the planner writes into
`plan.toon`. It is a *reader*; the harness never needs to emit TOON.

What it handles:
  - object fields            key: scalar
  - nested objects           key:\\n  child: ...
  - inline objects           anchor: {x: 12, y: 64, z: -7}
  - tabular arrays           rows[2]{a,b}:\\n  1,2\\n  3,4   (explicit length)
  - inline primitive arrays  vals[3]: 1,2,3
  - expanded list arrays     items[2]:\\n  - ...\\n  - ...
  - root object, root tabular array, root inline array, root scalar
  - scalars: quoted strings (with \\n \\t \\r \\" \\\\ \\uXXXX), numbers, bools, null

The explicit `[N]` counts let us consume exactly N rows/items, which removes
all indentation ambiguity between table rows and sibling fields.

Stdlib only. No dependencies.
"""
from __future__ import annotations

import re

_HEADER_RE = re.compile(r"^(?P<key>(?:\"(?:[^\"\\]|\\.)*\")|[^:\[\]{}]*?)\[(?P<n>\d+)\](?:\{(?P<cols>[^}]*)\})?:\s?(?P<rest>.*)$")


class ToonError(ValueError):
    pass


def parse(text):
    """Parse a TOON document into Python data (dict / list / scalar)."""
    lines = _tokenize(text)
    if not lines:
        return {}
    parser = _Parser(lines)
    return parser.parse_root()


# --------------------------------------------------------------------------- tokenize

def _tokenize(text):
    """Return [(indent_level, content)] for each non-blank line. 2 spaces / level."""
    out = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not raw.strip():
            continue
        stripped = raw.lstrip(" ")
        indent = len(raw) - len(stripped)
        out.append((indent // 2, stripped))
    return out


# --------------------------------------------------------------------------- parser

class _Parser:
    def __init__(self, lines):
        self.lines = lines
        self.i = 0

    def _peek(self):
        return self.lines[self.i] if self.i < len(self.lines) else None

    def _next(self):
        item = self.lines[self.i]
        self.i += 1
        return item

    def parse_root(self):
        first = self._peek()
        if first is None:
            return {}
        _, content = first
        if content == "[]":
            self._next()
            return []
        # Root array header has no key: starts with "["
        m = _HEADER_RE.match(content)
        if m and (m.group("key") == "" or m.group("key") is None):
            return self._parse_array_from_header(m, base_indent=0)
        if content.startswith("- "):
            return self._parse_expanded_list(base_indent=0)
        # Root object, or a bare scalar.
        if ":" in content or m:
            return self._parse_object(0)
        self._next()
        return _scalar(content)

    def _parse_object(self, indent):
        obj = {}
        while True:
            item = self._peek()
            if item is None:
                break
            ind, content = item
            if ind < indent:
                break
            if ind > indent:
                # Shouldn't happen at object start; tolerate by stopping.
                break
            key, value = self._parse_field(indent, content)
            obj[key] = value
        return obj

    def _parse_field(self, indent, content):
        m = _HEADER_RE.match(content)
        if m:
            key = _unkey(m.group("key"))
            self._next()
            return key, self._parse_array_body(m, indent)
        # plain `key: rest` / `key:`
        if ":" not in content:
            raise ToonError(f"expected 'key:' got {content!r}")
        key_part, _, rest = content.partition(":")
        key = _unkey(key_part.strip())
        rest = rest.strip()
        self._next()
        if rest == "":
            # nested object (children indented) or empty
            nxt = self._peek()
            if nxt is not None and nxt[0] > indent and not nxt[1].startswith("- "):
                return key, self._parse_object(indent + 1)
            return key, {}
        if rest == "[]":
            return key, []
        return key, _scalar(rest)

    def _parse_array_from_header(self, m, base_indent):
        # root array: consume the header line first
        self._next()
        return self._parse_array_body(m, base_indent)

    def _parse_array_body(self, m, indent):
        n = int(m.group("n"))
        cols = m.group("cols")
        rest = (m.group("rest") or "").strip()
        if cols is not None:
            # tabular: next N rows at indent+1
            field_names = [_unkey(c.strip()) for c in _split_cells(cols)]
            rows = []
            for _ in range(n):
                item = self._peek()
                if item is None:
                    break
                _, rowtext = self._next()
                cells = _split_cells(rowtext)
                row = {}
                for idx, fname in enumerate(field_names):
                    row[fname] = _cell_scalar(cells[idx]) if idx < len(cells) else None
                rows.append(row)
            return rows
        if rest:
            # inline primitive array
            return [_scalar(c) for c in _split_cells(rest)]
        if n == 0:
            return []
        # expanded list: N items starting with "- "
        return self._parse_expanded_list(indent + 1, count=n)

    def _parse_expanded_list(self, base_indent, count=None):
        items = []
        while count is None or len(items) < count:
            item = self._peek()
            if item is None:
                break
            ind, content = item
            if ind < base_indent or not content.startswith("-"):
                break
            self._next()
            body = content[1:].strip()
            if body == "":
                items.append({})
            elif ":" in body or _HEADER_RE.match(body):
                # list-item object: first field on hyphen line, rest indented
                first_key, first_val = self._inline_field(base_indent, body)
                obj = {first_key: first_val}
                # additional fields at base_indent + 1
                while True:
                    nxt = self._peek()
                    if nxt is None or nxt[0] <= base_indent or nxt[1].startswith("-"):
                        break
                    k, v = self._parse_field(base_indent + 1, nxt[1])
                    obj[k] = v
                items.append(obj)
            else:
                items.append(_scalar(body))
        return items

    def _inline_field(self, indent, body):
        m = _HEADER_RE.match(body)
        if m:
            key = _unkey(m.group("key"))
            return key, self._parse_array_body(m, indent + 1)
        key_part, _, rest = body.partition(":")
        key = _unkey(key_part.strip())
        rest = rest.strip()
        if rest == "":
            return key, self._parse_object(indent + 2)
        return key, _scalar(rest)


# --------------------------------------------------------------------------- scalars

def _scalar(tok):
    tok = tok.strip()
    if tok == "" or tok == "null":
        return None
    if tok == "true":
        return True
    if tok == "false":
        return False
    if tok[0] == '"':
        return _unquote(tok)
    if tok[0] == "{":
        return _inline_object(tok)
    if tok[0] == "[":
        inner = tok[1:-1].strip()
        return [_scalar(c) for c in _split_cells(inner)] if inner else []
    num = _try_number(tok)
    return num if num is not None else tok


def _cell_scalar(tok):
    """Scalar for tabular row cells. Unlike `_scalar`, it never interprets a
    leading `{`/`[` as a TOON inline object/array — a cell like an SNBT `note`
    (`{front_text:{...}}`) or a coord stays a raw string. Only quoted strings,
    numbers, booleans, and null are decoded."""
    tok = tok.strip()
    if tok == "" or tok == "null":
        return None
    if tok == "true":
        return True
    if tok == "false":
        return False
    if tok and tok[0] == '"':
        return _unquote(tok)
    num = _try_number(tok)
    return num if num is not None else tok


def _try_number(s):
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except ValueError:
            return None
    if re.fullmatch(r"-?\d+\.\d+([eE][+-]?\d+)?", s) or re.fullmatch(r"-?\d+[eE][+-]?\d+", s):
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _inline_object(tok):
    inner = tok.strip()[1:-1].strip()
    obj = {}
    if not inner:
        return obj
    for cell in _split_cells(inner):
        k, _, v = cell.partition(":")
        obj[_unkey(k.strip())] = _scalar(v.strip())
    return obj


def _unkey(k):
    k = k.strip()
    if k and k[0] == '"':
        return _unquote(k)
    return k


def _unquote(tok):
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        body = tok[1:-1]
    else:
        body = tok
    out = []
    i = 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            if nxt == "n":
                out.append("\n")
            elif nxt == "t":
                out.append("\t")
            elif nxt == "r":
                out.append("\r")
            elif nxt == "u" and i + 5 < len(body) + 1:
                try:
                    out.append(chr(int(body[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    out.append(nxt)
            else:
                out.append(nxt)
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _split_cells(s):
    """Split on top-level commas, respecting quotes and []{} nesting."""
    cells = []
    buf = []
    depth = 0
    in_q = False
    i = 0
    while i < len(s):
        c = s[i]
        if in_q:
            buf.append(c)
            if c == "\\" and i + 1 < len(s):
                buf.append(s[i + 1])
                i += 2
                continue
            if c == '"':
                in_q = False
            i += 1
            continue
        if c == '"':
            in_q = True
            buf.append(c)
        elif c in "[{":
            depth += 1
            buf.append(c)
        elif c in "]}":
            depth -= 1
            buf.append(c)
        elif c == "," and depth == 0:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(c)
        i += 1
    cells.append("".join(buf).strip())
    return cells
