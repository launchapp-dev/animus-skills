---
name: animus-daemon-operations
description: Start, stop, restart, monitor the Animus daemon — plugin preflight, health verdict, observe front-door, events, logs, metrics, pool sizing, common issues
user_invocable: false
auto_invoke: true
animus_version: "0.5.21"   # animus CLI surface this skill targets
---

# Daemon Operations

The Animus daemon dispatches queued subjects, supervises workflow runs, manages
agent processes, runs schedules, and coordinates installed provider, subject,
workflow_runner, queue, transport, trigger, and log-storage plugins.

## Preflight

The daemon runs plugin preflight on every startup and refuses to start when a
required role is unsatisfied: at least one provider,
`at_least_one_subject_backend` (any installed `subject_backend` plugin — as
of v0.5.20 specific kinds are no longer hard-coded), `workflow_runner`, and
`queue`.

```bash
animus daemon preflight
animus plugin install-defaults --flavor default --yes
animus daemon preflight
```

`animus plugin install-defaults` (no flags) installs the flavor's full
required set — provider, both subject backends, transport, workflow runner,
and queue — so a single pass covers every preflight role.
`--include-recommended` adds the recommended set.

Preflight behavior:

- When more than one role is missing, the failure output prints per-role
  `animus plugin install ...` commands plus the single composed fix
  (`animus plugin install-defaults --flavor default --yes`).
- Non-fatal WARNING when the installed `workflow_runner` plugin is below the
  skill payload floor (v0.4.2) — such a runner silently ignores phase skills.
  Fix with `animus plugin update`.
- Exit codes: `0` all roles satisfied, `2` at least one role missing (fix
  command in the error message), `1` transient discovery failure.

Useful startup flags:

- `--auto-install` — install missing recommended default plugins before continuing.
- `--skip-preflight` — bypass the plugin check for local development only.

## Starting the Daemon

### Background (default)

```bash
animus daemon start
animus daemon start --pool-size 5
```

`animus daemon start` **always** detaches: it spawns the daemon as a
background process, prints the daemon pid and the background log path
(`~/.animus/<repo-scope>/daemon/daemon.log`), and returns. Starting while a
daemon is already running is idempotent — it reports the running pid instead
of failing. The legacy `--autonomous` flag was removed — `daemon start` now
errors on it as an unknown argument.

The daemon is **queue-only**: it executes explicitly-enqueued entries
(`animus queue enqueue`) plus cron `schedules:` occurrences. It never scans
the subject backend for Ready subjects, and a `ready` status alone does not
cause pickup.

Scheduler/start options:

- `--pool-size N` (alias `--max-agents`) — max concurrent agent workflows.
- `--interval-secs N` — fallback heartbeat (see below), not dispatch latency.
- `--startup-cleanup true|false` — run cleanup before scheduling (default true).
- `--resume-interrupted true|false` — attempt interrupted workflow recovery (default true).
- `--reconcile-stale true|false` — recover stale in-progress tasks/runs on startup (default true).
- `--stale-threshold-hours N` — flag stale in-progress work.
- `--max-tasks-per-tick N` — max new workflows to dispatch per scheduler pass.
- `--phase-timeout-secs N` — override phase timeout.
- `--auto-install` / `--skip-preflight` — preflight controls (above).

The old `--auto-merge` / `--auto-pr` / `--auto-commit-before-merge` /
`--auto-prune-worktrees-after-merge` / `--idle-timeout-secs` flags were
removed. Git automation (commit / push / PR / merge) is now expressed as
`command:` phases running `git` / `gh` in the workflow — `post_success.merge`
was removed and now fails to parse.

### Restart

```bash
animus daemon restart
animus daemon restart --shutdown-timeout-secs 120 --pool-size 5
```

Gracefully stops the running daemon, then starts it again detached. If the
daemon is not running, it just starts. Accepts every `daemon start` flag —
flags come from the restart invocation, not the previous run.

### Foreground mode (dev/debug)

```bash
animus daemon run --pool-size 2
animus daemon run --once
```

`animus daemon run` runs in the current foreground process (Ctrl-C to stop);
`--once` runs a single scheduler tick and exits. Use it for startup failures
and plugin preflight debugging.

## Event-Driven Scheduler

