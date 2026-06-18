---
name: animus-workflow-patterns
description: Battle-tested pipeline patterns — QA gates, command phases, conflict resolution, CI checks, stale PR handling, budget guardrails, human approval gates
user_invocable: false
auto_invoke: true
animus_version: "0.5.21"   # animus CLI surface this skill targets
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

Animus no longer performs git operations as runner automation — `post_success.merge`
and the daemon `auto_merge`/`auto_pr` config keys were removed and now fail to parse,
and `animus git` is inspection-only (no `commit`/`push`/`pull` verbs). Anything
git-mutating in a pipeline is a shell `git`/`gh` command phase like the
`push-branch` / `create-pr` ones above — that is the only path.

## Critical: cwd_mode for Command Phases

**This is the #1 gotcha.** The default is inconsistent across config layers: the workflow YAML parser resolves an omitted `cwd_mode` to `project_root`, while the serde runtime-config layer defaults to `task_root` — so an unconfigured command phase may run in the main repo, NOT in the task's worktree. Never rely on the default: always set `cwd_mode: task_root` explicitly on command phases that operate on task code.

```yaml
command:
  cwd_mode: task_root    # NOT the default — set it explicitly
```

Without this, `git push` pushes from `main` (nothing to push), `gh pr create` sees no branch, and `pnpm build` may use stale code.

### cwd_mode options:
- `task_root` — the task's git worktree (what you almost always want for task code)
- `project_root` — main repo directory (the default when omitted in workflow YAML)
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
    model: claude-opus-4-8
    tool: claude
    reasoning_effort: high      # low | medium | high
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

**Why one daemon, not many:** with one daemon, the conductor has full state visibility, the daemon manages each task's worktree under `~/.animus/<repo-scope>/worktrees/`, and tasks are titled `<repo-id>:<action>`. Per-repo sub-daemons fragment state and force the conductor to coordinate cross-daemon — almost always wrong.

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

For deterministic gates, `evals` can be declared directly on the phase instead of a separate QA agent — **but as of v0.5.14 evals parse and validate only; the workflow runner does not execute them yet, so phases advance regardless of the gate**. Declaring an `evals:` block emits a declared-but-unenforced warning at compile time and in `animus workflow config validate`. Author the gate now if you want, but keep a real `qa-changes` agent phase (or a command phase) as the enforced gate until the runner pin lands:

```yaml
phases:
  implement-feature:
    mode: agent
    agent: implementer
    evals:
      pass_threshold: 1.0        # default — all checks must pass
      on_fail: rework            # or block (default) — pause for a human
      max_reworks: 2
      checks:
        - { id: build, kind: command, command: pnpm, args: ["build"] }
        - { id: lint,  kind: command, command: pnpm, args: ["lint"] }
```

`kind: llm_judge` (with `agent` + `prompt`) covers checks that need judgment. On rework, the failure context is injected into the next attempt's prompt. (Unlike evals, `budget:` caps ARE enforced — see the next section.)

## Phase Guardrails: budget, skip_if, idempotency

Three phase-entry knobs that keep autonomous loops bounded:

```yaml
workflows:
  - id: implement
    budget: { max_cost_usd: 10.0 }         # workflow cap subsumes phase caps
    phases:
      - implement-feature:
          budget:
            max_tokens: 500000
            max_cost_usd: 5.0
            on_exceed: pause               # pause (default) | fail | warn
      - install-deps:
          skip_if: ["subject_kind == 'requirement'"]
```

