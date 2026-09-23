# Runtime Architecture and Workflow Lifecycle

This reference describes the current rc.50 kernel and the hosted portal's
runner 0.4.71. Always inspect the deployed runner/plugin versions: the CLI
repository's default install manifest can pin older behavior.

## Architecture: kernel contracts, plugin-owned behavior

The Animus kernel owns config compilation, the plugin host, scheduling,
lifecycle transitions, runtime contracts, and projections. Plugins supply the
operational roles:

- `config_source`: canonical workflow configuration
- `subject_backend`: tasks and other qualified subjects
- `queue`: durable admission, leases, and dispatch authority
- `workflow_journal`: durable run/event projection
- `workflow_runner`: phase execution and runner-side contracts
- provider/session backends: model/tool execution
- environment provider: remote workspace allocation and execution
- transports, log storage, notifications, and other optional integrations

A daemon-capable install currently needs a provider, a subject backend, a
workflow runner, a queue, and a config source. Check preflight; do not infer
role availability from installed binaries alone.

Project files under `.animus/` declare configuration, manifests, and locks.
Mutable local runtime state is scoped outside the repo under
`~/.animus/<repo-scope>/`. On the portal, Postgres and `/data` replace much of
that local storage. Treat all managed state as API/CLI-owned.

## End-to-end lifecycle

```text
external fact / operator request
  -> qualified subject (kind:native-id)
  -> explicit queue admission or actor-bound direct launch
  -> queue lease + workflow/subject/repository generation fence
  -> config and agent/provider resolution
  -> environment/workspace allocation when supported
  -> phase execution -> durable output -> lifecycle verdict
  -> evaluation gate when supported
  -> next phase, bounded rework, manual pause, or terminal state
  -> explicit publication/effect verification
  -> task/business-state reconciliation by its owning system
```

The daemon is queue-driven. A Ready subject is not automatically discovered
and run. Autonomous ingress should enqueue explicitly; schedules enqueue at
their due time. The portal's current coding scheduler uses a bounded five-slot,
generation-fenced path so stale or colliding repository generations do not
enter execution. That capacity is deployment policy, not a universal kernel
default.

One authoritative workflow ID is reserved through dispatch. The execution
fence binds the queue lease, workflow and subject generations, and any
reserved repo base/head. A stale runner must not publish, release, or mutate a
newer generation. Preserve the fence across retries and handoffs.

## Launch idempotency

Queue and direct-launch idempotency protect dispatch, not downstream effects.

- Reusing a queue key with the same effective request returns the original
  receipt; changing request content conflicts.
- Actor-bound detached workflow keys require authenticated `user_id` and
  `tenant_id`, are limited to 128 characters in `[A-Za-z0-9._:-]`, and bind
  workflow, input, variables, and actor. A pending reservation may be
  reclaimed after its lease; every outer portal reservation must recover too.
- The portal's public MCP `queue_enqueue` and `run_workflow` wrappers may omit
  fields exposed by the core CLI. Inspect the live tool schema before assuming
  an idempotency key or arbitrary input is accepted.
- A downstream write, message, deployment, or payment needs its own stable
  idempotency key and outcome ledger.

## Phase and lifecycle semantics

- `skip_if` is evaluated before dispatch and can bypass consecutive phases.
  Its expression language is deliberately small (`==` and `!=` over supported
  scalar subject fields).
- `advance` continues. `rework` follows the configured target and consumes the
  phase-definition retry budget. `fail` terminates.
- An emitted `skip` is terminal: a reason containing `already_done` completes
  the run; otherwise it cancels it. Use `skip_if` to omit one phase and keep
  going.
- Runner/transport exceptions are infrastructure failures, not semantic
  rework. Do not spend an agent loop on missing credentials, provider auth,
  absent tools, or a broken environment.
- Full-pipeline execution persists phase output before advancement and uses
  completion markers for crash replay. `workflow execute --phase` is a
  diagnostic single-phase surface; it does not perform the full lifecycle or
  normal terminal projection.
- Successful workflow completion deliberately does not mark a task Done.
  The subject/business backend owns that transition after its required proof.

## Capability matrix

`animus --version` identifies the kernel, not all execution behavior.

| Capability | rc.50 schema/kernel | CLI default runner pinned in the rc.50 source manifest | Current portal runner 0.4.71 |
|---|---|---|---|
| agent/command/manual phases and lifecycle routing | yes | yes | yes |
| command JSON `phase_decision` | yes | yes | yes |
| phase `evals` execution | parsed/validated | not executed by the older pinned runner | enforced for command and `llm_judge` checks |
| workflow `permission_mode` transport | modeled | verify provider/runner path | honored by the current portal path; not an authorization boundary |
| environment/workspace routing | modeled | not consumed by the older pinned runner | used with a compatible environment plugin |
| explicit publication contract | validated | not enforced by the older pinned runner | runner- or phase-owned receipt enforcement |

The separately developed default runner gained these features after the old
CLI manifest pin. A local operator may install a newer runner, so inspect the
active plugin version and run a canary instead of identifying capability from
the kernel version.

## State and observability

Workflow truth is the journal/state projection plus phase decisions. Detailed
transcripts and artifact files are useful but may be absent, pruned, local to
another instance, or stored remotely. Do not make transcript availability the
only completion test.

Use these categories when diagnosing a terminal run:

1. **Business branch:** the inputs legitimately produce approve/reject/no-op.
2. **Deterministic gate:** a command exits successfully but emits a `fail` or
   `rework` decision. Process success is not workflow success.
3. **Infrastructure:** provider auth, capacity, environment, runner, plugin,
   or transport failed. Escalate/repair; do not semantic-loop.
4. **Ambiguous side effect:** the request may have reached an external system
   but no durable receipt was observed. Reconcile before any replay.
5. **Stale generation:** the fence no longer owns the repo/subject generation.
   Stop and let the current owner proceed.

For every production workflow, retain enough correlation to connect subject,
queue receipt, run ID, phase attempts, external idempotency keys, and final
verification receipts.
