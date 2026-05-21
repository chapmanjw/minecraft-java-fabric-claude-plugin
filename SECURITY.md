# Security Policy

## Reporting a vulnerability

Please report security issues privately through
[GitHub Security Advisories](https://github.com/chapmanjw/minecraft-java-fabric-claude-plugin/security/advisories/new)
rather than a public issue. You will receive an acknowledgement within a few days.

## Security model

This repository ships **no executable code** — it is a Claude Code plugin made
of skill and agent instructions (Markdown) plus manifest files (JSON). It does
not bundle or auto-run an MCP server. The security-relevant surface is the
guidance the skills give and the credentials handled while following them.

- **The bearer token.** A single-player install on `127.0.0.1` needs no token —
  the mod binds to loopback only. A dedicated/remote server requires
  authentication: the mod generates one **bearer token** on first boot and logs
  it once. The skills instruct that this token must never be committed and that
  the `.mcp.json` / config files holding it stay out of version control;
  [`.gitignore`](.gitignore) enforces this. The token grants full control of the
  Minecraft world — treat it as a credential.
- **No bundled MCP config.** The plugin does not ship an active `.mcp.json`.
  [`.mcp.json.example`](.mcp.json.example) is a template only; for remote setups
  it sources the token from an environment variable so the committed file stays
  secret-free.
- **Remote exposure.** The mod refuses to bind to a non-loopback address unless
  the operator explicitly opts in *and* enables authentication, and it warns
  when running without TLS. The skills follow that posture: localhost by
  default, auth + (ideally) TLS before any LAN/internet exposure.
- **Downstream component.** The MCP server is embedded in the
  [`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server)
  Fabric mod, which has its own security model and policy — see that
  repository's `SECURITY.md` and `docs/security.md`.

## Scope

Report issues in this repository's skill or agent instructions (for example,
guidance that would lead a user to expose a token) or in its manifests.
Vulnerabilities in the MCP server / Fabric mod belong in that repository.