- `budget` — token/cost ceiling (input + output + reasoning), **enforced by the daemon** on its housekeeping cadence (once per heartbeat, default 30s). `on_exceed: pause` (default) pauses the workflow and annotates the task — `animus subject get` shows `paused by workflow wf-... — budget exceeded ($7.50 > $5.00 max_cost_usd)`; `fail` fails the current phase; `warn` records only. The workflow-level cap is authoritative over phase caps; phase caps reset per rework attempt. Honest caveats: an in-flight phase can overshoot by up to one sweep, and enforcement needs a running daemon. Breaches surface in `animus daemon health`, `animus status` (Budget section), `animus cost decisions`, and the per-run `animus output decisions` log — so autonomous loops can finally rely on cost guardrails instead of trusting the conductor's discipline.
- `skip_if` — guards evaluated against the subject (`==` / `!=` on `subject_kind`, `subject_id`, or any subject attribute). A matched guard skips the phase and records why.
- `idempotency` — set `idempotency: idempotent` on phase definitions that are safe to re-run; after a daemon crash those auto-retry. `sideeffecting` (or the default `unknown`) blocks for manual `animus workflow resume --id <run_id> --force`. Mark command phases like `install-deps` and `build-check` idempotent.

## Human Approval Gate (Suspend/Resume HITL)

Agents can ask questions and request approvals mid-phase via the `animus.agent.ask` / `animus.agent.request_approval` MCP tools. In a workflow phase the call suspends: the workflow pauses, the pending interaction lands in the inbox, and answering resumes the provider session with the decision as feedback. Scope it per agent with `approval_policy`:

```yaml
agents:
  implementer:
    model: claude-sonnet-4-6
    tool: claude
    approval_policy:
      auto_allow: ["cargo *", "pnpm *", "git.commit"]
      auto_deny:  ["git.push*"]        # deny wins on overlap (fail closed)
      default: ask                     # ask (escalate to human) | allow | deny
```

Answer from the inbox:

```bash
animus agent interactions list                 # pending questions + approvals
animus agent interactions show <ID>
animus agent interactions answer <ID> --allow
animus agent interactions answer <ID> --deny --message "too risky"
animus agent interactions answer <ID> --text "use the copy table"   # question
animus agent interactions answer <ID> --select "Format=Summary"     # structured question (one per --select)
```

With the claude provider, the gate covers more than explicit MCP calls: the transport wires `animus.agent.request_approval` as the CLI's `--permission-prompt-tool`, so the provider's own gated tool calls and native `AskUserQuestion` prompts land in this same inbox (structured questions answer via `--select` / `--text`).

Answering a suspend-created approval resumes the paused workflow automatically (if the resume spawn fails, the output carries the exact `animus workflow resume` command). Use this instead of a `mode: manual` phase when the *agent* knows where the risky moment is — the gate fires only when actually hit, not on every run. Unanswered approvals deny fail-closed on timeout, so a forgotten inbox never silently allows.

This pairs well with AGENT_PRINCIPLES.md anti-patterns: encode "no auto-merge of PRs touching auth" as `auto_deny` globs the agent cannot talk its way around.

Adjacent knob, different layer: `permission_mode` on agent profiles (and phase `runtime:` overrides) sets the provider's own gating posture (claude `--permission-mode`, codex `approval_policy`, gemini approval mode). Caveat: ad-hoc `animus agent run` / `animus chat send` honor it today, but workflow-phase enforcement waits on the workflow-runner plugin pin — don't rely on `permission_mode` as a workflow gate yet; `approval_policy` + the interactions inbox is the enforced path.

## Phase Skills as Shared Capability

Phase-level `skills:` actually apply to phase agents now (requires workflow-runner plugin v0.4.2+; `animus daemon preflight` warns when the installed runner is older and would silently ignore them). The effective set is the phase's `skills:` ∪ the agent profile's `skills:` — so a shared `qa-changes` phase can carry the QA skill once instead of every tester profile redeclaring it:

```yaml
phases:
  qa-changes:
    mode: agent
    agent: tester
    skills: [code-review]      # applies regardless of which tester profile runs it
```

Typo'd skill names are not silent: explicit `skills:` declarations that don't resolve WARN at compile time and in `animus workflow config validate`; at runtime a miss is a loud dispatch-log warning plus a `missing` metadata record (never a hard failure). Verify after a run with `animus output phase-outputs --workflow-id <id>` — it shows requested vs applied vs missing skills per phase.

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

