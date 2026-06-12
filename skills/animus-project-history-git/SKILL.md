---
name: animus-project-history-git
description: Manage Animus project registry entries, active project selection, execution history search and cleanup, Git repo registry, worktrees, sync, and confirmation records.
user_invocable: false
auto_invoke: true
---

# Project, History, and Git

Use these CLI trees when the work is about Animus's project registry,
execution history, or Git/worktree orchestration rather than workflow YAML.

## Project Registry

```bash
animus project list
animus project active
animus project get --id <project-id>
animus project create --name "Billing API" --path /path/to/repo --project-type web-app
animus project load --id <project-id>
animus project rename --id <project-id> --name "Billing Platform"
animus project archive --id <project-id>
animus project remove --id <project-id>
```

Use `project load` when the active project is wrong for daemon or MCP calls.
Use `--project-root <PATH>` on individual commands when you need an explicit
repo without changing global active state.

## Execution History

```bash
animus history recent --limit 20
animus history task --task-id TASK-001 --limit 20
animus history get --id <history-id>
animus history search --task-id TASK-001 --status failed --limit 25
animus history search --workflow-id wf-abc --started-after 2026-05-01T00:00:00Z
animus history cleanup --days 30
```

History replaces the retired `animus errors ...` surface for post-run
investigation. Combine it with `animus output ...` for run payloads and
artifacts.

## Git Repo Registry

```bash
animus git repo list
animus git repo get --repo /path/to/repo
animus git repo init --name billing-api --path /path/to/repo
animus git repo clone --url git@github.com:org/repo.git --name repo --path /path/to/repo
```

`--repo` accepts a registered repo name or path.

## Git Status and Branches

```bash
animus git branches --repo billing-api
animus git status --repo billing-api
animus git commit --repo billing-api --message "fix: handle upload limits"
animus git pull --repo billing-api --remote origin --branch main
animus git push --repo billing-api --remote origin --branch main
```

`animus git commit` commits staged and untracked changes according to Animus's
Git orchestration layer. Inspect status first when user changes may be present.

## Worktrees

```bash
animus git worktree create --repo billing-api --worktree-name TASK-001 --worktree-path ../billing-api-TASK-001 --branch codex/TASK-001 --create-branch
animus git worktree list --repo billing-api
animus git worktree get --repo billing-api --worktree-name TASK-001
animus git worktree pull --repo billing-api --worktree-name TASK-001
animus git worktree push --repo billing-api --worktree-name TASK-001
animus git worktree sync --repo billing-api --worktree-name TASK-001
animus git worktree sync-status --repo billing-api --worktree-name TASK-001
```

Prune completed managed worktrees:

```bash
animus git worktree prune --repo billing-api --dry-run
animus git worktree prune --repo billing-api --confirmation-id <id>
```

## Destructive Git Confirmation

Force pushes, dirty worktree removals, and pruning require confirmation ids.

```bash
animus git confirm request --operation-type remove_worktree --repo-name billing-api --context-json '{"worktree":"TASK-001"}'
animus git confirm respond --request-id <id> --approved true --comment "OK to remove completed task worktree"
animus git worktree remove --repo billing-api --worktree-name TASK-001 --confirmation-id <id>
animus git confirm outcome --request-id <id> --success true --message "removed worktree"
```

Use `--dry-run` before destructive operations whenever available.

## Safety Notes

- Do not remove or force-push worktrees with user changes unless the user explicitly approved that exact action.
- Prefer repo names only after confirming they resolve to the intended path.
- Keep history cleanup conservative; default is 30 days.
- Use `animus status`, `animus daemon health`, and `animus history recent` together for quick project triage.
