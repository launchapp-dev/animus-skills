---
name: animus-project-history-git
description: Inspect Animus execution history, Git repo and worktree state, and approval records — history search and cleanup, worktree listing and pruning, repo-scope resolution, and the approval gate for destructive operations. Use for post-run forensics, worktree housekeeping, or approval round-trips.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.27"   # animus CLI surface this skill targets
---

# History, Git Inspection, and Approvals

Surface changes to know before reaching for older commands: the
`animus project` command group (list/active/get/create/set-active/rename/
archive/remove) was **removed in v0.5.14** — there is no project registry;
the daemon routes purely via git root + repo-scope. `animus git` was
**trimmed to inspection-only**: mutation verbs (`repo get/init/clone`,
`branches`, `status`, `commit`, `push`, `pull`, and `worktree
create/get/remove/pull/push/sync/sync-status`) are gone. Agent-driven
merge/PR/commit is expressed as `command:` phases running `git`/`gh` in
workflow YAML (the `post_success.merge` block was removed and now hard-fails
to parse).

## Repo Scope (replaces the project registry)

Project root resolution per command: `--project-root <PATH>` → git common
root for the cwd or linked worktree → cwd. Scoped runtime state lives at
`~/.animus/<repo-scope>/` (scope is `<repo-name>-<12-hex>`). To target a
different repo, pass `--project-root` on the individual command — there is
no global "active project" to switch.

## Execution History

```bash
animus history recent --limit 20
animus history task --task-id TASK-001 --limit 20
animus history get --id <history-id>
animus history search --task-id TASK-001 --status failed --limit 25
animus history search --workflow-id wf-abc --since 7d
animus history search --started-after 2026-05-01T00:00:00Z --started-before 2026-06-01T00:00:00Z
animus history cleanup --days 30
```

- `--since` takes a relative window (`7d`, `12h`, `30m`; bare numbers are
  seconds) and conflicts with `--started-after`. `search` also takes
  `--offset` for paging.
- History records carry a `run_id` when resolvable — pivot into the run's
  raw output with `animus output read --run-id <id>` (forensic chain:
  history → run events → artifacts via `animus output artifacts`).
- `history cleanup` removes history records only. Reclaiming run disk
  (runs/, artifacts/, checkpoints) is `animus workflow prune` /
  `animus workflow delete` — dry-run by default, `--yes` to delete.

History replaced the retired `animus errors` surface for post-run
investigation.

## Git Inspection

```bash
animus git repo list                          # registered repositories
animus git worktree list --repo <name|path>   # repository worktrees
```

Prune managed task worktrees for done/cancelled tasks (keeps its approval
gate — see below):

```bash
animus git worktree prune --repo <name|path> --dry-run
animus git worktree prune --repo <name|path> --confirmation-id <id>
animus git worktree prune --repo <name|path> --confirmation-id <id> \
  --delete-remote-branch --remote origin
```

`--repo` accepts a registered repo name or a path. For everything else
(status, branches, commits, pushes), use plain `git`; Animus no longer
wraps those operations.

v0.7 note: worktree pruning covers **locally managed** task worktrees.
Runs pinned to an execution environment materialize their workspaces inside
ephemeral remote nodes instead — those are torn down by the environment
broker (lease records under
`~/.animus/<repo-scope>/workflow-environments/`), not by `worktree prune`.

`animus doctor --fix --yes` additionally removes orphan worktrees
(`git worktree remove --force`) as part of its remediations.

## Approval Records

`animus approval` (formerly `git confirm`; the hidden alias was removed in
v0.5.14) manages the records gating destructive operations.
`git worktree prune` refuses to run until an approved `prune_worktrees`
record exists and its id is passed via `--confirmation-id`:

```bash
animus approval request --operation-type prune_worktrees --repo-name billing-api
animus approval respond --request-id <id> --approve --comment "OK to prune"
animus git worktree prune --repo billing-api --confirmation-id <id>
animus approval outcome --request-id <id> --success --message "pruned"
```

- `respond` requires exactly one of `--approve` / `--reject` (omitting both
  errors "provide exactly one of --approve or --reject"); pass `--reject` to
  decline. For `outcome`, `--message` is **required** and `--success` is a
  flag: omit it to record failure.
  `request` takes optional `--context-json`; `respond` takes optional
  `--user-id`; `outcome` takes optional `--metadata-json`.
- The record schema still accepts the legacy operation types
  (`force_push`, `remove_worktree`, `remove_repo`, `hard_reset`,
  `clean_untracked`) for plugins that perform their own git mutations.
- This store is distinct from the agent human-in-the-loop inbox: approvals
  agents raise mid-run via `animus.agent.request_approval` are answered
  with `animus agent interactions answer <ID> --allow|--deny`, not here.

## Safety Notes

- Always `--dry-run` a worktree prune first; never prune worktrees with
  user changes unless the user approved that exact action.
- Keep `history cleanup` conservative; default retention is 30 days.
- Triage combo: `animus status`, `animus daemon health`,
  `animus history recent`.
- All verbs answer `--json` with the `animus.cli.v1` envelope; exit codes
  follow the typed scheme (2 invalid input, 3 not found, 5 unavailable) —
  see `docs/reference/cli/exit-codes.md` in the animus-cli repo.
