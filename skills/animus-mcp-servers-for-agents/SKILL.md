---
name: animus-mcp-servers-for-agents
description: Connect agents to Context7, package-version, sequential-thinking, memory, GitHub MCP servers
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.18"   # animus CLI surface this skill targets
---

# MCP Servers for Animus Agents

Animus agents can connect to external MCP servers beyond the built-in `animus` server. This gives agents access to documentation lookup, package version checking, structured reasoning, persistent memory, and GitHub operations.

## Configuring MCP Servers

### 1. Define servers under the top-level `mcp_servers:` key

Servers go in `.animus/workflows.yaml` or any `.animus/workflows/*.yaml` file:

```yaml
mcp_servers:
  context7:
    command: npx
    args: ["-y", "@upstash/context7-mcp"]
  package-version:
    command: npx
    args: ["-y", "mcp-package-version"]
  sequential-thinking:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  memory:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-memory"]
  github:
    transport: http
    url: https://api.githubcopilot.com/mcp/
    oauth:
      flow: manual_bearer
      bearer_env: GITHUB_MCP_TOKEN
```

(The `@modelcontextprotocol/server-github` npm package is deprecated
upstream — use GitHub's hosted MCP endpoint, as the OAuth example later in
this skill does.)

Each entry picks exactly one transport via `transport:`:

- `stdio` (default when omitted) — requires `command:`; optional `args:` and `env:`. `url` must not be set.
- `http` — requires `url:` (an `http://` or `https://` endpoint). `command`, `args`, and `env` must not be set.

```yaml
mcp_servers:
  my-remote:
    transport: http
    url: https://mcp.example.com/mcp
```

Optional per-server fields: `config:` (arbitrary key-value config passed to the server) and `tools:` (declared tool-name list — schema-validated but not currently enforced as a runtime filter, so don't rely on it to restrict access).

Secrets in `env:` blocks: use `${VAR}` interpolation (`${VAR:-default}`, `${VAR:?error}`) rather than literal values. Resolution checks the process environment first, then OS keychain entries set via `animus secret set <KEY>` (preferred for credentials).

### 2. Bind servers to agent profiles

```yaml
agents:
  implementer:
    mcp_servers: ["animus", "context7"]
  researcher:
    mcp_servers: ["animus", "context7", "package-version", "memory"]
  reviewer:
    mcp_servers: ["animus", "github", "sequential-thinking"]
```

Agents only get access to the servers listed in their `mcp_servers` array.

### How servers reach the provider

The resolved server set is passed down to the provider plugins themselves:
it rides the provider contract for `animus agent run` and `animus chat` to
any provider plugin that declares `supports_mcp` (manifest field, plugin
protocol 1.2.0; undeclared defaults true), and on the workflow path via
workflow-runner v0.4.3+. Secret-bearing servers (all OAuth flows) are
rewritten to `animus-mcp-proxy` stdio entries before pass-down — tokens
never reach CLI configs or argv. The name `animus` always resolves to the
built-in `animus mcp serve` stdio surface.

For deterministic, LLM-free access from scripts and command phases, use
`animus mcp tools <server>` (list) and
`animus mcp call <server> <tool> --args '<json>'` (v0.7.0-rc.9+) — OAuth
servers route through the proxy with the bearer injected, never printed.

### 3. Reference tools in agent prompts

Tell agents what tools are available and when to use them:

```yaml
implementer:
  system_prompt: |
    TOOLS: You have access to context7 MCP tools. Before writing code
    that uses external libraries, use resolve-library-id and
    get-library-docs to look up the CURRENT API.
```

## OAuth-Protected HTTP Servers

http servers can carry an `oauth:` block. Flows: `authorization_code` (interactive browser login via `animus mcp auth <server>`), `client_credentials`, `refresh_token`, `manual_bearer`. Credential material is read from env vars via `*_env` fields (`client_id_env`, `client_secret_env`, `refresh_token_env`, `bearer_env`), never from YAML. Other fields: `token_url`, `scopes`, `audience`, `cache` (default true), and — for `authorization_code` providers without Dynamic Client Registration — a pre-registered `client_id` plus `client_secret_env` for confidential clients (v0.7.0-rc.12+; resolved from process env, then the `animus secret` keychain).

```yaml
mcp_servers:
  github:
    transport: http
    url: https://api.githubcopilot.com/mcp/
    oauth:
      flow: authorization_code
      scopes: [repo, read:user]
```

CLI: `animus mcp auth <server>` (login), `animus mcp auth-status`, `animus mcp auth-logout <server>`. Full shape and validation rules: `docs/reference/mcp-oauth.md` in animus-cli.

## Phase-Level Bindings

Top-level `phase_mcp_bindings` attaches servers to specific phases (mainly used by pack overlays):

```yaml
phase_mcp_bindings:
  research:
    servers: [context7]
```

Server names must resolve against the `mcp_servers:` map. See the pack-authoring docs for how packs ship these.

Skills are a third attachment path (v0.5.14): a skill definition can declare `mcp_servers`, and when a workflow phase's `skills:` (or the executing agent profile's `skills:`) resolve and apply, the skill's declared servers join the phase contract the same way `phase_mcp_bindings` do — resolved by name against the `mcp_servers:` map; unknown names warn and are skipped.

