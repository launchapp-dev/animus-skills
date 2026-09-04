# Portal Runtime and Authoring Limits

This describes the hosted animus-launchapp generation currently running
Animus rc.50 and workflow runner 0.4.71. Inspect live health and config first;
the release can advance independently of this document.

## Runtime topology and durability

Each organization has a Railway service/container, Postgres, and a `/data`
volume. The public proxy is the internet-facing boundary; Animus transports
and sidecars bind internally.

The base image does not blindly own the current runtime. A pinned, signed,
hashed manifest stages kernel/plugins/runner/web assets under `/data/runtime`,
checks compatibility and preflight, then atomically activates the candidate.
Failed activation preserves last-known-good. Hot activation restarts affected
processes and daemon recovery resumes orphaned runs.

`/healthz` is liveness and may remain 200 while runtime is degraded.
`/readyz`, daemon health, plugin/provider readiness, and the nested active
runtime state are the deployment proof.

Postgres is authoritative for Team config, subjects, queue/journal, auth,
trigger ledger, capacity metadata, and publication receipts. `/data` holds
runtime assets, workflow state/log artifacts, scripts, skills, secrets/OAuth
material, knowledge, and MCP binding materialization. A missing/unwritable
volume is fatal for a manifest-selected deployment.

## Authoring authority

First-boot YAML seeds Team config; it is not canonical afterward.

The safest multi-object authoring path is one full Team Studio publication:

1. Read the actor-scoped canonical Team model.
2. Validate agents, providers/capacity, global phase names, protected assets,
   skills, MCP servers, and transcript prerequisites.
3. Serialize under a Postgres advisory lock; no task runs during preview/
   publication.
4. Apply the full config, re-stamp portal metadata, seal an immutable
   publication receipt, and restore the previous snapshot on failure.
5. Reload and re-read effective config.

Targeted `team_*` MCP writes are useful for simple fields, but are not a
lossless general editor:

- `team_workflow_set` rebuilds only ID/name/description/phases/budget and can
  strip `environment`, `workspace`, and `publication`.
- `team_phase_set` stamps `idempotency: unknown` after `extraConfig`.
- Team serialization can drop `phase_mcp_bindings`; use agent-level bindings.
- Structured agent `runtimePolicy` is not reliably round-tripped. For
  portal-managed agents use current legacy provider/tool/capacity/model fields
  until the platform preserves it.
- Full Team publication currently emits empty workflow descriptions and null
  budgets, so it can erase lower-level values.
- Existing environment/workspace/publication metadata survives a full Studio
  save, but Studio cannot author those fields for a new workflow.

Do not update a workflow with opaque execution metadata through a targeted
MCP call. Use the full Team path when it can preserve the existing fields; use
managed bootstrap/release configuration for advanced fields the Team model
cannot create. Always compare `team_config_get` before and after.

For a **new** workflow that requires `publication`, `environment`, or
`workspace`, the current public Team UI/MCP is insufficient. Treat this as a
portal release change, not an operator workaround. Follow the portal-owned
reconciler pattern: define a versioned canonical contract in portal source,
acquire the Team publication advisory lock, read a rollback snapshot, build a
complete config that preserves unrelated sections, apply it through
`animus workflow config set --file -`, re-stamp portal ownership/runtime
metadata, seal the publication receipt, and restore the snapshot on any
failure. Advance the locked runtime/application release, then re-read and
canary. First-boot YAML can seed a new organization but is not a migration
mechanism for an existing canonical Postgres Team.

## Break-glass SQL repairs

`sql_execute` is a legitimate temporary repair path only when all of these are
true:

- A confirmed defect or lossy authoring surface makes the supported UI, MCP,
  application, CLI, or versioned reconciler path unavailable or unsafe.
- The intended change is narrow, its deployed read/write invariants are known,
  and it has a deterministic before/after check.
- The operation is reversible from a captured before-image and does not depend
  on guessing whether an external side effect already happened.
- An authorized admin accepts the incident scope. Discoverable admin tooling
  is not authorization by itself.

