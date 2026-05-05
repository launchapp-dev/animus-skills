# Workflow, Queue, And Requirement Tools

Use this reference when the Animus operation is about workflow runtime, workflow definitions, queue dispatch, or requirement state.

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
| `animus.workflow.phase.approve` | `workflow_id`, `phase_id`, `feedback` |

## Workflow decisions and definitions

| Tool | Key parameters |
|------|----------------|
| `animus.workflow.decisions` | `id`, `limit`, `offset`, `max_tokens` |
| `animus.workflow.checkpoints.list` | `id`, `limit`, `offset`, `max_tokens` |
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
| `animus.queue.hold` | `subject_id` |
| `animus.queue.release` | `subject_id` |
| `animus.queue.drop` | `subject_id`, `project_root` |

## Requirement tools

| Tool | Key parameters |
|------|----------------|
| `animus.requirements.list` | `limit`, `offset`, `max_tokens`, `status` |
| `animus.requirements.get` | `id` |
| `animus.requirements.create` | `title`, `description`, `priority`, `acceptance_criterion[]` |
| `animus.requirements.update` | `id`, `title`, `description`, `priority`, `status`, `acceptance_criterion[]` |
| `animus.requirements.delete` | `id` |
| `animus.requirements.refine` | `id[]`, `focus`, `use_ai`, `tool`, `model`, `timeout_secs`, `start_runner`, `input_json` |

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
5. `animus.task.get`
