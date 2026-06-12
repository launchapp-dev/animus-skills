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
animus workflow config validate
```

`animus doctor --fix` applies safe remediations (stale daemon pid cleanup, zombie phase-session normalization, lock-file removal). Exit codes are typed: `2` invalid input, `3` not found, `5` daemon/backend unavailable — useful when scripting checks.

## Daemon Won't Start

### Missing providers or subject backends

Current Animus requires installed plugins. The daemon refuses to start when
required provider or subject roles are missing.

```bash
<<<<<<< HEAD
animus daemon health    # check if actually alive
animus daemon stop      # try graceful stop
animus doctor --fix     # cleans stale pid/lock files
# If it still exits unexpectedly, run in the foreground:
animus daemon run
```

`animus daemon restart` does stop+start in one step and accepts all start flags.

### Preflight Failure (missing plugins)
The daemon refuses to start when a required plugin role is missing (provider, `subject_kind:task`, `subject_kind:requirement`, `workflow_runner`, `queue`). The error prints the exact install command.
```bash
animus daemon preflight                  # standalone report
animus plugin install-defaults           # install the recommended set
animus daemon start --auto-install      # or install on the fly
```

### Daemon Crashes Immediately
Check the log:
=======
animus daemon preflight
animus plugin install-defaults --include-subjects
animus daemon start --autonomous
```

For web UI support:

```bash
animus plugin install-defaults --include-transports
```

For a dev machine where you want the daemon to remediate automatically:

```bash
animus daemon start --autonomous --auto-install
```

Use `--skip-preflight` only when intentionally debugging without plugins.

If preflight reports missing plugins that are installed, check per-project
plugin scoping — `flavor-only` or `allowlist` modes in
`.animus/plugin-scope.yaml` can exclude them from discovery:

```bash
animus plugin scope show
```

### Stale PID file

A leftover `daemon.pid` pointing at a dead process can block daemon start.
`animus doctor` detects it; `animus doctor --fix` removes the stale pid file
(and a dead control socket).

### Daemon already running

```bash
animus daemon health
animus daemon stop
animus daemon run
```

### Daemon crashes immediately
>>>>>>> origin/main

```bash
animus daemon logs --limit 50
animus logs tail --level error --since 1h
animus daemon stream --level error --pretty
```

Common causes:
<<<<<<< HEAD
- **Disk full**: worktrees and old runs accumulate. Run `animus workflow prune --older-than 30 --yes` and `animus git worktree prune`.
- **Lock contention**: another process holds the daemon lock.
- **Config error**: invalid workflow YAML. Run `animus workflow config validate`.
=======
>>>>>>> origin/main

- Missing, unsigned, or unhealthy plugins.
- Invalid workflow YAML.
- Disk full from worktrees or build artifacts.
- Lock contention.

<<<<<<< HEAD
### CLAUDECODE Environment Variable
Current builds detect and unset `CLAUDECODE` before spawning a nested `claude` CLI, so this should not bite anymore. On older builds, when the daemon was started from inside Claude Code:
```bash
env -u CLAUDECODE animus daemon start --autonomous ...
```

### Pool Exhaustion
If `pool_size` is too small, cron workflows can't get a pool slot.
=======
## Workflows Fail Immediately

### Claude Code environment variables

When the daemon is started from inside Claude Code, embedded-session env vars
may prevent nested `claude` runs on older builds.

```bash
env -u CLAUDECODE -u CLAUDE_CODE_SESSION_ACCESS_TOKEN animus daemon start --autonomous
```

Current Animus strips the known guard vars at provider spawn points.

### Pool exhaustion

If `pool_size` is too small, schedules or queued workflows can wait too long or
fail operational checks.
>>>>>>> origin/main

```bash
<<<<<<< HEAD
animus daemon config --pool-size 5    # hot-reloaded, no restart needed
```

### Provider Plugin Unhealthy or Missing
There is no agent-runner sidecar anymore (deleted v0.5.3) — provider plugins run the CLIs end to end. If phases fail to launch a provider:
```bash
animus plugin status                          # per-plugin state, restart counts, supervisor cooldowns
animus daemon health                          # per-plugin rows + provider_plugins_healthy
animus plugin ping --name animus-provider-claude
animus doctor --check orphan_cli_processes    # orphaned provider CLI processes
=======
animus daemon config --pool-size 5
animus daemon health
```

Rule of thumb: `pool_size >= concurrent_schedules + 2`.

### Runner connection failure

```bash
animus runner health
animus runner orphans detect
animus daemon stream --cat runner --level warn --pretty
animus daemon stop
animus daemon start --autonomous
>>>>>>> origin/main
```
A plugin disabled by the restart supervisor shows a cooldown in `animus plugin status`; fix the underlying error, then `animus daemon restart`. A missing provider plugin hard-errors with the exact `animus plugin install ...` command.