Do not use SQL to test an assumption, bypass validation or permissions, perform
broad cleanup, or save the effort of implementing a supported fix. The repair
must leave an issue or migration task with an owner and a removal condition;
otherwise a temporary workaround silently becomes an undocumented control
plane.

### Prepare and quiesce

1. Record the incident, deployed portal/kernel/plugin versions, target rows,
   expected diff, success checks, abort conditions, and rollback statement.
   Do not record secret values.
2. Inspect the live tool schema, then use `list_tables`, `describe_table`, and
   parameterized `sql_query` calls to establish the current schema, exact row
   count, dependent rows, and current values. Source code or an older schema is
   supporting evidence, not proof of the deployed database.
3. Identify what the deployed reader treats as authoritative. Team config can
   exist both as normalized `team_*` rows and in `team_config.config`; a change
   to only one representation can be ignored, reverted, or partially compiled.
   Update both only when the deployed load/write contract requires both, and
   preserve every unrelated JSON key.
4. Pause new leases with `daemon_pause`, disable only the affected triggers if
   they can still enqueue elsewhere, and wait for affected in-flight runs to
   become terminal. If the change cannot interfere with execution, document
   why a narrower quiescence boundary is safe. Do not proceed when ownership
   or in-flight status is uncertain.
5. Capture a durable before-image outside the live tables: the complete rows or
   JSON subtrees that will change, their identifiers and timestamps, and any
   dependent metadata needed to restore them. Keep sensitive snapshots in an
   approved secret-bearing incident store, not chat or logs. Verify the
   rollback predicate against current state before writing.

### Execute one guarded transaction

Use one `sql_execute` call for the complete repair. That tool already wraps the
submitted query in `BEGIN`/`COMMIT` and rolls back on error. The submitted SQL
must:

- Acquire `pg_advisory_xact_lock(1906075)`, the transaction-scoped equivalent
  of the Portal's whole-Team publication lock, in the same statement as the
  repair. With parameterized values, use an ordered CTE or another single-
  statement form that makes the write depend on the lock acquisition. Never
  call session-scoped `pg_advisory_lock` through the pooled SQL tool: the lock
  can survive the transaction and return to the pool.
- Bind dynamic values with `$1`, `$2`, ... and `params`; never interpolate user
  or secret data into SQL. The audit log records SQL text but intentionally not
  parameter values.
- Lock or match the exact current rows and include old-value/version predicates
  so concurrent drift turns the operation into zero changes. Make multi-row
  changes all-or-none against the expected candidate count; never issue an
  unbounded `UPDATE` or `DELETE`.
- Change every representation the verified deployed reader consumes. For Team
  config, preserve unrelated blob fields and bump the relevant normalized
  `updated_at` values plus `team_config.updated_at`; the Postgres config source
  includes that timestamp in its cache token.
- Return the changed identifiers and enough non-secret fields to verify the
  exact diff. Zero or unexpected rows is a failed precondition: stop and
  re-inspect instead of broadening the predicate or blindly retrying.

DDL, bulk data repair, or a change spanning independently owned subsystems is a
versioned database migration, not an interactive break-glass edit.

### Verify, resume, and retire

After the write, call `team_reload` when config was touched, then re-read the
canonical object with `team_config_get` and the relevant read API. Confirm the
full affected object—not just the edited field—plus daemon/plugin/provider
readiness. Run one disposable canary through the exact launch path and inspect
journaled decisions and terminal receipts. Only then restore triggers and call
`daemon_resume`.

Roll back immediately and stop if reload fails, the effective object differs
from the intended full object, runtime readiness degrades, the canary fails, or
concurrent drift is detected. Record the SQL shape, non-secret parameter
description, before/after hashes, returned row count, operator, time, canary,
rollback result, and linked product bug. Remove the workaround once the fixed
supported path is deployed and verified.

### Tables that need their own recovery runbook

Do not use this generic procedure to edit queue leases, workflow run journals
or execution fences, trigger-delivery or idempotency/deduplication ledgers,
publication receipts, authentication/membership, OAuth or secret material, or
provider-capacity/account state. These encode ownership, replay, authorization,
or external-effect claims. Repair them only under a table-specific incident
procedure that defines invariants, generation/fence ownership, replay safety,
and independent reconciliation evidence.

