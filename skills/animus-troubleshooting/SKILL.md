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

## Daemon Won't Start

### "daemon already running"
```bash
animus daemon health    # check if actually alive
animus daemon stop      # try graceful stop
# If it still exits unexpectedly, run in the foreground:
animus daemon run
```

### Daemon Crashes Immediately
Check the log:

```bash
animus daemon logs --limit 50
animus daemon stream --level error --pretty
```

Common causes:
- **Disk full**: worktrees and build artifacts accumulate. Run `cargo clean` or add a cleanup phase.
- **Lock contention**: another process holds the daemon lock.
- **Config error**: invalid workflow YAML. Run `animus workflow config validate`.

## Workflows Fail Immediately (Cancelled in <5 seconds)

### CLAUDECODE Environment Variable
When the daemon is started from inside Claude Code, it inherits session env vars that prevent `claude` CLI from launching.

**Fix**: Build from latest (commit 47d0d192+) which strips these at spawn points. Or:
```bash
env -u CLAUDECODE -u CLAUDE_CODE_SESSION_ACCESS_TOKEN animus daemon start --autonomous ...
```

### Pool Exhaustion
If `pool_size` is too small, cron workflows get cancelled when they can't get a pool slot.

**Fix**: Increase pool_size. Rule of thumb: `pool_size >= concurrent_crons + 2`.
```bash
animus daemon start --autonomous --pool-size 5 ...
```

### "failed to connect runner"
The agent-runner process isn't responding. Usually means it crashed.
```bash
animus runner health
animus runner orphans detect
animus daemon stream --cat llm --level warn --pretty
animus daemon stop
animus daemon start --autonomous
```

## Workflows Fail at Implementation Phase

### "no changes were detected"
The agent didn't write any code. Check the task description — it might be too vague.

**Fix**: Update the task with more specific requirements:
```bash
animus task update --id TASK-XXX --description "Specific implementation details..."
```

### "missing required field 'commit_message'"
The implementation phase contract requires a commit. The agent either didn't commit or the output contract wasn't satisfied.

**Fix**: This is usually a prompt quality issue. Ensure the agent prompt says to commit changes.

## Queue Issues

### Stale Assigned Entries
Entries stuck as `assigned` with no running workflow. Happens when daemon restarts mid-workflow.

```bash
animus queue list              # identify stale entries
animus queue drop --subject-id TASK-XXX    # remove them
```

### Queue Not Filling
If queue stays empty:

1. Check if there are ready tasks: `animus task list --status ready`
2. Enqueue a task manually: `animus queue enqueue --task-id TASK-XXX`
3. Check daemon health: `animus daemon health`
4. Inspect recent workflows: `animus workflow list --limit 5`
5. Follow scheduler logs: `animus daemon stream --cat schedule --pretty`

## Task State Issues

### Tasks Stuck as "blocked"
```bash
animus task list --status blocked
animus task get --id TASK-XXX
animus task status --id TASK-XXX --status ready    # force unblock
```

### Tasks Stuck as "in-progress"
No active workflow but task is still in-progress:
```bash
animus task status --id TASK-XXX --status ready    # reset to ready
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
- `animus output run --run-id <id>` when the run already finished

## PR Issues

### PRs Not Getting Merged
Check recent workflow state and daemon config:
```bash
animus workflow list --limit 5
animus daemon config
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

### Too Many agent-runner Processes
```bash
animus runner orphans detect
animus runner restart-stats
```

## State Location Reference

```
.ao/
├── config.json
├── pm-config.json
├── workflows.yaml
└── workflows/
```

```
~/.ao/<repo-scope>/
├── core-state.json
├── resume-config.json
├── tasks/
├── requirements/
├── runs/
├── artifacts/
└── worktrees/
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

Changes to `.ao/workflows.yaml` or `.ao/workflows/*.yaml` are not picked up by an already-running daemon.

**Fix:** Validate, then restart:
```bash
animus workflow config validate
animus daemon stop
animus daemon start --autonomous --auto-run-ready true --pool-size 3
```

## Tasks Stuck in Infinite Retry Loop

If a task keeps blocking and the planner/reconciler keeps re-enqueuing it, it can waste agent slots forever.

**Detection:** Task version number is very high (>10) and status cycles between ready → blocked.

**Fixes:**
1. Check `animus.output.tail --task-id TASK-XXX` for the actual error
2. Check the worktree: `git -C <worktree_path> log --oneline -3`
3. If the code is committed but push fails: manually push and create PR
4. If the task is fundamentally stuck: cancel it and create a better-scoped replacement
5. Add `consecutive_dispatch_failures > 3` skip rule to the planner prompt

## Parallel Agents Cause Merge Conflicts

Multiple agents running in parallel will conflict on shared files (especially `pnpm-lock.yaml`).

**Mitigations:**
1. Use `rebase-and-retry` workflow — the reviewer queues it for conflicting PRs
2. Reduce `pool_size` to 1 if conflicts are too frequent
3. The rebase agent resolves conflicts intelligently (keeps both sides)

## auto_merge and auto_pr Should Be False

If the daemon's `auto_merge` is `true`, it merges PRs without code review. Set both to `false` and let the pr-review phase handle merging:

```bash
animus daemon config --auto-merge false --auto-pr false
```
