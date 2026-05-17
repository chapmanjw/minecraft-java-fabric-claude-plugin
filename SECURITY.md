# Security Policy

## Reporting a vulnerability

Please report security issues privately through
[GitHub Security Advisories](https://github.com/chapmanjw/minecraft-bedrock-claude-plugin/security/advisories/new)
rather than a public issue. You will receive an acknowledgement within a few days.

## Security model

This repository ships **no executable code** — it is a Claude Code plugin made
of skill and agent instructions (Markdown) plus manifest files (JSON). It does
not bundle or auto-run an MCP server. The security-relevant surface is the
guidance the skills give and the credentials handled while following them.

- **Bearer tokens.** Setup produces two secrets — a client token (for Claude)
  and an agent token (for the behavior pack). The skills instruct that these
  must never be committed and that `.mcp.json` / `.env` files holding them stay
  out of version control; [`.gitignore`](.gitignore) enforces this. The client
  token grants full control of the Minecraft world — treat it as a credential.
- **No bundled MCP config.** The plugin does not ship an active `.mcp.json`.
  [`.mcp.json.example`](.mcp.json.example) is a template only, and it sources
  the token from an environment variable so the committed file stays
  secret-free.
- **Downstream components.** The MCP server and behavior pack this plugin
  guides you to install have their own security models and policies — see
  [`minecraft-bedrock-mcp-server`](https://github.com/chapmanjw/minecraft-bedrock-mcp-server/blob/main/SECURITY.md)
  and
  [`minecraft-bedrock-mcp-behavior-pack`](https://github.com/chapmanjw/minecraft-bedrock-mcp-behavior-pack/blob/main/SECURITY.md).

## Scope

Report issues in this repository's skill or agent instructions (for example,
guidance that would lead a user to expose a token) or in its manifests.
Vulnerabilities in the MCP server or behavior pack belong in those repositories.
