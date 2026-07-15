# Animus Skills — Source-Surface Audit

> **HISTORICAL — v0.5.21 baseline.** This audit describes the skill set as verified against animus-cli v0.5.21 (2026-06-18). The skills have since been re-baselined to **v0.7.0-rc.18 + the animus-launchapp portal surface**; the current ground truth, per-skill findings, and update tasks live in [`plans/2026-07-15-v0.7-rebaseline.md`](plans/2026-07-15-v0.7-rebaseline.md).

**Date:** 2026-06-18
**Audited against:** `animus-cli` `main` @ **v0.5.21** (git `0e0aae39`) — source code + reference docs **and** the installed **v0.5.21** binary (installed CLI and source now match). Originally audited at the same `main`; re-confirmed at 0.5.21 source + binary (see the two verification subsections below).
**Skills audited:** all 27 under `skills/` (40 markdown files: 27 `SKILL.md` + 13 `references/*.md`)
**Passes:** (1) parallel domain audit, then (2) a **strict full-read verification pass** — every one of the 40 files re-read end-to-end (no grep substitution, no truncation), each prior finding re-verified against source, and a line-by-line hunt for anything the first pass missed.

> Scope rule: version numbers and each skill's `animus_version` frontmatter are irrelevant — the only question is whether content matches the *current* code/CLI/MCP/config surface. Where source code and reference docs disagree, **source code wins**, and the exact file/symbol is cited per finding.

---

## Review completeness (full-read verification)

All 40 files were read in their entirety in pass 2. Reported line counts matched the on-disk inventory (±1 trailing-newline line). No file was sampled via grep in lieu of reading.

| Group | Files (all read in full) |
|---|---|
| Onboarding | getting-started (242), setup (115), mcp-setup (257), bootstrap (430) |
| Daemon/obs | daemon-operations (384), observability (238), troubleshooting (489), configuration (416) |
| Subject/queue | subject-operations (200), task-management (223), queue-management (159) |
| Workflow/pack/skill-auth | workflow-authoring SKILL (81) + 4 refs (258/198/175/209); workflow-patterns (787); pack-authoring SKILL (49) + 3 refs (174/158/180); skill-authoring SKILL (64) + 3 refs (107/108/231) |
| Agent/chat/cost/model | agent-operations (225), agent-interactions (203), agent-personas (303), chat (165), cost-operations (174), model-operations (192) |
| Plugin/flavor/security/mcp | plugin-operations (278), flavor-operations (178), supply-chain-security (187), mcp-tools SKILL (54) + 3 refs (152/155/89), mcp-servers-for-agents (215), project-history-git (111) |

**Corrections the full-read pass made to the first audit:**
- **`post_success.merge` is in 7 skills, not 3.** First pass missed it in `daemon-operations` (~79-82), `configuration` (~164-168), `troubleshooting` (~296-298), and `project-history-git` (~18-19), all of which point at it as the live merge surface.
- **troubleshooting `runtime: paused` finding — largely refuted.** The human-readable `daemon health` output literally prints `runtime: paused` (`runtime_daemon.rs:306-307`); only the JSON wire field is `runtime_paused` (bool). The skill text is acceptable; downgraded to optional.
- **plugin-operations `--name` finding — over-scoped.** Only `plugin info --name` is wrong (`name` is positional, `plugin_types.rs:633`). `plugin status [NAME]` and `revoke-trust <ORG>` are already positional in the skill (correct); `plugin ping`/`plugin call` legitimately use `--name` (`plugin_types.rs:641,657`). The `outdated --project` finding was **moot** — the skill never claims that flag.
- **New lower-severity items** surfaced: bootstrap/personas `claude-haiku-4-5` is a pass-through id (no roster/alias entry), task-management line ~216 reinforces the removed auto-dispatch model, model-operations `plugin info --name`, mcp-tools `queue.enqueue` MCP missing `run_at`/`expire_after`, pack-authoring `native_module` required-vs-optional mislabel, skill-authoring missing `--priority`/incomplete capability aliases.

---

## Source-verification pass — confirmed against `animus-cli` source @ v0.5.21 (2026-06-18)

**Method.** Every source citation in this audit was independently re-checked against `/Users/rafal/animus-cli` (workspace `crates/orchestrator-cli` v0.5.21, git `0e0aae39`) by reading the cited structs, parse rejections, tests, and registry tables directly — not the reference docs. Skill-file line citations were re-quoted from disk. Verification was fanned out across 7 parallel readers covering daemon / workflow / MCP / subject-queue-task / history-plugin-model / cost-agent-supply-pack-skillauth / the 7 "Accurate" skills.

**Outcome: all three themes and every High- and Medium-severity source claim CONFIRMED.** One sub-finding refuted, four refined, zero themes missed in the "Accurate" set. Installed CLI is now **0.5.19** (the `~/.claude/CLAUDE.md` 0.5.14 note lagged, as it warns it may); source `main` is ahead at **0.5.21** — the line numbers in this section are exact against 0.5.21.

### Refinements / corrections to findings above

1. **workflow-patterns finding #2 — REFUTED, remove it.** Only ONE `post_success.merge` block exists in `animus-workflow-patterns/SKILL.md` (prose at line 99, single YAML block at 104-109). There is no distinct *second* standalone `post_success: merge:` block; finding #1 fully covers it. (Inline row already struck above.)

2. **workflow-patterns finding #4 (cwd_mode) — now LOCATED, CONFIRMED.** The dual-default is real: YAML→definition parser defaults an omitted `cwd_mode` to `ProjectRoot` (`yaml_parser.rs:172`); serde runtime layer defaults to `TaskRoot` (`default_command_cwd_mode`, `agent_runtime_config.rs:1045-1046`; field `:784-785`). Allowed values `project_root|task_root|path` (`parse_cwd_mode`, `yaml_parser.rs:97-103`). The skill already documents this correctly at `animus-workflow-patterns/SKILL.md:114-117`, so the "verify before relying" caveat can be dropped — keep "always set `cwd_mode` explicitly."

3. **workflow-authoring ref finding #4 ("omits daemon.budget") — clarify the fix.** `YamlWorkflowFile` (`yaml_types.rs:374-413`) has **no** top-level `budget:` key. `budget` exists only as (a) the `daemon.budget` fleet cap (`DaemonBudgetConfig`, `types.rs:785-796`: `max_cost_usd_per_day`, `on_exceed`) — *this* is the real fourth `DaemonConfig` field that finding #2 should list — and (b) a per-workflow / per-phase `BudgetConfig` (`YamlWorkflowDefinition.budget`, `yaml_types.rs:256`). The fix note should read "add `daemon.budget`," not "top-level `budget:`."

