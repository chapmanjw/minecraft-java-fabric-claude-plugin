"""Tag tools — registry tag listing / membership.

All three tag tools are read-only registry queries, so every case is "safe"
(no world mutation, nothing to clean up). The minecraft:block registry and the
well-known minecraft:logs tag are stable across versions, so we can assert real
content: the tag list contains minecraft:logs, that tag's members include
oak_log, and a membership check agrees with the member listing.

Response shapes (confirmed by live probe + the TOON reader):
  * tag_list_in_registry -> TOON inline array  -> Python list[str] of tag ids
  * tag_get_members       -> TOON inline array  -> Python list[str] of member ids
  * tag_check_membership  -> bare "true"/"false" -> Python bool
Assertions are tolerant of a dict-wrapped variant ({"tags": [...]}, {"members":
[...]}, {"member": true}) in case the encoder changes.
"""
from __future__ import annotations

from ..harness import case, Ctx, Skip

# Stable, version-independent fixtures.
_REG = "minecraft:block"
_TAG = "minecraft:logs"
_MEMBER = "minecraft:oak_log"
_NON_MEMBER = "minecraft:stone"


def _as_list(data):
    """Coerce a tag/member response to a list of strings.

    The tools emit a bare TOON array (parsed to a Python list); tolerate a
    dict-wrapped form too in case the encoder ever wraps it.
    """
    if isinstance(data, list):
        return [str(x) for x in data]
    if isinstance(data, dict):
        for key in ("tags", "members", "entries", "values", "ids", "result"):
            v = data.get(key)
            if isinstance(v, list):
                return [str(x) for x in v]
        # last resort: a dict whose values are the entries
        return [str(x) for x in data.values()]
    # plain string fallback (e.g. a single un-parsed line)
    return [s for s in str(data).replace(",", " ").split() if s]


@case("tag_list_in_registry", level="safe")
def test_list_in_registry(ctx: Ctx):
    data = ctx.call("tag_list_in_registry", {"registry": _REG})
    tags = _as_list(data)
    ctx.expect(len(tags) > 0, f"no tags listed for {_REG}: {str(data)[:160]}")
    # minecraft:logs is a vanilla block tag present in every modern version.
    ctx.expect(_TAG in tags, f"expected {_TAG} in block-tag list, got {len(tags)} tags")


@case("tag_get_members", level="safe")
def test_get_members(ctx: Ctx):
    data = ctx.call("tag_get_members", {"registry": _REG, "tag": _TAG})
    members = _as_list(data)
    ctx.expect(len(members) > 0, f"no members for {_TAG}: {str(data)[:160]}")
    ctx.expect(_MEMBER in members,
               f"expected {_MEMBER} in members of {_TAG}, got {len(members)} members")


@case("tag_check_membership", level="safe")
def test_check_membership(ctx: Ctx):
    # Positive: oak_log IS in minecraft:logs.
    yes_text, is_err = ctx.call_text(
        "tag_check_membership", {"registry": _REG, "tag": _TAG, "member": _MEMBER})
    ctx.expect(not is_err, f"membership check errored: {yes_text}")
    ctx.expect("true" in yes_text.lower(),
               f"expected {_MEMBER} to be a member of {_TAG}, got {yes_text!r}")

    # Negative: stone is NOT a log. Cross-check the result against the member
    # listing so the boolean genuinely reflects the tag's contents.
    no_text, is_err = ctx.call_text(
        "tag_check_membership", {"registry": _REG, "tag": _TAG, "member": _NON_MEMBER})
    ctx.expect(not is_err, f"negative membership check errored: {no_text}")
    members = _as_list(ctx.call("tag_get_members", {"registry": _REG, "tag": _TAG}))
    if _NON_MEMBER not in members:
        ctx.expect("false" in no_text.lower(),
                   f"expected {_NON_MEMBER} to NOT be a member of {_TAG}, got {no_text!r}")
    else:  # registry surprised us — don't false-fail, just note it
        raise Skip(f"{_NON_MEMBER} unexpectedly in {_TAG}; can't assert negative case")
