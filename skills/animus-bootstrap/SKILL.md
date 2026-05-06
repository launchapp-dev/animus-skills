---
name: animus-bootstrap
description: Guide a project from idea to autonomous engineering setup — interview the user, write VISION.md, AGENT_PRINCIPLES.md, registry, agents/workflows/phases/schedules YAML, scripts, and a first runnable task. Use when standing up Animus in a new project beyond the minimal /animus-setup scaffold.
user_invocable: true
auto_invoke: false
---

# Animus Bootstrap — Idea → Autonomous Engineering Team

You are bootstrapping a complete Animus-driven autonomous engineering setup for the current project. By the end of this flow the user has a daemon running, a conductor on a cron, specialists wired up, a VISION.md, an AGENT_PRINCIPLES.md, scripts in place, and one real task running end-to-end.

This is heavier than `/animus-setup`. Use that one when the user just needs a daemon and a hello-world workflow. Use this one when the user is committing a project to autonomous operation — "build a team, give them a brief, watch them work."

## How to run this flow

1. **Interview before writing.** Ask one focused batch of questions, get answers, then write artifacts. Do not generate VISION.md from a one-line user prompt — the result will be generic and the user will throw it away.
2. **Use AskUserQuestion** for branching decisions (project type, repo scope, model routing). Use plain prose questions for free-form input (mission, success criteria, kill criteria).
3. **Write artifacts in dependency order** (vision → principles → registry → agents → phases → workflows → schedules → mcp → scripts → CLAUDE.md). Later files reference earlier ones; do not skip ahead.
4. **Commit after each phase.** Atomic commits make the bootstrap auditable and revertable. Use messages like `bootstrap: vision`, `bootstrap: principles`, `bootstrap: agents.yaml`, etc.
5. **Verify before declaring done.** Run the daemon, create one task, run it, watch it via `animus daemon stream`, confirm the conductor is producing dispatches.

If the user has already completed `/animus-setup`, skip to Phase 3. If they haven't, run `/animus-setup` first (or do its work inline) — this skill assumes `.ao/` exists and the daemon can start.

## Reference reads

Open these only when you reach the matching phase, not up front:
- `../animus-workflow-patterns/SKILL.md` — conductor / sweep / qa-changes / scheduled specialists / kill criteria
- `../animus-agent-personas/SKILL.md` — system-prompt skeleton, specialist prompts, cron stagger
- `../animus-workflow-authoring/SKILL.md` — YAML schema details for agents/phases/workflows
- `../animus-daemon-operations/SKILL.md` — `animus daemon stream`, MCP tools, runner architecture
- `../animus-mcp-servers-for-agents/SKILL.md` — wiring Context7, memory, GitHub MCP

## Phase 1 — Discovery interview

Ask these in one `AskUserQuestion` batch (4 questions max — split if needed). Frame as decisions the conductor will make from, not metadata.

1. **Project shape.** Single repo / fleet of related repos / single service with deploy / artifact pipeline (blog, docs, marketing).
2. **Primary work character.** Code (features, bugs, refactors) / content (writing, design) / ops (deploys, scans, audits) / mixed.
3. **Cron cadence preference.** Aggressive (every 15–30 min, lots of parallel sweeps) / steady (hourly) / conservative (every 4–6h, run mostly on demand).
4. **Risk tolerance.** Auto-merge approved PRs / require human review / no auto-anything.

Then ask, in plain prose:
- "In one paragraph, what is this project? Who uses it? What does success look like in 90 days?" — this becomes the VISION.md mission.
- "What's the **one** kill criterion that should halt all other work the moment it trips?" — seeds AGENT_PRINCIPLES.md.
- "Which models do you want to use, and where?" (Default: Sonnet for implementation, Opus for the conductor, Haiku for cheap scans, Codex for second-opinion implementation. Ask if they want to deviate.)

Stop and confirm understanding before writing anything. If their answers contradict (e.g., "no auto-anything" + "aggressive cadence with auto-merge"), name the contradiction and ask them to resolve it.

## Phase 2 — VISION.md

Write to project root. Structure:

```markdown
# <Project Name> Vision

## Mission
<one paragraph from the user's discovery answer — keep their words where possible>

## Who this is for
- <persona 1>
- <persona 2>

## What success looks like (90 days)
- <measurable outcome 1>
- <measurable outcome 2>
- <measurable outcome 3>

## What we are NOT building
- <explicit non-goal 1>
- <explicit non-goal 2>

## North star metric
<one number that, when it moves up, means the project is winning>
```

Non-goals are as important as goals — they keep the conductor from drifting into adjacent work. Push the user to name at least two.

## Phase 3 — registry.yaml (or surfaces.yaml)

For fleets and multi-repo projects only. Skip for single-repo.

