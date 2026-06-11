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

1. Call `animus.daemon.status`.
2. Call `animus.subject.list` with `{ "kind": "task", "limit": 5 }`.
3. Call `animus.workflow.config.validate`.

If subject tools fail with a missing backend, install defaults and rerun
preflight:

```bash
animus plugin install-defaults --include-subjects
animus daemon preflight
```

## Available Tool Groups

| Prefix | Tools | Purpose |
|--------|-------|---------|
| `animus.agent.*` | 12 | Agent runs, profiles, memory, messages, ask/approval |
| `animus.interactions.*` | 2 | Answer pending agent questions (`mcp serve --management` only) |
| `animus.daemon.*` | 11 | Daemon lifecycle and monitoring |
| `animus.subject.*` | 6 | Task, requirement, and external subject CRUD |
| `animus.queue.*` | 7 | Dispatch queue management |
| `animus.workflow.*` | 16 | Workflow execution, phases, config, checkpoints |
| `animus.output.*` | 6 | Run output, JSONL, monitor, artifacts |
| `animus.runner.*` | 3 | Runner health and orphan cleanup |
| `animus.logs.*` | 1 | Active log backend tailing |
| `animus.skill.*` | 5 | Skill list, resolve, search, create, update |
| `animus.memory.*` | 4 | Project-scoped agent memory |
| `animus.plugin.*` | 9 | Plugin control and marketplace tools |

`animus.task.*` and `animus.requirements.*` are gone. Use
`animus.subject.*` with `kind: "task"` or `kind: "requirement"`.

## Claude Code Settings

To auto-approve selected Animus MCP tools, add entries like these to
`.claude/settings.local.json`. If your MCP server name is `animus`, Claude
Code tool ids look like `mcp__animus__animus_subject_list`.

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
      "mcp__animus__animus_subject_list",
      "mcp__animus__animus_subject_get",
      "mcp__animus__animus_subject_create",
      "mcp__animus__animus_subject_update",
      "mcp__animus__animus_subject_status",
      "mcp__animus__animus_subject_next",
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
      "mcp__animus__animus_runner_orphans_detect",
      "mcp__animus__animus_logs_tail",
      "mcp__animus__animus_plugin_list",
      "mcp__animus__animus_skill_search"
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

Tool ids include the server name, for example
`mcp__animus-frontend__animus_subject_list`.

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

- Restart the assistant after changing `.mcp.json`.
- Check `enableAllProjectMcpServers: true` in Claude settings.
- Restart again after upgrading `animus`; many clients cache the tool list.

### Subject calls fail

- Run `animus plugin install-defaults --include-subjects`.
- Run `animus daemon preflight` and install any reported missing plugins.

### Tool mismatch or missing methods

- Compare against `docs/reference/mcp-tools.md` in the animus-cli repo.
- Translate stale `animus.task.*` and `animus.requirements.*` calls to
  `animus.subject.*`.
