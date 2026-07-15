# Portal (animus-launchapp) MCP Tool Families

Use this reference when driving Animus through the portal's MCP server
(`mcp__animus-launchapp__*`). These families exist only on the portal, not on
local `animus mcp serve`. Portal names are flat snake_case; params camelCase.

**Admin visibility:** tools marked ADMIN are only *registered* for admin
users — a non-admin client never sees them in `tools/list` (and the handlers
re-check). If a documented tool is missing, check the connected user's role
before suspecting a version mismatch.

## Team tools — author workflows/agents/phases over MCP

These are DEFINITION tools (they shape the team config), wrapping
`animus workflow config …` write-back verbs. A complete custom workflow —
agent + phase + workflow — is authorable through MCP alone.

| Tool | Access | Key parameters |
|------|--------|----------------|
| `team_config_get` | read | none — returns the compiled WorkflowConfig: agent profiles, workflow definitions, phase definitions, MCP server definitions |
| `team_agent_set` | ADMIN | `id`, `model?`, `tool?` (`claude`/`codex`/…), `systemPrompt?`, `mcpServers?` (string[]), `extraConfig?` (passthrough bag, e.g. `reasoning_effort`; keys clashing with model/tool/provider/system_prompt are stripped) |
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
and survives redeploys; `path` installs and `skill_create` land in the
ephemeral project scope (`/app/.animus/skills`) and are wiped on redeploy —
prefer GitHub installs for anything that must persist. Org-owned skill packs
are re-seeded on boot.

## Renamed dispatch params (v0.7 breaking, portal side)

- `run_workflow`: `taskId` → `subjectId` (qualified id of any kind).
- `queue_enqueue`: `taskId`/`requirementId` removed → `subjectId`
  (mutually exclusive with `title` for ad-hoc dispatch).
- `workflow_list`: `taskId` → `subjectId`.
- `list_subjects`: paginated — `cursor` (from `next_cursor`; page until
  null) + `status` filter alongside `kind`/`limit` (max 200). Never assume
  the first page is the whole board.
- `list_kinds`: also advertises MCP-binding-derived `ext.*` kinds.

## Trigger-event observability

Every trigger delivery (schedules, `triggers:` blocks, webhooks) writes a
`trigger_event` subject (status `done`, delivery metadata in `custom`) —
query them like any subject (`list_subjects` with `kind: "trigger_event"`)
to answer "did my trigger fire". Events are pruned past 30 days beyond the
newest 2000.
