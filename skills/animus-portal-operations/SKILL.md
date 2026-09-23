---
name: animus-portal-operations
description: Operate and author workflows on the hosted animus-launchapp Portal, including live MCP discovery, Team config, provider capacity, scripts, queues, triggers, runtime health, durability, and break-glass SQL. Use when the target is the hosted Portal; use the local domain skills without this one for a YAML-only CLI project.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---

# Animus Portal Operations

The portal is a hosted Animus kernel with Postgres-backed Team config,
subjects, queue, and workflow journal; durable `/data` state; independently
versioned plugins/runner; and an OAuth-protected MCP/application boundary.
Current production pairs rc.50 with runner 0.4.71.

Read
[portal runtime and authoring limits](../animus-workflow-authoring/references/portal-runtime-and-authoring.md)
before mutating Team config or relying on durability. Read
[runtime and lifecycle](../animus-workflow-authoring/references/runtime-and-lifecycle.md)
when diagnosing execution.

## Discover, then act

Tool names are flat snake_case, but the host prefix is client-defined (for
example this environment may expose `mcp__launchapp__...`). Parameter casing
also varies. Inspect the connected server's live tool schema; do not hard-code
a prefix or infer authority from tool visibility.

Start with:

1. `daemon_health` and plugin/runtime status
2. `team_config_get` for canonical effective Team config
3. agent/provider/capacity status and advertised models
4. installed skills, MCP definitions, scripts, and command allowlist
5. queue and recent run events for operational context

Admin-gated tools may remain discoverable and then return `forbidden`, while
other clients may hide them. A schema being visible grants nothing.

## Safe Team authoring

Phase IDs share one global map; namespace them. Create/verify prerequisites
before composing the workflow. Use one full Team Studio publication for
multi-object changes when possible: it validates the model, serializes writes,
creates a receipt, applies/reloads, and rolls back on failure.

Targeted MCP writes are suitable only when their schema covers the complete
object you intend to preserve:

- `team_agent_set`: current legacy provider/tool/capacity/model fields are the
  safest portal round-trip surface.
- `team_phase_set`: useful for simple agent/command/manual definitions, but it
  stamps phase idempotency to `unknown`.
- `team_workflow_set`: handles ID/name/description/phases/budget but can strip
  `environment`, `workspace`, and `publication` from an existing workflow.
- Team serialization can drop `phase_mcp_bindings`; prefer least-privilege
  agent-level MCP assignments.

Therefore: read before write, avoid targeted updates to workflows with opaque
execution metadata, reload, and re-read the entire affected object. Use a
portal-owned, versioned reconciler/release for a new workflow whose advanced
fields the Team model cannot author; this is a code/release change, not a
hidden MCP operation. The system PR-review assets are protected and must not
be repurposed.

## Break-glass SQL

Direct SQL is an exceptional repair path when a confirmed portal bug or
lossy authoring surface leaves no supported way to make a bounded, reversible
change. It is not a convenient substitute for Team publication, targeted MCP
writes, an application endpoint, or a versioned reconciler.

Before any `sql_execute`, read the **Break-glass SQL repairs** section in
[portal runtime and authoring limits](../animus-workflow-authoring/references/portal-runtime-and-authoring.md).
The minimum gate is: establish the live schema and source-of-truth behavior;
quiesce affected dispatch; capture a durable before-image and rollback;
perform one preconditioned, parameterized transaction under
`pg_advisory_xact_lock(1906075)`; update every representation and cache token
the deployed reader actually consumes; reload, re-read, and canary before
resuming. Never use the session-scoped advisory lock through pooled
`sql_execute` connections.

Do not generically repair queue leases, run journals/fences, delivery or
idempotency ledgers, publication receipts, authentication/membership,
OAuth/secrets, or provider-capacity state. Those require a subsystem-specific
recovery procedure because a plausible-looking row edit can duplicate work,
violate ownership, or conceal an ambiguous external effect.

## Durable command phases

Use Team Scripts for deterministic logic that must survive redeploy without a
new image. Call `phase_context_schema` first; it is the authoritative contract
for `ANIMUS_*` variables, the context file, and decision output.

Store a bash/Python/TypeScript script, invoke its materialized path with the
allowlisted interpreter, set `parse_json_output: true`, and print exactly one
`phase_decision` object. Process exit 0 can still produce a workflow `fail` or
`rework` verdict; inspect the decision, not only the exit code.

## Dispatch and operations

Queue admission is the normal automation path. The public portal MCP enqueue
and run wrappers are narrower than the core CLI, so inspect their schema for
idempotency/input support. Trusted application launches can bind an actor and
durable idempotency key. Keep subject, delivery, queue receipt, run ID, and
external effect receipt correlated.
When MCP does not expose the needed key, use the authorized application
endpoint `POST /api/application/v1/subjects/:kind/:id/runs` with an
`Idempotency-Key`; the body may contain only optional `workflow_ref`.

Before enabling a trigger, validate its workflow/cron and canary the exact
path. GitHub delivery replay/deduplication is stronger than current cron/test
crash handling. Use trigger delivery tools and journal events to reconcile.

Treat provider authentication/capacity errors as readiness failures, not agent
rework. Run history and journal decisions are authoritative; transcripts and
S3/local details may be unavailable.

## Security and durability

- MCP/application requests recheck membership and resource policy. Tool
  assignment and `permission_mode` do not replace server authorization.
- Use `${secret.NAME}` references. External MCP definitions are an admin trust
  boundary; review stdio commands and HTTP endpoints.
- Never rely on `mcpServers: []` as a deny rule: portal serialization can drop
  it and omission can fall through to all configured servers.
- GitHub-source skill installs in the volume registry are durable. Local path
  installs and project/user skill creation are ephemeral in the portal image.
- Team Scripts are durable. Ad-hoc plugin/scope changes can be reverted by the
  next locked runtime activation; permanent changes belong in the release
  manifest/lock.
- `/healthz` proves liveness, not runtime readiness. Check `/readyz`, active
  manifest state, daemon/plugin/provider health, and a canary.
- Source skill edits are not automatically live: the portal seeds a pinned
  animus-skills git revision, which must be advanced in a release.

Use the portal for execution only after the effective config and canary agree
with the intended workflow. Do not mutate the live Team merely to test an
assumption that can be checked read-only.
