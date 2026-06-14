---
name: animus-troubleshooting
description: Common Animus issues and fixes — daemon crashes, plugin preflight, workflow failures, queue problems, merge conflicts
user_invocable: true
auto_invoke: true
---

# Troubleshooting Animus

Start with:

```bash
animus doctor
animus daemon preflight
animus daemon observe --since 15m
animus status --failures 5
animus workflow config validate
```

`animus daemon observe` is the observability front-door: bare it prints a
data-source matrix plus a recent merged tail; `--since <dur>` merges daemon
events + logs chronologically; `--follow` tails the live stream;
`--source <logs|events|stream|workflow>` routes to one surface.

## Typed Exit Codes in Scripts

`subject`, `cost`, `events`, and `plugin` commands exit with typed codes
(previously all errors exited 1 — update old script matches): `2` invalid
input, `3` not found, `4` conflict, `5` unavailable (daemon down / missing
plugin / network), `1` internal. `animus daemon preflight` exits `2` when a
required role is missing and `1` on transient discovery failure.

## Daemon Won't Start

### Missing required plugins (preflight)

The daemon refuses to start when any required role is unsatisfied:
at least one provider, `subject_kind:task`, `subject_kind:requirement`,
`workflow_runner`, and `queue`. The error prints the exact
`animus plugin install ...` fix per role, plus one composed fix when several
roles are missing.

```bash
animus daemon preflight
animus plugin install-defaults        # installs the flavor's required set (all roles)
animus daemon start
```

For web UI support: `animus plugin install-defaults --include-transports`.
To auto-remediate on a dev machine: `animus daemon start --auto-install`.
Use `--skip-preflight` only when intentionally debugging without plugins —
the daemon will still fail at the first missing plugin RPC.

Preflight may also emit a non-fatal WARNING when the installed
`workflow_runner` plugin is older than the skill-payload floor (v0.4.2) —
such a runner silently ignores phase `skills:`. Fix with
`animus plugin update --name animus-workflow-runner-default`.

If preflight reports missing plugins that are installed, check per-project
plugin scoping — `flavor-only` or `allowlist` modes in
`.animus/plugin-scope.yaml` can exclude them from discovery, and a stale
`active_flavor:` selection falls back to the default flavor's plugin set:

```bash
animus plugin scope show
animus flavor current
```

A broken `flavors/default.toml` under `flavor-only` scope fails closed:
every role reports missing and the fix message says to repair or delete the
manifest, not to install plugins.

### Stale PID file

A leftover `daemon.pid` pointing at a dead process can block daemon start.
`animus doctor` detects it; `animus doctor --fix` removes the stale pid file
(and a dead control socket).

### Daemon already running

`animus daemon start` is idempotent — it reports the running pid instead of
failing. To pick up new plugin binaries or transport settings:

```bash
animus daemon restart        # graceful stop, then detached start
```

### Daemon crashes immediately

```bash
animus daemon observe --since 15m
animus daemon logs --limit 50
animus logs tail --level error --since 1h
```

Common causes:

- Missing, unsigned, or unhealthy plugins.
- Invalid workflow YAML.
- Disk full from worktrees, runs, or artifacts.
- Lock contention.

## Workflows Fail Immediately

### Claude Code environment variables

When the daemon is started from inside Claude Code, embedded-session env vars
may prevent nested `claude` runs on older builds.

```bash
env -u CLAUDECODE -u CLAUDE_CODE_SESSION_ACCESS_TOKEN animus daemon start
```

Current Animus strips the known guard vars at provider spawn points.

### Pool exhaustion or slow ramp-up

Dispatch is event-driven (sub-second pickup after subject/queue mutations),
but two knobs bound it: `pool_size` caps concurrent runners (upper-bounded by
`ANIMUS_WORKFLOW_CONCURRENCY_MAX`, default 10) and `max_tasks_per_tick`
(default 2) caps new dispatches per pass.

