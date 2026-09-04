---
name: animus-troubleshooting
description: Diagnose and repair Animus failures across daemon startup, providers, plugins, workflows, queues, subjects, schedules, permissions, worktrees, environments, and publication. Use when a concrete symptom or failed operation needs root-cause analysis; use the narrower operations skill for routine, healthy-system commands.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---

# Animus Troubleshooting

Diagnose from durable evidence and identify the failed layer before changing
state. A request to diagnose does not authorize a repair, retry, deletion,
replay, or external side effect.

Use [the troubleshooting runbook](references/troubleshooting-runbook.md) by
symptom; read only the matching section:

- daemon startup, stale PID, or crashes: **Daemon Won't Start**;
- immediate provider/plugin/config failures: **Workflows Fail Immediately**;
- bad agent output or phase behavior: **Workflows Fail During Implementation**;
- crashed sessions, paused runs, or budget stops: **Crashed or Stuck Phase
  Sessions** and **Workflow Paused, Task "Stuck"**;
- queue, subject, schedule, or trigger symptoms: their matching sections;
- PR/merge/publication ambiguity: **PR Issues** and **Tasks Marked Done But PR
  Never Merged**;
- permissions, MCP OAuth, disk, plugin drift, worktrees, environments, config
  reload, retry loops, or parallel conflicts: the named later sections.

## Evidence ladder

1. Capture the exact command/tool error and structured remediation payload.
2. Resolve the project/repo scope and current kernel, plugin, runner, and
   environment versions.
3. Inspect daemon readiness and required plugin/provider health.
4. Correlate subject ID, queue entry, run ID, phase attempt, decision, fence,
   artifact, and external receipt as applicable.
5. Classify the failure as configuration, readiness/infrastructure, semantic
   agent output, workflow routing, ownership/fencing, or external-effect
   ambiguity.
6. State the cause and the smallest safe repair. Implement it only when the
   user requested a fix and the action stays within their authority.
7. Verify the repaired invariant with the narrowest meaningful canary; do not
   treat a restarted process or a zero exit code as sufficient proof.

## Stop conditions

- Do not blindly retry provider authentication, uncertain interaction replies,
  publication, webhook replay, or another external side effect.
- Do not edit queue leases, workflow journals/fences, idempotency ledgers,
  receipts, authentication, or secret state without a subsystem-specific
  recovery procedure.
- Do not broaden cleanup or kill processes until their exact scope and owner
  are established.
- Preserve failed-run evidence until the incident is understood.

Route routine lifecycle commands to `animus-daemon-operations`, read-only
evidence gathering to `animus-observability`, provider/model readiness to
`animus-model-operations`, and Portal-only recovery to
`animus-portal-operations`.
