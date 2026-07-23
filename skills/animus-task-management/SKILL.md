---
name: animus-task-management
description: Task lifecycle through the unified subject surface - create, list, update, block/unblock, enqueue, and inspect task-like subjects via CLI and MCP
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
---

# Task Management

Current Animus routes tasks through the unified subject surface. The old
`animus task ...` CLI tree and `animus.task.*` MCP tools were removed; use
`animus subject --kind task ...` and `animus.subject.*` with `kind: "task"`.

Task operations require a subject backend plugin. The default local task
backend (`animus-subject-default`) is part of the flavor's required set, so:

```bash
animus plugin install-defaults
animus daemon preflight
```

`animus subject` commands use typed exit codes: invalid input `2`,
not-found `3`, unavailable (missing backend plugin / daemon unreachable)
`5`. Scripts matching exit `1` for these cases must update.

## Task Lifecycle

Common normalized statuses:

```text
ready -> in-progress -> done
      -> blocked -> ready
      -> cancelled
```

Backends may support additional raw states, but the CLI forwards normalized
status buckets. The canonical display form is hyphenated (`in-progress`), but
the parser accepts `in_progress` on input too.

## CLI Commands

### Create

```bash
animus subject create --kind task --title "Fix login bug" --priority p1 --status ready
animus subject create --kind task --title "Add dark mode" --body "Support system theme preference" --priority p2 --labels feature,frontend
```

Supported fields:

- `--kind`: usually `task`; omit only when `.animus/config.json` sets the right `default_subject_kind`
- `--title`: required for creation
- `--body`: free-form description
- `--status`: normalized status such as `ready`, `blocked`, `in-progress`, `done`
- `--priority`: backend priority bucket, commonly `p0`, `p1`, `p2`, `p3`
- `--labels`: comma-separated labels

### Batch Create / Update

```bash
animus subject batch-create --kind task --file items.json
animus subject batch-update --kind task --file patches.json --on-error continue
```

`--file` takes a JSON items array (bare array or `{"items": [...]}`
wrapper), max 100 items. Create items: `{"title", "status"?, "priority"?,
"labels"?, "body"?}`; update items: `{"id", "status"?, "priority"?,
"labels"?}` with at least one patch field. `--on-error stop` (default)
skips remaining items after the first failure; `continue` runs every item.
Emits an `animus.cli.batch.result.v1` envelope with per-item results; if
any item failed the command exits non-zero with the payload under
`/error/details`. MCP equivalents: `animus.subject.batch-create` /
`animus.subject.batch-update`.

### List and Filter

```bash
animus subject list --kind task
animus subject list --kind task --status ready
animus subject list --kind task --status blocked --limit 50
animus subject next --kind task
```

Use `animus queue stats` and `animus workflow list` for runtime metrics; the old
task-specific `stats` and `prioritized` commands are gone.

### Get Details

```bash
animus subject get --kind task --id TASK-001
```

Prefer copying the exact id returned by `subject list` or `subject create`,
especially when using non-default backends that return wire ids like
`linear:ENG-123`.

`subject get` also explains stalls: a task bound to a paused workflow
carries a `paused by workflow <id>` annotation in `blocked_reason`
(informational only — status and the `paused` flag are untouched). Budget
breaches enrich the marker, e.g. `paused by workflow wf-... — budget
exceeded ($7.50 > $5.00 max_cost_usd)`.

### Update Status

```bash
animus subject status --kind task --id TASK-001 --status ready
animus subject status --kind task --id TASK-001 --status in-progress
animus subject status --kind task --id TASK-001 --status done
animus subject status --kind task --id TASK-001 --status blocked
animus subject status --kind task --id TASK-001 --status cancelled
```

Setting `--status ready` prints an `unstuck: cleared ...` line (stderr,
human output) naming any `paused` / `blocked_*` flags the transition
cleared, so unsticking a stuck task is visible. On the default task backend
this clears the `paused`, `blocked_at`, `blocked_reason`, and `blocked_by`
bookkeeping fields.

Status changes (and creates/updates/enqueues) send a fire-and-forget
`daemon/nudge`, so the daemon reacts effectively immediately — there is no
need to wait for the next scheduler tick; `--interval-secs` is only a
fallback heartbeat.

### Update Fields

```bash
animus subject update --kind task --id TASK-001 --status blocked --priority p1
animus subject update --kind task --id TASK-001 --labels backend,urgent
animus subject update --kind task --id TASK-001 --body "New description"
animus subject update --kind task --id TASK-001 --title "Renamed" --data '{"git_repo": "acme/api"}'   # v0.7-rc/portal only
```

