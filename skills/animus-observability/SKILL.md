---
name: animus-observability
description: Inspect Animus status, daemon observe/health/metrics, structured streams, logs, run output, decision logs, artifacts, budget breaches, plugin status, web UI transports, and trigger events.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.18"   # animus CLI surface this skill targets
---

# Observability

Use this skill when the user asks what Animus is doing, why a run failed, how
to inspect logs or artifacts, or how to open the web UI.

## Fast Triage

```bash
animus status
animus status --failures 10
animus daemon health
animus daemon observe
animus daemon observe --since 1h
animus history recent --limit 20
animus queue stats
```

- `animus status` is the unified dashboard. `--failures <N>` sets how many
  recent workflow failures to list (default 3; applies to human and `--json`
  output). It also shows a Budget section: enforcement state, active breach
  count, and the worst offender.
- `animus daemon health` leads with a one-line verdict — `healthy: true`,
  `healthy: true (paused)`, or `healthy: false` — then `runtime_paused`,
  per-plugin supervisor state (restart counts, cooldown-until), and a
  `budget_enforcement: {enabled, last_sweep_at}` line with a 24h breach
  rollup.
- `animus daemon observe` is the observability front-door: bare prints a
  data-source matrix plus the last ~20 merged event+log lines.

If the daemon cannot start, run:

```bash
animus daemon preflight
animus install   # with a committed animus.toml; else: animus plugin install-defaults --flavor default --yes
```

## Observe Front-Door

```bash
animus daemon observe                        # matrix + recent merged tail
animus daemon observe --follow               # live; delegates to daemon stream --pretty
animus daemon observe --since 2h             # merged events + logs, source-labeled
animus daemon observe --source logs --limit 50
animus daemon observe --source events --since 1d
animus daemon observe --workflow wf-abc --since 1d
animus daemon observe --json
```

`--source <logs|events|stream|workflow>` routes to one existing surface;
`--follow` cannot combine with `--since` or a non-stream `--source`. Every
branch reuses the existing `daemon events` / `daemon logs` / `daemon stream`
readers. MCP: `animus.daemon.observe` (non-streaming; works offline).

## Daemon Views

```bash
animus daemon status
animus daemon health
animus daemon events --limit 50              # one-shot by default
animus daemon events --follow                # opt into streaming
animus daemon logs --limit 100
animus daemon metrics --pretty               # live counters; offline-tolerant
animus daemon metrics --watch --interval-secs 5 --pretty
animus daemon metrics status                 # telemetry opt-in state
```

`animus daemon metrics` is now a subcommand group: bare invocation is the
live display (with no daemon it prints an offline telemetry summary and exits
0; only `--watch` requires a running daemon), and the telemetry verbs are
`daemon metrics {status,enable,disable,flush,cleanup}` (folded in from the
removed top-level `animus metrics`). `daemon metrics` and `daemon observe`
are CLI surfaces; only `observe` has an MCP counterpart.

## Live Stream

```bash
animus daemon stream --pretty
animus daemon stream --cat phase --level warn --pretty
animus daemon stream --workflow wf-abc --tail 100 --pretty
animus daemon stream --run run-xyz --no-follow
```

Stream flags:

- `--cat <prefix>` filters categories such as `llm`, `phase`, `schedule`, `queue`, `runner`, `daemon`, `agent`, or `task`.
- `--level <debug|info|warn|error>` sets minimum level.
- `--workflow <id-or-ref>` narrows to one workflow.
- `--run <id>` narrows to one run.
- `--tail <n>` replays recent entries before following.
- `--no-follow` prints recent entries and exits.
- `--pretty` renders human-readable output instead of raw JSONL.
- `--full` (with `--pretty`) renders full message bodies instead of truncated previews.

There is no `--phase` stream flag; use `--cat phase` and filter JSON when
needed. `daemon stream` and `daemon events --follow` no longer lose records
across log rotation.

## Workflow Lifecycle Events

```bash
animus events tail
animus events tail --workflow-id wf-abc --since 5m --json
```

Subscribes to `workflow/events` and renders `phase_started`,
`phase_completed`, `workflow_completed`, `workflow_failed`. A `--workflow-id`
stream terminates naturally when that workflow completes or fails; otherwise
it follows until Ctrl-C. `--since` is a client-side rewind filter (the daemon
does not buffer history).

## Logs

```bash
animus logs tail --level info --since 1h --limit 100
animus logs tail --plugin animus-provider-codex --level debug --since 15m
```