```bash
animus daemon config --pool-size 5 --max-tasks-per-tick 3
animus daemon health
```

Changes apply on the next tick without a restart.

### Provider plugin problems

```bash
animus plugin status                 # per-plugin pid, state, restarts, supervisor cooldown
animus plugin ping --name animus-provider-claude
animus daemon health                 # leads with healthy: true|false verdict
```

A plugin disabled by the restart supervisor (3 restarts in 60s → 5-minute
cooldown) reports `Unhealthy` with a `disabled by supervisor` detail and
flips the health verdict to `healthy: false`. `animus plugin status` also
carries aggregate provider health (`provider_plugins_healthy`). A missing
provider plugin is a hard error naming the install command — there is no
in-tree fallback.

## Workflows Fail During Implementation

### No changes were detected

The agent may have lacked enough instructions. Update the task subject with a
clearer title, labels, status, or plugin-specific body field if the backend
supports it:

```bash
animus subject get --kind task --id TASK-XXX
animus subject update --kind task --id TASK-XXX --labels backend,needs-detail
```

If the current subject backend does not expose body updates through the generic
CLI, update the source system directly or create a replacement task subject with
a clearer `--body`.

### Missing required output field

If a phase reports an output-contract error such as a missing commit message,
inspect the rendered prompt and phase output:

```bash
animus workflow get --id WF-XXX
animus workflow prompt render --workflow-id WF-XXX --phase implementation
animus output phase-outputs --workflow-id WF-XXX
```

This is usually a workflow prompt or phase contract issue.
`output phase-outputs` also renders a Skills section (requested vs applied vs
missing), so a typo'd skill name is visible instead of a silent no-op.

## Crashed or Stuck Phase Sessions

`animus doctor` detects both:

- Zombie sessions: phase session JSON stuck in `running` for over 6 hours
  after a daemon or provider crash. `animus doctor --fix` closes them out
  (status normalized to `failed`).
- Recent crashes: phase sessions `blocked` within the last 24 hours. After
  reviewing run output, recover with
  `animus workflow resume --id <WF-ID> --force`.

## Workflow Paused, Task "Stuck"

Lifecycle controls annotate the bound task so stalls are explainable:

- `workflow pause` sets the task's `blocked_reason` to
  `paused by workflow <id>`; a budget breach enriches it, e.g.
  `paused by workflow wf-... — budget exceeded ($7.50 > $5.00 max_cost_usd)`.
- An agent waiting on a human answer parks in the interactions inbox:
  `animus agent interactions list`, then `answer <ID> --text ...` /
  `--allow` / `--deny`. Suspend-mode answers auto-resume the workflow.
- `workflow resume` clears the pause annotation (never a genuine failure
  reason). `workflow cancel` syncs the task to `cancelled`.
- `animus subject status ... --status ready` prints an
  `unstuck: cleared ...` line naming any paused/blocked flags it cleared.

### Budget breaches

```bash
animus daemon health             # budget_enforcement: {enabled, last_sweep_at} + 24h breaches
animus status                    # Budget section: active breaches + worst offender
animus cost decisions --since 24h
```

Raise the `budget:` cap in workflow YAML (or change `on_exceed`), then
`animus workflow resume --id <WF-ID>`. Enforcement is per housekeeping sweep,
so an in-flight phase can overshoot by up to one sweep.
`ANIMUS_DAEMON_DISABLE_BUDGET_ENFORCEMENT=1` (daemon restart) disables the
sweep entirely.

## Queue Issues

### Stale assigned entries

Entries stuck as `assigned` with no running workflow can happen after a
daemon crash.

```bash
animus queue list
animus queue drop TASK-XXX            # positional ids; --all --yes for everything
```

### Queue not filling

1. Check the runtime is not paused: `animus daemon health` (`runtime: paused`
   means someone ran `animus daemon pause` — fix with `animus daemon resume`).