## Workflows Fail During Implementation

### No changes were detected

The agent may have lacked enough instructions. Update the task subject with a
clearer title, labels, status, or plugin-specific body field if the backend
supports it:

<<<<<<< HEAD
**Fix**: Give the task more specific requirements. `animus subject update` only changes status/priority/labels, so for a better body, create a replacement and cancel the original:
```bash
animus subject create --kind task --title "..." --body "Specific implementation details..."
animus subject status --kind task --id task:TASK-XXX --status cancelled
=======
```bash
animus subject get --kind task --id TASK-XXX
animus subject update --kind task --id TASK-XXX --labels backend,needs-detail
>>>>>>> origin/main
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

## Crashed or Stuck Phase Sessions

`animus doctor` detects both:

- Zombie sessions: phase session JSON stuck in `running` for over 6 hours
  after a daemon or provider crash. `animus doctor --fix` closes them out
  (status normalized to `failed`).
- Recent crashes: phase sessions `blocked` within the last 24 hours. After
  reviewing run output, recover with `animus workflow resume <id> --force`.

## Queue Issues

### Stale assigned entries

Entries stuck as `assigned` with no running workflow can happen after daemon
restart or runner crash.

```bash
<<<<<<< HEAD
animus queue list                   # identify stale entries
animus queue drop TASK-XXX          # remove one (positional ids, multiple allowed)
animus queue drop --all --yes       # clear everything
=======
animus queue list
animus queue drop --subject-id TASK-XXX
>>>>>>> origin/main
```

### Queue not filling

<<<<<<< HEAD
1. Check if there are ready tasks: `animus subject list --kind task --status ready`
2. Enqueue a task manually: `animus queue enqueue --task-id TASK-XXX`
3. Check daemon health: `animus daemon health` (also shows `runtime: paused` if someone ran `animus daemon pause`)
4. Inspect recent workflows: `animus workflow list --limit 5`
5. Follow scheduler logs: `animus daemon stream --cat schedule --pretty`

Subject and queue mutations nudge the daemon immediately — if nothing dispatches within seconds, suspect pause state, pool exhaustion, or `auto_run_ready=false`.

## Task State Issues
=======
1. Check ready task subjects: `animus subject list --kind task --status ready`.
2. Enqueue one manually: `animus queue enqueue --task-id TASK-XXX`.
3. Check daemon health: `animus daemon health`.
4. Inspect recent workflows: `animus workflow list --limit 5`.
5. Follow scheduler logs: `animus daemon stream --cat schedule --pretty`.

## Subject State Issues

### Tasks stuck as blocked
>>>>>>> origin/main

```bash
animus subject list --kind task --status blocked
<<<<<<< HEAD
animus subject get --kind task --id task:TASK-XXX
animus subject status --kind task --id task:TASK-XXX --status ready    # force unblock
=======
animus subject get --kind task --id TASK-XXX
animus subject status --kind task --id TASK-XXX --status ready
>>>>>>> origin/main
```

### Tasks stuck as in_progress

No active workflow but the task subject is still in progress:

```bash
<<<<<<< HEAD
animus subject status --kind task --id task:TASK-XXX --status ready    # reset to ready
=======
animus subject status --kind task --id TASK-XXX --status ready
>>>>>>> origin/main
```

Then verify queue and workflow state before re-enqueueing.

## Log Streaming Patterns

```bash
animus daemon stream --pretty
animus daemon stream --cat schedule --level warn --pretty
animus daemon stream --cat phase --level warn --pretty
animus daemon stream --workflow wf-abc123 --tail 100 --pretty
animus daemon stream --run run-xyz789 --tail 100 --pretty
```

Use:
<<<<<<< HEAD
- `animus daemon stream` when you need cross-cutting operational logs
- `animus output monitor --run-id <id>` when you need the live stdout/stderr stream for a single run
- `animus output read --run-id <id>` when the run already finished

## PR Issues

### PRs Not Getting Merged
Merge/PR policy lives in workflow YAML `post_success.merge` (executed by the workflow-runner plugin), not in daemon config — the old daemon `auto_merge`/`auto_pr` flags were removed in v0.5.x. Check the workflow definition and recent runs:
```bash
animus workflow list --limit 5
animus workflow config get
```

If merges depend on a review phase in your workflow, inspect that phase output with:

