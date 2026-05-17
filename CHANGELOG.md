# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-05-16

Initial release. Pairs with
[`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server)
v0.1.0 and
[`minecraft-bedrock-mcp-behavior-pack`](https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack)
v0.1.0 — install all three together.

### Added

- Plugin manifest (`.claude-plugin/plugin.json`) and marketplace manifest
  (`.claude-plugin/marketplace.json`) — the repo is installable directly as a
  Claude Code plugin marketplace.
- Four guided setup skills, run in order, that walk a user through standing up
  the whole stack: `setup-bedrock-server`, `setup-minecraft-world`,
  `setup-mcp-server`, and `connect-claude`.
- `minecraft-mcp-setup` agent — orchestrates all four setup phases end to end
  in one continuous session, with the setup skills preloaded as per-phase
  procedures.
- `.mcp.json.example` — a secret-free reference template for registering the
  `minecraft-bedrock` MCP server with Claude.
- CI workflow that validates the plugin, marketplace, skill, and agent files.
