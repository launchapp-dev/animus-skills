# Top-Level And Routing

Use this reference when deciding which top-level sections belong in a workflow YAML file, or when composing workflows out of pack refs and sub-workflows.

## Current top-level authored surface

`animus-cli` currently supports these top-level sections in workflow YAML:

```yaml
default_workflow_ref:
phase_catalog:
workflows:
phases:
agents:
agent_channels:
models:
tools_allowlist:
mcp_servers:
phase_mcp_bindings:
tools:
integrations:
schedules:
triggers:
daemon:
secrets:
```

`agent_channels:` defines named channels for agent-to-agent messaging.

`secrets:` maps logical secret names to env vars (`env`, `required` —
default true, `description`); reference them in any YAML scalar with
`${secret.<name>}`. Resolution happens at compile time: explicit process env
wins, then the project-scoped keychain populated by `animus secret set`.
A plain `${VAR}` whose name matches `TOKEN|KEY|SECRET|PASSWORD` outside the
`secrets:` block lints a move-it-to-secrets warning. `${...}` inside YAML
comments is not interpolated, and `animus workflow phases upsert` /
`definitions upsert` write generated overlays with `${...}` references
preserved unresolved — resolved secret values never land in the project tree.

Prefer this list over older docs that still describe `pipelines:` as the canonical surface.

## Default workflow ref

Use `default_workflow_ref` when the repo should have a stable default workflow if no explicit ref is passed.

```yaml
default_workflow_ref: standard-workflow
```

The referenced workflow must exist.

## Workflow definitions

Project-local workflow definitions live under `workflows:`.

```yaml
workflows:
  - id: standard-workflow
    name: Standard Workflow
    description: Repository default delivery workflow.
    phases:
      - workflow_ref: animus.task/standard

  - id: hotfix-workflow
    name: Hotfix Workflow
    description: Fast-track workflow for urgent fixes.
    phases:
      - workflow_ref: animus.task/quick-fix
```

Project YAML usually wraps canonical pack refs instead of reimplementing bundled task logic.

## Workflow phase entries

Workflow phases can be:

- A simple phase ID like `implementation`
- A rich phase entry (a single-key map) with `max_rework_attempts`,
  `on_verdict`, `skip_if`, and `budget`
- A sub-workflow reference via `workflow_ref`

```yaml
workflows:
  - id: delivery
    name: Delivery
    phases:
      - requirements
      - implementation
      - code-review:
          max_rework_attempts: 3
          on_verdict:
            rework:
              target: implementation
            advance:
              target: testing
          skip_if:
            - "task.type == 'docs'"
      - testing
```

## Sub-workflows

Use `workflow_ref` entries to compose reusable sequences inline.

```yaml
workflows:
  - id: review-cycle
    name: Review Cycle
    phases:
      - code-review
      - testing

  - id: standard
    name: Standard
    phases:
      - requirements
      - implementation
      - workflow_ref: review-cycle
```

Avoid circular sub-workflow references. Validation rejects them.

## Variables

Workflow variables can be declared on the workflow definition and filled via runtime input.

```yaml
workflows:
  - id: release
    name: Release
    phases:
      - implementation
      - testing
    variables:
      - name: target_branch
        description: Branch to merge into
        required: false
        default: main
      - name: reviewer
        description: Assigned reviewer
        required: true
```

Variable expansion uses `{{var_name}}` placeholders in authored text.

## Budget caps

A `budget:` block sets cost ceilings, either top-level on a workflow
definition (authoritative across all phases) or inline on a rich phase entry
(resets per rework attempt). At least one of `max_tokens` / `max_cost_usd`
is required, both must be > 0.

```yaml
workflows:
  - id: expensive-flow
    name: Expensive Flow
    phases:
      - exploration:
          budget:
            max_tokens: 100_000
            max_cost_usd: 1.00
            on_exceed: fail
      - implementation
    budget:
      max_tokens: 1_000_000
      max_cost_usd: 5.00
      on_exceed: pause      # pause (default) | fail | warn
```

Caps are ENFORCED by the daemon's housekeeping sweep (once per heartbeat
interval): on a newly crossed cap, `pause` pauses the workflow, `fail` fails
the current phase terminally, `warn` records and notifies only. Breaches are
visible in `animus subject get` (inline pause cause), `animus daemon health`
(`budget_enforcement` line + 24h rollup), and `animus status`. Caveats: a
phase in flight can overshoot by up to one sweep, and enforcement requires a
running daemon. Kill-switch: `ANIMUS_DAEMON_DISABLE_BUDGET_ENFORCEMENT=1`
(daemon restart required).

A separate `daemon.budget` sub-block (under `daemon:`) caps total fleet spend
across all workflows — `max_cost_usd_per_day` with `on_exceed` — distinct from
the per-workflow/per-phase `budget:` field shown above. There is no top-level
`budget:` key: it exists only as `daemon.budget` and as the per-workflow /
per-phase `budget:` field.

## Worktree control

A `worktree:` block on a workflow definition sets the default; a phase-level
`worktree:` always overrides it. Modes: `auto` (default), `required`
(fail-fast if creation fails), `skip` (run in the project root). Long form
adds `cleanup` (default true) and `base_ref`; `worktree: skip` is accepted as
a short-form scalar. Enforcement is owned by the workflow runner plugin
(v0.4.0+); older runners treat everything as `auto`.

## Git automation = command phases

Animus no longer performs git operations as runner automation. `post_success.merge`
and the daemon-level git policy keys were removed in v0.5.x and now fail to parse.
Express commit/push/PR/merge as `command:` phases — a phase with a `command:`
block running `git`/`gh`:

```yaml
phases:
  push-branch:
    mode: command
    command:
      program: git
      args: ["push", "-u", "origin", "HEAD"]
      cwd_mode: task_root
  create-pr:
    mode: command
    command:
      program: gh
      args: ["pr", "create", "--fill", "--base", "main"]
      cwd_mode: task_root

workflows:
  - id: standard
    name: Standard
    phases:
      - workflow_ref: animus.task/standard
      - push-branch
      - create-pr
```
