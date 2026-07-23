# Workflow, Queue, And Requirement Tools

Use this reference when the Animus operation is about workflow runtime,
workflow definitions, queue dispatch, or requirement state.

## Workflow runtime tools

| Tool | Key parameters |
|------|----------------|
| `animus.workflow.run` | `subject_id` (qualified `task:TASK-001` / any kind, or bare — router-resolved), `title`, `description`, `workflow_ref`, `input_json`, `project_root` |
| `animus.workflow.run-multiple` | `runs[]` (each: `subject_id`, `workflow_ref`, `input_json`), `on_error`, `project_root` |
| `animus.workflow.execute` | `subject_id`, `workflow_ref`, `phase`, `model`, `tool`, `phase_timeout_secs`, `input_json`, `project_root` |
| `animus.workflow.get` | `id` |
| `animus.workflow.list` | `status`, `workflow_ref`, `subject_id`, `phase_id`, `search`, `sort`, `limit`, `offset`, `max_tokens`, `project_root` |
| `animus.workflow.pause` | `id`, `confirm`, `dry_run` |
| `animus.workflow.cancel` | `id`, `confirm`, `dry_run` |
| `animus.workflow.resume` | `id` |
| `animus.workflow.phase.approve` | `workflow_id`, `phase_id` (alias `phase`), `feedback` (alias `note`) |
| `animus.workflow.phase.reject` | `workflow_id`, `phase_id` (alias `phase`), `reason` (alias `note`/`feedback`, required) |

`animus.workflow.phase.reject` is the decline-path mirror of `phase.approve`;
both require a pending gate phase.

Pruning terminal runs (`animus workflow prune`) and `animus workflow delete
--run-id` are CLI-only — there is no matching MCP tool.

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
| `animus.workflow.config.set` | `file` (path to a full RAW source `WorkflowConfig` JSON), `project_root` |
| `animus.workflow.config.agent-set` | `id`, `input_json`, `project_root` |
| `animus.workflow.config.agent-remove` | `id`, `project_root` |
| `animus.workflow.config.workflow-set` | `input_json` (must include an `id`), `project_root` |
| `animus.workflow.config.workflow-remove` | `id`, `project_root` |

The five config write-back tools persist through the installed writable
`config_source` plugin and fail cleanly when the source is read-only (e.g.
YAML). `config.set` replaces the entire config and must be fed the RAW
source model — never the effective output of `animus.workflow.config.get`
(that is post-pack-merge; feeding it back would bake pack-provided entities
into the source). For single-entity edits prefer the entity verbs
(`agent-set` / `workflow-set` / `*-remove`), which read-modify-write the raw
model and validate before writing. `config.agent-set` manages agent
*definitions* — it does not collide with the runtime `animus.agent.*` tools.

## Queue tools

| Tool | Key parameters |
|------|----------------|
| `animus.queue.list` | `project_root` |
| `animus.queue.stats` | `project_root` |
| `animus.queue.enqueue` | `subject_id` (qualified `kind:ID` of any kind, or bare), `title`, `description`, `workflow_ref`, `input_json`, `run_at`, `expire_after` (requires `run_at`), `project_root` |
| `animus.queue.reorder` | `subject_ids[]` |
| `animus.queue.hold` | `subject_id`, `subject_ids[]` |
| `animus.queue.release` | `subject_id`, `subject_ids[]` |
| `animus.queue.drop` | `subject_id`, `subject_ids[]`, `project_root` |

`hold`, `release`, and `drop` accept either a single `subject_id` or a bulk
`subject_ids[]` array; each id is processed independently.

## Requirement state

Requirements are subjects now. The removed `animus.requirements.*` MCP family
maps to `animus.subject.*` with `kind: "requirement"`.

| Old intent | Current MCP tool |
|------------|------------------|
| List requirements | `animus.subject.list` with `kind: "requirement"` |
| Get a requirement | `animus.subject.get` with `kind: "requirement"` |
| Create a requirement | `animus.subject.create` with `kind: "requirement"` |
| Update status or metadata | `animus.subject.update` or `animus.subject.status` with `kind: "requirement"` |
| Pick next ready requirement | `animus.subject.next` with `kind: "requirement"` |

Requirement refinement is no longer a dedicated core MCP verb. Run the
appropriate requirements workflow, such as `animus.workflow.run` with a
requirements workflow ref, or use the subject backend plugin if it exposes a
plugin-specific method.

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
5. `animus.subject.get` with the workflow's subject kind and id
