---
name: animus-subject-operations
description: Work with Animus subjects and subject_backend plugins, including task, requirement, Linear, SQLite, Markdown, and custom subject kinds, default_subject_kind, wire ids, and status routing.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.18"   # animus CLI surface this skill targets
---

# Subject Operations

Subjects are Animus's generic work items. Tasks, requirements, Linear issues,
SQLite rows, Markdown tasks, and custom external work items all route through
the same subject surface when a `subject_backend` plugin claims the kind.

The legacy `animus task ...`, `animus requirements ...`, `animus.task.*`, and
`animus.requirements.*` surfaces are removed. Use:

```bash
animus subject <command> --kind task
animus subject <command> --kind requirement
```

## Requirements

Subject operations require an installed subject backend plugin:

```bash
animus plugin install-defaults
animus daemon preflight
```

Bare `install-defaults` installs the flavor's required set, which includes
`subject-default` (kind=task) and `subject-requirements` (kind=requirement).
The recommended extras — `subject-linear`, `subject-sqlite`,
`subject-markdown`, `subject-github` — install via `--include-recommended`
(the legacy `--include-subjects` flag still works and adds the recommended
subject slice). In a project with a committed `animus.toml`, `animus install`
is the canonical way to install the declared plugin set.

Two v0.7-era backends worth knowing (multi-kind plugins route by
`serves_kind`): **`animus-postgres`** — a consolidated Postgres BaaS plugin
serving subject_backend (catch-all `*` kind), config_source, queue,
workflow_journal, and conversation_store from one process (it replaced the
five separate `animus-subject-postgres`/`animus-config-postgres`/… plugins);
and **`animus-subject-mcp`** — a generic read-only adapter that projects
entities from connected external MCP servers as subjects of kind
`ext.<server>.<entity>` (its `ext.*` glob beats the Postgres catch-all).

There is no in-tree subject fallback after v0.4.12. If
`ANIMUS_DAEMON_DISABLE_SUBJECT_PLUGINS=1` is set, subject calls behave as if no
backend is installed.

## Kind and IDs

`--kind` selects the backend route. When omitted, Animus falls back to
`.animus/config.json` `default_subject_kind`, which defaults to `task`.

Subject ids may be simple local ids or backend-qualified wire ids:

```text
TASK-001
requirement:REQ-004
linear:ENG-123
sqlite:01HX...
```

Prefer using the exact id returned by `subject create`, `subject list`, or the
backend integration.

## CLI Surface

```bash
animus subject list --kind task
animus subject list --kind task --status ready --limit 25
animus subject list --kind task --query "login"        # title filter (v0.6.23+)
animus subject list --kind task --cursor <next_cursor> # pagination (default limit 50)
animus subject get --kind task --id TASK-001
animus subject next --kind task
```

`subject list` is paginated: default `--limit` 50 (`0` = uncapped), and the
output footer carries a `next_cursor` to pass back via `--cursor`. Page
through rather than raising the limit; never assume the first page is the
whole board.

Create:

```bash
animus subject create --kind task --title "Fix login bug" --status ready --priority p1
animus subject create --kind requirement --title "SOC2 evidence export" --body "Export audit events" --labels compliance,audit
```

Update:

```bash
animus subject update --kind task --id TASK-001 --status blocked --priority p1
animus subject update --kind task --id TASK-001 --labels backend,urgent
animus subject update --kind task --id TASK-001 --title "New title" --body "New description"
animus subject status --kind task --id TASK-001 --status done
```

The generic update surface supports normalized `status`, `priority`,
replacement `labels`, plus `--title` (rename, v0.7.0-rc.5+) and `--body`
(v0.6.0+). Structured custom fields ride `--data` (v0.7.0-rc.10+) on
`create`/`update`/`batch-create`/`batch-update` — a JSON object merged into
the subject's `custom` bag, which workflow runners can read (e.g.
`{{git_repo}}` resolution by workflow-runner v0.4.34+):

```bash
animus subject update --kind task --id TASK-001 --data '{"git_repo": "acme/api", "story_points": 3}'
```

Deeper backend-specific operations belong in the backend plugin's own API or
`animus plugin call`.

`subject status ... --status ready` prints an `unstuck: cleared ...` line
(stderr, human output) naming any `paused` / `blocked_*` flags the
transition cleared. `subject get` explains stalls: a task bound to a paused
workflow carries a `paused by workflow <id>` annotation in `blocked_reason`
(enriched with the cause on budget breaches, e.g. `— budget exceeded
($7.50 > $5.00 max_cost_usd)`).

