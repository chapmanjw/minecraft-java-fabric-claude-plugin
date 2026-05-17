# Contributing

Thanks for your interest in improving the Minecraft Bedrock Claude plugin.

## What's in this repo

This is a Claude Code plugin — there is no build step and no runtime code. It
is made of:

- `.claude-plugin/plugin.json` — the plugin manifest.
- `.claude-plugin/marketplace.json` — the marketplace manifest.
- `skills/<name>/SKILL.md` — agent skills, each with YAML frontmatter.
- `agents/<name>.md` — agents, each with YAML frontmatter.

## Checks

Every change must pass the validation CI runs. Run it locally with Node 20+:

```sh
node scripts/validate-plugin.mjs
```

It checks that the manifests and `.mcp.json.example` parse, that every skill
and agent has the required frontmatter, and that skill folder names match the
`name` in their frontmatter.

## Conventions

- **Skills are playbooks for Claude, not docs for the user.** Write a `SKILL.md`
  body as instructions to Claude — what to do, what to ask, what to verify —
  not as prose for a human to read.
- **Descriptions drive invocation.** A skill's or agent's `description` is what
  Claude matches against to decide when to use it. Make it concrete and
  specific about *when* to trigger.
- One skill per setup phase; keep the four setup skills runnable in order, each
  handing off to the next.
- Keep instructions interactive — do one step, verify, then proceed — and never
  have a skill tell the user to commit a secret.
- Kebab-case names. A skill's `name` must match its folder name.
- Keep the four-component stack in lockstep: the BDS version, behavior pack,
  MCP server, and the values referenced in these skills (e.g. the behavior
  pack UUID and version) must stay aligned.

## Releasing

Bump `version` in `.claude-plugin/plugin.json` and the marketplace entry, add a
dated section to [CHANGELOG.md](CHANGELOG.md), and tag the commit (`vX.Y.Z`).
The plugin is installed directly from the repository — there is no published
artifact.

## Pull requests

Keep pull requests focused on a single change. Describe what changed and how
you verified it.