The daemon main loop is event-driven, not polling. A dispatch pass runs on:

1. **`daemon/nudge` control messages** — sent fire-and-forget by
   `animus subject create/update/status` and `animus queue enqueue/release`
   (and their MCP equivalents); also fires on workflow/phase completion
   events and workflow-config hot-reloads. Pickup is typically sub-second.
2. **Cron deadlines** — the loop sleeps until the next compiled `schedules:`
   occurrence, so cron fires on time.
3. **Fallback heartbeat (`interval_secs`)** — the maximum sleep when no event
   arrives. It bounds pickup of out-of-band state edits made without the
   CLI/MCP and paces heavier housekeeping legs (zombie/stale reconciliation),
   which run at most once per heartbeat period.

See `docs/reference/configuration.md#scheduler-wake-model`.

## Pool Size Guidance

- `pool_size=2`: minimal, may starve schedules.
- `pool_size=5`: good default for a few schedules plus active task workflows.
- `pool_size=8`: heavy workload; needs enough provider API quota.

If the queue has more pending work than open pool slots, entries remain pending
until capacity frees.

## Monitoring

### Observe (front-door)

```bash
animus daemon observe                       # data-source matrix + last ~20 merged lines
animus daemon observe --follow              # live: delegates to daemon stream --pretty
animus daemon observe --since 2h            # merged events + logs window, source-labeled
animus daemon observe --source events --limit 50
animus daemon observe --workflow wf-abc --since 1d
animus daemon observe --json
```

`daemon observe` is a router over the existing `events` / `logs` / `stream`
surfaces — start here when you don't know which surface to reach for.
`--follow` cannot be combined with `--since` or a non-stream `--source`.

### Health

```bash
animus daemon health
```

Human output leads with a one-line verdict: `healthy: true`,
`healthy: true (paused)` (a paused runtime is deliberate, not a failure), or
`healthy: false` (daemon down/crashed, critical subsystem failing, or any
plugin unhealthy — including supervisor-disabled plugins). Also reports:

- `runtime_paused` (+ `paused_at`) — distinguish paused from stuck.
- One row per plugin from the live status registry, with supervisor state:
  a plugin disabled by the restart supervisor (default budget: 3 restarts in
  60s, then 5-minute cooldown) shows restart count and `cooldown until <ts>`.
- `budget_enforcement: {enabled, last_sweep_at}` plus a breaches-in-last-24h
  rollup with the worst offender.

### Metrics

`animus daemon metrics` is a subcommand group:

```bash
animus daemon metrics                       # live counters/gauges/histograms
animus daemon metrics --watch --interval-secs 5 --pretty
animus daemon metrics status                # telemetry opt-in state, install id, buffer
animus daemon metrics enable
animus daemon metrics disable
animus daemon metrics flush
animus daemon metrics cleanup
```

Bare `daemon metrics` works offline: with no daemon it prints
`daemon not running; live metrics unavailable` plus the telemetry summary and
exits 0. Only `--watch` still requires a running daemon. The telemetry verbs
(folded in from the removed top-level `animus metrics` group) always work
offline.

### Events

```bash
animus daemon events --limit 50             # one-shot: print and exit
animus daemon events --follow               # stream until Ctrl-C
```

`daemon events` is one-shot by default; `--follow` opts into streaming.
Use events for a lower-volume audit trail.

### Logs

```bash
animus daemon logs --limit 100
animus logs tail --level info --since 1h --limit 100
```

`animus logs tail` reads the active log storage backend, falling back to the
in-tree structured event log when no log-storage plugin is installed.

### Live Structured Log Streaming

`animus daemon stream` is the full-fidelity live view. It merges daemon,
workflow, and run events into one stream with fields such as `ts`, `level`,
`cat`, `workflow_id`, `run_id`, `phase`, `msg`, and `data`. Neither
`daemon stream` nor `daemon events --follow` loses records across log
rotation.

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
- `--full` — with `--pretty`, render full message bodies (LLM output, command stdout) as formatted markdown instead of truncated previews.

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
| `animus daemon observe` | Front-door: routes to the right surface; merged recent window |
| `animus daemon stream` | Full-fidelity live view across daemon, workflows, and runs |
| `animus daemon events` | Coarse audit trail (one-shot; `--follow` to stream) |
| `animus daemon logs` | Snapshot daemon log lines |
| `animus logs tail` | Active log-storage backend |
| `animus events tail` | Workflow lifecycle events (phase/workflow started/completed/failed) |
| `animus output monitor --run-id <id>` | Raw output from one agent process |
| `animus output read --run-id <id>` | One-shot dump of a finished run |

