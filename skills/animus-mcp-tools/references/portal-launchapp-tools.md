# Portal (animus-launchapp) MCP Tool Families

Use this reference when driving Animus through the portal's MCP server
(`mcp__animus-launchapp__*`). Most of these families are portal-only — though
local `animus mcp serve` does expose skill tools
(`animus.skill.{list,search,get,create,update}`); only the
`skill_install`/`skill_uninstall`/`skill_info` shapes are portal-only. Portal
names are flat snake_case. Param casing is mixed: dispatch/team tools use
camelCase (`subjectId`, `workflowRef`); `trigger_*`, kind management, and
`run_events` use snake_case (`workflow_ref`, `github_event`, `run_id`).

**Admin visibility:** tools marked ADMIN are only *registered* for admin
users — a non-admin client never sees them in `tools/list` (and the handlers
re-check). The complete admin-only set: `team_*` writes,
`script_set`/`script_remove`, `sql_execute` (the other sql tools are
read-scope), all five `trigger_*`, `queue_drop`/`queue_reorder`,
`daemon_pause`/`daemon_resume`, `agent_control`,
`plugin_install`/`plugin_uninstall`/`plugin_update`,
`declare_kind`/`update_kind`/`delete_kind`, and
`note_list_pending`/`note_approve`/`note_reject`/`note_review_pending`.
If a documented tool is missing, check the connected user's role before
suspecting a version mismatch.

## Team tools — author workflows/agents/phases over MCP

These are DEFINITION tools (they shape the team config), wrapping
`animus workflow config …` write-back verbs. A complete custom workflow —
agent + phase + workflow — is authorable through MCP alone.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `team_config_get` | read | none — returns the compiled WorkflowConfig: agent profiles, workflow definitions, phase definitions, MCP server definitions |
| `team_agent_set` | ADMIN | `id`, `model?`, `tool?` (`claude`/`codex`/…), `systemPrompt?`, `mcpServers?` (string[]), `extraConfig?` (passthrough bag, e.g. `reasoning_effort`; keys clashing with model/tool/provider/system_prompt/system_prompt_file are stripped) |
| `team_agent_remove` | ADMIN | `id` |
| `team_workflow_set` | ADMIN | `id`, `name`, `description?`, `phases` (bare phase-name strings OR rich steps `{id, on_verdict?, max_rework_attempts?}`), `budget?` (object or null), `isDefault?` (note: does NOT currently update `default_workflow_ref`) |
| `team_phase_set` | ADMIN | `id`, `agentId?`, `mode?` (`agent` default \| `command` \| `manual`), `directive?`, `extraConfig?` (capabilities, output_contract, retry, command, …) |
| `team_workflow_remove` | ADMIN | `id` |
| `team_reload` | ADMIN | none — force a daemon config reload (writes attempt auto-reload; this is the explicit apply) |

`team_phase_set` (needs ao-cli ≥ v0.7.0-rc.13) writes `phase_definitions` on
the config_source **base** — the layer `workflow config validate` actually
sees — unlike the legacy `workflow phases upsert`, which writes an
agent-runtime overlay the validator ignores. Prefer `team_phase_set` for any
phase authoring.

The portal-only `provider` routing field on agents is set in the web Team
Designer, not through `team_agent_set`.

## Script registry — durable command-phase scripts

Team-editable scripts stored in Postgres and materialized to
`/data/animus-state/scripts/<name>.<ext>` (0755, atomic) — survive redeploys
and volume resets, no image rebuild. v1 is interpreted-only.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `script_list` | read | none — metadata only, content omitted |
| `script_get` | read | `name` — full record including content |
| `script_set` | ADMIN | `name` (`^[a-zA-Z0-9._-]+$`, no `..`), `content`, `language?` (`bash` default \| `python` \| `typescript`), `description?` |
| `script_remove` | ADMIN | `name` — deletes row + materialized file |

Interpreter map: bash→`bash` (.sh), python→`python3` (.py),
typescript→`tsx` (.ts). The interpreter must be in the daemon's command-phase
`tools_allowlist`. Seeds under `deploy/script-seeds/` are inserted-if-absent
on boot and never overwrite admin edits.

Wire a script into a workflow phase:

```yaml
phases:
  my-scripted-phase:
    mode: command
    command:
      program: bash
      args: ["/data/animus-state/scripts/<name>.sh"]
      parse_json_output: true    # required for the script's phase_decision to count
```

## `phase_context_schema` — the command-phase authoring contract

Read-scope, no params. Returns ONE JSON document containing everything a
command-phase script author needs:

