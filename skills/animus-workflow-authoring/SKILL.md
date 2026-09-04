---
name: animus-workflow-authoring
description: Design, write, review, or repair Animus workflows and workflow config for local CLI projects or the hosted Animus portal. Use for agents, phases, routing, retries, evaluations, execution environments, queue dispatch, publication, schedules, triggers, and workflow safety.
metadata:
  user_invocable: true
  auto_invoke: true
  animus_version: "0.7.0-rc.50"
---

# Animus Workflow Authoring

Author against the effective deployment, not the schema alone. Animus is a
kernel plus independently versioned plugins; a field can parse in the rc.50
CLI while an older workflow runner does not execute it. The hosted portal
currently pairs rc.50 with a newer runner than the CLI repository's default
install manifest.

## Start here

1. Identify the config authority and runtime versions.
   - Local/default YAML: `.animus/workflows.yaml` plus lexical
     `.animus/workflows/*.yaml|yml` overlays, served at runtime by a
     `config_source` plugin.
   - Portal: Postgres is canonical after first boot. Read `team_config_get`;
     do not treat image YAML as the live team.
   - Inspect kernel, workflow-runner, provider, environment, queue, and config
     source health before relying on optional behavior.
2. Model one bounded unit of work: one qualified subject, one queue lease or
   idempotent direct launch, one workflow state machine, and one independently
   verifiable terminal outcome.
3. Give every phase a single responsibility. Use command phases for
   deterministic checks/transforms, agent phases for judgment or generative
   work, and manual phases for real human authority.
4. Make permissions explicit. `writes_files: true` permits repository edits;
   `mutates_state: true` alone explicitly does not. Add
   `requires_commit: true` only when a commit is part of the phase contract.
5. Route structured decisions deliberately. Bound every cycle on the rework
   **target** with `phases.<target>.retry.max_attempts`; `1` permits one
   re-entry (at most two executions of that target). Do not rely on rich-step
   `max_rework_attempts` or transition `guard`, which currently parse but do
   not control lifecycle execution.
6. Separate workflow success from external success. A completed run does not
   mark its task Done, prove a push/PR/deploy, or make an ambiguous external
   side effect safe to retry.
7. Validate, inspect the compiled/effective config, reload, run a canary, and
   inspect decisions/events before enabling triggers.

## Minimal agent workflow

Use provider/model values advertised by the deployment; these are examples.

```yaml
agents:
  implementer:
    tool: codex
    model: gpt-5.6-sol

phases:
  sample-implementation:
    mode: agent
    agent: implementer
    directive: Implement the requested change and report the verification run.
    capabilities:
      writes_files: true
      requires_commit: true

workflows:
  - id: sample-delivery
    name: Sample delivery
    phases: [sample-implementation]
```

Phase IDs share a global definition map. Namespace physical IDs by workflow
or domain (`billing-implement`, `billing-test`) instead of reusing generic
names across independently managed portal workflows. Exact legacy names such
as `implementation` receive compatibility defaults; never depend on those
defaults for authorization.

## Choose the relevant reference

- Read [references/runtime-and-lifecycle.md](references/runtime-and-lifecycle.md)
  for the kernel/plugin architecture, dispatch lifecycle, fences, state,
  version-dependent behavior, and failure taxonomy.
- Read [references/agents-and-phases.md](references/agents-and-phases.md) for
  agent runtime selection, phase modes, capabilities, decisions, skills,
  permission modes, retries, and enforced evaluations.
- Read [references/top-level-and-routing.md](references/top-level-and-routing.md)
  for overlays, workflows, subworkflows, `skip_if`, routing, budgets,
  environments/workspaces, and the explicit publication contract.
- Read
  [references/automation-and-integrations.md](references/automation-and-integrations.md)
  for queue idempotency, actors, schedules, triggers, MCP, tool policy, and
  external-effect design.
- Read [references/optimal-patterns.md](references/optimal-patterns.md) for
  recommended coding, event, approval, quality-gate, and reconciliation
  patterns.
- When operating the hosted service, also read
  [animus-portal-operations](../animus-portal-operations/SKILL.md); its Team
  authoring surfaces do not round-trip every kernel field.

## Validation and rollout

For a local CLI source:

```bash
animus workflow config validate
animus workflow config compile
animus workflow definitions list
animus workflow phases list
animus plugin status
animus daemon preflight
```

Use `animus workflow prompt render` where the installed CLI exposes it. A
successful parse proves shape, not runner enforcement. Treat warnings as
evidence to investigate, not as a definitive capability report: the rc.50 CLI
validator and a newer portal runner can disagree.

For the portal, re-read `team_config_get` after publication/reload, verify
provider capacity and daemon readiness, enqueue one disposable canary, and
check its journaled phase decisions plus terminal publication/effect receipt.
Do not enable an autonomous trigger until the canary proves the exact deployed
path.