## Names, permissions, and protection

Phase definitions are globally keyed. Namespace every physical phase ID;
Portal rejects collisions across workflows. Protected `pr-reviewer`,
`pr-review`, their phases, and binding cannot be reused or modified through
normal authoring.

Tool schemas may be discoverable even when execution is forbidden, and some
clients filter them entirely. Visibility is not authority. Targeted team
writes, scripts, triggers, MCP definitions, secrets, provider pools, plugin
changes, and kind management are admin-gated. Skill MCP writes use a broader
write scope than the browser route even though skills are workspace-shared;
review ownership before mutating.

An omitted agent MCP-server list can fall through to all configured servers.
Portal Team serialization also drops explicit empty lists. Never use `[]` as
a security deny rule: give a non-empty least-privilege assignment in a
dedicated configuration and enforce authorization on each server.

## Providers and capacity

Resolution considers explicit call override, structured/legacy agent pins,
then defaults. Pinned pools and `require` account pins fail closed;
`prefer` may fall back. Models must be advertised, capacity visible to the
actor, and credentials healthy. Provider authentication is a preflight
dependency, not a rework verdict. A live coding run has reached final review
and then failed solely because the selected provider required authentication;
canary the complete provider chain.

## Durable command scripts

Team Scripts are the supported no-redeploy command-phase path. Read
`phase_context_schema` first. It defines the exact `ANIMUS_*` variables and
context file, including prior `{id, verdict, outputs}` records.

Scripts are stored in Postgres and atomically materialized under
`/data/animus-state/scripts` for `bash`, `python3`, or `tsx`. The interpreter
must be allowlisted. With `parse_json_output: true`, print exactly one
`phase_decision` JSON object; otherwise stdout cannot control routing.

## Ingress, history, and human gates

Queue dispatch is the normal automation boundary. GitHub deliveries are
durably claimed/deduplicated. Cron uses five-field UTC and bounded catch-up;
cron/test dispatch has a known crash window that can duplicate enqueue.
Validate cron and workflow reference before save because REST persistence does
not prove them.

An authorized application can launch idempotently through
`POST /api/application/v1/subjects/:kind/:id/runs`, supplying
`Idempotency-Key` and only an optional `workflow_ref`. The server derives the
actor and runtime config. Prefer this when the public MCP wrapper lacks the
required dispatch key.

The generic application/MCP engine accepts qualified subjects; the browser
launcher is narrower and task-shaped. Do not infer engine limitations from
that UI.

History and events are durable journal projections. Live details use SSE with
cursor/reset and polling fallback; a connection is bounded. Transcripts may be
local/S3 and unavailable, so completion checks must use state, decisions, and
receipts.

Human interactions re-check authorization before answer. Interaction replies
are currently non-reclaimable because the underlying CLI lacks a durable
reply replay key; an uncertain response needs operator reconciliation.

After an infrastructure failure, repair the provider/environment first, then
inspect the journal, queue lease, and execution fence. Resume only through the
supported workflow control when that generation still owns the fence;
otherwise reconcile terminal/external state and enqueue a new generation with
a new producer key. Never convert credential repair into semantic rework.

For an ambiguous publication result, inspect the runner's publication events
and receipt plus the reserved remote recovery ref/commit/tree. Let the current
fenced runner resume/reconcile when possible. Do not manually push or create a
second PR merely because the client timed out.

## What survives redeploy

- GitHub-source skills installed into the volume registry are durable; local
  path installs and project/user `skill create` are ephemeral in this image.
- Team Scripts are durable.
- Runtime plugin/scope mutations are not a permanent release mechanism; a
  locked activation can revert them. Commit permanent plugin changes to the
  release manifest/lock and roll them out.
- External MCP-backed `ext.*` subjects are read-only projections. A saved DB
  binding whose file materialization failed may remain stale until
  reconciliation/restart.
- The portal's own seeded Animus skill pack is pinned to a git revision. A
  source-repository edit is not live until that pin/release is advanced.
