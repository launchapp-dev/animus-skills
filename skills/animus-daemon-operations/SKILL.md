---
name: animus-daemon-operations
description: Start, stop, restart, monitor the Animus daemon — health checks, events, logs, pool sizing, common issues
user_invocable: false
auto_invoke: true
---

# Daemon Operations

The Animus daemon is a background process that dispatches workflows from the queue, supervises plugin processes, and runs cron schedules.

## Starting the Daemon

### Basic start

```bash
animus daemon start
```

Every start runs a plugin preflight first. Default posture is refuse-to-start
when a required role (provider, `subject_kind:task`, `subject_kind:requirement`,
`workflow_runner`, `queue`) is unsatisfied; the error prints the exact
`animus plugin install ...` fix. Pass `--auto-install` to install the
recommended defaults on the fly, or `--skip-preflight` as a dev escape hatch.
`animus daemon preflight` runs the same check as a standalone report.

### Autonomous Mode (recommended)
```bash
animus daemon start --autonomous --auto-run-ready true --pool-size 5
```

Options:
- `--autonomous` — fork to background, detach from terminal
- `--auto-run-ready true` — automatically dispatch ready tasks from queue (default: true)
- `--pool-size N` — max concurrent agent workflows
- `--interval-secs N` — fallback heartbeat in seconds (default: 5). Dispatch is event-driven (subject/queue mutations nudge the daemon, cron fires on precise deadlines); this only bounds pickup of out-of-band edits and paces housekeeping
- `--auto-install` — install missing required plugins from recommended defaults during preflight
- `--skip-preflight` — bypass the plugin preflight (dev only)
- `--startup-cleanup` — run cleanup before scheduling (default: true)
- `--resume-interrupted` — resume interrupted workflows (default: true)
- `--reconcile-stale` — reconcile stale task/workflow state (default: true)
- `--stale-threshold-hours N` — flag in-progress tasks as stale after N hours (default: 24)
- `--max-tasks-per-tick N` — max new workflows to dispatch per tick (default: 2)
- `--phase-timeout-secs N` — override phase timeout

The old `--auto-merge`, `--auto-pr`, `--auto-commit-before-merge`, and
`--idle-timeout-secs` flags were removed in v0.5.x — merge/PR policy lives in
workflow YAML `post_success.merge`, executed by the workflow-runner plugin.

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
animus daemon run --pool-size 2
```

Use foreground mode when debugging startup or plugin issues. `--once` runs a single scheduler tick and exits.

### Restart
```bash
animus daemon restart --autonomous --pool-size 5
```

Graceful stop, then start with the supplied flags (start flags come from the
restart invocation, not the previous run — pass `--autonomous` to restart into
background mode). `--shutdown-timeout-secs N` bounds the wait for in-flight
agents (default 60). Use this after installing/updating plugins or changing
daemon transport settings.

## Pool Size Guidance

Cron workflows each take one pool slot when running. If pool_size < number of simultaneous crons, some will be skipped until capacity frees up. The effective cap is `min(pool_size, ANIMUS_WORKFLOW_CONCURRENCY_MAX)` (default 10).

## Monitoring

### Health

```bash
animus daemon health
```

Returns: status, active agents, pool size/utilization, queue depth, a
`runtime: paused (since <ts>)` / `runtime: active` line (so a paused scheduler
is distinguishable from a stuck one), and one row per discovered plugin from
the live status registry — a plugin disabled by the restart supervisor reports
`Unhealthy` with a cooldown detail and degrades the top-level verdict.
Provider health is rolled up as `provider_plugins_healthy` (the agent-runner
sidecar and its `runner_connected` field were deleted in v0.5.3 — provider
plugins run the CLIs end to end).

### Events

```bash
animus daemon events --limit 50      # bounded history
animus daemon events --follow        # keep streaming until Ctrl-C
```

Event types: `health`, `queue`, `workflow`, `task-state-change` (plus interaction lifecycle events).

### Logs

```bash
animus daemon logs --limit 100 [--search <substr>]
```

Log file location: `~/.animus/<repo-scope>/daemon/daemon.log`

### Live Structured Log Streaming

The single most useful operational tool. One JSONL stream merges everything the daemon, every running workflow, and every spawned agent process emit — phase transitions, LLM calls, queue mutations, schedule fires, plugin crashes — with consistent structure (`ts`, `level`, `cat`, `workflow_id`, `run_id`, `phase`, `msg`, `data`). It replaces tailing five log files at once.

```bash
animus daemon stream --pretty
animus daemon stream --cat phase --level warn
animus daemon stream --workflow wf-abc123 --tail 50
animus daemon stream --run run-xyz789 --no-follow
animus daemon stream --cat llm | jq -r '.data.tokens'
```

**Filters:**
- `--cat <prefix>` — category prefix. Common: `llm`, `phase`, `schedule`, `queue`, `daemon`, `plugin`, `task`, `reconciliation`.
- `--level <debug|info|warn|error>` — minimum level. Default is `info`.
- `--workflow <id>` — narrow to one workflow. Combine with `--run` for a single execution.
- `--run <id>` — narrow to one run.
- `--tail <n>` — replay recent entries before following.
- `--no-follow` — print the tail and exit.
- `--pretty` — colorized human output. Omit for raw JSONL.
- `--full` — with `--pretty`, render full message bodies (LLM output, command stdout) as formatted markdown instead of truncated previews.

There is no `--phase` flag in the current CLI; filter phase entries with
`--cat phase` and pipe JSON to `jq` when needed.

| `--cat` | What you see |
|---------|--------------|
| `llm` | Model calls — provider, tokens in/out, latency, cost per call |
| `phase` | Phase start, transition, verdict, rework loops, exit code |
| `schedule` | Cron fires, schedule-skipped-because-busy, next-fire timestamps |
| `queue` | Enqueue, dispatch, hold, drop, reorder, dependency resolution |
| `plugin` | Plugin spawn/handshake/dispatch, restart supervision, disable cooldowns |
| `daemon` | Pool sizing, autonomous mode toggles, config reloads |
| `task` | State changes (ready → in-progress → done) |
| `reconciliation` | Zombie-workflow and stale in-progress sweeps |

```bash
animus daemon stream --cat schedule --pretty
animus daemon stream --cat phase --level info --pretty
animus daemon stream --cat llm --pretty
```
Each call prints `provider model tokens_in/tokens_out latency cost`. Spot model-routing bugs (Sonnet running on what should be Haiku work) and runaway prompts (token counts climbing each iteration of a rework loop). For aggregates, see `animus cost summary`.

**Single workflow run, end to end:**
```bash
animus daemon stream --workflow wf-abc123 --pretty
```
One stream, every phase of one workflow, nothing else. Pair with `animus output monitor --run-id <id>` in another terminal for the actual stdout/stderr from the spawned agent.

**Error firehose (always-on tab):**
```bash
animus daemon stream --level error --pretty
```

```bash
animus daemon stream --cat phase --tail 1000 --no-follow \
  | jq -r 'select(.data.verdict) | "\(.ts) \(.workflow_id) \(.phase) -> \(.data.verdict)"'
