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

## Daemon Won't Start

### Missing providers or subject backends

Current Animus requires installed plugins. The daemon refuses to start when
required provider or subject roles are missing.

```bash
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

### Daemon already running

```bash
animus daemon health
animus daemon stop
animus daemon run
```

### Daemon crashes immediately

```bash
animus daemon logs --limit 50
animus logs tail --level error --since 1h
animus daemon stream --level error --pretty
```

Common causes:

- Missing, unsigned, or unhealthy plugins.
- Invalid workflow YAML.
- Disk full from worktrees or build artifacts.
- Lock contention.

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

```bash
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
```

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

## Queue Issues

### Stale assigned entries

Entries stuck as `assigned` with no running workflow can happen after daemon
restart or runner crash.

```bash
animus queue list
animus queue drop --subject-id TASK-XXX
```

### Queue not filling

1. Check ready task subjects: `animus subject list --kind task --status ready`.
2. Enqueue one manually: `animus queue enqueue --task-id TASK-XXX`.
3. Check daemon health: `animus daemon health`.
4. Inspect recent workflows: `animus workflow list --limit 5`.
5. Follow scheduler logs: `animus daemon stream --cat schedule --pretty`.

## Subject State Issues

### Tasks stuck as blocked

```bash
animus subject list --kind task --status blocked
animus subject get --kind task --id TASK-XXX
animus subject status --kind task --id TASK-XXX --status ready
```

### Tasks stuck as in_progress

No active workflow but the task subject is still in progress:

```bash
animus subject status --kind task --id TASK-XXX --status ready
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

- `animus daemon stream` for cross-cutting operational logs.
- `animus logs tail` for active log-storage backend entries.
- `animus output monitor --run-id <id>` for live stdout/stderr from one run.
- `animus output run --run-id <id>` for a finished run.

## PR Issues

### PRs not getting merged

```bash
animus workflow list --limit 5
animus daemon config
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

```bash
animus runner orphans detect
animus runner restart-stats
animus runner orphans cleanup --run-id <run-id>
```

## State Location Reference

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

Validate, then restart:

```bash
animus workflow config validate
animus daemon stop
animus daemon start --autonomous --auto-run-ready true --pool-size 3
```

## Infinite Retry Loop

Detection: a subject cycles between `ready` and `blocked`, or the same
workflow repeatedly fails with the same phase verdict.

Fixes:

1. Inspect `animus workflow get --id WF-XXX`.
2. Inspect run output with `animus output run --run-id <run-id>`.
3. Check the worktree: `git -C <worktree_path> log --oneline -3`.
4. If the task is fundamentally stuck, cancel or mark it blocked and create a clearer replacement.
5. Add a consecutive-failure skip rule to the planner prompt.

## Parallel Agents Cause Merge Conflicts

Mitigations:

1. Use a rebase-and-retry workflow if the project defines one.
2. Reduce `pool_size` to 1 for conflict-heavy repos.
3. Split broad tasks into smaller subjects that touch fewer shared files.

## auto_merge and auto_pr Should Usually Be False

If daemon-level `auto_merge` is `true`, it can bypass expected review policy.
For review-first workflows:

```bash
animus daemon config --auto-merge false --auto-pr false
```
