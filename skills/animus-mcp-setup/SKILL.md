---
name: animus-mcp-setup
description: Set up .mcp.json, Claude Code permissions, and connect AI tools to Animus's MCP server
user_invocable: true
auto_invoke: true
---

# MCP Server Setup

Animus exposes all its operations as an MCP (Model Context Protocol) server. This lets any MCP-aware AI assistant (Claude Code, etc.) use Animus tools directly.

## Quick Setup

### Claude Code

After installing Animus via the upstream installer, the binary lives on `PATH` (typically `~/.local/bin/animus`). Verify with:

```bash
which animus    # → /Users/<you>/.local/bin/animus
animus --version
```

Create `.mcp.json` in your project root:

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

The relative `--project-root .` resolves against Claude Code's launch directory, so this same config works for every project. Use an absolute path if you launch Claude from a different working directory.

### Pinning to an absolute binary path

If `animus` is not on `PATH` for the launching process (some editor integrations strip the user `PATH`), pin to the install location returned by `which animus`:

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

After creating `.mcp.json`, restart your AI assistant (e.g., restart Claude Code). Then test:

1. Ask the assistant to call `animus.daemon.status` — it should return running/stopped
2. Ask it to call `animus.task.stats` — it should return task counts
3. If tools aren't available, check that the `animus` binary path is correct

## Available Tool Groups

Once connected, the assistant gets access to:

| Prefix | Tools | Purpose |
|--------|-------|---------|
| `animus.task.*` | 20 tools | Task CRUD, status, assign, checklists, bulk ops, priorities, deadlines |
| `animus.queue.*` | 7 tools | Dispatch queue management |
| `animus.daemon.*` | 11 tools | Daemon lifecycle and monitoring |
| `animus.workflow.*` | 16 tools | Workflow execution, phases, config, checkpoints |
| `animus.output.*` | 6 tools | Run output, tail, monitor, artifacts |
| `animus.requirements.*` | 6 tools | Requirement CRUD and refinement |
| `animus.runner.*` | 4 tools | Runner health and diagnostics |
| `animus.agent.*` | 3 tools | Agent control and status |

## Claude Code Settings

To auto-approve Animus MCP tools, add to `.claude/settings.local.json`. If your MCP server name is `animus`, Claude Code tool ids look like `mcp__animus__animus_task_list`.

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
      "mcp__animus__animus_daemon_config_set",
      "mcp__animus__animus_task_list",
      "mcp__animus__animus_task_get",
      "mcp__animus__animus_task_create",
      "mcp__animus__animus_task_status",
      "mcp__animus__animus_task_update",
      "mcp__animus__animus_task_stats",
      "mcp__animus__animus_task_prioritized",
      "mcp__animus__animus_task_next",
      "mcp__animus__animus_queue_list",
      "mcp__animus__animus_queue_enqueue",
      "mcp__animus__animus_queue_drop",
      "mcp__animus__animus_workflow_list",
      "mcp__animus__animus_workflow_run",
      "mcp__animus__animus_workflow_get",
      "mcp__animus__animus_output_tail",
      "mcp__animus__animus_output_run",
      "mcp__animus__animus_output_phase_outputs",
      "mcp__animus__animus_runner_health",
      "mcp__animus__animus_runner_orphans_detect"
    ]
  },
  "enableAllProjectMcpServers": true
}
```

## Multiple Projects

You can manage multiple projects by running separate MCP servers:

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

Tool names will be prefixed: `mcp__animus-frontend__animus_task_list`, `mcp__animus-backend__animus_task_list`.

## Other AI Tools

Any MCP-compatible tool can connect to Animus. The server uses stdio transport:

```bash
# Manual test — sends JSON-RPC over stdin/stdout
animus --project-root /path/to/project mcp serve
```

The server speaks the MCP protocol (JSON-RPC 2.0 over stdio).

## Troubleshooting

### "MCP server not found"
- Check that the `animus` binary path in `.mcp.json` is absolute and correct
- Verify `animus mcp serve` runs without errors: `animus --project-root . mcp serve`

### Tools not appearing
- Restart your AI assistant after creating/modifying `.mcp.json`
- Check `enableAllProjectMcpServers: true` in Claude settings

### "project_root" errors
- Ensure `--project-root` points to a directory with `.animus/` or a git repo
- Use absolute paths, not relative

### Tool mismatch or missing methods
- Compare against the current MCP surface in `docs/reference/mcp-tools.md`
- Restart the client after upgrading `animus`; most clients cache the tool list for the session