## AGENT_PRINCIPLES.md — Stable Prompt Anchor

Conductor system prompts grow — ship targets, gates, kill criteria, anti-patterns. Tuning those by editing the agent's `system_prompt:` triggers a daemon restart and is a high-friction loop for product-side changes. Extract the policy into a sibling file the conductor reads at sweep start:

```
.animus/workflows/
├── agents.yaml             # conductor system_prompt: "READ FIRST: AGENT_PRINCIPLES.md"
├── workflows.yaml
├── schedules.yaml
└── AGENT_PRINCIPLES.md     # ship targets, gates, kill criteria, anti-patterns
```

The conductor's prompt stays short and stable. AGENT_PRINCIPLES.md becomes the lever non-engineers can edit: tighten a gate, raise a ship target, add a new kill criterion. Restart-free policy iteration.

Typical AGENT_PRINCIPLES.md sections:
1. **Ship targets** — numeric thresholds per gate (e2e ≥ 70, lint = 0, build = pass).
2. **Kill criteria** — conditions that halt all other work (build red, deploy failed, security CVE ≥ high, score < threshold).
3. **Sweep priorities** — ordered list, conductor stops at first applicable.
4. **Anti-patterns** — things explicitly NOT to do (no major version bumps in dep updates, no auto-merge of PRs touching auth, etc.).
5. **Tools** — allowed/preferred tooling per task class.

## Kill Criteria + Ship Score Discipline

Two complementary policies that keep a conductor from drifting into reflex-triage:

```yaml
# AGENT_PRINCIPLES.md fragment
ship_readiness_target: 70

kill_criteria:
  - id: build-red
    description: pnpm build exits non-zero on flagship
    severity: critical
  - id: deploy-failed
    description: latest production deploy returned non-200 healthcheck
    severity: critical
  - id: security-cve-high
    description: pnpm audit reports a high/critical advisory
    severity: critical
  - id: e2e-floor
    description: e2e score below 50 on any surface
    severity: critical

gates:
  build:        { weight: 25, target: pass }
  lint:         { weight: 10, target: 0_errors }
  e2e:          { weight: 30, target: ">= 70" }
  token_compliance: { weight: 15, target: ">= 80" }
  design_audit: { weight: 20, target: ">= 70" }
```

The conductor reads this each sweep. It computes a per-surface ship score (weighted average of gate scores), checks kill criteria first, then dispatches the work that moves the lowest-scoring closable gap. If the **fleet average score** doesn't move across three consecutive sweeps, the conductor must escalate (write a blocker report, stop reflex-triage). This is what stops the daemon from spinning forever.

## Reports Directory Convention

Specialists write structured reports the conductor reads next sweep. This is how state survives across daemon restarts and how the conductor builds situational awareness without re-running scans every cycle.

```
reports/
├── health/<repo-id>.json              # build/lint/test results, age-stamped
├── security/<repo-id>.md              # pnpm audit + secret scan findings
├── parity/<repo-id>.md                # feature gaps vs flagship
├── openapi/<repo-id>.json             # endpoint diff vs flagship
├── token-compliance/<repo-id>.json    # hardcoded color violations
├── schema/<repo-id>.json              # Drizzle schema drift
├── design/<repo-id>.md                # design audit findings
├── fleet-ship-plan-<date>.md          # conductor escalation report
└── blockers-<date>.md                 # stuck tasks the conductor noticed
```

Rules:
- Reports are written by specialists, **read by the conductor**. One direction.
- Every report has a timestamp at the top. Conductor ignores reports older than the workflow's recheck cadence.
- Reports are committed to git so they survive daemon restarts and become auditable.
- Conductor writes only escalation reports (`fleet-ship-plan`, `blockers`) — never the per-repo scan reports.

## Worktree + Task Title Conventions

The daemon manages task worktrees — agents should not invent their own paths. Each task gets a worktree under the repo's scoped state dir:

