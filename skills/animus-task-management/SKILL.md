---
name: animus-task-management
description: Task lifecycle through the unified subject surface - create, list, update, block/unblock, enqueue, and inspect task-like subjects via CLI and MCP
user_invocable: false
auto_invoke: true
---

# Task Management

Current Animus routes tasks through the unified subject surface. The old
`animus task ...` CLI tree and `animus.task.*` MCP tools were removed; use
`animus subject <subcommand> --kind task ...` and `animus.subject.*` with
`kind: "task"`.

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
cleared, so unsticking a stuck task is visible.

Status changes (and creates/updates/enqueues) send a fire-and-forget
`daemon/nudge`, so the daemon reacts effectively immediately — there is no
need to wait for the next scheduler tick; `--interval-secs` is only a
fallback heartbeat.

### Update Fields

```bash
animus subject update --kind task --id TASK-001 --status blocked --priority p1
animus subject update --kind task --id TASK-001 --labels backend,urgent
```

The current generic subject CLI exposes status, priority, and labels for
updates. Backend-specific fields such as checklists, dependency edges,
deadlines, assignees, or native task type are no longer part of the core CLI
surface; use the backend plugin directly if it provides those operations.

### Delete

```bash
animus subject delete --kind task --id TASK-001 --yes
```

`--yes` confirms the destructive operation; without it the command only prints
what would be deleted. Backends that do not support delete return an
unsupported error. There is no MCP delete tool, so deletion is CLI-only.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `animus.subject.list` | List task subjects with `kind: "task"` |
| `animus.subject.get` | Fetch one task subject |
| `animus.subject.create` | Create a task subject |
| `animus.subject.update` | Patch task subject fields |
| `animus.subject.next` | Get the next ready task subject |
| `animus.subject.status` | Set normalized task status |
| `animus.subject.batch-create` | Create up to 100 task subjects (`items[]`, `on_error`) |
| `animus.subject.batch-update` | Patch up to 100 task subjects (`items[]`, `on_error`) |

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

Tasks are dispatchable when the subject backend reports `ready`:

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

Typical flow:

1. Create or select a `ready` task subject.
2. Enqueue it with `animus queue enqueue --task-id TASK-XXX` (explicit
   enqueues drain even when `daemon.auto_run_ready` is false).
3. Run a workflow explicitly with `animus workflow run <workflow-ref> --task-id TASK-XXX`, or let the daemon pick it up.
4. Inspect execution with `animus workflow list`, `animus history task --task-id TASK-XXX`, `animus output read`, and `animus output phase-outputs`.
