---
name: animus-daemon-operations
description: Start, stop, monitor the Animus daemon — plugin preflight, health checks, events, logs, pool sizing, common issues
user_invocable: false
auto_invoke: true
---

# Daemon Operations

The Animus daemon dispatches queued subjects, supervises workflow runs, manages
agent processes, runs schedules, and coordinates installed provider, subject,
transport, trigger, and log-storage plugins.

## Preflight

Current Animus runs plugin preflight on daemon startup. Missing provider or
subject backend plugins stop the daemon before work begins.

```bash
animus daemon preflight
animus plugin install-defaults --include-subjects
animus daemon preflight
```

Useful startup flags:

- `--auto-install` — install missing recommended default plugins before continuing.
- `--skip-preflight` — bypass the plugin check for local development only.

## Starting the Daemon

### Basic start

```bash
animus daemon start
```

### Autonomous mode

```bash
animus daemon start --autonomous --auto-run-ready true --pool-size 5 --interval-secs 10
```

Options:

- `--autonomous` — fork to background and detach from the terminal.
- `--auto-run-ready true` — automatically dispatch ready queued subjects.
- `--pool-size N` — max concurrent agent workflows.
- `--interval-secs N` — housekeeping timer interval in seconds.
- `--auto-merge true` — override auto-merge behavior.
- `--auto-pr true` — override PR creation behavior.
- `--auto-commit-before-merge true` — commit worktree changes before merge.
- `--auto-prune-worktrees-after-merge true` — prune completed worktrees after merge.
- `--startup-cleanup true` — run cleanup before scheduling.
- `--resume-interrupted true` — attempt interrupted workflow recovery.
- `--reconcile-stale true` — reconcile stale task/workflow runtime state.
- `--stale-threshold-hours N` — flag stale in-progress work.
- `--max-tasks-per-tick N` — max new workflows to dispatch per scheduler tick.
- `--phase-timeout-secs N` — override phase timeout.
- `--idle-timeout-secs N` — override workflow idle timeout.
- `--skip-runner` — do not auto-start the runner process.

### Foreground mode

```bash
animus daemon run --pool-size 2 --interval-secs 5
animus daemon run --once
```

Use foreground mode for startup failures, plugin preflight debugging, or runner
diagnostics.

## Pool Size Guidance

- `pool_size=2`: minimal, may starve schedules.
- `pool_size=5`: good default for a few schedules plus active task workflows.
- `pool_size=8`: heavy workload; needs enough provider API quota.

If the queue has more pending work than open pool slots, entries remain pending
until capacity frees.

## Monitoring

### Health

```bash
animus daemon health
```

Use this for daemon liveness, pool state, active agents, queue depth, runner
health, and plugin health checks.

### Events

```bash
animus daemon events --limit 50
```

Use events for a lower-volume audit trail.

### Logs

```bash
animus daemon logs --limit 100
animus logs tail --level info --since 1h --limit 100
```

`animus logs tail` reads the active log storage backend, falling back to the
in-tree structured event log when no log-storage plugin is installed.

### Live Structured Log Streaming

`animus daemon stream` is the default live operations view. It merges daemon,
workflow, and run events into one stream with fields such as `ts`, `level`,
`cat`, `workflow_id`, `run_id`, `phase`, `msg`, and `data`.

```bash
animus daemon stream --pretty
animus daemon stream --cat phase --level warn
animus daemon stream --workflow wf-abc123 --tail 50
animus daemon stream --run run-xyz789 --no-follow
animus daemon stream --cat llm | jq -r '.data.tokens'
```

Filters:

- `--cat <prefix>` — category prefix. Common: `llm`, `phase`, `schedule`, `queue`, `runner`, `daemon`, `agent`, `task`.
- `--level <debug|info|warn|error>` — minimum level.
- `--workflow <id-or-ref>` — narrow to one workflow id or ref.
- `--run <id>` — narrow to one run.
- `--tail <n>` — replay recent entries before following.
- `--no-follow` — print the tail and exit.
- `--pretty` — colorized human output. Omit for raw JSONL.

There is no `--phase` flag in the current CLI; filter phase entries with
`--cat phase` and pipe JSON to `jq` when needed.

## Useful Stream Patterns

```bash
animus daemon stream --cat schedule --pretty
animus daemon stream --cat phase --level info --pretty
animus daemon stream --cat llm --pretty
animus daemon stream --level error --pretty
```

```bash
animus daemon stream --cat phase --tail 1000 --no-follow \
  | jq -r 'select(.data.verdict) | "\(.ts) \(.workflow_id) \(.phase) -> \(.data.verdict)"'
```

## Stream vs Other Surfaces

| Tool | Use |
|------|-----|
| `animus daemon stream` | Default live view across daemon, workflows, and runs |
| `animus daemon events` | Coarse audit trail |
| `animus daemon logs` | Snapshot daemon log lines |
| `animus logs tail` | Active log-storage backend |
| `animus output monitor --run-id <id>` | Raw output from one agent process |
| `animus output run --run-id <id>` | One-shot dump of a finished run |

## Stopping

```bash
animus daemon stop
animus daemon stop --shutdown-timeout-secs 120
```

## Persistent Config

```bash
animus daemon config
animus daemon config --pool-size 3 --auto-run-ready true --auto-merge false --auto-pr false
```

MCP names:

| Tool | Purpose |
|------|---------|
| `animus.daemon.start` | Start the daemon |
| `animus.daemon.stop` | Stop the daemon |
| `animus.daemon.status` | Basic running/stopped check |
| `animus.daemon.health` | Detailed health metrics |
| `animus.daemon.events` | Recent daemon events |
| `animus.daemon.logs` | Read daemon log |
| `animus.daemon.agents` | List active agent processes |
| `animus.daemon.config` | Read daemon config |
| `animus.daemon.config-set` | Update daemon config |
| `animus.daemon.pause` | Pause dispatch |
| `animus.daemon.resume` | Resume dispatch |

`daemon stream`, `clear-logs`, `preflight`, and `metrics` are CLI surfaces, not
MCP daemon tools in the current reference.

## Architecture

Animus resolves a project root, loads repo-scoped runtime state under
`~/.animus/<repo-scope>/`, manages the queue, and uses the runner plus installed
provider plugins to execute workflow phases.

## Common Issues

### Missing plugins

```bash
animus daemon preflight
animus plugin install-defaults --include-subjects
```

If the web UI is needed:

```bash
animus plugin install-defaults --include-transports
```

### Claude Code environment variables

When starting the daemon from inside Claude Code, embedded-session environment
variables may be inherited. Current Animus strips the known Claude guard vars at
spawn points. On older builds:

```bash
env -u CLAUDECODE -u CLAUDE_CODE_SESSION_ACCESS_TOKEN animus daemon start --autonomous
```

### Daemon crashes

```bash
animus daemon logs --limit 100
animus logs tail --level error --since 1h
animus daemon stream --level error --pretty
```

Common causes:

- Missing or unhealthy provider/subject plugins.
- Disk full from accumulated worktrees or logs.
- Too many runner processes.
- Lock file contention.

### Process leaks

```bash
pgrep -f agent-runner | wc -l
animus runner orphans detect
animus runner orphans cleanup --run-id <run-id>
```
