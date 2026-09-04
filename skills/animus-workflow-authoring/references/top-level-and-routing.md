# Top-Level Configuration and Routing

## Sources and overlays

The default YAML compiler reads `.animus/workflows.yaml`, then lexically
ordered `.animus/workflows/*.yaml|yml`. Prefix overlays numerically when order
matters. Later workflow definitions with the same case-insensitive ID replace
the earlier workflow definition wholesale; they do not deep-merge it. Keep a
workflow's complete definition in one winning overlay.

At runtime, an installed `config_source` is authoritative. YAML is the common
local source, but the portal uses Postgres. Some non-strict listing paths can
fall back to an empty/default config on source errors; strict compile,
preflight, or runner loading is the proof that matters.

The common authored surface includes `agents`, executable `phases`,
`workflows`, `default_workflow_ref`, pack references, tool/integration policy,
MCP bindings, schedules, triggers, and related runtime sections. Every phase
referenced by a workflow must have an executable definition under `phases`;
a catalog entry alone is insufficient.

## Workflow composition

Simple phase entries are IDs. A rich entry is a single-key map whose key is
the phase ID; do not add a sibling `id` field.

```yaml
workflows:
  - id: orders-delivery
    name: Orders delivery
    phases:
      - orders-implement
      - orders-review:
          on_verdict:
            rework:
              target: orders-implement
      - orders-test
```

Subworkflows (`workflow_ref`) are expanded inline with cycle detection.
Expanded phase IDs must remain unique because state, retry counters, and
phase-output filenames are ID-keyed.

## Conditional omission and decisions

`skip_if` is a list of small expressions evaluated before dispatch. It
supports `==` and `!=` against recognized scalar attributes such as
`subject_kind`, `subject_id`, `task_type`, `priority`, and requirement status.
Validate every expression; `task.type` is not the runtime field name.

Do not emit a `skip` verdict to mean “continue without this phase.” Emitted
`skip` closes the workflow: `already_done` in its reason completes it;
otherwise it cancels. Use `skip_if` for a phase-local omission.

`on_verdict.<key>.target` is enforced and keys can be custom strings. The
transition `guard` field currently is not evaluated. Agent-selected target
overrides require `allow_agent_target` and, preferably, `allowed_targets`.
Use `phases.<target>.retry.max_attempts` for the real semantic loop bound; the
counter belongs to the phase being re-entered. `max_attempts: 1` allows one
re-entry (two total target executions). Rich-entry `max_rework_attempts` is not
consumed by the rc.50 lifecycle.

## Budgets

Workflow/phase budgets are coarse circuit breakers observed by daemon cost
aggregation, not hard per-request token or currency caps. A daemon sweep,
provider usage metadata, and a working journal are required for enforcement;
there can be lag and unobserved spend. Keep provider-side limits and bounded
attempts as primary controls.

Portal Team Studio currently writes workflow `budget: null` and empty
descriptions on full publication, so a later Studio save can erase values
authored through lower-level config tools.

## Worktrees, environments, and workspaces

These are separate concepts:

- Subject integration may create/reuse a managed task worktree regardless of
  the workflow's `worktree` declaration.
- `cwd_mode: task_root` directs a command to that task checkout.
- Workflow/phase `environment` selects an execution environment when the
  active runner and environment plugin implement it.
- `workspace` selects a named repository/workspace definition for those
  environment-backed runs.

Environment precedence is phase override, first matching routing rule,
workflow setting, default, then local execution. The older runner pinned by
the CLI source manifest does not consume environment/workspace/worktree
policy; the current portal does use environment/workspace with a compatible
plugin. Verify by plugin version and canary.

Portal targeted `team_workflow_set` cannot express and may strip
`environment`, `workspace`, and `publication`; do not use it to update a
workflow that carries those fields.

## Explicit publication

There is no hidden kernel “auto git” policy. Publication must be explicit:

```yaml
workflows:
  - id: orders-delivery
    phases: [orders-implement, orders-test]
    publication:
      schema: animus.workflow-publication.v1
      version: 1
      required: true
      owner:
        kind: runner
      cleanup: after_remote_verified
```

Absence means publication is disabled; it is never inferred from a workflow
name. `required: false` cannot declare an owner. A required contract has one
owner:

- `kind: runner`: after phases pass, a compatible runner publishes the exact
  fenced head/recovery ref, ensures the PR, independently verifies remote ref,
  commit, and tree, then records the receipt. This requires a task subject,
  queue-backed execution fence, and reserved repository base/head.
- `kind: phase, phase_id: <id>`: exactly one named agent/command phase owns
  publication and must emit `animus.publication-receipt.v1`. A command owner
  needs JSON parsing and the expected result kind. Manual phases cannot own it.

`cleanup` is `retain` or `after_remote_verified`. Failure, auth denial,
unknown remote state, or stale generation must retain the environment and
recovery state. Never clean merely because local process execution succeeded.

The publication contract proves the fenced head; it does not name a phase
output containing “the tested head.” For exact-test provenance, have the test
phase emit top-level scalar commit/tree values and place a final read-only gate
after review that requires current clean HEAD/tree to equal those values. Put
no write-capable phase between that gate and runner publication, and canary the
runner/fence behavior.

Publication enforcement is runner-version dependent. Portal runner 0.4.71
supports the contract; the older runner in the CLI rc.50 default manifest does
not. On an older deployment, use explicit agent/command publish and verify
phases, each with least privilege and a durable effect receipt.

Do not equate workflow success, publication success, PR merge, deployment,
and subject completion. Model and verify whichever terminal fact the business
process actually requires.
