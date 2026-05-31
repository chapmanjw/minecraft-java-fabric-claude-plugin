"""Resource tools — Fabric resource-manager reads + ResourceCondition eval.

Three live tools, all safe reads (no world mutation, nothing to clean up):
  * resource_loader_list_namespaces   (safe read)  — names registered with the
                                                      server ResourceManager
  * resource_loader_get_resource      (safe read)  — bytes of a datapack file,
                                                      returned base64-encoded
  * resource_condition_evaluate       (safe read)  — decode + evaluate a Fabric
                                                      ResourceCondition JSON

Observed response shapes (probed live, 26.1.2):
  list_namespaces  -> TOON inline array -> Python list[str], e.g.
                      ["minecraft", "fabric-convention-tags-v2", "c"]
  get_resource     -> ToolResult.ofText(base64) -> a plain base64 string (the
                      TOON reader can't parse it, so call_toon falls through to
                      the raw text; we use call_text). A missing location throws
                      McpException("Resource not found: <ns>:<path>") which the
                      transport surfaces as an McpError (=> FAIL if unexpected).
  condition_eval   -> TOON object -> {"matches": <bool>, "condition_id": <str>}

The server resource manager serves *datapack* (data/) files. Modern Minecraft
(1.21+/26.x) uses singular registry dirs, so the reliably-present probe target
is the vanilla stone block loot table at "loot_table/blocks/stone.json" under
the "minecraft" namespace (verified live). The get_resource test still tolerates
the file being absent on a future pack layout by falling back through a couple of
candidate paths and Skipping if none resolve, rather than hard-failing.
"""
from __future__ import annotations

import base64

from ..harness import case, Ctx, Skip


# ---------------------------------------------------------------------------
# resource_loader_list_namespaces — safe read
# ---------------------------------------------------------------------------

@case("resource_loader_list_namespaces", level="safe")
def test_list_namespaces(ctx: Ctx):
    """Every running server registers at least the vanilla 'minecraft'
    namespace with its ResourceManager. The tool emits a TOON inline array, so
    call_toon decodes it to a list[str]."""
    data = ctx.call("resource_loader_list_namespaces", {})
    # Tolerant: normally a list; if a single-element edge case decoded to a bare
    # scalar, wrap it so the membership check still holds.
    names = data if isinstance(data, list) else [data]
    ctx.expect(len(names) > 0, f"no namespaces returned: {data!r}")
    ctx.expect("minecraft" in names,
               f"expected the 'minecraft' namespace to be registered, got {names!r}")


# ---------------------------------------------------------------------------
# resource_loader_get_resource — safe read
# ---------------------------------------------------------------------------

# Candidate datapack files that should exist in a vanilla server's resource
# manager. Singular registry dir is the modern (1.21+/26.x) layout; the plural
# form is kept as a fallback for older builds. First one that resolves wins.
_RESOURCE_CANDIDATES = [
    ("minecraft", "loot_table/blocks/stone.json"),
    ("minecraft", "loot_tables/blocks/stone.json"),
    ("minecraft", "recipe/stone_stairs.json"),
]


@case("resource_loader_get_resource", level="safe")
def test_get_resource(ctx: Ctx):
    """Read a known vanilla datapack file and confirm it decodes to non-empty,
    well-formed bytes. The tool returns the resource base64-encoded as plain
    text, so we use call_text and decode locally. A missing location surfaces as
    an McpError; we probe a few stable candidates and only Skip if none of them
    exist (a pack-layout change), never hard-fail on absence."""
    last_err = None
    for ns, path in _RESOURCE_CANDIDATES:
        try:
            text, is_err = ctx.call_text("resource_loader_get_resource",
                                         {"namespace": ns, "path": path})
        except Exception as e:  # McpError "Resource not found" — try the next candidate
            last_err = f"{ns}:{path} -> {e}"
            continue
        ctx.expect(not is_err, f"get_resource {ns}:{path} returned error flag: {text}")
        ctx.expect(isinstance(text, str) and text.strip() != "",
                   f"get_resource {ns}:{path} returned empty payload")
        # The payload is base64; it must decode cleanly to non-empty bytes.
        raw = base64.b64decode(text.strip(), validate=True)
        ctx.expect(len(raw) > 0, f"decoded resource {ns}:{path} was empty")
        # These candidates are all JSON datapack files — sanity-check the shape.
        head = raw.lstrip()[:1]
        ctx.expect(head in (b"{", b"["),
                   f"resource {ns}:{path} did not decode to JSON-looking bytes: {raw[:32]!r}")
        return
    raise Skip(f"no stable vanilla resource resolved (pack layout changed?): {last_err}")


# ---------------------------------------------------------------------------
# resource_condition_evaluate — safe read
# ---------------------------------------------------------------------------

@case("resource_condition_evaluate", level="safe")
def test_condition_evaluate(ctx: Ctx):
    """Decode + evaluate two Fabric ResourceConditions against the live
    registry: one that must hold ('minecraft' mod is loaded) and one that must
    not (a mod id that cannot exist). Asserting both polarities proves the tool
    actually evaluates rather than echoing a constant.

    Response is a TOON object {"matches": <bool>, "condition_id": <str>}."""
    import json

    # 1) all_mods_loaded[minecraft] must be true on any running server.
    true_cond = json.dumps({"condition": "fabric:all_mods_loaded",
                            "values": ["minecraft"]})
    res_true = ctx.call("resource_condition_evaluate", {"condition_json": true_cond})
    matches_true = ctx.expect_field(res_true, "matches")
    cid_true = ctx.expect_field(res_true, "condition_id")
    ctx.expect(matches_true is True,
               f"all_mods_loaded[minecraft] should match, got {res_true}")
    ctx.expect("all_mods_loaded" in str(cid_true),
               f"unexpected decoded condition_id: {res_true}")

    # 2) any_mods_loaded against an id that cannot exist must be false — same
    #    decoder, opposite outcome, so the result is genuinely evaluated.
    false_cond = json.dumps({"condition": "fabric:any_mods_loaded",
                             "values": ["mcb_itest_nonexistent_mod_zzz"]})
    res_false = ctx.call("resource_condition_evaluate", {"condition_json": false_cond})
    matches_false = ctx.expect_field(res_false, "matches")
    ctx.expect(matches_false is False,
               f"any_mods_loaded[bogus] should not match, got {res_false}")
