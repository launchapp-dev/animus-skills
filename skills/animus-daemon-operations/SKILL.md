---
name: animus-daemon-operations
description: Start, stop, monitor the Animus daemon — health checks, events, logs, pool sizing, common issues
user_invocable: false
auto_invoke: true
---

# Daemon Operations

The Animus daemon is a background process that dispatches workflows from the queue, manages agent processes, and runs cron schedules.

## Starting the Daemon

### Basic Start
```bash
animus daemon start
```

### Autonomous Mode (recommended)
```bash
animus daemon start --autonomous --auto-run-ready true --pool-size 5 --interval-secs 10
```

Options:
- `--autonomous` — fork to background, detach from terminal
- `--auto-run-ready true` — automatically dispatch ready tasks from queue (default: true)
- `--pool-size N` — max concurrent agent workflows
- `--interval-secs N` — housekeeping timer interval in seconds (default: 5)
- `--auto-merge true` — auto-merge approved PRs
- `--auto-commit-before-merge true` — commit worktree changes before merge
- `--startup-cleanup` — run cleanup before scheduling (default: true)
- `--resume-interrupted` — resume interrupted workflows (default: true)
- `--reconcile-stale` — reconcile stale task/workflow state (default: true)
- `--stale-threshold-hours N` — flag in-progress tasks as stale after N hours (default: 24)
- `--max-tasks-per-tick N` — max new workflows to dispatch per tick (default: 2)
- `--phase-timeout-secs N` — override phase timeout
- `--idle-timeout-secs N` — override workflow idle timeout
- `--skip-runner` — do not auto-start the runner process

### Foreground Mode
```bash
animus daemon run --pool-size 2 --interval-secs 5
```

Use foreground mode when debugging startup failures or runner issues.

### Pool Size Guidance
- **pool_size=2**: minimal, may starve cron workflows (also the default `--max-tasks-per-tick`)
- **pool_size=5**: good default — 3 crons + 2 task workflows
- **pool_size=8**: heavy workload, needs sufficient API quota

Cron workflows (work-planner, reconciler, pr-reviewer) each take one pool slot when running. If pool_size < number of simultaneous crons, some will be cancelled.

## Monitoring

### Health Check
```bash
animus daemon health
```

Returns: status, active_agents, pool_size, pool_utilization, runner status, queued_tasks.

### Events
```bash
animus daemon events --limit 50
```

Event types: `health`, `queue`, `workflow`, `task-state-change`.

### Logs
```bash
animus daemon logs --limit 100
```

Log file location: `~/.ao/<repo-scope>/daemon/daemon.log`

### Live Structured Log Streaming
```bash
animus daemon stream --pretty
animus daemon stream --cat phase --level warn
animus daemon stream --workflow wf-abc123 --tail 50
animus daemon stream --run run-xyz789 --no-follow
```

Use `animus daemon stream` for the new structured log stream across daemon, workflows, and runs.

Key filters:
- `--cat <prefix>` — category prefix such as `llm`, `schedule`, or `phase`
- `--level <debug|info|warn|error>` — minimum log level
- `--workflow <id>` — narrow to one workflow
- `--run <id>` — narrow to one run
- `--tail <n>` — print the most recent `n` entries before following
- `--no-follow` — print the tail and exit
- `--pretty` — colorized human-readable output instead of raw JSON

### Status
```bash
animus daemon status
```

### Which Stream To Use
- `animus daemon stream` — real-time structured logs from daemon, workflows, and runs
- `animus daemon events` — daemon event history and follow-mode event stream
- `animus output monitor --run-id <id>` — live output for one specific run
- `animus daemon logs` — read recent daemon log lines without following

## Stopping

```bash
animus daemon stop
```

Graceful shutdown waits for in-flight work up to the configured timeout.

### Persistent Config
```bash
animus daemon config
animus daemon config --pool-size 3 --auto-run-ready true --auto-merge false --auto-pr false
```

`animus daemon config` is the current mutation command for daemon settings. The MCP name remains `animus.daemon.config-set`.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `animus.daemon.start` | Start the daemon |
| `animus.daemon.stop` | Stop the daemon |
| `animus.daemon.status` | Basic running/stopped check |
| `animus.daemon.health` | Detailed health metrics |
| `animus.daemon.events` | Recent daemon events |
| `animus.daemon.logs` | Read daemon log |
| `animus.daemon.stream` | Stream structured logs in real time (CLI only) |
| `animus.daemon.agents` | List active agent processes |
| `animus.daemon.config` | Read daemon config |
| `animus.daemon.config-set` | Update daemon config over MCP |
| `animus.daemon.clear-logs` | Clear log file |
| `animus.daemon.pause` | Pause dispatch |
| `animus.daemon.resume` | Resume dispatch |

## Daemon Architecture

Animus resolves a project root, loads repo-scoped runtime state under `~/.ao/<repo-scope>/`, manages the queue, and uses `agent-runner` to launch `claude`, `codex`, or `gemini` for workflow phases.

## Common Issues

### CLAUDECODE Environment Variable
When starting the daemon from inside Claude Code, the `CLAUDECODE` and `CLAUDE_CODE_SESSION_ACCESS_TOKEN` env vars are inherited. These cause spawned `claude` CLI processes to fail.

**Fix**: The daemon strips these at spawn points automatically (as of commit 47d0d192). If running an older build, use:
```bash
env -u CLAUDECODE -u CLAUDE_CODE_SESSION_ACCESS_TOKEN animus daemon start --autonomous ...
```

### Daemon Crashes
Check the log:
```bash
animus daemon logs --limit 100
animus daemon stream --level error --pretty
```

Common causes:
- Disk full (worktrees accumulate)
- Too many agent-runner processes (process leak)
- Lock file contention

### Stale Lock
If the daemon won't start ("daemon already running"):
```bash
# Check if actually running
ps -p $(cat ~/.ao/<repo-scope>/daemon/daemon.lock)
# If not running, the lock is stale — daemon start will clean it up
```

### Process Leak
Agent-runner processes can accumulate across daemon restarts:
```bash
pgrep -f agent-runner | wc -l    # count
animus runner orphans detect
```
