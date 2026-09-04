# Automation and Integrations

## Queue-first autonomous dispatch

The daemon drains explicit queue entries and due schedules; it does not scan
all Ready subjects. Admit only a subject state intended for execution (normally
Ready or InProgress), select the workflow explicitly, and retain the queue
receipt. Use direct `workflow run` for an operator-controlled run, not as the
default webhook/automation boundary.

The scheduler is event-driven by queue nudges, completions, config reload,
cron/deferred deadlines, with a heartbeat fallback. Do not tune workflow YAML
as though it were a polling loop.

## Three independent idempotency layers

1. **Dispatch key:** queue or detached workflow `idempotency_key` deduplicates
   producer retries. Derive it from an immutable event/delivery ID.
2. **Phase idempotency:** phase `idempotency` and crash markers prevent unsafe
   repetition during runner recovery. This is not producer deduplication.
3. **Effect key:** each external write uses a stable key/conditional request
   understood by the downstream system and records an effect receipt.

Reusing a dispatch key with the same effective request replays the canonical
receipt; changed content conflicts. An unkeyed producer retry creates another
entry. Actor-bound detached launch additionally binds user, tenant, workflow,
input, and variables.

The portal MCP wrapper is narrower than the core CLI: current
`queue_enqueue` accepts exactly a `subjectId` or a title plus a few scheduling
fields, and `run_workflow` accepts subject/workflow. Neither necessarily
exposes the core idempotency/input fields. Trusted portal producers and the
application API can provide stronger keys; always inspect the live schema.
The trusted application launch endpoint is
`POST /api/application/v1/subjects/:kind/:id/runs` with an
`Idempotency-Key` header and optional `{"workflow_ref":"..."}` body. It
derives actor and execution configuration server-side and requires the
subject's authorized `launch` action.

## Schedules and triggers

Build and canary the workflow manually before attaching ingress. A trigger is
an event producer, not a place to hide business logic.

- Validate the workflow reference and cron semantics before save; persistence
  alone may not prove either.
- Stagger schedules to avoid provider/capacity spikes.
- Portal cron is five-field UTC, checked on a minute loop, with bounded missed
  tick catch-up. Current cron/test enqueue has weaker crash deduplication than
  GitHub deliveries.
- Portal GitHub deliveries have a durable delivery ledger and deduplicate by
  trigger/delivery identity. Use delivery list/replay for reconciliation.
- Record observation-only events without enqueuing when no action is required.

One external fact should normally launch one bounded workflow. If a customer
reply or approval arrives later, launch a continuation workflow keyed by that
new fact instead of parking an agent run indefinitely.

## MCP and tool policy

Use agent-level MCP assignments for the smallest authority surface. The
actor-bound workflow MCP surface is intentionally smaller than management MCP
and can omit queue/config/global operations. Agents must tolerate that.

`phase_mcp_bindings` can add servers for a specific phase in core config, but
the portal Team serialization currently drops this section. Prefer
agent-level assignments for portal-managed workflows until round-trip support
is verified.

An MCP server assignment and prompt are defense in depth, not authorization.
The server must enforce actor, tenant, resource, and operation permissions.
Use secret references such as `${secret.NAME}`; never embed credentials in
workflow YAML, scripts, or directives. Review stdio commands and HTTP targets
as code-execution/network trust boundaries.

Command programs also require the daemon's positive `tools_allowlist`.
Allowlisting an interpreter allows whatever reviewed script it executes, so
keep durable scripts versioned/controlled and inputs constrained.

## External effects

Classify every integration action before authoring:

| Class | Workflow treatment |
|---|---|
| read/observe | retryable within bounded transport policy |
| propose/draft | durable output; no external authority yet |
| reversible write | downstream idempotency key + receipt + bounded retry |
| irreversible/high-impact write | precondition, human/server authorization, idempotency, independent verification |
| unknown outcome | stop and reconcile; never blind replay |

Approval, execution, delivery, and acknowledgement are different facts. For
example, “approved to send” is not “provider accepted,” and provider accepted
is not “recipient received.” Emit and persist the exact fact you have.

## Fan-out and fan-in

Prefer one workflow with explicit phases when work shares one subject and
publication boundary. Use multiple workflows only when they have independent
ownership, time horizons, or retry domains. Fan-in must query durable child
state/receipts and handle partial completion; do not infer completion from an
agent transcript.
