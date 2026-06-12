---
name: animus-task-management
description: Full task lifecycle on the unified subject surface — create, list, update, block/unblock, dispatch via CLI and MCP
user_invocable: false
auto_invoke: true
---

# Task Management

Tasks and requirements live exclusively on the unified `animus subject` surface
(`--kind task` / `--kind requirement`). The legacy `animus task ...` and
`animus requirements ...` command trees and the `animus.task.*` /
`animus.requirements.*` MCP tool families were removed in v0.4.4. Subject
operations route through installed `subject_backend` plugins
(`animus plugin install-defaults --include-subjects` keeps `kind=task` and
`kind=requirement` routable).

IDs on this surface are backend-qualified wire ids: `<kind>:<native_id>`,
e.g. `task:TASK-001`. Statuses are normalized kebab-case buckets.

## Task Lifecycle

```
backlog → ready → in-progress → done
            ↘ blocked → ready
            ↘ on-hold → ready
backlog/ready/in-progress → cancelled
```

Normalized statuses: `backlog` (alias `todo`), `ready`, `in-progress`,
`blocked`, `on-hold`, `done`, `cancelled`. Snake_case spellings
(`in_progress`) parse as aliases.

## CLI Commands

### Create
```bash
animus subject create --kind task --title "Fix login bug" --priority p0
animus subject create --kind task --title "Add dark mode" --priority p2 --body "Support system theme preference"
```

Options:
- `--priority`: priority bucket — `p0` (highest), `p1`, `p2`, `p3`
- `--body`: free-form description
- `--labels`: comma-separated labels (`--labels bugfix,auth`)
- `--status`: normalized status to set on creation
- `--kind`: defaults to `default_subject_kind` in `.animus/config.json` (`task` when unset)

### List and Filter
```bash
animus subject list --kind task                      # all tasks
animus subject list --kind task --status ready       # ready tasks only
animus subject list --kind task --status blocked     # blocked tasks
animus subject list --kind task --limit 20           # cap result count
```

### Get Details
```bash
animus subject get --kind task --id task:TASK-001
```

### Next Ready Task
```bash
animus subject next --kind task    # highest-priority Ready subject (JSON null when none)
```

### Update Status
```bash
animus subject status --kind task --id task:TASK-001 --status ready
animus subject status --kind task --id task:TASK-001 --status in-progress
animus subject status --kind task --id task:TASK-001 --status done
animus subject status --kind task --id task:TASK-001 --status blocked
animus subject status --kind task --id task:TASK-001 --status on-hold
animus subject status --kind task --id task:TASK-001 --status cancelled
```

Setting `ready` clears blocked/paused bookkeeping on the default task backend
(`paused`, `blocked_at`, `blocked_reason`, `blocked_by`).

### Update Priority / Labels
```bash
animus subject update --kind task --id task:TASK-001 --priority p0
animus subject update --kind task --id task:TASK-001 --labels auth,backend   # replaces labels
```

### Delete
```bash
animus subject delete --kind task --id task:TASK-001          # dry-run preview, exits 0
animus subject delete --kind task --id task:TASK-001 --yes    # actually delete
```

Backends that don't support delete return an `Unsupported` error.

### Removed verbs
The old per-task verbs (`pause`, `resume`, `cancel`, `reopen`, `set-priority`,
`set-deadline`, `checklist-add`, `checklist-update`, `dependency-add`,
`stats`, `prioritized`, bulk ops) went away with the v0.4.4 task tree. Use
`subject status` for lifecycle moves (`on-hold` ≈ pause, `cancelled` ≈ cancel),
`subject update` for priority/labels, and `subject next` for prioritized pickup.
Checklist and dependency detail belongs in the task `--body` or your external
tracker's subject backend.

## MCP Tools

| Tool | Purpose | Key parameters |
|------|---------|----------------|
| `animus.subject.list` | List subjects for a kind | `kind`, `status`, `limit`, `project_root` |
| `animus.subject.get` | Fetch a subject by wire id | `kind`, `id`, `project_root` |
| `animus.subject.create` | Create a subject | `kind`, `title`, `priority`, `status`, `labels[]`, `body`, `project_root` |
| `animus.subject.update` | Update priority/status/labels | `kind`, `id`, `priority`, `status`, `labels[]`, `project_root` |
| `animus.subject.next` | Highest-priority Ready subject | `kind`, `project_root` |
| `animus.subject.status` | Set subject status | `kind`, `id`, `status`, `project_root` |

### MCP Examples

```json
// Create a task
{ "kind": "task", "title": "Add rate limiting", "priority": "p1" }

// List ready tasks
{ "kind": "task", "status": "ready" }

// Update status
{ "kind": "task", "id": "task:TASK-042", "status": "done" }

// Get the next task to work on
{ "kind": "task" }
```

## Patterns

### Promoting from Backlog
Tasks start as `backlog`. Promote to `ready` when dependencies are met:
```bash
animus subject status --kind task --id task:TASK-005 --status ready
```

### Blocking and Unblocking
When a task can't proceed:
```bash
animus subject status --kind task --id task:TASK-005 --status blocked
# Later, when the blocker is resolved:
animus subject status --kind task --id task:TASK-005 --status ready
```

### Scripting
Exit codes are typed and stable: `0` success, `2` invalid input, `3` not found,
`5` daemon/backend unavailable. Pair with `--json` (the `animus.cli.v1`
envelope) for machine consumption.

### Workflow Integration
Typical flow:
1. Move the task to `ready`
2. Enqueue it with `animus queue enqueue --task-id TASK-XXX`
3. Run a workflow explicitly (`animus workflow run --task-id TASK-XXX`) or let the daemon pick it up
4. Inspect execution with `animus workflow list`, `animus output read`, and `animus output phase-outputs`

`animus subject create/update/status` and `animus queue enqueue/release` send a
fire-and-forget `daemon/nudge` to the running daemon, so dispatch is
event-driven — you don't wait for the next heartbeat tick.
