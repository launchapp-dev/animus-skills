---
name: animus-observability
description: Inspect Animus status, daemon metrics, structured streams, logs, run output, artifacts, runner health, web UI transports, and trigger events.
user_invocable: false
auto_invoke: true
---

# Observability

Use this skill when the user asks what Animus is doing, why a run failed, how
to inspect logs or artifacts, or how to open the web UI.

## Fast Triage

```bash
animus status
animus daemon health
animus daemon stream --pretty --tail 50
animus history recent --limit 20
animus queue stats
```

If the daemon cannot start, run:

```bash
animus daemon preflight
animus plugin install-defaults --include-subjects
```

## Daemon Views

```bash
animus daemon status
animus daemon health
animus daemon events --limit 50
animus daemon logs --limit 100
animus daemon metrics --pretty
animus daemon metrics --watch --interval-secs 5 --pretty
```

`daemon metrics` is CLI-only in the current reference.

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

There is no `--phase` stream flag; use `--cat phase` and filter JSON when
needed.

## Logs

```bash
animus logs tail --level info --since 1h --limit 100
animus logs tail --plugin animus-provider-codex --level debug --since 15m
```

`animus logs tail` reads the active `log_storage_backend` plugin. When none is
installed, it falls back to the in-tree `events.jsonl` log. Set
`ANIMUS_DAEMON_DISABLE_LOG_STORAGE_PLUGIN=1` only to force that fallback.

MCP: `animus.logs.tail`.

## Run Output and Artifacts

```bash
animus output run --run-id <run-id>
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

Use output commands when you already have a `run_id`, `workflow_id`, or
`execution_id`. Use history first when you only know a task id.

MCP output tools include `animus.output.run`, `monitor`, `jsonl`, `artifacts`,
and `phase-outputs`. The MCP reference also exposes `animus.output.tail`; the
current CLI tree does not have a matching `animus output tail` command.

## Runner Health

```bash
animus runner health
animus runner restart-stats
animus runner orphans detect
animus runner orphans cleanup --run-id <run-id>
```

Use runner commands when agent processes are stuck, orphaned, or failing to
restart cleanly.

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
external HTTP request. The daemon dispatches the queued trigger event on the
next tick.