The generic subject CLI exposes status, priority, labels, and `--body`
(v0.6.0+ — the current 0.6.x write path for long-form content). `--title`
(rename, v0.7.0-rc.5+) and `--data` (v0.7.0-rc.10+ — JSON merged into the
subject's `custom` bag, readable by workflow runners) are v0.7-rc/portal
only — on 0.6.x local installs those flags error. Deeper
backend-specific fields such as checklists, dependency edges, deadlines, or
assignees stay in the backend plugin's own API if it provides those
operations.

### Delete

```bash
animus subject delete --kind task --id TASK-001 --yes
```

`--yes` confirms the destructive operation; without it the command only prints
what would be deleted. Backends that do not support delete return an
unsupported error. There is no MCP delete tool, so deletion is CLI-only.

## MCP Tools

| Tool | Purpose | Key parameters |
|------|---------|----------------|
| `animus.subject.list` | List task subjects with `kind: "task"` | `kind`, `status`, `limit`, `cursor` (page via `next_cursor`), `project_root` |
| `animus.subject.get` | Fetch one task subject | `kind`, `id`, `project_root` |
| `animus.subject.create` | Create a task subject | `kind`, `title`, `priority`, `status`, `labels[]`, `body`, `project_root` |
| `animus.subject.update` | Patch task subject fields | `kind`, `id`, `priority`, `status`, `labels[]`, `project_root` |
| `animus.subject.next` | Get the next ready task subject | `kind`, `project_root` |
| `animus.subject.status` | Set normalized task status | `kind`, `id`, `status`, `project_root` |
| `animus.subject.batch-create` | Create up to 100 task subjects (`items[]`, `on_error`) | `kind`, `items[]`, `on_error`, `project_root` |
| `animus.subject.batch-update` | Patch up to 100 task subjects (`items[]`, `on_error`) | `kind`, `items[]`, `on_error`, `project_root` |

### MCP Examples

```json
{ "kind": "task", "title": "Add rate limiting", "priority": "p1", "status": "ready" }
```

```json
{ "kind": "task", "status": "ready", "limit": 25 }
```

```json
{ "kind": "task", "id": "TASK-042", "status": "done" }
```

## Patterns

### Promote Work

A `ready` status from the subject backend makes a task *eligible* to enqueue;
it is dispatched only after `animus queue enqueue` (or a cron schedule), never
auto-picked-up from `ready` alone:

```bash
animus subject status --kind task --id TASK-005 --status ready
```

### Block and Unblock

```bash
animus subject status --kind task --id TASK-005 --status blocked
animus subject status --kind task --id TASK-005 --status ready
```

A `task-blocked` notifier event fires once per blocked transition (and
`workflow-failed` once per workflow failure), so notifiers can react
without polling.

### Scripting

`animus subject` returns typed, stable exit codes: `0` success, `2` invalid
input, `3` not found, `5` daemon/backend unavailable. Pair with `--json` (the
`animus.cli.v1` envelope) for machine consumption.

### Workflow Lifecycle Sync

Workflow controls keep the bound task explainable instead of leaving ghost
state:

- `animus workflow cancel` syncs the task to `cancelled` (unless already
  terminal).
- `animus workflow pause` annotates the task's `blocked_reason` with
  `paused by workflow <id>` (informational; status untouched);
  `animus workflow resume` clears exactly that annotation without
  clobbering genuine failure reasons. Any non-blocked status transition
  (e.g. `--status ready`) also clears it.
- Manually-claimed in-progress tasks are no longer re-blocked each tick;
  in-progress tasks with no workflow self-heal to Ready; a task whose
  terminal workflow died Cancelled projects Cancelled (not Blocked).

### Workflow Integration

Typical flow (queue-driven is the default — let the daemon dispatch):

1. Create or select a `ready` task subject.
2. Enqueue it with `animus queue enqueue --subject-id task:TASK-XXX`. This is
   both required and the normal run trigger — the daemon dispatches enqueued
   entries and cron schedules only, and `enqueue` nudges it to pick the entry
   up immediately. A `ready` status alone is never auto-run. (On 0.6.x local
   installs both the legacy `--task-id`/`--requirement-id` flags and
   `--subject-id` (added v0.6.29) work; the legacy flags are removed on the
   v0.7-rc line, so prefer `--subject-id` with a qualified `kind:ID` — bare
   ids also work, resolved by the router.)
3. Let the running daemon dispatch the enqueued entry (start it with
   `animus daemon start` if it is not already up). Prefer this path for normal
   task execution — it respects the daemon's pool size and scheduling.
4. Inspect execution with `animus queue list`, `animus workflow list --task-id TASK-XXX` (on the v0.7-rc line use `--subject-id task:TASK-XXX` — the filter matches the stored **qualified** id, so a bare `TASK-XXX` returns nothing), `animus history task --task-id TASK-XXX` (history keeps its `--task-id` flag), `animus output read`, and `animus output phase-outputs`.

`animus workflow run <workflow-ref> --subject-id task:TASK-XXX` is the
**ad-hoc** alternative: it runs one workflow directly, bypassing the queue
and the daemon's pool/scheduling. By default it spawns a detached
workflow_runner and returns; pass `--sync` to run in the foreground in your
terminal. `--actor-json` threads a per-user Actor onto the run (v0.6.21+,
also on `workflow config get|validate`). Reach for it only for one-off
manual runs or when debugging a specific workflow — not as the default way
to execute tasks.