2. Check ready task subjects: `animus subject list --kind task --status ready`.
3. Enqueue one manually: `animus queue enqueue --task-id TASK-XXX` — explicit
   enqueues drain even when `auto_run_ready` is false (that flag gates only
   ready-task auto-dispatch).
4. Inspect recent workflows: `animus workflow list --limit 5`.
5. Follow scheduler activity: `animus daemon stream --cat schedule --pretty`.

## Subject State Issues

### Tasks stuck as blocked

```bash
animus subject list --kind task --status blocked
animus subject get --kind task --id TASK-XXX     # read blocked_reason first
animus subject status --kind task --id TASK-XXX --status ready
```

### Tasks stuck as in_progress

Mostly self-healing as of v0.5.13: an in-progress task with no live workflow
is reset to Ready by the reconciler, and manually-claimed in-progress tasks
are no longer re-blocked every tick. If one persists:

```bash
animus subject status --kind task --id TASK-XXX --status ready
```

Then verify queue and workflow state before re-enqueueing.

## Schedules or Triggers Not Firing

- Schedules fire on precise cron deadlines, with a 10-minute catch-up horizon
  for occurrences missed while the daemon was busy; longer gaps (daemon
  stopped, `active_hours` closed) are skipped, not replayed.
- Check `animus trigger list`, the daemon health plugin rows (a trigger
  plugin disabled by the supervisor stops dispatching), and
  `animus daemon stream --cat schedule --pretty`.
- `ANIMUS_DAEMON_DISABLE_TRIGGERS=1` in the daemon's environment disables all
  trigger plugins — check for a leftover kill-switch.
- Test a webhook trigger manually with `animus trigger fire`.

## Log and Output Surfaces

```bash
animus daemon observe                       # data-source matrix + merged tail
animus daemon observe --since 2h --workflow wf-abc123
animus daemon stream --cat phase --level warn --pretty
animus daemon events --limit 50             # one-shot by default; --follow streams
animus events tail --workflow-id wf-abc123  # lifecycle events; ends on terminal event
animus output monitor --run-id <id>         # live stdout/stderr for one run
animus output read --run-id <id>            # finished run (formerly `output run`)
animus output decisions --run-id <id>       # per-run LLM decision log
```

Note: `animus daemon events` stopped streaming by default in v0.5.13 —
scripted `daemon events --limit N` now exits; pass `--follow` to stream.

## PR Issues

### PRs not getting merged

Merge/PR behavior is defined per workflow in `post_success.merge` (executed
by the workflow runner plugin) — the old daemon-level `auto_merge`/`auto_pr`
knobs were removed in v0.5.13.

```bash
animus workflow list --limit 5
animus output phase-outputs --workflow-id WF-XXX
```

If merges depend on a review phase, inspect that phase output and the relevant
GitHub PR checks.

### Merge conflicts

```bash
gh pr list --state open --json number,mergeable
```

Rebase manually, run a rebase workflow if the project defines one, or create a
new task subject for conflict resolution.

## Process Leaks

`animus doctor` absorbed orphaned-CLI detection (the `animus runner` group
was removed in v0.5.13):

```bash
animus doctor                # detects orphaned tracked CLI processes
animus doctor --fix          # prunes dead tracker entries; live PIDs get a manual kill suggestion
animus doctor --fix --yes    # additionally removes orphan worktrees
```

## permission_denied Errors

When `principals.yaml` sets `policy.rbac: enforce`, daemon control calls are
authorized per principal and denied calls fail with `permission_denied`.

```bash
animus auth whoami
```

Shows the resolved principal. Use the global `--as <principal>` flag to run a
command as a different mapped principal.

## MCP OAuth Failures

If an OAuth-protected MCP server rejects requests or its token expired:

```bash
animus mcp auth-status
animus mcp auth <server>
```

`auth-status` shows token expiry per server; `auth` reruns the browser login.
As of v0.5.13, `invalid_grant` responses self-recover (the cached refresh
chain is evicted and the env seed retried in the same call) and corrupt
keychain credentials degrade to unauthenticated instead of bricking
`auth-status` / `auth-logout`.

