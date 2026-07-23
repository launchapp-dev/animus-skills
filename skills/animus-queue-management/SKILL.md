---
name: animus-queue-management
description: Dispatch queue operations — enqueue, hold, release, drop, reorder, and queue patterns
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
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
pending (deferred) → pending, leasable (when --at run_at passes)
pending → assigned → (removed on completion)
pending → held → pending (released)
any → dropped (via animus queue drop)
```

`deferred` is not a separate state: it is the not-yet-leasable subset of
`pending` (entries whose `--at run_at` has not passed), matching the
`(N deferred)` annotation in `queue stats`.

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

Returns: total, pending, assigned, held counts. When any entries are
scheduled but not yet due it also prints `(N deferred)` — `deferred` is a
subset of `pending` that is not yet leasable.

### Enqueue
`animus queue enqueue` enqueues a subject dispatch by subject id or custom
title (`--subject-id` / `--title` are mutually exclusive):

```bash
animus queue enqueue --subject-id TASK-001
animus queue enqueue --subject-id task:TASK-001 --workflow-ref animus.task/quick-fix

# Requirement — name the workflow explicitly (see migration note below)
animus queue enqueue --subject-id requirement:REQ-039 --workflow-ref animus.requirement/plan

# Any custom/dynamic kind — the kind prefix routes to that kind's backend
animus queue enqueue --subject-id blog:BLOG-001 --workflow-ref publish-blog

# Custom subject
animus queue enqueue --title "Run nightly build" --description "Verify the release branch" --workflow-ref ops
```

> **Version note.** On 0.6.x local installs (mainline, v0.6.33) both the
> legacy `--task-id` / `--requirement-id` flags (and `task_id` /
> `requirement_id` MCP params) and `--subject-id` (added v0.6.29) work.
> The legacy flags/params are removed on the v0.7-rc line (the portal
> already enforces `subjectId`), so prefer `--subject-id` with a qualified
> `kind:ID`, or a bare id (the subject router resolves the kind by probing
> backends). (v0.7-rc/portal only:) task and requirement become ordinary
> kinds there — a requirement dispatched via `--subject-id` without an
> explicit `--workflow-ref` uses the project **default** workflow, not
> `animus.requirement/plan` — always name the workflow.

The daemon picks up pending entries and assigns them to agents. `--subject-id`
enqueues a subject of **any** kind: the kind prefix is trusted, the queue
lease and runner resolve the subject via that kind's backend (`<kind>/get`).

Subjectless ad-hoc runs: `animus queue enqueue --adhoc --workflow-ref <ref>`
declares a run with no subject at all (v0.7-rc/portal only — the flag does
not exist on 0.6.x local installs; use direct dispatch there). Caveat: with the current
default queue plugin (wire pinned to a non-optional subject), enqueue-`--adhoc`
fails fast — direct dispatch (`animus workflow run <ref>` with no subject)
carries subjectless runs end-to-end.

Deferred dispatch flags:

```bash
# Schedule for later — sets run_at; the entry stays `deferred` until due
animus queue enqueue --subject-id TASK-001 --at "2026-06-18T18:00:00Z"

# Grace window after --at; if still pending past --at + window the entry is
# dropped instead of dispatched. REQUIRES --at.
animus queue enqueue --subject-id TASK-001 --at "2026-06-18T18:00:00Z" --expire-after 30m

# Attach structured input forwarded to the workflow
animus queue enqueue --subject-id TASK-001 --input-json '{"branch":"main"}'
```

A not-yet-due `--at` entry sits in the `deferred` queue state until its
`run_at` passes, then becomes leasable like any other pending entry.

The queue is queue-only: enqueued entries lease into free pool headroom as
slots free up (bounded by `pool_size`). There is no `auto_run_ready` gate —
that key was removed; a `ready` subject status never auto-dispatches on its
own.

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
{ "subject_id": "task:TASK-042" }

// Enqueue with workflow override
{ "subject_id": "task:TASK-042", "workflow_ref": "animus.task/quick-fix" }

// Enqueue a dynamic-kind subject
{ "subject_id": "blog:BLOG-001", "workflow_ref": "publish-blog" }

// Drop a stuck entry
{ "subject_id": "TASK-042" }

// Bulk hold
{ "subject_ids": ["TASK-042", "TASK-043"] }
```

(`animus.queue.enqueue` params: `title`, `subject_id`, `description`,
`workflow_ref`, `input_json`, `run_at`, `expire_after`, `project_root` — the
legacy `task_id`/`requirement_id` params still work on 0.6.x local installs
but are removed on the v0.7-rc line; prefer `subject_id`.)

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
Enqueue is not deduplicated by core. Re-enqueueing a subject that is already
queued may surface a `subject dispatch already queued (via queue plugin)`
message plus a warning from the queue plugin, but it does not hard-block.
Treat `animus queue enqueue` as safe to retry, but still verify current queue
state with `animus queue list` when debugging duplicate work.

### Queue Capacity
The daemon dispatches from the queue up to its configured `pool_size`. If the queue has more pending work than open slots, the rest stay pending until capacity frees up.