4. **bootstrap finding #4 / personas `claude-haiku-4-5` — downgrade to borderline non-issue.** It is a pass-through id (absent from the `canonical_model_id` alias table and from `default_model_specs()`, which lists only `claude-sonnet-4-6`/`claude-opus-4-8`, `model_routing.rs:207-219`). **But tool inference still routes it without `tool:`**: `tool_for_model_id` matches substring `claude` → `claude` (`model_routing.rs:170`). Since bootstrap already sets `tool: claude` explicitly, the config is fully valid; the only consequence is roster/cost-table membership. Reframe as "valid pass-through, not in the curated roster," not "needs explicit `tool:`."

### Implementation-ready details (verbatim error strings, tests, corrected paths)

Captured so the rewrites can quote the exact behavior users hit and so reviewers can grep the contract.

**Theme 2 — hard parse rejections at workflow load:**
- `post_success.merge` → fn `reject_removed_post_success_merge` (`yaml_parser.rs:383-412`, error at `:407`): *"`post_success.merge` was removed in v0.5.x ({location}): Animus no longer performs git operations as runner automation. Express commit/push/PR/merge as command phases (a phase with a `command:` running `git`/`gh`). See docs/reference/workflow-yaml.md."* — test `yaml_rejects_removed_post_success_merge_block` (`tests.rs:437-458`).
- `integrations.git.auto_merge` → (`yaml_parser.rs:414-432`, `:427-431`): *"`integrations.git.auto_merge` was removed in v0.5.x ({location}): Animus no longer merges to main autonomously. Express commit/push/PR/merge as command phases ..."* — test `yaml_rejects_removed_auto_merge_in_integrations_git` (`tests.rs:460-470`).
- `GitIntegrationConfig` = `provider` / `base_branch` / `config` only (`types.rs:595-602`).

**Theme 1 — removed key + queue-only:**
- `daemon.auto_run_ready` removed-key warning (`validation.rs:1150-1153`): *"this key was removed: the daemon is queue-only and never auto-dispatches Ready tasks; enqueue work with `animus queue enqueue` or drive it from a `schedules:` cron entry"* — test `removed_daemon_auto_run_ready_is_flagged` (`tests.rs:4359-4363`).
- No `--auto-run-ready` flag anywhere in `daemon_types.rs`. `DaemonStartArgs` (`:188-204`) = flattened `DaemonSchedulerArgs` (`:128-186`: `pool_size`/alias `max_agents`, `interval_secs`, `startup_cleanup`, `resume_interrupted`, `reconcile_stale`, `stale_threshold_hours`, `max_tasks_per_tick`, `phase_timeout_secs`) + `auto_install` + `skip_preflight`. `DaemonConfigArgs` (`:273-329`) = `pool_size`, `interval_secs`, `max_tasks_per_tick`, `stale_threshold_hours`, `phase_timeout_secs`, **`max_daily_usd`** (`:316`), **`silent_threshold_mins`** (`:322`), `notification_config_json`, `notification_config_file`, `clear_notification_config`.

**Theme 3 — `--autonomous` errors:** test `daemon_start_rejects_removed_autonomous_flag` (`cli_types/mod.rs:190-197`) asserts `ErrorKind::UnknownArgument`. No `autonomous` field in `daemon_types.rs`.

**MCP input structs (`services/operations/ops_mcp/`):**
- `DaemonStartInput` (`daemon_inputs.rs:4-23`): 9 fields = `pool_size` (alias `max_agents`) / `interval_secs` / `stale_threshold_hours` / `max_tasks_per_tick` / `phase_timeout_secs` / `startup_cleanup` / `resume_interrupted` / `reconcile_stale` / `project_root`. None of the 5 phantom params.
- `DaemonConfigSetInput` (`daemon_inputs.rs:70-90`): `pool_size` / `interval_secs` / `max_tasks_per_tick` / `stale_threshold_hours` / `phase_timeout_secs` / `notification_config_json` / `notification_config_file` / `clear_notification_config` / `project_root`. No `auto_run_ready`.
- `QueueEnqueueInput` (`queue_inputs.rs:4-29`): includes `run_at` (`:21`) + `expire_after` (`:26`, "Requires `run_at`").

**CLI arg structs:**
- `approval respond`: `--approve` + `--reject` (group `decision`); omitting both → *"provide exactly one of --approve or --reject"* (`approval_types.rs:30-34,44-52`). `approval outcome`: `--success` bare flag, omit = failure (`:59-60`).
- `plugin info <NAME>` positional (`plugin_types.rs:633`); `plugin ping`/`plugin call` use `--name` (`:641`,`:657`); `plugin status [NAME]` (`:234`) + `revoke-trust <ORG>` (`:120`) positional; `plugin prune` exists with `--yes`/`--json` (`:593-601`, registered `:27`).
- `queue enqueue`: `--at`→`run_at`, `--expire-after`→`expire_after_secs` (`requires = "run_at"`), `--input-json` (`queue_types.rs:55-70`); `QueueStats.deferred` printed as `(N deferred)` when >0 (`ops_queue.rs:253-254`); enqueue dedup is plugin-delegated — host surfaces *"subject dispatch already queued (via queue plugin)"* + warning (`ops_queue.rs:162-166`).
- `cost summary`: `CostSummaryBy::{Provider,Model,Task}` (`cost_types.rs:34-42`); `--lifetime` (`:55-59`); `(est.)` markers (`docs/reference/cli/index.md:331`). (`CostWorkflowBy` = Provider/Model/Phase, no Task.)
- `agent run --start-runner`: `hide = true`, *"Deprecated no-op (the agent-runner sidecar was removed in v0.5.3; provider plugins handle CLI invocation)."* (`agent_types.rs:236-243`); same on `AgentControlArgs` (`:276-278`) / `AgentStatusArgs` (`:298-300`).
- Supervisor budget: 3 restarts / 60s window / 5-min cooldown, trips on the 4th (`orchestrator-plugin-host/src/session/plugin_supervisor.rs:21-26,116`; doc string at `status.rs:48`). **Audit's `crates/plugin-host/...` path is wrong — crate is `orchestrator-plugin-host`.**
- Workflow-runner default pin **v0.4.5** (`plugin_registry.rs:30-31`).
- `PackNativeModule`: `feature`+`module_id` required, only `optional` defaulted; `#[serde(deny_unknown_fields)]` (`pack_config/types.rs:206-213`).
- `SkillRegistryAddArgs --priority` (`skill_types.rs:53-54`); accepted capability aliases also include `file_writes`, `state_mutation`/`managed_state_mutation`, `require_commit`, `product_changes`, `is_ui_ux|ui_ux|ui-ux`, `research`, `review`, `testing`, `requirements` (`skill_definition.rs:197-207`); `--source built-in` still in CLI help (`skill_types.rs:144`) despite no builtin tier.
- Status enum (`protocol/src/orchestrator.rs`): canonical `in-progress` (alias `in_progress`/`inprogress`, `:18,51,68`); full set also includes `Backlog` (alias `todo`) and `OnHold` (alias `on_hold`/`onhold`) beyond ready/blocked/done/cancelled — the audit's enumerated set is a subset.