## Disk Fills Up From Old Runs

`runs/<run-id>/` and `artifacts/<run-id>/` under `~/.animus/<repo-scope>/`
are never auto-deleted. Both verbs are dry-run by default; `--yes` deletes.
Only terminal runs are eligible.

```bash
animus workflow prune --older-than 30            # preview (days)
animus workflow prune --older-than 30 --yes
animus workflow prune --keep-last 50 --status failed --yes
animus workflow delete --run-id <RUN_ID> --yes
```

## Plugin Version Drift

```bash
animus plugin outdated                 # installed vs recommended pin vs latest (--exit-code for CI)
animus plugin update --all --restart-daemon
animus plugin lock verify              # sweeps global + project lockfiles
```

## State Location Reference

```text
.animus/
├── config.json            # self-update + CLI settings only (no daemon settings)
├── workflows.yaml
├── workflows/
├── skills/
├── plugin-scope.yaml      # scope mode + active_flavor
├── plugins/  plugins.yaml  plugins.lock   # project-scoped plugin triple
└── .gitignore             # written by init/project installs; covers plugins/
```

```text
~/.animus/<repo-scope>/
├── core-state.json
├── cost-state.v1.json  decisions.jsonl  budget-enforcement.v1.json
├── workflow.db
├── daemon/              # pm-config.json (daemon runtime settings), daemon.log
├── interactions/        # pending agent questions/approvals
├── logs/  runs/  artifacts/
├── state/
└── worktrees/
```

## Tasks Marked Done But PR Never Merged

The implementation phase may complete successfully while push/PR/merge phases
fail later.

Detection:

```bash
animus subject get --kind task --id TASK-XXX
animus workflow list --task-id TASK-XXX
gh pr list --state merged --search "TASK-XXX"
```

Fix in a reconciler prompt:

```text
Check for task subjects marked done that have no merged PR.
Set them back to ready and queue rebase-and-retry or a replacement task.
```

## Worktrees Have No Dependencies

Command phases can fail in worktrees because dependencies are not installed.
Add an install phase before build/test/lint commands:

```yaml
install-deps:
  mode: command
  command:
    program: pnpm
    args: ["install"]
    cwd_mode: task_root
  idempotency: idempotent
```

Read-only phases can skip worktree creation entirely with `worktree: skip`.

## Reviewer Merges PRs With Failing CI

Add explicit CI policy to the reviewer prompt:

```text
Before merging, run: gh pr checks <number>
If checks fail, decide whether the failure belongs to this PR.
If it does, queue rework. If it is pre-existing, merge only if policy allows and create a fix task.
If checks are pending, skip and let the next cycle pick it up.
```

## Daemon Doesn't Reload YAML Changes

A running daemon hot-reloads `.animus/workflows.yaml` and
`.animus/workflows/*.yaml` automatically (500 ms debounce); a malformed edit
keeps the prior config and broadcasts `config_reload_failed`. If the
filesystem watcher misses an edit:

```bash
animus workflow config validate
animus workflow config reload          # manual hot-reload trigger
```

Only daemon transport settings and `.animus/plugins.lock` changes require
`animus daemon restart`.

## Infinite Retry Loop

Detection: a subject cycles between `ready` and `blocked`, or the same
workflow repeatedly fails with the same phase verdict.

Fixes:

1. Inspect `animus workflow get --id WF-XXX`.
2. Inspect run output with `animus output read --run-id <run-id>`.
3. Check the worktree: `git -C <worktree_path> log --oneline -3`.
4. If the task is fundamentally stuck, cancel or mark it blocked and create a clearer replacement.
5. Add a consecutive-failure skip rule to the planner prompt.

## Parallel Agents Cause Merge Conflicts

Mitigations:

1. Use a rebase-and-retry workflow if the project defines one.
2. Reduce `pool_size` to 1 for conflict-heavy repos.
3. Split broad tasks into smaller subjects that touch fewer shared files.
