---
name: animus-workflow-patterns
description: Battle-tested pipeline patterns — QA gates, command phases, conflict resolution, CI checks, stale PR handling
user_invocable: false
auto_invoke: true
---

# Workflow Patterns — Production-Ready Pipelines

Battle-tested patterns from building a full SaaS monorepo with Animus. These patterns address real issues discovered over 150+ autonomous PRs.

## The Scaffold Pipeline (recommended for all new projects)

```yaml
phases:
  implementation:
    mode: agent
    agent: implementer
    directive: "Implement the task requirements. Write code, commit."
    capabilities:
      mutates_state: true

  install-deps:
    mode: command
    directive: "Install dependencies in the worktree"
    command:
      program: pnpm
      args: ["install"]
      cwd_mode: task_root
      timeout_secs: 120

  build-check:
    mode: command
    directive: "Verify the project builds"
    command:
      program: pnpm
      args: ["build"]
      cwd_mode: task_root
      timeout_secs: 300

  lint-check:
    mode: command
    directive: "Run lint"
    command:
      program: pnpm
      args: ["lint"]
      cwd_mode: task_root
      timeout_secs: 120

  push-branch:
    mode: command
    directive: "Push the branch to origin"
    command:
      program: git
      args: ["push", "-u", "origin", "HEAD"]
      cwd_mode: task_root
      timeout_secs: 60

  create-pr:
    mode: command
    directive: "Create a PR"
    command:
      program: gh
      args: ["pr", "create", "--fill", "--base", "main"]
      cwd_mode: task_root
      timeout_secs: 60

  wait-for-ci:
    mode: command
    directive: "Wait for CI checks"
    command:
      program: gh
      args: ["pr", "checks", "--watch", "--fail-fast"]
      cwd_mode: task_root
      timeout_secs: 600

  pr-review:
    mode: agent
    agent: reviewer
    directive: "Review the PR and merge if approved."

workflows:
  - id: scaffold
    phases:
      - implementation
      - install-deps
      - build-check
      - lint-check
      - push-branch
      - create-pr
      - wait-for-ci
      - pr-review:
          on_verdict:
            rework:
              target: implementation
```

## Critical: cwd_mode for Command Phases

**This is the #1 gotcha.** While `cwd_mode` defaults to `task_root`, it's best practice to always set it explicitly for clarity. If you accidentally override it to `project_root`, the command runs in the main repo — NOT in the task's worktree.

```yaml
command:
  cwd_mode: task_root    # default, but be explicit
```

Without this, `git push` pushes from `main` (nothing to push), `gh pr create` sees no branch, and `pnpm build` may use stale code.

### cwd_mode options:
- `task_root` — the task's git worktree (default — what you almost always want)
- `project_root` — main repo directory
- `path` — custom relative path (requires `cwd_path`)

## Why Command Phases Over Agent Phases for Git/PR

Agent phases (mode: agent) spawn a full Claude/Codex session. For deterministic operations like `git push` and `gh pr create`, this is:
- Slow (spawns entire LLM session for a shell command)
- Unreliable (the agent might do unexpected things)
- Expensive (uses model tokens for no reason)

**Rule: Use agent phases for decisions, command phases for execution.**

| Operation | Phase Mode | Why |
|-----------|-----------|-----|
| Write code | agent | Needs intelligence |
| Run tests | command | Pass/fail, no interpretation |
| Push branch | command | Deterministic |
| Create PR | command | Deterministic |
| Wait for CI | command | Just polling |
| Review PR | agent | Needs judgment |
| Resolve conflicts | agent | Needs intelligence |

## install-deps Phase — Why It's Required

Worktrees don't have `node_modules`. The implementation agent uses Claude Code's file tools (Read/Write/Edit) which don't need deps installed. But command phases that run `pnpm build`, `pnpm test`, or `pnpm lint` will fail with "command not found" errors.

**Always add `install-deps` before any command phase that needs node_modules.**

## QA Gates Without Rework Loops

Don't add `on_verdict: rework` to CI/CD gates — it creates infinite loops:

```yaml
# BAD — infinite loop if build always fails
- build-check:
    on_verdict:
      rework:
        target: implementation

# GOOD — fail cleanly, let PO/auditor create a fix task
- build-check
- lint-check
- wait-for-ci
```

Only `pr-review` should have a rework loop (reviewer feedback is actionable).

## Conflict Resolution Pipeline

When parallel agents merge PRs, later PRs conflict. Add a rebase workflow:

```yaml
phases:
  rebase-on-main:
    mode: agent
    agent: implementer
    directive: |
      Rebase this branch onto latest main. Resolve conflicts:
      - For lockfiles: accept theirs, run pnpm install
      - For code: keep both sides, combine logic
      - Run pnpm build to verify result
    capabilities:
      mutates_state: true

  force-push:
    mode: command
    command:
      program: git
      args: ["push", "--force-with-lease", "origin", "HEAD"]
      cwd_mode: task_root

workflows:
  - id: rebase-and-retry
    phases:
      - rebase-on-main
      - force-push
      - pr-review

  - id: rework
    phases:
      - address-review
      - force-push
      - pr-review
```

The reviewer agent queues `rebase-and-retry` when it sees a conflicting PR, and `rework` when it requests changes.

## Reviewer CI Check Pattern

The reviewer MUST check CI before merging:

```yaml
pr-review:
  mode: agent
  agent: reviewer
  directive: |
    Before merging, run: gh pr checks <number>
    - If checks fail and caused by THIS PR: queue rework
    - If checks fail but pre-existing: merge anyway, create fix task
    - If checks pending: skip, next cycle will pick it up
    - If all pass: review diff and merge if approved
```