```
~/.animus/<repo-scope>/worktrees/task-<sanitized-task-id>/
```

`<repo-scope>` is `<repo-name>-<hash>` (hash of the canonical project root), and the default branch is `animus/<sanitized-task-id>`. Multiple agents stay isolated because each task gets its own worktree.

Task title format: `<repo-id>:<action>`. The implementer agent parses `<repo-id>` to pick which repo to operate on.

```bash
animus subject create --kind task --title "launchapp-nextjs:update-deps" --status ready
animus queue enqueue --task-id <created-task-id> --workflow-ref update-deps

animus subject create --kind task --title "launchapp-nuxt:fix-build" --status ready
animus queue enqueue --task-id <created-task-id> --workflow-ref fix-build

animus subject create --kind task --title "launchapp-react-router:design-improve" --status ready
animus queue enqueue --task-id <created-task-id> --workflow-ref design-improve
```

The workflow ref is bound at dispatch time (queue enqueue or workflow run), not on the task itself.
```

This convention lets you grep `animus queue list` for all in-flight work on a single repo, and lets the conductor write rules like "skip queueing the same `<repo-id>:<action>` 3+ times in a week — that loop is broken."

## Per-Model Implementation Routing

Don't have one `implement` workflow — have several, one per model. The conductor picks based on task character:

```yaml
workflows:
  - id: implement              # default — Claude Sonnet 4.6
    phases: [implement-feature, qa-changes]
  - id: implement-codex        # GPT-5.x via codex — different reasoning footprint
    phases: [implement-feature-codex, qa-changes]
  - id: implement-opus         # Claude Opus — high-judgment / risky changes
    phases: [implement-feature-opus, qa-changes]
  - id: implement-haiku        # Claude Haiku — cheap mechanical fixes
    phases: [implement-feature-haiku, qa-changes]
```

Each `implement-feature-*` phase routes to a different agent persona that uses a different model. The QA gate is shared. Decision rule:

| Task character | Workflow |
|---|---|
| Mechanical fix (lint, simple bug, dep bump) | `implement-haiku` |
| Standard feature work | `implement` (Sonnet) |
| Architecture / API design / cross-package refactor | `implement-opus` |
| Conductor flagged uncertainty / contentious change | `implement-codex` (different brain) |

This is the implementation-side analog of the dual-brain conductor: model diversity catches blind spots that compound when one model owns every decision.

## Scan-Type Workflows (Read-Only Producers)

Scans don't dispatch work — they produce reports the conductor reads next cycle. Pattern:

```yaml
phases:
  scan-token-compliance:
    mode: command
    directive: "Scan for hardcoded colors not coming from --la-* tokens"
    command:
      program: ./scripts/scan-token-compliance.sh
      args: ["${REPO_ID}"]
      cwd_mode: project_root
      timeout_secs: 120

  scan-token-compliance-all:
    mode: agent
    agent: scanner
    directive: |
      Run scripts/scan-token-compliance-all.sh.
      For each repo result, write reports/token-compliance/<repo-id>.json.
      Append a fleet summary to reports/token-compliance/_fleet.md.
      Do NOT enqueue fix tasks — the conductor decides priority.

workflows:
  - id: scan-token-compliance       # single repo
    phases: [scan-token-compliance]
  - id: scan-token-compliance-all   # fleet
    phases: [scan-token-compliance-all]
```

Other useful scans observed in production: `scan-openapi-parity` (live `/api/openapi.json` diff vs flagship), `scan-schema-parity` (Drizzle schema drift), `check-parity` (feature gap report). Scans run on their own schedule (not via conductor) so the conductor never blocks on a scan completing.

## Review-then-Rework as Separate Phase

For PR review with rework, two valid shapes — they fail differently:

```yaml
# Shape A: review with rework target
- id: review-pr
  phases:
    - review-pr:
        on_verdict:
          rework: { target: implement-feature }
          fail:   { target: implement-feature }
        max_rework_attempts: 3