1. **Runner-injected env scalars:** `ANIMUS_SUBJECT_ID` (kind-qualified, e.g.
   `task:TASK-123`), `ANIMUS_SUBJECT_NATIVE_ID`, `ANIMUS_SUBJECT_KIND`,
   `ANIMUS_SUBJECT_TITLE`, `ANIMUS_SUBJECT_STATUS`, `ANIMUS_WORKFLOW_REF`,
   `ANIMUS_WORKFLOW_ID` (run id), `ANIMUS_PHASE_ID`, `ANIMUS_PROJECT_ROOT`,
   `ANIMUS_EXECUTION_CWD`, `ANIMUS_DISPATCH_INPUT`, `ANIMUS_CONTEXT_FILE`.
2. **JSON Schema of the `$ANIMUS_CONTEXT_FILE` document:**
   `{subject: {id, native_id, kind, title, status, priority, description,
   data, labels, dependencies}, workflow: {ref, run_id, phase_id},
   phases: [{id, verdict, outputs}] (prior completed phases with real
   outputs), dispatch_input}`.
3. **The `phase_decision` emit schema:** the script prints exactly one JSON
   object to stdout —
   `{kind: "phase_decision", verdict: "advance|rework|skip|fail|<custom>",
   reason?, confidence?, risk?, target_phase?, outputs?}`. Parsed ONLY when
   the phase command sets `parse_json_output: true` (optionally
   `expected_result_kind` / `expected_schema`). Custom verdicts route via the
   phase's `on_verdict` map — full agent-phase parity.

Call it before authoring any command-phase script; do not hand-roll the
contract from memory.

## Portal skill tools

Wrap `animus skill …`. list/search/info are read-scope; the mutators are
write-scope (not admin).

| Tool | Key parameters |
|------|----------------|
| `skill_list` | `source?` (`built-in`/`user`/`project`/`installed`), `verbose?` |
| `skill_search` | `query`, `source?`, `registry?` |
| `skill_info` | `name` |
| `skill_install` | exactly one of `source` (GitHub `OWNER/REPO[@ref]`, tree URL, or raw SKILL.md URL) or `path` (local); `name?` (path only), `version?` |
| `skill_create` | `name`, `description`, `prompt`, `category?` (implementation/testing/review/research/documentation/operations/planning), `tags?`, `user?` |
| `skill_uninstall` | `name` (destructive) |
| `skill_update` | `name?` — omit to update all installed |

**Durability on the portal:** GitHub `skill_install --source` writes the
durable on-volume registry (`/data/animus-state/state/skills-registry.v1.json`)
and survives redeploys. `path` installs materialize into `/app/.animus/skills`;
`skill_create` writes project-scope skill definitions at
`.animus/config/skill_definitions/` — both are ephemeral and wiped on
redeploy. Prefer GitHub installs for anything that must persist. Org-owned
skill packs are re-seeded on boot.

## Knowledge notes (`note_*`)

Private-by-default personal notes with an org-share review loop. The owner
is always the authed session user — never client-supplied. Reviewer tools
are admin-only registered.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `note_log` | write | `title`, `body`, `tags?`, `source?` — creates a PRIVATE note owned by you |
| `note_search` | read | `query?`, `scope?` (`mine`/`org`/`all` default) — your own notes + org-shared; never returns others' private/pending notes |
| `note_get` | read | `id` — allowed if owner, org-visible, or admin |
| `note_submit` | write | `id` — owner-only; secret scan first (a hard secret BLOCKS and the note stays private), else → `pending_review` |
| `note_list_pending` | ADMIN | none — the `pending_review` queue with scan results |
| `note_approve` | ADMIN | `id`, `review_note?` — pending → org-wide |
| `note_reject` | ADMIN | `id`, `reason` — pending → rejected (owner keeps access) |
| `note_review_pending` | ADMIN | `limit?`, `dry_run?` — LLM auto-reviewer over the queue; FAIL-CLOSED (any error/uncertainty rejects, never auto-approves) |

## Documents (`*_document`)

Persist and read rendered Office documents (xlsx/pptx/docx) as `document`
subjects + S3 objects. Render the bytes FIRST via the animus-document-engine
MCP (`render_document`); these tools only persist. Write-scope, NOT admin.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `author_document` | write | `format` (`xlsx`/`pptx`/`docx`), `spec`, `bytes_base64`, `title`, `visibility?` (`private` default / `org`), `filename?`, `source_subject_id?` — owner = session user |
| `edit_document` | write | `id`, `bytes_base64`, `spec?` — owner-only replace of bytes + spec |
| `get_document` | read | `id` — owner or workspace-shared; others' private docs report not-found |
| `list_documents` | read | `scope?` (`mine`/`workspace`/`all` default), `format?` |

## Subject-kind management (ADMIN)

