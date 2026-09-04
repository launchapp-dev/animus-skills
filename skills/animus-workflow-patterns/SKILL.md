---
name: animus-workflow-patterns
description: Choose and implement safe Animus workflow patterns for coding delivery, deterministic quality gates, bounded rework, event automation, approval, publication, and external side effects. Use when deciding workflow shape or reviewing whether a workflow is production-ready.
metadata:
  user_invocable: false
  auto_invoke: true
  animus_version: "0.7.0-rc.50"
---

# Animus Workflow Patterns

There is no single production scaffold. Select the smallest state machine that
matches the subject, authority boundary, side effects, and deployed runner.

Read
[the pattern catalog](../animus-workflow-authoring/references/optimal-patterns.md)
for detailed coding, event, approval, research, and recovery patterns. Read
[runtime and lifecycle](../animus-workflow-authoring/references/runtime-and-lifecycle.md)
before relying on evals, environments, publication, or crash recovery.

## Core invariants

1. One run represents one bounded fact or unit of work. A later human/external
   event normally starts an idempotent continuation run.
2. Autonomous work enters through the queue; Ready subjects do not launch
   themselves.
3. Phase IDs are globally keyed and should be namespaced by workflow/domain.
4. Deterministic facts belong in command phases. Judgment and generation
   belong in agent phases. Human authority belongs in manual/application
   approval.
5. Repository edits require `writes_files: true`. `mutates_state: true` alone
   tells the agent not to edit repository files.
6. Bound semantic loops on the rework target with
   `phases.<target>.retry.max_attempts`; `1` permits one re-entry. Do not depend on
   rich-step `max_rework_attempts`, transition `guard`, or provider retry
   declarations that the lifecycle does not consume.
7. Dispatch idempotency, phase crash idempotency, and downstream-effect
   idempotency are three different contracts.
8. Workflow success, task completion, publication, merge, deployment, and
   delivery are separate facts. Persist and verify the fact that matters.

## Default design sequence

```text
preflight -> produce -> deterministic verify -> judgment/approval if needed
          -> exact-output/head gate -> effect/publication
          -> independent verification -> reconcile
```

Omit stages that add no value. Dependency install is conditional and
lockfile-safe, not universal. Prefer focused tests before expensive broad
checks. A reviewer reworks only actionable product defects; auth, capacity,
missing tools, and broken environments go to an operator.

For coding on the current portal, prefer explicit runner-owned publication
with exact-head remote verification. On an older/default runner that does not
enforce the publication contract, implement separate least-privilege publish
and verify phases. Never force-push or merge through failing, pending, or
stale-head checks unless an explicit human policy authorizes that exact action.

## Decision loop

```yaml
phases:
  billing-implement:
    mode: agent
    agent: implementer
    capabilities:
      writes_files: true
      requires_commit: true
    retry:
      max_attempts: 1

workflows:
  - id: billing-delivery
    phases:
      - billing-implement
      - billing-test
      - billing-review:
          on_verdict:
            rework:
              target: billing-implement
      - billing-exact-head-gate
```

The review phase must produce a structured decision. Routing back re-executes
the implementation, test, and review phases; the target implementation's
`max_attempts: 1` permits exactly one such remediation. The final gate must
require the current clean head/tree to match the recorded tested and reviewed
head before publication. An eval layer can add
command/LLM checks on current runners, but its in-memory rework count resets
after runner restart; keep the lifecycle bound.

## External effects

Before a write, verify current authorization and preconditions. Send a stable
downstream idempotency key, record the request correlation, and query the
external system for an independent receipt. If the outcome is unknown, stop
and reconcile; never blindly replay.

Treat approval, provider acceptance, execution, and delivery as separate
states. Prompts and tool filtering are not authorization; enforce actor,
tenant, resource, and operation scope at the server/API boundary.

## Production readiness checklist

- Effective config was re-read after write/reload.
- Active runner/plugin/provider versions support every relied-on field.
- Provider auth/capacity, tools, skills, MCP servers, secrets, and environment
  pass preflight.
- Every write-capable phase has explicit least privilege.
- Every cycle has a real durable bound and terminal escape.
- Dispatch and external effects have independent stable keys.
- Publication/effects retain recovery state until remote verification.
- One canary has exercised the exact subject, provider, environment, and
  terminal-effect path.
- Monitoring uses journal state/decisions/receipts, not transcript presence.

For hosted authoring limitations, read
[animus-portal-operations](../animus-portal-operations/SKILL.md).
