---
name: animus-mcp-setup
description: Set up .mcp.json, Claude Code permissions, and connect AI tools to Animus's MCP server
user_invocable: true
auto_invoke: true
animus_version: "0.5.15"   # animus CLI surface this skill targets
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

### Serve flags

`animus mcp serve` accepts three flags worth knowing:

- `--management` — also exposes the `animus.interactions.*` inbox tools
  (list/answer pending agent questions and approvals). Off by default so
  agent-injected servers can never answer their own approvals. Use it for
  your own assistant's `.mcp.json` if you want to triage the escalation
  inbox over MCP (the CLI alternative is `animus agent interactions`).
- `--agent-id <ID>` — pins the identity used by the blocking
  `animus.agent.ask` / `animus.agent.request_approval` tools (env fallback:
  `ANIMUS_MCP_AGENT_ID`), so a payload `agent_id` cannot select a looser
  `approval_policy`.
- `--workflow-id <ID>` — pins the workflow context and flips the escalation
  tools' default wait mode from block to suspend (env fallback:
  `ANIMUS_MCP_WORKFLOW_ID`).

The pins are appended automatically on the agent-injection paths
(`animus agent run --agent`, workflow phases); set them yourself only when
hand-wiring a server for a known agent.

Do not put API keys in `.mcp.json` `env` blocks. Store credentials in the OS
keychain with `animus secret set <KEY>` (preferred, v0.5.8+); workflow YAML
`${VAR}` interpolation and plugin spawning check keychain entries when the
env var is unset.

## Verifying the Connection

Restart the assistant after creating or editing `.mcp.json`, then test:

1. Call `animus.daemon.status`.
2. Call `animus.subject.list` with `{ "kind": "task", "limit": 5 }`.
3. Call `animus.workflow.config.validate`.

If subject tools fail with a missing backend, the error's `remediation`
payload carries the exact install command. Typically:

```bash
animus plugin install-defaults
animus daemon preflight
```

(Flagless `install-defaults` installs the active flavor's full required set —
provider, both subject backends, transport, workflow runner, queue — as of
v0.5.14.)

## Available Tool Groups

86 built-in tools in management mode; the default server exposes 84 (the two
`animus.interactions.*` tools are gated behind `--management`).

| Prefix | Tools | Purpose |
|--------|-------|---------|
| `animus.agent.*` | 12 | Agent runs, profiles, memory, messages, ask/approval escalation |
| `animus.interactions.*` | 2 | List/answer pending agent questions and approvals (`mcp serve --management` only) |
| `animus.daemon.*` | 12 | Daemon lifecycle, monitoring, and the `observe` front-door |
| `animus.cost.*` | 1 | Budget-cap breach log (`animus.cost.decisions`) |
| `animus.subject.*` | 8 | Task, requirement, and external subject CRUD plus batch create/update |
| `animus.queue.*` | 7 | Dispatch queue management (bulk `subject_ids[]` on hold/release/drop) |
| `animus.workflow.*` | 17 | Workflow execution, phases, gate approve/reject, config, checkpoints |
| `animus.output.*` | 6 | Run output, JSONL, monitor, artifacts |
| `animus.logs.*` | 1 | Active log backend tailing |
| `animus.skill.*` | 5 | Skill list, resolve, search, create, update (project or user scope) |
| `animus.memory.*` | 4 | Project-scoped agent memory |
| `animus.plugin.*` | 9 | Plugin control and marketplace tools |
| `animus.tools.*` | 2 | Tool discovery: `search` (ranked intent search) and `list` (grouped catalog) |

`animus.task.*` and `animus.requirements.*` are gone — use `animus.subject.*`
with `kind: "task"` or `kind: "requirement"`. The `animus.runner.*` tools were
removed in v0.5.13: use `animus.daemon.health` (`provider_plugins_healthy`)
for runner/provider health and the CLI's `animus doctor --fix` for orphan
cleanup.

## Claude Code Settings

To auto-approve selected Animus MCP tools, add entries like these to
`.claude/settings.local.json`. If your MCP server name is `animus`, Claude
Code tool ids look like `mcp__animus__animus_subject_list` (dots become
underscores; hyphens inside a verb are kept, e.g.
`mcp__animus__animus_daemon_config-set`).

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
      "mcp__animus__animus_daemon_observe",
      "mcp__animus__animus_daemon_agents",
      "mcp__animus__animus_daemon_config",
      "mcp__animus__animus_subject_list",
      "mcp__animus__animus_subject_get",
      "mcp__animus__animus_subject_create",
      "mcp__animus__animus_subject_update",
      "mcp__animus__animus_subject_status",
      "mcp__animus__animus_subject_next",
      "mcp__animus__animus_queue_list",
      "mcp__animus__animus_queue_enqueue",
      "mcp__animus__animus_workflow_list",
      "mcp__animus__animus_workflow_run",
      "mcp__animus__animus_workflow_get",
      "mcp__animus__animus_output_tail",
      "mcp__animus__animus_output_run",
      "mcp__animus__animus_output_phase-outputs",
      "mcp__animus__animus_cost_decisions",
      "mcp__animus__animus_logs_tail",
      "mcp__animus__animus_plugin_list",
      "mcp__animus__animus_skill_search",
      "mcp__animus__animus_tools_search",
      "mcp__animus__animus_tools_list"
    ]
  },
  "enableAllProjectMcpServers": true
}
```

Keep destructive tools such as cancel, pause, queue drop, `daemon config-set`,
plugin install, and plugin uninstall on manual approval unless the project
policy explicitly allows them.

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

At run time Animus rewrites these servers to the `animus-mcp-proxy` stdio
bridge automatically, so tokens never reach CLI configs, `.mcp.json`, or
argv. Details live in `docs/reference/mcp-oauth.md` in the animus-cli repo.

## Troubleshooting

### MCP server not found

- Check that the `animus` binary path in `.mcp.json` is correct.
- Verify `animus --project-root . mcp serve` starts without errors.

### Tools not appearing

- Restart the assistant after changing `.mcp.json`.
- Check `enableAllProjectMcpServers: true` in Claude settings.
- Restart again after upgrading `animus`; many clients cache the tool list.
- `animus.interactions.*` only appear with `--management`.

### Subject calls fail

- Read the error's `remediation.install_command` — it names the exact fix.
- Run `animus plugin install-defaults`.
- Run `animus daemon preflight` and install any reported missing plugins.

### Tool mismatch or missing methods

- Call `animus.tools.search` with intent keywords, or `animus.tools.list`
  for the full live catalog — results always reflect the serving binary.
- Compare against `docs/reference/mcp-tools.md` in the animus-cli repo.
- Translate stale `animus.task.*` / `animus.requirements.*` calls to
  `animus.subject.*`, and drop stale `animus.runner.*` calls (removed).

## Differences on installed v0.5.14

This skill documents the **v0.5.15** surface (see `animus_version`). On an installed **v0.5.14**, the following differ:

- The tool-count table reflects v0.5.15 (86 / 84). On v0.5.14 it is 83 / 81, and `animus.cost.decisions`, `animus.workflow.phase.reject`, and `animus.daemon.observe` are not registered.
