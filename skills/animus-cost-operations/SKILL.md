---
name: animus-cost-operations
description: Inspect Animus token and USD spend, attribute cost to providers/models/phases, and operate workflow budget caps. Use when a question involves cost, spend, tokens, USD, budget caps or `budget:` blocks, budget breaches, paused-for-budget workflows, provider/model cost attribution, cost leaderboards, or `animus cost` commands.
user_invocable: false
auto_invoke: true
---

# Cost Operations

The `animus cost` surface (v0.5.5+) reports token + USD spend per workflow
run, and the daemon enforces declared `budget:` caps on its housekeeping
sweep. Cost state lives at the scoped root
(`~/.animus/<repo-scope>/cost-state.v1.json`); budget breaches append to the
scoped fleet log `~/.animus/<repo-scope>/decisions.jsonl`.

## CLI Commands

```bash
animus cost summary                       # aggregate spend, default --since 24h
animus cost summary --since 7d --top 10   # window: 30m/12h/7d/2w; top-spender cap (default 5)
animus cost summary --by provider         # in-window spend grouped by tool, with %
animus cost summary --by model            # grouped by model id

animus cost workflow <WORKFLOW_RUN_ID>            # per-phase breakdown for one run
animus cost workflow <WORKFLOW_RUN_ID> --by provider|model|phase

animus cost top                           # rank runs by --by tokens|cost (default cost), --limit N (default 10)
animus cost top --by model                # cross-run model leaderboard (tokens, USD, %)
animus cost top --by provider             # cross-run provider leaderboard

animus cost trends --window day|week|month --n 30  # bucketed totals (workflow-level only)
animus cost conversation <CONVERSATION_ID>         # spend for one chat conversation (v0.5.10)
animus cost decisions [--since <DURATION>]         # recorded budget-cap breaches from the scoped breach log
```

`cost workflow` takes the workflow RUN id (the per-run identifier that
`cost summary`/`top` rows carry), not a workflow definition id.

Typed exit codes (v0.5.13+): invalid input = 2, not-found = 3,
unavailable = 5. `--json` envelope schemas include `animus.cost.summary.v1`,
`animus.cost.workflow.v1`, `animus.cost.top.v1`, `animus.cost.trends.v1`,
`animus.cost.conversation.v1`, `animus.cost.decisions.v1`, and the grouped
views `animus.cost.summary.breakdown.v1`,
`animus.cost.workflow.breakdown.v1`, `animus.cost.top.models.v1`.

### Attribution caveats

- Grouped views attribute **live** workflows only. Archived `history` rows
  keep workflow-level totals but no per-phase provider/model detail: they
  are excluded from `cost summary --by`, fold into `unknown` in
  `cost top --by model`, and `cost workflow --by` is rejected for archived
  runs.
- Phases with no `(provider, model)` attribution fold into an `unknown`
  bucket rather than being dropped. When `unknown` exceeds **20%** of
  grouped cost, the grouped views print a one-line attribution-honesty hint
  ("N% of spend lacks model attribution; provider plugins must report
  model_id"). Fix at the plugin: emit `model_id` on metadata frames.
- `cost trends` is intentionally workflow-level only — buckets are built
  from workflow-level totals (including history) and are not split by
  provider/model.

## Budget caps in workflow YAML

`budget:` declares cost ceilings at the workflow level (whole run) or
inline on a rich phase entry (one phase; resets per rework attempt). The
workflow-level cap is authoritative even if a phase declares a higher one.

```yaml
workflows:
  - id: expensive-flow
    name: Expensive Flow
    phases:
      - exploration:
          budget:
            max_tokens: 100_000
            max_cost_usd: 1.00
            on_exceed: fail
      - implementation
    budget:
      max_tokens: 1_000_000
      max_cost_usd: 5.00
      on_exceed: pause
```

Fields: `max_tokens` (input + output + reasoning; cache reads/writes
tracked but excluded), `max_cost_usd` (cents precision), `on_exceed:
pause|fail|warn` (default `pause`). At least one cap is required; both
must be > 0.

**Enforcement model:** the daemon enforces caps on its housekeeping sweep,
once per heartbeat (`interval_secs`, default 30s) — not mid-phase
token-by-token. A phase in flight can overshoot the cap by up to one sweep
before the action lands. Enforcement requires a running daemon; without
one, caps are only recorded when an `animus cost` command runs (never
paused). Each newly crossed cap is acted on exactly once: `pause` pauses
the workflow, `fail` fails the current phase terminally, `warn` records and
notifies only.

## Breach visibility

A breach writes to the run's `decisions.jsonl` and the scoped fleet log
(schema `animus.budget-exceeded.v1`), and emits one `workflow-budget-breach`
notifier event per breach (subscribe via `notification_config`
`subscriptions[].event_types`).

- **Task annotation** — a budget-paused workflow annotates its task's
  `blocked_reason` (visible in `animus subject get --kind task --id <id>`):
  `paused by workflow wf-... — budget exceeded ($7.50 > $5.00 max_cost_usd)`
  (phase caps read `phase <id> budget exceeded (…)`). Informational only;
  cleared by `animus workflow resume`.
- **`animus daemon health`** — `budget_enforcement: {enabled, last_sweep_at}`
  (persisted each sweep to `~/.animus/<repo-scope>/budget-enforcement.v1.json`)
  plus a "breaches in last 24h: N" rollup with worst offender.
- **`animus status`** — Budget section with enforcement state and active
  breaches. A breach counts as active when `on_exceed: pause` and the
  workflow is still Paused; resuming drops it. `warn`/`fail` breaches never
  count as active.
- **`animus cost decisions`** — the full breach log; works offline (reads
  the scoped log, daemon not required).

## Three decision logs — don't confuse them

| Command | Reads |
|---|---|
| `animus cost decisions [--since <dur>]` | Scoped fleet breach log (`~/.animus/<repo-scope>/decisions.jsonl`) — budget breaches only |
| `animus output decisions --run-id <run_id>` | Per-run LLM decision log (`runs/<run_id>/decisions.jsonl`): prompts, tool calls, errors; budget breaches land here too |
| `animus workflow decisions --id <workflow_id>` | Phase-advance verdicts (advance/skip/rework) on workflow state |

## Kill-switch

`ANIMUS_DAEMON_DISABLE_BUDGET_ENFORCEMENT=1` (daemon restart required)
skips the enforcement leg: no rescan, no auto-pause/fail, no
`workflow-budget-breach` events. The sweep still records
`{enabled: false, last_sweep_at}` so `daemon health` / `status` show the
leg as disabled.

## Runbook: cap → breach → diagnose → resume

```bash
# 1. Declare a cap in .animus/workflows/*.yaml (budget: block above), then run
animus workflow run --task-id TASK-042

# 2. Detect: status shows the Budget section; the task explains itself
animus status
animus subject get --kind task --id TASK-042   # blocked_reason carries the breach
animus cost decisions --since 24h              # the breach record

# 3. Diagnose what drove the spend
animus cost workflow wf-... --by phase
animus cost workflow wf-... --by model

# 4. Resume (clears the annotation) or raise the cap in YAML first
animus workflow resume --id wf-...
```

## MCP

One cost tool: `animus.cost.decisions` (params `since`, `project_root`) —
lists recorded budget-cap breaches; works offline.

## Related skills

- **animus-observability** — status/health dashboards, the forensic chain, notifier events.
- **animus-workflow-authoring** — full workflow YAML reference beyond the `budget:` block.
- **animus-daemon-operations** — daemon lifecycle, heartbeat config, kill-switches generally.