## Stale PR Detection

PRs can become stale when tasks are marked done prematurely:

```yaml
pr-review-sweep:
  directive: |
    For each open PR:
    1. Get task ID from branch name
    2. If task is "done" but NO merged PR exists:
       The task was marked done prematurely.
       Queue rebase-and-retry (don't close the PR!)
    3. If task is "done" AND a merged PR exists:
       Close with comment linking the merged PR.
```

## Conductor / Sweep Pattern (Single-Daemon SDLC)

For projects that own an ecosystem of repos — fleets, product owners, template managers — drive the whole thing from **one daemon, one conductor agent, periodic sweeps**. No per-repo sub-daemons.

The conductor is an Opus-grade agent on a cron. Each sweep it: reads state, picks the highest-leverage closable gap, queues specialist tasks, and exits. Specialists handle worktrees, commits, PRs themselves.

```yaml
agents:
  conductor:
    model: claude-opus-4-7
    tool: claude
    mcp_servers: ["animus", "memory", "github", "sequential-thinking"]
    system_prompt: |
      You are the conductor. Read AGENT_PRINCIPLES.md first.
      Each sweep:
        1. Check kill criteria — clear before anything else
        2. Find the biggest *closable* gap (not the lowest score, the most gettable)
        3. Queue ONE focused dispatch
        4. Self-check: did the last 3 sweeps move the score? If not, escalate
      Never queue same repo+task title 3+ times in a week. If stuck, write a blocker report.

  implementer: { model: claude-sonnet-4-6, tool: claude }
  tester:      { model: claude-sonnet-4-6, tool: claude }
  scanner:     { model: claude-haiku-4-5,  tool: claude }

phases:
  conductor-sweep:
    mode: agent
    agent: conductor
    directive: "Run the sweep. Queue at most one dispatch."

workflows:
  - id: conductor-loop
    phases: [conductor-sweep]

schedules:
  - id: conductor
    cron: "0,30 * * * *"        # every 30 min
    workflow_ref: conductor-loop
```

**Why one daemon, not many:** with one daemon, the conductor has full state visibility, agents create their own worktrees under `<project>/worktrees/<repo-id>--<branch>`, and tasks are titled `<repo-id>:<action>`. Per-repo sub-daemons fragment state and force the conductor to coordinate cross-daemon — almost always wrong.

## Dual-Brain Conductor (Cross-Check)

Run two product-owner brains on offset crons so they audit each other instead of compounding the same mistake:

```yaml
schedules:
  - id: conductor              # Opus
    cron: "0 * * * *"          # top of the hour
    workflow_ref: conductor-loop
  - id: product-owner-codex    # GPT-5.x via codex
    cron: "30 * * * *"         # offset 30 min
    workflow_ref: product-owner-codex-loop
```

Codex's reasoning footprint differs from Opus enough to catch confirmation bias. Use this when the conductor's decisions compound (roadmap, scope, "what to ship next") rather than for mechanical work.

## qa-changes Rework Gate

Wrap every implementation phase with a reusable QA gate that loops back on `rework` and `fail`:

```yaml
phases:
  qa-changes:
    mode: agent
    agent: tester
    directive: |
      Verify the change. Verdicts:
      - approve: build/lint/test pass, behavior matches the task
      - rework:  fixable issues — list them; loop back to implementation
      - fail:    structurally wrong — loop back, force a rethink

workflows:
  - id: implement
    phases:
      - implement-feature
      - qa-changes:
          on_verdict:
            rework: { target: implement-feature }
            fail:   { target: implement-feature }
          max_rework_attempts: 3
```

Cap `max_rework_attempts` at 2–3. Beyond that, the QA gate is masking a real problem — let it fail and surface the task as blocked. Apply this gate to `update-deps`, `sync-feature`, `fix-build`, `fix-lint`, `create-template`, `design-improve`, etc.

## Scheduled Specialists (Cross-Check & Memory)

The conductor handles dispatch. Pair it with smaller, dedicated schedules that run independently:

```yaml
schedules:
  - id: memory-curator         # extract knowledge from logs
    cron: "30 */2 * * *"
    workflow_ref: curate-memory
  - id: competitive-scan       # market intel, daily
    cron: "0 8 * * *"
    workflow_ref: competitive-scan
  - id: e2e-periodic           # baseline live behavior 4×/day
    cron: "0 */6 * * *"
    workflow_ref: e2e-test
```

These sit alongside the conductor — they don't dispatch work, they refresh context the conductor reads next sweep.

## Sweep Scripts (DRY the Tool Calls)

Every implementer/tester would otherwise make 3–5 separate Bash calls per repo (install, build, lint, test, audit). Bundle them into one script the agent invokes once:

```bash
# scripts/repo-health.sh
#!/usr/bin/env bash
set -euo pipefail
REPO_ID="${1:?Usage: repo-health.sh <repo-id>}"
cd "$HOME/brain/repos/$REPO_ID"
echo "=== HEALTH: $REPO_ID @ $(git log --oneline -1) ==="
pnpm install --frozen-lockfile 2>&1 | tail -3
pnpm build 2>&1 | tail -10
pnpm lint  2>&1 | tail -10
pnpm test  2>&1 | tail -10
```

Pair with batch dispatch:

```bash
# scripts/sweep-dispatch.sh — usage: sweep-dispatch.sh "title 1" "title 2" ...
for title in "$@"; do
  animus queue enqueue --title "$title" --workflow-ref implement
done
animus queue list
```

Surface them via `tools_allowlist` so command phases can call them. Cuts agent token cost meaningfully on multi-repo sweeps.