```yaml
# .ao/registry.yaml — what surfaces this project owns
ship_mode: parallel        # parallel | sequential | flagship-first
ship_readiness_target: 70

surfaces:
  - id: my-app-flagship
    role: flagship
    repo: github.com/<owner>/<repo>
    framework: <react-router|nextjs|nuxt|...>
    path: ~/brain/repos/my-app-flagship
    ship_targets:
      build: pass
      lint: 0_errors
      e2e: ">= 70"

  - id: my-app-mobile
    role: variant
    repo: github.com/<owner>/<mobile-repo>
    path: ~/brain/repos/my-app-mobile
    ship_targets: { ... }
```

If the user doesn't have a clear flagship/variant relationship, omit `role` and just list surfaces.

## Phase 4 — AGENT_PRINCIPLES.md

Write to `.ao/workflows/AGENT_PRINCIPLES.md`. This is the conductor's policy file — separated from `system_prompt:` so the user can tune ship targets without restarting the daemon.

Sections:
1. **Ship targets** — numeric thresholds per gate.
2. **Kill criteria** — conditions that halt all other work.
3. **Sweep priorities** — ordered list. Conductor stops at first applicable.
4. **Anti-patterns** — explicit DON'Ts.
5. **Tools** — preferred tooling per task class.

See `../animus-workflow-patterns/SKILL.md` "AGENT_PRINCIPLES.md — Stable Prompt Anchor" and "Kill Criteria + Ship Score Discipline" sections for the full template.

## Phase 5 — agents.yaml

Write to `.ao/workflows/agents.yaml`. Always include the conductor; include specialists based on Phase 1's work character.

```yaml
agents:
  conductor:
    model: claude-opus-4-7         # Opus pays back on judgment work
    tool: claude
    mcp_servers: ["animus", "memory", "github", "sequential-thinking"]
    system_prompt: |
      You are the conductor for <project>.

      ## READ FIRST
      Read `.ao/workflows/AGENT_PRINCIPLES.md` before anything else.
      That file owns ship targets, gates, kill criteria, and anti-patterns.

      ## Mission
      <one-sentence pull from VISION.md>

      ## Project Root
      <absolute path>

      ## Sweep priorities
      See AGENT_PRINCIPLES.md §3.

      ## Output
      Queue at most ONE focused dispatch per sweep.
      Title format: <surface-id>:<action>. Workflow ref: <implement|fix-build|...>.

  implementer:    { model: claude-sonnet-4-6, tool: claude, mcp_servers: ["animus", "context7"] }
  reviewer:       { model: claude-sonnet-4-6, tool: claude, mcp_servers: ["animus", "github"] }
  tester:         { model: claude-sonnet-4-6, tool: claude, mcp_servers: ["animus"] }

  # Add only if Phase 1 needs them:
  scanner:        { model: claude-haiku-4-5,  tool: claude, mcp_servers: ["animus", "package-version"] }
  syncer:         { model: claude-sonnet-4-6, tool: claude, mcp_servers: ["animus"] }       # for fleet/parity work
  implementer-codex: { model: gpt-5.5, tool: codex, mcp_servers: ["animus"] }              # second-opinion impl
  product-owner-codex: { model: gpt-5.5, tool: codex, ... }                                # for dual-brain conductor
  cloud-tester:   { model: claude-sonnet-4-6, tool: claude, mcp_servers: ["animus", "playwright"] }  # for deploy verify
```

See `../animus-agent-personas/SKILL.md` for the full conductor prompt skeleton.

## Phase 6 — phases.yaml

Write to `.ao/workflows/phases.yaml`. Define phases referenced by workflows. Always include `qa-changes` (the rework gate).

```yaml
phases:
  conductor-sweep:
    mode: agent
    agent: conductor
    directive: "Run the sweep. Queue at most one dispatch."

  implement-feature:
    mode: agent
    agent: implementer
    directive: "Implement the assigned task. Worktree at <project>/worktrees/<surface-id>--<branch>. Commit, push, open PR."
    capabilities: { mutates_state: true }

  qa-changes:
    mode: agent
    agent: tester
    directive: |
      Verify the change. Verdicts:
      - approve: build/lint/test pass, behavior matches the task
      - rework:  fixable issues — list them; loop back to implementation
      - fail:    structurally wrong — loop back, force a rethink

  review-pr:
    mode: agent
    agent: reviewer
    directive: |
      Before merging, check `gh pr checks <number>`.
      - Failures caused by THIS PR: queue rework.
      - Pre-existing failures: merge anyway, create a fix task.
      - Pending checks: skip, next cycle picks it up.
      - All pass: review the diff, merge if approved.

  # Command phases (deterministic — use these for git/test/build, not agents):
  install-deps: { mode: command, command: { program: pnpm, args: [install], cwd_mode: task_root, timeout_secs: 120 } }
  build-check:  { mode: command, command: { program: pnpm, args: [build],   cwd_mode: task_root, timeout_secs: 300 } }
  lint-check:   { mode: command, command: { program: pnpm, args: [lint],    cwd_mode: task_root, timeout_secs: 120 } }
  push-branch:  { mode: command, command: { program: git,  args: [push, -u, origin, HEAD], cwd_mode: task_root, timeout_secs: 60 } }
  create-pr:    { mode: command, command: { program: gh,   args: [pr, create, --fill, --base, main], cwd_mode: task_root, timeout_secs: 60 } }
  wait-for-ci:  { mode: command, command: { program: gh,   args: [pr, checks, --watch, --fail-fast], cwd_mode: task_root, timeout_secs: 600 } }
```