## Per-Run Wiring (CLI)

`animus agent run` and `animus chat send` resolve the server set as: the
`--agent` profile's `mcp_servers` ∪ the `--skill`'s `mcp_servers` ∪
`--mcp-server <name>` additions (repeatable; the name must exist in the
project's `mcp_servers` map, or `animus` for the built-in surface), minus the
built-in `animus` server when `--no-animus-mcp` is passed. When no profile or
skill names any server, the baseline set is just the built-in `animus` server.
A tool whose CLI cannot speak MCP receives no MCP wiring.

## Recommended Servers

### Context7 (`@upstash/context7-mcp`) — HIGH priority

Up-to-date, version-specific library documentation. Prevents hallucinated APIs.

**Tools:** `resolve-library-id`, `get-library-docs`

**Best for:** implementer, architect, docs-writer, researcher

**Why:** LLM training data goes stale. React Router 7, Hono, Drizzle, and Better-Auth all move fast. Context7 gives agents current docs instead of guessing.

### Package Version Check (`mcp-package-version`) — MEDIUM priority

Checks latest stable versions from npm registry.

**Tools:** Check npm/PyPI/Maven/Go versions, bulk check multiple packages.

**Best for:** researcher, auditor

**Why:** Prevents agents from adding outdated dependency versions.

### Sequential Thinking (`@modelcontextprotocol/server-sequential-thinking`) — MEDIUM priority

Helps agents break down complex problems step by step.

**Best for:** architect (dependency graphs), product-owner (feature evaluation), reviewer (code review), auditor (security analysis)

**Why:** Complex reasoning tasks benefit from structured step-by-step thinking.

### Memory (`@modelcontextprotocol/server-memory`) — MEDIUM priority

Persistent memory across agent runs. Agents can remember what they reviewed last time.

**Best for:** planner, researcher, scanner, product-owner, architect, reconciler

**Why:** Without memory, each cron run starts from scratch. The PO can't remember what it reviewed, the researcher re-checks the same packages, the reconciler re-analyzes the same tasks.

### GitHub (`@modelcontextprotocol/server-github`) — LOW priority

Structured GitHub operations as MCP tools.

**Best for:** planner, reviewer, reconciler

**Why:** Mostly redundant with `gh` CLI (already in tools_allowlist). Useful for structured PR data (reviews, checks, mergeable status) without parsing CLI output.

### Skipped Servers

- **Filesystem MCP** — redundant with Claude Code's native Read/Write/Glob/Grep
- **Fetch MCP** — redundant with WebFetch already in tools_allowlist
- **Rust-docs MCP** — only useful for Rust projects
- **SonarQube MCP** — requires external infrastructure

## Agent ↔ Server Matrix

```
                    animus  ctx7  pkg-ver  seq-think  memory  github
planner             x                                x      x
implementer         x    x
reviewer            x                     x                x
researcher          x    x      x                   x
scanner             x                               x
product-owner       x                     x         x
architect           x    x                x         x
auditor             x           x         x
docs-writer         x    x
reconciler          x                               x      x
devops              x
```

## Tools Allowlist

MCP server tools are separate from the `tools_allowlist`. The allowlist controls which shell programs command phases can invoke. MCP tools are controlled per-agent via the `mcp_servers` binding.

To enable web search for agents, add to `tools_allowlist`:
```yaml
tools_allowlist:
  - WebSearch
  - WebFetch
```
