---
name: animus-troubleshooting
description: Common Animus issues and fixes — daemon crashes, workflow failures, queue problems, merge conflicts
user_invocable: true
auto_invoke: true
---

# Troubleshooting Animus

Start with:

```bash
animus doctor
```

`animus doctor --fix` applies safe remediations (stale daemon pid cleanup, zombie phase-session normalization, lock-file removal). Exit codes are typed: `2` invalid input, `3` not found, `5` daemon/backend unavailable — useful when scripting checks.

## Daemon Won't Start

### "daemon already running"
```bash
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

```bash
animus daemon logs --limit 50
animus daemon stream --level error --pretty
```

Common causes:
- **Disk full**: worktrees and old runs accumulate. Run `animus workflow prune --older-than 30 --yes` and `animus git worktree prune`.
- **Lock contention**: another process holds the daemon lock.
- **Config error**: invalid workflow YAML. Run `animus workflow config validate`.

## Workflows Fail Immediately (Cancelled in <5 seconds)

### CLAUDECODE Environment Variable
Current builds detect and unset `CLAUDECODE` before spawning a nested `claude` CLI, so this should not bite anymore. On older builds, when the daemon was started from inside Claude Code:
```bash
env -u CLAUDECODE animus daemon start --autonomous ...
```

### Pool Exhaustion
If `pool_size` is too small, cron workflows can't get a pool slot.

**Fix**: Increase pool_size. Rule of thumb: `pool_size >= concurrent_crons + 2`.
```bash
animus daemon config --pool-size 5    # hot-reloaded, no restart needed
```

### Provider Plugin Unhealthy or Missing
There is no agent-runner sidecar anymore (deleted v0.5.3) — provider plugins run the CLIs end to end. If phases fail to launch a provider:
```bash
animus plugin status                          # per-plugin state, restart counts, supervisor cooldowns
animus daemon health                          # per-plugin rows + provider_plugins_healthy
animus plugin ping --name animus-provider-claude
animus doctor --check orphan_cli_processes    # orphaned provider CLI processes
```
A plugin disabled by the restart supervisor shows a cooldown in `animus plugin status`; fix the underlying error, then `animus daemon restart`. A missing provider plugin hard-errors with the exact `animus plugin install ...` command.

## Workflows Fail at Implementation Phase

### "no changes were detected"
The agent didn't write any code. Check the task description — it might be too vague.

**Fix**: Give the task more specific requirements. `animus subject update` only changes status/priority/labels, so for a better body, create a replacement and cancel the original:
```bash
animus subject create --kind task --title "..." --body "Specific implementation details..."
animus subject status --kind task --id task:TASK-XXX --status cancelled
```

### "missing required field 'commit_message'"
The implementation phase contract requires a commit. The agent either didn't commit or the output contract wasn't satisfied.

**Fix**: This is usually a prompt quality issue. Ensure the agent prompt says to commit changes.

## Queue Issues

### Stale Assigned Entries
Entries stuck as `assigned` with no running workflow. Happens when daemon restarts mid-workflow.

```bash
animus queue list                   # identify stale entries
animus queue drop TASK-XXX          # remove one (positional ids, multiple allowed)
animus queue drop --all --yes       # clear everything
```

### Queue Not Filling
If queue stays empty:

1. Check if there are ready tasks: `animus subject list --kind task --status ready`
2. Enqueue a task manually: `animus queue enqueue --task-id TASK-XXX`
3. Check daemon health: `animus daemon health` (also shows `runtime: paused` if someone ran `animus daemon pause`)
4. Inspect recent workflows: `animus workflow list --limit 5`
5. Follow scheduler logs: `animus daemon stream --cat schedule --pretty`

Subject and queue mutations nudge the daemon immediately — if nothing dispatches within seconds, suspect pause state, pool exhaustion, or `auto_run_ready=false`.

## Task State Issues

### Tasks Stuck as "blocked"
```bash
animus subject list --kind task --status blocked
animus subject get --kind task --id task:TASK-XXX
animus subject status --kind task --id task:TASK-XXX --status ready    # force unblock
```

### Tasks Stuck as "in-progress"
No active workflow but task is still in-progress:
```bash
animus subject status --kind task --id task:TASK-XXX --status ready    # reset to ready
```

Then verify the queue and workflow state before re-enqueueing.

## Log Streaming Patterns

### Watch All New Structured Logs
```bash
animus daemon stream --pretty
```

### Focus On Scheduler Or Phase Problems
```bash
animus daemon stream --cat schedule --level warn --pretty
animus daemon stream --cat phase --level warn --pretty
```

### Focus On One Workflow Or Run
```bash
animus daemon stream --workflow wf-abc123 --tail 100 --pretty
animus daemon stream --run run-xyz789 --tail 100 --pretty
```

### Compare Live Logs With Run Output
Use:
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
animus output phase-outputs --workflow-id WF-XXX
```

