# Optimal Workflow Patterns

There is no universal scaffold. Choose the smallest pattern that matches the
effect, uncertainty, and ownership boundary.

## Coding delivery

Recommended shape:

```text
preflight -> implement -> deterministic checks -> review/evals
          -> exact-head publication -> independent remote verification
          -> subject reconciliation
```

- Preflight provider auth/capacity, repo/base/head reservation, required
  tools, secrets, and environment readiness before spending model tokens.
- The implementation phase declares `writes_files`; add `requires_commit`
  only if the publication path requires a commit.
- Install dependencies only when the repository requires it; use its package
  manager and lockfile-safe/frozen mode.
- Run focused tests first, then the minimum broader gates justified by risk.
  Record the tested commit/tree as top-level scalar outputs.
- Use a deterministic command for build/lint/test facts. Use an agent reviewer
  only for judgments deterministic tooling cannot make.
- After review, run a final read-only gate that requires the current clean
  HEAD/tree to equal the recorded tested and reviewed head. Put no write-capable
  phase after that gate and before publication.
- On the current portal prefer runner-owned explicit publication. On runners
  without that contract, use explicit least-privilege publish and verify
  phases. Never merge on failing, pending, or stale-head checks.
- Treat `pending_ci`, `stale_head`, auth denial, and unknown remote result as
  non-publication outcomes. Retain recovery state.

## Bounded quality loop

```text
producer -> deterministic verifier -> [advance | rework producer | fail]
```

Use rework only when the producer can change the failed condition. Put the
durable bound on the rework target: `phases.<target>.retry.max_attempts`.
The value is permitted re-entries, so `1` means exactly one remediation and at
most two executions of that producer. Provider auth,
missing tools, environment failure, or an invariant violation should block or
fail to an operator rather than burn the loop.

Current runners can attach `evals` to an advancing phase, but eval rework
counts reset across runner restart. Combine evals with lifecycle bounds and
use command checks for load-bearing deterministic criteria.

## Event ingestion and continuation

```text
delivery claim -> validate/classify -> no-op OR enqueue bounded workflow
workflow -> proposal/effect -> receipt -> finish
later external event -> new idempotent continuation workflow
```

Use the immutable delivery/event identity for dispatch deduplication. Store
the correlation from delivery to queue receipt to run ID. A duplicate delivery
should replay its receipt, not create a parallel run. An event that changes no
actionable fact should be journaled and acknowledged without dispatch.

Do not keep a workflow open while waiting for ordinary customer or partner
behavior. A later fact is a new bounded execution and retry domain.

## Approval and high-impact effects

Split proposal from authority:

```text
analyze -> durable proposal -> human/server approval -> perform effect
        -> query external system -> verified receipt
```

Re-read authorization immediately before the effect. Use conditional writes
or a downstream idempotency key. If the client times out after submitting,
reconcile by key/status; do not assume failure and send again.

Manual phases are appropriate for short, workflow-owned gates. For long-lived
business approval, end after the proposal and dispatch a new workflow from the
approval event.

## Research or decision workflow

Use agents for evidence gathering/synthesis and command phases for mechanical
normalization or validation. Require structured outputs only for fields a
later phase consumes. Add a human gate when the decision grants authority;
model confidence is not authorization.

## Recovery and operations

Before retrying, classify the failure:

- semantic `rework`: actor can improve the output
- deterministic `fail`: input/invariant says stop
- infrastructure: repair provider/plugin/environment and resume or relaunch
- stale generation: abandon the old owner
- ambiguous side effect: reconcile externally before replay

Production readiness requires a canary with the exact workflow, subject kind,
provider/capacity path, environment, tools, and publication/effect boundary.
Monitor journaled decisions and receipts. Transcripts and artifacts are
diagnostic aids, not the sole source of truth.

## Anti-patterns

- One giant “implement, test, push, deploy, and report” agent phase
- `mutates_state` used as permission to edit repository files
- Unbounded reviewer/implementer cycles
- Rework on provider authentication or missing infrastructure
- Every workflow starting with unconditional dependency installation
- Blind force-push, merge despite checks, or cleanup before remote proof
- Treating workflow completion as task Done or external delivery success
- Treating tool visibility, prompts, or `permission_mode` as authorization
- Retrying an external write whose outcome is unknown
