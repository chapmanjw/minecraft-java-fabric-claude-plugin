"""Offline tests for the rail/wire continuity verifier (Zion P4).

No live server: the MCP ``call`` is a fake that serves scripted ``block_scan_region``
text from a configured "present" set and records every ``block_set_state`` patch.
"""
from voxel.continuity import (
    find_gaps, layer_tiles, parse_positions, _reply_text, scan_present,
    verify_and_patch, SCAN_VOLUME_CAP,
)


# --------------------------------------------------------------------------- pure core

def test_find_gaps_basic():
    intended = [(0, 0), (1, 0), (2, 0)]
    assert find_gaps(intended, {(0, 0), (2, 0)}) == [(1, 0)]


def test_find_gaps_preserves_order_and_dedupes():
    intended = [(1, 0), (1, 0), (0, 0), (2, 0)]
    assert find_gaps(intended, set()) == [(1, 0), (0, 0), (2, 0)]


def test_find_gaps_none_missing():
    intended = [(0, 0), (1, 0)]
    assert find_gaps(intended, {(0, 0), (1, 0), (9, 9)}) == []


def test_find_gaps_xyz_tuples():
    intended = [(0, 64, 0), (1, 64, 0)]
    assert find_gaps(intended, {(0, 64, 0)}) == [(1, 64, 0)]


# --------------------------------------------------------------------------- tiling

def test_layer_tiles_partition_exactly():
    rect = (-5, -5, 20, 30)
    cells = {(x, z) for x in range(rect[0], rect[2] + 1)
             for z in range(rect[1], rect[3] + 1)}
    covered = set()
    for (ax0, az0, ax1, az1) in layer_tiles(*rect, cap=64):
        area = (ax1 - ax0 + 1) * (az1 - az0 + 1)
        assert area <= 64
        for x in range(ax0, ax1 + 1):
            for z in range(az0, az1 + 1):
                key = (x, z)
                assert key not in covered, "tiles overlap"
                covered.add(key)
    assert covered == cells, "tiles must partition the rectangle exactly"


def test_layer_tiles_single_when_small():
    tiles = list(layer_tiles(0, 0, 3, 3, cap=SCAN_VOLUME_CAP))
    assert tiles == [(0, 0, 3, 3)]


# --------------------------------------------------------------------------- parsing

def test_parse_positions_extracts_xz():
    text = "x: -30 y: -45 z: -225\n x:24 y:-44 z:185 \nnoise"
    assert parse_positions(text) == {(-30, -225), (24, 185)}


def test_reply_text_shapes():
    assert _reply_text("plain") == "plain"
    assert _reply_text({"result": {"content": [{"text": "abc"}]}}) == "abc"
    assert _reply_text({"content": [{"text": "xyz"}]}) == "xyz"
    assert _reply_text({}) == ""


# --------------------------------------------------------------------------- fake-server wiring

class _FakeServer:
    """Serves block_scan_region text from a present set; records set_state calls."""

    def __init__(self, present, y):
        self.present = set(present)
        self.y = y
        self.scans = []
        self.set_states = []

    def call(self, name, args):
        if name == "block_scan_region":
            box = args["box"]
            f, t = box["from"], box["to"]
            self.scans.append((f, t))
            if f["y"] != self.y or t["y"] != self.y:
                return ""
            lines = [f"x: {x} y: {self.y} z: {z}"
                     for (x, z) in self.present
                     if f["x"] <= x <= t["x"] and f["z"] <= z <= t["z"]]
            return {"result": {"content": [{"text": "\n".join(lines)}]}}
        if name == "block_set_state":
            self.set_states.append(args)
            return {"result": {"content": [{"text": "ok"}]}}
        raise AssertionError(f"unexpected call {name}")


def test_scan_present_unions_tiles():
    present = {(0, 0), (5, 5), (40, 40)}
    srv = _FakeServer(present, y=64)
    got = scan_present("minecraft:overworld", 64, 0, 0, 40, 40,
                       call=srv.call, cap=64)
    assert got == present
    assert len(srv.scans) > 1, "a 41x41 layer at cap 64 must tile"


def test_verify_and_patch_fills_only_the_gaps():
    intended = [(0, 0), (1, 0), (2, 0), (3, 0)]
    present = {(0, 0), (1, 0), (3, 0)}          # (2, 0) was silently dropped
    srv = _FakeServer(present, y=64)
    shape_of = {c: "east_west" for c in intended}

    report = verify_and_patch(intended, "minecraft:overworld", 64,
                              shape_of=shape_of, call=srv.call)

    assert report["gaps"] == [(2, 0)]
    assert report["patched"] == 1
    assert len(srv.set_states) == 1
    patch = srv.set_states[0]
    assert patch["position"] == {"x": 2, "y": 64, "z": 0}
    assert patch["block"] == {"id": "minecraft:rail",
                              "properties": {"shape": "east_west"}}


def test_verify_and_patch_noop_when_complete():
    intended = [(0, 0), (1, 0)]
    srv = _FakeServer(set(intended), y=70)
    report = verify_and_patch(intended, "minecraft:overworld", 70, call=srv.call)
    assert report["gaps"] == [] and report["patched"] == 0
    assert srv.set_states == []