`cwd_mode: task_root` is the #1 gotcha — see `../animus-workflow-patterns/SKILL.md`.

## Phase 7 — workflows.yaml

Write to `.ao/workflows/workflows.yaml`. Always include: `conductor-loop`, `implement` (with qa-changes gate), `review-pr`. Add others based on Phase 1.

```yaml
default_workflow_ref: implement

workflows:
  - id: conductor-loop
    name: "Conductor Loop"
    description: "Sweep state, prioritize, queue at most one dispatch"
    phases: [conductor-sweep]

  - id: implement
    name: "Implement"
    phases:
      - implement-feature
      - install-deps
      - build-check
      - lint-check
      - push-branch
      - create-pr
      - wait-for-ci
      - qa-changes:
          on_verdict:
            rework: { target: implement-feature }
            fail:   { target: implement-feature }
          max_rework_attempts: 3
      - review-pr:
          on_verdict:
            rework: { target: implement-feature }
          max_rework_attempts: 2

  - id: review-pr
    phases: [review-pr]

  # Add by work character:
  - id: implement-codex   # for the second-opinion route
    phases: [implement-feature-codex, install-deps, build-check, lint-check, push-branch, create-pr, wait-for-ci, qa-changes]
  - id: fix-build         # critical/kill-criterion workflow
    phases: [fix-build, install-deps, build-check, qa-changes]
  - id: scan-security     # read-only producer
    phases: [scan-security]
```

For richer patterns (scan-type, chained creative pipelines, multi-surface deploy, review-then-rework as separate phase) see `../animus-workflow-patterns/SKILL.md`.

## Phase 8 — schedules.yaml

Write to `.ao/workflows/schedules.yaml`. Stagger cron offsets — never start everything on the minute.

Match cadence to Phase 1's preference. Examples:

```yaml
# Aggressive (default for active development):
schedules:
  - { id: conductor,         cron: "0,30 * * * *",  workflow_ref: conductor-loop }
  - { id: memory-curator,    cron: "15 */2 * * *",  workflow_ref: curate-memory }
  - { id: e2e-periodic,      cron: "45 */6 * * *",  workflow_ref: e2e-test }

# Steady (default for stable projects):
schedules:
  - { id: conductor,         cron: "0 * * * *",     workflow_ref: conductor-loop }
  - { id: memory-curator,    cron: "30 */4 * * *",  workflow_ref: curate-memory }

# Conservative (mostly on-demand):
schedules:
  - { id: conductor,         cron: "0 */6 * * *",   workflow_ref: conductor-loop }
```

If Phase 1 said "fleet of repos" or "dual-brain", add:
```yaml
  - { id: product-owner-codex, cron: "30 * * * *",   workflow_ref: product-owner-codex-loop }
  - { id: competitive-scan,    cron: "0 8 * * *",    workflow_ref: competitive-scan }
```

## Phase 9 — mcp-servers.yaml

Write to `.ao/workflows/mcp-servers.yaml`. Wire the MCP servers the agents in Phase 5 reference.

```yaml
mcp_servers:
  animus:
    command: animus
    args: ["--project-root", ".", "mcp", "serve"]
  memory:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-memory"]
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
  context7:
    command: npx
    args: ["-y", "@upstash/context7-mcp"]
  sequential-thinking:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-sequential-thinking"]
```

Only include servers actually referenced in Phase 5 — extras burn agent context.

## Phase 10 — scripts/

Create `scripts/` at project root with at least these two:

**`scripts/repo-health.sh`** (per `../animus-workflow-patterns/SKILL.md` — DRYs the 3–5 separate Bash calls every implementer/tester would otherwise make):
```bash
#!/usr/bin/env bash
set -euo pipefail
SURFACE="${1:?Usage: repo-health.sh <surface-id>}"
cd "$HOME/brain/repos/$SURFACE"
echo "=== HEALTH: $SURFACE @ $(git log --oneline -1) ==="
pnpm install --frozen-lockfile 2>&1 | tail -3
pnpm build 2>&1 | tail -10
pnpm lint  2>&1 | tail -10
pnpm test  2>&1 | tail -10
```