## Stopping

```bash
animus daemon stop
animus daemon stop --shutdown-timeout-secs 120
```

## Persistent Config

```bash
animus daemon config
animus daemon config --pool-size 3 --interval-secs 60
animus daemon config --max-daily-usd 50 --silent-threshold-mins 20
```

Hot-reloaded settings: `--pool-size`, `--interval-secs`,
`--max-tasks-per-tick`, `--stale-threshold-hours`, `--phase-timeout-secs`,
plus notification config (`--notification-config-json` /
`--notification-config-file` / `--clear-notification-config`). Two fleet
knobs: `--max-daily-usd` (rolling-24h fleet cost cap; pass `0` to clear) and
`--silent-threshold-mins` (default 20). There is no `--auto-run-ready`; the
old `--auto-merge` / `--auto-pr` knobs were removed.

MCP names:

| Tool | Purpose |
|------|---------|
| `animus.daemon.start` | Start the daemon (always detached) |
| `animus.daemon.stop` | Stop the daemon |
| `animus.daemon.status` | Basic running/stopped check |
| `animus.daemon.health` | Detailed health metrics (carries the `healthy` verdict) |
| `animus.daemon.observe` | Merged events+logs window or single-source route (non-streaming) |
| `animus.daemon.events` | Recent daemon events |
| `animus.daemon.logs` | Read daemon log |
| `animus.daemon.agents` | List active agent processes |
| `animus.daemon.config` | Read daemon config |
| `animus.daemon.config-set` | Update daemon config |
| `animus.daemon.pause` | Pause dispatch |
| `animus.daemon.resume` | Resume dispatch |

`daemon stream`, `clear-logs`, `preflight`, `restart`, and `metrics` are CLI
surfaces, not MCP daemon tools in the current reference.

## Kill-Switches

Operator escape hatches; all require a daemon restart to take effect:

- `ANIMUS_DAEMON_DISABLE_TRIGGERS=1` — skip the trigger plugin supervisor.
- `ANIMUS_DAEMON_DISABLE_SUBJECT_PLUGINS=1` — skip subject plugin discovery.
- `ANIMUS_DAEMON_DISABLE_LOG_STORAGE_PLUGIN=1` — force the in-tree log backend.
- `ANIMUS_DAEMON_DISABLE_BUDGET_ENFORCEMENT=1` — skip the budget-cap
  enforcement housekeeping leg (no auto-pause/fail of breaching workflows);
  `daemon health` and `animus status` still report the leg as disabled.

## Architecture

Animus resolves a project root, loads repo-scoped runtime state under
`~/.animus/<repo-scope>/`, manages the queue via the installed queue plugin,
and dispatches workflow phases through the installed workflow_runner and
provider plugins.

## Common Issues

### Missing plugins

```bash
animus daemon preflight
animus plugin install-defaults --flavor default --yes
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
env -u CLAUDECODE -u CLAUDE_CODE_SESSION_ACCESS_TOKEN animus daemon start
```

### Daemon crashes

```bash
animus daemon logs --limit 100
animus logs tail --level error --since 1h
animus daemon stream --level error --pretty
```

Common causes:

- Missing or unhealthy required-role plugins.
- Disk full from accumulated worktrees or logs.
- Lock file contention.

### Stuck plugins / process leaks

The `animus runner` group was removed. Provider health lives in
`animus plugin status` (per-plugin pid, state, restart count,
`disabled_by_supervisor`, `cooldown_until`, plus aggregate
`provider_plugins_healthy`), and orphaned-CLI-process detection moved into
`animus doctor`:

```bash
animus plugin status
animus doctor
animus doctor --fix          # prunes stale cli-tracker entries for exited processes
```

Live tracked PIDs get a manual `kill` suggestion instead of automatic cleanup
(the tracker is global across projects).