```

### Stream vs other observability surfaces

| Tool | What it streams | When to use |
|------|----------------|-------------|
| `animus daemon stream` | Structured JSONL — daemon + every workflow + every run, one merged stream | Default. Almost always what you want. |
| `animus daemon events` | Coarse event history (`health`, `queue`, `workflow`, `task-state-change`) | Audit trail, MCP-friendly, smaller volume than stream |
| `animus daemon logs` | Raw daemon log file lines | Snapshot a window, no follow |
| `animus events tail` | Workflow lifecycle events (`phase_started`, `workflow_completed`, ...) | Scripting against one workflow's lifecycle |
| `animus output monitor --run-id <id>` | Raw stdout/stderr from one agent process | When the agent itself is misbehaving (timeouts, weird tool errors). Stream tells you *what* phase failed; `output monitor` tells you *why*. |
| `animus output read --run-id <id>` | One-shot dump of a finished run's output | Post-mortem, not live |

**Rule of thumb:** start with `animus daemon stream`. If a phase failed and the JSON `data` doesn't tell you why, drop down to `animus output monitor` for that specific run.

### Status
```bash
animus daemon status
```

`--json` includes `runtime_paused` / `paused_at` while the daemon is reachable.

## Stopping

```bash
animus daemon stop [--shutdown-timeout-secs 60]
```

## Persistent Config

```bash
animus daemon config
animus daemon config --pool-size 3 --auto-run-ready true --interval-secs 10
```

`animus daemon config` is the current mutation command for daemon settings,
persisted at `~/.animus/<repo-scope>/daemon/pm-config.json` and hot-reloaded
once per tick. The MCP name remains `animus.daemon.config-set`.

## MCP Tools

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
| `animus.daemon.config-set` | Update daemon config over MCP |
| `animus.daemon.pause` | Pause dispatch |
| `animus.daemon.resume` | Resume dispatch |

`animus daemon stream`, `restart`, `preflight`, `metrics`, and `clear-logs` are CLI-only — no MCP equivalents.

## Daemon Architecture

Animus resolves a project root, loads repo-scoped runtime state under
`~/.animus/<repo-scope>/`, manages the queue, and dispatches workflow phases
through installed plugins: the `workflow_runner` plugin drives phase
execution, and provider plugins (`animus-provider-claude`, `-codex`,
`-gemini`, ...) spawn the underlying CLIs end to end. There is no separate
agent-runner sidecar process (deleted in v0.5.3).

## Common Issues

### CLAUDECODE Environment Variable
When starting the daemon from inside Claude Code, the `CLAUDECODE` env var is
inherited, which would block spawned `claude` CLI processes. Animus detects
and unsets it before spawning a nested `claude` CLI, so current builds need no
workaround. On older builds: `env -u CLAUDECODE animus daemon start --autonomous ...`

### Daemon Refuses to Start (preflight)
A missing required plugin role fails startup with the exact install command.
```bash
animus daemon preflight          # standalone report (exit 2 = missing roles)
animus plugin install-defaults   # or: animus daemon start --auto-install
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
- Disk full (worktrees and old runs accumulate — `animus workflow prune --older-than 30 --yes` reclaims run/artifact disk)
- A flapping plugin (check `animus plugin status` for restart counts and supervisor cooldowns)
- Lock file contention

### Stale Lock
If the daemon won't start ("daemon already running"):
```bash
animus daemon status                       # check if actually running
animus doctor --fix                        # cleans stale daemon pid/lock files
```

### Orphaned CLI Processes
Provider CLI processes can be orphaned by crashes:
```bash
animus doctor --check orphan_cli_processes        # detect
animus doctor --check orphan_cli_processes --fix  # prune dead tracker entries
```
Live PIDs get a manual `kill` suggestion (the tracker is global across projects).