```bash
=======

- `animus daemon stream` for cross-cutting operational logs.
- `animus logs tail` for active log-storage backend entries.
- `animus output monitor --run-id <id>` for live stdout/stderr from one run.
- `animus output run --run-id <id>` for a finished run.

## PR Issues

### PRs not getting merged

```bash
animus workflow list --limit 5
animus daemon config
>>>>>>> origin/main
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

<<<<<<< HEAD
### Orphaned Provider CLI Processes
```bash
animus doctor --check orphan_cli_processes          # detect
animus doctor --check orphan_cli_processes --fix    # prune dead tracker entries
=======
```bash
animus runner orphans detect
animus runner orphans cleanup --run-id <run-id>
>>>>>>> origin/main
```
Live tracked PIDs get a manual `kill` suggestion because the tracker is global across projects.

`--run-id` is repeatable to clean up several runs in one call.

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

## State Location Reference

<<<<<<< HEAD
```
.animus/                          # project-local, authored
├── config.json                   # self-update + repo-local settings (NOT daemon settings)
├── workflows.yaml
├── workflows/
├── plugins/
└── plugins.lock
```

```
~/.animus/<repo-scope>/           # scoped runtime state, tool-managed
├── config/                       # compiled workflow/agent-runtime/state-machine config
├── daemon/                       # pm-config.json, daemon.log, daemon.lock
├── runs/
├── artifacts/
├── state/
├── logs/
└── interactions/
=======
```text
.animus/
├── config.json
├── workflows.yaml
├── workflows/
├── skills/
└── plugins/
```

```text
~/.animus/<repo-scope>/
├── core-state.json
├── resume-config.json
├── workflow.db
├── daemon/
│   └── pm-config.json
├── state/
├── runs/
└── worktrees/
>>>>>>> origin/main
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

## Reviewer Merges PRs With Failing CI

Add explicit CI policy to the reviewer prompt:

```text
Before merging, run: gh pr checks <number>
If checks fail, decide whether the failure belongs to this PR.
If it does, queue rework. If it is pre-existing, merge only if policy allows and create a fix task.
If checks are pending, skip and let the next cycle pick it up.
```

## Daemon Doesn't Reload YAML Changes

<<<<<<< HEAD
A running daemon hot-reloads `.animus/workflows.yaml` and `.animus/workflows/*.yaml` edits via a filesystem watcher; a malformed edit keeps the prior config active (look for `config_reload_failed` in `animus daemon events`). If a reload didn't land:
=======
Validate, then restart:
>>>>>>> origin/main

```bash
animus workflow config validate
animus workflow config reload     # manual hot-reload trigger
animus daemon restart --autonomous --auto-run-ready true --pool-size 3   # last resort
```

<<<<<<< HEAD
Daemon transport settings and `.animus/plugins.lock` changes always require a restart.

## Tasks Stuck in Infinite Retry Loop
=======
## Infinite Retry Loop
>>>>>>> origin/main

Detection: a subject cycles between `ready` and `blocked`, or the same
workflow repeatedly fails with the same phase verdict.

Fixes:

<<<<<<< HEAD
**Fixes:**
1. Check the MCP tool `animus.output.tail` with `task_id: "TASK-XXX"` (or `animus output monitor --run-id <id>` for a known run) for the actual error
2. Check the worktree: `git -C <worktree_path> log --oneline -3`
3. If the code is committed but push fails: manually push and create PR
4. If the task is fundamentally stuck: set it to `cancelled` and create a better-scoped replacement
5. Add `consecutive_dispatch_failures > 3` skip rule to the planner prompt
=======
1. Inspect `animus workflow get --id WF-XXX`.
2. Inspect run output with `animus output run --run-id <run-id>`.
3. Check the worktree: `git -C <worktree_path> log --oneline -3`.
4. If the task is fundamentally stuck, cancel or mark it blocked and create a clearer replacement.
5. Add a consecutive-failure skip rule to the planner prompt.
>>>>>>> origin/main

## Parallel Agents Cause Merge Conflicts

Mitigations:

1. Use a rebase-and-retry workflow if the project defines one.
2. Reduce `pool_size` to 1 for conflict-heavy repos.
3. Split broad tasks into smaller subjects that touch fewer shared files.

<<<<<<< HEAD
## Unreviewed Merges

If PRs land without code review, check your workflow's `post_success.merge` block — that is where merge policy lives now (the daemon-level `auto_merge`/`auto_pr` settings were removed in v0.5.x). Gate merging behind a review phase in the workflow definition instead of merging in `post_success` unconditionally.
=======
## auto_merge and auto_pr Should Usually Be False

If daemon-level `auto_merge` is `true`, it can bypass expected review policy.
For review-first workflows:

```bash
animus daemon config --auto-merge false --auto-pr false
```
>>>>>>> origin/main