### Skill-file line-number corrections (audit was ±1-2 off)

- **project-history-git:** the `--approved` errors are at **line 87** (not ~88) and **line 92**. Line 92 *also* wrongly says "omit … to reject" — there is no silent reject; you must pass `--reject`. (Two distinct fixes on that line.)
- **plugin-operations** `plugin info --name`: **lines 60 and 175** (not ~61/~176). `plugin prune` is never shown as a runnable command (line 66 only references "the prune remedy" in prose) — documenting it is a net-new gap, not a correction.
- **model-operations** `plugin info --name`: line **183-184** (audit ~184, fine).
- **supply-chain-security** stale pin: **line 53** AND **line 187** (line 187 carries the v0.5.15→`v0.4.3` / v0.5.14→`v0.4.1` split; the v0.5.15 value should be `v0.4.5`).
- **workflow-patterns** "Differences on installed v0.5.14" section exists at **lines 782-788** but covers only `interactions answer --select` + budget-pause annotation — it does NOT mention the post_success.merge / auto_run_ready removals, so dropping it loses nothing theme-related.

### Upstream follow-up — narrowed

`docs/reference/mcp-tools.md:127` lists `auto_install`/`skip_preflight` on `animus.daemon.start` (phantom params) — CONFIRMED stale. But it does **not** list `auto_run_ready`/`skip_runner`/`autonomous` (so it is *less* wrong than the skill's `agent-daemon-task.md:89`), and `mcp-tools.md:222` (queue.enqueue, with `run_at`/`expire_after`) and `:137` (config-set) are CLEAN. The upstream correction should target line 127 only.

### Binary-level pass @ v0.5.21 (independent confirmation)

Now that the installed CLI is **0.5.21** (== audited source), every High/Medium claim was re-checked by driving the actual binary — not just reading source. All passed:

| Claim | Binary check | Result |
|---|---|---|
| Theme 3 `--autonomous` | `daemon start --autonomous` | `error: unexpected argument '--autonomous' found` ✓ |
| Theme 1 `--auto-run-ready` | `daemon start --auto-run-ready true` | `error: unexpected argument '--auto-run-ready' found` ✓ |
| `--skip-runner` | `daemon start --skip-runner` | `error: unexpected argument '--skip-runner' found` (tip: `--skip-preflight`) ✓ |
| Theme 1 removed key | `workflow config validate` w/ `daemon.auto_run_ready: true` | warning verbatim: *"…this key was removed: the daemon is queue-only and never auto-dispatches Ready tasks…"* ✓ |
| Theme 2a `post_success.merge` | validate w/ `workflows[].post_success.merge` | hard error verbatim: *"`post_success.merge` was removed in v0.5.x …Express commit/push/PR/merge as command phases…"* ✓ |
| Theme 2b `integrations.git.auto_merge` | validate w/ that key | hard error verbatim: *"`integrations.git.auto_merge` was removed in v0.5.x …"* ✓ |
| `daemon config` knobs | `daemon config --help` | shows `--max-daily-usd`, `--silent-threshold-mins`; no `--auto-run-ready` ✓ |
| `plugin info` positional | `plugin info --name foo` | `error: unexpected argument '--name'`; usage shows `<NAME>` ✓ |
| `plugin prune` | `plugin prune --help` | exists, `--yes` previews-then-removes ✓ |
| `approval respond` | `approval respond … --approved` | `error: unexpected argument '--approved'`; help shows `--approve`/`--reject` ✓ |
| `queue enqueue` flags | `queue enqueue --help` | shows `--at`, `--expire-after` ("grace window after `--at`"), `--input-json` ✓ |
| `cost summary` | `cost summary --help` | `--by provider\|model\|task`, `--lifetime` present ✓ |
| `skill registry add` | `skill registry add --help` | `--priority` present ✓ |
| `agent run --start-runner` | `agent run --help` | not shown (hidden) ✓ |
| Pin v0.4.5 | `plugin_registry.rs:31` | `("launchapp-dev/animus-workflow-runner-default", "v0.4.5")` ✓ |

Nuance worth recording: the `post_success.merge` reject scanner (`yaml_parser.rs:389-396`) only matches `workflows[].post_success.merge` (workflow-item level). At phase level the key is simply an unknown/ignored field. Either way it is dead — remediation (remove it, use `command:` phases) is unchanged.

> Also reconfirmed at 0.5.21: top-level `workflows:` is a **sequence** of definitions each with an `id:` (`Vec<YamlWorkflowDefinition>`, `yaml_types.rs:381`), not a map — and the skills already document it that way (`- id:` form). No discrepancy.

### Version baseline — re-based to v0.5.21

Installed CLI and audited source are both **0.5.21**, so the "Differences on installed **v0.5.14**" sections (15 skills) describe a version that is no longer installed — they are obsolete and carry no remaining delta (0.5.21 ≥ the documented v0.5.15 surface). **Decision:** drop those sections and bump every skill's `animus_version: "0.5.15"` → `"0.5.21"` (the surface we have now actually verified against, source + binary). This is in addition to the correctness fixes below.

### MCP tool count — RESOLVED, skill is correct

`animus-mcp-setup` claims **86 management / 84 default** MCP tool counts (`SKILL.md:101-102`). Confirmed authoritatively by querying the live MCP server (installed CLI 0.5.19) via `tools/list`:
- `animus mcp serve` → **84** tools (default profile).
- `animus mcp serve --management` → **86** tools.
- The 2 management-only tools are exactly `animus.interactions.answer` and `animus.interactions.list` (gated behind `--management`, per `mcp_types.rs:22-27`).

The skill's numbers match exactly — **no change needed**. (Earlier source greps undercounted because some `animus.*` names are registered dynamically rather than as static `#[tool(name=...)]` literals.)

---

## Executive summary

Findings cluster around **three source changes the skills (and in two places the `animus-cli` CLAUDE.md itself) have not caught up with.**

### Theme 1 — Daemon is queue-only; `auto_run_ready` is gone — 11 skills (DOMINANT)
`daemon.auto_run_ready` was removed and is flagged as an unenforced/removed key (`crates/orchestrator-config/src/workflow_config/validation.rs:1150-1152`: "the daemon is queue-only and never auto-dispatches Ready tasks"). The `--auto-run-ready` flag no longer exists on `daemon start`/`run`/`config` (`crates/orchestrator-cli/src/cli_types/daemon_types.rs` — neither `DaemonSchedulerArgs` nor `DaemonConfigArgs` has the field). The daemon **executes only explicitly-enqueued entries plus cron `schedules:` — it never scans the backend for Ready subjects**; setting a subject to `ready` does not cause pickup.
**Affects:** getting-started, setup, bootstrap, daemon-operations, troubleshooting, configuration, subject-operations, task-management, queue-management, workflow-authoring, workflow-patterns.

### Theme 2 — `post_success.merge` is a hard parse error — 7 skills
`post_success.merge` was removed and now **fails compilation**: "Animus no longer performs git operations as runner automation. Express commit/push/PR/merge as command phases" (`crates/orchestrator-config/src/workflow_config/yaml_parser.rs:383-412`, test `yaml_rejects_removed_post_success_merge_block`). `integrations.git.auto_merge` is likewise rejected at parse (`yaml_parser.rs:414-432`); `GitIntegrationConfig` has only `provider`/`base_branch`/`config` (`types.rs:595-602`).
**Affects:** workflow-authoring, workflow-patterns, bootstrap, daemon-operations, configuration, troubleshooting, project-history-git. Git automation must be expressed as `command:` phases running `git`/`gh`.

### Theme 3 — `--autonomous` now errors — 4 skills
`daemon start --autonomous` is rejected as an unknown argument (test `daemon_start_rejects_removed_autonomous_flag`, `cli_types/mod.rs:191-195`; `docs/reference/cli/index.md:387-390`). Several skills still call it a "hidden, deprecated no-op."
**Affects:** getting-started, setup, daemon-operations, configuration.

> ⚠️ **`animus-cli` CLAUDE.md is itself stale on Themes 1 & 2** — it still lists `daemon:` as consuming `auto_run_ready` and says "merge/PR behavior lives in workflow `post_success.merge`." Verified wrong against source on 2026-06-18. Skills must follow source; the upstream brief should be corrected separately.

### Isolated higher-severity fixes
- **mcp-tools (High):** `animus.daemon.start` MCP row + prose list params (`auto_run_ready`, `skip_runner`, `autonomous`, `auto_install`, `skip_preflight`) that don't exist on `DaemonStartInput` (`ops_mcp/daemon_inputs.rs:4-23`); `config-set` lists a nonexistent `auto_run_ready`.
- **project-history-git (High):** `approval respond --approved` → flag is `--approve`; omitting the decision now *errors* (must pass `--approve` or `--reject`).
- **daemon-operations (High):** documents a nonexistent `--skip-runner` flag (sidecar deleted v0.5.3).

### Smaller fixes
- **plugin-operations / model-operations (Medium):** `plugin info --name X` → `name` is positional.
- **cost-operations (Medium):** `cost summary` missing `--by task` and `--lifetime`.
- **queue-management (Medium):** `queue enqueue` missing `--at`/`--expire-after`/`--input-json`; `queue stats` missing `deferred`. **mcp-tools (Medium):** `queue.enqueue` MCP missing `run_at`/`expire_after`.
- **agent-operations (Medium):** `--start-runner` shown as a live flag (hidden deprecated no-op).
- **configuration / daemon-operations (Medium):** `daemon config` missing `--max-daily-usd` and `--silent-threshold-mins`.
- **Low:** supply-chain pin v0.4.3 → v0.4.5; bootstrap/personas `claude-haiku-4-5` pass-through id; pack-authoring `native_module` field-requiredness; skill-authoring `--priority`/alias completeness; observability exit-code 4 omission; assorted version-delta sections to drop.

---

## Verdicts at a glance

| Skill | Verdict | Highest sev | Dominant issue(s) |
|---|---|---|---|
| animus-getting-started | Significant | High | Theme 1 + Theme 3 |
| animus-setup | Significant | High | Theme 1 + Theme 3 |
| animus-bootstrap | Significant | High | Theme 2 (post_success.merge) + Theme 1 |
| animus-daemon-operations | Significant | High | Theme 1 + Theme 2 + `--skip-runner` (nonexistent) + Theme 3 |
| animus-configuration | Significant | High | Theme 1 + Theme 2 + Theme 3 + missing config knobs |
| animus-troubleshooting | Significant ↑ | High | Theme 2 (newly found) + Theme 1 |
| animus-workflow-authoring | Significant | High | Theme 2 + Theme 1 + `integrations.git` |
| animus-workflow-patterns | Significant | High | Theme 2 ("ONLY surface") + Theme 1 |
| animus-queue-management | Significant | High | Theme 1 + missing `--at`/`--expire-after` |
| animus-mcp-tools | Significant ↑ | High | nonexistent `daemon.start`/`config-set` MCP params |
| animus-project-history-git | Significant ↑ | High | Theme 2 (newly found) + `--approved`→`--approve` |
| animus-subject-operations | Minor | High | Theme 1 (one sentence) |
| animus-task-management | Minor | High | Theme 1 (two spots) |
| animus-plugin-operations | Minor | Medium | `plugin info --name` positional |
| animus-cost-operations | Minor | Medium | missing `--by task` / `--lifetime` |
| animus-agent-operations | Minor | Medium | `--start-runner` shown as live |
| animus-model-operations | Minor ↑ | Medium | `plugin info --name` positional |
| animus-supply-chain-security | Minor | Low | stale v0.4.3 pin (now v0.4.5) |
| animus-pack-authoring | Minor ↑ | Low | `native_module` field-requiredness mislabel |
| animus-skill-authoring | Minor ↑ | Low | missing `--priority`; incomplete capability aliases |
| animus-observability | Accurate | Low (opt) | clean (2 optional Low) |
| animus-mcp-setup | Accurate | — | clean |
| animus-flavor-operations | Accurate | — | clean (preflight fix already applied) |
| animus-mcp-servers-for-agents | Accurate | — | clean |
| animus-agent-interactions | Accurate | — | clean |
| animus-agent-personas | Accurate | — | clean |
| animus-chat | Accurate | — | clean |

(↑ = bumped after the full-read pass.) **Tally:** 11 Significant · 9 Minor · 7 Accurate.

**Already fixed in the current working session** (do not re-apply): 4-role preflight (`at_least_one_provider`, `at_least_one_subject_backend`, `workflow_runner`, `queue`) in plugin-operations, flavor-operations, daemon-operations, troubleshooting; and the `<kind>:<native>` qualified-`--task-id` note in queue-management and subject-operations.

---

## Detailed findings by skill

Severity key: **High** = wrong / produces a failing command or false mental model · **Medium** = stale or materially incomplete · **Low** = cosmetic / optional. Line numbers are approximate (±2); all confirmed by full read.

---

### animus-getting-started — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~133/175 | `daemon start --auto-run-ready true --pool-size N` | No `auto_run_ready` on `DaemonStartArgs`/`DaemonSchedulerArgs` (`daemon_types.rs:127-204`) | High | Drop the flag; `daemon start --pool-size N` |
| 2 | ~126-130/153-158 | "that flag only gates auto-dispatch of Ready tasks" | Queue-only; no Ready scan (`validation.rs:1150-1152`) | High | Replace with queue-only model (enqueue/cron is the only trigger) |
| 3 | ~168-172 | Assumes `subject create` id is `TASK-001`, enqueues it | Id is backend-assigned (`subject_types.rs` SubjectCreateArgs) | Low | Use the id returned by `subject create` |
| 4 | ~142-143 | "`--autonomous` is a deprecated no-op" | Rejected as unknown (`cli_types/mod.rs:191-195`) | Medium | "removed; now errors" |
| 5 | tree | Omits `chat/`, `metrics/`, `secrets/` | Present (`docs/reference/data-layout.md:80-115`) | Low | Add for completeness |
| 6 | ~19/41-47 | Conflates flavor-`required` plugins with daemon preflight roles (lists `transport-http` among required) | transport is bundled by the flavor but is not a preflight *required role* (`plugin_preflight`) | Low | Clarify "flavor required plugins" vs "preflight required roles" |

**Verified clean:** install commands, `plugin install-defaults`/`--include-recommended`, `init --walkthrough`, subject verbs, all MCP tool names, `daemon stream --pretty`.

---

### animus-setup — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~83-85 | `daemon start --auto-run-ready true --pool-size 5` | Flag removed (`daemon_types.rs:188-204`) | High | `daemon start --pool-size 5` |
| 2 | ~105-108 | "drain even when `auto_run_ready` is false" | No such gate; queue-only (`validation.rs:1151`) | High | Drop contrast; enqueue is the trigger |
| 3 | ~89-90 | "`--autonomous` is a deprecated no-op" | Errors (`cli_types/mod.rs:191-195`) | Medium | "removed; now errors" |

**Verified clean:** `init` flags, `plugin install-defaults`/`--flavor`/`--yes`, `plugin install --project` + `.animus/plugins.lock`, preflight flags, `agent interactions`, minimal workflow YAML, `--interval-secs` "fallback heartbeat" wording, `model: claude-sonnet-4-6`.

---

### animus-bootstrap — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~429 | Anti-pattern recommends `post_success.merge.auto_merge: false` | Hard parse error (`yaml_parser.rs:383-412`) | High | Remove; express merge/PR as `command:` phases (Phase 6 already does) |
| 2 | ~384 | `daemon start --auto-run-ready true --pool-size 3` | Flag removed | High | `daemon start --pool-size 3` |
| 3 | Phase 10/13 | Dispatch narrative | Daemon queue-only | Low | Don't introduce Ready-auto-dispatch language |
| 4 | ~148 | `scanner: { model: claude-haiku-4-5, tool: claude }` | `claude-haiku-4-5` not in roster/alias table (`model_routing.rs`); passes through only because `tool: claude` set | Low | Use a roster model or note haiku needs explicit `tool:` |

**Verified clean:** model roster (opus-4-8/sonnet-4-6/gpt-5.5), `approval_policy`, `permission_mode`, `cwd_mode: task_root`, `on_verdict`, `max_rework_attempts`, `budget:` (`on_exceed: pause|fail|warn`), cron `schedules:`, `workflow config validate`, `workflow definitions list`, `queue enqueue --title/--workflow-ref`.

---

### animus-daemon-operations — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~56/67 | `--auto-run-ready true` example + `--auto-run-ready true\|false` option | No field in `DaemonSchedulerArgs` (`daemon_types.rs:127-186`) | High | Remove from example + options list |
| 2 | ~67 | option help "automatically dispatch ready queued subjects" | Queue-only (`validation.rs:1151`) | High | Reframe: executes enqueued entries + cron schedules |
| 3 | ~79-82 | "merge/PR behavior lives in workflow `post_success.merge`" **(new)** | Hard parse error (`yaml_parser.rs:383-412`) | High | Replace with command-phase guidance |
| 4 | ~76 | `--skip-runner` "do not auto-start the runner" | No such arg; sidecar deleted v0.5.3 | High | Delete the line |
| 5 | ~63 | "`--autonomous` is a hidden deprecated no-op" | Errors (`docs/reference/cli/index.md:387-390`) | Medium | "removed; now errors" |
| 6 | ~274-283 | `daemon config --auto-run-ready true`; omits real knobs | `DaemonConfigArgs` has `--max-daily-usd` + `--silent-threshold-mins`, no `auto_run_ready` (`daemon_types.rs:281-328`) | Medium | Remove the flag; add the two knobs |

**Verified clean:** 4-role preflight (already fixed), supervisor budget "3/60s → 5-min cooldown" (`plugin-host/src/status.rs:48`), `daemon metrics cleanup`, MCP-tool table, `daemon stream` flags, exit codes, kill-switches.

---

### animus-configuration — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~153 | `daemon config --pool-size 3 --auto-run-ready true` | No `auto_run_ready` (`daemon_types.rs:281-328`) | High | Remove `--auto-run-ready true` |
| 2 | ~164-168 | "merge/PR behavior lives in workflow `post_success.merge`" **(new)** | Hard parse error (`yaml_parser.rs:383-412`) | High | Replace with command-phase guidance |
| 3 | config section | Omits `--max-daily-usd` (24h fleet cap) + `--silent-threshold-mins` (default 20) | `daemon_types.rs:316,322`; `daemon_config.rs:15` | Medium | Add both |
| 4 | ~180-181 | "`--autonomous` is a hidden deprecated no-op" | Errors (`docs/reference/cli/index.md:387-390`) | Medium | "removed; now errors" |
| 5 | ~391-393 | `cost ... --by provider\|model` | Also `--by task` (`cost_types.rs`) | Low | Add `task` |

**Verified clean:** scheduler defaults (`interval_secs`=5, `max_tasks_per_tick`=2), env-var tables incl. `ANIMUS_WORKFLOW_CONCURRENCY_MAX`/`TRIGGER_BACKLOG_MAX`/`SUBSCRIBER_MEMORY_MAX_MB`/`PLUGIN_PROCESS_MAX` (10/1000/10/50, `quotas.rs:24-40`), removed `ANIMUS_RUNNER_*` vars, kill-switches, secret handling, state tree.

---

### animus-troubleshooting — Significant fixes ↑

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~296-298 | "Merge/PR behavior is defined per workflow in `post_success.merge`" **(new)** | Hard parse error (`yaml_parser.rs:383-412`) | High | Rewrite: merge/PR = `command:` phases |
| 2 | ~237-238 | "drain even when `auto_run_ready` is false (gates ready-task auto-dispatch)" | Removed; queue-only (`validation.rs:1151`) | High | Drop parenthetical; "enqueued entries dispatch as slots free" |
| 3 | ~235 | Step 2 "Check ready task subjects" implies ready→pickup | Ready alone never dispatches (`validation.rs:1151`) | Medium | "a `ready` subject is eligible to enqueue, not auto-run" |
| 4 | ~233 | `daemon health` shows `runtime: paused` | **Revised — acceptable.** Human output prints `runtime: paused` (`runtime_daemon.rs:306-307`); only the JSON field is `runtime_paused` | Low (opt) | Optional: mention the JSON field name `runtime_paused` |

**Verified clean:** 4-role preflight + exit-code table (2/3/4/5 + preflight 2/1, `cli_error.rs:150`), pool defaults (10/2), removed merge keys, `runner`→doctor, budget kill-switch, `agent interactions`, `queue drop` positional ids, `subject status --status ready` "unstuck: cleared", `workflow prompt render`, `mcp auth`.

---

### animus-workflow-authoring — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | SKILL ~60; references/top-level-and-routing.md ~189-209 | `post_success.merge` is a supported merge/PR surface ("the only merge/PR automation surface") | Hard parse error (`yaml_parser.rs:383-412`) | High | Remove; git automation = command phases |
| 2 | references/automation-and-integrations.md ~161-198 | `auto_run_ready` listed as one of four consumed daemon YAML fields ("# auto-dispatch Ready subjects"); plus an `auto_run_ready` overlay-merge note (~197-198) | Not a `DaemonConfig` field (only `active_hours`/`phase_routing`/`mcp`/`budget`, `types.rs:766-781`); removed key (`validation.rs:1151`) | High | Drop `auto_run_ready`; list `daemon.budget` (`max_cost_usd_per_day`, `on_exceed`, `types.rs:785-796`) as the real fourth field |
| 3 | references/automation-and-integrations.md ~58-71, ~183-187 | `integrations.git` with `auto_pr: true`/`auto_merge: false`; "merge/PR lives in `post_success.merge`" | `auto_merge` rejected at parse (`yaml_parser.rs:414-432`); no such fields (`types.rs:595-602`) — won't compile | High | Keep only `provider`/`base_branch`/`config`; command-phase guidance |
| 4 | references/top-level-and-routing.md surface list | Omits `daemon.budget` | `YamlWorkflowFile` (`yaml_types.rs:375-413`) | Low | Note the `budget:` sub-block |

**Verified clean (full reads of all 4 references):** agents/phases schema (phase fields, `evals` parse-only `validation.rs:1170-1173`, `runtime` overrides, `permission_mode` forwarded, worktree shorthands, skill-union), schedules (workflow_ref required), triggers (`file_watcher`/`webhook`/`github_webhook`/`plugin`), top-level surface list matches `yaml_types.rs:375-413` exactly.

---

### animus-workflow-patterns — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~99-112 | `post_success.merge` is "the ONLY built-in merge/PR surface" (full YAML block) | Hard parse error (`yaml_parser.rs:383-412`) | High | Delete block + framing; command-phase push/PR shown elsewhere is the only path |
| 2 | ~107-112 | A second standalone `post_success: merge:` simplification block ~~**(new — distinct from #1)**~~ | **REFUTED (source pass):** only ONE `post_success.merge` block exists (prose ~99 + single YAML block 104-109); no distinct second block | — | **Drop this row** — #1 covers it |
| 3 | ~770 | Created-Ready tasks "auto-dispatch when `auto_run_ready` is on" | Never auto-dispatched (`validation.rs:1151`) | High | Rewrite: Ready subjects are never auto-run; enqueue/cron required |
| 4 | ~114-117 | cwd_mode dual-default (parser `project_root` vs serde `task_root`) | **CONFIRMED (source pass):** parser defaults omitted `cwd_mode`→`ProjectRoot` (`yaml_parser.rs:172`); serde runtime defaults→`TaskRoot` (`agent_runtime_config.rs:1045-1046`, field `:784-785`); allowed `project_root\|task_root\|path` (`yaml_parser.rs:97-103`). Skill text at 114-117 already correct | Low | No change needed — keep "always set `cwd_mode` explicitly". Drop the "verify before relying" caveat |
| 5 | ~782-788 | "Differences on installed v0.5.14" version-delta | Out of scope; describes shipped surface | Low | Drop the section |

**Verified clean:** cwd_mode gotcha advice, command-vs-agent split, rework loops, conductor/sweep architecture, per-model routing, `daemon stream`/`observe`, `agent interactions answer --select`, `workflow resume --id --force`, `workflow prune/delete`, `output decisions`, budget enforcement, evals-not-executed.

---

### animus-queue-management — Significant fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~72-74 | "drain even when `daemon.auto_run_ready` is false; gates ready-task auto-dispatch" | Removed; queue-only (`validation.rs:1150-1152`) | High | Delete paragraph; queue-only leasing model |
| 2 | ~48-70 | Omits deferred-dispatch flags | `QueueEnqueueArgs` has `--at`→`run_at`, `--expire-after`→`expire_after_secs` (requires `run_at`), `--input-json` (`queue_types.rs:55-70`) | Medium | Add all three; note `deferred` state |
| 3 | ~41-46 | Stats fields: total/pending/assigned/held | Also `(N deferred)` (`ops_queue.rs:250-254`; `QueueStats.deferred`) | Low | Add `deferred` |

**Verified clean:** bulk `hold`/`release`/`drop` (positional ids, `--all --yes`, eligible-status rules), legacy `--subject-id`, `reorder --subject-id`, non-zero exit on partial failure, MCP tool table (7 tools), `<kind>:<native>` enqueue fallback (already applied), nudge/event-driven paragraph. Note: enqueue is **not** deduplicated (warns on dupes) — the "Duplicate Prevention" pattern could be sharpened.

---

### animus-subject-operations — Minor fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~158-159 | "drain even when `daemon.auto_run_ready` is false; gates ready-task auto-dispatch" | Removed; queue-only (`validation.rs:1150-1152`) | High | Delete the final sentence (nudge prose above it is accurate) |
| 2 | ~196-201 + `animus_version` | Version-delta section | `batch-create`/`batch-update` exist (`subject_types.rs:48,57`) | Low | Drop the section |

**Verified clean:** `--include-subjects` legacy claim, exit codes (2/3/5 global), batch schema ids `animus.cli.batch.result.v1` (`ops_subject.rs:25`) / `animus.mcp.batch.result.v1` (`ops_mcp.rs:156`), create-`--body`/update-rejects-`--body`, delete CLI-only (no `animus.subject.delete` MCP tool; 8 subject tools), 100-item cap, wire-id formats, `<kind>:<native>` note (already applied).

---

### animus-task-management — Minor fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~214-215 | "enqueue drains even when `daemon.auto_run_ready` false" | Removed; queue-only (`validation.rs:1150-1152`) | High | Remove parenthetical; enqueue required (daemon runs enqueued + cron only) |
| 2 | ~174-180 | "Tasks are dispatchable when the backend reports `ready`" | `ready` alone never auto-dispatches (`validation.rs:1152`) | Medium | "`ready` = eligible to enqueue; dispatched only after `queue enqueue`/cron" |
| 3 | ~216 | Step 3 "or let the daemon pick it up" **(new)** | Daemon picks up *enqueued* entries, not arbitrary Ready tasks | Medium | "picked up because enqueued in step 2 — no separate Ready-pickup path" |
| 4 | ~219-224 + `animus_version` | Version-delta section | Batch subcommands exist | Low | Drop the section |

**Verified clean:** status lifecycle (`in-progress` canonical, `in_progress` input alias `orchestrator.rs:51,68`; ready/blocked/done/cancelled), `history task --task-id`, `output read`/`phase-outputs`, `workflow run <pipeline> --task-id`, MCP tool table (8 tools), batch schema/cap.

---

### animus-mcp-tools — Significant fixes ↑

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | references/agent-daemon-task.md ~89 | `daemon.start` params include `auto_run_ready`, `skip_runner`, `autonomous`, `auto_install`, `skip_preflight` | `DaemonStartInput` (`ops_mcp/daemon_inputs.rs:4-23`) has none — only pool_size/interval_secs/stale_threshold_hours/max_tasks_per_tick/phase_timeout_secs/startup_cleanup/resume_interrupted/reconcile_stale/project_root | High | Remove all five; list the 9 real fields |
| 2 | references/agent-daemon-task.md ~84-85 (prose) | "`auto_install`/`skip_preflight` exposed on `daemon.start`; `autonomous` deprecated no-op" | Not on the input struct (`daemon_inputs.rs:4-23`) | High | Delete the prose |
| 3 | references/agent-daemon-task.md ~99 | `daemon.config-set` includes `auto_run_ready` | `DaemonConfigSetInput` (`daemon_inputs.rs:69-90`) has no `auto_run_ready` | Medium | Remove it |
| 4 | references/workflow-queue-requirements.md ~47 | `queue.enqueue` params omit deferred-dispatch **(new)** | `QueueEnqueueInput` also has `run_at` + `expire_after` (`queue_inputs.rs:21-26`; `mcp-tools.md:222`) | Medium | Add `run_at`/`expire_after` |

**Verified clean (SKILL + all 3 refs):** every MCP tool *name* matches the registered set (`ops_mcp/` grep) and `docs/reference/mcp-tools.md`; `animus.task.*`/`animus.requirements.*` are back-compat-only and not registered (skill's "removed" claim correct); `output.run` MCP vs `output read` CLI; `phase.reject` `reason` required; `agent.run`/`plugin.install` params; pagination/batch/remediation conventions. **Note:** `docs/reference/mcp-tools.md:127` is itself stale (lists `auto_install`/`skip_preflight` on `daemon.start`) — source struct wins.

---

### animus-project-history-git — Significant fixes ↑

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~18-19 | "merge/PR/commit lives in the workflow runner plugin via `post_success.merge`" **(new)** | Hard parse error (`yaml_parser.rs:383-412`) | High | Remove; merge/PR = `command:` phases |
| 2 | ~88 | `approval respond --request-id <id> --approved` | Flag is `--approve` (`approval_types.rs:30-31`); `--approved` errors as unknown | High | `--approved` → `--approve` |
| 3 | ~92-93 | "omit `--approved`/`--success` to reject / record failure" | `respond` requires exactly one of `--approve`/`--reject` (omitting errors, `approval_types.rs:44-52`); `outcome` omit-`--success`=failure is correct | Medium | "respond requires `--approve` or `--reject`; for `outcome`, omit `--success` for failure" |

**Verified clean:** git inspection surface (only `repo list`, `worktree list`, `worktree prune`; deleted verbs flagged), `worktree prune` args (`--repo`/`--confirmation-id`/`--delete-remote-branch`/`--remote`/`--dry-run`, `git_types.rs:37-58`), history verbs/flags (`--since` vs `--started-after` conflict, `--offset`), `approval request/respond/outcome` arg names, repo-scope resolution.

---

### animus-plugin-operations — Minor fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~61, ~176 | `plugin info --name X` | `PluginInfoArgs.name` is positional (`plugin_types.rs:633`) | Medium | `plugin info X` (drop `--name`) |
| 2 | (whole) | No mention of `plugin prune` | `PluginPruneArgs`/`Prune` subcommand exists (`plugin_types.rs:593-601`); it's the "prune remedy" cited at ~66/192 | Low | Document `plugin prune [--yes]` |

**Revised from pass 1:** `plugin status [NAME]` and `revoke-trust <ORG>` are already positional in the skill (correct); `plugin ping`/`plugin call` legitimately use `--name` (`plugin_types.rs:641,657`). The `outdated --project` finding was **moot** — the skill never claims it. **Verified clean:** discovery order (incl. legacy `~/.config/animus/plugins.yaml`), 4-role preflight (already fixed), signature-policy flags/aliases, TOFU verbs, lockfile dual-root, install flags (`--latest`/`@TAG`/`--as-kind`/`--allow-shadow-builtin`), MCP-tools subsection list.

---

### animus-model-operations — Minor fixes ↑

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~184 | `plugin info --name <NAME>` | `name` is positional (`plugin_types.rs:633`) | Medium | `plugin info <NAME>` |

**Verified clean:** correctly states `animus model`/`runner` groups removed (absent from `root_types.rs`); tool-inference table matches `tool_for_model_id` (`model_routing.rs:159-197`); `canonical_model_id()` aliases (`opus`→`claude-opus-4-8`, `model_routing.rs:119`); `fallback_models` ids valid; `workflow agent-runtime {get,validate,set}`; `plugin ping --name` is correct (`ping` takes a flag).

---

### animus-cost-operations — Minor fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~22-24 | `cost summary --by provider\|model` | `CostSummaryBy` also has `Task` (`cost_types.rs:34-42`; `docs/reference/cli/index.md:331`) | Medium | Add `--by task` |
| 2 | ~20 | No `--lifetime` | `--lifetime` reports each run's full lifetime spend (`cost_types.rs:55-59`) | Medium | Document it |
| 3 | ~21 | No reported-vs-estimated note | Text output marks `(est.)` (`cli/index.md:331`) | Low | Optional detail |

**Verified clean:** `animus.cost.decisions` MCP tool, state paths, `cost top --by tokens|cost|model|provider` (default cost, limit 10), `cost workflow --by provider|model|phase`, `cost trends --window day|week|month --n 30`, `cost conversation`, `cost decisions --since`, budget YAML.

---

### animus-agent-operations — Minor fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~57 | `--start-runner true\|false` "controls automatic runner startup" | `hide = true`, "Deprecated no-op (sidecar removed v0.5.3)" (`agent_types.rs:236-243`) | Medium | Remove from useful-flags, or mark hidden deprecated no-op |

**Verified clean:** memory/message/interactions tools (`animus.agent.*`/`memory.*`/`interactions.*`), `agent.ask`/`request_approval` (`wait: block|suspend`), interaction timeout (600s/3600s, `interaction_tools.rs:11-12`), all `agent run` flags (`agent_types.rs:168-264`), `interactions answer --allow/--deny/--remember/--updated-input/--select/--by`.

---

### animus-supply-chain-security — Minor fixes

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | ~53-54, ~183-187 | "workflow-runner default pin v0.4.3 is the first cosign-signed runner release" | Current default pin v0.4.5 (`plugin_registry.rs:31`) | Low | Update to v0.4.5 or make version-neutral |

> Borderline vs the "ignore version numbers" scope rule — included because it's a concrete, source-checkable claim about the current registry default, not an "installed version" concern.

**Verified clean:** install pipeline (sha256 → cosign → TOFU → lockfile fail-closed), policy modes + aliases (`require_signature`/`allow_unsigned`/`skip_signature`, `plugin_types.rs:536-549`), `--allow-shadow-builtin` builtin list incl. `oai-runner` (`:555`), `--force-rewrite-lockfile` (`:570-577`), `trust list`/`revoke-trust` (positional org), dual lockfile roots.

---

### animus-pack-authoring — Minor fixes ↑

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | references/manifest.md ~138-140 | `native_module.feature`/`module_id` marked optional | `PackNativeModule` (`pack_config/types.rs:206-213`) makes both **required** when `[native_module]` present; only `optional` defaults | Low | Mark `feature`/`module_id` required |
| 2 | references/runtime-and-workflows.md ~67 | `tool_policy.deny: [..., project.remove]` example | `project` CLI/MCP group removed; `project.remove` is a dead tool-id | Low | Use a live tool-id in the illustration (freeform globs, harmless) |

**Verified clean (SKILL + all 3 refs):** full `pack.toml` schema (`animus.pack.v1`, ownership, compatibility incl. `ao_core` alias, subjects, workflows root/exports, runtime, mcp, schedules, dependencies, `requires_plugins` repo/tag/role/optional/reason, permissions, secrets, native_module, skills) matches `pack_config/types.rs:8-256`; full `pack` CLI (`install`/`list`/`info`/`pin`/`uninstall`/`search`/`publish`/`registry`) matches `pack_types.rs`.

---

### animus-skill-authoring — Minor fixes ↑

| # | Location | Claim | Source says | Sev | Fix |
|---|---|---|---|---|---|
| 1 | references/cli-and-registry.md ~92-96 | `skill registry add --id --url` | `SkillRegistryAddArgs` also has `--priority` (`skill_types.rs:53-54`) | Low | Add `--priority` (search priority; lower = higher) |
| 2 | references/schema.md ~117-130 | Capability alias list | Source accepts more aliases (e.g. `file_writes`, `state_mutation`, `require_commit`, `product_changes`, etc., `skill_definition.rs:193-209`) | Low | Note the list is a subset |
| 3 | references/cli-and-registry.md ~46 | `--source built-in` advertised | CLI help still lists it (`skill_types.rs:144`) though there is no builtin tier (schema.md:216 says so) | Low | Both mirror code; harmless |

**Verified clean (SKILL + all 3 refs):** full `SkillDefinition` schema (name/version/description/category/activation/prompt/tool_policy/model/mcp_servers/timeout_secs/capabilities/extra_args/env/codex_config_overrides/adapters/tags, `skill_definition.rs:89-134`), category enum (`:9-18`), capability validation, full `skill` CLI (`create`/`search`/`install`/`list`/`info`/`update`/`uninstall`/`publish`/`registry`), `--name` slug rule, tool-id alias normalization (`open-code`→`opencode`).

---

### Accurate skills (verified clean in full read)

- **animus-observability** — observe/health/metrics/stream/events/logs surfaces + flags, `output {read,decisions,monitor,jsonl,phase-outputs,artifacts,download,cli}`, exit codes, `animus.output.tail` MCP-only. *Optional Low:* exit-code para omits conflict→4 (`cli_error.rs:150`); `--cat runner` is a legacy label. Carries none of the three themes.
- **animus-mcp-setup** — `mcp serve`/`memory`/`auth*`, tool counts (86 management / 84 default) + per-group counts, Claude Code tool-id mangling, removed-surface guidance. *Optional Low:* drop version-delta section.
- **animus-flavor-operations** — verbs/flags/envelope, default required+recommended sets vs `flavors/default.toml`, 4-role preflight (already fixed) all match `flavor_types.rs:4-47` + `plugin_preflight/mod.rs:194-214`. Fully clean.
- **animus-mcp-servers-for-agents** — `McpServerDefinition`/`OauthConfig` fields + all four OAuth flows, `mcp_servers:`/`phase_mcp_bindings:`, `mcp auth*`, env pins, `secret set`, skill-as-attachment-path. Fully clean.
- **animus-agent-interactions** — interactions list/show/answer + all flags, block-vs-suspend, approval_policy routing, claude `--permission-prompt-tool` wire contract (verbatim, `interaction_tools.rs:274-306`), `no animus.interactions.get`, `animus approval` distinction. *Optional Low:* add `questions[]` to the `agent.ask` param list.
- **animus-agent-personas** — model ids (`model_routing.rs:209-211`; `claude-haiku-4-5` is valid pass-through), `skill.create`/`update`, `output phase-outputs`, guardrails, escalation via `agent.ask`/`request_approval`. Persona/pack content is illustrative; no removed-surface refs.
- **animus-chat** — every `chat` subcommand + all `send` flags (`chat_types.rs:11-107`), `--reasoning-effort` mapping, `export --format`, `search --limit/--case-sensitive`, resume-XOR-replay (single replay retry, `docs/reference/chat.md:9-35`), `cost conversation`. Fully clean.

---

## Recommended remediation order

1. **Theme 1 sweep (11 skills)** — purge `--auto-run-ready` / `daemon.auto_run_ready` / "gates ready-task auto-dispatch" everywhere; replace with the queue-only model (enqueue + cron `schedules:` are the only triggers; `ready` status ≠ pickup). Highest blast radius, mostly mechanical.
2. **Theme 2 sweep (7 skills)** — remove `post_success.merge` / `integrations.git.auto_merge` guidance; point to `command:` phases. Now confirmed in daemon-operations, configuration, troubleshooting, and project-history-git in addition to the three workflow/bootstrap skills.
3. **High-severity isolated** — mcp-tools daemon MCP params; project-history-git `--approve`; daemon-operations `--skip-runner` deletion.
4. **Theme 3** — `--autonomous` "now errors" wording (4 skills).
5. **Medium gaps** — plugin/model `plugin info` positional; cost `--by task`/`--lifetime`; queue + mcp-tools deferred-dispatch params; agent-operations `--start-runner`; daemon/config `--max-daily-usd`/`--silent-threshold-mins`; task-management line ~216.
6. **Low/cleanup** — supply-chain pin v0.4.5; bootstrap/personas `claude-haiku-4-5`; pack `native_module` requiredness + dead `project.remove` glob; skill-authoring `--priority`/alias completeness; observability exit-code 4; drop version-delta sections / `animus_version` pins gating already-shipped surface.

## Upstream follow-up (separate repo)

`animus-cli`'s own `CLAUDE.md` is stale on Themes 1 & 2 (it still describes `daemon:` consuming `auto_run_ready` and `post_success.merge` as the live merge surface), and `docs/reference/mcp-tools.md:127` lists `auto_install`/`skip_preflight` on `animus.daemon.start` that the input struct doesn't have. All three verified wrong against source on 2026-06-18 — worth a corrective PR so future skill refreshes don't re-inherit the errors.