`animus logs tail` reads the active `log_storage_backend` plugin. When none is
installed, it falls back to the in-tree `events.jsonl` log. Set
`ANIMUS_DAEMON_DISABLE_LOG_STORAGE_PLUGIN=1` only to force that fallback.

MCP: `animus.logs.tail`.

## Run Output, Decisions, and Artifacts

```bash
animus output read --run-id <run-id>
animus output read --workflow-id <workflow-id>     # resolves the latest run
animus output decisions --run-id <run-id>
animus output decisions --workflow-id <workflow-id>
animus output monitor --run-id <run-id>
animus output monitor --run-id <run-id> --task-id TASK-001 --phase-id implement
animus output jsonl --run-id <run-id>
animus output jsonl --run-id <run-id> --entries
animus output phase-outputs --workflow-id <workflow-id>
animus output phase-outputs --workflow-id <workflow-id> --phase-id test
animus output artifacts --execution-id <execution-id>
animus output download --execution-id <execution-id> --artifact-id <artifact-id>
animus output cli --run-id <run-id>
```

- `output read` replaced `output run` (alias removed). Both `output read` and
  `output decisions` accept `--run-id` or `--workflow-id` (latest run for that
  workflow; clear error when none or ambiguous).
- `output decisions` reads the per-run LLM decision log
  (`runs/<run_id>/decisions.jsonl`: session header, prompts, tool
  calls/results, errors). Distinct from `animus workflow decisions`, which
  shows phase-advance decision history (advance/skip/rework verdicts) stored
  on workflow state.
- `output phase-outputs` renders one human block per phase (verdict, reason,
  commit) plus a Skills section — requested vs applied (source scope +
  contribution kinds) vs missing — so attached skills are verifiably applied;
  `--json` carries the raw outputs including persisted skill records.

## Forensic Chain from History

History records carry a `run_id` when resolvable, so a task id pivots into
run forensics:

```bash
animus history task --task-id TASK-001
animus history search --since 7d --status failed
animus output read --run-id <run-id-from-history>
animus output decisions --run-id <run-id-from-history>
```

`history search --since` takes a relative window (`7d`, `12h`, `30m`);
RFC3339 `--started-after` / `--started-before` remain, and `--since`
conflicts with `--started-after`.

MCP output tools include `animus.output.run`, `monitor`, `jsonl`,
`artifacts`, and `phase-outputs`. The MCP reference also exposes
`animus.output.tail`; the current CLI tree does not have a matching
`animus output tail` command.

## Plugin and Provider Health

The `animus runner` group (and `animus.runner.*` MCP tools) was removed.

```bash
animus plugin status
animus plugin status --json
animus doctor
animus doctor --fix
```

- `animus plugin status` shows per-plugin runtime status (pid, state, last
  RPC, restart count, last error) plus supervisor fields
  (`disabled_by_supervisor`, `cooldown_until`), a `providers` array with
  per-provider install state, and the rolled-up `provider_plugins_healthy`
  boolean (absorbed from the removed `animus runner health`).
- `animus doctor --fix` absorbed orphaned-CLI-process detection: it prunes
  stale cli-tracker entries for exited processes; live tracked PIDs get a
  manual `kill` suggestion.

## Web UI

`animus web` is plugin-backed. Install transports first:

```bash
animus plugin install-defaults --include-transports
animus web serve --open
animus web open --path /runs
animus web open --url http://127.0.0.1:3100
```

There is no in-tree web server after the transport/UI plugin extraction.

## Triggers

```bash
animus trigger list
animus trigger fire <trigger-id> --payload '{"action":"test"}'
```

Use `trigger fire` to test webhook or GitHub webhook triggers without an
external HTTP request. It queues the event directly; the daemon dispatches it
on the next scheduler pass.

## Exit Codes

`subject`, `cost`, `events`, and `plugin` commands use typed exit codes:
invalid input exits 2, not-found 3, conflict 4, unavailable (missing plugin / network) 5.
Scripts matching on exit 1 for these cases must update.

## Trigger-Event Subjects (portal, v0.7)

Every trigger delivery — schedules, `triggers:` blocks, webhooks — writes a
`trigger_event` subject (status `done`, delivery metadata in the `custom`
bag). "Did my trigger fire?" is answerable from the board or
`animus subject list --kind trigger_event` / `list_subjects` with
`kind: "trigger_event"` — no log spelunking. Events are pruned past 30 days
beyond the newest 2000.