Batch create/update (up to 100 items per call, mirroring the
`animus.subject.batch-*` MCP tools):

```bash
animus subject batch-create --kind task --file items.json
animus subject batch-update --kind task --file patches.json --on-error continue
```

`--file` takes a JSON items array — bare array or `{"items": [...]}`
wrapper. Create items are `{"title", "status"?, "priority"?, "labels"?,
"body"?}`; update items are `{"id", "status"?, "priority"?, "labels"?}`
with at least one patch field. `--on-error stop` (default) skips remaining
items after the first failure; `continue` runs every item. Output is an
`animus.cli.v1`-wrapped `animus.cli.batch.result.v1` envelope with per-item
results; a batch where any item failed exits non-zero with the full payload
under `/error/details`.

Delete:

```bash
animus subject delete --kind task --id TASK-001 --yes
```

`--yes` confirms the destructive operation. Without it the command only
prints what would be deleted and exits 0.

## Normalized Statuses

Common statuses:

```text
ready
in-progress
blocked
done
cancelled
```

Backends may map richer native states into these buckets. Query native fields
through the backend plugin when the normalized status is not enough.

## Queue and Workflow Use

Enqueue is the default way to run a subject — it hands the work to the daemon,
which dispatches it (the daemon is queue-only):

```bash
animus queue enqueue --subject-id task:TASK-001 --workflow-ref animus.task/standard
animus queue enqueue --subject-id requirement:REQ-001 --workflow-ref animus.requirement/standard
```

`animus workflow run` is the ad-hoc / foreground-debug alternative — it runs
one workflow directly, bypassing the queue and daemon. Use it only for one-off
manual runs or debugging, not as the default execution path:

```bash
animus workflow run animus.task/standard --subject-id task:TASK-001
```

> **Removed in v0.7 (breaking).** `--task-id` / `--requirement-id` are gone
> from queue and workflow commands — `--subject-id` is the universal dispatch
> selector for subjects of **any** kind. A qualified `<kind>:<native>` id
> (e.g. `--subject-id song:SONG-001`) trusts the prefix and resolves via that
> kind's backend; a bare id is resolved by the subject router probing
> backends. Task and requirement are ordinary kinds: a requirement dispatched
> without an explicit `--workflow-ref` uses the project **default** workflow
> (no longer `animus.requirement/plan`) — always name the workflow.

Dispatch is event-driven: `subject create/update/status` and
`queue enqueue/release` (CLI and MCP) send a fire-and-forget `daemon/nudge`,
so the daemon reacts effectively immediately — `--interval-secs` is only a
fallback heartbeat, not the dispatch latency. `queue enqueue` (or a cron
`schedules:` entry) is what dispatches work; a `ready` status alone does not
cause auto-pickup.

## Exit Codes

`animus subject` commands use typed exit codes (also on `cost`, `events`,
and `plugin`): invalid input exits `2`, not-found exits `3`, unavailable
(missing plugin / daemon unreachable) exits `5`. Scripts that matched exit
`1` for these cases must update; `1` is now reserved for unclassified
internal errors.

## MCP Tools

Use:

- `animus.subject.list`
- `animus.subject.get`
- `animus.subject.create`
- `animus.subject.update`
- `animus.subject.next`
- `animus.subject.status`
- `animus.subject.batch-create` (`items[]`, `on_error`, 100-item cap)
- `animus.subject.batch-update` (`items[]`, `on_error`, 100-item cap)

Set `kind` to `task`, `requirement`, or the custom kind claimed by the subject
backend plugin. Batch responses use the `animus.mcp.batch.result.v1` schema
with succeeded/failed/skipped counts and per-item results.

Delete is CLI-only: there is no `animus.subject.delete` MCP tool.

## Backend Troubleshooting

- `Unavailable` (exit code 5) for every subject call: no plugin claims that kind, or subject plugins are disabled. `NotFound` (exit code 3) means the backend is routable but the subject id does not exist.
- Daemon refuses to start: run `animus daemon preflight`; install missing subject plugins.
- Unexpected state names: distinguish normalized Animus status from native backend status.
- Missing body/title update support in CLI: use a backend-specific plugin method if exposed.
- Requirements no longer list: use `animus subject list --kind requirement`, not `animus requirements list`.