# Shape B: review-then-rework as separate phase
- id: review-pr
  phases:
    - review-pr
    - rework-pr:
        on_verdict:
          rework: { target: rework-pr }      # iterate the rework
          fail:   { target: review-pr }      # bounce to a fresh review
        max_rework_attempts: 2
```

Shape A loops the IMPLEMENTATION agent; cheap if the original implementer is the right model for the rework. Shape B introduces a dedicated `rework-pr` phase — useful when the rework is "address the reviewer's specific comments" rather than "redo the implementation". `rework-pr` typically runs a smaller, faster model since the change set is small.

ao-templates uses Shape B for `review-pr` and Shape A for everything else. The general rule: use Shape B only when the rework character genuinely differs from the original implementation.

## Chained Creative Pipelines

For artifact pipelines (blog posts, docs, marketing copy, design assets), chain phases linearly with no gates between — each phase is itself the gate:

```yaml
- id: blog-draft-daily
  phases:
    - blog-topic-research      # agent — picks topic from registry
    - blog-content-writing     # agent — writes draft
    - blog-seo-review          # agent — keyword density, title length, meta
    - blog-asset-generation    # command — image gen pipeline
    - blog-commit-pr           # command — git, gh pr create
```

No `qa-changes` gate, because each phase has structured output the next phase reads. If `blog-seo-review` rejects, the workflow fails cleanly — the human reviews the PR (or the conductor sees the failure next sweep and re-queues with a different topic).

Apply the same pattern to:
- Documentation generation (research → outline → draft → review → publish)
- Release announcements (changelog scrape → tone-pass → asset gen → post)
- Competitive intel briefs (research → cluster → summarize → distribute)

## Multi-Surface Deploy Pipeline

For a service with deploy + verify steps, chain command + agent phases. Use the agent only where judgment is needed:

```yaml
phases:
  cloud-deploy:
    mode: command
    command: { program: fly, args: ["deploy"], cwd_mode: project_root, timeout_secs: 600 }
  cloud-healthcheck:
    mode: command
    command: { program: ./scripts/healthcheck.sh, cwd_mode: project_root, timeout_secs: 60 }
  cloud-e2e:
    mode: agent
    agent: cloud-tester
    directive: "Run Playwright E2E against the live URL. Report pass/fail per flow."
  cloud-design-audit:
    mode: agent
    agent: cloud-designer
    directive: "Audit the deployed dashboard against design tokens."

workflows:
  - id: cloud-deploy-and-verify
    phases:
      - cloud-deploy
      - cloud-healthcheck       # gate — fail here = deploy is broken
      - cloud-e2e
      - cloud-design-audit