BaaS kind registry — reshapes the board for the whole workspace. Snake_case
params; built-in kinds cannot be redeclared or deleted.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `declare_kind` | ADMIN | `name` (lower_snake), `id_prefix?` (e.g. `CAMP-`), `title_field?`, `fields?` (each `{name, type, required?, default?, description?}`) |
| `update_kind` | ADMIN | `name` + at least one of `fields`/`title_field`/`id_prefix` |
| `delete_kind` | ADMIN | `name`, `cascade?` (true also deletes every subject of the kind, irreversible; otherwise refuses while rows exist) |

## SQL over the live portal DB

The read tools run inside a READ-ONLY transaction and are registered for
all members; only `sql_execute` is admin.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `sql_query` | read | `sql` (use `$1, $2, …`), `params?`, `limit?` (default 200, max 1000) — writes rejected by the DB |
| `list_tables` | read | none — public-schema base tables |
| `describe_table` | read | `table` — columns, types, nullability |
| `sql_execute` | ADMIN | `sql`, `params?` — read-WRITE in `BEGIN..COMMIT`, audit-logged |

## Packs

Wrap `animus pack …`. List is read-scope; the mutators are write-scope
(NOT admin).

| Tool | Access | Key parameters |
|------|--------|----------------|
| `pack_list` | read | `source?` (`bundled`/`installed`/`project_override`), `active_only?` |
| `pack_install` | write | exactly one of `name` (+ `registry?`) or `path`; `activate?` |
| `pack_uninstall` | write | `name` — destructive (per-boot seeds re-install on reboot) |
| `pack_activate` | write | `name` — wraps `animus pack pin --pack-id` |

## Plugins

Read tools for all members; the mutators are ADMIN.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `plugin_list` | read | none — installed plugins by role |
| `plugin_status` | read | none — per-plugin runtime status (pid, state, restarts) |
| `plugin_info` | read | `name` — manifest + initialize-time capabilities |
| `plugin_outdated` | read | none — installed vs recommended vs latest tags |
| `plugin_search` | read | `query` — public registry search |
| `plugin_install` | ADMIN | `spec` (`OWNER/REPO[@TAG]`, local path, or URL) |
| `plugin_uninstall` | ADMIN | `name` — removing a required-role plugin can break the daemon |
| `plugin_update` | ADMIN | `name?` — omit to update all release-source plugins |

## Ops diagnostics

| Tool | Access | Key parameters |
|------|--------|----------------|
| `run_events` | read | `run_id`, `tail_bytes?` (default 64 KiB), `since?` (ISO-8601, unix-ms, or `5m`/`2h`-style) — tails a run's `events.jsonl`; `age_secs` is the hung-run signal |
| `knowledge_search` | read | `query`, `limit?` (default 25, max 200) — substring search over `kind='knowledge'` subjects |
| `logs_tail` | read | `lines?` (default 100, max 1000) — true tail of the daemon's structured log file |
| `daemon_pause` | ADMIN | none — stop leasing new work (in-flight runs continue) |
| `daemon_resume` | ADMIN | none |

## Renamed dispatch params (v0.7 breaking, portal side)

- `run_workflow`: `taskId` → `subjectId` (qualified id of any kind).
- `queue_enqueue`: `taskId`/`requirementId` removed → `subjectId`
  (mutually exclusive with `title` for ad-hoc dispatch).
- `workflow_list`: `taskId` → `subjectId`.
- `list_subjects`: paginated — `cursor` (from `next_cursor`; page until
  null) + `status` filter alongside `kind`/`limit` (max 200). Never assume
  the first page is the whole board.
- `list_kinds`: also advertises MCP-binding-derived `ext.*` kinds.

## Automation triggers (`trigger_*`, ADMIN)

DB-backed portal triggers (GitHub webhook + cron), managed directly over MCP
— there is no `animus trigger *` CLI verb behind them. All five tools are
ADMIN. Params are snake_case.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `trigger_list` | ADMIN | none — every trigger row |
| `trigger_create` | ADMIN | `name`, `enabled?` (default true), `kind` (`github`\|`cron`), `workflow_ref`; github: `github_event` (required), `github_action?` (null = any), `repo_filter?` (`*` / `owner/*` / `owner/repo`); cron: `cron` (5-field UTC, minute hour dom month dow) |
| `trigger_update` | ADMIN | `id` + the same fields as create — FULL REPLACE, not a patch |
| `trigger_delete` | ADMIN | `id` — destructive |
| `trigger_test` | ADMIN | `id` — dispatches the trigger's workflow immediately regardless of match; does NOT stamp `last_fired_at` |

## Trigger-event observability

Every trigger delivery (schedules, `triggers:` blocks, webhooks) writes a
`trigger_event` subject (status `done`, delivery metadata in `custom`) —
query them like any subject (`list_subjects` with `kind: "trigger_event"`)
to answer "did my trigger fire". Events are pruned past 30 days beyond the
newest 2000.
