---
name: animus-mcp-setup
description: Set up .mcp.json, Claude Code permissions, and connect AI tools to Animus's MCP server
user_invocable: true
auto_invoke: true
---

# MCP Server Setup

Animus exposes its operations as an MCP server. MCP-aware assistants can call
typed tools instead of shelling out to `animus`.

## Quick Setup

After installing Animus, verify the binary path:

```bash
which animus
animus --version
```

Create `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "animus": {
      "command": "animus",
      "args": ["--project-root", ".", "mcp", "serve"]
    }
  }
}
```

The relative `--project-root .` resolves against the assistant's launch
directory. Use an absolute path if the assistant is launched elsewhere.

If the launch environment strips `PATH`, pin the binary returned by
`which animus`:

```json
{
  "mcpServers": {
    "animus": {
      "command": "/Users/you/.local/bin/animus",
      "args": ["--project-root", "/Users/you/my-project", "mcp", "serve"]
    }
  }
}
```

## Verifying the Connection

Restart the assistant after creating or editing `.mcp.json`, then test:

1. Ask the assistant to call `animus.daemon.status` — it should return running/stopped
2. Ask it to call `animus.subject.list` with `kind=task` — it should return the task list
3. If tools aren't available, check that the `animus` binary path is correct

## Available Tool Groups

| Prefix | Tools | Purpose |
|--------|-------|---------|
| `animus.subject.*` | 6 tools | Task and requirement CRUD via `kind=task` / `kind=requirement` (replaced `animus.task.*` / `animus.requirements.*` in v0.4.4) |
| `animus.queue.*` | 7 tools | Dispatch queue management (enqueue, hold, release, drop, reorder — all support bulk ids) |
| `animus.daemon.*` | 11 tools | Daemon lifecycle and monitoring |
| `animus.workflow.*` | 16 tools | Workflow execution, phases, config, checkpoints |
| `animus.output.*` | 6 tools | Run output, tail, monitor, artifacts |
| `animus.agent.*` | 12 tools | Agent control, status, memory, messages, ask/approval |
| `animus.skill.*` | 5 tools | Skill list, get, search, create, update |
| `animus.memory.*` | 4 tools | Top-level agent memory |
| `animus.plugin.*` | 9 tools | Plugin control + marketplace |
| `animus.logs.tail` | 1 tool | Log storage backend tail |

The current server registers 79 built-in tools total; see `docs/reference/mcp-tools.md` in the Animus repo for the authoritative list.

## Claude Code Settings

To auto-approve Animus MCP tools, add to `.claude/settings.local.json`. If your MCP server name is `animus`, Claude Code tool ids look like `mcp__animus__animus_subject_list`.

```json
{
  "permissions": {
    "allow": [
      "mcp__animus__animus_daemon_health",
      "mcp__animus__animus_daemon_status",
      "mcp__animus__animus_daemon_start",
      "mcp__animus__animus_daemon_stop",
      "mcp__animus__animus_daemon_events",
      "mcp__animus__animus_daemon_logs",
      "mcp__animus__animus_daemon_agents",
      "mcp__animus__animus_daemon_config",
      "mcp__animus__animus_daemon_config-set",
      "mcp__animus__animus_subject_list",
      "mcp__animus__animus_subject_get",
      "mcp__animus__animus_subject_create",
      "mcp__animus__animus_subject_status",
      "mcp__animus__animus_subject_update",
      "mcp__animus__animus_subject_next",
      "mcp__animus__animus_queue_list",
      "mcp__animus__animus_queue_enqueue",
      "mcp__animus__animus_queue_drop",
      "mcp__animus__animus_workflow_list",
      "mcp__animus__animus_workflow_run",
      "mcp__animus__animus_workflow_get",
      "mcp__animus__animus_output_tail",
      "mcp__animus__animus_output_run",
      "mcp__animus__animus_output_phase-outputs",
      "mcp__animus__animus_plugin_list",
      "mcp__animus__animus_daemon_health"
    ]
  },
  "enableAllProjectMcpServers": true
}
```

Keep destructive tools such as cancel, pause, queue drop, plugin install, and
plugin uninstall on manual approval unless the project policy explicitly allows
them.

## Multiple Projects

Run separate MCP servers with distinct names:

```json
{
  "mcpServers": {
    "animus-frontend": {
      "command": "animus",
      "args": ["--project-root", "/path/to/frontend", "mcp", "serve"]
    },
    "animus-backend": {
      "command": "animus",
      "args": ["--project-root", "/path/to/backend", "mcp", "serve"]
    }
  }
}
```

Tool names will be prefixed: `mcp__animus-frontend__animus_subject_list`, `mcp__animus-backend__animus_subject_list`.

## Manual Test

```bash
animus --project-root /path/to/project mcp serve
```

The server speaks JSON-RPC 2.0 over stdio.

`animus mcp memory` starts the separate memory-context MCP server that
workflow phases use.

## OAuth-Protected Upstream Servers

For MCP servers that require OAuth (configured with an `oauth:` block in
workflow config):

```bash
animus mcp auth <server>        # browser login; tokens go to the OS keychain
animus mcp auth-status          # show authenticated servers and token expiry
animus mcp auth-logout <server> # delete stored tokens
```

At run time Animus launches the `animus-mcp-proxy` stdio bridge automatically
for these servers, so agents never see tokens. Details live in
`docs/reference/mcp-oauth.md` in the animus-cli repo.

## Troubleshooting

### MCP server not found

- Check that the `animus` binary path in `.mcp.json` is correct.
- Verify `animus --project-root . mcp serve` starts without errors.

### Tools not appearing

### "project_root" errors
- Ensure `--project-root` points to a directory with `.animus/` or a git repo
- Use absolute paths, not relative

### Tool mismatch or missing methods

- Compare against `docs/reference/mcp-tools.md` in the animus-cli repo.
- Translate stale `animus.task.*` and `animus.requirements.*` calls to
  `animus.subject.*`.