### Merge Conflicts
When multiple task branches diverge from main:
```bash
gh pr list --state open --json number,mergeable
```

The pr-reviewer should skip conflicted PRs. Rebase manually or create a task to resolve.

## Process Leaks

### Orphaned Provider CLI Processes
```bash
animus doctor --check orphan_cli_processes          # detect
animus doctor --check orphan_cli_processes --fix    # prune dead tracker entries
```
Live tracked PIDs get a manual `kill` suggestion because the tracker is global across projects.

## State Location Reference

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
```

## Tasks Marked "Done" But PR Never Merged

The implementation phase may complete successfully, but push/PR phases fail. The task gets marked "done" by the workflow runner even though the code never reached main.

**Detection:** Task status is "done" but `gh pr list --state merged --search "TASK-XXX"` returns nothing.

**Fix in reconciler prompt:**
```
Check for tasks marked "done" that have NO merged PR.
These were marked done prematurely. Set them back to "ready"
and queue rebase-and-retry.
```

## Worktrees Have No node_modules

Command phases (`pnpm build`, `pnpm test`, `pnpm lint`) fail in worktrees because `node_modules` doesn't exist. The implementation agent works fine (uses Claude Code file tools, not the build system), but command phases need deps.

**Fix:** Add `install-deps` command phase before any command that needs `node_modules`:
```yaml
install-deps:
  mode: command
  command:
    program: pnpm
    args: ["install"]
    cwd_mode: task_root
```

## Reviewer Merges PRs With Failing CI

By default, the reviewer agent doesn't check CI status before merging.

**Fix:** Add to reviewer prompt:
```
Before merging, run: gh pr checks <number>
If checks fail, evaluate: is the failure from THIS PR or pre-existing?
- If from this PR: queue rework
- If pre-existing: merge anyway, create a fix task
- If pending: skip, next cycle picks it up
```

## Daemon Doesn't Reload YAML Changes

A running daemon hot-reloads `.animus/workflows.yaml` and `.animus/workflows/*.yaml` edits via a filesystem watcher; a malformed edit keeps the prior config active (look for `config_reload_failed` in `animus daemon events`). If a reload didn't land:

```bash
animus workflow config validate
animus workflow config reload     # manual hot-reload trigger
animus daemon restart --autonomous --auto-run-ready true --pool-size 3   # last resort
```

Daemon transport settings and `.animus/plugins.lock` changes always require a restart.

## Tasks Stuck in Infinite Retry Loop

If a task keeps blocking and the planner/reconciler keeps re-enqueuing it, it can waste agent slots forever.

**Detection:** Task version number is very high (>10) and status cycles between ready → blocked.

**Fixes:**
1. Check the MCP tool `animus.output.tail` with `task_id: "TASK-XXX"` (or `animus output monitor --run-id <id>` for a known run) for the actual error
2. Check the worktree: `git -C <worktree_path> log --oneline -3`
3. If the code is committed but push fails: manually push and create PR
4. If the task is fundamentally stuck: set it to `cancelled` and create a better-scoped replacement
5. Add `consecutive_dispatch_failures > 3` skip rule to the planner prompt

## Parallel Agents Cause Merge Conflicts

Multiple agents running in parallel will conflict on shared files (especially `pnpm-lock.yaml`).

**Mitigations:**
1. Use `rebase-and-retry` workflow — the reviewer queues it for conflicting PRs
2. Reduce `pool_size` to 1 if conflicts are too frequent
3. The rebase agent resolves conflicts intelligently (keeps both sides)

## Unreviewed Merges

If PRs land without code review, check your workflow's `post_success.merge` block — that is where merge policy lives now (the daemon-level `auto_merge`/`auto_pr` settings were removed in v0.5.x). Gate merging behind a review phase in the workflow definition instead of merging in `post_success` unconditionally.
