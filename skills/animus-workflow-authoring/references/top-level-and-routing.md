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
models:
tools_allowlist:
mcp_servers:
phase_mcp_bindings:
tools:
integrations:
schedules:
triggers:
daemon:
```

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
- A rich phase entry with `max_rework_attempts`, `on_verdict`, and `skip_if`
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

## Post-success hooks

Use `post_success.merge` to control merge and PR behavior after all phases succeed.

```yaml
workflows:
  - id: standard
    name: Standard
    phases:
      - workflow_ref: animus.task/standard
    post_success:
      merge:
        strategy: merge
        target_branch: main
        create_pr: true
        auto_merge: false
        cleanup_worktree: true
```

Supported merge strategies are `squash`, `merge`, and `rebase`.
