# Patterns And Examples

Use this reference when you need concrete workflow shapes, rework loops, sub-workflow composition, or pack-wrapping examples.

## Complete YAML structure

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

## Tools allowlist

```yaml
tools_allowlist:
  - npm
  - npx
  - node
  - pnpm
  - git
  - gh
  - WebSearch
  - WebFetch
```

## MCP servers

```yaml
mcp_servers:
  context7:
    command: npx
    args: ["-y", "@upstash/context7-mcp"]
  package-version:
    command: npx
    args: ["-y", "mcp-package-version"]
  sequential-thinking:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  memory:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-memory"]
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
```

## Wrap bundled pack refs

Prefer pack refs when you want standard Animus behavior with light repo-local customization.

```yaml
default_workflow_ref: standard-workflow

workflows:
  - id: standard-workflow
    name: Standard Workflow
    description: Repository default delivery workflow.
    phases:
      - workflow_ref: animus.task/standard

  - id: ui-ux-workflow
    name: UI UX Workflow
    phases:
      - workflow_ref: animus.task/ui-ux
```

## Workflows

```yaml
workflows:
  - id: scaffold
    name: "Scaffold Workflow"
    description: "Implement -> Build -> Push -> PR -> CI -> Review"
    phases:
      - implementation
      - install-deps
      - build-check
      - lint-check
      - push-branch
      - create-pr
      - wait-for-ci
      - pr-review:
          on_verdict:
            rework:
              target: implementation

  - id: quick-fix
    phases: [implementation, install-deps, build-check, lint-check, push-branch, create-pr, wait-for-ci, pr-review]

  - id: rework
    description: "Address reviewer feedback"
    phases: [address-review, force-push, pr-review]

  - id: rebase-and-retry
    description: "Rebase conflicting branch"
    phases: [rebase-on-main, force-push, pr-review]
```

## Phase catalog

Use `phase_catalog` for UI-facing labels and metadata without changing execution behavior.

```yaml
phase_catalog:
  implementation:
    label: "Implementation"
    description: "Implement production-quality code changes"
    category: development
    tags: [coding, implementation]
```

### Rework support

Only use rework on agent phases.

```yaml
  - pr-review:
      on_verdict:
        rework:
          target: implementation
```

Do not put rework on command phases like `build-check`, `lint-check`, or `wait-for-ci`.

## Skills and runtime on phases

```yaml
phases:
  pr-review:
    mode: agent
    agent: pr-reviewer
    directive: "Review open PRs"
    skills:
      - code-review
    runtime:
      tool: claude
      model: claude-sonnet-4-6
    decision_contract:
      min_confidence: 0.7
      max_risk: medium
      allow_missing_decision: false
```

Phase `skills:` are resolved daemon-side at dispatch and applied by the
workflow runner (v0.4.2+). Verify application with
`animus output phase-outputs --workflow-id <id>` (requested vs applied vs
missing) or preview with `animus workflow prompt render`. Unresolvable
explicit skill names warn at compile time in
`animus workflow config validate` / `compile` — never a hard failure.

## Budget-capped autonomous workflow

```yaml
workflows:
  - id: overnight-batch
    name: Overnight Batch
    phases: [implementation, build-check, pr-review]
    budget:
      max_cost_usd: 5.00
      on_exceed: pause     # daemon pauses the workflow on breach
```
