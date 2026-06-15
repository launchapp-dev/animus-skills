# Workflow And Queue Tools

Use this reference when the Animus operation is about workflow runtime, workflow definitions, or queue dispatch.

Requirements no longer have their own tool family: the `animus.requirements.*` tools were removed in v0.4.4. Use the `animus.subject.*` tools with `kind=requirement` (see [agent-daemon-task.md](agent-daemon-task.md) for the subject tool table).

## Workflow runtime tools

| Tool | Key parameters |
|------|----------------|
| `animus.workflow.run` | `task_id`, `requirement_id`, `title`, `description`, `workflow_ref`, `input_json` |
| `animus.workflow.run-multiple` | `runs[]`, `on_error` |
| `animus.workflow.execute` | `task_id`, `workflow_ref`, `phase`, `model`, `tool`, `phase_timeout_secs`, `input_json` |
| `animus.workflow.get` | `id` |
| `animus.workflow.list` | `status`, `workflow_ref`, `task_id`, `phase_id`, `search`, `sort`, `limit`, `offset`, `max_tokens` |
| `animus.workflow.pause` | `id`, `confirm`, `dry_run` |
| `animus.workflow.cancel` | `id`, `confirm`, `dry_run` |
| `animus.workflow.resume` | `id` |
| `animus.workflow.phase.approve` | `workflow_id`, `phase_id` (alias `phase`), `feedback` (alias `note`) |

Gate rejection (`animus workflow phase reject`) is CLI-only — there is no matching MCP tool. Pruning terminal runs (`animus workflow prune` / `animus workflow delete --run-id`) is also CLI-only.

## Decisions and checkpoints

| Tool | Key parameters |
|------|----------------|
| `animus.workflow.decisions` | `id`, `limit`, `offset`, `max_tokens` |
| `animus.workflow.checkpoints.list` | `id`, `limit`, `offset`, `max_tokens` |

## Definition and config tools

| Tool | Key parameters |
|------|----------------|
| `animus.workflow.phases.list` | `project_root` |
| `animus.workflow.phases.get` | `phase` |
| `animus.workflow.definitions.list` | `project_root` |
| `animus.workflow.config.get` | `project_root` |
| `animus.workflow.config.validate` | `project_root` |

## Queue tools

| Tool | Key parameters |
|------|----------------|
| `animus.queue.list` | `project_root` |
| `animus.queue.stats` | `project_root` |
| `animus.queue.enqueue` | `task_id`, `requirement_id`, `title`, `description`, `workflow_ref`, `input_json` |
| `animus.queue.reorder` | `subject_ids[]` |
| `animus.queue.hold` | `subject_id` or `subject_ids[]` |
| `animus.queue.release` | `subject_id` or `subject_ids[]` |
| `animus.queue.drop` | `subject_id` or `subject_ids[]`, `project_root` |

`hold`, `release`, and `drop` are bulk-capable: pass `subject_ids[]` for multiple subjects in one call (per-item failures don't stop the batch). The CLI equivalents also accept positional ids and `--all --yes`.

## Practical patterns

### Enqueue and monitor

1. `animus.queue.enqueue`
2. `animus.queue.list`
3. `animus.workflow.list`
4. `animus.output.monitor` or `animus.output.run`

### Debug a failed workflow

1. `animus.workflow.list`
2. `animus.workflow.get`
3. `animus.output.run` or `animus.output.jsonl`
4. `animus.output.phase-outputs`
5. `animus.subject.get` (`kind: "task"`)