**`scripts/sweep-dispatch.sh`** — batch-enqueue:
```bash
#!/usr/bin/env bash
set -euo pipefail
for title in "$@"; do
  animus queue enqueue --title "$title" --workflow-ref implement
done
animus queue list
```

`chmod +x` both. Add more scripts when Phase 1 implies them (deploy verify, design audit, parity scans, etc.) — see `../animus-workflow-patterns/SKILL.md` "Scan-Type Workflows".

## Phase 11 — reports/ directory

Create `reports/` at project root. Drop a `.gitkeep`. Pre-create the subdirs the workflows in Phase 7 will write to: `health/`, `security/`, `parity/` (if fleet), `design/` (if UI), `blockers/` (always — conductor escalation reports land here).

`reports/` is committed to git so it survives daemon restarts and becomes auditable. Specialists write; conductor reads. See `../animus-workflow-patterns/SKILL.md` "Reports Directory Convention".

## Phase 12 — CLAUDE.md (or AGENTS.md for Codex)

Write or extend project CLAUDE.md with an Animus section so any agent picking up the repo knows how it's organized:

```markdown
## Animus

This project runs an Animus daemon (single-daemon SDLC). Conductor sweeps every <cadence>.

- **VISION.md** — product vision, north star metric
- **.ao/workflows/AGENT_PRINCIPLES.md** — ship targets, gates, kill criteria
- **.ao/workflows/{agents,phases,workflows,schedules,mcp-servers}.yaml** — daemon config
- **scripts/** — repo-health.sh, sweep-dispatch.sh, ...
- **reports/** — specialist outputs the conductor reads each sweep
- **worktrees/** — agents create their own at `<project>/worktrees/<surface-id>--<branch>`

Watch the daemon: `animus daemon stream --pretty`
Sweep priorities: `.ao/workflows/AGENT_PRINCIPLES.md` §3
```

## Phase 13 — verify end-to-end

Don't declare done until you've watched a real task complete.

```bash
# 1. Validate config
animus workflow config validate
animus workflow definitions list

# 2. Start the daemon
animus daemon start --autonomous --auto-run-ready true --pool-size 3 --interval-secs 10
animus daemon health

# 3. Create one real task that exercises the implement workflow
animus task create --title "<surface>:bootstrap-smoke-test" --task-type chore --priority high \
  --description "Add a NOTES.md file at repo root with one sentence about the project. Verify worktree, commit, PR flow."

# 4. Enqueue and watch
animus queue enqueue --title "<surface>:bootstrap-smoke-test"
animus daemon stream --pretty
```

Confirm in the stream:
- A `phase` event for `implement-feature` starting
- An `llm` event with the implementer model
- A `phase` event for `qa-changes` returning `approve`
- A PR opened (`runner` or `phase` event with the PR URL)

If the conductor schedule is firing but produces no dispatch within 60s of fire, drop into:
```bash
animus daemon stream --workflow conductor-loop --pretty
```
…and look at the conductor agent's actual output. If it loaded principles + reports and produced no dispatch, the sweep priorities aren't matching reality (typically: kill criteria too narrow, ship score not moving). See `../animus-workflow-patterns/SKILL.md` "Watching the Conductor Work".

## Final hand-off

Tell the user, in this order:
1. The artifacts that landed (file list, with one-line each).
2. How to watch the daemon (`animus daemon stream --pretty`).
3. How to tune principles without restarting (edit `.ao/workflows/AGENT_PRINCIPLES.md`).
4. How to add a new specialist (edit `.ao/workflows/agents.yaml`, add a workflow that uses it, restart daemon).
5. The first real task they should queue (something concrete from VISION.md's 90-day success criteria).

Do **not** offer to "tune the conductor" or "add more workflows" as a follow-up — let them run the smoke test, see autonomous work happen, and come back with their own asks.

## Anti-patterns specific to bootstrap

1. **Generating VISION.md from a one-line prompt.** Pushes the user into editing a generic template. Always do the discovery interview first.
2. **Skipping AGENT_PRINCIPLES.md "because the conductor's prompt is enough."** The whole point of separating them is restart-free policy iteration — burying ship targets in `system_prompt:` defeats it.
3. **Wiring every MCP server "just in case."** Each one in `mcp_servers:` adds tokens to every agent invocation. Wire only what Phase 5's agents reference.
4. **Cron storms.** Every schedule on `0 * * * *` causes minute-rollover storms. Stagger by 5–15 min offsets (see `../animus-agent-personas/SKILL.md` "Recommended Cron Schedule").
5. **Auto-merge on a fresh setup.** Even if the user wants it, default to `auto_merge: false` for the first week. Let them watch the conductor work, then flip.
6. **Bootstrapping without a real task.** A daemon with no work is unobservable. Phase 13's smoke test is non-optional — without it you cannot verify the wiring.
