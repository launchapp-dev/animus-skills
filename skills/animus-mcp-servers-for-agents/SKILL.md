---
name: animus-mcp-servers-for-agents
description: Connect agents to Context7, package-version, sequential-thinking, memory, GitHub MCP servers
user_invocable: false
auto_invoke: true
---

# MCP Servers for Animus Agents

Animus agents can connect to external MCP servers beyond the built-in `animus` server. This gives agents access to documentation lookup, package version checking, structured reasoning, persistent memory, and GitHub operations.

## Configuring MCP Servers

### 1. Define servers in custom.yaml (top-level)

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
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
```

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

### 3. Reference tools in agent prompts

Tell agents what tools are available and when to use them:

```yaml
implementer:
  system_prompt: |
    TOOLS: You have access to context7 MCP tools. Before writing code
    that uses external libraries, use resolve-library-id and
    get-library-docs to look up the CURRENT API.
```

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
