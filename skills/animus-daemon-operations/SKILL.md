---
name: animus-daemon-operations
description: Start, stop, restart, pause, resume, and size the Animus daemon, including preflight and immediate health checks. Use when changing daemon lifecycle or scheduler capacity; use animus-observability for evidence gathering and animus-troubleshooting when the cause spans providers, queues, workflows, or state.
license: MIT
metadata:
  animus-version: "0.7.0-rc.50"
---

# Animus Daemon Operations

Operate the daemon as the scheduler and plugin supervisor for one resolved
project scope. Do not confuse a running process with a ready execution stack.

Read [the daemon operations runbook](references/daemon-runbook.md) for exact
commands, pool sizing, streams, persistent configuration, kill switches, and
known failure modes. Use only the relevant section.

## Normal lifecycle

1. Resolve the intended project root and inspect existing daemon status before
   starting another process.
2. Run preflight and treat missing required plugins, provider authentication,
   invalid workflow config, or an unavailable state directory as readiness
   failures.
3. Start in detached mode for normal use; use foreground mode only for active
   development or diagnosis.
4. Verify daemon health, required plugin roles, provider readiness, config
   generation, and queue lease activity appropriate to the project.
5. Use pause/resume to control new leasing. Pausing does not cancel in-flight
   work; wait for or explicitly reconcile those runs before maintenance.
6. Restart only when configuration or process state requires it. A restart is
   not a generic repair for a bad provider, workflow, queue entry, or run fence.
7. Stop the daemon through the supported command and verify that the matching
   project-scoped process exited before removing stale state.

## Boundaries

- `/healthz` or a live PID proves liveness only. Use the deployment's readiness
  and plugin/provider checks before dispatch.
- Preserve unrelated daemons belonging to other repo scopes.
- Never delete a PID/lock merely because it is old-looking; verify process
  identity and project scope first.
- Size concurrency against provider capacity, environment-node supply, and
  downstream rate limits—not CPU count alone.
- Prefer structured observe/events/log surfaces over repeated ad-hoc polling.

Use `animus-observability` when the task is to explain current state without
changing lifecycle. Use `animus-troubleshooting` after a concrete failure needs
cross-subsystem root-cause analysis.