```

Pattern: deploy + healthcheck are deterministic command phases (no LLM tokens for `fly deploy`). Verification (E2E, design audit) is agent because it needs interpretation. Putting healthcheck immediately after deploy means a broken deploy fails fast without burning agent tokens on an audit that can't possibly pass.

## Watching the Conductor Work — `animus daemon stream`

Autonomous loops are unobservable until they break. `animus daemon stream` is the live JSONL feed that merges every phase transition, model call, queue mutation, and schedule fire into one structured stream. Keep one terminal running it whenever you're tuning a conductor.

**Sweep diagnostics:**
```bash
# Did my conductor fire? Did it produce a dispatch?
animus daemon stream --cat schedule --pretty &
animus daemon stream --cat phase --level info --pretty
```

If a schedule fires and no `phase` activity follows within ~60 seconds, the conductor is stuck — usually waiting on an MCP call, mis-reading state, or hitting a cap. Drop down to:

```bash
animus daemon stream --cat phase --workflow <conductor-loop-id> --pretty
```

…and look at the conductor agent's actual output. If it loaded principles + reports and produced no dispatch, the sweep priorities aren't matching reality (kill criteria too narrow, ship score not moving — see *Kill Criteria + Ship Score Discipline*).

**Cost watch on dual-brain conductors:**
```bash
animus daemon stream --cat llm --pretty | grep -E "opus|gpt-5"
```
Dual-brain (Opus + Codex) is the pattern most likely to surprise you on cost. Watch the merged stream until you've seen one full cycle and confirmed the offset crons aren't double-firing.

**Rework loop detection:**
```bash
animus daemon stream --cat phase --pretty | grep -i rework      # live
animus workflow decisions --id <workflow-id>                    # recorded rework verdicts per run
```
If you see the same `<repo-id>:<action>` task rework three times within a sweep window, your `qa-changes` gate is hiding a structural problem — let it fail (anti-pattern #5).

**Alerting without polling:** notifier plugins receive `workflow-failed` and `task-blocked` events (fired once per transition, not per tick), plus `workflow-budget-breach` (once per breach) — wire a Slack/webhook notifier for those three and you can stop tail-watching for failures entirely.

Not sure which surface to reach for? `animus daemon observe` is the front-door — bare invocation prints a data-source matrix (events vs logs vs stream) plus a recent merged tail; `--follow` delegates to the live stream. See `animus-daemon-operations` for the full filter matrix.

## Run Retention for Autonomous Loops

A conductor on a 30-min cron produces ~48 runs/day, each with `runs/`, `artifacts/`, and persisted phase outputs under `~/.animus/<repo-scope>/`. Prune on a schedule or you'll find out the hard way:

```bash
animus workflow prune --older-than 30d            # preview (dry-run is the default)
animus workflow prune --older-than 30d --yes      # delete; unit suffixes work (12h, 90m)
animus workflow prune --keep-last 200 --status failed --yes
animus workflow delete --run-id <RUN_ID> --yes    # surgical single-run removal
```

Only terminal runs (`completed`, `failed`, `escalated`, `cancelled`) are eligible — in-progress and paused runs are always skipped. Wrap the prune in a weekly command-phase workflow on its own schedule, like any other scan.

## Anti-Patterns (Things That Look Right But Aren't)

Production failures that taught these:

1. **Cron storms** — every schedule starts on the minute (`0 * * * *`). The event-driven scheduler fires each cron on its precise deadline now (no more waiting for the next tick), but 8 simultaneous fires still contend for the per-tick dispatch budget and pool slots — later spawns get rejected and retried. Stagger: `0 * * * *`, `7 * * * *`, `14 * * * *`, etc.

2. **Conductor that dispatches multiple tasks per sweep** — feels efficient but obscures which dispatch moved the score. Cap at one dispatch per sweep until you have telemetry to know which dispatches help.

3. **Agent that creates AND enqueues** — the planner enqueues. Specialists CREATE tasks (status: ready) and let the planner pick them up. Agents that auto-enqueue race the planner and double-execute. Note what makes the split enforceable: the daemon is queue-only — Ready subjects are NEVER auto-run. Work dispatches only when something calls `animus queue enqueue` or a cron `schedules:` entry fires, so a created-Ready task just sits until the planner enqueues it.

4. **Reading every report every sweep** — the conductor loads `reports/**/*` and burns 50K tokens on stale data. Filter by mtime ≥ "since last sweep" and only read what changed.

5. **`max_rework_attempts > 3`** — looks defensive, hides a real bug. After 3 reworks, the gate is masking a structural issue. Let it fail and surface the task as blocked so a human (or the conductor's escalation report) can intervene.

6. **`implement` for everything** — using Sonnet for a 3-line lint fix burns money; using Sonnet for an architecture rewrite under-resources judgment. Route by task character (see Per-Model Implementation Routing).

7. **No `AGENT_PRINCIPLES.md`** — the conductor's `system_prompt` becomes a 2000-line tuning surface that triggers a daemon restart on every edit. Extract policy into a sibling file the conductor reads at sweep start.

8. **Per-repo sub-daemons** — feels like isolation; actually fragments state and forces the conductor to coordinate cross-daemon. One daemon, one conductor, daemon-managed worktrees per task.
