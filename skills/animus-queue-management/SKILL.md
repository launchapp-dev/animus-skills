---
name: animus-queue-management
description: Dispatch queue operations — enqueue, hold, release, drop, reorder, and queue patterns
user_invocable: false
auto_invoke: true
---

# Queue Management

The dispatch queue controls what work the daemon picks up next. Subjects can be
tasks, requirements, or custom dispatches. Task and requirement records now come
from `subject_backend` plugins; create them through `animus subject ...` before
enqueueing their ids. The queue itself is a required-role plugin
(`launchapp-dev/animus-queue-default`, installed by `animus plugin
install-defaults`); the daemon's plugin preflight refuses to start the
daemon without it.

Dispatch is event-driven: `animus queue enqueue` and `animus queue release`
(and their MCP equivalents) send a fire-and-forget `daemon/nudge` to the
daemon, so pickup is effectively immediate — `--interval-secs` is only a
fallback heartbeat, not the dispatch latency.

## Queue Entry States

```
pending → assigned → (removed on completion)
pending → held → pending (released)
any → dropped (via animus queue drop)
```

## CLI Commands

### List Queue
```bash
animus queue list
```

Shows each entry's `subject_id`, status, and selected metadata.

### Queue Stats
```bash
animus queue stats
```

Returns: total, pending, assigned, held counts.

### Enqueue
`animus queue enqueue` enqueues a subject dispatch for a task, requirement,
or custom title (`--task-id` / `--requirement-id` / `--title` are mutually
exclusive):

```bash
animus queue enqueue --task-id TASK-001
animus queue enqueue --task-id TASK-001 --workflow-ref animus.task/quick-fix

# Requirement
animus queue enqueue --requirement-id REQ-039

# Custom subject
animus queue enqueue --title "Run nightly build" --description "Verify the release branch" --workflow-ref ops
```

The daemon picks up pending entries and assigns them to agents.
`--task-id` still exists on queue and workflow commands even though the old
`animus task ...` CRUD tree was removed.

Explicit enqueue entries are operator commands: they drain into free pool
headroom even when `daemon.auto_run_ready` is `false`. That flag now gates
only ready-task auto-dispatch, not the explicit queue.

### Hold / Release / Drop (bulk)
`hold`, `release`, and `drop` take one or more subject ids as positional
arguments, or `--all --yes` to target every eligible entry (`hold`: pending,
`release`: held, `drop`: pending/held/assigned). Each id is processed
independently — per-item failures do not stop the batch, results are
summarized, and the exit code is non-zero if any item failed. The legacy
`--subject-id <ID>` flag form still works and may be combined with
positional ids.

```bash
animus queue hold TASK-001 TASK-002 TASK-003
animus queue release TASK-001
animus queue release --all --yes
animus queue drop TASK-001 TASK-002
animus queue drop --all --yes
animus queue hold --subject-id TASK-001   # legacy flag form
```

`--yes` skips the confirmation prompt required by `--all` (required in
scripts, CI, and `--json` pipelines). With `--json`, the envelope carries
per-item results (`requested`, `succeeded`, `failed`, `items[]`); partial
failures emit an error envelope with the same payload under
`error.details`.

Use `drop` to remove entries regardless of status, including stale
assigned entries that are stuck.

### Reorder
Set dispatch priority order:
```bash
animus queue reorder --subject-id TASK-003 --subject-id TASK-001 --subject-id TASK-002
```

Repeat `--subject-id` in the exact order you want the daemon to consider.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `animus.queue.list` | List all queue entries |
| `animus.queue.stats` | Aggregate queue metrics |
| `animus.queue.enqueue` | Add a dispatch to the queue |
| `animus.queue.hold` | Hold one or more pending entries (`subject_id` or `subject_ids[]`) |
| `animus.queue.release` | Release one or more held entries (`subject_id` or `subject_ids[]`) |
| `animus.queue.drop` | Remove one or more entries, any status (`subject_id` or `subject_ids[]`) |
| `animus.queue.reorder` | Set dispatch order (`subject_ids[]`) |

`hold` / `release` / `drop` accept either a single `subject_id` or a
`subject_ids[]` array and route through the same bulk path as the CLI.

### MCP Examples

```json
// Enqueue a task
{ "task_id": "TASK-042" }

// Enqueue with workflow override
{ "task_id": "TASK-042", "workflow_ref": "animus.task/quick-fix" }

// Drop a stuck entry
{ "subject_id": "TASK-042" }

// Bulk hold
{ "subject_ids": ["TASK-042", "TASK-043"] }
```

## Patterns

### Queue Draining
When all pending entries are processed, the queue is empty. Refill it by
enqueueing task or requirement subjects directly, or by running whatever
workflow/schedule in your project is responsible for planning work.

### Stale Assigned Entries
If a workflow completes or fails but the queue entry stays `assigned`, it's stale. The reconciler should drop these, or use:
```bash
animus queue drop TASK-XXX
```

### Duplicate Prevention
Treat `animus queue enqueue` as safe to retry, but still verify current queue state with `animus queue list` when debugging duplicate work.

### Queue Capacity
The daemon dispatches from the queue up to its configured `pool_size`. If the queue has more pending work than open slots, the rest stay pending until capacity frees up.
